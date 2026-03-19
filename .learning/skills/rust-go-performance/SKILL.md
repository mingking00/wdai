# Rust/Go 高性能编程技能 v1.0

> 从GitHub/GitHub资料提炼的性能优化模式
> 创建时间: 2026-03-17
> 来源: Conf42 Rust演讲、Go Concurrency Patterns 2025

---

## Rust 高性能模式

### 1. Zero-Copy 零拷贝处理

**核心原则**: 避免数据复制，直接引用内存

```rust
// 传统方式: 5次拷贝（网卡→内核→用户→处理→网卡）
// Zero-Copy方式: 直接映射网卡缓冲区到用户空间

// 使用借用检查确保安全的零拷贝
pub fn process_packet(buf: &[u8]) -> Result<(), Error> {
    // &buf 是引用，不拷贝数据
    let header = parse_header(&buf[0..HEADER_SIZE])?;
    let payload = &buf[HEADER_SIZE..]; // 切片，零拷贝
    process_payload(payload)
}
```

**关键技巧**:
- 使用 `&[u8]` 切片代替 `Vec<u8>`
- `memmap` 直接映射文件到内存
- 环形缓冲区 (Ring Buffer) 无锁队列

**性能收益**: 延迟降低 40-65%，CPU核心释放用于其他工作

### 2. 无锁并发 (Fearless Concurrency)

```rust
use std::sync::Arc;
use std::atomic::{AtomicU64, Ordering};

// 原子操作，无锁
static COUNTER: AtomicU64 = AtomicU64::new(0);

// Arc + 借用检查 = 安全共享
pub fn process_parallel(data: Arc<Data>) {
    // 编译时保证无数据竞争
    std::thread::spawn(move || {
        data.process(); // 所有权系统自动管理
    });
}
```

**模式**:
- `Arc<T>`: 原子引用计数，线程间共享所有权
- `Mutex<T>`: 必要时使用，但优先用channel
- `RwLock<T>`: 多读单写场景

### 3. 自定义分配器

```rust
use std::alloc::{GlobalAlloc, Layout, System};

// 预分配缓冲区，避免频繁malloc/free
pub struct PooledAllocator;

unsafe impl GlobalAlloc for PooledAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        // 从预分配池获取内存
        // 确定性延迟，适合400Gbps场景
    }
    // ...
}
```

**适用场景**:
- 高频交易 (HFT): 延迟从120ms降至32ms (4倍提升)
- 网络数据包处理
- 实时系统

### 4. 安全边界

```rust
unsafe fn hardware_access() {
    // unsafe块必须最小化
    // 用safe wrapper封装
}

pub fn safe_wrapper() {
    // 验证输入
    validate_input()?;
    
    // 调用unsafe核心
    unsafe { hardware_access() }
}
```

**安全收益**: 70%的CVE（缓冲区溢出、use-after-free）在编译时被消除

---

## Go 高性能模式

### 1. Worker Pool 工作池

**问题**: 无限制goroutine会导致内存泄漏和CPU抖动

```go
// 限制并发数，防止资源耗尽
func WorkerPool(jobs <-chan Job, results chan<- Result, numWorkers int) {
    var wg sync.WaitGroup
    
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                results <- process(job)
            }
        }()
    }
    
    wg.Wait()
    close(results)
}

// 使用: 处理图片/数据/请求时，限制worker数量
```

**最佳实践**:
- worker数量 = CPU核心数 或 连接池大小
- 使用buffered channel减少阻塞

### 2. Fan-Out/Fan-In 并行处理

```go
// Fan-Out: 分发任务到多个goroutine
func fanOut(tasks []Task, numWorkers int) []chan Result {
    taskChan := make(chan Task, len(tasks))
    for _, t := range tasks {
        taskChan <- t
    }
    close(taskChan)
    
    results := make([]chan Result, numWorkers)
    for i := 0; i < numWorkers; i++ {
        results[i] = make(chan Result, 100)
        go worker(taskChan, results[i])
    }
    return results
}

// Fan-In: 合并结果
func fanIn(channels []chan Result) <-chan Result {
    combined := make(chan Result)
    var wg sync.WaitGroup
    
    for _, ch := range channels {
        wg.Add(1)
        go func(c <-chan Result) {
            defer wg.Done()
            for r := range c {
                combined <- r
            }
        }(ch)
    }
    
    go func() {
        wg.Wait()
        close(combined)
    }()
    
    return combined
}
```

**应用场景**:
- 图片批量处理
- 分布式搜索（同时查询多个源）
- 数据处理管道

### 3. Context 生命周期管理

**问题**: goroutine泄漏（等待永远不会到来的channel值）

