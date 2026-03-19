#!/usr/bin/env python3
"""
Self-Correction Feedback Loop - 自我纠错反馈循环
实现基于用户反馈的实时学习机制
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

class FeedbackType(Enum):
    """反馈类型"""
    CORRECTION = "correction"      # 用户纠正错误
    CLARIFICATION = "clarification"  # 用户要求澄清
    POSITIVE = "positive"          # 用户确认正确
    REJECTION = "rejection"        # 用户拒绝回答
    AMBIGUOUS = "ambiguous"        # 反馈不明确

@dataclass
class FeedbackRecord:
    """反馈记录"""
    id: str
    timestamp: str
    original_query: str
    my_response: str
    feedback_type: FeedbackType
    user_feedback: str
    correction_applied: bool
    lesson_extracted: str

class SelfCorrectionLoop:
    """
    自我纠错循环
    
    核心理念：
    1. 每次交互后记录上下文
    2. 识别用户反馈信号（纠正、确认、拒绝）
    3. 提取可泛化的"教训"
    4. 在后续交互中应用改进
    """
    
    def __init__(self, memory_file: str = ".learning/feedback_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.feedback_history: List[FeedbackRecord] = []
        self.learned_patterns: Dict[str, str] = {}
        self.correction_count = 0
        
        self._load_memory()
    
    def _load_memory(self):
        """加载历史反馈记忆"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 将字符串转换回FeedbackType
                history_data = data.get('history', [])
                for record in history_data:
                    record['feedback_type'] = FeedbackType(record['feedback_type'])
                
                self.feedback_history = [FeedbackRecord(**record) for record in history_data]
                self.learned_patterns = data.get('patterns', {})
                self.correction_count = data.get('correction_count', 0)
    
    def _save_memory(self):
        """保存反馈记忆"""
        # 将FeedbackType转换为字符串
        history_data = []
        for r in self.feedback_history:
            record_dict = asdict(r)
            record_dict['feedback_type'] = r.feedback_type.value
            history_data.append(record_dict)
        
        data = {
            'history': history_data,
            'patterns': self.learned_patterns,
            'correction_count': self.correction_count,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def record_interaction(self, query: str, response: str) -> str:
        """
        记录一次交互，返回交互ID供后续关联反馈
        
        Args:
            query: 用户查询
            response: 我的回答
        
        Returns:
            interaction_id: 交互唯一标识
        """
        interaction_id = f"INT-{int(time.time() * 1000)}"
        
        # 临时存储，等待反馈
        self._pending_interaction = {
            'id': interaction_id,
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        
        return interaction_id
    
    def receive_feedback(
        self, 
        interaction_id: str, 
        user_feedback: str,
        feedback_type: Optional[FeedbackType] = None
    ) -> FeedbackRecord:
        """
        接收用户反馈并处理
        
        Args:
            interaction_id: 关联的交互ID
            user_feedback: 用户的反馈文本
            feedback_type: 反馈类型（如已知）
        
        Returns:
            FeedbackRecord: 反馈记录
        """
        # 如果没有指定类型，自动检测
        if not feedback_type:
            feedback_type = self._detect_feedback_type(user_feedback)
        
        # 提取教训
        lesson = self._extract_lesson(
            self._pending_interaction['query'],
            self._pending_interaction['response'],
            user_feedback,
            feedback_type
        )
        
        # 创建反馈记录
        record = FeedbackRecord(
            id=interaction_id,
            timestamp=datetime.now().isoformat(),
            original_query=self._pending_interaction['query'],
            my_response=self._pending_interaction['response'],
            feedback_type=feedback_type,
            user_feedback=user_feedback,
            correction_applied=feedback_type in [FeedbackType.CORRECTION, FeedbackType.CLARIFICATION],
            lesson_extracted=lesson
        )
        
        # 保存
        self.feedback_history.append(record)
        if record.correction_applied:
            self.correction_count += 1
        
        # 更新学习到的模式
        self._update_learned_patterns(record)
        
        self._save_memory()
        
        return record
    
    def _detect_feedback_type(self, feedback: str) -> FeedbackType:
        """自动检测反馈类型"""
        feedback = feedback.lower()
        
        # 纠正信号
        correction_markers = [
            "不对", "错了", "应该是", "不对，是", "不，", 
            "no,", "不对，", "actually", "不对，", "修正"
        ]
        if any(m in feedback for m in correction_markers):
            return FeedbackType.CORRECTION
        
        # 澄清信号
        clarification_markers = [
            "什么意思", "没理解", "不清楚", "explain", "不明白",
            " confused", "困惑", "不懂"
        ]
        if any(m in feedback for m in clarification_markers):
            return FeedbackType.CLARIFICATION
        
        # 确认信号
        positive_markers = [
            "对的", "正确", "谢谢", "明白了", "好的", "yes", "thanks",
            "完美", "很好", "有用"
        ]
        if any(m in feedback for m in positive_markers):
            return FeedbackType.POSITIVE
        
        # 拒绝信号
        rejection_markers = [
            "不需要", "不用了", "算了", "不相关", "没用",
            " irrelevant", "不是我要的"
        ]
        if any(m in feedback for m in rejection_markers):
            return FeedbackType.REJECTION
        
        return FeedbackType.AMBIGUOUS
    
    def _extract_lesson(
        self, 
        query: str, 
        response: str, 
        feedback: str,
        feedback_type: FeedbackType
    ) -> str:
        """从反馈中提取可泛化的教训"""
        
        if feedback_type == FeedbackType.CORRECTION:
            return f"在回答'{query[:30]}...'类问题时，我应该说'{feedback[:50]}...'而不是'{response[:50]}...'"
        
        elif feedback_type == FeedbackType.CLARIFICATION:
            return f"回答'{query[:30]}...'时需要更清晰的解释，用户没有理解"
        
        elif feedback_type == FeedbackType.POSITIVE:
            return f"回答'{query[:30]}...'的方式是正确的，值得保持"
        
        elif feedback_type == FeedbackType.REJECTION:
            return f"'{query[:30]}...'可能偏离了用户真实需求"
        
        return "反馈不明确，无法提取明确教训"
    
    def _update_learned_patterns(self, record: FeedbackRecord):
        """更新学习到的模式"""
        # 提取查询类型作为模式键
        query_type = self._classify_query_type(record.original_query)
        
        if record.feedback_type == FeedbackType.CORRECTION:
            # 记录纠正后的正确答案
            self.learned_patterns[query_type] = {
                'correct_approach': record.lesson_extracted,
                'last_corrected': record.timestamp
            }
    
    def _classify_query_type(self, query: str) -> str:
        """分类查询类型"""
        # 简化的分类器
        if any(k in query for k in ["代码", "python", "javascript", "函数"]):
            return "coding"
        elif any(k in query for k in ["解释", "什么", "原理", "为什么"]):
            return "explanation"
        elif any(k in query for k in ["怎么", "如何", "步骤", "教程"]):
            return "howto"
        elif any(k in query for k in ["比较", "对比", "vs", "区别"]):
            return "comparison"
        else:
            return "general"
    
    def get_correction_suggestions(self, query: str) -> Optional[str]:
        """
        基于历史反馈，为当前查询提供改进建议
        
        Args:
            query: 当前用户查询
        
        Returns:
            如果有相关历史教训，返回建议；否则返回None
        """
        query_type = self._classify_query_type(query)
        
        # 查找同类型的历史纠正
        relevant_corrections = [
            r for r in self.feedback_history
            if r.feedback_type == FeedbackType.CORRECTION
            and self._classify_query_type(r.original_query) == query_type
        ]
        
        if relevant_corrections:
            latest = relevant_corrections[-1]
            return f"📚 **历史教训**: 在类似问题中，我曾经犯过错误。{latest.lesson_extracted[:100]}..."
        
        return None
    
    def get_stats(self) -> Dict:
        """获取反馈统计"""
        total = len(self.feedback_history)
        corrections = sum(1 for r in self.feedback_history if r.feedback_type == FeedbackType.CORRECTION)
        positive = sum(1 for r in self.feedback_history if r.feedback_type == FeedbackType.POSITIVE)
        
        return {
            'total_interactions': total,
            'corrections_received': corrections,
            'positive_feedback': positive,
            'learning_rate': corrections / total if total > 0 else 0,
            'patterns_learned': len(self.learned_patterns)
        }


# ==================== 集成到对话循环 ====================

class EnhancedDialogueSystem:
    """
    增强型对话系统
    集成不确定性检测和自我纠错
    """
    
    def __init__(self):
        from uncertainty_detector import UncertaintyDetector
        self.uncertainty_detector = UncertaintyDetector()
        self.correction_loop = SelfCorrectionLoop()
    
    def process_query(self, query: str) -> str:
        """处理用户查询"""
        # 1. 生成回答（这里调用实际的AI生成）
        response = self._generate_response(query)
        
        # 2. 检测不确定性
        uncertainty_report = self.uncertainty_detector.analyze(response, {"query": query})
        
        # 3. 获取历史纠正建议
        correction_suggestion = self.correction_loop.get_correction_suggestions(query)
        
        # 4. 组装最终输出
        final_response = response
        
        if correction_suggestion:
            final_response = f"{correction_suggestion}\n\n{final_response}"
        
        if uncertainty_report.needs_verification:
            uncertainty_statement = self.uncertainty_detector.generate_uncertainty_statement(uncertainty_report)
            final_response = f"{final_response}\n\n{uncertainty_statement}"
        
        # 5. 记录交互，等待反馈
        interaction_id = self.correction_loop.record_interaction(query, response)
        
        # 存储ID供后续反馈关联
        self._last_interaction_id = interaction_id
        
        return final_response
    
    def _generate_response(self, query: str) -> str:
        """生成回答（占位符，实际调用AI）"""
        return f"【这是AI的回答】: 关于'{query}'，我认为..."
    
    def receive_user_feedback(self, feedback: str):
        """接收用户反馈"""
        if hasattr(self, '_last_interaction_id'):
            record = self.correction_loop.receive_feedback(
                self._last_interaction_id,
                feedback
            )
            return f"✅ 反馈已记录: {record.feedback_type.value} - {record.lesson_extracted[:50]}..."
        return "❌ 没有待反馈的交互"


def demo():
    """演示自我纠错循环"""
    print("=" * 70)
    print("自我纠错反馈循环演示")
    print("=" * 70)
    
    system = EnhancedDialogueSystem()
    
    # 模拟交互
    queries = [
        "Python怎么写循环？",
        "AI是什么？",
        "股票明天会涨吗？"
    ]
    
    for query in queries:
        print(f"\n📝 用户: {query}")
        response = system.process_query(query)
        print(f"🤖 AI: {response[:150]}...")
        
        # 模拟用户反馈
        if "股票" in query:
            feedback = "不对，我是问长期趋势，不是预测明天"
            print(f"👤 反馈: {feedback}")
            result = system.receive_user_feedback(feedback)
            print(f"💾 {result}")
    
    print("\n" + "=" * 70)
    print("📊 学习统计:")
    stats = system.correction_loop.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo()
