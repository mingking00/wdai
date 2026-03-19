"""
ReAct Agent - Reasoning + Acting
基础Tool-use Agent实现

基于论文: ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2023)
arXiv: 2210.03629
"""

import json
import re
from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Thought:
    """思考步骤"""
    step: int
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Action:
    """行动步骤"""
    name: str
    input_data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Observation:
    """观察结果"""
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Tool:
    """工具基类"""
    
    def __init__(self, name: str, description: str, parameters: Dict):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def execute(self, **kwargs) -> str:
        """执行工具，子类需实现"""
        raise NotImplementedError
    
    def get_schema(self) -> Dict:
        """获取工具JSON Schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class CalculatorTool(Tool):
    """计算器工具 - 示例"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行数学计算",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，例如 '2 + 2' 或 'sqrt(16)'"
                    }
                },
                "required": ["expression"]
            }
        )
    
    def execute(self, expression: str) -> str:
        try:
            # 安全计算 - 只允许基本运算
            allowed_names = {
                "abs": abs, "max": max, "min": min,
                "pow": pow, "round": round, "sum": sum
            }
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"


class SearchTool(Tool):
    """搜索工具 - 示例(模拟)"""
    
    def __init__(self):
        super().__init__(
            name="search",
            description="搜索信息",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    }
                },
                "required": ["query"]
            }
        )
        # 模拟知识库
        self.knowledge_base = {
            "react": "ReAct是Reasoning + Acting的缩写，是一种让LLM交错进行推理和行动的方法。",
            "llm agent": "LLM Agent是基于大语言模型的智能体，能够自主规划、推理和执行任务。",
            "chain of thought": "Chain-of-Thought prompting通过让模型展示推理过程来提升复杂任务的表现。"
        }
    
    def execute(self, query: str) -> str:
        query_lower = query.lower()
        for key, value in self.knowledge_base.items():
            if key in query_lower:
                return f"搜索结果: {value}"
        return f"搜索结果: 未找到关于 '{query}' 的信息"


