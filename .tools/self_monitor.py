"""
自我监控自动化 - Self-Monitoring Automation
自动触发关键检查，减少遗漏
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Callable
from enum import Enum

class TriggerType(Enum):
    KEYWORD = "keyword"          # 关键词触发
    PATTERN = "pattern"          # 模式匹配
    CONTEXT = "context"          # 上下文检测
    TEMPORAL = "temporal"        # 时间触发

@dataclass
class MonitorRule:
    name: str
    trigger_type: TriggerType
    pattern: str
    check_function: str
    priority: int  # 1-10, 10为最高
    description: str

class SelfMonitor:
    """自我监控系统"""
    
    RULES = [
        MonitorRule(
            name="physical_reality_check",
            trigger_type=TriggerType.CONTEXT,
            pattern="real_world_entity",
            check_function="check_physical_constraints",
            priority=9,
            description="涉及真实世界实体时检查物理约束"
        ),
        MonitorRule(
            name="validation_check",
            trigger_type=TriggerType.CONTEXT,
            pattern="new_design",
            check_function="check_validation_needed",
            priority=8,
            description="新设计方案需要验证"
        ),
        MonitorRule(
            name="over_inference_check",
            trigger_type=TriggerType.PATTERN,
            pattern=r"(always|never|certainly|definitely|all|none)",
            check_function="check_absolute_claims",
            priority=7,
            description="检测绝对化表述"
        ),
        MonitorRule(
            name="assumption_check",
            trigger_type=TriggerType.PATTERN,
            pattern=r"(assume|assuming|presumably|likely)",
            check_function="flag_unverified_assumptions",
            priority=6,
            description="标记未验证假设"
        ),
        MonitorRule(
            name="time_estimate_check",
            trigger_type=TriggerType.PATTERN,
            pattern=r"(\d+\s*(seconds?|minutes?|hours?|days?))",
            check_function="validate_time_estimate",
            priority=5,
            description="验证时间估计合理性"
        ),
    ]
    
    def __init__(self):
        self.triggered_checks: List[str] = []
        self.check_functions: dict = {
            "check_physical_constraints": self._check_physical,
            "check_validation_needed": self._check_validation,
            "check_absolute_claims": self._check_absolute,
            "flag_unverified_assumptions": self._flag_assumption,
            "validate_time_estimate": self._check_time,
        }
    
    def analyze(self, text: str, context: dict = None) -> List[dict]:
        """
        分析文本，识别需要触发的检查
        
        Returns:
            需要执行的检查列表
        """
        triggered = []
        
        for rule in self.RULES:
            should_trigger = False
            
            if rule.trigger_type == TriggerType.PATTERN:
                if re.search(rule.pattern, text, re.IGNORECASE):
                    should_trigger = True
                    
            elif rule.trigger_type == TriggerType.KEYWORD:
                if rule.pattern.lower() in text.lower():
                    should_trigger = True
                    
            elif rule.trigger_type == TriggerType.CONTEXT:
                if context and rule.pattern in context.get('tags', []):
                    should_trigger = True
            
            if should_trigger:
                check_fn = self.check_functions.get(rule.check_function)
                if check_fn:
                    result = check_fn(text, context)
                    triggered.append({
                        "rule": rule.name,
                        "priority": rule.priority,
                        "result": result,
                        "description": rule.description
                    })
        
        # 按优先级排序
        triggered.sort(key=lambda x: x['priority'], reverse=True)
        return triggered
    
    def _check_physical(self, text: str, context: dict) -> dict:
        """检查物理约束"""
        entities = self._extract_entities(text)
        return {
            "type": "physical_reality",
            "entities_found": entities,
            "action": "加载physical_constraints.yaml进行验证",
            "severity": "high" if entities else "low"
        }
    
    def _check_validation(self, text: str, context: dict) -> dict:
        """检查是否需要验证"""
        return {
            "type": "validation_needed",
            "action": "使用validation_toolkit进行假设验证",
            "severity": "medium"
        }
    
    def _check_absolute(self, text: str, context: dict) -> dict:
        """检查绝对化表述"""
        absolutes = re.findall(r"(always|never|certainly|definitely|all\s+\w+|none\s+\w+)", 
                               text, re.IGNORECASE)
        return {
            "type": "absolute_claims",
            "claims_found": absolutes,
            "warning": "从单一案例推广到所有场景可能存在过度推断",
            "severity": "medium" if absolutes else "low"
        }
    
    def _flag_assumption(self, text: str, context: dict) -> dict:
        """标记假设"""
        assumptions = re.findall(r"(assume.*?[.]|assuming.*?[.,]|presumably|likely)", 
                                text, re.IGNORECASE)
        return {
            "type": "unverified_assumptions",
            "assumptions_found": assumptions,
            "note": "这些假设需要验证或有证据支持",
            "severity": "low"
        }
    
    def _check_time(self, text: str, context: dict) -> dict:
        """检查时间估计"""
        times = re.findall(r"(\d+\s*(seconds?|minutes?|hours?|days?))", text, re.IGNORECASE)
        return {
            "type": "time_estimates",
            "estimates_found": times,
            "note": "检查是否符合physical_constraints.yaml中的时间尺度",
            "severity": "low"
        }
    
    def _extract_entities(self, text: str) -> List[str]:
        """提取可能的物理实体"""
        # 简化实现：查找大写名词和特定关键词
        entities = []
        real_world_keywords = [
            "human", "person", "user", "server", "machine", "device",
            "file", "database", "network", "api", "cpu", "memory",
            "cost", "price", "time", "hour", "day", "week"
        ]
        for keyword in real_world_keywords:
            if keyword in text.lower():
                entities.append(keyword)
        return entities

# 使用示例
if __name__ == "__main__":
    monitor = SelfMonitor()
    
    # 测试文本
    test_text = """
    设计一个系统，人类可以实时审核所有AI输出。
    这肯定能提升质量。假设审核者会立即响应。
    估计每个审核需要2 minutes。
    """
    
    results = monitor.analyze(test_text, {"tags": ["new_design"]})
    
    print("触发的检查:")
    for r in results:
        print(f"  [{r['priority']}] {r['rule']}: {r['description']}")
        print(f"       严重程度: {r['result']['severity']}")
