# Redis 架构分析 - 2026-03-17

## 项目信息
- **名称**: Redis (Remote Dictionary Server)
- **定位**: 高性能键值存储/内存数据库
- **核心特点**: 单线程事件循环、内存操作、丰富的数据结构
- **性能**: 单机可达 100K+ QPS

## 核心架构

### 1. 单线程事件循环 (Reactor模式)

```c
// ae.c - Redis事件循环核心
void aeMain(aeEventLoop *eventLoop) {
    eventLoop->stop = 0;
    while (!eventLoop->stop) {
        aeProcessEvents(eventLoop, AE_ALL_EVENTS|
                                   AE_CALL_BEFORE_SLEEP|
                                   AE_CALL_AFTER_SLEEP);
    }
}
```

**为什么单线程？**
```
优势:
├── 无锁开销 - 单线程修改数据，无需同步机制
├── CPU不是瓶颈 - 内存操作极快，网络/内存带宽先饱和
├── 简单可预测 - 无并发bug，命令天然原子性
└── 缓存友好 - 单线程最大化CPU缓存命中率

劣势:
├── 单核限制 - 无法利用多核处理命令
├── 长命令阻塞 - KEYS *, 复杂Lua脚本会阻塞所有客户端
└── 无抢占 - 命令必须执行完才能处理新事件
```

**事件类型:**
```c
typedef struct aeEventLoop {
    int maxfd;
    aeFileEvent events[AE_SETSIZE];      // 文件事件 (I/O)
    aeFiredEvent fired[AE_SETSIZE];      // 就绪事件
    aeTimeEvent *timeEventHead;          // 时间事件 (定时器)
    // ...
} aeEventLoop;
```

### 2. 文件事件处理

```c
// aeProcessEvents - 核心事件处理
int aeProcessEvents(aeEventLoop *eventLoop, int flags) {
    int numevents = aeApiPoll(eventLoop, tvp);  // epoll_wait
    
    for (j = 0; j < numevents; j++) {
        int fd = eventLoop->fired[j].fd;
        aeFileEvent *fe = &eventLoop->events[fd];
        
        // 读事件 - 客户端发来命令
        if (fe->mask & mask & AE_READABLE) {
            fe->rfileProc(eventLoop, fd, fe->clientData, mask);
        }
        
        // 写事件 - 可以发送响应
        if (fe->mask & mask & AE_WRITABLE) {
            fe->wfileProc(eventLoop, fd, fe->clientData, mask);
        }
    }
}
```

**处理流程:**
```
Client -> TCP连接 -> accept_handler
         -> 注册读事件到epoll
         -> 客户端发送命令 -> 触发读事件
         -> 读取命令 -> 执行命令 (内存操作)
         -> 队列响应 -> 触发写事件
         -> 发送响应
```

### 3. 时间事件 (定时器)

```c
typedef struct aeTimeEvent {
    long long id;                    // 事件ID
    long when_sec;                   // 触发秒
    long when_ms;                    // 触发毫秒
    aeTimeProc *timeProc;            // 处理函数
    aeEventFinalizerProc *finalizerProc;
    void *clientData;
    struct aeTimeEvent *next;        // 链表下一个
} aeTimeEvent;
```

**用途:**
- Key过期检查 (过期删除策略)
- 后台保存 (BGSAVE)
- AOF重写 (BGREWRITEAOF)
- 集群心跳

### 4. I/O多路复用抽象

```c
// ae_epoll.c - Linux epoll实现
static int aeApiPoll(aeEventLoop *eventLoop, struct timeval *tvp) {
    aeApiState *state = eventLoop->apidata;
    
    // 阻塞等待事件 (有timeout)
    int retval = epoll_wait(state->epfd, state->events, 
                            eventLoop->setsize, 
                            tvp ? (tvp->tv_sec*1000 + ...) : -1);
    
    // 将就绪事件填充到 fired 数组
    for (j = 0; j < numevents; j++) {
        struct epoll_event *e = state->events+j;
        eventLoop->fired[j].fd = e->data.fd;
        eventLoop->fired[j].mask = ...
    }
    return numevents;
}
```

**跨平台支持:**
- Linux: epoll
- BSD/macOS: kqueue
- Windows: select (旧版) / IOCP (新版)

### 5. 命令处理原子性

```c
// 单线程保证原子性
void processCommand(client *c) {
    // 1. 查找命令
    struct redisCommand *cmd = lookupCommand(c->argv[0]->ptr);
    
    // 2. 执行命令 (原子操作)
    call(c, CMD_CALL_FULL);
    
    // 3. 添加响应到输出缓冲区
    addReply(c, ...);
}
```

**关键保证:**
- 命令执行期间不会被其他客户端打断
- 无需锁机制
- 简单命令 (GET/SET) 复杂度 O(1)

### 6. 高性能优化技巧

