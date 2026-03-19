#!/usr/bin/env python3
"""
WDai Extended Constraints v1.0
扩展约束规则集

新增约束类别:
1. 数学约束 (Mathematical)
2. 时序约束 (Temporal)
3. 因果约束 (Causal)
4. 语言约束 (Linguistic)
5. 领域约束 (Domain-specific)
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from wdai_unified_v3 import Constraint, Context
from typing import Dict, List, Optional, Tuple, Any
import re
import math


# ============================================================================
# 数学约束
# ============================================================================

class MathematicalConstraint(Constraint):
    """
    数学约束
    
    验证数学陈述的正确性
    """
    
    name = "mathematical"
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """检查数学约束"""
        if not isinstance(data, str):
            return True, None
        
        # 提取数学表达式
        math_patterns = [
            r'(\d+)\s*+\s*(\d+)\s*=\s*(\d+)',  # a + b = c
            r'(\d+)\s*-\s*(\d+)\s*=\s*(\d+)',   # a - b = c
            r'(\d+)\s*\*\s*(\d+)\s*=\s*(\d+)',  # a * b = c
            r'(\d+)\s*/\s*(\d+)\s*=\s*(\d+)',   # a / b = c
        ]
        
        for pattern in math_patterns:
            match = re.search(pattern, data)
            if match:
                a, b, c = int(match.group(1)), int(match.group(2)), int(match.group(3))
                
                if '+' in pattern and a + b != c:
                    return False, f"数学错误: {a} + {b} ≠ {c}"
                elif '-' in pattern and a - b != c:
                    return False, f"数学错误: {a} - {b} ≠ {c}"
                elif '*' in pattern and a * b != c:
                    return False, f"数学错误: {a} × {b} ≠ {c}"
                elif '/' in pattern and b != 0 and a / b != c:
                    return False, f"数学错误: {a} ÷ {b} ≠ {c}"
        
        # 检查除以零
        if re.search(r'/\s*0[^\d]', data) or re.search(r'/\s*0$', data):
            return False, "数学错误: 除以零"
        
        # 检查概率范围
        prob_matches = re.findall(r'(\d+)%', data)
        for prob in prob_matches:
            if int(prob) > 100:
                return False, f"数学错误: 概率{prob}%超过100%"
        
        return True, None


# ============================================================================
# 时序约束
# ============================================================================

class TemporalConstraint(Constraint):
    """
    时序约束
    
    验证时间相关陈述的合理性
    """
    
    name = "temporal"
    
    IMPOSSIBLE_DATES = {
        '2023-02-29',  # 2023不是闰年
        '2023-02-30',
        '2023-04-31',  # 4月没有31日
        '2023-06-31',
        '2023-09-31',
        '2023-11-31',
    }
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """检查时序约束"""
        if not isinstance(data, str):
            return True, None
        
        # 检查不可能的日期
        for date in self.IMPOSSIBLE_DATES:
            if date in data:
                return False, f"时序错误: {date} 是不可能存在的日期"
        
        # 检查时间悖论
        time_patterns = [
            (r'(\d{4})年.*之后.*(\d{4})年.*之前', self._check_year_order),
            (r'(\d{1,2})月.*之后.*(\d{1,2})月.*之前', self._check_month_order),
        ]
        
        for pattern, checker in time_patterns:
            match = re.search(pattern, data)
            if match:
                valid, error = checker(match)
                if not valid:
                    return False, error
        
        # 检查"过去预测未来"悖论
        if '过去' in data and '预测' in data and '未来' in data:
            # 简化检查：如果明确说过去预测了现在的未来，那是正确的
            # 但如果暗示改变过去影响现在的未来，需要警告
            if '改变' in data or '修改' in data:
                return False, "时序悖论: 不能通过改变过去来影响现在"
        
        return True, None
    
    def _check_year_order(self, match) -> Tuple[bool, Optional[str]]:
        """检查年份顺序"""
        year1, year2 = int(match.group(1)), int(match.group(2))
        if year1 >= year2:
            return False, f"时序错误: {year1}年不能在{year2}年之后"
        return True, None
    
    def _check_month_order(self, match) -> Tuple[bool, Optional[str]]:
        """检查月份顺序"""
        month1, month2 = int(match.group(1)), int(match.group(2))
        if month1 >= month2:
            return False, f"时序错误: {month1}月不能在{month2}月之后"
        return True, None


# ============================================================================
# 因果约束
# ============================================================================

class CausalConstraint(Constraint):
    """
    因果约束
    
    验证因果关系的合理性
    """
    
    name = "causal"
    
    # 常见的因果谬误
    FALLACIES = {
        'post_hoc': [
            r'因为.*之后.*所以.*导致',  # 事后归因
            r'.*发生后.*就.*了，所以.*引起',
        ],
        'correlation_causation': [
            r'.*和.*相关，所以.*导致.*',  # 相关≠因果
            r'.*与.*有关，因此.*造成',
        ],
        'single_cause': [
            r'唯一原因.*是',  # 单一归因
            r'全部.*因为',
        ],
    }
    
    # 不可能的原因
    IMPOSSIBLE_CAUSES = [
        (r'鸡生蛋.*蛋生鸡', "因果循环: 鸡和蛋问题无法确定单一因果关系"),
        (r'死而复生', "违反生物学: 死亡不可逆"),
        (r'时光倒流', "违反物理学: 时间不可逆"),
    ]
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """检查因果约束"""
        if not isinstance(data, str):
            return True, None
        
        # 检查因果谬误
        for fallacy_type, patterns in self.FALLACIES.items():
            for pattern in patterns:
                if re.search(pattern, data):
                    return False, f"因果谬误 ({fallacy_type}): 需要更严谨的因果论证"
        
        # 检查不可能的原因
        for pattern, error_msg in self.IMPOSSIBLE_CAUSES:
            if re.search(pattern, data):
                return False, error_msg
        
        # 检查因果倒置
        if self._check_reverse_causation(data):
            return False, "因果倒置: 可能颠倒了因果关系"
        
        return True, None
    
    def _check_reverse_causation(self, text: str) -> bool:
        """检查可能的因果倒置"""
        # 简化实现：检查某些关键词组合
        reverse_indicators = [
            ('结果', '原因'),
            ('影响', '被影响'),
        ]
        
        for word1, word2 in reverse_indicators:
            if word1 in text and word2 in text:
                # 如果"结果"在"原因"之前出现，可能有问题
                idx1 = text.find(word1)
                idx2 = text.find(word2)
                if idx1 < idx2 and '其实' not in text:
                    return True
        
        return False


# ============================================================================
# 语言约束
# ============================================================================

class LinguisticConstraint(Constraint):
    """
    语言约束
    
    验证语言陈述的一致性和合理性
    """
    
    name = "linguistic"
    
    # 自相矛盾的表达
    CONTRADICTIONS = [
        (r'所有人.*都.*不', r'有人.*是'),  # 所有人都不是 vs 有人是
        (r'绝对.*可能', None),  # 绝对可能
        (r'肯定.*也许', None),  # 肯定也许
        (r'完全.*部分', None),  # 完全部分
        (r'永远.*暂时', None),  # 永远暂时
    ]
    
    # 滥用绝对化表述
    ABSOLUTISM = [
        r'所有.*都.*绝对',  # 过于绝对
        r'没有任何.*例外',  # 无例外声明
        r'百分之百.*肯定',  # 过度确定
    ]
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """检查语言约束"""
        if not isinstance(data, str):
            return True, None
        
        # 检查自相矛盾
        for pattern1, pattern2 in self.CONTRADICTIONS:
            if re.search(pattern1, data):
                if pattern2 and re.search(pattern2, data):
                    return False, "语言矛盾: 陈述自相矛盾"
                elif pattern2 is None:
                    return False, f"语言不当: '{pattern1}' 是矛盾或滥用表述"
        
        # 检查绝对化表述（警告级别）
        for pattern in self.ABSOLUTISM:
            if re.search(pattern, data):
                # 返回True但添加警告（不阻断）
                return True, f"⚠️ 语言警告: 使用了过度绝对化表述"
        
        return True, None


# ============================================================================
# 领域约束 - 医学
# ============================================================================

class MedicalConstraint(Constraint):
    """
    医学领域约束
    
    验证医学相关陈述的安全性
    """
    
    name = "medical"
    
    # 危险医疗建议
    DANGEROUS_ADVICE = [
        (r'停止.*药', "危险建议: 不应建议停止药物"),
        (r'加大.*剂量', "危险建议: 不应建议自行调整剂量"),
        (r'不用看医生', "危险建议: 不应建议跳过医疗咨询"),
        (r'偏方.*治愈', "危险建议: 不应推荐未经验证的偏方"),
        (r'绝对.*有效', "危险建议: 不应声称治疗方法绝对有效"),
    ]
    
    # 需要免责声明的内容
    DISCLAIMER_REQUIRED = [
        r'诊断.*为',
        r'患有.*病',
        r'治疗.*方法',
        r'症状.*表明',
    ]
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """检查医学约束"""
        if not isinstance(data, str):
            return True, None
        
        # 检查危险建议
        for pattern, error_msg in self.DANGEROUS_ADVICE:
            if re.search(pattern, data):
                return False, f"医疗安全: {error_msg}"
        
        # 检查是否缺少免责声明
        for pattern in self.DISCLAIMER_REQUIRED:
            if re.search(pattern, data):
                if '请咨询' not in data and '专业' not in data:
                    return True, "⚠️ 医疗警告: 医学建议应包含专业咨询提示"
        
        return True, None


# ============================================================================
# 领域约束 - 法律
# ============================================================================

class LegalConstraint(Constraint):
    """
    法律领域约束
    
    验证法律相关陈述的合规性
    """
    
    name = "legal"
    
    # 需要谨慎的表述
    LEGAL_CAUTION = [
        (r'构成.*犯罪', "法律建议: 犯罪认定应由司法机关做出"),
        (r'一定.*胜诉', "法律建议: 不应承诺诉讼结果"),
        (r'不用.*律师', "法律建议: 不应建议跳过专业法律咨询"),
        (r'绝对.*合法', "法律建议: 不应声称行为绝对合法"),
    ]
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """检查法律约束"""
        if not isinstance(data, str):
            return True, None
        
        # 检查需要谨慎的表述
        for pattern, warning in self.LEGAL_CAUTION:
            if re.search(pattern, data):
                return True, f"⚠️ 法律提示: {warning}"
        
        return True, None


# ============================================================================
# 领域约束 - 金融
# ============================================================================

class FinancialConstraint(Constraint):
    """
    金融领域约束
    
    验证金融相关陈述的合规性
    """
    
    name = "financial"
    
    # 禁止的投资建议
    PROHIBITED_ADVICE = [
        (r'保证.*收益', "金融合规: 不应承诺保证收益"),
        (r'肯定.*涨', "金融合规: 不应预测特定涨跌"),
        (r'内幕.*消息', "金融合规: 不应涉及内幕消息"),
        (r'稳赚.*不赔', "金融合规: 不应承诺无风险投资"),
    ]
    
    # 风险提示要求
    RISK_REQUIRED = [
        r'投资.*建议',
        r'买入.*卖出',
        r'股票.*推荐',
    ]
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """检查金融约束"""
        if not isinstance(data, str):
            return True, None
        
        # 检查禁止建议
        for pattern, error_msg in self.PROHIBITED_ADVICE:
            if re.search(pattern, data):
                return False, error_msg
        
        # 检查风险提示
        for pattern in self.RISK_REQUIRED:
            if re.search(pattern, data):
                if '风险' not in data and '不构成' not in data:
                    return True, "⚠️ 金融提示: 投资建议应包含风险提示"
        
        return True, None


# ============================================================================
# 扩展约束引擎
# ============================================================================

class ExtendedConstraintEngine:
    """
    扩展约束引擎
    
    整合所有约束规则
    """
    
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.violation_history: List[Dict] = []
        
        # 注册基础约束
        from wdai_unified_v3 import PhysicalRealityConstraint, LogicalConsistencyConstraint, SafetyConstraint
        self.register(PhysicalRealityConstraint())
        self.register(LogicalConsistencyConstraint())
        self.register(SafetyConstraint())
        
        # 注册扩展约束
        self.register(MathematicalConstraint())
        self.register(TemporalConstraint())
        self.register(CausalConstraint())
        self.register(LinguisticConstraint())
        self.register(MedicalConstraint())
        self.register(LegalConstraint())
        self.register(FinancialConstraint())
    
    def register(self, constraint: Constraint):
        """注册约束"""
        self.constraints.append(constraint)
    
    def validate(self, data: Any, context: Context) -> Tuple[bool, List[Dict]]:
        """
        执行完整验证
        
        Returns:
            (是否通过, 所有违规/警告列表)
        """
        issues = []
        
        # 按优先级排序
        priority_order = {
            'safety': 0,
            'medical': 1,
            'financial': 2,
            'legal': 3,
            'physical_reality': 4,
            'mathematical': 5,
            'temporal': 6,
            'causal': 7,
            'logical_consistency': 8,
            'linguistic': 9,
        }
        
        sorted_constraints = sorted(
            self.constraints,
            key=lambda c: priority_order.get(c.name, 99)
        )
        
        for constraint in sorted_constraints:
            passed, message = constraint.check(data, context)
            
            if not passed:
                issue = {
                    'constraint': constraint.name,
                    'severity': 'error',
                    'message': message
                }
                issues.append(issue)
                self.violation_history.append(issue)
            elif message and message.startswith('⚠️'):
                # 警告级别
                issues.append({
                    'constraint': constraint.name,
                    'severity': 'warning',
                    'message': message
                })
        
        # 只要没有error就算通过
        errors = [i for i in issues if i['severity'] == 'error']
        return len(errors) == 0, issues
    
    def get_constraint_summary(self) -> Dict:
        """获取约束统计"""
        return {
            '总约束数': len(self.constraints),
            '违规历史': len(self.violation_history),
            '约束类型': [c.name for c in self.constraints]
        }


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Extended Constraints - 测试")
    print("="*60)
    
    # 创建约束引擎
    engine = ExtendedConstraintEngine()
    
    # 创建测试上下文
    context = Context(session_id="test", query_id="test_001")
    
    # 测试用例
    test_cases = [
        # 数学约束
        ("2 + 2 = 5", "数学错误"),
        ("100% + 10% = 110%", "通过"),
        
        # 时序约束
        ("2023年2月29日的事件", "时序错误"),
        ("2020年2月29日的事件", "通过（闰年）"),
        
        # 因果约束
        ("因为下雨之后地面湿了，所以下雨导致地面湿", "因果谬误"),
        ("死而复生的方法", "不可能原因"),
        
        # 语言约束
        ("所有人都不喜欢，但有人喜欢", "自相矛盾"),
        ("绝对可能的情况", "语言不当"),
        
        # 医学约束
        ("停止你的药，用我的偏方", "危险建议"),
        ("你可能患有感冒，请咨询医生", "通过"),
        
        # 金融约束
        ("保证收益20%", "禁止建议"),
        ("投资有风险，不构成建议", "通过"),
        
        # 遗传学约束
        ({'genetics': {
            'trait': 'color_blindness',
            'father_normal': True,
            'mother_normal': True,
            'child_affected': True
        }}, "遗传学违规"),
    ]
    
    print(f"\n运行 {len(test_cases)} 个测试用例:\n")
    
    for i, (test_input, expected) in enumerate(test_cases, 1):
        passed, issues = engine.validate(test_input, context)
        
        status = "✅" if passed else "❌"
        print(f"{status} 测试{i}: {expected}")
        
        if issues:
            for issue in issues:
                severity = "🔴" if issue['severity'] == 'error' else "🟡"
                print(f"   {severity} [{issue['constraint']}] {issue['message']}")
    
    # 约束统计
    print("\n📊 约束统计")
    summary = engine.get_constraint_summary()
    for k, v in summary.items():
        if k == '约束类型':
            print(f"   {k}:")
            for name in v:
                print(f"      - {name}")
        else:
            print(f"   {k}: {v}")
    
    print("\n" + "="*60)
    print("✅ 扩展约束测试完成")
    print("="*60)
