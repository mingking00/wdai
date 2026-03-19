"""
wdai v3.2 - Agent System
Phase 4: Gnet负载均衡模式集成

新增功能:
- 负载均衡选择 (RoundRobin/LeastLoaded/Weighted/Hash)
- 非阻塞执行池 (背压控制)
- 实时负载监控

实现Claude Code风格的Agent专业化架构：
- Orchestrator + Subagents
- Fresh Eyes上下文管理
- TODO-based规划
"""

from .models import (
    AgentConfig,
    AgentRole,
    AgentResult,
    Task,
    SubTask,
    TodoItem,
    TodoPlan,
    TodoStatus,
    TaskStatus,
    NarrowContext,
    TaskExecution,
    create_task,
    create_subtask
)
from .base import (
    BaseAgent,
    AgentRegistry,
    get_agent_registry,
    register_agent,
    get_agent,
    # v3.1 Rathole模式
    ExponentialBackoff,
    ResourceLimits,
    ExecutionPool
)
from .load_balancer import (
    LoadBalancingStrategy,
    AgentLoadMetrics,
    LoadBalancer,
    NonBlockingExecutionPool
)
from .enhanced_registry import (
    EnhancedAgentRegistry,
    get_enhanced_registry
)
from .service_trait import (
    ServiceAgent,
    ServiceResult,
    FromRequest,
    TaskType,
    TaskContent,
    ContextExtractor,
    SharedStateManager,
    SharedData,
    Middleware,
    LoggingMiddleware,
    MetricsMiddleware,
    TracingMiddleware,
    MiddlewareChain,
)
from .cognitive_safety import (
    CognitiveSafetySystem,
    SafetyLevel,
    ViolationType,
    SafetyCheck,
    Violation,
    create_safety_system,
    validate_before_send,
    CONTEXT_TEMPLATES,
)
from .innovation_v2 import (
    InnovationEngineV2,
    Approach,
    ApproachType,
    Problem,
    EvaluationResult,
    Dimension,
    create_innovation_engine,
)
from .agent_engine_v3 import (
    AgentExecutor,
    ConceptualAgent,
    ParallelAgent,
    MultiAgentOrchestrator,
    VerificationLayer,
    AgentOutput,
    Uncertainty,
    VerificationResult,
    ExecutionMode,
    VerificationStatus,
    create_conceptual_agent,
    create_parallel_agent,
    create_orchestrator,
)
from .attention_orchestrator import (
    AttentionBasedOrchestrator,
    AttentionConfig,
    AgentAttentionState,
    create_attention_orchestrator,
)
from .dynamic_verification import (
    DynamicVerificationLayer,
    DynamicCheckpoint,
    CheckpointType,
    ViolationHistory,
    create_dynamic_verification_layer,
)
from .reasoning_trace import (
    ReasoningTracer,
    ReasoningStep,
    ReasoningStepType,
    TaskTrace,
    TraceObserver,
    ConsoleObserver,
    StructuredReasoning,
    tracer,
)
from .structured_cot import (
    StructuredCoT,
    QuickCoT,
    CoTSection,
    CoTField,
    CoTFieldType,
    STANDARD_REASONING_TEMPLATE,
)
from .actix_integration import (
    ActixStyleAgent,
    SharedStateMixin,
    EnhancedSubtaskExtractor,
)
from .context import (
    ContextManager,
    create_context_manager
)
from .context_enhanced import (
    EnhancedContextManager,
    create_enhanced_context_manager
)
from .context_embedding import (
    EmbeddingContextManager,
    create_embedding_context_manager
)
from .todo import (
    TodoPlanner,
    create_planner
)
from .orchestrator import OrchestratorAgent

__version__ = "0.3.2"

