#!/usr/bin/env python3
"""
memory_search.py - 混合语义检索脚本

基于 02-retrieval-pipeline.md 实现
支持：向量检索 + BM25 + 时间过滤 + RRF融合
"""

import json
import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

# 添加技能目录到路径
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR))

@dataclass
class Memory:
    """记忆数据模型"""
    id: str
    content: str
    category: str
    importance: float
    confidence: float
    user_id: str
    created_at: str
    access_count: int = 0
    embedding: Optional[List[float]] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Memory":
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            category=data.get("category", "fact"),
            importance=data.get("importance", 0.5),
            confidence=data.get("confidence", 0.8),
            user_id=data.get("user_id", "default"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            access_count=data.get("access_count", 0),
            embedding=data.get("embedding")
        )

class SimpleEmbedding:
    """简化版嵌入生成（实际应使用OpenAI等）"""
    
    def __init__(self, method: str = "simple"):
        self.method = method
        
    def encode(self, text: str) -> List[float]:
        """生成文本嵌入"""
        # 简化实现：词袋+哈希
        # 实际应调用 OpenAI/text-embedding-3-small 等
        words = text.lower().split()
        vector = [0.0] * 128
        
        for i, word in enumerate(words):
            idx = hash(word) % 128
            vector[idx] += 1.0
            
        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = [v / norm for v in vector]
            
        return vector
    
    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(v1, v2))
        return dot

class HybridRetriever:
    """混合检索器"""
    
    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.embedder = SimpleEmbedding()
        self.memories: List[Memory] = []
        self.rrf_k = 60  # RRF常数
        
    def load_memories(self, user_id: Optional[str] = None) -> "HybridRetriever":
        """加载记忆文件"""
        self.memories = []
        
        # 支持多种存储格式
        patterns = ["*.json", "*.jsonl", "*.md"]
        
        for pattern in patterns:
            for file_path in self.memory_dir.glob(pattern):
                try:
                    if file_path.suffix == ".json":
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for item in data:
                                    mem = Memory.from_dict(item)
                                    if user_id is None or mem.user_id == user_id:
                                        self.memories.append(mem)
                    elif file_path.suffix == ".jsonl":
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                item = json.loads(line.strip())
                                mem = Memory.from_dict(item)
                                if user_id is None or mem.user_id == user_id:
                                    self.memories.append(mem)
                except Exception as e:
                    print(f"Warning: Failed to load {file_path}: {e}", file=sys.stderr)
                    
        print(f"Loaded {len(self.memories)} memories")
        return self
    
    def vector_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """向量语义检索"""
        if not self.memories:
            return []
            
        query_vec = self.embedder.encode(query)
        
        results = []
        for mem in self.memories:
            if mem.embedding:
                mem_vec = mem.embedding
            else:
                # 动态计算
                mem_vec = self.embedder.encode(mem.content)
                
            score = self.embedder.cosine_similarity(query_vec, mem_vec)
            results.append({
                "memory": mem,
                "score": score,
                "source": "vector"
            })
        
        # 排序并返回Top K
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def bm25_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """BM25关键词检索（简化版）"""
        if not self.memories:
            return []
            
        query_words = set(query.lower().split())
        results = []
        
        for mem in self.memories:
            content_words = set(mem.content.lower().split())
            
            # 计算匹配度
            matches = len(query_words & content_words)
            total_query = len(query_words)
            
            if total_query > 0:
                score = matches / total_query
            else:
                score = 0.0
                
            results.append({
                "memory": mem,
                "score": score,
                "source": "bm25"
            })
        
        # 排序并返回Top K
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def temporal_filter(self, days: int = 30) -> List[Memory]:
        """时间范围过滤"""
        cutoff = datetime.now() - timedelta(days=days)
        
        filtered = []
        for mem in self.memories:
            try:
                mem_date = datetime.fromisoformat(mem.created_at)
                if mem_date >= cutoff:
                    filtered.append(mem)
            except:
                continue
                
        return filtered
    
    def rrf_fuse(self, vector_results: List[Dict], bm25_results: List[Dict]) -> List[Dict]:
        """
        RRF (Reciprocal Rank Fusion) 融合算法
        
        score = Σ(1 / (k + rank_i))
        """
        # 按ID聚合分数
        rrf_scores = {}
        memory_map = {}
        
        # 处理向量结果
        for rank, item in enumerate(vector_results, 1):
            mem_id = item["memory"].id
            rrf_scores[mem_id] = rrf_scores.get(mem_id, 0) + 1.0 / (self.rrf_k + rank)
            memory_map[mem_id] = item["memory"]
        
        # 处理BM25结果
        for rank, item in enumerate(bm25_results, 1):
            mem_id = item["memory"].id
            rrf_scores[mem_id] = rrf_scores.get(mem_id, 0) + 1.0 / (self.rrf_k + rank)
            memory_map[mem_id] = item["memory"]
        
        # 排序
        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [{
            "memory": memory_map[mem_id],
            "score": score,
            "source": "hybrid_rrf"
        } for mem_id, score in sorted_ids]
    
    def apply_decay(self, results: List[Dict], half_life_days: float = 30.0) -> List[Dict]:
        """应用时间衰减"""
        now = datetime.now()
        
        for item in results:
            mem = item["memory"]
            try:
                mem_date = datetime.fromisoformat(mem.created_at)
                age_days = (now - mem_date).days
                
                # 指数衰减
                decay = np.exp(-0.693 * age_days / half_life_days)
                
                # 访问频率提升
                access_boost = min(mem.access_count * 0.05, 0.2)
                
                item["score"] = item["score"] * decay + access_boost
                item["decay_applied"] = True
            except:
                pass
                
        # 重新排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    def search(self, 
               query: str, 
               top_k: int = 10,
               user_id: Optional[str] = None,
               days: Optional[int] = None,
               half_life: float = 30.0,
               hybrid: bool = True) -> List[Dict]:
        """
        执行完整检索流程
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            user_id: 用户过滤
            days: 时间范围过滤
            half_life: 衰减半衰期（天）
            hybrid: 是否使用混合检索
        """
        # 加载记忆
        self.load_memories(user_id)
        
        # 时间预过滤
        if days:
            self.memories = self.temporal_filter(days)
            print(f"After temporal filter ({days} days): {len(self.memories)} memories")
        
        if not self.memories:
            return []
        
        # 多路召回
        print(f"Retrieving with query: '{query}'")
        
        if hybrid:
            # 向量检索
            vector_results = self.vector_search(query, top_k=20)
            print(f"  Vector: {len(vector_results)} results")
            
            # BM25检索
            bm25_results = self.bm25_search(query, top_k=20)
            print(f"  BM25: {len(bm25_results)} results")
            
            # RRF融合
            fused = self.rrf_fuse(vector_results, bm25_results)
            print(f"  Fused: {len(fused)} results")
        else:
            # 仅向量
            fused = self.vector_search(query, top_k=top_k)
        
        # 时间衰减
        results = self.apply_decay(fused, half_life)
        
        # 返回Top K
        return results[:top_k]

