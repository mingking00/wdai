#!/usr/bin/env python3
"""
用户反馈循环 记忆验证系统 v0.4

基于用户确认/否认调整记忆验证权重

Author: wdai
Version: 0.4 (用户反馈版)
"""

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class FeedbackRecord:
    """反馈记录"""
    query: str
    memory_content: str
    original_decision: str
    original_confidence: float
    user_feedback: str  # 'confirm', 'deny', 'correct'
    user_correction: Optional[str]  # 如果correct，用户提供的正确答案
    timestamp: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FeedbackRecord':
        return cls(**data)


class UserFeedbackLearningSystem:
    """
    用户反馈学习系统
    
    基于用户反馈调整记忆验证策略
    """
    
    def __init__(self, data_dir: str = ".claw-status/feedback_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_history: List[FeedbackRecord] = []
        self.feedback_file = self.data_dir / "feedback_history.json"
        self.load_feedback()
        
        # 学习参数
        self.learning_rate = 0.1
        self.confidence_adjustments: Dict[str, float] = {}
        
        # 统计
        self.stats = {
            'total_feedback': 0,
            'confirmations': 0,
            'denials': 0,
            'corrections': 0,
            'avg_confidence_delta': 0.0
        }
    
    def load_feedback(self):
        """加载历史反馈"""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    data = json.load(f)
                    self.feedback_history = [
                        FeedbackRecord.from_dict(r) for r in data
                    ]
                print(f"[FeedbackLearning] 加载 {len(self.feedback_history)} 条历史反馈")
            except Exception as e:
                print(f"[FeedbackLearning] 加载反馈失败: {e}")
    
    def save_feedback(self):
        """保存反馈历史"""
        try:
            with open(self.feedback_file, 'w') as f:
                data = [r.to_dict() for r in self.feedback_history]
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[FeedbackLearning] 保存反馈失败: {e}")
    
    def record_feedback(
        self,
        query: str,
        memory_content: str,
        original_decision: str,
        original_confidence: float,
        user_feedback: str,  # 'confirm', 'deny', 'correct'
        user_correction: Optional[str] = None
    ) -> Dict:
        """
        记录用户反馈
        
        Returns:
            学习结果
        """
        record = FeedbackRecord(
            query=query,
            memory_content=memory_content,
            original_decision=original_decision,
            original_confidence=original_confidence,
            user_feedback=user_feedback,
            user_correction=user_correction,
            timestamp=datetime.now().isoformat()
        )
        
        self.feedback_history.append(record)
        self.save_feedback()
        
        # 更新统计
        self.stats['total_feedback'] += 1
        if user_feedback == 'confirm':
            self.stats['confirmations'] += 1
        elif user_feedback == 'deny':
            self.stats['denials'] += 1
        elif user_feedback == 'correct':
            self.stats['corrections'] += 1
        
        # 学习调整
        learning_result = self._learn_from_feedback(record)
        
        print(f"[FeedbackLearning] 记录反馈: {user_feedback}")
        print(f"  查询: {query[:50]}...")
        print(f"  原始置信度: {original_confidence:.2f}")
        print(f"  调整: {learning_result.get('adjustment', 0):+.2f}")
        
        return learning_result
    
    def _learn_from_feedback(self, record: FeedbackRecord) -> Dict:
        """
        从反馈中学习
        
        调整策略:
        - confirm (高置信度正确): 保持阈值
        - confirm (低置信度正确): 降低阈值
        - deny (高置信度错误): 提高阈值
        - deny (低置信度正确): 保持阈值
        - correct: 记录正确答案
        """
        conf = record.original_confidence
        feedback = record.user_feedback
        
        adjustment = 0.0
        lesson = ""
        
        if feedback == 'confirm':
            if conf > 0.8:
                # 高置信度被确认 → 当前策略正确
                lesson = "高置信度策略有效"
            elif conf > 0.5:
                # 中等置信度被确认 → 可以降低阈值
                adjustment = -0.05
                lesson = "中等置信度也可靠，可适当降低阈值"
            else:
                # 低置信度被确认 → 降低更多
                adjustment = -0.1
                lesson = "低置信度也有价值，降低阈值"
        
        elif feedback == 'deny':
            if conf > 0.8:
                # 高置信度被拒绝 → 提高阈值
                adjustment = 0.1
                lesson = "高置信度也有误报，提高阈值"
            elif conf > 0.5:
                # 中等置信度被拒绝 → 策略正确
                lesson = "中等置信度需要确认，策略正确"
            else:
                # 低置信度被拒绝 → 当前策略正确
                lesson = "低置信度正确识别为不可靠"
        
        elif feedback == 'correct':
            # 用户提供了正确答案
            adjustment = 0.05
            lesson = f"记录正确答案: {record.user_correction[:50] if record.user_correction else 'N/A'}..."
            # 可以在这里更新记忆库
        
        # 应用调整
        query_pattern = self._extract_pattern(record.query)
        current_adjustment = self.confidence_adjustments.get(query_pattern, 0.0)
        self.confidence_adjustments[query_pattern] = current_adjustment + adjustment
        
        return {
            'adjustment': adjustment,
            'lesson': lesson,
            'new_threshold_delta': self.confidence_adjustments[query_pattern]
        }
    
    def _extract_pattern(self, query: str) -> str:
        """提取查询模式"""
        # 提取核心关键词作为模式
        keywords = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query.lower())
        # 取前2-3个关键词
        return '_'.join(keywords[:3]) if keywords else 'default'
    
    def get_adjusted_confidence(
        self,
        query: str,
        original_confidence: float
    ) -> Tuple[float, str]:
        """
        获取调整后的置信度
        
        Returns:
            (adjusted_confidence, reasoning)
        """
        query_pattern = self._extract_pattern(query)
        adjustment = self.confidence_adjustments.get(query_pattern, 0.0)
        
        adjusted = original_confidence + adjustment
        adjusted = max(0.0, min(1.0, adjusted))  # 限制在0-1
        
        if abs(adjustment) > 0.01:
            reasoning = f"基于历史反馈调整 {adjustment:+.2f}"
        else:
            reasoning = "无历史反馈调整"
        
        return adjusted, reasoning
    
    def get_learning_insights(self) -> Dict:
        """获取学习洞察"""
        if not self.feedback_history:
            return {"message": "暂无反馈数据"}
        
        # 分析反馈模式
        recent_feedback = self.feedback_history[-20:]  # 最近20条
        
        confirm_rate = sum(1 for r in recent_feedback if r.user_feedback == 'confirm') / len(recent_feedback)
        deny_rate = sum(1 for r in recent_feedback if r.user_feedback == 'deny') / len(recent_feedback)
        
        # 高置信度错误率
        high_conf_wrong = sum(
            1 for r in recent_feedback
            if r.original_confidence > 0.8 and r.user_feedback == 'deny'
        )
        high_conf_total = sum(
            1 for r in recent_feedback
            if r.original_confidence > 0.8
        )
        high_conf_error_rate = high_conf_wrong / high_conf_total if high_conf_total > 0 else 0
        
        return {
            'total_feedback': len(self.feedback_history),
            'recent_confirm_rate': confirm_rate,
            'recent_deny_rate': deny_rate,
            'high_conf_error_rate': high_conf_error_rate,
            'suggested_threshold_adjustment': self._suggest_threshold_adjustment(),
            'confidence_adjustments': self.confidence_adjustments
        }
    
    def _suggest_threshold_adjustment(self) -> str:
        """建议阈值调整"""
        recent = [r for r in self.feedback_history if r.timestamp > 
                  (datetime.now() - timedelta(days=7)).isoformat()]
        
        if not recent:
            return "数据不足"
        
        # 分析是否需要调整阈值
        high_conf_confirms = sum(1 for r in recent if r.original_confidence > 0.8 and r.user_feedback == 'confirm')
        high_conf_denies = sum(1 for r in recent if r.original_confidence > 0.8 and r.user_feedback == 'deny')
        
        if high_conf_denies > high_conf_confirms:
            return "高置信度误报较多，建议提高阈值至0.85+"
        elif high_conf_confirms > high_conf_denies * 3:
            return "高置信度准确率很高，可考虑降低阈值至0.75"
        
        return "当前阈值合适"
    
    def print_learning_report(self):
        """打印学习报告"""
        insights = self.get_learning_insights()
        
        print("\n" + "="*60)
        print("📊 用户反馈学习报告")
        print("="*60)
        print(f"总反馈数: {insights['total_feedback']}")
        print(f"近期确认率: {insights['recent_confirm_rate']:.1%}")
        print(f"高置信度错误率: {insights['high_conf_error_rate']:.1%}")
        print(f"建议: {insights['suggested_threshold_adjustment']}")
        
        if self.confidence_adjustments:
            print("\n模式调整:")
            for pattern, adj in list(self.confidence_adjustments.items())[:5]:
                print(f"  {pattern}: {adj:+.2f}")


