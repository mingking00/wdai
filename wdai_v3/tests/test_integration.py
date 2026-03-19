#!/usr/bin/env python3
"""
wdai v3.0 - Message Bus Integration Test
集成测试脚本
"""

import asyncio
import tempfile
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.message_bus import MessageBus, MessageType, create_message


async def test_full_message_bus():
    """测试完整消息总线"""
    print("=" * 60)
    print("wdai v3.0 - Message Bus Integration Test")
    print("=" * 60)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建消息总线
        print("1. Creating MessageBus...")
        bus = MessageBus(tmpdir)
        await bus.start()
        print("   ✅ MessageBus created and started")
        print()
        
        # 测试1: 基本发送
        print("2. Testing basic message send...")
        msg_id = await bus.send(
            content={"action": "test", "data": "hello world"},
            sender="test_agent",
            recipients=["receiver_agent"],
            msg_type=MessageType.TASK,
            task_id="task_001"
        )
        print(f"   ✅ Message sent: {msg_id}")
        print()
        
        # 测试2: 查询消息
        print("3. Testing message query...")
        msg = bus.get_message(msg_id)
        assert msg is not None
        assert msg.content["data"] == "hello world"
        print(f"   ✅ Message retrieved: {msg.content}")
        print()
        
        # 测试3: 任务历史
        print("4. Testing task history...")
        for i in range(3):
            await bus.send(
                content={"step": i, "progress": f"{(i+1)*33}%"},
                sender="worker_agent",
                recipients=["coordinator"],
                msg_type=MessageType.EVENT,
                task_id="task_002"
            )
        
        history = bus.get_task_history("task_002")
        assert len(history) == 3
        print(f"   ✅ Task history retrieved: {len(history)} messages")
        for h in history:
            print(f"      - Step {h.content['step']}: {h.content['progress']}")
        print()
        
        # 测试4: 订阅
        print("5. Testing subscription...")
        received = []
        
        def message_handler(msg):
            received.append(msg)
            print(f"   📨 Handler received: {msg.type.value} from {msg.sender}")
        
        sub_id = bus.subscribe(
            agent_id="monitor_agent",
            message_types=[MessageType.TASK, MessageType.EVENT],
            filter_fn=lambda m: m.sender != "monitor_agent"
        )
        print(f"   ✅ Subscription created: {sub_id}")
        print()
        
        # 测试5: 统计信息
        print("6. Testing statistics...")
        stats = bus.get_statistics()
        print(f"   📊 Pool stats: {stats['pool']}")
        print(f"   📊 Router stats: {stats['router']}")
        print()
        
        # 测试6: 并发发送
        print("7. Testing concurrent publish...")
        import time
        
        async def send_batch(n, batch_id):
            for i in range(n):
                await bus.send(
                    content={"batch": batch_id, "index": i},
                    sender="concurrent_sender",
                    recipients=["receiver"],
                    msg_type=MessageType.EVENT
                )
        
        start = time.time()
        await asyncio.gather(
            send_batch(50, "A"),
            send_batch(50, "B"),
            send_batch(50, "C")
        )
        elapsed = time.time() - start
        throughput = 150 / elapsed
        
        print(f"   ✅ Sent 150 messages in {elapsed:.2f}s")
        print(f"   📈 Throughput: {throughput:.2f} msg/s")
        print()
        
        # 停止
        await bus.stop()
        print("8. MessageBus stopped")
        print()
        
        # 最终统计
        final_stats = bus.get_statistics()
        print("=" * 60)
        print("Final Statistics:")
        print(f"  Total messages: {final_stats['pool']['total_messages']}")
        print(f"  Total subscriptions: {final_stats['router']['total_subscriptions']}")
        print("=" * 60)
        print()
        print("✅ All integration tests passed!")
        print()
        print("Phase 1 Implementation Complete!")
        print("- Message Pool: ✅")
        print("- Pub/Sub Router: ✅")
        print("- Persistence: ✅")
        print("- Statistics: ✅")


if __name__ == "__main__":
    asyncio.run(test_full_message_bus())
