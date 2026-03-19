# 原则执行系统集成方案
# 从"文档"到"自动运行"

## 实施方案（3步走）

### 第一步：自动检查点（已部署）

**文件**: `.claw-status/principle_enforcer.py`

**使用方式1: 装饰器（推荐）**
```python
from principle_enforcer import enforce_principles

@enforce_principles
def deploy_to_github():
    """部署到GitHub - 自动插入所有检查点"""
    # 部署逻辑
    pass
```

**使用方式2: 手动调用（灵活控制）**
```python
from principle_enforcer import task_check, execution_check, failure_handler, success_handler, delivery_check

# 1. 任务启动前
task_check("部署博客")

# 2. 执行中检查
execution_check("github_api", attempt=1)

# 3. 失败处理
try:
    result = upload_file()
    success_handler("github_api", result)
except Exception as e:
    result = failure_handler("github_api", str(e))
    if result["status"] == "MUST_INNOVATE":
        # 强制换方法！
        use_git_push_instead()

# 4. 交付前检查
delivery_check(result)
```

---

### 第二步：集成到现有工具

**修改 `work_monitor.py`**
```python
from principle_enforcer import get_enforcer

enforcer = get_enforcer()

def start_task(name, steps=1):
    # 原有逻辑...
    
    # 新增：任务前原则检查
    enforcer.before_task(name)
```

**修改 `growth_check.py`**
```python
from principle_engine import get_engine

# 每日自检时增加违规分析
engine = get_engine()
analysis = engine.analyze_violations()

if analysis["total_violations"] > 0:
    print("⚠️ 发现原则违规，请查看 .claw-status/principle_state.json")
```

---

### 第三步：创建快捷命令

**添加命令到 `.bashrc` 或别名**
```bash
# 查看原则状态
alias principle-status="python3 ~/.openclaw/workspace/.claw-status/principle_engine.py"

# 查看创新触发器状态
alias innovation-status="python3 ~/.openclaw/workspace/.claw-status/innovation_trigger.py"

# 强制原则检查（手动触发）
alias principle-check="python3 -c 'from principle_enforcer import task_check; task_check(\"manual check\")'"
```

---

## 自动触发场景

### 场景1: 代码开发
```
用户: "帮我部署博客"

系统自动执行:
1. task_check("部署博客")
   ✓ 安全检查通过
   ✓ 双路径认知: System2（复杂任务）
   ✓ 已有能力优先: 查询memory/skills

2. 执行中: github_api_upload
   - 第1次失败 → 记录，重试
   - 第2次失败 → 记录，重试
   - 第3次失败 → 🚨 强制创新触发！
     "github_api已失败3次，必须换方法"
     建议: ["使用git push", "使用GitHub CLI", "手动上传"]

3. 自动切换: git_push
   - 成功！
   - 验证远程文件 ✓

4. delivery_check
   ✓ 验证完成
   ✓ 简单性检查
   ✓ 结构化检查

5. 报告: "部署完成（通过git push）"
```

### 场景2: 多Agent协作
```
协调者: 分解任务给Coder和Reviewer

Coder: "我认为用React"
Reviewer: "我认为用Vue更好"

协调者自动触发:
- resolve_principle_conflict(["创新能力", "已有能力优先"], context)
- 胜出: 创新能力 (设计任务)
- 决策: 提出第三方案 Svelte
```

---

## 监控仪表盘

**创建 `status_dashboard.py`**
```python
#!/usr/bin/env python3
"""原则执行状态仪表盘"""

import json
from datetime import datetime

def show_dashboard():
    print("=" * 60)
    print("📊 原则执行状态仪表盘")
    print("=" * 60)
    
    # 1. 创新触发器状态
    print("\n🔥 创新触发器状态:")
    try:
        with open(".claw-status/innovation_state.json") as f:
            state = json.load(f)
            for key, data in state.items():
                if data["count"] >= 3:
                    print(f"   🔒 {key}: 已锁定 ({data['count']}次失败)")
                else:
                    print(f"   ⚠️ {key}: {data['count']}次失败")
    except:
        print("   暂无失败记录")
    
    # 2. 原则违规
    print("\n⚠️ 原则违规记录:")
    try:
        with open(".claw-status/principle_state.json") as f:
            state = json.load(f)
            violations = state.get("violations", [])
            if violations:
                from collections import Counter
                counts = Counter([v["principle"] for v in violations])
                for principle, count in counts.most_common(5):
                    print(f"   {principle}: {count}次")
            else:
                print("   无违规记录 ✓")
    except:
        print("   暂无记录")
    
    # 3. 今日统计
    print("\n📈 今日执行统计:")
    # 这里可以集成work_monitor的数据
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    show_dashboard()
```

---

## 执行检查清单

**每个任务自动运行：**
- [ ] 任务启动: `task_check()`
- [ ] 方法尝试: `execution_check(method, attempt)`
- [ ] 失败处理: `failure_handler(method, error)` 或 `success_handler(method, output)`
- [ ] 交付前: `delivery_check(output)`

**每日自检运行：**
- [ ] `python3 .claw-status/principle_engine.py`
- [ ] `python3 .claw-status/innovation_trigger.py`
- [ ] `python3 status_dashboard.py` (新建)

**每周回顾：**
- [ ] 查看违规模式
- [ ] 调整原则权重（如需要）
- [ ] 更新执行策略

---

## 下一步行动

**立即可做：**
1. 测试集成器: `python3 .claw-status/principle_enforcer.py`
2. 创建仪表盘: `python3 status_dashboard.py`
3. 在下次任务中使用 `@enforce_principles` 装饰器

**本周完成：**
1. 修改 `work_monitor.py` 集成检查点
2. 修改 `growth_check.py` 增加违规分析
3. 在HEARTBEAT.md中添加原则状态检查

**持续优化：**
1. 收集执行数据
2. 调整权重和触发阈值
3. 自动化更多检查点

---

*这就是从"知道"到"做到"的完整路径。*
