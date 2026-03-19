"""
wdai v3.0 - Base Agent
Phase 3: Agent专业化系统 - Agent基类
"""

import asyncio
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .models import (
    AgentConfig, AgentRole, AgentResult,
    SubTask, NarrowContext, TaskStatus
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Agent抽象基类
    
    所有专业Agent必须继承此类
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.role = config.role
        self.name = config.name
        self.expertise = config.expertise
        self._execution_count = 0
        self._success_count = 0
        self._total_execution_time_ms = 0
    
    @abstractmethod
    async def execute(self, subtask: SubTask, context: NarrowContext) -> AgentResult:
        """
        执行子任务
        
        Args:
            subtask: 子任务定义
            context: 窄上下文 (Fresh Eyes)
        
        Returns:
            Agent执行结果
        """
        pass
    
    @abstractmethod
    def can_handle(self, task_type: str) -> bool:
        """
        检查是否能处理该任务类型
        
        Args:
            task_type: 任务类型字符串
            
        Returns:
            是否能处理
        """
        pass
    
    async def run_with_retry(
        self,
        subtask: SubTask,
        context: NarrowContext
    ) -> AgentResult:
        """
        带重试的执行
        
        Args:
            subtask: 子任务
            context: 上下文
            
        Returns:
            执行结果
        """
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            start_time = time.time()
            
            try:
                # 设置超时
                result = await asyncio.wait_for(
                    self.execute(subtask, context),
                    timeout=self.config.timeout_seconds
                )
                
                execution_time = int((time.time() - start_time) * 1000)
                result.execution_time_ms = execution_time
                
                # 更新统计
                self._execution_count += 1
                self._total_execution_time_ms += execution_time
                if result.success:
                    self._success_count += 1
                
                return result
                
            except asyncio.TimeoutError:
                last_error = f"执行超时 ({self.config.timeout_seconds}秒)"
                logger.warning(f"{self.name} 第{attempt+1}次尝试超时")
                
                if attempt < self.config.max_retries:
                    delay = min(2 ** attempt, 10)  # 指数退避，最大10秒
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                last_error = str(e)
                logger.exception(f"{self.name} 执行异常")
                
                if attempt < self.config.max_retries:
                    delay = min(2 ** attempt, 10)
                    await asyncio.sleep(delay)
        
        # 所有重试都失败
        return AgentResult(
            success=False,
            error_message=f"{self.name} 执行失败 (重试{self.config.max_retries}次): {last_error}"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
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
            "success_rate": f"{success_rate:.1f}%",
            "avg_execution_time_ms": int(avg_time)
        }
    
    def _build_system_prompt(self, context: NarrowContext) -> str:
        """
        构建系统提示
        
        Args:
            context: 窄上下文
            
        Returns:
            系统提示字符串
        """
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
        """
        构建任务提示
        
        Args:
            subtask: 子任务
            context: 窄上下文
            
        Returns:
            任务提示字符串
        """
        return f"""{context.to_prompt_context()}

请完成上述任务，并返回结构化的结果。
"""


class AgentRegistry:
    """Agent注册表"""
    
    def __init__(self):
        self._agents: Dict[AgentRole, BaseAgent] = {}
        self._handlers: Dict[str, List[BaseAgent]] = {}  # task_type -> agents
    
    def register(self, agent: BaseAgent):
        """注册Agent"""
        self._agents[agent.role] = agent
        logger.info(f"Agent已注册: {agent.name} ({agent.role.value})")
    
    def get(self, role: AgentRole) -> Optional[BaseAgent]:
        """获取Agent"""
        return self._agents.get(role)
    
    def find_agent_for_task(self, task_type: str) -> Optional[BaseAgent]:
        """
        查找能处理该任务的Agent
        
        按优先级:
        1. 专门处理该类型的Agent
        2. 通用Agent
        """
        # 先找专门处理的
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
