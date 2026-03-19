"""
WDai ReAct + Tool-DC 集成

将 Tool-DC 集成到 WDai 的 ReAct 循环中
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from ..models import Tool, ToolCall, ToolDCResult
from .. import create_tool_dc_handler, ToolDCHandler
from ..config import ToolDCConfig

logger = logging.getLogger(__name__)


@dataclass
class ReActStep:
    """ReAct 单步记录"""
    step_number: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict] = None
    observation: Optional[str] = None
    tool_dc_result: Optional[ToolDCResult] = None


@dataclass
class ReActResult:
    """ReAct 执行结果"""
    success: bool
    steps: List[ReActStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    error: Optional[str] = None
    total_steps: int = 0
    tool_dc_stats: Dict[str, Any] = field(default_factory=dict)


class WDaiReActToolDC:
    """
    WDai ReAct + Tool-DC 集成器
    
    在标准 ReAct 循环中，使用 Tool-DC 替代简单的工具选择逻辑
    """
    
    def __init__(
        self,
        llm,
        tools: List[Tool],
        config: Optional[ToolDCConfig] = None,
        max_iterations: int = 10,
        tool_executor: Optional[Callable] = None
    ):
        """
        初始化
        
        Args:
            llm: LLM 实例，需要实现 generate(prompt) 接口
            tools: 可用工具列表
            config: Tool-DC 配置
            max_iterations: 最大迭代次数
            tool_executor: 工具执行函数，接收 ToolCall，返回结果
        """
        self.llm = llm
        self.tools = tools
        self.config = config or ToolDCConfig()
        self.max_iterations = max_iterations
        self.tool_executor = tool_executor or self._default_executor
        
        # 创建 Tool-DC 处理器
        self.tool_dc = create_tool_dc_handler(
            llm=llm,
            config=self.config
        )
        
        # 工具名到工具的映射
        self._tool_map = {tool.name: tool for tool in tools}
        
        logger.info(f"WDaiReActToolDC 初始化完成 (工具数: {len(tools)})")
    
    def run(self, query: str, context: Optional[str] = None) -> ReActResult:
        """
        执行 ReAct + Tool-DC 循环
        
        Args:
            query: 用户查询
            context: 额外上下文
            
        Returns:
            ReActResult: 执行结果
        """
        result = ReActResult(success=False, steps=[])
        
        # 构建系统提示
        system_prompt = self._build_system_prompt()
        
        # 初始化对话历史
        conversation = []
        if context:
            conversation.append(f"Context: {context}")
        conversation.append(f"Question: {query}")
        
        for step_num in range(1, self.max_iterations + 1):
            logger.info(f"ReAct Step {step_num}/{self.max_iterations}")
            
            # 构建当前提示
            prompt = self._build_prompt(system_prompt, conversation)
            
            # 生成 Thought
            try:
                response = self.llm.generate(prompt)
            except Exception as e:
                result.error = f"LLM 生成失败: {e}"
                return result
            
            # 解析 Thought
            thought = self._extract_thought(response)
            step = ReActStep(step_number=step_num, thought=thought)
            
            logger.info(f"Thought: {thought[:100]}...")
            
            # 检查是否可以直接回答
            if self._is_final_answer(thought):
                final_answer = self._extract_answer(thought)
                result.success = True
                result.final_answer = final_answer
                result.total_steps = step_num
                result.steps.append(step)
                logger.info(f"ReAct 完成，共 {step_num} 步")
                return result
            
            # 使用 Tool-DC 选择工具
            tool_dc_result = self.tool_dc.select_tool(thought, self.tools)
            step.tool_dc_result = tool_dc_result
            
            if not tool_dc_result.success:
                logger.warning("Tool-DC 未能选择工具，尝试直接推理")
                # 降级：尝试从 response 中解析 Action
                action_data = self._extract_action_from_response(response)
                if action_data:
                    tool_call = ToolCall(
                        name=action_data["action"],
                        arguments=action_data.get("action_input", {})
                    )
                else:
                    result.error = f"Step {step_num}: 无法选择工具"
                    result.steps.append(step)
                    return result
            else:
                tool_call = tool_dc_result.final_call
            
            step.action = tool_call.name
            step.action_input = tool_call.arguments
            
            logger.info(f"Action: {tool_call.name}({tool_call.arguments})")
            
            # 执行工具
            try:
                observation = self.tool_executor(tool_call)
                step.observation = str(observation)
                logger.info(f"Observation: {str(observation)[:100]}...")
            except Exception as e:
                step.observation = f"Error: {e}"
                logger.error(f"工具执行失败: {e}")
            
            result.steps.append(step)
            
            # 添加到对话历史
            conversation.append(f"Thought: {thought}")
            conversation.append(f"Action: {step.action}")
            conversation.append(f"Observation: {step.observation}")
        
        # 达到最大迭代次数
        result.error = f"达到最大迭代次数 ({self.max_iterations})"
        result.total_steps = self.max_iterations
        return result
    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        tools_desc = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tools
        ])
        
        return f"""你是一个智能助手，可以使用以下工具来完成任务：

