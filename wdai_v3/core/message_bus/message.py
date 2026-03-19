"""
wdai v3.0 - Core Message Bus
消息总线核心模块 - Phase 1 实现
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Set
import json
import uuid
import asyncio
from pathlib import Path


class MessageType(Enum):
    """消息类型枚举"""
    TASK = "task"           # 任务消息
    EVENT = "event"         # 事件通知
    NOTIFICATION = "notify" # 系统通知
    AUDIT = "audit"         # 审计日志
    RESPONSE = "response"   # 响应消息


@dataclass
class Message:
    """
    消息数据模型
    
    不可变消息对象，所有字段在创建时确定
    """
    # 身份标识
    id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    type: MessageType = MessageType.EVENT
    
    # 路由信息
    sender: str = "system"
    recipients: List[str] = field(default_factory=list)
    task_id: Optional[str] = None
    
    # 内容
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # 优先级 (0=普通, 1=高, 2=紧急)
    priority: int = 0
    
    def __post_init__(self):
        """验证消息数据"""
        if not self.id:
            self.id = f"msg_{uuid.uuid4().hex[:12]}"
        if isinstance(self.type, str):
            self.type = MessageType(self.type)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.expires_at, str):
            self.expires_at = datetime.fromisoformat(self.expires_at)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "sender": self.sender,
            "recipients": self.recipients,
            "task_id": self.task_id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建消息"""
        return cls(
            id=data.get("id"),
            type=MessageType(data.get("type", "event")),
            sender=data.get("sender", "system"),
            recipients=data.get("recipients", []),
            task_id=data.get("task_id"),
            content=data.get("content", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            priority=data.get("priority", 0)
        )
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """从JSON字符串创建消息"""
        return cls.from_dict(json.loads(json_str))
    
    def is_expired(self) -> bool:
        """检查消息是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def is_broadcast(self) -> bool:
        """检查是否是广播消息"""
        return "*" in self.recipients or len(self.recipients) == 0
    
    def __repr__(self) -> str:
        return f"Message({self.id}, type={self.type.value}, sender={self.sender})"


class MessageStorage:
    """
    消息持久化存储
    
    基于文件系统的简单实现，支持append-only写入
    支持文件锁和索引重建
    """
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.messages_file = self.storage_path / "messages.jsonl"
        self.index_file = self.storage_path / "index.json"
        self.lock_file = self.storage_path / ".lock"
        
        # 内存索引
        self._index: Dict[str, int] = {}  # message_id -> line_number
        self._lock = asyncio.Lock()  # 异步锁
        
        # 加载或重建索引
        if not self._load_index():
            self._rebuild_index()
    
    def _load_index(self) -> bool:
        """
        加载索引
        
        Returns:
            是否成功加载
        """
        if not self.index_file.exists():
            return False
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self._index = json.load(f)
            return True
        except (json.JSONDecodeError, IOError) as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to load index: {e}, will rebuild")
            return False
    
    def _save_index(self):
        """保存索引（带临时文件保护）"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 使用临时文件，避免写入过程中损坏
        temp_file = self.index_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, ensure_ascii=False)
            # 原子重命名
            temp_file.replace(self.index_file)
        except IOError as e:
            logger.error(f"Failed to save index: {e}")
    
    def _rebuild_index(self):
        """
        重建索引
        
        扫描消息文件，重建索引
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("Rebuilding index from messages file...")
        self._index = {}
        
        if not self.messages_file.exists():
            return
        
        valid_lines = 0
        corrupted_lines = 0
        
        with open(self.messages_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                try:
                    msg = Message.from_json(line.strip())
                    self._index[msg.id] = line_num
                    valid_lines += 1
                except (json.JSONDecodeError, KeyError) as e:
                    corrupted_lines += 1
                    logger.debug(f"Skipping corrupted line {line_num}: {e}")
        
        self._save_index()
        
        if corrupted_lines > 0:
            logger.warning(f"Index rebuilt: {valid_lines} valid, {corrupted_lines} corrupted lines skipped")
        else:
            logger.info(f"Index rebuilt: {valid_lines} messages indexed")
    
    async def append(self, message: Message) -> str:
        """
        追加消息到存储
        
        使用异步锁确保并发安全
        
        Returns:
            message_id: 消息ID
        """
        async with self._lock:
            # 获取当前行号
            line_number = 0
            if self.messages_file.exists():
                with open(self.messages_file, 'r', encoding='utf-8') as f:
                    line_number = sum(1 for _ in f)
            
            # 写入消息
            with open(self.messages_file, 'a', encoding='utf-8') as f:
                f.write(message.to_json() + '\n')
                f.flush()  # 确保写入磁盘
            
            # 更新索引
            self._index[message.id] = line_number
            
            # 批量保存索引（每100条保存一次）
            if len(self._index) % 100 == 0:
                self._save_index()
        
        return message.id
    
    async def flush(self):
        """刷新数据到磁盘"""
        self._save_index()
    
    def get(self, message_id: str) -> Optional[Message]:
        """根据ID获取消息"""
        if message_id not in self._index:
            return None
        
        line_number = self._index[message_id]
        
        with open(self.messages_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == line_number:
                    return Message.from_json(line.strip())
        
        return None
    
    def get_all(self, limit: int = None, offset: int = 0) -> List[Message]:
        """获取所有消息"""
        messages = []
        
        if not self.messages_file.exists():
            return messages
        
        with open(self.messages_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i < offset:
                    continue
                if limit and len(messages) >= limit:
                    break
                messages.append(Message.from_json(line.strip()))
        
        return messages
    
    def query(self, 
              message_type: MessageType = None,
              sender: str = None,
              recipient: str = None,
              task_id: str = None) -> List[Message]:
        """查询消息"""
        results = []
        
        for message in self.get_all():
            if message_type and message.type != message_type:
                continue
            if sender and message.sender != sender:
                continue
            if recipient and recipient not in message.recipients:
                continue
            if task_id and message.task_id != task_id:
                continue
            results.append(message)
        
        return results
    
    def count(self) -> int:
        """获取消息总数"""
        return len(self._index)


class MessagePool:
    """
    全局消息池
    
    提供消息的发布、查询和订阅管理
    """
    
    def __init__(self, storage_path: str = None):
        """
        初始化消息池
        
        Args:
            storage_path: 存储路径，默认使用工作区目录
        """
        if storage_path is None:
            storage_path = Path.home() / ".openclaw" / "workspace" / ".v3" / "messages"
        
        self.storage = MessageStorage(str(storage_path))
        self._subscribers: Dict[MessageType, Set[Callable]] = {
            msg_type: set() for msg_type in MessageType
        }
        self._lock = asyncio.Lock()
    
    async def publish(self, message: Message) -> str:
        """
        发布消息到池中
        
        Args:
            message: 要发布的消息
            
        Returns:
            message_id: 消息ID
        """
        # 持久化存储（内部有锁）
        message_id = await self.storage.append(message)
        
        # 通知订阅者
        await self._notify_subscribers(message)
        
        return message_id
    
    async def _notify_subscribers(self, message: Message):
        """通知订阅者"""
        subscribers = self._subscribers.get(message.type, set())
        
        # 创建通知任务
        tasks = []
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(message))
                else:
                    callback(message)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")
        
        # 并发执行所有通知
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, 
                  message_type: MessageType, 
                  callback: Callable[[Message], None]):
        """
        订阅特定类型的消息
        
        Args:
            message_type: 消息类型
            callback: 回调函数，可以是同步或异步
        """
        self._subscribers[message_type].add(callback)
    
    def unsubscribe(self, 
                    message_type: MessageType, 
                    callback: Callable[[Message], None]):
        """取消订阅"""
        self._subscribers[message_type].discard(callback)
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """获取单个消息"""
        return self.storage.get(message_id)
    
    def query(self, 
              message_type: MessageType = None,
              sender: str = None,
              recipient: str = None,
              task_id: str = None,
              limit: int = None) -> List[Message]:
        """
        查询消息
        
        Args:
            message_type: 消息类型筛选
            sender: 发送者筛选
            recipient: 接收者筛选
            task_id: 任务ID筛选
            limit: 返回数量限制
            
        Returns:
            符合条件的消息列表
        """
        messages = self.storage.query(
            message_type=message_type,
            sender=sender,
            recipient=recipient,
            task_id=task_id
        )
        
        if limit:
            messages = messages[:limit]
        
        return messages
    
    def get_task_history(self, task_id: str) -> List[Message]:
        """获取任务的完整消息历史"""
        return self.storage.query(task_id=task_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取消息池统计信息"""
        return {
            "total_messages": self.storage.count(),
            "subscribers": {
                msg_type.value: len(subs) 
                for msg_type, subs in self._subscribers.items()
            }
        }


