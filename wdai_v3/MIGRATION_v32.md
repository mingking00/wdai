# wdai v3.2 升级说明 - Gnet模式应用

## 升级内容

### 1. 新增文件
- `core/agent_system/load_balancer.py` - 负载均衡与执行池
- `core/agent_system/enhanced_registry.py` - 增强版注册表

### 2. 主要改进 (Gnet模式)

| 模式 | 来源 | 改进前 | 改进后 | 收益 |
|:---|:---|:---|:---|:---:|
| **负载均衡** | Gnet load_balancer.go | 固定分配 | 4种策略可选 | 更优调度 |
| **非阻塞池** | Gnet ants | 阻塞等待 | 背压控制 | 防雪崩 |
| **负载监控** | Gnet eventloop | 基础统计 | 实时指标 | 可观测性 |
| **健康评分** | Gnet LeastConnections | 无 | 0-1评分 | 智能选择 |

### 3. 负载均衡策略

```python
from core.agent_system.load_balancer import LoadBalancingStrategy

# 策略1: 轮询 (RoundRobin)
# 简单均匀，适合任务类型相同

# 策略2: 最少负载 (LeastLoaded) - 默认
# 选择当前负载最低的Agent，适合长任务

# 策略3: 加权响应 (WeightedResponse)
# 考虑历史成功率+响应时间，适合异构Agent

# 策略4: 哈希 (HashBased)
# 相同任务路由到同一Agent，适合缓存友好
```

### 4. 使用示例

#### 基本使用

```python
from core.agent_system.enhanced_registry import EnhancedAgentRegistry
from core.agent_system.load_balancer import LoadBalancingStrategy

# 创建增强版注册表
registry = EnhancedAgentRegistry(
    default_strategy=LoadBalancingStrategy.LEAST_LOADED
)
await registry.initialize()

# 注册Agent (与普通注册表相同)
registry.register(agent)

# 负载均衡选择 (新增)
agent = registry.select(
    role=AgentRole.CODER,
    task_hint="python refactoring"  # 用于哈希策略
)
```

#### 不同策略选择

```python
# 策略1: 最少负载 (默认)
agent = registry.select(AgentRole.CODER)

# 策略2: 轮询
agent = registry.select(
    AgentRole.CODER,
    strategy=LoadBalancingStrategy.ROUND_ROBIN
)

# 策略3: 加权响应 (考虑历史性能)
agent = registry.select(
    AgentRole.CODER,
    strategy=LoadBalancingStrategy.WEIGHTED_RESPONSE
)

# 策略4: 哈希 (相同task_hint路由到同一Agent)
agent = registry.select(
    AgentRole.CODER,
    task_hint="user_123_task_456",
    strategy=LoadBalancingStrategy.HASH_BASED
)
```

#### 负载监控

```python
# 获取Agent指标
metrics = registry.get_agent_metrics('coder-1')
print(f'当前负载: {metrics.current_load}')
print(f'成功率: {metrics.success_rate:.0%}')
print(f'健康评分: {metrics.health_score:.2f}')
print(f'平均响应: {metrics.avg_response_time_ms:.0f}ms')

# 获取注册表完整状态
status = registry.get_registry_status()
print(f'总Agent数: {status[\"total_agents\"]}')
print(f'全局池: {status[\"global_pool\"]}')
print(f'角色分布: {status[\"role_distribution\"]}')
```

### 5. 非阻塞执行池

```python
from core.agent_system.load_balancer import NonBlockingExecutionPool

# 创建非阻塞池
pool = NonBlockingExecutionPool(
    max_concurrent=10,      # 最大并发
    max_queue_size=100,     # 队列大小
    nonblocking=True        # 满时立即返回错误
)
await pool.initialize()

# 获取槽位
if await pool.acquire_slot(timeout=5.0):
    try:
        # 执行任务
        result = await execute_task()
    finally:
        await pool.release_slot()
else:
    # 池满，背压控制
    raise RuntimeError("系统过载，请稍后重试")

# 监控池状态
print(f'池利用率: {pool.metrics[\"utilization\"]:.0%}')
print(f'已拒绝: {pool.metrics[\"rejected\"]}')
```

### 6. 向后兼容

增强版注册表完全兼容原注册表API:

```python
# 原有代码无需修改
registry = EnhancedAgentRegistry()  # 替换原AgentRegistry
registry.register(agent)
agent = registry.get(AgentRole.CODER)  # 仍然可用
```

**推荐迁移**:
```python
# 改进: 使用负载均衡选择
agent = registry.select(AgentRole.CODER)  # 替代 registry.get()
```

### 7. 与v3.1 Rathole模式对比

| 特性 | v3.1 (Rathole) | v3.2 (Gnet) |
|:---|:---|:---|
| **重试机制** | 指数退避 | 指数退避 |
| **并发控制** | Semaphore限制 | 非阻塞池 + 背压 |
| **Agent选择** | 固定分配 | 4种负载均衡策略 |
| **负载监控** | 基础统计 | 实时指标 + 健康评分 |
| **资源管理** | 执行槽位 | 执行槽位 + 队列池 |

### 8. 集成测试

```bash
cd wdai_v3 && python3 -c "
import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system.load_balancer import (
    LoadBalancingStrategy, AgentLoadMetrics, NonBlockingExecutionPool
)
from core.agent_system.enhanced_registry import EnhancedAgentRegistry

async def test():
    # 测试负载均衡器
    registry = EnhancedAgentRegistry(LoadBalancingStrategy.LEAST_LOADED)
    await registry.initialize()
    
    print('✅ 增强版注册表创建成功')
    print(f'   默认策略: {registry._default_strategy.name}')
    
    # 测试非阻塞池
    pool = NonBlockingExecutionPool(max_concurrent=5)
    await pool.initialize()
    ok = await pool.acquire_slot()
    print(f'✅ 非阻塞池: 获取槽位={ok}')
    await pool.release_slot()
    
    print('\\n✅ v3.2 Gnet模式应用成功!')

asyncio.run(test())
"
```

### 9. 配置建议

**小规模部署** (1-3 Agent每角色):
```python
LoadBalancingStrategy.ROUND_ROBIN  # 简单均匀
```

**大规模部署** (5+ Agent每角色):
```python
LoadBalancingStrategy.LEAST_LOADED  # 动态负载均衡
```

**异构Agent** (性能差异大):
```python
LoadBalancingStrategy.WEIGHTED_RESPONSE  # 考虑历史性能
```

**缓存优化**:
```python
LoadBalancingStrategy.HASH_BASED  # 相同任务路由到同一Agent
```

### 10. 迁移步骤

1. **备份**:
```bash
cp core/agent_system/agent_registry.py core/agent_system/agent_registry_v30_backup.py
```

2. **更新导入**:
```python
# 修改前
from core.agent_system.agent_registry import AgentRegistry

# 修改后
from core.agent_system.enhanced_registry import EnhancedAgentRegistry as AgentRegistry
```

3. **使用负载均衡选择**:
```python
# 修改前
agent = registry.get(AgentRole.CODER)

# 修改后 (推荐)
agent = registry.select(AgentRole.CODER)
```

### 11. 验证清单

- [ ] 注册表初始化成功
- [ ] Agent注册正常
- [ ] 负载均衡选择工作
- [ ] 非阻塞池获取/释放正常
- [ ] 指标上报正常
- [ ] 向后兼容测试通过

---
*升级文档 - 2026-03-17*  
*Gnet模式来源: https://github.com/panjf2000/gnet*