def format_output(results: List[Dict], verbose: bool = False) -> str:
    """格式化输出"""
    if not results:
        return "No relevant memories found."
    
    lines = [f"Found {len(results)} relevant memories:\n"]
    
    for i, item in enumerate(results, 1):
        mem = item["memory"]
        score = item["score"]
        source = item.get("source", "unknown")
        
        lines.append(f"\n{i}. [{mem.category.upper()}] (score: {score:.3f}, source: {source})")
        lines.append(f"   Content: {mem.content}")
        
        if verbose:
            lines.append(f"   ID: {mem.id}")
            lines.append(f"   Created: {mem.created_at}")
            lines.append(f"   Importance: {mem.importance}, Confidence: {mem.confidence}")
            lines.append(f"   Access Count: {mem.access_count}")
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(
        description="Search memories using hybrid retrieval (vector + BM25 + temporal)"
    )
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="Search query"
    )
    parser.add_argument(
        "--memory-dir", "-d",
        type=Path,
        default=Path(".memory"),
        help="Directory containing memory files (default: .memory)"
    )
    parser.add_argument(
        "--user-id", "-u",
        help="Filter by user ID"
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=10,
        help="Number of results to return (default: 10)"
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Only search memories from last N days"
    )
    parser.add_argument(
        "--half-life",
        type=float,
        default=30.0,
        help="Decay half-life in days (default: 30)"
    )
    parser.add_argument(
        "--no-hybrid",
        action="store_true",
        help="Disable hybrid retrieval (vector only)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # 检查记忆目录
    if not args.memory_dir.exists():
        print(f"Error: Memory directory not found: {args.memory_dir}", file=sys.stderr)
        sys.exit(1)
    
    # 执行检索
    retriever = HybridRetriever(args.memory_dir)
    results = retriever.search(
        query=args.query,
        top_k=args.top_k,
        user_id=args.user_id,
        days=args.days,
        half_life=args.half_life,
        hybrid=not args.no_hybrid
    )
    
    # 输出结果
    if args.json:
        output = [{
            "id": r["memory"].id,
            "content": r["memory"].content,
            "category": r["memory"].category,
            "score": r["score"],
            "source": r.get("source", "unknown"),
            "created_at": r["memory"].created_at
        } for r in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(format_output(results, args.verbose))

if __name__ == "__main__":
    main()
