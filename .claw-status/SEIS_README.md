# WDai 自执行改进系统 (SEIS)

> 自动监控 → 触发 → 执行 → 反馈  
> 版本: 1.0 | 创建: 2026-03-19

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    WDai Core (v3.7)                      │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│   SEIS引擎   │ │  守护进程 │ │  内存优化器   │
│ (seis_engine)│ │(guardian)│ │(memory_opt)  │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       └──────────────┼──────────────┘
                      ▼
            ┌─────────────────┐
            │  自动触发任务池   │
            │  imp-001~imp-005 │
            └─────────────────┘
```

---

## 核心组件

### 1. SEIS引擎 (`seis_engine.py`)

**功能**: 监控指标、检测触发、执行任务

**运行方式**:
```bash
# 手动运行
python3 .claw-status/seis_engine.py

# 自动定时（每15分钟）
cron: */15 * * * *
```

**监控指标**:
- 过载分数 (0-1)
- CPU使用率
- 内存使用率
- 响应时间
- 活跃任务数

### 2. 守护进程 (`wdai_guardian.py`)

**功能**: 过载保护、紧急保存、优雅降级

**运行方式**:
```bash
# 单次检查
python3 .claw-status/wdai_guardian.py --check

# 持续监控
python3 .claw-status/wdai_guardian.py --monitor

# 从快照恢复
python3 .claw-status/wdai_guardian.py --recover snapshot.json
```

**保护措施**:
- 过载分数 > 0.9 → 紧急保存 + 优雅降级
- 自动暂停非关键任务
- 释放缓存
- 启用简化模式

### 3. 内存优化器 (`memory_optimizer.py`)

**功能**: 自动压缩旧记忆、清理临时文件

**触发条件**:
- 内存使用 > 85%
- 每周日凌晨自动执行

**优化动作**:
- 压缩30天前的记忆文件
- 清理临时文件
- 优化索引

---

## 自动触发任务

| 任务ID | 名称 | 触发条件 | 执行动作 | 频率 |
|--------|------|---------|---------|------|
| imp-001 | 过载简化 | 过载 > 0.7 | 启用极简模式 | 实时 |
| imp-002 | 卡死搜索 | 卡住 > 15min | 自动搜索新思路 | 实时 |
| imp-003 | 错误重构 | 错误 > 3次/小时 | 分析+提重构方案 | 实时 |
| imp-004 | 每日评估 | 每天 00:00 | 评估evo完成率 | 每日 |
| imp-005 | 内存压缩 | 内存 > 85% | 触发记忆压缩 | 实时/每周 |

---

## 执行流程

### 正常运行
```
1. SEIS每15分钟收集指标
2. 检查是否有触发条件
3. 如有，执行对应任务
4. 保存状态到json
```

### 过载保护
```
1. Guardian检测到过载 (>0.9)
2. 紧急保存状态到snapshot
3. 执行优雅降级
4. 暂停非关键任务
5. 等待负载下降
6. 自动恢复
```

### 没思路时
```
1. 检测卡住 (>15分钟无进展)
2. 自动执行搜索
3. 提取关键信息
4. 生成建议方案
5. 等待用户确认
```

---

## 配置说明

### 阈值配置

```python
# seis_engine.py
self.overload_threshold = 0.7      # 过载触发
self.stuck_threshold_minutes = 15  # 卡死触发

# wdai_guardian.py
self.overload_threshold = 0.9      # 紧急保护触发
```

### 文件位置

```
.claw-status/
├── seis_engine.py           # SEIS主引擎
├── wdai_guardian.py         # 守护进程
├── memory_optimizer.py      # 内存优化
├── system_metrics.jsonl     # 指标记录
├── improvement_tasks.json   # 任务状态
├── auto_improvement_checklist.md  # 改进清单
└── SIMPLIFY_MODE            # 简化模式标志
```

---

## 使用示例

### 查看当前状态
```bash
python3 .claw-status/seis_engine.py
```

输出:
```
============================================================
SEIS 监控周期 2026-03-19 00:51:23
============================================================
📊 指标: 过载=0.30, 内存=44.6%
✅ 系统正常，无触发任务
============================================================
```

### 手动触发内存优化
```bash
python3 .claw-status/memory_optimizer.py
```

### 检查是否需要恢复
```bash
python3 .claw-status/wdai_guardian.py --check
```

---

## 集成到WDai

```python
# 在WDai主循环中集成
from seis_engine import SelfImprovementEngine

class WDai:
    def __init__(self):
        self.seis = SelfImprovementEngine()
    
    def process(self, task):
        # 每次处理前先检查
        triggered = self.seis.run_cycle()
        
        if triggered:
            # 有自动任务执行，简化输出
            return self._simplified_process(task)
        
        # 正常处理
        return self._normal_process(task)
```

---

## 下一步

- [ ] 运行SEIS收集基线数据
- [ ] 根据数据调整阈值
- [ ] 完善imp-002搜索逻辑
- [ ] 添加更多架构优化任务

---

*SEIS v1.0 | 守护WDai健康运行*
