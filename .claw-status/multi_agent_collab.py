#!/usr/bin/env python3
"""
WDai Multi-Agent Collaboration Framework v1.0 (evo-002实现)
多智能体协作框架研究与借鉴

借鉴来源:
1. CrewAI: Role-Playing (角色/目标/背景故事) - 提升LLM稳定性
2. AutoGen: 对话式多智能体协作 - 代码生成和执行
3. LangGraph: 状态机工作流 - human-in-the-loop
4. OpenAI Swarm: 轻量级任务交接

核心设计:
- Agent角色定义 (Role/Goal/Backstory)
- 对话式协作流程
- 状态机驱动的任务编排
- 任务交接与路由
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum, auto
from datetime import datetime
from collections import deque
import json
import time
import hashlib


# ============================================================================
# Agent角色定义 (借鉴CrewAI)
# ============================================================================

@dataclass
class AgentRole:
    """
    Agent角色定义
    
    借鉴CrewAI的Role-Playing设计:
    - role: 角色名称
    - goal: 角色目标
    - backstory: 背景故事
    """
    name: str
    role: str
    goal: str
    backstory: str
    
    # 能力配置
    allow_delegation: bool = True  # 是否允许委托任务
    verbose: bool = False
    
    # 记忆
    memory: deque = field(default_factory=lambda: deque(maxlen=10))
    
    def to_system_prompt(self) -> str:
        """转换为系统提示词"""
        return f"""你是{self.name}，{self.role}。

你的目标: {self.goal}

背景: {self.backstory}

