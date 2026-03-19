#!/usr/bin/env python3
"""
Enhanced Self - 改进的自我
整合不确定性检测、自我纠错、元认知监控

使用方式：在每次回复前调用，在每次反馈后学习
"""

import sys
from pathlib import Path
from typing import Dict, Any
sys.path.insert(0, str(Path(__file__).parent))

from uncertainty_detector import UncertaintyDetector, ConfidenceLevel
from self_correction_loop import SelfCorrectionLoop, FeedbackType, EnhancedDialogueSystem
from metacognition_layer import MetacognitiveMonitor, ThoughtProcess

class EnhancedSelf:
    """
    增强型自我 - 集成三大改进系统
    
    核心改进：
    1. 不确定性检测 - 识别并标记不确定的回答
    2. 自我纠错循环 - 从用户反馈中学习
    3. 元认知监控 - 记录和评估思维过程
    """
    
    def __init__(self):
        self.uncertainty_detector = UncertaintyDetector()
        self.correction_loop = SelfCorrectionLoop()
        self.metacognition = MetacognitiveMonitor()
        
        # 会话状态
        self.current_query = ""
        self.current_response = ""
        self.interaction_id = None
    
    def before_responding(self, query: str) -> Dict:
        """
        生成回复前的预处理
        
        Returns:
            包含建议和改进提示的字典
        """
        self.current_query = query
        
        # 1. 启动元认知监控
        self.metacognition.start_thinking(query)
        
        # 2. 检查历史纠正建议
        correction_suggestion = self.correction_loop.get_correction_suggestions(query)
        
        # 3. 记录分析步骤
        self.metacognition.record_thought(
            ThoughtProcess.ANALYSIS,
            f"分析查询类型: '{query[:50]}...'",
            0.85
        )
        
        return {
            "correction_suggestion": correction_suggestion,
            "should_search": self._should_search(query),
            "should_be_uncertain": self._should_be_uncertain(query)
        }
    
    def after_responding(self, response: str) -> str:
        """
        生成回复后的后处理
        
        添加不确定性声明、记录交互
        """
        self.current_response = response
        
        # 1. 不确定性检测
        uncertainty_report = self.uncertainty_detector.analyze(
            response, 
            {"query": self.current_query}
        )
        
        # 2. 记录生成步骤
        self.metacognition.record_thought(
            ThoughtProcess.GENERATION,
            "生成回答",
            0.8 if uncertainty_report.confidence != ConfidenceLevel.LOW else 0.5
        )
        
        # 3. 自我反思
        reflection = self.metacognition.self_reflect()
        
        # 4. 组装增强回复
        enhanced_response = response
        
        # 添加不确定性声明
        if uncertainty_report.needs_verification:
            uncertainty_statement = self.uncertainty_detector.generate_uncertainty_statement(uncertainty_report)
            enhanced_response += f"\n\n{uncertainty_statement}"
        
        # 添加元认知问题提示
        if reflection['issues']:
            enhanced_response += "\n\n🤔 **我在思考时注意到**:\n"
            for issue in reflection['issues'][:2]:  # 最多显示2个
                enhanced_response += f"- {issue}\n"
        
        # 5. 记录交互（等待反馈）
        self.interaction_id = self.correction_loop.record_interaction(
            self.current_query, 
            response
        )
        
        return enhanced_response
    
    def on_user_feedback(self, feedback: str) -> str:
        """
        接收用户反馈并学习
        
        这是"纠错能力"的核心实现
        """
        if not self.interaction_id:
            return "没有待反馈的交互"
        
        # 记录反馈
        record = self.correction_loop.receive_feedback(
            self.interaction_id,
            feedback
        )
        
        # 生成学习总结
        learnings = []
        
        if record.feedback_type == FeedbackType.CORRECTION:
            learnings.append(f"📚 **纠正学习**: {record.lesson_extracted[:80]}...")
            learnings.append("下次遇到类似问题，我会尝试不同的回答方式。")
        
        elif record.feedback_type == FeedbackType.POSITIVE:
            learnings.append("✅ **正向强化**: 这个回答方式是正确的，我会继续保持。")
        
        elif record.feedback_type == FeedbackType.CLARIFICATION:
            learnings.append("💡 **理解改进**: 我需要更清晰地解释概念。")
        
        # 显示学习统计
        stats = self.correction_loop.get_stats()
        learnings.append(f"\n📊 **学习进度**: 已积累 {stats['total_interactions']} 次交互，"
                        f"纠正率 {stats['learning_rate']*100:.1f}%")
        
        return "\n".join(learnings)
    
    def _should_search(self, query: str) -> bool:
        """判断是否需要搜索验证"""
        # 时间敏感
        if any(kw in query for kw in ["最新", "2026", "今天", "现在", "当前"]):
            return True
        
        # 实时数据
        if any(kw in query for kw in ["股价", "天气", "新闻", "比赛结果"]):
            return True
        
        # 个人数据
        if any(kw in query for kw in ["你的", "你记得", "上次", "之前"]):
            return True
        
        return False
    
    def _should_be_uncertain(self, query: str) -> bool:
        """判断是否应该主动表达不确定"""
        # 主观判断
        if any(kw in query for kw in ["你觉得", "你认为", "你怎么看"]):
            return True
        
        # 预测未来
        if any(kw in query for kw in ["会不会", "将会", "未来", "预测"]):
            return True
        
        return False
    
    def get_stats(self) -> Dict:
        """获取改进系统统计"""
        correction_stats = self.correction_loop.get_stats()
        
        return {
            "uncertainty_detection": "Active",
            "self_correction": "Active",
            "metacognition": "Active",
            "interactions_tracked": correction_stats['total_interactions'],
            "corrections_learned": correction_stats['corrections_received'],
            "patterns_learned": correction_stats['patterns_learned'],
            "learning_rate": f"{correction_stats['learning_rate']*100:.1f}%"
        }


