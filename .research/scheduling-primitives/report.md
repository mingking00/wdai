# Jonathan Tsai 调度原语深度解析

> 来源: OpenClaw Command Center
> 作者: Jonathan Tsai (UC Berkeley CS, 硅谷20年经验)
> 核心技术: 基于 CS162 (操作系统) 的调度算法

---

## 🎯 核心哲学

**"为什么手动配置 AI agents？为什么手动调度它们的工作？Agent 应该自己做这些。"**

> Use AI to use AI. 用 AI 来管理 AI。

---

## 📚 调度原语一览 (6种)

### 1. `run-if-idle` — 空闲时执行

**概念**: 仅在系统有空闲容量时执行任务

**OS 类比**: 类似于 CPU 空闲调度器，只在 `cpu_idle()` 时执行低优先级任务

**应用场景**:
```python
# 仅在系统负载 < 50% 时执行数据清理
@schedule(run_if=lambda: psutil.cpu_percent() < 50)
def cleanup_old_logs():
    pass
```

**实现逻辑**:
```python
def should_run_if_idle(task, system_load):
    threshold = task.config.get('cpu_threshold', 50)
    return system_load['cpu'] < threshold
```

---

### 2. `run-if-not-run-since` —  freshness 保证

**概念**: "X 时间内没运行过？现在必须运行"

**OS 类比**: 类似于 watchdog 机制，确保关键任务定期执行

**应用场景**:
```python
# 确保备份任务每天至少执行一次
@schedule(max_interval=timedelta(hours=4))
def backup_data():
    pass
```

**实现逻辑**:
```python
def should_run_if_fresh(task, last_run_time):
    max_interval = task.config.get('max_interval', 3600)  # 默认1小时
    time_since_last = now() - last_run_time
    return time_since_last > max_interval
```

---

### 3. `run-at-least-X-times-per-period` — SLA 强制执行

**概念**: 服务质量保证，必须达到最低执行频率

**OS 类比**: 实时系统的 deadline scheduling

**应用场景**:
```python
# 健康检查必须每天运行3次（早中晚）
@schedule(min_runs_per_day=3, distribute_evenly=True)
def health_check():
    pass
```

**实现逻辑**:
```python
def ensure_min_runs(task, run_history, period_hours=24):
    period_start = now() - timedelta(hours=period_hours)
    runs_in_period = sum(1 for r in run_history if r > period_start)
    min_required = task.config.get('min_runs', 1)
    
    if runs_in_period < min_required:
        remaining = min_required - runs_in_period
        slots_remaining = calculate_available_slots(period_end)
        if remaining > slots_remaining:
            return True  # 必须现在执行，否则来不及
    return False
```

---

### 4. `skip-if-last-run-within` — 防抖机制

**概念**: 避免任务过于频繁执行

**OS 类比**: interrupt debouncing (中断防抖)

**应用场景**:
```python
# 价格检查不要太频繁，至少间隔30分钟
@schedule(min_interval=timedelta(minutes=30))
def check_price():
    pass
```

**实现逻辑**:
```python
def should_skip_if_recent(task, last_run_time):
    min_interval = task.config.get('min_interval', 600)  # 默认10分钟
    time_since_last = now() - last_run_time
    return time_since_last < min_interval  # 如果最近刚执行过，跳过
```

---

### 5. `conflict-avoidance` — 冲突避免

**概念**: 贪心算法防止重任务重叠

**OS 类比**: 资源死锁避免 (deadlock avoidance) + 银行家算法

**应用场景**:
```python
# 训练任务不能与其他GPU密集型任务同时运行
@schedule(exclusive_resources=['gpu'], max_concurrent=1)
def train_model():
    pass
```

**实现逻辑**:
```python
def check_conflict_avoidance(task, running_tasks):
    required_resources = task.config.get('resources', [])
    max_concurrent = task.config.get('max_concurrent', 1)
    
    # 检查资源冲突
    for running in running_tasks:
        if any(r in running.resources for r in required_resources):
            if running.conflict_level == 'exclusive':
                return False  # 有冲突，不能执行
    
    # 检查并发数
    similar_tasks = [t for t in running_tasks if t.type == task.type]
    if len(similar_tasks) >= max_concurrent:
        return False
    
    return True
```

---

### 6. `priority-queue` — 优先级抢占

**概念**: 关键任务可以抢占后台工作

**OS 类比**: 多级反馈队列 (Multi-Level Feedback Queue)

