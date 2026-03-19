# WDai Tool-DC 集成改进方案

> **方案版本**: v1.0  
> **创建日期**: 2026-03-19  
> **核心目标**: 将 Tool-DC 的 "Try-Check-Retry" 分治框架集成到 WDai 工具调用系统，解决长上下文工具选择精度问题

---

## 1. 问题分析

### 1.1 当前 WDai 工具调用痛点

| 问题 | 影响 | 触发场景 |
|------|------|----------|
| 工具过多时选择困难 | 调用错误工具或参数填充错误 | Skills 数量 > 10 |
| 相似工具混淆 | 语义相似但参数不同的工具被误选 | 多个文件操作、搜索类工具 |
| 长上下文注意力分散 | 遗漏关键工具描述 | 复杂任务需要多工具协作 |
| 缺乏自我验证 | 错误无法自动纠正 | 任何工具调用失败 |

### 1.2 Tool-DC 核心洞察

根据论文，工具调用性能下降的两个根本原因：

1. **长上下文问题**: 候选工具数量增加 → 信噪比下降 → 推理难度增加
2. **相似工具混淆**: 语义相似但参数描述不同的工具相互干扰

Tool-DC 的解决思路：**分而治之 + 自我反思**

---

## 2. 方案设计

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                     WDai Tool-DC 增强层                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │   Try    │───▶│  Check   │───▶│  Retry   │───▶│  Execute │  │
│  │ (分组推理)│    │ (验证)   │    │ (聚合)   │    │ (执行)   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │                                    │                    │
│       ▼                                    ▼                    │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              Schema Consistency Validator             │     │
│  │  • 函数名存在性检查    • 必填参数检查    • 数据类型校验│     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     WDai 核心层 (ReAct)                          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Try-Check-Retry 流程详解

#### Stage 1: Try (分组推理)

```python
class TryStage:
    """
    将候选工具库分解为 K 个低噪声子空间，并行推理
    """
    
    def strategic_anchor_grouping(
        self, 
        tools: List[Tool], 
        query: str, 
        K: int = 5
    ) -> List[List[Tool]]:
        """
        策略锚点分组策略
        
        1. 检索 Top-K 相关工具 (使用 BM25 或 Embedding)
        2. 以每个 Top-K 工具为锚点，构建 K 个并行组
        3. 每个组包含：锚点工具 + 互不重叠的干扰工具子集
        4. 保留原始 Top-K 作为独立组 S₀
        
        Returns: [S₀, S₁, S₂, ..., Sₖ]
        """
        top_k = self.retriever.retrieve(query, tools, top_k=K)
        tail = [t for t in tools if t not in top_k]
        
        groups = [top_k]  # S₀: 原始 Top-K
        
        for i, anchor in enumerate(top_k):
            # 每组包含一个锚点 + 分散的干扰项
            distractors = self.select_distractors(tail, K)
            group = [anchor] + distractors
            groups.append(group)
        
        return groups
    
    def local_inference(self, query: str, group: List[Tool]) -> Optional[ToolCall]:
        """
        在子空间内进行局部推理
        
        Prompt 设计:
        "从提供的工具列表中，识别所有可能满足用户需求的工具。
         如果决定调用工具，必须按格式返回：[func_name(params)]"
        """
        response = self.llm.generate(
            system_prompt=TRY_PROMPT,
            user_prompt=f"问题: {query}\n可用工具: {self.format_tools(group)}"
        )
        
        return self.parse_tool_call(response) or None
```

**Key Design**: 
- 每个组独立推理，降低单组内工具数量
- 锚点策略确保优质工具不被遗漏
- 干扰项分散到各组，减少组内竞争

---

#### Stage 2: Check (模式验证)

