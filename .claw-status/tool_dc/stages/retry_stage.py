"""
Tool-DC Retry Stage: Global Aggregation and Decision
"""

import logging
from typing import List, Optional, Optional

from ..models import Tool, ToolCall
from ..config import ToolDCConfig

logger = logging.getLogger(__name__)


# Retry Stage Prompt 模板
RETRY_PROMPT_TEMPLATE = """# System:
你是工具组合专家。基于已验证的有效候选，做出最优决策。

## 背景信息：
以下工具调用已经过严格验证（函数名存在、参数完整、类型正确）。
这些调用来自不同的工具组，每个组只看到了部分候选工具。

## 你的任务：
1. 分析所有验证通过的候选调用
2. 判断哪个调用最能完整满足用户需求
3. 如果多个调用都相关，选择最准确的那个
4. 必要时可以组合多个调用

## 输出格式：
直接输出最终选择的工具调用：
[func_name1(param1=value1, param2=value2)]

只输出最终调用，不要任何解释。"""


class RetryStage:
    """
    Retry Stage: 全局聚合与决策
    
    利用 LLM 的自我反思能力，从验证通过的工具中做出全局最优决策。
    """
    
    def __init__(self, config: ToolDCConfig, llm=None):
        self.config = config
        self.llm = llm
    
    def global_aggregation(
        self, 
        query: str,
        valid_calls: List[ToolCall],
        all_tools: List[Tool]
    ) -> Optional[ToolCall]:
        """
        聚合验证通过的工具，进行最终决策
        
        Args:
            query: 用户查询
            valid_calls: 验证通过的工具调用
            all_tools: 所有可用工具
            
        Returns:
            Optional[ToolCall]: 最终选定的工具调用
        """
        if not valid_calls:
            return None
        
        # 只有一个候选，直接返回
        if len(valid_calls) == 1:
            if self.config.verbose_logging:
                logger.info(f"只有一个有效候选，直接选择: {valid_calls[0]}")
            return valid_calls[0]
        
        # 多个候选，需要聚合决策
        if not self.llm:
            # 无 LLM 时，选择第一个
            logger.warning("未配置 LLM，选择第一个候选")
            return valid_calls[0]
        
        # 构建精炼候选集 T_retry
        t_retry = self._build_retry_set(valid_calls, all_tools)
        
        # 构建反思 Prompt
        candidates_desc = self._format_candidates(valid_calls)
        prompt = (
            f"{RETRY_PROMPT_TEMPLATE}\n\n"
            f"# 用户问题:\n{query}\n\n"
            f"# 验证通过的候选调用:\n{candidates_desc}\n\n"
            f"# 可用工具定义:\n{self._format_tools(t_retry)}"
        )
        
        try:
            response = self.llm.generate(prompt)
            
            if self.config.verbose_logging:
                logger.debug(f"Retry Stage 响应: {response[:200]}...")
            
            # 解析最终调用
            final_call = self._parse_tool_call(response)
            
            if final_call:
                # 验证最终调用确实在 valid_calls 中
                if self._validate_in_candidates(final_call, valid_calls):
                    logger.info(f"Retry Stage 选择: {final_call}")
                    return final_call
                else:
                    logger.warning(f"LLM 选择了不在候选中的调用，从候选中选择最佳匹配")
                    return self._find_best_match(final_call, valid_calls)
            else:
                # 解析失败，回退到第一个候选
                logger.warning("解析 Retry 响应失败，回退到第一个候选")
                return valid_calls[0]
                
        except Exception as e:
            logger.error(f"Retry Stage 失败: {e}")
            return valid_calls[0]
    
    def _build_retry_set(
        self, 
        valid_calls: List[ToolCall], 
        all_tools: List[Tool]
    ) -> List[Tool]:
        """
        构建重试阶段的精炼工具集
        
        从有效调用中提取涉及的工具定义
        """
        involved_names = set(call.name for call in valid_calls)
        t_retry = [t for t in all_tools if t.name in involved_names]
        return t_retry
    
    def _format_candidates(self, calls: List[ToolCall]) -> str:
        """格式化候选调用"""
        lines = []
        for i, call in enumerate(calls, 1):
            lines.append(f"{i}. {call}")
            if call.source_group is not None:
                lines.append(f"   (来自组 {call.source_group})")
        return "\n".join(lines)
    
    def _format_tools(self, tools: List[Tool]) -> str:
        """格式化工具定义"""
        lines = []
        for tool in tools:
            lines.append(f"- {tool.name}: {tool.description}")
            if tool.parameters:
                for param in tool.parameters:
                    req = "(必填)" if param.required else ""
                    lines.append(f"    - {param.name}: {param.description} [{param.type.value}]{req}")
        return "\n".join(lines)
    
    def _parse_tool_call(self, response: str) -> Optional[ToolCall]:
        """解析工具调用
        
        复用 Try Stage 的解析逻辑
        """
        response = response.strip()
        
        if not response or response.upper() == "NO_TOOL":
            return None
        
        # 移除可能的方括号
        if response.startswith("[") and response.endswith("]"):
            response = response[1:-1].strip()
        
        try:
            paren_idx = response.find("(")
            if paren_idx == -1:
                return ToolCall(name=response, arguments={})
            
            func_name = response[:paren_idx].strip()
            args_str = response[paren_idx + 1:].rstrip(")").strip()
            
            arguments = {}
            if args_str:
                args_str = args_str.replace("'", '"')
                for pair in args_str.split(","):
                    if "=" in pair:
                        key, val = pair.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"')
                        arguments[key] = self._convert_value(val)
            
            return ToolCall(name=func_name, arguments=arguments)
            
        except Exception as e:
            logger.error(f"解析 Retry 响应失败: {e}")
            return None
    
    def _convert_value(self, val: str):
        """转换值为合适类型"""
        if val.lower() in ("true", "false"):
            return val.lower() == "true"
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val
    
    def _validate_in_candidates(
        self, 
        call: ToolCall, 
        candidates: List[ToolCall]
    ) -> bool:
        """验证调用是否在候选列表中"""
        for cand in candidates:
            if cand.name == call.name:
                # 简单比较：名称相同且参数大致匹配
                return True
        return False
    
    def _find_best_match(
        self, 
        target: ToolCall, 
        candidates: List[ToolCall]
    ) -> ToolCall:
        """在候选中找到最佳匹配"""
        # 优先匹配名称相同的
        for cand in candidates:
            if cand.name == target.name:
                return cand
        
        # 否则返回第一个
        return candidates[0]
    
    def self_correction(
        self,
        query: str,
        original_call: ToolCall,
        error_message: str,
        tools: List[Tool]
    ) -> Optional[ToolCall]:
        """
        自我纠正机制
        
        当工具调用失败时，尝试纠正错误
        
        Args:
            query: 原始查询
            original_call: 失败的调用
            error_message: 错误信息
            tools: 可用工具
            
        Returns:
            Optional[ToolCall]: 纠正后的调用
        """
        if not self.config.enable_self_correction:
            return None
        
        if not self.llm:
            return None
        
        correction_prompt = f"""# System:
你是工具调用纠错专家。

## 失败信息：
- 原始调用: {original_call}
- 错误信息: {error_message}

## 你的任务：
分析错误原因，尝试修正工具调用。可能的错误：
1. 参数类型错误
2. 缺少必填参数
3. 参数值格式错误
4. 选择了错误的工具

## 输出格式：
如果成功修正，输出修正后的调用：
[func_name(param=value)]

如果无法修正，输出：
UNFIXABLE
"""
        
        try:
            response = self.llm.generate(correction_prompt)
            
            if "UNFIXABLE" in response.upper():
                return None
            
            corrected = self._parse_tool_call(response)
            if corrected:
                logger.info(f"自我纠正: {original_call} -> {corrected}")
            return corrected
            
        except Exception as e:
            logger.error(f"自我纠正失败: {e}")
            return None
