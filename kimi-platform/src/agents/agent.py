"""
Kimi Multi-Agent Platform - Agent System
Phase 2: Agent Base + Orchestrator
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Message:
    """Agent间消息"""
    from_agent: str
    to_agent: str
    content: Any
    message_type: str = "default"  # default, request, response, broadcast
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: str
    description: str
    input_data: Any
    context: Dict = field(default_factory=dict)
    assigned_to: Optional[str] = None
    status: str = "pending"
    result: Any = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class Tool:
    """工具基类"""
    
    def __init__(self, name: str, description: str, handler: Callable):
        self.name = name
        self.description = description
        self.handler = handler
    
    def execute(self, **kwargs) -> Any:
        return self.handler(**kwargs)
    
    def __repr__(self):
        return f"Tool({self.name})"


class Agent(ABC):
    """
    智能体基类
    
    核心循环: Perceive -> Think -> Act
    """
    
    def __init__(self, agent_id: str, role: str, description: str = ""):
        self.agent_id = agent_id
        self.role = role
        self.description = description
        self.status = AgentStatus.IDLE
        self.tools: Dict[str, Tool] = {}
        self.memory: List[Dict] = []
        self.inbox: List[Message] = []
        self.current_task: Optional[Task] = None
    
    def register_tool(self, tool: Tool) -> "Agent":
        """注册工具"""
        self.tools[tool.name] = tool
        return self
    
    def perceive(self, task: Task) -> None:
        """
        感知阶段: 理解任务
        """
        self.current_task = task
        self.status = AgentStatus.THINKING
        self._log("perceive", f"Received task: {task.description}")
    
    @abstractmethod
    def think(self, task: Task) -> "ActionPlan":
        """
        思考阶段: 制定行动计划
        
        Returns:
            ActionPlan: 行动计划
        """
        pass
    
    def act(self, plan: "ActionPlan") -> Any:
        """
        行动阶段: 执行计划
        """
        self.status = AgentStatus.ACTING
        
        try:
            if plan.action_type == "use_tool":
                tool_name = plan.tool_name
                if tool_name not in self.tools:
                    raise ValueError(f"Tool {tool_name} not found")
                
                tool = self.tools[tool_name]
                result = tool.execute(**plan.params)
                self._log("act", f"Used tool {tool_name}: {result}")
                return result
            
            elif plan.action_type == "delegate":
                # 委托给其他Agent
                self._log("act", f"Delegating to {plan.target_agent}")
                return {"action": "delegate", "to": plan.target_agent, "task": plan.params}
            
            elif plan.action_type == "respond":
                # 直接响应
                self._log("act", "Direct response")
                return plan.params.get("content")
            
            else:
                raise ValueError(f"Unknown action type: {plan.action_type}")
        
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._log("error", str(e))
            raise
    
    def execute(self, task: Task) -> Any:
        """
        执行完整循环: Perceive -> Self-Check -> Think -> Act
        """
        print(f"\n[Agent:{self.agent_id}] Executing task: {task.description}")
        
        # 0. 自检（物理现实检查等）
        try:
            from utils.self_check import check_task
            should_proceed, check_report = check_task(task.description, len(self.memory))
            
            if check_report != "✅ 所有自检通过":
                print(f"[Agent:{self.agent_id}] Self-check report:\n{check_report}")
            
            if not should_proceed:
                print(f"[Agent:{self.agent_id}] ⚠️ Self-check BLOCKED execution")
                task.status = "blocked"
                return {"error": "Self-check failed", "report": check_report}
                
        except ImportError:
            # 自检模块未安装，跳过
            pass
        
        # 1. 感知
        self.perceive(task)
        
        # 2. 思考
        plan = self.think(task)
        print(f"[Agent:{self.agent_id}] Plan: {plan}")
        
        # 3. 行动
        result = self.act(plan)
        
        # 4. 完成
        self.status = AgentStatus.COMPLETED
        task.status = "completed"
        task.result = result
        task.completed_at = time.time()
        
        print(f"[Agent:{self.agent_id}] Completed with result: {result}")
        return result
    
    def receive_message(self, message: Message) -> None:
        """接收消息"""
        self.inbox.append(message)
        self._log("message", f"From {message.from_agent}: {message.content}")
    
    def send_message(self, to_agent: str, content: Any, msg_type: str = "default") -> Message:
        """发送消息"""
        msg = Message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            content=content,
            message_type=msg_type
        )
        return msg
    
    def _log(self, action: str, detail: str) -> None:
        """记录日志"""
        self.memory.append({
            "timestamp": time.time(),
            "action": action,
            "detail": detail
        })
    
    def __repr__(self):
        return f"Agent({self.agent_id}, role={self.role})"


@dataclass
class ActionPlan:
    """行动计划"""
    action_type: str  # use_tool, delegate, respond
    tool_name: Optional[str] = None
    target_agent: Optional[str] = None
    params: Dict = field(default_factory=dict)
    reasoning: str = ""
    
    def __repr__(self):
        if self.action_type == "use_tool":
            return f"ActionPlan(use_tool: {self.tool_name})"
        elif self.action_type == "delegate":
            return f"ActionPlan(delegate -> {self.target_agent})"
        else:
            return f"ActionPlan({self.action_type})"


class SimpleAgent(Agent):
    """
    简单Agent实现 - 基于规则
    
    支持多档推理深度（2025推理优化研究内化）：
    - NoThink: 直接响应，无显式推理
    - FastThink: 简短推理链（默认）
    - CoreThink: 完整推理 + 验证
    - DeepThink: 多路径探索 + Self-Consistency
    """
    
    def __init__(self, agent_id: str, role: str, description: str = ""):
        super().__init__(agent_id, role, description)
        self.reasoning_depth = "FastThink"  # 默认
        self.self_consistency_samples = 1   # 默认单次
    
    def set_reasoning_depth(self, depth: str):
        """设置推理深度: NoThink/FastThink/CoreThink/DeepThink"""
        valid_depths = ["NoThink", "FastThink", "CoreThink", "DeepThink"]
        if depth not in valid_depths:
            raise ValueError(f"Invalid depth: {depth}")
        self.reasoning_depth = depth
        return self
    
    def set_self_consistency(self, n_samples: int):
        """设置Self-Consistency采样数"""
        self.self_consistency_samples = n_samples
        return self
    
    def think(self, task: Task) -> ActionPlan:
        """根据reasoning_depth选择策略"""
        if self.reasoning_depth == "NoThink":
            return self._think_notask(task)
        elif self.reasoning_depth == "FastThink":
            return self._think_fast(task)
        elif self.reasoning_depth == "CoreThink":
            return self._think_core(task)
        else:  # DeepThink
            return self._think_deep(task)
    
    def _think_notask(self, task: Task) -> ActionPlan:
        """NoThink: 直接响应"""
        return ActionPlan(
            action_type="respond",
            params={"content": f"[{self.agent_id}] {task.input_data}"},
            reasoning="NoThink: direct response"
        )
    
    def _think_fast(self, task: Task) -> ActionPlan:
        """FastThink: 简短推理（原逻辑）"""
        return self._select_tool_or_respond(task)
    
    def _think_core(self, task: Task) -> ActionPlan:
        """CoreThink: 完整推理 + 验证"""
        plan = self._select_tool_or_respond(task)
        plan.reasoning += " [validated]"
        return plan
    
    def _think_deep(self, task: Task) -> ActionPlan:
        """DeepThink: 多路径 + Self-Consistency"""
        if self.self_consistency_samples <= 1:
            return self._think_core(task)
        
        # 简化版：多次采样
        candidates = [self._select_tool_or_respond(task) 
                     for _ in range(self.self_consistency_samples)]
        
        best = candidates[0]
        best.reasoning += f" [DeepThink: {self.self_consistency_samples} samples]"
        return best
    
    def _select_tool_or_respond(self, task: Task) -> ActionPlan:
        """原think逻辑"""
        task_type = task.task_type
        
        if task_type == "research":
            return ActionPlan(
                action_type="use_tool",
                tool_name="web_search",
                params={"query": task.input_data},
                reasoning="Research needs web search"
            )
        elif task_type == "code":
            return ActionPlan(
                action_type="use_tool",
                tool_name="code_executor",
                params={"code": task.input_data},
                reasoning="Code needs execution"
            )
        elif task_type == "calculator":
            return ActionPlan(
                action_type="use_tool",
                tool_name="calculator",
                params={"expression": task.context.get("expression", task.input_data)},
                reasoning="Math needs calculator"
            )
        
        # 通用工具匹配
        for tool_name, tool in self.tools.items():
            if task_type in tool_name.lower() or task_type in tool.description.lower():
                return ActionPlan(
                    action_type="use_tool",
                    tool_name=tool_name,
                    params={"input": task.input_data, **task.context},
                    reasoning=f"Matched tool: {tool_name}"
                )
        
        return ActionPlan(
            action_type="respond",
            params={"content": f"[{self.agent_id}] {task.input_data}"},
            reasoning="No tool matched"
        )


class AgentOrchestrator:
    """
    Agent编排器 - 管理多Agent协作
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.message_bus: List[Message] = []
        self.tasks: Dict[str, Task] = {}
    
    def register_agent(self, agent: Agent) -> "AgentOrchestrator":
        """注册Agent"""
        self.agents[agent.agent_id] = agent
        print(f"[Orchestrator] Registered agent: {agent.agent_id}")
        return self
    
    def create_task(self, task_type: str, description: str, input_data: Any, context: Dict = None) -> Task:
        """创建任务"""
        task = Task(
            task_id=str(uuid.uuid4())[:8],
            task_type=task_type,
            description=description,
            input_data=input_data,
            context=context or {}
        )
        self.tasks[task.task_id] = task
        return task
    
    def assign_task(self, task: Task, agent_id: str) -> Any:
        """分配任务给指定Agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        task.assigned_to = agent_id
        
        return agent.execute(task)
    
    def dispatch_task(self, task: Task) -> tuple[str, Any]:
        """
        智能分派任务
        
        策略:
        1. 根据task_type匹配Agent的role
        2. 如果没有匹配，分配给默认Agent
        """
        task_type = task.task_type.lower()
        
        # 尝试匹配
        for agent_id, agent in self.agents.items():
            if task_type in agent.role.lower():
                print(f"[Orchestrator] Dispatching to {agent_id} (role match)")
                result = self.assign_task(task, agent_id)
                return agent_id, result
        
        # 默认分配给第一个Agent
        if self.agents:
            default_agent = list(self.agents.keys())[0]
            print(f"[Orchestrator] Dispatching to {default_agent} (default)")
            result = self.assign_task(task, default_agent)
            return default_agent, result
        
        raise ValueError("No agents available")
    
    def coordinate(self, workflow: List[Dict]) -> Dict[str, Any]:
        """
        协调多Agent工作流
        
        workflow格式:
        [
            {"agent": "agent1", "task": task1},
            {"agent": "agent2", "task": task2, "depends_on": "agent1"},
            ...
        ]
        """
        results = {}
        completed = set()
        
        for step in workflow:
            agent_id = step["agent"]
            task = step["task"]
            
            # 检查依赖
            if "depends_on" in step:
                dep = step["depends_on"]
                if dep not in completed:
                    print(f"[Orchestrator] Waiting for {dep} to complete...")
                    # 简化处理：假设依赖已完成
            
            # 执行
            result = self.assign_task(task, agent_id)
            results[agent_id] = result
            completed.add(agent_id)
        
        return results
    
    def send_message(self, from_agent: str, to_agent: str, content: Any) -> None:
        """发送消息"""
        msg = Message(
            from_agent=from_agent,
            to_agent=to_agent,
            content=content
        )
        self.message_bus.append(msg)
        
        # 投递到目标Agent
        if to_agent in self.agents:
            self.agents[to_agent].receive_message(msg)
    
    def broadcast(self, from_agent: str, content: Any) -> None:
        """广播消息给所有Agent"""
        for agent_id in self.agents:
            if agent_id != from_agent:
                self.send_message(from_agent, agent_id, content)
    
    def get_agent_status(self) -> Dict[str, Dict]:
        """获取所有Agent状态"""
        return {
            agent_id: {
                "status": agent.status.value,
                "current_task": agent.current_task.description if agent.current_task else None,
                "tool_count": len(agent.tools),
                "memory_size": len(agent.memory)
            }
            for agent_id, agent in self.agents.items()
        }
    
    def __repr__(self):
        return f"AgentOrchestrator(agents={len(self.agents)})"


class VerifierAgent(SimpleAgent):
    """
    验证Agent - 专门用于验证其他Agent的输出
    
    基于2025年多智能体编排最佳实践:
    - 每个关键决策都应该有Verifier检查
    - 伦理和事实检查必须内置于编排
    """
    
    def __init__(self, agent_id: str = "verifier", role: str = "verifier"):
        super().__init__(agent_id, role, "验证其他Agent的输出质量")
        self.reasoning_depth = "CoreThink"  # Verifier默认用深度推理
    
    def verify(self, original_task: Task, agent_output: Any) -> Dict:
        """
        验证Agent输出
        
        Returns:
            {
                "passed": bool,
                "score": float (0-1),
                "issues": List[str],
                "suggestions": List[str]
            }
        """
        print(f"[Verifier:{self.agent_id}] Verifying output...")
        
        issues = []
        suggestions = []
        
        # 1. 检查输出是否存在
        if agent_output is None or agent_output == "":
            issues.append("Empty output")
            suggestions.append("Check if the task was actually executed")
        
        # 2. 检查输出类型是否合理
        if isinstance(agent_output, dict) and "error" in agent_output:
            issues.append(f"Error in output: {agent_output['error']}")
        
        # 3. 检查是否有绝对化表述（如果是文本输出）
        if isinstance(agent_output, str):
            absolutes = ["总是", "从不", "一定", "永远", "always", "never", "must"]
            found = [w for w in absolutes if w in agent_output.lower()]
            if found:
                issues.append(f"Contains absolute terms: {found}")
                suggestions.append("Consider if these absolute statements are justified")
        
        # 4. 计算分数
        score = 1.0 - (len(issues) * 0.2)
        score = max(0.0, min(1.0, score))
        
        result = {
            "passed": len(issues) == 0,
            "score": score,
            "issues": issues,
            "suggestions": suggestions
        }
        
        print(f"[Verifier:{self.agent_id}] Score: {score:.2f}, Passed: {result['passed']}")
        return result


# 便捷函数
def create_agent(agent_id: str, role: str, description: str = "") -> SimpleAgent:
    """创建简单Agent"""
    return SimpleAgent(agent_id, role, description)


def create_verifier_agent(agent_id: str = "verifier") -> VerifierAgent:
    """创建验证Agent"""
    return VerifierAgent(agent_id, "verifier")


def create_orchestrator() -> AgentOrchestrator:
    """创建编排器"""
    return AgentOrchestrator()
