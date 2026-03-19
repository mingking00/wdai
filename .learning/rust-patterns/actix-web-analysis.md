# Actix-web 架构分析 - 2026-03-17

## 项目信息
- **名称**: Actix-web
- **语言**: Rust
- **大小**: 5.2MB (312个Rust文件)
- **定位**: 高性能、务实的Web框架
- **核心特点**: Actor模型、Service trait系统、中间件链

## 核心架构

### 1. Service Trait 系统 (核心抽象)

```rust
// 核心Service trait - 处理请求的基本单元
pub trait Service<Req> {
    type Response;
    type Error;
    type Future: Future<Output = Result<Self::Response, Self::Error>>;
    
    fn call(&self, req: Req) -> Self::Future;
}

// ServiceFactory - 创建Service的工厂
pub trait ServiceFactory<Req> {
    type Service: Service<Req>;
    type Config;
    type Error;
    type InitError;
    type Future: Future<Output = Result<Self::Service, Self::InitError>>;
    
    fn new_service(&self, cfg: Self::Config) -> Self::Future;
}
```

**架构层次**:
```
HttpServer
    └── Worker threads (N = CPU cores)
        └── App (per worker)
            └── Middleware chain (wrap)
                └── Router
                    └── Route
                        └── Handler
                            └── Extractor(s)
```

### 2. 多Worker模型

```rust
// HttpServer - 管理多个worker线程
pub struct HttpServer<F, I, S, B> {
    factory: F,           // App工厂
    builder: ServerBuilder,
    // ...
}

// 默认worker数 = std::thread::available_parallelism()
// 每个worker有独立的App实例
HttpServer::new(|| {
    App::new()
        .service(handler)
})
.bind(("127.0.0.1", 8080))?
.workers(4)  // 显式设置worker数
.run()
```

**Worker模型特点**:
- 每个worker独立运行，无共享状态
- 请求通过round-robin分发到workers
- App工厂每个worker调用一次
- 状态通过 `web::Data<T>` (Arc包装)共享

### 3. Data共享状态

```rust
// Data<T> - 线程安全的应用状态
#[derive(Debug)]
pub struct Data<T: ?Sized>(Arc<T>);

// 使用方式
let data = web::Data::new(Mutex::new(MyState { count: 0 }));

App::new()
    .app_data(data.clone())  // 共享状态
    .route("/", web::get().to(handler))

async fn handler(state: web::Data<Mutex<MyState>>) -> impl Responder {
    let mut state = state.lock().unwrap();
    state.count += 1;
    HttpResponse::Ok().body(format!("Count: {}", state.count))
}
```

**关键设计**:
- `Data<T>` 包装 `Arc<T>`，克隆成本低
- 状态在worker间通过Arc共享
- 并发控制由状态内部类型负责 (Mutex/RwLock/Atomic)

### 4. 中间件系统

```rust
// 中间件顺序 (洋葱模型)
// Request -> C -> B -> A -> Handler -> A -> B -> C -> Response

App::new()
    .wrap(MiddlewareA)  // 最外层
    .wrap(MiddlewareB)
    .wrap(MiddlewareC)  // 最内层
    .service(handler)
```

**中间件实现**:
```rust
// 简单中间件 - from_fn
async fn my_mw(
    req: ServiceRequest,
    next: Next<impl MessageBody>,
) -> Result<ServiceResponse<impl MessageBody>, Error> {
    // pre-processing
    println!("Before handler");
    
    // 调用下一个中间件/handler
    let res = next.call(req).await?;
    
    // post-processing
    println!("After handler");
    
    Ok(res)
}

// 复杂中间件 - Transform + Service trait
pub struct MyMiddleware;

impl<S, B> Transform<S, ServiceRequest> for MyMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>>,
{
    type Response = ServiceResponse<B>;
    type Error = S::Error;
    type Transform = MyMiddlewareService<S>;
    type InitError = ();
    type Future = Ready<Result<Self::Transform, Self::InitError>>;
    
    fn new_transform(&self, service: S) -> Self::Future {
        ok(MyMiddlewareService { service })
    }
}
```

**内置中间件**:
- Logger: 请求日志
- Compress: 响应压缩 (br, gzip, deflate, zstd)
- NormalizePath: 路径规范化
- DefaultHeaders: 默认响应头
- ErrorHandlers: 错误处理
- Condition: 条件中间件

### 5. Handler与Extractor

