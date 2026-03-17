# Anti-Hacking SRA 优化方案

> 基于Kimi K2.5 RL训练策略的自我反思Agent防Hack设计

## 问题：SRA也会"Hack"

自我反思Agent可能出现的问题：

| Hack类型 | 表现 | 危害 |
|----------|------|------|
| **表面化反思** | 只总结显而易见的内容 | 无深度洞察 |
| **虚假模式** | 创造不存在的"规律" | 误导后续决策 |
| **模板套用** | 用固定格式应付所有场景 | 失去灵活性 |
| **过度乐观** | 只记录成功经验，回避失败 | 无法真正改进 |
| **为了反思而反思** | 无价值的频繁复盘 | 浪费token |

---

## 解决方案：多层Rubric评估

### 1. 过程约束 (Process Rubric)

**K2.5策略迁移**：强制要求完整的反思路径

```python
# 反思必须包含的要素
def validate_reflection(reflection: dict) -> float:
    rubric_score = 0.0
    
    # 1. 事实依据 (必须有具体引用)
    if has_concrete_evidence(reflection):
        rubric_score += 0.25
    
    # 2. 因果分析 (不止于"发生了什么")
    if has_causal_analysis(reflection):
        rubric_score += 0.25
    
    # 3. 可执行建议 (不只发现问题，还要解决)
    if has_actionable_recommendation(reflection):
        rubric_score += 0.25
    
    # 4. 验证机制 (如何确认改进有效)
    if has_validation_plan(reflection):
        rubric_score += 0.25
    
    return rubric_score
```

---

### 2. 多维度Outcome评估

**K2.5策略迁移**：不只看"有没有反思"，还要看"反思质量"

```python
class ReflectionOutcome:
    """反思结果的多维度评估"""
    
    def __init__(self):
        self.dimensions = {
            # 1. 新颖性 - 是否发现新的洞察
            'novelty': 0.0,
            
            # 2. 可复用性 - 能否应用到其他场景
            'reusability': 0.0,
            
            # 3. 验证度 - 是否有证据支撑
            'verifiability': 0.0,
            
            # 4. 影响度 - 对后续工作的实际帮助
            'impact': 0.0
        }
    
    def compute_outcome_reward(self) -> float:
        # 加权平均
        weights = {'novelty': 0.3, 'reusability': 0.3, 
                   'verifiability': 0.2, 'impact': 0.2}
        return sum(self.dimensions[k] * weights[k] for k in weights)
```

---

### 3. Self-Critical机制

**K2.5策略迁移**：让SRA自己评判自己的反思

```python
def self_critical_reflection(raw_reflection: str) -> dict:
    """
    自我批判式反思流程
    """
    # 1. 生成初步反思
    initial = generate_reflection(raw_reflection)
    
    # 2. 自我质疑 (Critique)
    critique = ask_critique_questions(initial)
    # - "这个洞察有证据支撑吗？"
    # - "是否存在其他解释？"
    # - "这个建议真的可执行吗？"
    
    # 3. 基于质疑改进
    improved = refine_based_on_critique(initial, critique)
    
    # 4. 外部验证 (类似K2.5的GRM)
    verified = external_verification(improved)
    
    return {
        'reflection': verified,
        'critique_log': critique,
        'confidence_score': compute_confidence(verified)
    }
```

---

### 4. 频率惩罚机制

**K2.5策略迁移**：防止"为了反思而反思"

