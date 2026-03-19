# wdai v3.0 - Message Bus

**Phase 1 实现** - 消息总线核心模块

---

## 📋 功能特性

- ✅ **全局消息池** - 持久化存储所有消息
- ✅ **发布-订阅** - 灵活的Pub/Sub机制
- ✅ **消息路由** - 自动路由到订阅者
- ✅ **查询系统** - 多维度消息查询
- ✅ **任务追踪** - 完整的任务历史
- ✅ **高性能** - 3300+ msg/s 吞吐量
- ✅ **持久化** - 文件系统自动存储
- ✅ **异步处理** - 全异步架构
- ✅ **边界测试** - 13项边界情况全部通过

---

## 🚀 快速开始

```python
import asyncio
from core.message_bus import MessageBus, MessageType

async def main():
    # 创建消息总线
    bus = MessageBus()
    await bus.start()
    
    # 发送消息
    msg_id = await bus.send(
        content={"action": "hello"},
        sender="agent_a",
        recipients=["agent_b"],
        msg_type=MessageType.TASK
    )
    
    # 查询消息
    msg = bus.get_message(msg_id)
    print(f"Message: {msg.content}")
    
    # 停止
    await bus.stop()

asyncio.run(main())
```

---

## 📦 架构组件

```
core/message_bus/
├── __init__.py      # MessageBus Facade
├── message.py       # Message + MessagePool + Storage
└── router.py        # PubSubRouter + AgentProxy
```

---

## 📊 性能指标

| 指标 | 数值 | 目标 |
|:---|:---:|:---:|
| 吞吐量 | 3303 msg/s | 1000 msg/s ✅ |
| 压力测试 | 1514 msg/s | 1000 msg/s ✅ |
| 延迟 | ~15ms | <100ms ✅ |
| 并发 | 支持 | 支持 ✅ |

---

## 🧪 测试覆盖

### 集成测试
```bash
python3 tests/test_integration.py
```

### 边界测试（13项）
```bash
python3 tests/test_edge_cases.py
```

**边界测试项**:
- ✅ 空内容消息
- ✅ 1MB大内容
- ✅ 特殊字符（中文/Emoji/换行）
- ✅ 广播消息
- ✅ 消息过期
- ✅ 异常处理
- ✅ 跨会话持久化
- ✅ 并发压力测试

---

*Phase 1 Complete - Ready for Phase 2: SOP Engine*
