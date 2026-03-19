# Agent Skills - CLI-Anything 架构

## 概述

这是重构后的 Agent Skills 系统，采用 CLI-Anything 风格的统一架构。

## 架构特点

### 1. 声明式命令定义
- 使用 `@command` 装饰器定义命令
- 使用 `arg()` 和 `opt()` 定义参数
- 元数据驱动，自描述

### 2. 统一 REPL 接口 (ReplSkin)
- 所有技能共享一致的交互体验
- 自动参数解析
- 上下文感知提示符

### 3. 状态管理 (SessionManager)
- 多会话支持
- Undo/Redo 支持
- 持久化能力

### 4. 模块化设计
- 每个技能独立模块
- 通过注册表组合
- 易于扩展

## 文件结构

```
.tools/
├── agent_cli.py           # 统一 CLI 入口
├── skill_generator.py     # 核心框架和模板
├── README.md              # 本文档
├── refactored/            # 重构后的技能
│   ├── react_agent_skill.py
│   ├── memory_context_skill.py
│   ├── task_decomp_skill.py
│   └── free_search_skill.py
└── (原始技能文件作为备份)
```

## 快速开始

### 启动 REPL 模式

```bash
cd /root/.openclaw/workspace/.tools
python3 agent_cli.py --interactive
```

### 单命令模式

```bash
# ReAct Agent
python3 agent_cli.py react run "分析代码结构" --tools read_file,execute

# Memory
python3 agent_cli.py memory add "重要决策记录" --importance 9 --tags decision,important

# Task
python3 agent_cli.py task create "实现新功能" --depth deep

# Search
python3 agent_cli.py search query "Python教程" --max-results 10
```

## 命令参考

### ReAct Agent (react)
| 命令 | 描述 | 示例 |
|------|------|------|
| `react.run <task>` | 运行 ReAct 任务 | `react.run "分析代码" --tools search,read_file` |
| `react.tools` | 列出可用工具 | `react.tools` |
| `react.status` | 查看当前状态 | `react.status` |
| `react.history` | 查看执行历史 | `react.history --limit 10` |
| `react.reset` | 重置会话 | `react.reset` |

### Memory (memory)
| 命令 | 描述 | 示例 |
|------|------|------|
| `memory.add <content>` | 添加记忆条目 | `memory.add "重要决策" --importance 9` |
| `memory.retrieve <query>` | 检索记忆 | `memory.retrieve "决策" --top-k 5` |
| `memory.context <query>` | 获取上下文 | `memory.context "当前话题"` |
| `memory.summarize` | 总结当前记忆 | `memory.summarize` |
| `memory.archive` | 归档会话 | `memory.archive --name my_session` |
| `memory.stats` | 显示统计 | `memory.stats` |
| `memory.clear` | 清空记忆 | `memory.clear` |

### Task (task)
| 命令 | 描述 | 示例 |
|------|------|------|
| `task.create <desc>` | 创建执行计划 | `task.create "实现功能" --depth deep` |
| `task.list` | 列出所有计划 | `task.list --status in_progress` |
| `task.show <plan_id>` | 显示计划详情 | `task.show PLAN-20260312-123456` |
| `task.update <plan> <task> <status>` | 更新状态 | `task.update PLAN-xxx T01 completed` |
| `task.next <plan_id>` | 获取下一步任务 | `task.next PLAN-xxx --count 3` |
| `task.delete <plan_id>` | 删除计划 | `task.delete PLAN-xxx` |

### Search (search)
| 命令 | 描述 | 示例 |
|------|------|------|
| `search.query <query>` | 执行搜索 | `search.query "Python教程" --max-results 10` |
| `search.backends` | 列出搜索后端 | `search.backends` |
| `search.last` | 显示上次结果 | `search.last --format markdown` |
| `search.stats` | 显示统计 | `search.stats` |
| `search.clear` | 清除历史 | `search.clear` |