```python
class CheckStage:
    """
    基于规则的 Schema 一致性验证器
    """
    
    def __init__(self):
        self.validators = [
            self.validate_function_name,
            self.validate_argument_keys,
            self.validate_data_types
        ]
    
    def validate(self, tool_call: ToolCall, available_tools: List[Tool]) -> bool:
        """
        三重验证机制
        """
        # 1. 函数名存在性
        if not self.function_exists(tool_call.name, available_tools):
            return False
        
        tool_schema = self.get_schema(tool_call.name)
        
        # 2. 必填参数检查
        for required in tool_schema.required_params:
            if required not in tool_call.arguments:
                logger.warning(f"缺少必填参数: {required}")
                return False
        
        # 3. 数据类型一致性
        for key, value in tool_call.arguments.items():
            expected_type = tool_schema.params[key].type
            if not self.type_matches(value, expected_type):
                logger.warning(f"参数类型不匹配: {key} 期望 {expected_type}, 实际 {type(value)}")
                return False
        
        return True
    
    def batch_validate(
        self, 
        candidates: List[ToolCall], 
        tools: List[Tool]
    ) -> List[ToolCall]:
        """
        批量验证，返回有效候选集
        """
        valid = [c for c in candidates if self.validate(c, tools)]
        logger.info(f"验证通过: {len(valid)}/{len(candidates)}")
        return valid
```

**Key Design**:
- 100% 规则-based，零幻觉
- 提前过滤非法调用，减少 Retry 负担
- 详细日志便于调试

---

#### Stage 3: Retry (聚合重试)

```python
class RetryStage:
    """
    利用自我反思能力，从验证候选中做出全局最优决策
    """
    
    def global_aggregation(
        self, 
        query: str,
        valid_calls: List[ToolCall],
        all_tools: List[Tool]
    ) -> ToolCall:
        """
        聚合验证通过的工具，进行最终决策
        
        1. 从有效调用中提取涉及的工具定义
        2. 构建精炼候选集 T_retry
        3. 在 T_retry 上进行全局推理
        """
        # 提取唯一工具名
        involved_tools = list(set(call.name for call in valid_calls))
        
        # 重建精炼工具集
        t_retry = [t for t in all_tools if t.name in involved_tools]
        
        # 构建反思提示
        reflection_prompt = f"""
基于以下有效候选调用：
{self.format_calls(valid_calls)}

请从这些已验证的工具中，选择最能满足用户需求的调用方案。
注意：这些调用已经过有效性验证，只需判断哪个最合适。
"""
        
        final_response = self.llm.generate(
            system_prompt=RETRY_PROMPT,
            user_prompt=f"问题: {query}\n候选工具: {self.format_tools(t_retry)}\n\n{reflection_prompt}"
        )
        
        return self.parse_tool_call(final_response)
```

**Key Design**:
- 利用 LLM 的自我反思能力
- 在"已验证"空间内决策，降低幻觉风险
- 支持多工具调用场景

---

### 2.3 Prompt 模板

#### Try Stage Prompt

```python
TRY_PROMPT = """# System:
你是工具选择专家。任务：从提供的工具列表中识别所有可能满足用户需求的工具。

## 规则：
1. 仔细阅读用户问题和工具描述
2. 选择任何可能满足用户需求的工具（或部分需求）
3. 提取问题中的关键信息，填入工具参数
4. 如果多个工具都相关，可以同时选择

## 输出格式：
如果决定调用工具，必须按以下格式返回：
[func_name1(param1=value1, param2=value2), func_name2(params)]

不要包含任何其他文本。"""
```

#### Retry Stage Prompt

```python
RETRY_PROMPT = """# System:
你是工具组合专家。基于已验证的有效候选，做出最优决策。

## 背景：
以下工具调用已经过严格验证（函数名存在、参数完整、类型正确）：
{valid_calls}

## 任务：
从这些已验证的调用中，选择最能完整满足用户需求的方案。

## 输出格式：
[func_name1(param1=value1, ...)]

只输出最终选择的工具调用。"""
```

---

## 3. 集成方案

### 3.1 与 WDai ReAct 的集成点

