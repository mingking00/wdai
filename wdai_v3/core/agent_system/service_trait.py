"""
Actix-web模式应用 - Service Trait系统

从Actix-web学习的关键模式:
1. Service Trait - 统一请求处理接口
2. Extractor模式 - 自动参数提取
3. Data<T>共享状态 - 跨组件状态共享
4. 中间件链 - 执行前后处理

应用到wdai:
- Agent实现统一的Service接口
- 使用Extractor简化参数提取
- 共享状态管理
"""

from typing import TypeVar, Generic, Protocol, runtime_checkable, Any, Dict, Optional
from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from functools import wraps
import uuid


# ============================================================================
# 1. Service Trait (核心抽象)
# ============================================================================

T = TypeVar('T')  # 请求类型
R = TypeVar('R')  # 响应类型
E = TypeVar('E')  # 错误类型


@runtime_checkable
class Service(Protocol, Generic[T, R, E]):
    """
    Service Trait - 统一的请求处理接口
    
    从Actix-web的Service trait简化而来:
    - call: 处理请求，返回Future
    - ready: 检查是否准备好处理请求
    """
    
    async def call(self, request: T) -> R:
        """处理请求"""
        ...
    
    def ready(self) -> bool:
        """检查是否准备好处理请求"""
        return True


class ServiceResult:
    """Service统一返回结果"""
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
    
    @property
    def is_ok(self) -> bool:
        return self.success
    
    @property
    def is_err(self) -> bool:
        return not self.success
    
    def unwrap(self) -> Any:
        if self.is_err:
            raise RuntimeError(f"Service error: {self.error}")
        return self.data
    
    @classmethod
    def ok(cls, data: Any = None) -> 'ServiceResult':
        return cls(success=True, data=data)
    
    @classmethod
    def err(cls, error: str) -> 'ServiceResult':
        return cls(success=False, error=error)


# ============================================================================
# 2. Extractor模式 (参数提取)
# ============================================================================

class FromRequest(ABC):
    """
    Extractor基类 - 从请求中提取数据
    
    从Actix-web的FromRequest trait简化
    """
    
    @classmethod
    @abstractmethod
    async def from_request(cls, request: Dict[str, Any]) -> 'FromRequest':
        """从请求中提取数据"""
        pass
    
    @classmethod
    def extract(cls, request: Dict[str, Any]):
        """同步提取包装"""
        try:
            return asyncio.run(cls.from_request(request))
        except RuntimeError:
            # 如果在event loop中
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(cls.from_request(request))


@dataclass
class TaskType(FromRequest):
    """任务类型提取器"""
    value: str
    
    @classmethod
    async def from_request(cls, request: Dict[str, Any]) -> 'TaskType':
        return cls(value=request.get('task_type', 'unknown'))


@dataclass
class TaskContent(FromRequest):
    """任务内容提取器"""
    value: str
    
    @classmethod
    async def from_request(cls, request: Dict[str, Any]) -> 'TaskContent':
        return cls(value=request.get('content', ''))


@dataclass
class ContextExtractor(FromRequest):
    """上下文提取器"""
    task_id: str
    parent_id: Optional[str]
    metadata: Dict[str, Any]
    
    @classmethod
    async def from_request(cls, request: Dict[str, Any]) -> 'ContextExtractor':
        return cls(
            task_id=request.get('task_id', ''),
            parent_id=request.get('parent_id'),
            metadata=request.get('metadata', {})
        )


# ============================================================================
# 3. Data<T>共享状态
# ============================================================================

import threading
from contextlib import contextmanager


