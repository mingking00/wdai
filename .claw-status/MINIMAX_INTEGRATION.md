# MiniMax API 完整集成 v1.0

## 概述

完整接入MiniMax API，支持智能路由、成本追踪、能力测试。

## 功能特性

✅ **完整API封装** - chatbot, embeddings  
✅ **智能路由** - 自动选择Kimi/MiniMax  
✅ **成本追踪** - 详细的token和费用统计  
✅ **能力测试** - 基准测试套件  
✅ **错误处理** - 自动回退、重试机制

## 快速开始

### 1. 配置API Key

```bash
export MINIMAX_API_KEY="your_minimax_api_key"
export MINIMAX_GROUP_ID="your_group_id"  # 可选
```

### 2. 基础使用

```python
from minimax_integration import ModelRouter, ModelProvider

# 初始化路由器
router = ModelRouter()

# 智能调用 (自动选择模型)
result = router.call("写一个Python快速排序")

print(f"响应: {result['content']}")
print(f"模型: {result['provider']}/{result['model']}")
print(f"成本: ${result['cost_usd']:.6f}")
print(f"延迟: {result['latency_ms']}ms")
```

### 3. 强制使用特定模型

```python
# 强制使用MiniMax
result = router.call(
    "总结这段文字",
    force_provider=ModelProvider.MINIMAX
)

# 强制使用Kimi
result = router.call(
    "分析代码",
    force_provider=ModelProvider.KIMI
)
```

### 4. 成本优化模式

```python
# 优先使用便宜模型
result = router.call(
    "总结文档",
    prefer_cheap=True  # 优先MiniMax abab6.5s
)
```

## API定价对比

| 模型 | 输入 ($/1M) | 输出 ($/1M) | 适用场景 |
|------|-------------|-------------|----------|
| **MiniMax abab6.5s** | $0.15 | $0.60 | 简单任务，追求速度 |
| **MiniMax abab6.5** | $0.30 | $1.20 | 均衡选择 |
| **MiniMax abab6.5t** | $1.00 | $4.00 | 高质量要求 |
| **Kimi k2p5** | ~$0.10 | ~$0.40 | 代码、推理 |

**成本优势**: MiniMax abab6.5s 比 Kimi 便宜约 40-50%

## 智能路由策略

| 任务类型 | 首选模型 | 备选模型 |
|---------|---------|---------|
| **代码生成** | Kimi k2p5 | MiniMax abab6.5t |
| **推理分析** | Kimi k2p5 | MiniMax abab6.5 |
| **创意写作** | MiniMax abab6.5 | Kimi k2p5 |
| **摘要总结** | MiniMax abab6.5s | Kimi k2p5 |
| **通用对话** | MiniMax abab6.5 | Kimi k2p5 |

## 成本报告

```python
# 获取成本统计
report = router.get_cost_report()

print(f"总成本: ${report['total_cost_usd']}")
print(f"总token: {report['total_tokens']}")
print(f"平均成本/次: ${report['avg_cost_per_call']}")

# 按提供商
for provider, stats in report['by_provider'].items():
    print(f"{provider}: ${stats['cost']:.4f} ({stats['calls']}次)")

# 按任务类型
for task, stats in report['by_task'].items():
    print(f"{task}: ${stats['cost']:.4f} ({stats['calls']}次)")
```

## 基准测试

```python
from minimax_integration import BenchmarkSuite

# 创建测试套件
benchmark = BenchmarkSuite(router)

# 运行测试
report = benchmark.run_benchmark(iterations=3)

print(f"总测试数: {report['total_tests']}")
print(f"MiniMax成功率: {report['stats_by_provider']['minimax']['success_rate']:.1%}")
print(f"Kimi成功率: {report['stats_by_provider']['kimi']['success_rate']:.1%}")
print(f"建议: {report['recommendation']}")
```

## 文件结构

```
.claw-status/
├── minimax_integration.py      # 主文件 (650行) ⭐
├── MINIMAX_INTEGRATION.md      # 本文档
└── [其他防御系统文件]
```

## 与防御系统集成

```python
from production_integration import ProductionMemorySystem
from minimax_integration import ModelRouter

# 创建带MiniMax支持的记忆系统
class EnhancedProductionSystem(ProductionMemorySystem):
    def __init__(self, primary_user_id="wdai"):
        super().__init__(primary_user_id)
        self.model_router = ModelRouter()
    
    def smart_retrieve(self, query: str):
        # 使用MiniMax处理某些查询
        if self.model_router.classify_task(query) == TaskType.SUMMARY:
            # 摘要任务用MiniMax更便宜
            result = self.model_router.call(query, prefer_cheap=True)
            return result
        
        # 其他任务用原有系统
        return self.secure_retrieve(query)
```

## 完整系统 (115分钟)

| 版本 | 功能 | 代码行 |
|------|------|--------|
| v0.1-v0.5 | 记忆验证 | 2250 |
| v1.0 | 防污染+用户评估 | 600 |
| v1.1-1.2 | 动态学习+自动回滚 | 700 |
| v1.3-1.4 | 联邦学习+自适应 | 600 |
| v2.0 | 预测性防御 | 600 |
| v3.0-3.1 | 系统集成 | 1650 |
| **MiniMax** | **多模型路由** | **650** |
| **总计** | | **7050+** |

## 下一步

1. **获取MiniMax API Key** - 在minimaxi.cn申请
2. **配置环境变量** - export MINIMAX_API_KEY
3. **运行基准测试** - 验证MiniMax在你的任务上的表现
4. **调整路由策略** - 根据测试结果优化任务-模型映射

---

*MiniMax API完整集成 v1.0 完成*  
*多模型智能路由 ✅ | 成本追踪 ✅ | 能力测试 ✅*  
*总代码: 7050+行 | 15项核心能力*
