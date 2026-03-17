# Deep Research Skill - 配置指南

## 快速配置

### 1. 获取 Brave Search API Key

1. 访问 [Brave Search API](https://brave.com/search/api/)
2. 注册并获取 API Key
3. 免费额度：每月 2000 次查询

### 2. 配置 OpenClaw

```bash
# 方式 1: 使用 openclaw configure
openclaw configure --section web
# 按提示输入 BRAVE_API_KEY

# 方式 2: 设置环境变量
export BRAVE_API_KEY="your_api_key_here"

# 方式 3: 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export BRAVE_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. 验证配置

```bash
# 测试搜索功能
python3 -c "
from tools.web_search import web_search
results = web_search('Python asyncio', count=3)
print(f'Found {len(results)} results')
for r in results[:2]:
    print(f'  - {r[\"title\"]}')
"
```

## 可选：使用其他搜索源

### DuckDuckGo (无需 API Key)

修改 `research_engine.py` 中的 `_search_with_fallback` 方法：

```python
async def _search_with_fallback(self, query: str) -> List[Dict]:
    # 尝试 DuckDuckGo
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=self.config.num_results):
                results.append({
                    "title": r["title"],
                    "url": r["href"],
                    "snippet": r["body"],
                    "domain": r.get("domain", "")
                })
            if results:
                return results
    except Exception:
        pass
    
    return []
```

安装依赖：
```bash
pip install duckduckgo-search
```

### Google Custom Search

需要 Google API Key 和 Custom Search Engine ID。

## 环境变量汇总

```bash
# 搜索配置
export BRAVE_API_KEY="xxx"

# Deep Research Skill 配置
export DEEP_RESEARCH_CACHE_TTL=3600
export DEEP_RESEARCH_CACHE_SIZE=128
export DEEP_RESEARCH_CACHE_PATH="~/.openclaw/deep_research_cache.db"
export DEEP_RESEARCH_AUTO_FALLBACK=true
```

## 故障排除

### 问题：搜索结果为空

**检查步骤：**
1. 确认 BRAVE_API_KEY 已设置
2. 检查 API Key 是否有效
3. 查看是否超出免费额度

```bash
# 检查环境变量
echo $BRAVE_API_KEY

# 测试直接调用
python3 -c "
import os
from tools.web_search import web_search
print('API Key:', os.getenv('BRAVE_API_KEY', 'NOT SET')[:10] + '...')
results = web_search('test', count=1)
print('Results:', len(results))
"
```

### 问题：模块导入失败

```bash
# 确保在正确的目录
cd /root/.openclaw/workspace

# 检查 skills/__init__.py 是否存在
ls -la skills/__init__.py

# 测试导入
python3 -c "from skills.deep_research import research; print('OK')"
```

## 测试命令

```bash
# 运行完整测试
python3 skills/deep_research/test_skill.py

# 运行演示
python3 skills/deep_research/demo.py
```

## 下一步

配置完成后，即可正常使用：

```python
from skills.deep_research import research

result = await research("Python asyncio best practices", depth="deep")
print(result.answer)
print(result.references_text)
```