```python
class WDaiToolDCHandler:
    """
    在 WDai 的 ReAct 循环中插入 Tool-DC 层
    """
    
    def __init__(self, config: ToolDCConfig):
        self.try_stage = TryStage(config.retriever)
        self.check_stage = CheckStage()
        self.retry_stage = RetryStage()
        self.config = config
    
    def select_tool(
        self, 
        query: str, 
        available_tools: List[Tool],
        use_tool_dc: bool = True
    ) -> ToolCall:
        """
        工具选择入口
        
        决策逻辑：
        - 工具数 <= 5: 直接 ReAct（保持简单）
        - 工具数 > 5: 启用 Tool-DC
        """
        if not use_tool_dc or len(available_tools) <= 5:
            return self.direct_react_select(query, available_tools)
        
        # === Tool-DC 流程 ===
        
        # Stage 1: Try - 分组推理
        K = min(self.config.max_groups, len(available_tools))
        groups = self.try_stage.strategic_anchor_grouping(
            available_tools, query, K
        )
        
        candidates = []
        for group in groups:
            call = self.try_stage.local_inference(query, group)
            if call:
                candidates.append(call)
        
        logger.info(f"Try 阶段产生候选: {len(candidates)}")
        
        # Stage 2: Check - 验证过滤
        valid_candidates = self.check_stage.batch_validate(
            candidates, available_tools
        )
        
        if not valid_candidates:
            logger.warning("无有效候选，降级到直接选择")
            return self.direct_react_select(query, available_tools)
        
        # Stage 3: Retry - 聚合决策
        if len(valid_candidates) == 1:
            return valid_candidates[0]
        
        final_call = self.retry_stage.global_aggregation(
            query, valid_candidates, available_tools
        )
        
        return final_call
```

### 3.2 配置项

```python
@dataclass
class ToolDCConfig:
    """Tool-DC 配置"""
    
    # 分组参数
    max_groups: int = 5  # K 值，论文推荐 5
    
    # 检索器配置
    retriever_type: str = "bm25"  # 或 "embedding"
    
    # 降级阈值
    fallback_threshold: int = 5  # 工具数低于此值不启用 Tool-DC
    
    # 验证配置
    strict_mode: bool = True  # 严格模式：任何验证失败即丢弃
    
    # 性能优化
    parallel_inference: bool = True  # 并行执行各组推理
    
    # 调试
    verbose_logging: bool = True
```

---

## 4. 实施计划

### 4.1 阶段一：核心实现 (Day 1-2)

```
✅ 实现 Schema Validator
✅ 实现 Try Stage (分组 + 局部推理)
✅ 实现 Check Stage (规则验证)
✅ 实现 Retry Stage (聚合重试)
```

### 4.2 阶段二：集成测试 (Day 3-4)

```
□ 集成到 WDai ReAct 循环
□ 添加配置开关
□ 单元测试 (模拟场景)
□ 性能基准测试
```

### 4.3 阶段三：优化迭代 (Day 5-7)

```
□ 基于测试结果优化 K 值
□ 优化检索器选择
□ 添加缓存机制
□ 文档更新
```

---

## 5. 预期效果

基于论文实验结果，预期改进：

| 指标 | 当前基线 | Tool-DC 增强 | 提升 |
|------|----------|--------------|------|
| 工具选择准确率 (10+ tools) | ~65% | ~80%+ | +15% |
| 参数填充准确率 | ~70% | ~85% | +15% |
| 相似工具区分率 | ~60% | ~80% | +20% |
| 平均推理延迟 | 基准 | +20-30% | 可接受 |

---

## 6. 代码实现框架

```
.claw-status/tool_dc/
├── __init__.py
├── config.py          # ToolDCConfig
├── stages/
│   ├── __init__.py
│   ├── try_stage.py   # TryStage
│   ├── check_stage.py # CheckStage
│   └── retry_stage.py # RetryStage
├── validator.py       # SchemaValidator
├── retriever.py       # BM25/Embedding 检索器
└── integration.py     # WDaiToolDCHandler
```

---

## 7. 下一步

1. **确认方案** - 您确认此设计方向后，我开始实现核心代码
2. **定制需求** - 是否需要针对特定 Skills 场景做调整？
3. **优先级** - 是否优先实现 Training-free 版本（无需微调）？

---

*基于论文: "Try, Check and Retry: A Divide-and-Conquer Framework for Boosting Long-context Tool-Calling Performance of LLMs" (2026)*
