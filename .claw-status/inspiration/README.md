# 灵感摄取系统 - 部署指南

## 系统架构

```
灵感摄取系统 v3.0 (Self-Evolving)
├── 调度器 (SmartScheduler)     - 智能调度，15分钟-48小时自适应
├── 抓取器 (Crawlers)
│   ├── arXiv RSS               - 主源
│   ├── GitHub API              - 主源
│   ├── arXiv Deep (list/sanity/search) - 空转解决
│   └── Reddit (multi-sub)      - 空转解决
├── 自愈系统 (SelfHealing)      - 熔断/重试/fallback
├── 空转解决器 (EmptySolver)    - 深度抓取/相关源/主动搜索
├── 通知器 (Notifier)           - 高质量内容推送
└── 🧬 进化引擎 (EvolutionEngine) - 灵感→洞察→方案→实施 [NEW]
    ├── 灵感分析器              - 提取模式/趋势/痛点
    ├── 优化方案设计器          - 生成架构优化方案
    └── 进化实施器              - 自动修改底层系统
```

## 文件结构

```
.claw-status/inspiration/
├── inspiration_runner.py       # 主运行器
├── scheduler.py                # 调度器 v2.0
├── self_healing.py             # 自愈系统
├── empty_run_solver.py         # 空转解决器
├── source_manager.py           # 源管理器
├── notifier.py                 # 通知模块
├── evolution_engine.py         # 🧬 进化引擎 [NEW]
├── crawler_arxiv_deep.py       # arXiv深度抓取
├── crawler_reddit.py           # Reddit抓取
├── tech_roadmap.py             # 技术路线图
├── run.sh                      # 运行脚本
├── status.sh                   # 状态查看
├── report.sh                   # 报告生成
└── data/                       # 数据目录
    ├── scheduler/              # 调度数据
    ├── runs/                   # 运行记录
    ├── healing/                # 自愈数据
    ├── insights/               # 🧬 洞察数据 [NEW]
    ├── plans/                  # 🧬 优化方案 [NEW]
    ├── cron.log                # 运行日志
    └── system_report_*.md      # 系统报告
```

## 定时任务配置

已配置Cron任务：`inspiration-system-auto-run`
- **频率**: 每15分钟运行一次
- **时区**: Asia/Shanghai
- **命令**: 执行 `run.sh` 脚本
- **模式**: isolated agent session

### 手动运行

```bash
cd /root/.openclaw/workspace/.claw-status/inspiration

# 自动模式（推荐）
./run.sh

# 或直接使用Python
python3 inspiration_runner.py --mode=auto

# 查看状态
./status.sh

# 生成报告
./report.sh

# 测试空转解决
python3 inspiration_runner.py --mode=dry-run
```

## 系统行为

### 完整闭环流程

```
灵感摄取 → 分析洞察 → 生成方案 → 自动实施 → 效果验证 → 知识固化
    ↑                                                        ↓
    └───────────────── 持续迭代优化 ←─────────────────────────┘
```

1. **灵感摄取**: 每15分钟抓取arXiv/GitHub/Reddit
2. **空转解决**: 主源无内容时启用深度策略
3. **知识整合**: 将内容存入待审核队列
4. **🧬 灵感进化**: [NEW]
   - 分析收集的内容，提取技术趋势/架构模式/痛点
   - 生成系统优化方案
   - 自动实施低风险改进
5. **效果验证**: 语法检查/运行时监控
6. **知识固化**: 更新文档/原则

### 进化引擎工作流

```python
# 每次运行后自动触发
def run_evolution(items):
    # Step 1: 分析灵感
    insights = analyzer.analyze_batch(items)
    # 输出: [{type: 'trend', content: 'MCP Protocol...', confidence: 0.9}, ...]
    
    # Step 2: 生成方案
    plans = [planner.generate_plan(i) for i in insights if i.confidence >= 0.6]
    # 输出: [{title: '集成MCP Protocol', risk_level: 'low', ...}, ...]
    
    # Step 3: 实施方案（只处理低风险）
    for plan in plans:
        if plan.risk_level == 'low':
            evolution.implement_plan(plan)
            # 实际修改系统文件
```

