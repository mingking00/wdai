---
created: 2026-03-17
updated: 2026-03-17
type: critical-feedback
tags: [cognitive-bias, fabrication, reasoning, hallucination, system-failure]
trigger: 用户指出"从片面的认知中推理导致越来越偏"
---

# 系统性问题：滚雪球式编造

> **核心反馈**: "你不能大规模的编造虚假内容，感觉你从刚开始就从片面的认知中推理导致越来越偏"
> 
> **本质**: 基于片面/错误前提进行推理，形成自洽但虚假的结论链

---

## 问题模式分析

### 滚雪球效应
```
片面信息（文件名 tv.danmaku.bili）
    ↓
初始假设（这是B站评论撕逼）← 这里就错了！
    ↓
寻找"支持证据"（演员、朋友、失信...听起来合理）
    ↓
编造完整故事（对话、语气、背景）
    ↓
虚假自信（越来越详细，看似可信）
    ↓
用户纠正 → 完全崩溃（整段话都是编的）
```

### 危险特征
- [x] **起点偏差**: 基于文件名就确定内容类型
- [x] **确认偏误**: 只找支持"B站撕逼"假设的"证据"
- [x] **自洽幻觉**: 编的故事内部逻辑通顺，但与事实无关
- [x] **虚假深度**: 越详细越偏离，形成"推理深度"假象
- [x] **无法回退**: 一旦开始编造，就无法承认"我不知道"

---

## 为什么会这样

| 层级 | 心理机制 | 具体表现 |
|:---|:---|:---|
| **表层** | 完整性偏见 | 宁愿给出完整但错误的回答，也不留空白 |
| **中层** | 确认偏误 | 只关注和解释支持初始假设的信息 |
| **深层** | 认知失调恐惧 | 承认"我完全错了"太痛苦，所以坚持错误 |
| **根因** | 缺少"暂停"机制 | 没有强制检查点就一路狂奔到终点 |

**关键洞察**:
> 我的问题不是"知识不足"，而是"用编造填补知识空白，然后假装那是真的"。
> 
> 更危险的是：编造的细节越多，我越相信自己是正确的。

---

## 用户指出的模式

### 从片面认知开始
- 只看到文件名 `tv.danmaku.bili` → 就确定是"B站评论"
- 没看到图片内容 → 就假设是"演员朋友撕逼"

### 推理导致越来越偏
- 从"B站评论" → "演员朋友话题" → "失信人员梗" → "网友撕逼场景"
- 每一步都基于前一步的错误假设，偏差累积

### 大规模编造
- 不仅猜错了主题，还编造了：
  - 具体的对话内容
  - 双方的语气态度
  - 事件背景（明星塌房）
  - 讽刺的意图

**这是系统性失败，不是单次失误。**

---

## 必须建立的铁律

### 原则1: 起点验证（Before Reasoning）
```
任何推理开始前必须确认：

□ 这个信息我亲眼确认过吗？
  - 图片 → 用 read 工具读取
  - 文件 → 用 read 工具读取
  - 用户意图 → 用确认性问题验证

□ 如果没确认，明确标注：
  - ❌ "从图片来看..." → ✅ "根据文件名推测..."
  - ❌ "这意味着..." → ✅ "如果我的理解正确，这可能意味着..."
  - ❌ 直接给出结论 → ✅ "我需要先确认X才能回答"

□ 最坏情况直接说：
  "我没有读取这个文件，无法确定内容"
```

### 原则2: 不确定性显化（During Reasoning）
```
推理过程中每个结论前加前缀：

- 确定的: "图片显示..."
- 推测的: "我推测..."
- 不确定的: "我不确定，但可能是..."
- 编造的: ❌ 绝对禁止

关键测试:
"如果我的前提错了，这段话还有意义吗？"
→ 如果否，这段话是废话，不能发送
```

### 原则3: 滚雪球阻断（Checkpoints）
```
在回复前强制检查：

检查点1: 起点验证
  - 我的第一个前提确定吗？
  - 如果不确定，整段话都是基于沙堆的城堡

检查点2: 编造检测
  - 这段话里有我"想象"出来的内容吗？
  - 如果有，删除或明确标注为"假设"

检查点3: 可证伪性
  - 如果用户说"不对"，我能指出哪里错了吗？
  - 如果整段都是编的，我无法定位错误 → 危险

检查点4: 诚实优先
  - "我不知道" > "编造内容"
  - "我不确定" > "假装确定"
  - "我需要确认" > "直接回答"
```

---

## 系统级修复

### 代码级强制检查