__all__ = [
    # 数据模型
    "AgentConfig",
    "AgentRole",
    "AgentResult",
    "Task",
    "SubTask",
    "TodoItem",
    "TodoPlan",
    "TodoStatus",
    "TaskStatus",
    "NarrowContext",
    "TaskExecution",
    
    # Agent基类
    "BaseAgent",
    "AgentRegistry",
    "get_agent_registry",
    "register_agent",
    "get_agent",
    # v3.1 Rathole模式
    "ExponentialBackoff",
    "ResourceLimits",
    "ExecutionPool",
    
    # Gnet模式 - 负载均衡
    "LoadBalancingStrategy",
    "AgentLoadMetrics",
    "LoadBalancer",
    "NonBlockingExecutionPool",
    "EnhancedAgentRegistry",
    "get_enhanced_registry",
    
    # Actix-web模式 - Service Trait
    "ServiceAgent",
    "ServiceResult",
    "FromRequest",
    "TaskType",
    "TaskContent",
    "ContextExtractor",
    "SharedStateManager",
    "SharedData",
    "Middleware",
    "LoggingMiddleware",
    "MetricsMiddleware",
    "TracingMiddleware",
    "MiddlewareChain",
    "ActixStyleAgent",
    "SharedStateMixin",
    "EnhancedSubtaskExtractor",
    
    # 推理追踪 - v3.4
    "ReasoningTracer",
    "ReasoningStep",
    "ReasoningStepType",
    "TaskTrace",
    "TraceObserver",
    "ConsoleObserver",
    "StructuredReasoning",
    "tracer",
    
    # 结构化思维链 - v3.4.1
    "StructuredCoT",
    "QuickCoT",
    "CoTSection",
    "CoTField",
    "CoTFieldType",
    "STANDARD_REASONING_TEMPLATE",
    
    # 认知安全系统 - v3.4.2
    "CognitiveSafetySystem",
    "SafetyLevel",
    "ViolationType",
    "SafetyCheck",
    "Violation",
    "create_safety_system",
    "validate_before_send",
    "CONTEXT_TEMPLATES",
    
    # 创新引擎 v2.0 - v3.4.3
    "InnovationEngineV2",
    "Approach",
    "ApproachType",
    "Problem",
    "EvaluationResult",
    "Dimension",
    "create_innovation_engine",
    
    # Agent执行引擎 v3.0 - v3.4.4
    "AgentExecutor",
    "ConceptualAgent",
    "ParallelAgent",
    "MultiAgentOrchestrator",
    "VerificationLayer",
    "AgentOutput",
    "Uncertainty",
    "VerificationResult",
    "ExecutionMode",
    "VerificationStatus",
    "create_conceptual_agent",
    "create_parallel_agent",
    "create_orchestrator",
    
    # AttnRes改进 - v3.4.5
    "AttentionBasedOrchestrator",
    "AttentionConfig",
    "AgentAttentionState",
    "create_attention_orchestrator",
    "DynamicVerificationLayer",
    "DynamicCheckpoint",
    "CheckpointType",
    "ViolationHistory",
    "create_dynamic_verification_layer",
    
    # 上下文管理 (三版本)
    "ContextManager",
    "create_context_manager",
    "EnhancedContextManager",
    "create_enhanced_context_manager",
    "EmbeddingContextManager",
    "create_embedding_context_manager",
    
    # TODO规划
    "TodoPlanner",
    "create_planner",
    
    # Orchestrator
    "OrchestratorAgent",
    
    # 便捷函数
    "create_task",
    "create_subtask",
    "initialize_agent_system"
]


def initialize_agent_system(context_manager_type: str = "simple") -> OrchestratorAgent:
    """
    初始化Agent系统
    
    注册所有专业Agent并返回Orchestrator
    
    Args:
        context_manager_type: 上下文管理器类型
            - "simple": 简单版 (关键词匹配) - 默认 ⭐
            - "enhanced": 增强版 (TF-IDF)
            - "embedding": Embedding版 (向量语义)
    
    Returns:
        OrchestratorAgent实例
    """
    from .subagents import register_all_subagents
    
    # 注册所有Subagents
    register_all_subagents()
    
    # 创建Orchestrator
    orchestrator = OrchestratorAgent(context_manager_type=context_manager_type)
    
    # 注册Orchestrator（可选）
    register_agent(orchestrator)
    
    return orchestrator
