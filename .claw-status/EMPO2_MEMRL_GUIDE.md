# EMPO² + MemRL 集成系统

> 将EMPO²的混合学习机制整合到MemRL记忆系统
> 
> 版本: v1.0 | 日期: 2026-03-20

---

## 核心改进

### 原有MemRL系统
```
记忆 = (z, e, Q)
- z: 意图嵌入
- e: 原始经验  
- Q: Q值 (学习效用)
```

### EMPO²增强版
```
记忆 = (z, e, Q, Tips, Rules)
- z: 意图嵌入
- e: 原始经验
- Q: Q值 (学习效用)
- Tips: 自我生成的指导提示
- Rules: 已内化的系统规则
```

---

## 四大核心机制

### 1. Self-Generated Tips (自我生成提示)

**自动从失败中提取教训**:

```python
from empo2_memrl_integration import EMPO2MemoryIntegration, TaskOutcome

empo2 = EMPO2MemoryIntegration()

# 记录失败任务
outcome = TaskOutcome(
    task_id="task_001",
    query="部署应用到服务器",
    actions=["ssh_connect", "docker_build"],
    outcome="failure",
    error_message="Connection timeout",
    duration_sec=30,
    tips_used=[],
    tips_generated=[],
    timestamp=datetime.now().isoformat()
)

# 系统自动生成Tip
empo2.update_from_outcome(outcome)
# 输出: 生成了Tip "⚠️ 超时错误 - 考虑减小任务粒度或增加超时时间"
```

**自动错误模式识别**:
- 超时错误 → "考虑减小任务粒度"
- 权限错误 → "检查文件权限"
- 路径错误 → "使用绝对路径"
- 限流错误 → "添加重试逻辑"
- API密钥错误 → "检查环境变量"

### 2. Hybrid Rollout (双模式检索)

**自适应选择是否使用记忆**:

```python
# 模式1: 纯参数化 (探索新方案)
result = empo2.retrieve_with_mode("新任务", mode="no_memory")
# 返回: 仅内化规则，无外部记忆

# 模式2: 记忆增强 (利用经验)
result = empo2.retrieve_with_mode("类似任务", mode="with_memory")
# 返回: 记忆 + Tips + 内化规则

# 模式3: 自适应 (概率p使用记忆)
result = empo2.retrieve_with_mode("未知任务", mode="auto")
# 以60%概率使用记忆，40%探索
```

### 3. On/Off-Policy Update (混合更新)

**On-policy (直接反馈)**:
```python
# 任务成功 → 提升相关记忆Q值
# 任务失败 → 降低相关记忆Q值
# 使用Tips → 更新Tips有效性
```

**Off-policy (知识蒸馏)**:
```python
# Tips使用次数 > 5 且 有效性 > 0.7
# → 自动内化为系统规则
# → 更新AGENTS.md或SOUL.md
```

### 4. Knowledge Distillation (知识内化)

**高频Tips自动固化**:

```python
# 初始: 外部Tip
Tip: "⚠️ 限流错误 - 添加重试逻辑"
  ↓ 使用5次，有效性0.85
  ↓ 自动内化
Rule: 添加到auto_internalized_rules.md
  ↓ 后续检索
自动包含在参数中，无需外部记忆
```

---

## 实际使用场景

### 场景1: 日常任务执行

```python
def execute_task(query: str):
    empo2 = EMPO2MemoryIntegration()
    
    # 1. 检索相关经验 (双模式)
    context = empo2.retrieve_with_mode(query, mode="auto")
    
    # 2. 构建Prompt
    system_prompt = ""
    
    # 添加内化规则 (始终包含)
    for rule in context['internalized_rules']:
        system_prompt += f"- {rule['content']}\n"
    
    # 添加Tips (如果使用记忆模式)
    if context['mode_used'] == "with_memory":
        for tip in context['tips']:
            system_prompt += f"- {tip.content}\n"
    
    # 3. 执行任务
    actions = []
    try:
        result = perform_task(query, system_prompt)
        outcome = "success"
    except Exception as e:
        result = str(e)
        outcome = "failure"
    
    # 4. 记录结果并更新系统
    task_outcome = TaskOutcome(
        task_id=generate_id(),
        query=query,
        actions=actions,
        outcome=outcome,
        error_message=result if outcome == "failure" else "",
        duration_sec=elapsed_time,
        tips_used=[tip.tip_id for tip in context['tips']],
        tips_generated=[],
        timestamp=datetime.now().isoformat()
    )
    
    empo2.update_from_outcome(task_outcome)
    
    return result
```

