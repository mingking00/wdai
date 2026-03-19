#!/usr/bin/env python3
"""
WDai Memory Migration Tool
将现有记忆文件迁移到向量存储

用法:
    python3 migrate_memory.py
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from vector_memory import VectorMemoryStore, MemoryEntry, MemorySearchEnhanced
from pathlib import Path
from datetime import datetime
import re

def migrate_all_memories():
    """迁移所有现有记忆到向量存储"""
    print("="*60)
    print("WDai Memory Migration Tool")
    print("="*60)
    
    # 初始化增强搜索（会自动加载现有记忆）
    print("\n🔄 初始化向量存储并加载现有记忆...")
    search = MemorySearchEnhanced()
    
    # 获取统计
    stats = search.vector_store.get_stats()
    print(f"\n✅ 迁移完成!")
    print(f"   向量数量: {stats.get('vectors_count', 'N/A')}")
    print(f"   状态: {stats.get('status', 'unknown')}")
    
    # 测试搜索
    print("\n--- 功能测试 ---")
    test_queries = [
        "GitHub部署",
        "Feishu发送消息",
        "PPT生成",
        "信息源监控",
        "方法指纹",
    ]
    
    for query in test_queries:
        results = search.search(query, top_k=3)
        print(f"\n🔍 '{query}':")
        if results:
            for r in results[:2]:
                snippet = r['content'][:80].replace('\n', ' ')
                print(f"   [{r['score']:.2f}] {snippet}...")
        else:
            print("   (无结果)")
    
    print("\n" + "="*60)
    print("✅ 向量存储已就绪，可以替换原有记忆搜索")
    print("="*60)
    
    return search

if __name__ == "__main__":
    search = migrate_all_memories()
