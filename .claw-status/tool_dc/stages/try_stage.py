"""
Tool-DC Try Stage: Grouping and Local Inference
"""

import logging
from typing import List, Optional, Union
import random

from ..models import Tool, ToolCall
from ..config import ToolDCConfig

logger = logging.getLogger(__name__)


# Try Stage Prompt 模板
TRY_PROMPT_TEMPLATE = """# System:
你是工具选择专家。任务：从提供的工具列表中识别所有可能满足用户需求的工具。

## 规则：
1. 仔细阅读用户问题和工具描述
2. 选择任何可能满足用户需求的工具（或部分需求）
3. 提取问题中的关键信息，填入工具参数
4. 如果多个工具都相关，可以同时选择

## 输出格式：
如果决定调用工具，必须按以下格式返回：
[func_name1(param1=value1, param2=value2), func_name2(params)]

如果没有合适的工具，返回：
NO_TOOL

不要包含任何其他文本。"""


class TryStage:
    """
    Try Stage: 策略锚点分组 + 局部推理
    
    核心逻辑：
    1. 检索 Top-K 相关工具
    2. 以每个 Top-K 工具为锚点，构建 K 个并行组
    3. 每组包含：锚点 + 不重叠的干扰工具子集
    4. 保留原始 Top-K 作为独立组 S₀
    """
    
    def __init__(self, config: ToolDCConfig, retriever=None, llm=None):
        self.config = config
        self.retriever = retriever
        self.llm = llm
        
    def strategic_anchor_grouping(
        self, 
        tools: List[Tool], 
        query: str, 
        K: int = 5
    ) -> List[List[Tool]]:
        """
        策略锚点分组
        
        Args:
            tools: 所有可用工具
            query: 用户查询
            K: 分组数
            
        Returns:
            List[Tool]: 分组列表 [S₀, S₁, S₂, ..., Sₖ]
        """
        if not tools:
            return []
        
        # 调整 K 值
        K = min(K, len(tools))
        
        # Step 1: 检索 Top-K 相关工具
        if self.retriever:
            top_k = self.retriever.retrieve(query, tools, top_k=K)
        else:
            # 无检索器时，使用前 K 个工具
            top_k = tools[:K]
        
        # Step 2: 构建干扰工具池 (T_tail)
        tail = [t for t in tools if t not in top_k]
        
        # Step 3: 构建分组
        groups = []
        
        # S₀: 原始 Top-K 组
        groups.append(top_k.copy())
        
        # S₁ ~ Sₖ: 锚点分组
        for i, anchor in enumerate(top_k):
            if i >= K:
                break
                
            # 选择干扰项 (轮流分配，确保不重叠)
            distractors = self._select_distractors(tail, K, i)
            
            # 构建组：锚点 + 干扰项
            group = [anchor] + distractors
            groups.append(group)
        
        if self.config.verbose_logging:
            logger.info(f"Try Stage: 创建 {len(groups)} 个组")
            for i, g in enumerate(groups):
                tool_names = [t.name for t in g]
                logger.debug(f"  组 {i}: {tool_names}")
        
        return groups
    
    def _select_distractors(
        self, 
        tail: List[Tool], 
        total_groups: int, 
        group_index: int
    ) -> List[Tool]:
        """
        选择干扰工具
        
        策略：将 tail 均匀分配到各组，确保不重叠
        """
        if not tail:
            return []
        
        # 计算每组应分配的干扰项数量
        base_count = len(tail) // total_groups
        remainder = len(tail) % total_groups
        
        # 当前组分配的数量
        count = base_count + (1 if group_index < remainder else 0)
        
        # 选择干扰项 (轮询分配)
        selected = []
        for i in range(count):
            idx = group_index + i * total_groups
            if idx < len(tail):
                selected.append(tail[idx])
        
        return selected
    
    def local_inference(
        self, 
        query: str, 
        group: List[Tool]
    ) -> Optional[ToolCall]:
        """
        在子空间内进行局部推理
        
        Args:
            query: 用户查询
            group: 工具子集
            
        Returns:
            Optional[ToolCall]: 工具调用或 None
        """
        if not self.llm:
            logger.warning("未配置 LLM，无法执行局部推理")
            return None
        
        # 构建 Prompt
        tools_desc = self._format_tools(group)
        prompt = f"{TRY_PROMPT_TEMPLATE}\n\n# 可用工具:\n{tools_desc}\n\n# 用户问题:\n{query}"
        
        try:
            # 调用 LLM
            response = self.llm.generate(prompt)
            
            if self.config.verbose_logging:
                logger.debug(f"局部推理响应: {response[:200]}...")
            
            # 解析工具调用
            return self._parse_tool_call(response)
            
        except Exception as e:
            logger.error(f"局部推理失败: {e}")
            return None
    
    def parallel_inference(
        self, 
        query: str, 
        groups: List[List[Tool]]
    ) -> List[ToolCall]:
        """
        并行执行各组的局部推理
        
        Args:
            query: 用户查询
            groups: 分组列表
            
        Returns:
            List[ToolCall]: 所有候选调用
        """
        candidates = []
        
        if self.config.parallel_inference:
            # TODO: 使用多线程/异步实现真正的并行
            # 当前实现：顺序执行
            pass
        
        for i, group in enumerate(groups):
            call = self.local_inference(query, group)
            if call:
                call.source_group = i
                candidates.append(call)
                
                if self.config.verbose_logging:
                    logger.info(f"组 {i} 产生候选: {call}")
        
        return candidates
    
    def _format_tools(self, tools: List[Tool]) -> str:
        """格式化工具描述"""
        lines = []
        for tool in tools:
            lines.append(f"- {tool.name}: {tool.description}")
            if tool.parameters:
                for param in tool.parameters:
                    req = "(必填)" if param.required else ""
                    lines.append(f"    - {param.name}: {param.description} [{param.type.value}]{req}")
        return "\n".join(lines)
    
    def _parse_tool_call(self, response: str) -> Optional[ToolCall]:
        """解析 LLM 响应中的工具调用
        
        支持的格式：
        - [func_name(param=value)]
        - func_name(param=value)
        """
        response = response.strip()
        
        # 处理 NO_TOOL
        if response.upper() == "NO_TOOL" or not response:
            return None
        
        # 移除可能的方括号
        if response.startswith("[") and response.endswith("]"):
            response = response[1:-1].strip()
        
        # 解析函数调用
        # 格式: func_name(arg1=val1, arg2=val2)
        try:
            # 找到第一个左括号
            paren_idx = response.find("(")
            if paren_idx == -1:
                # 没有参数的情况
                return ToolCall(name=response, arguments={})
            
            func_name = response[:paren_idx].strip()
            
            # 找到对应的右括号
            args_str = response[paren_idx + 1:].rstrip(")").strip()
            
            # 解析参数
            arguments = {}
            if args_str:
                # 简单的参数解析 (支持基本类型)
                args_str = args_str.replace("'", '"')
                # TODO: 使用更健壮的解析器处理复杂参数
                for pair in args_str.split(","):
                    if "=" in pair:
                        key, val = pair.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"')
                        # 尝试转换为合适类型
                        arguments[key] = self._convert_value(val)
            
            return ToolCall(name=func_name, arguments=arguments)
            
        except Exception as e:
            logger.error(f"解析工具调用失败: {e}, 响应: {response[:100]}")
            return None
    
    def _convert_value(self, val: str) -> Union[str, int, float, bool]:
        """尝试将字符串转换为适当类型"""
        # 布尔值
        if val.lower() in ("true", "false"):
            return val.lower() == "true"
        
        # 整数
        try:
            return int(val)
        except ValueError:
            pass
        
        # 浮点数
        try:
            return float(val)
        except ValueError:
            pass
        
        # 默认字符串
        return val
