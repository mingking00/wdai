# Unified Workflow System - 三层工作流集成
## Mitchell + GSD + Infinite Tasks

**版本**: 1.0  
**创建时间**: 2026-03-13  
**核心理念**: 结合结构化规划与无限灵活性

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        UNIFIED WORKFLOW SYSTEM                          │
│              (Mitchell + GSD + Infinite Tasks Fusion)                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: MITCHELL METHODOLOGY (High-level Guidance)                     │
│ ─────────────────────────────────────────────────                       │
│                                                                         │
│  🎯 Planning        → "Consult the oracle", create spec                 │
│  🔬 Prototyping     → Quick exploration, use AI as muse                 │
│  🧹 Cleanup         → Anti-Slop, review every line                      │
│  👁️ Review          → Deep analysis, no code                            │
│  💡 Breakthrough    → Stop AI, manual research                          │
│                                                                         │
│  ↓ Guides GSD Phases                                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: GSD PHASE MANAGEMENT (Project Structure)                       │
│ ─────────────────────────────────────────────────                       │
│                                                                         │
│  Phase 1: Planning & Architecture                                       │
│     ├─ Planning Session (Mitchell)                                      │
│     ├─ Discuss → Plan → Execute → Verify                                │
│     └─ Max 3 main tasks                                                 │
│                                                                         │
│  Phase 2: Core Implementation                                           │
│     ├─ Prototype → Cleanup → Review (Mitchell)                          │
│     ├─ Subagent execution (fresh context)                               │
│     └─ Max 3 main tasks                                                 │
│                                                                         │
│  Phase 3: Integration & Polish                                          │
│     ├─ Cleanup → Review (Mitchell)                                      │
│     ├─ Verify-work quality gates                                        │
│     └─ Max 3 main tasks                                                 │
│                                                                         │
│  ↓ Contains Infinite Tasks                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: INFINITE TASK SYSTEM (Daily Execution)                         │
│ ─────────────────────────────────────────────────                       │
│                                                                         │
│  📥 INBOX       [∞] Capture everything                                  │
│       ↓                                                                 │
│  📋 BACKLOG     [∞] Prioritized queue                                   │
│       ↓                                                                 │
│  ⭐ TODAY       [Dynamic] Smart selection                               │
│       ↓                                                                 │
│  🎯 PROGRESS    [Max 3] Deep focus                                      │
│       ↓                                                                 │
│  ⏳ WAITING     [∞] Blocked/External                                    │
│       ↓                                                                 │
│  ✅ DONE        [∞] Archive (keep stats)                                │
│                                                                         │
│  Each task linked to GSD Phase + Mitchell Session                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 工作流示例

### 场景: 开发新Skill

```
用户: 我要开发一个新的Skill

Layer 1 (Mitchell - 方法论指导):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Planning Session
   └─ Goal: 设计新Skill的架构
   └─ Output: spec.md (不编码)
   └─ Questions: 核心问题？约束？验证标准？

Layer 2 (GSD - 结构化项目):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. Create GSD Phase 1: "Design & Planning"
   └─ discuss-phase 1: 澄清需求
   └─ plan-phase 1: 创建3个任务
   └─ execute-phase 1: 并行执行
   └─ verify-phase 1: 质量检查

3. Create GSD Phase 2: "Implementation"  
   └─ discuss-phase 2
   └─ plan-phase 2
   └─ execute-phase 2
   └─ verify-phase 2

Layer 3 (Infinite Tasks - 日常执行):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. Capture Tasks (Infinite)
   ├─ "研究类似Skill的设计"
   ├─ "设计API接口"
   ├─ "实现核心逻辑"
   ├─ "添加测试"
   ├─ "编写文档"
   ├─ "Anti-Slop清理"
   └─ ... 无限添加

5. Smart Today (Algorithm)
   └─ 选择Top 5基于优先级+GSD Phase+年龄

6. Focus Mode (Max 3 Concurrent)
   ├─ Task 1: 🟢 IN_PROGRESS
   ├─ Task 2: 🟢 IN_PROGRESS  
   ├─ Task 3: 🟢 IN_PROGRESS
   └─ Queue: ⏳ ⏳ ⏳ (等待)

7. Mitchell Cleanup Session
   └─ Anti-Slop: 重构AI生成的代码
   └─ 添加文档
   └─ 确保理解每一行
```

---

## 🔗 集成点详解

### 集成点 1: Mitchell → GSD

```python
# Mitchell Session 指导 GSD Phase
mitchell_session = {
    "type": "planning",
    "goal": "设计架构",
    "output": "spec.md"
}

# GSD Phase 引用 Mitchell Session
gsd_phase = {
    "phase_num": 1,
    "planning_session_ref": mitchell_session.id,
    "status": "planning"
}
```

**流程**:
1. Mitchell Planning → 创建 GSD Phase 1
2. Mitchell Cleanup → GSD Phase 1 Verification
3. Mitchell Review → GSD Phase transition decision

---

### 集成点 2: GSD → Infinite Tasks

```python
# GSD Phase 包含 Infinite Tasks
gsd_phase = {
    "phase_id": "phase-1",
    "title": "Design",
    "task_ids": ["task-001", "task-002", "task-003", ...]  # 无限
}

# Task 关联 GSD Phase
task = {
    "id": "task-001",
    "title": "研究设计模式",
    "gsd_phase_id": "phase-1",
    "status": "inbox"
}
```

**规则**:
- GSD Phase 最多3个**主要**任务
- Infinite Task System 管理**所有**任务
- Smart Today 优先选择当前GSD Phase的任务