class SharedData:
    """
    共享状态容器 (简化版Actix-web Data<T>)
    
    特点:
    - 线程安全 (使用RLock)
    - 引用计数
    - 支持嵌套锁定
    """
    
    def __init__(self, data: Any):
        self._data = data
        self._lock = threading.RLock()
        self._ref_count = 1
    
    def clone(self) -> 'SharedData':
        """克隆引用 (增加引用计数)"""
        self._ref_count += 1
        return SharedData(self._data)
    
    @contextmanager
    def read(self):
        """获取读锁"""
        with self._lock:
            yield self._data
    
    @contextmanager  
    def write(self):
        """获取写锁"""
        with self._lock:
            yield self._data
    
    def get(self) -> Any:
        """获取数据 (非锁定，只读安全类型使用)"""
        return self._data


class SharedStateManager:
    """共享状态管理器"""
    
    def __init__(self):
        self._states: Dict[str, SharedData] = {}
        self._lock = threading.Lock()
    
    def register(self, name: str, data: Any) -> SharedData:
        """注册共享状态"""
        with self._lock:
            if name in self._states:
                return self._states[name]
            shared = SharedData(data)
            self._states[name] = shared
            return shared
    
    def get(self, name: str) -> Optional[SharedData]:
        """获取共享状态"""
        with self._lock:
            return self._states.get(name)
    
    def list(self) -> Dict[str, type]:
        """列出所有共享状态"""
        with self._lock:
            return {k: type(v._data) for k, v in self._states.items()}


# ============================================================================
# 4. 中间件链 (简化版)
# ============================================================================

@dataclass
class RequestContext:
    """请求上下文"""
    request: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ResponseContext:
    """响应上下文"""
    result: ServiceResult
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Middleware(ABC):
    """中间件基类"""
    
    @abstractmethod
    async def before_request(self, ctx: RequestContext) -> RequestContext:
        """请求前处理"""
        return ctx
    
    @abstractmethod
    async def after_request(self, ctx: ResponseContext) -> ResponseContext:
        """请求后处理"""
        return ctx


class LoggingMiddleware(Middleware):
    """日志中间件"""
    
    async def before_request(self, ctx: RequestContext) -> RequestContext:
        ctx.metadata['start_time'] = asyncio.get_event_loop().time()
        print(f"[Request] {ctx.request.get('task_type', 'unknown')}")
        return ctx
    
    async def after_request(self, ctx: ResponseContext) -> ResponseContext:
        start_time = ctx.metadata.get('start_time')
        if start_time:
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"[Response] success={ctx.result.success}, elapsed={elapsed:.3f}s")
        return ctx


class MetricsMiddleware(Middleware):
    """指标中间件"""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_latency = 0.0
    
    async def before_request(self, ctx: RequestContext) -> RequestContext:
        self.request_count += 1
        return ctx
    
    async def after_request(self, ctx: ResponseContext) -> ResponseContext:
        if not ctx.result.success:
            self.error_count += 1
        return ctx
    
    def get_metrics(self) -> Dict:
        return {
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / self.request_count if self.request_count > 0 else 0
        }


class TracingMiddleware(Middleware):
    """追踪中间件 - 集成推理追踪"""
    
    def __init__(self, tracer=None):
        self.tracer = tracer
    
    async def before_request(self, ctx: RequestContext) -> RequestContext:
        # 生成任务ID
        task_id = str(uuid.uuid4())[:8]
        ctx.metadata['task_id'] = task_id
        ctx.metadata['start_time'] = asyncio.get_event_loop().time()
        
        # 如果有tracer，开始追踪
        if self.tracer:
            task_type = ctx.request.get('task_type', 'unknown')
            agent_name = ctx.request.get('agent_name', 'unknown')
            self.tracer.start_task(task_id, task_type, agent_name)
        
        return ctx
    
    async def after_request(self, ctx: ResponseContext) -> ResponseContext:
        task_id = ctx.metadata.get('task_id')
        
        if self.tracer and task_id:
            if ctx.result.success:
                self.tracer.complete_task(task_id, ctx.result.data)
            else:
                self.tracer.fail_task(task_id, ctx.result.error or "Unknown error")
        
        return ctx


