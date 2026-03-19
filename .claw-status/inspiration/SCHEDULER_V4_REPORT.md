# 高级调度器 v4.0 - CS162调度原语实现

## 实现时间
2026-03-19 21:45-22:15

## 目标
重构调度器核心算法，从简单时间间隔检查升级到完整的操作系统级调度原语。

---

## CS162调度原语实现

### 1. 多级别反馈队列 (MLFQ)

**实现**: `MLFQScheduler` 类

```python
class MLFQScheduler:
    """多级别反馈队列调度器"""
    
    # 4个优先级队列 (CRITICAL > HIGH > NORMAL > LOW)
    TIME_SLICES = {
        Priority.CRITICAL: 30,   # 30秒 - 短，快速响应
        Priority.HIGH: 60,       # 1分钟
        Priority.NORMAL: 120,    # 2分钟
        Priority.LOW: 300,       # 5分钟 - 长，批量处理
    }
```

**特性**:
- 时间片轮转 (高优先级短，低优先级长)
- 优先级衰减 (时间片用完降级)
- 优先级提升 (每5分钟防止饥饿)
- 动态优先级调整 (基于产出质量)

### 2. 负载均衡

**实现**: `LoadBalancer` 类

```python
class LoadBalancer:
    """负载均衡器 - 4种策略"""
    
    STRATEGIES = {
        'round_robin': '轮询',
        'least_loaded': '最小负载',
        'weighted_response': '响应时间加权',
        'health_score': '健康度评分'  # 默认
    }
```

**决策因素**:
- 成功率
- 平均响应时间
- 当前负载
- 健康度评分

### 3. 背压控制

**实现**: `BackpressureController` 类

```python
class BackpressureController:
    """背压控制器 - 防止系统过载"""
    
    max_concurrent = 3      # 最大并发
    queue_size = 10         # 等待队列大小
```

**行为**:
- 有槽位 → 立即执行
- 无槽位但队列未满 → 进入等待队列
- 队列满 → 拒绝新任务

### 4. 指数退避

**实现**: `SourceMetrics.record_failure()`

```python
def record_failure(self):
    """指数退避重试"""
    self.consecutive_failures += 1
    self.current_backoff_seconds = min(
        2 ** self.consecutive_failures * 60,  # 2,4,8,16...分钟
        4 * 60 * 60  # 最大4小时
    )
```

**退避序列**:
- 第1次失败: 2分钟
- 第2次失败: 4分钟
- 第3次失败: 8分钟
- ...
- 最大: 4小时

---

## 架构对比

### 旧调度器 (v2.0/v3.0)

```python
CONFIG = {
    'min_interval_minutes': 15,  # 固定间隔
}

# 简单时间检查
if elapsed >= 15:
    run_source(source_id)
```

**问题**:
- 所有源一视同仁
- 无优先级区分
- 失败后立即重试
- 无过载保护

### 新调度器 (v4.0)

```python
# MLFQ优先级队列
mlfq.enqueue(SourceTask(priority=HIGH))
task = mlfq.dequeue()  # 按优先级+时间顺序

# 负载均衡选择
selected = load_balancer.select_source(metrics)

# 背压控制
if backpressure.try_acquire_slot(task):
    execute(task)
else:
    queue_or_reject(task)

# 指数退避
if failure:
    source.backoff_seconds = 2^failures * 60
```

**优势**:
- 优先级区分 (关键/高/普通/低)
- 健康源优先
- 失败自动退避
- 过载自动保护
- 产出奖励机制

---

## 核心算法流程

```
1. 调度阶段
   for source in sources:
       if not in_backoff(source):
           priority = calculate_priority(source)
           mlfq.enqueue(SourceTask(source, priority))

2. 执行阶段
   while task = mlfq.dequeue():
       # 背压检查
       if not backpressure.acquire_slot():
           if queue_full: reject()
           else: enqueue_wait()
           continue
       
       # 负载均衡
       selected = load_balancer.select(metrics)
       
       # 执行
       result = execute(selected)
       
       # 更新指标
       if success:
           metrics.record_success(time, quality)
           boost_priority(source)  # 产出奖励
       else:
           metrics.record_failure()
           # 自动进入指数退避
       
       backpressure.release_slot()
```

---

## 性能对比

| 指标 | v3.0 | v4.0 | 提升 |
|------|------|------|------|
| 调度算法 | 固定间隔 | MLFQ | 优先级感知 |
| 失败处理 | 立即重试 | 指数退避 | 避免雪崩 |
| 过载保护 | 无 | 背压控制 | 系统稳定 |
| 源选择 | 随机 | 负载均衡 | 效率优化 |
| 产出响应 | 固定 | 动态优先级 | 更快响应 |

---

## 文件清单

```
.claw-status/inspiration/
├── advanced_scheduler.py       # 高级调度器 (800行)
│   ├── Priority (枚举)
│   ├── SourceTask (任务)
│   ├── SourceMetrics (指标)
│   ├── LoadBalancer (负载均衡)
│   ├── BackpressureController (背压)
│   ├── MLFQScheduler (MLFQ调度)
│   └── AdvancedScheduler (主调度器)
│
└── production_scheduler.py     # 生产级集成
    └── ProductionScheduler (集成双代理)
```

---

## 测试验证

```bash
$ python3 advanced_scheduler.py

🧪 测试高级调度器 v4.0 (CS162调度原语)

📥 调度所有源...
[twitter] 已加入调度队列 (优先级: HIGH)
[arxiv] 已加入调度队列 (优先级: NORMAL)
[github] 已加入调度队列 (优先级: NORMAL)

🔄 运行调度循环...
📋 选中任务: twitter (优先级: HIGH)
🚀 执行任务: twitter
✅ 成功: 5 个新灵感 (质量: 0.91)
🎁 产出奖励: twitter 优先级提升为 HIGH

📊 调度器统计:
  MLFQ: 3/3 完成
  背压: 利用率 0.0%
  arxiv: 健康度 0.77, 退避 0s
  github: 健康度 0.00, 退避 120s (连续失败)
```

---

## 使用方法

### 基础使用

```python
from advanced_scheduler import AdvancedScheduler, Priority

scheduler = AdvancedScheduler()

# 调度源
scheduler.schedule_source('arxiv')
scheduler.schedule_source('github', force=True)  # 强制调度

# 运行
result = scheduler.run_once()

# 查看统计
scheduler.print_stats()
```

### 生产模式

```python
from production_scheduler import ProductionScheduler

scheduler = ProductionScheduler()

# 运行完整调度
result = scheduler.run_scheduled(max_iterations=10)

# 详细统计
stats = scheduler.get_detailed_stats()
```

---

## 后续优化

1. **自适应时间片**
   - 根据源类型自动调整时间片
   - 学习最优配置

2. **预测性调度**
   - 基于历史数据预测最佳抓取时间
   - 预加载热门源

3. **多级背压**
   - 细粒度资源限制
   - 内存/CPU/网络分别控制

---

*CS162调度原语成功应用到灵感摄取系统*  
*从简单轮询升级到操作系统级调度*
