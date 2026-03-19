"""
wdai v3.0 - Integration Layer
系统集成层 - 连接所有Phase

实现: Message Bus + Workflow Engine + Agent System 集成
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime

from core.message_bus import (
    MessageBus, get_message_bus, Message, MessageType, create_message
)
from core.workflow import (
    WorkflowEngine, Workflow, Step, StepState, StepStatus,
    LLMExecutor, ShellExecutor, PythonExecutor,
    BaseExecutor, StepExecutionResult
)
from core.workflow.models import StepAction
from core.agent_system import (
    OrchestratorAgent, BaseAgent, AgentRole, get_agent_registry,
    initialize_agent_system, create_task, Task, SubTask
)

logger = logging.getLogger(__name__)


class AgentMessageAdapter:
    """
    Agent消息适配器
    
    将Agent系统接入Message Bus
    """
    
    def __init__(self, message_bus: MessageBus = None):
        self.message_bus = message_bus or get_message_bus()
        self._agent_handlers: Dict[str, Callable] = {}
    
    async def connect_agent(self, agent: BaseAgent, agent_id: str = None):
        """
        将Agent连接到消息总线
        
        Args:
            agent: Agent实例
            agent_id: Agent ID（可选，默认使用agent.name）
        """
        agent_id = agent_id or agent.name.lower()
        
        # 创建消息处理器
        async def message_handler(message: Message):
            await self._handle_agent_message(agent, message)
        
        # 订阅消息
        self.message_bus.subscribe(
            agent_id=agent_id,
            message_types=[MessageType.TASK, MessageType.EVENT, MessageType.NOTIFICATION],
            filter_fn=lambda m: agent_id in m.recipients or agent.role.value in m.recipients
        )
        
        # 注册处理器
        self.message_bus.register_handler(agent_id, message_handler)
        self._agent_handlers[agent_id] = message_handler
        
        logger.info(f"Agent {agent_id} 已连接到消息总线")
    
    async def disconnect_agent(self, agent_id: str):
        """断开Agent连接"""
        self.message_bus.unregister_handler(agent_id)
        self.message_bus.unsubscribe(agent_id)
        if agent_id in self._agent_handlers:
            del self._agent_handlers[agent_id]
        logger.info(f"Agent {agent_id} 已断开连接")
    
    async def _handle_agent_message(self, agent: BaseAgent, message: Message):
        """处理发送给Agent的消息"""
        logger.debug(f"Agent {agent.name} 收到消息: {message.id}")
        
        # 从消息中提取任务信息
        content = message.content
        task_type = content.get("task_type", "custom")
        
        # 检查Agent是否能处理
        if not agent.can_handle(task_type):
            logger.warning(f"Agent {agent.name} 无法处理任务类型: {task_type}")
            
            # 发送无法处理的消息
            await self._send_response(
                original_msg=message,
                success=False,
                error=f"Agent {agent.name} 无法处理 {task_type}"
            )
            return
        
        # 对于Orchestrator，直接执行Task
        if isinstance(agent, OrchestratorAgent):
            task = Task(
                id=content.get("task_id", f"task_{datetime.now().timestamp()}"),
                description=content.get("description", ""),
                goal=content.get("goal", ""),
                constraints=content.get("constraints", []),
                priority=content.get("priority", 0)
            )
            
            result = await agent.execute(task)
            
            # 发送结果
            await self._send_response(
                original_msg=message,
                success=result.success,
                output=result.output,
                error=result.error_message
            )
        else:
            # Subagent需要SubTask和NarrowContext
            # 这里简化处理，实际需要从消息中解析
            logger.info(f"Subagent {agent.name} 收到任务请求")
    
    async def _send_response(
        self,
        original_msg: Message,
        success: bool,
        output: Any = None,
        error: str = None
    ):
        """发送响应消息"""
        response = create_message(
            msg_type=MessageType.RESPONSE,
            content={
                "success": success,
                "output": output,
                "error": error,
                "original_message_id": original_msg.id
            },
            sender=original_msg.recipients[0] if original_msg.recipients else "agent",
            recipients=[original_msg.sender],
            task_id=original_msg.task_id,
            parent_id=original_msg.id
        )
        
        await self.message_bus.publish(response)


class AgentStepExecutor(BaseExecutor):
    """
    Agent步骤执行器
    
    用于Workflow Engine调用Agent执行步骤
    """
    
    def __init__(
        self,
        orchestrator: OrchestratorAgent = None,
        message_bus: MessageBus = None
    ):
        super().__init__(StepAction.CUSTOM)
        self.orchestrator = orchestrator
        self.message_bus = message_bus or get_message_bus()
    
    async def execute(self, step: Step, context: Dict[str, Any]) -> StepExecutionResult:
        """
        执行Agent步骤
        
        将Workflow步骤转换为Task，通过Orchestrator执行
        """
        from core.workflow.executor import StepExecutionResult
        
        # 从步骤中提取任务信息
        task_description = step.config.get("description") or step.name
        task_goal = step.config.get("goal", task_description)
        task_constraints = step.config.get("constraints", [])
        
        # 创建Task
        task = create_task(
            description=task_description,
            goal=task_goal,
            constraints=task_constraints
        )
        
        logger.info(f"Workflow步骤 {step.id} 触发Agent任务: {task.description}")
        
        # 使用Orchestrator执行
        if self.orchestrator:
            result = await self.orchestrator.execute(task)
        else:
            # 通过消息总线发送请求
            result = await self._execute_via_message_bus(task)
        
        if result.success:
            return StepExecutionResult(
                success=True,
                output=result.output,
                metadata={
                    "task_id": task.id,
                    "execution_time_ms": result.execution_time_ms
                }
            )
        else:
            return StepExecutionResult(
                success=False,
                error=result.error_message or "Agent执行失败"
            )
    
    async def _execute_via_message_bus(self, task: Task):
        """通过消息总线执行（异步方式）"""
        from core.agent_system.models import AgentResult
        
        # 创建请求消息
        message = create_message(
            msg_type=MessageType.TASK,
            content={
                "task_id": task.id,
                "description": task.description,
                "goal": task.goal,
                "constraints": task.constraints,
                "priority": task.priority
            },
            sender="workflow_engine",
            recipients=["orchestrator"],
            task_id=task.id
        )
        
        # 发布消息
        await self.message_bus.publish(message)
        
        # 等待响应（简化实现）
        # 实际应该使用future或回调机制
        logger.info(f"任务 {task.id} 已通过消息总线发送")
        
        # 返回一个pending结果
        return AgentResult(
            success=True,
            output={"status": "pending", "message_id": message.id}
        )


class IntegratedSystem:
    """
    集成系统
    
    统一管理Message Bus、Workflow Engine和Agent System
    """
    
    def __init__(self):
        self.message_bus: Optional[MessageBus] = None
        self.workflow_engine: Optional[WorkflowEngine] = None
        self.orchestrator: Optional[OrchestratorAgent] = None
        self.agent_adapter: Optional[AgentMessageAdapter] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化所有组件"""
        if self._initialized:
            return
        
        logger.info("初始化集成系统...")
        
        # 1. 初始化消息总线
        self.message_bus = get_message_bus()
        await self.message_bus.start()
        logger.info("✓ Message Bus 已启动")
        
        # 2. 初始化Agent系统
        self.orchestrator = initialize_agent_system()
        logger.info("✓ Agent System 已初始化")
        
        # 3. 初始化Agent消息适配器
        self.agent_adapter = AgentMessageAdapter(self.message_bus)
        
        # 4. 将Orchestrator连接到消息总线
        await self.agent_adapter.connect_agent(self.orchestrator, "orchestrator")
        logger.info("✓ Orchestrator 已连接到Message Bus")
        
        # 5. 初始化工作流引擎
        self.workflow_engine = WorkflowEngine()
        
        # 6. 注册Agent步骤执行器
        from core.workflow.executor import get_executor_registry
        executor_registry = get_executor_registry()
        executor_registry.register(AgentStepExecutor(
            orchestrator=self.orchestrator,
            message_bus=self.message_bus
        ))
        logger.info("✓ Agent Step Executor 已注册")
        
        self._initialized = True
        logger.info("集成系统初始化完成")
    
    async def shutdown(self):
        """关闭所有组件"""
        logger.info("关闭集成系统...")
        
        if self.agent_adapter:
            await self.agent_adapter.disconnect_agent("orchestrator")
        
        if self.message_bus:
            await self.message_bus.stop()
        
        logger.info("集成系统已关闭")
    
    async def execute_task(self, description: str, goal: str = None, constraints: List[str] = None) -> Dict[str, Any]:
        """
        执行独立任务
        
        通过Orchestrator直接执行
        """
        if not self._initialized:
            await self.initialize()
        
        task = create_task(
            description=description,
            goal=goal or description,
            constraints=constraints or []
        )
        
        result = await self.orchestrator.execute(task)
        
        return {
            "task_id": task.id,
            "success": result.success,
            "output": result.output,
            "error": result.error_message,
            "execution_time_ms": result.execution_time_ms
        }
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        通过Workflow Engine执行
        """
        if not self._initialized:
            await self.initialize()
        
        # 注册并启动工作流
        self.workflow_engine.register_workflow(workflow)
        instance = await self.workflow_engine.start(
            workflow=workflow,
            context=context or {}
        )
        
        # 等待完成
        while instance.status not in ["completed", "failed", "cancelled"]:
            await asyncio.sleep(0.1)
            instance = self.workflow_engine.get_instance(instance.id)
        
        return {
            "instance_id": instance.id,
            "workflow_id": workflow.id,
            "status": instance.status,
            "results": instance.results,
            "execution_time": instance.end_time.isoformat() if instance.end_time else None
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {
            "initialized": self._initialized
        }
        
        if self.message_bus:
            stats["message_bus"] = self.message_bus.get_statistics()
        
        if self.orchestrator:
            stats["agent_system"] = {
                "agents": get_agent_registry().get_all_statistics()
            }
        
        return stats


# 全局实例
_system: Optional[IntegratedSystem] = None


async def get_integrated_system() -> IntegratedSystem:
    """获取集成系统实例（单例）"""
    global _system
    if _system is None:
        _system = IntegratedSystem()
        await _system.initialize()
    return _system


async def execute_task(description: str, goal: str = None, constraints: List[str] = None) -> Dict[str, Any]:
    """
    便捷函数：执行任务
    
    Args:
        description: 任务描述
        goal: 任务目标
        constraints: 约束条件
        
    Returns:
        执行结果
    """
    system = await get_integrated_system()
    return await system.execute_task(description, goal, constraints)


__all__ = [
    "IntegratedSystem",
    "AgentMessageAdapter",
    "AgentStepExecutor",
    "get_integrated_system",
    "execute_task"
]
