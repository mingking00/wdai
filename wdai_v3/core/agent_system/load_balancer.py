"""
Gnet模式应用 - 负载均衡与Agent选择

从Gnet学习的关键模式:
1. 负载均衡策略: RoundRobin, LeastConnections, SourceAddrHash
2. 负载监控: 跟踪每个eventloop的连接数和状态
3. 非阻塞提交: 避免资源堆积

应用到wdai:
- AgentRegistry添加负载均衡选择
- 跟踪每个Agent的执行负载
- 支持多种选择策略
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Callable
import time
from dataclasses import dataclass, field


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = auto()           # 轮询 - 简单均匀
    LEAST_LOADED = auto()          # 最少负载 - 当前最优
    WEIGHTED_RESPONSE = auto()     # 加权响应 - 考虑历史性能
    HASH_BASED = auto()            # 哈希 - 相同任务路由到同一Agent


@dataclass
class AgentLoadMetrics:
    """Agent负载指标"""
    agent_name: str
    agent_role: str
    
    # 当前状态
    active_executions: int = 0
    queued_tasks: int = 0
    
    # 历史统计
    total_executions: int = 0
    success_count: int = 0
    error_count: int = 0
    
    # 性能指标
    total_execution_time_ms: float = 0.0
    avg_response_time_ms: float = 0.0
    last_execution_time_ms: float = 0.0
    
    # 时间戳
    last_updated: float = field(default_factory=time.time)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_executions == 0:
            return 1.0
        return self.success_count / self.total_executions
    
    @property
    def current_load(self) -> int:
        """当前总负载 (活跃 + 队列)"""
        return self.active_executions + self.queued_tasks
    
    @property
    def is_overloaded(self) -> bool:
        """是否过载"""
        return self.queued_tasks > 10 or self.active_executions > 5
    
    @property
    def health_score(self) -> float:
        """健康评分 (0-1, 越高越好)"""
        if self.is_overloaded:
            return 0.0
        
        # 基于成功率、响应时间、当前负载计算
        score = self.success_rate
        
        # 响应时间惩罚 (假设100ms为理想值)
        if self.avg_response_time_ms > 0:
            response_penalty = min(0.3, self.avg_response_time_ms / 1000)
            score -= response_penalty
        
        # 负载惩罚
        load_penalty = min(0.3, self.current_load / 10)
        score -= load_penalty
        
        return max(0.0, score)


class LoadBalancer:
    """
    Agent负载均衡器 (Gnet模式)
    
    支持多种策略:
    - ROUND_ROBIN: 轮询，简单均匀
    - LEAST_LOADED: 最少负载，当前最优
    - WEIGHTED_RESPONSE: 加权响应，考虑历史性能
    - HASH_BASED: 基于任务哈希，相同任务路由到同一Agent
    """
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED):
        self.strategy = strategy
        self._agents: Dict[str, 'BaseAgent'] = {}
        self._metrics: Dict[str, AgentLoadMetrics] = {}
        self._round_robin_index = 0
    
    def register_agent(self, agent: 'BaseAgent') -> None:
        """注册Agent"""
        self._agents[agent.name] = agent
        self._metrics[agent.name] = AgentLoadMetrics(
            agent_name=agent.name,
            agent_role=agent.role.value
        )
    
    def unregister_agent(self, agent_name: str) -> None:
        """注销Agent"""
        self._agents.pop(agent_name, None)
        self._metrics.pop(agent_name, None)
    
    def update_metrics(self, agent_name: str, **kwargs) -> None:
        """更新Agent指标"""
        if agent_name in self._metrics:
            metrics = self._metrics[agent_name]
            for key, value in kwargs.items():
                if hasattr(metrics, key):
                    setattr(metrics, key, value)
            metrics.last_updated = time.time()
            
            # 重新计算平均响应时间
            if metrics.total_executions > 0:
                metrics.avg_response_time_ms = (
                    metrics.total_execution_time_ms / metrics.total_executions
                )
    
    def select_agent(self, task_hint: Optional[str] = None) -> Optional['BaseAgent']:
        """
        选择最优Agent
        
        Args:
            task_hint: 任务提示，用于HASH_BASED策略
        
        Returns:
            选中的Agent，无可用时返回None
        """
        if not self._agents:
            return None
        
        # 过滤掉过载的Agent
        available = [
            (name, agent) for name, agent in self._agents.items()
            if not self._metrics[name].is_overloaded
        ]
        
        if not available:
            # 全部过载，选负载最低的
            available = list(self._agents.items())
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available)
        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._select_least_loaded(available)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RESPONSE:
            return self._select_weighted(available)
        elif self.strategy == LoadBalancingStrategy.HASH_BASED:
            return self._select_hash_based(available, task_hint)
        
        return self._select_least_loaded(available)
    
    def _select_round_robin(self, available: List[tuple]) -> Optional['BaseAgent']:
        """轮询选择"""
        if not available:
            return None
        idx = self._round_robin_index % len(available)
        self._round_robin_index += 1
        return available[idx][1]
    
    def _select_least_loaded(self, available: List[tuple]) -> Optional['BaseAgent']:
        """最少负载选择 (Gnet LeastConnections模式)"""
        if not available:
            return None
        
        # 找负载最小的
        min_load = float('inf')
        selected = None
        
        for name, agent in available:
            metrics = self._metrics[name]
            if metrics.current_load < min_load:
                min_load = metrics.current_load
                selected = agent
        
        return selected
    
    def _select_weighted(self, available: List[tuple]) -> Optional['BaseAgent']:
        """加权选择 (考虑健康评分)"""
        if not available:
            return None
        
        # 按健康评分排序
        scored = [
            (agent, self._metrics[name].health_score)
            for name, agent in available
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[0][0]
    
    def _select_hash_based(self, available: List[tuple], task_hint: Optional[str]) -> Optional['BaseAgent']:
        """哈希选择 (Gnet SourceAddrHash模式)"""
        if not available:
            return None
        if not task_hint:
            return self._select_round_robin(available)
        
        # 简单哈希
        hash_val = hash(task_hint)
        idx = abs(hash_val) % len(available)
        return available[idx][1]
    
    def get_all_metrics(self) -> Dict[str, AgentLoadMetrics]:
        """获取所有Agent指标"""
        return self._metrics.copy()
    
    def get_balancer_status(self) -> Dict:
        """获取均衡器状态"""
        total_active = sum(m.active_executions for m in self._metrics.values())
        total_queued = sum(m.queued_tasks for m in self._metrics.values())
        
        return {
            "strategy": self.strategy.name,
            "registered_agents": len(self._agents),
            "total_active_executions": total_active,
            "total_queued_tasks": total_queued,
            "agents_status": {
                name: {
                    "load": metrics.current_load,
                    "health": round(metrics.health_score, 2),
                    "avg_response_ms": round(metrics.avg_response_time_ms, 2)
                }
                for name, metrics in self._metrics.items()
            }
        }


class NonBlockingExecutionPool:
    """
    非阻塞执行池 (Gnet ants模式)
    
    特点:
    - 非阻塞提交: 满时立即返回错误，不堆积
    - 背压控制: 自动拒绝超额请求
    - 指标追踪: 实时监控池状态
    """
    
    def __init__(
        self,
        max_concurrent: int = 10,
        max_queue_size: int = 100,
        nonblocking: bool = True
    ):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.nonblocking = nonblocking
        
        self._active_count = 0
        self._queued_count = 0
        self._completed_count = 0
        self._rejected_count = 0
        
        self._lock = None  # 使用asyncio.Lock
    
    async def initialize(self):
        """初始化异步锁"""
        import asyncio
        self._lock = asyncio.Lock()
    
    async def acquire_slot(self, timeout: Optional[float] = None) -> bool:
        """
        获取执行槽位
        
        Returns:
            True: 获取成功
            False: 非阻塞模式下池满，或超时
        """
        import asyncio
        
        if self._lock is None:
            await self.initialize()
        
        async with self._lock:
            # 检查是否可以直接执行
            if self._active_count < self.max_concurrent:
                self._active_count += 1
                return True
            
            # 检查队列
            if self._queued_count < self.max_queue_size:
                self._queued_count += 1
                return True
            
            # 池满
            if self.nonblocking:
                self._rejected_count += 1
                return False
        
        # 阻塞模式: 等待槽位
        if timeout:
            try:
                await asyncio.wait_for(self._wait_for_slot(), timeout=timeout)
                return True
            except asyncio.TimeoutError:
                return False
        
        await self._wait_for_slot()
        return True
    
    async def _wait_for_slot(self):
        """等待槽位可用"""
        import asyncio
        while True:
            async with self._lock:
                if self._active_count < self.max_concurrent:
                    self._active_count += 1
                    if self._queued_count > 0:
                        self._queued_count -= 1
                    return
            await asyncio.sleep(0.01)  # 10ms轮询
    
    async def release_slot(self):
        """释放执行槽位"""
        if self._lock is None:
            return
        
        async with self._lock:
            if self._active_count > 0:
                self._active_count -= 1
                self._completed_count += 1
    
    @property
    def metrics(self) -> Dict:
        """池指标"""
        return {
            "active": self._active_count,
            "queued": self._queued_count,
            "completed": self._completed_count,
            "rejected": self._rejected_count,
            "available_slots": self.max_concurrent - self._active_count,
            "utilization": self._active_count / self.max_concurrent if self.max_concurrent > 0 else 0
        }
    
    @property
    def is_overloaded(self) -> bool:
        """是否过载"""
        return (
            self._active_count >= self.max_concurrent and
            self._queued_count >= self.max_queue_size
        )


# 导出
__all__ = [
    'LoadBalancingStrategy',
    'AgentLoadMetrics',
    'LoadBalancer',
    'NonBlockingExecutionPool'
]
