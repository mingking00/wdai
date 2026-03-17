#!/usr/bin/env python3
"""
记忆压缩系统
- 检测相似记忆
- 自动合并
- 提取摘要
"""

import chromadb
import numpy as np
import re
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
DB_PATH = MEMORY_DIR / ".vectordb"

def calculate_text_similarity(text1, text2):
    """计算文本相似度"""
    return SequenceMatcher(None, text1, text2).ratio()

def find_similar_memories(threshold=0.85):
    """查找相似记忆"""
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection("memories")
    
    # 获取所有记忆
    all_memories = collection.get()
    
    similar_groups = []
    processed = set()
    
    for i, (doc1, meta1, id1) in enumerate(zip(
        all_memories['documents'],
        all_memories['metadatas'],
        all_memories['ids']
    )):
        if id1 in processed:
            continue
        
        group = [{
            "id": id1,
            "document": doc1,
            "metadata": meta1
        }]
        
        for j, (doc2, meta2, id2) in enumerate(zip(
            all_memories['documents'],
            all_memories['metadatas'],
            all_memories['ids']
        )):
            if i != j and id2 not in processed:
                similarity = calculate_text_similarity(doc1, doc2)
                if similarity >= threshold:
                    group.append({
                        "id": id2,
                        "document": doc2,
                        "metadata": meta2,
                        "similarity": similarity
                    })
                    processed.add(id2)
        
        if len(group) > 1:
            processed.add(id1)
            similar_groups.append(group)
    
    return similar_groups

def extract_summary(documents):
    """从多个文档中提取摘要"""
    # 简单实现：取最长文档的前200字
    longest = max(documents, key=len)
    
    # 提取关键句子（包含关键词的句子）
    sentences = re.split(r'[。！？\n]', longest)
    key_sentences = []
    
    keywords = ["核心", "关键", "重要", "原则", "方法", "总结"]
    for sent in sentences:
        if any(kw in sent for kw in keywords) and len(sent) > 10:
            key_sentences.append(sent.strip())
    
    if key_sentences:
        summary = "；".join(key_sentences[:3])
    else:
        summary = longest[:200] + "..." if len(longest) > 200 else longest
    
    return summary

def merge_memories(group):
    """合并相似记忆"""
    # 提取所有文档
    documents = [m["document"] for m in group]
    
    # 生成摘要
    summary = extract_summary(documents)
    
    # 合并元数据
    merged_meta = {
        "title": f"[合并] {group[0]['metadata'].get('title', '无标题')}",
        "path": group[0]['metadata'].get('path', 'unknown'),
        "type": group[0]['metadata'].get('type', 'unknown'),
        "importance": max([m['metadata'].get('importance', 'medium') for m in group]),
        "created": group[0]['metadata'].get('created', ''),
        "tags": ",".join(set(
            tag for m in group 
            for tag in m['metadata'].get('tags', '').split(',') if tag
        )),
        "merged_from": ",".join([m['id'] for m in group]),
        "merge_count": len(group)
    }
    
    return summary, merged_meta

def compress_memories(dry_run=True):
    """压缩记忆"""
    print("🔍 查找相似记忆...")
    similar_groups = find_similar_memories(threshold=0.80)
    
    if not similar_groups:
        print("  未发现相似记忆")
        return 0
    
    print(f"  发现 {len(similar_groups)} 组相似记忆")
    
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection("memories")
    
    compressed = 0
    
    for i, group in enumerate(similar_groups, 1):
        print(f"\n📦 组 {i}/{len(similar_groups)}:")
        for m in group:
            print(f"  - {m['metadata'].get('path', 'unknown')}")
        
        # 合并
        summary, merged_meta = merge_memories(group)
        
        print(f"  📝 摘要: {summary[:100]}...")
        
        if not dry_run:
            # 删除旧记忆
            collection.delete(ids=[m['id'] for m in group])
            
            # 添加合并后的记忆
            new_id = f"merged_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
            collection.add(
                ids=[new_id],
                documents=[summary],
                metadatas=[merged_meta]
            )
            
            print(f"  ✅ 已合并为新记忆: {new_id}")
        else:
            print(f"  🔍 [预览模式] 未实际合并")
        
        compressed += len(group)
    
    return compressed

def extract_key_insights():
    """提取关键洞察"""
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection("memories")
    
    # 按类型分组
    all_memories = collection.get()
    
    insights = {
        "principles": [],
        "skills": [],
        "errors": [],
        "learnings": []
    }
    
    for doc, meta in zip(all_memories['documents'], all_memories['metadatas']):
        mem_type = meta.get('type', 'unknown')
        
        # 提取关键句子
        sentences = re.split(r'[。！？\.\n]', doc)
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 20 and len(sent) < 200:
                # 检查是否是重要句子
                if any(kw in sent for kw in ["关键", "核心", "重要", "必须", "始终"]):
                    if mem_type in insights:
                        insights[mem_type].append(sent)
    
    # 生成洞察报告
    report = "# 记忆洞察报告\n\n"
    report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    for category, items in insights.items():
        if items:
            report += f"## {category.upper()}\n\n"
            for item in items[:5]:  # 只取前5个
                report += f"- {item}\n"
            report += "\n"
    
    # 保存报告
    report_path = MEMORY_DIR / ".reports" / f"insights_{datetime.now().strftime('%Y%m%d')}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📊 洞察报告已保存: {report_path}")
    return insights

def main():
    """主函数"""
    print("=" * 60)
    print("🗜️ 记忆压缩系统")
    print("=" * 60)
    
    # 1. 查找并压缩相似记忆
    print("\n📦 相似记忆检测与压缩")
    print("-" * 60)
    compressed = compress_memories(dry_run=False)
    print(f"\n✅ 处理了 {compressed} 个相似记忆")
    
    # 2. 提取关键洞察
    print("\n💡 提取关键洞察")
    print("-" * 60)
    extract_key_insights()
    
    print("\n" + "=" * 60)
    print("✅ 记忆压缩完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
