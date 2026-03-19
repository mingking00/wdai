# 置信度驱动的记忆验证系统 v0.1

## 设计目标

解决当前记忆系统的核心问题：
- ❌ 不知道提取的记忆有多可靠
- ❌ 错了也不知道，下次还错
- ❌ 没有反馈循环

## 核心架构 (借鉴 LexChronos)

```
┌─────────────────────────────────────────────────────────────┐
│              Confidence-Driven Memory System                 │
├─────────────────────────┬───────────────────────────────────┤
│   Extraction Agent      │      Verification Agent           │
│   (记忆提取)            │      (验证评分)                   │
├─────────────────────────┼───────────────────────────────────┤
│  • 语义检索             │  • 关键词匹配度计算               │
│  • 召回候选记忆         │  • 语义相关性验证                 │
│  • 多源聚合             │  • 置信度评分 (0-1)               │
└─────────────────────────┴───────────────────────────────────┘
           ↓                           ↓
           └──────→ Confidence-Driven Loop ←──────┘
                      (置信度驱动循环)
```

## 置信度决策树

```
提取候选记忆
    ↓
验证评分
    ↓
    ├─ 置信度 > 0.8 (HIGH)
    │      ↓
    │   直接使用 → 返回结果
    │
    ├─ 置信度 0.5-0.8 (MEDIUM)
    │      ↓
    │   需要确认 → "我找到一段可能相关的记忆，但不太确定..."
    │
    └─ 置信度 < 0.5 (LOW)
           ↓
        承认不知道 → "我没有找到关于这个的可靠记忆"
```

## 实现文件

```
.claw-status/
└── confidence_memory.py      # 核心实现 (300行)
    ├── ExtractionAgent       # 记忆提取代理
    ├── VerificationAgent     # 验证评分代理
    ├── ConfidenceDrivenMemorySystem  # 主系统
    └── test_confidence_driven_memory # 测试
```

## 使用方法

```python
from confidence_memory import ConfidenceDrivenMemorySystem

# 初始化系统
system = ConfidenceDrivenMemorySystem()

# 检索记忆
result = system.retrieve("我的B站UID是多少？")

# 根据置信度决策
if result.decision == "use":
    # 高置信度，直接使用
    print(result.answer)
elif result.decision == "confirm":
    # 中等置信度，需要确认
    print(result.clarification_question)
else:
    # 低置信度，承认不知道
    print(result.answer)
```

## 验证评分算法

```python
# 1. 关键词重叠度
keyword_overlap = len(query_keywords & content_keywords) / len(query_keywords)

# 2. 语义相关性 (来自memory_search)
semantic_relevance = retrieval_score

# 3. 综合置信度
confidence = keyword_overlap * 0.3 + semantic_relevance * 0.7
```

## 统计追踪

系统会自动追踪：
- 总查询数
- 高置信度直接使用次数/比例
- 中等置信度需确认次数/比例
- 低置信度未知次数/比例
- 最终承认不知道次数/比例

## 下一步改进

1. **LLM-based验证**
   - 用LLM判断记忆内容是否真正回答查询
   - 比关键词匹配更准确

2. **用户反馈集成**
   - 用户确认/否认后更新记忆权重
   - 强化学习优化置信度阈值

3. **多轮对话上下文**
   - 结合对话历史判断相关性
   - 上下文感知的记忆检索

4. **记忆来源可信度**
   - 不同来源赋予不同权重
   - USER.md > MEMORY.md > 网络搜索

---

*置信度驱动记忆系统 v0.1 原型完成*  
*借鉴 LexChronos 双代理架构*
