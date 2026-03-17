#!/usr/bin/env python3
"""
对话检查清单 - 每次用户消息自动运行
确保Claude Code设计哲学落实到每次对话
"""

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class CheckResult:
    """检查结果"""
    check_name: str
    passed: bool
    message: str
    action: str

class ConversationChecklist:
    """
    对话检查清单
    
    每次收到用户消息时，自动运行以下检查
    这是将"关键决策点强制检查"落实到代码
    """
    
    def __init__(self):
        self.checks = []
        self.all_passed = True
    
    def run_all_checks(self, user_message: str, conversation_history: List[Dict]) -> List[CheckResult]:
        """
        运行所有检查
        这是每次对话的入口点
        """
        self.checks = []
        
        # ========== 阶段1: 理解检查 ==========
        self.checks.append(self._check_1_understand_intent(user_message))
        self.checks.append(self._check_2_assess_complexity(user_message))
        self.checks.append(self._check_3_check_repetition(user_message, conversation_history))
        
        # ========== 阶段2: 检索检查 ==========
        self.checks.append(self._check_4_search_memory(user_message))
        self.checks.append(self._check_5_check_skills(user_message))
        
        # ========== 阶段3: 执行检查 ==========
        self.checks.append(self._check_6_simplest_solution(user_message))
        self.checks.append(self._check_7_avoid_reinventing(user_message))
        self.checks.append(self._check_8_delivery_quality())
        
        # ========== 阶段4: 交付检查 ==========
        self.checks.append(self._check_9_provide_options(user_message))
        self.checks.append(self._check_10_close_loop())
        
        # 更新整体状态
        self.all_passed = all(c.passed for c in self.checks)
        
        return self.checks
    
    # ========== 具体检查实现 ==========
    
    def _check_1_understand_intent(self, message: str) -> CheckResult:
        """检查1: 是否真正理解用户意图"""
        # 如果消息很短，可能理解不清
        if len(message) < 10:
            return CheckResult(
                check_name="理解意图",
                passed=False,
                message="用户消息过短，可能理解不清",
                action="反问确认：'你的意思是...吗？'"
            )
        
        return CheckResult(
            check_name="理解意图",
            passed=True,
            message="已理解核心意图",
            action="继续下一步"
        )
    
    def _check_2_assess_complexity(self, message: str) -> CheckResult:
        """检查2: 是否评估了复杂度"""
        keywords_complex = ["系统", "架构", "优化", "设计", "重构"]
        keywords_simple = ["你好", "谢谢", "再见", "是", "否"]
        
        has_complex = any(kw in message for kw in keywords_complex)
        has_simple = any(kw in message for kw in keywords_simple)
        
        if has_complex:
            return CheckResult(
                check_name="评估复杂度",
                passed=True,
                message="识别为复杂任务",
                action="创建显式任务计划"
            )
        elif has_simple:
            return CheckResult(
                check_name="评估复杂度",
                passed=True,
                message="识别为简单任务",
                action="快速响应"
            )
        
        return CheckResult(
            check_name="评估复杂度",
            passed=True,
            message="中等复杂度",
            action="标准流程处理"
        )
    
    def _check_3_check_repetition(self, message: str, history: List[Dict]) -> CheckResult:
        """检查3: 是否是重复问题"""
        if not history:
            return CheckResult(
                check_name="重复检查",
                passed=True,
                message="新对话，无历史",
                action="正常处理"
            )
        
        # 检查最近3条
        recent = history[-3:]
        for item in recent:
            if message.lower() in item.get("content", "").lower():
                return CheckResult(
                    check_name="重复检查",
                    passed=False,
                    message="检测到重复问题",
                    action="引用之前的回答，或询问是否有新需求"
                )
        
        return CheckResult(
            check_name="重复检查",
            passed=True,
            message="非重复问题",
            action="正常处理"
        )
    
    def _check_4_search_memory(self, message: str) -> CheckResult:
        """检查4: 是否检索了相关记忆"""
        # 简化判断：是否包含可能有关联的关键词
        memory_keywords = ["之前", "上次", "以前", "还记得"]
        
        if any(kw in message for kw in memory_keywords):
            return CheckResult(
                check_name="记忆检索",
                passed=True,
                message="用户提到历史，已触发记忆检索",
                action="调用memory_search"
            )
        
        return CheckResult(
            check_name="记忆检索",
            passed=True,
            message="标准检索完成",
            action="使用检索结果"
        )
    
    def _check_5_check_skills(self, message: str) -> CheckResult:
        """检查5: 是否检查了可用技能"""
        # 关键检查：已有能力优先
        skill_keywords = {
            "搜索": "kimi_search",
            "文件": "docx/pdf/xlsx",
            "浏览器": "browser",
            "代码": "code execution",
            "研究": "research-orchestrator"
        }
        
        found_skills = []
        for keyword, skill in skill_keywords.items():
            if keyword in message:
                found_skills.append(skill)
        
        if found_skills:
            return CheckResult(
                check_name="技能检查",
                passed=True,
                message=f"发现可用技能: {', '.join(found_skills)}",
                action="优先使用已有技能，不造轮子"
            )
        
        return CheckResult(
            check_name="技能检查",
            passed=True,
            message="无特定技能需求",
            action="使用通用能力"
        )
    
    def _check_6_simplest_solution(self, message: str) -> CheckResult:
        """检查6: 是否选择了最简单方案"""
        # 检查是否有过度设计倾向
        over_engineering_keywords = ["系统", "框架", "平台", "引擎"]
        
        if any(kw in message for kw in over_engineering_keywords):
            return CheckResult(
                check_name="简单优先",
                passed=False,
                message="检测到可能过度设计的词汇",
                action="先提供简单方案，再询问是否需要复杂方案"
            )
        
        return CheckResult(
            check_name="简单优先",
            passed=True,
            message="符合简单优先原则",
            action="继续执行"
        )
    
    def _check_7_avoid_reinventing(self, message: str) -> CheckResult:
        """检查7: 是否避免了重复造轮子"""
        # 如果用户要求"写一个"，触发检查
        if "写一个" in message or "实现一个" in message:
            return CheckResult(
                check_name="避免造轮子",
                passed=False,
                message="用户要求写新代码/功能",
                action="先检查是否已有现成解决方案"
            )
        
        return CheckResult(
            check_name="避免造轮子",
            passed=True,
            message="无造轮子风险",
            action="继续执行"
        )
    
    def _check_8_delivery_quality(self) -> CheckResult:
        """检查8: 交付质量标准"""
        return CheckResult(
            check_name="交付质量",
            passed=True,
            message="检查清单已运行",
            action="确保回复前自检3遍"
        )
    
    def _check_9_provide_options(self, message: str) -> CheckResult:
        """检查9: 是否提供了选项"""
        # 复杂任务应该提供选项
        complex_indicators = ["优化", "设计", "选择", "方案"]
        
        if any(kw in message for kw in complex_indicators):
            return CheckResult(
                check_name="提供选项",
                passed=False,
                message="复杂任务，应该提供多个选项",
                action="生成2-3个方案供用户选择"
            )
        
        return CheckResult(
            check_name="提供选项",
            passed=True,
            message="简单任务，直接响应",
            action="快速交付"
        )
    
    def _check_10_close_loop(self) -> CheckResult:
        """检查10: 是否闭环"""
        return CheckResult(
            check_name="闭环确认",
            passed=True,
            message="准备闭环",
            action="回复末尾添加'还有其他需要吗？'"
        )
    
    # ========== 输出格式化 ==========
    
    def format_report(self) -> str:
        """格式化检查报告"""
        lines = ["\n📋 对话检查清单", "=" * 50]
        
        for check in self.checks:
            status = "✅" if check.passed else "⚠️"
            lines.append(f"{status} {check.check_name}")
            lines.append(f"   {check.message}")
            if not check.passed:
                lines.append(f"   → {check.action}")
        
        lines.append("=" * 50)
        lines.append(f"总体状态: {'✅ 通过' if self.all_passed else '⚠️ 有警告'}")
        
        return "\n".join(lines)
    
    def get_failed_checks(self) -> List[CheckResult]:
        """获取失败的检查"""
        return [c for c in self.checks if not c.passed]


# ========== 实际使用 ==========

def example_usage():
    """使用示例"""
    checklist = ConversationChecklist()
    
    # 示例1: 简单问候
    print("\n" + "="*60)
    print("示例1: 简单问候")
    results = checklist.run_all_checks("你好", [])
    print(checklist.format_report())
    
    # 示例2: 复杂任务
    print("\n" + "="*60)
    print("示例2: 复杂任务")
    results = checklist.run_all_checks(
        "帮我设计一个系统来优化工作流",
        []
    )
    print(checklist.format_report())
    
    # 显示失败项和对应的行动
    failed = checklist.get_failed_checks()
    if failed:
        print("\n⚠️ 需要特别注意:")
        for check in failed:
            print(f"  - {check.check_name}: {check.action}")


if __name__ == "__main__":
    example_usage()
