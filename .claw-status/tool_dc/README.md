# Tool-DC for WDai

基于论文 **"Try, Check and Retry: A Divide-and-Conquer Framework for Boosting Long-context Tool-Calling Performance of LLMs"** 的完整实现。

---

## 核心特性

| 特性 | 描述 |
|------|------|
| **分治策略** | Try-Check-Retry 三阶段处理长上下文工具选择 |
| **零幻觉验证** | Schema 规则验证，确保调用有效性 |
| **自我反思** | Retry 阶段利用 LLM 自我反思做最终决策 |
| **自动降级** | 工具数≤5时自动使用简单策略 |
| **BM25 检索** | 内置 BM25，无需外部依赖 |
| **Skills 适配** | 支持 OpenAI/OpenAPI/Python/JSON 多种格式 |
| **Kimi 集成** | 内置 Kimi API 接口 |
| **ReAct 集成** | 完整 ReAct + Tool-DC 循环实现 |
| **多格式解析** | 支持 7 种 LLM 输出格式自动识别 |
| **并行推理** | ThreadPoolExecutor 实现真正的并行 |
| **WDai 集成** | 与 OpenClaw/WDai 无缝集成 |

---

## 架构

```
User Query → Try Stage → Check Stage → Retry Stage → Execute
                ↓            ↓              ↓
           [分组推理]    [规则验证]     [聚合决策]
                ↑
           BM25 检索器 (初始筛选)
```

---

## 快速开始

### 1. 基本使用

```python
from tool_dc import create_tool_dc_handler
from tool_dc.models import Tool, ToolParam, ToolParamType

# 定义工具
tools = [
    Tool(
        name="file_read",
        description="读取文件",
        parameters=[ToolParam("path", ToolParamType.STRING, "路径", required=True)],
        required_params=["path"]
    ),
]

# 创建处理器
handler = create_tool_dc_handler(llm=your_llm)

# 选择工具
result = handler.select_tool("读取 /tmp/test.txt", tools)
if result.success:
    print(f"选中: {result.final_call}")
```

### 2. Kimi API 使用

```python
from tool_dc.llm.kimi import create_kimi_llm

# 自动读取 KIMI_API_KEY 环境变量
llm = create_kimi_llm(model="kimi-k2.5")

# 或显式指定
llm = create_kimi_llm(api_key="your_key", model="kimi-k2.5")

# 使用
response = llm.generate("你的提示")
```

### 3. ReAct + Tool-DC

```python
from tool_dc.integration.react_integration import create_react_tool_dc

react = create_react_tool_dc(llm=llm, tools=tools, max_iterations=10)

result = react.run("帮我读取配置文件")

print(f"成功: {result.success}")
print(f"步骤数: {result.total_steps}")
print(f"答案: {result.final_answer}")

# 查看详细步骤
for step in result.steps:
    print(f"Step {step.step_number}:")
    print(f"  Thought: {step.thought}")
    print(f"  Action: {step.action}")
    print(f"  Tool-DC: 候选={len(step.tool_dc_result.try_candidates)}")
```

### 4. Skills 自动转换

```python
from tool_dc.adapters import WDaiSkillAdapter, WDaiSkillRegistry

# OpenAI Schema → Tool
tool = WDaiSkillAdapter.from_openai_schema(schema)

# Python 函数 → Tool
tool = WDaiSkillAdapter.from_python_function(my_func)

# OpenAPI 文件 → Tools
tools = WDaiSkillAdapter.from_openapi_schema("api.json")

# Skills 目录扫描
registry = WDaiSkillRegistry(skills_dir="/path/to/skills")
tools = registry.scan_skills()
```

### 5. BM25 检索器

```python
from tool_dc.retrievers import BM25Retriever

retriever = BM25Retriever(k1=1.5, b=0.75)
retriever.build_index(tools)

# 检索
results = retriever.retrieve("搜索关键词", tools, top_k=5)

# 集成到 Tool-DC
handler = create_tool_dc_handler(llm=llm, retriever=retriever)
```

