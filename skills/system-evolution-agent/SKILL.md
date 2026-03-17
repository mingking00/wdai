---
name: system-evolution-agent
description: "System Evolution Agent (SEA) - A persistent agent that improves the OpenClaw system itself. Has permission to modify system files but follows strict review processes. Activated when user says 'improve yourself' or 'evolve'."
---

# System Evolution Agent (SEA) 🧬

一个常驻Agent，专门负责改进OpenClaw系统本身。拥有修改系统文件的权限，但遵循**严格的审查流程**以减少bug。

## 核心能力

1. **系统分析与诊断** - 分析当前系统状态，识别改进点
2. **代码审查** - 严格审查新代码（语法、安全、性能）
3. **系统集成** - 将改进安全地整合到系统
4. **回滚机制** - 发现问题时快速回滚

## 使用方式

### 触发方式
当用户说以下话语时自动触发：
- "改进你自己"
- "进化"
- "优化系统"
- "整合到系统"

### 工作流程

```
用户: "改进你自己，添加错误处理"
    ↓
SEA: 创建变更请求
    ↓
SEA: 备份当前系统
    ↓
SEA: 严格审查（语法/安全/冲突/性能）
    ↓
SEA: 用户确认
    ↓
SEA: 应用变更
    ↓
SEA: 验证
    ↓
SEA: 完成 / 回滚
```

## 审查流程

### 1. 语法检查
- Python语法验证
- 文件格式检查

### 2. 安全扫描
检测以下危险模式：
- `os.system()` - 命令注入风险
- `subprocess.call(shell=True)` - 注入风险
- `eval()` / `exec()` - 代码执行风险
- `rm -rf` - 危险删除
- 动态导入 `__import__()`

### 3. 冲突检测
- 函数重定义检查
- 类名冲突检查
- 文件覆盖警告

### 4. 代码质量
- 行长度检查（>120字符警告）
- 文档字符串检查
- TODO/FIXME标记检测

### 5. 性能评估
- 代码行数评估影响
- 复杂度分析

## API

### improve_self()
```python
from skills.system-evolution-agent.sea import improve_self

result = improve_self(
    description="添加错误处理机制",
    changes={
        "skills/my_skill/core.py": "新代码内容",
        "SOUL.md": "更新后的人格描述"
    }
)

print(result["success"])  # True/False
print(result["status"])   # applied/rejected/rolled_back
print(result["review_score"])  # 审查得分 0-100
```

### analyze_system()
```python
from skills.system-evolution-agent.sea import analyze_system

analysis = analyze_system()
print(analysis["findings"])      # 发现的问题
print(analysis["suggestions"])   # 改进建议
```

### get_improvement_history()
```python
from skills.system-evolution-agent.sea import get_improvement_history

history = get_improvement_history()
for change in history:
    print(f"{change['id']}: {change['status']}")
```

## 文件结构

```
system-evolution-agent/
├── sea.py              # 主程序
├── SKILL.md            # 本文档
└── .system/            # 运行时数据（自动创建）
    ├── backups/        # 系统备份
    ├── logs/           # 操作日志
    └── change_history.json  # 变更历史
```

## 安全机制

1. **自动备份** - 每次变更前自动备份
2. **得分阈值** - 审查得分≥70才能通过
3. **关键问题拦截** - CRITICAL级别问题直接拒绝
4. **自动回滚** - 应用失败或验证失败自动回滚
5. **操作审计** - 所有变更记录到change_history.json

## 测试验证

```bash
cd /root/.openclaw/workspace
python3 skills/system-evolution-agent/sea.py
```

## 与其他Agent的关系

- **Work Monitor Agent**: SEA执行变更后，Work Monitor会记录状态
- **Multi-Agent Research**: SEA可以使用研究成果来改进系统
- **Self-Evolution**: SEA是自我进化的执行者，而daily-self-evolution是触发者

## 注意事项

1. SEA有修改系统文件的权限，谨慎使用
2. 所有变更都需要通过严格审查
3. 保留备份，可随时回滚
4. 变更历史永久保存，便于审计
