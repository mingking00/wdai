"""
Kimi Platform - Evaluation Framework
评估框架设计（基于第16轮学习）
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class MetricCategory(Enum):
    """评估指标类别"""
    GOAL_FULFILLMENT = "goal_fulfillment"      # 目标完成
    RESPONSE_QUALITY = "response_quality"      # 响应质量
    EFFICIENCY = "efficiency"                  # 效率
    ROBUSTNESS = "robustness"                  # 鲁棒性


@dataclass
class MetricResult:
    """指标结果"""
    metric_name: str
    score: float  # 0-1
    category: MetricCategory
    details: Dict[str, Any]
    passed: bool  # 是否通过阈值


class BaseMetric(ABC):
    """评估指标基类"""
    
    def __init__(self, name: str, threshold: float = 0.8):
        self.name = name
        self.threshold = threshold
    
    @abstractmethod
    def evaluate(self, task: Any, output: Any, context: Dict = None) -> MetricResult:
        """评估指标"""
        pass


class TaskCompletionMetric(BaseMetric):
    """
    任务完成度指标
    
    评估Agent是否完成了任务的预期目标
    """
    
    def __init__(self, threshold: float = 0.8):
        super().__init__("task_completion", threshold)
        self.category = MetricCategory.GOAL_FULFILLMENT
    
    def evaluate(self, task: Any, output: Any, context: Dict = None) -> MetricResult:
        """
        评估任务完成度
        
        简化实现：检查output是否为空/错误
        完整实现：应该用LLM判断output是否满足task目标
        """
        context = context or {}
        
        # 基础检查
        if output is None or output == "":
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                category=self.category,
                details={"error": "Empty output"},
                passed=False
            )
        
        if isinstance(output, dict) and "error" in output:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                category=self.category,
                details={"error": output["error"]},
                passed=False
            )
        
        # 简化评分：假设非空即部分完成
        # 完整实现应该用LLM-as-Judge评估
        score = 1.0
        
        return MetricResult(
            metric_name=self.name,
            score=score,
            category=self.category,
            details={"output_type": type(output).__name__},
            passed=score >= self.threshold
        )


class ToolCorrectnessMetric(BaseMetric):
    """
    工具调用正确性指标
    
    评估Agent是否调用了正确的工具，参数是否正确
    """
    
    def __init__(self, threshold: float = 0.8):
        super().__init__("tool_correctness", threshold)
        self.category = MetricCategory.RESPONSE_QUALITY
    
    def evaluate(self, task: Any, output: Any, context: Dict = None) -> MetricResult:
        """
        评估工具调用正确性
        
        需要context中包含:
        - expected_tool: 期望调用的工具名
        - actual_tool: 实际调用的工具名
        - expected_params: 期望的参数
        - actual_params: 实际的参数
        """
        context = context or {}
        
        expected_tool = context.get("expected_tool")
        actual_tool = context.get("actual_tool")
        
        if not expected_tool:
            return MetricResult(
                metric_name=self.name,
                score=1.0,  # 无期望值，默认通过
                category=self.category,
                details={"note": "No expected tool specified"},
                passed=True
            )
        
        # 工具匹配检查
        tool_match = expected_tool == actual_tool
        
        # 参数匹配检查（简化）
        expected_params = context.get("expected_params", {})
        actual_params = context.get("actual_params", {})
        
        if expected_params and actual_params:
            # 检查关键参数
            param_matches = sum(
                1 for k, v in expected_params.items()
                if k in actual_params and actual_params[k] == v
            )
            param_score = param_matches / len(expected_params) if expected_params else 1.0
        else:
            param_score = 1.0
        
        # 综合评分
        score = (0.6 if tool_match else 0.0) + (0.4 * param_score)
        
        return MetricResult(
            metric_name=self.name,
            score=score,
            category=self.category,
            details={
                "tool_match": tool_match,
                "param_score": param_score,
                "expected_tool": expected_tool,
                "actual_tool": actual_tool
            },
            passed=score >= self.threshold
        )


class LatencyMetric(BaseMetric):
    """
    延迟指标
    
    评估Agent响应时间是否在可接受范围内
    """
    
    def __init__(self, max_latency_ms: float = 5000):
        super().__init__("latency", threshold=0.9)
        self.max_latency_ms = max_latency_ms
        self.category = MetricCategory.EFFICIENCY
    
    def evaluate(self, task: Any, output: Any, context: Dict = None) -> MetricResult:
        """
        评估延迟
        
        需要context中包含:
        - latency_ms: 实际延迟（毫秒）
        """
        context = context or {}
        latency_ms = context.get("latency_ms", 0)
        
        # 计算分数（越低越好）
        if latency_ms <= self.max_latency_ms:
            score = 1.0
        else:
            # 超出部分线性扣分
            over_ratio = (latency_ms - self.max_latency_ms) / self.max_latency_ms
            score = max(0.0, 1.0 - over_ratio)
        
        return MetricResult(
            metric_name=self.name,
            score=score,
            category=self.category,
            details={
                "latency_ms": latency_ms,
                "max_latency_ms": self.max_latency_ms
            },
            passed=score >= self.threshold
        )


class TokenEfficiencyMetric(BaseMetric):
    """
    Token效率指标
    
    评估Agent是否高效使用Token（推理时计算）
    """
    
    def __init__(self, max_tokens: int = 2000):
        super().__init__("token_efficiency", threshold=0.8)
        self.max_tokens = max_tokens
        self.category = MetricCategory.EFFICIENCY
    
    def evaluate(self, task: Any, output: Any, context: Dict = None) -> MetricResult:
        """
        评估Token效率
        
        需要context中包含:
        - tokens_used: 使用的Token数
        """
        context = context or {}
        tokens_used = context.get("tokens_used", 0)
        
        # 计算分数
        if tokens_used <= self.max_tokens:
            score = 1.0
        else:
            over_ratio = (tokens_used - self.max_tokens) / self.max_tokens
            score = max(0.0, 1.0 - over_ratio)
        
        return MetricResult(
            metric_name=self.name,
            score=score,
            category=self.category,
            details={
                "tokens_used": tokens_used,
                "max_tokens": self.max_tokens
            },
            passed=score >= self.threshold
        )


class EvaluationFramework:
    """
    评估框架主类
    
    管理所有指标，执行综合评估
    """
    
    def __init__(self):
        self.metrics: List[BaseMetric] = []
        self.history: List[Dict] = []
    
    def add_metric(self, metric: BaseMetric) -> "EvaluationFramework":
        """添加指标"""
        self.metrics.append(metric)
        return self
    
    def evaluate(self, task: Any, output: Any, context: Dict = None) -> Dict:
        """
        执行综合评估
        
        Returns:
            {
                "overall_score": float,
                "passed": bool,
                "results": List[MetricResult],
                "category_scores": Dict[str, float]
            }
        """
        context = context or {}
        results = []
        
        for metric in self.metrics:
            result = metric.evaluate(task, output, context)
            results.append(result)
        
        # 计算综合分数
        if results:
            overall_score = sum(r.score for r in results) / len(results)
            passed = all(r.passed for r in results)
            
            # 按类别汇总
            category_scores = {}
            for category in MetricCategory:
                category_results = [r for r in results if r.category == category]
                if category_results:
                    category_scores[category.value] = sum(r.score for r in category_results) / len(category_results)
        else:
            overall_score = 0.0
            passed = False
            category_scores = {}
        
        evaluation_result = {
            "overall_score": overall_score,
            "passed": passed,
            "results": results,
            "category_scores": category_scores,
            "timestamp": __import__('time').time()
        }
        
        # 记录历史
        self.history.append(evaluation_result)
        
        return evaluation_result
    
    def get_default_framework() -> "EvaluationFramework":
        """获取默认评估框架"""
        framework = EvaluationFramework()
        framework.add_metric(TaskCompletionMetric())
        framework.add_metric(ToolCorrectnessMetric())
        framework.add_metric(LatencyMetric())
        framework.add_metric(TokenEfficiencyMetric())
        return framework
    
    def print_report(self, result: Dict) -> str:
        """打印评估报告"""
        lines = [
            "=" * 60,
            "EVALUATION REPORT",
            "=" * 60,
            f"Overall Score: {result['overall_score']:.2f}",
            f"Status: {'✅ PASSED' if result['passed'] else '❌ FAILED'}",
            "",
            "Category Scores:",
        ]
        
        for category, score in result['category_scores'].items():
            lines.append(f"  • {category}: {score:.2f}")
        
        lines.extend(["", "Detailed Results:"])
        
        for r in result['results']:
            status = "✅" if r.passed else "❌"
            lines.append(f"  {status} {r.metric_name}: {r.score:.2f}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
