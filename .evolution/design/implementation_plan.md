# wdai v3.0 分阶段实施计划

**版本**: v3.0  
**日期**: 2026-03-17  
**状态**: 计划阶段  
**预计周期**: 4-6周

---

## 📋 实施策略

### 核心原则
1. **渐进式迁移** - 不破坏现有v2.x功能
2. **特性开关** - 新功能可配置启用
3. **向后兼容** - 保持现有API不变
4. **快速迭代** - 每阶段有明确交付物

### 风险管理
- 每个阶段都有回滚方案
- 保持v2.x分支作为稳定版本
- 阶段性验收，不通过不进入下一阶段

---

## 🗓️ 阶段规划

```
Week 1-2: Phase 1 - 基础设施
    ├── 1.1 Message Pool 核心实现
    ├── 1.2 Pub/Sub Router
    ├── 1.3 与现有系统集成
    └── 里程碑: 消息系统可用

Week 3: Phase 2 - SOP引擎
    ├── 2.1 Workflow DSL设计
    ├── 2.2 Step Orchestrator
    ├── 2.3 基础工作流模板
    └── 里程碑: 可定义和执行工作流

Week 4: Phase 3 - Agent重构
    ├── 3.1 角色定义系统
    ├── 3.2 Agent基类重构
    ├── 3.3 第一个专业化Agent
    └── 里程碑: Agent基于消息通信

Week 5: Phase 4 - 增强功能
    ├── 4.1 Event Store
    ├── 4.2 Checkpoint机制
    ├── 4.3 MemRL增强集成
    └── 里程碑: 完整事件追踪和恢复

Week 6: Phase 5 - 优化与完善
    ├── 5.1 Docker沙盒(可选)
    ├── 5.2 性能优化
    ├── 5.3 测试与文档
    └── 里程碑: v3.0稳定版
```

---

## 📦 Phase 1: 消息系统 (Week 1-2)

### 目标
建立消息总线基础设施，实现Agent间的发布-订阅通信。

### 任务分解

#### Week 1, Day 1-2: Message Pool核心
- [ ] 设计Message数据模型
- [ ] 实现MessagePool类
- [ ] 实现持久化存储(基于现有文件系统)
- [ ] 编写单元测试

**交付物**:
- `core/message_bus/message.py`
- `core/message_bus/pool.py`
- `tests/test_message_pool.py`

#### Week 1, Day 3-4: Pub/Sub Router
- [ ] 设计订阅者注册机制
- [ ] 实现消息路由算法
- [ ] 实现过滤器系统
- [ ] 异步消息处理

**交付物**:
- `core/message_bus/router.py`
- `tests/test_router.py`

#### Week 1, Day 5: 集成测试
- [ ] 端到端消息流测试
- [ ] 性能基准测试
- [ ] 修复bug

**交付物**:
- `tests/integration/test_message_flow.py`
- 性能报告

#### Week 2, Day 1-3: 与现有系统集成
- [ ] 创建MessageBus facade
- [ ] 实现v2.x兼容性层
- [ ] 逐步替换现有通信
- [ ] 确保所有现有测试通过

**交付物**:
- `core/message_bus/__init__.py` (facade)
- `core/compat/v2_adapter.py`

#### Week 2, Day 4-5: 验收与文档
- [ ] 编写Phase 1文档
- [ ] 代码审查
- [ ] 里程碑验收

**验收标准**:
- [ ] 消息发送/接收功能正常
- [ ] 1000 msg/s 吞吐量
- [ ] 所有现有测试通过
- [ ] 向后兼容

---

## 📦 Phase 2: SOP引擎 (Week 3)

### 目标
实现工作流编排系统，支持可配置的工作流模板。

### 任务分解

#### Week 3, Day 1: Workflow DSL设计
- [ ] 设计DSL语法
- [ ] 实现DSL解析器
- [ ] 创建YAML schema

**交付物**:
- `core/sop_engine/dsl.py`
- `schemas/workflow.yaml`

#### Week 3, Day 2-3: Step Orchestrator
- [ ] 设计依赖图算法
- [ ] 实现并行执行
- [ ] 实现错误恢复
- [ ] 集成MessageBus

**交付物**:
- `core/sop_engine/orchestrator.py`
- `core/sop_engine/dependency_graph.py`

