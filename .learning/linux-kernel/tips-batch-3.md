# Linux内核技巧 - Batch 3 (阶段2)

> 分析文件: sched/core.c, sched/fair.c, mm/page_alloc.c, mm/slub.c

## 技巧17: 使用per-CPU变量减少缓存竞争

**类别**: 调度器

### 代码片段
```c
DEFINE_PER_CPU_SHARED_ALIGNED(struct rq, runqueues);
```

### 解释
将运行队列(runqueue)定义为per-CPU变量，每个CPU有自己的副本，避免多核之间的缓存一致性开销。

### 应用场景
多核系统中需要频繁访问的共享数据，如连接池、计数器等。

---

## 技巧18: 使用const_debug在发布版中移除调试代码

**类别**: 调度器

### 代码片段
```c
const_debug unsigned int sysctl_sched_nr_migrate = SCHED_NR_MIGRATE_BREAK;
```

### 解释
const_debug宏在调试版本中保留变量，在发布版本中将其转为编译时常量，允许编译器优化。

### 应用场景
需要条件编译的调试/性能监控代码。

---

## 技巧19: 使用__read_mostly优化很少修改的数据

**类别**: 调度器

### 代码片段
```c
__read_mostly int sysctl_resched_latency_warn_ms = 100;
```

### 解释
将很少修改但频繁读取的变量标记为__read_mostly，编译器会将其放在特殊段，优化缓存。

### 应用场景
配置参数、系统常量、启动时设置后不变的数据。

---

## 技巧20: 使用likely/unlikely优化分支预测

**类别**: 调度器

### 代码片段
```c
if (likely(!arch_irqs_disabled()))
    local_irq_disable();
```

### 解释
通过__builtin_expect向编译器提示分支概率，帮助CPU预取指令，减少流水线冲刷。

### 应用场景
错误处理、边界检查、常见/罕见条件分支。

---

## 技巧21: 使用RCU实现无锁读取

**类别**: 调度器

### 代码片段
```c
rcu_read_lock();
struct task_struct *p = rcu_dereference(rq->curr);
// 访问p...
rcu_read_unlock();
```

### 解释
RCU(Read-Copy-Update)允许读者无锁访问共享数据，写者通过复制更新，延迟释放旧数据。

### 应用场景
读多写少的场景：路由表、任务列表、配置缓存。

---

## 技巧22: 使用虚拟运行时间(vruntime)实现公平调度

**类别**: 调度器

### 代码片段
```c
struct sched_entity {
    u64 vruntime;
    u64 exec_start;
    u64 sum_exec_runtime;
    // ...
};
```

### 解释
CFS(完全公平调度器)使用vruntime衡量任务应得的CPU时间，vruntime最小的任务获得CPU。

### 应用场景
需要公平分配资源的场景：线程池、请求队列、带宽分配。

---

## 技巧23: 使用红黑树实现O(log n)任务管理

**类别**: 调度器

### 代码片段
```c
struct rb_root_cached rb_root_cached;
struct sched_entity *se = rb_entry(first, struct sched_entity, run_node);
```

### 解释
CFS使用红黑树存储可运行任务，查找vruntime最小的任务时间复杂度为O(log n)。

### 应用场景
需要动态排序的数据结构：定时器队列、事件调度、优先级队列。

---

## 技巧24: 使用PELT衰减算法跟踪负载

**类别**: 调度器

### 代码片段
```c
#define LOAD_AVG_PERIOD 32
#define LOAD_AVG_DECAY 1572864 /* 2^32 * (1 - 1/e) */
```

### 解释
PELT(Per-Entity Load Tracking)使用指数衰减计算历史负载，平滑短期波动，反映长期趋势。

### 应用场景
需要平滑历史数据的场景：负载均衡、流量控制、性能监控。

---

## 技巧25: 使用hrtimer实现微秒级精度定时器

**类别**: 调度器

### 代码片段
```c
hrtimer_start(&se->period_timer, ns_to_ktime(period), HRTIMER_MODE_ABS_PINNED);
```

### 解释
hrtimer(高精度定时器)提供微秒级精度，相比传统jiffies定时器精度提升1000倍。

### 应用场景
需要精确定时的场景：多媒体、实时系统、网络超时。

---

## 技巧26: 使用伙伴系统管理连续物理内存

**类别**: 内存管理

### 代码片段
```c
struct free_area {
    struct list_head free_list[MIGRATE_TYPES];
    unsigned long nr_free;
};

struct zone {
    struct free_area free_area[MAX_ORDER];
};
```

### 解释
伙伴系统将内存分为2^n大小的块，分配时拆分，释放时合并，有效减少外部碎片。

### 应用场景
需要分配可变大小连续内存的场景：DMA缓冲区、大页分配、内存池。

---

## 技巧27: NUMA节点亲和性优化内存访问延迟

**类别**: 内存管理

### 代码片段
```c
int preferred_zone = zone_idx(preferred_zone);
if (zone_idx(zone) > preferred_zone)
    continue; /* 优先从本地节点分配 */
```

### 解释
优先从当前CPU所在NUMA节点分配内存，避免跨节点访问的延迟惩罚。

### 应用场景
多路服务器、大数据应用、需要低延迟内存访问的场景。

---

## 技巧28: 使用迁移类型减少内存碎片

**类别**: 内存管理

### 代码片段
```c
enum migratetype {
    MIGRATE_UNMOVABLE,
    MIGRATE_MOVABLE,
    MIGRATE_RECLAIMABLE,
    MIGRATE_TYPES
};
```

### 解释
将页面按可移动性分类：不可移动、可移动、可回收，减少不同类页面之间的碎片。

### 应用场景
长期运行系统的内存管理、避免内存碎片导致分配失败。

---

## 技巧29: 使用SLUB分配器优化小对象分配

**类别**: 内存管理

### 代码片段
```c
struct kmem_cache {
    unsigned int size;
    unsigned int object_size;
    struct kmem_cache_order_objects oo;
    void (*ctor)(void *);
    // ...
};
```

### 解释
SLUB(Slab Unqueued)分配器为特定大小对象创建缓存，减少内部碎片，提高分配速度。

### 应用场景
频繁分配释放小对象的场景：数据库连接池、网络包缓冲区、对象池。

---

## 技巧30: per-CPU缓存消除slab分配锁竞争

**类别**: 内存管理

### 代码片段
```c
struct kmem_cache_cpu {
    void **freelist;
    struct page *page;
    struct page *partial;
    // ...
} __aligned(2 * sizeof(void *));

DEFINE_PER_CPU(struct kmem_cache_cpu, cpu_slab);
```

### 解释
每个CPU有自己的slab缓存，分配释放时无需加锁，只在跨CPU或缓存耗尽时同步。

### 应用场景
高并发场景下的内存分配：Web服务器、数据库、消息队列。

---

