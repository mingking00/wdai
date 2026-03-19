# Network Distributed Architecture
# 网络分布式架构详细设计

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Network Distributed System                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Master Node                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐     │   │
│  │  │ Task Queue   │  │ Worker Pool  │  │ Result Aggregator    │     │   │
│  │  │ 任务队列      │  │ Worker管理    │  │ 结果聚合器            │     │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘     │   │
│  │         │                 │                                       │   │
│  │  ┌──────▼─────────────────▼──────────────────┐                   │   │
│  │  │         TCP Server (Port 8765)            │                   │   │
│  │  │  - 监听Worker连接                          │                   │   │
│  │  │  - 分发任务                                │                   │   │
│  │  │  - 收集结果                                │                   │   │
│  │  └──────────────────┬─────────────────────────┘                   │   │
│  └─────────────────────┼─────────────────────────────────────────────┘   │
│                        │                                                   │
│           TCP Socket   │   JSON Protocol                                  │
│                        │                                                   │
│       ┌────────────────┼────────────────┐                                 │
│       │                │                │                                 │
│  ┌────▼────┐     ┌────▼────┐     ┌────▼────┐                            │
│  │ Worker1 │     │ Worker2 │     │ Worker3 │                            │
│  │ (192.168│     │ (192.168│     │ (192.168│                            │
│  │  .1.101)│     │  .1.102)│     │  .1.103)│                            │
│  │         │     │         │     │         │                            │
│  │ ┌─────┐ │     │ ┌─────┐ │     │ ┌─────┐ │                            │
│  │ │Task │ │     │ │Task │ │     │ │Task │ │                            │
│  │ │Exec │ │     │ │Exec │ │     │ │Exec │ │                            │
│  │ └─────┘ │     │ └─────┘ │     │ └─────┘ │                            │
│  └─────────┘     └─────────┘     └─────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. 通信协议

### 2.1 协议层次

```
┌─────────────────────────────────────────┐
│  Application Layer (应用层)              │
│  - Task Definition                       │
│  - Result Format                         │
│  - Status Update                         │
├─────────────────────────────────────────┤
│  Message Layer (消息层)                  │
│  - JSON Serialization                    │
│  - Message Type                          │
│  - Payload Encoding                      │
├─────────────────────────────────────────┤
│  Transport Layer (传输层)                │
│  - TCP Socket                            │
│  - Port 8765                             │
│  - Connection Management                 │
├─────────────────────────────────────────┤
│  Network Layer (网络层)                  │
│  - IP Address                            │
│  - Routing                               │
└─────────────────────────────────────────┘
```

### 2.2 消息格式

所有消息使用 **JSON格式**，UTF-8编码。

#### Message Type 1: Worker Registration (Worker注册)
```json
{
  "msg_type": "register",
  "timestamp": "2026-03-10T04:30:00.000Z",
  "payload": {
    "worker_id": "worker-001",
    "hostname": "server-01",
    "capabilities": {
      "cpu_cores": 8,
      "memory_gb": 32,
      "gpu": false
    },
    "version": "1.0.0"
  }
}
```

#### Message Type 2: Task Assignment (任务分配)
```json
{
  "msg_type": "task_assign",
  "timestamp": "2026-03-10T04:30:01.000Z",
  "task_id": "task-uuid-001",
  "payload": {
    "task_config": {
      "task_id": "data_fetch_1",
      "agent_type": "DataFetcher",
      "duration": 0.5,
      "timeout": 3.0,
      "max_retries": 2
    },
    "deadline": "2026-03-10T04:30:31.000Z"
  }
}
```

#### Message Type 3: Task Result (任务结果)
```json
{
  "msg_type": "task_result",
  "timestamp": "2026-03-10T04:30:05.000Z",
  "task_id": "task-uuid-001",
  "payload": {
    "status": "success",
    "duration": 0.49,
    "output": {
      "data": "...",
      "metadata": {}
    },
    "worker_id": "worker-001"
  }
}
```

#### Message Type 4: Heartbeat (心跳)
```json
{
  "msg_type": "heartbeat",
  "timestamp": "2026-03-10T04:30:10.000Z",
  "payload": {
    "worker_id": "worker-001",
    "status": "idle",
    "load": {
      "cpu_percent": 15.5,
      "memory_percent": 42.0
    }
  }
}
```

#### Message Type 5: Error (错误)
```json
{
  "msg_type": "error",
  "timestamp": "2026-03-10T04:30:15.000Z",
  "task_id": "task-uuid-001",
  "payload": {
    "error_type": "timeout",
    "error_message": "Task execution exceeded timeout",
    "worker_id": "worker-001"
  }
}
```