**应用场景**:
```python
# 用户请求必须优先于定时清理任务
@schedule(priority=Priority.HIGH, preempt_lower=True)
def handle_user_request():
    pass

@schedule(priority=Priority.LOW)
def background_cleanup():
    pass
```

**实现逻辑**:
```python
class Priority(Enum):
    CRITICAL = 0   # 关键任务，必须立即执行
    HIGH = 1       # 高优先级，可抢占低优先级
    NORMAL = 2     # 普通任务
    LOW = 3        # 后台任务
    BACKGROUND = 4 # 最低优先级

def should_preempt(task, running_tasks):
    task_priority = task.config.get('priority', Priority.NORMAL)
    
    for running in running_tasks:
        running_priority = running.config.get('priority', Priority.NORMAL)
        
        # 如果新任务优先级更高且允许抢占
        if task_priority < running_priority and task.config.get('preempt', False):
            if running.can_be_paused:
                running.pause()  # 暂停低优先级任务
                return True
    
    return True
```

---

## 🔧 调度器核心架构

```
┌─────────────────────────────────────────────────────┐
│                   Task Scheduler                     │
├─────────────────────────────────────────────────────┤
│  1. 接收新任务 → 评估所有调度条件                     │
│  2. 检查冲突避免 → 确认资源可用                       │
│  3. 优先级比较 → 决定抢占/等待                        │
│  4. 更新任务队列 → 执行选中的任务                     │
└─────────────────────────────────────────────────────┘
```

---

## 💡 与 OS 调度算法的对比

| Tsai 原语 | OS 对应算法 | 核心思想 |
|-----------|------------|---------|
| `run-if-idle` | Idle Scheduling | 资源空闲时才执行低优先级任务 |
| `run-if-not-run-since` | Watchdog Timer | 确保关键任务定期执行 |
| `run-at-least-X-times` | Deadline Scheduling | 实时系统的截止时间保证 |
| `skip-if-last-run-within` | Interrupt Debouncing | 防止抖动和过度触发 |
| `conflict-avoidance` | Banker's Algorithm | 资源分配的死锁避免 |
| `priority-queue` | MLFQ | 多级反馈队列的优先级抢占 |

---

## 🚀 应用到我们的系统

### 场景1: 智能搜索调度

```python
@scheduler.register(
    priority=Priority.NORMAL,
    run_if_idle=True,  # 只在CPU空闲时执行
    skip_if_last_run_within=300,  # 5分钟内搜索过就跳过
)
def periodic_search_update():
    """定期更新搜索结果"""
    pass
```

### 场景2: 文档处理保障

```python
@scheduler.register(
    priority=Priority.HIGH,
    run_at_least_x_times_per_period={'count': 3, 'period': 'day'},
    run_if_not_run_since=14400,  # 4小时必须执行一次
)
def process_pending_documents():
    """处理待处理的文档"""
    pass
```

### 场景3: 模型训练任务

```python
@scheduler.register(
    priority=Priority.LOW,
    conflict_avoidance={'resources': ['gpu'], 'max_concurrent': 1},
    run_if_idle=True,  # 只在系统空闲时训练
)
def background_training():
    """后台训练任务"""
    pass
```

---

## 📊 调度决策流程图

```
新任务到达
    ↓
检查 conflict-avoidance
    ↓ (通过)
检查 priority-queue (是否需要抢占?)
    ↓ (确定优先级)
检查 skip-if-last-run-within (防抖)
    ↓ (不需要跳过)
检查 run-if-idle (系统负载?)
    ↓ (负载允许)
检查 run-if-not-run-since (freshness)
    ↓ (需要执行)
检查 run-at-least-X-times (SLA)
    ↓ (满足要求)
执行任务
```

---

## 🎯 关键洞察

1. **资源感知**: 不同于简单的 cron，Tsai 的调度器是**资源感知**的
2. **多层次保障**: 从防抖到SLA，覆盖各种场景
3. **抢占机制**: 关键任务可以中断后台任务
4. **可组合**: 多个原语可以组合使用

> "这套调度系统不是学术练习，而是运行在生产环境的真实系统。"
> — Jonathan Tsai (每天运行 20+ 定时任务，7x24小时)

---

## 🔗 参考

- 项目: https://github.com/jontsai/openclaw-command-center
- 作者博客: https://www.jontsai.com
- CS162: UC Berkeley 操作系统课程
