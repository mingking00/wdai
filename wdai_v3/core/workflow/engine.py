"""
wdai v3.0 - Workflow Engine
SOP工作流引擎 - 核心引擎

负责编排和执行工作流
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime

from .models import (
    Workflow, WorkflowInstance, WorkflowStatus,
    Step, StepState, StepStatus, ErrorInfo
)
from .dependency import DependencyResolver
from .executor import get_executor_registry, StepExecutionResult

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self._instances: Dict[str, WorkflowInstance] = {}
        self._workflows: Dict[str, Workflow] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._event_handlers: List[Callable[[str, Dict], None]] = []
        self._lock = asyncio.Lock()
    
    def register_workflow(self, workflow: Workflow) -> str:
        """
        注册工作流定义
        
        Args:
            workflow: 工作流定义
            
        Returns:
            workflow_id: 工作流ID
        """
        # 验证工作流
        errors = workflow.validate()
        if errors:
            raise ValueError(f"工作流验证失败: {'; '.join(errors)}")
        
        self._workflows[workflow.id] = workflow
        logger.info(f"工作流已注册: {workflow.id} ({workflow.name})")
        return workflow.id
    
    async def start(
        self,
        workflow: Workflow,
        context: Optional[Dict[str, Any]] = None,
        instance_id: Optional[str] = None
    ) -> WorkflowInstance:
        """
        启动工作流实例
        
        Args:
            workflow: 工作流定义
            context: 初始上下文
            instance_id: 指定实例ID（可选）
            
        Returns:
            工作流实例
        """
        # 创建工作流实例
        instance = WorkflowInstance(
            id=instance_id,
            workflow_id=workflow.id,
            status=WorkflowStatus.PENDING,
            context=context or {},
            started_at=datetime.now()
        )
        
        # 初始化步骤状态
        for step in workflow.steps:
            instance.step_states[step.id] = StepState(step_id=step.id)
        
        # 保存实例
        async with self._lock:
            self._instances[instance.id] = instance
            if workflow.id not in self._workflows:
                self._workflows[workflow.id] = workflow
        
        # 触发事件
        await self._emit_event("workflow.started", {
            "instance_id": instance.id,
            "workflow_id": workflow.id,
            "workflow_name": workflow.name
        })
        
        # 开始执行
        task = asyncio.create_task(self._execute_workflow(instance, workflow))
        self._running_tasks[instance.id] = task
        
        # 添加完成回调
        task.add_done_callback(lambda t: self._on_workflow_complete(instance.id, t))
        
        instance.status = WorkflowStatus.RUNNING
        logger.info(f"工作流实例已启动: {instance.id}")
        
        return instance
    
    async def _execute_workflow(self, instance: WorkflowInstance, workflow: Workflow):
        """执行工作流"""
        try:
            resolver = DependencyResolver(workflow)
            registry = get_executor_registry()
            
            completed_steps: Set[str] = set()
            running_steps: Dict[str, asyncio.Task] = {}
            failed_steps: Set[str] = set()
            
            while True:
                # 检查是否被取消
                if instance.status == WorkflowStatus.CANCELLED:
                    logger.info(f"工作流已取消: {instance.id}")
                    break
                
                # 获取可执行的步骤
                ready = resolver.graph.get_ready_steps(completed_steps)
                ready = [s for s in ready if s not in completed_steps and s not in running_steps]
                
                # 过滤掉已失败步骤的依赖
                ready = [s for s in ready if not resolver.graph.get_dependencies(s) & failed_steps]
                
                if not ready and not running_steps:
                    # 没有可执行步骤且没有运行中的步骤
                    if len(completed_steps) == len(workflow.steps):
                        # 所有步骤完成
                        instance.status = WorkflowStatus.COMPLETED
                        instance.completed_at = datetime.now()
                        logger.info(f"工作流完成: {instance.id}")
                    else:
                        # 有步骤失败导致无法继续
                        instance.status = WorkflowStatus.FAILED
                        instance.completed_at = datetime.now()
                        if not instance.error_info:
                            instance.error_info = ErrorInfo(
                                step_id="",
                                error_type="WorkflowError",
                                error_message="部分步骤失败导致工作流无法完成"
                            )
                        logger.warning(f"工作流失败: {instance.id}")
                    break
                
                # 启动就绪的步骤
                for step_id in ready:
                    step = workflow.get_step(step_id)
                    if not step:
                        continue
                    
                    # 检查条件
                    if step.condition and not self._evaluate_condition(step.condition, instance.context):
                        logger.debug(f"步骤 {step_id} 条件不满足，跳过")
                        completed_steps.add(step_id)
                        state = instance.get_step_state(step_id)
                        state.status = StepStatus.SKIPPED
                        continue
                    
                    # 启动步骤执行
                    task = asyncio.create_task(
                        self._execute_step(instance, step, registry)
                    )
                    running_steps[step_id] = task
                    
                    # 添加完成回调
                    task.add_done_callback(
                        lambda t, sid=step_id: self._on_step_complete(
                            instance.id, sid, t, completed_steps, failed_steps, running_steps
                        )
                    )
                
                # 等待任意步骤完成
                if running_steps:
                    done, _ = await asyncio.wait(
                        running_steps.values(),
                        return_when=asyncio.FIRST_COMPLETED
                    )
                else:
                    # 没有运行中的步骤，检查是否还有可执行的
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.exception(f"工作流执行异常: {instance.id}")
            instance.status = WorkflowStatus.FAILED
            instance.completed_at = datetime.now()
            instance.error_info = ErrorInfo(
                step_id="",
                error_type=type(e).__name__,
                error_message=str(e)
            )
    
    async def _execute_step(
        self,
        instance: WorkflowInstance,
        step: Step,
        registry
    ):
        """执行单个步骤"""
        state = instance.get_step_state(step.id)
        state.status = StepStatus.RUNNING
        state.started_at = datetime.now()
        
        logger.info(f"执行步骤: {step.id} ({step.name})")
        
        # 触发事件
        await self._emit_event("step.started", {
            "instance_id": instance.id,
            "step_id": step.id,
            "step_name": step.name
        })
        
        # 构建步骤上下文
        step_context = {
            **instance.context,
            "step_id": step.id,
            "step_name": step.name,
            "workflow_id": instance.workflow_id,
            "instance_id": instance.id
        }
        
        # 添加依赖步骤的输出
        for dep_id in step.dependencies:
            dep_state = instance.step_states.get(dep_id)
            if dep_state and dep_state.output is not None:
                step_context[f"{dep_id}_output"] = dep_state.output
        
        # 执行步骤
        result = await registry.execute(step, step_context)
        
        # 更新状态
        state.completed_at = datetime.now()
        if result.success:
            state.status = StepStatus.COMPLETED
            state.output = result.output
            state.execution_time_ms = result.execution_time_ms
            
            # 将输出添加到全局上下文
            if result.output is not None:
                instance.context[f"{step.id}_output"] = result.output
            
            logger.info(f"步骤完成: {step.id} ({result.execution_time_ms}ms)")
            
            await self._emit_event("step.completed", {
                "instance_id": instance.id,
                "step_id": step.id,
                "execution_time_ms": result.execution_time_ms
            })
        else:
            state.status = StepStatus.FAILED
            state.error = result.error
            state.execution_time_ms = result.execution_time_ms
            
            logger.warning(f"步骤失败: {step.id} - {result.error.error_message}")
            
            await self._emit_event("step.failed", {
                "instance_id": instance.id,
                "step_id": step.id,
                "error": result.error.error_message if result.error else "Unknown"
            })
        
        return result
    
    def _on_step_complete(
        self,
        instance_id: str,
        step_id: str,
        task: asyncio.Task,
        completed_steps: Set[str],
        failed_steps: Set[str],
        running_steps: Dict[str, asyncio.Task]
    ):
        """步骤完成回调"""
        del running_steps[step_id]
        
        try:
            result = task.result()
            if result.success:
                completed_steps.add(step_id)
            else:
                failed_steps.add(step_id)
        except Exception as e:
            logger.exception(f"步骤任务异常: {step_id}")
            failed_steps.add(step_id)
    
    def _on_workflow_complete(self, instance_id: str, task: asyncio.Task):
        """工作流完成回调"""
        if instance_id in self._running_tasks:
            del self._running_tasks[instance_id]
        
        try:
            task.result()
        except Exception as e:
            logger.exception(f"工作流任务异常: {instance_id}")
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估条件表达式"""
        try:
            # 简单的条件评估
            # 支持: "key" (检查key存在且为真), "key == value", "key != value"
            if "==" in condition:
                key, value = condition.split("==", 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                return str(context.get(key)) == value
            elif "!=" in condition:
                key, value = condition.split("!=", 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                return str(context.get(key)) != value
            else:
                key = condition.strip()
                value = context.get(key)
                return bool(value) if value is not None else False
        except Exception as e:
            logger.warning(f"条件评估失败: {condition} - {e}")
            return False
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                logger.exception(f"事件处理器异常: {e}")
    
    def on_event(self, handler: Callable[[str, Dict], None]):
        """注册事件处理器"""
        self._event_handlers.append(handler)
    
    async def wait(self, instance_id: str, timeout: Optional[float] = None) -> WorkflowInstance:
        """
        等待工作流完成
        
        Args:
            instance_id: 实例ID
            timeout: 超时时间（秒）
            
        Returns:
            工作流实例
        """
        task = self._running_tasks.get(instance_id)
        if task:
            try:
                await asyncio.wait_for(task, timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"等待工作流超时: {instance_id}")
        
        return self._instances.get(instance_id)
    
    async def cancel(self, instance_id: str) -> bool:
        """
        取消工作流
        
        Args:
            instance_id: 实例ID
            
        Returns:
            是否成功取消
        """
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        
        if instance.is_completed():
            return False
        
        instance.status = WorkflowStatus.CANCELLED
        
        # 取消运行中的任务
        task = self._running_tasks.get(instance_id)
        if task and not task.done():
            task.cancel()
        
        # 取消步骤任务
        for step_id, step_task in list(self._running_tasks.items()):
            if step_id.startswith(f"{instance_id}:"):
                if not step_task.done():
                    step_task.cancel()
        
        logger.info(f"工作流已取消: {instance_id}")
        
        await self._emit_event("workflow.cancelled", {
            "instance_id": instance_id
        })
        
        return True
    
    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """获取工作流实例"""
        return self._instances.get(instance_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self._instances)
        completed = sum(1 for i in self._instances.values() if i.status == WorkflowStatus.COMPLETED)
        failed = sum(1 for i in self._instances.values() if i.status == WorkflowStatus.FAILED)
        running = sum(1 for i in self._instances.values() if i.status == WorkflowStatus.RUNNING)
        
        return {
            "total_instances": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "registered_workflows": len(self._workflows),
            "active_tasks": len(self._running_tasks)
        }
