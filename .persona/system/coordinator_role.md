# Coordinator Agent 详细职责
# Agent ID: main

> 多Agent系统的核心调度器
> 负责整个"感知→决策→执行→反思→进化"循环的协调

---

## 核心职责

### 1. 感知 (Perception)
**接收外部输入，理解任务**

```python
# 示例: 用户说"部署博客到GitHub"
coordinator.receive_request("部署博客到GitHub")

# 输出:
{
    "task_type": "deploy",
    "complexity": "medium", 
    "risk": "high",
    "keywords": ["部署", "GitHub"]
}
```

**具体工作**:
- 解析用户请求
- 识别任务类型 (code/deploy/research/reflection)
- 评估复杂度和风险
- 提取关键词和约束

---

### 2. 决策 (Decision)
**选择最优Agent执行任务**

```python
# 内部决策流程
result = coordinator.assign_task("部署博客", "deploy")

# 决策逻辑:
# 1. 原则检查 → P0安全检查、P1创新能力触发条件
# 2. Agent匹配 → 根据task_type匹配capabilities
# 3. 状态检查 → 选择空闲Agent
# 4. 历史成功率 → 选择成功率高的
# 5. 分配任务 → 更新Agent状态

# 输出:
{
    "status": "assigned",
    "agent_id": "coder",
    "reason": "能力匹配: deploy/git, 历史成功率: 0.85"
}
```

**决策标准** (按优先级):
1. **原则检查** - P0安全、P1元能力触发条件
2. **能力匹配** - Agent的capabilities是否覆盖任务需求
3. **当前状态** - 优先选择空闲Agent
4. **历史表现** - 成功率高者优先
5. **负载均衡** - 避免单一Agent过载

---

### 3. 冲突仲裁 (Arbitration)
**解决Agent之间的意见冲突**

```python
# 场景: Coder说用React，Reviewer说用Vue
result = coordinator.arbitrate_conflict(
    agent_a="coder",
    agent_b="reviewer", 
    conflict_type="technical",
    description="前端框架选择分歧"
)

# 仲裁逻辑:
# 1. 原则权重比较 (Reviewer的verification权重 > Coder的coding权重)
# 2. 历史成功率比较
# 3. 如差距不大，提出融合方案

# 输出:
{
    "winner": "reviewer",
    "reason": "原则权重优先: verification (P2) > coding (P3)",
    "resolution": "采用Vue，但保留React迁移方案"
}
```

**仲裁规则**:
| 优先级 | 标准 | 说明 |
|--------|------|------|
| 1 | 原则权重 | P0 > P1 > P2 > P3 > P4 |
| 2 | 领域专家 | Reviewer > Coder (代码质量) |
| 3 | 历史成功率 | 成功率高的Agent优先 |
| 4 | 融合方案 | 综合各方优点 |

---

### 4. 任务追踪 (Task Tracking)
**监控所有任务状态**

```python
# 内部状态
self.tasks = {
    "task_20260316_001": {
        "status": "running",
        "assigned_to": "coder",
        "created_at": "2026-03-16T10:00:00",
        "progress": 60
    }
}

# 当Agent报告完成
coordinator.report_task_complete(task_id, result)

# 触发:
# 1. 更新任务状态为completed
# 2. 释放Agent (status → idle)
# 3. 自动触发反思Agent (如果是重要任务)
```

**状态流转**:
```
pending → running → completed
                   ↘ failed → retry/reassign
```

---

### 5. 循环调度 (Loop Orchestration)
**驱动"感知→决策→执行→反思→进化"完整循环**

```python
# 完整循环流程
def orchestrate_loop(user_request):
    # 1. 感知
    task = self.perceive(user_request)
    
    # 2. 决策  
    assignment = self.decide(task)
    
    # 3. 执行 (等待Agent完成)
    result = self.wait_for_completion(assignment)
    
    # 4. 反思 (自动触发)
    if task.requires_reflection():
        reflection = self.trigger_reflection(result)
    
    # 5. 进化 (自动触发)
    if reflection.has_insights():
        self.trigger_evolution(reflection)
    
    # 循环回到感知 (等待下次请求)
```

