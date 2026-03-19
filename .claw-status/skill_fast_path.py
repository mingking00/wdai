#!/usr/bin/env python3
"""
WDai Skill Fast Path
技能快速路径 - 高频查询绕过LLM

核心功能:
1. 缓存高频查询的响应
2. 相似度匹配返回缓存结果
3. 模式学习自动优化缓存
4. 命中率统计和缓存管理
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import json
import hashlib
import time
from vector_memory import VectorMemoryStore, MemoryEntry


@dataclass
class CachedResponse:
    """缓存的响应"""
    query_hash: str
    query_pattern: str  # 原始查询模式
    response: str
    metadata: Dict
    created_at: float
    last_used: float
    use_count: int
    avg_confidence: float


class SkillFastPath:
    """
    技能快速路径
    
    工作原理:
    1. 查询到达
    2. 计算与缓存模式的相似度
    3. 如果相似度 > threshold: 返回缓存响应
    4. 否则: 走正常LLM流程
    5. LLM响应后: 评估是否值得缓存
    """
    
    def __init__(
        self,
        storage_dir: str = ".claw-status/fast_path",
        similarity_threshold: float = 0.92,
        min_use_count: int = 2,
        max_cache_size: int = 1000
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.storage_dir / "response_cache.json"
        self.stats_file = self.storage_dir / "stats.json"
        
        self.similarity_threshold = similarity_threshold
        self.min_use_count = min_use_count
        self.max_cache_size = max_cache_size
        
        # 内存缓存
        self.cache: Dict[str, CachedResponse] = {}
        
        # 向量存储用于语义匹配
        self.vector_store: Optional[VectorMemoryStore] = None
        try:
            self.vector_store = VectorMemoryStore(
                storage_dir=str(self.storage_dir / "vector_cache")
            )
        except Exception as e:
            print(f"⚠️ 向量存储初始化失败: {e}")
        
        # 统计
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0.0,
            "last_reset": datetime.now().isoformat()
        }
        
        # 加载缓存
        self._load_cache()
        
        print(f"✅ SkillFastPath 初始化完成")
        print(f"   缓存大小: {len(self.cache)}")
        print(f"   相似度阈值: {similarity_threshold}")
    
    def _normalize_query(self, query: str) -> str:
        """标准化查询"""
        # 移除多余空格
        query = " ".join(query.split())
        # 转小写
        query = query.lower()
        # 移除常见变体词
        filler_words = ['请', '帮我', '可以', '一下', '吗', '呢']
        for word in filler_words:
            query = query.replace(word, '')
        return query.strip()
    
    def _hash_query(self, query: str) -> str:
        """生成查询哈希"""
        normalized = self._normalize_query(query)
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """
        计算两个查询的相似度
        
        使用多种方法:
        1. 精确匹配 (最高权重)
        2. 编辑距离
        3. 向量相似度 (如果可用)
        """
        # 1. 标准化
        q1 = self._normalize_query(query1)
        q2 = self._normalize_query(query2)
        
        # 2. 精确匹配
        if q1 == q2:
            return 1.0
        
        # 3. 编辑距离 (简化版)
        edit_sim = self._levenshtein_similarity(q1, q2)
        
        # 4. 向量相似度
        vector_sim = 0.0
        if self.vector_store:
            try:
                # 使用vector_store的简单embed
                v1 = self.vector_store._simple_embed(q1)
                v2 = self.vector_store._simple_embed(q2)
                
                import math
                dot = sum(a*b for a, b in zip(v1, v2))
                norm1 = math.sqrt(sum(a*a for a in v1))
                norm2 = math.sqrt(sum(b*b for b in v2))
                
                if norm1 > 0 and norm2 > 0:
                    vector_sim = dot / (norm1 * norm2)
            except:
                pass
        
        # 融合得分 (编辑距离为主，向量为辅)
        final_sim = 0.6 * edit_sim + 0.4 * vector_sim
        
        return final_sim
    
    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """计算编辑距离相似度"""
        if len(s1) < len(s2):
            return self._levenshtein_similarity(s2, s1)
        
        if len(s2) == 0:
            return 0.0
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        
        return 1.0 - (distance / max_len)
    
    def lookup(self, query: str) -> Optional[Tuple[str, float, Dict]]:
        """
        查找缓存响应
        
        Returns:
            (response, confidence, metadata) 如果命中
            None 如果未命中
        """
        self.stats["total_queries"] += 1
        
        query_hash = self._hash_query(query)
        
        # 1. 精确匹配
        if query_hash in self.cache:
            cached = self.cache[query_hash]
            cached.last_used = time.time()
            cached.use_count += 1
            
            self.stats["cache_hits"] += 1
            self._update_stats()
            
            return (cached.response, 1.0, cached.metadata)
        
        # 2. 相似度匹配
        if len(query) > 10:  # 只对较长的查询进行相似度匹配
            best_match = None
            best_sim = 0.0
            
            for cached in self.cache.values():
                sim = self._calculate_similarity(query, cached.query_pattern)
                if sim > best_sim and sim >= self.similarity_threshold:
                    best_sim = sim
                    best_match = cached
            
            if best_match:
                best_match.last_used = time.time()
                best_match.use_count += 1
                
                self.stats["cache_hits"] += 1
                self._update_stats()
                
                return (best_match.response, best_sim, best_match.metadata)
        
        # 未命中
        self.stats["cache_misses"] += 1
        self._update_stats()
        
        return None
    
    def cache_response(
        self,
        query: str,
        response: str,
        metadata: Dict = None,
        confidence: float = 0.8
    ):
        """
        缓存响应
        
        只有高置信度、通用的响应才值得缓存
        """
        # 过滤条件
        if len(query) < 5:  # 太短的查询
            return
        
        if len(response) > 2000:  # 太长的响应
            return
        
        if confidence < 0.7:  # 低置信度
            return
        
        # 检查是否已存在
        query_hash = self._hash_query(query)
        if query_hash in self.cache:
            # 更新现有缓存
            self.cache[query_hash].response = response
            self.cache[query_hash].last_used = time.time()
            return
        
        # 检查缓存大小
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()
        
        # 创建新缓存
        cached = CachedResponse(
            query_hash=query_hash,
            query_pattern=query,
            response=response,
            metadata=metadata or {},
            created_at=time.time(),
            last_used=time.time(),
            use_count=1,
            avg_confidence=confidence
        )
        
        self.cache[query_hash] = cached
        
        # 添加到向量存储
        if self.vector_store:
            entry = MemoryEntry(
                id=f"cache_{query_hash}",
                content=f"Q: {query}\nA: {response[:200]}",
                metadata={
                    "type": "cached_response",
                    "query_hash": query_hash,
                    "use_count": 1
                },
                timestamp=time.time(),
                source="semantic"
            )
            try:
                self.vector_store.add_memory(entry)
            except:
                pass
        
        # 保存到磁盘
        self._save_cache()
    
    def _evict_oldest(self):
        """淘汰最老的缓存"""
        if not self.cache:
            return
        
        # 找到最少使用且最老的
        oldest = min(
            self.cache.values(),
            key=lambda x: (x.use_count, x.last_used)
        )
        
        del self.cache[oldest.query_hash]
        print(f"🗑️ 淘汰缓存: {oldest.query_pattern[:50]}...")
    
    def _load_cache(self):
        """从磁盘加载缓存"""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                cached = CachedResponse(**item)
                self.cache[cached.query_hash] = cached
            
            # 加载统计
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats.update(json.load(f))
            
            print(f"✅ 已加载 {len(self.cache)} 条缓存")
        except Exception as e:
            print(f"⚠️ 加载缓存失败: {e}")
    
    def _save_cache(self):
        """保存缓存到磁盘"""
        try:
            data = [
                {
                    "query_hash": c.query_hash,
                    "query_pattern": c.query_pattern,
                    "response": c.response,
                    "metadata": c.metadata,
                    "created_at": c.created_at,
                    "last_used": c.last_used,
                    "use_count": c.use_count,
                    "avg_confidence": c.avg_confidence
                }
                for c in self.cache.values()
            ]
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 保存统计
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"⚠️ 保存缓存失败: {e}")
    
    def _update_stats(self):
        """更新统计信息"""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total > 0:
            self.stats["hit_rate"] = self.stats["cache_hits"] / total
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "avg_use_count": sum(c.use_count for c in self.cache.values()) / len(self.cache) if self.cache else 0
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0.0,
            "last_reset": datetime.now().isoformat()
        }
        
        if self.cache_file.exists():
            self.cache_file.unlink()
        
        print("✅ 缓存已清空")


# ============ 与LLM流程集成 ============

class FastPathLLMWrapper:
    """
    带快速路径的LLM包装器
    
    使用方式:
        wrapper = FastPathLLMWrapper()
        
        # 查询时自动走快速路径或LLM
        response = wrapper.query("用户问题")
    """
    
    def __init__(self, llm_func=None):
        self.fast_path = SkillFastPath()
        self.llm_func = llm_func or self._default_llm
    
    def _default_llm(self, query: str) -> str:
        """默认LLM函数 (占位)"""
        return f"[LLM响应] {query}"
    
    def query(self, query: str, use_cache: bool = True) -> str:
        """
        查询 (带快速路径)
        
        流程:
        1. 检查缓存
        2. 命中: 返回缓存
        3. 未命中: 调用LLM
        4. 评估是否缓存LLM响应
        """
        # 1. 检查快速路径
        if use_cache:
            cached = self.fast_path.lookup(query)
            if cached:
                response, confidence, metadata = cached
                print(f"⚡ 快速路径命中 (置信度: {confidence:.2f})")
                return response
        
        # 2. 调用LLM
        print(f"🤖 LLM处理中...")
        response = self.llm_func(query)
        
        # 3. 评估是否缓存
        # 简化: 如果响应不太长，就缓存
        confidence = 0.8 if len(response) < 1000 else 0.6
        self.fast_path.cache_response(query, response, confidence=confidence)
        
        return response
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return self.fast_path.get_stats()


# ============ 测试 ============

if __name__ == "__main__":
    print("="*60)
    print("Skill Fast Path - 测试")
    print("="*60)
    
    fast_path = SkillFastPath()
    
    # 测试1: 缓存响应
    print("\n1. 缓存测试响应")
    test_queries = [
        ("你好", "你好！有什么我可以帮你的？"),
        ("你是谁", "我是wdai，工作空间自适应智能进化系统。"),
        ("你会什么", "我可以帮你写代码、做研究、管理项目等。"),
    ]
    
    for query, response in test_queries:
        fast_path.cache_response(query, response, confidence=0.9)
        print(f"   已缓存: '{query}'")
    
    # 测试2: 精确匹配
    print("\n2. 精确匹配测试")
    result = fast_path.lookup("你好")
    if result:
        print(f"   ✅ 命中: '{result[0]}'")
    else:
        print("   ❌ 未命中")
    
    # 测试3: 相似度匹配
    print("\n3. 相似度匹配测试")
    similar_queries = [
        "你好啊",
        "你是谁？",
        "你会做什么",
    ]
    
    for query in similar_queries:
        result = fast_path.lookup(query)
        if result:
            print(f"   ✅ '{query}' -> 命中 (相似度: {result[1]:.2f})")
        else:
            print(f"   ❌ '{query}' -> 未命中")
    
    # 测试4: 统计
    print("\n4. 统计信息")
    stats = fast_path.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2%}" if 'rate' in key else f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    # 测试5: 包装器
    print("\n5. LLM包装器测试")
    wrapper = FastPathLLMWrapper()
    
    # 第一次查询 (未命中)
    print("\n第一次查询 '你好':")
    r1 = wrapper.query("你好")
    print(f"   响应: {r1}")
    
    # 第二次查询 (命中)
    print("\n第二次查询 '你好啊' (相似):")
    r2 = wrapper.query("你好啊")
    print(f"   响应: {r2}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)
