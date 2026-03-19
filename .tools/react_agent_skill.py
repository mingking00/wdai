#!/usr/bin/env python3
"""
ReAct Agent Skill - 可实际调用的推理行动Agent

用途: 在复杂任务中自动推理和执行工具
调用: python3 react_agent_skill.py "任务描述" [--tools tool1,tool2]

集成到OpenClaw工作流:
- 多步骤问题解决
- 自动工具选择和执行
- 可追踪的执行历史
"""

import sys
import json
import re
import argparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

# 配置路径
WORKSPACE = Path("/root/.openclaw/workspace")
LOG_DIR = WORKSPACE / ".logs" / "agent-runs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AgentStep:
    """Agent执行步骤记录"""
    iteration: int
    thought: str
    action: str
    action_input: Dict
    observation: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ToolRegistry:
    """工具注册表 - 管理可用工具"""
    
    def __init__(self):
        self.tools: Dict[str, Dict] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 搜索工具
        self.register(
            name="search",
            description="搜索网络信息",
            func=self._search,
            parameters={
                "query": {"type": "string", "description": "搜索查询"}
            }
        )
        
        # 文件读取工具
        self.register(
            name="read_file",
            description="读取文件内容",
            func=self._read_file,
            parameters={
                "path": {"type": "string", "description": "文件路径"}
            }
        )
        
        # 执行命令工具
        self.register(
            name="execute",
            description="执行shell命令",
            func=self._execute,
            parameters={
                "command": {"type": "string", "description": "要执行的命令"}
            }
        )
        
        # 计算工具
        self.register(
            name="calculate",
            description="执行数学计算",
            func=self._calculate,
            parameters={
                "expression": {"type": "string", "description": "数学表达式"}
            }
        )
        
        # 记忆检索工具
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
        """获取工具定义"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self.tools.keys())
    
    def format_tools_prompt(self) -> str:
        """格式化工具描述用于Prompt"""
        lines = ["可用工具:"]
        for name, tool in self.tools.items():
            lines.append(f"- {name}: {tool['description']}")
            params = ", ".join(tool['parameters'].keys())
            lines.append(f"  参数: {params}")
        return "\n".join(lines)
    
    # 工具实现
    def _search(self, query: str) -> str:
        """搜索工具 - 实际调用kimi_search"""
        try:
            # 这里简化实现，实际可调用 kimi_search
            return f"[搜索'{query}'的结果将在实际调用时返回]"
        except Exception as e:
            return f"搜索失败: {e}"
    
    def _read_file(self, path: str) -> str:
        """读取文件"""
        try:
            full_path = WORKSPACE / path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content[:2000] + "..." if len(content) > 2000 else content
        except Exception as e:
            return f"读取失败: {e}"
    
    def _execute(self, command: str) -> str:
        """执行命令"""
        import subprocess
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            return output[:1000] + "..." if len(output) > 1000 else output
        except Exception as e:
            return f"执行失败: {e}"
    
    def _calculate(self, expression: str) -> str:
        """计算表达式"""
        try:
            allowed = {"abs": abs, "max": max, "min": min, "pow": pow, "round": round}
            result = eval(expression, {"__builtins__": {}}, allowed)
            return str(result)
        except Exception as e:
            return f"计算错误: {e}"
    
    def _recall(self, query: str, limit: int = 3) -> str:
        """记忆检索"""
        # 简化实现，实际可调用 memory_search
        return f"[记忆检索'{query}'的结果]"


class ReActSkill:
    """
    ReAct Agent Skill - 推理行动循环
    
    工作流程:
    1. 分析任务 -> Thought
    2. 选择工具 -> Action
    3. 执行获取结果 -> Observation
    4. 循环直到完成
    """
    
    def __init__(self, max_iterations: int = 10, model: str = "kimi-coding/k2p5"):
        self.max_iterations = max_iterations
        self.model = model
        self.tools = ToolRegistry()
        self.steps: List[AgentStep] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def run(self, task: str, available_tools: List[str] = None) -> Dict:
        """
        执行任务
        
        Args:
            task: 任务描述
            available_tools: 允许使用的工具列表，None表示全部
            
        Returns:
            执行结果字典
        """
        print(f"🎯 任务: {task}")
        print("=" * 60)
        
        # 筛选工具
        if available_tools:
            tool_list = [t for t in available_tools if t in self.tools.list_tools()]
        else:
            tool_list = self.tools.list_tools()
        
        # 构建工具提示
        tools_prompt = self._build_tools_prompt(tool_list)
        
        context = ""
        final_answer = None
        
        for i in range(self.max_iterations):
            # ReAct循环
            thought = self._think(task, context, tools_prompt)
            print(f"\n💭 Thought [{i+1}]: {thought}")
            
            action_name, action_input = self._decide_action(thought, tool_list)
            
            if action_name == "finish" or action_name is None:
                final_answer = action_input.get("answer", thought)
                print(f"✅ 完成: {final_answer}")
                break
            
            print(f"🔧 Action: {action_name}({action_input})")
            
            # 执行工具
            observation = self._execute_action(action_name, action_input)
            print(f"👁️ Observation: {observation[:200]}...")
            
            # 记录步骤
            step = AgentStep(
                iteration=i+1,
                thought=thought,
                action=action_name,
                action_input=action_input,
                observation=observation
            )
            self.steps.append(step)
            
            # 更新上下文
            context += f"\nStep {i+1}:\nThought: {thought}\nAction: {action_name}\nObservation: {observation}\n"
        
        # 保存执行记录
        result = self._save_result(task, final_answer)
        return result
    
    def _think(self, task: str, context: str, tools_prompt: str) -> str:
        """
        思考步骤 - 决定下一步行动
        
        实际实现中应调用LLM API
        这里使用基于规则的模拟
        """
        # TODO: 接入实际LLM调用
        # response = sessions_spawn(task=full_prompt, agent_id="main")
        
        # 模拟思考逻辑
        if not context:
            return f"我需要分析任务: {task}。让我先理解需求，然后选择合适的工具。"
        
        # 基于上下文决定
        if "文件" in task or "read" in task.lower():
            return "这个任务涉及文件操作，我应该使用read_file工具。"
        elif "计算" in task or any(op in task for op in "+-*/"):
            return "这是一个计算任务，我需要使用calculate工具。"
        elif "搜索" in task or "查询" in task:
            return "我需要搜索相关信息，应该使用search工具。"
        else:
            return "基于已有信息，我可以给出答案了。"
    
    def _decide_action(self, thought: str, available_tools: List[str]) -> tuple:
        """
        解析Thought，决定Action
        
        返回: (action_name, action_params)
        """
        thought_lower = thought.lower()
        
        # 简单规则匹配
        if "read_file" in thought_lower or "读取文件" in thought:
            return "read_file", {"path": "MEMORY.md"}  # 默认示例
        
        elif "calculate" in thought_lower or "计算" in thought_lower:
            # 尝试提取表达式
            expr_match = re.search(r'(\d+\s*[\+\-\*/]\s*\d+)', thought)
            expr = expr_match.group(1) if expr_match else "2+2"
            return "calculate", {"expression": expr}
        
        elif "search" in thought_lower:
            return "search", {"query": "相关信息"}
        
        elif "完成" in thought_lower or "答案" in thought_lower:
            return "finish", {"answer": thought}
        
        # 默认完成
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
    
    def _build_tools_prompt(self, tool_list: List[str]) -> str:
        """构建工具提示"""
        lines = []
        for name in tool_list:
            tool = self.tools.get_tool(name)
            if tool:
                lines.append(f"- {name}: {tool['description']}")
        return "\n".join(lines)
    
    def _save_result(self, task: str, final_answer: str) -> Dict:
        """保存执行结果"""
        result = {
            "session_id": self.session_id,
            "task": task,
            "final_answer": final_answer,
            "steps_count": len(self.steps),
            "steps": [asdict(s) for s in self.steps],
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存到日志文件
        log_file = LOG_DIR / f"react_{self.session_id}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 执行记录已保存: {log_file}")
        return result
    
    def get_execution_history(self) -> List[Dict]:
        """获取执行历史"""
        return [asdict(s) for s in self.steps]


def main():
    parser = argparse.ArgumentParser(description="ReAct Agent Skill")
    parser.add_argument("task", help="要执行的任务描述")
    parser.add_argument("--tools", help="允许的工具，逗号分隔", default=None)
    parser.add_argument("--max-iter", type=int, default=10, help="最大迭代次数")
    
    args = parser.parse_args()
    
    # 解析工具列表
    tool_list = None
    if args.tools:
        tool_list = [t.strip() for t in args.tools.split(",")]
    
    # 运行Agent
    agent = ReActSkill(max_iterations=args.max_iter)
    result = agent.run(args.task, tool_list)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("📊 执行结果")
    print("=" * 60)
    print(f"任务: {result['task']}")
    print(f"结果: {result['final_answer']}")
    print(f"步骤数: {result['steps_count']}")


if __name__ == "__main__":
    main()
