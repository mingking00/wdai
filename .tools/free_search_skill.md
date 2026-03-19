# Free Search Skill - 免费联网搜索技能

**创建日期**: 2026-03-12  
**位置**: `.tools/free_search_skill.py`  
**费用**: 完全免费

---

## 功能特性

✅ **完全免费** - 无需API Key，无需注册  
✅ **多后端备份** - 自动切换可用后端  
✅ **零依赖** - 仅需Python标准库（可选ddgs增强）  
✅ **多格式输出** - text/markdown/json  

---

## 使用方法

### 命令行

```bash
# 基础搜索
python3 free_search_skill.py "搜索关键词"

# 指定结果数量
python3 free_search_skill.py "Python教程" --max-results 10

# JSON格式输出
python3 free_search_skill.py "AI新闻" --format json

# Markdown格式
python3 free_search_skill.py "技术博客" --format markdown
```

### Python调用

```python
from free_search_skill import FreeSearchSkill

skill = FreeSearchSkill()
results = skill.search("OpenClaw", max_results=5)

for r in results:
    print(f"{r.title}: {r.href}")
```

---

## 技术实现

### 多后端策略

| 优先级 | 后端 | 说明 |
|--------|------|------|
| 1 | DuckDuckGo (ddgs) | 首选，结构化数据 |
| 2 | SearXNG 实例 | 社区公共实例 |
| 3 | DuckDuckGo HTML | 直接抓取，最后备选 |

### 公共SearXNG实例

- `https://search.sapti.me`
- `https://search.bus-hit.me`
- `https://search.projectsegfault.com`

---

## 研究报告

详细研究报告: `.research-free-search/report.md`

对比了8+免费搜索方案，最终选择多后端备份策略确保可用性。

---

## 集成到OpenClaw

添加到 `.tools/` 目录后，可在对话中直接调用：

```
使用 free_search_skill 搜索 "最新AI进展"
```

或使用统一工具入口：
```
./agent-toolkit react "研究LLM agents" --tools free_search_skill
```
