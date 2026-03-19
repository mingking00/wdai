# 灵感摄取系统 (Inspiration Ingestion System) - 架构文档

> **版本**: 1.0  
> **日期**: 2026-03-19  
> **作者**: wdai  
> **状态**: 已部署

---

## 1. 系统概述

灵感摄取系统是wdai的**外部进化灵感自动获取机制**，负责从外部世界（论文、开源项目、技术趋势）持续摄取高质量信息，转化为可执行的进化任务。

### 核心目标
- **自动化** - 无需人工干预持续监控外部信息源
- **质量筛选** - 智能过滤，只保留高价值内容
- **人工审核** - 关键决策点必须由人工确认
- **深度集成** - 与现有evo Hook架构无缝对接

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        灵感摄取系统 (Inspiration Ingestion)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  论文抓取器   │    │  项目监控器   │    │        趋势分析器            │   │
│  │   (Paper)    │    │   (GitHub)   │    │       (Trend Analyzer)       │   │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┬───────────────┘   │
│         │                   │                            │                  │
│         ▼                   ▼                            ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    原始灵感池 (Raw Inspiration Pool)                   │    │
│  │                    - 去重机制 (Deduplication)                         │    │
│  │                    - 初步过滤 (Pre-filter)                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    知识整合器 (Knowledge Integrator)                   │    │
│  │                    - 摘要生成 (Summary Generation)                    │    │
│  │                    - 质量评分 (Quality Scoring)                       │    │
│  │                    - 关联分析 (Relevance to Existing evo)             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    灵感评估队列 (Inspiration Review Queue)             │    │
│  │                    - 候选存储 (Candidate Storage)                     │    │
│  │                    - 等待人工审核 (Pending Human Review)              │    │
│  │                    - 优先级排序 (Priority Ranking)                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                         │
│                    ┌──────────────┴──────────────┐                         │
│                    ▼                              ▼                         │
│              [人工审核]                      [自动过滤]                     │
│                    │                              │                         │
│                    ▼                              ▼                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │              Evo Hook 触发器 (Evolution Trigger)                       │    │
│  │              - 自动生成evo任务                                         │    │
│  │              - 深度集成现有Hook架构                                     │    │
│  │              - 执行状态追踪                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              外部信息源
    ┌─────────────────┬──────────────────┬──────────────────┐
    │   arXiv RSS     │   GitHub API     │   Tech News      │
    │   (cs.AI/cs.CL) │   (Release/Star) │   (HackerNews)   │
    └─────────────────┴──────────────────┴──────────────────┘
```

---

## 3. 核心组件详解

### 3.1 论文抓取器 (PaperCrawler)

**职责**: 从arXiv自动抓取AI/ML相关论文

**数据源**:
- arXiv RSS Feed (cs.AI, cs.CL, cs.LG, cs.IR)
- 关键词: agent, llm, rag, reasoning, multi-agent, self-improving

**工作流程**:
```python
1. fetch_rss_feed(categories=['cs.AI', 'cs.CL']) 
2. parse_entries() → 提取标题/作者/摘要/链接
3. keyword_filter(keywords=config.keywords) → 匹配关键词
4. quality_score() → 初步质量评分
5. store_to_pool() → 存入原始灵感池
```

**配置参数**:
- `categories`: 监控的arXiv分类
- `keywords`: 关键词列表 (支持正则)
- `min_quality_score`: 最低质量分数阈值
- `download_pdf`: 是否自动下载PDF

---

### 3.2 项目监控器 (ProjectMonitor)

**职责**: 监控GitHub上的高价值项目动态

**监控类型**:
- **Release监控**: 关注项目的版本发布
- **Commit监控**: 关键项目的代码提交
- **Trending监控**: GitHub Trending榜单

**数据源**:
- GitHub REST API
- GitHub GraphQL API (用于复杂查询)

**工作流程**:
```python
1. fetch_releases(repos=config.monitored_repos)
2. fetch_trending(language='python', since='daily')
3. analyze_stars_growth() → 星标增长率分析
4. extract_key_changes() → 提取关键变更
5. store_to_pool() → 存入原始灵感池
```

**监控项目示例**:
- `langchain-ai/langchain` - LangChain框架
- `microsoft/autogen` - 多Agent框架
- `openai/openai-python` - OpenAI SDK
- `meta-llama/llama` - Llama模型

---

### 3.3 趋势分析器 (TrendAnalyzer)

**职责**: 分析内容热度、预测技术趋势

**算法**:
- **热度计算**: 基于时间衰减的加权分数
- **质量评分**: 多维度评估 (引用数、作者影响力、代码活跃度)
- **趋势预测**: 简单线性回归预测未来热度

**评分维度**:
```python
quality_score = (
    relevance_weight * relevance_score +      # 相关性
    novelty_weight * novelty_score +          # 新颖性
    impact_weight * impact_score +            # 潜在影响力
    timeliness_weight * timeliness_score      # 时效性
) / total_weight
```

---

### 3.4 知识整合器 (KnowledgeIntegrator)

**职责**: 去重、摘要生成、关联分析

**功能模块**:
- **去重引擎**: 基于标题/URL/内容的相似度检测
- **摘要生成**: 提取关键信息生成结构化摘要
- **关联分析**: 识别与现有evo任务的关联

**去重策略**:
```python
# 1. URL精确匹配
# 2. 标题相似度 (fuzzy matching)
# 3. 内容指纹 (simhash)
```

---

### 3.5 灵感评估队列 (InspirationQueue)

**职责**: 管理候选灵感的人工审核流程

**状态流转**:
```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  NEW    │───▶│ PENDING │───▶│APPROVED │───▶│ EVOLVED │
│ (新发现)│    │(待审核) │    │ (已批准)│    │(已进化) │
└─────────┘    └────┬────┘    └─────────┘    └─────────┘
                    │
                    ▼
              ┌─────────┐
              │REJECTED │
              │ (已拒绝)│
              └─────────┘
