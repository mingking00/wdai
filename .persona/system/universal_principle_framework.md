# 通用原则执行框架 (UPEF)
# Universal Principle Enforcement Framework

> 适用于所有Agent、所有任务类型、所有场景的强制执行系统

---

## 核心特性

### 1. 多Agent支持
```python
# 为不同Agent创建独立实例
coordinator_engine = get_engine("coordinator")
coder_engine = get_engine("coder")
reviewer_engine = get_engine("reviewer")

# 每个Agent有自己的状态
# coordinator 不会受到 coder 的失败影响
```

### 2. 自动任务分类
```python
# 系统自动识别任务类型
tasks = [
    "部署博客"           → TaskType.DEPLOY
    "研究AI框架"         → TaskType.RESEARCH
    "写报告"            → TaskType.WRITE
    "分析CSV"           → TaskType.DATA
    "修复Bug"           → TaskType.CODE
    "发送消息"          → TaskType.COMMUNICATE
]
```

### 3. 上下文感知原则
```python
# 不同任务类型适用不同原则
code_task = [创新, 双路径认知, 已有能力优先, 简单优先, 检查验证]
research_task = [创新, 双路径认知, 已有能力优先, 纠错学习]
write_task = [第一性原理, 已有能力优先, 用户偏好匹配]
```

---

## 使用方式

### 方式1: 自动加载（推荐）

在每个Agent启动时自动执行：

```python
from init_universal_principles import initialize_universal_principles

# Agent启动
success, summary = initialize_universal_principles(agent_id="coder")
# 自动加载原则、恢复状态、显示锁定方法
```

### 方式2: 检查方法状态

```python
from init_universal_principles import check_method_status

# 尝试方法前检查
status = check_method_status("github_api", task_type="deploy")

if status["locked"]:
    print(f"方法已锁定！失败{status['failures']}次")
    print(f"建议替代: {status['alternatives']}")
    # 必须换方法！
else:
    # 可以执行
    execute_method()
```

### 方式3: 记录执行结果

```python
from init_universal_principles import record_attempt

# 方法执行后记录
try:
    result = execute_method()
    record_attempt("github_api", success=True, task_type="deploy")
except Exception as e:
    result = record_attempt("github_api", success=False, 
                           task_type="deploy", error=str(e))
    
    if result["status"] == "MUST_INNOVATE":
        # 强制创新触发！
        print(f"必须换方法！建议: {result['alternatives']}")
```

### 方式4: 完整手动控制

```python
from universal_principle_engine import get_engine

engine = get_engine("my_agent")

# 1. 任务前检查
result = engine.pre_task_check("部署应用到服务器")
if not result["approved"]:
    raise Exception("安全检查未通过")

# 2. 执行中记录
for attempt in range(1, 4):
    try:
        execute()
        engine.record_method_attempt("api_call", success=True)
        break
    except Exception as e:
        result = engine.record_method_attempt("api_call", success=False, error=str(e))
        if result["status"] == "MUST_INNOVATE":
            switch_to_git_push()  # 强制换路！

# 3. 交付前检查
if not engine.pre_delivery_check(output)["approved"]:
    fix_issues()
```

---

## 原则优先级（通用）

```
P0 (安全)          → 绝对优先，无条件执行
                    适用: 所有任务
                    
P1 (元能力)        → 创新(100) > 双路径认知(90) > 第一性原理(80)
                    适用: CODE, RESEARCH, ANALYZE, CREATE
                    
P2 (执行策略)      → 已有能力优先(50) > 简单优先(45) > 检查验证(40)
                    适用: 所有任务
                    
P3 (质量)          → 物理现实检查(20) > 纠错学习(15)
                    适用: DEPLOY, COMMUNICATE, DATA
                    
P4 (偏好)          → 用户偏好匹配(5)
                    适用: COMMUNICATE, WRITE
```

---

## 跨Agent协调

### 冲突仲裁

```python
# 当两个Agent建议冲突时
def arbitrate(agent_a_suggestion, agent_b_suggestion):
    # 获取各自的原则引擎
    engine_a = get_engine(agent_a)
    engine_b = get_engine(agent_b)
    
    # 基于原则权重决策
    winner = resolve_conflict(
        principles=["创新能力", "已有能力优先"],
        context={"task": current_task}
    )
    
    return winner
```

