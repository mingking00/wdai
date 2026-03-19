# Session 11: 自适应学习率

## 目标
实现自适应学习系统，根据任务成功率自动调整学习参数，优化探索与利用的平衡。

## 前置要求
- ✅ s05: 学习闭环 (错误记录、模式识别)
- ✅ s10: 自动会话摘要 (成功率统计)
- ✅ s04: 自动记忆提取 (带权重的记忆系统)

## 预计时间
6-8 小时

---

## 学习目标

完成本 Session 后，你将：

1. **理解自适应学习算法** (ε-greedy, UCB, Thompson Sampling)
2. **掌握探索 vs 利用的权衡**
3. **实现动态参数调优机制**

---

## 核心问题

**当前问题**:
- 所有任务用相同的学习参数
- 高频任务没有更快收敛
- 新任务没有充分探索
- 无法根据历史表现优化策略

**目标**:
- 高频任务快速收敛 (高利用率)
- 新任务充分探索 (高发现率)
- 自动调整参数，无需人工干预

---

## 强化学习框架

```
状态 (State): 当前任务类型 + 历史成功率 + 最近表现
动作 (Action): 选择的学习策略/参数
奖励 (Reward): 任务成功 = +1, 失败 = 0
目标: 最大化长期累积奖励
```

---

## 实现步骤

### Step 1: 任务成功率追踪

**目标**: 建立任务-成功率的映射

**实现**:
```python
# wdai_v3/core/learning/success_tracker.py
class SuccessTracker:
    """追踪每种任务的成功率"""
    
    def __init__(self):
        self.task_stats = {}  # task_type -> TaskStats
    
    def record_attempt(self, task_type: str, success: bool):
        """记录一次任务尝试"""
        if task_type not in self.task_stats:
            self.task_stats[task_type] = TaskStats()
        
        stats = self.task_stats[task_type]
        stats.attempts += 1
        if success:
            stats.successes += 1
        
        # 更新成功率 (指数加权移动平均)
        stats.success_rate = 0.9 * stats.success_rate + 0.1 * int(success)
    
    def get_success_rate(self, task_type: str) -> float:
        """获取某类任务的成功率"""
        stats = self.task_stats.get(task_type)
        if not stats or stats.attempts < 5:
            return 0.5  # 未知任务默认 0.5
        return stats.success_rate
    
    def get_confidence(self, task_type: str) -> float:
        """获取成功率的置信度 (尝试次数越多越可信)"""
        stats = self.task_stats.get(task_type)
        if not stats:
            return 0.0
        return min(1.0, stats.attempts / 20)  # 20次达到满置信度


@dataclass
class TaskStats:
    attempts: int = 0
    successes: int = 0
    success_rate: float = 0.5
    last_attempt: datetime = None
```

**数据来源**:
- 从 s10 的会话摘要中提取任务完成情况
- 从 s05 的学习闭环中读取错误记录
- 实时记录每个任务的执行结果

### Step 2: 自适应参数系统

**目标**: 根据成功率动态调整学习参数

**实现**:
```python
# wdai_v3/core/learning/adaptive_params.py
class AdaptiveLearningParams:
    """自适应学习参数"""
    
    def __init__(self):
        self.base_params = {
            "exploration_rate": 0.3,      # 探索概率
            "learning_rate": 0.1,          # 学习率
            "retry_threshold": 3,          # 最大重试次数
            "timeout_seconds": 60,         # 默认超时
        }
        self.task_params = {}  # 每类任务的专用参数
    
    def get_params(self, task_type: str) -> dict:
        """获取某类任务的优化参数"""
        success_rate = success_tracker.get_success_rate(task_type)
        confidence = success_tracker.get_confidence(task_type)
        
        # 根据成功率调整参数
        if confidence < 0.3:
            # 新任务: 高探索，低学习率
            return {
                "exploration_rate": 0.5,   # 多尝试不同方法
                "learning_rate": 0.05,      # 谨慎更新
                "retry_threshold": 5,       # 多给几次机会
                "timeout_seconds": 120,     # 宽松超时
            }
        elif success_rate > 0.8:
            # 高频成功任务: 低探索，高利用
            return {
                "exploration_rate": 0.1,   # 信任现有策略
                "learning_rate": 0.2,       # 快速微调
                "retry_threshold": 2,       # 快速失败
                "timeout_seconds": 30,      # 严格超时
            }
        elif success_rate < 0.3:
            # 困难任务: 高探索，中等学习率
            return {
                "exploration_rate": 0.4,   # 多尝试
                "learning_rate": 0.15,      # 中等学习
                "retry_threshold": 4,
                "timeout_seconds": 90,
            }
        else:
            # 中等任务: 平衡策略
            return self.base_params
```