class ReActAgent:
    """
    ReAct Agent实现
    
    ReAct = Reasoning (思考) + Acting (行动)
    
    工作流程:
    1. Thought: 分析当前情况，决定下一步
    2. Action: 执行工具调用
    3. Observation: 获取执行结果
    4. 重复1-3直到完成任务
    """
    
    def __init__(self, tools: List[Tool], max_iterations: int = 10):
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = max_iterations
        self.history: List[Dict] = []
        self.thoughts: List[Thought] = []
        self.actions: List[Action] = []
        self.observations: List[Observation] = []
    
    def _format_tools(self) -> str:
        """格式化工具描述"""
        tool_descriptions = []
        for name, tool in self.tools.items():
            tool_descriptions.append(
                f"- {name}: {tool.description}\n"
                f"  参数: {json.dumps(tool.parameters, indent=2, ensure_ascii=False)}"
            )
        return "\n".join(tool_descriptions)
    
    def _parse_action(self, text: str) -> Optional[Action]:
        """从文本中解析Action"""
        # 匹配 Action: tool_name[input]
        pattern = r'Action:\s*(\w+)\[(.*?)\]'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            tool_name = match.group(1)
            input_str = match.group(2)
            
            # 尝试解析JSON参数
            try:
                input_data = json.loads(input_str)
            except json.JSONDecodeError:
                # 如果不是JSON，当作字符串参数
                input_data = {"query": input_str} if tool_name == "search" else {"expression": input_str}
            
            return Action(name=tool_name, input_data=input_data)
        
        return None
    
    def _parse_thought(self, text: str) -> Optional[str]:
        """从文本中解析Thought"""
        pattern = r'Thought:\s*(.*?)(?=Action:|Observation:|$)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def _format_prompt(self, task: str, context: str = "") -> str:
        """格式化ReAct提示词"""
        tools_desc = self._format_tools()
        
        prompt = f"""你是一个智能助手，可以使用以下工具完成任务：

可用工具:
{tools_desc}

你需要使用ReAct框架（推理+行动）来完成任务。

格式指南:
1. Thought: 分析当前情况，决定下一步行动
2. Action: tool_name[参数]  - 调用工具
3. Observation: 观察结果

当前任务: {task}

{context}
"""
        return prompt
    
    def think(self, prompt: str, iteration: int = 0) -> str:
        """
        思考步骤 - 生成Thought和Action
        
        在实际实现中，这里应该调用LLM API
        这里使用模拟实现演示逻辑
        """
        # TODO: 替换为实际的LLM调用
        # 例如: openai.ChatCompletion.create() 或 anthropic.messages.create()
        
        # 从prompt中提取任务
        if "任务:" in prompt:
            task_start = prompt.find("任务:") + 3
            task_end = prompt.find("\n", task_start)
            task = prompt[task_start:task_end].strip()
        else:
            task = ""
        
        # 简单模式匹配决定行动
        if iteration >= 2:  # 限制迭代次数
            return f"Thought: 已经尝试多次，任务应该已完成。\nAction: finish[已完成: {task}]"
        
        if any(word in task for word in ["计算", "calculate", "math", "*", "+", "-", "/"]):
            # 提取表达式
            import re
            expr_match = re.search(r'(\d+\s*[\+\-\*/\^]\s*\d+)', task)
            if expr_match:
                expr = expr_match.group(1).replace(" ", "")
                return f"Thought: 用户需要数学计算，我应该使用calculator工具计算 {expr}。\nAction: calculator[{json.dumps({'expression': expr})}]"
            else:
                return "Thought: 用户需要计算，我应该使用calculator工具。\nAction: calculator[{\"expression\": \"2 + 2\"}]"
        
        elif any(word in task for word in ["搜索", "search", "查询", "什么是", "查找"]):
            # 提取查询词
            query = task.replace("什么是", "").replace("搜索", "").replace("查询", "").strip()
            return f"Thought: 用户需要查询信息，我应该使用search工具。\nAction: search[{json.dumps({'query': query})}]"
        
        else:
            return f"Thought: 这是一个通用任务，我直接完成它。\nAction: finish[已处理: {task}]"
    
    def execute_action(self, action: Action) -> Observation:
        """执行Action并返回Observation"""
        if action.name == "finish":
            return Observation(content=action.input_data.get("result", "任务完成"))
        
        if action.name not in self.tools:
            return Observation(content=f"错误: 未知工具 '{action.name}'")
        
        tool = self.tools[action.name]
        try:
            result = tool.execute(**action.input_data)
            return Observation(content=result)
        except Exception as e:
            return Observation(content=f"执行错误: {str(e)}")
    
    def run(self, task: str) -> Dict:
        """
        运行ReAct Agent完成任务
        
        Args:
            task: 任务描述
            
        Returns:
            包含执行历史的字典
        """
        print(f"🎯 任务: {task}")
        print("=" * 50)
        
        context = ""
        final_answer = None
        
        for i in range(self.max_iterations):
            print(f"\n--- 迭代 {i+1} ---")
            
            # 1. 思考 (Thought)
            prompt = self._format_prompt(task, context)
            response = self.think(prompt, iteration=i)
            
            thought_content = self._parse_thought(response)
            if thought_content:
                thought = Thought(step=i+1, content=thought_content)
                self.thoughts.append(thought)
                print(f"💭 Thought: {thought_content}")
            
            # 2. 行动 (Action)
            action = self._parse_action(response)
            if action:
                if action.name == "finish":
                    final_answer = action.input_data.get("result", "任务完成")
                    print(f"✅ 完成: {final_answer}")
                    break
                
                self.actions.append(action)
                print(f"🔧 Action: {action.name}({action.input_data})")
                
                # 3. 观察 (Observation)
                observation = self.execute_action(action)
                self.observations.append(observation)
                print(f"👁️ Observation: {observation.content[:100]}...")
                
                # 更新上下文
                context += f"\nThought: {thought_content}\nAction: {action.name}\nObservation: {observation.content}\n"
            else:
                print("⚠️ 无法解析Action")
                break
        
        # 整理结果
        result = {
            "task": task,
            "iterations": len(self.thoughts),
            "thoughts": [t.__dict__ for t in self.thoughts],
            "actions": [{"name": a.name, "input": a.input_data} for a in self.actions],
            "observations": [o.__dict__ for o in self.observations],
            "final_answer": final_answer or "未完成任务"
        }
        
        self.history.append(result)
        return result
    
    def get_history(self) -> List[Dict]:
        """获取执行历史"""
        return self.history


# ==================== 演示 ====================

def demo():
    """ReAct Agent演示"""
    
    print("🤖 ReAct Agent Demo")
    print("=" * 50)
    
    # 创建工具
    calculator = CalculatorTool()
    search = SearchTool()
    
    # 创建Agent
    agent = ReActAgent(tools=[calculator, search])
    
    # 任务1: 计算
    print("\n\n任务1: 简单计算")
    result1 = agent.run("计算 15 * 23 等于多少")
    
    # 任务2: 搜索
    print("\n\n任务2: 信息查询")
    result2 = agent.run("什么是ReAct?")
    
    # 打印总结
    print("\n\n📊 执行总结")
    print("=" * 50)
    print(f"完成任务数: {len(agent.get_history())}")
    print(f"总思考步骤: {sum(r['iterations'] for r in agent.get_history())}")


if __name__ == "__main__":
    demo()