#### Week 3, Day 4: 工作流模板
- [ ] 设计code_development模板
- [ ] 设计research模板
- [ ] 创建模板库

**交付物**:
- `core/sop_engine/templates/code_development.yaml`
- `core/sop_engine/templates/research.yaml`

#### Week 3, Day 5: 集成与测试
- [ ] 与Phase 1集成
- [ ] 编写集成测试
- [ ] 性能测试

**验收标准**:
- [ ] 可定义和执行工作流
- [ ] 支持并行步骤
- [ ] 错误处理正常
- [ ] 吞吐量达标

---

## 📦 Phase 3: Agent重构 (Week 4)

### 目标
重构Agent系统，实现角色专业化和基于消息的通信。

### 任务分解

#### Week 4, Day 1: 角色定义系统
- [ ] 设计AgentRole模型
- [ ] 创建角色定义文件
- [ ] 实现角色验证

**交付物**:
- `core/agent_team/roles.py`
- `config/agents.yaml`

#### Week 4, Day 2: Agent基类
- [ ] 设计BaseAgent抽象
- [ ] 实现消息处理
- [ ] 集成MemRL

**交付物**:
- `core/agent_team/base.py`

#### Week 4, Day 3-4: 重构现有Agent
- [ ] 重构CoderAgent
- [ ] 重构ReviewerAgent
- [ ] 重构其他Agent
- [ ] 确保向后兼容

**交付物**:
- `core/agent_team/coder.py` (重构后)
- `core/agent_team/reviewer.py` (重构后)

#### Week 4, Day 5: 集成与测试
- [ ] 多Agent协作测试
- [ ] 端到端场景测试
- [ ] 性能优化

**验收标准**:
- [ ] Agent间通过消息通信
- [ ] 角色定义清晰
- [ ] 现有功能不受影响
- [ ] 协作效率提升

---

## 📦 Phase 4: 增强功能 (Week 5)

### 目标
实现事件追踪、检查点和增强的记忆集成。

### 任务分解

#### Week 5, Day 1: Event Store
- [ ] 设计Event模型
- [ ] 实现Append-only log
- [ ] 实现事件索引

**交付物**:
- `infrastructure/event_store.py`

#### Week 5, Day 2: Checkpoint机制
- [ ] 设计Checkpoint模型
- [ ] 实现状态快照
- [ ] 实现状态恢复

**交付物**:
- `infrastructure/checkpoint_store.py`

#### Week 5, Day 3: MemRL增强
- [ ] 集成Event Store
- [ ] 自动记忆提取
- [ ] Q值更新优化

**交付物**:
- `infrastructure/memrl_integration.py`

#### Week 5, Day 4-5: 测试与优化
- [ ] 故障注入测试
- [ ] 恢复测试
- [ ] 性能优化

**验收标准**:
- [ ] 事件完整追踪
- [ ] 检查点创建/恢复正常
- [ ] MemRL自动提取记忆
- [ ] 系统可恢复性达标

---

## 📦 Phase 5: 优化与完善 (Week 6)

### 目标
完成Docker沙盒、性能优化和文档完善。

### 任务分解

#### Week 6, Day 1-2: Docker沙盒 (可选)
- [ ] 研究OpenHands Runtime
- [ ] 实现Docker客户端
- [ ] 集成到Agent执行

**交付物**:
- `infrastructure/sandbox/client.py`
- `infrastructure/sandbox/runtime.py`

#### Week 6, Day 3: 性能优化
- [ ] 消息处理优化
- [ ] 内存管理优化
- [ ] 存储优化

**交付物**:
- 性能优化报告

#### Week 6, Day 4: 测试完善
- [ ] 单元测试覆盖
- [ ] 集成测试
- [ ] 端到端测试

**交付物**:
- 测试报告

#### Week 6, Day 5: 文档完善
- [ ] 更新架构文档
- [ ] 编写用户指南
- [ ] 编写开发指南

**交付物**:
- `docs/v3_migration_guide.md`
- `docs/api_reference.md`

---

## 🎯 里程碑汇总

