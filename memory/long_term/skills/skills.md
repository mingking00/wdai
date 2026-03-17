# 技能与工具清单

> 可用技能和工具的快速参考
> 更新频率: 新增技能时更新

---

## 🔧 核心工具 (内置)

| 工具 | 功能 | 使用场景 |
|------|------|----------|
| `kimi_search` | 联网搜索 | 需要实时信息时 |
| `web_search` | Brave搜索 | 需要API key |
| `web_fetch` | 网页抓取 | 提取页面内容 |
| `browser` | 浏览器自动化 | 网页交互、截图 |
| `exec` | 执行命令 | 系统操作 |
| `read/write/edit` | 文件操作 | 代码/文档编辑 |

---

## 🎯 OpenClaw Master Skills

### 浏览器自动化
- **agent-browser** - 网页导航、表单、截图
- **dogfood** - QA测试
- **electron** - 桌面应用控制

### 研究分析
- **research-orchestrator** - 多源研究
- **advanced-research-orchestrator** - 增强版研究
- **advanced-planner** - 任务规划

### 文档处理
- **docx** - Word文档
- **pdf** - PDF处理
- **pptx** - PowerPoint
- **xlsx** - Excel表格

### 开发工具
- **github** - GitHub CLI
- **tmux** - 终端会话
- **mcp-builder** - MCP服务器

### 内容创作
- **canvas-design** - 视觉设计
- **frontend-design** - 前端界面
- **theme-factory** - 主题系统

---

## 🚀 我的 Skills

### ClawFlow (工作流引擎)
- 位置: `skills/clawflow/`
- 功能: 工作流编排、并行执行
- 节点: 18种

### Research Pipeline (研究管道)
- 位置: `skills/clawflow/research_*.py`
- 功能: 搜索→分析→报告

---

## 📋 快速使用

### 搜索
```python
# kimi_search (推荐)
kimi_search(query="Python asyncio", limit=5)

# web_search (需要API key)
web_search(query="Python", count=5)
```

### 浏览器
```bash
agent-browser open https://example.com
agent-browser snapshot -i
```

### GitHub
```bash
gh pr checks 55 --repo owner/repo
gh run list --repo owner/repo
```

---

## 🔍 发现新技能

```bash
npx skills find [关键词]
npx skills add <owner/repo@skill>
```

技能仓库: https://skills.sh/

---

*Last updated: 2026-03-13*