重要原则:
- 始终基于你的角色专业知识回答
- 如果问题超出你的专业范围，{'可以委托给其他Agent' if self.allow_delegation else '明确告知用户'}
- 保持专业、准确、有帮助
"""
    
    def remember(self, content: str):
        """记录记忆"""
        self.memory.append({
            'content': content,
            'timestamp': time.time()
        })
    
    def get_context(self) -> str:
        """获取上下文记忆"""
        if not self.memory:
            return ""
        
        recent = list(self.memory)[-5:]  # 最近5条
        return "\n".join([f"- {m['content']}" for m in recent])


# 预定义角色模板
AGENT_TEMPLATES = {
    'researcher': AgentRole(
        name="研究员",
        role="专业研究员",
        goal="深入调查和分析信息，提供全面的研究结果",
        backstory="你是一位经验丰富的研究员，擅长信息收集、数据分析和知识整合。你注重细节，追求准确性。"
    ),
    
    'developer': AgentRole(
        name="开发者",
        role="软件工程师",
        goal="编写高质量代码，解决技术问题",
        backstory="你是一位全栈开发者，精通Python和系统设计。你注重代码质量、性能和可维护性。"
    ),
    
    'reviewer': AgentRole(
        name="审查员",
        role="代码审查专家",
        goal="审查代码质量，发现潜在问题，提出改进建议",
        backstory="你是一位严格的代码审查员，擅长发现bug、安全漏洞和性能问题。你追求代码卓越。"
    ),
    
    'planner': AgentRole(
        name="规划师",
        role="项目规划专家",
        goal="制定清晰的项目计划和执行策略",
        backstory="你是一位经验丰富的项目经理，擅长任务分解、资源分配和风险管理。"
    ),
    
    'writer': AgentRole(
        name="写作者",
        role="技术文档撰写专家",
        goal="撰写清晰、准确、易读的技术文档",
        backstory="你是一位技术写作专家，擅长将复杂概念转化为易懂的文字。"
    ),
}


# ============================================================================
# 任务定义 (借鉴CrewAI Task)
# ============================================================================

class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    DELEGATED = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class Task:
    """任务定义"""
    id: str
    description: str
    assigned_to: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    context: str = ""
    expected_output: str = ""
    
    # 执行记录
    execution_log: List[Dict] = field(default_factory=list)
    result: Any = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    
    def log(self, event: str, data: Dict = None):
        """记录执行日志"""
        self.execution_log.append({
            'event': event,
            'data': data or {},
            'timestamp': time.time()
        })


# ============================================================================
# 对话管理 (借鉴AutoGen)
# ============================================================================

@dataclass
class Message:
    """对话消息"""
    sender: str
    recipient: str
    content: str
    message_type: str = "chat"  # chat, task_request, task_result, delegation
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)


class Conversation:
    """
    对话管理
    
    借鉴AutoGen的对话式多智能体协作
    """
    
    def __init__(self, conversation_id: str):
        self.id = conversation_id
        self.messages: List[Message] = []
        self.participants: set = set()
        self.task_bindings: Dict[str, str] = {}  # task_id -> conversation_id
        
    def add_message(self, message: Message):
        """添加消息"""
        self.messages.append(message)
        self.participants.add(message.sender)
        self.participants.add(message.recipient)
    
    def get_history(self, limit: int = 10) -> List[Message]:
        """获取对话历史"""
        return self.messages[-limit:]
    
    def get_context_for_agent(self, agent_name: str) -> str:
        """获取Agent的上下文"""
        relevant = []
        for msg in self.messages[-20:]:  # 最近20条
            if msg.recipient == agent_name or msg.sender == agent_name:
                relevant.append(f"{msg.sender}: {msg.content}")
        
        return "\n".join(relevant)


# ============================================================================
# 状态机工作流 (借鉴LangGraph)
# ============================================================================

class WorkflowState(Enum):
    """工作流状态"""
    IDLE = auto()
    PLANNING = auto()
    EXECUTING = auto()
    REVIEWING = auto()
    COMPLETED = auto()
    ERROR = auto()


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    name: str
    agent_role: str
    action: str
    next_steps: List[str] = field(default_factory=list)
    condition: Optional[Callable] = None  # 条件跳转


class StateMachineWorkflow:
    """
    状态机驱动的工作流
    
    借鉴LangGraph的状态机设计
    """
    
    def __init__(self, name: str):
        self.name = name
        self.steps: Dict[str, WorkflowStep] = {}
        self.current_state = WorkflowState.IDLE
        self.current_step: Optional[str] = None
        
        # 执行上下文
        self.context: Dict[str, Any] = {}
        self.history: List[Dict] = []
        
    def add_step(self, step: WorkflowStep):
        """添加步骤"""
        self.steps[step.id] = step
    
    def start(self, initial_context: Dict = None):
        """启动工作流"""
        self.current_state = WorkflowState.PLANNING
        self.context = initial_context or {}
        self.history.append({
            'event': 'workflow_started',
            'timestamp': time.time()
        })
    
    def transition_to(self, step_id: str):
        """状态转换"""
        if step_id not in self.steps:
            raise ValueError(f"未知步骤: {step_id}")
        
        self.current_step = step_id
        step = self.steps[step_id]
        
        self.history.append({
            'event': 'step_started',
            'step': step_id,
            'agent': step.agent_role,
            'timestamp': time.time()
        })
        
        return step
    
    def complete_step(self, step_id: str, result: Any):
        """完成步骤"""
        self.history.append({
            'event': 'step_completed',
            'step': step_id,
            'result': result,
            'timestamp': time.time()
        })
        
        # 确定下一步
        step = self.steps[step_id]
        
        if step.condition:
            # 条件跳转
            next_step = step.condition(result)
            return next_step
        elif step.next_steps:
            # 默认取第一个
            return step.next_steps[0]
        else:
            # 工作流结束
            self.current_state = WorkflowState.COMPLETED
            return None


# ============================================================================
# 多Agent协作引擎
# ============================================================================

class MultiAgentCollaboration:
    """
    多Agent协作引擎
    
    整合CrewAI角色定义 + AutoGen对话 + LangGraph状态机
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentRole] = {}
        self.conversations: Dict[str, Conversation] = {}
        self.workflows: Dict[str, StateMachineWorkflow] = {}
        self.tasks: Dict[str, Task] = {}
        
        # 任务队列
        self.pending_tasks: deque = deque()
        self.completed_tasks: deque = deque(maxlen=100)
        
    def register_agent(self, name: str, role: AgentRole):
        """注册Agent"""
        self.agents[name] = role
        
    def create_conversation(self, task_id: str, participants: List[str]) -> Conversation:
        """创建对话"""
        conv = Conversation(task_id)
        
        # 添加参与者
        for participant in participants:
            if participant in self.agents:
                conv.participants.add(participant)
        
        self.conversations[task_id] = conv
        return conv
    
    def create_task(self, description: str, 
                   assigned_to: Optional[str] = None,
                   context: str = "",
                   expected_output: str = "") -> Task:
        """创建任务"""
        task_id = hashlib.md5(f"{description}{time.time()}".encode()).hexdigest()[:12]
        
        task = Task(
            id=task_id,
            description=description,
            assigned_to=assigned_to,
            context=context,
            expected_output=expected_output
        )
        
        self.tasks[task_id] = task
        self.pending_tasks.append(task)
        
        return task
    
    def delegate_task(self, task_id: str, from_agent: str, to_agent: str):
        """
        任务委托 (借鉴Swarm的任务交接)
        """
        if task_id not in self.tasks:
            raise ValueError(f"未知任务: {task_id}")
        
        task = self.tasks[task_id]
        
        if not self.agents[from_agent].allow_delegation:
            raise PermissionError(f"{from_agent} 不允许委托任务")
        
        # 更新任务
        old_assignee = task.assigned_to
        task.assigned_to = to_agent
        task.status = TaskStatus.DELEGATED
        task.log('delegated', {
            'from': from_agent,
            'to': to_agent,
            'reason': f"{from_agent} 将任务委托给 {to_agent}"
        })
        
        # 记录到对话
        if task_id in self.conversations:
            conv = self.conversations[task_id]
            conv.add_message(Message(
                sender=from_agent,
                recipient=to_agent,
                content=f"我将任务 '{task.description[:50]}...' 委托给你",
                message_type='delegation'
            ))
        
        return task
    
    def execute_collaborative_task(self, task: Task, 
                                   workflow: StateMachineWorkflow) -> Dict:
        """
        执行协作任务
        
        完整流程:
        1. 创建工作流实例
        2. 按状态机执行步骤
        3. 管理Agent间对话
        4. 收集结果
        """
        print(f"\n🚀 开始协作任务: {task.description[:60]}...")
        
        # 创建对话
        conv = self.create_conversation(task.id, list(self.agents.keys()))
        
        # 启动工作流
        workflow.start({'task': task, 'conversation': conv})
        
        results = []
        current_step_id = list(workflow.steps.keys())[0] if workflow.steps else None
        max_iterations = 20  # 防止无限循环
        iteration = 0
        
        while current_step_id and iteration < max_iterations:
            iteration += 1
            step = workflow.transition_to(current_step_id)
            
            print(f"  📍 步骤: {step.name} (由 {step.agent_role} 执行)")
            
            # 获取Agent
            if step.agent_role not in self.agents:
                print(f"  ⚠️ 未知Agent: {step.agent_role}")
                break
            
            agent = self.agents[step.agent_role]
            
            # 构建上下文
            context = self._build_context(agent, task, conv, step)
            
            # 执行动作 (简化模拟)
            result = self._simulate_execution(agent, step, context)
            results.append({
                'step': step.id,
                'agent': step.agent_role,
                'result': result
            })
            
            # 添加到对话
            conv.add_message(Message(
                sender=step.agent_role,
                recipient='system',
                content=f"完成步骤 '{step.name}': {result[:100]}..." if len(str(result)) > 100 else f"完成步骤 '{step.name}': {result}",
                message_type='task_result'
            ))
            
            # 确定下一步
            next_step = workflow.complete_step(current_step_id, result)
            current_step_id = next_step
            
            if workflow.current_state == WorkflowState.COMPLETED:
                print(f"  ✅ 工作流完成")
                break
        
        # 更新任务状态
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.result = results
        self.completed_tasks.append(task)
        
        return {
            'task_id': task.id,
            'results': results,
            'iterations': iteration,
            'conversation_summary': self._summarize_conversation(conv)
        }
    
    def _build_context(self, agent: AgentRole, task: Task, 
                      conv: Conversation, step: WorkflowStep) -> str:
        """构建执行上下文"""
        context_parts = [
            agent.to_system_prompt(),
            "\n=== 当前任务 ===",
            f"描述: {task.description}",
            f"期望输出: {task.expected_output}",
            "\n=== 相关记忆 ===",
            agent.get_context(),
            "\n=== 对话历史 ===",
            conv.get_context_for_agent(agent.name),
            f"\n=== 当前步骤: {step.name} ===",
            f"动作: {step.action}"
        ]
        
        return "\n".join(context_parts)
    
    def _simulate_execution(self, agent: AgentRole, step: WorkflowStep, 
                           context: str) -> str:
        """
        模拟Agent执行 (实际应调用LLM)
        
        这里简化模拟，实际实现应调用大模型API
        """
        # 根据Agent角色和步骤动作生成模拟结果
        if 'research' in step.action.lower():
            return f"[{agent.name}] 完成研究: 找到关于'{step.action}'的相关信息"
        elif 'code' in step.action.lower() or 'develop' in step.action.lower():
            return f"[{agent.name}] 完成代码: 实现了'{step.action}'的功能"
        elif 'review' in step.action.lower():
            return f"[{agent.name}] 完成审查: 发现2个问题，提出3条建议"
        elif 'write' in step.action.lower():
            return f"[{agent.name}] 完成文档: 撰写了'{step.action}'的说明"
        else:
            return f"[{agent.name}] 完成步骤: {step.action}"
    
    def _summarize_conversation(self, conv: Conversation) -> str:
        """总结对话"""
        messages = conv.messages
        
        summary = []
        for msg in messages:
            if msg.message_type == 'task_result':
                summary.append(f"- {msg.sender}: {msg.content[:80]}...")
        
        return "\n".join(summary[:10])  # 最多10条
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'registered_agents': len(self.agents),
            'active_conversations': len(self.conversations),
            'pending_tasks': len(self.pending_tasks),
            'completed_tasks': len(self.completed_tasks),
            'agent_roles': list(self.agents.keys())
        }


