"""
wdai v3.0 - Message Bus
消息总线模块 - Phase 1 Facade

提供统一的消息系统接口
"""

import asyncio
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

from .message import (
    Message, 
    MessageType, 
    MessagePool,
    create_message
)
from .router import PubSubRouter, AgentProxy


class MessageBus:
    """
    消息总线门面类
    
    提供统一的消息系统接口，简化使用
    """
    
    _instance: Optional["MessageBus"] = None
    _allow_new_instance = False  # 测试用：允许创建新实例
    
    def __new__(cls, *args, **kwargs):
        """单例模式（测试时可覆盖）"""
        if cls._allow_new_instance or cls._instance is None:
            instance = super().__new__(cls)
            instance._initialized = False
            if not cls._allow_new_instance:
                cls._instance = instance
            return instance
        return cls._instance
    
    def __init__(self, storage_path: str = None, max_queue_size: int = 10000):
        if self._initialized:
            return
        
        if storage_path is None:
            storage_path = Path.home() / ".openclaw" / "workspace" / ".v3" / "messages"
        
        self._pool = MessagePool(str(storage_path))
        self._router = PubSubRouter(self._pool, max_queue_size=max_queue_size)
        self._initialized = True
        self._started = False
    
    @classmethod
    def _reset_for_testing(cls):
        """重置单例（仅用于测试）"""
        cls._instance = None
        cls._allow_new_instance = True
    
    @classmethod
    def _restore_singleton(cls):
        """恢复单例模式（仅用于测试）"""
        cls._allow_new_instance = False
    
    async def start(self):
        """启动消息总线"""
        if not self._started:
            await self._router.start()
            self._started = True
    
    async def stop(self):
        """停止消息总线"""
        if self._started:
            # 优雅关闭路由器
            await self._router.stop(timeout=5.0)
            # 刷新存储
            await self._pool.storage.flush()
            self._started = False
    
    # ============ 发布订阅接口 ============
    
    async def publish(self, message: Message) -> str:
        """
        发布消息
        
        Args:
            message: 消息对象
            
        Returns:
            message_id: 消息ID
        """
        return await self._router.publish(message)
    
    async def send(self,
                   content: Dict[str, Any],
                   sender: str,
                   recipients: List[str],
                   msg_type: MessageType = MessageType.EVENT,
                   task_id: str = None,
                   priority: int = 0) -> str:
        """
        便捷发送消息
        
        Args:
            content: 消息内容
            sender: 发送者ID
            recipients: 接收者列表
            msg_type: 消息类型
            task_id: 关联任务ID
            priority: 优先级
            
        Returns:
            message_id: 消息ID
        """
        message = create_message(
            msg_type=msg_type,
            content=content,
            sender=sender,
            recipients=recipients,
            task_id=task_id,
            priority=priority
        )
        return await self.publish(message)
    
    def subscribe(self,
                  agent_id: str,
                  message_types: List[MessageType],
                  filter_fn: Callable[[Message], bool] = None,
                  priority: int = 0) -> str:
        """
        订阅消息
        
        Args:
            agent_id: Agent ID
            message_types: 消息类型列表
            filter_fn: 过滤器函数
            priority: 优先级
            
        Returns:
            subscription_id: 订阅ID
        """
        return self._router.subscribe(
            agent_id=agent_id,
            message_types=message_types,
            filter_fn=filter_fn,
            priority=priority
        )
    
    def unsubscribe(self, agent_id: str) -> bool:
        """
        取消订阅
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功
        """
        return self._router.unsubscribe(agent_id)
    
    # ============ 查询接口 ============
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """获取消息"""
        return self._pool.get_message(message_id)
    
    def query_messages(self,
                       message_type: MessageType = None,
                       sender: str = None,
                       recipient: str = None,
                       task_id: str = None,
                       limit: int = None) -> List[Message]:
        """查询消息"""
        return self._pool.query(
            message_type=message_type,
            sender=sender,
            recipient=recipient,
            task_id=task_id,
            limit=limit
        )
    
    def get_task_history(self, task_id: str) -> List[Message]:
        """获取任务历史"""
        return self._pool.get_task_history(task_id)
    
    # ============ 统计接口 ============
    
    def register_handler(self, agent_id: str, handler: Callable[[Message], None]):
        """
        注册消息处理器
        
        Args:
            agent_id: Agent ID
            handler: 消息处理函数
        """
        self._router.register_handler(agent_id, handler)
    
    def unregister_handler(self, agent_id: str) -> bool:
        """
        注销消息处理器
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功注销
        """
        return self._router.unregister_handler(agent_id)
    
    # ============ 统计接口 ============
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "pool": self._pool.get_statistics(),
            "router": self._router.get_statistics()
        }
    
    # ============ Agent代理接口 ============
        """获取统计信息"""
        return {
            "pool": self._pool.get_statistics(),
            "router": self._router.get_statistics()
        }
    
    # ============ Agent代理接口 ============
    
    def create_agent_proxy(self,
                          agent_id: str,
                          message_handler: Callable[[Message], None]) -> AgentProxy:
        """
        创建Agent代理
        
        Args:
            agent_id: Agent ID
            message_handler: 消息处理函数
            
        Returns:
            AgentProxy实例
        """
        return AgentProxy(agent_id, self._router, message_handler)


# 便捷函数
def get_message_bus(storage_path: str = None) -> MessageBus:
    """获取消息总线实例（单例）"""
    return MessageBus(storage_path)


# 导出
__all__ = [
    "MessageBus",
    "get_message_bus",
    "Message",
    "MessageType",
    "MessagePool",
    "PubSubRouter",
    "AgentProxy",
    "create_message"
]