class MiddlewareChain:
    """中间件链"""
    
    def __init__(self):
        self.middlewares: list[Middleware] = []
    
    def add(self, mw: Middleware) -> 'MiddlewareChain':
        """添加中间件 (返回self支持链式调用)"""
        self.middlewares.append(mw)
        return self
    
    async def execute(self, request: Dict[str, Any], handler) -> ServiceResult:
        """执行中间件链"""
        # 构建请求上下文
        ctx = RequestContext(request=request)
        
        # 前置处理 (正序)
        for mw in self.middlewares:
            ctx = await mw.before_request(ctx)
        
        # 执行handler
        try:
            result = await handler(ctx.request)
        except Exception as e:
            result = ServiceResult.err(str(e))
        
        # 构建响应上下文
        resp_ctx = ResponseContext(result=result, metadata=ctx.metadata)
        
        # 后置处理 (逆序)
        for mw in reversed(self.middlewares):
            resp_ctx = await mw.after_request(resp_ctx)
        
        return resp_ctx.result


# ============================================================================
# 5. 增强版Agent (集成Service Trait)
# ============================================================================

class ServiceAgent(ABC):
    """
    增强版Agent (Service Trait集成)
    
    实现统一的Service接口
    """
    
    def __init__(self, name: str, shared_state: Optional[SharedStateManager] = None, enable_tracing: bool = True):
        self.name = name
        self.shared_state = shared_state or SharedStateManager()
        self.middleware_chain = MiddlewareChain()
        self._ready = True
        self._enable_tracing = enable_tracing
        
        # 集成追踪
        if enable_tracing:
            try:
                from .reasoning_trace import tracer
                self.tracer = tracer
                self.middleware_chain.add(TracingMiddleware(tracer))
            except ImportError:
                self.tracer = None
        else:
            self.tracer = None
    
    def add_middleware(self, mw: Middleware) -> 'ServiceAgent':
        """添加中间件"""
        self.middleware_chain.add(mw)
        return self
    
    def ready(self) -> bool:
        """检查是否准备好"""
        return self._ready
    
    async def call(self, request: Dict[str, Any]) -> ServiceResult:
        """
        统一调用接口 (Service Trait)
        
        流程:
        1. 中间件前置处理
        2. 提取参数 (Extractor)
        3. 执行业务逻辑
        4. 中间件后置处理
        """
        if not self.ready():
            return ServiceResult.err("Agent not ready")
        
        # 添加agent_name到request
        request = dict(request)
        request['agent_name'] = self.name
        
        # 通过中间件链执行
        return await self.middleware_chain.execute(request, self._handle)
    
    @abstractmethod
    async def _handle(self, request: Dict[str, Any]) -> ServiceResult:
        """子类实现的处理逻辑"""
        pass
    
    async def extract_params(self, request: Dict[str, Any], *extractors) -> tuple:
        """提取多个参数"""
        return tuple(await ext.from_request(request) for ext in extractors)
    
    def trace_step(self, task_id: str, step_type, content: str, metadata: Optional[Dict] = None):
        """手动添加推理步骤 (供子类使用)"""
        if self.tracer and task_id:
            from .reasoning_trace import ReasoningStepType
            self.tracer.add_step(
                task_id=task_id,
                step_type=step_type if isinstance(step_type, ReasoningStepType) else ReasoningStepType.EXECUTE,
                content=content,
                agent_name=self.name,
                metadata=metadata or {}
            )


# 导出
__all__ = [
    # Service Trait
    'Service',
    'ServiceResult',
    
    # Extractor
    'FromRequest',
    'TaskType',
    'TaskContent', 
    'ContextExtractor',
    
    # 共享状态
    'SharedData',
    'SharedStateManager',
    
    # 中间件
    'Middleware',
    'LoggingMiddleware',
    'MetricsMiddleware',
    'TracingMiddleware',
    'MiddlewareChain',
    'RequestContext',
    'ResponseContext',
    
    # 增强Agent
    'ServiceAgent',
]
