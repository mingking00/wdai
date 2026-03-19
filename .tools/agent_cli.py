#!/usr/bin/env python3
"""
Agent CLI - 统一的 Agent Skills CLI 入口

整合所有重构后的 Skills：
- react: ReAct Agent 多步骤推理
- memory: 记忆上下文管理
- task: 任务分解规划
- search: 免费联网搜索

用法:
    python3 agent_cli.py [skill] [command] [args...]
    python3 agent_cli.py --interactive    # 进入 REPL 模式

示例:
    python3 agent_cli.py react run "分析代码" --tools read_file,execute
    python3 agent_cli.py memory add "重要决策" --importance 9
    python3 agent_cli.py task create "实现新功能" --depth deep
    python3 agent_cli.py search query "Python教程" --max-results 10
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# 确保能导入重构后的技能
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "refactored"))

# 导入核心框架
from skill_generator import (
    ReplSkin, CommandRegistry, SessionManager,
    CommandContext, CommandResult, ArgumentType,
    command, CommandMetadata, arg, opt
)

# 导入各技能
from refactored.react_agent_skill import (
    ReactRunCommand, ReactToolsCommand, ReactStatusCommand,
    ReactHistoryCommand, ReactResetCommand, ReActAgent
)
from refactored.memory_context_skill import (
    MemoryAddCommand, MemoryRetrieveCommand, MemoryContextCommand,
    MemorySummarizeCommand, MemoryArchiveCommand, MemoryStatsCommand,
    MemoryClearCommand
)
from refactored.task_decomp_skill import (
    TaskCreateCommand, TaskListCommand, TaskShowCommand,
    TaskUpdateCommand, TaskNextCommand, TaskDeleteCommand
)
from refactored.free_search_skill import (
    SearchQueryCommand, SearchBackendsCommand, SearchLastCommand,
    SearchStatsCommand, SearchClearCommand
)


# ============================================================================
# 全局会话管理命令
# ============================================================================

@command(CommandMetadata(
    name="session.create",
    description="创建新工作会话",
    category="session",
    modifies_state=True,
    requires_session=False
))
class SessionCreateCommand:
    """创建会话"""
    
    name = opt("name", ArgumentType.STRING, default=None, help="会话名称")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        name = ctx.options.get("name")
        session = ctx.session_manager.create_session(name)
        return CommandResult(
            success=True,
            message=f"创建会话: {session.session_id}",
            data={"session_id": session.session_id}
        )


@command(CommandMetadata(
    name="session.list",
    description="列出所有会话",
    category="session",
    modifies_state=False,
    requires_session=False
))
class SessionListCommand:
    """列出会话"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        # 从 session_manager 获取所有会话
        sessions = []
        for sid, session in ctx.session_manager._sessions.items():
            sessions.append({
                "id": sid,
                "created_at": session.created_at,
                "data_keys": list(session.data.keys()),
                "is_active": sid == ctx.session_manager._active_session
            })
        
        return CommandResult(
            success=True,
            data={"sessions": sessions, "count": len(sessions)}
        )


@command(CommandMetadata(
    name="session.switch",
    description="切换到指定会话",
    category="session",
    modifies_state=True,
    requires_session=False
))
class SessionSwitchCommand:
    """切换会话"""
    
    session_id = arg("session_id", ArgumentType.STRING, help="会话ID")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        sid = ctx.args.get("session_id", "")
        if sid in ctx.session_manager._sessions:
            ctx.session_manager.set_active_session(sid)
            return CommandResult(
                success=True,
                message=f"切换到会话: {sid}"
            )
        else:
            return CommandResult(
                success=False,
                error=f"未找到会话: {sid}"
            )


@command(CommandMetadata(
    name="session.save",
    description="保存会话到文件",
    category="session",
    modifies_state=False,
    requires_session=True
))
class SessionSaveCommand:
    """保存会话"""
    
    path = arg("path", ArgumentType.STRING, help="保存路径")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        save_path = Path(ctx.args.get("path", "session.json"))
        ctx.session_manager.save_session(ctx.session.session_id, save_path)
        return CommandResult(
            success=True,
            message=f"会话已保存到: {save_path}"
        )


