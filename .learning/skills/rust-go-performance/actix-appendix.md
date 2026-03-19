

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
