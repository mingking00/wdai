#!/usr/bin/env python3
"""
ReAct Agent Skill - CLI-Anything 风格重构
ReAct Agent 多步骤推理

用法: python3 react_agent_skill.py [进入REPL模式]
     或在 REPL 中使用: react.run <任务> [--tools t1,t2]
"""

import sys
import json
import re
import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

# 导入核心框架
sys.path.insert(0, str(Path(__file__).parent))
from skill_generator import (
    command, CommandMetadata, arg, opt,
    CommandContext, CommandResult,
    ArgumentType,
    ReplSkin, CommandRegistry, SessionManager, SessionState,
    StateSnapshot, CommandHistory
)

# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class AgentStep:
    """Agent执行步骤记录"""
    iteration: int
    thought: str
    action: str
    action_input: Dict
    observation: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReActSession:
    """ReAct 会话状态"""
    task: str = ""
    steps: List[AgentStep] = field(default_factory=list)
    max_iterations: int = 10
    available_tools: List[str] = field(default_factory=list)
    final_answer: str = ""
    status: str = "idle"  # idle, running, completed, failed


# ============================================================================
# 工具注册表
# ============================================================================

class ToolRegistry:
    """工具注册表 - 管理可用工具"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.tools: Dict[str, Dict] = {}
        self._register_default_tools()
        self._initialized = True
    
    def _register_default_tools(self):
        """注册默认工具"""
        self.register(
            name="search",
            description="搜索网络信息",
            func=self._search,
            parameters={"query": {"type": "string", "description": "搜索查询"}}
        )
        self.register(
            name="read_file",
            description="读取文件内容",
            func=self._read_file,
            parameters={"path": {"type": "string", "description": "文件路径"}}
        )
        self.register(
            name="execute",
            description="执行shell命令",
            func=self._execute,
            parameters={"command": {"type": "string", "description": "要执行的命令"}}
        )
        self.register(
            name="calculate",
            description="执行数学计算",
            func=self._calculate,
            parameters={"expression": {"type": "string", "description": "数学表达式"}}
        )
        self.register(
            name="recall",
            description="从记忆中检索相关信息",
            func=self._recall,
            parameters={
                "query": {"type": "string", "description": "检索查询"},
                "limit": {"type": "integer", "description": "返回结果数量", "default": 3}
            }
        )
    
    def register(self, name: str, description: str, func: callable, parameters: Dict):
        """注册新工具"""
        self.tools[name] = {
            "name": name,
            "description": description,
            "function": func,
            "parameters": parameters
        }
    
    def get_tool(self, name: str) -> Optional[Dict]:
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        return list(self.tools.keys())
    
    def format_tools_prompt(self) -> str:
        """格式化工具描述"""
        lines = ["可用工具:"]
        for name, tool in self.tools.items():
            lines.append(f"- {name}: {tool['description']}")
            params = ", ".join(tool['parameters'].keys())
            lines.append(f"  参数: {params}")
        return "\n".join(lines)
    
    # 工具实现
    def _search(self, query: str) -> str:
        try:
            return f"[搜索'{query}'的结果]"
        except Exception as e:
            return f"搜索失败: {e}"
    
    def _read_file(self, path: str) -> str:
        try:
            full_path = Path(path)
            if not full_path.is_absolute():
                full_path = Path("/root/.openclaw/workspace") / path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content[:2000] + "..." if len(content) > 2000 else content
        except Exception as e:
            return f"读取失败: {e}"
    
    def _execute(self, command: str) -> str:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            return output[:1000] + "..." if len(output) > 1000 else output
        except Exception as e:
            return f"执行失败: {e}"
    
    def _calculate(self, expression: str) -> str:
        try:
            allowed = {"abs": abs, "max": max, "min": min, "pow": pow, "round": round}
            result = eval(expression, {"__builtins__": {}}, allowed)
            return str(result)
        except Exception as e:
            return f"计算错误: {e}"
    
    def _recall(self, query: str, limit: int = 3) -> str:
        return f"[记忆检索'{query}'的结果]"


# ============================================================================
# ReAct Agent 核心逻辑
# ============================================================================

class ReActAgent:
    """ReAct Agent 实现"""
    
    def __init__(self, session_state: Dict):
        self.session = session_state
        self.tools = ToolRegistry()
    
    def run(self, task: str, available_tools: List[str] = None, 
            max_iterations: int = 10) -> Dict:
        """执行 ReAct 循环"""
        self.session["task"] = task
        self.session["status"] = "running"
        self.session["max_iterations"] = max_iterations
        self.session["steps"] = []
        
        # 筛选工具
        if available_tools:
            tool_list = [t for t in available_tools if t in self.tools.list_tools()]
        else:
            tool_list = self.tools.list_tools()
        
        self.session["available_tools"] = tool_list
        
        context = ""
        final_answer = None
        
        for i in range(max_iterations):
            thought = self._think(task, context, tool_list)
            action_name, action_input = self._decide_action(thought, tool_list)
            
            if action_name == "finish" or action_name is None:
                final_answer = action_input.get("answer", thought)
                break
            
            observation = self._execute_action(action_name, action_input)
            
            step = AgentStep(
                iteration=i+1,
                thought=thought,
                action=action_name,
                action_input=action_input,
                observation=observation
            )
            self.session["steps"].append(asdict(step))
            
            context += f"\nStep {i+1}: Thought: {thought}, Action: {action_name}, Observation: {observation}\n"
        
        self.session["final_answer"] = final_answer or "未能得出答案"
        self.session["status"] = "completed"
        
        return {
            "task": task,
            "final_answer": self.session["final_answer"],
            "steps_count": len(self.session["steps"]),
            "steps": self.session["steps"]
        }
    
    def _think(self, task: str, context: str, tools_prompt: List[str]) -> str:
        """思考步骤"""
        if not context:
            return f"我需要分析任务: {task}。让我先理解需求，然后选择合适的工具。"
        
        if "文件" in task or "read" in task.lower():
            return "这个任务涉及文件操作，我应该使用read_file工具。"
        elif "计算" in task or any(op in task for op in "+-*/"):
            return "这是一个计算任务，我需要使用calculate工具。"
        elif "搜索" in task or "查询" in task:
            return "我需要搜索相关信息，应该使用search工具。"
        else:
            return "基于已有信息，我可以给出答案了。"
    
    def _decide_action(self, thought: str, available_tools: List[str]) -> tuple:
        """解析Thought，决定Action"""
        thought_lower = thought.lower()
        
        if "read_file" in thought_lower or "读取文件" in thought:
            return "read_file", {"path": "MEMORY.md"}
        elif "calculate" in thought_lower or "计算" in thought_lower:
            expr_match = re.search(r'(\d+\s*[\+\-\*/]\s*\d+)', thought)
            expr = expr_match.group(1) if expr_match else "2+2"
            return "calculate", {"expression": expr}
        elif "search" in thought_lower:
            return "search", {"query": "相关信息"}
        elif "完成" in thought_lower or "答案" in thought_lower:
            return "finish", {"answer": thought}
        
        return "finish", {"answer": thought}
    
    def _execute_action(self, action_name: str, action_input: Dict) -> str:
        """执行工具调用"""
        tool = self.tools.get_tool(action_name)
        if not tool:
            return f"错误: 未知工具 '{action_name}'"
        
        try:
            return tool["function"](**action_input)
        except Exception as e:
            return f"执行错误: {e}"


# ============================================================================
# CLI 命令定义
# ============================================================================

@command(CommandMetadata(
    name="react.run",
    description="运行 ReAct Agent 任务",
    category="react",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class ReactRunCommand:
    """运行 ReAct Agent"""
    
    task = arg("task", ArgumentType.STRING, help="要执行的任务描述")
    tools = opt("tools", ArgumentType.STRING, default=None,
                help="允许的工具，逗号分隔 (search,read_file,execute,calculate,recall)")
    max_iter = opt("max-iter", ArgumentType.INTEGER, default=10,
                   help="最大迭代次数")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        session = ctx.session
        
        # 获取 ReAct 状态或创建新的
        react_state = session.get("react", {})
        
        task = ctx.args.get("task", "")
        tools_str = ctx.options.get("tools")
        max_iter = int(ctx.options.get("max-iter", 10))
        
        tool_list = None
        if tools_str:
            tool_list = [t.strip() for t in tools_str.split(",")]
        
        # 运行 Agent
        agent = ReActAgent(react_state)
        result = agent.run(task, tool_list, max_iter)
        
        # 保存状态
        session.set("react", react_state)
        
        return CommandResult(
            success=True,
            message=f"ReAct 完成: {result['final_answer'][:100]}...",
            data=result,
            state_change={"react_steps": len(result["steps"])}
        )


@command(CommandMetadata(
    name="react.tools",
    description="列出可用工具",
    category="react",
    modifies_state=False,
    requires_session=True
))
class ReactToolsCommand:
    """列出 ReAct 工具"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        registry = ToolRegistry()
        tools = []
        
        for name in registry.list_tools():
            tool = registry.get_tool(name)
            tools.append({
                "name": name,
                "description": tool["description"],
                "parameters": list(tool["parameters"].keys())
            })
        
        return CommandResult(
            success=True,
            message=f"可用工具: {', '.join(registry.list_tools())}",
            data={"tools": tools}
        )


