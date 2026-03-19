# OpenHands (原OpenDevin) 架构研究报告

**研究日期**: 2026-03-17  
**GitHub**: https://github.com/All-Hands-AI/OpenHands  
**Stars**: 38K+  
**语言**: Python/TypeScript

---

## 📋 项目概述

OpenHands 是一个开源的自主软件Agent框架，目标是让用户"Code Less, Make More"。它能够：
- 修改代码
- 执行命令
- 浏览网页
- 调用API
- 自主完成端到端的软件开发任务

---

## 🏗️ 核心架构

### 1. 事件驱动架构 (Event-Driven Architecture)

```
┌─────────────────────────────────────────┐
│         User Interface (Web/CLI)         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Event Stream Controller          │
│  (Orchestrates all agent actions)       │
└─────┬────────────────────┬──────────────┘
      │                    │
┌─────▼──────┐      ┌──────▼─────┐
│   Planner  │      │  Sandbox   │
│ (LLM)      │      │ (Docker)   │
└─────┬──────┘      └──────┬─────┘
      │                    │
┌─────▼────────────────────▼─────┐
│      Execution Engine           │
│  (Maps plans → container ops)   │
└─────────────────────────────────┘
```

**关键特点**:
- 每个动作都是不可变事件
- 支持确定性重放（调试Agent行为）
- 检查点机制（可回滚到任意执行点）
- 多Agent可订阅同一事件流

### 2. Runtime Sandbox (Docker容器)

**安全执行环境**:
- 隔离的Docker容器
- 可配置的只读工作空间访问
- 网络限制（可禁用）
- 资源限制（CPU、内存、磁盘）
- 会话结束自动清理

**Client-Server架构**:
```
User Input → 构建Docker镜像 → 启动容器 → 
初始化ActionExecutor → RESTful API通信 → 
执行动作 → 返回Observations
```

### 3. 状态与事件流

**状态 (State)**:
- 封装Agent执行任务的所有信息
- 关键组件：事件流（按时间顺序收集动作和观察）

**动作 (Actions)**:
- `IPythonRunCellAction` - 执行Python代码
- `CmdRunAction` - 执行bash命令
- `BrowserInteractiveAction` - 浏览器交互
- `AgentDelegateAction` - 委托子任务给其他Agent

**观察 (Observations)**:
- 用户自然语言指令
- 动作执行结果（代码执行结果等）
- 环境变化描述

### 4. LLM集成层

**规划系统**:
- 将复杂请求分解为子任务
- 维护已完成步骤的工作记忆
- 验证LLM输出是否符合预期schema
- 失败时修改prompt重试

**支持的模型**:
- OpenAI (GPT-4o)
- Anthropic (Claude)
- Google (Gemini)
- 本地模型 (Ollama)
- 通过LiteLLM统一接口

---

## 🔑 核心优势

| 优势 | 说明 |
|:---|:---|
| **完全自主** | 端到端处理完整功能实现，无需人工干预 |
| **浏览器访问** | 可搜索文档、研究、完成web+代码的完整任务循环 |
| **模型无关** | 可切换Claude/GPT-4o/开源LLM |
| **SWE-Bench** | 在公开排行榜上排名前10 |
| **数据隐私** | 完全本地执行，数据不出机器 |
| **沙盒安全** | Docker隔离执行所有命令 |

---

## ⚠️ 局限性

| 局限 | 说明 |
|:---|:---|
| **性能波动** | 依赖底层LLM、代码库复杂度、测试质量 |
| **模糊任务** | 不明确的需求会导致规划漂移和重复循环 |
| **Token消耗** | 任务不明确时可能"token-hungry" |
| **非人类替代** | 目前更适合作为"强力实习生"而非独立开发者 |
| **基础设施** | 需要Docker，Windows安装复杂 |
| **长周期任务** | 上下文碎片化和有限长期记忆 |

---

## 🎯 适用场景