#### 6.1 Pipeline (管道)
```python
# 坏：1000次往返
for i in range(1000):
    r.set(f'key:{i}', f'value:{i}')  # 1000次RTT

# 好：1次往返
pipe = r.pipeline()
for i in range(1000):
    pipe.set(f'key:{i}', f'value:{i}')
pipe.execute()  # 批量发送，批量响应
```

#### 6.2 合适的数据结构
```python
# 坏：分散存储
r.set('user:1:name', 'Alice')
r.set('user:1:email', 'a@b.com')
r.set('user:1:age', '30')  # 3个key

# 好：Hash聚合
r.hset('user:1', mapping={
    'name': 'Alice',
    'email': 'a@b.com',
    'age': 30
})  # 1个key，内存更高效
```

#### 6.3 避免O(N)操作
```python
# 坏：大集合阻塞
all = r.smembers('large_set')  # 可能数百万元素，阻塞!

# 好：迭代器分批处理
cursor = 0
while True:
    cursor, members = r.sscan('large_set', cursor, count=100)
    process(members)
    if cursor == 0: break
```

#### 6.4 MGET/MSET批量操作
```python
# 坏：多次RTT
values = [r.get(k) for k in keys]

# 好：单次RTT
values = r.mget(keys)
```

### 7. 持久化策略

#### 7.1 RDB (快照)
- **机制**: Fork子进程，写入内存快照
- **优点**: 文件紧凑，恢复速度快
- **缺点**: 可能丢失最后一次快照后的数据
- **触发**: 定时/定量/手动 SAVE/BGSAVE

#### 7.2 AOF (追加日志)
- **机制**: 记录每个写操作命令
- **优点**: 数据更安全，最多丢失1秒数据
- **缺点**: 文件大，恢复慢
- **重写**: BGREWRITEAOF 压缩日志

#### 7.3 混合模式 (Redis 4.0+)
- RDB做全量，AOF做增量
- 兼顾速度和安全性

### 8. 内存管理

#### 8.1 内存分配器
- 默认: jemalloc (减少内存碎片)
- 可选: libc malloc, tcmalloc

#### 8.2 过期策略
```
被动删除: 访问时发现过期，立即删除
主动删除: 定时随机抽查，删除过期key
内存淘汰: 内存满时按策略删除 (LRU/LFU/TTL等)
```

#### 8.3 内存优化
- 小整数共享 (0-9999)
- 字符串SDS优化
- ziplist/listpack紧凑编码

## 可复用模式

| 模式 | 实现 | 可应用性 |
|:---|:---|:---:|
| **单线程Reactor** | ae.c | ⭐⭐⭐ |
| **事件分层** | 文件+时间事件 | ⭐⭐⭐ |
| **I/O多路复用抽象** | ae_epoll/kqueue/select | ⭐⭐⭐ |
| **Pipeline批量** | 客户端优化 | ⭐⭐ |
| **原子性保证** | 单线程执行 | ⭐⭐ |
| **内存优先** | 全内存+异步持久化 | ⭐ |

## 与Gnet/Rathole对比

| 特性 | Redis | Gnet | Rathole |
|:---|:---|:---|:---|
| **线程模型** | 单线程 | 多线程Reactor | 多线程tokio |
| **I/O** | epoll/kqueue | epoll/kqueue | tokio async |
| **并发** | 无锁(单线程) | 无锁(多loop) | Arc+锁 |
| **适用** | 内存操作 | 网络I/O | 网络代理 |
| **性能** | 100K+ QPS | 高吞吐 | 低延迟 |

## 应用到wdai

### 可借鉴模式:

1. **单线程事件循环** (如果任务处理极快)
   ```python
   # 当前：多Agent并发
   # 可选：单线程事件循环 (类似Redis)
   # 适用场景：任务处理极快 (<1ms)，无阻塞
   ```

2. **时间事件 (定时器)**
   ```python
   # 当前：无定时任务
   # 改进：添加定时器支持
   # 用途：超时检查、心跳、定期清理
   ```

3. **Pipeline批量处理**
   ```python
   # 当前：每个任务单独提交
   # 改进：批量提交子任务
   # 用途：减少调度开销
   ```

4. **命令原子性保证**
   ```python
   # 当前：asyncio可能穿插执行
   # 改进：关键路径单线程执行
   # 用途：避免竞态条件
   ```

## 关键洞察

**Redis选择单线程的原因:**
1. 内存操作足够快，CPU不是瓶颈
2. 避免锁开销，代码更简单
3. 网络延迟远大于内存操作时间
4. 水平扩展(多实例)比垂直扩展(多线程)更容易

**什么时候该用单线程:**
- 任务处理极快 (<1ms)
- 无阻塞I/O
- 数据竞争敏感
- 水平扩展可行

**什么时候不该用:**
- CPU密集型任务
- 需要利用多核
- 任务执行时间长

---