```

**人工审核界面**:
- 命令行交互: `python3 inspiration_queue.py --review`
- Web界面: (未来扩展)

---

### 3.6 Evo Hook触发器

**职责**: 将批准的灵感转化为evo进化任务

**集成点**:
```python
from evolution_hook_framework import EvolutionEvent, emit_event

# 触发evo任务创建
def on_inspiration_approved(inspiration):
    emit_event(EvolutionEvent.INSPIRATION_APPROVED, {
        'source': inspiration.source,
        'title': inspiration.title,
        'priority': inspiration.priority,
        'evo_task': generate_evo_task(inspiration)
    })
```

---

## 4. 数据存储设计

### 4.1 文件结构

```
.claw-status/inspiration/
├── config/
│   └── inspiration_config.json    # 主配置文件
├── data/
│   ├── raw_pool.jsonl             # 原始灵感池
│   ├── queue.json                 # 评估队列
│   ├── processed.jsonl            # 已处理记录
│   └── papers/                    # 下载的论文PDF
│       └── arxiv/
└── logs/
    ├── crawler.log                # 抓取日志
    ├── analysis.log               # 分析日志
    └── evolution.log              # 进化触发日志
```

### 4.2 数据模型

**InspirationRecord**:
```json
{
  "id": "uuid",
  "source": "arxiv|github|news",
  "source_type": "paper|repo|article",
  "title": "...",
  "url": "...",
  "authors": [...],
  "summary": "...",
  "keywords": [...],
  "quality_score": 0.85,
  "trend_score": 0.72,
  "status": "pending",
  "created_at": "2026-03-19T13:30:00Z",
  "reviewed_at": null,
  "reviewer": null,
  "review_note": "",
  "related_evo": ["evo-001", "evo-002"],
  "metadata": {...}
}
```

---

## 5. 配置系统

### 5.1 主配置文件

```json
{
  "system": {
    "name": "灵感摄取系统",
    "version": "1.0",
    "auto_crawl": true,
    "require_human_review": true,
    "default_priority": "medium"
  },
  "arxiv": {
    "enabled": true,
    "categories": ["cs.AI", "cs.CL", "cs.LG", "cs.IR"],
    "keywords": [
      "agent", "llm", "rag", "reasoning", 
      "multi-agent", "self-improving", "autonomous"
    ],
    "min_quality_score": 0.6,
    "max_papers_per_run": 50,
    "download_pdf": false
  },
  "github": {
    "enabled": true,
    "monitored_repos": [
      "langchain-ai/langchain",
      "microsoft/autogen",
      "openai/openai-python"
    ],
    "trending_languages": ["python", "typescript"],
    "min_stars": 1000,
    "check_releases": true,
    "check_commits": false
  },
  "analysis": {
    "deduplication_threshold": 0.85,
    "quality_weights": {
      "relevance": 0.3,
      "novelty": 0.25,
      "impact": 0.25,
      "timeliness": 0.2
    },
    "trend_window_days": 7
  },
  "queue": {
    "max_pending": 100,
    "auto_archive_rejected": true,
    "archive_after_days": 30
  },
  "evo_integration": {
    "enabled": true,
    "auto_trigger_on_approval": true,
    "default_evo_priority": "medium"
  }
}
```

---

## 6. Cron任务配置

### 6.1 定时任务

```bash
# 灵感摄取系统 - Cron配置
# 文件: .claw-status/inspiration/crontab.txt

