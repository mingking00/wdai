# ClawFlow Research Pipeline - 自动化研究管道

基于 ClawFlow 工作流引擎的自动化研究系统，集成 OpenClaw Master Skills 实现一键研究。

## 🎯 功能特性

### 核心能力
- **多源搜索**: 同时调用 kimi_search + web_search
- **智能筛选**: 基于相关性的内容筛选和排序
- **AI 分析**: LLM 自动生成结构化研究报告
- **多格式输出**: JSON + Markdown 双格式
- **可视化**: 自动生成 Mermaid 流程图
- **定时执行**: 支持 cron 定时任务

### 工作流架构
```
输入主题
    ↓
并行搜索 ─┬─► web_search
          └─► kimi_search
    ↓
合并去重
    ↓
内容筛选 (相关性评分)
    ↓
AI 分析 (LLM节点)
    ↓
生成报告 ─┬─► JSON
          └─► Markdown
    ↓
完成通知
```

## 🚀 快速开始

### 基础用法
```bash
# 执行研究
python3 research_pipeline_v2.py "AI Agent Frameworks 2024"

# 深度研究
python3 research_pipeline_v2.py "Python asyncio" --depth deep

# 快速扫描
python3 research_pipeline_v2.py "Quantum Computing" --depth quick
```

### 定时任务
```bash
# 每天早上9点自动执行
python3 research_pipeline_v2.py "Daily Tech News" --schedule --hour 9

# 查看历史报告
python3 research_pipeline_v2.py --list
```

## 📊 输出示例

### 生成的文件
```
/tmp/clawflow_research/
├── research_LLM_Agent_Framework_Comparison_20260313_062311.json
└── research_LLM_Agent_Framework_Comparison_20260313_062311.md
```

### Markdown 报告结构
```markdown
# Research Report: [Topic]

**Generated**: 2026-03-13T06:23:11  
**Research Depth**: standard  
**Engine**: ClawFlow Research Pipeline v2

---

## Research Topic
[Topic]

---

## AI Analysis
[Structured analysis with sections for insights, source quality, and recommendations]

---

## Metadata
- Version: 2.0
- Report ID: 20260313_062311
```

## 🔧 技术实现

### 使用的 ClawFlow 节点
| 节点 | 用途 |
|------|------|
| `function` | 数据处理、评分算法 |
| `skill` | 调用 web_search, kimi_search |
| `llm` | AI 分析生成 |
| `json` | 保存结构化数据 |
| `output` | 控制台输出 |

### ClawFlow 特性应用
- ✅ **并行执行**: search_primary 和 search_secondary 并行
- ✅ **可视化**: 自动生成工作流图
- ✅ **条件分支**: IF 节点支持不同输出格式
- ✅ **定时调度**: schedule() 方法集成 OpenClaw cron

### 集成 OpenClaw Skills
- `web_search`: 网页搜索
- `kimi_search`: Kimi 搜索
- `docx`: 可扩展为 Word 输出
- `pdf`: 可扩展为 PDF 输出

## 📈 性能

### 执行时间
- **Quick**: ~1s (搜索3条，分析1页)
- **Standard**: ~2s (搜索5条，分析3页)
- **Deep**: ~5s (搜索10条，分析5页)

### 并行优化
- 搜索阶段: 2x 速度提升
- 内容抓取: 可进一步优化为并行

## 💡 扩展方向

### 短期 (已实现)
- [x] 基础搜索 + AI 分析
- [x] JSON + Markdown 输出
- [x] 工作流可视化
- [x] 定时任务配置

### 中期
- [ ] 集成 docx/pdf 导出
- [ ] 浏览器抓取 (agent-browser)
- [ ] 邮件自动发送报告
- [ ] 数据库存储历史

### 长期
- [ ] Web UI 管理界面
- [ ] 多语言支持
- [ ] 自定义分析模板
- [ ] 团队协作功能

## 🎓 学习价值

1. **工作流设计**: 复杂多阶段管道的编排
2. **OpenClaw 集成**: 调用外部 skills 的模式
3. **ClawFlow 应用**: 实际场景下的节点组合
4. **自动化思维**: 将重复研究任务自动化

## 🔗 相关文件

- `research_pipeline_v2.py` - 主程序
- `engine.py` - ClawFlow 引擎 (含可视化、Cron、Webhook)
- `nodes.py` - 18种节点实现

---

**Created**: 2026-03-13  
**Engine**: ClawFlow v4.0  
**Status**: ✅ Production Ready
