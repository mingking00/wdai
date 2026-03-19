"""
wdai v3.0 - Workflow Models
SOP工作流引擎 - 数据模型
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"          # 待执行
    RUNNING = "running"          # 执行中
    PAUSED = "paused"            # 暂停
    COMPLETED = "completed"      # 完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 取消


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"          # 待执行
    WAITING = "waiting"          # 等待依赖
    RUNNING = "running"          # 执行中
    COMPLETED = "completed"      # 完成
    FAILED = "failed"            # 失败
    SKIPPED = "skipped"          # 跳过
    CANCELLED = "cancelled"      # 取消


class StepAction(Enum):
    """步骤动作类型"""
    LLM = "llm"                  # LLM调用
    SHELL = "shell"              # Shell命令
    PYTHON = "python"            # Python代码
    SUB_WORKFLOW = "sub_workflow" # 子工作流
    CUSTOM = "custom"            # 自定义动作
    WAIT = "wait"                # 等待条件


@dataclass
class RetryPolicy:
    """重试策略"""
    max_retries: int = 3                     # 最大重试次数
    retry_delay: float = 1.0                 # 初始延迟（秒）
    backoff_multiplier: float = 2.0          # 退避乘数
    retry_on: List[str] = field(default_factory=lambda: ["error"])  # 重试触发条件
    
    def get_delay(self, attempt: int) -> float:
        """获取第n次重试的延迟时间"""
        return self.retry_delay * (self.backoff_multiplier ** attempt)


@dataclass
class ErrorInfo:
    """错误信息"""
    step_id: str
    error_type: str
    error_message: str
    traceback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Step:
    """工作流步骤定义"""
    id: str
    name: str
    description: str = ""
    action: StepAction = StepAction.CUSTOM
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    condition: Optional[str] = None           # 执行条件表达式
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    timeout: Optional[int] = None             # 超时时间（秒）
    allow_parallel: bool = False              # 是否允许与其他步骤并行
    
    def __post_init__(self):
        if isinstance(self.action, str):
            self.action = StepAction(self.action)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "action": self.action.value,
            "config": self.config,
            "dependencies": self.dependencies,
            "condition": self.condition,
            "retry_policy": {
                "max_retries": self.retry_policy.max_retries,
                "retry_delay": self.retry_policy.retry_delay,
                "backoff_multiplier": self.retry_policy.backoff_multiplier,
            },
            "timeout": self.timeout,
            "allow_parallel": self.allow_parallel
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        """从字典创建"""
        retry_data = data.get("retry_policy", {})
        retry_policy = RetryPolicy(
            max_retries=retry_data.get("max_retries", 3),
            retry_delay=retry_data.get("retry_delay", 1.0),
            backoff_multiplier=retry_data.get("backoff_multiplier", 2.0)
        )
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            action=StepAction(data.get("action", "custom")),
            config=data.get("config", {}),
            dependencies=data.get("dependencies", []),
            condition=data.get("condition"),
            retry_policy=retry_policy,
            timeout=data.get("timeout"),
            allow_parallel=data.get("allow_parallel", False)
        )


@dataclass
class Workflow:
    """工作流定义"""
    id: str = field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    steps: List[Step] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_step(self, step_id: str) -> Optional[Step]:
        """获取指定步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_dependencies(self, step_id: str) -> List[Step]:
        """获取步骤的所有依赖"""
        step = self.get_step(step_id)
        if not step:
            return []
        return [s for s in self.steps if s.id in step.dependencies]
    
    def validate(self) -> List[str]:
        """验证工作流定义，返回错误列表"""
        errors = []
        
        # 检查步骤ID唯一性
        step_ids = [s.id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("步骤ID存在重复")
        
        # 检查依赖是否存在
        for step in self.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    errors.append(f"步骤 '{step.id}' 依赖不存在的步骤 '{dep_id}'")
        
        # 检查循环依赖
        if self._has_cycle():
            errors.append("工作流存在循环依赖")
        
        return errors
    
    def _has_cycle(self) -> bool:
        """检测是否存在循环依赖"""
        # 构建邻接表
        graph = {s.id: s.dependencies for s in self.steps}
        
        # DFS检测环
        visited = set()
        rec_stack = set()
        
        def has_cycle_util(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for step_id in graph:
            if step_id not in visited:
                if has_cycle_util(step_id):
                    return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [s.to_dict() for s in self.steps],
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """从字典创建"""
        return cls(
            id=data.get("id", f"wf_{uuid.uuid4().hex[:12]}"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            steps=[Step.from_dict(s) for s in data.get("steps", [])],
            context=data.get("context", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            metadata=data.get("metadata", {})
        )


@dataclass
class StepState:
    """步骤执行状态"""
    step_id: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Any = None
    error: Optional[ErrorInfo] = None
    retry_count: int = 0
    execution_time_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "output": self.output,
            "error": self.error.to_dict() if self.error else None,
            "retry_count": self.retry_count,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class WorkflowInstance:
    """工作流实例（运行时）"""
    id: str = field(default_factory=lambda: f"wfi_{uuid.uuid4().hex[:12]}")
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    step_states: Dict[str, StepState] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_info: Optional[ErrorInfo] = None
    
    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = WorkflowStatus(self.status)
    
    def get_step_state(self, step_id: str) -> StepState:
        """获取步骤状态，如果不存在则创建"""
        if step_id not in self.step_states:
            self.step_states[step_id] = StepState(step_id=step_id)
        return self.step_states[step_id]
    
    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.status in [
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED
        ]
    
    def is_running(self) -> bool:
        """检查是否运行中"""
        return self.status == WorkflowStatus.RUNNING
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "context": self.context,
            "step_states": {k: v.to_dict() for k, v in self.step_states.items()},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_info": self.error_info.to_dict() if self.error_info else None
        }


# 便捷函数
def create_workflow(name: str, steps: List[Step], **kwargs) -> Workflow:
    """创建工作流"""
    return Workflow(
        name=name,
        steps=steps,
        **kwargs
    )


def create_step(id: str, name: str, action: StepAction, **kwargs) -> Step:
    """创建步骤"""
    return Step(
        id=id,
        name=name,
        action=action,
        **kwargs
    )
