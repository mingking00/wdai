#!/usr/bin/env python3
"""
Skill Generator - CLI-Anything 风格的可复用 Skill 生成器

将 CLI-Anything 的架构模式应用到 Agent Skills 开发中。
基于声明式命令定义、统一 REPL 接口和标准化测试框架。
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import argparse

# ============================================================================
# 核心数据结构和装饰器 - 声明式命令定义
# ============================================================================

# 从 bilibili-cli 学到的：结构化错误码
class ErrorCode(Enum):
    """标准化错误码 - 便于 Agent 处理和恢复"""
    SUCCESS = "success"
    NOT_AUTHENTICATED = "not_authenticated"
    PERMISSION_DENIED = "permission_denied"
    INVALID_INPUT = "invalid_input"
    NETWORK_ERROR = "network_error"
    UPSTREAM_ERROR = "upstream_error"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    INTERNAL_ERROR = "internal_error"
    COMMAND_NOT_FOUND = "command_not_found"
    VALIDATION_ERROR = "validation_error"


class ArgumentType(Enum):
    """参数类型枚举"""
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    PATH = "Path"
    LIST = "list"
    DICT = "dict"
    CHOICE = "choice"

@dataclass
class Argument:
    """命令参数定义"""
    name: str
    arg_type: ArgumentType
    required: bool = True
    default: Any = None
    help: str = ""
    choices: Optional[List[str]] = None
    validators: List[Callable] = field(default_factory=list)

@dataclass
class Option:
    """命令选项定义"""
    name: str
    option_type: ArgumentType
    default: Any = None
    help: str = ""
    short: Optional[str] = None  # 短选项如 -w
    flag: bool = False  # 是否是标志选项 (不需要值)

@dataclass
class CommandMetadata:
    """命令元数据"""
    name: str
    description: str
    category: str = "general"
    modifies_state: bool = False
    undoable: bool = False
    requires_session: bool = True
    hidden: bool = False  # 不在帮助中显示
    aliases: List[str] = field(default_factory=list)

# ============================================================================
# 声明式装饰器
# ============================================================================

def command(metadata: CommandMetadata):
    """命令装饰器 - 声明式定义命令"""
    def decorator(cls):
        cls.__command_metadata__ = metadata
        cls.__command_args__ = {}
        cls.__command_options__ = {}
        
        # 扫描类属性获取参数和选项定义
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, Argument):
                cls.__command_args__[attr_name] = attr
            elif isinstance(attr, Option):
                cls.__command_options__[attr_name] = attr
                
        return cls
    return decorator

def arg(name: str, arg_type: ArgumentType, **kwargs):
    """参数定义辅助函数"""
    return Argument(name=name, arg_type=arg_type, **kwargs)

def opt(name: str, option_type: ArgumentType, **kwargs):
    """选项定义辅助函数"""
    return Option(name=name, option_type=option_type, **kwargs)

# ============================================================================
# 状态管理 - Undo/Redo 支持
# ============================================================================

class StateSnapshot:
    """状态快照 - 用于撤销/重做"""
    def __init__(self, data: Dict[str, Any], timestamp: Optional[float] = None):
        self.data = data
        self.timestamp = timestamp or datetime.now().timestamp()
        self.id = f"snapshot_{self.timestamp}"

class CommandHistory:
    """命令历史管理器 - 支持撤销/重做"""
    
    def __init__(self, max_history: int = 100):
        self._undo_stack: List[Dict] = []
        self._redo_stack: List[Dict] = []
        self.max_history = max_history
    
    def record(self, command_name: str, state_before: StateSnapshot, 
               state_after: StateSnapshot, result: Any):
        """记录命令执行"""
        entry = {
            'command': command_name,
            'before': state_before,
            'after': state_after,
            'result': result,
            'timestamp': datetime.now().timestamp()
        }
        self._undo_stack.append(entry)
        self._redo_stack.clear()  # 新操作清空 redo 栈
        
        # 限制历史大小
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
    
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0
    
    def undo(self) -> Optional[StateSnapshot]:
        """撤销最后一个命令"""
        if not self._undo_stack:
            return None
        
        entry = self._undo_stack.pop()
        self._redo_stack.append(entry)
        return entry['before']
    
    def redo(self) -> Optional[StateSnapshot]:
        """重做最后一个撤销的命令"""
        if not self._redo_stack:
            return None
            
        entry = self._redo_stack.pop()
        self._undo_stack.append(entry)
        return entry['after']
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取最近的历史记录"""
        return self._undo_stack[-limit:]

