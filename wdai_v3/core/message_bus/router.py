"""
wdai v3.0 - Pub/Sub Router
发布-订阅路由器 - Phase 1 实现
"""

import asyncio
from typing import Dict, List, Set, Callable, Optional, Any
from dataclasses import dataclass, field
import uuid

from .message import Message, MessageType, MessagePool


@dataclass
class Subscription:
    """订阅信息"""
    id: str
    agent_id: str
    message_types: Set[MessageType]
    filter_fn: Optional[Callable[[Message], bool]] = None
    priority: int = 0  # 优先级，数字越大优先级越高


class PubSubRouter:
    """
    发布-订阅路由器
    
    负责将消息路由到对应的订阅者
    支持消息过滤和优先级处理
    """
    
    def __init__(self, message_pool: MessagePool, max_queue_size: int = 10000):
        self.message_pool = message_pool
        
        # 订阅者注册表
        # agent_id -> Subscription
        self._subscriptions: Dict[str, Subscription] = {}
        
        # 消息处理器注册表
        # agent_id -> handler function
        self._handlers: Dict[str, Callable[[Message], None]] = {}
        
        # 按消息类型索引
        # MessageType -> Set[agent_id]
        self._type_index: Dict[MessageType, Set[str]] = {
            msg_type: set() for msg_type in MessageType
        }
        
        # 消息队列（用于异步处理）
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._max_queue_size = max_queue_size
        self._processing = False
        self._processor_task: Optional[asyncio.Task] = None
        self._dropped_messages = 0  # 统计丢弃的消息
    
    async def start(self):
        """启动路由器"""
        if not self._processing:
            self._processing = True
            self._processor_task = asyncio.create_task(self._process_messages())
    
    async def stop(self, timeout: float = 5.0):
        """
        停止路由器
        
        会尝试处理完队列中的消息再停止
        
        Args:
            timeout: 等待处理完消息的超时时间（秒）
        """
        import logging
        logger = logging.getLogger(__name__)
        
        self._processing = False
        
        # 等待队列中的消息处理完
        if not self._message_queue.empty():
            logger.info(f"Processing {self._message_queue.qsize()} remaining messages...")
            try:
                await asyncio.wait_for(
                    self._drain_queue(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for queue to drain, {self._message_queue.qsize()} messages remaining")
        
        # 取消处理器任务
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
    
    async def _drain_queue(self):
        """处理队列中剩余的消息"""
        while not self._message_queue.empty():
            try:
                message = self._message_queue.get_nowait()
                await self._route_message(message)
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error draining message: {e}")
    
    def subscribe(self,
                  agent_id: str,
                  message_types: List[MessageType],
                  filter_fn: Callable[[Message], bool] = None,
                  priority: int = 0) -> str:
        """
        订阅消息
        
        Args:
            agent_id: Agent唯一标识
            message_types: 感兴趣的消息类型列表
            filter_fn: 可选的消息过滤器
            priority: 订阅优先级
            
        Returns:
            subscription_id: 订阅ID
        """
        subscription_id = f"sub_{agent_id}_{uuid.uuid4().hex[:8]}"
        
        subscription = Subscription(
            id=subscription_id,
            agent_id=agent_id,
            message_types=set(message_types),
            filter_fn=filter_fn,
            priority=priority
        )
        
        # 注册订阅
        self._subscriptions[agent_id] = subscription
        
        # 更新类型索引
        for msg_type in message_types:
            self._type_index[msg_type].add(agent_id)
        
        return subscription_id
    
    def unsubscribe(self, agent_id: str) -> bool:
        """
        取消订阅
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功取消
        """
        if agent_id not in self._subscriptions:
            return False
        
        subscription = self._subscriptions[agent_id]
        
        # 从类型索引中移除
        for msg_type in subscription.message_types:
            self._type_index[msg_type].discard(agent_id)
        
        # 移除订阅
        del self._subscriptions[agent_id]
        
        return True
    
    async def publish(self, message: Message) -> str:
        """
        发布消息
        
        消息会被添加到队列中异步处理
        如果队列已满，会丢弃最旧的消息或阻塞（根据配置）
        
        Args:
            message: 要发布的消息
            
        Returns:
            message_id: 消息ID
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 首先存入消息池
        message_id = await self.message_pool.publish(message)
        
        # 添加到处理队列
        try:
            # 使用put_nowait检查队列是否已满
            self._message_queue.put_nowait(message)
        except asyncio.QueueFull:
            # 队列已满，丢弃最旧的消息
            try:
                old_msg = self._message_queue.get_nowait()
                self._dropped_messages += 1
                logger.warning(f"Queue full, dropped message: {old_msg.id}")
                # 放入新消息
                self._message_queue.put_nowait(message)
            except asyncio.QueueEmpty:
                # 队列突然空了，直接放入
                self._message_queue.put_nowait(message)
        
        return message_id
    
    async def _process_messages(self):
        """消息处理循环"""
        while self._processing:
            try:
                # 获取消息（带超时，以便检查_processing状态）
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=0.1
                )
                
                # 路由消息
                await self._route_message(message)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing message: {e}")
    
    def register_handler(self, agent_id: str, handler: Callable[[Message], None]):
        """
        注册消息处理器
        
        Args:
            agent_id: Agent ID
            handler: 消息处理函数（同步或异步）
        """
        self._handlers[agent_id] = handler
    
    def unregister_handler(self, agent_id: str) -> bool:
        """
        注销消息处理器
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功注销
        """
        if agent_id in self._handlers:
            del self._handlers[agent_id]
            return True
        return False
    
    async def _route_message(self, message: Message):
        """
        路由消息到订阅者
        
        实际调用注册的处理器来传递消息
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 获取对此类型感兴趣的订阅者
        interested_agents = self._type_index.get(message.type, set())
        
        # 按优先级排序
        candidates = []
        for agent_id in interested_agents:
            subscription = self._subscriptions.get(agent_id)
            if subscription:
                # 应用过滤器
                if subscription.filter_fn and not subscription.filter_fn(message):
                    continue
                candidates.append((subscription.priority, agent_id, subscription))
        
        # 按优先级排序（高优先级在前）
        candidates.sort(reverse=True)
        
        # 通知订阅者
        for priority, agent_id, subscription in candidates:
            handler = self._handlers.get(agent_id)
            if handler:
                try:
                    # 使用超时防止处理器卡住
                    if asyncio.iscoroutinefunction(handler):
                        await asyncio.wait_for(
                            handler(message),
                            timeout=5.0
                        )
                    else:
                        # 同步处理器在线程池中运行
                        loop = asyncio.get_event_loop()
                        await asyncio.wait_for(
                            loop.run_in_executor(None, handler, message),
                            timeout=5.0
                        )
                except asyncio.TimeoutError:
                    logger.warning(f"Handler timeout for agent {agent_id}")
                except Exception as e:
                    logger.error(f"Handler error for agent {agent_id}: {e}")
            else:
                # 没有处理器，只是订阅但没有注册处理器
                logger.debug(f"No handler registered for agent {agent_id}")
    
    def get_subscribers(self, message_type: MessageType = None) -> Dict[str, Subscription]:
        """
        获取订阅者信息
        
        Args:
            message_type: 如果指定，只返回对该类型感兴趣的订阅者
            
        Returns:
            订阅者字典
        """
        if message_type is None:
            return dict(self._subscriptions)
        
        agent_ids = self._type_index.get(message_type, set())
        return {
            agent_id: self._subscriptions[agent_id]
            for agent_id in agent_ids
            if agent_id in self._subscriptions
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取路由器统计信息"""
        return {
            "total_subscriptions": len(self._subscriptions),
            "total_handlers": len(self._handlers),
            "by_message_type": {
                msg_type.value: len(agents)
                for msg_type, agents in self._type_index.items()
            },
            "queue_size": self._message_queue.qsize(),
            "max_queue_size": self._max_queue_size,
            "dropped_messages": self._dropped_messages
        }


class AgentProxy:
    """
    Agent代理
    
    简化Agent与消息系统的交互
    """
    
    def __init__(self, 
                 agent_id: str,
                 router: PubSubRouter,
                 message_handler: Callable[[Message], None]):
        self.agent_id = agent_id
        self.router = router
        self.message_handler = message_handler
        self._subscription_id: Optional[str] = None
    
    async def connect(self, 
                      message_types: List[MessageType] = None,
                      filter_fn: Callable[[Message], bool] = None):
        """连接到消息系统"""
        if message_types is None:
            message_types = list(MessageType)
        
        # 包装消息处理器
        async def handler_wrapper(message: Message):
            if asyncio.iscoroutinefunction(self.message_handler):
                await self.message_handler(message)
            else:
                self.message_handler(message)
        
        # 订阅消息
        self._subscription_id = self.router.subscribe(
            agent_id=self.agent_id,
            message_types=message_types,
            filter_fn=filter_fn
        )
        
        # 注册处理器到路由器
        # 这里简化处理，实际应该通过更复杂的机制
    
    async def disconnect(self):
        """断开连接"""
        if self._subscription_id:
            self.router.unsubscribe(self.agent_id)
            self._subscription_id = None
    
    async def send(self, 
                   message: Message,
                   wait_for_response: bool = False,
                   timeout: float = 30.0) -> Optional[Message]:
        """
        发送消息
        
        Args:
            message: 要发送的消息
            wait_for_response: 是否等待响应
            timeout: 等待超时时间
            
        Returns:
            如果wait_for_response为True，返回响应消息
        """
        message_id = await self.router.publish(message)
        
        if wait_for_response:
            # 等待响应逻辑
            # 实际实现应该使用future或事件
            pass
        
        return None


# 测试代码
if __name__ == "__main__":
    import tempfile
    import sys
    sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')
    
    from core.message_bus.message import MessagePool, create_message, MessageType
    
    async def test_router():
        """测试路由器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建消息池
            pool = MessagePool(tmpdir)
            
            # 创建路由器
            router = PubSubRouter(pool)
            await router.start()
            
            # 测试订阅
            received = []
            
            def handler(msg):
                received.append(msg)
                print(f"Agent received: {msg.content}")
            
            sub_id = router.subscribe(
                agent_id="test_agent",
                message_types=[MessageType.TASK, MessageType.EVENT],
                filter_fn=lambda m: m.sender != "test_agent"  # 过滤自己发的
            )
            print(f"Subscription created: {sub_id}")
            
            # 测试发布
            msg = create_message(
                msg_type=MessageType.TASK,
                content={"action": "test"},
                sender="other_agent",
                recipients=["test_agent"]
            )
            
            await router.publish(msg)
            await asyncio.sleep(0.2)
            
            # 查看统计
            stats = router.get_statistics()
            print(f"Router stats: {stats}")
            
            # 停止路由器
            await router.stop()
            
            print("✅ Router tests completed!")
    
    asyncio.run(test_router())