```go
func processWithTimeout(ctx context.Context, job Job) error {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel() // 确保资源释放
    
    select {
    case result := <-doWork(ctx, job):
        return handle(result)
    case <-ctx.Done():
        return ctx.Err() // 超时或取消
    }
}

// 级联取消：客户端断开→取消所有下游操作
func handler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context() // 自动关联请求生命周期
    processWithTimeout(ctx, job)
}
```

**关键模式**:
- 每个对外调用都传 `context.Context`
- 使用 `defer cancel()` 防止泄漏
- 检查 `ctx.Done()` 及时退出

### 4. Rate Limiting 限流

```go
type LeakyBucket struct {
    rate       float64    // 每秒token数
    capacity   float64    // 桶容量（突发）
    tokens     float64
    lastRefill time.Time
    mu         sync.Mutex
}

func (lb *LeakyBucket) Allow() bool {
    lb.mu.Lock()
    defer lb.mu.Unlock()
    
    now := time.Now()
    elapsed := now.Sub(lb.lastRefill).Seconds()
    lb.tokens = math.Min(lb.capacity, lb.tokens + elapsed*lb.rate)
    lb.lastRefill = now
    
    if lb.tokens >= 1 {
        lb.tokens--
        return true
    }
    return false
}

// 使用
limiter := NewLeakyBucket(100, 200) // 100/s, 突发200
if !limiter.Allow() {
    return ErrRateLimited
}
```

**效果**: Cloudflare报告错误率降低70%

### 5. 错误处理与资源清理

```go
// 结构化错误处理
func processDocuments(ctx context.Context, docs []Document) ([]Result, error) {
    g, ctx := errgroup.WithContext(ctx)
    
    results := make(chan Result, len(docs))
    defer close(results)
    
    // Fan-out
    for _, doc := range docs {
        doc := doc // 闭包捕获
        g.Go(func() error {
            result, err := process(ctx, doc)
            if err != nil {
                return err // 传播错误
            }
            select {
            case results <- result:
                return nil
            case <-ctx.Done():
                return ctx.Err()
            }
        })
    }
    
    // Fan-in
    var processed []Result
    go func() {
        for r := range results {
            processed = append(processed, r)
        }
    }()
    
    return processed, g.Wait() // 等待所有goroutine
}
```

---

## 语言选择决策树

```
性能关键场景:
├── 极致性能 + 内存安全 → Rust
│   ├── 网络基础设施 (Servo, Rathole)
│   ├── 高频交易 (120ms→32ms)
│   ├── 系统编程 (OS, 驱动)
│   └── AI推理引擎 (微秒级)
│
├── 快速开发 + 高并发 → Go
│   ├── Web服务 (Gin, Echo)
│   ├── 微服务架构
│   ├── 云原生工具 (Docker, K8s)
│   └── 数据处理管道
│
└── 遗留系统集成 → FFI桥接
    ├── Go调用Rust (性能热点)
    └── 逐步迁移策略
```

---

## 常见陷阱

| 语言 | 陷阱 | 解决方案 |
|:---|:---|:---|
| Rust | 过度使用unsafe | 最小化unsafe块，用safe wrapper封装 |
| Rust | 所有权借用冲突 | 使用Arc/Mutex，或重新设计数据结构 |
| Go | Goroutine泄漏 | 始终使用context管理生命周期 |
| Go | 数据竞争 | 使用-race检测，优先用channel而非共享内存 |
| Go | 死锁 | 确保channel有发送者和接收者，使用select |

---

## 性能基准

| 场景 | 指标 | Rust | Go | 对比 |
|:---|:---|:---:|:---:|:---|
| 网络延迟 | P99 | 32ms | - | Rust 4倍提升 |
| 内存安全 | CVE消除 | 70% | - | Rust编译时保证 |
| 并发模型 | 启动成本 | 2KB | 2KB | 相近 |
| 吞吐量 | 事务/秒 | 3.4x | 基准 | Rust同硬件提升 |
| 开发速度 | 新人上手 | 慢 | 快 | Go更易学 |

### 5. 高性能网络并发模式 (Rathole案例分析)

