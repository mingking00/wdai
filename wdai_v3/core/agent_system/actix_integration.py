"""
Actix-web模式集成 - 增强版Agent基类

将Service Trait集成到现有BaseAgent中
"""

import asyncio
from typing import Dict, Any, Optional

from .base import BaseAgent, AgentConfig, AgentResult, SubTask, NarrowContext
from .service_trait import (
    ServiceResult,
    ServiceAgent,
    SharedStateManager,
    MiddlewareChain,
    Middleware,
    TaskType,
    TaskContent,
    ContextExtractor,
)


class ActixStyleAgent(BaseAgent, ServiceAgent):
    """
    Actix-web风格Agent
    
    集成:
    - Service Trait (统一call接口)
    - Extractor模式 (自动参数提取)
    - 中间件链 (日志、监控、重试)
    - 共享状态 (跨Agent数据)
    """
    
    def __init__(
        self,
        config: AgentConfig,
        shared_state: Optional[SharedStateManager] = None
    ):
        # 初始化BaseAgent部分
        from .base import ResourceLimits, ExecutionPool
        super(BaseAgent, self).__init__(config)
        self.config = config
        self.role = config.role
        self.name = config.name
        self.expertise = config.expertise
        self._pool = ExecutionPool(ResourceLimits())
        self._execution_count = 0
        self._success_count = 0
        self._total_execution_time_ms = 0
        self._error_count = 0
        self._log_ctx = {'agent': self.name, 'role': self.role.value}
        
        # 初始化ServiceAgent部分
        ServiceAgent.__init__(self, config.name, shared_state)
    
    async def execute(self, subtask: SubTask, context: NarrowContext) -> AgentResult:
        """
        标准执行接口 (BaseAgent)
        
        内部使用Service Trait模式
        """
        # 构建请求
        request = {
            'subtask': subtask,
            'context': context,
            'task_type': subtask.type,
            'content': subtask.description,
            'task_id': subtask.id,
            'parent_id': subtask.parent_id,
        }
        
        # 使用Service Trait调用
        result = await self.call(request)
        
        # 转换回AgentResult
        if result.success:
            return AgentResult(
                success=True,
                output=result.data,
                execution_time_ms=0  # 由中间件记录
            )
        else:
            return AgentResult(
                success=False,
                error_message=result.error
            )
    
    async def _handle(self, request: Dict[str, Any]) -> ServiceResult:
        """
        子类实现的具体处理逻辑
        
        使用Extractor模式提取参数:
        - TaskType: 任务类型
        - TaskContent: 任务内容  
        - ContextExtractor: 上下文信息
        """
        try:
            # 提取参数
            subtask = request.get('subtask')
            context = request.get('context')
            
            if not subtask or not context:
                return ServiceResult.err("Missing subtask or context")
            
            # 调用子类的process方法
            result = await self.process(subtask, context)
            
            return ServiceResult.ok(result)
            
        except Exception as e:
            return ServiceResult.err(str(e))
    
    async def process(self, subtask: SubTask, context: NarrowContext) -> Any:
        """
        子类必须实现的业务逻辑
        
        Args:
            subtask: 子任务
            context: 窄上下文
        
        Returns:
            处理结果 (任意类型)
        """
        raise NotImplementedError("Subclasses must implement process()")


class SharedStateMixin:
    """
    共享状态Mixin
    
    为Agent提供访问共享状态的能力
    """
    
    _global_state_manager: Optional[SharedStateManager] = None
    
    @classmethod
    def init_global_state(cls) -> SharedStateManager:
        """初始化全局共享状态"""
        if cls._global_state_manager is None:
            cls._global_state_manager = SharedStateManager()
        return cls._global_state_manager
    
    @classmethod
    def get_global_state(cls, name: str) -> Optional[Any]:
        """获取全局共享状态"""
        manager = cls.init_global_state()
        shared = manager.get(name)
        return shared.get() if shared else None
    
    @classmethod
    def update_global_state(cls, name: str, updater):
        """更新全局共享状态"""
        manager = cls.init_global_state()
        shared = manager.get(name)
        if shared:
            with shared.write() as data:
                updater(data)


class EnhancedSubtaskExtractor:
    """
    子任务专用Extractor
    
    从请求中提取SubTask和NarrowContext
    """
    
    @staticmethod
    async def extract_subtask(request: Dict) -> Optional[SubTask]:
        """提取SubTask"""
        return request.get('subtask')
    
    @staticmethod
    async def extract_context(request: Dict) -> Optional[NarrowContext]:
        """提取NarrowContext"""
        return request.get('context')
    
    @staticmethod
    async def extract_metadata(request: Dict) -> Dict[str, Any]:
        """提取元数据"""
        ctx = await ContextExtractor.from_request(request)
        return ctx.metadata


# 导出
__all__ = [
    'ActixStyleAgent',
    'SharedStateMixin',
    'EnhancedSubtaskExtractor',
]
