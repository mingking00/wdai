# wdai v3.0 Phase 3 - Agent专业化系统设计文档

**阶段**: Phase 3  
**目标**: 实现Agent专业化系统 (Orchestrator-Subagent架构)  
**参考**: Claude Code WAT框架 + Fresh Eyes原则  
**状态**: 🚧 进行中

---

## 📋 目标

实现Claude Code风格的Agent专业化系统：
1. **BaseAgent抽象** - 统一的Agent接口
2. **Orchestrator Agent** - 任务分解与协调
3. **专业Subagents** - Coder/Reviewer/Debugger/Architect
4. **Agent调度器** - 任务分配与结果收集
5. **Fresh Eyes上下文管理** - 窄上下文传递
6. **TODO-based规划** - 可追踪的执行计划

---

## 🏗️ 架构设计

### 核心架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 3: Agent System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    Orchestrator Agent                    │  │
│   │  (唯一入口，负责任务分解、规划、调度、结果整合)            │  │
│   │                                                          │  │
│   │  - 接收用户请求                                          │  │
│   │  - 分解为Subtasks                                        │  │
│   │  - 生成TODO计划                                          │  │
│   │  - 调度Subagents                                         │  │
│   │  - 整合结果                                              │  │
│   └───────────────────────────┬─────────────────────────────┘  │
│                               │                                 │
│           ┌───────────────────┼───────────────────┐             │
│           ↓                   ↓                   ↓             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │  CoderAgent │     │ReviewerAgent│     │DebuggerAgent│      │
│   │  (代码实现)  │     │  (代码审查)  │     │  (调试定位)  │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│           ↑                   ↑                   ↑             │
│           │                   │                   │             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐      │
│   │ArchitectAgent│     │  TestAgent  │     │  DocAgent   │      │
│   │  (架构设计)  │     │  (测试验证)  │     │  (文档生成)  │      │
│   └─────────────┘     └─────────────┘     └─────────────┘      │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                  Fresh Eyes Context                      │  │
│   │                                                          │  │
│   │  Subagent只接收:                                         │  │
│   │  - 任务描述 (task_description)                           │  │
│   │  - 相关文件 (relevant_files)                             │  │
│   │  - 必要上下文 (minimal_context)                          │  │
│   │  - 不包含: 完整工作流、其他任务信息                       │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                   TODO-based Planning                    │  │
│   │                                                          │  │
│   │  □ 1. 分析需求                                           │  │
│   │  □ 2. 设计架构  ← 当前                                   │  │
│   │  □ 3. 实现代码                                           │  │
│   │  □ 4. 审查代码                                           │  │
│   │  □ 5. 运行测试                                           │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 数据模型

### Agent基类

```python
@dataclass
class AgentConfig:
    """Agent配置"""
    role: str                      # Agent角色
    expertise: List[str]           # 专长领域
    system_prompt: str             # 系统提示
    max_context_tokens: int = 4000 # 最大上下文
    timeout: int = 300             # 超时时间

class BaseAgent(ABC):
    """Agent抽象基类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.message_bus = get_message_bus()
    
    @abstractmethod
    async def execute(self, task: SubTask, context: NarrowContext) -> AgentResult:
        """执行子任务"""
        pass
    
    @abstractmethod
    def can_handle(self, task_type: str) -> bool:
        """检查是否能处理该任务类型"""
        pass
```

### 任务模型

```python
@dataclass
class Task:
    """用户任务"""
    id: str
    description: str               # 任务描述
    goal: str                      # 目标
    constraints: List[str]         # 约束条件
    context: Dict[str, Any]        # 完整上下文

@dataclass
class SubTask:
    """子任务"""
    id: str
    parent_id: str                 # 父任务ID
    type: str                      # 任务类型
    description: str               # 描述
    assigned_to: Optional[str]     # 分配给哪个Agent
    dependencies: List[str]        # 依赖的子任务ID
    status: TaskStatus
    result: Optional[AgentResult]

@dataclass
class NarrowContext:
    """窄上下文 (Fresh Eyes)"""
    subtask: SubTask               # 当前子任务
    relevant_files: List[str]      # 相关文件
    parent_context: Dict[str, Any] # 父任务关键信息
    previous_results: Dict[str, Any] # 依赖任务的结果
    # 不包含: 完整工作流、其他无关任务
```