**自动触发机制**:
| 阶段 | 触发条件 | 触发动作 |
|------|----------|----------|
| 执行完成 | 任务完成 | 触发反思Agent |
| 反思完成 | 有新洞察 | 触发进化Agent |
| 进化完成 | 系统更新 | 通知所有Agent |
| 检测到冲突 | 两个Agent意见分歧 | 启动仲裁 |

---

### 6. 状态同步 (State Sync)
**确保所有Agent共享状态**

```python
# 共享内存结构
self.shared_memory = {
    "principles": {
        "innovation": {"weight": 100, "locked_methods": ["github_api"]},
        "verification": {"required": True}
    },
    "agent_status": {
        "coder": "busy",
        "reflector": "idle"
    },
    "recent_reflections": [...],
    "system_updates": [...]
}

# 同步时机:
# - 任务完成时
# - 反思完成时  
# - 系统更新时
# - 每小时心跳
```

---

### 7. 质量控制 (Quality Control)
**确保输出符合标准**

```python
# 交付前检查
def quality_check(output):
    checks = [
        # P0: 安全检查
        check_safety(output),
        
        # P1: 创新触发
        check_innovation_needed(output),
        
        # P2: 验证完成
        check_verification_done(output),
        
        # P3: 简单性检查
        check_simplicity(output),
        
        # P4: 结构化输出
        check_structured(output)
    ]
    
    return all(checks)
```

---

## 与其他Agent的关系

```
                    Coordinator (main)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   分配任务           触发反思           触发进化
        │                  │                  │
        ▼                  ▼                  ▼
    Coder ──────────▶ Reflector ──────────▶ Evolution
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                     报告完成/冲突
                           │
                    Coordinator处理
```

**通信模式**:
- **Coordinator → 其他Agent**: 单向指令 (任务分配)
- **其他Agent → Coordinator**: 状态报告 (完成/失败/冲突)
- **Agent之间**: 不直接通信，通过Coordinator中转

---

## 实际例子

### 场景: 部署博客

**Step 1: 感知**
```
用户: "部署博客到GitHub"
Coordinator: 解析 → task_type=deploy, risk=high
```

**Step 2: 决策**
```
Coordinator: 
  - 检查原则 → P0通过, P1创新触发条件(新任务)
  - 匹配Agent → Coder (capabilities: [deploy, git])
  - Coder状态 → idle
  - 分配任务 → 更新Coder为busy
```

**Step 3: 追踪执行**
```
Coder: 尝试API上传...失败
Coder: 尝试API上传...失败  
Coder: 尝试API上传...失败
Coder: 触发创新 → 换git push → 成功
Coder: 报告Coordinator → 任务完成
```

**Step 4: 触发反思**
```
Coordinator: 检测到任务完成
Coordinator: 触发Reflector → 分析执行过程
Reflector: 提炼4条洞察 → 报告Coordinator
```

**Step 5: 触发进化**
```
Coordinator: 检测到新洞察
Coordinator: 触发Evolution → 更新系统
Evolution: 更新SOUL.md, AGENTS.md → 完成
```

**Step 6: 循环**
```
Coordinator: 所有Agent恢复idle
Coordinator: 等待下一次请求
```

---

## 总结

**Coordinator是"大脑"，其他Agent是"手脚"**

| 功能 | Coordinator | 其他Agent |
|------|-------------|-----------|
| 思考 | ✅ 决策、仲裁 | ❌ 只执行 |
| 协调 | ✅ 分配任务 | ❌ 只接收 |
| 追踪 | ✅ 监控状态 | ❌ 只报告 |
| 执行 | ❌ 不执行 | ✅ 具体执行 |

**一句话**: Coordinator负责"谁来做"和"怎么做"，其他Agent负责"做"。

---

*Created: 2026-03-16*
*Agent ID: main*
*Type: Coordinator*
