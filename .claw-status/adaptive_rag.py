#!/usr/bin/env python3
"""
WDai Adaptive RAG v1.0 (evo-001实现)
自适应检索增强生成架构

核心组件:
1. QueryClassifier - 查询类型分类器
2. StrategySelector - 检索策略选择器  
3. ParameterTuner - 动态参数调整器
4. MultiStageRAG - 多阶段检索流程

架构流程:
用户查询 → 查询分类 → 策略选择 → 动态参数 → 多阶段检索 → 重排序 → 生成
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from wdai_unified_v3 import (
    EventBus, Context, Result, Event, EventType,
    RetrievalCapability, LocalEmbedder
)
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import time
import re


# ============================================================================
# 查询分类器 (Query Classifier)
# ============================================================================

class QueryType(Enum):
    """查询类型枚举"""
    FACTUAL = "factual"           # 事实性："什么是..." "什么时候..."
    EXPLANATORY = "explanatory"   # 解释性："为什么..." "如何工作..."
    CREATIVE = "creative"         # 创造性："写一个..." "设计一个..."
    COMPARATIVE = "comparative"   # 对比性："比较..." "区别是什么..."
    PROCEDURAL = "procedural"     # 程序性："怎么做..." "步骤是什么..."


@dataclass
class QueryClassification:
    """查询分类结果"""
    primary_type: QueryType
    confidence: float
    secondary_types: List[Tuple[QueryType, float]] = field(default_factory=list)
    complexity_score: float = 0.0  # 0-1复杂度评分


class QueryClassifier:
    """
    查询分类器
    
    基于规则和语义特征对查询进行分类
    """
    
    # 关键词模式
    PATTERNS = {
        QueryType.FACTUAL: [
            r'什么(是|时候|地方|人|原因)',
            r'谁|哪|多少|几个|第几',
            r'define|what is|when|where|who|how many',
        ],
        QueryType.EXPLANATORY: [
            r'为什么|为何|怎么(会)|原理',
            r'解释|说明|阐述|分析',
            r'why|how does|explain|analyze',
        ],
        QueryType.CREATIVE: [
            r'写|创作|设计|生成|创造',
            r'故事|诗歌|代码|脚本|文案',
            r'write|create|design|generate|draft',
        ],
        QueryType.COMPARATIVE: [
            r'比较|对比|区别|差异|优劣',
            r'vs|versus|difference|compare|better',
        ],
        QueryType.PROCEDURAL: [
            r'怎么(做|办)|如何|步骤|流程',
            r'tutorial|guide|how to|steps|procedure',
        ],
    }
    
    def __init__(self):
        self.classification_history: List[Dict] = []
    
    def classify(self, query: str) -> QueryClassification:
        """
        对查询进行分类
        
        返回主类型、置信度、次要类型
        """
        query_lower = query.lower()
        scores = {}
        
        # 基于关键词匹配计算分数
        for qtype, patterns in self.PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches * 0.3  # 每个匹配+0.3分
            scores[qtype] = min(1.0, score)
        
        # 基于查询复杂度计算
        complexity = self._calculate_complexity(query)
        
        # 排序获取主次类型
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_type = sorted_types[0][0]
        confidence = sorted_types[0][1]
        
        # 如果没有明显匹配，默认EXPLANATORY
        if confidence < 0.1:
            primary_type = QueryType.EXPLANATORY
            confidence = 0.5
        
        secondary_types = [
            (t, s) for t, s in sorted_types[1:] if s > 0.1
        ]
        
        result = QueryClassification(
            primary_type=primary_type,
            confidence=confidence,
            secondary_types=secondary_types,
            complexity_score=complexity
        )
        
        # 记录历史
        self.classification_history.append({
            'query': query[:50],
            'type': primary_type.value,
            'confidence': confidence,
            'timestamp': time.time()
        })
        
        return result
    
    def _calculate_complexity(self, query: str) -> float:
        """计算查询复杂度"""
        # 基于长度、从句数量、专业词汇等
        complexity = 0.0
        
        # 长度因子
        length = len(query)
        if length > 100:
            complexity += 0.3
        elif length > 50:
            complexity += 0.2
        
        # 从句数量（简单估计：连接词数量）
        connectors = ['因为', '所以', '但是', '如果', '虽然', 'and', 'but', 'because', 'if']
        clause_count = sum(1 for c in connectors if c in query)
        complexity += min(0.3, clause_count * 0.1)
        
        # 疑问词数量
        questions = query.count('?') + query.count('？')
        complexity += min(0.2, questions * 0.1)
        
        return min(1.0, complexity)
    
    def get_stats(self) -> Dict:
        """获取分类统计"""
        if not self.classification_history:
            return {}
        
        from collections import Counter
        type_counts = Counter([h['type'] for h in self.classification_history])
        
        return {
            'total_classified': len(self.classification_history),
            'type_distribution': dict(type_counts),
            'avg_confidence': sum(h['confidence'] for h in self.classification_history) / len(self.classification_history)
        }


# ============================================================================
# 检索策略选择器 (Strategy Selector)
# ============================================================================

@dataclass
class RetrievalStrategy:
    """检索策略配置"""
    name: str
    top_k: int
    similarity_threshold: float
    use_hybrid: bool  # 是否使用混合检索（关键词+向量）
    use_rerank: bool  # 是否重排序
    expand_query: bool  # 是否查询扩展
    max_context_length: int  # 最大上下文长度


class StrategySelector:
    """
    检索策略选择器
    
    基于查询类型选择最优检索策略
    """
    
    # 预定义策略
    STRATEGIES = {
        QueryType.FACTUAL: RetrievalStrategy(
            name="high_precision",
            top_k=3,
            similarity_threshold=0.85,
            use_hybrid=True,
            use_rerank=True,
            expand_query=False,
            max_context_length=2000
        ),
        QueryType.EXPLANATORY: RetrievalStrategy(
            name="balanced",
            top_k=5,
            similarity_threshold=0.70,
            use_hybrid=True,
            use_rerank=True,
            expand_query=True,
            max_context_length=4000
        ),
        QueryType.CREATIVE: RetrievalStrategy(
            name="diverse",
            top_k=8,
            similarity_threshold=0.60,
            use_hybrid=False,
            use_rerank=False,
            expand_query=True,
            max_context_length=6000
        ),
        QueryType.COMPARATIVE: RetrievalStrategy(
            name="multi_aspect",
            top_k=6,
            similarity_threshold=0.75,
            use_hybrid=True,
            use_rerank=True,
            expand_query=True,
            max_context_length=4000
        ),
        QueryType.PROCEDURAL: RetrievalStrategy(
            name="step_by_step",
            top_k=4,
            similarity_threshold=0.80,
            use_hybrid=True,
            use_rerank=True,
            expand_query=False,
            max_context_length=3000
        ),
    }
    
    def select(self, classification: QueryClassification) -> RetrievalStrategy:
        """
        根据查询分类选择策略
        """
        primary_type = classification.primary_type
        
        # 获取基础策略
        base_strategy = self.STRATEGIES.get(primary_type, self.STRATEGIES[QueryType.EXPLANATORY])
        
        # 根据复杂度调整参数
        if classification.complexity_score > 0.7:
            # 复杂查询：增加top_k，降低阈值以获取更多上下文
            adjusted_strategy = RetrievalStrategy(
                name=f"{base_strategy.name}_complex",
                top_k=min(10, base_strategy.top_k + 2),
                similarity_threshold=max(0.5, base_strategy.similarity_threshold - 0.1),
                use_hybrid=base_strategy.use_hybrid,
                use_rerank=True,  # 复杂查询强制重排序
                expand_query=True,  # 复杂查询强制扩展
                max_context_length=base_strategy.max_context_length + 1000
            )
            return adjusted_strategy
        
        return base_strategy
    
    def explain_selection(self, classification: QueryClassification, strategy: RetrievalStrategy) -> str:
        """解释策略选择原因"""
        reasons = [
            f"查询类型: {classification.primary_type.value} (置信度: {classification.confidence:.2f})",
            f"复杂度评分: {classification.complexity_score:.2f}",
            f"选择策略: {strategy.name}",
            f"参数: top_k={strategy.top_k}, threshold={strategy.similarity_threshold}",
        ]
        
        if strategy.use_hybrid:
            reasons.append("启用混合检索(关键词+向量)")
        if strategy.use_rerank:
            reasons.append("启用重排序")
        if strategy.expand_query:
            reasons.append("启用查询扩展")
        
        return "\n".join(reasons)


# ============================================================================
# 动态参数调整器 (Parameter Tuner)
# ============================================================================

class ParameterTuner:
    """
    动态参数调整器
    
    基于实时反馈调整检索参数
    """
    
    def __init__(self):
        self.performance_history: List[Dict] = []
        self.current_params = {
            'default_top_k': 5,
            'default_threshold': 0.70,
            'adaptation_rate': 0.1,
        }
    
    def tune(self, query_type: QueryType, 
             retrieval_result: Dict, 
             user_feedback: Optional[str] = None) -> Dict:
        """
        根据检索结果和用户反馈调整参数
        
        Args:
            query_type: 查询类型
            retrieval_result: 检索结果统计
            user_feedback: 用户反馈（satisfied/dissatisfied）
        
        Returns:
            调整后的参数建议
        """
        # 分析检索质量
        result_count = retrieval_result.get('result_count', 0)
        avg_similarity = retrieval_result.get('avg_similarity', 0)
        
        adjustments = {}
        
        # 基于结果数量调整
        if result_count < 2:
            # 结果太少，降低阈值
            adjustments['similarity_threshold'] = -0.05
            adjustments['top_k'] = +2
        elif result_count > 10:
            # 结果太多，提高阈值
            adjustments['similarity_threshold'] = +0.05
        
        # 基于平均相似度调整
        if avg_similarity > 0.9:
            # 相似度太高可能缺乏多样性
            adjustments['diversity_boost'] = True
        elif avg_similarity < 0.5:
            # 相似度太低，质量可能不高
            adjustments['similarity_threshold'] = -0.1
        
        # 基于用户反馈调整
        if user_feedback == 'dissatisfied':
            # 用户不满意，激进调整
            adjustments['top_k'] = adjustments.get('top_k', 0) + 3
            adjustments['similarity_threshold'] = adjustments.get('similarity_threshold', 0) - 0.1
            adjustments['use_rerank'] = True
        
        # 记录历史
        self.performance_history.append({
            'query_type': query_type.value,
            'result_count': result_count,
            'avg_similarity': avg_similarity,
            'feedback': user_feedback,
            'adjustments': adjustments,
            'timestamp': time.time()
        })
        
        return adjustments
    
    def get_optimized_params(self, query_type: QueryType) -> Dict:
        """获取某查询类型的优化参数"""
        # 过滤该类型的历史记录
        type_history = [
            h for h in self.performance_history 
            if h['query_type'] == query_type.value
        ]
        
        if len(type_history) < 5:
            return {}  # 数据不足，使用默认参数
        
        # 分析满意率高的记录的参数
        satisfied = [h for h in type_history if h['feedback'] == 'satisfied']
        
        if not satisfied:
            return {}
        
        # 提取共同特征
        avg_count = sum(h['result_count'] for h in satisfied) / len(satisfied)
        avg_sim = sum(h['avg_similarity'] for h in satisfied) / len(satisfied)
        
        return {
            'recommended_top_k': int(avg_count),
            'recommended_threshold': avg_sim * 0.9,  # 留点余量
            'confidence': len(satisfied) / len(type_history)
        }


# ============================================================================
# 多阶段RAG引擎 (Multi-Stage RAG)
# ============================================================================

class MultiStageRAG:
    """
    多阶段RAG引擎
    
    实现完整的自适应检索流程
    """
    
    def __init__(self, base_retrieval: RetrievalCapability):
        self.base_retrieval = base_retrieval
        self.classifier = QueryClassifier()
        self.strategy_selector = StrategySelector()
        self.parameter_tuner = ParameterTuner()
        
        # 统计
        self.query_stats: Dict[str, Dict] = {}
    
    def retrieve(self, query: str, context: Context) -> Result:
        """
        执行自适应检索
        
        完整流程:
        1. 查询分类
        2. 策略选择
        3. 查询扩展（可选）
        4. 初步检索
        5. 重排序（可选）
        6. 上下文构建
        """
        start_time = time.time()
        
        # 1. 查询分类
        classification = self.classifier.classify(query)
        
        # 2. 策略选择
        strategy = self.strategy_selector.select(classification)
        
        # 3. 查询扩展（如果需要）
        expanded_queries = [query]
        if strategy.expand_query:
            expanded_queries.extend(self._expand_query(query, classification))
        
        # 4. 多查询检索
        all_results = []
        for q in expanded_queries:
            results = self._retrieve_single(q, strategy)
            all_results.extend(results)
        
        # 去重
        seen = set()
        unique_results = []
        for r in all_results:
            key = r.get('content', '')[:100]
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        # 5. 重排序（如果需要）
        if strategy.use_rerank and len(unique_results) > strategy.top_k:
            unique_results = self._rerank(query, unique_results, strategy)
        
        # 6. 截断到top_k
        final_results = unique_results[:strategy.top_k]
        
        # 计算指标
        avg_sim = sum(r.get('similarity', 0) for r in final_results) / len(final_results) if final_results else 0
        
        # 记录统计
        self.query_stats[context.query_id] = {
            'query': query[:50],
            'type': classification.primary_type.value,
            'strategy': strategy.name,
            'expanded_queries': len(expanded_queries),
            'retrieved': len(all_results),
            'final': len(final_results),
            'avg_similarity': avg_sim,
            'latency_ms': (time.time() - start_time) * 1000
        }
        
        return Result(
            success=True,
            data={
                'results': final_results,
                'classification': {
                    'type': classification.primary_type.value,
                    'confidence': classification.confidence,
                    'complexity': classification.complexity_score
                },
                'strategy': {
                    'name': strategy.name,
                    'top_k': strategy.top_k,
                    'threshold': strategy.similarity_threshold
                }
            },
            confidence=classification.confidence,
            sources=[r.get('key', '') for r in final_results]
        )
    
    def _expand_query(self, query: str, classification: QueryClassification) -> List[str]:
        """查询扩展"""
        expansions = []
        
        # 基于类型添加同义词/相关词
        if classification.primary_type == QueryType.EXPLANATORY:
            # 解释性查询：添加"原因" "原理" 等
            if '为什么' in query:
                expansions.append(query.replace('为什么', '原因'))
        
        elif classification.primary_type == QueryType.COMPARATIVE:
            # 对比性查询：分别查询两个对象
            parts = re.split(r'和|vs|versus|与', query)
            if len(parts) == 2:
                expansions.extend([p.strip() for p in parts])
        
        return expansions[:2]  # 最多2个扩展查询
    
    def _retrieve_single(self, query: str, strategy: RetrievalStrategy) -> List[Dict]:
        """执行单次检索"""
        # 调用基础检索能力
        query_vector = self.base_retrieval.embedder.encode(query)
        
        results = []
        for key, stored_vector in self.base_retrieval.index.items():
            similarity = self._cosine_similarity(query_vector, stored_vector)
            if similarity >= strategy.similarity_threshold:
                results.append({
                    'key': key,
                    'content': self.base_retrieval.memory_store[key]['content'],
                    'similarity': similarity,
                    'metadata': self.base_retrieval.memory_store[key].get('metadata', {})
                })
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
    
    def _rerank(self, query: str, results: List[Dict], strategy: RetrievalStrategy) -> List[Dict]:
        """重排序（简化实现）"""
        # 基于查询相关性和多样性重排序
        # 实际应使用更复杂的重排序模型
        
        # 简单策略：保持高相似度，但增加多样性
        reranked = []
        topics = set()
        
        for r in results:
            topic = r['metadata'].get('category', 'general')
            if topic not in topics or r['similarity'] > 0.9:
                reranked.append(r)
                topics.add(topic)
        
        return reranked
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def feedback(self, query_id: str, feedback: str):
        """接收用户反馈，调整参数"""
        if query_id not in self.query_stats:
            return
        
        stats = self.query_stats[query_id]
        query_type = QueryType(stats['type'])
        
        # 调用参数调整器
        adjustments = self.parameter_tuner.tune(
            query_type,
            {'result_count': stats['final'], 'avg_similarity': stats['avg_similarity']},
            feedback
        )
        
        print(f"🎛️ 参数调整: {adjustments}")
    
    def get_stats(self) -> Dict:
        """获取检索统计"""
        if not self.query_stats:
            return {}
        
        total = len(self.query_stats)
        type_dist = {}
        avg_latency = 0
        
        for stats in self.query_stats.values():
            t = stats['type']
            type_dist[t] = type_dist.get(t, 0) + 1
            avg_latency += stats['latency_ms']
        
        return {
            'total_queries': total,
            'type_distribution': type_dist,
            'avg_latency_ms': avg_latency / total,
            'classifier_stats': self.classifier.get_stats()
        }


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Adaptive RAG v1.0 - 测试")
    print("="*60)
    
    # 创建基础检索
    from wdai_unified_v3 import RetrievalCapability, EventBus
    event_bus = EventBus()
    base_retrieval = RetrievalCapability(event_bus)
    
    # 添加测试知识
    print("\n📚 添加测试知识...")
    test_knowledge = [
        ("WDai采用分层记忆架构，包括工作记忆、情景记忆、语义记忆", {'category': 'architecture'}),
        ("向量存储使用384维本地嵌入，支持离线运行", {'category': 'tech'}),
        ("多路径推理包括直觉、分析、保守、创新四条路径", {'category': 'reasoning'}),
        ("自适应RAG根据查询类型动态选择检索策略", {'category': 'rag'}),
        ("查询分类器将查询分为事实性、解释性、创造性等类型", {'category': 'rag'}),
    ]
    
    for content, meta in test_knowledge:
        base_retrieval.add_memory(content, meta)
    
    print(f"   已添加{len(test_knowledge)}条知识")
    
    # 创建自适应RAG
    print("\n🔧 初始化自适应RAG...")
    adaptive_rag = MultiStageRAG(base_retrieval)
    
    # 测试不同类型的查询
    test_queries = [
        ("什么是WDai的记忆架构？", "factual"),
        ("为什么使用分层记忆？", "explanatory"),
        ("写一个关于向量存储的说明", "creative"),
        ("比较直觉路径和分析路径", "comparative"),
        ("怎么用自适应RAG？", "procedural"),
    ]
    
    print(f"\n🧪 测试{len(test_queries)}个不同类型的查询:\n")
    
    for query, expected_type in test_queries:
        print(f"📝 查询: {query}")
        
        # 分类
        classification = adaptive_rag.classifier.classify(query)
        print(f"   分类: {classification.primary_type.value} (置信度: {classification.confidence:.2f})")
        print(f"   复杂度: {classification.complexity_score:.2f}")
        
        # 选择策略
        strategy = adaptive_rag.strategy_selector.select(classification)
        print(f"   策略: {strategy.name} (k={strategy.top_k}, threshold={strategy.similarity_threshold})")
        
        # 执行检索
        from wdai_unified_v3 import Context
        context = Context(session_id="test", query_id=f"test_{hash(query) % 10000}")
        result = adaptive_rag.retrieve(query, context)
        
        if result.success:
            data = result.data
            print(f"   结果数: {len(data['results'])}")
            print(f"   扩展查询: {data['classification']['complexity']:.2f}")
            
            if data['results']:
                print(f"   最高相似度: {data['results'][0]['similarity']:.2f}")
        
        print()
    
    # 统计
    print("\n📊 统计信息")
    stats = adaptive_rag.get_stats()
    print(f"   总查询数: {stats.get('total_queries', 0)}")
    print(f"   类型分布: {stats.get('type_distribution', {})}")
    print(f"   平均延迟: {stats.get('avg_latency_ms', 0):.1f}ms")
    
    print("\n" + "="*60)
    print("✅ 自适应RAG测试完成")
    print("="*60)
