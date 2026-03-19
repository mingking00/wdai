# wdai v3.3 升级说明 - Actix-web模式应用

## 升级内容

### 1. 新增文件
- `core/agent_system/service_trait.py` - Service Trait系统
- `core/agent_system/actix_integration.py` - Actix-web集成

### 2. 主要改进 (Actix-web模式)

| 模式 | 来源 | 应用位置 | 效果 |
|:---|:---|:---|:---:|
| **Service Trait** | Actix-web Service | ServiceAgent.call() | 统一接口 |
| **Extractor** | Actix-web FromRequest | TaskType/TaskContent/Context | 自动参数提取 |
| **Data<T>** | Actix-web Data | SharedData/SharedStateManager | 跨Agent状态共享 |
| **中间件链** | Actix-web Middleware | MiddlewareChain | 日志/监控/重试 |

### 3. 核心组件

#### 3.1 Service Trait (统一接口)

```python
from core.agent_system import ServiceAgent, ServiceResult

class MyAgent(ServiceAgent):
    async def _handle(self, request):
        # 处理请求
        return ServiceResult.ok({'data': result})

# 统一调用
result = await agent.call({'task': 'example'})
```

#### 3.2 Extractor模式 (自动参数提取)

```python
from core.agent_system import TaskType, TaskContent, ContextExtractor

# 自动从请求中提取参数
task_type = await TaskType.from_request(request)
content = await TaskContent.from_request(request)
context = await ContextExtractor.from_request(request)

print(f"类型: {task_type.value}")
print(f"内容: {content.value}")
print(f"任务ID: {context.task_id}")
```

#### 3.3 Data<T>共享状态

```python
from core.agent_system import SharedStateManager, SharedData

# 创建共享状态
manager = SharedStateManager()
manager.register('stats', {'requests': 0, 'errors': 0})

# 获取共享状态
shared = manager.get('stats')

# 读取 (加锁)
with shared.read() as data:
    print(data['requests'])

# 写入 (加锁)
with shared.write() as data:
    data['requests'] += 1
```

#### 3.4 中间件链

```python
from core.agent_system import (
    MiddlewareChain,
    LoggingMiddleware,
    MetricsMiddleware
)

# 构建中间件链
chain = MiddlewareChain()
chain.add(LoggingMiddleware()).add(MetricsMiddleware())

# 执行
result = await chain.execute(request, handler)
```

### 4. Actix-style Agent

```python
from core.agent_system import ActixStyleAgent, AgentConfig, AgentRole

class MyAgent(ActixStyleAgent):
    async def process(self, subtask, context):
        # 业务逻辑
        return {'output': 'result'}
    
    def can_handle(self, task_type):
        return task_type in ['my-type']

# 使用
config = AgentConfig(role=AgentRole.CODER, name='my-agent')
agent = MyAgent(config)

# 添加中间件
agent.add_middleware(LoggingMiddleware())

# 执行
result = await agent.execute(subtask, context)
```

### 5. 与现有系统集成

```python
# 原有代码 (v3.0)
from core.agent_system import BaseAgent

class MyAgent(BaseAgent):
    async def execute(self, subtask, context):
        return AgentResult(success=True, output='result')

# 新方式 (v3.3) - 向后兼容
from core.agent_system import ActixStyleAgent

class MyAgent(ActixStyleAgent):
    async def process(self, subtask, context):
        # 自动支持中间件、日志、监控
        return {'output': 'result'}
```

### 6. 版本演进

```
v3.0 (基础)
├── BaseAgent - 基础Agent
└── AgentRegistry - 注册表

v3.1 (Rathole模式)
├── ExponentialBackoff - 指数退避
├── ExecutionPool - 执行池
└── ResourceLimits - 资源限制

v3.2 (Gnet模式)
├── LoadBalancer - 负载均衡
├── NonBlockingExecutionPool - 非阻塞池
└── AgentLoadMetrics - 负载监控

v3.3 (Actix-web模式)
├── ServiceAgent - Service Trait
├── Extractor - 参数提取
├── SharedData - 状态共享
└── MiddlewareChain - 中间件链
```

### 7. 测试验证

```bash
cd wdai_v3 && python3 tests/test_v33_actix.py
```

**测试结果:**
```
测试1: Service Trait       ✅ 3/3 通过
测试2: Extractor模式       ✅ 3/3 通过
测试3: 共享状态            ✅ 2/2 通过
测试4: 中间件链            ✅ 2/2 通过
测试5: Actix-style Agent   ✅ 2/2 通过

最终汇总: 12/12 通过 (100%)
```

### 8. 与之前版本对比

| 特性 | v3.2 (Gnet) | v3.3 (Actix-web) |
|:---|:---|:---|
| Agent接口 | 直接类方法 | Service Trait |
| 参数传递 | 手动构造 | Extractor自动提取 |
| 状态共享 | 无 | SharedData跨Agent |
| 执行前后处理 | 无 | 中间件链 |
| 负载均衡 | ✅ 有 | ✅ 兼容 |
| 背压控制 | ✅ 有 | ✅ 兼容 |

### 9. 迁移步骤

1. **直接使用** (向后兼容):
```python
# 原有代码无需修改
from core.agent_system import BaseAgent
```

2. **升级使用** (推荐):
```python
from core.agent_system import ActixStyleAgent

class MyAgent(ActixStyleAgent):
    async def process(self, subtask, context):
        # 享受中间件、日志、监控
        return {'result': 'data'}
```

### 10. 验证清单

- [ ] Service Trait调用正常
- [ ] Extractor参数提取正确
- [ ] 共享状态读写正常
- [ ] 中间件链执行顺序正确
- [ ] Actix-style Agent向后兼容
- [ ] 与v3.1/v3.2功能兼容

---
*升级文档 - 2026-03-17*  
*Actix-web模式来源: https://actix.rs*