### Session 管理
| 命令 | 描述 | 示例 |
|------|------|------|
| `session.create` | 创建会话 | `session.create --name my_session` |
| `session.list` | 列出会话 | `session.list` |
| `session.switch <id>` | 切换会话 | `session.switch session_abc123` |
| `session.save <path>` | 保存会话 | `session.save my_session.json` |

### 通用命令
| 命令 | 描述 |
|------|------|
| `status` | 显示所有技能状态概览 |
| `skills` | 列出所有可用技能 |
| `undo` | 撤销上一步操作 |
| `redo` | 重做上一步撤销 |
| `help` | 显示帮助 |
| `exit` | 退出 REPL |

## REPL 使用示例

```
$ python3 agent_cli.py --interactive

============================================================
🚀 Agent CLI - 统一的 Agent Skills
============================================================

可用技能:
  🤖 react  - ReAct Agent 多步骤推理
  🧠 memory - 记忆上下文管理
  📋 task   - 任务分解规划
  🔍 search - 免费联网搜索

...

[session_abc123]> session.create --name my_project
✅ 创建会话: session_def456

[session_def456]> task.create "分析用户需求并设计API" --depth deep
✅ 创建计划: PLAN-20260312-154230
📋 执行计划: 分析用户需求并设计API
ID: PLAN-20260312-154230
状态: pending
预计耗时: 180 分钟
完成进度: 0/5

子任务列表:
------------------------------------------------------------
⏳ [T01] 🔴 需求理解
   预计: 15分钟
⏳ [T02] 🟠 信息收集
   预计: 30分钟 (依赖: T01)
...

[session_def456]> task.update PLAN-20260312-154230 T01 completed
✅ 已更新任务状态

[session_def456]> memory.add "决定使用 FastAPI 作为后端框架" --importance 8 --tags decision,api
✅ 已添加条目: a1b2c3d4

[session_def456]> react.run "根据记忆设计API结构" --tools recall,read_file
✅ ReAct 完成: 基于记忆中的重要决策，建议使用 FastAPI...

[session_def456]> undo
✅ Undo successful

[session_def456]> status
{
  "session_id": "session_def456",
  "react": "completed",
  "memory_entries": 1,
  "plans": 1,
  "search_count": 0
}

[session_def456]> exit
Goodbye!
```

## 开发新技能

使用 `skill_generator.py` 提供的模板创建新技能：

```python
from skill_generator import (
    command, CommandMetadata, arg, opt,
    CommandContext, CommandResult,
    ArgumentType
)

@command(CommandMetadata(
    name="my_skill.do_something",
    description="做某事",
    category="my_skill",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class DoSomethingCommand:
    param = arg("param", ArgumentType.STRING, help="参数")
    option = opt("option", ArgumentType.STRING, default="default", help="选项")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        # 实现逻辑
        return CommandResult(
            success=True,
            message="完成",
            data={}
        )
```

然后在 `agent_cli.py` 中注册命令：

```python
from refactored.my_skill import DoSomethingCommand
registry.register(DoSomethingCommand)
```

## 架构对比

| 特性 | 旧架构 | 新架构 (CLI-Anything) |
|------|--------|---------------------|
| 命令定义 | 手动解析 argparse | 声明式装饰器 |
| REPL | 每个技能独立 | 统一 ReplSkin |
| 状态管理 | 各自实现 | SessionManager |
| Undo/Redo | 不支持 | 内置支持 |
| 扩展性 | 难以组合 | 注册表组合 |
| 学习成本 | 每个技能不同 | 统一接口 |

## 依赖

- Python 3.8+
- skill_generator.py 提供核心框架
- 各技能的额外依赖（如 ddgs）

## 迁移指南

原始技能文件已保留在 `.tools/` 根目录作为备份。
重构后的版本位于 `.tools/refactored/`。

使用新架构的优势：
1. 统一的用户体验
2. 更好的状态管理
3. 支持撤销/重做
4. 更容易扩展和维护