### 6. WDai 实际集成

```python
from tool_dc.integration.wdai_openclaw import create_wdai_tool_dc

# 创建 WDai Tool-DC 实例
wdai = create_wdai_tool_dc(api_key="your_key")

# 加载 Skills
wdai.load_skills()

# 工具选择 + 执行
result = wdai.select_and_execute("读取配置文件")
print(f"选中工具: {result['tool_call']['name']}")
print(f"执行结果: {result['result']}")

# 或聊天接口
response = wdai.chat("搜索 AI 新闻")
print(response['response'])
```

### 7. 多格式解析器

```python
from tool_dc.parsers import parse_tool_call, parse_multiple_tool_calls

# 自动识别格式
response = '[file_read(path="/tmp/test.txt")]'
call = parse_tool_call(response)

# 支持格式:
# - [func(args)]           方括号
# - {"name": "func", ...}   JSON
# - <tool>func</tool>      XML
# - ```json {...} ```      Markdown
# - Action: func           ReAct
# - func: args             纯文本

# 多工具调用
multi = '[func1(args1), func2(args2)]'
calls = parse_multiple_tool_calls(multi)
```

### 8. 并行推理

```python
from tool_dc.config import ToolDCConfig

# 启用并行
config = ToolDCConfig(
    parallel_inference=True,
    max_workers=5
)

handler = create_tool_dc_handler(llm=llm, config=config)

# 性能对比
from tool_dc.parallel import ParallelInferenceEngine

engine = ParallelInferenceEngine(config)
results = engine.benchmark(query, groups, llm, prompt_builder)

print(f"加速比: {results['speedup']:.2f}x")
```

---

## 文件结构

```
tool_dc/
├── __init__.py              # 主入口
├── config.py                # 配置
├── models.py                # 数据模型
├── parallel.py              # 并行推理
├── README.md                # 本文档
├── demo_wdai_integration.py # WDai 集成示例
├── demo_bc_complete.py      # B+C 功能演示
├── demo_ad_complete.py      # A+D 功能演示
├── demo_all_features.py     # 完整功能演示
├── llm/
│   ├── __init__.py
│   └── kimi.py              # Kimi API 接口
├── integration/
│   ├── __init__.py
│   ├── react_integration.py # ReAct 集成
│   └── wdai_openclaw.py     # WDai 集成
├── stages/
│   ├── __init__.py
│   ├── try_stage.py         # Try Stage
│   ├── check_stage.py       # Check Stage
│   └── retry_stage.py       # Retry Stage
├── retrievers/
│   ├── __init__.py
│   └── bm25.py              # BM25 检索器
├── adapters/
│   ├── __init__.py
│   └── wdai_adapter.py      # Skills 适配器
└── parsers/
    └── __init__.py          # 多格式解析器
```

---

## 配置

```python
from tool_dc.config import ToolDCConfig, HIGH_ACCURACY_CONFIG, LIGHTWEIGHT_CONFIG

# 自定义
config = ToolDCConfig(
    max_groups=5,              # K值
    fallback_threshold=5,       # 启用阈值
    strict_mode=True,           # 严格验证
    enable_self_correction=True # 自我纠正
)

# 预设
config = HIGH_ACCURACY_CONFIG  # 高精度
config = LIGHTWEIGHT_CONFIG    # 轻量级
```

---

## 预期效果

| 场景 | 基线 | Tool-DC | 提升 |
|------|------|---------|------|
| 10+ 工具选择 | ~65% | ~80% | +15% |
| 参数填充 | ~70% | ~85% | +15% |
| 相似工具区分 | ~60% | ~80% | +20% |

---

## 依赖

```bash
# 必需
pip install requests

# 可选 (YAML 支持)
pip install pyyaml
```

---

## 参考

- 论文: [arXiv:2603.11495](https://arxiv.org/abs/2603.11495)
- 设计方案: `../wdai_tool_dc_proposal.md`
