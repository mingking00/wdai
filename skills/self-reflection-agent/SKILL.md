# Self-Reflection Agent (SRA) 🤔

**自我复盘常驻Agent** - 持续分析对话，提取可复用资产

## 职责

1. **每日自动复盘** - 分析当天的对话记录
2. **技巧提取** - 识别可复用的工作模式
3. **错误记录** - 记录教训和修正
4. **模式识别** - 发现重复的工作流
5. **报告生成** - 生成日复盘报告

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Kimi Claw (主Agent)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 对话记录
                              ↓
┌─────────────────────────────────────────────────────────────┐
│           Self-Reflection Agent Service (常驻)               │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  内容分析    │→│  技巧提取    │→│  模式识别    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         ↓                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  错误记录    │  │  报告生成    │  │  SOUL.md    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 四个常驻Agent

| Agent | 职责 | 状态 |
|-------|------|------|
| **Kimi Claw** | 主对话Agent | 运行中 |
| **SEA Service** | 系统进化Agent | 运行中 |
| **MARS Service** | 研究Agent v3.0 | 运行中 |
| **SRA Service** | 自我复盘Agent | 运行中 |

## 自动运行

### 定时复盘
- **每天01:00** - 执行自我进化复盘（整合自 daily-self-evolution）
- **每天22:00** - 执行日复盘
- **每周日22:30** - 执行周复盘

### 监控内容
- `memory/daily/YYYY-MM-DD.md` - 每日对话记录
- 工作监察日志
- 技能使用情况

## 提取的技巧类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **pattern** | 工作模式 | "先用web_search查文档再动手" |
| **tool** | 工具技巧 | "用sessions_spawn处理耗时任务" |
| **lesson** | 教训 | "检查文件存在性前先确认路径" |
| **optimization** | 优化 | "批量更新cron任务比逐个快" |

## 快速使用

### 管理命令
```bash
cd /root/.openclaw/workspace/skills/self-reflection-agent

./sra.sh start      # 启动服务
./sra.sh stop       # 停止服务
./sra.sh restart    # 重启服务
./sra.sh status     # 查看状态
./sra.sh logs       # 查看日志
```

### 提交复盘
```bash
# 复盘今天
./sra.sh reflect

# 复盘特定日期
./sra.sh reflect 2026-03-14
```

### 查看技巧
```bash
./sra.sh tips       # 查看提取的技巧
./sra.sh list       # 查看复盘报告
```

## 程序化调用

```python
from sra_service import submit_reflection_request, quick_reflect

# 提交复盘请求
req_id = submit_reflection_request('daily', '2026-03-15')

# 或快速复盘
result = quick_reflect('2026-03-15')
```

## 复盘报告格式

```markdown
# 日复盘报告 - 2026-03-15

**生成时间**: 2026-03-15T22:00:00

## 统计

- 提取技巧: 5 个
- 发现模式: 2 个
- 记录错误: 1 个

## 提取的技巧

### 1. [pattern] 先用memory_search查已有能力再动手...

- **上下文**: extracted_from_memory
- **提取时间**: 2026-03-15T22:05:00
- **验证状态**: ○

## 工作流模式

1. 查记忆→执行→沉淀→复用

## 错误与修正

1. 忘记检查文件存在性导致FileNotFoundError

## 明日建议

- 验证新提取的技巧在实际任务中的有效性
- 避免重复出现已记录的错误
- 继续沉淀可复用的工作流模式
```

## 文件位置

```
skills/self-reflection-agent/
├── sra_service.py        # 常驻服务
├── sra.sh                # 管理脚本
├── SKILL.md              # 本文档
└── .sra/                 # 运行时数据
    ├── sra.pid           # 进程ID
    ├── sra_status.json   # 服务状态
    ├── requests/         # 请求队列
    ├── responses/        # 响应结果
    ├── reflections/      # 复盘报告
    │   └── reflection_YYYY-MM-DD.md
    └── tips/             # 提取的技巧
        └── extracted_tips.json
```

## 与SOUL.md的关系

SRA提取的技巧经过验证后，可以：
1. 更新到SOUL.md的"人格锚点"部分
2. 创建新的工作流技能
3. 添加到AGENTS.md的约定中

## 定时任务

| 任务 | 时间 | 动作 |
|------|------|------|
| sra-service-keepalive | 每5分钟 | 确保SRA服务运行 |
| auto-reflection | 每天22:00 | 执行日复盘 |
| weekly-reflection | 每周日22:30 | 执行周复盘 |

✅ **四个常驻Agent已就绪**
