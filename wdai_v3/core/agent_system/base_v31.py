"""
wdai v3.1 - Base Agent (Rathole模式增强)
改进: 指数退避、并发控制、结构化日志
"""

import asyncio
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime

from .models import (
    AgentConfig, AgentRole, AgentResult,
    SubTask, NarrowContext, TaskStatus
)

logger = logging.getLogger(__name__)


@dataclass
class ExponentialBackoff:
    """
    指数退避策略 (来自Rathole模式)
    
    避免雪崩效应，资源不足时自动退避
    """
    initial_interval: float = 1.0      # 初始间隔(秒)
    max_interval: float = 60.0         # 最大间隔(秒)
    multiplier: float = 2.0            # 乘数
    max_elapsed_time: Optional[float] = None  # 最大总时间
    
    def __post_init__(self):
        self._current_interval = self.initial_interval
        self._start_time = time.time()
        self._attempt = 0
    
    def next_backoff(self) -> Optional[float]:
        """获取下一次退避时间，返回None表示已超过最大时间"""
        if self.max_elapsed_time:
            elapsed = time.time() - self._start_time
            if elapsed >= self.max_elapsed_time:
                return None
        
        backoff = self._current_interval
        self._current_interval = min(
            self._current_interval * self.multiplier,
            self.max_interval
        )
        self._attempt += 1
        return backoff
    
    def reset(self):
        """重置退避状态"""
        self._current_interval = self.initial_interval
        self._start_time = time.time()
        self._attempt = 0
    
    @property
    def attempt(self) -> int:
        return self._attempt


@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_concurrent_executions: int = 5     # 最大并发执行数
    max_queue_size: int = 100              # 最大队列大小
    execution_timeout_seconds: int = 300   # 执行超时
    

class ExecutionPool:
    """
    执行池 (Worker Pool模式)
    
    限制并发数，防止资源耗尽
    """
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self._semaphore = asyncio.Semaphore(limits.max_concurrent_executions)
        self._queue_size = 0
        self._metrics = {
            'active': 0,
            'queued': 0,
            'completed': 0,
            'failed': 0
        }
    
    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """获取执行槽位"""
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=timeout
            )
            self._metrics['active'] += 1
            return True
        except asyncio.TimeoutError:
            return False
    
    def release(self, success: bool = True):
        """释放执行槽位"""
        self._semaphore.release()
        self._metrics['active'] -= 1
        if success:
            self._metrics['completed'] += 1
        else:
            self._metrics['failed'] += 1
    
    @property
    def metrics(self) -> Dict[str, int]:
        return self._metrics.copy()
    
    @property
    def available_slots(self) -> int:
        return self.limits.max_concurrent_executions - self._metrics['active']


