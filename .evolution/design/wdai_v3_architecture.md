# wdai v3.0 架构设计文档

**版本**: v3.0-alpha  
**日期**: 2026-03-17  
**设计基于**: OpenHands + MetaGPT 研究  
**状态**: 设计阶段

---

## 📋 设计目标

### 核心目标
1. **解耦通信** - 从直接函数调用转向消息驱动
2. **流程标准化** - SOP驱动的工作流编排
3. **角色专业化** - 明确的Agent职责定义
4. **可观察性** - 完整的事件追踪和检查点

### 设计原则
- **渐进式演进** - 不破坏现有功能，逐步迁移
- **向后兼容** - v2.x功能继续可用
- **可配置** - 新功能可开关，按需启用
- **可测试** - 每个组件独立可测

---

## 🏗️ 目标架构 (v3.0)

```
┌─────────────────────────────────────────────────────────────┐
│                      wdai v3.0 System                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 User Interface                       │   │
│  │  (CLI / API / Web - 保持现有接口)                    │   │
│  └─────────────────────┬───────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │              Message Bus (消息总线)                  │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │          Global Message Pool                 │   │   │
│  │  │  ┌─────────────────────────────────────┐   │   │   │
│  │  │  │  • Task Messages                     │   │   │   │
│  │  │  │  • Event Messages                    │   │   │   │
│  │  │  │  • Notification Messages             │   │   │   │
│  │  │  │  • Audit Messages                    │   │   │   │
│  │  │  └─────────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                    │                              │   │
│  │  ┌─────────────────▼──────────────────┐          │   │
│  │  │      Pub/Sub Router (路由)          │          │   │
│  │  │  • Message Filter                   │          │   │
│  │  │  • Subscriber Registry              │          │   │
│  │  │  • Priority Queue                   │          │   │
│  │  └────────────────────────────────────┘          │   │
│  └─────────────────────┬────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │              SOP Engine (工作流引擎)                 │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │        Workflow Definitions                  │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐            │   │   │
│  │  │  │ CodeDevFlow │ │ ResearchFlow│            │   │   │
│  │  │  │ • Analyze   │ │ • Search    │            │   │   │
│  │  │  │ • Design    │ │ • Synthesis │            │   │   │
│  │  │  │ • Implement │ │ • Report    │            │   │   │
│  │  │  │ • Review    │ └─────────────┘            │   │   │
│  │  │  └─────────────┘                            │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                    │                              │   │
│  │  ┌─────────────────▼──────────────────┐          │   │
│  │  │      Step Orchestrator (编排器)     │          │   │
│  │  │  • Dependency Graph                 │          │   │
│  │  │  • Parallel Execution               │          │   │
│  │  │  • Error Recovery                   │          │   │
│  │  └────────────────────────────────────┘          │   │
│  └─────────────────────┬────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │              Agent Team (Agent团队)                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │   │
│  │  │ Product  │ │Architect │ │  Coder   │            │   │
│  │  │ Manager  │ │          │ │          │            │   │
│  │  │ • PRD    │ │ • Design │ │ • Code   │            │   │
│  │  └──────────┘ └──────────┘ └──────────┘            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │   │
│  │  │ Reviewer │ │Reflector │ │Evolution │            │   │
│  │  │ • Review │ │ • Learn  │ │ • Evolve │            │   │
│  │  └──────────┘ └──────────┘ └──────────┘            │   │
│  └─────────────────────────────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────┐   │
│  │              Infrastructure (基础设施)               │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌───────────┐   │   │
│  │  │   MemRL      │ │  Event Store │ │ Checkpoint│   │   │
│  │  │  (Memory)    │ │  (Event Log) │ │   Store   │   │   │
│  │  └──────────────┘ └──────────────┘ └───────────┘   │   │
│  │  ┌──────────────┐ ┌──────────────┐                  │   │
│  │  │  Sandbox     │ │   Three      │                  │   │
│  │  │ (Optional)   │ │   Zones      │                  │   │
│  │  └──────────────┘ └──────────────┘                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 核心组件设计

### 1. Message Bus (消息总线)

#### 1.1 Global Message Pool (全局消息池)

**职责**: 存储所有消息，支持查询和订阅

```python
class MessagePool:
    """全局消息池 - 持久化存储所有消息"""
    
    def __init__(self, storage_path: str):
        self.storage = PersistentStorage(storage_path)
        self.index = MessageIndex()  # 用于快速查询
    
    def publish(self, message: Message) -> str:
        """发布消息到池中"""
        message_id = self.storage.save(message)
        self.index.add(message)
        return message_id
    
    def query(self, 
              message_type: str = None,
              sender: str = None,
              recipient: str = None,
              time_range: Tuple[datetime, datetime] = None,
              content_filter: Callable = None) -> List[Message]:
        """查询消息"""
        return self.index.query(...)
    
    def get_history(self, task_id: str) -> List[Message]:
        """获取任务完整历史"""
        return self.query(task_id=task_id)
