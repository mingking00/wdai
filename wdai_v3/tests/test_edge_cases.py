#!/usr/bin/env python3
"""
wdai v3.0 - Message Bus Extended Tests (Fixed)
消息总线扩展测试 - 修复版本
"""

import asyncio
import tempfile
import json
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.message_bus import (
    MessageBus,
    Message,
    MessageType,
    create_message
)


# 启用测试模式
MessageBus._reset_for_testing()


def create_test_bus(suffix=""):
    """创建测试用的消息总线"""
    # 重置单例以允许新实例
    MessageBus._reset_for_testing()
    tmpdir = tempfile.mkdtemp(suffix=suffix)
    return MessageBus(tmpdir), tmpdir


async def test_empty_content():
    """测试空内容消息"""
    bus, tmpdir = create_test_bus("_empty")
    await bus.start()
    
    try:
        msg_id = await bus.send(
            content={},
            sender="test",
            recipients=["receiver"]
        )
        
        msg = bus.get_message(msg_id)
        assert msg.content == {}, f"Expected empty content, got {msg.content}"
        print("✅ Empty content message")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_large_content():
    """测试大内容消息"""
    bus, tmpdir = create_test_bus("_large")
    await bus.start()
    
    try:
        large_data = "x" * (1024 * 1024)  # 1MB
        msg_id = await bus.send(
            content={"data": large_data},
            sender="test",
            recipients=["receiver"]
        )
        
        msg = bus.get_message(msg_id)
        assert len(msg.content["data"]) == 1024 * 1024
        print("✅ Large content message (1MB)")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_special_characters():
    """测试特殊字符"""
    bus, tmpdir = create_test_bus("_special")
    await bus.start()
    
    try:
        special_chars = {
            "chinese": "中文测试内容",
            "emoji": "🎉🚀✅",
            "newlines": "line1\nline2\nline3",
            "quotes": 'He said "Hello"',
            "unicode": "日本語テ스트한국어"
        }
        
        msg_id = await bus.send(
            content=special_chars,
            sender="test",
            recipients=["receiver"]
        )
        
        msg = bus.get_message(msg_id)
        assert msg.content["chinese"] == "中文测试内容"
        assert msg.content["emoji"] == "🎉🚀✅"
        assert "\n" in msg.content["newlines"]
        print("✅ Special characters")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_broadcast_message():
    """测试广播消息"""
    bus, tmpdir = create_test_bus("_broadcast")
    await bus.start()
    
    try:
        msg = create_message(
            msg_type=MessageType.NOTIFICATION,
            content={"announcement": "system update"},
            sender="system",
            recipients=["*"]
        )
        
        msg_id = await bus.publish(msg)
        retrieved = bus.get_message(msg_id)
        
        assert "*" in retrieved.recipients
        assert retrieved.is_broadcast()
        print("✅ Broadcast message")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_message_expiration():
    """测试消息过期"""
    bus, tmpdir = create_test_bus("_expire")
    await bus.start()
    
    try:
        msg = Message(
            type=MessageType.EVENT,
            content={"temp": True},
            sender="test",
            recipients=["receiver"],
            expires_at=datetime.now() + timedelta(milliseconds=100)
        )
        
        msg_id = await bus.publish(msg)
        
        # 未过期
        msg1 = bus.get_message(msg_id)
        assert not msg1.is_expired()
        
        # 等待过期
        await asyncio.sleep(0.15)
        
        # 已过期
        msg2 = bus.get_message(msg_id)
        assert msg2.is_expired()
        print("✅ Message expiration")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_nonexistent_message():
    """测试获取不存在的消息"""
    bus, tmpdir = create_test_bus("_none")
    await bus.start()
    
    try:
        msg = bus.get_message("nonexistent_id_12345")
        assert msg is None
        print("✅ Nonexistent message")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_duplicate_subscription():
    """测试重复订阅"""
    bus, tmpdir = create_test_bus("_dup")
    await bus.start()
    
    try:
        # 第一次订阅
        sub1 = bus.subscribe(
            agent_id="agent_1",
            message_types=[MessageType.TASK]
        )
        
        # 第二次订阅（覆盖）
        sub2 = bus.subscribe(
            agent_id="agent_1",
            message_types=[MessageType.EVENT]
        )
        
        stats = bus.get_statistics()
        assert stats["router"]["total_subscriptions"] == 1
        print("✅ Duplicate subscription")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_unsubscribe_nonexistent():
    """测试取消不存在的订阅"""
    bus, tmpdir = create_test_bus("_unsub")
    await bus.start()
    
    try:
        result = bus.unsubscribe("nonexistent_agent")
        assert result is False
        print("✅ Unsubscribe nonexistent")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_nested_content():
    """测试嵌套复杂内容"""
    bus, tmpdir = create_test_bus("_nested")
    await bus.start()
    
    try:
        nested_content = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": [1, 2, 3, {"key": "value"}],
                        "deep": True
                    }
                }
            },
            "list": [
                {"id": 1, "name": "item1"},
                {"id": 2, "name": "item2"}
            ],
            "null_value": None,
            "bool_value": True,
            "number": 3.14159
        }
        
        msg_id = await bus.send(
            content=nested_content,
            sender="test",
            recipients=["receiver"]
        )
        
        msg = bus.get_message(msg_id)
        assert msg.content["level1"]["level2"]["level3"]["deep"] is True
        assert len(msg.content["list"]) == 2
        assert msg.content["null_value"] is None
        print("✅ Nested complex content")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_persistence_across_sessions():
    """测试跨会话持久化"""
    tmpdir = tempfile.mkdtemp(suffix="_persist")
    
    # 重置单例
    MessageBus._reset_for_testing()
    
    # 会话1：发送消息
    bus1 = MessageBus(tmpdir)
    await bus1.start()
    
    msg_ids = []
    for i in range(5):
        msg_id = await bus1.send(
            content={"session": 1, "index": i},
            sender="test",
            recipients=["receiver"]
        )
        msg_ids.append(msg_id)
    
    await bus1.stop()
    
    # 重置单例
    MessageBus._reset_for_testing()
    
    # 会话2：读取消息
    bus2 = MessageBus(tmpdir)
    await bus2.start()
    
    try:
        for msg_id in msg_ids:
            msg = bus2.get_message(msg_id)
            assert msg is not None
            assert msg.content["session"] == 1
        
        stats = bus2.get_statistics()
        assert stats["pool"]["total_messages"] == 5
        print("✅ Persistence across sessions")
        
    finally:
        await bus2.stop()
        shutil.rmtree(tmpdir)