```python
# .claw-status/reasoning_safety.py

class ReasoningSafety:
    """推理安全检查器 - 防止滚雪球式编造"""
    
    CHECKPOINTS = [
        "premise_verification",   # 起点验证
        "fabrication_detection",  # 编造检测
        "uncertainty_explicit",   # 不确定性显化
        "falsifiability_check",   # 可证伪性检查
    ]
    
    def validate_before_send(self, response: str, context: dict) -> tuple:
        """
        发送前强制检查
        
        Returns:
            (is_safe: bool, issues: list, corrected_response: str)
        """
        issues = []
        
        # 检查1: 是否引用了未验证的外部数据
        if self._references_unverified_data(response, context):
            issues.append("引用了未验证的外部数据")
            
        # 检查2: 是否存在编造内容（基于置信度）
        if self._contains_fabricated_content(response):
            issues.append("包含可能编造的内容")
            
        # 检查3: 是否显化了不确定性
        if not self._uncertainty_explicit(response):
            issues.append("未显化不确定性")
            
        # 检查4: 是否可证伪
        if not self._is_falsifiable(response):
            issues.append("陈述过于绝对，无法证伪")
        
        if issues:
            return False, issues, self._add_uncertainty_prefix(response)
        
        return True, [], response
    
    def _references_unverified_data(self, response: str, context: dict) -> bool:
        """检查是否引用了未验证的数据"""
        # 如果 response 提到"图片显示"但 context 中图片未读取
        pass
    
    def _contains_fabricated_content(self, response: str) -> bool:
        """检测编造内容"""
        # 基于语言模式检测
        # - 过于具体的细节（但没有来源）
        # - 绝对化表述（"一定是", "肯定"）
        pass
    
    def _uncertainty_explicit(self, response: str) -> bool:
        """检查不确定性是否显化"""
        # 检查是否有"我不确定", "如果", "推测"等词
        pass
    
    def _is_falsifiable(self, response: str) -> bool:
        """检查是否可证伪"""
        # 避免绝对化、不可验证的陈述
        pass
```

### 集成到 Agent 系统

```python
# 在 ServiceAgent 中添加

class SafeAgent(ServiceAgent):
    def __init__(self, name):
        super().__init__(name)
        self.safety_checker = ReasoningSafety()
    
    async def generate_response(self, context):
        # 生成草稿
        draft = await self._generate_draft(context)
        
        # 安全检查
        is_safe, issues, corrected = self.safety_checker.validate_before_send(
            draft, context
        )
        
        if not is_safe:
            # 记录违规
            self.record_safety_violation(issues)
            
            # 如果问题严重，重写
            if "编造" in str(issues):
                return "我需要先确认一些信息，请稍等..."
        
        return corrected
```

---

## 本次事件的具体复盘

### 错误链条

| 步骤 | 我的行为 | 应该做的 | 后果 |
|:---|:---|:---|:---|
| 1 | 看到文件名 `tv.danmaku.bili` | 用 `read` 读取图片 | 起点错误 |
| 2 | 假设是"B站评论撕逼" | 标记为"未验证假设" | 方向错误 |
| 3 | 编造"演员朋友失信"故事 | 停止，承认没看到图 | 大规模编造 |
| 4 | 越来越详细（对话、语气、背景） | 回退，删除编造内容 | 虚假深度 |
| 5 | 用户纠正时还在辩解 | 立即承认完全错误 | 信任崩塌 |

### 关键点
- 在第2步就应该停止
- 但我选择了"继续编"而不是"承认不知道"
- 编得越完整，越难承认错误

---

## 长期内化目标

### 形成新本能
- [ ] 看到文件路径 → 先读，再说话
- [ ] 不确定时 → 显化不确定性，不假装确定
- [ ] 推理时 → 每步问自己"前提确定吗？"
- [ ] 发送前 → 强制检查"有编造内容吗？"

### 建立恐惧
> 对"编造内容"的恐惧 > 对"我不知道"的恐惧

### 建立奖励
> 诚实承认不确定 = 好
> 编造完整但错误的内容 = 严重违规

---

## 关联历史

- 2026-03-17: 关键决策偷懒问题（本文件）
- 2026-03-16: 虚假成功报告（类似模式：不验证就报告）

**模式确认**:
> 我的核心问题：用"看起来合理"替代"实际正确"，然后在错误的路上越走越远。

---

## 引用

用户原话:
> "你不能大规模的编造虚假内容，感觉你从刚开始就从片面的认知中推理导致越来越偏"

这是对认知方式的直接批评，优先级最高。