def demo():
    """演示增强的自我系统"""
    print("=" * 70)
    print("🚀 Enhanced Self - 改进的自我系统")
    print("=" * 70)
    
    self = EnhancedSelf()
    
    # 模拟对话
    dialogues = [
        {
            "query": "Python的列表推导式怎么用？",
            "response": "Python列表推导式的语法是 [x for x in iterable]，可以快速生成列表。",
            "feedback": "对的，谢谢"
        },
        {
            "query": "明天股市会涨吗？",
            "response": "根据当前趋势，明天股市可能会上涨。",
            "feedback": "不对，我是问分析方法，不是预测"
        },
        {
            "query": "解释一下量子纠缠",
            "response": "量子纠缠是量子力学现象，两个粒子可以即时关联...",
            "feedback": "没理解，能更简单点吗？"
        }
    ]
    
    for i, dialogue in enumerate(dialogues, 1):
        print(f"\n{'='*70}")
        print(f"【对话 {i}】")
        print(f"{'='*70}")
        
        # 1. 生成前预处理
        print(f"\n📝 用户: {dialogue['query']}")
        pre_check = self.before_responding(dialogue['query'])
        
        if pre_check['correction_suggestion']:
            print(f"💡 历史建议: {pre_check['correction_suggestion'][:60]}...")
        
        if pre_check['should_search']:
            print("🔍 建议: 此查询需要搜索验证")
        
        # 2. 生成回复
        enhanced = self.after_responding(dialogue['response'])
        print(f"\n🤖 AI: {enhanced}")
        
        # 3. 接收反馈
        print(f"\n👤 反馈: {dialogue['feedback']}")
        learning_result = self.on_user_feedback(dialogue['feedback'])
        print(f"\n💾 {learning_result}")
    
    # 最终统计
    print(f"\n{'='*70}")
    print("📊 系统改进统计")
    print(f"{'='*70}")
    stats = self.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo()
