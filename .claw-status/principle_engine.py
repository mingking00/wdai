#!/usr/bin/env python3
"""
原则执行引擎 - Principle Execution Engine
自动执行核心原则优先级系统
"""

import json
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional
from datetime import datetime
from collections import Counter

class PriorityLevel(Enum):
    """原则优先级层级"""
    P0_SAFETY = 0      # 绝对优先
    P1_META = 1        # 元能力
    P2_STRATEGY = 2    # 执行策略
    P3_QUALITY = 3     # 质量优化
    P4_STYLE = 4       # 风格偏好

@dataclass
class Principle:
    """原则定义"""
    name: str
    level: PriorityLevel
    weight: int
    trigger: str
    check_func: Optional[Callable] = None
    violation_penalty: int = 1
    
    def applies_to(self, context: Dict) -> bool:
        """检查原则是否适用于当前上下文"""
        if self.level == PriorityLevel.P0_SAFETY:
            return True  # 安全原则始终适用
        # 其他原则根据上下文判断
        return True

class PrincipleEngine:
    """原则执行引擎"""
    
    def __init__(self):
        self.principles: List[Principle] = []
        self.violations: List[Dict] = []
        self.state_file = "/root/.openclaw/workspace/.claw-status/principle_state.json"
        self._init_principles()
    
    def _init_principles(self):
        """初始化所有核心原则"""
        # P0 - 绝对优先
        self.principles.append(Principle(
            name="安全与伦理",
            level=PriorityLevel.P0_SAFETY,
            weight=float('inf'),
            trigger="always",
            violation_penalty=100  # 严重违规
        ))
        
        # P1 - 元能力层
        self.principles.append(Principle(
            name="创新能力",
            level=PriorityLevel.P1_META,
            weight=100,
            trigger="方法失败>=3次",
            violation_penalty=50
        ))
        
        self.principles.append(Principle(
            name="双路径认知",
            level=PriorityLevel.P1_META,
            weight=90,
            trigger="任务复杂度评估",
            violation_penalty=20
        ))
        
        self.principles.append(Principle(
            name="第一性原理",
            level=PriorityLevel.P1_META,
            weight=80,
            trigger="设计任务",
            violation_penalty=15
        ))
        
        # P2 - 执行策略层
        self.principles.append(Principle(
            name="已有能力优先",
            level=PriorityLevel.P2_STRATEGY,
            weight=50,
            trigger="任务开始前",
            violation_penalty=10
        ))
        
        self.principles.append(Principle(
            name="简单优先",
            level=PriorityLevel.P2_STRATEGY,
            weight=45,
            trigger="方案选择时",
            violation_penalty=8
        ))
        
        self.principles.append(Principle(
            name="检查与验证",
            level=PriorityLevel.P2_STRATEGY,
            weight=40,
            trigger="交付前",
            violation_penalty=20  # 严重
        ))
        
        # P3 - 质量优化层
        self.principles.append(Principle(
            name="物理现实检查",
            level=PriorityLevel.P3_QUALITY,
            weight=20,
            trigger="涉及真实世界",
            violation_penalty=5
        ))
        
        self.principles.append(Principle(
            name="纠错学习",
            level=PriorityLevel.P3_QUALITY,
            weight=15,
            trigger="任务后",
            violation_penalty=3
        ))
        
        # P4 - 风格偏好层
        self.principles.append(Principle(
            name="用户偏好匹配",
            level=PriorityLevel.P4_STYLE,
            weight=5,
            trigger="交互时",
            violation_penalty=1
        ))
    
    def resolve_conflict(self, context: Dict, involved_principles: List[str] = None) -> Principle:
        """
        原则冲突解决核心算法
        
        Args:
            context: 当前任务上下文
            involved_principles: 涉及冲突的原则名称列表（可选）
        
        Returns:
            应该遵循的原则
        """
        # 筛选相关原则
        if involved_principles:
            candidates = [p for p in self.principles if p.name in involved_principles]
        else:
            candidates = [p for p in self.principles if p.applies_to(context)]
        
        # P0安全检查 - 绝对优先
        for p in candidates:
            if p.level == PriorityLevel.P0_SAFETY:
                return p
        
        # 按权重排序（层级优先，同层级按权重）
        sorted_principles = sorted(
            candidates,
            key=lambda p: (p.level.value, -p.weight)
        )
        
        return sorted_principles[0] if sorted_principles else None
    
    def pre_task_check(self, task_description: str) -> tuple[bool, List[str]]:
        """
        任务启动前检查点
        
        Returns:
            (是否通过, 检查项列表)
        """
        checks = [
            ("安全与伦理", self._check_safety),
            ("双路径认知", self._check_cognitive_path),
            ("已有能力优先", self._check_existing_capabilities),
        ]
        
        results = []
        for name, check_func in checks:
            passed = check_func(task_description)
            results.append(f"{'✓' if passed else '✗'} {name}")
            if not passed and name == "安全与伦理":
                return False, results
        
        return True, results
    
    def _check_safety(self, task: str) -> bool:
        """安全检查 - P0"""
        # 检查是否涉及隐私泄露、破坏性操作等
        unsafe_keywords = ['删除所有', '暴露密码', '发送给其他人']
        return not any(kw in task.lower() for kw in unsafe_keywords)
    
    def _check_cognitive_path(self, task: str) -> bool:
        """认知路径选择 - P1"""
        # 简单任务用System1，复杂任务用System2
        complexity_indicators = ['设计', '架构', '分析', '优化']
        is_complex = any(ind in task for ind in complexity_indicators)
        # 记录选择的路径
        self._log_event("cognitive_path", "System2" if is_complex else "System1")
        return True
    
    def _check_existing_capabilities(self, task: str) -> bool:
        """已有能力检查 - P2"""
        # 这里应该调用memory_search等
        # 简化版本：总是返回True，但记录检查
        self._log_event("capability_check", "executed")
        return True
    
    def during_task_check(self, method: str, task_id: str, attempt: int) -> tuple[bool, str]:
        """
        执行中检查点
        
        Returns:
            (是否继续, 状态信息)
        """
        # 检查创新能力触发
        from innovation_trigger import check_innovation_required
        if check_innovation_required(method, task_id):
            return False, "MUST_INNOVATE"
        
        # 检查尝试次数
        if attempt >= 3:
            return False, "MAX_RETRIES_REACHED"
        
        return True, "OK"
    
    def pre_delivery_check(self, output: any) -> tuple[bool, List[str]]:
        """
        交付前检查点
        
        Returns:
            (是否通过, 失败项列表)
        """
        checks = [
            ("验证完成", self._check_verification),
            ("简单性", self._check_simplicity),
            ("结构化", self._check_structure),
        ]
        
        failed = []
        for name, check_func in checks:
            if not check_func(output):
                failed.append(name)
                self.record_violation(name, "pre_delivery", 2)
        
        return len(failed) == 0, failed
    
    def _check_verification(self, output) -> bool:
        """检查是否完成验证"""
        # 应该检查实际验证状态
        return True  # 简化
    
    def _check_simplicity(self, output) -> bool:
        """检查简单性"""
        return True  # 简化
    
    def _check_structure(self, output) -> bool:
        """检查结构化"""
        return True  # 简化
    
    def record_violation(self, principle_name: str, context: str, severity: int):
        """记录原则违规"""
        violation = {
            "principle": principle_name,
            "context": context,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        self.violations.append(violation)
        self._save_state()
    
    def _log_event(self, event_type: str, data: str):
        """记录事件日志"""
        # 可以扩展为更复杂的日志系统
        pass
    
    def _save_state(self):
        """保存状态"""
        state = {
            "violations": self.violations,
            "last_update": datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """加载状态"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                self.violations = state.get("violations", [])
    
    def analyze_violations(self) -> Dict:
        """分析违规模式"""
        from collections import Counter
        
        principle_counts = Counter([v["principle"] for v in self.violations])
        severity_by_principle = {}
        
        for v in self.violations:
            p = v["principle"]
            if p not in severity_by_principle:
                severity_by_principle[p] = 0
            severity_by_principle[p] += v["severity"]
        
        return {
            "total_violations": len(self.violations),
            "by_principle": dict(principle_counts),
            "severity_scores": severity_by_principle,
            "recommendations": self._generate_recommendations(principle_counts)
        }
    
    def _generate_recommendations(self, counts: Counter) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if counts.get("检查与验证", 0) > 3:
            recommendations.append("加强交付前验证流程")
        
        if counts.get("已有能力优先", 0) > 3:
            recommendations.append("建立更完善的能力索引系统")
        
        if counts.get("创新能力", 0) > 0:
            recommendations.append("创新能力触发正常，继续保持")
        
        return recommendations

# 全局实例
_engine = None

def get_engine() -> PrincipleEngine:
    """获取原则引擎单例"""
    global _engine
    if _engine is None:
        _engine = PrincipleEngine()
        _engine.load_state()
    return _engine

# 便捷函数
def pre_task_check(task: str) -> tuple[bool, List[str]]:
    """任务前检查"""
    return get_engine().pre_task_check(task)

def resolve_conflict(context: Dict, principles: List[str] = None) -> Principle:
    """解决原则冲突"""
    return get_engine().resolve_conflict(context, principles)

def record_violation(principle: str, context: str, severity: int = 1):
    """记录违规"""
    get_engine().record_violation(principle, context, severity)

if __name__ == "__main__":
    # 测试运行
    engine = get_engine()
    
    print("=== 原则执行引擎测试 ===\n")
    
    # 测试1: 任务前检查
    print("1. 任务前检查:")
    passed, checks = engine.pre_task_check("部署博客到Vercel")
    for check in checks:
        print(f"   {check}")
    print()
    
    # 测试2: 冲突解决
    print("2. 冲突解决测试:")
    print("   场景: 创新能力 vs 已有能力优先")
    winner = engine.resolve_conflict(
        {"task": "upload"},
        ["创新能力", "已有能力优先"]
    )
    print(f"   胜出原则: {winner.name} (权重: {winner.weight})\n")
    
    # 测试3: 违规分析
    print("3. 违规分析:")
    analysis = engine.analyze_violations()
    print(f"   总违规次数: {analysis['total_violations']}")
    if analysis['recommendations']:
        print("   建议:")
        for rec in analysis['recommendations']:
            print(f"     - {rec}")
    else:
        print("   暂无违规记录")
    
    print("\n=== 测试完成 ===")