@command(CommandMetadata(
    name="react.status",
    description="查看当前 ReAct 会话状态",
    category="react",
    modifies_state=False,
    requires_session=True
))
class ReactStatusCommand:
    """查看状态"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        react_state = ctx.session.get("react", {})
        
        return CommandResult(
            success=True,
            data={
                "status": react_state.get("status", "idle"),
                "task": react_state.get("task", ""),
                "steps_count": len(react_state.get("steps", [])),
                "final_answer": react_state.get("final_answer", "")[:200]
            }
        )


@command(CommandMetadata(
    name="react.history",
    description="查看执行历史",
    category="react",
    modifies_state=False,
    requires_session=True
))
class ReactHistoryCommand:
    """查看历史"""
    
    limit = opt("limit", ArgumentType.INTEGER, default=10, help="显示步骤数")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        react_state = ctx.session.get("react", {})
        steps = react_state.get("steps", [])
        limit = int(ctx.options.get("limit", 10))
        
        recent_steps = steps[-limit:] if steps else []
        
        return CommandResult(
            success=True,
            data={
                "total_steps": len(steps),
                "recent_steps": recent_steps
            }
        )


@command(CommandMetadata(
    name="react.reset",
    description="重置 ReAct 会话",
    category="react",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class ReactResetCommand:
    """重置会话"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.session.set("react", {
            "status": "idle",
            "task": "",
            "steps": [],
            "final_answer": ""
        })
        
        return CommandResult(
            success=True,
            message="ReAct 会话已重置"
        )


