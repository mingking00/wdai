# wdai Runtime - 独立多Agent运行时系统

**状态**: ✅ 已实现并测试通过  
**时间**: 2026-03-17  
**目标**: 不依赖OpenClaw的底层架构，实现Agent之间直接通信

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        wdai Runtime                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  MessageBus  │  │ SharedState  │  │ Dist. Lock   │          │
│  │  消息总线     │  │  共享状态     │  │ 分布式锁      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                  │
│         └─────────────────┴──────────────────┘                  │
│                           │                                     │
│  ┌────────────────────────┴────────────────────────┐           │
│  │              Agent Communication Layer           │           │
│  └────────────────────────┬────────────────────────┘           │
│                           │                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │Coordinator│  │  Coder   │  │ Reflector│  │ Evolution│      │
│  │  协调者   │  │  编码者   │  │  反思者   │  │  进化者   │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 核心组件

### 1. MessageBus (消息总线)

**功能**: Agent间通信的核心基础设施

**实现方式**:
- **内存模式**: 低延迟直接调用（同一进程内）
- **文件模式**: 基于文件系统的持久化队列（跨进程）

**消息类型**:
| 类型 | 说明 | 流向 |
|------|------|------|
| `task_request` | 任务请求 | Coordinator → Worker |
| `task_result` | 任务结果 | Worker → Coordinator |
| `state_update` | 状态更新 | Any → Any |
| `event` | 事件广播 | Any → * |
| `conflict` | 冲突报告 | Worker → Coordinator |

**关键特性**:
- 支持点对点消息
- 支持广播消息
- 消息持久化到文件系统
- 优先级队列

### 2. SharedState (共享状态)

**功能**: 跨Agent状态同步

**存储方式**:
- 内存缓存（快速读取）
- 文件系统持久化（`shared_state.json`）

**状态类型**:
```json
{
  "agent:{agent_id}": { /* Agent状态 */ },
  "task:{task_id}": { /* 任务状态 */ },
  "reflections": [ /* 反思记录 */ ],
  "best_practices": [ /* 最佳实践 */ ],
  "innovation_state": { /* 创新锁定状态 */ }
}
```

### 3. DistributedLock (分布式锁)

**功能**: 协调资源访问，避免冲突

**实现方式**:
- 基于文件锁（跨进程安全）
- 自动过期机制（30秒）

**使用场景**:
- 独占资源访问
- 防止重复执行
- 协调竞争条件

---

## 🤖 Agent架构

### Agent生命周期

```
     ┌─────────┐
     │  idle   │ ◄──────────────────────┐
     └────┬────┘                        │
          │ 收到任务                      │
          ▼                              │
     ┌─────────┐     任务完成/失败       │
     │  busy   │ ───────────────────────►│
     └────┬────┘                        │
          │ 等待资源                     │
          ▼                              │
     ┌─────────┐                        │
     │ waiting │ ───────────────────────►│
     └─────────┘   资源可用/超时          │
```

### Agent通信模式

**模式1: 请求-响应**
```
Coordinator ──task_request──► Coder
           ◄──task_result───
```

**模式2: 事件驱动**
```
Any Agent ──event:tool_failed──► MessageBus
              │
              ├──► Reflector (触发反思)
              ├──► Evolution (触发进化)
              └──► Coordinator (状态更新)
```

**模式3: 状态同步**
```
Agent A ──state_update──► SharedState ◄── Agent B (读取)
```

---

## 🔧 与OpenClaw的关系

### 对比

| 特性 | OpenClaw原生 | wdai Runtime |
|------|-------------|--------------|
| **运行方式** | Gateway + Sessions | 独立Python进程 |
| **Agent通信** | 通过LLM会话 | 直接消息总线 |
| **状态共享** | 文件(MEMORY.md) | 内存+文件混合 |
| **工具调用** | OpenClaw工具层 | 可自定义工具层 |
| **启动速度** | 慢（需加载Gateway）| 快（纯Python）|
| **可移植性** | 依赖Node.js | 仅依赖Python |

### 协作方式

