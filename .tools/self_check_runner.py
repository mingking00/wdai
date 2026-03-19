#!/usr/bin/env python3
"""
Self-Check Runner - 自检运行器
将内化的原则转化为可执行代码

每次任务开始时自动运行：
1. 物理现实检查
2. 验证流程检查  
3. 过度推断警告
4. 假设标记
"""

import sys
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class CheckStatus(Enum):
    PASS = "✅"
    WARNING = "⚠️"
    FAIL = "❌"
    SKIP = "⏭️"

@dataclass
class CheckResult:
    check_name: str
    status: CheckStatus
    message: str
    action_required: str

class PhysicalRealityChecker:
    """物理现实检查器"""
    
    # 已知的物理约束（持续更新）
    PHYSICAL_CONSTRAINTS = {
        "人类": {
            "response_time": "minutes to hours",
            "attention_span": "20 minutes",
            "work_hours": "8h/day"
        },
        "网络": {
            "latency_min": "1ms (same datacenter)",
            "latency_cross_region": "50-200ms",
            "bandwidth": "finite"
        },
        "计算": {
            "cpu": "finite cores",
            "memory": "finite RAM",
            "time": "proportional_to_complexity"
        }
    }
    
    def check(self, task_description: str) -> CheckResult:
        """检查任务是否涉及物理约束"""
        
        # 识别涉及的真实世界实体
        entities = self._extract_entities(task_description)
        
        if not entities:
            return CheckResult(
                check_name="物理现实检查",
                status=CheckStatus.SKIP,
                message="不涉及真实世界实体",
                action_required="无需检查"
            )
        
        # 检查每个实体的物理约束
        violations = []
        for entity in entities:
            if entity in self.PHYSICAL_CONSTRAINTS:
                constraint = self.PHYSICAL_CONSTRAINTS[entity]
                # 检查任务描述中是否有违反约束的假设
                violation = self._check_constraint_violation(
                    task_description, entity, constraint
                )
                if violation:
                    violations.append(violation)
        
        if violations:
            return CheckResult(
                check_name="物理现实检查",
                status=CheckStatus.WARNING,
                message=f"; ".join(violations),
                action_required="验证物理约束或查阅文献"
            )
        
        return CheckResult(
            check_name="物理现实检查",
            status=CheckStatus.PASS,
            message=f"涉及实体: {', '.join(entities)}，已检查物理约束",
            action_required="继续执行"
        )
    
    def _extract_entities(self, text: str) -> List[str]:
        """提取文本中的真实世界实体"""
        entities = []
        keywords = ["人类", "用户", "网络", "服务器", "实时", "同步"]
        for kw in keywords:
            if kw in text:
                entities.append(kw)
        return entities
    
    def _check_constraint_violation(
        self, text: str, entity: str, constraint: Dict
    ) -> str:
        """检查是否有违反约束的描述"""
        # 简单启发式检查
        if entity == "人类" and ("实时" in text or "立即" in text):
            return f"'人类' + '实时/立即' 可能违反物理约束 (人类响应: 分钟到小时级)"
        return ""


class ValidationChecker:
    """验证流程检查器"""
    
    def check(self, is_new_design: bool) -> CheckResult:
        """检查是否需要验证"""
        
        if not is_new_design:
            return CheckResult(
                check_name="验证流程检查",
                status=CheckStatus.SKIP,
                message="不是新设计方案",
                action_required="无需验证"
            )
        
        return CheckResult(
            check_name="验证流程检查",
            status=CheckStatus.WARNING,
            message="新设计方案需要进行验证",
            action_required="1)小规模测试 2)对照实验 3)文献查证"
        )


class OverInferenceChecker:
    """过度推断检查器"""
    
    WARNING_PATTERNS = [
        ("从单一案例推广", "学习Redis → 所有系统都应该简单"),
        ("从个人经验推广", "我见过...所以所有情况都..."),
        ("绝对化表述", "总是、从不、一定、必须"),
    ]
    
    def check(self, reasoning: str) -> CheckResult:
        """检查是否有过度推断"""
        
        for pattern_type, example in self.WARNING_PATTERNS:
            if pattern_type in reasoning or self._has_absolute_words(reasoning):
                return CheckResult(
                    check_name="过度推断检查",
                    status=CheckStatus.WARNING,
                    message=f"可能存在{pattern_type}: {example}",
                    action_required="寻找更多案例验证，或查阅文献支持"
                )
        
        return CheckResult(
            check_name="过度推断检查",
            status=CheckStatus.PASS,
            message="未发现明显的过度推断",
            action_required="继续执行"
        )
    
    def _has_absolute_words(self, text: str) -> bool:
        """检查是否有绝对化词语"""
        absolute_words = ["总是", "从不", "一定", "必须", "所有", "任何"]
        return any(word in text for word in absolute_words)


class SelfCheckRunner:
    """自检运行器"""
    
    def __init__(self):
        self.checkers = {
            "physical": PhysicalRealityChecker(),
            "validation": ValidationChecker(),
            "inference": OverInferenceChecker()
        }
    
    def run_all_checks(self, task_context: Dict) -> List[CheckResult]:
        """运行所有检查"""
        
        results = []
        
        # 1. 物理现实检查
        task_desc = task_context.get("task_description", "")
        results.append(self.checkers["physical"].check(task_desc))
        
        # 2. 验证流程检查
        is_new_design = task_context.get("is_new_design", False)
        results.append(self.checkers["validation"].check(is_new_design))
        
        # 3. 过度推断检查
        reasoning = task_context.get("reasoning", "")
        results.append(self.checkers["inference"].check(reasoning))
        
        return results
    
    def print_report(self, results: List[CheckResult]):
        """打印检查报告"""
        print("\n" + "="*70)
        print("🔍 自检报告 (Self-Check Report)")
        print("="*70)
        
        warnings = 0
        for result in results:
            print(f"\n{result.status.value} {result.check_name}")
            print(f"   信息: {result.message}")
            if result.status == CheckStatus.WARNING:
                print(f"   行动: {result.action_required}")
                warnings += 1
        
        print("\n" + "-"*70)
        if warnings > 0:
            print(f"⚠️  发现 {warnings} 个警告，请处理后再继续")
        else:
            print("✅ 所有检查通过，可以继续执行")
        print("="*70)


# 使用示例
def example_usage():
    """使用示例"""
    
    runner = SelfCheckRunner()
    
    # 场景1: 设计涉及人类审核的系统
    context1 = {
        "task_description": "设计一个系统，人类实时审核每个Agent输出",
        "is_new_design": True,
        "reasoning": "从Redis学习，单线程简单，所以人类审核应该立即响应"
    }
    
    print("\n场景1: 设计人类实时审核系统")
    results1 = runner.run_all_checks(context1)
    runner.print_report(results1)
    
    # 场景2: 设计文件读写系统
    context2 = {
        "task_description": "实现文件读取功能",
        "is_new_design": False,
        "reasoning": "使用标准库函数"
    }
    
    print("\n\n场景2: 实现文件读取")
    results2 = runner.run_all_checks(context2)
    runner.print_report(results2)


if __name__ == "__main__":
    example_usage()
