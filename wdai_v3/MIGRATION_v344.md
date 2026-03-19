# wdai v3.4.4 Agent执行引擎重构

## 背景

用户要求"修改底层机制"，基于之前发现的系统性问题：
1. 概念Agent vs 真并行Agent的混淆
2. 缺乏强制验证机制
3. 编造内容无自动检测
4. 不确定性未显化

## 根本性重构

### 核心设计原则

1. **验证即代码** - 验证不是可选项，是强制环节
2. **不确定性传播** - 不确定性必须显化并传递
3. **明确执行模式** - 概念Agent和真并行Agent明确区分
4. **阻断机制** - 危险操作自动阻断

---

## 新架构

```
Agent执行引擎 v3.0
├── VerificationLayer（验证层）- 强制检查点
│   ├── 置信度检查
│   ├── 编造内容检测
│   ├── 不确定性显化检查
│   └── 外部数据验证
│
├── AgentExecutor（基类）- 所有Agent必须继承
│   ├── ConceptualAgent（概念Agent - 串行）
│   └── ParallelAgent（真并行Agent - 独立session）
│
└── MultiAgentOrchestrator（协调器）
    ├── execute_single（单Agent执行）
    ├── execute_parallel（多Agent并行）
    ├── execute_with_verification_chain（验证链）
    └── integrate_outputs（结果整合）
```

---

## 核心改进

### 1. 强制验证（不再能跳过）

**之前**（v1.0/v2.0）：
```python
# 验证是可选项
if use_verification:
    verify(output)  # 可能被跳过
```

**之后**（v3.0）：
```python
# 验证是强制环节
verified_output = verification_layer.verify(output, context)
# 如果验证失败且阻断，必须修正
```

### 2. AgentOutput 强制结构化

```python
@dataclass
class AgentOutput:
    content: Any               # 结果
    confidence: float         # 强制！0-1
    reasoning: str           # 强制！推理过程
    uncertainties: List[Uncertainty]  # 强制！不确定性列表
    verification: VerificationResult  # 验证结果
```

**关键**：如果置信度 < 1.0，必须有不确定性记录！

### 3. 不确定性显化

```python
@dataclass
class Uncertainty:
    source: str        # 来源
    description: str   # 描述
    confidence: float  # 置信度
    impact: str       # 影响
```

**传播机制**：
- 每个Agent必须显化自己的不确定性
- 整合时传播不确定性
- 最终用户看到的是完整的不确定性链

### 4. 概念Agent vs 真并行Agent

```python
# 概念Agent - 串行执行（我扮演）
conceptual = ConceptualAgent("analyzer")
# 特点：快速，低延迟
# 局限：视角可能不独立

# 真并行Agent - 独立session
parallel = ParallelAgent("analyzer", agent_id="parallel-1")
# 特点：真正独立视角
# 代价：延迟稍高，资源消耗大
```

**选择策略**：
```python
if complexity < 0.5:
    use ConceptualAgent  # 简单任务
else:
    use ParallelAgent    # 需要独立视角
```

---

## 验证检查点

### 默认检查点

| 检查点 | 功能 | 阻断性 |
|:---|:---|:---:|
| confidence_check | 置信度合理性 | 否 |
| fabrication_detection | 编造内容检测 | 是 |
| uncertainty_explicit | 不确定性显化 | 是 |
| external_data_verification | 外部数据验证 | 是 |

### 编造内容检测

```python
def _check_fabrication(output):
    # 检测模式：过于具体的细节但没有来源
    if '"' in output and '根据' not in output:
        return FAILED("具体细节缺乏来源")
    if '具体' in output and '来源' not in output:
        return FAILED("缺乏来源引用")
```

### 外部数据验证

```python
def _check_external_data(output):
    if '图片' in output and not metadata.get('image_verified'):
        return FAILED("引用了图片但未验证（未读取）")
```

**这正是我之前犯的错误！**

---

## 验证链模式

```python
# 生成 → 验证 → 审查 → 整合
result = await orchestrator.execute_with_verification_chain(
    task=task,
    executor_agent='coder',           # 生成
    verifier_agents=['reviewer-1', 'reviewer-2']  # 并行审查
)

# 流程：
# 1. Coder 生成输出
# 2. 自动通过VerificationLayer验证
# 3. Reviewer-1 和 Reviewer-2 并行审查（独立视角）
# 4. 整合审查结果
# 5. 如果发现问题，修正或标记
```

---