### 场景2: 持续优化循环

```python
def continuous_improvement():
    """每日优化循环"""
    empo2 = EMPO2MemoryIntegration()
    
    # 1. 查看今日生成的Tips
    new_tips = [t for t in empo2.tips 
                if t.created_at.startswith(today)]
    print(f"今日生成 {len(new_tips)} 个Tips")
    
    # 2. 查看已内化的规则
    print(f"已内化 {len(empo2.internalized_rules)} 条规则")
    for rule in empo2.internalized_rules[-5:]:
        print(f"  - {rule['content'][:50]}...")
    
    # 3. 生成系统报告
    report = empo2.generate_report()
    print(f"成功率: {report['outcomes']['success'] / report['outcomes']['total']:.1%}")
```

---

## 系统集成点

### 与现有MemRL集成

```python
# 原有MemRL功能保持不变
from memrl_memory import MemRLMemory

base_memory = MemRLMemory()
base_memory.add_experience(query, experience, reward)
base_memory.retrieve(query)
base_memory.update_q_value(memory_id, reward)
```

### EMPO²扩展功能

```python
from empo2_memrl_integration import EMPO2MemoryIntegration

empo2 = EMPO2MemoryIntegration()

# 新增: Tips管理
empo2.generate_tip(task_outcome)  # 从失败生成
empo2._retrieve_tips(query)        # 检索相关Tips

# 新增: 双模式检索
empo2.retrieve_with_mode(query, mode="auto")

# 新增: 知识内化
empo2._internalize_tip(tip)        # 将Tip固化为规则

# 新增: 探索奖励
empo2.get_exploration_bonus(query) # 新任务类型奖励
```

---

## 配置参数

```python
config = {
    "tip_generation_threshold": 3,      # 生成Tip的最小错误次数
    "internalization_threshold": 5,     # 内化到参数的使用次数
    "effectiveness_threshold": 0.7,     # 高有效性阈值
    "exploration_bonus": 0.1,           # 探索奖励系数
    "memory_rollout_prob": 0.6,         # 使用记忆的rollout概率
}
```

---

## 数据存储

```
.claw-status/empo2_integration/
├── tips.json                 # 自我生成的Tips
├── outcomes.json             # 任务结果历史
├── internalized_rules.json   # 已内化的规则
└── auto_internalized_rules.md # 可读的规则文档
```

---

## 与Agent Lightning的关系

**本系统**: EMPO²概念的简化实现，专注于提示工程层面
**Agent Lightning**: 完整的RL训练框架，支持模型权重更新

**差异**:
| 维度 | 本系统 | Agent Lightning |
|------|--------|-----------------|
| 更新对象 | 系统Prompt/规则 | 模型权重 |
| 训练方式 | 启发式规则 | 梯度下降 |
| 适用场景 | 无微调权限的部署Agent | 自有模型训练 |
| 实现复杂度 | 低 | 高 |

**未来**: 如果获得可训练模型，可迁移到Agent Lightning

---

## 下一步改进

### 短期 (本周)
- [ ] 集成到日常任务执行流程
- [ ] 每日生成Tips审查报告
- [ ] 手动审核内化规则

### 中期 (本月)
- [ ] 更智能的Tip生成 (使用LLM总结)
- [ ] 语义相似度检索 (向量数据库)
- [ ] 探索奖励的动态调整

### 长期 (本季度)
- [ ] 多Agent协作的共享记忆
- [ ] 与Agent Lightning的桥接
- [ ] 自动化的A/B测试框架

---

## 快速开始

```bash
# 1. 运行演示
python3 .claw-status/empo2_memrl_integration.py

# 2. 在实际任务中使用
# 修改你的任务执行代码，添加EMPO2集成

# 3. 查看生成的规则
cat .claw-status/empo2_integration/auto_internalized_rules.md
```

---

*EMPO² + MemRL 集成完成*  
*记忆系统从"纯检索"进化到"检索+内化"*  
*下一步: 持续运行，观察内化效果*