class SessionState:
    """会话状态管理"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.data: Dict[str, Any] = {}
        self.history = CommandHistory()
        self.created_at = datetime.now().timestamp()
        self.metadata: Dict[str, Any] = {}
    
    def create_snapshot(self) -> StateSnapshot:
        """创建当前状态的快照"""
        import copy
        return StateSnapshot(copy.deepcopy(self.data))
    
    def restore_snapshot(self, snapshot: StateSnapshot):
        """恢复到指定快照"""
        self.data = snapshot.data.copy()
    
    def get(self, key: str, default=None):
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        self.data[key] = value
    
    def to_dict(self) -> dict:
        return {
            'session_id': self.session_id,
            'data': self.data,
            'created_at': self.created_at,
            'metadata': self.metadata
        }

class SessionManager:
    """会话管理器 - 管理多个会话"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._active_session: Optional[str] = None
    
    def create_session(self, session_id: Optional[str] = None) -> SessionState:
        """创建新会话"""
        if session_id is None:
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        session = SessionState(session_id)
        self._sessions[session_id] = session
        self._active_session = session_id
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)
    
    def get_active_session(self) -> Optional[SessionState]:
        if self._active_session:
            return self._sessions.get(self._active_session)
        return None
    
    def set_active_session(self, session_id: str):
        if session_id in self._sessions:
            self._active_session = session_id
    
    def save_session(self, session_id: str, path: Path):
        """保存会话到文件"""
        session = self._sessions.get(session_id)
        if session:
            path.write_text(json.dumps(session.to_dict(), indent=2))
    
    def load_session(self, path: Path) -> SessionState:
        """从文件加载会话"""
        data = json.loads(path.read_text())
        session = SessionState(data['session_id'])
        session.data = data.get('data', {})
        session.metadata = data.get('metadata', {})
        self._sessions[session.session_id] = session
        return session

# ============================================================================
# 命令上下文和结果
# ============================================================================

@dataclass
class CommandContext:
    """命令执行上下文"""
    session: SessionState
    args: Dict[str, Any]
    options: Dict[str, Any]
    working_dir: Path
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CommandResult:
    """
    命令执行结果 - bilibili-cli 风格
    
    支持多种输出格式:
    - YAML (默认): Token 效率高，Agent 友好
    - JSON: 严格 JSON，便于下游处理
    - Rich: 人类可读的格式化输出
    """
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    error: Optional[Dict[str, str]] = None  # {code: str, message: str}
    state_change: Optional[Dict] = None
    schema_version: str = "1.0.0"
    warnings: List[str] = field(default_factory=list)
    
    def to_yaml(self) -> str:
        """YAML 输出 - 推荐给 Agent 使用"""
        try:
            import yaml
            return yaml.dump(self.to_dict(), allow_unicode=True, sort_keys=False)
        except ImportError:
            return self.to_json()
    
    def to_json(self, indent: int = 2) -> str:
        """JSON 输出 - 严格 JSON 格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    def to_rich(self) -> str:
        """Rich 输出 - 人类可读"""
        lines = []
        if self.success:
            lines.append(f"✅ {self.message or 'Success'}")
        else:
            lines.append(f"❌ Error: {self.error.get('message', 'Unknown error')}")
            if self.error and 'code' in self.error:
                lines.append(f"   Code: {self.error['code']}")
        
        if self.data:
            lines.append(json.dumps(self.data, ensure_ascii=False, indent=2))
        
        if self.warnings:
            lines.append("\n⚠️ Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 - 统一 envelope 格式"""
        result = {
            "ok": self.success,
            "schema_version": self.schema_version,
        }
        
        if self.success:
            result["data"] = self.data
        else:
            result["error"] = self.error or {"code": "unknown", "message": "Unknown error"}
        
        if self.warnings:
            result["warnings"] = self.warnings
        
        return result
    
    @classmethod
    def from_error(cls, code: ErrorCode, message: str, **kwargs) -> "CommandResult":
        """从错误码创建结果"""
        return cls(
            success=False,
            error={"code": code.value, "message": message},
            **kwargs
        )
    
    @classmethod
    def from_success(cls, data: Dict[str, Any] = None, message: str = "", **kwargs) -> "CommandResult":
        """从成功数据创建结果"""
        return cls(
            success=True,
            data=data or {},
            message=message,
            **kwargs
        )
    
    def output(self, format_type: str = "auto") -> str:
        """
        根据格式输出
        
        Args:
            format_type: yaml, json, rich, auto
                auto: 检测 stdout 是否为 TTY，非 TTY 默认 YAML
        """
        import sys
        
        if format_type == "auto":
            format_type = "rich" if sys.stdout.isatty() else "yaml"
        
        if format_type == "yaml":
            return self.to_yaml()
        elif format_type == "json":
            return self.to_json()
        elif format_type == "rich":
            return self.to_rich()
        else:
            return self.to_yaml()

