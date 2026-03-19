"""
Tool-DC: A Divide-and-Conquer Framework for Tool-Calling

基于论文: "Try, Check and Retry: A Divide-and-Conquer Framework for Boosting Long-context Tool-Calling Performance of LLMs"

主要组件：
- TryStage: 策略锚点分组 + 局部推理
- CheckStage: Schema 一致性验证
- RetryStage: 全局聚合与决策

新增组件：
- BM25Retriever: BM25 检索器
- WDaiSkillAdapter: WDai Skills 自动转换
- WDaiSkillRegistry: Skills 注册表
"""

import logging
from typing import List, Optional, Any
from dataclasses import dataclass
import time

from .config import ToolDCConfig, DEFAULT_CONFIG
from .models import Tool, ToolCall, ToolDCResult
from .stages import TryStage, CheckStage, RetryStage

logger = logging.getLogger(__name__)


@dataclass
class LLMInterface:
    """
    LLM 接口抽象
    
    用户需要实现这个接口来适配自己的 LLM
    """
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
            
        Returns:
            str: 生成的文本
        """
        raise NotImplementedError("子类必须实现 generate 方法")


class ToolDCHandler:
    """
    Tool-DC 主处理器
    
    封装 Try-Check-Retry 完整流程
    """
    
    def __init__(
        self, 
        config: Optional[ToolDCConfig] = None,
        llm: Optional[Any] = None,
        retriever: Optional[Any] = None
    ):
        """
        初始化 Tool-DC 处理器
        
        Args:
            config: 配置，默认使用 DEFAULT_CONFIG
            llm: LLM 实例，需要实现 generate(prompt) -> str 接口
            retriever: 检索器实例，需要实现 retrieve(query, tools, top_k) 接口
        """
        self.config = config or DEFAULT_CONFIG
        self.llm = llm
        self.retriever = retriever
        
        # 初始化各 Stage
        self.try_stage = TryStage(self.config, retriever, llm)
        self.check_stage = CheckStage(self.config)
        self.retry_stage = RetryStage(self.config, llm)
        
        logger.info(f"Tool-DC 初始化完成 (K={self.config.max_groups})")
    
    def select_tool(
        self, 
        query: str, 
        available_tools: List[Tool],
        force_tool_dc: bool = False
    ) -> ToolDCResult:
        """
        选择工具的主入口
        
        决策逻辑：
        - 工具数 <= fallback_threshold: 直接 ReAct（如启用）
        - 工具数 > fallback_threshold 或 force_tool_dc=True: 启用 Tool-DC
        
        Args:
            query: 用户查询
            available_tools: 所有可用工具
            force_tool_dc: 强制启用 Tool-DC
            
        Returns:
            ToolDCResult: 完整执行结果
        """
        start_time = time.time()
        
        result = ToolDCResult()
        
        # 检查是否需要启用 Tool-DC
        if not force_tool_dc and len(available_tools) <= self.config.fallback_threshold:
            logger.info(f"工具数 ({len(available_tools)}) <= 阈值，使用直接选择")
            result.fallback_used = True
            final_call = self._direct_select(query, available_tools)
            result.final_call = final_call
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
        
        logger.info(f"启用 Tool-DC (工具数: {len(available_tools)})")
        
        try:
            # === Stage 1: Try ===
            K = min(self.config.max_groups, len(available_tools))
            groups = self.try_stage.strategic_anchor_grouping(
                available_tools, query, K
            )
            
            # 并行/串行推理
            if self.config.parallel_inference:
                # TODO: 实现真正的并行
                candidates = self.try_stage.parallel_inference(query, groups)
            else:
                candidates = self.try_stage.parallel_inference(query, groups)
            
            result.try_candidates = candidates
            result.groups_processed = len(groups)
            
            logger.info(f"Try Stage: {len(candidates)} 个候选来自 {len(groups)} 个组")
            
            # 无候选，降级
            if not candidates:
                logger.warning("Try Stage 无候选，降级到直接选择")
                result.fallback_used = True
                result.final_call = self._direct_select(query, available_tools)
                result.execution_time_ms = (time.time() - start_time) * 1000
                return result
            
            # === Stage 2: Check ===
            valid_candidates = self.check_stage.batch_validate(
                candidates, available_tools
            )
            
            result.valid_candidates = valid_candidates
            result.validation_passed = len(valid_candidates)
            result.validation_failed = len(candidates) - len(valid_candidates)
            
            logger.info(f"Check Stage: {result.validation_passed} 通过, {result.validation_failed} 失败")
            
            # 无有效候选，降级
            if not valid_candidates:
                logger.warning("Check Stage 无有效候选，降级到直接选择")
                result.fallback_used = True
                result.final_call = self._direct_select(query, available_tools)
                result.execution_time_ms = (time.time() - start_time) * 1000
                return result
            
            # === Stage 3: Retry ===
            if len(valid_candidates) == 1:
                # 只有一个，直接选择
                result.final_call = valid_candidates[0]
                logger.info(f"只有一个有效候选，直接选择")
            else:
                # 多个候选，聚合决策
                final_call = self.retry_stage.global_aggregation(
                    query, valid_candidates, available_tools
                )
                result.final_call = final_call
            
        except Exception as e:
            logger.error(f"Tool-DC 执行失败: {e}", exc_info=True)
            # 异常时降级
            result.fallback_used = True
            result.final_call = self._direct_select(query, available_tools)
        
        result.execution_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Tool-DC 完成: 耗时 {result.execution_time_ms:.2f}ms, 成功={result.success}")
        
        return result
    
    def _direct_select(self, query: str, tools: List[Tool]) -> Optional[ToolCall]:
        """
        直接选择（降级策略）
        
        使用简单的 ReAct 方式
        """
        if not self.llm:
            return None
        
        tools_desc = self._format_tools_for_direct(tools)
        prompt = f"""根据用户问题选择合适的工具。

