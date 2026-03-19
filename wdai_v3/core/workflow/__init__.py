"""
wdai v3.0 - Workflow Engine
SOP工作流引擎 - Phase 2 实现

提供标准化的工作流程编排和执行
"""

from .models import (
    Workflow,
    Step,
    WorkflowInstance,
    StepState,
    WorkflowStatus,
    StepStatus,
    StepAction,
    RetryPolicy,
    ErrorInfo,
    create_workflow,
    create_step
)
from .engine import WorkflowEngine
from .dependency import DependencyResolver, resolve_dependencies
from .executor import (
    BaseExecutor,
    LLMExecutor,
    ShellExecutor,
    PythonExecutor,
    WaitExecutor,
    CustomExecutor,
    ExecutorRegistry,
    get_executor_registry,
    StepExecutionResult
)

__all__ = [
    # 数据模型
    "Workflow",
    "Step", 
    "WorkflowInstance",
    "StepState",
    "WorkflowStatus",
    "StepStatus",
    "StepAction",
    "RetryPolicy",
    "ErrorInfo",
    
    # 核心引擎
    "WorkflowEngine",
    
    # 依赖解析
    "DependencyResolver",
    "resolve_dependencies",
    
    # 执行器
    "BaseExecutor",
    "LLMExecutor",
    "ShellExecutor",
    "PythonExecutor",
    "WaitExecutor",
    "CustomExecutor",
    "ExecutorRegistry",
    "get_executor_registry",
    "StepExecutionResult",
    
    # 便捷函数
    "create_workflow",
    "create_step"
]

__version__ = "0.2.0"
