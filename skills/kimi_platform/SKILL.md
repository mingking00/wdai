# Kimi Multi-Agent Platform Skill

OpenClaw集成Kimi多智能体平台

## 功能

- 工作流编排 (DAG执行引擎)
- 多智能体协作 (Perceive-Think-Act)
- 三层记忆系统 (短期/长期/语义)
- 13个内置工具

## 使用

### 快速集成接口

```python
from skills.kimi_platform.integration import (
    quick_research, quick_calculate, 
    quick_workflow, quick_remember, quick_recall
)

# 快速研究
result = quick_research("AI trends")

# 快速计算
result = quick_calculate("100 + 200")

# 快速工作流
result = quick_workflow([
    {"name": "step1", "handler": lambda ctx, cfg: "done"}
])

# 快速记忆
quick_remember("Important fact", importance="high")

# 快速回忆
results = quick_recall("programming")
```

### 完整API

```python
from skills.kimi_platform import (
    create_workflow, run_workflow,
    create_agent, create_orchestrator,
    create_memory_manager,
    get_all_tools
)
```

## 架构

基于GitHub优秀项目架构学习:
- 工作流引擎: n8n模式 (DAG执行)
- Agent系统: Dify模式 (编排器+工具)
- 记忆系统: Mem0模式 (三层记忆)

## 文件结构

```
kimi_platform/
├── __init__.py        # 核心API导出
├── integration.py     # 快速集成接口
└── SKILL.md          # 技能文档
```

实际代码位于: `kimi-platform/src/`