---

### 集成点 3: Mitchell → Infinite Tasks

```python
# Task 可以引用 Mitchell Session
task = {
    "id": "task-001",
    "title": "重构代码",
    "mitchell_session_id": "cleanup-session-1",
    "session_type": "cleanup"  # Anti-Slop任务
}
```

**应用**:
- Anti-Slop Cleanup 是一个任务类型
- Review Session 生成待办任务列表
- Breakthrough Session 标记需要人工研究的任务

---

## 📊 数据模型关系

```
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│ Mitchell Session │         │   GSD Phase      │         │     Task         │
├──────────────────┤         ├──────────────────┤         ├──────────────────┤
│ id               │         │ id               │         │ id               │
│ type             │◄────────│ mitchell_session │         │ title            │
│ goal             │         │ phase_num        │◄────────│ gsd_phase_id     │
│ learnings        │         │ title            │         │ mitchell_session │
│ gsd_phase_ref    │────────►│ task_ids[]       │────────►│ status           │
└──────────────────┘         │ status           │         │ priority         │
                             └──────────────────┘         └──────────────────┘
```

---

## 🎮 使用场景

### 场景 1: 日常任务管理

```
用户: 我今天想做什么？

1. smart_today()
   └─ 算法从无限任务池选择Top 5
   └─ 考虑GSD Phase优先级 + Mitchell session类型

2. focus_mode()
   └─ 显示当前3个Focus任务
   └─ 显示所属的GSD Phase
   └─ 显示关联的Mitchell Session

3. complete(task_id)
   └─ 完成任务
   └─ 从Waiting Queue自动补充
```

### 场景 2: 新项目启动

```
用户: 开始一个新项目

1. create_project("Name", "Description")
   └─ 创建统一项目容器

2. start_planning("项目目标")
   └─ Mitchell Planning Session
   └─ 输出: spec.md

3. create_gsd_phase(1, "Phase 1", "目标")
   └─ 创建结构化阶段
   └─ 关联Planning Session

4. capture_task("任务1", gsd_phase_id="phase-1")
   capture_task("任务2", gsd_phase_id="phase-1")
   ...
   └─ 无限捕获任务

5. gsd_execute_phase("phase-1")
   └─ 并行执行3个主要任务
   └─ 每个子agent干净上下文

6. start_cleanup("Phase 1代码")
   └─ Mitchell Anti-Slop
   └─ 重构和文档

7. verify_phase("phase-1")
   └─ GSD质量门
   └─ Mitchell Review
```

### 场景 3: 复杂研究任务

```
用户: 深入研究Transformer架构

Layer 1:
  start_planning("Transformer研究")
  → 确定研究范围和方法

Layer 2:
  create_gsd_phase(1, "基础研究", "理解核心机制")
  create_gsd_phase(2, "论文阅读", "阅读关键论文")
  create_gsd_phase(3, "代码实现", "实现简化版")

Layer 3:
  capture_task("读Attention is All You Need")
  capture_task("理解Self-Attention机制")
  capture_task("学习Positional Encoding")
  capture_task("实现简单Transformer")
  capture_task("对比不同实现")
  ... (无限)

smart_today()
→ 选择Top 5任务，优先Phase 1

focus_mode()
→ 深度研究3个任务

start_breakthrough("遇到理解瓶颈")
→ 停止AI，人工研究
→ 记录突破到任务系统
```

---

## 💡 设计决策

### 决策 1: 为什么三层？

| 层级 | 解决的问题 | 类比 |
|------|-----------|------|
| Mitchell | 方法论指导 | 战略层 (CEO) |
| GSD | 项目结构化 | 战术层 (Manager) |
| Infinite Tasks | 日常执行 | 执行层 (Worker) |

### 决策 2: 为什么无限任务但限制Focus？

```
问题: 用户说有"无限任务"

方案:
- ✅ 可以无限捕获 (Inbox)
- ✅ 智能选择今天做什么 (Smart Today)
- ✅ 限制并发Focus (Max 3)

原因:
- 减少心理负担 (不用担心遗漏)
- 提高执行效率 (深度工作)
- 避免上下文切换 (限制并发)
```

### 决策 3: 如何防止Context Rot？

```
多层保护:
1. GSD: 每个任务独立子agent (200K clean context)
2. Mitchell: Cleanup session (定期重构)
3. Infinite: Focus limit (减少同时进行的任务)
```

---

## 📈 效果评估

### 定量指标

| 指标 | 目标 | 测量方法 |
|------|------|---------|
| Context Rot | 0 incidents | 监控任务执行质量 |
| 任务完成率 | >80% | Done / Total |
| Focus深度 | 平均Focus时间 >30min | 任务开始-完成时间 |
| Anti-Slop频率 | 1/session | Cleanup session计数 |

### 定性指标

- **用户反馈**: "比以前更有条理"
- **系统感知**: 能处理更复杂的长期项目
- **代码质量**: 定期Cleanup后的代码更易维护

---

## 🚀 下一步

1. **完善Unified Dashboard** - 实时可视化
2. **添加自动化** - Smart Today自动运行
3. **集成到Heartbeat** - 定期任务提醒
4. **用户偏好学习** - 优化算法参数

---

## 📚 参考

- Mitchell's 16-session methodology: `.learning/mitchell_16_sessions_analysis.md`
- GSD for Claude Code: `.learning/gsd-integration-plan.md`
- Infinite Task System: `.tools/infinite_task_system.py`

---

**文件**: `.tools/unified_workflow.py` (22KB)  
**状态**: ✅ 核心架构完成，可运行演示
