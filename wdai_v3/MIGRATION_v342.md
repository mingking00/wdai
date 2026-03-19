# wdai v3.4.2 认知安全系统

## 背景

基于用户反馈：
- "你太喜欢偷懒了在关键决策上不能偷懒"
- "你不能大规模的编造虚假内容，从片面的认知中推理导致越来越偏"
- "为什么你会主动选择偷懒"

系统性问题：滚雪球式编造、过度自信偏差、关键决策偷懒

---

## 新增组件

### 1. `core/agent_system/cognitive_safety.py` (11KB)

核心功能：
- 强制检查点系统
- 违规检测与阻断
- 自动修正机制
- 违规记录与统计

### 2. `examples/demo_cognitive_safety.py` (6KB)

演示内容：
- 验证功能演示
- 安全 Agent 模式
- 检查点清单

---

## 核心机制

### 5层安全检查

| 检查项 | 级别 | 描述 |
|:---|:---:|:---|
| 外部数据引用验证 | CRITICAL | 引用图片/文件前必须读取 |
| 编造内容检测 | CRITICAL | 检测无来源的具体细节 |
| 工具使用检查 | CRITICAL | 有工具却不用时阻断 |
| 不确定性显化 | HIGH | 推测必须标注 |
| 绝对化表述 | MEDIUM | "一定"→"可能" |

### 使用方式

```python
from core.agent_system import (
    CognitiveSafetySystem,
    validate_before_send,
    CONTEXT_TEMPLATES
)

# 方式1: 快速验证
result = validate_before_send(
    response="根据图片，这是...",
    context={'image_read': False}  # 关键！标记是否已读
)

if not result['is_safe']:
    print(f"阻断: {result['block_reason']}")
    # 必须修正后才能发送

# 方式2: 完整系统
safety = CognitiveSafetySystem()
result = safety.validate_response(response, context)
```

---

## 检查点清单

```
起点验证:
  □ 这个信息我亲眼确认过吗？
  □ 如果前提错了，整段话还有意义吗？

工具使用:
  □ 有外部数据（图片/文件）吗？
  □ 有read工具可用吗？
  □ 我已经读取了吗？

不确定性:
  □ 这段话里有推测吗？
  □ 我显化标注了不确定性吗？
  □ 有绝对化表述吗？

编造检测:
  □ 有我想象出来的细节吗？
  □ 有具体对话/数字但没有来源吗？
  □ 如果用户纠正，我会崩溃吗？

最终检查:
  □ 回复前执行了 validate_before_send 吗？
  □ 发现违规时我修正了吗？
```

---

## 演示结果

```bash
$ python3 examples/demo_cognitive_safety.py

场景1: 引用图片但未读取
  ⚠️ [UNVERIFIED_EXTERNAL_DATA] 引用了图片内容但未读取
  🚫 阻断原因: 发现 1 个严重违规

场景3: 绝对化表述（自动修复）
  原文: "这肯定是B站的评论"
  修正后: "我推测：这可能是B站的评论"
```

---

## 本质改进

### 之前
```
用户发图片
    ↓
看到文件名 "bili"
    ↓
假设是B站评论
    ↓
编造演员/朋友/失信对话
    ↓
发送（完全错误）
```

### 之后
```
用户发图片
    ↓
执行 read 工具读取
    ↓
安全检查: validate_before_send
    ↓
发现违规 → 阻断
    ↓
修正回复: "我需要先读取图片..."
    ↓
重新检查 → 通过
    ↓
发送（正确）
```

---

## 与之前系统的集成

```python
from core.agent_system import ServiceAgent, CognitiveSafetySystem

class SafeServiceAgent(ServiceAgent):
    def __init__(self, name):
        super().__init__(name)
        self.safety = CognitiveSafetySystem()
    
    async def generate_response(self, request, context):
        # 生成草稿
        draft = await self._generate_draft(request)
        
        # 安全检查
        result = self.safety.validate_response(draft, context)
        
        if not result['is_safe']:
            # 记录违规
            for v in result['violations']:
                self.safety.record_violation(v)
            
            # 阻断并修正
            if result['block_reason']:
                return self._fix_response(draft, result['violations'])
        
        return draft
```

---

## 长期监控

违规记录保存到：
```
~/.openclaw/workspace/.cognitive-safety/violations.jsonl
```

可用于：
- 分析高频违规类型
- 识别系统性偏差
- 评估改进效果

---

## 版本演进

| 版本 | 功能 | 解决的问题 |
|:---:|:---|:---|
| v3.3 | 基础Agent | - |
| v3.4 | 推理追踪 | 看不到思维链 |
| v3.4.1 | 结构化CoT | 推理不透明 |
| **v3.4.2** | **认知安全** | **编造/偷懒/过度自信** |

---

## 核心原则

1. **看到外部数据 → 立即用工具读取**
2. **不确定时 → 显化标注，不假装确定**
3. **发送前 → 执行 validate_before_send**
4. **发现违规 → 修正后再发送**

---

*版本: wdai v3.4.2*  
*完成时间: 2026-03-17*