# ============================================================================
# REPL 入口
# ============================================================================

def create_react_skill():
    """创建 ReAct Skill 注册表"""
    registry = CommandRegistry()
    
    # 注册 ReAct 命令
    registry.register(ReactRunCommand)
    registry.register(ReactToolsCommand)
    registry.register(ReactStatusCommand)
    registry.register(ReactHistoryCommand)
    registry.register(ReactResetCommand)
    
    return registry


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ReAct Agent Skill")
    parser.add_argument("--interactive", "-i", action="store_true", 
                        help="启动 REPL 模式")
    parser.add_argument("--task", help="直接执行任务")
    parser.add_argument("--tools", help="允许的工具")
    
    args = parser.parse_args()
    
    registry = create_react_skill()
    session_manager = SessionManager()
    
    if args.task:
        # 直接模式 - 创建一个临时会话并执行
        session = session_manager.create_session("react_cli")
        
        # 构建参数
        ctx = CommandContext(
            session=session,
            args={"task": args.task},
            options={"tools": args.tools} if args.tools else {},
            working_dir=Path.cwd()
        )
        
        cmd = ReactRunCommand()
        result = cmd.execute(ctx)
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
    else:
        # REPL 模式
        print("🤖 ReAct Agent Skill")
        print("命令: react.run, react.tools, react.status, react.history, react.reset")
        print("其他: session.create, undo, redo, help, exit\n")
        
        repl = ReplSkin(registry, session_manager)
        repl.run()


if __name__ == "__main__":
    main()
