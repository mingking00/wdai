# Claude Code vs wdai v3 架构对比分析

**分析时间**: 2026-03-17  
**分析人**: wdai

---

## 🏗️ Claude Code 核心架构

### 1. WAT 框架 (Workflows-Agents-Tools)

```
┌─────────────────────────────────────────────────────────────┐
│                      WAT Framework                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Workflows  │  │   Agents    │  │       Tools         │ │
│  │   工作流层   │  │   推理层    │  │      工具层         │ │
│  │  (导演)     │  │   (演员)    │  │    (道具设备)        │ │
│  ├─────────────┤  ├─────────────┤  ├─────────────────────┤ │
│  │ - 编排逻辑   │  │ - 接收上下文 │  │ - 具体能力          │ │
│  │ - 执行顺序   │  │ - 推理决策   │  │ - 系统交互          │ │
│  │ - 条件控制   │  │ - 工具调用   │  │ - 外部服务          │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                    │            │
│         └────────────────┼────────────────────┘            │
│                          ↓                                  │
│                    交互方式                                 │
│         Workflows → 指挥 → Agents → 使用 → Tools           │
│         Tools → 返回结果 → Agents → 报告 → Workflows       │
└─────────────────────────────────────────────────────────────┘
```

**核心原则**: 单一职责分离
- Workflow不做推理
- Agent不直接操作工具细节
- Tool不包含业务逻辑

---

### 2. 单线程主循环 (nO)

```
Claude Code Session Lifecycle (nO)
┌─────────────────────────────────────────┐
│  1. User Command (用户命令)              │
│          ↓                              │
│  2. Intent Analysis (意图分析)           │
│          ↓                              │
│  3. Agent Selection (Agent选择)          │
│    ├─ Explore Agent (代码探索)           │
│    ├─ Debugger Agent (调试)              │
│    ├─ Code Reviewer (审查)               │
│    └─ Custom Agents (自定义)             │
│          ↓                              │
│  4. Tool Execution (工具执行)            │
│    ├─ Read/Write/Grep/Edit               │
│    ├─ Bash (命令执行)                    │
│    ├─ MCP Servers (外部服务)             │
│    └─ Skills (自定义技能)                │
│          ↓                              │
│  5. Result Presentation (结果呈现)       │
└─────────────────────────────────────────┘
```

**设计哲学**: "简单、单线程的主循环 + 规范的工具和规划 = 可控的自主性"

---

### 3. Agent 团队架构

```
~/.claude/                    # 文件系统作为协调层
├── teams/{team-name}/
│   ├── config.json           # 团队成员注册表
│   └── inboxes/{agent}.json  # 每个Agent的邮箱
└── tasks/{team-name}/
    ├── .lock                 # 文件锁（并发控制）
    ├── .highwatermark        # 自增计数器
    ├── 1.json                # 任务文件
    └── 2.json

┌─────────────────────────────────────────────┐
│              Agent Team (去中心化)            │
├─────────────────────────────────────────────┤
│                                             │
│    ┌─────────┐                              │
│    │ Team    │ 创建团队、生成任务、协调       │
│    │ Lead    │                              │
│    └────┬────┘                              │
│         │                                   │
│    ┌────┴────┬─────────┬─────────┐         │
│    ↓         ↓         ↓         ↓         │
│ ┌────┐   ┌────┐   ┌────┐   ┌────┐         │
│ │A1  │   │A2  │   │A3  │   │A4  │   teammates │
│ │Bug │   │Comp│   │Good│   │Dev │           │
│ │Hunt│   │lex │   │Adv │   │    │           │
│ └────┘   └────┘   └────┘   └────┘         │
│                                             │
│ 通信方式: 文件读写 (JSON inbox)              │
│ 任务获取: 自声明 (Self-claim)               │
│ 协调层: 文件系统                            │
└─────────────────────────────────────────────┘
```

**特点**:
- 无后台进程，纯文件协调
- 自声明任务（非分配）
- 基于文件锁的并发控制

---

### 4. Orchestrator-Subagent 模式

```
┌─────────────────────────────────────────────────────┐
│              Hub-and-Spoke 模式                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│                     ┌─────────┐                    │
│                     │  Hub    │  (中心路由)         │
│                     │Router   │                    │
│                     └────┬────┘                    │
│                          │                         │
│         ┌────────────────┼────────────────┐        │
│         ↓                ↓                ↓        │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐    │
│    │Subagent │     │Subagent │     │Subagent │    │
│    │   A     │     │   B     │     │   C     │    │
│    │(专门化) │     │(专门化) │     │(专门化) │    │
│    └────┬────┘     └────┬────┘     └────┬────┘    │
│         │               │               │         │
│         └───────────────┴───────────────┘         │
│                     ↓                              │
│              完成Token → 返回Hub                   │
│                                                     │
│ 关键规则:                                          │
│ - 只有协调Agent能编排工作流                        │
│ - Subagent完成任务后必须返回Hub                     │
│ - 防止边界越界                                     │
└─────────────────────────────────────────────────────┘
```