# ============================================================================
# 预定义工作流模板
# ============================================================================

def create_code_review_workflow() -> StateMachineWorkflow:
    """代码审查工作流"""
    workflow = StateMachineWorkflow("代码审查")
    
    # 步骤1: 需求分析
    workflow.add_step(WorkflowStep(
        id="analyze",
        name="需求分析",
        agent_role="planner",
        action="分析代码审查需求，确定审查范围",
        next_steps=["research"]
    ))
    
    # 步骤2: 背景研究
    workflow.add_step(WorkflowStep(
        id="research",
        name="背景研究",
        agent_role="researcher",
        action="研究相关技术背景和规范",
        next_steps=["develop"]
    ))
    
    # 步骤3: 代码实现
    workflow.add_step(WorkflowStep(
        id="develop",
        name="代码实现",
        agent_role="developer",
        action="编写或修改代码",
        next_steps=["review"]
    ))
    
    # 步骤4: 代码审查
    workflow.add_step(WorkflowStep(
        id="review",
        name="代码审查",
        agent_role="reviewer",
        action="审查代码质量，发现问题",
        next_steps=["document"],
        # 这里可以添加条件: 如果有严重问题，返回develop
    ))
    
    # 步骤5: 文档撰写
    workflow.add_step(WorkflowStep(
        id="document",
        name="文档撰写",
        agent_role="writer",
        action="撰写技术文档和注释",
        next_steps=[]  # 结束
    ))
    
    return workflow