# 每小时抓取arXiv (错峰: 每小时的第17分钟)
17 * * * * cd /root/.openclaw/workspace && python3 .claw-status/inspiration/crawler.py --source arxiv >> .claw-status/inspiration/logs/crawler.log 2>&1

# 每天9:17监控GitHub Trending
17 9 * * * cd /root/.openclaw/workspace && python3 .claw-status/inspiration/crawler.py --source github --type trending >> .claw-status/inspiration/logs/crawler.log 2>&1

# 每天12:17监控GitHub Releases
17 12 * * * cd /root/.openclaw/workspace && python3 .claw-status/inspiration/crawler.py --source github --type releases >> .claw-status/inspiration/logs/crawler.log 2>&1

# 每天18:17运行趋势分析
17 18 * * * cd /root/.openclaw/workspace && python3 .claw-status/inspiration/analyzer.py --analyze-trends >> .claw-status/inspiration/logs/analysis.log 2>&1

# 每天21:17生成灵感日报
17 21 * * * cd /root/.openclaw/workspace && python3 .claw-status/inspiration/reporter.py --daily >> .claw-status/inspiration/logs/reporter.log 2>&1
```

### 6.2 安装Cron任务

```bash
# 安装cron任务
crontab .claw-status/inspiration/crontab.txt

# 查看已安装的cron任务
crontab -l
```

---

## 7. 使用方式

### 7.1 手动触发抓取

```bash
# 抓取arXiv论文
python3 .claw-status/inspiration/crawler.py --source arxiv

# 监控GitHub
python3 .claw-status/inspiration/crawler.py --source github

# 立即分析所有未处理内容
python3 .claw-status/inspiration/analyzer.py --process-all
```

### 7.2 审核队列管理

```bash
# 查看待审核列表
python3 .claw-status/inspiration/queue.py --list

# 交互式审核
python3 .claw-status/inspiration/queue.py --review

# 批准特定灵感
python3 .claw-status/inspiration/queue.py --approve <inspiration_id>

# 拒绝特定灵感
python3 .claw-status/inspiration/queue.py --reject <inspiration_id>
```

### 7.3 系统状态查看

```bash
# 查看系统状态
python3 .claw-status/inspiration/manager.py --status

# 生成日报
python3 .claw-status/inspiration/reporter.py --daily

# 查看统计数据
python3 .claw-status/inspiration/manager.py --stats
```

### 7.4 Python API

```python
from inspiration_system import InspirationSystem

# 初始化系统
system = InspirationSystem()

# 手动触发抓取
system.crawl(source='arxiv')

# 获取待审核列表
pending = system.queue.get_pending()

# 批准并触发evo
system.queue.approve(inspiration_id, reviewer='wdai')
```

---

## 8. 测试方案

### 8.1 单元测试

```bash
# 运行所有测试
python3 .claw-status/inspiration/tests/run_all.py

# 测试论文抓取器
python3 .claw-status/inspiration/tests/test_crawler.py

# 测试趋势分析器
python3 .claw-status/inspiration/tests/test_analyzer.py

# 测试队列管理
python3 .claw-status/inspiration/tests/test_queue.py
```

### 8.2 集成测试

```bash
# 端到端测试
python3 .claw-status/inspiration/tests/test_integration.py

# 模拟数据测试 (不调用真实API)
python3 .claw-status/inspiration/tests/test_mock.py
```

---

## 9. 监控与告警

### 9.1 健康检查

```bash
# 检查系统健康状态
python3 .claw-status/inspiration/health_check.py
```

### 9.2 日志查看

```bash
# 实时查看日志
tail -f .claw-status/inspiration/logs/crawler.log

# 查看最近的灵感发现
grep "NEW_INSPIRATION" .claw-status/inspiration/logs/crawler.log | tail -20
```

---

## 10. 扩展计划

### 10.1 短期 (1-2周)
- [x] 基础论文抓取
- [x] GitHub监控
- [x] 人工审核队列
- [ ] 邮件/通知集成

### 10.2 中期 (1个月)
- [ ] 更多数据源 (Twitter/X, Reddit, Discord)
- [ ] 高级趋势预测模型
- [ ] Web界面
- [ ] 与Notion/Obsidian集成

### 10.3 长期 (3个月)
- [ ] 自动摘要生成 (LLM-based)
- [ ] 智能推荐系统
- [ ] 多Agent协作研究
- [ ] 预测性evo触发

---

## 11. 相关文档

- [配置说明](config/README.md)
- [API文档](docs/API.md)
- [测试报告](tests/REPORT.md)
- [进化系统集成](docs/EVO_INTEGRATION.md)

---

*Last Updated: 2026-03-19*