**Fresh Eyes 原则**: Subagent只接收相关上下文，不接收完整工作流信息

---

### 5. 关键设计决策

| 决策 | Claude Code 选择 | 理由 |
|:---|:---|:---|
| **并发模型** | 单线程主循环 + 有限并行 | 可调试性 > 性能 |
| **协调层** | 文件系统 | 简单、持久、无状态 |
| **消息传递** | JSON文件 | 人类可读、可审计 |
| **上下文管理** | Fresh Eyes (窄上下文) | 专注度 > 全局信息 |
| **规划方式** | TODO-based (扁平) | 清晰、可追踪 |
| **代码变更** | Diff-based | 精确、可回滚 |

---

## 🏗️ wdai v3 当前架构

### 当前实现 (Phase 1 + Phase 2)

```
wdai v3.0 Current Architecture
┌─────────────────────────────────────────────────────────────┐
│                      wdai v3.0                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 2: Workflow Engine (SOP)                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Workflow → Step → Dependency → Executor            │   │
│  │  工作流    → 步骤 → 依赖解析  → 执行器              │   │
│  │                                                      │   │
│  │  - DAG依赖管理                                       │   │
│  │  - 并行/串行执行                                     │   │
│  │  - 重试策略                                          │   │
│  │  - 模板系统                                          │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│  Phase 1: Message Bus (Pub/Sub)                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Message → MessagePool → PubSubRouter               │   │
│  │  消息     → 消息池      → 发布订阅路由器             │   │
│  │                                                      │   │
│  │  - 异步消息传递                                      │   │
│  │  - 持久化存储                                        │   │
│  │  - 事件驱动                                          │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                 │
│  Infrastructure                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  - Memory System (MemRL)                            │   │
│  │  - IER (经验学习)                                    │   │
│  │  - Self-Reflection                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 架构对比

### 1. 分层对比

| 维度 | Claude Code | wdai v3 (当前) | 差距 |
|:---|:---|:---|:---:|
| **工作流层** | ✅ WAT框架 | ✅ Phase 2实现 | 相当 |
| **Agent层** | ✅ 专业化分工 | ❌ 单一Agent | 🔴 缺失 |
| **工具层** | ✅ 100+工具 | ⚠️ 有限工具 | 🟡 不足 |
| **协调层** | ✅ 文件系统 | ✅ 消息总线 | 相当 |
| **上下文管理** | ✅ Fresh Eyes | ❌ 完整上下文 | 🔴 差距 |
| **规划方式** | ✅ TODO-based | ❌ 无明确规划 | 🔴 缺失 |

### 2. 具体差距分析

#### 🔴 关键差距 1: Agent专业化 (缺失)

**Claude Code**:
```
Explore Agent → Debugger Agent → Code Reviewer
     ↓                ↓                ↓
 代码探索          调试定位          代码审查
```

**wdai v3 (当前)**:
```
单一Agent处理所有任务
```

**影响**: 缺乏专业化分工，复杂任务效率低

---

#### 🔴 关键差距 2: Fresh Eyes 上下文管理 (缺失)

**Claude Code**:
```python
# Subagent只接收相关上下文
task_context = {
    "file": "test_auth.py",
    "task": "fix failing test",
    # 不包含其他5个任务的信息
}
spawn_subagent(task_context)
```

**wdai v3 (当前)**:
```python
# 完整上下文传递
context = {
    "all_tasks": [...],  # 全部任务
    "full_history": [...],  # 完整历史
    # 信息过载
}
```

**影响**: 上下文膨胀，Agent专注度下降

---

#### 🔴 关键差距 3: TODO-based 规划 (缺失)

**Claude Code**:
```
当前TODO列表:
□ 1. 分析代码结构
□ 2. 定位bug位置  ← 当前
□ 3. 修复bug
□ 4. 运行测试
```

**wdai v3 (当前)**:
```
无显式规划机制
```

**影响**: 缺乏可追踪的执行计划

---

#### 🟡 次要差距 4: 工具丰富度 (不足)

**Claude Code**: 100+ 内置工具
- Read/Write/Grep/Edit
- Bash
- MCP Servers
- Skills

**wdai v3**: 有限工具
- LLM调用
- Shell执行
- Python执行

**影响**: 工具调用能力受限

---

## 💡 改进建议

### 高优先级改进

#### 1. 实现 Agent 专业化系统

```python
# 新增: core/agents/
class BaseAgent(ABC):
    """Agent基类"""
    role: str
    expertise: List[str]
    
    @abstractmethod
    async def execute(self, task: Task, context: NarrowContext) -> Result:
        pass