| 阶段 | 时间 | 核心目标 | 验收标准 |
|:---:|:---:|:---|:---|
| **Phase 1** | Week 1-2 | 消息系统 | 消息通信正常，1000 msg/s，向后兼容 |
| **Phase 2** | Week 3 | SOP引擎 | 可定义/执行工作流，支持并行 |
| **Phase 3** | Week 4 | Agent重构 | Agent基于消息通信，角色定义清晰 |
| **Phase 4** | Week 5 | 增强功能 | 事件追踪，检查点恢复，记忆自动提取 |
| **Phase 5** | Week 6 | 优化完善 | Docker沙盒(可选)，性能达标，文档完善 |

---

## ⚙️ 特性开关配置

```yaml
# config/system.yaml
version: "3.0"

features:
  # Phase 1
  message_bus:
    enabled: true
    persistence: true
    max_queue_size: 10000
  
  # Phase 2
  sop_engine:
    enabled: true
    default_workflow: "code_development"
    max_parallel_steps: 5
  
  # Phase 3
  agent_v3:
    enabled: true
    roles:
      - product_manager
      - architect
      - coder
      - reviewer
      - reflector
      - evolution
  
  # Phase 4
  event_store:
    enabled: true
    retention_days: 30
  
  checkpoint:
    enabled: true
    auto_checkpoint: true
    interval_minutes: 10
  
  # Phase 5
  sandbox:
    enabled: false  # 默认关闭，按需启用
    docker_host: "unix:///var/run/docker.sock"

# 向后兼容
compat:
  v2_api: true  # 保持v2 API可用
  migration_mode: "gradual"  # gradual | immediate
```

---

## 🔄 回滚策略

### 每个阶段的回滚方案

#### Phase 1 回滚
```python
# 如果消息系统有问题，回退到直接调用
if not features.message_bus.enabled:
    # 使用v2.x的调用方式
    return v2_adapter.call_agent(agent_id, task)
```

#### Phase 2 回滚
```python
# 如果SOP引擎有问题，使用简单顺序执行
if not features.sop_engine.enabled:
    # 顺序执行步骤
    for step in workflow.steps:
        result = execute_step(step)
```

#### Phase 3 回滚
```python
# 如果Agent v3有问题，使用v2 Agent
if not features.agent_v3.enabled:
    return v2_agents[agent_id].execute(task)
```

---

## 📊 成功指标

### 技术指标
- [ ] 消息吞吐量 >= 1000 msg/s
- [ ] P99延迟 <= 100ms
- [ ] 内存占用 <= 2GB
- [ ] 测试覆盖率 >= 80%

### 功能指标
- [ ] 完整工作流可执行
- [ ] 多Agent协作正常
- [ ] 事件可追踪
- [ ] 状态可恢复

### 业务指标
- [ ] 任务完成时间减少20%
- [ ] 错误率降低50%
- [ ] 用户体验评分 >= 4.0/5.0

---

## 📝 任务追踪

| ID | 任务 | 阶段 | 负责人 | 状态 | 截止日期 |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1.1 | Message模型设计 | P1 | wdai | ⏳ 待开始 | Week 1 Day 2 |
| 1.2 | MessagePool实现 | P1 | wdai | ⏳ 待开始 | Week 1 Day 2 |
| 1.3 | Pub/Sub Router | P1 | wdai | ⏳ 待开始 | Week 1 Day 4 |
| 1.4 | 系统集成 | P1 | wdai | ⏳ 待开始 | Week 2 Day 3 |
| 2.1 | Workflow DSL | P2 | wdai | ⏳ 待开始 | Week 3 Day 1 |
| 2.2 | Orchestrator | P2 | wdai | ⏳ 待开始 | Week 3 Day 3 |
| 3.1 | 角色定义 | P3 | wdai | ⏳ 待开始 | Week 4 Day 1 |
| 3.2 | Agent重构 | P3 | wdai | ⏳ 待开始 | Week 4 Day 4 |
| 4.1 | Event Store | P4 | wdai | ⏳ 待开始 | Week 5 Day 1 |
| 4.2 | Checkpoint | P4 | wdai | ⏳ 待开始 | Week 5 Day 2 |
| 5.1 | Docker沙盒 | P5 | wdai | ⏳ 待开始 | Week 6 Day 2 |
| 5.2 | 文档完善 | P5 | wdai | ⏳ 待开始 | Week 6 Day 5 |

---

*Implementation Plan - wdai v3.0*
