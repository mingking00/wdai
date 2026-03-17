# 通用原则执行框架 - 快速参考卡

## 启动时自动执行

```python
import sys
sys.path.insert(0, '.claw-status')
from init_universal_principles import initialize_universal_principles

# 初始化
success, summary = initialize_universal_principles(agent_id="main")
# 输出: 🔥 通用原则执行系统已激活
```

## 常用命令

```bash
# 查看系统状态
python3 .claw-status/init_universal_principles.py

# 检查方法是否锁定
python3 .claw-status/init_universal_principles.py --check METHOD --task-type TYPE

# 查看特定Agent
python3 .claw-status/init_universal_principles.py --agent AGENT_ID
```

## 快速代码片段

### 检查方法状态
```python
from init_universal_principles import check_method_status

status = check_method_status("github_api", "deploy")
if status["locked"]:
    print("必须换方法！")
```

### 记录执行结果
```python
from init_universal_principles import record_attempt

# 成功
record_attempt("method", success=True, task_type="code")

# 失败 - 自动计数，3次后触发创新
result = record_attempt("method", success=False, task_type="code", error="timeout")
if result["status"] == "MUST_INNOVATE":
    print(f"换方法！建议: {result['alternatives']}")
```

### 完整工作流
```python
from universal_principle_engine import get_engine

engine = get_engine("my_agent")

# 1. 任务前
engine.pre_task_check("任务描述")

# 2. 执行中
result = engine.record_method_attempt("method", success=False)
if result["status"] == "MUST_INNOVATE":
    # 强制换路！
    pass

# 3. 交付前
engine.pre_delivery_check(output)
```

## 原则优先级速查

```
P0: 安全与伦理 (∞)        - 所有任务
P1: 创新(100) > 认知(90) > 第一性(80)  - CODE/RESEARCH/ANALYZE
P2: 复用(50) > 简单(45) > 验证(40)   - 所有任务
P3: 现实(20) > 学习(15)            - DEPLOY/DATA/COMM
P4: 用户偏好(5)              - WRITE/COMM
```

## 任务类型

| 关键词 | 类型 |
|--------|------|
| 代码、deploy、build | CODE |
| 研究、分析、search | RESEARCH |
| 写、doc、report | WRITE |
| CSV、JSON、数据 | DATA |
| 部署、upload、server | DEPLOY |
| 消息、发送、通知 | COMMUNICATE |
| 创建、设计、画 | CREATE |

## 状态文件

```
.claw-status/
├── universal_principles_{agent_id}.json  # Agent状态
├── innovation_state.json                 # 旧版兼容
└── principle_state.json                  # 旧版兼容
```

## 故障排除

```bash
# 重置所有状态
rm .claw-status/universal_principles_*.json

# 查看详细日志
python3 -c "
import sys
sys.path.insert(0, '.claw-status')
from universal_principle_engine import get_engine
engine = get_engine('default')
print(engine.get_summary())
"
```

---

*Keep this card handy!*
