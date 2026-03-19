# wdai v3.0 Phase 2 - SOP工作流引擎设计文档

**阶段**: Phase 2  
**目标**: 实现SOP (Standard Operating Procedure) 工作流引擎  
**参考**: MetaGPT架构  
**状态**: 🚧 进行中

---

## 📋 目标

基于MetaGPT的SOP理念，实现一个灵活的工作流引擎：
1. 定义标准化的工作流程
2. 支持步骤编排和依赖管理
3. 自动执行和错误处理
4. 支持并行和串行步骤
5. 与Phase 1的消息总线集成

---

## 🏗️ 架构设计

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                     Workflow Engine                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Workflow  │  │    Step     │  │   Step Executor     │ │
│  │   工作流定义 │  │   步骤定义   │  │    步骤执行器        │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                    │            │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────────▼──────────┐ │
│  │   Context   │  │  Dependency │  │   Event Publisher   │ │
│  │   上下文    │  │   依赖管理   │  │    事件发布器        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      底层支撑                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │Message Bus  │  │ Persistence │  │   State Machine     │ │
│  │(Phase 1)    │  │   持久化     │  │    状态机           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 数据模型

### Workflow 工作流

```python
@dataclass
class Workflow:
    id: str                          # 工作流唯一ID
    name: str                        # 工作流名称
    description: str                 # 描述
    steps: List[Step]                # 步骤列表
    context: Dict[str, Any]          # 全局上下文
    created_at: datetime             # 创建时间
    metadata: Dict[str, Any]         # 元数据
```

### Step 步骤

```python
@dataclass
class Step:
    id: str                          # 步骤ID
    name: str                        # 步骤名称
    description: str                 # 描述
    action: str                      # 执行动作类型
    config: Dict[str, Any]           # 动作配置
    dependencies: List[str]          # 依赖的步骤ID
    condition: Optional[str]         # 执行条件（可选）
    retry_policy: RetryPolicy        # 重试策略
    timeout: Optional[int]           # 超时时间（秒）
```

### WorkflowInstance 工作流实例

```python
@dataclass
class WorkflowInstance:
    id: str                          # 实例ID
    workflow_id: str                 # 关联工作流ID
    status: WorkflowStatus           # 状态
    context: Dict[str, Any]          # 运行时上下文
    step_states: Dict[str, StepState] # 步骤状态
    started_at: Optional[datetime]   # 开始时间
    completed_at: Optional[datetime] # 完成时间
    error_info: Optional[ErrorInfo]  # 错误信息
```

---

## 🔄 执行流程

```
1. 创建实例
   ↓
2. 解析依赖图 (DAG)
   ↓
3. 找到可执行步骤（依赖已完成）
   ↓
4. 并行/串行执行
   ↓
5. 更新状态，发送事件
   ↓
6. 检查是否完成
   ↓
7. 完成或继续步骤3
```

---

## 🎯 实现计划

### Task 1: 核心数据模型 (30分钟)
- [ ] Workflow, Step, WorkflowInstance 定义
- [ ] 状态枚举 (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
- [ ] 重试策略配置

### Task 2: 依赖解析引擎 (45分钟)
- [ ] DAG构建
- [ ] 循环依赖检测
- [ ] 拓扑排序

### Task 3: 执行引擎 (60分钟)
- [ ] StepExecutor 基类
- [ ] 并行/串行执行策略
- [ ] 超时控制
- [ ] 错误处理和重试

### Task 4: 状态机和持久化 (30分钟)
- [ ] 状态转换
- [ ] 事件发布
- [ ] 检查点保存

### Task 5: 与消息总线集成 (30分钟)
- [ ] 发送工作流事件
- [ ] 接收外部触发
- [ ] 异步执行支持

### Task 6: 测试 (45分钟)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 边界测试

**总预计时间**: ~4小时

---

## 📁 文件结构

```
core/
├── message_bus/           # Phase 1 已完成
└── workflow/
    ├── __init__.py        # Facade
    ├── models.py          # 数据模型
    ├── engine.py          # 执行引擎
    ├── dependency.py      # 依赖解析
    ├── executor.py        # 步骤执行器
    ├── state_machine.py   # 状态机
    └── templates/         # 工作流模板
        ├── __init__.py
        └── common.py      # 常用模板
```

---

## 🔌 接口设计

### 基础用法

```python
# 定义工作流
workflow = Workflow(
    name="软件开发",
    steps=[
        Step(id="design", action="llm", config={"prompt": "设计架构"}),
        Step(id="code", action="llm", config={"prompt": "编写代码"}, 
             dependencies=["design"]),
        Step(id="test", action="shell", config={"command": "pytest"},
             dependencies=["code"])
    ]
)

# 执行
engine = WorkflowEngine()
instance = await engine.start(workflow)
result = await engine.wait(instance.id)
```

### 使用模板

```python
from wdai_v3.workflow.templates import software_dev_template

workflow = software_dev_template.create(
    name="我的项目",
    requirements="构建一个Web服务"
)
```

---

## 🎨 设计原则

1. **简单优先**: 先实现基础串行执行，再添加并行
2. **事件驱动**: 通过消息总线解耦
3. **可扩展**: 易于添加新的Action类型
4. **容错**: 内置重试和错误恢复
5. **可观测**: 详细的事件和状态跟踪

---

*Design Doc - wdai v3.0 Phase 2*
