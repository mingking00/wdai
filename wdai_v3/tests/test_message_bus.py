"""
wdai v3.0 - Message Bus Tests
消息总线测试
"""

import asyncio
import tempfile
import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.message_bus import (
    MessageBus,
    Message,
    MessageType,
    create_message
)


class TestMessage:
    """测试Message类"""
    
    def test_message_creation(self):
        """测试消息创建"""
        msg = Message(
            type=MessageType.TASK,
            content={"action": "test"},
            sender="agent_1",
            recipients=["agent_2"],
            task_id="task_001"
        )
        
        assert msg.type == MessageType.TASK
        assert msg.content == {"action": "test"}
        assert msg.sender == "agent_1"
        assert msg.recipients == ["agent_2"]
        assert msg.task_id == "task_001"
        assert msg.id.startswith("msg_")
    
    def test_message_serialization(self):
        """测试消息序列化"""
        msg = create_message(
            msg_type=MessageType.EVENT,
            content={"data": "test"},
            sender="sender",
            recipients=["recipient"]
        )
        
        # 测试to_dict/from_dict
        data = msg.to_dict()
        msg2 = Message.from_dict(data)
        
        assert msg.id == msg2.id
        assert msg.type == msg2.type
        assert msg.content == msg2.content
        
        # 测试to_json/from_json
        json_str = msg.to_json()
        msg3 = Message.from_json(json_str)
        
        assert msg.id == msg3.id
        assert msg.type == msg3.type
    
    def test_message_expiration(self):
        """测试消息过期"""
        from datetime import datetime, timedelta
        
        # 未过期消息
        msg1 = Message(expires_at=datetime.now() + timedelta(hours=1))
        assert not msg1.is_expired()
        
        # 已过期消息
        msg2 = Message(expires_at=datetime.now() - timedelta(hours=1))
        assert msg2.is_expired()
        
        # 永不过期消息
        msg3 = Message()
        assert not msg3.is_expired()


class TestMessageBus:
    """测试MessageBus"""
    
    @pytest.fixture
    async def message_bus(self):
        """创建测试用的消息总线"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(tmpdir)
            await bus.start()
            yield bus
            await bus.stop()
    
    @pytest.mark.asyncio
    async def test_publish_and_query(self):
        """测试发布和查询"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(tmpdir)
            await bus.start()
            
            try:
                # 发布消息
                msg_id = await bus.send(
                    content={"action": "test", "value": 42},
                    sender="agent_a",
                    recipients=["agent_b"],
                    msg_type=MessageType.TASK,
                    task_id="task_001"
                )
                
                assert msg_id.startswith("msg_")
                
                # 查询消息
                msg = bus.get_message(msg_id)
                assert msg is not None
                assert msg.content["value"] == 42
                
                # 按类型查询
                tasks = bus.query_messages(message_type=MessageType.TASK)
                assert len(tasks) == 1
                
                # 按发送者查询
                from_a = bus.query_messages(sender="agent_a")
                assert len(from_a) == 1
                
            finally:
                await bus.stop()
    
    @pytest.mark.asyncio
    async def test_task_history(self):
        """测试任务历史"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(tmpdir)
            await bus.start()
            
            try:
                # 发送多个相关消息
                for i in range(5):
                    await bus.send(
                        content={"step": i},
                        sender="agent",
                        recipients=["other"],
                        task_id="task_history_test"
                    )
                
                # 获取历史
                history = bus.get_task_history("task_history_test")
                assert len(history) == 5
                
                # 验证顺序
                for i, msg in enumerate(history):
                    assert msg.content["step"] == i
                
            finally:
                await bus.stop()
    
    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self):
        """测试订阅和接收"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(tmpdir)
            await bus.start()
            
            try:
                received_messages = []
                
                def handler(msg):
                    received_messages.append(msg)
                
                # 订阅
                sub_id = bus.subscribe(
                    agent_id="test_agent",
                    message_types=[MessageType.EVENT],
                    filter_fn=lambda m: m.sender != "test_agent"
                )
                
                # 发布消息
                await bus.send(
                    content={"data": "hello"},
                    sender="other_agent",
                    recipients=["test_agent"],
                    msg_type=MessageType.EVENT
                )
                
                # 等待处理
                await asyncio.sleep(0.2)
                
                # 注意：由于当前实现是异步的，这里需要实际集成Agent才能测试接收
                # 这里主要测试订阅机制是否正常工作
                stats = bus.get_statistics()
                assert stats["router"]["total_subscriptions"] == 1
                
                # 取消订阅
                result = bus.unsubscribe("test_agent")
                assert result is True
                
                stats = bus.get_statistics()
                assert stats["router"]["total_subscriptions"] == 0
                
            finally:
                await bus.stop()
    
    @pytest.mark.asyncio
    async def test_statistics(self):
        """测试统计信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(tmpdir)
            await bus.start()
            
            try:
                # 初始状态
                stats = bus.get_statistics()
                assert stats["pool"]["total_messages"] == 0
                
                # 发送消息
                await bus.send(
                    content={"test": True},
                    sender="a",
                    recipients=["b"]
                )
                
                # 检查统计
                stats = bus.get_statistics()
                assert stats["pool"]["total_messages"] == 1
                
            finally:
                await bus.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_publish(self):
        """测试并发发布"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(tmpdir)
            await bus.start()
            
            try:
                async def publish_n(n):
                    for i in range(n):
                        await bus.send(
                            content={"index": i},
                            sender="concurrent",
                            recipients=["receiver"]
                        )
                
                # 并发发布
                await asyncio.gather(
                    publish_n(50),
                    publish_n(50),
                    publish_n(50)
                )
                
                # 验证
                stats = bus.get_statistics()
                assert stats["pool"]["total_messages"] == 150
                
            finally:
                await bus.stop()


class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_throughput(self):
        """测试吞吐量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(tmpdir)
            await bus.start()
            
            try:
                import time
                
                # 发送1000条消息
                count = 1000
                start = time.time()
                
                for i in range(count):
                    await bus.send(
                        content={"index": i},
                        sender="perf_test",
                        recipients=["receiver"]
                    )
                
                elapsed = time.time() - start
                throughput = count / elapsed
                
                print(f"\nThroughput: {throughput:.2f} msg/s")
                print(f"Elapsed: {elapsed:.2f}s for {count} messages")
                
                # 验证目标：1000 msg/s
                assert throughput >= 500, f"Throughput too low: {throughput}"
                
            finally:
                await bus.stop()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
