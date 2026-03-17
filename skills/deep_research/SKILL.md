# deep_research Skill

深度研究工具，整合 WebRooter 设计哲学，为 OpenClaw 提供企业级研究能力。

## 版本

- **Version**: 1.0.0
- **Author**: Kimi Claw
- **License**: MIT

## 安装

```bash
# Skill 已位于 skills/deep_research/
# 确保 skills/__init__.py 存在
touch skills/__init__.py
```

## 功能特性

### 三种研究模式

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| `quick` | 仅搜索摘要，1-2秒响应 | 快速事实核查、初步了解 |
| `standard` | 搜索 + 抓取详情 | 中等深度研究 |
| `deep` | MindSearch 风格深度研究 | 复杂问题、多维度分析 |

### 核心特性

- **双层缓存**: 内存 LRU + SQLite 持久化
- **智能回退**: HTTP → Browser 自动切换
- **强制引用**: 所有结果可追溯来源
- **流式输出**: 实时展示研究进度
- **压力感知**: 自适应降级保护

## 使用方式

### 方法 1: 直接导入

```python
from skills.deep_research import research, run

# 方式 1: 直接函数
result = await research("AI agent frameworks", depth="deep")
print(result.answer)
print(result.references_text)

# 方式 2: Skill 接口
result = await run({
    "query": "Python best practices",
    "depth": "standard"
})
print(result["answer"])
```

### 方法 2: 集成到主 Agent

```python
from skills.deep_research.integration import register_to_agent, handle_message

# 注册到 Agent
register_to_agent(my_agent)

# 使用
result = await my_agent.deep_research.research("query", depth="deep")
```

### 方法 3: 命令解析

```python
from skills.deep_research.integration import parse_research_command

is_research, query, depth = parse_research_command("研究 Python asyncio")
if is_research:
    result = await research(query, depth=depth)
```

## 参数说明

### 输入参数

```python
{
    "query": str,           # 必填，研究问题
    "depth": str,           # 可选，quick/standard/deep，默认 standard
    "sources": List[str],   # 可选，搜索源列表，默认 ["web"]
    "max_results": int      # 可选，最大结果数，默认 10
}
```

### 输出格式

```python
{
    "success": bool,
    "answer": str,              # 综合答案
    "references_text": str,     # 格式化引用
    "citations": List[Dict],    # 结构化引用
    "sources_count": int,       # 来源数量
    "exploration_path": List,   # 深度模式：探索路径
    "metadata": Dict            # 元数据
}
```

## 示例

### Quick 模式

```python
result = await research("Python asyncio best practices", depth="quick")
# 输出：摘要 + 3-5个来源引用
```

### Standard 模式

```python
result = await research("OpenClaw AI agent", depth="standard")
# 输出：详细答案 + 抓取内容 + 引用
```

### Deep 模式

```python
result = await research("AI agent frameworks comparison 2026", depth="deep")
# 输出：
# - 综合研究报告
# - 多维度探索路径
# - 结构化引用
# - 10-20个来源
```

### 流式输出

```python
from skills.deep_research import run_stream

async for event in run_stream({"query": "AI", "depth": "deep"}):
    print(event)
    # {"event": "start", ...}
    # {"event": "decomposed", ...}
    # {"event": "level_complete", ...}
    # {"event": "complete", "result": ...}
```

## 缓存配置

缓存文件位置：`~/.openclaw/deep_research_cache.db`

环境变量：
- `DEEP_RESEARCH_CACHE_TTL`: 缓存过期时间（秒），默认 3600
- `DEEP_RESEARCH_CACHE_SIZE`: 最大缓存条目数，默认 128
- `DEEP_RESEARCH_CACHE_PATH`: 缓存文件路径

## 依赖

- OpenClaw 内置：`web_search`, `web_fetch`, `browser`
- Python 标准库：`sqlite3`, `asyncio`, `hashlib`

## 测试

```bash
cd /root/.openclaw/workspace
python3 skills/deep_research/test_skill.py
```

## 文件结构

```
skills/deep_research/
├── SKILL.md              # 本文件
├── __init__.py           # 入口
├── research_engine.py    # 核心引擎
├── cache.py              # 双层缓存
├── citation.py           # 引用生成
├── config.py             # 配置管理
├── integration.py        # 主系统集成
├── examples.py           # 使用示例
└── test_skill.py         # 测试脚本
```

## 实现参考

基于 WebRooter (https://github.com/baojiachen0214/web-rooter) 设计：
- `ResearchKernel`: 页面获取内核
- `MindSearchPipeline`: 深度研究流程
- `Citation System`: 引用追溯机制