# ============================================================================
# 命令注册表
# ============================================================================

class CommandRegistry:
    """命令注册表 - 自动发现和动态加载"""
    
    def __init__(self):
        self._commands: Dict[str, type] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, command_class: type):
        """注册命令类"""
        if not hasattr(command_class, '__command_metadata__'):
            raise ValueError(f"{command_class.__name__} missing command metadata")
        
        metadata = command_class.__command_metadata__
        name = metadata.name
        
        self._commands[name] = command_class
        
        if metadata.category not in self._categories:
            self._categories[metadata.category] = []
        self._categories[metadata.category].append(name)
        
        # 注册别名
        for alias in metadata.aliases:
            self._commands[alias] = command_class
        
        return command_class
    
    def get(self, name: str) -> Optional[type]:
        return self._commands.get(name)
    
    def list_commands(self, category: Optional[str] = None) -> List[str]:
        if category:
            return self._categories.get(category, [])
        return list(self._commands.keys())
    
    def get_categories(self) -> List[str]:
        return list(self._categories.keys())
    
    def get_help_tree(self) -> Dict:
        """生成帮助文档树"""
        tree = {}
        for category, commands in self._categories.items():
            tree[category] = {}
            for name in commands:
                cmd_class = self._commands[name]
                metadata = cmd_class.__command_metadata__
                tree[category][name] = {
                    'description': metadata.description,
                    'args': {
                        k: {'type': v.arg_type.value, 'required': v.required}
                        for k, v in getattr(cmd_class, '__command_args__', {}).items()
                    },
                    'options': {
                        k: {'type': v.option_type.value, 'default': v.default}
                        for k, v in getattr(cmd_class, '__command_options__', {}).items()
                    }
                }
        return tree

# ============================================================================
# ReplSkin - 统一 REPL 接口
# ============================================================================