## 3. 架构组件

### 3.1 Master组件

```python
class MasterNode:
    """
    Master节点职责：
    1. 监听Worker连接
    2. 维护Worker池
    3. 任务调度分配
    4. 结果收集聚合
    5. 故障检测恢复
    """
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.workers: Dict[str, WorkerConnection] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results: Dict[str, TaskResult] = {}
        
    async def start(self):
        """启动Master服务"""
        server = await asyncio.start_server(
            self._handle_worker,
            self.host,
            self.port
        )
        
        # 启动调度器
        asyncio.create_task(self._scheduler())
        
        async with server:
            await server.serve_forever()
    
    async def _scheduler(self):
        """任务调度器"""
        while True:
            task = await self.task_queue.get()
            
            # 选择合适的Worker
            worker = self._select_worker(task)
            
            if worker:
                await self._assign_task(worker, task)
            else:
                # 没有可用Worker，放回队列
                await asyncio.sleep(1)
                await self.task_queue.put(task)
    
    def _select_worker(self, task: Task) -> Optional[Worker]:
        """Worker选择策略"""
        for worker in self.workers.values():
            if worker.status == "idle" and self._check_resources(worker, task):
                return worker
        return None
```

### 3.2 Worker组件

```python
class WorkerNode:
    """
    Worker节点职责：
    1. 连接Master
    2. 接收执行任务
    3. 执行任务逻辑
    4. 返回执行结果
    5. 定期心跳汇报
    """
    
    def __init__(self, master_host: str, master_port: int):
        self.master_host = master_host
        self.master_port = master_port
        self.worker_id = str(uuid.uuid4())
        self.status = "idle"
        
    async def start(self):
        """启动Worker"""
        reader, writer = await asyncio.open_connection(
            self.master_host,
            self.master_port
        )
        
        # 注册到Master
        await self._register(reader, writer)
        
        # 启动心跳
        asyncio.create_task(self._heartbeat(writer))
        
        # 监听任务
        await self._listen_tasks(reader, writer)
    
    async def _execute_task(self, task: Task) -> TaskResult:
        """执行任务"""
        self.status = "busy"
        
        try:
            # 实际执行任务
            result = await self._run_agent_logic(task)
            return TaskResult(success=True, output=result)
        except Exception as e:
            return TaskResult(success=False, error=str(e))
        finally:
            self.status = "idle"
```

## 4. 状态机

### 4.1 Worker状态机

```
                    ┌─────────────┐
                    │   INIT      │
                    └──────┬──────┘
                           │ connect
                           ▼
                    ┌─────────────┐
               ┌────┤ REGISTERING │
               │    └──────┬──────┘
               │           │ register success
               │           ▼
               │    ┌─────────────┐
               │◄───┤    IDLE     │◄────────┐
               │    └──────┬──────┘         │
               │           │ task assigned   │
               │           ▼                 │
               │    ┌─────────────┐         │
               │◄───┤    BUSY     ├─────────┤ task complete
               │    └──────┬──────┘         │
               │           │ heartbeat timeout
               │           ▼                 │
               │    ┌─────────────┐         │
               └───►│  OFFLINE    ├─────────┘ reconnect
                    └─────────────┘
```

### 4.2 Task状态机

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ PENDING │────►│ QUEUED  │────►│ASSIGNED │
└─────────┘     └─────────┘     └────┬────┘
                                     │
                                     ▼
                              ┌─────────────┐
                         ┌────┤   RUNNING   │
                         │    └──────┬──────┘
                         │           │
              timeout/   │           │ success
              error      │           ▼
                         │    ┌─────────────┐
                         └───►│   FAILED    │
                              └─────────────┘
                                     │
                                     │ retry
                                     ▼
                              ┌─────────────┐
                              │   SUCCESS   │
                              └─────────────┘
```

## 5. 容错机制

### 5.1 Worker故障检测

```python
class FaultToleranceManager:
    """容错管理器"""
    
    HEARTBEAT_TIMEOUT = 10  # 秒
    
    async def monitor_workers(self):
        """监控Worker健康"""
        while True:
            for worker in self.workers.values():
                if self._is_worker_dead(worker):
                    await self._handle_worker_failure(worker)
            await asyncio.sleep(5)
    
    def _is_worker_dead(self, worker: Worker) -> bool:
        """检测Worker是否失效"""
        time_since_last_heartbeat = time.time() - worker.last_heartbeat
        return time_since_last_heartbeat > self.HEARTBEAT_TIMEOUT
    
    async def _handle_worker_failure(self, worker: Worker):
        """处理Worker故障"""
        # 1. 标记Worker离线
        worker.status = "offline"
        
        # 2. 重新分配该Worker的任务
        for task in worker.assigned_tasks:
            task.status = "pending"
            await self.task_queue.put(task)
        
        # 3. 通知其他组件
        await self._notify_worker_failure(worker)
