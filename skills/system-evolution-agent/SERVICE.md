# System Evolution Agent Service (SEAS) 🧬

**常驻服务版本的系统进化代理**

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Kimi Claw (主Agent)                       │
│                      - 处理用户对话                           │
│                      - 触发改进请求                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 提交请求文件
                              ↓
┌─────────────────────────────────────────────────────────────┐
│          System Evolution Agent Service (常驻)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 请求处理器    │  │ 心跳检查      │  │ 自动分析      │      │
│  │ (实时处理)    │  │ (每30秒)      │  │ (每天4点)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           严格审查流程 (语法/安全/冲突)                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 两个常驻Agent

| Agent | 职责 | 状态 |
|-------|------|------|
| **Kimi Claw** | 主对话Agent，处理所有交互 | ✅ 运行中 |
| **SEA Service** | 系统进化Agent，负责改进系统 | ✅ 运行中 (PID: 236317) |

## 快速使用

### 启动/停止服务
```bash
cd /root/.openclaw/workspace/skills/system-evolution-agent

./seas.sh start     # 启动
./seas.sh stop      # 停止
./seas.sh restart   # 重启
./seas.sh status    # 查看状态
./seas.sh logs      # 查看日志
```

### 提交改进请求
```bash
./seas.sh improve "优化错误处理" "skills/my_tool/core.py"
```

### 提交分析请求
```bash
./seas.sh analyze
```

## 程序化调用

### 从主Agent调用
```python
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/system-evolution-agent')
from sea_service import submit_improvement_request, get_response

# 提交改进
req_id = submit_improvement_request(
    description="添加缓存机制",
    changes={
        "skills/my_skill/core.py": "新代码内容"
    }
)

# 等待结果
response = get_response(req_id, timeout=60)
if response['result']['success']:
    print(f"改进成功！得分: {response['result']['review_score']}")
```

## 自动功能

### 1. 心跳监控
- 每30秒更新一次状态
- 保活任务每5分钟检查一次
- 服务崩溃自动重启

### 2. 每日自动分析
- 每天凌晨4点自动分析系统
- 识别改进机会
- 生成建议报告到 `.system/auto_suggestion_YYYYMMDD.json`

### 3. 实时请求处理
- 监听 `.system/requests/` 目录
- 新请求文件自动触发处理
- 结果保存到 `.system/responses/`

## 文件结构

```
system-evolution-agent/
├── sea.py              # 核心实现
├── sea_service.py      # 常驻服务 ⭐
├── seas.sh             # 管理脚本
├── SKILL.md            # 本文档
└── .system/            # 运行时数据
    ├── seas.pid        # 进程ID
    ├── seas_status.json # 服务状态
    ├── requests/       # 请求队列
    │   └── REQ_*.json
    ├── responses/      # 响应结果
    │   └── RSP_*.json
    ├── backups/        # 系统备份
    └── logs/           # 服务日志
```

## 安全机制

1. **自动备份** - 每次变更前自动备份
2. **严格审查** - 语法/安全/冲突/性能检查
3. **得分阈值** - ≥70分才能通过
4. **关键拦截** - 危险代码直接拒绝
5. **自动回滚** - 失败自动恢复
6. **操作审计** - 所有变更永久记录

## 触发方式

当用户说以下话语时，主Agent应该通过文件向SEA提交请求：
- "改进你自己"
- "进化"
- "优化系统"
- "审查这段代码"

## 状态

```
服务状态: 运行中 ✅
PID: 236317
启动时间: 2026-03-15T14:55:58
最后心跳: 2026-03-15T14:55:58
总请求数: 1
已完成: 1
失败: 0
```

## 定时任务

| 任务 | 时间 | 动作 |
|------|------|------|
| sea-service-keepalive | 每5分钟 | 确保SEA服务运行 |
| 自动分析 | 每天04:00 | 分析系统并生成建议 |

✅ **两个常驻Agent已就绪**
