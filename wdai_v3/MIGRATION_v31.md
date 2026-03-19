# wdai v3.1 升级说明 - Rathole模式应用

## 升级内容

### 1. 新增文件
- `core/agent_system/base_v31.py` - 增强版Base Agent

### 2. 主要改进

| 改进项 | 原实现 | 新实现 (Rathole模式) | 收益 |
|:---|:---|:---|:---|
| **指数退避** | 简单 `min(2^attempt, 10)` | `ExponentialBackoff`类，支持重置、最大时间 | 更灵活，避免雪崩 |
| **并发控制** | 无限制 | `ExecutionPool` + Semaphore | 防止资源耗尽 |
| **错误分类** | 统一重试 | `_is_retryable_error()`区分可重试/致命 | 减少无效重试 |
| **日志追踪** | 简单logger | 结构化日志 + 上下文 | 更好的可观测性 |
| **资源监控** | 基础统计 | Pool metrics + 可用槽位 | 实时资源状态 |

### 3. 关键代码对比

#### 指数退避 (Before -> After)
```python
# Before: 简单退避
delay = min(2 ** attempt, 10)
await asyncio.sleep(delay)

# After: Rathole模式
backoff = ExponentialBackoff(
    initial_interval=1.0,
    max_interval=10.0,
    max_elapsed_time=timeout * 2
)
delay = backoff.next_backoff()  # 自动计算，支持重置
```

#### 并发控制 (新增)
```python
# Rathole Worker Pool模式
self._pool = ExecutionPool(ResourceLimits(
    max_concurrent_executions=5,
    max_queue_size=100
))

# 获取槽位
if not await self._pool.acquire(timeout=30.0):
    return AgentResult(success=False, error_message="系统繁忙")
```

#### 错误分类 (新增)
```python
def _is_retryable_error(self, error: Exception) -> bool:
    retryable = [
        'timeout', 'connection', 'temporarily unavailable',
        'rate limit', 'resource exhausted'
    ]
    # 语法错误、权限错误 → 不重试
    # 网络超时、资源暂不可用 → 重试
```

### 4. 统计增强

```python
# 新增指标
{
    "error_count": 10,              # 错误计数
    "pool_metrics": {
        'active': 3,                # 活跃执行
        'completed': 45,            # 已完成
        'failed': 5                 # 失败
    },
    "available_slots": 2            # 可用槽位
}
```

## 迁移步骤

### 步骤1: 备份原文件
```bash
cp core/agent_system/base.py core/agent_system/base_v30_backup.py
```

### 步骤2: 替换文件
```bash
cp core/agent_system/base_v31.py core/agent_system/base.py
```

### 步骤3: 更新Subagents
所有继承BaseAgent的类需要更新构造函数:

```python
# Before
def __init__(self, config: AgentConfig):
    super().__init__(config)

# After (可选资源限制)
def __init__(self, config: AgentConfig):
    limits = ResourceLimits(
        max_concurrent_executions=3,  # 该Agent最大并发
        max_queue_size=50
    )
    super().__init__(config, limits)
```

### 步骤4: 测试
```bash
cd wdai_v3 && python3 -c "
from core.agent_system.base import BaseAgent, ExponentialBackoff, ExecutionPool
print('✅ 导入成功')

# 测试指数退避
backoff = ExponentialBackoff(initial_interval=1.0, max_interval=10.0)
print(f'退避1: {backoff.next_backoff()}s')
print(f'退避2: {backoff.next_backoff()}s')
backoff.reset()
print(f'重置后: {backoff.next_backoff()}s')
print('✅ 指数退避测试通过')
"
```

## 回滚方案

如需回滚:
```bash
cp core/agent_system/base_v30_backup.py core/agent_system/base.py
```

## 验证清单

- [ ] 所有Subagents能正常初始化
- [ ] 任务执行统计正确
- [ ] 并发控制生效 (同时运行多个任务)
- [ ] 错误重试逻辑正确
- [ ] 日志输出包含结构化上下文

---
*升级文档 - 2026-03-17*