## 与之前版本的对比

| 特性 | v1.0/v2.0 | v3.0 |
|:---|:---|:---|
| 验证 | 可选项 | 强制环节 |
| 不确定性 | 可隐藏 | 必须显化 |
| Agent类型 | 混淆 | 明确区分 |
| 编造检测 | 无 | 自动检测并阻断 |
| 执行模式 | 伪并行 | 真并行支持 |
| 失败处理 | 继续执行 | 阻断或修正 |

---

## 使用示例

### 基本使用

```python
from core.agent_system import (
    create_conceptual_agent,
    create_orchestrator,
    AgentOutput
)

# 创建Agent
agent = create_conceptual_agent("my-agent")

# 执行任务（自动验证）
result = await agent.execute({
    'description': '分析方案',
    'image_verified': True  # 必须标记
})

# 检查结果
if result.verification.status == VerificationStatus.FAILED:
    print(f"问题: {result.verification.issues}")
else:
    print(f"结果: {result.content}")
    print(f"置信度: {result.confidence}")
    print(f"不确定性: {result.uncertainties}")
```

### 验证链

```python
orchestrator = create_orchestrator()
orchestrator.register_agent(create_conceptual_agent("coder"))
orchestrator.register_agent(create_conceptual_agent("reviewer"))

result = await orchestrator.execute_with_verification_chain(
    task={'description': '写代码'},
    executor_agent='coder',
    verifier_agents=['reviewer']
)
```

---

## 演示结果

```bash
$ python3 examples/demo_agent_engine_v3.py

演示1: 强制验证机制
  任务: 分析图片（未验证）
  验证状态: FAILED
  问题: ['引用了图片但未验证（未读取）']
  ❌ 阻断！

演示2: 不确定性显化
  Agent-1 不确定性: 概念Agent可能存在偏见
  Agent-2 不确定性: 概念Agent可能存在偏见
  整合后不确定性: 包含2个Agent的不确定性 + 整合过程不确定性

演示3: 验证链
  Coder生成 → Reviewer-1审查 → Reviewer-2审查 → 整合
  最终结果: 状态 PASSED，置信度 0.7

演示4: 概念 vs 并行
  概念Agent: 快速，串行，可能共享偏见
  并行Agent: 延迟稍高，真正独立视角，有独立Session ID

演示5: 失败检测
  危险任务: 根据文件名分析图片
  检测: 引用了图片但未验证
  行为: 阻断，要求修正
```

---

## 系统集成

### 与认知安全系统结合

```python
from core.agent_system import (
    CognitiveSafetySystem,
    VerificationLayer
)

# 认知安全系统检测内容层面的问题
safety = CognitiveSafetySystem()

# 验证层检测执行层面的问题
verification = VerificationLayer()

# 双层防护
```

### 与创新引擎结合

```python
from core.agent_system import (
    InnovationEngineV2,
    MultiAgentOrchestrator
)

# 创新引擎生成多种思路
innovation = InnovationEngineV2()
approaches = await innovation._generate_approaches_parallel(problem)

# 验证层确保每个思路都通过验证
for approach in approaches:
    output = AgentOutput(...)
    verified = verification.verify(output, context)
```

### 与结构化思维链结合

```python
from core.agent_system import QuickCoT

# 在验证过程中记录思维链
cot = QuickCoT("验证过程")
cot.section1("原始输出", output.content)
cot.section2("验证结果", str(output.verification.status))
cot.section3("发现的问题", str(output.verification.issues))
```

---

## 改进路线

| 版本 | 核心机制 | 解决的问题 |
|:---:|:---|:---|
| v1.0 | 基础Agent | - |
| v2.0 | 负载均衡 | 资源管理 |
| v3.3 | 推理追踪 | 可观察性 |
| v3.4.1 | 结构化CoT | 推理透明 |
| v3.4.2 | 认知安全 | 编造/偷懒 |
| v3.4.3 | 创新引擎v2 | 线性思维 |
| **v3.4.4** | **Agent引擎重构** | **系统性验证** |

---

## 核心原则

1. **验证不是可选项** - 每个输出必须通过验证层
2. **不确定性必须显化** - 不能隐藏不确定性
3. **阻断优于错误** - 危险操作自动阻断
4. **模式明确区分** - 概念Agent和真并行Agent用途清晰
5. **传播而非掩盖** - 不确定性在系统中传播，不丢失

---

*版本: wdai v3.4.4*  
*完成时间: 2026-03-17*
