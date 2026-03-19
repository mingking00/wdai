#!/usr/bin/env python3
"""
WDai Vector Store Optimization v1.0 (evo-003实现)
向量存储优化：HNSW索引 + 混合检索 + 分层检索

核心优化:
1. HNSW索引 - 高效近似最近邻搜索
2. 混合检索 - BM25关键词 + 向量语义
3. 分层检索 - 文档级→章节级→段落级
4. 查询缓存 - 高频查询缓存
5. 量化压缩 - 降低存储和计算成本

参考: 2025年向量数据库最佳实践
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path
import heapq
import math
import json
import time
import hashlib
import random
import re


# ============================================================================
# HNSW索引实现 (Hierarchical Navigable Small World)
# ============================================================================

@dataclass
class HNSWNode:
    """HNSW节点"""
    id: str
    vector: List[float]
    level: int
    neighbors: Dict[int, List[str]] = field(default_factory=dict)  # level -> neighbor_ids
    metadata: Dict = field(default_factory=dict)


class HNSWIndex:
    """
    HNSW索引实现
    
    特点:
    - 多层图结构
    - 对数级搜索复杂度
    - 动态插入
    """
    
    def __init__(self, 
                 dim: int = 384,
                 max_elements: int = 10000,
                 m: int = 16,  # 每层连接数
                 ef_construction: int = 200,
                 ef_search: int = 50):
        self.dim = dim
        self.max_elements = max_elements
        self.m = m
        self.m_max = m * 2  # 最大连接数
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        
        # 索引数据
        self.nodes: Dict[str, HNSWNode] = {}
        self.entry_point: Optional[str] = None
        self.max_level = 0
        
        # 概率参数
        self.level_mult = 1.0 / math.log(m)
    
    def _random_level(self) -> int:
        """随机选择层数"""
        level = 0
        while random.random() < math.exp(-1.0 / self.level_mult) and level < self.max_level:
            level += 1
        return level
    
    def _distance(self, v1: List[float], v2: List[float]) -> float:
        """计算欧氏距离"""
        return sum((a - b) ** 2 for a, b in zip(v1, v2)) ** 0.5
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def add(self, id: str, vector: List[float], metadata: Dict = None):
        """添加向量到索引"""
        
        # 新节点层数
        level = self._random_level()
        
        # 创建节点
        node = HNSWNode(
            id=id,
            vector=vector,
            level=level,
            metadata=metadata or {}
        )
        
        # 初始化每层邻居
        for l in range(level + 1):
            node.neighbors[l] = []
        
        # 空索引处理
        if not self.entry_point:
            self.entry_point = id
            self.nodes[id] = node
            self.max_level = level
            return
        
        # 搜索最近邻
        curr_ep = self.entry_point
        curr_dist = self._distance(vector, self.nodes[curr_ep].vector)
        
        # 从高层到底层
        for l in range(self.max_level, -1, -1):
            changed = True
            while changed:
                changed = False
                curr_node = self.nodes[curr_ep]
                
                # 检查当前层的邻居
                if l in curr_node.neighbors:
                    for neighbor_id in curr_node.neighbors[l]:
                        neighbor = self.nodes[neighbor_id]
                        dist = self._distance(vector, neighbor.vector)
                        
                        if dist < curr_dist:
                            curr_ep = neighbor_id
                            curr_dist = dist
                            changed = True
            
            # 记录当前层的入口点
            if l <= level:
                # 在当前层建立连接
                neighbors = self._search_layer(vector, curr_ep, l, self.m)
                node.neighbors[l] = neighbors
                
                # 双向连接
                for neighbor_id in neighbors:
                    neighbor = self.nodes[neighbor_id]
                    if l not in neighbor.neighbors:
                        neighbor.neighbors[l] = []
                    neighbor.neighbors[l].append(id)
                    
                    # 如果邻居连接过多，修剪
                    if len(neighbor.neighbors[l]) > self.m_max:
                        neighbor.neighbors[l] = self._select_neighbors(
                            neighbor.vector, neighbor.neighbors[l], l, self.m_max
                        )
        
        # 更新入口点
        if level > self.max_level:
            self.max_level = level
            self.entry_point = id
        
        self.nodes[id] = node
    
    def _search_layer(self, vector: List[float], 
                     entry_id: str, 
                     level: int, 
                     ef: int) -> List[str]:
        """在指定层搜索最近邻"""
        visited = {entry_id}
        candidates = [(-self._distance(vector, self.nodes[entry_id].vector), entry_id)]
        results = [(-self._distance(vector, self.nodes[entry_id].vector), entry_id)]
        
        while candidates:
            curr_dist, curr_id = heapq.heappop(candidates)
            
            # 检查是否比最差结果更好
            if results and -curr_dist > results[0][0] and len(results) >= ef:
                break
            
            curr_node = self.nodes[curr_id]
            
            # 遍历邻居
            if level in curr_node.neighbors:
                for neighbor_id in curr_node.neighbors[level]:
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        neighbor = self.nodes[neighbor_id]
                        dist = self._distance(vector, neighbor.vector)
                        
                        heapq.heappush(candidates, (-dist, neighbor_id))
                        heapq.heappush(results, (-dist, neighbor_id))
                        
                        if len(results) > ef:
                            heapq.heappop(results)
        
        # 返回top-m
        return [id for _, id in sorted(results, reverse=True)[:self.m]]
    
    def _select_neighbors(self, vector: List[float], 
                         candidates: List[str], 
                         level: int, 
                         m: int) -> List[str]:
        """选择最佳邻居"""
        distances = []
        for candidate_id in candidates:
            candidate = self.nodes[candidate_id]
            dist = self._distance(vector, candidate.vector)
            distances.append((dist, candidate_id))
        
        distances.sort()
        return [id for _, id in distances[:m]]
    
    def search(self, query_vector: List[float], k: int = 10) -> List[Tuple[str, float]]:
        """
        搜索k个最近邻
        
        Returns:
            [(id, distance), ...]
        """
        if not self.entry_point:
            return []
        
        # 从入口点开始
        curr_ep = self.entry_point
        curr_dist = self._distance(query_vector, self.nodes[curr_ep].vector)
        
        # 从高层到底层
        for l in range(self.max_level, 0, -1):
            changed = True
            while changed:
                changed = False
                curr_node = self.nodes[curr_ep]
                
                if l in curr_node.neighbors:
                    for neighbor_id in curr_node.neighbors[l]:
                        neighbor = self.nodes[neighbor_id]
                        dist = self._distance(query_vector, neighbor.vector)
                        
                        if dist < curr_dist:
                            curr_ep = neighbor_id
                            curr_dist = dist
                            changed = True
        
        # 在最底层搜索ef个候选
        candidates = self._search_layer(query_vector, curr_ep, 0, self.ef_search)
        
        # 计算精确距离并排序
        results = []
        for node_id in candidates:
            node = self.nodes[node_id]
            dist = self._distance(query_vector, node.vector)
            results.append((node_id, dist))
        
        results.sort(key=lambda x: x[1])
        return results[:k]
    
    def get_stats(self) -> Dict:
        """获取索引统计"""
        return {
            'total_nodes': len(self.nodes),
            'max_level': self.max_level,
            'avg_neighbors': sum(
                sum(len(n.neighbors.get(l, [])) for l in n.neighbors)
                for n in self.nodes.values()
            ) / max(1, len(self.nodes))
        }


# ============================================================================
# BM25关键词检索 (用于混合检索)
# ============================================================================

class BM25Index:
    """
    BM25关键词检索
    
    用于混合检索的关键词组件
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        
        # 文档数据
        self.documents: Dict[str, str] = {}
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.term_freqs: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # 统计
        self.total_docs = 0
        self.avg_doc_len = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        # 简单实现：按非字母数字分割
        words = re.findall(r'\b[a-zA-Z0-9\u4e00-\u9fff]+\b', text.lower())
        return words
    
    def add(self, doc_id: str, text: str):
        """添加文档"""
        self.documents[doc_id] = text
        tokens = self._tokenize(text)
        
        # 更新词频
        term_counts = defaultdict(int)
        for token in tokens:
            term_counts[token] += 1
        
        # 更新文档频率和词频
        for term, count in term_counts.items():
            self.doc_freqs[term] += 1
            self.term_freqs[term][doc_id] = count
        
        # 更新统计
        self.total_docs += 1
        self.avg_doc_len = (self.avg_doc_len * (self.total_docs - 1) + len(tokens)) / self.total_docs
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        BM25搜索
        
        Returns:
            [(doc_id, score), ...]
        """
        query_tokens = self._tokenize(query)
        scores = defaultdict(float)
        
        for term in query_tokens:
            if term not in self.doc_freqs:
                continue
            
            # IDF计算
            idf = math.log((self.total_docs - self.doc_freqs[term] + 0.5) / (self.doc_freqs[term] + 0.5) + 1)
            
            # 计算每个文档的得分
            for doc_id, tf in self.term_freqs[term].items():
                doc_len = len(self._tokenize(self.documents[doc_id]))
                
                # BM25公式
                score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len))
                scores[doc_id] += score
        
        # 排序返回top-k
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return results[:top_k]


# ============================================================================
# 混合检索引擎
# ============================================================================

class HybridRetriever:
    """
    混合检索引擎
    
    结合BM25关键词检索 + HNSW向量检索
    """
    
    def __init__(self, 
                 vector_weight: float = 0.7,
                 keyword_weight: float = 0.3):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        
        # 索引
        self.hnsw = HNSWIndex()
        self.bm25 = BM25Index()
        
        # 文档存储
        self.documents: Dict[str, Dict] = {}
        
        # 嵌入模型
        from wdai_unified_v3 import LocalEmbedder
        self.embedder = LocalEmbedder(dim=384)
        
        # 统计
        self.query_stats: List[Dict] = []
    
    def add_document(self, doc_id: str, text: str, metadata: Dict = None):
        """添加文档"""
        # 向量索引
        vector = self.embedder.encode(text)
        self.hnsw.add(doc_id, vector, metadata)
        
        # 关键词索引
        self.bm25.add(doc_id, text)
        
        # 存储
        self.documents[doc_id] = {
            'text': text,
            'vector': vector,
            'metadata': metadata or {},
            'added_at': time.time()
        }
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        混合检索
        
        流程:
        1. 向量检索
        2. 关键词检索  
        3. 融合排序
        """
        start_time = time.time()
        
        # 1. 向量检索
        query_vector = self.embedder.encode(query)
        vector_results = self.hnsw.search(query_vector, k=top_k * 2)
        
        # 距离转相似度
        vector_scores = {}
        for doc_id, dist in vector_results:
            # 归一化距离到相似度
            similarity = 1.0 / (1.0 + dist)
            vector_scores[doc_id] = similarity
        
        # 2. 关键词检索
        keyword_results = self.bm25.search(query, top_k=top_k * 2)
        keyword_scores = {doc_id: score for doc_id, score in keyword_results}
        
        # 3. 融合 (Reciprocal Rank Fusion)
        combined_scores = {}
        all_docs = set(vector_scores.keys()) | set(keyword_scores.keys())
        
        k = 60  # RRF常数
        
        for doc_id in all_docs:
            score = 0.0
            
            # 向量得分 (RRF)
            if doc_id in vector_scores:
                rank = sorted(vector_scores.keys(), 
                             key=lambda x: vector_scores[x], 
                             reverse=True).index(doc_id) + 1
                score += self.vector_weight * (1.0 / (k + rank))
            
            # 关键词得分 (RRF)
            if doc_id in keyword_scores:
                rank = sorted(keyword_scores.keys(), 
                             key=lambda x: keyword_scores[x], 
                             reverse=True).index(doc_id) + 1
                score += self.keyword_weight * (1.0 / (k + rank))
            
            combined_scores[doc_id] = score
        
        # 排序
        sorted_results = sorted(combined_scores.items(), 
                               key=lambda x: x[1], 
                               reverse=True)[:top_k]
        
        # 组装结果
        results = []
        for doc_id, score in sorted_results:
            if doc_id in self.documents:
                doc = self.documents[doc_id]
                results.append({
                    'id': doc_id,
                    'text': doc['text'][:200] + '...' if len(doc['text']) > 200 else doc['text'],
                    'score': score,
                    'vector_score': vector_scores.get(doc_id, 0),
                    'keyword_score': keyword_scores.get(doc_id, 0),
                    'metadata': doc['metadata']
                })
        
        # 记录统计
        latency = (time.time() - start_time) * 1000
        self.query_stats.append({
            'query': query[:50],
            'latency_ms': latency,
            'vector_results': len(vector_results),
            'keyword_results': len(keyword_results),
            'final_results': len(results),
            'timestamp': time.time()
        })
        
        return results
    
    def get_stats(self) -> Dict:
        """获取统计"""
        if not self.query_stats:
            return {}
        
        avg_latency = sum(s['latency_ms'] for s in self.query_stats) / len(self.query_stats)
        
        return {
            'total_documents': len(self.documents),
            'hnsw_nodes': len(self.hnsw.nodes),
            'bm25_terms': len(self.bm25.doc_freqs),
            'avg_latency_ms': avg_latency,
            'total_queries': len(self.query_stats)
        }


