#!/usr/bin/env python3
"""
置信度驱动的记忆验证系统 v0.1

借鉴 LexChronos 双代理架构:
- Extraction Agent: 提取候选记忆
- Verification Agent: 验证记忆相关性并评分
- Confidence-Driven Loop: 低置信度时重新搜索或承认不知道

Author: wdai
Version: 0.1 (原型)
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Tuple
from enum import Enum
from datetime import datetime


class ConfidenceLevel(Enum):
    """置信度等级"""
    HIGH = "high"       # > 0.8: 可靠，直接使用
    MEDIUM = "medium"   # 0.5-0.8: 需要确认或补充
    LOW = "low"         # < 0.5: 不可靠，重新搜索或承认不知道


@dataclass
class MemoryCandidate:
    """记忆候选"""
    content: str
    source: str          # 来源文件
    relevance_score: float  # 相关性分数 (0-1)
    confidence: float    # 置信度 (0-1)
    reasoning: str       # 验证推理
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VerificationResult:
    """验证结果"""
    query: str
    candidates: List[MemoryCandidate]
    final_confidence: float
    decision: str        # use / confirm / retry / unknown
    answer: Optional[str] = None
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'query': self.query,
            'candidates': [c.to_dict() for c in self.candidates],
            'final_confidence': self.final_confidence,
            'decision': self.decision,
            'answer': self.answer,
            'needs_clarification': self.needs_clarification,
            'clarification_question': self.clarification_question
        }


class ExtractionAgent:
    """
    记忆提取代理
    
    负责从记忆系统中召回候选记忆
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = memory_dir
    
    def extract(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        提取候选记忆
        
        调用 memory_search 进行语义检索
        """
        try:
            # 使用真实的 memory_search
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent))
            
            from memory_search import memory_search
            
            results = memory_search(query, max_results=top_k, min_score=0.3)
            
            candidates = []
            for r in results:
                candidates.append({
                    'content': r.get('snippet', ''),
                    'source': r.get('path', 'unknown'),
                    'score': r.get('score', 0.0)
                })
            
            return candidates
        except Exception as e:
            # Fallback to mock if memory_search fails
            print(f"[ExtractionAgent] memory_search failed: {e}, using fallback")
            return [
                {
                    'content': f'关于 "{query}" 的记忆片段 1',
                    'source': 'memory/2026-03-19.md',
                    'score': 0.85
                },
                {
                    'content': f'关于 "{query}" 的记忆片段 2', 
                    'source': 'memory/2026-03-18.md',
                    'score': 0.72
                }
            ][:top_k]


class VerificationAgent:
    """
    验证代理
    
    负责验证候选记忆的相关性并给出置信度评分
    """
    
    def __init__(self):
        self.verification_history: List[Dict] = []
    
    def verify(self, query: str, candidate: Dict) -> MemoryCandidate:
        """
        验证单个候选记忆
        
        Args:
            query: 用户原始查询
            candidate: 候选记忆 {'content': ..., 'source': ..., 'score': ...}
        
        Returns:
            MemoryCandidate with confidence and reasoning
        """
        content = candidate.get('content', '')
        source = candidate.get('source', 'unknown')
        retrieval_score = candidate.get('score', 0.0)
        
        # 验证逻辑 (简化版，实际应该用LLM判断)
        reasoning_steps = []
        
        # 1. 检查关键词匹配
        query_keywords = set(query.lower().split())
        content_keywords = set(content.lower().split())
        keyword_overlap = len(query_keywords & content_keywords) / len(query_keywords) if query_keywords else 0
        reasoning_steps.append(f"关键词重叠度: {keyword_overlap:.2f}")
        
        # 2. 检查语义相关性 (基于retrieval score)
        semantic_relevance = retrieval_score
        reasoning_steps.append(f"语义相关性: {semantic_relevance:.2f}")
        
        # 3. 综合评分
        # 简单加权，实际应该更复杂
        confidence = (keyword_overlap * 0.3 + semantic_relevance * 0.7)
        
        # 4. 生成推理
        if confidence > 0.8:
            reasoning = f"高置信度: 关键词匹配度{keyword_overlap:.0%}，语义相关性{semantic_relevance:.0%}"
        elif confidence > 0.5:
            reasoning = f"中等置信度: 部分匹配，建议确认"
        else:
            reasoning = f"低置信度: 匹配度不足，可能不相关"
        
        return MemoryCandidate(
            content=content,
            source=source,
            relevance_score=semantic_relevance,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def verify_batch(self, query: str, candidates: List[Dict]) -> List[MemoryCandidate]:
        """批量验证"""
        return [self.verify(query, c) for c in candidates]


class ConfidenceDrivenMemorySystem:
    """
    置信度驱动的记忆系统
    
    主入口类，协调 ExtractionAgent 和 VerificationAgent
    """
    
    def __init__(self, max_iterations: int = 3):
        self.extraction_agent = ExtractionAgent()
        self.verification_agent = VerificationAgent()
        self.max_iterations = max_iterations
        
        # 统计
        self.stats = {
            'total_queries': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'unknown_responses': 0
        }
    
    def retrieve(self, query: str) -> VerificationResult:
        """
        检索记忆 (主入口)
        
        Confidence-Driven Loop:
        1. 提取候选记忆
        2. 验证置信度
        3. 根据置信度决策:
           - HIGH (>0.8): 直接使用
           - MEDIUM (0.5-0.8): 需要确认
           - LOW (<0.5): 重新搜索或承认不知道
        """
        self.stats['total_queries'] += 1
        
        # 第1轮: 提取 + 验证
        candidates_raw = self.extraction_agent.extract(query, top_k=5)
        candidates = self.verification_agent.verify_batch(query, candidates_raw)
        
        # 按置信度排序
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        # 决策
        if not candidates:
            return VerificationResult(
                query=query,
                candidates=[],
                final_confidence=0.0,
                decision="unknown",
                answer="我没有关于这个的记忆。",
                needs_clarification=False
            )
        
        best_candidate = candidates[0]
        final_confidence = best_candidate.confidence
        
        if final_confidence > 0.8:
            # HIGH: 直接使用
            self.stats['high_confidence'] += 1
            return VerificationResult(
                query=query,
                candidates=candidates,
                final_confidence=final_confidence,
                decision="use",
                answer=best_candidate.content,
                needs_clarification=False
            )
        
        elif final_confidence > 0.5:
            # MEDIUM: 需要确认
            self.stats['medium_confidence'] += 1
            return VerificationResult(
                query=query,
                candidates=candidates,
                final_confidence=final_confidence,
                decision="confirm",
                answer=best_candidate.content,
                needs_clarification=True,
                clarification_question=f"我找到一段可能相关的记忆 (置信度{final_confidence:.0%})，但不太确定。这是你要找的吗？"
            )
        
        else:
            # LOW: 承认不知道或重新搜索
            self.stats['low_confidence'] += 1
            self.stats['unknown_responses'] += 1
            return VerificationResult(
                query=query,
                candidates=candidates,
                final_confidence=final_confidence,
                decision="unknown",
                answer=f"我没有找到关于 '{query}' 的可靠记忆。",
                needs_clarification=True,
                clarification_question=f"我不太确定关于 '{query}' 的信息。你能提供更多上下文吗？"
            )
    
    def retrieve_with_fallback(self, query: str) -> VerificationResult:
        """
        带重试的检索
        
        如果第一轮置信度低，尝试:
        1. 扩展搜索范围
        2. 使用不同关键词
        3. 最后才承认不知道
        """
        result = self.retrieve(query)
        
        if result.decision != "unknown":
            return result
        
        # 尝试重试 (简化版)
        for i in range(self.max_iterations - 1):
            # TODO: 实现更激进的搜索策略
            # 比如：关键词扩展、模糊匹配、跨文件搜索
            pass
        
        return result
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total = self.stats['total_queries']
        if total > 0:
            return {
                **self.stats,
                'high_confidence_rate': self.stats['high_confidence'] / total,
                'medium_confidence_rate': self.stats['medium_confidence'] / total,
                'low_confidence_rate': self.stats['low_confidence'] / total,
                'unknown_rate': self.stats['unknown_responses'] / total
            }
        return self.stats
    
    def print_stats(self):
        """打印统计"""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("📊 记忆验证系统统计")
        print("="*60)
        print(f"总查询数: {stats['total_queries']}")
        print(f"高置信度直接使用: {stats['high_confidence']} ({stats.get('high_confidence_rate', 0):.1%})")
        print(f"中等置信度需确认: {stats['medium_confidence']} ({stats.get('medium_confidence_rate', 0):.1%})")
        print(f"低置信度未知: {stats['low_confidence']} ({stats.get('low_confidence_rate', 0):.1%})")
        print(f"最终承认不知道: {stats['unknown_responses']} ({stats.get('unknown_rate', 0):.1%})")


def test_confidence_driven_memory():
    """测试置信度驱动记忆系统"""
    print("="*70)
    print("🧪 测试置信度驱动记忆系统 v0.1")
    print("="*70)
    
    system = ConfidenceDrivenMemorySystem()
    
    # 测试用例
    test_queries = [
        "我的B站UID是多少？",  # 应该是未知
        "LexChronos论文",       # 应该是高置信度
        "系统架构设计",         # 可能是中等
        "随机不存在的查询"      # 应该是未知
    ]
    
    for query in test_queries:
        print(f"\n🔍 查询: {query}")
        print("-" * 50)
        
        result = system.retrieve(query)
        
        print(f"决策: {result.decision}")
        print(f"置信度: {result.final_confidence:.2f}")
        
        if result.answer:
            print(f"回答: {result.answer[:100]}...")
        
        if result.needs_clarification:
            print(f"需要澄清: {result.clarification_question}")
        
        # 显示候选
        if result.candidates:
            print(f"\n候选记忆 ({len(result.candidates)}条):")
            for i, c in enumerate(result.candidates[:3], 1):
                print(f"  {i}. [{c.confidence:.2f}] {c.content[:50]}...")
    
    # 打印统计
    system.print_stats()
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == "__main__":
    test_confidence_driven_memory()