### 状态同步

```python
# 多Agent共享状态（可选）
def sync_agent_states():
    agents = initialize_all_agents()
    
    for agent_id in agents:
        engine = get_engine(agent_id)
        # 检查是否有方法被锁定
        # 广播给其他Agent
```

---

## 持久化与恢复

### 状态文件

每个Agent独立存储：
```
.claw-status/
├── universal_principles_default.json    # 默认Agent
├── universal_principles_coder.json      # 编码Agent
├── universal_principles_reviewer.json   # 审查Agent
└── innovation_state.json                # 旧版兼容
```

### 自动恢复

```python
# 会话重启后
engine = get_engine("coder")
# 自动从 universal_principles_coder.json 恢复：
# - 方法失败计数
# - 违规记录
# - 锁定状态
```

---

## 监控与告警

### 查看所有Agent状态

```bash
# 查看默认Agent
python3 .claw-status/init_universal_principles.py

# 查看特定Agent
python3 .claw-status/init_universal_principles.py --agent coder

# 检查方法是否锁定
python3 .claw-status/init_universal_principles.py \
    --check github_api \
    --task-type deploy
```

### 集成到HEARTBEAT.md

```python
def heartbeat_check():
    from init_universal_principles import initialize_universal_principles
    
    success, summary = initialize_universal_principles()
    
    if summary["locked_methods"]:
        alert(f"有{len(summary['locked_methods'])}个方法被锁定")
    
    if summary["total_violations"] > 10:
        alert(f"违规次数过多: {summary['total_violations']}")
```

---

## 实际场景

### 场景1: 编码Agent遇到API限制

```
CoderAgent: 调用OpenAI API
  → 第1次失败 → 记录
  → 第2次失败 → 记录  
  → 第3次失败 → 🚨 强制创新触发！
                → CoderEngine锁定"openai_api"
                → 建议: ["本地模型", "缓存结果", "降频请求"]
  → 切换到本地模型 → 成功
```

### 场景2: 协调Agent分配任务

```
CoordinatorAgent: 收到"开发博客系统"
  → pre_task_check()
  → 分解为子任务
  → 分配给 CoderAgent + ReviewerAgent
  
CoderAgent: 建议使用React
ReviewerAgent: 建议使用Vue

CoordinatorAgent:
  → resolve_conflict([创新能力, 已有能力优先])
  → 创新能力胜出（设计任务）
  → 提出第三方案: Svelte
```

### 场景3: 多轮对话保持状态

```
用户: "部署博客"
  → Agent记录: deploy:github_api 失败1次

用户: "再试一次"  
  → deploy:github_api 失败2次

用户: "再试一次"
  → deploy:github_api 失败3次 → 锁定！
  → Agent: "必须换方法，建议用git push"

用户: "好，用git push"
  → deploy:git_push 成功
  → 解锁github_api（可选）
```

---

## 扩展指南

### 添加新原则

```python
# 在 universal_principle_engine.py 中添加
self.principles.append(Principle(
    name="新原则",
    level=PriorityLevel.P2_STRATEGY,
    weight=35,
    description="描述",
    trigger="触发条件",
    applies_to=[TaskType.CODE, TaskType.DEPLOY]
))
```

### 添加新任务类型

```python
class TaskType(Enum):
    # 现有类型...
    NEW_TYPE = "new_type"  # 新类型
```

### 自定义检查函数

```python
def my_custom_check(task_description: str) -> bool:
    # 自定义检查逻辑
    return True

# 绑定到原则
principle.check_func = my_custom_check
```

---

## 与旧版兼容

旧版 `innovation_trigger.py` 和 `principle_engine.py` 仍然可用：

```python
# 旧版API（兼容）
from innovation_trigger import record_failure
from principle_engine import get_engine

# 新版API（推荐）
from init_universal_principles import record_attempt
from universal_principle_engine import get_engine
```

状态文件独立存储，互不干扰。

---

## 总结

**通用原则执行框架 =**
- ✅ 所有Agent（多实例隔离）
- ✅ 所有任务类型（自动分类）
- ✅ 所有场景（上下文感知）
- ✅ 自动持久化（重启恢复）
- ✅ 跨Agent协调（冲突仲裁）

**这就是"适用于所有情况"的执行系统。**

---

*Created: 2026-03-16*
*Status: Production Ready*