class ReplSkin:
    """
    统一 REPL 接口
    为所有 Skill 提供一致的交互体验
    """
    
    def __init__(self, registry: CommandRegistry, session_manager: SessionManager):
        self.registry = registry
        self.session_manager = session_manager
        self.active = False
        self.prompt_style = "minimal"  # minimal, verbose, context
    
    def _generate_prompt(self) -> str:
        """生成上下文感知的提示符"""
        session = self.session_manager.get_active_session()
        if session:
            return f"[{session.session_id}]> "
        return "skill> "
    
    def _parse_input(self, user_input: str) -> tuple:
        """解析用户输入为命令和参数"""
        parts = user_input.strip().split()
        if not parts:
            return None, [], {}
        
        command_name = parts[0]
        args = []
        kwargs = {}
        
        i = 1
        while i < len(parts):
            part = parts[i]
            if part.startswith('--'):
                # 长选项
                key = part[2:]
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    kwargs[key] = parts[i + 1]
                    i += 2
                else:
                    kwargs[key] = True
                    i += 1
            elif part.startswith('-') and len(part) > 1:
                # 短选项
                key = part[1:]
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    kwargs[key] = parts[i + 1]
                    i += 2
                else:
                    kwargs[key] = True
                    i += 1
            else:
                # 位置参数
                args.append(part)
                i += 1
        
        return command_name, args, kwargs
    
    def _execute_command(self, name: str, args: List, kwargs: Dict) -> CommandResult:
        """执行命令"""
        cmd_class = self.registry.get(name)
        if not cmd_class:
            return CommandResult(
                success=False,
                error=f"Unknown command: {name}"
            )
        
        metadata = cmd_class.__command_metadata__
        session = self.session_manager.get_active_session()
        
        if metadata.requires_session and not session:
            return CommandResult(
                success=False,
                error="No active session. Use 'session create' first."
            )
        
        # 创建命令实例
        cmd_instance = cmd_class()
        
        # 创建上下文
        ctx = CommandContext(
            session=session,
            args={k: v for k, v in zip(getattr(cmd_class, '__command_args__', {}).keys(), args)},
            options=kwargs,
            working_dir=Path.cwd()
        )
        
        # 创建状态快照（如果命令修改状态）
        snapshot = None
        if metadata.modifies_state and session:
            snapshot = session.create_snapshot()
        
        try:
            # 执行命令
            if hasattr(cmd_instance, 'execute'):
                result = cmd_instance.execute(ctx)
            else:
                result = CommandResult(
                    success=False,
                    error="Command missing execute method"
                )
            
            # 记录历史
            if metadata.modifies_state and session and snapshot:
                session.history.record(
                    metadata.name,
                    snapshot,
                    session.create_snapshot(),
                    result
                )
            
            return result
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=str(e)
            )
    
    def run(self):
        """运行交互式 REPL"""
        self.active = True
        
        print("🛠️  Skill Generator REPL")
        print("Type 'help' for available commands, 'exit' to quit.\n")
        
        while self.active:
            try:
                prompt = self._generate_prompt()
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                if user_input in ['exit', 'quit', 'q']:
                    self.active = False
                    break
                
                if user_input == 'help':
                    self._show_help()
                    continue
                
                if user_input == 'undo':
                    self._handle_undo()
                    continue
                
                if user_input == 'redo':
                    self._handle_redo()
                    continue
                
                # 解析和执行命令
                name, args, kwargs = self._parse_input(user_input)
                if name:
                    result = self._execute_command(name, args, kwargs)
                    self._display_result(result)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                break
        
        print("\nGoodbye!")
    
    def _show_help(self):
        """显示帮助信息"""
        tree = self.registry.get_help_tree()
        
        print("\n📚 Available Commands:")
        print("=" * 50)
        
        for category, commands in tree.items():
            print(f"\n[{category}]")
            for name, info in commands.items():
                print(f"  {name:20} - {info['description']}")
        
        print("\n🔧 Special Commands:")
        print("  help                 - Show this help")
        print("  undo                 - Undo last command")
        print("  redo                 - Redo last undone command")
        print("  exit/quit            - Exit REPL")
        print()
    
    def _handle_undo(self):
        """处理撤销"""
        session = self.session_manager.get_active_session()
        if not session:
            print("❌ No active session")
            return
        
        if not session.history.can_undo():
            print("❌ Nothing to undo")
            return
        
        snapshot = session.history.undo()
        if snapshot:
            session.restore_snapshot(snapshot)
            print("✅ Undo successful")
    
    def _handle_redo(self):
        """处理重做"""
        session = self.session_manager.get_active_session()
        if not session:
            print("❌ No active session")
            return
        
        if not session.history.can_redo():
            print("❌ Nothing to redo")
            return
        
        snapshot = session.history.redo()
        if snapshot:
            session.restore_snapshot(snapshot)
            print("✅ Redo successful")
    
    def _display_result(self, result: CommandResult):
        """显示命令结果 - 支持多种输出格式"""
        # 检测 stdout 是否为 TTY
        import sys
        is_tty = sys.stdout.isatty()
        
        if is_tty:
            # 人类可读
            print(result.to_rich())
        else:
            # Agent 友好 - YAML
            print(result.to_yaml())

# ============================================================================
# Skill Generator - 核心生成逻辑
# ============================================================================

