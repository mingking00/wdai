#!/usr/bin/env python3
"""
WDai Vector Store v3.4 (evo-003集成)
集成向量存储优化
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from wdai_v33_multiagent import WDaiSystemV33
from vector_store_opt import HybridRetriever, QueryCache
import hashlib
import time


class WDaiSystemV34(WDaiSystemV33):
    """
    WDai v3.4
    新增：向量存储优化 (evo-003)
    """
    
    _instance = None
    
    def __init__(self):
        if self._initialized:
            return
        
        # 先初始化父类（v3.3）
        super().__init__()
        
        print("\n" + "="*60)
        print("🔥 升级至 WDai v3.4")
        print("="*60)
        
        # 用优化后的检索器替换基础检索
        print("🚀 启用优化向量存储...")
        self.hybrid_retriever = HybridRetriever(
            vector_weight=0.7,
            keyword_weight=0.3
        )
        self.query_cache = QueryCache(max_size=1000, ttl_seconds=3600)
        
        # 迁移现有记忆
        self._migrate_memories()
        
        print("✅ 向量存储优化已集成")
        print("   - HNSW索引: 高效近似最近邻搜索")
        print("   - BM25检索: 关键词匹配")
        print("   - 混合检索: 向量+关键词融合")
        print("   - 查询缓存: 高频查询加速")
        print("="*60)
    
    def _migrate_memories(self):
        """迁移现有记忆到新索引"""
        print(f"\n🔄 迁移{len(self.retrieval.memory_store)}条记忆...")
        
        for key, data in self.retrieval.memory_store.items():
            self.hybrid_retriever.add_document(
                doc_id=key,
                text=data['content'],
                metadata=data.get('metadata', {})
            )
        
        print(f"   已迁移{len(self.retrieval.memory_store)}条记忆")
    
    def optimized_search(self, query: str, top_k: int = 10, use_cache: bool = True) -> dict:
        """
        优化的检索接口
        
        流程:
        1. 检查缓存
        2. 混合检索 (HNSW + BM25)
        3. 缓存结果
        """
        # 检查缓存
        if use_cache:
            cached = self.query_cache.get(query, top_k)
            if cached:
                return {
                    'success': True,
                    'results': cached,
                    'source': 'cache',
                    'count': len(cached)
                }
        
        # 执行混合检索
        results = self.hybrid_retriever.search(query, top_k)
        
        # 缓存结果
        if use_cache:
            self.query_cache.set(query, top_k, results)
        
        return {
            'success': True,
            'results': results,
            'source': 'hybrid_search',
            'count': len(results)
        }
    
    def add_knowledge(self, content: str, metadata: dict = None) -> str:
        """添加知识（同时更新两个索引）"""
        # 添加到基础索引
        key = super().add_knowledge(content, metadata)
        
        # 添加到优化索引
        self.hybrid_retriever.add_document(key, content, metadata)
        
        return key
    
    def get_vector_stats(self) -> dict:
        """获取向量存储统计"""
        stats = self.hybrid_retriever.get_stats()
        stats['cache_hit_rate'] = self.query_cache.get_hit_rate()
        return stats


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Vector Store v3.4 - 集成测试")
    print("="*60)
    
    # 创建系统
    system = WDaiSystemV34()
    
    # 添加测试知识
    print("\n📚 添加测试知识...")
    test_knowledge = [
        "自适应RAG根据查询类型动态选择检索策略",
        "多Agent协作框架支持角色扮演和工作流编排",
        "HNSW索引实现高效的近似最近邻搜索",
        "BM25算法用于关键词匹配和文本检索",
        "混合检索结合向量相似度和关键词匹配的优势",
    ]
    
    for content in test_knowledge:
        system.add_knowledge(content, {'category': 'test'})
    
    print(f"   已添加{len(test_knowledge)}条知识")
    
    # 测试优化检索
    print("\n🔍 测试优化检索:\n")
    
    test_queries = [
        "RAG策略",
        "Agent协作",
        "向量索引",
    ]
    
    for query in test_queries:
        print(f"📝 查询: '{query}'")
        
        # 第一次查询（非缓存）
        result = system.optimized_search(query, top_k=3, use_cache=True)
        print(f"   来源: {result['source']}, 结果数: {result['count']}")
        
        # 第二次查询（缓存）
        result2 = system.optimized_search(query, top_k=3, use_cache=True)
        print(f"   来源: {result2['source']}, 结果数: {result2['count']}")
        
        print()
    
    # 统计
    print("\n📊 向量存储统计")
    stats = system.get_vector_stats()
    print(f"   总文档: {stats['total_documents']}")
    print(f"   HNSW节点: {stats['hnsw_nodes']}")
    print(f"   BM25词项: {stats['bm25_terms']}")
    print(f"   平均延迟: {stats['avg_latency_ms']:.1f}ms")
    print(f"   缓存命中率: {stats['cache_hit_rate']:.1%}")
    
    print("\n" + "="*60)
    print("✅ v3.4 向量存储优化集成测试完成")
    print("="*60)
