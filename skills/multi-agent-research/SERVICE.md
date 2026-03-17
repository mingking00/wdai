# Multi-Agent Research Service (MARS) v3.0 🧠

**并行多Agent研究系统 - 常驻服务版本**

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Kimi Claw (主Agent)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 提交研究请求
                              ↓
┌─────────────────────────────────────────────────────────────┐
│        Multi-Agent Research Service (常驻) v3.0              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Conductor (统一协调器)                        │  │
│  │  - 冲突预测 + 智能调度 + 结果合并                      │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓                    ↓                    ↓        │
│  ┌──────────┐        ┌──────────┐         ┌──────────┐    │
│  │ Explorer │───────→│Investigator│──────→│  Critic  │    │
│  │  (1个)   │        │  (并行×N)  │         │(并行×M) │    │
│  └──────────┘        └──────────┘         └──────────┘    │
│         ↑                                          ↓       │
│         └────────────┐                    ┌─────────┘      │
│                      ↓                    ↓                │
│              ┌─────────────────┐    ┌──────────┐          │
│              │ ConflictCoordinator│← │Synthesist│          │
│              │   (冲突解决中心)    │   │  (1个)   │          │
│              └─────────────────┘    └──────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## 两个常驻Agent

| Agent | 职责 | 状态 |
|-------|------|------|
| **Kimi Claw** | 主对话Agent | 运行中 |
| **MARS** | 研究Agent v3.0 | 运行中 PID:236588 |
| **SEA** | 系统进化Agent | 运行中 PID:236317 |

## 核心特性

### 并行执行
- **Explorer**: 生成多角度搜索查询
- **Investigator**: 并行搜索不同角度
- **Critic**: 并行评估信息质量
- **Synthesist**: 合并生成最终答案

### 冲突解决
- **ConflictPredictor**: 预测潜在信息冲突
- **SemanticMergeStrategy**: 语义合并冲突结果
- **智能调度**: 基于冲突情况调整并行度

### 常驻服务
- 实时监听研究请求
- 每5分钟保活检查
- 每天早上8点自动执行AI趋势研究

## 快速使用

### 管理命令
```bash
cd /root/.openclaw/workspace/skills/multi-agent-research

./mars.sh start      # 启动服务
./mars.sh stop       # 停止服务
./mars.sh restart    # 重启服务
./mars.sh status     # 查看状态
./mars.sh logs       # 查看日志
./mars.sh list       # 列出研究报告
```

### 提交研究请求
```bash
# 后台研究（非阻塞）
./mars.sh research "Latest AI breakthroughs 2026"

# 快速研究（阻塞等待结果）
./mars.sh quick "GPT-5 rumors and predictions"
```

### 程序化调用
```python
from mars_service import submit_research_request, get_response, quick_research

# 提交研究
req_id = submit_research_request(
    query="Latest AI frameworks",
    priority=8,
    max_parallel=5
)

# 等待结果
response = get_response(req_id, timeout=300)

# 或一键研究
result = quick_research("AI safety trends")
print(result['final_answer'])
```

## 通信机制

```
.mars/
├── mars.pid              # 进程ID
├── mars_status.json      # 服务状态
├── requests/             # 请求队列
│   ├── REQ_*.json        # 待处理请求
│   └── completed/        # 已完成请求
├── responses/            # 响应结果
│   └── RSP_*.json
└── research_history/     # 研究报告
    └── REPORT_*.md
```

## 自动研究

每天早上8点自动执行:
- 研究主题: "Latest AI trends and breakthroughs"
- 结果保存到: `.mars/research_history/REPORT_AUTO_YYYYMMDD.md`

## 报告格式

```markdown
# 研究报告: [查询]

**状态**: 成功  
**时间**: 2026-03-15T15:05:45  
**并行Agent数**: 5  
**耗时**: 45.2秒

## 研究结论

[最终答案]

## 技术细节

- **冲突解决**: 启用
- **冲突检测**: 3 个
- **冲突解决**: 3 个

## 来源

1. [Source Title](https://...)
2. [Source Title](https://...)
```

## 性能指标

- **并行Agent数**: 可配置（默认5个）
- **典型研究时间**: 30-120秒
- **冲突检测**: 自动识别信息重叠和矛盾
- **质量保证**: 多Critic投票评估

## 安全机制

1. **超时控制**: 默认300秒超时
2. **资源限制**: 控制并行Agent数量
3. **错误处理**: Agent失败不影响整体研究
4. **结果保存**: 自动保存研究报告到文件

## 定时任务

| 任务 | 时间 | 动作 |
|------|------|------|
| mars-service-keepalive | 每5分钟 | 确保MARS服务运行 |
| auto-research | 每天08:00 | 执行AI趋势研究 |

✅ **两个常驻Agent已就绪**

## 文件位置

```
skills/multi-agent-research/
├── mars_service.py       # 常驻服务 ⭐
├── mars.sh               # 管理脚本
├── parallel_orchestrator.py  # v3.0并行编排器
├── SKILL.md              # 技能文档
└── .mars/                # 运行时数据
```