class FeedbackEnabledMemorySystem:
    """
    启用反馈的记忆系统
    
    整合验证和反馈学习
    """
    
    def __init__(self):
        # 导入之前的验证系统
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from kimi_api_memory import KimiAPIVerificationAgent
        
        self.verification_agent = KimiAPIVerificationAgent()
        self.feedback_system = UserFeedbackLearningSystem()
        
        self.stats = {
            'total_queries': 0,
            'with_feedback': 0
        }
    
    def retrieve_and_verify(self, query: str, memories: List[str]) -> Dict:
        """检索并验证 (带反馈学习)"""
        self.stats['total_queries'] += 1
        
        if not memories:
            return {
                'query': query,
                'decision': 'unknown',
                'confidence': 0.0,
                'feedback_enabled': True
            }
        
        # 验证所有候选
        verified = []
        for memory in memories:
            result = self.verification_agent.verify(query, memory)
            
            # 应用用户反馈调整
            adjusted_conf, adjustment_reason = self.feedback_system.get_adjusted_confidence(
                query, result.confidence
            )
            
            verified.append({
                'content': memory,
                'verification': result,
                'adjusted_confidence': adjusted_conf,
                'adjustment_reason': adjustment_reason
            })
        
        # 按调整后置信度排序
        verified.sort(key=lambda x: x['adjusted_confidence'], reverse=True)
        
        # 决策
        best = verified[0]
        conf = best['adjusted_confidence']
        
        result = {
            'query': query,
            'original_confidence': best['verification'].confidence,
            'adjusted_confidence': conf,
            'adjustment_reason': best['adjustment_reason'],
            'feedback_enabled': True,
            'all_candidates': verified
        }
        
        if conf > 0.8:
            result.update({
                'decision': 'use',
                'answer': best['content'],
                'reasoning': best['verification'].reasoning
            })
        elif conf > 0.5:
            result.update({
                'decision': 'confirm',
                'answer': best['content'],
                'reasoning': best['verification'].reasoning,
                'clarification': f"置信度{conf:.0%}，请确认"
            })
        else:
            result.update({
                'decision': 'unknown',
                'answer': f"没有可靠记忆",
                'reasoning': "相关性低"
            })
        
        return result
    
    def record_user_feedback(
        self,
        query: str,
        memory_content: str,
        original_decision: str,
        original_confidence: float,
        user_feedback: str,
        user_correction: Optional[str] = None
    ):
        """记录用户反馈"""
        self.stats['with_feedback'] += 1
        return self.feedback_system.record_feedback(
            query, memory_content, original_decision,
            original_confidence, user_feedback, user_correction
        )
    
    def print_feedback_report(self):
        """打印反馈报告"""
        self.feedback_system.print_learning_report()


def test_feedback_system():
    """测试反馈系统"""
    print("="*70)
    print("🧪 测试用户反馈循环系统 v0.4")
    print("="*70)
    
    system = FeedbackEnabledMemorySystem()
    
    # 模拟查询
    query = "我的B站UID是多少？"
    memories = [
        '用户的B站UID是 12345678',
        '用户是程序员',
        '系统架构是微服务'
    ]
    
    print(f"\n🔍 查询: {query}")
    print("-" * 50)
    
    result = system.retrieve_and_verify(query, memories)
    
    print(f"原始置信度: {result['original_confidence']:.2f}")
    print(f"调整后置信度: {result['adjusted_confidence']:.2f}")
    print(f"决策: {result['decision']}")
    
    # 模拟用户反馈
    print("\n💬 用户反馈: 'confirm'")
    feedback_result = system.record_user_feedback(
        query=query,
        memory_content=result['answer'],
        original_decision=result['decision'],
        original_confidence=result['original_confidence'],
        user_feedback='confirm'
    )
    
    print(f"学习结果: {feedback_result['lesson']}")
    
    # 打印报告
    system.print_feedback_report()
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == "__main__":
    test_feedback_system()