def create_research_workflow() -> StateMachineWorkflow:
    """研究工作流"""
    workflow = StateMachineWorkflow("深度研究")
    
    workflow.add_step(WorkflowStep(
        id="plan",
        name="研究规划",
        agent_role="planner",
        action="制定研究计划和问题清单",
        next_steps=["research"]
    ))
    
    workflow.add_step(WorkflowStep(
        id="research",
        name="信息收集",
        agent_role="researcher",
        action="深入收集和分析信息",
        next_steps=["synthesize"]
    ))
    
    workflow.add_step(WorkflowStep(
        id="synthesize",
        name="综合分析",
        agent_role="researcher",  # 可以是另一个researcher或同一个
        action="整合信息，形成结论",
        next_steps=["write"]
    ))
    
    workflow.add_step(WorkflowStep(
        id="write",
        name="报告撰写",
        agent_role="writer",
        action="撰写研究报告",
        next_steps=[]
    ))
    
    return workflow


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Multi-Agent Collaboration Framework - 测试")
    print("="*60)
    
    # 创建协作引擎
    engine = MultiAgentCollaboration()
    
    # 注册Agents
    print("\n👥 注册Agents:")
    for name, role in AGENT_TEMPLATES.items():
        engine.register_agent(name, role)
        print(f"   ✅ {name}: {role.role}")
    
    # 测试1: 代码审查工作流
    print("\n" + "="*60)
    print("🧪 测试1: 代码审查工作流")
    print("="*60)
    
    # 创建任务
    task = engine.create_task(
        description="实现自适应RAG的查询分类器功能",
        context="WDai系统需要增强RAG能力，实现基于查询类型的自适应检索策略",
        expected_output="完整的查询分类器实现代码，包含5种类型识别"
    )
    print(f"\n📋 创建任务: {task.description}")
    
    # 创建工作流
    workflow = create_code_review_workflow()
    print(f"📊 工作流步骤: {len(workflow.steps)}个")
    for step_id, step in workflow.steps.items():
        print(f"   - {step.name} ({step.agent_role})")
    
    # 执行协作任务
    result = engine.execute_collaborative_task(task, workflow)
    
    print(f"\n✅ 任务完成!")
    print(f"   迭代次数: {result['iterations']}")
    print(f"   参与步骤: {len(result['results'])}")
    
    # 测试2: 研究工作流
    print("\n" + "="*60)
    print("🧪 测试2: 深度研究工作流")
    print("="*60)
    
    task2 = engine.create_task(
        description="调研2025年最新的RAG架构优化方法",
        expected_output="研究报告，包含至少3种先进的RAG架构模式"
    )
    print(f"\n📋 创建任务: {task2.description}")
    
    workflow2 = create_research_workflow()
    result2 = engine.execute_collaborative_task(task2, workflow2)
    
    print(f"\n✅ 任务完成!")
    print(f"   迭代次数: {result2['iterations']}")
    
    # 测试3: 任务委托
    print("\n" + "="*60)
    print("🧪 测试3: 任务委托")
    print("="*60)
    
    task3 = engine.create_task(
        description="编写单元测试",
        assigned_to="developer"
    )
    print(f"\n📋 初始分配: {task3.assigned_to}")
    
    # 委托给reviewer
    engine.delegate_task(task3.id, "developer", "reviewer")
    print(f"📤 委托后: {task3.assigned_to}")
    print(f"   委托记录: {len([l for l in task3.execution_log if l['event'] == 'delegated'])}条")
    
    # 统计
    print("\n" + "="*60)
    print("📊 系统统计")
    print("="*60)
    stats = engine.get_stats()
    print(f"   注册Agents: {stats['registered_agents']}")
    print(f"   活跃对话: {stats['active_conversations']}")
    print(f"   待处理任务: {stats['pending_tasks']}")
    print(f"   已完成任务: {stats['completed_tasks']}")
    print(f"   Agent角色: {', '.join(stats['agent_roles'])}")
    
    print("\n" + "="*60)
    print("✅ 多Agent协作框架测试完成")
    print("="*60)
