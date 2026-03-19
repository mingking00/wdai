"""
wdai v3.0 - Orchestrator Agent
Phase 3: Agent专业化系统 - 协调者Agent

唯一入口，负责任务分解、规划、调度、结果整合
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from .models import (
    AgentConfig, AgentRole, AgentResult,
    Task, SubTask, TodoItem, TodoPlan, TodoStatus,
    TaskStatus, TaskExecution, NarrowContext
)
from .base import BaseAgent, get_agent_registry, get_agent
from .context import SimpleContextManager, create_context_manager
from .context_enhanced import EnhancedContextManager, create_enhanced_context_manager
from .context_embedding import EmbeddingContextManager, create_embedding_context_manager
from .todo import TodoPlanner, create_planner

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    协调者Agent
    
    负责:
    1. 接收用户任务
    2. 分解为子任务
    3. 生成TODO计划
    4. 调度专业Agent执行
    5. 整合结果
    """
    
    def __init__(self, context_manager_type: str = "simple"):
        """
        初始化Orchestrator
        
        Args:
            context_manager_type: 上下文管理器类型
                - "simple": 简单版 (关键词匹配) - 默认 ⭐
                - "enhanced": 增强版 (TF-IDF)
                - "embedding": Embedding版 (向量语义)
        """
        config = AgentConfig(
            role=AgentRole.ORCHESTRATOR,
            name="Orchestrator",
            expertise=["task_decomposition", "planning", "coordination"],
            system_prompt="""你是Orchestrator，一个任务协调专家。

你的职责:
1. 理解用户任务的完整目标
2. 将复杂任务分解为可执行的子任务
3. 为每个子任务分配合适的专业Agent
4. 监控执行进度，处理依赖关系
5. 整合所有子任务的结果

原则:
- 只做协调，不直接执行具体工作
- 确保子任务之间的依赖正确
- 及时发现并报告问题

当前使用的上下文管理器: """ + context_manager_type + """
"""
        )
        super().__init__(config)
        
        # 根据类型选择上下文管理器
        if context_manager_type == "simple":
            self.context_manager = create_context_manager()
        elif context_manager_type == "embedding":
            self.context_manager = create_embedding_context_manager()
        else:  # enhanced (default)
            self.context_manager = create_enhanced_context_manager()
        
        self.context_manager_type = context_manager_type
        self.todo_planner = create_planner()
        self._executions: Dict[str, TaskExecution] = {}
        self._available_files: List[str] = []
        self._file_contents: Dict[str, str] = {}
    
    def can_handle(self, task_type: str) -> bool:
        """Orchestrator可以处理任何任务"""
        return True
    
    async def execute(self, task: Task) -> AgentResult:
        """
        执行任务（入口点）
        
        Args:
            task: 用户任务
            
        Returns:
            执行结果
        """
        logger.info(f"Orchestrator开始执行任务: {task.id}")
        
        try:
            # 1. 任务分解
            subtasks = await self._decompose_task(task)
            
            # 2. 创建TODO计划
            plan = self.todo_planner.create_plan(task, subtasks)
            
            # 3. 创建执行记录
            execution = TaskExecution(
                task=task,
                plan=plan,
                subtasks={s.id: s for s in subtasks}
            )
            execution.start()
            self._executions[task.id] = execution
            
            # 4. 执行计划
            await self._execute_plan(task, plan, execution)
            
            # 5. 整合结果
            result = self._aggregate_results(task, execution)
            execution.finish(result)
            
            logger.info(f"任务执行完成: {task.id}, 成功={result.success}")
            return result
            
        except Exception as e:
            logger.exception(f"任务执行异常: {task.id}")
            return AgentResult(
                success=False,
                error_message=f"Orchestrator执行失败: {str(e)}"
            )
    
    async def execute_subtask(self, subtask: SubTask, context: NarrowContext) -> AgentResult:
        """
        执行子任务（用于直接执行单个SubTask）
        
        Args:
            subtask: 子任务
            context: 窄上下文
            
        Returns:
            执行结果
        """
        # 找到合适的Agent
        registry = get_agent_registry()
        agent = registry.find_agent_for_task(subtask.type)
        
        if not agent:
            return AgentResult(
                success=False,
                error_message=f"未找到能处理任务类型 '{subtask.type}' 的Agent"
            )
        
        # 执行
        return await agent.run_with_retry(subtask, context)
    
    async def _decompose_task(self, task: Task) -> List[SubTask]:
        """
        任务分解
        
        将复杂任务分解为子任务
        """
        # 这里简化实现，实际可能需要LLM进行智能分解
        # 基于任务描述中的关键词进行简单分解
        
        subtasks = []
        description = task.description.lower()
        prev_subtask_id = None
        
        # 检查是否需要架构设计
        if any(kw in description for kw in ["设计", "架构", "design", "architect", "规划"]):
            st = SubTask(
                parent_id=task.id,
                type="design",
                description=f"设计{task.goal}的架构",
                dependencies=[]
            )
            subtasks.append(st)
            prev_subtask_id = st.id
        
        # 检查是否需要实现
        if any(kw in description for kw in ["实现", "开发", "写代码", "implement", "develop", "code"]):
            deps = [prev_subtask_id] if prev_subtask_id else []
            st = SubTask(
                parent_id=task.id,
                type="implement",
                description=f"实现{task.goal}的核心功能",
                dependencies=deps
            )
            subtasks.append(st)
            prev_subtask_id = st.id
        
        # 检查是否需要审查
        if any(kw in description for kw in ["审查", "review", "检查", "audit"]):
            deps = [prev_subtask_id] if prev_subtask_id else []
            st = SubTask(
                parent_id=task.id,
                type="review",
                description=f"审查{task.goal}的实现",
                dependencies=deps
            )
            subtasks.append(st)
            prev_subtask_id = st.id
        
        # 检查是否需要测试
        if any(kw in description for kw in ["测试", "test", "验证", "verify"]):
            deps = [prev_subtask_id] if prev_subtask_id else []
            st = SubTask(
                parent_id=task.id,
                type="test",
                description=f"测试{task.goal}",
                dependencies=deps
            )
            subtasks.append(st)
        
        # 如果没有匹配到任何类型，创建一个通用实现任务
        if not subtasks:
            subtasks.append(SubTask(
                parent_id=task.id,
                type="implement",
                description=task.description,
                dependencies=[]
            ))
        
        logger.info(f"任务 {task.id} 被分解为 {len(subtasks)} 个子任务")
        return subtasks
    
    async def _execute_plan(
        self,
        task: Task,
        plan: TodoPlan,
        execution: TaskExecution
    ):
        """执行计划"""
        completed_todos: Set[str] = set()
        
        while not plan.is_complete():
            # 获取下一个可执行的TODO
            todo = self._get_next_executable_todo(plan, completed_todos)
            
            if not todo:
                # 检查是否有运行中的任务
                if not any(t.status == TodoStatus.RUNNING for t in plan.todos):
                    # 没有可执行的，也没有运行中的，可能有问题
                    logger.warning(f"没有可执行的TODO，但计划未完成")
                    break
                
                # 等待一下再检查
                await asyncio.sleep(0.5)
                continue
            
            # 获取对应的SubTask
            subtask = execution.subtasks.get(todo.subtask_id)
            if not subtask:
                logger.error(f"找不到TODO对应的SubTask: {todo.subtask_id}")
                todo.mark_failed("找不到对应的SubTask")
                completed_todos.add(todo.id)
                continue
            
            # 执行
            await self._execute_todo(task, todo, subtask, execution)
            completed_todos.add(todo.id)
        
        logger.info(f"计划执行完成: {task.id}")
    
    def _get_next_executable_todo(
        self,
        plan: TodoPlan,
        completed_todos: Set[str]
    ) -> Optional[TodoItem]:
        """获取下一个可执行的TODO"""
        for todo in plan.todos:
            if todo.status != TodoStatus.PENDING:
                continue
            
            # 检查依赖
            if todo.dependencies:
                deps_completed = all(
                    dep_id in completed_todos 
                    for dep_id in todo.dependencies
                )
                if not deps_completed:
                    continue
            
            return todo
        
        return None
    
    async def _execute_todo(
        self,
        task: Task,
        todo: TodoItem,
        subtask: SubTask,
        execution: TaskExecution
    ):
        """执行单个TODO"""
        todo.mark_started()
        subtask.mark_started()
        
        logger.info(f"开始执行TODO: {todo.description}")
        
        # 裁剪上下文 (Fresh Eyes) - 根据管理器类型传递不同参数
        if self.context_manager_type == "embedding":
            narrow_context = self.context_manager.narrow_context(
                task=task,
                subtask=subtask,
                plan=execution.plan,
                available_files=self._available_files,
                file_contents=self._file_contents
            )
        else:
            narrow_context = self.context_manager.narrow_context(
                task=task,
                subtask=subtask,
                plan=execution.plan,
                available_files=self._available_files
            )
        
        # 找到Agent
        agent = None
        if todo.assigned_agent:
            agent = get_agent(todo.assigned_agent)
        
        if not agent:
            # 尝试根据任务类型查找
            registry = get_agent_registry()
            agent = registry.find_agent_for_task(subtask.type)
        
        if not agent:
            logger.error(f"未找到Agent执行TODO: {todo.description}")
            todo.mark_failed("未找到合适的Agent")
            subtask.mark_completed(AgentResult(
                success=False,
                error_message="未找到合适的Agent"
            ))
            return
        
        # 执行
        result = await agent.run_with_retry(subtask, narrow_context)
        
        # 更新状态
        if result.success:
            todo.mark_completed()
        else:
            todo.mark_failed(result.error_message or "执行失败")
        
        subtask.mark_completed(result)
        
        logger.info(f"TODO执行完成: {todo.description}, 成功={result.success}")
    
    def _aggregate_results(
        self,
        task: Task,
        execution: TaskExecution
    ) -> AgentResult:
        """
        整合所有子任务的结果
        """
        failed_subtasks = [
            s for s in execution.subtasks.values()
            if s.status == TaskStatus.FAILED
        ]
        
        if failed_subtasks:
            error_msgs = [
                f"- {s.description}: {s.result.error_message if s.result else '未知错误'}"
                for s in failed_subtasks
            ]
            
            return AgentResult(
                success=False,
                error_message=f"以下子任务失败:\n" + "\n".join(error_msgs),
                metadata={
                    "failed_count": len(failed_subtasks),
                    "total_count": len(execution.subtasks)
                }
            )
        
        # 收集所有成功结果
        outputs = {
            s.id: s.result.output if s.result else None
            for s in execution.subtasks.values()
        }
        
        return AgentResult(
            success=True,
            output={
                "task_id": task.id,
                "goal": task.goal,
                "subtask_results": outputs,
                "execution_time_seconds": execution.duration_seconds
            },
            metadata={
                "completed_count": len(execution.subtasks),
                "total_count": len(execution.subtasks)
            }
        )
    
    def get_execution(self, task_id: str) -> Optional[TaskExecution]:
        """获取执行记录"""
        return self._executions.get(task_id)
    
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """获取任务进度"""
        execution = self._executions.get(task_id)
        if not execution:
            return {"error": "未找到执行记录"}
        
        return execution.plan.get_progress()
    
    def generate_report(self, task_id: str) -> str:
        """生成执行报告"""
        execution = self._executions.get(task_id)
        if not execution:
            return "未找到执行记录"
        
        lines = [
            f"任务: {execution.task.description}",
            f"目标: {execution.task.goal}",
            f"执行时间: {execution.duration_seconds:.1f}秒",
            "",
            self.todo_planner.generate_report(task_id)
        ]
        
        return "\n".join(lines)
    
    def set_available_files(self, files: List[str]):
        """设置可用文件列表（用于上下文裁剪）"""
        self._available_files = files
    
    def set_file_contents(self, contents: Dict[str, str]):
        """
        设置文件内容（供Embedding版使用）
        
        Args:
            contents: {file_path: file_content}
        """
        self._file_contents = contents
    
    def get_context_manager_info(self) -> Dict[str, Any]:
        """获取当前上下文管理器信息"""
        return {
            "type": self.context_manager_type,
            "class": self.context_manager.__class__.__name__,
            "max_files": getattr(self.context_manager, 'max_files', None),
            "max_tokens": getattr(self.context_manager, 'max_total_tokens', None)
        }