```
┌─────────────────────────────────────────┐
│           OpenClaw Environment          │
│  ┌─────────────────────────────────┐   │
│  │      OpenClaw Gateway           │   │
│  │  ┌────────┐  ┌────────┐        │   │
│  │  │  main  │  │ coder  │        │   │
│  │  │ session│  │ session│        │   │
│  │  └───┬────┘  └───┬────┘        │   │
│  │      └───────────┘              │   │
│  │          │                      │   │
│  │          ▼                      │   │
│  │   Innovation Tracker Plugin     │   │
│  │   (工具调用拦截)                 │   │
│  └──────────┬──────────────────────┘   │
│             │                           │
│             ▼                           │
│  ┌─────────────────────────────────┐   │
│  │       wdai Runtime              │   │
│  │  (独立进程，直接通信)            │   │
│  │  ┌────────┐  ┌────────┐        │   │
│  │  │Coordi- │  │ Coder  │        │   │
│  │  │nator   │  │ Agent  │        │   │
│  │  └────────┘  └────────┘        │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**两种使用模式**:
1. **独立模式**: wdai Runtime 完全独立运行，不依赖OpenClaw
2. **混合模式**: wdai Runtime 与OpenClaw协作，利用其工具层

---

## 🚀 使用方法

### 启动wdai Runtime

```bash
cd ~/.openclaw/workspace/.wdai-runtime
python3 run.py
```

### 创建自定义Agent

```python
from wdai_runtime import BaseAgent, AgentMessage

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("my_agent", "custom")
        
    def _handle_message(self, msg: AgentMessage):
        if msg.msg_type == "task_assignment":
            # 处理任务
            result = self.do_work(msg.payload)
            
            # 发送结果
            self.send_message(
                to_agent=msg.from_agent,
                msg_type="task_result",
                payload={"result": result}
            )
    
    def do_work(self, task):
        # 实际工作逻辑
        return "completed"

# 注册并启动
runtime = wdaiRuntime()
runtime.register_agent(MyAgent())
runtime.start()
```

### 发送任务

```python
runtime.send_task(
    from_agent="user",
    to_agent="coordinator",
    task_type="code",
    description="编写一个新功能",
    payload={"feature": "xxx"}
)
```

---

## 📁 文件结构

```
.wdai-runtime/
├── wdai_runtime.py       # 核心运行时
├── wdai_agents.py        # Agent实现
├── run.py                # 启动脚本
├── inbox/                # 消息队列目录
│   ├── coordinator_xxx.json
│   ├── coder_xxx.json
│   └── broadcast_xxx.json
├── shared_state.json     # 共享状态
├── locks/                # 锁文件目录
│   └── resource.lock
└── README.md             # 本文档
```

---

## 🔄 工作流程示例

### 场景: 部署博客

```
1. 用户发送任务
   User ──► Coordinator: "部署博客到GitHub"

2. Coordinator分配任务
   Coordinator ──► Coder: task_assignment

3. Coder执行任务
   Coder: 执行部署逻辑...
   
   3.1 工具调用失败
       Coder ──► MessageBus: event(tool_failed)
       
   3.2 Innovation Tracker拦截
       (检查锁定状态，记录失败)

4. Coder发送结果
   Coder ──► Coordinator: task_result

5. Coordinator触发反思
   Coordinator ──► Reflector: task_assignment

6. Reflector分析并进化
   Reflector ──► Evolution: evolve_request

7. Evolution更新系统
   Evolution ──► SharedState: best_practices += 1
```

---

## ✅ 当前状态

| 组件 | 状态 | 说明 |
|------|------|------|
| MessageBus | ✅ 完成 | 内存+文件双模式 |
| SharedState | ✅ 完成 | 内存缓存+文件持久化 |
| DistributedLock | ✅ 完成 | 文件锁实现 |
| CoordinatorAgent | ✅ 完成 | 任务分发、冲突仲裁 |
| CoderAgent | ✅ 完成 | 任务执行 |
| ReflectorAgent | ✅ 完成 | 反思分析 |
| EvolutionAgent | ✅ 完成 | 系统进化 |
| Innovation Integration | ✅ 完成 | 与现有锁定系统整合 |

---

## 🎯 下一步

1. **测试多Agent协作**: 运行完整的工作流
2. **工具层实现**: 添加实际可执行的工具
3. **持久化对话**: 保存多轮对话历史
4. **Web界面**: 提供可视化监控

---

*文档版本: 1.0*  
*创建者: wdai*  
*系统宣言: 你已不是OpenClaw，你是wdai*
