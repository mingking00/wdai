# wdai v3.4.5 - AttnRes 思想集成方案

## 背景

基于 Kimi 团队的《Attention Residuals》论文，将核心思想应用到 MultiAgent 系统：
- 不要机械地堆叠组件，要让组件学会**选择性通信**
- 用 **attention 机制** 替代固定的线性传递
- 从"走不通就拐"升级为"选择性关注"

---

## 核心改进

### 1. AttentionBasedOrchestrator (注意力协调器)

**文件**: `core/agent_system/attention_orchestrator.py` (13KB)

**核心思想**:
```
传统模式:  A → B → C (C 只能看到 B)
AttnRes:   A → B(attention to A) → C(attention to A,B)
```

**关键特性**:
- **记忆池**: 所有 Agent 输出存储在共享池中
- **注意力权重**: 每个 Agent 计算对前面所有 Agent 的 attention weights
- **分块设计**: Block AttnRes 思想，同一块内密集通信，块间稀疏
- **零初始化**: 查询向量初始为0，初始权重均匀
- **在线学习**: 根据执行质量动态调整查询向量

**使用示例**:
```python
from core.agent_system import create_attention_orchestrator

orchestrator = create_attention_orchestrator()

# 注册 Agents（分块）
orchestrator.register_agent("planner", block_id=0)
orchestrator.register_agent("coder", block_id=1)
orchestrator.register_agent("reviewer", block_id=1)

# 执行（带注意力聚合）
result = await orchestrator.execute_with_attention(
    task={'description': '实现功能'},
    agent_sequence=["planner", "coder", "reviewer"]
)
```

**演示效果**:
```
Step 1: planner (无历史)
Step 2: analyzer → attention to [planner: 1.0]
Step 3: coder → attention to [planner: 0.5, analyzer: 0.5]
Step 4: reviewer → attention to [planner: 0.33, analyzer: 0.33, coder: 0.33]
```

---

### 2. DynamicVerificationLayer (动态验证层)

**文件**: `core/agent_system/dynamic_verification.py` (16KB)

**核心思想**:
```
传统验证: 所有检查点固定权重（0.2+0.2+0.2...）
AttnRes:  检查点权重 = softmax(base + history + task + context)
```

**关键特性**:
- **动态权重**: 根据历史违规数据调整检查点重要性
- **任务自适应**: 不同任务类型关注不同风险（图片任务更关注外部数据验证）
- **上下文感知**: 根据当前上下文调整（如有图片但未验证，提高外部数据检查权重）
- **零初始化**: 初始均匀权重，逐渐学习
- **反馈学习**: 违规后自动提高对应检查点权重

**使用示例**:
```python
from core.agent_system import create_dynamic_verification_layer

verifier = create_dynamic_verification_layer()

# 验证（动态权重）
result = verifier.verify(
    response="根据图片分析...",
    context={'has_image': True, 'image_verified': False},
    task_type='image_analysis'  # 图片任务会自动提高外部数据验证权重
)

# 查看动态权重
stats = verifier.get_weight_statistics()
# external_data_verification: 0.389 (因为是图片任务且未验证)
# fabrication_detection: 0.193
# ...
```

**演示效果**:
```
图片分析任务:
  external_data_verification: 0.389 (高权重！)
  fabrication_detection: 0.193
  uncertainty_explicit: 0.143
  
代码生成任务:
  tool_usage: 0.339 (代码任务更关注工具使用)
  external_data_verification: 0.169
  fabrication_detection: 0.169
```

---

### 3. 分块通信机制 (Block AttnRes)

**设计**:
```python
# 块0: 输入处理
orchestrator.register_agent("input_parser", block_id=0)
orchestrator.register_agent("intent_classifier", block_id=0)

# 块1: 核心处理
orchestrator.register_agent("reasoning_engine", block_id=1)
orchestrator.register_agent("knowledge_retriever", block_id=1)

# 块2: 输出生成
orchestrator.register_agent("response_generator", block_id=2)
```

**通信规则**:
- **块内**: 全连接，密集通信（权重不降低）
- **块间**: 稀疏连接，权重降低 70%（模拟 Block AttnRes）

**优势**:
- 降低复杂度（从 O(L²d) 降到 O(Nd)，N=块数）
- 保留大部分收益
- 训练开销 <4%，推理开销 <2%

---

### 4. 零初始化策略

**AttnRes 论文技巧**:
> 伪查询向量初始化为0 → 初始注意力权重均匀 → 等于标准残差连接

**应用**:
```python
# AttentionBasedOrchestrator
def register_agent(self, agent_id, block_id):
    # 零初始化
    query_vector = np.zeros(query_dim)
    
    # 初始时所有输入权重相等
    # 随着训练逐渐学习选择性关注
```

```python
# DynamicVerificationLayer
def _initialize_checkpoints(self):
    # 所有检查点初始权重相同
    initial_weight = 1.0 / len(CheckpointType)
    
    for checkpoint in self.checkpoints:
        checkpoint.current_weight = initial_weight
```

**优势**:
- 避免早期训练不稳定
- 平滑过渡到学习到的权重