class BaseAgent(ABC):
    """
    Agent抽象基类 (v3.1增强版)
    
    改进:
    1. 指数退避重试 (Rathole模式)
    2. 执行池限制并发
    3. 结构化日志追踪
    4. 资源使用监控
    """
    
    def __init__(self, config: AgentConfig, limits: Optional[ResourceLimits] = None):
        self.config = config
        self.role = config.role
        self.name = config.name
        self.expertise = config.expertise
        
        # 执行池 (Rathole Worker Pool模式)
        self._pool = ExecutionPool(limits or ResourceLimits())
        
        # 统计
        self._execution_count = 0
        self._success_count = 0
        self._total_execution_time_ms = 0
        self._error_count = 0
        
        # 日志上下文
        self._log_ctx = {'agent': self.name, 'role': self.role.value}
    
    @abstractmethod
    async def execute(self, subtask: SubTask, context: NarrowContext) -> AgentResult:
        """执行子任务"""
        pass
    
    @abstractmethod
    def can_handle(self, task_type: str) -> bool:
        """检查是否能处理该任务类型"""
        pass
    
    async def run_with_retry(
        self,
        subtask: SubTask,
        context: NarrowContext
    ) -> AgentResult:
        """
        带重试的执行 (指数退避增强版)
        
        改进:
        - 使用ExponentialBackoff替代简单sleep
        - 区分可重试错误和致命错误
        - 结构化日志记录每次尝试
        """
        backoff = ExponentialBackoff(
            initial_interval=1.0,
            max_interval=10.0,
            max_elapsed_time=self.config.timeout_seconds * 2
        )
        
        last_error = None
        
        # 获取执行槽位
        if not await self._pool.acquire(timeout=30.0):
            logger.warning(f"获取执行槽位超时", extra=self._log_ctx)
            return AgentResult(
                success=False,
                error_message="系统繁忙，请稍后重试"
            )
        
        try:
            while True:
                attempt = backoff.attempt
                start_time = time.time()
                
                try:
                    logger.info(
                        f"开始执行 (尝试 {attempt + 1}/{self.config.max_retries + 1})",
                        extra={**self._log_ctx, 'attempt': attempt, 'task_id': subtask.id}
                    )
                    
                    # 设置超时
                    result = await asyncio.wait_for(
                        self.execute(subtask, context),
                        timeout=self.config.timeout_seconds
                    )
                    
                    execution_time = int((time.time() - start_time) * 1000)
                    result.execution_time_ms = execution_time
                    
                    # 更新统计
                    self._update_stats(result.success, execution_time)
                    
                    if result.success:
                        logger.info(
                            f"执行成功 ({execution_time}ms)",
                            extra={**self._log_ctx, 'duration_ms': execution_time}
                        )
                    else:
                        logger.warning(
                            f"执行失败: {result.error_message}",
                            extra={**self._log_ctx}
                        )
                    
                    self._pool.release(result.success)
                    return result
                    
                except asyncio.TimeoutError:
                    last_error = f"执行超时 ({self.config.timeout_seconds}秒)"
                    logger.warning(
                        f"第{attempt + 1}次尝试超时",
                        extra={**self._log_ctx, 'attempt': attempt}
                    )
                    
                    if attempt >= self.config.max_retries:
                        break
                    
                    delay = backoff.next_backoff()
                    if delay is None:
                        break
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    last_error = str(e)
                    self._error_count += 1
                    
                    # 判断是否是可重试错误
                    if self._is_retryable_error(e) and attempt < self.config.max_retries:
                        logger.exception(
                            f"第{attempt + 1}次尝试异常，准备重试",
                            extra={**self._log_ctx}
                        )
                        delay = backoff.next_backoff()
                        if delay:
                            await asyncio.sleep(delay)
                            continue
                    else:
                        logger.exception(
                            f"执行异常 (不可重试)",
                            extra={**self._log_ctx}
                        )
                        self._pool.release(False)
                        raise
            
            # 所有重试都失败
            self._pool.release(False)
            return AgentResult(
                success=False,
                error_message=f"{self.name} 执行失败 (重试{backoff.attempt}次): {last_error}"
            )
            
        except Exception:
            self._pool.release(False)
            raise
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        判断错误是否可重试
        
        可重试: 网络超时、资源暂时不可用
        不可重试: 语法错误、权限不足
        """
        retryable = [
            'timeout', 'connection', 'temporarily unavailable',
            'rate limit', 'resource exhausted'
        ]
        error_str = str(error).lower()
        return any(r in error_str for r in retryable)
    
    def _update_stats(self, success: bool, execution_time_ms: int):
        """更新执行统计"""
        self._execution_count += 1
        self._total_execution_time_ms += execution_time_ms
        if success:
            self._success_count += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息 (增强版)"""
        avg_time = (self._total_execution_time_ms / self._execution_count 
                   if self._execution_count > 0 else 0)
        success_rate = (self._success_count / self._execution_count * 100 
                       if self._execution_count > 0 else 0)
        
        return {
            "name": self.name,
            "role": self.role.value,
            "expertise": self.expertise,
            "execution_count": self._execution_count,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "success_rate": f"{success_rate:.1f}%",
            "avg_execution_time_ms": int(avg_time),
            "pool_metrics": self._pool.metrics,
            "available_slots": self._pool.available_slots
        }
    
    def _build_system_prompt(self, context: NarrowContext) -> str:
        """构建系统提示"""
        base_prompt = f"""你是 {self.name}，一个专业的AI助手。

角色: {self.role.value}
专长: {', '.join(self.expertise)}

{self.config.system_prompt}

重要原则:
1. 专注于你的专业领域
2. 只处理分配给你的任务
3. 如需其他专业帮助，明确说明
4. 保持输出简洁、结构化
"""
        return base_prompt
    
    def _build_task_prompt(self, subtask: SubTask, context: NarrowContext) -> str:
        """构建任务提示"""
        return f"""{context.to_prompt_context()}

请完成上述任务，并返回结构化的结果。
"""


class AgentRegistry:
    """Agent注册表 (增强版)"""
    
    def __init__(self):
        self._agents: Dict[AgentRole, BaseAgent] = {}
        self._handlers: Dict[str, List[BaseAgent]] = {}
        self._registry_metrics = {
            'registered': 0,
            'total_executions': 0
        }
    
    def register(self, agent: BaseAgent):
        """注册Agent"""
        self._agents[agent.role] = agent
        self._registry_metrics['registered'] += 1
        logger.info(
            f"Agent已注册: {agent.name} ({agent.role.value})",
            extra={'agent': agent.name, 'role': agent.role.value}
        )
    
    def get(self, role: AgentRole) -> Optional[BaseAgent]:
        """获取Agent"""
        return self._agents.get(role)
    
    def find_agent_for_task(self, task_type: str) -> Optional[BaseAgent]:
        """查找能处理该任务的Agent"""
        for agent in self._agents.values():
            if agent.can_handle(task_type):
                return agent
        return None
    
    def list_agents(self) -> List[BaseAgent]:
        """列出所有Agent"""
        return list(self._agents.values())
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有Agent统计"""
        return {
            agent.name: agent.get_statistics()
            for agent in self._agents.values()
        }
    
    def get_registry_metrics(self) -> Dict[str, Any]:
        """获取注册表指标"""
        return self._registry_metrics.copy()


# 全局注册表
_default_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """获取默认Agent注册表"""
    global _default_registry
    if _default_registry is None:
        _default_registry = AgentRegistry()
    return _default_registry


def register_agent(agent: BaseAgent):
    """便捷函数：注册Agent"""
    get_agent_registry().register(agent)


def get_agent(role: AgentRole) -> Optional[BaseAgent]:
    """便捷函数：获取Agent"""
    return get_agent_registry().get(role)