{tools_desc}

请使用以下格式思考：
Thought: 分析问题，确定下一步行动
Action: 选择要使用的工具
Action Input: 工具的输入参数
Observation: 工具执行的结果

当你完成任务时，输出：
Final Answer: 最终答案

重要提示：
1. 仔细分析问题，选择最合适的工具
2. 确保所有必填参数都已提供
3. 如果一次工具调用无法完成任务，继续下一步
4. 只有当你确定任务完成时，才输出 Final Answer"""
    
    def _build_prompt(self, system_prompt: str, conversation: List[str]) -> str:
        """构建完整提示"""
        history = "\n\n".join(conversation)
        return f"{system_prompt}\n\n{history}\n\nThought:"
    
    def _extract_thought(self, response: str) -> str:
        """提取 Thought"""
        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("Thought:"):
                return line[8:].strip()
            elif line and not line.startswith("Action"):
                return line
        return response.strip()
    
    def _is_final_answer(self, thought: str) -> bool:
        """检查是否是最终答案"""
        indicators = [
            "Final Answer:",
            "最终答案:",
            "Answer:",
            "答案是",
            "我可以直接回答"
        ]
        return any(ind in thought for ind in indicators)
    
    def _extract_answer(self, thought: str) -> str:
        """提取答案"""
        if "Final Answer:" in thought:
            return thought.split("Final Answer:", 1)[1].strip()
        elif "最终答案:" in thought:
            return thought.split("最终答案:", 1)[1].strip()
        elif "Answer:" in thought:
            return thought.split("Answer:", 1)[1].strip()
        return thought
    
    def _extract_action_from_response(self, response: str) -> Optional[Dict]:
        """从响应中提取 Action"""
        lines = response.strip().split("\n")
        action = None
        action_input = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("Action:"):
                action = line[7:].strip()
            elif line.startswith("Action Input:"):
                input_str = line[13:].strip()
                try:
                    action_input = json.loads(input_str)
                except:
                    action_input = {"input": input_str}
        
        if action:
            return {"action": action, "action_input": action_input}
        return None
    
    def _default_executor(self, tool_call: ToolCall) -> Any:
        """默认工具执行器"""
        tool = self._tool_map.get(tool_call.name)
        if not tool:
            return f"Error: 工具 '{tool_call.name}' 不存在"
        
        # 这里应该调用实际的工具执行逻辑
        # 对于演示，返回模拟结果
        return f"Executed {tool_call.name} with {tool_call.arguments}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "tools_count": len(self.tools),
            "max_iterations": self.max_iterations,
            "config": {
                "max_groups": self.config.max_groups,
                "fallback_threshold": self.config.fallback_threshold,
                "strict_mode": self.config.strict_mode
            }
        }


# 便捷函数
def create_react_tool_dc(
    llm,
    tools: List[Tool],
    **kwargs
) -> WDaiReActToolDC:
    """
    创建 ReAct + Tool-DC 实例
    
    Args:
        llm: LLM 实例
        tools: 工具列表
        **kwargs: 其他参数
        
    Returns:
        WDaiReActToolDC: 实例
    """
    return WDaiReActToolDC(llm=llm, tools=tools, **kwargs)
