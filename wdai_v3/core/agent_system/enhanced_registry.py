"""
Gnet模式集成 - AgentRegistry增强版

集成内容:
1. 负载均衡选择Agent (RoundRobin/LeastLoaded/Weighted/Hash)
2. 非阻塞执行池 (背压控制)
3. 实时负载监控和指标上报
"""

from typing import Dict, List, Optional, Type, Any
import asyncio
import time

from .models import AgentRole, AgentConfig
from .base import BaseAgent
from .load_balancer import (
    LoadBalancingStrategy,
    AgentLoadMetrics,
    LoadBalancer,
    NonBlockingExecutionPool
)


class EnhancedAgentRegistry:
    """
    增强版Agent注册表 (Gnet模式集成)
    
    新增功能:
    - 负载均衡选择 (多种策略)
    - 实时负载监控
    - 非阻塞执行池
    """
    
    def __init__(self, default_strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED):
        self._agents: Dict[str, BaseAgent] = {}
        self._role_index: Dict[AgentRole, List[str]] = {}
        self._load_balancers: Dict[AgentRole, LoadBalancer] = {}
        self._default_strategy = default_strategy
        
        # 全局执行池
        self._global_pool = NonBlockingExecutionPool(
            max_concurrent=20,
            max_queue_size=200,
            nonblocking=True
        )
    
    async def initialize(self):
        """初始化"""
        await self._global_pool.initialize()
    
    def register(self, agent: BaseAgent) -> None:
        """注册Agent"""
        self._agents[agent.name] = agent
        
        # 更新角色索引
        if agent.role not in self._role_index:
            self._role_index[agent.role] = []
        self._role_index[agent.role].append(agent.name)
        
        # 更新负载均衡器
        if agent.role not in self._load_balancers:
            self._load_balancers[agent.role] = LoadBalancer(self._default_strategy)
        self._load_balancers[agent.role].register_agent(agent)
        
        print(f"[Registry] Registered agent: {agent.name} ({agent.role.value})")
    
    def unregister(self, agent_name: str) -> None:
        """注销Agent"""
        if agent_name not in self._agents:
            return
        
        agent = self._agents[agent_name]
        
        # 从角色索引移除
        if agent.role in self._role_index and agent_name in self._role_index[agent.role]:
            self._role_index[agent.role].remove(agent_name)
        
        # 从负载均衡器移除
        if agent.role in self._load_balancers:
            self._load_balancers[agent.role].unregister_agent(agent_name)
        
        del self._agents[agent_name]
        print(f"[Registry] Unregistered agent: {agent_name}")
    
    def get(self, role: AgentRole) -> Optional[BaseAgent]:
        """
        获取Agent (原始方法，保持兼容)
        
        注意: 建议使用select()方法进行负载均衡选择
        """
        agents = self.get_by_role(role)
        if not agents:
            return None
        # 默认返回第一个 (保持原有行为)
        return agents[0]
    
    def select(
        self,
        role: AgentRole,
        task_hint: Optional[str] = None,
        strategy: Optional[LoadBalancingStrategy] = None
    ) -> Optional[BaseAgent]:
        """
        负载均衡选择Agent (Gnet模式)
        
        Args:
            role: Agent角色
            task_hint: 任务提示，用于哈希策略
            strategy: 临时指定策略，None使用默认
        
        Returns:
            选中的Agent，无可用时返回None
        """
        if role not in self._load_balancers:
            return self.get(role)
        
        balancer = self._load_balancers[role]
        
        # 临时切换策略
        if strategy:
            original = balancer.strategy
            balancer.strategy = strategy
            agent = balancer.select_agent(task_hint)
            balancer.strategy = original
            return agent
        
        return balancer.select_agent(task_hint)
    
    def get_by_role(self, role: AgentRole) -> List[BaseAgent]:
        """获取指定角色的所有Agent"""
        names = self._role_index.get(role, [])
        return [self._agents[name] for name in names if name in self._agents]
    
    def list_agents(self) -> List[BaseAgent]:
        """列出所有Agent"""
        return list(self._agents.values())
    
    def list_roles(self) -> List[AgentRole]:
        """列出所有角色类型"""
        return list(self._role_index.keys())
    
    def update_agent_metrics(self, agent_name: str, **kwargs) -> None:
        """更新Agent负载指标"""
        if agent_name not in self._agents:
            return
        
        agent = self._agents[agent_name]
        if agent.role in self._load_balancers:
            self._load_balancers[agent.role].update_metrics(agent_name, **kwargs)
    
    def get_agent_metrics(self, agent_name: str) -> Optional[AgentLoadMetrics]:
        """获取Agent指标"""
        if agent_name not in self._agents:
            return None
        
        agent = self._agents[agent_name]
        if agent.role in self._load_balancers:
            return self._load_balancers[agent.role]._metrics.get(agent_name)
        return None
    
    def get_all_metrics(self) -> Dict[AgentRole, Dict[str, AgentLoadMetrics]]:
        """获取所有Agent指标"""
        return {
            role: balancer.get_all_metrics()
            for role, balancer in self._load_balancers.items()
        }
    
    def get_registry_status(self) -> Dict[str, Any]:
        """获取注册表完整状态"""
        return {
            "total_agents": len(self._agents),
            "role_distribution": {
                role.value: len(names)
                for role, names in self._role_index.items()
            },
            "load_balancers": {
                role.value: balancer.get_balancer_status()
                for role, balancer in self._load_balancers.items()
            },
            "global_pool": self._global_pool.metrics
        }
    
    async def execute_with_load_balancing(
        self,
        role: AgentRole,
        task_hint: Optional[str] = None,
        execute_fn = None,
        *args,
        **kwargs
    ):
        """
        带负载均衡的执行
        
        流程:
        1. 选择最优Agent
        2. 上报开始执行
        3. 执行并计时
        4. 上报结果
        """
        # 1. 选择Agent
        agent = self.select(role, task_hint)
        if not agent:
            raise RuntimeError(f"No available agent for role: {role.value}")
        
        # 2. 上报开始
        self.update_agent_metrics(
            agent.name,
            active_executions=agent.get_statistics().get('active_executions', 0) + 1
        )
        
        start_time = time.time()
        
        try:
            # 3. 执行
            if execute_fn:
                result = await execute_fn(*args, **kwargs)
            else:
                result = None
            
            # 4. 上报成功
            exec_time_ms = (time.time() - start_time) * 1000
            self._record_execution(agent.name, success=True, exec_time_ms=exec_time_ms)
            
            return result
            
        except Exception as e:
            # 4. 上报失败
            exec_time_ms = (time.time() - start_time) * 1000
            self._record_execution(agent.name, success=False, exec_time_ms=exec_time_ms)
            raise
    
    def _record_execution(self, agent_name: str, success: bool, exec_time_ms: float):
        """记录执行结果"""
        if agent_name not in self._agents:
            return
        
        agent = self._agents[agent_name]
        current = agent.get_statistics()
        
        self.update_agent_metrics(
            agent_name,
            active_executions=max(0, current.get('active_executions', 1) - 1),
            total_executions=current.get('total_executions', 0) + 1,
            success_count=current.get('success_count', 0) + (1 if success else 0),
            error_count=current.get('error_count', 0) + (0 if success else 1),
            last_execution_time_ms=exec_time_ms,
            total_execution_time_ms=current.get('total_execution_time_ms', 0) + exec_time_ms
        )


# 全局注册表实例 (向后兼容)
_registry_instance: Optional[EnhancedAgentRegistry] = None


def get_enhanced_registry() -> EnhancedAgentRegistry:
    """获取增强版注册表实例"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = EnhancedAgentRegistry()
    return _registry_instance


def reset_registry():
    """重置注册表 (测试用)"""
    global _registry_instance
    _registry_instance = None


__all__ = [
    'EnhancedAgentRegistry',
    'get_enhanced_registry',
    'reset_registry'
]