**表现优秀**:
- ✅ 明确的bug修复（有可复现的测试）
- ✅ 代码库范围的重构（有清晰需求约束）
- ✅ 文档更新
- ✅ 依赖升级
- ✅ 语言转换

**表现较差**:
- ❌ 模糊的产品需求
- ❌ 脆弱环境（flaky tests、慢安装）
- ❌ 复杂多服务编排
- ❌ 长周期、多仓库变更

---

## 🔧 Agent实现

### 核心方法：`step()`

```python
def step(self, state: State) -> Action:
    """
    将当前状态作为输入
    根据Agent逻辑生成适当的动作
    """
    # 1. 观察环境和历史
    # 2. 思考下一步
    # 3. 生成Action
    return action
```

### 默认Agent: MonologueAgent

- 有限的但稳定的能力
- 适合大多数任务

### 其他Agent

- **SWE Agent** - 专门用于软件工程任务（开发中）

---

## 🔄 与wdai的对比

| 维度 | OpenHands | wdai v2.2 |
|:---|:---|:---|
| **架构** | 事件驱动 + Docker沙盒 | 三区安全 + 持久状态 |
| **执行环境** | 隔离Docker容器 | 主机直接执行（有安全检查） |
| **多Agent** | 支持（通过AgentDelegateAction） | 5个专用Agent |
| **记忆** | 事件流 + 工作记忆 | MemRL + 文件持久化 |
| **自主性** | 高（完整任务循环） | 中等（任务驱动） |
| **人机协作** | 可干预、调整提示 | 提案审批系统 |
| **安全性** | Docker隔离 | 三区安全架构 |
| **浏览器** | 内置浏览器工具 | 需外部集成 |

---

## 💡 可借鉴的设计

### 1. 事件流架构
**价值**: 比wdai当前的文件状态更灵活
**适用性**: 🔴 高

```python
# wdai可以实现类似的事件系统
class Event:
    timestamp: datetime
    action: Action
    observation: Observation
    agent_id: str

event_stream: List[Event]  # 可重放、可检查点
```

### 2. Docker沙盒执行
**价值**: 比wdai的"安全检查"更强的隔离
**适用性**: 🟡 中（需要Docker环境）

### 3. Agent委托机制
**价值**: 多Agent协作的标准化方式
**适用性**: 🔴 高

```python
# 当前wdai的多Agent是独立的
# 可以实现委托机制：
class AgentDelegateAction(Action):
    subtask: str
    target_agent: str  # "coder", "reviewer", "reflector"
```

### 4. 检查点与重放
**价值**: 调试Agent行为、回滚错误
**适用性**: 🔴 高

```python
# wdai的持久状态可以扩展
checkpoint = create_checkpoint()
# ... agent执行 ...
if error:
    rollback_to(checkpoint)
```

### 5. 结构化动作/观察
**价值**: 比自由文本更可靠的Agent行为
**适用性**: 🔴 高

---

## 📊 适用性评分

| 维度 | 评分 | 说明 |
|:---|:---:|:---|
| **架构创新** | 0.9 | 事件驱动架构优秀 |
| **wdai集成** | 0.7 | 需要Docker环境 |
| **安全增强** | 0.8 | Docker隔离优于当前方案 |
| **多Agent** | 0.6 | wdai已有Agent系统 |
| **总体** | **0.75** | 高适用性 |

---

## 🚀 集成建议

### 短期（可行）
1. 实现事件流日志系统
2. 添加Agent委托Action
3. 改进检查点机制

### 中期（需规划）
4. 可选Docker沙盒执行
5. 集成浏览器自动化

### 长期（研究）
6. 完全自主的任务循环

---

## 📚 参考资料

- [OpenHands Docs](https://docs.openhands.dev)
- [Architecture Overview](https://docs.openhands.dev/openhands/usage/architecture)
- [Runtime Architecture](https://docs.openhands.dev/openhands/usage/architecture/runtime)

---

*Research completed: 2026-03-17*
