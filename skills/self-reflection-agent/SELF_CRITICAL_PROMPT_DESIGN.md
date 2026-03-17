# Anti-Hacking SRA Phase 2: Self-Critical Prompt设计

## 核心概念

Self-Critical机制让SRA在生成初步反思后，**自己质疑自己**，发现并修正问题。

```
初步反思 → Self-Critical质疑 → 改进 → 最终反思
```

---

## 质疑维度 (Critique Dimensions)

### 1. 事实性质疑 (Factual Critique)

**Prompt模板:**
```
请审查以下反思内容的事实准确性:

[初步反思内容]

请回答:
1. 反思中提到的具体事件/数据是否有原文支撑?
2. 是否存在过度推断或假设?
3. 时间线是否正确?
4. 引用的代码/命令是否准确?

如果有问题,请指出具体问题并给出修正建议。
```

**预期输出格式:**
```json
{
  "factual_issues": [
    {
      "claim": "声称XXX",
      "issue": "缺乏原文支撑",
      "evidence": "原文实际说的是YYY",
      "suggestion": "修正为YYY"
    }
  ],
  "confidence": 0.8
}
```

---

### 2. 逻辑性质疑 (Logical Critique)

**Prompt模板:**
```
请审查以下反思的逻辑一致性:

[初步反思内容]

请检查:
1. 因果推断是否合理? (A导致B是否有充分证据)
2. 是否存在归因偏差? (将结果归因于错误原因)
3. 建议与问题是否匹配? (解决方案是否针对问题)
4. 是否存在自相矛盾?

如果发现逻辑问题,请指出并建议修正。
```

**预期输出格式:**
```json
{
  "logical_issues": [
    {
      "inference": "推断XXX导致YYY",
      "issue": "归因偏差",
      "reason": "还有其他因素ZZZ影响",
      "suggestion": "应归因于XXX和ZZZ共同作用"
    }
  ],
  "confidence": 0.75
}
```

---

### 3. 深度质疑 (Depth Critique)

**Prompt模板:**
```
请审查以下反思是否足够深入:

[初步反思内容]

请评估:
1. 是否只描述了表面现象?(5 Whys测试)
2. 是否触及根本原因?
3. 建议是否可操作?
4. 是否有验证机制?
5. 能否提炼出通用模式?

如果反思过于肤浅,请引导深入:
- 问"为什么"至少3次
- 挖掘根本原因
- 提出更深刻的洞察
```

**预期输出格式:**
```json
{
  "depth_issues": [
    {
      "observation": "观察到XXX",
      "surface_level": true,
      "root_cause": "根本原因是YYY",
      "deeper_insight": "这反映了ZZZ模式"
    }
  ],
  "confidence": 0.7
}
```

---

### 4. 实用性质疑 (Utility Critique)

**Prompt模板:**
```
请审查以下反思的实用价值:

[初步反思内容]

请评估:
1. 提取的技巧是否可复用?
2. 建议是否能在下次类似场景中应用?
3. 是否有具体的实施步骤?
4. 如何验证建议的有效性?
5. 是否需要更新SOUL.md或其他文档?

如果实用性不足,请提出改进建议。
```

**预期输出格式:**
```json
{
  "utility_issues": [
    {
      "recommendation": "建议XXX",
      "issue": "过于抽象",
      "improved_version": "具体步骤: 1. ... 2. ... 3. ...",
      "verification": "可通过YYY验证"
    }
  ],
  "confidence": 0.85
}
```

---

## 完整Critique Pipeline

```python
class SelfCriticalPipeline:
    """
    自我批判式反思流程
    """
    
    def critique(self, initial_reflection: str, original_content: str) -> Dict:
        # 1. 事实性质疑
        factual = self._factual_critique(initial_reflection, original_content)
        
        # 2. 逻辑性质疑
        logical = self._logical_critique(initial_reflection)
        
        # 3. 深度质疑
        depth = self._depth_critique(initial_reflection)
        
        # 4. 实用性质疑
        utility = self._utility_critique(initial_reflection)
        
        # 5. 综合评分
        confidence = (factual['confidence'] + logical['confidence'] + 
                     depth['confidence'] + utility['confidence']) / 4
        
        # 6. 生成改进建议
        improvements = self._generate_improvements(
            factual, logical, depth, utility
        )
        
        return {
            'factual': factual,
            'logical': logical,
            'depth': depth,
            'utility': utility,
            'confidence': confidence,
            'improvements': improvements,
            'should_refine': confidence < 0.7 or len(improvements) > 3
        }
    
    def refine(self, initial_reflection: str, critique_result: Dict) -> str:
        """
        基于质疑结果改进反思
        """
        prompt = f"""
基于以下质疑结果,请改进原始反思:

[原始反思]
{initial_reflection}

[质疑结果]
事实问题: {json.dumps(critique_result['factual'], ensure_ascii=False)}
逻辑问题: {json.dumps(critique_result['logical'], ensure_ascii=False)}
深度问题: {json.dumps(critique_result['depth'], ensure_ascii=False)}
实用性问题: {json.dumps(critique_result['utility'], ensure_ascii=False)}

请输出改进后的反思,解决以上问题。
"""
        # 调用LLM生成改进版本
        improved = self._call_llm(prompt)
        return improved
```

---

## 集成到SRA

在 `_reflect_daily()` 中添加:

```python
def _reflect_daily(self, date: str, exp_prompt: str = "") -> Dict:
    # ... Phase 1代码 ...
    
    # ===== Anti-Hacking Phase 2: Self-Critical =====
    self.logger.info("[Anti-Hacking] 执行Self-Critical质疑...")
    
    # 生成初步反思报告
    initial_report = self._generate_daily_report(date, tips, patterns, errors)
    
    # Self-Critical质疑
    critique_result = self.self_critical_pipeline.critique(
        initial_report, content
    )
    
    if critique_result['should_refine']:
        self.logger.info(f"[Anti-Hacking] 反思需要改进,置信度: {critique_result['confidence']:.2f}")
        
        # 改进反思
        improved_report = self.self_critical_pipeline.refine(
            initial_report, critique_result
        )
        
        # 使用改进版本
        report = improved_report
        
        self.logger.success("[Anti-Hacking] 反思已改进")
    else:
        self.logger.info("[Anti-Hacking] 反思通过Self-Critical检查")
    
    # ... 继续Phase 1的Rubric评估 ...
```

---

## 多轮改进循环

```
初步反思 → Critique → 改进 → Critique → 改进 → ... → 最终反思
           ↑___________________________________________|
           
           (最多3轮,直到confidence >= 0.8 或 improvements < 2)
```

---

## 预期效果

| 问题类型 | Phase 1检测 | Phase 2修复 |
|----------|-------------|-------------|
| 事实错误 | ❌ 拒绝 | ✅ 自动修正 |
| 逻辑漏洞 | ❌ 拒绝 | ✅ 自动修正 |
| 过于肤浅 | ❌ 拒绝 | ✅ 深化洞察 |
| 不够实用 | ❌ 拒绝 | ✅ 具体化建议 |

---

*Phase 2设计完成,等待实现*
