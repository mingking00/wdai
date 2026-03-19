"""
Kimi Multi-Agent Platform - Self-Check System
物理现实检查 + 验证驱动设计
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class CheckStatus(Enum):
    PASS = "pass"
    WARNING = "warning"
    BLOCK = "block"


@dataclass
class CheckResult:
    """检查结果"""
    check_name: str
    status: CheckStatus
    message: str
    suggestion: Optional[str] = None


class PhysicalRealityChecker:
    """
    物理现实检查器
    
    自动检查任务是否违反物理约束
    """
    
    # 时间相关关键词
    TIME_SENSITIVE_WORDS = [
        "立即", "马上", "立刻", "实时", "秒级", "毫秒",
        "instantly", "immediately", "real-time", "second", "millisecond"
    ]
    
    # 人类响应时间参考（分钟）
    HUMAN_RESPONSE_TIME = {
        "simple_task": 5,      # 简单任务
        "complex_task": 30,    # 复杂任务
        "review": 60,          # 审核
        "decision": 240,       # 决策
    }
    
    # 资源密集型关键词
    RESOURCE_INTENSIVE = [
        "所有", "全部", "每一个", "无限", "永远",
        "all", "every", "infinite", "forever", "unlimited"
    ]
    
    def __init__(self):
        self.checks = [
            self.check_human_response_time,
            self.check_resource_constraints,
            self.check_absolute_terms,
            self.check_time_scale,
        ]
    
    def check(self, task_description: str) -> List[CheckResult]:
        """
        执行所有检查
        
        Returns:
            检查结果列表
        """
        results = []
        for check_func in self.checks:
            result = check_func(task_description)
            if result:
                results.append(result)
        return results
    
    def check_human_response_time(self, task: str) -> Optional[CheckResult]:
        """检查是否假设人类能实时响应"""
        task_lower = task.lower()
        
        for word in ["人类", "human", "user", "用户"]:
            if word in task_lower:
                for time_word in self.TIME_SENSITIVE_WORDS:
                    if time_word in task_lower:
                        return CheckResult(
                            check_name="human_response_time",
                            status=CheckStatus.WARNING,
                            message=f"任务可能假设人类能'{time_word}'响应",
                            suggestion="人类响应通常是分钟级，设计应是非阻塞的，有超时机制"
                        )
        return None
    
    def check_resource_constraints(self, task: str) -> Optional[CheckResult]:
        """检查是否考虑资源限制"""
        task_lower = task.lower()
        
        # 检查是否涉及处理大量数据而没有限制
        if any(word in task_lower for word in ["所有文件", "所有数据", "全部"]):
            if "限制" not in task_lower and "limit" not in task_lower:
                return CheckResult(
                    check_name="resource_constraints",
                    status=CheckStatus.WARNING,
                    message="任务涉及'所有'资源但没有提到限制",
                    suggestion="考虑添加batch_size、max_items等限制，避免OOM"
                )
        
        return None
    
    def check_absolute_terms(self, task: str) -> Optional[CheckResult]:
        """检查是否使用绝对化词语"""
        task_lower = task.lower()
        
        absolutes = ["总是", "从不", "一定", "必须", "永远", 
                     "always", "never", "must", "forever"]
        
        found = [w for w in absolutes if w in task_lower]
        if found:
            return CheckResult(
                check_name="absolute_terms",
                status=CheckStatus.WARNING,
                message=f"任务使用绝对化词语: {found}",
                suggestion="'总是/从不'通常是过度推断，考虑边界条件和例外"
            )
        
        return None
    
    def check_time_scale(self, task: str) -> Optional[CheckResult]:
        """检查时间尺度是否合理"""
        task_lower = task.lower()
        
        # 检查是否涉及未来预测但没有时间范围
        if any(w in task_lower for w in ["预测", "forecast", "predict"]):
            if not any(w in task_lower for w in ["天", "周", "月", "年", "day", "week", "month", "year"]):
                return CheckResult(
                    check_name="time_scale",
                    status=CheckStatus.WARNING,
                    message="任务涉及预测但没有时间范围",
                    suggestion="明确预测时间范围（如：未来7天），长期预测误差大"
                )
        
        return None
    
    def format_report(self, results: List[CheckResult]) -> str:
        """格式化检查报告"""
        if not results:
            return "✅ 物理现实检查通过"
        
        lines = ["⚠️  物理现实检查警告:"]
        for r in results:
            icon = "🔴" if r.status == CheckStatus.BLOCK else "🟡"
            lines.append(f"\n{icon} {r.check_name}")
            lines.append(f"   问题: {r.message}")
            if r.suggestion:
                lines.append(f"   建议: {r.suggestion}")
        
        return "\n".join(lines)


class ValidationChecker:
    """
    验证流程检查器
    
    确保新设计经过验证
    """
    
    def __init__(self):
        self.validation_required_keywords = [
            "设计", "design", "架构", "architecture",
            "方案", "solution", "新模式", "new pattern"
        ]
    
    def should_validate(self, task: str) -> bool:
        """判断任务是否需要验证流程"""
        task_lower = task.lower()
        return any(kw in task_lower for kw in self.validation_required_keywords)
    
    def get_validation_checklist(self) -> List[str]:
        """获取验证检查清单"""
        return [
            "[ ] 小规模测试 - 原型验证",
            "[ ] 对照实验 - 与现有方案对比", 
            "[ ] 文献查证 - 有论文/数据支持吗？",
            "[ ] 统计显著 - 不是偶然结果",
            "[ ] 用户反馈 - 真实场景验证"
        ]
    
    def format_reminder(self) -> str:
        """格式化验证提醒"""
        lines = [
            "📋 验证流程提醒:",
            "这是一个新设计方案，需要验证:",
            ""
        ]
        lines.extend(self.get_validation_checklist())
        lines.append("\n⚠️  推广前先验证！")
        
        return "\n".join(lines)


class OverInferenceChecker:
    """
    过度推断检查器
    
    防止从单一案例过度推广
    """
    
    def check(self, task: str, history_count: int = 0) -> Optional[CheckResult]:
        """
        检查是否存在过度推断
        
        Args:
            task: 任务描述
            history_count: 历史成功案例数
        """
        task_lower = task.lower()
        
        # 从单一经验推断
        if history_count < 3:
            if any(w in task_lower for w in ["应该", "总是", "最佳", "optimal", "best"]):
                return CheckResult(
                    check_name="over_inference",
                    status=CheckStatus.WARNING,
                    message=f"基于{history_count}个案例推断'最佳实践'",
                    suggestion="需要至少3个成功案例才能总结规律，当前可能过度推断"
                )
        
        # 从个人经验推广
        if "我觉得" in task or "我认为" in task or "我的经验" in task:
            return CheckResult(
                check_name="personal_experience",
                status=CheckStatus.WARNING,
                message="基于个人经验，可能不是普适规律",
                suggestion="寻找更多证据，询问'这在其他场景也成立吗？'"
            )
        
        return None


class SelfCheckRunner:
    """
    自检运行器 - 整合所有检查
    
    每个Agent执行任务前自动运行
    """
    
    def __init__(self):
        self.physical_checker = PhysicalRealityChecker()
        self.validation_checker = ValidationChecker()
        self.inference_checker = OverInferenceChecker()
    
    def run_all_checks(self, task: str, history_count: int = 0) -> Tuple[bool, str]:
        """
        运行所有检查
        
        Returns:
            (should_proceed, report)
            should_proceed: 是否继续执行
            report: 检查报告
        """
        reports = []
        should_proceed = True
        
        # 1. 物理现实检查
        physical_results = self.physical_checker.check(task)
        if physical_results:
            reports.append(self.physical_checker.format_report(physical_results))
            # 有BLOCK级别则停止
            if any(r.status == CheckStatus.BLOCK for r in physical_results):
                should_proceed = False
        
        # 2. 验证流程检查
        if self.validation_checker.should_validate(task):
            reports.append(self.validation_checker.format_reminder())
        
        # 3. 过度推断检查
        inference_result = self.inference_checker.check(task, history_count)
        if inference_result:
            reports.append(f"⚠️  {inference_result.check_name}: {inference_result.message}")
            if inference_result.suggestion:
                reports.append(f"   建议: {inference_result.suggestion}")
        
        if not reports:
            return True, "✅ 所有自检通过"
        
        full_report = "\n\n".join(reports)
        return should_proceed, full_report


# 便捷函数
def check_task(task_description: str, history_count: int = 0) -> Tuple[bool, str]:
    """快速检查任务"""
    runner = SelfCheckRunner()
    return runner.run_all_checks(task_description, history_count)