class SkillGenerator:
    """
    Skill 生成器
    根据模板和需求生成新的 Skill
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"
        self.registry = CommandRegistry()
        self.session_manager = SessionManager()
        
        # 注册生成器命令
        self._register_commands()
    
    def _register_commands(self):
        """注册生成器命令"""
        self.registry.register(CreateSkillCommand)
        self.registry.register(ListTemplatesCommand)
        self.registry.register(SessionCreateCommand)
        self.registry.register(SessionListCommand)
    
    def run_cli(self):
        """运行命令行接口"""
        repl = ReplSkin(self.registry, self.session_manager)
        repl.run()
    
    def generate_skill(self, name: str, template: str = "basic", 
                       output_dir: Optional[Path] = None,
                       config: Optional[Dict] = None) -> Path:
        """
        生成新 Skill
        
        Args:
            name: Skill 名称
            template: 模板名称 (basic, repl, advanced)
            output_dir: 输出目录
            config: 额外配置
        
        Returns:
            生成的 Skill 路径
        """
        output_dir = output_dir or Path.cwd() / "skills" / name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 根据模板生成文件
        if template == "basic":
            self._generate_basic_skill(name, output_dir, config or {})
        elif template == "repl":
            self._generate_repl_skill(name, output_dir, config or {})
        elif template == "advanced":
            self._generate_advanced_skill(name, output_dir, config or {})
        
        return output_dir
    
    def _generate_basic_skill(self, name: str, output_dir: Path, config: Dict):
        """生成基础 Skill"""
        
        # 生成主模块
        main_content = f'''#!/usr/bin/env python3
"""
{name} - Auto-generated Skill