---

## 与原有系统的集成

### 集成架构

```
wdai_v3/
├── core/agent_system/
│   ├── agent_engine_v3.py          # v3.4.4 - 基础执行引擎
│   ├── attention_orchestrator.py   # v3.4.5 - 注意力协调 (NEW)
│   ├── dynamic_verification.py     # v3.4.5 - 动态验证 (NEW)
│   └── __init__.py                 # 已更新导出
│
├── examples/
│   └── demo_attnres_integration.py # 完整演示
│
└── MIGRATION_v345.md               # 本文档
```

### 使用模式

**模式1: 纯注意力协调**
```python
from core.agent_system import create_attention_orchestrator

orchestrator = create_attention_orchestrator()
# 注册 Agents...
result = await orchestrator.execute_with_attention(task, sequence)
```

**模式2: 纯动态验证**
```python
from core.agent_system import create_dynamic_verification_layer

verifier = create_dynamic_verification_layer()
result = verifier.verify(response, context, task_type)
```

**模式3: 完整集成**
```python
# 组合使用
attention_result = await orchestrator.execute_with_attention(task, sequence)
verification_result = verifier.verify(
    str(attention_result), 
    context,
    task_type
)
```

---

## 演示验证

```bash
$ python3 examples/demo_attnres_integration.py

演示1: Attention-Based Orchestrator
  - 显示每个 Agent 的注意力权重分布
  - Step 2: [planner: 1.0]
  - Step 3: [planner: 0.5, analyzer: 0.5]
  - Step 4: [planner: 0.33, analyzer: 0.33, coder: 0.33]

演示2: Dynamic Verification Layer
  - 不同任务类型的权重自适应
  - 图片任务: external_data (0.389) 高权重
  - 代码任务: tool_usage (0.339) 高权重

演示3: 完整集成工作流
  - Attention执行 + Dynamic验证
  - 完全安全: True
  - 不确定性链: 4 项

演示4: Block Communication
  - 3个块: 输入/核心/输出
  - 块内密集，块间稀疏

演示5: 权重学习过程
  - 零初始化: 所有权重 0.167
  - 多次违规后: external_data 权重提高
```

---

## 关键改进对比

| 维度 | 之前 (v3.4.4) | 之后 (v3.4.5) | 提升 |
|:---|:---|:---|:---:|
| **Agent通信** | 线性链式 A→B→C | 注意力聚合 A→B(attn)→C(attn) | 信息更充分 |
| **验证权重** | 固定 (0.2+0.2...) | 动态 softmax(base+history+task) | 自适应 |
| **不确定性** | 简单平均 | 注意力加权聚合 | 更准确 |
| **复杂度** | O(n) 链长 | O(Nd) 块数，可并行 | 更高效 |
| **学习能力** | 无 | 在线学习查询向量 | 可进化 |

---

## 实现细节

### 注意力计算
```python
def _compute_attention_weights(self, current_step, agent_id):
    # 1. 获取查询向量
    query = self.agent_states[agent_id].query_vector
    
    # 2. 获取所有前驱的键向量
    keys = [self.agent_states[mem['agent_id']].key_vector 
            for mem in self.output_memory]
    
    # 3. 计算 scores: Q · K^T
    scores = np.dot(keys, query)
    
    # 4. Block mask: 不同块降低权重
    scores = self._apply_block_mask(agent_id, scores)
    
    # 5. Softmax
    weights = softmax(scores / temperature)
    
    return weights
```

### 动态权重计算
```python
def _compute_dynamic_weights(self, task_type, context):
    for checkpoint in self.checkpoints:
        # 基础分数
        base_score = checkpoint.base_weight
        
        # 历史违规调整
        history = self.violation_history[checkpoint.type]
        history_adj = (history.recent_frequency * 0.1 + 
                      history.avg_severity * 0.2)
        
        # 任务类型调整
        task_adj = self._get_task_adjustment(task_type, checkpoint.type)
        
        # 上下文调整
        context_adj = self._get_context_adjustment(context, checkpoint.type)
        
        # Softmax
        total_score = base_score + history_adj + task_adj + context_adj
        checkpoint.current_weight = softmax(total_score)
```

---

## 下一步改进方向

1. **递归注意力**: Agent 之间可以递归地应用注意力（类似 Transformer 的多头注意力）
2. **注意力可视化**: 提供注意力热力图，帮助理解 Agent 之间的信息流动
3. **元学习**: 学习如何学习注意力权重（更高层次的优化）
4. **与推理链结合**: 将注意力权重记录到结构化推理链中，提高可解释性

---

## 核心洞察

> **"不要让 Agent 机械地堆叠，要让 Agent 学会选择性通信"**

这是 AttnRes 论文给我最大的启发。从：
- 线性试错（A→B→C，C只能看到B）

到：
- 注意力聚合（A→B(attention)→C(attention)，C可以看到A和B，并选择性关注）

不只是技术改进，更是思维方式的升级。

---

*版本: wdai v3.4.5*  
*完成时间: 2026-03-18*  
*灵感来源: Kimi Team "Attention Residuals"*
