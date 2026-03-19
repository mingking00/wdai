# 原则执行系统 - 持久化与自动加载方案

## 状态持久化

### 持久化文件列表

| 文件 | 内容 | 自动保存 |
|------|------|----------|
| `.claw-status/innovation_state.json` | 方法失败计数 | ✓ 每次失败时 |
| `.claw-status/principle_state.json` | 原则违规记录 | ✓ 每次违规时 |
| `.claw-status/work_state.json` | 工作监控状态 | ✓ 任务完成时 |

### 状态文件格式

**innovation_state.json:**
```json
{
  "task_id:method_name": {
    "count": 3,
    "first_fail": "2026-03-16T16:02:58",
    "last_fail": "2026-03-16T16:02:58"
  }
}
```

**principle_state.json:**
```json
{
  "violations": [
    {
      "principle": "检查验证",
      "context": "deploy_blog",
      "severity": 2,
      "timestamp": "2026-03-16T16:09:25"
    }
  ],
  "last_update": "2026-03-16T16:09:25"
}
```

---

## 自动加载机制

### 方案1: AGENTS.md 加载（推荐）

**在 AGENTS.md 的 "Every Session" 中添加:**

```python
# 自动加载原则执行系统
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".openclaw/workspace/.claw-status"))

try:
    from init_principles import initialize_principle_system
    initialize_principle_system()
except Exception as e:
    print(f"⚠️ 原则执行系统加载失败: {e}")
```

### 方案2: 环境变量触发

**添加 `.env` 文件:**
```bash
PRINCIPLE_SYSTEM_AUTOLOAD=true
```

**启动时检查:**
```python
import os
if os.getenv("PRINCIPLE_SYSTEM_AUTOLOAD") == "true":
    initialize_principle_system()
```

### 方案3: 系统服务（高级）

**创建 systemd 服务 (Linux):**
```ini
# /etc/systemd/system/principle-engine.service
[Unit]
Description=Principle Execution Engine

[Service]
Type=simple
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/.claw-status/init_principles.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 会话恢复流程

```
会话启动
  ↓
读取 AGENTS.md
  ↓
执行 "Every Session" 检查点
  ↓
自动加载原则执行系统
  ↓
  ├── 加载 innovation_state.json
  ├── 加载 principle_state.json
  └── 显示当前状态
  ↓
系统就绪，开始处理任务
```

---

## 重启后验证

### 验证命令
```bash
# 检查原则执行系统状态
python3 ~/.openclaw/workspace/.claw-status/init_principles.py

# 检查锁定的方法
python3 -c "
import sys
sys.path.insert(0, '.claw-status')
from innovation_trigger import get_status
status = get_status()
locked = [k for k,v in status.items() if v.get('count',0) >= 3]
print('锁定方法:', locked)
"

# 检查违规记录
python3 -c "
import sys
sys.path.insert(0, '.claw-status')
from principle_engine import get_engine
engine = get_engine()
print('违规记录:', len(engine.violations))
"
```

---

## 状态同步策略

### 跨会话同步
- 所有状态写入 JSON 文件（磁盘持久化）
- 每次状态变更立即保存
- 会话启动时从磁盘加载

### 多Agent同步（未来）
- 使用共享存储（Redis/数据库）
- 或文件锁机制
- 状态变更广播

---

## 清理机制

### 自动清理规则
```python
# 失败计数自动衰减
def auto_decay():
    for method in failed_methods:
        if time_since_last_fail > 7_days:
            count *= 0.5  # 7天后衰减50%
        if time_since_last_fail > 30_days:
            reset_counter(method)  # 30天后重置

# 违规记录归档
def archive_old_violations():
    if violation_age > 90_days:
        move_to_archive()
```

### 手动清理
```bash
# 重置所有状态
rm ~/.openclaw/workspace/.claw-status/*_state.json

# 重置特定方法
python3 -c "
from innovation_trigger import reset_counter
reset_counter('github_api', 'task_id')
"
```

---

## 监控与告警

### 日常监控
```bash
# 添加到 HEARTBEAT.md
def check_principle_system():
    summary = get_principle_summary()
    if summary["locked_methods"]:
        alert_user(f"有{len(summary['locked_methods'])}个方法被锁定")
    if summary["total_violations"] > 10:
        alert_user(f"违规次数过多: {summary['total_violations']}")
```

### 状态仪表盘
```bash
# 查看完整状态
python3 ~/.openclaw/workspace/.claw-status/init_principles.py
```

---

## 故障恢复

### 场景1: 状态文件损坏
```python
# 自动备份与恢复
if state_file_corrupted:
    restore_from_backup()
    or_reset_to_default()
```

### 场景2: 加载失败
```python
try:
    initialize_principle_system()
except Exception as e:
    # 降级模式：仅使用默认原则
    use_default_principles()
    log_error(e)
```

---

## 实施检查清单

- [x] 创建状态文件（JSON格式）
- [x] 实现自动保存机制
- [x] 创建 `init_principles.py` 启动器
- [x] 更新 AGENTS.md 自动加载
- [ ] 添加每日状态检查到 HEARTBEAT.md
- [ ] 创建备份机制
- [ ] 添加状态清理规则
- [ ] 测试重启恢复

---

*Last updated: 2026-03-16*
*Status: 已实施基础持久化，自动加载已激活*