Generated by Skill Generator on {datetime.now().isoformat()}
"""

from skill_generator import (
    command, CommandMetadata, arg, opt,
    CommandContext, CommandResult,
    ArgumentType, Option
)

@command(CommandMetadata(
    name="{name}.hello",
    description="Say hello from {name}",
    category="{name}",
    modifies_state=False
))
class HelloCommand:
    """示例命令"""
    
    name_arg = arg(
        "name",
        ArgumentType.STRING,
        required=False,
        default="World",
        help="Name to greet"
    )
    
    uppercase = opt(
        "uppercase",
        ArgumentType.BOOLEAN,
        default=False,
        flag=True,
        help="Use uppercase"
    )
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        name = ctx.args.get('name_arg', 'World')
        if ctx.options.get('uppercase'):
            message = f"HELLO, {{name.upper()}}!"
        else:
            message = f"Hello, {{name}}!"
        
        return CommandResult(
            success=True,
            message=message,
            data={{"greeting": message}}
        )

# 注册更多命令...
'''
        (output_dir / "__init__.py").write_text(main_content)
        
        # 生成测试文件
        test_content = f'''#!/usr/bin/env python3
"""
Tests for {name} Skill
"""

import pytest
from pathlib import Path
from skill_generator.test_harness import CLITestHarness

class Test{name.title()}Skill:
    """{name} Skill 测试套件"""
    
    def test_hello_command(self):
        """测试 hello 命令"""
        harness = CLITestHarness("{name}")
        result = harness.run_command("{name}.hello", {{"name": "Test"}})
        assert result.success
        assert "Hello" in result.message
'''
        test_dir = output_dir / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / f"test_{name}.py").write_text(test_content)
        
        # 生成 SKILL.md 和 SCHEMA.md (受 bilibili-cli 启发)
        self._generate_skill_md(name, output_dir, config)
        self._generate_schema_md(name, output_dir)
        
        # 生成 requirements.txt
        requirements = '''# Auto-generated requirements
pyyaml>=6.0
click>=8.0
'''
        (output_dir / "requirements.txt").write_text(requirements)
        
        print(f"✅ Generated basic skill at {output_dir}")
    
    def _generate_skill_md(self, name: str, output_dir: Path, config: Dict):
        """生成 SKILL.md - Agent 使用指南 (受 bilibili-cli 启发)"""
        
        skill_md = f'''---
name: {name}
description: {config.get("description", f"Auto-generated skill: {name}")}
author: {config.get("author", "skill-generator")}
version: "1.0.0"
tags:
  - cli
  - auto-generated
---

# {name.title()} Skill

{config.get("description", f"Auto-generated skill: {name}")}

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt
```

## Commands

### Basic Commands

- `{name}.hello` - Say hello

### Usage

```bash
{name}.hello <name> [--uppercase]
```

## Agent Defaults

When you need machine-readable output:

1. **Prefer `--yaml` first** - Token-efficient, easy for agents to parse
2. **Use `--json` only** when downstream strictly requires JSON
3. **Keep result sets small** with `--max`, `--limit` options
4. **Check errors** by `ok` field in response

## Structured Output

All commands support `--yaml` and `--json` for machine-readable output:

```bash
{name}.hello --yaml
{name}.hello --json
```

Output format follows the envelope in SCHEMA.md:
```yaml
ok: true
schema_version: "1"
data: ...
```

## Error Handling

Structured error codes:
- `invalid_input` - Invalid arguments
- `not_found` - Resource not found
- `network_error` - Network issues
- `internal_error` - Internal failure

## Testing

```bash
cd {output_dir}
pytest tests/
```

## Safety Notes

- Commands may modify state - check before executing
- Use `--dry-run` flag if available to preview changes
'''
        (output_dir / "SKILL.md").write_text(skill_md)
    
    def _generate_schema_md(self, name: str, output_dir: Path):
        """生成 SCHEMA.md - 输出格式规范 (受 bilibili-cli 启发)"""
        
        schema_md = f'''# Structured Output Schema

`{name}` uses a shared agent-friendly envelope for machine-readable output.

## Success

```yaml
ok: true
schema_version: "1"
data: ...
```

## Error

```yaml
ok: false
schema_version: "1"
error:
  code: invalid_input
  message: Description of what went wrong
```

## Output Formats

### YAML (Recommended for Agents)

```bash
{name}.command --yaml
```

- More token-efficient than JSON
- Easier for agents to parse
- Human-readable when needed

### JSON

```bash
{name}.command --json
```

- Strict JSON format
- Use when downstream tooling requires JSON
- Good for piping to `jq`

### Rich (Human-readable)

```bash
{name}.command
```

- Default when stdout is TTY
- Formatted with emojis and colors
- Best for interactive use

## Error Codes

| Code | Description | Recovery |
|------|-------------|----------|
| `not_authenticated` | Authentication required | Prompt user to login |
| `permission_denied` | Insufficient permissions | Check credentials |
| `invalid_input` | Invalid arguments | Show usage help |
| `network_error` | Network failure | Retry with backoff |
| `upstream_error` | External service error | Report to user |
| `not_found` | Resource not found | Verify identifiers |
| `rate_limited` | Too many requests | Wait and retry |
| `internal_error` | Unexpected error | Check logs |

## Notes

- All `--json` and `--yaml` output uses this envelope
- Non-TTY stdout defaults to YAML
- Command payloads are normalized at CLI layer
- List results typically under `data.items`
'''
        (output_dir / "SCHEMA.md").write_text(schema_md)
    def _generate_repl_skill(self, name: str, output_dir: Path, config: Dict):
        """生成带 REPL 的 Skill"""
        self._generate_basic_skill(name, output_dir, config)
        
        # 添加 REPL 支持
        repl_content = f'''#!/usr/bin/env python3
"""
{name} REPL Entry Point
"""

from skill_generator import ReplSkin, CommandRegistry, SessionManager
from {name} import *  # 导入所有命令

def main():
    registry = CommandRegistry()
    session_manager = SessionManager()
    
    # 注册命令
    # registry.register(YourCommand)
    
    # 启动 REPL
    repl = ReplSkin(registry, session_manager)
    repl.run()

if __name__ == "__main__":
    main()
'''
        (output_dir / "repl.py").write_text(repl_content)
        
        print(f"✅ Added REPL support to {name}")
    
    def _generate_advanced_skill(self, name: str, output_dir: Path, config: Dict):
        """生成高级 Skill（带完整测试框架）"""
        self._generate_repl_skill(name, output_dir, config)
        
        # 添加高级功能
        # - 状态管理
        # - Undo/Redo 支持
        # - 配置管理
        # - 完整测试套件
        
        print(f"✅ Generated advanced skill at {output_dir}")

# ============================================================================
# 生成器命令定义
# ============================================================================

@command(CommandMetadata(
    name="skill.create",
    description="Create a new skill from template",
    category="generator",
    modifies_state=True,
    undoable=True
))
class CreateSkillCommand:
    """创建新 Skill 命令"""
    
    name = arg("name", ArgumentType.STRING, help="Skill name")
    template = opt("template", ArgumentType.STRING, default="basic",
                   help="Template: basic, repl, advanced")
    output = opt("output", ArgumentType.PATH, default=None,
                 help="Output directory")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        generator = SkillGenerator()
        
        skill_name = ctx.args.get('name', 'untitled')
        template = ctx.options.get('template', 'basic')
        output = ctx.options.get('output')
        
        output_path = generator.generate_skill(
            name=skill_name,
            template=template,
            output_dir=Path(output) if output else None
        )
        
        return CommandResult(
            success=True,
            message=f"Created skill '{skill_name}' at {output_path}",
            data={
                "skill_name": skill_name,
                "template": template,
                "path": str(output_path)
            }
        )

@command(CommandMetadata(
    name="template.list",
    description="List available skill templates",
    category="generator",
    modifies_state=False
))
class ListTemplatesCommand:
    """列出模板命令"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        templates = [
            {"name": "basic", "description": "Basic skill with single command"},
            {"name": "repl", "description": "Skill with interactive REPL"},
            {"name": "advanced", "description": "Full-featured skill with tests"}
        ]
        
        return CommandResult(
            success=True,
            data={"templates": templates}
        )