可用工具:
{tools_desc}

用户问题: {query}

输出格式: [func_name(param1=value1, param2=value2)]
如果没有合适工具，输出 NO_TOOL"""
        
        try:
            response = self.llm.generate(prompt)
            return self._parse_tool_call(response)
        except Exception as e:
            logger.error(f"直接选择失败: {e}")
            return None
    
    def _format_tools_for_direct(self, tools: List[Tool]) -> str:
        """格式化工具描述（直接选择用）"""
        lines = []
        for tool in tools:
            lines.append(f"- {tool.name}: {tool.description}")
            if tool.parameters:
                params = ", ".join(
                    f"{p.name}({p.type.value}{'*' if p.required else ''})"
                    for p in tool.parameters
                )
                lines.append(f"  参数: {params}")
        return "\n".join(lines)
    
    def _parse_tool_call(self, response: str) -> Optional[ToolCall]:
        """简单工具调用解析"""
        response = response.strip()
        
        if not response or response.upper() == "NO_TOOL":
            return None
        
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
            
        except Exception:
            return None
    
    def _convert_value(self, val: str):
        """转换值类型"""
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
    
    def execute_with_self_correction(
        self,
        query: str,
        tools: List[Tool],
        execute_fn: callable,
        max_attempts: int = 2
    ) -> dict:
        """
        执行工具调用，支持自我纠正
        
        Args:
            query: 用户查询
            tools: 可用工具
            execute_fn: 工具执行函数，接收 ToolCall，返回 (success, result/error)
            max_attempts: 最大尝试次数
            
        Returns:
            dict: 执行结果
        """
        for attempt in range(max_attempts):
            # 选择工具
            result = self.select_tool(query, tools)
            
            if not result.success:
                return {
                    "success": False,
                    "error": "工具选择失败",
                    "attempts": attempt + 1
                }
            
            call = result.final_call
            
            # 执行工具
            success, exec_result = execute_fn(call)
            
            if success:
                return {
                    "success": True,
                    "tool_call": call,
                    "result": exec_result,
                    "attempts": attempt + 1,
                    "tool_dc_result": result
                }
            
            # 执行失败，尝试自我纠正
            if attempt < max_attempts - 1 and self.config.enable_self_correction:
                logger.info(f"执行失败，尝试自我纠正 (尝试 {attempt + 1})")
                corrected = self.retry_stage.self_correction(
                    query, call, str(exec_result), tools
                )
                if corrected:
                    # 使用纠正后的调用继续
                    call = corrected
                    success, exec_result = execute_fn(call)
                    if success:
                        return {
                            "success": True,
                            "tool_call": call,
                            "result": exec_result,
                            "attempts": attempt + 2,
                            "corrected": True,
                            "tool_dc_result": result
                        }
        
        return {
            "success": False,
            "error": exec_result,
            "attempts": max_attempts,
            "final_call": call
        }


# 便捷函数
def create_tool_dc_handler(
    llm=None,
    retriever=None,
    config: Optional[ToolDCConfig] = None
) -> ToolDCHandler:
    """
    创建 Tool-DC 处理器的便捷函数
    
    Args:
        llm: LLM 实例
        retriever: 检索器实例
        config: 配置
        
    Returns:
        ToolDCHandler: 处理器实例
    """
    return ToolDCHandler(config=config, llm=llm, retriever=retriever)