**参数说明**:
| 参数 | 高探索场景 | 高利用场景 | 说明 |
|:---|:---:|:---:|:---|
| exploration_rate | 0.5 | 0.1 | 尝试新方法的概率 |
| learning_rate | 0.05 | 0.2 | 更新策略的速度 |
| retry_threshold | 5 | 2 | 失败前重试次数 |
| timeout_seconds | 120 | 30 | 任务超时时间 |

### Step 3: 策略选择器 (Bandit 算法)

**目标**: 智能选择最优策略

**实现** (UCB1 算法):
```python
# wdai_v3/core/learning/strategy_selector.py
class StrategySelector:
    """基于 UCB1 算法的策略选择器"""
    
    def __init__(self):
        self.strategies = {}  # strategy_id -> StrategyStats
    
    def select_strategy(self, task_type: str) -> str:
        """为任务选择最优策略"""
        available = self.get_strategies_for(task_type)
        
        if not available:
            return "default"
        
        # UCB1: 平衡探索和利用
        # score = average_reward + sqrt(2 * ln(total_attempts) / attempts)
        
        total_attempts = sum(s.attempts for s in available.values())
        
        best_strategy = None
        best_score = -1
        
        for strategy_id, stats in available.items():
            if stats.attempts == 0:
                # 未尝试过的策略，给予高探索 bonus
                score = float('inf')
            else:
                avg_reward = stats.total_reward / stats.attempts
                exploration_bonus = math.sqrt(
                    2 * math.log(total_attempts + 1) / stats.attempts
                )
                score = avg_reward + exploration_bonus
            
            if score > best_score:
                best_score = score
                best_strategy = strategy_id
        
        return best_strategy
    
    def update_strategy(self, strategy_id: str, reward: float):
        """更新策略表现"""
        if strategy_id not in self.strategies:
            self.strategies[strategy_id] = StrategyStats()
        
        stats = self.strategies[strategy_id]
        stats.attempts += 1
        stats.total_reward += reward


@dataclass
class StrategyStats:
    attempts: int = 0
    total_reward: float = 0.0
    # success_rate = total_reward / attempts
```

**策略示例**:
```python
strategies = {
    "rule_based": "基于规则的简单处理",
    "llm_basic": "基础 LLM 调用",
    "llm_advanced": "高级 LLM + 多步骤",
    "multi_agent": "多 Agent 协作",
    "cached": "使用缓存结果",
}
```

### Step 4: 学习率自动调整

**目标**: 根据收敛情况调整学习速度

**实现**:
```python
# wdai_v3/core/learning/adaptive_learning_rate.py
class AdaptiveLearningRate:
    """自适应学习率调整"""
    
    def __init__(self):
        self.history = deque(maxlen=10)  # 最近10次表现
        self.current_lr = 0.1
    
    def update(self, reward: float):
        """根据奖励调整学习率"""
        self.history.append(reward)
        
        if len(self.history) < 5:
            return
        
        recent_avg = sum(self.history) / len(self.history)
        older_avg = sum(list(self.history)[:5]) / 5
        
        if recent_avg > older_avg:
            # 表现提升，保持或略增学习率
            self.current_lr = min(0.5, self.current_lr * 1.1)
        elif recent_avg < older_avg:
            # 表现下降，降低学习率
            self.current_lr = max(0.01, self.current_lr * 0.9)
        # else: 表现稳定，保持当前学习率
    
    def get_learning_rate(self) -> float:
        return self.current_lr
```

### Step 5: 集成到 Agent 系统

**目标**: 让 Agent 自动使用自适应参数

**实现**:
```python
# wdai_v3/core/learning/adaptive_agent.py
class AdaptiveAgent:
    """具有自适应学习能力的 Agent"""
    
    def __init__(self):
        self.param_system = AdaptiveLearningParams()
        self.strategy_selector = StrategySelector()
        self.success_tracker = SuccessTracker()
    
    async def execute_task(self, task: Task) -> TaskResult:
        # 1. 获取自适应参数
        params = self.param_system.get_params(task.type)
        
        # 2. 选择策略
        strategy = self.strategy_selector.select_strategy(task.type)
        
        # 3. 执行 (带重试)
        for attempt in range(params["retry_threshold"]):
            result = await self.execute_with_strategy(task, strategy)
            
            if result.success:
                # 记录成功
                self.success_tracker.record_attempt(task.type, success=True)
                self.strategy_selector.update_strategy(strategy, reward=1.0)
                return result
            
            # 失败，考虑切换策略
            if attempt < params["retry_threshold"] - 1:
                # 以 exploration_rate 概率尝试新策略
                if random.random() < params["exploration_rate"]:
                    strategy = self.strategy_selector.select_strategy(task.type)
        
        # 全部失败
        self.success_tracker.record_attempt(task.type, success=False)
        self.strategy_selector.update_strategy(strategy, reward=0.0)
        return result
```

