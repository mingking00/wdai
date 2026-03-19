# MetaGPT 架构研究报告

**研究日期**: 2026-03-17  
**GitHub**: https://github.com/geekan/MetaGPT  
**Stars**: 45K+  
**语言**: Python

---

## 📋 项目概述

MetaGPT 是一个元编程框架，通过多Agent协作模拟完整软件开发团队。它将LLM-based Agent组织成角色（产品经理、架构师、工程师、QA），通过结构化通信协作，将自然语言需求转化为完整软件解决方案。

**核心理念**: "SOP as Code" - 将标准操作流程编码为Agent行为

---

## 🏗️ 核心架构

### 1. 角色系统 (Role System)

```
┌─────────────────────────────────────────┐
│            Environment                   │
│  (Message routing + Role management)    │
└──────┬──────────────┬───────────────────┘
       │              │
┌──────▼──────┐  ┌────▼─────────┐
│   Roles     │  │  Message Pool │
│             │  │  (Global)     │
│ • Product    │  └──────────────┘
│   Manager   │         ▲
│ • Architect  │         │
│ • Engineer   │         │
│ • QA         │         │
│ • Project    │    ┌────┴────┐
│   Manager    │    │  Team   │
└──────┬──────┘    └─────────┘
       │
  ┌────┴────┐
  │ Actions │
  │ Memory  │
  └─────────┘
```

### 2. 软件开发团队角色

| 角色 | 职责 | 关键动作 |
|:---|:---|:---|
| **Product Manager** | 需求分析、PRD编写 | 市场调研、用户故事、需求池 |
| **Architect** | 系统设计 | 文件列表、数据结构、接口定义 |
| **Project Manager** | 任务分配 | 拆解任务、分配工程师 |
| **Engineer** | 代码实现 | 编写类/函数、执行代码 |
| **QA Engineer** | 质量保证 | 测试用例、代码审查 |

### 3. 消息传递架构

**发布-订阅机制 (Publish-Subscribe)**:

```
┌─────────────────────────────────────────┐
│           Global Message Pool            │
├─────────────────────────────────────────┤
│  Message 1: PRD (from Product Manager)   │
│  Message 2: Design (from Architect)      │
│  Message 3: Task (from Project Manager)  │
│  Message 4: Code (from Engineer)         │
│  Message 5: Review (from QA)             │
└─────────────────────────────────────────┘
        ▲          ▲          ▲
        │          │          │
   ┌────┴───┐  ┌───┴───┐  ┌──┴────┐
   │ Role A │  │Role B │  │Role C │
   └───┬────┘  └───┬───┘  └──┬────┘
       │           │         │
       └───────────┴─────────┘
              Subscribe
```

**消息结构**:
```python
class Message:
    content: str          # 内容（结构化文档）
    role: str             # 发送者角色
    cause: str            # 触发原因
    send_to: List[str]    # 目标接收者
```

### 4. 标准操作流程 (SOP)

**软件开发生命周期自动化**:

```
用户需求
    ↓
产品经理 (Product Manager)
    ↓ 输出: PRD (产品需求文档)
    ↓     包含: 用户故事、需求池
    ↓
架构师 (Architect)
    ↓ 输出: 系统设计
    ↓     包含: 文件列表、数据结构、接口定义
    ↓
项目经理 (Project Manager)
    ↓ 输出: 任务分配
    ↓     包含: 具体类/函数任务
    ↓
工程师 (Engineer)
    ↓ 输出: 代码实现
    ↓
QA工程师 (QA Engineer)
    ↓ 输出: 测试用例、代码审查
    ↓
完整软件解决方案
```

### 5. 动作框架 (Action Framework)

**Action基类**:
```python
class Action:
    name: str           # 动作名称
    prefix: str         # Prompt工程前缀
    
    async def run(self, **kwargs) -> Message:
        # 使用LLM生成响应
        # 基于精心设计的prompt
        return message
```

**关键Actions**:
- `WritePRD` - 编写产品需求文档
- `DesignAPI` - API设计
- `WriteCode` - 代码编写
- `WriteCodeReview` - 代码审查
- `RunCode` - 代码执行

### 6. 记忆系统 (Memory)

**角色记忆**:
- 存储消息历史
- 检索相关信息
- 跨角色持久化知识

```python
class Memory:
    storage: List[Message]
    
    def add(self, message: Message)
    def get(self, k: int) -> List[Message]  # 最近k条
    def search(self, query: str) -> List[Message]
```

---

## 🔑 核心优势

| 优势 | 说明 |
|:---|:---|
| **角色专业化** | 明确角色分工，像真实团队一样协作 |
| **结构化通信** | 文档和图表而非自由对话，减少歧义 |
| **SOP驱动** | 标准操作流程确保一致性和可重复性 |
| **完整交付物** | PRD、架构文档、代码、测试，端到端 |
| **研究支持** | Stanford、CMU等活跃研究社区 |
| **端到端自动化** | 从需求到完整软件的完整流水线 |

---

## ⚠️ 局限性

| 局限 | 说明 |
|:---|:---|
| **领域局限** | 针对软件开发生命周期优化，其他领域需适配 |
| **Token成本** | 多Agent多轮对话，成本较高 |
| **代码质量** | 生成代码需要人工审查才能上生产 |
| **灵活性** | 预定义角色不如通用框架灵活 |
| **学习曲线** | 理解SOP和角色系统需要时间 |

---

## 🎯 与wdai的对比分析

### 当前wdai的Agent系统

```
Coordinator (main)
├── Coder (coder)
├── Reviewer (reviewer)
├── Reflector (reflector)
└── Evolution (evolution)

通信: 通过文件和函数调用
协作: 由Coordinator显式调度
```

### MetaGPT的Agent系统