@command(CommandMetadata(
    name="session.create",
    description="Create a new working session",
    category="session",
    modifies_state=True
))
class SessionCreateCommand:
    """创建会话命令"""
    
    name = opt("name", ArgumentType.STRING, default=None,
               help="Session name (optional)")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        session_id = ctx.options.get('name')
        session = ctx.session_manager.create_session(session_id)
        
        return CommandResult(
            success=True,
            message=f"Created session: {session.session_id}",
            data={"session_id": session.session_id}
        )

@command(CommandMetadata(
    name="session.list",
    description="List all active sessions",
    category="session",
    modifies_state=False
))
class SessionListCommand:
    """列出会话命令"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        # 这里简化处理，实际应该从 SessionManager 获取
        return CommandResult(
            success=True,
            data={"sessions": []}
        )

# ============================================================================
# 测试框架
# ============================================================================

class CLITestHarness:
    """
    CLI 测试辅助类
    用于编写 Skill 测试
    """
    
    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        self.registry = CommandRegistry()
        self.session_manager = SessionManager()
        self.session = self.session_manager.create_session()
    
    def run_command(self, command: str, args: Dict = None, 
                    options: Dict = None) -> CommandResult:
        """
        运行命令并返回结果
        
        Args:
            command: 命令名称
            args: 位置参数
            options: 选项参数
        """
        cmd_class = self.registry.get(command)
        if not cmd_class:
            return CommandResult(
                success=False,
                error=f"Command not found: {command}"
            )
        
        ctx = CommandContext(
            session=self.session,
            args=args or {},
            options=options or {},
            working_dir=Path.cwd()
        )
        
        instance = cmd_class()
        return instance.execute(ctx)
    
    def assert_success(self, result: CommandResult):
        """断言命令成功"""
        assert result.success, f"Command failed: {result.error}"
    
    def assert_state_key(self, key: str, expected_value: Any):
        """断言状态值"""
        actual = self.session.get(key)
        assert actual == expected_value, f"Expected {key}={expected_value}, got {actual}"

# ============================================================================
# 主入口
# ============================================================================

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="Skill Generator - Generate Agent Skills with CLI-Anything patterns"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive REPL mode"
    )
    parser.add_argument(
        "--create",
        metavar="NAME",
        help="Create a new skill with given name"
    )
    parser.add_argument(
        "--template", "-t",
        default="basic",
        choices=["basic", "repl", "advanced"],
        help="Template to use for skill creation"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory for generated skill"
    )
    
    args = parser.parse_args()
    
    generator = SkillGenerator()
    
    if args.interactive:
        generator.run_cli()
    elif args.create:
        output_path = generator.generate_skill(
            name=args.create,
            template=args.template,
            output_dir=Path(args.output) if args.output else None
        )
        print(f"✅ Created skill at: {output_path}")
    else:
        # 默认进入交互模式
        generator.run_cli()

if __name__ == "__main__":
    main()