```

**消息类型**:
```python
class MessageType(Enum):
    TASK = "task"           # 任务相关
    EVENT = "event"         # 事件通知
    NOTIFICATION = "notify" # 系统通知
    AUDIT = "audit"         # 审计日志
```

#### 1.2 Pub/Sub Router (发布-订阅路由)

**职责**: 将消息路由给订阅者

```python
class PubSubRouter:
    """发布-订阅路由器"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Agent]] = {}
        self.filters: Dict[str, MessageFilter] = {}
    
    def subscribe(self, 
                  agent: Agent, 
                  message_types: List[str],
                  filter_fn: Callable = None):
        """Agent订阅消息"""
        for msg_type in message_types:
            if msg_type not in self.subscribers:
                self.subscribers[msg_type] = []
            self.subscribers[msg_type].append(agent)
            
        if filter_fn:
            self.filters[agent.id] = filter_fn
    
    def route(self, message: Message):
        """路由消息到订阅者"""
        targets = self.subscribers.get(message.type, [])
        
        for agent in targets:
            # 应用过滤器
            if agent.id in self.filters:
                if not self.filters[agent.id](message):
                    continue
            
            # 异步发送
            asyncio.create_task(agent.handle_message(message))
```

#### 1.3 消息格式

```python
@dataclass
class Message:
    id: str                      # 消息唯一ID
    type: MessageType            # 消息类型
    
    # 路由信息
    sender: str                  # 发送者ID
    recipients: List[str]        # 接收者ID列表
    task_id: str                 # 关联任务ID
    
    # 内容
    content: Dict[str, Any]      # 消息内容
    metadata: Dict[str, Any]     # 元数据
    
    # 时间
    created_at: datetime
    expires_at: Optional[datetime]
    
    # 优先级
    priority: int = 0            # 0=普通, 1=高, 2=紧急
```

---

### 2. SOP Engine (工作流引擎)

#### 2.1 Workflow Definition (工作流定义)

**DSL设计**:
```python
@workflow("code_development")
def code_dev_flow():
    """代码开发工作流"""
    
    # 步骤1: 需求分析
    analyze = step(
        name="analyze_requirement",
        agent="product_manager",
        input_template="{user_request}",
        output_schema=PRD
    )
    
    # 步骤2: 系统设计 (依赖步骤1)
    design = step(
        name="design_architecture",
        agent="architect",
        input_template="{analyze.output}",
        output_schema=DesignDoc,
        depends_on=[analyze]
    )
    
    # 步骤3: 代码实现 (依赖步骤2)
    implement = step(
        name="implement_code",
        agent="coder",
        input_template="{design.output}",
        output_schema=Code,
        depends_on=[design]
    )
    
    # 步骤4: 代码审查 (依赖步骤3)
    review = step(
        name="review_code",
        agent="reviewer",
        input_template="{implement.output}",
        output_schema=ReviewReport,
        depends_on=[implement]
    )
    
    # 错误处理
    on_error(review, retry=2, fallback="human_review")
    
    return review
```

#### 2.2 Step Orchestrator (步骤编排器)

```python
class StepOrchestrator:
    """步骤编排器 - 管理工作流执行"""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.execution_graph: Dict[str, Step] = {}
        self.results: Dict[str, Any] = {}
    
    async def execute(self, workflow: Workflow, context: Dict) -> WorkflowResult:
        """执行工作流"""
        
        # 构建执行图
        graph = self._build_dependency_graph(workflow)
        
        # 并行执行无依赖的步骤
        ready_steps = graph.get_ready_steps()
        
        while ready_steps:
            # 并行执行
            tasks = [
                self._execute_step(step, context) 
                for step in ready_steps
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for step, result in zip(ready_steps, results):
                if isinstance(result, Exception):
                    # 错误处理
                    handled = await self._handle_error(step, result)
                    if not handled:
                        return WorkflowResult(success=False, error=result)
                else:
                    self.results[step.name] = result
            
            # 获取下一步
            ready_steps = graph.get_ready_steps()
        
        return WorkflowResult(success=True, results=self.results)
    
    async def _execute_step(self, step: Step, context: Dict) -> Any:
        """执行单个步骤"""
        # 发送消息给对应Agent
        message = Message(
            type=MessageType.TASK,
            sender="orchestrator",
            recipients=[step.agent],
            content={
                "task": step.name,
                "input": self._render_input(step.input_template, context),
                "output_schema": step.output_schema
            }
        )
        
        # 等待Agent响应
        response = await self.message_bus.send_and_wait(message)
        return response.content["result"]
```

#### 2.3 工作流模板库

```
workflows/
├── code_development.yaml      # 代码开发
├── research.yaml              # 研究任务
├── document_creation.yaml     # 文档创建
├── code_review.yaml           # 代码审查
└── system_evolution.yaml      # 系统进化
```

---

### 3. Agent Team (Agent团队)

#### 3.1 角色定义

```python
@dataclass
class AgentRole:
    """Agent角色定义"""
    
    # 身份
    name: str                    # 角色名称
    description: str             # 角色描述
    
    # 能力
    skills: List[str]            # 技能列表
    constraints: List[str]       # 约束条件
    
    # 行为
    goals: List[str]             # 目标
    responsibilities: List[str]  # 职责
    
    # 输入输出
    input_schema: Type           # 输入数据格式
    output_schema: Type          # 输出数据格式
    
    # 配置
    llm_config: LLMConfig        # LLM配置
    timeout: int                 # 超时时间

# 角色定义示例
PRODUCT_MANAGER = AgentRole(
    name="ProductManager",
    description="分析需求并创建产品文档",
    skills=["requirement_analysis", "user_story", "prd_writing"],
    constraints=["不直接写代码", "专注于需求"],
    goals=["清晰理解用户需求", "创建可执行的需求文档"],
    responsibilities=["需求分析", "PRD编写", "需求澄清"],
    input_schema=UserRequest,
    output_schema=PRD,
    llm_config=LLMConfig(model="kimi-coding/k2p5"),
    timeout=300
)
```

#### 3.2 Agent基类

```python
class BaseAgent(ABC):
    """Agent基类 - 所有Agent的抽象"""
    
    def __init__(self, role: AgentRole, message_bus: MessageBus):
        self.role = role
        self.message_bus = message_bus
        self.id = f"{role.name}_{uuid4().hex[:8]}"
        self.memory = AgentMemory()
        
        # 订阅消息
        self._subscribe_to_messages()
    
    def _subscribe_to_messages(self):
        """订阅感兴趣的消息"""
        self.message_bus.subscribe(
            agent=self,
            message_types=[MessageType.TASK, MessageType.EVENT],
            filter_fn=self._message_filter
        )
    
    def _message_filter(self, message: Message) -> bool:
        """消息过滤器 - 只接收发给此Agent的消息"""
        return self.id in message.recipients or "*" in message.recipients
    
    async def handle_message(self, message: Message):
        """处理接收到的消息"""
        if message.type == MessageType.TASK:
            result = await self.execute_task(message.content)
            
            # 发送响应
            response = Message(
                type=MessageType.EVENT,
                sender=self.id,
                recipients=[message.sender],
                content={"result": result},
                task_id=message.task_id
            )
            await self.message_bus.publish(response)
    
    @abstractmethod
    async def execute_task(self, task: Dict) -> Any:
        """执行任务 - 子类实现"""
        pass
```

#### 3.3 具体Agent实现

```python
class ProductManagerAgent(BaseAgent):
    """产品经理Agent"""
    
    def __init__(self, message_bus: MessageBus):
        super().__init__(PRODUCT_MANAGER, message_bus)
    
    async def execute_task(self, task: Dict) -> PRD:
        """执行需求分析任务"""
        user_request = task["input"]
        
        # 调用LLM进行分析
        prd = await self.llm.generate(
            prompt=self._build_prd_prompt(user_request),
            schema=PRD
        )
        
        # 保存到记忆
        self.memory.add_experience(
            query=user_request,
            experience=str(prd),
            tags=["prd", "requirement"]
        )
        
        return prd

class CoderAgent(BaseAgent):
    """程序员Agent"""
    
    def __init__(self, message_bus: MessageBus):
        super().__init__(CODER, message_bus)
    
    async def execute_task(self, task: Dict) -> Code:
        """执行编码任务"""
        design_doc = task["input"]
        
        # 生成代码
        code = await self.llm.generate(
            prompt=self._build_code_prompt(design_doc),
            schema=Code
        )
        
        # 验证代码
        if not self._validate_code(code):
            raise CodeValidationError("代码验证失败")
        
        return code
```

---

### 4. Infrastructure (基础设施)

#### 4.1 MemRL 集成增强

```python
class MemRLIntegration:
    """MemRL与消息系统集成"""
    
    def __init__(self, message_bus: MessageBus, memrl: MemRLMemory):
        self.message_bus = message_bus
        self.memrl = memrl
        
        # 订阅所有消息，提取记忆
        self.message_bus.subscribe(
            agent=self,
            message_types=[MessageType.EVENT, MessageType.AUDIT],
            filter_fn=lambda m: True  # 接收所有
        )
    
    async def handle_message(self, message: Message):
        """从消息中提取语义记忆"""
        
        # 提取关键信息
        experience = self._extract_experience(message)
        
        if experience:
            # 添加到MemRL
            self.memrl.add_experience(
                query=experience["query"],
                experience=experience["content"],
                reward=experience.get("reward", 0.5),
                tags=experience.get("tags", [])
            )
```

#### 4.2 Event Store (事件存储)

```python
class EventStore:
    """事件存储 - 持久化所有事件"""
    
    def __init__(self, storage_path: str):
        self.storage = AppendOnlyLog(storage_path)
        self.checkpoints: Dict[str, int] = {}  # task_id -> event_index
    
    def append(self, event: Event):
        """追加事件"""
        self.storage.append(event.to_json())
    
    def create_checkpoint(self, task_id: str) -> str:
        """创建检查点"""
        checkpoint_id = f"checkpoint_{task_id}_{uuid4().hex[:8]}"
        current_index = self.storage.size()
        self.checkpoints[checkpoint_id] = current_index
        return checkpoint_id
    
    def replay(self, 
               start_checkpoint: str = None,
               end_checkpoint: str = None) -> List[Event]:
        """重放事件"""
        start_idx = self.checkpoints.get(start_checkpoint, 0)
        end_idx = self.checkpoints.get(end_checkpoint, self.storage.size())
        
        events = []
        for i in range(start_idx, end_idx):
            event_data = self.storage.read(i)
            events.append(Event.from_json(event_data))
        
        return events
```

#### 4.3 Checkpoint Store (检查点存储)

```python
class CheckpointStore:
    """检查点存储 - 保存系统状态"""
    
    def __init__(self, storage_path: str):
        self.storage = storage_path
    
    def save(self, 
             checkpoint_id: str,
             state: SystemState) -> str:
        """保存检查点"""
        path = f"{self.storage}/{checkpoint_id}.json"
        
        checkpoint = {
            "id": checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "message_pool_state": state.message_pool.snapshot(),
            "agent_states": {
                agent_id: agent.get_state()
                for agent_id, agent in state.agents.items()
            },
            "workflow_states": state.workflows
        }
        
        with open(path, 'w') as f:
            json.dump(checkpoint, f)
        
        return path
    
    def load(self, checkpoint_id: str) -> SystemState:
        """加载检查点"""
        path = f"{self.storage}/{checkpoint_id}.json"
        
        with open(path, 'r') as f:
            checkpoint = json.load(f)
        
        # 恢复状态
        state = SystemState()
        state.message_pool.restore(checkpoint["message_pool_state"])
        # ... 恢复其他状态
        
        return state
```

---

## 📁 目录结构

```
wdai/
├── core/                           # 核心系统
│   ├── __init__.py
│   ├── message_bus/               # 消息总线
│   │   ├── __init__.py
│   │   ├── pool.py                # MessagePool
│   │   ├── router.py              # PubSubRouter
│   │   ├── message.py             # Message定义
│   │   └── storage.py             # 持久化存储
│   ├── sop_engine/                # SOP引擎
│   │   ├── __init__.py
│   │   ├── workflow.py            # 工作流定义
│   │   ├── orchestrator.py        # 编排器
│   │   ├── dsl.py                 # DSL解析
│   │   └── templates/             # 工作流模板
│   │       ├── code_development.yaml
│   │       ├── research.yaml
│   │       └── ...
│   └── agent_team/                # Agent团队
│       ├── __init__.py
│       ├── base.py                # BaseAgent
│       ├── roles.py               # 角色定义
│       ├── product_manager.py
│       ├── architect.py
│       ├── coder.py
│       ├── reviewer.py
│       ├── reflector.py
│       └── evolution.py
├── infrastructure/                 # 基础设施
│   ├── __init__.py
│   ├── memrl_integration.py       # MemRL集成
│   ├── event_store.py             # 事件存储
│   ├── checkpoint_store.py        # 检查点存储
│   └── sandbox/                   # Docker沙盒(可选)
│       ├── client.py
│       └── runtime.py
├── config/                         # 配置
│   ├── agents.yaml                # Agent配置
│   ├── workflows.yaml             # 工作流配置
│   └── system.yaml                # 系统配置
└── tests/                          # 测试
    ├── test_message_bus/
    ├── test_sop_engine/
    └── test_agents/
```

---

## 🔧 配置示例

### agents.yaml
```yaml
agents:
  product_manager:
    role: ProductManager
    llm:
      model: kimi-coding/k2p5
      temperature: 0.7
    skills:
      - requirement_analysis
      - user_story
    timeout: 300
    
  coder:
    role: Coder
    llm:
      model: kimi-coding/k2p5
      temperature: 0.2
    skills:
      - code_generation
      - refactoring
    timeout: 600
    
  reviewer:
    role: Reviewer
    llm:
      model: kimi-coding/k2p5
      temperature: 0.1
    skills:
      - code_review
      - security_audit
    timeout: 300
```

### workflows.yaml
```yaml
workflows:
  code_development:
    description: "完整的代码开发流程"
    steps:
      - name: analyze
        agent: product_manager
        output: prd
        
      - name: design
        agent: architect
        input: "{{ steps.analyze.output }}"
        output: design_doc
        depends_on: [analyze]
        
      - name: implement
        agent: coder
        input: "{{ steps.design.output }}"
        output: code
        depends_on: [design]
        
      - name: review
        agent: reviewer
        input: "{{ steps.implement.output }}"
        output: review_report
        depends_on: [implement]
        
    error_handling:
      retry: 2
      fallback: human_review
```

---

## 🧪 测试策略

### 单元测试
- MessageBus: 发布、订阅、路由
- SOP Engine: 依赖图构建、步骤执行
- Agent: 角色定义、任务执行

### 集成测试
- 完整工作流执行
- 多Agent协作
- 错误恢复

### 端到端测试
- 真实任务执行
- 性能基准
- 故障注入

---

## 📊 性能考虑

### 1. 消息吞吐量
- 目标: 1000 msg/s
- 优化: 批量处理、异步IO

### 2. 存储
- 消息池: 分区存储、自动归档
- 事件存储: Append-only log

### 3. 内存
- Agent池: 按需创建、超时回收
- 消息缓存: LRU策略

---

*Architecture Design Document - wdai v3.0*