@command(CommandMetadata(
    name="status",
    description="显示所有技能的状态概览",
    category="general",
    modifies_state=False,
    requires_session=True
))
class StatusCommand:
    """状态概览"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        session = ctx.session
        
        overview = {
            "session_id": session.session_id,
            "react": session.get("react", {}).get("status", "未初始化"),
            "memory_entries": len(session.get("memory", {}).get("entries", [])),
            "plans": len(session.get("plans", {})),
            "search_count": session.get("search", {}).get("search_count", 0)
        }
        
        return CommandResult(
            success=True,
            data=overview
        )


@command(CommandMetadata(
    name="skills",
    description="列出所有可用技能和命令",
    category="general",
    modifies_state=False,
    requires_session=False
))
class SkillsCommand:
    """技能列表"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        skills = {
            "react": {
                "description": "ReAct Agent 多步骤推理",
                "commands": ["react.run", "react.tools", "react.status", "react.history", "react.reset"]
            },
            "memory": {
                "description": "记忆上下文管理",
                "commands": ["memory.add", "memory.retrieve", "memory.context", 
                           "memory.summarize", "memory.archive", "memory.stats", "memory.clear"]
            },
            "task": {
                "description": "任务分解规划",
                "commands": ["task.create", "task.list", "task.show", 
                           "task.update", "task.next", "task.delete"]
            },
            "search": {
                "description": "免费联网搜索",
                "commands": ["search.query", "search.backends", "search.last", 
                           "search.stats", "search.clear"]
            },
            "session": {
                "description": "会话管理",
                "commands": ["session.create", "session.list", "session.switch", "session.save"]
            }
        }
        
        return CommandResult(
            success=True,
            data=skills
        )


# ============================================================================
# 全局注册表构建
# ============================================================================

def create_global_registry():
    """创建全局命令注册表"""
    registry = CommandRegistry()
    
    # 注册 ReAct 命令
    registry.register(ReactRunCommand)
    registry.register(ReactToolsCommand)
    registry.register(ReactStatusCommand)
    registry.register(ReactHistoryCommand)
    registry.register(ReactResetCommand)
    
    # 注册 Memory 命令
    registry.register(MemoryAddCommand)
    registry.register(MemoryRetrieveCommand)
    registry.register(MemoryContextCommand)
    registry.register(MemorySummarizeCommand)
    registry.register(MemoryArchiveCommand)
    registry.register(MemoryStatsCommand)
    registry.register(MemoryClearCommand)
    
    # 注册 Task 命令
    registry.register(TaskCreateCommand)
    registry.register(TaskListCommand)
    registry.register(TaskShowCommand)
    registry.register(TaskUpdateCommand)
    registry.register(TaskNextCommand)
    registry.register(TaskDeleteCommand)
    
    # 注册 Search 命令
    registry.register(SearchQueryCommand)
    registry.register(SearchBackendsCommand)
    registry.register(SearchLastCommand)
    registry.register(SearchStatsCommand)
    registry.register(SearchClearCommand)
    
    # 注册 Session 管理命令
    registry.register(SessionCreateCommand)
    registry.register(SessionListCommand)
    registry.register(SessionSwitchCommand)
    registry.register(SessionSaveCommand)
    
    # 注册通用命令
    registry.register(StatusCommand)
    registry.register(SkillsCommand)
    
    return registry


# ============================================================================
# CLI 解析和执行
# ============================================================================

def parse_cli_args(args: List[str]) -> tuple:
    """解析命令行参数"""
    if not args:
        return None, None, [], {}
    
    # 尝试识别命令模式
    # 模式1: agent_cli.py react run "task" --tools t1
    # 模式2: agent_cli.py --interactive
    
    if args[0] == "--interactive" or args[0] == "-i":
        return "interactive", None, [], {}
    
    # 解析命令
    skill = args[0] if len(args) > 0 else None
    command_name = args[1] if len(args) > 1 else None
    
    # 解析剩余参数
    pos_args = []
    kwargs = {}
    
    i = 2
    while i < len(args):
        part = args[i]
        if part.startswith("--"):
            key = part[2:]
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                kwargs[key] = args[i + 1]
                i += 2
            else:
                kwargs[key] = True
                i += 1
        elif part.startswith("-") and len(part) > 1:
            key = part[1:]
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                kwargs[key] = args[i + 1]
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            pos_args.append(part)
            i += 1
    
    return skill, command_name, pos_args, kwargs