### Step 6: 可视化监控

**目标**: 展示学习进展和参数调整

**实现**:
```python
# wdai_v3/core/learning/learning_dashboard.py
class LearningDashboard:
    def generate_report(self) -> dict:
        return {
            "task_performance": {
                task_type: {
                    "success_rate": stats.success_rate,
                    "attempts": stats.attempts,
                    "trend": self.calculate_trend(stats)
                }
                for task_type, stats in self.tracker.task_stats.items()
            },
            "strategy_performance": {
                strategy_id: {
                    "success_rate": stats.total_reward / stats.attempts,
                    "attempts": stats.attempts
                }
                for strategy_id, stats in self.selector.strategies.items()
            },
            "adaptive_params": {
                task_type: self.params.get_params(task_type)
                for task_type in self.tracker.task_stats.keys()
            }
        }
```

**输出示例**:
```markdown
# 自适应学习报告

## 任务表现
| 任务类型 | 成功率 | 尝试次数 | 趋势 |
|:---|:---:|:---:|:---:|
| security_check | 95% | 120 | ↗️ 上升 |
| code_generation | 78% | 85 | ➡️ 稳定 |
| research | 45% | 30 | ↘️ 下降 |

## 策略表现
| 策略 | 成功率 | 使用次数 |
|:---|:---:|:---:|
| rule_based | 92% | 200 |
| llm_basic | 75% | 150 |
| multi_agent | 88% | 50 |

## 自适应参数 (security_check)
- exploration_rate: 0.1 (高频任务，低探索)
- learning_rate: 0.2 (快速微调)
- retry_threshold: 2 (快速失败)
```

---

## 验收标准

- [ ] 能追踪每类任务的成功率
- [ ] 根据成功率自动调整参数 (探索/利用)
- [ ] 新任务自动高探索，高频任务自动高利用
- [ ] 策略选择使用 Bandit 算法 (UCB1)
- [ ] 学习率根据收敛情况自动调整
- [ ] 提供可视化监控面板

---

## 经验总结

### 学到的原则

1. **探索 vs 利用**: 新任务需要探索，成熟任务需要利用
2. **数据驱动**: 参数调整基于实际成功率，而非预设
3. **动态平衡**: 没有固定最优参数，只有最适合当前状态的参数

### 常见陷阱

- **冷启动**: 新任务缺乏数据，需要合理的默认值
- **延迟反馈**: 任务结果可能需要时间才能确认
- **环境变化**: 成功率可能随时间变化，需要遗忘机制

### 延伸阅读

- [Multi-Armed Bandit: UCB1 Algorithm](https://banditalgs.com/2016/09/18/the-upper-confidence-bound-algorithm/)
- [Adaptive Learning Rate in RL](https://arxiv.org/abs/1605.02026)
- [Thompson Sampling](https://web.stanford.edu/~bvr/pubs/TS_Tutorial.pdf)

---

## 前后对比

### Before
- 所有任务使用相同参数
- 高频任务没有更快收敛
- 新任务没有充分探索
- 手动调整参数

### After
- 每类任务有专用参数
- 高频任务高利用，快速收敛
- 新任务高探索，充分发现
- 参数自动调整，无需人工干预

---

## 下一步

完成本 Session 后：

- **v2.0 发布**: wdai 基础功能完成
- **扩展到新领域**: 根据自适应学习的经验，扩展到其他 Agent 类型

---

## 依赖关系总结

```
s01 (基础 Agent)
  ↓
s02 (记忆系统)
  ↓
s03 (多 Agent 协调)
  ↓
s04 (自动记忆提取)
  ↓
s05 (学习闭环) ───────┐
  ↓                    │
s06 (安全 Agent)       │
  ↓                    │
s07 (时态记忆)         │
  ↓                    │
s08 (注意力机制)       │
  ↓                    │
s09 (L2/L3 安全)       │
  ↓                    │
s10 (自动摘要) ────────┤
  ↓                    │
s11 (自适应学习率) ◄───┘ (依赖 s05 和 s10)
```

---

*Session 设计完成时间: 2026-03-18*
*这是 Phase 4 的最后一个 Session，完成后 wdai v2.0 基础功能就绪*