class ExploreAgent(BaseAgent):
    """代码探索Agent"""
    role = "explorer"
    expertise = ["code_structure", "dependency_analysis"]

class DebuggerAgent(BaseAgent):
    """调试Agent"""
    role = "debugger"
    expertise = ["error_analysis", "log_parsing"]

class ArchitectAgent(BaseAgent):
    """架构设计Agent"""
    role = "architect"
    expertise = ["design_patterns", "system_design"]
```

---

#### 2. 实现 Fresh Eyes 上下文裁剪

```python
class ContextManager:
    """上下文管理器"""
    
    def narrow_context(
        self,
        task: Task,
        full_context: FullContext
    ) -> NarrowContext:
        """
        根据任务裁剪上下文
        
        只保留:
        - 任务相关文件
        - 任务依赖信息
        - 必要的系统状态
        """
        relevant_files = self.find_relevant_files(task)
        relevant_history = self.filter_history(task, full_context.history)
        
        return NarrowContext(
            task=task,
            files=relevant_files,
            history=relevant_history,
            # 不包含其他任务信息
        )
```

---

#### 3. 实现 TODO-based 规划系统

```python
@dataclass
class TodoItem:
    id: str
    description: str
    status: TodoStatus
    dependencies: List[str]
    estimated_effort: int

class TodoManager:
    """TODO管理器"""
    
    def create_plan(self, goal: str) -> List[TodoItem]:
        """基于目标生成TODO列表"""
        
    def get_current_todo(self) -> Optional[TodoItem]:
        """获取当前应执行的TODO"""
        
    def complete_todo(self, todo_id: str):
        """标记TODO完成"""
        
    def update_plan(self, feedback: ExecutionFeedback):
        """根据执行反馈调整计划"""
```

---

### 中优先级改进

#### 4. 扩展工具系统

```python
# 新增工具类型
class ToolRegistry:
    def register_search_tools(self):
        """搜索工具"""
        
    def register_code_tools(self):
        """代码分析工具"""
        
    def register_doc_tools(self):
        """文档工具"""
```

---

#### 5. 优化工作流模板

```python
# 更丰富的模板
class CodeReviewTemplate:
    """代码审查工作流"""
    
class BugFixTemplate:
    """Bug修复工作流"""
    
class RefactorTemplate:
    """重构工作流"""
```

---

## 🎯 wdai v3.1 演进路线

```
wdai v3.0 (当前)
    ↓
├── v3.1: Agent专业化
│   ├── BaseAgent抽象
│   ├── 专业Agent实现
│   └── Agent调度器
    ↓
├── v3.2: 上下文管理
│   ├── Fresh Eyes实现
│   ├── 上下文裁剪
│   └── 相关性分析
    ↓
├── v3.3: 规划系统
│   ├── TODO管理器
│   ├── 动态规划
│   └── 计划调整
    ↓
├── v3.4: 工具扩展
│   ├── 搜索工具
│   ├── 代码分析工具
│   └── 文档工具
    ↓
wdai v3.5 (目标: 接近Claude Code能力)
```

---

## 📈 能力提升预测

| 改进项 | 预期提升 | 工作量 |
|:---|:---:|:---:|
| Agent专业化 | +40% 复杂任务效率 | 3天 |
| Fresh Eyes | +30% 上下文利用率 | 2天 |
| TODO规划 | +25% 可追踪性 | 1天 |
| 工具扩展 | +35% 任务覆盖 | 2天 |

---

## 🏁 结论

**Claude Code 核心优势**:
1. **专业化分工** - Orchestrator + 专业Subagents
2. **上下文管理** - Fresh Eyes原则
3. **规划系统** - TODO-based planning
4. **工具生态** - 丰富的内置工具

**wdai v3 当前状态**:
- ✅ Workflow引擎已具备
- ✅ Message Bus已完善
- ❌ Agent专业化缺失
- ❌ 上下文管理待优化
- ❌ 规划系统待实现

**建议**: 进入 **Phase 3: Agent专业化系统**，实现Orchestrator-Subagent架构

---

*Architecture Analysis - wdai v3 vs Claude Code*
