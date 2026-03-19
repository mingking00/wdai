"""
Tool-DC Parallel Inference

真正的并行推理实现
"""

import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .models import Tool, ToolCall
from .config import ToolDCConfig
from .parsers import ToolCallParser

logger = logging.getLogger(__name__)


class ParallelInferenceEngine:
    """
    并行推理引擎
    
    使用 ThreadPoolExecutor 实现真正的并行 LLM 调用
    """
    
    def __init__(self, config: ToolDCConfig):
        self.config = config
        self.executor = None
    
    def execute(
        self,
        query: str,
        groups: List[List[Tool]],
        llm,
        prompt_builder
    ) -> List[ToolCall]:
        """
        并行执行各组推理
        
        Args:
            query: 用户查询
            groups: 分组列表
            llm: LLM 实例
            prompt_builder: 构建 Prompt 的函数
            
        Returns:
            List[ToolCall]: 所有候选调用
        """
        if not self.config.parallel_inference or len(groups) <= 1:
            # 串行执行
            return self._sequential_execute(query, groups, llm, prompt_builder)
        
        # 并行执行
        return self._parallel_execute(query, groups, llm, prompt_builder)
    
    def _sequential_execute(
        self,
        query: str,
        groups: List[List[Tool]],
        llm,
        prompt_builder
    ) -> List[ToolCall]:
        """串行执行"""
        candidates = []
        
        for i, group in enumerate(groups):
            try:
                prompt = prompt_builder(query, group)
                response = llm.generate(prompt)
                call = self._parse_response(response, i)
                if call:
                    candidates.append(call)
            except Exception as e:
                logger.error(f"组 {i} 推理失败: {e}")
        
        return candidates
    
    def _parallel_execute(
        self,
        query: str,
        groups: List[List[Tool]],
        llm,
        prompt_builder
    ) -> List[ToolCall]:
        """并行执行"""
        candidates = []
        max_workers = min(self.config.max_workers, len(groups))
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_group = {}
            for i, group in enumerate(groups):
                prompt = prompt_builder(query, group)
                future = executor.submit(self._inference_task, llm, prompt, i)
                future_to_group[future] = i
            
            # 收集结果
            for future in as_completed(future_to_group):
                group_idx = future_to_group[future]
                try:
                    call = future.result(timeout=30)  # 30秒超时
                    if call:
                        candidates.append(call)
                        logger.debug(f"组 {group_idx} 完成")
                except Exception as e:
                    logger.error(f"组 {group_idx} 失败: {e}")
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"并行推理完成: {len(groups)} 组, {len(candidates)} 候选, {elapsed:.2f}ms")
        
        return candidates
    
    def _inference_task(self, llm, prompt: str, group_idx: int) -> Optional[ToolCall]:
        """单个推理任务"""
        try:
            response = llm.generate(prompt)
            return self._parse_response(response, group_idx)
        except Exception as e:
            logger.error(f"推理任务失败: {e}")
            return None
    
    def _parse_response(self, response: str, group_idx: int) -> Optional[ToolCall]:
        """解析响应"""
        parser = ToolCallParser()
        call = parser.parse(response)
        if call:
            call.source_group = group_idx
        return call
    
    def benchmark(
        self,
        query: str,
        groups: List[List[Tool]],
        llm,
        prompt_builder,
        iterations: int = 3
    ) -> dict:
        """
        性能基准测试
        
        对比串行 vs 并行性能
        """
        results = {
            "sequential": [],
            "parallel": [],
            "groups": len(groups),
            "iterations": iterations
        }
        
        # 串行测试
        for _ in range(iterations):
            start = time.time()
            _ = self._sequential_execute(query, groups, llm, prompt_builder)
            results["sequential"].append((time.time() - start) * 1000)
        
        # 并行测试
        for _ in range(iterations):
            start = time.time()
            _ = self._parallel_execute(query, groups, llm, prompt_builder)
            results["parallel"].append((time.time() - start) * 1000)
        
        # 统计
        results["sequential_avg"] = sum(results["sequential"]) / iterations
        results["parallel_avg"] = sum(results["parallel"]) / iterations
        results["speedup"] = results["sequential_avg"] / results["parallel_avg"] if results["parallel_avg"] > 0 else 0
        
        return results