```
Team (Environment)
├── Product Manager
├── Architect
├── Project Manager
├── Engineer
└── QA Engineer

通信: 通过全局消息池（发布-订阅）
协作: 通过SOP流程自组织
```

### 对比表

| 维度 | MetaGPT | wdai v2.2 |
|:---|:---|:---|
| **角色定义** | 预定义软件开发角色 | 通用Agent（Coder/Reviewer等） |
| **通信机制** | 消息池（发布-订阅） | 直接函数调用 + 文件 |
| **协作流程** | SOP驱动（流水线） | 任务驱动（人工调度） |
| **交付物** | 完整SDLC产出 | 代码 + 文档 |
| **自主性** | 高（自组织） | 中（需Coordinator） |
| **领域** | 专注软件开发 | 通用任务 |
| **人机协作** | 可干预流程 | 提案审批系统 |
| **记忆** | 角色级记忆 | MemRL全局记忆 |

---

## 💡 可借鉴的设计

### 1. 发布-订阅消息系统
**价值**: 比wdai的直接调用更解耦、更灵活
**适用性**: 🔴 高

```python
# wdai可以实现类似的消息池
class MessagePool:
    messages: List[Message]
    subscribers: Dict[str, List[Agent]]
    
    def publish(self, message: Message):
        self.messages.append(message)
        for agent in self.subscribers.get(message.target_role, []):
            agent.notify(message)
    
    def subscribe(self, role: str, agent: Agent):
        self.subscribers[role].append(agent)
```

### 2. 角色专业化
**价值**: 明确分工，每个Agent有清晰职责
**适用性**: 🔴 高

```python
# wdai可以进一步细化角色
class ProductManager(Agent):
    goal: str = "分析需求并编写PRD"
    skills: List[str] = ["market_research", "user_story"]
    
class Architect(Agent):
    goal: str = "设计系统架构"
    skills: List[str] = ["system_design", "api_design"]
```

### 3. SOP as Code
**价值**: 将流程编码，确保一致性和可复现
**适用性**: 🔴 高

```python
# wdai可以定义SOP
class SOP:
    steps: List[Step]
    
    @step
    def analyze_requirement(self, input: str) -> PRD:
        return product_manager.run(input)
    
    @step
    def design_architecture(self, prd: PRD) -> Design:
        return architect.run(prd)
    
    @step
    def implement_code(self, design: Design) -> Code:
        return engineer.run(design)
```

### 4. 结构化通信格式
**价值**: 文档化产出比自由对话更可靠
**适用性**: 🟡 中

```python
# 当前wdai的自由文本 → 结构化模板
class PRD:
    user_stories: List[UserStory]
    requirement_pool: List[Requirement]
    
class Design:
    file_list: List[str]
    data_structures: Dict[str, Schema]
    api_definitions: List[API]
```

### 5. 团队级编排
**价值**: 比Coordinator更高级的抽象
**适用性**: 🔴 高

```python
# wdai可以实现Team类
class Team:
    environment: Environment
    roles: Dict[str, Role]
    sop: SOP
    
    def run(self, requirement: str) -> Software:
        # 自动按照SOP执行
        for step in self.sop.steps:
            step.execute()
        return self.environment.get_result()
```

---

## 📊 适用性评分

| 维度 | 评分 | 说明 |
|:---|:---:|:---|
| **架构创新** | 0.9 | 发布-订阅 + SOP非常优秀 |
| **wdai集成** | 0.8 | 可逐步引入消息池和SOP |
| **多Agent协调** | 0.9 | 比当前Coordinator更先进 |
| **实用性** | 0.7 | 专注软件开发，需适配通用任务 |
| **总体** | **0.825** | 非常高适用性 |

---

## 🚀 集成建议

### 短期（可行）
1. **实现消息池系统**
   - 全局消息存储
   - 发布-订阅机制
   - 与现有MemRL集成

2. **细化Agent角色**
   - 为每个Agent定义明确goal和skills
   - 标准化输入输出格式

### 中期（需规划）
3. **SOP工作流引擎**
   - 定义可配置的工作流
   - 步骤之间的依赖管理
   - 错误处理和重试

4. **结构化产出物**
   - 代码设计文档模板
   - 代码审查报告模板
   - 提案文档模板

### 长期（愿景）
5. **完整软件工厂**
   - 从需求到部署的完整流水线
   - 集成OpenHands的Docker沙盒
   - 自动化测试和部署

---

## 🎯 wdai改进提案

基于MetaGPT架构，建议wdai演进至v3.0：

### v3.0 架构愿景

```
Team (wdai)
├── Environment (消息池 + 共享状态)
│   └── MessagePool
│   └── SharedMemory (MemRL)
│
├── SOP Engine (工作流编排)
│   └── Workflow Definitions
│   └── Step Dependencies
│
└── Roles (专业化Agent)
    ├── ProductManager (需求分析)
    ├── Architect (系统设计)
    ├── Coder (代码实现)
    ├── Reviewer (代码审查)
    ├── Reflector (反思改进)
    └── Evolution (系统进化)
```

### 关键改进

1. **消息驱动**: Agent间通过消息池通信
2. **SOP流程**: 预定义任务类型的工作流
3. **角色专业化**: 每个Agent有明确职责和技能
4. **结构化产出**: 标准化文档格式

---

## 📚 参考资料

- [MetaGPT GitHub](https://github.com/geekan/MetaGPT)
- [MetaGPT Paper (ICLR 2024)](https://proceedings.iclr.cc/paper_files/paper/2024/file/6507b115562bb0a305f1958ccc87355a-Paper-Conference.pdf)
- [DeepWiki Core Architecture](https://deepwiki.com/geekan/MetaGPT/2-core-architecture)

---

*Research completed: 2026-03-17*
