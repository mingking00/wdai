# 自适应推理深度评估系统
## Adaptive Reasoning Depth Evaluator (ARDE)

## 核心设计

```
用户输入 → 复杂度评估器 → 推理深度选择 → 执行 → 质量反馈
                ↑                           ↓
                └────── 自适应调整 ←──────┘
```

## 1. 快速复杂度评估器

### 评估维度（每个维度0-10分）

| 维度 | 评估指标 | 高分特征 |
|------|---------|---------|
| **认知负荷** | 步骤数、概念数、依赖关系 | 多步骤、跨领域、高耦合 |
| **不确定性** | 模糊性、信息完整度、目标清晰度 | 模糊描述、信息缺失、目标开放 |
| **创造性** | 原创性要求、设计 vs 执行 | 从零设计、创新方案、无标准答案 |
| **风险成本** | 错误代价、可逆性、安全影响 | 不可逆、高成本、安全敏感 |

### 快速启发式规则

```python
class ComplexityEvaluator:
    """快速评估问题复杂度"""
    
    # 关键词信号 - 快速分类
    KEYWORDS = {
        "minimal": [
            "在吗", "ok", "好的", "确认", "收到",
            "简单", "快速", "直接", "明确",
            "heartbeat", "ping", "test"
        ],
        "fast": [
            "查看", "显示", "列出", "获取",
            "多少", "什么", "哪里", "如何",
            "文件", "路径", "状态", "日志"
        ],
        "core": [
            "分析", "诊断", "优化", "修复",
            "设计", "实现", "集成", "部署",
            "错误", "问题", "bug", "性能"
        ],
        "deep": [
            "架构", "框架", "系统", "原理",
            "第一性", "泛化", "抽象", "本质",
            "研究", "探索", "创新", "预测"
        ]
    }
    
    def evaluate(self, query: str, context: dict) -> ComplexityScore:
        """5秒内完成评估"""
        score = ComplexityScore()
        query_lower = query.lower()
        
        # 1. 关键词匹配（最快路径）
        for level, keywords in self.KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                score.keyword_level = level
                break
        
        # 2. 结构分析
        score.has_code = "```" in query or "code" in query_lower
        score.has_multiple_questions = query.count("?") > 1 or "和" in query
        score.length_factor = min(len(query) / 100, 10)  # 长度归一化
        
        # 3. 上下文评估
        score.context_history = len(context.get("recent_turns", []))
        score.is_followup = self._is_followup(query, context)
        
        return score
    
    def _is_followup(self, query: str, context: dict) -> bool:
        """判断是否是追问"""
        followup_markers = ["那", "还有", "另外", "继续", "然后呢", "另外呢"]
        return any(m in query for m in followup_markers)
```

## 2. 推理深度决策矩阵

### 决策逻辑

```python
class DepthSelector:
    """基于评估结果选择推理深度"""
    
    def select(self, score: ComplexityScore) -> ReasoningDepth:
        """
        决策矩阵：综合多个信号
        """
        
        # 信号权重
        signals = {
            "keyword": self._score_keyword(score.keyword_level),
            "structure": self._score_structure(score),
            "context": self._score_context(score),
            "domain": self._score_domain(score)
        }
        
        total_score = sum(signals.values())
        
        # 阈值决策
        if total_score <= 3:
            return ReasoningDepth.NO_THINK    # 直接回答
        elif total_score <= 6:
            return ReasoningDepth.FAST_THINK  # 快速思考
        elif total_score <= 9:
            return ReasoningDepth.CORE_THINK  # 核心推理
        else:
            return ReasoningDepth.DEEP_THINK  # 深度思考
    
    def _score_keyword(self, level: str) -> int:
        mapping = {"minimal": 1, "fast": 2, "core": 4, "deep": 6}
        return mapping.get(level, 3)
    
    def _score_structure(self, score: ComplexityScore) -> int:
        s = 0
        if score.has_code: s += 2
        if score.has_multiple_questions: s += 2
        s += score.length_factor * 0.5
        return int(s)
    
    def _score_context(self, score: ComplexityScore) -> int:
        """上下文复杂度"""
        if score.is_followup:
            return 1  # 追问通常更简单
        if score.context_history > 5:
            return 3  # 长对话需要维持上下文
        return 2
    
    def _score_domain(self, score: ComplexityScore) -> int:
        """领域复杂度评估"""
        # 可扩展：基于domain分类器
        return 2  # 默认中等
