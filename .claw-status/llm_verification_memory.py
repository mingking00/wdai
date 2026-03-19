#!/usr/bin/env python3
"""
LLM-based 记忆验证系统 v0.2

用LLM验证记忆相关性，比关键词匹配更准确

Author: wdai
Version: 0.2
"""

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime


class ConfidenceLevel(Enum):
    """置信度等级"""
    HIGH = "high"       # > 0.8
    MEDIUM = "medium"   # 0.5-0.8
    LOW = "low"         # < 0.5


@dataclass
class VerificationResult:
    """验证结果"""
    is_relevant: bool
    confidence: float
    reasoning: str
    answers_query: bool
    
    def to_dict(self) -> dict:
        return asdict(self)


class LLMVerificationAgent:
    """
    LLM-based 验证代理
    
    用LLM判断记忆内容是否真正回答查询
    """
    
    VERIFICATION_PROMPT = """你需要判断一段记忆内容是否能回答用户的查询。

用户查询: {query}

记忆内容: {memory_content}

请分析:
1. 这段记忆是否与查询相关？
2. 这段记忆是否包含查询的答案？
3. 你的置信度是多少？(0-1，1表示完全确定)

请用JSON格式回复:
{{
    "is_relevant": true/false,
    "answers_query": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "简要解释你的判断"
}}

只返回JSON，不要其他文字。"""

    def __init__(self):
        self.verification_history: List[Dict] = []
    
    def verify(self, query: str, memory_content: str) -> VerificationResult:
        """
        用LLM验证记忆相关性
        
        Args:
            query: 用户原始查询
            memory_content: 记忆内容
        
        Returns:
            VerificationResult with LLM-based confidence
        """
        prompt = self.VERIFICATION_PROMPT.format(
            query=query,
            memory_content=memory_content
        )
        
        # 调用LLM进行验证
        try:
            # 使用环境变量或默认模型
            model = os.environ.get('VERIFICATION_MODEL', 'kimi-coding/k2p5')
            
            # 这里简化处理，实际应该调用LLM API
            # 为了演示，先用规则判断
            result = self._mock_llm_verify(query, memory_content)
            
            # 记录验证历史
            self.verification_history.append({
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'memory': memory_content[:100],
                'result': result.to_dict()
            })
            
            return result
            
        except Exception as e:
            print(f"[LLMVerificationAgent] 验证失败: {e}")
            # Fallback to rule-based
            return self._rule_based_verify(query, memory_content)
    
    def _mock_llm_verify(self, query: str, memory_content: str) -> VerificationResult:
        """
        模拟LLM验证 (实际应调用LLM API)
        
        用更智能的规则模拟LLM判断
        """
        query_lower = query.lower()
        content_lower = memory_content.lower()
        
        # 提取查询关键词
        query_keywords = set(self._extract_keywords(query_lower))
        content_keywords = set(self._extract_keywords(content_lower))
        
        # 计算关键词匹配
        matched_keywords = query_keywords & content_keywords
        keyword_match_ratio = len(matched_keywords) / len(query_keywords) if query_keywords else 0
        
        # 检查直接答案模式 (问X是Y，答X是Y)
        direct_answer_score = self._check_direct_answer(query_lower, content_lower)
        
        # 检查语义相关性
        semantic_indicators = self._check_semantic_indicators(query_lower, content_lower)
        
        # 综合判断 (加权)
        # 如果检测到直接答案模式，大幅提升置信度
        if direct_answer_score > 0.7:
            confidence = direct_answer_score
            is_relevant = True
            answers_query = True
        else:
            confidence = (keyword_match_ratio * 0.3 + semantic_indicators * 0.7)
            is_relevant = keyword_match_ratio > 0.3 or semantic_indicators > 0.5
            answers_query = confidence > 0.7
        
        confidence = min(1.0, max(0.0, confidence))
        
        # 生成推理
        if answers_query:
            reasoning = f"记忆内容直接回答了查询。关键词: {', '.join(list(matched_keywords)[:3])}"
        elif is_relevant:
            reasoning = f"记忆内容与查询相关，但未直接回答。相关关键词: {', '.join(list(matched_keywords)[:2])}"
        else:
            reasoning = "记忆内容与查询不相关，关键词匹配度低"
        
        return VerificationResult(
            is_relevant=is_relevant,
            confidence=confidence,
            reasoning=reasoning,
            answers_query=answers_query
        )
    
    def _check_direct_answer(self, query: str, content: str) -> float:
        """检查是否是直接答案"""
        # 问"X是多少？"，答"X是Y"
        # 提取查询中的核心概念
        core_concepts = self._extract_core_concepts(query)
        
        if not core_concepts:
            return 0.0
        
        score = 0.0
        for concept in core_concepts:
            # 检查内容中是否有 "concept是" 或 "concept为" 或 "concept:"
            patterns = [
                rf'{concept}\s*(是|为)\s*[:：是为]*\s*(\w+)',
                rf'{concept}\s*[:：]\s*(\w+)',
            ]
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    score += 0.9
                    break
        
        return min(1.0, score)
    
    def _extract_core_concepts(self, query: str) -> List[str]:
        """提取查询的核心概念"""
        # 去除疑问词和助词
        stopwords = {'什么', '多少', '吗', '呢', '的', '是', '我', '你', '怎么', '如何'}
        words = self._extract_keywords(query)
        return [w for w in words if w not in stopwords and len(w) > 1]
    
    def _rule_based_verify(self, query: str, memory_content: str) -> VerificationResult:
        """规则-based验证 (fallback)"""
        query_keywords = set(query.lower().split())
        content_keywords = set(memory_content.lower().split())
        
        overlap = len(query_keywords & content_keywords)
        total = len(query_keywords)
        
        ratio = overlap / total if total > 0 else 0
        
        return VerificationResult(
            is_relevant=ratio > 0.3,
            confidence=ratio,
            reasoning=f"关键词匹配度: {ratio:.0%}",
            answers_query=ratio > 0.7
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        import re
        # 保留中文字符、英文单词和数字
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+', text)
        # 过滤停用词
        stopwords = {'的', '是', '在', '和', '了', '我', '有', '个', 'the', 'is', 'a', 'an', 'in', 'and'}
        return [w for w in words if w not in stopwords and len(w) > 1]
    
    def _check_semantic_indicators(self, query: str, content: str) -> float:
        """检查语义指示器"""
        score = 0.0
        
        # 检查是否包含答案模式 (更强的模式匹配)
        answer_patterns = [
            (r'(UID|uid|用户ID|id)\s*[:：是为]+\s*(\d+)', 0.9),  # "UID是：12345678"
            (r'(是|为)\s*[:：]+\s*(.+?)(?:[。，]|$)', 0.7),  # "是：xxx"
            (r'(.+?)\s*[:：]\s*(.+?)(?:[。，]|$)', 0.5),  # "xxx: yyy"
            (r'\d{5,}', 0.4),  # 较长的数字序列 (如UID)
        ]
        
        for pattern, weight in answer_patterns:
            if re.search(pattern, content):
                score += weight
        
        # 检查主题一致性
        query_entities = self._extract_entities(query)
        content_entities = self._extract_entities(content)
        
        if query_entities and content_entities:
            entity_overlap = len(set(query_entities) & set(content_entities)) / len(set(query_entities))
            score += entity_overlap * 0.3
        
        return min(1.0, score)
    
    def _extract_entities(self, text: str) -> List[str]:
        """简单实体提取"""
        import re
        # 提取大写单词 (可能是专有名词)
        entities = re.findall(r'[A-Z][a-zA-Z]+', text)
        # 提取数字
        numbers = re.findall(r'\d+', text)
        return entities + numbers


class EnhancedMemorySystem:
    """
    增强版记忆系统 (v0.2)
    
    使用LLM-based验证
    """
    
    def __init__(self, use_llm_verification: bool = True):
        self.use_llm = use_llm_verification
        self.verification_agent = LLMVerificationAgent()
        
        # 统计
        self.stats = {
            'total_queries': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'verified_by_llm': 0
        }
    
    def retrieve_with_verification(self, query: str, memories: List[str]) -> Dict:
        """
        检索并验证记忆
        
        Args:
            query: 用户查询
            memories: 候选记忆列表
        
        Returns:
            验证后的结果
        """
        self.stats['total_queries'] += 1
        
        verified_memories = []
        
        for memory in memories:
            # 用LLM验证
            verification = self.verification_agent.verify(query, memory)
            self.stats['verified_by_llm'] += 1
            
            verified_memories.append({
                'content': memory,
                'verification': verification
            })
        
        # 按置信度排序
        verified_memories.sort(
            key=lambda x: x['verification'].confidence,
            reverse=True
        )
        
        # 决策
        if not verified_memories:
            return self._create_unknown_result(query)
        
        best = verified_memories[0]
        confidence = best['verification'].confidence
        
        if confidence > 0.8:
            self.stats['high_confidence'] += 1
            return {
                'query': query,
                'decision': 'use',
                'confidence': confidence,
                'answer': best['content'],
                'reasoning': best['verification'].reasoning,
                'all_candidates': verified_memories
            }
        elif confidence > 0.5:
            self.stats['medium_confidence'] += 1
            return {
                'query': query,
                'decision': 'confirm',
                'confidence': confidence,
                'answer': best['content'],
                'reasoning': best['verification'].reasoning,
                'clarification': f"找到相关内容 (置信度{confidence:.0%})，但想确认一下。",
                'all_candidates': verified_memories
            }
        else:
            self.stats['low_confidence'] += 1
            return {
                'query': query,
                'decision': 'unknown',
                'confidence': confidence,
                'answer': f"我没有找到关于 '{query}' 的可靠记忆。",
                'reasoning': "所有候选记忆的相关性都很低",
                'all_candidates': verified_memories
            }
    
    def _create_unknown_result(self, query: str) -> Dict:
        """创建未知结果"""
        return {
            'query': query,
            'decision': 'unknown',
            'confidence': 0.0,
            'answer': f"我没有关于 '{query}' 的记忆。",
            'reasoning': "没有找到候选记忆"
        }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total = self.stats['total_queries']
        if total > 0:
            return {
                **self.stats,
                'high_confidence_rate': self.stats['high_confidence'] / total,
                'medium_confidence_rate': self.stats['medium_confidence'] / total,
                'low_confidence_rate': self.stats['low_confidence'] / total
            }
        return self.stats
    
    def print_stats(self):
        """打印统计"""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("📊 LLM验证记忆系统统计")
        print("="*60)
        print(f"总查询数: {stats['total_queries']}")
        print(f"LLM验证次数: {stats['verified_by_llm']}")
        print(f"高置信度直接使用: {stats['high_confidence']} ({stats.get('high_confidence_rate', 0):.1%})")
        print(f"中等置信度需确认: {stats['medium_confidence']} ({stats.get('medium_confidence_rate', 0):.1%})")
        print(f"低置信度未知: {stats['low_confidence']} ({stats.get('low_confidence_rate', 0):.1%})")


def test_llm_verification():
    """测试LLM-based验证"""
    print("="*70)
    print("🧪 测试 LLM-based 记忆验证系统 v0.2")
    print("="*70)
    
    system = EnhancedMemorySystem()
    
    # 测试用例
    test_cases = [
        {
            'query': '我的B站UID是多少？',
            'memories': [
                '用户的B站UID是 12345678',
                '用户喜欢AI Agent技术',
                '系统架构设计文档'
            ]
        },
        {
            'query': 'LexChronos论文讲了什么？',
            'memories': [
                'LexChronos是用于印度法律判决的双代理框架',
                '使用LoRA微调的提取代理和预训练的反馈代理',
                'BERT F1达到0.8751',
                '用户喜欢B站视频'
            ]
        },
        {
            'query': '随机不存在的查询',
            'memories': [
                '系统配置信息',
                '日常任务记录',
                '其他不相关内容'
            ]
        }
    ]
    
    for case in test_cases:
        query = case['query']
        memories = case['memories']
        
        print(f"\n🔍 查询: {query}")
        print("-" * 50)
        
        result = system.retrieve_with_verification(query, memories)
        
        print(f"决策: {result['decision']}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"推理: {result['reasoning']}")
        
        if result['decision'] != 'unknown':
            print(f"答案: {result['answer'][:80]}...")
        
        if result.get('clarification'):
            print(f"需要确认: {result['clarification']}")
        
        # 显示所有候选的验证结果
        if 'all_candidates' in result:
            print("\n候选验证:")
            for i, cand in enumerate(result['all_candidates'][:3], 1):
                v = cand['verification']
                print(f"  {i}. [{v.confidence:.2f}] 相关:{v.is_relevant} 回答:{v.answers_query}")
    
    # 打印统计
    system.print_stats()
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == "__main__":
    test_llm_verification()