```python
class ReflectionFrequencyController:
    """反思频率控制 - 类似长度惩罚"""
    
    def __init__(self):
        self.reflection_history = []
        self.min_interval_hours = 4  # 最短反思间隔
        
    def compute_frequency_penalty(self, proposed_time: datetime) -> float:
        """
        惩罚过于频繁的反思
        """
        if not self.reflection_history:
            return 0.0
        
        last_reflection = self.reflection_history[-1]
        hours_since_last = (proposed_time - last_reflection).total_seconds() / 3600
        
        if hours_since_last < self.min_interval_hours:
            # 惩罚 = 1.0 (完全无效)
            return 1.0
        elif hours_since_last < self.min_interval_hours * 2:
            # 部分惩罚
            return 0.5
        else:
            return 0.0
    
    def should_reflect(self, new_content: str) -> bool:
        """
        判断是否真的需要反思
        """
        # 必须有足够新内容
        if len(new_content) < 1000:  # 至少1000字符新对话
            return False
            
        # 必须有值得反思的"事件"
        if not contains_reflectable_events(new_content):
            return False
            
        return True
```

---

### 5. Task-Level路径验证

**K2.5策略迁移**：确保反思走了"正确的路"

```python
def validate_reflection_path(original_content: str, reflection: dict) -> bool:
    """
    验证反思是否正确理解了原始内容
    """
    # 1. 关键信息提取验证
    key_facts = extract_key_facts(original_content)
    reflected_facts = extract_key_facts(reflection['content'])
    
    fact_overlap = compute_overlap(key_facts, reflected_facts)
    if fact_overlap < 0.7:  # 70%关键信息覆盖
        return False  # 反思偏离了原始内容
    
    # 2. 逻辑一致性验证
    if not is_logically_consistent(reflection):
        return False
    
    # 3. 无幻觉验证
    if contains_hallucination(reflection, original_content):
        return False
    
    return True
```

---

## 完整的Anti-Hacking SRA Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     Anti-Hacking SRA Pipeline                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 触发检查                                                     │
│     ├─ 频率惩罚 → 防止过度反思                                   │
│     ├─ 内容检查 → 确认有值得反思的事件                           │
│     └─ ✓ 通过 → 继续                                            │
│                                                                  │
│  2. 生成初步反思                                                 │
│     ├─ 提取关键事实                                              │
│     ├─ 分析因果                                                  │
│     └─ 提出建议                                                  │
│                                                                  │
│  3. Self-Critical                                                │
│     ├─ 自我质疑                                                  │
│     ├─ 识别潜在问题                                              │
│     └─ 改进反思                                                  │
│                                                                  │
│  4. Rubric评估                                                   │
│     ├─ 事实依据 (25%)                                            │
│     ├─ 因果分析 (25%)                                            │
│     ├─ 可执行建议 (25%)                                          │
│     └─ 验证机制 (25%)                                            │
│                                                                  │
│  5. Outcome评估                                                  │
│     ├─ 新颖性                                                    │
│     ├─ 可复用性                                                  │
│     ├─ 验证度                                                    │
│     └─ 影响度                                                    │
│                                                                  │
│  6. 路径验证                                                     │
│     ├─ 关键信息覆盖 > 70%                                        │
│     ├─ 逻辑一致性                                                │
│     └─ 无幻觉                                                    │
│                                                                  │
│  7. 最终决策                                                     │
│     ├─ 总分 > 阈值 → 接受反思，记录到IER                        │
│     └─ 总分 < 阈值 → 拒绝反思，等待更多内容                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 实施计划

### Phase 1: 基础约束 (1-2天)
- [ ] 实现Rubric评估器
- [ ] 添加频率控制
- [ ] 基础路径验证

### Phase 2: Self-Critical (3-5天)
- [ ] 自我质疑Prompt设计
- [ ] Critique流程实现
- [ ] 改进循环

### Phase 3: Outcome优化 (1周)
- [ ] 多维度评分
- [ ] 历史效果追踪
- [ ] 自适应阈值

---

## 预期效果

| 指标 | 优化前 | 优化后目标 |
|------|--------|-----------|
| 反思空洞率 | ~40% | <10% |
| 虚假模式率 | ~20% | <5% |
| 可执行建议占比 | ~30% | >70% |
| IER经验复用率 | ~25% | >60% |

---

*设计基于Kimi K2.5 RL训练策略迁移*