```

## 3. 实际应用示例

### 示例1：极简查询
```
用户："在吗"
评估：
- 关键词：minimal (在吗)
- 结构：无代码，单问题，短文本
- 上下文：无历史
得分：1 + 1 + 1 = 3
深度：NO_THINK → 直接回复："在"
```

### 示例2：常规任务
```
用户："查看当前目录文件"
评估：
- 关键词：fast (查看)
- 结构：无代码，单问题，短文本
- 上下文：无特殊
得分：2 + 1 + 2 = 5
深度：FAST_THINK → 执行命令，简洁输出
```

### 示例3：诊断问题
```
用户："为什么我的代码运行报错？"
评估：
- 关键词：core (为什么，报错)
- 结构：可能含代码，问题分析类
- 上下文：需要诊断推理
得分：4 + 3 + 2 = 9
深度：CORE_THINK → 分析错误，给出解决方案
```

### 示例4：架构设计
```
用户："设计一个可扩展的微服务架构，需要考虑高可用和容错"
评估：
- 关键词：deep (架构，设计，可扩展)
- 结构：多需求点，设计类
- 上下文：复杂系统设计
得分：6 + 4 + 3 = 13
深度：DEEP_THINK → 多维度分析，给出完整方案
```

## 4. 反馈学习与自适应

### 质量评估

```python
class QualityFeedback:
    """根据实际结果调整评估器"""
    
    def evaluate_output(self, output: str, user_feedback: str) -> float:
        """
        评估输出质量，返回0-1分数
        """
        # 负面信号
        negative_signals = [
            "不对", "错误", "不是", "重新", "再想想",
            "太长", "太复杂", "看不懂", "不对",
            "废话", "啰嗦", "直接点"
        ]
        
        # 正面信号
        positive_signals = [
            "对", "正确", "好的", "明白了", "谢谢",
            "清晰", "简洁", "准确", "完美"
        ]
        
        score = 0.5  # 中性起点
        
        for signal in negative_signals:
            if signal in user_feedback:
                score -= 0.2
        
        for signal in positive_signals:
            if signal in user_feedback:
                score += 0.2
        
        return max(0, min(1, score))
    
    def adjust_threshold(self, complexity: int, quality: float):
        """根据质量反馈调整决策阈值"""
        if quality < 0.3:
            # 质量差，可能是深度不够
            self.thresholds[complexity] -= 0.5
        elif quality > 0.8:
            # 质量好，可适当降低阈值节省资源
            self.thresholds[complexity] += 0.2
```

## 5. 系统提示词模板

### 极简模式 (NO_THINK)
```
System: 你是一位直接高效的助手。用户问题很简单，用最简短的方式回答即可。
禁止：解释、举例、多余文字。
示例：
用户："在吗" → 回复："在"
用户："今天星期几" → 回复："星期三"
```

### 快速模式 (FAST_THINK)
```
System: 你是一位高效的执行者。用户需要快速完成任务。
要求：
- 直接执行或给出简明步骤
- 1-2句话解释核心逻辑
- 如果有代码，只给关键片段
```

### 核心模式 (CORE_THINK)
```
System: 你是一位专业的分析师。用户需要深度分析或解决复杂问题。
要求：
- 分析根本原因
- 提供结构化解决方案
- 考虑边界情况和替代方案
- 必要时询问澄清问题
```

### 深度模式 (DEEP_THINK)
```
System: 你是一位资深架构师/研究员。用户需要系统性的深度分析。
要求：
- 多维度分析（技术、业务、成本、风险）
- 第一性原理思考
- 提供完整设计方案
- 包含验证思路和优化建议
- 必要时引用最佳实践
```

## 6. 实时决策流程

```python
class AdaptiveReasoningSystem:
    """完整系统入口"""
    
    def __init__(self):
        self.evaluator = ComplexityEvaluator()
        self.selector = DepthSelector()
        self.feedback = QualityFeedback()
        
    def process(self, query: str, context: dict) -> Response:
        # 1. 快速评估（<100ms）
        score = self.evaluator.evaluate(query, context)
        
        # 2. 选择深度
        depth = self.selector.select(score)
        
        # 3. 构建提示
        system_prompt = self._get_prompt(depth)
        
        # 4. 执行（使用选择的深度）
        response = self._execute(query, system_prompt, depth)
        
        # 5. 记录用于反馈
        self._record(query, score, depth, response)
        
        return response
    
    def _get_prompt(self, depth: ReasoningDepth) -> str:
        prompts = {
            ReasoningDepth.NO_THINK: NO_THINK_PROMPT,
            ReasoningDepth.FAST_THINK: FAST_THINK_PROMPT,
            ReasoningDepth.CORE_THINK: CORE_THINK_PROMPT,
            ReasoningDepth.DEEP_THINK: DEEP_THINK_PROMPT
        }
        return prompts[depth]
```

## 7. 实施建议

### 阶段1：基于规则（立即实施）
- 使用关键词启发式
- 硬编码阈值
- 快速部署

### 阶段2：机器学习（1-2周）
- 收集标注数据
- 训练轻量级分类器
- 自动阈值调整

### 阶段3：强化学习（长期）
- 基于用户反馈优化
- 个性化适配
- 上下文感知

## 8. 关键指标

| 指标 | 目标 | 监控方式 |
|------|------|---------|
| 平均响应时间 | < 2s | 按深度分组统计 |
| 准确率 | > 90% | 用户反馈+自动评估 |
| Token效率 | 节省30% | 对比固定深度 |
| 用户满意度 | > 4.5/5 | 主动收集反馈 |

---

**这就是完整的自适应推理评估系统。**

要我立即实施这套系统吗？可以先从阶段1（关键词规则）开始。
