# Deep Research Skill - 快速开始

## 1分钟上手

### 安装检查
```bash
cd /root/.openclaw/workspace
ls skills/deep_research/  # 确认文件存在
python3 -c "from skills.deep_research import research; print('✅ Ready')"
```

### 基础使用

```python
import asyncio
from skills.deep_research import research

async def main():
    # 快速研究
    result = await research("Python asyncio", depth="quick")
    print(result.answer)
    print(result.references_text)

asyncio.run(main())
```

### 三种模式对比

| 模式 | 代码 | 适用场景 |
|------|------|----------|
| Quick | `depth="quick"` | 快速事实核查 |
| Standard | `depth="standard"` | 中等深度 |
| Deep | `depth="deep"` | 复杂多维度研究 |

### 集成到主 Agent

```python
from skills.deep_research.integration import register_to_agent

# 一行代码完成集成
register_to_agent(my_agent)

# 然后可以使用
result = await my_agent.deep_research.research("query")
```

### 命令解析集成

```python
from skills.deep_research.integration import parse_research_command, handle_message

# 自动识别研究命令
text = "研究 Python asyncio"
is_research, query, depth = parse_research_command(text)
# is_research=True, query='Python asyncio', depth='standard'
```

## 运行测试

```bash
python3 skills/deep_research/test_skill.py
```

预期输出：
- ✅ Command Parser: 6/6 通过
- ✅ Cache System: 3/3 通过
- ✅ Citation System: 正常
- ✅ API Tests: 依赖 web_search/web_fetch

## 文件清单

```
skills/deep_research/
├── SKILL.md              # 完整文档
├── __init__.py           # 主要入口
├── research_engine.py    # 核心引擎
├── cache.py              # 缓存系统
├── citation.py           # 引用生成
├── config.py             # 配置
├── integration.py        # 主系统集成
├── examples.py           # 示例代码
└── test_skill.py         # 测试套件
```

## 环境变量

```bash
export DEEP_RESEARCH_CACHE_TTL=3600         # 缓存过期时间
export DEEP_RESEARCH_CACHE_SIZE=128         # 内存缓存大小
export DEEP_RESEARCH_AUTO_FALLBACK=true     # HTTP失败时自动使用Browser
```

## 下一步

1. ✅ 测试验证完成
2. ✅ 主系统集成完成
3. ⏳ 实际搜索功能依赖 OpenClaw 环境的 web_search/web_fetch 工具

## 参考

- WebRooter: https://github.com/baojiachen0214/web-rooter
- OpenClaw Skills 架构: AGENTS.md