# 便捷函数
def create_message(
    msg_type: MessageType,
    content: Dict[str, Any],
    sender: str = "system",
    recipients: List[str] = None,
    task_id: str = None,
    priority: int = 0
) -> Message:
    """便捷创建消息"""
    return Message(
        type=msg_type,
        content=content,
        sender=sender,
        recipients=recipients or [],
        task_id=task_id,
        priority=priority
    )


# 测试代码
if __name__ == "__main__":
    import tempfile
    
    async def test_message_bus():
        """测试消息总线"""
        # 创建临时存储
        with tempfile.TemporaryDirectory() as tmpdir:
            pool = MessagePool(tmpdir)
            
            # 测试订阅
            received_messages = []
            
            def on_task(msg):
                received_messages.append(msg)
                print(f"Received: {msg}")
            
            pool.subscribe(MessageType.TASK, on_task)
            
            # 测试发布
            msg = create_message(
                msg_type=MessageType.TASK,
                content={"action": "test", "data": "hello"},
                sender="test_agent",
                recipients=["target_agent"],
                task_id="task_001"
            )
            
            msg_id = await pool.publish(msg)
            print(f"Published message: {msg_id}")
            
            # 等待通知
            await asyncio.sleep(0.1)
            
            # 验证
            assert len(received_messages) == 1
            assert received_messages[0].id == msg_id
            
            # 查询测试
            history = pool.get_task_history("task_001")
            assert len(history) == 1
            
            # 统计测试
            stats = pool.get_statistics()
            print(f"Statistics: {stats}")
            assert stats["total_messages"] == 1
            
            print("✅ All tests passed!")
    
    # 运行测试
    asyncio.run(test_message_bus())