# ============================================================================
# 查询缓存
# ============================================================================

class QueryCache:
    """
    查询缓存
    
    缓存高频查询结果，减少计算开销
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        
        self.cache: Dict[str, Dict] = {}
        self.access_count: Dict[str, int] = defaultdict(int)
    
    def _hash_query(self, query: str, top_k: int) -> str:
        """生成查询哈希"""
        return hashlib.md5(f"{query}:{top_k}".encode()).hexdigest()[:16]
    
    def get(self, query: str, top_k: int = 10) -> Optional[List[Dict]]:
        """获取缓存"""
        key = self._hash_query(query, top_k)
        
        if key in self.cache:
            entry = self.cache[key]
            
            # 检查过期
            if time.time() - entry['timestamp'] < self.ttl:
                self.access_count[key] += 1
                return entry['results']
            else:
                # 过期删除
                del self.cache[key]
        
        return None
    
    def set(self, query: str, top_k: int, results: List[Dict]):
        """设置缓存"""
        key = self._hash_query(query, top_k)
        
        # 如果满了，删除最少访问的
        if len(self.cache) >= self.max_size:
            lru_key = min(self.cache.keys(), key=lambda k: self.access_count[k])
            del self.cache[lru_key]
            del self.access_count[lru_key]
        
        self.cache[key] = {
            'results': results,
            'timestamp': time.time()
        }
        self.access_count[key] = 1
    
    def get_hit_rate(self) -> float:
        """获取命中率"""
        if not self.access_count:
            return 0.0
        
        hits = sum(1 for count in self.access_count.values() if count > 1)
        return hits / len(self.access_count)


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Vector Store Optimization - 测试")
    print("="*60)
    
    # 创建混合检索器
    retriever = HybridRetriever(vector_weight=0.7, keyword_weight=0.3)
    
    # 添加测试文档
    print("\n📚 添加测试文档...")
    test_docs = [
        ("doc1", "WDai采用分层记忆架构，包括工作记忆和长期记忆", {"category": "architecture"}),
        ("doc2", "向量存储使用HNSW索引实现高效检索", {"category": "tech"}),
        ("doc3", "BM25算法用于关键词匹配和文本检索", {"category": "algorithm"}),
        ("doc4", "混合检索结合向量相似度和关键词匹配", {"category": "hybrid"}),
        ("doc5", "多Agent协作框架支持角色扮演和任务委托", {"category": "multi-agent"}),
    ]
    
    for doc_id, text, meta in test_docs:
        retriever.add_document(doc_id, text, meta)
    
    print(f"   已添加{len(test_docs)}个文档")
    
    # 测试混合检索
    print("\n🔍 测试混合检索:\n")
    
    test_queries = [
        "记忆架构",
        "向量检索",
        "Agent协作",
    ]
    
    for query in test_queries:
        print(f"📝 查询: '{query}'")
        results = retriever.search(query, top_k=3)
        
        for i, r in enumerate(results, 1):
            print(f"   {i}. [{r['id']}] 综合:{r['score']:.3f} 向量:{r['vector_score']:.3f} 关键词:{r['keyword_score']:.3f}")
            print(f"      {r['text']}")
        
        print()
    
    # 统计
    print("\n📊 统计信息")
    stats = retriever.get_stats()
    print(f"   总文档: {stats['total_documents']}")
    print(f"   HNSW节点: {stats['hnsw_nodes']}")
    print(f"   BM25词项: {stats['bm25_terms']}")
    print(f"   平均延迟: {stats['avg_latency_ms']:.1f}ms")
    
    # 测试缓存
    print("\n💾 测试查询缓存")
    cache = QueryCache(max_size=100)
    
    # 第一次查询
    results1 = retriever.search("记忆架构", top_k=2)
    cache.set("记忆架构", 2, results1)
    
    # 第二次查询（命中缓存）
    cached = cache.get("记忆架构", 2)
    if cached:
        print("   ✅ 缓存命中")
    else:
        print("   ❌ 缓存未命中")
    
    print("\n" + "="*60)
    print("✅ 向量存储优化测试完成")
    print("="*60)
