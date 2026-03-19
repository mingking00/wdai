"""
wdai v3.0 - Agent System Models
Phase 3: Agent专业化系统 - 数据模型
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid


class AgentRole(Enum):
    """Agent角色"""
    ORCHESTRATOR = "orchestrator"    # 协调者
    CODER = "coder"                  # 代码实现
    REVIEWER = "reviewer"            # 代码审查
    DEBUGGER = "debugger"            # 调试定位
    ARCHITECT = "architect"          # 架构设计
    TESTER = "tester"                # 测试验证
    DOC_WRITER = "doc_writer"        # 文档编写
    CUSTOM = "custom"                # 自定义


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"              # 待处理
    PLANNED = "planned"              # 已规划
    RUNNING = "running"              # 执行中
    COMPLETED = "completed"          # 完成
    FAILED = "failed"                # 失败
    CANCELLED = "cancelled"          # 取消


class TodoStatus(Enum):
    """TODO状态"""
    PENDING = "pending"              # 待执行
    BLOCKED = "blocked"              # 被阻塞
    RUNNING = "running"              # 执行中
    COMPLETED = "completed"          # 完成
    FAILED = "failed"                # 失败
    SKIPPED = "skipped"              # 跳过


@dataclass
class AgentConfig:
    """Agent配置"""
    role: AgentRole
    name: str
    expertise: List[str] = field(default_factory=list)
    system_prompt: str = ""
    max_context_tokens: int = 4000
    timeout_seconds: int = 300
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    output: Any = None
    error_message: Optional[str] = None
    execution_time_ms: int = 0
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def failed(self) -> bool:
        return not self.success


@dataclass
class Task:
    """用户任务"""
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    description: str = ""
    goal: str = ""
    constraints: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    priority: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "goal": self.goal,
            "constraints": self.constraints,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "priority": self.priority
        }


@dataclass
class SubTask:
    """子任务"""
    id: str = field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:8]}")
    parent_id: str = ""
    type: str = ""                   # 任务类型: implement/review/debug/...
    description: str = ""
    assigned_to: Optional[AgentRole] = None
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[AgentResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def mark_started(self):
        """标记开始"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
    
    def mark_completed(self, result: AgentResult):
        """标记完成"""
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.result = result
        self.completed_at = datetime.now()
    
    def is_ready(self, completed_ids: Set[str]) -> bool:
        """检查是否就绪（所有依赖已完成）"""
        return all(dep_id in completed_ids for dep_id in self.dependencies)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "type": self.type,
            "description": self.description,
            "assigned_to": self.assigned_to.value if self.assigned_to else None,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class NarrowContext:
    """
    窄上下文 (Fresh Eyes原则)
    
    Subagent只接收必要信息，不包含完整工作流
    """
    subtask: SubTask
    relevant_files: List[str] = field(default_factory=list)
    parent_goal: str = ""            # 父任务目标
    parent_context: Dict[str, Any] = field(default_factory=dict)
    previous_results: Dict[str, Any] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)
    
    def to_prompt_context(self) -> str:
        """转换为Prompt上下文"""
        lines = [
            f"任务: {self.subtask.description}",
            f"类型: {self.subtask.type}",
            ""
        ]
        
        if self.parent_goal:
            lines.extend([
                f"整体目标: {self.parent_goal}",
                ""
            ])
        
        if self.relevant_files:
            lines.extend([
                "相关文件:",
                *[f"  - {f}" for f in self.relevant_files],
                ""
            ])
        
        if self.previous_results:
            lines.extend([
                "前置结果:",
                *[f"  {k}: {v}" for k, v in list(self.previous_results.items())[:3]],
                ""
            ])
        
        return "\n".join(lines)


@dataclass
class TodoItem:
    """TODO项"""
    id: str = field(default_factory=lambda: f"todo_{uuid.uuid4().hex[:6]}")
    description: str = ""
    status: TodoStatus = TodoStatus.PENDING
    assigned_agent: Optional[AgentRole] = None
    subtask_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    estimated_minutes: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: str = ""                  # 执行备注
    
    @property
    def is_completed(self) -> bool:
        return self.status == TodoStatus.COMPLETED
    
    @property
    def is_blocked(self, completed_ids: Set[str] = None) -> bool:
        """检查是否被阻塞"""
        if completed_ids is None:
            return self.status == TodoStatus.BLOCKED
        return not all(dep in completed_ids for dep in self.dependencies)
    
    def mark_started(self):
        """标记开始"""
        self.status = TodoStatus.RUNNING
        self.started_at = datetime.now()
    
    def mark_completed(self, notes: str = ""):
        """标记完成"""
        self.status = TodoStatus.COMPLETED
        self.completed_at = datetime.now()
        if notes:
            self.notes = notes
    
    def mark_failed(self, error: str):
        """标记失败"""
        self.status = TodoStatus.FAILED
        self.completed_at = datetime.now()
        self.notes = f"失败: {error}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent.value if self.assigned_agent else None,
            "subtask_id": self.subtask_id,
            "dependencies": self.dependencies,
            "estimated_minutes": self.estimated_minutes,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class TodoPlan:
    """TODO计划"""
    task_id: str
    todos: List[TodoItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_current_todo(self) -> Optional[TodoItem]:
        """获取当前应执行的TODO"""
        completed_ids = {t.id for t in self.todos if t.is_completed}
        
        for todo in self.todos:
            if todo.status == TodoStatus.PENDING and not todo.is_blocked(completed_ids):
                return todo
            if todo.status == TodoStatus.RUNNING:
                return todo
        
        return None
    
    def get_progress(self) -> Dict[str, int]:
        """获取进度"""
        total = len(self.todos)
        completed = sum(1 for t in self.todos if t.is_completed)
        failed = sum(1 for t in self.todos if t.status == TodoStatus.FAILED)
        pending = sum(1 for t in self.todos if t.status == TodoStatus.PENDING)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "percentage": int(completed / total * 100) if total > 0 else 0
        }
    
    def is_complete(self) -> bool:
        """检查是否全部完成"""
        return all(t.is_completed or t.status == TodoStatus.SKIPPED 
                   for t in self.todos)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "todos": [t.to_dict() for t in self.todos],
            "progress": self.get_progress(),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class TaskExecution:
    """任务执行记录"""
    task: Task
    plan: TodoPlan
    subtasks: Dict[str, SubTask] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    final_result: Optional[AgentResult] = None
    
    def start(self):
        """开始执行"""
        self.start_time = datetime.now()
    
    def finish(self, result: AgentResult):
        """完成执行"""
        self.end_time = datetime.now()
        self.final_result = result
    
    @property
    def duration_seconds(self) -> float:
        """执行时长"""
        if not self.start_time:
            return 0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


# 便捷函数
def create_task(description: str, goal: str = "", **kwargs) -> Task:
    """创建任务"""
    return Task(description=description, goal=goal, **kwargs)


def create_subtask(
    description: str,
    task_type: str,
    parent_id: str = "",
    dependencies: List[str] = None
) -> SubTask:
    """创建子任务"""
    return SubTask(
        description=description,
        type=task_type,
        parent_id=parent_id,
        dependencies=dependencies or []
    )