```

### 5.2 任务重试策略

```python
class RetryPolicy:
    """重试策略"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    def get_retry_delay(self, attempt: int) -> float:
        """指数退避"""
        return (self.backoff_factor ** attempt)
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否重试"""
        if attempt >= self.max_retries:
            return False
        
        # 某些错误不重试（如语法错误）
        non_retryable = [SyntaxError, TypeError]
        if any(isinstance(error, e) for e in non_retryable):
            return False
        
        return True
```

## 6. 性能优化

### 6.1 连接池

```python
class ConnectionPool:
    """TCP连接池"""
    
    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.connections: Queue = Queue()
        self.active_connections: int = 0
    
    async def acquire(self) -> Connection:
        """获取连接"""
        if not self.connections.empty():
            return await self.connections.get()
        
        if self.active_connections < self.max_connections:
            conn = await self._create_connection()
            self.active_connections += 1
            return conn
        
        # 等待可用连接
        return await self.connections.get()
    
    async def release(self, conn: Connection):
        """释放连接"""
        await self.connections.put(conn)
```

### 6.2 负载均衡

```python
class LoadBalancer:
    """负载均衡器"""
    
    STRATEGIES = {
        "round_robin": RoundRobinStrategy(),
        "least_connections": LeastConnectionsStrategy(),
        "weighted": WeightedStrategy(),
        "resource_based": ResourceBasedStrategy()
    }
    
    def select_worker(self, task: Task, workers: List[Worker]) -> Worker:
        """选择Worker"""
        strategy = self.STRATEGIES.get(task.scheduling_strategy)
        return strategy.select(workers, task)
```

## 7. 安全考虑

### 7.1 认证机制

```python
class Authenticator:
    """认证器"""
    
    async def authenticate_worker(self, reader, writer) -> bool:
        """Worker认证"""
        # 1. 接收认证令牌
        auth_token = await reader.readline()
        
        # 2. 验证令牌
        if not self._verify_token(auth_token):
            writer.close()
            return False
        
        return True
    
    def _verify_token(self, token: bytes) -> bool:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload.get("role") == "worker"
        except jwt.InvalidTokenError:
            return False
```

### 7.2 通信加密

```python
# 使用TLS加密通信
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain('server.crt', 'server.key')
ssl_context.load_verify_locations('ca.crt')

server = await asyncio.start_server(
    self._handle_worker,
    self.host,
    self.port,
    ssl=ssl_context
)
```

## 8. 部署配置

### 8.1 Master节点启动

```python
# master.py
async def main():
    master = MasterNode(
        host="0.0.0.0",
        port=8765,
        max_workers=100,
        task_timeout=300
    )
    
    await master.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### 8.2 Worker节点启动

```python
# worker.py
async def main():
    worker = WorkerNode(
        master_host="master.example.com",
        master_port=8765,
        worker_id="worker-001",
        capabilities={
            "cpu_cores": 8,
            "memory_gb": 32,
            "gpu": True
        }
    )
    
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## 9. 监控与日志

### 9.1 指标收集

```python
class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = {
            "tasks_total": 0,
            "tasks_success": 0,
            "tasks_failed": 0,
            "worker_count": 0,
            "avg_task_duration": 0.0
        }
    
    def record_task_completion(self, task: Task, result: TaskResult):
        """记录任务完成"""
        self.metrics["tasks_total"] += 1
        
        if result.success:
            self.metrics["tasks_success"] += 1
        else:
            self.metrics["tasks_failed"] += 1
        
        # 更新平均耗时
        self.metrics["avg_task_duration"] = (
            (self.metrics["avg_task_duration"] * (self.metrics["tasks_total"] - 1) + result.duration)
            / self.metrics["tasks_total"]
        )
```

---

## 总结

这个网络分布式架构设计提供了：

1. **可扩展性** - Master-Worker架构支持动态扩缩容
2. **容错性** - 心跳检测、自动重试、故障恢复
3. **高性能** - 连接池、负载均衡、异步通信
4. **安全性** - TLS加密、JWT认证
5. **可观测性** - 监控指标、结构化日志

这是一个生产就绪的分布式系统设计。