def execute_command(registry: CommandRegistry, session_manager: SessionManager,
                   full_command: str, args: List[str], kwargs: Dict) -> CommandResult:
    """执行单个命令"""
    # 构建完整命令名
    cmd_class = registry.get(full_command)
    
    if not cmd_class:
        return CommandResult(
            success=False,
            error=f"未知命令: {full_command}"
        )
    
    metadata = cmd_class.__command_metadata__
    
    # 获取或创建会话
    if metadata.requires_session:
        session = session_manager.get_active_session()
        if not session:
            session = session_manager.create_session("default")
    else:
        session = session_manager.get_active_session()
    
    # 构建参数映射
    cmd_args = getattr(cmd_class, '__command_args__', {})
    cmd_options = getattr(cmd_class, '__command_options__', {})
    
    args_dict = {}
    for i, (arg_name, arg_def) in enumerate(cmd_args.items()):
        if i < len(args):
            args_dict[arg_name] = args[i]
    
    options_dict = kwargs.copy()
    
    ctx = CommandContext(
        session=session,
        args=args_dict,
        options=options_dict,
        working_dir=Path.cwd(),
        session_manager=session_manager
    )
    
    instance = cmd_class()
    return instance.execute(ctx)


# ============================================================================
# 主入口
# ============================================================================

def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Agent CLI - 统一的 Agent Skills CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --interactive                    # 进入交互式 REPL
  %(prog)s react run "分析代码" --tools read_file
  %(prog)s memory add "重要决策" --importance 9
  %(prog)s task create "实现功能" --depth deep
  %(prog)s search query "Python教程" --max-results 10
        """
    )
    
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="进入 REPL 交互模式")
    parser.add_argument("--version", action="version", version="Agent CLI 2.0")
    
    # 允许捕获所有剩余参数
    parser.add_argument("remainder", nargs=argparse.REMAINDER,
                        help="命令和参数 (skill command [args...])")
    
    args = parser.parse_args()
    
    # 创建全局组件
    registry = create_global_registry()
    session_manager = SessionManager()
    
    if args.interactive or not args.remainder:
        # REPL 模式
        print("=" * 60)
        print("🚀 Agent CLI - 统一的 Agent Skills")
        print("=" * 60)
        print("\n可用技能:")
        print("  🤖 react  - ReAct Agent 多步骤推理")
        print("  🧠 memory - 记忆上下文管理")
        print("  📋 task   - 任务分解规划")
        print("  🔍 search - 免费联网搜索")
        print("\n通用命令:")
        print("  session.create/list/switch - 会话管理")
        print("  status   - 查看状态概览")
        print("  skills   - 列出所有技能")
        print("  undo/redo - 撤销/重做")
        print("  help     - 显示帮助")
        print("  exit     - 退出")
        print("\n" + "=" * 60)
        print("输入 'session.create' 创建新会话开始工作")
        print("=" * 60 + "\n")
        
        repl = ReplSkin(registry, session_manager)
        repl.run()
    
    else:
        # 单命令模式
        skill, command, pos_args, kwargs = parse_cli_args(args.remainder)
        
        if not skill:
            parser.print_help()
            return
        
        # 构建完整命令名
        full_command = f"{skill}.{command}" if command else skill
        
        # 执行命令
        result = execute_command(registry, session_manager, full_command, pos_args, kwargs)
        
        if result.success:
            if result.data:
                print(json.dumps(result.data, indent=2, ensure_ascii=False))
            else:
                print(f"✅ {result.message}")
        else:
            print(f"❌ 错误: {result.error}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