async def test_stress_test():
    """压力测试"""
    bus, tmpdir = create_test_bus("_stress")
    await bus.start()
    
    try:
        message_count = 1000
        start = time.time()
        
        async def send_batch(start_idx, count):
            for i in range(count):
                await bus.send(
                    content={"batch_start": start_idx, "index": i},
                    sender=f"agent_{start_idx}",
                    recipients=["receiver"]
                )
        
        tasks = [send_batch(i * 100, 100) for i in range(10)]
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        throughput = message_count / elapsed
        
        print(f"✅ Stress test (1000 messages) - {throughput:.0f} msg/s")
        
        stats = bus.get_statistics()
        assert stats["pool"]["total_messages"] == message_count
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_all_message_types():
    """测试所有消息类型"""
    bus, tmpdir = create_test_bus("_types")
    await bus.start()
    
    try:
        for msg_type in MessageType:
            msg_id = await bus.send(
                content={"type": msg_type.value},
                sender="test",
                recipients=["receiver"],
                msg_type=msg_type
            )
            
            msg = bus.get_message(msg_id)
            assert msg.type == msg_type
            
            queried = bus.query_messages(message_type=msg_type)
            assert len(queried) == 1
        
        print("✅ All message types")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def test_message_metadata():
    """测试消息元数据"""
    bus, tmpdir = create_test_bus("_meta")
    await bus.start()
    
    try:
        msg = create_message(
            msg_type=MessageType.TASK,
            content={"action": "test"},
            sender="test_agent",
            recipients=["receiver"],
            task_id="task_123"
        )
        
        msg.metadata = {
            "source": "user_input",
            "version": "1.0",
            "tags": ["important", "urgent"]
        }
        
        msg_id = await bus.publish(msg)
        retrieved = bus.get_message(msg_id)
        
        assert retrieved.metadata["source"] == "user_input"
        assert "important" in retrieved.metadata["tags"]
        print("✅ Message metadata")
        
    finally:
        await bus.stop()
        shutil.rmtree(tmpdir)


async def main():
    """主函数"""
    print("=" * 60)
    print("wdai v3.0 - Message Bus Extended Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_empty_content,
        test_large_content,
        test_special_characters,
        test_broadcast_message,
        test_message_expiration,
        test_nonexistent_message,
        test_duplicate_subscription,
        test_unsubscribe_nonexistent,
        test_nested_content,
        test_persistence_across_sessions,
        test_stress_test,
        test_all_message_types,
        test_message_metadata,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All extended tests passed!")
        return True
    else:
        print("\n⚠️ Some tests failed")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