### 空转解决流程
```
1. 主源没有新内容
2. 检测连续空转次数
3. 自动启用解决策略:
   - 第1次: arXiv深度抓取 (列表页+Sanity)
   - 第2次: Reddit讨论抓取
   - 第3次: 关键词搜索
4. 合并所有来源的内容
```

### 错误处理
```
API限流    → 自动等待60秒 → 重试
网络超时   → 指数退避 → fallback API
连续失败   → 熔断30分钟 → 使用备用方案
解析错误   → 记录日志 → 跳过该项
```

## 监控指标

### 日志位置
- 运行日志: `data/cron.log`
- 运行记录: `data/runs/run_YYYYMMDD_HHMMSS.json`
- 系统报告: `data/system_report_YYYYMMDD.md`

### 关键指标
```
- 今日运行次数
- 发现新内容数
- 空转解决成功次数
- 自动恢复次数
- 熔断器状态
```

## 配置调整

### 修改运行频率
编辑Cron任务：
```
当前: */15 * * * * (每15分钟)
可选: */30 * * * * (每30分钟)
      0 * * * *    (每小时)
```

### 修改调度参数
编辑 `scheduler.py` 中的 CONFIG:
```python
CONFIG = {
    'min_interval_minutes': 15,     # 最小间隔
    'max_interval_hours': 48,       # 最大间隔
    'empty_backoff_multiplier': 2,  # 空转退避倍数
    'max_consecutive_empty': 5,     # 空转暂停阈值
}
```

### 添加新源
编辑 `inspiration_runner.py` 中的 sources 列表:
```python
sources = [
    {'id': 'arxiv', 'name': 'arXiv论文', 'fetcher': self._fetch_arxiv},
    {'id': 'github', 'name': 'GitHub项目', 'fetcher': self._fetch_github},
    # 添加新源...
]
```

## 故障排查

### 检查系统健康
```bash
python3 -c "
from scheduler import get_scheduler
report = get_scheduler().get_source_report()
print(f\"状态: {report['overload_mode']}\")
print(f\"今日运行: {report['daily_stats']['run_count']}\")
"
```

### 检查自愈状态
```bash
python3 -c "
from self_healing import SelfHealingSystem
report = SelfHealingSystem().get_health_report()
print(f\"健康: {report['status']}\")
print(f\"24h错误: {report['recent_errors_24h']}\")
print(f\"熔断器: {report['circuit_breakers']}\")
"
```

### 手动测试抓取器
```bash
# 测试arXiv深度抓取
python3 crawler_arxiv_deep.py

# 测试Reddit
python3 crawler_reddit.py
```

## 扩展计划

### Phase 1 (已完成)
- ✅ 调度器 v2.0
- ✅ 自愈系统
- ✅ 空转解决器
- ✅ arXiv深度抓取
- ✅ Reddit抓取
- ✅ 🧬 灵感进化引擎 [NEW]
  - ✅ 灵感分析器 (模式/趋势/痛点识别)
  - ✅ 优化方案设计器 (自动生成改进方案)
  - ✅ 进化实施器 (自动修改底层系统)

### Phase 2 (待实现)
- ⬜ Semantic Scholar API (引用数据)
- ⬜ YouTube Data API
- ⬜ Product Hunt API
- ⬜ Hacker News监控
- ⬜ Newsletter存档

### Phase 3 (未来)
- ⬜ X/Twitter API (评估成本)
- ⬜ Discord社区 (权限问题)
- ⬜ 智能摘要生成
- ⬜ 内容质量自动评分

## 联系方式

系统维护: wdai evolution system
配置文件: `.claw-status/inspiration/`

---
*Deployed: 2026-03-19*
