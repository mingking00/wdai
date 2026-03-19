# 好用的 Agent Skills 推荐清单

> 收集时间: 2026-03-16
> 适用: OpenClaw / Kimi-Claw Agent

---

## 📊 快速分类索引

| 类别 | 推荐 Skills | 用途 |
|------|------------|------|
| 🔍 搜索研究 | advanced-research-orchestrator, research-orchestrator, tavily-web-search | 深度研究、信息聚合 |
| 🧠 记忆自进化 | self-improving-agent, mem0-memory, advanced-planner | 持续学习、任务规划 |
| 🌐 浏览器自动化 | agent-browser, slack, electron, dogfood | 网页交互、测试、截图 |
| 💻 开发编程 | frontend-design, mcp-builder, coding-agent, debug-pro | 代码生成、调试、设计 |
| 📄 文档处理 | pdf, docx, xlsx, pptx | Office 文档操作 |
| 🎨 内容创作 | canvas-design, algorithmic-art, slack-gif-creator | 视觉设计、艺术创作 |
| 🔧 系统运维 | healthcheck, docker-essentials, aws-infra | 安全审计、部署 |
| 📚 知识管理 | obsidian, notion, logseq | 笔记管理、知识库 |

---

## 🏆 必装 Skills（核心推荐）

### 1. 🔬 Advanced Research Orchestrator
**用途**: 深度多源研究，自动验证和知识图谱构建
**触发词**: "研究...", "分析...", "对比..."
**核心能力**:
- 四维评估（相关性/权威性/时效性/可信度）
- 自主知识循环（定时更新监控）
- KAG 风格知识图谱存储

```bash
# 使用方法
./scripts/research.sh "quantum computing breakthroughs 2024" --depth deep --verify
```

**本地路径**: `/root/.openclaw/skills/advanced-research-orchestrator/`

---

### 2. 🌐 Agent Browser
**用途**: 浏览器自动化，网页交互、截图、数据提取
**触发词**: "打开网站", "截图", "点击按钮", "填写表单"
**核心能力**:
- 页面导航和 DOM 操作
- 自动截图和 PDF 导出
- 表单填写和按钮点击
- Electron 应用控制

```bash
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser click @e3
agent-browser screenshot page.png
```

**本地路径**: `/root/.openclaw/skills/agent-browser/`

---

### 3. 🧠 Self-Improving Agent
**用途**: 错误追踪、主动学习、功能请求记录
**触发词**: "记住这个错误", "记录学习", "避免下次再犯"
**核心能力**:
- 自动记录错误和纠正
- 存储用户偏好
- 持续优化响应质量

**本地路径**: `/root/.openclaw/skills/self-improving-agent/`

---

### 4. 🎯 Advanced Planner
**用途**: 复杂任务分解、多方案生成、执行反思
**触发词**: "规划...", "分解任务", "制定方案"
**核心能力**:
- Task Decomposition (任务分解)
- Plan Selection (方案选择)
- External Module (外部工具编排)
- Reflection (执行后反思)
- Memory (经验记忆)

```bash
./scripts/planner.sh decompose --task "deploy web app"
./scripts/planner.sh generate --task "..." --num-plans 3
```

**本地路径**: `/root/.openclaw/skills/advanced-planner/`

---

### 5. 🎨 Frontend Design
**用途**: 创建高质量前端界面，避免"AI 味"设计
**触发词**: "做个网页", "设计界面", "美化组件"
**核心能力**:
- 生产级 HTML/CSS/JS/React/Vue 代码
- 独特视觉风格（极简/极繁/复古未来主义等）
- 精致排版和细节打磨

**本地路径**: `/root/.openclaw/skills/anthropic-skills/skills/frontend-design/`

---

### 6. 📄 PDF / DOCX / XLSX / PPTX
**用途**: Office 文档全流程处理
**触发词**: "读取 PDF", "生成 Word", "处理 Excel", "制作 PPT"
**核心能力**:
- PDF: 读取、合并、拆分、OCR、加密
- DOCX: 创建、编辑、模板填充
- XLSX: 数据分析、图表生成、公式计算
- PPTX: 幻灯片创建、主题应用

**本地路径**: `/root/.openclaw/skills/anthropic-skills/skills/pdf/` (等同目录下有 docx/xlsx/pptx)

---

