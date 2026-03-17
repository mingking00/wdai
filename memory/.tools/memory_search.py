#!/usr/bin/env python3
"""
自适应记忆检索
- 动态权重：相关性 × 重要性 × 时效性
- 个性化排序
"""

import chromadb
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
DB_PATH = MEMORY_DIR / ".vectordb"

def calculate_time_decay(created_date, decay_days=30):
    """计算时间衰减分数"""
    if not created_date:
        return 0.5
    
    try:
        date = datetime.strptime(created_date, "%Y-%m-%d")
        days_old = (datetime.now() - date).days
        
        # 指数衰减
        decay = np.exp(-days_old / decay_days)
        return max(0.1, min(1.0, decay))
    except:
        return 0.5

def calculate_importance_score(metadata):
    """计算重要性分数"""
    importance_map = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.3
    }
    
    base_score = importance_map.get(metadata.get("importance", "medium"), 0.5)
    
    # 类型加成
    type_bonus = {
        "principle": 0.2,
        "skill": 0.15,
        "error": 0.1,
        "learning": 0.05
    }
    
    bonus = type_bonus.get(metadata.get("type"), 0)
    return min(1.0, base_score + bonus)

def search_with_weights(query, n_results=5, weights=None):
    """
    带权重的记忆检索
    
    weights: dict with keys 'relevance', 'importance', 'recency'
    """
    if weights is None:
        weights = {
            "relevance": 0.5,
            "importance": 0.3,
            "recency": 0.2
        }
    
    # 连接数据库
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection("memories")
    
    # 基础语义检索（获取更多候选）
    results = collection.query(
        query_texts=[query],
        n_results=n_results * 3,  # 获取更多用于重排
        include=["documents", "metadatas", "distances"]
    )
    
    if not results or not results['documents'][0]:
        return []
    
    # 计算综合分数
    scored_results = []
    
    for doc, meta, dist in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ):
        # 相关性分数（基于向量距离）
        relevance = 1 - dist  # 转换为相似度
        
        # 重要性分数
        importance = calculate_importance_score(meta)
        
        # 时效性分数
        recency = calculate_time_decay(meta.get("created"))
        
        # 综合分数
        final_score = (
            weights["relevance"] * relevance +
            weights["importance"] * importance +
            weights["recency"] * recency
        )
        
        scored_results.append({
            "document": doc[:200] + "..." if len(doc) > 200 else doc,
            "metadata": meta,
            "scores": {
                "relevance": relevance,
                "importance": importance,
                "recency": recency,
                "final": final_score
            }
        })
    
    # 按综合分数排序
    scored_results.sort(key=lambda x: x["scores"]["final"], reverse=True)
    
    return scored_results[:n_results]

def main():
    """测试自适应检索"""
    print("=" * 60)
    print("🧠 自适应记忆检索")
    print("=" * 60)
    
    test_queries = [
        "如何使用技能",
        "Claude Code 工作流",
        "错误处理方法"
    ]
    
    for query in test_queries:
        print(f"\n🔍 查询: '{query}'")
        print("-" * 60)
        
        results = search_with_weights(query, n_results=3)
        
        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            scores = result["scores"]
            
            print(f"\n  {i}. [{meta.get('type', 'unknown')}] {meta.get('title', '无标题')}")
            print(f"     📍 {meta.get('path', '未知路径')}")
            print(f"     📊 分数: 综合={scores['final']:.2%} | "
                  f"相关性={scores['relevance']:.2%} | "
                  f"重要性={scores['importance']:.2%} | "
                  f"时效性={scores['recency']:.2%}")
            print(f"     📝 {result['document'][:80]}...")

if __name__ == "__main__":
    main()
