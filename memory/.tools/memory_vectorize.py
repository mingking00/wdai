#!/usr/bin/env python3
"""
记忆向量数据库
- 将 Markdown 记忆文件向量化
- 支持语义检索
- 使用 ChromaDB
"""

import chromadb
import re
import hashlib
from datetime import datetime
from pathlib import Path

# 配置
MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
DB_PATH = MEMORY_DIR / ".vectordb"

def extract_content(filepath):
    """提取文件内容（去除元数据）"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 去除元数据块
        content = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
        
        # 提取标题和正文
        lines = content.strip().split('\n')
        title = lines[0] if lines else ""
        body = '\n'.join(lines[1:])
        
        return title, body.strip()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return "", ""

def extract_metadata(filepath):
    """提取文件元数据"""
    meta = {
        'type': 'unknown',
        'importance': 'medium',
        'created': '',
        'tags': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(2000)
        
        # 解析元数据
        import re
        for key in ['type', 'importance', 'created']:
            match = re.search(rf'{key}:\s*(.+)', content)
            if match:
                meta[key] = match.group(1).strip()
        
        # 解析 tags
        match = re.search(r'tags:\s*\[(.+?)\]', content)
        if match:
            meta['tags'] = [t.strip().strip('"').strip("'") for t in match.group(1).split(',')]
    except Exception as e:
        pass
    
    return meta

def get_file_id(filepath):
    """生成文件唯一ID"""
    relative_path = str(filepath.relative_to(MEMORY_DIR))
    return hashlib.md5(relative_path.encode()).hexdigest()

def index_memories():
    """索引所有记忆文件"""
    # 初始化 ChromaDB
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_or_create_collection("memories")
    
    # 遍历所有 Markdown 文件
    files = list(MEMORY_DIR.rglob("*.md"))
    # 只排除隐藏目录下的文件
    files = [f for f in files if not any(part.startswith('.') for part in f.relative_to(MEMORY_DIR).parts[:-1])]
    
    print(f"\n📁 发现 {len(files)} 个记忆文件")
    
    indexed = 0
    for filepath in files:
        doc_id = get_file_id(filepath)
        title, content = extract_content(filepath)
        
        if not content:
            continue
        
        meta = extract_metadata(filepath)
        relative_path = str(filepath.relative_to(MEMORY_DIR))
        
        # 组合标题和内容用于向量化
        full_text = f"{title}\n\n{content[:2000]}"  # 限制长度
        
        # 添加到向量数据库
        collection.add(
            ids=[doc_id],
            documents=[full_text],
            metadatas=[{
                "title": title,
                "path": relative_path,
                "type": meta['type'],
                "importance": meta['importance'],
                "created": meta['created'],
                "tags": ','.join(meta['tags'])
            }]
        )
        
        indexed += 1
        print(f"  [{indexed}/{len(files)}] {relative_path}")
    
    print(f"\n✅ 索引完成: {indexed} 个文件")
    return collection

def search_memories(query, n_results=5):
    """语义检索"""
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection("memories")
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    return results

def main():
    """主函数"""
    print("=" * 50)
    print("🧠 记忆向量化")
    print("=" * 50)
    
    # 索引记忆
    collection = index_memories()
    
    # 测试检索
    print("\n🔍 测试检索: '技能使用方法'")
    results = search_memories("技能使用方法", n_results=3)
    
    if results and results['documents']:
        print("\n📌 相关记忆:")
        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(f"\n  {i}. [{meta['type']}] {meta['title']}")
            print(f"     📍 {meta['path']}")
            print(f"     🏷️  {meta.get('tags', '无标签')}")
            print(f"     📊 相似度: {1-dist:.2%}")
    
    print("\n✅ 向量化完成!")

if __name__ == "__main__":
    main()