**来源**: [rathole-org/rathole](https://github.com/rathole-org/rathole) - 轻量级高性能反向代理

```rust
// 1. 使用 tokio::select! 实现多路复用
loop {
    tokio::select! {
        // 接受新连接
        ret = transport.accept(&listener) => {
            match ret {
                Ok((conn, addr)) => {
                    // 每个连接一个独立任务
                    tokio::spawn(async move {
                        handle_connection(conn).await
                    }.instrument(info_span!("connection", %addr)));
                }
                Err(e) => handle_error(e),
            }
        }
        // 监听关闭信号
        _ = shutdown_rx.recv() => break,
        // 处理配置更新
        change = update_rx.recv() => handle_config_change(change),
    }
}

// 2. 双键索引结构 (MultiMap) - O(1)双路查找
pub struct MultiMap<K1, K2, V> {
    map1: HashMap<Key<K1>, RawItem<K1, K2, V>>,
    map2: HashMap<Key<K2>, RawItem<K1, K2, V>>,
}
// 实现：一个Box，两个HashMap共享所有权，通过unsafe指针索引
// 用途：服务名hash查、token查，同一条连接

// 3. 连接池 + 背压控制
const TCP_POOL_SIZE: usize = 8;   // TCP连接缓存数
const UDP_POOL_SIZE: usize = 2;   // UDP连接缓存数
const CHAN_SIZE: usize = 2048;    // Channel缓冲区大小

// 4. Transport Trait抽象 - 运行时多态零成本
#[async_trait]
pub trait Transport: Send + Sync {
    type Stream: AsyncRead + AsyncWrite + Unpin + Send + Sync;
    async fn handshake(&self, conn: Self::RawStream) -> Result<Self::Stream>;
    async fn connect(&self, addr: &AddrMaybeCached) -> Result<Self::Stream>;
}
// 支持TCP/TLS/Noise/WebSocket，编译时确定，零运行时开销

// 5. 优雅错误处理 + 指数退避
let mut backoff = ExponentialBackoff {
    max_interval: Duration::from_millis(100),
    max_elapsed_time: None,
    ..Default::default()
};
// EMFILE/ENFILE/ENOMEM时自动退避，避免雪崩
```

**关键技巧**:
- `tokio::spawn` + `instrument`：每个连接独立追踪
- `tokio::select!`：单线程多路复用，无需多线程锁
- `Arc<RwLock<T>>`：读多写少场景的共享状态
- `Bytes`/`BytesMut`：引用计数缓冲区，零拷贝传输

---

## Gnet 高性能网络模式 (Go案例)

**来源**: [panjf2000/gnet](https://github.com/panjf2000/gnet) - 高性能事件驱动网络框架

### 1. Reactor模式

```go
// 多事件循环 + 负载均衡
type eventloop struct {
    idx          int               // 循环索引
    poller       *netpoll.Poller   // epoll/kqueue封装
    connections  connMatrix        // 连接存储
    buffer       []byte            // 读取缓冲区(64KB)
}

// Reactor主循环
func (el *eventloop) run() {
    for {
        // 等待I/O事件 (边缘触发ET模式)
        n, err := el.poller.Wait(el.buffer)
        if err != nil {
            handleError(err)
            continue
        }
        
        // 处理所有就绪事件
        for i := 0; i < n; i++ {
            fd := el.buffer[i]
            if conn := el.connections.get(fd); conn != nil {
                conn.processIO()
            }
        }
    }
}
```

**关键设计**:
- **多loop并行**: 每个loop一个goroutine，避免锁竞争
- **边缘触发(ET)**: 减少epoll_wait调用次数
- **预分配buffer**: 64KB读取缓冲区，减少内存分配

### 2. 负载均衡策略

```go
// 策略1: 轮询 (RoundRobin) - 简单均匀
func (lb *roundRobinLoadBalancer) next() *eventloop {
    el := lb.eventLoops[lb.nextIndex%uint64(lb.size)]
    lb.nextIndex++
    return el
}

// 策略2: 最少连接 (LeastConnections) - 长连接场景
func (lb *leastConnectionsLoadBalancer) next() *eventloop {
    el := lb.eventLoops[0]
    minN := el.countConn()
    for _, v := range lb.eventLoops[1:] {
        if n := v.countConn(); n < minN {
            minN = n
            el = v
        }
    }
    return el
}

// 策略3: 源地址哈希 (SourceAddrHash) - 会话保持
func (lb *sourceAddrHashLoadBalancer) next(addr net.Addr) *eventloop {
    hashCode := crc32.ChecksumIEEE([]byte(addr.String()))
    return lb.eventLoops[hashCode%lb.size]
}
```

**选择建议**:
- 均匀负载 → 轮询
- 长连接场景 → 最少连接
- 会话保持 → 源地址哈希

### 3. Goroutine池 (ants模式)

```go
const (
    DefaultAntsPoolSize = 1 << 18  // 256K容量
    ExpiryDuration = 10 * time.Second  // 过期清理
    Nonblocking = true  // 非阻塞提交
)

// 提交任务 (非阻塞)
func (p *Pool) Submit(task func()) error {
    w := p.getWorker()
    if w == nil {
        if p.Nonblocking {
            return ErrPoolOverload  // 立即返回错误，不堆积
        }
        // 阻塞等待...
    }
    w.task <- task
    return nil
}
```

**关键设计**:
- 非阻塞提交：避免goroutine堆积
- 自动过期：10秒无任务worker被回收
- panic恢复：防止单个任务崩溃影响整个池

### 4. 内存池化

```go
// 弹性缓冲区 - 延迟初始化 + 池化
type RingBuffer struct {
    rb *ring.Buffer
}

// 延迟初始化
func (b *RingBuffer) instance() *ring.Buffer {
    if b.rb == nil {
        b.rb = rbPool.Get()  // 从池获取
    }
    return b.rb
}

// 自动回收
func (b *RingBuffer) done() {
    if b.rb != nil && b.rb.IsEmpty() {
        rbPool.Put(b.rb)  // 归还池
        b.rb = nil
    }
}
```

**设计要点**:
- 延迟初始化：用到时才分配
- 池化复用：减少GC压力
- 自动归还：空缓冲区自动回池

---

## 实战建议

1. **新系统**: 优先Go（开发快），性能瓶颈处用Rust重写
2. **性能敏感**: 直接用Rust（零拷贝、无GC暂停）
3. **遗留系统**: FFI桥接，逐步替换
4. **团队技能**: 考虑学习曲线，Go更适合快速扩张团队

---

## 参考资源

- [Building Next-Generation Network Infrastructure in Rust - Conf42 2025](https://www.conf42.com/Rustlang_2025)
- [Go Concurrency Patterns 2025 - Madrigan](https://blog.madrigan.com)
- [7 Powerful Golang Concurrency Patterns - Cristian Curteanu](https://cristiancurteanu.com)
- [Go Memory Management - Liam Hampton](https://www.youtube.com)
- [Gnet: High-Performance Event-Driven Networking Framework](https://github.com/panjf2000/gnet)
- [Redis单线程事件循环深度解析](https://thuva4.com/blog/part-1-the-core-of-redis/)
- [Redis内部工作原理](https://betterprogramming.pub/internals-workings-of-redis-718f5871be84)

---

*技能内化完成 - 2026-03-17*  
*更新: v1.3 添加Rathole + Gnet + Redis模式分析*  
*包含: 单线程Reactor、Pipeline批量处理、时间事件定时器*


---

## Actix-web 高性能Web模式 (Rust案例)

**来源**: [actix/actix-web](https://github.com/actix/actix-web) - 高性能Rust Web框架

### 1. Service Trait 抽象

```rust
// 核心Service trait - 统一的请求处理接口
pub trait Service<Req> {
    type Response;
    type Error;
    type Future: Future<Output = Result<Self::Response, Self::Error>>;
    
    fn call(&self, req: Req) -> Self::Future;
}
```

**设计要点**:
- **统一接口**: 所有组件实现相同的Service trait
- **可组合**: Service可以嵌套组合
- **类型安全**: 编译时检查请求/响应类型

### 2. Extractor 模式 (参数提取)

```rust
// FromRequest trait - 从请求中提取数据
pub trait FromRequest: Sized {
    type Error;
    type Future: Future<Output = Result<Self, Self::Error>>;
    
    fn from_request(req: &HttpRequest, payload: &mut Payload) -> Self::Future;
}

// 应用：自动参数提取
async fn handler(
    path: web::Path<(String, u32)>,      // 路径参数
    query: web::Query<MyQuery>,          // 查询参数
    body: web::Json<MyBody>,             // JSON body
    state: web::Data<MyState>,           // 应用状态
) -> impl Responder {
    // 参数自动提取，无需手动解析
}
```

**优点**:
- 声明式参数提取
- 类型安全
- 自动错误处理

### 3. Data<T> 共享状态

```rust
// Data<T> - 线程安全的应用状态共享
pub struct Data<T: ?Sized>(Arc<T>);

impl<T> Data<T> {
    pub fn new(state: T) -> Data<T> {
        Data(Arc::new(state))
    }
}

// 使用：跨Worker共享状态
let data = web::Data::new(Mutex::new(MyState { count: 0 }));

App::new()
    .app_data(data.clone())  // 所有Worker共享
    .service(handler)
```

**特点**:
- Arc包装，克隆成本低
- 线程安全
- 状态在Worker间共享

### 4. 中间件链 (洋葱模型)

```rust
// 中间件执行顺序 (洋葱模型)
// Request -> C -> B -> A -> Handler -> A -> B -> C -> Response

App::new()
    .wrap(LoggingMiddleware)   // 最外层
    .wrap(MetricsMiddleware)   // 中间
    .wrap(AuthMiddleware)      // 最内层
    .service(handler)
```

---

*技能文档 v1.3*
*更新: 添加Actix-web Service Trait、Extractor、Data<T>、中间件链模式*
