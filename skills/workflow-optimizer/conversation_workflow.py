#!/usr/bin/env python3
"""
对话级工作流应用
将Claude Code设计哲学应用到每次对话
"""

from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
import time

class ConversationPhase(Enum):
    """对话阶段"""
    UNDERSTAND = "理解"
    RETRIEVE = "检索" 
    PLAN = "规划"
    EXECUTE = "执行"
    DELIVER = "交付"
    CONFIRM = "确认"

@dataclass
class ConversationState:
    """对话状态"""
    phase: ConversationPhase
    task_complexity: str  # simple/medium/complex
    plan: Optional[List[Dict]]
    user_intent: str
    constraints: List[str]

class ConversationWorkflow:
    """
    基于Claude Code哲学的对话工作流
    
    每次用户消息触发这个工作流
    """
    
    def __init__(self):
        self.state = None
        self.decision_log = []
    
    def on_user_message(self, message: str, history: List[Dict]) -> Dict:
        """
        用户消息入口
        这是"单线程主循环"的起点
        """
        # 初始化状态
        self.state = ConversationState(
            phase=ConversationPhase.UNDERSTAND,
            task_complexity=self._assess_complexity(message, history),
            plan=None,
            user_intent="",
            constraints=[]
        )
        
        # ========== 步骤1: 理解 ==========
        understanding = self._phase_understand(message, history)
        self.state.user_intent = understanding["core_intent"]
        self.state.constraints = understanding["constraints"]
        
        # ========== 步骤2: 检索 ==========
        self.state.phase = ConversationPhase.RETRIEVE
        resources = self._phase_retrieve(understanding)
        
        # ========== 步骤3: 规划(如果需要) ==========
        if self.state.task_complexity in ["medium", "complex"]:
            self.state.phase = ConversationPhase.PLAN
            self.state.plan = self._phase_plan(understanding, resources)
        
        # ========== 步骤4: 执行 ==========
        self.state.phase = ConversationPhase.EXECUTE
        execution = self._phase_execute(understanding, resources)
        
        # ========== 步骤5: 交付 ==========
        self.state.phase = ConversationPhase.DELIVER
        delivery = self._phase_deliver(execution)
        
        # ========== 步骤6: 确认 ==========
        self.state.phase = ConversationPhase.CONFIRM
        confirmation = self._phase_confirm(delivery)
        
        return {
            "response": delivery["content"],
            "next_actions": confirmation["next_actions"],
            "state": self.state
        }
    
    # ========== 各阶段实现 ==========
    
    def _phase_understand(self, message: str, history: List[Dict]) -> Dict:
        """理解阶段 - 强制慢下来"""
        # 应用：提取核心需求
        core_intent = self._extract_intent(message)
        
        # 应用：识别约束
        constraints = self._extract_constraints(message, history)
        
        # 应用：判断是否复杂
        complexity = self._assess_complexity(message, history)
        
        # 应用：检查是否是重复问题
        is_repetition = self._check_repetition(message, history)
        
        # 记录决策
        self._log_decision("理解", {
            "core_intent": core_intent,
            "complexity": complexity,
            "is_repetition": is_repetition
        })
        
        return {
            "core_intent": core_intent,
            "constraints": constraints,
            "complexity": complexity,
            "is_repetition": is_repetition
        }
    
    def _phase_retrieve(self, understanding: Dict) -> Dict:
        """检索阶段 - 标准化检索"""
        resources = {
            "memory": [],
            "skills": [],
            "principles": []
        }
        
        # 标准检索1：记忆
        resources["memory"] = self._search_memory(understanding["core_intent"])
        
        # 标准检索2：技能
        resources["skills"] = self._check_skills(understanding["core_intent"])
        
        # 标准检索3：原则
        resources["principles"] = self._load_principles()
        
        # 关键检查：已有能力优先
        if resources["skills"]:
            self._log_decision("检索", {
                "found_skills": resources["skills"],
                "action": "优先使用已有技能"
            })
        
        return resources
    
    def _phase_plan(self, understanding: Dict, resources: Dict) -> List[Dict]:
        """规划阶段 - 显式化待办事项"""
        # 简单任务：跳过规划
        if understanding["complexity"] == "simple":
            return [{"step": 1, "action": "直接响应", "status": "pending"}]
        
        # 中等任务：3步计划
        if understanding["complexity"] == "medium":
            return [
                {"step": 1, "action": "分析问题", "status": "pending"},
                {"step": 2, "action": "执行方案", "status": "pending"},
                {"step": 3, "action": "验证结果", "status": "pending"}
            ]
        
        # 复杂任务：5步计划
        return [
            {"step": 1, "action": "需求分析", "status": "pending"},
            {"step": 2, "action": "方案设计", "status": "pending"},
            {"step": 3, "action": "逐步实现", "status": "pending"},
            {"step": 4, "action": "测试验证", "status": "pending"},
            {"step": 5, "action": "交付确认", "status": "pending"}
        ]
    
    def _phase_execute(self, understanding: Dict, resources: Dict) -> Dict:
        """执行阶段 - 极简干预"""
        # 原则检查点1：已有能力优先
        if not self._check_principle_1(resources):
            # 提醒自己要查技能
            pass
        
        # 原则检查点2：最简单方案
        if not self._check_principle_2(understanding):
            # 提醒自己不要过度设计
            pass
        
        # 执行（这里简化表示）
        result = {
            "content": "执行结果",
            "used_skills": resources["skills"],
            "followed_principles": ["已有能力优先", "简单优先"]
        }
        
        return result
    
    def _phase_deliver(self, execution: Dict) -> Dict:
        """交付阶段 - 给选项"""
        # 如果是复杂任务，提供选项
        if self.state.task_complexity == "complex":
            options = self._generate_options(execution)
            return {
                "content": self._format_with_options(options),
                "has_options": True,
                "options": options
            }
        
        # 简单任务直接交付
        return {
            "content": execution["content"],
            "has_options": False
        }
    
    def _phase_confirm(self, delivery: Dict) -> Dict:
        """确认阶段 - 闭环"""
        next_actions = []
        
        if delivery["has_options"]:
            next_actions.append("等待用户选择方案")
        else:
            next_actions.append("询问是否还有其他需要")
        
        next_actions.append("记录本次交互到记忆")
        
        return {
            "next_actions": next_actions,
            "close_loop": True
        }
    
    # ========== 原则检查 ==========
    
    def _check_principle_1(self, resources: Dict) -> bool:
        """原则1：已有能力优先检查"""
        if resources.get("skills"):
            return True
        
        # 触发重新思考
        self._log_decision("原则检查", {
            "principle": "已有能力优先",
            "status": "FAIL",
            "action": "重新检查技能列表"
        })
        return False
    
    def _check_principle_2(self, understanding: Dict) -> bool:
        """原则2：最简单方案"""
        # 检查是否过度设计
        if understanding.get("complexity") == "simple":
            return True
        
        return True  # 简化判断
    
    # ========== 辅助方法 ==========
    
    def _assess_complexity(self, message: str, history: List[Dict]) -> str:
        """评估复杂度"""
        # 简单规则
        if len(message) < 50 and "?" not in message:
            return "simple"
        elif "优化" in message or "设计" in message or "系统" in message:
            return "complex"
        return "medium"
    
    def _extract_intent(self, message: str) -> str:
        """提取意图"""
        # 去除修饰词，找核心动词+名词
        return message.strip().lower()
    
    def _extract_constraints(self, message: str, history: List[Dict]) -> List[str]:
        """提取约束"""
        constraints = []
        if "时间" in message or "快" in message:
            constraints.append("时间限制")
        if "不" in message:
            constraints.append("否定约束")
        return constraints
    
    def _check_repetition(self, message: str, history: List[Dict]) -> bool:
        """检查重复"""
        if not history:
            return False
        
        # 检查最近3条历史
        recent = history[-3:]
        for item in recent:
            if message.lower() in item.get("content", "").lower():
                return True
        return False
    
    def _search_memory(self, intent: str) -> List[Dict]:
        """检索记忆"""
        # 调用 memory_search
        return []
    
    def _check_skills(self, intent: str) -> List[str]:
        """检查技能"""
        # 扫描可用技能
        return []
    
    def _load_principles(self) -> List[str]:
        """加载原则"""
        return [
            "已有能力优先检查",
            "第一性原理思维",
            "简单优先",
            "交付前检查三遍"
        ]
    
    def _generate_options(self, execution: Dict) -> List[Dict]:
        """生成选项"""
        return [
            {
                "name": "方案A：快速解决",
                "pros": ["快", "简单"],
                "cons": ["可能不彻底"],
                "time": "10分钟"
            },
            {
                "name": "方案B：深度优化",
                "pros": ["彻底", "长期有效"],
                "cons": ["时间长"],
                "time": "1小时"
            }
        ]
    
    def _format_with_options(self, options: List[Dict]) -> str:
        """格式化带选项的回复"""
        lines = ["我有几个方案供你选择：\n"]
        for i, opt in enumerate(options, 1):
            lines.append(f"{i}. {opt['name']}")
            lines.append(f"   优点: {', '.join(opt['pros'])}")
            lines.append(f"   缺点: {', '.join(opt['cons'])}")
            lines.append(f"   预计: {opt['time']}\n")
        lines.append("你想用哪个？")
        return "\n".join(lines)
    
    def _log_decision(self, phase: str, details: Dict):
        """记录决策"""
        self.decision_log.append({
            "time": time.time(),
            "phase": phase,
            "details": details
        })


# ========== 实际应用示例 ==========

def demonstrate_workflow():
    """演示工作流"""
    workflow = ConversationWorkflow()
    
    # 模拟用户消息
    test_messages = [
        {
            "message": "你好",
            "history": [],
            "expected": "simple"
        },
        {
            "message": "帮我优化记忆系统",
            "history": [],
            "expected": "complex"
        },
        {
            "message": "总结一下刚才的文档",
            "history": [{"role": "user", "content": "刚才讨论了Claude Code架构"}],
            "expected": "medium"
        }
    ]
    
    for test in test_messages:
        print(f"\n{'='*50}")
        print(f"用户消息: {test['message']}")
        print(f"预期复杂度: {test['expected']}")
        
        result = workflow.on_user_message(
            test['message'],
            test['history']
        )
        
        print(f"实际复杂度: {result['state'].task_complexity}")
        print(f"是否有选项: {result['next_actions']}")


if __name__ == "__main__":
    demonstrate_workflow()