```rust
// Handler trait - 处理请求的函数
pub trait Handler<Args>: Clone + 'static {
    type Output;
    type Future: Future<Output = Self::Output>;
    fn call(&self, args: Args) -> Self::Future;
}

// FromRequest trait - 从请求中提取数据
pub trait FromRequest: Sized {
    type Error: Into<Error>;
    type Future: Future<Output = Result<Self, Self::Error>>;
    fn from_request(req: &HttpRequest, payload: &mut Payload) -> Self::Future;
}
```

**Extractor示例**:
```rust
async fn handler(
    path: web::Path<(String, u32)>,      // URL路径参数
    query: web::Query<MyQuery>,          // URL查询参数
    body: web::Json<MyBody>,             // JSON body
    state: web::Data<MyState>,           // 应用状态
    req: HttpRequest,                    // 完整请求
) -> impl Responder {
    // 使用提取的数据...
}
```

### 6. 路由系统

```rust
// Router结构
App::new()
    .service(
        web::scope("/api")              // Scope - 路径前缀
            .guard(guard::Header("version", "v1"))
            .service(
                web::resource("/users") // Resource - 资源
                    .route(web::get().to(list_users))
                    .route(web::post().to(create_user))
            )
    )
    .service(
        web::resource("/articles/{id}") // 路径参数
            .route(web::get().to(get_article))
            .route(web::put().to(update_article))
            .route(web::delete().to(delete_article))
    )
    .default_service(web::to(|| async { "404" }))  // 默认服务
```

**路由匹配**:
- 按注册顺序匹配
- 支持路径参数 `{id}`
- 支持正则约束 `{id:\d+}`
- Guard条件匹配 (Header, Method, etc.)

## 可复用模式

| 模式 | 实现 | 可应用性 |
|:---|:---|:---:|
| **Service Trait抽象** | actix-service | ⭐⭐⭐ |
| **多Worker模型** | HttpServer.workers() | ⭐⭐ |
| **共享状态** | Data<Arc<T>> | ⭐⭐⭐ |
| **中间件链** | Transform/Service | ⭐⭐ |
| **Extractor模式** | FromRequest | ⭐⭐⭐ |
| **App工厂** | Fn() -> App | ⭐⭐ |

## 与之前项目对比

| 特性 | Actix-web | Gnet | Redis | Rathole |
|:---|:---|:---|:---|:---|
| **线程模型** | 多Worker | 多EventLoop | 单线程 | 多线程tokio |
| **状态共享** | Data<Arc<T>> | 无锁 | 无锁 | Arc<RwLock> |
| **并发** | 每个Worker独立 | 多Loop | 单Loop | Async |
| **扩展性** | 中间件链 | 负载均衡 | Pipeline | - |
| **适用** | Web服务 | 网络框架 | KV存储 | NAT代理 |

## 应用到wdai

### 可借鉴模式:

1. **Service Trait抽象**
   ```python
   # 当前: Agent是类
   # 改进: Agent作为Service trait
   # 好处: 统一的请求处理接口
   ```

2. **Extractor模式**
   ```python
   # 当前: 手动构造Context
   # 改进: 自动从请求提取参数
   # 好处: 简化handler签名
   
   # 改进前
   async def execute(self, subtask: SubTask, context: NarrowContext)
   
   # 改进后 (类似Extractor)
   async def execute(
       self,
       task_type: FromSubTask[str],
       content: FromSubTask[str],
       context: FromRequest[NarrowContext]
   )
   ```

3. **共享状态 (Data<T>)**
   ```python
   # 当前: 每个Agent独立状态
   # 改进: 共享统计信息、配置
   # 好处: 跨Agent访问公共数据
   
   shared_stats = Data(Arc::new(Stats::new()))
   registry.register(coder, shared_stats.clone())
   registry.register(reviewer, shared_stats.clone())
   ```

4. **App工厂模式**
   ```python
   # 当前: 注册表单例
   # 改进: 工厂函数创建Agent
   # 好处: 每个任务独立配置
   
   AgentSystem::new(|| {
       let config = load_config();
       Agent::new(config)
   })
   .workers(4)
   ```

5. **中间件链**
   ```python
   # 当前: 直接执行
   # 改进: 执行前后可插入处理
   # 好处: 日志、监控、重试统一处理
   
   Agent::new()
       .wrap(LoggingMiddleware)
       .wrap(MetricsMiddleware)
       .wrap(RetryMiddleware)
       .service(handler)
   ```

## 建议

**暂不应用**:
- 多Worker模型 - 与当前asyncio单进程冲突
- 完整的中间件链 - 复杂度较高

**可考虑**:
- **Extractor模式** - 简化Context构造
- **Data<T>共享状态** - 统一统计和配置
- **Service trait思想** - 统一Agent接口

---