### TODO规划

```python
@dataclass
class TodoItem:
    """TODO项"""
    id: str
    description: str
    status: TodoStatus             # pending/running/completed/failed
    assigned_agent: Optional[str]  # 分配给哪个Agent
    dependencies: List[str]        # 依赖的TODO ID
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class TodoPlan:
    """TODO计划"""
    task_id: str
    todos: List[TodoItem]
    current_index: int
```

---

## 🔄 执行流程

```
1. 用户提交任务
   ↓
2. Orchestrator接收任务
   ↓
3. 任务分解 → 生成Subtasks
   ↓
4. 生成TODO计划
   ↓
5. 循环执行:
   ├─ 获取当前TODO
   ├─ 选择合适Agent
   ├─ 裁剪上下文 (Fresh Eyes)
   ├─ 发送给Subagent执行
   ├─ 收集结果
   ├─ 更新TODO状态
   └─ 检查是否完成
   ↓
6. 整合结果
   ↓
7. 返回给用户
```

---

## 🎯 实现计划

### Task 1: BaseAgent抽象 (30分钟)
- [ ] AgentConfig数据类
- [ ] BaseAgent抽象基类
- [ ] AgentRegistry注册表
- [ ] 消息总线集成

### Task 2: Orchestrator Agent (45分钟)
- [ ] Orchestrator实现
- [ ] 任务分解逻辑
- [ ] TODO计划生成
- [ ] Agent调度逻辑

### Task 3: 专业Subagents (60分钟)
- [ ] CoderAgent - 代码实现
- [ ] ReviewerAgent - 代码审查
- [ ] DebuggerAgent - 调试定位
- [ ] ArchitectAgent - 架构设计

### Task 4: Fresh Eyes上下文管理 (30分钟)
- [ ] NarrowContext裁剪
- [ ] 文件相关性分析
- [ ] 上下文压缩

### Task 5: TODO-based规划 (30分钟)
- [ ] TodoPlan管理
- [ ] 动态规划调整
- [ ] 执行追踪

### Task 6: 测试 (45分钟)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 端到端测试

**总预计时间**: ~4小时

---

## 📁 文件结构

```
core/
├── message_bus/           # Phase 1
├── workflow/              # Phase 2
└── agent_system/          # Phase 3 (新增)
    ├── __init__.py
    ├── models.py          # 数据模型
    ├── base.py            # BaseAgent
    ├── orchestrator.py    # Orchestrator Agent
    ├── subagents/         # 专业Subagents
    │   ├── __init__.py
    │   ├── coder.py
    │   ├── reviewer.py
    │   ├── debugger.py
    │   └── architect.py
    ├── context.py         # Fresh Eyes上下文
    ├── todo.py            # TODO规划
    └── registry.py        # Agent注册表
```

---

## 🔌 接口设计

### 基础用法

```python
# 创建Orchestrator
orchestrator = OrchestratorAgent()

# 提交任务
task = Task(
    description="实现一个Web服务",
    goal="构建RESTful API",
    constraints=["使用Python", "Flask框架"]
)

# 执行任务
result = await orchestrator.execute(task)

# 获取执行计划
plan = orchestrator.get_plan(task.id)
for todo in plan.todos:
    print(f"{'✅' if todo.status == 'completed' else '⏳'} {todo.description}")
```

### 使用专业Agent

```python
# 直接使用专业Agent
coder = CoderAgent()
result = await coder.execute(
    subtask=SubTask(
        type="implement",
        description="实现用户认证模块"
    ),
    context=NarrowContext(
        relevant_files=["auth.py", "models.py"]
    )
)
```

---

## 🎨 设计原则

1. **单一职责**: 每个Agent只做一件事
2. **Fresh Eyes**: Subagent只接收必要上下文
3. **显式规划**: TODO列表清晰可见
4. **事件驱动**: 通过消息总线通信
5. **可扩展**: 易于添加新Agent类型

---

*Design Doc - wdai v3.0 Phase 3*