### 7. 🔧 MCP Builder
**用途**: 构建 MCP (Model Context Protocol) 服务器
**触发词**: "创建 MCP", "接入 API", "开发工具"
**核心能力**:
- FastMCP (Python) 和 MCP SDK (Node/TS) 指导
- 工具设计和 API 封装最佳实践
- 工作流工具 vs 全面 API 覆盖的权衡

**本地路径**: `/root/.openclaw/skills/anthropic-skills/skills/mcp-builder/`

---

### 8. 🔍 Research Orchestrator
**用途**: 多源研究编排，轻量版研究工具
**触发词**: "搜索...", "调研..."
**核心能力**:
- Web Search + GitHub + RSS + Browser 抓取
- 去重和交叉验证
- 洞察提取和报告生成

```bash
./scripts/research.sh "AI agent frameworks comparison" --depth deep --verify
```

**本地路径**: `/root/.openclaw/skills/research-orchestrator/`

---

## 🌟 特色 Skills（按需安装）

### 内容创作类
| Skill | 用途 | 触发词 |
|-------|------|--------|
| **canvas-design** | 创建精美视觉艺术 | "设计海报", "创作艺术" |
| **algorithmic-art** | p5.js 生成艺术 | "生成艺术", "粒子系统" |
| **slack-gif-creator** | 制作 Slack 动图 | "做 GIF", "动画表情" |
| **theme-factory** | 主题样式工具包 | "应用主题", "配色方案" |

### 开发工具类
| Skill | 用途 | 触发词 |
|-------|------|--------|
| **webapp-testing** | Playwright 测试网页 | "测试网站", "检查功能" |
| **claude-api** | Anthropic SDK 开发 | "用 Claude API", "SDK 开发" |
| **skill-creator** | 创建新 Skills | "创建 skill", "扩展能力" |
| **doc-coauthoring** | 协作文档写作 | "写文档", "技术规格" |

### 系统运维类
| Skill | 用途 | 触发词 |
|-------|------|--------|
| **healthcheck** | 安全审计和加固 | "安全检查", "系统审计" |
| **tmux** | 远程控制 tmux | "管理会话", "后台任务" |
| **openai-whisper** | 本地语音转文字 | "转录音频", "语音识别" |

### 知识管理类
| Skill | 用途 | 触发词 |
|-------|------|--------|
| **obsidian** | Obsidian 笔记管理 | "查笔记", "写笔记" |
| **notion** | Notion 页面/数据库 | "查 Notion", "更新数据库" |
| **docx** | Word 文档处理 | "生成报告", "写文档" |

---

## 📥 安装方法

### 方式 1: ClawHub 安装（推荐）
```bash
# 搜索技能
clawhub search <keyword>

# 安装技能
clawhub install <skill-name>

# 示例
clawhub install agent-browser
clawhub install advanced-research-orchestrator
```

### 方式 2: 手动安装
```bash
# 克隆到 skills 目录
cd /root/.openclaw/skills
git clone <skill-repo-url>

# 安装依赖（如果有）
cd <skill-folder>
pip install -r requirements.txt
```

### 方式 3: 本地开发
```bash
# 在 workspace/skills 下创建
cd /root/.openclaw/workspace/skills
mkdir my-skill
cd my-skill
touch SKILL.md
```

---

## 🎯 按场景推荐组合

### 场景 1: 深度研究分析
```
advanced-research-orchestrator + research-orchestrator + agent-browser
```

### 场景 2: 全栈开发
```
frontend-design + mcp-builder + webapp-testing + coding-agent
```

### 场景 3: 内容创作
```
canvas-design + docx + pdf + slack-gif-creator + theme-factory
```

### 场景 4: 自动化运维
```
healthcheck + docker-essentials + tmux + agent-browser
```

### 场景 5: 知识管理
```
self-improving-agent + mem0-memory + obsidian + notion
```

---

## ⚠️ 注意事项

1. **权限检查**: 安装前查看 SKILL.md 的权限要求
2. **依赖安装**: 部分 skills 需要额外的 CLI 工具或 API Key
3. **冲突避免**: 功能相似的 skills 可能触发冲突，按需选择
4. **安全审计**: 第三方 skills 建议先用 `skill-scanner` 检查

---

## 🔗 相关资源

- **ClawHub**: https://clawhub.com
- **OpenClaw Docs**: https://docs.openclaw.ai
- **Awesome OpenClaw Skills**: https://github.com/openclaw/awesome-openclaw-skills

---

*整理: wdai | 更新: 2026-03-16*
