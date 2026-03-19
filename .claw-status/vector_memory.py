"""
WDai Vector Memory Store
基于Qdrant的向量存储后端 (内存模式)

阶段A实现：向量检索替换文件搜索
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: float
    source: str  # 'daily', 'core', 'semantic'


class VectorMemoryStore:
    """
    向量记忆存储
    
    使用Qdrant内存模式，无需Docker
    支持语义检索和关键词检索
    """
    
    # 使用简单的hash-based embedding (无需外部API)
    # 后续可替换为sentence-transformers或OpenAI embedding
    VECTOR_SIZE = 384  # 使用minilm-like维度
    
    def __init__(self, storage_dir: str = ".memory/vector_store"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Qdrant客户端 (内存模式 + 持久化)
        self.client = QdrantClient(
            location=":memory:",  # 内存模式
        )
        
        # 创建集合
        self._ensure_collection()
        
        # 简单embedding模型 (使用哈希 + TF-like统计)
        self.vocab = self._build_vocab()
        
        print(f"✅ VectorMemoryStore 初始化完成")
        print(f"   向量维度: {self.VECTOR_SIZE}")
        print(f"   存储路径: {self.storage_dir}")
    
    def _build_vocab(self) -> Dict[str, int]:
        """构建简单词表用于embedding"""
        # 常见技术词汇
        words = [
            # 技术领域
            "python", "javascript", "typescript", "react", "vue", "node",
            "docker", "kubernetes", "aws", "gcp", "azure",
            "database", "api", "frontend", "backend", "fullstack",
            "机器学习", "深度学习", "ai", "llm", "神经网络",
            "git", "github", "ci/cd", "devops", "agile",
            
            # 动作
            "创建", "删除", "更新", "查询", "部署", "调试",
            "分析", "优化", "重构", "测试", "修复", "实现",
            "部署", "配置", "安装", "升级", "迁移",
            
            # 概念
            "错误", "问题", "解决方案", "最佳实践", "架构",
            "性能", "安全", "可维护性", "可扩展性",
            "设计模式", "算法", "数据结构",
            
            # 时间
            "今天", "昨天", "上周", "最近", "之前", "之后",
            
            # 记忆类型
            "技能", "错误记录", "学习", "项目", "对话",
        ]
        return {word: idx for idx, word in enumerate(words)}
    
    def _simple_embed(self, text: str) -> List[float]:
        """
        简单的本地embedding (无需外部API)
        
        基于:
        1. 词频统计
        2. 字符n-gram哈希
        3. 位置编码
        """
        text_lower = text.lower()
        vec = [0.0] * self.VECTOR_SIZE
        
        # 1. 词表匹配
        for word, idx in self.vocab.items():
            if word in text_lower:
                vec[idx % self.VECTOR_SIZE] += 1.0
        
        # 2. 字符n-gram哈希
        for i in range(len(text) - 2):
            ngram = text[i:i+3]
            hash_val = hash(ngram) % self.VECTOR_SIZE
            vec[hash_val] += 0.1
        
        # 3. 归一化
        import math
        norm = math.sqrt(sum(x*x for x in vec))
        if norm > 0:
            vec = [x/norm for x in vec]
        
        return vec
    
    def _ensure_collection(self):
        """确保集合存在"""
        try:
            self.client.create_collection(
                collection_name="wdai_memory",
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
            print("✅ 创建集合: wdai_memory")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ 集合已存在: wdai_memory")
            else:
                raise
    
    def add_memory(self, entry: MemoryEntry) -> str:
        """添加单条记忆"""
        import uuid
        
        # 生成embedding
        embedding = self._simple_embed(entry.content)
        
        # 使用UUID或整数ID
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entry.id))
        
        # 准备payload
        payload = {
            "content": entry.content,
            "metadata": entry.metadata,
            "timestamp": entry.timestamp,
            "source": entry.source,
            "date": datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d"),
            "original_id": entry.id  # 保留原始ID
        }
        
        # 插入Qdrant
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )
        
        self.client.upsert(
            collection_name="wdai_memory",
            points=[point]
        )
        
        return point_id
    
    def add_memories(self, entries: List[MemoryEntry]) -> int:
        """批量添加记忆"""
        import uuid
        
        points = []
        for entry in entries:
            embedding = self._simple_embed(entry.content)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, entry.id))
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "content": entry.content,
                    "metadata": entry.metadata,
                    "timestamp": entry.timestamp,
                    "source": entry.source,
                    "date": datetime.fromtimestamp(entry.timestamp).strftime("%Y-%m-%d"),
                    "original_id": entry.id
                }
            )
            points.append(point)
        
        self.client.upsert(
            collection_name="wdai_memory",
            points=points
        )
        
        return len(entries)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.3,
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        语义搜索记忆
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            source_filter: 按来源过滤 (daily/core/semantic)
        """
        # 生成查询embedding
        query_vec = self._simple_embed(query)
        
        # 构建过滤条件
        filter_condition = None
        if source_filter:
            from qdrant_client.models import FieldCondition, MatchValue
            filter_condition = FieldCondition(
                key="source",
                match=MatchValue(value=source_filter)
            )
        
        # 执行搜索 - 使用 query_points
        results = self.client.query_points(
            collection_name="wdai_memory",
            query=query_vec,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=filter_condition,
            with_payload=True
        ).points
        
        return [
            {
                "id": r.id,
                "score": r.score,
                "content": r.payload.get("content"),
                "metadata": r.payload.get("metadata"),
                "timestamp": r.payload.get("timestamp"),
                "source": r.payload.get("source")
            }
            for r in results
        ]
    
    def hybrid_search(
        self,
        query: str,
        keywords: List[str],
        top_k: int = 5
    ) -> List[Dict]:
        """
        混合搜索: 语义 + 关键词
        """
        # 语义搜索
        semantic_results = self.search(query, top_k=top_k*2)
        
        # 关键词匹配
        keyword_set = set(k.lower() for k in keywords)
        for r in semantic_results:
            content_lower = r['content'].lower()
            keyword_matches = sum(1 for k in keyword_set if k in content_lower)
            r['keyword_score'] = keyword_matches / len(keyword_set) if keyword_set else 0
            
            # 融合得分 (70%语义 + 30%关键词)
            r['hybrid_score'] = 0.7 * r['score'] + 0.3 * r['keyword_score']
        
        # 按融合得分排序
        semantic_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return semantic_results[:top_k]
    
    def get_stats(self) -> Dict:
        """获取存储统计"""
        try:
            info = self.client.get_collection("wdai_memory")
            return {
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": "active"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def export_to_file(self, filepath: str):
        """导出所有记忆到文件 (备份)"""
        # 滚动获取所有数据
        all_points = []
        offset = None
        
        while True:
            result = self.client.scroll(
                collection_name="wdai_memory",
                limit=100,
                offset=offset,
                with_payload=True
            )
            
            points = result.points if hasattr(result, 'points') else result[0]
            next_offset = result.next_page_offset if hasattr(result, 'next_page_offset') else result[1]
            
            all_points.extend(points)
            
            if next_offset is None:
                break
            offset = next_offset
        
        # 保存为JSON
        data = [
            {
                "id": p.id,
                "payload": p.payload
            }
            for p in all_points
        ]
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return len(data)


# ============ 与现有系统集成 ============

class MemorySearchEnhanced:
    """
    增强版记忆搜索
    
    替换现有的文件搜索，使用向量检索
    """
    
    def __init__(self):
        self.vector_store = VectorMemoryStore()
        self._load_existing_memories()
    
    def _load_existing_memories(self):
        """加载现有记忆文件到向量存储"""
        import os
        import re
        
        memory_dir = Path("/root/.openclaw/workspace/memory")
        if not memory_dir.exists():
            return
        
        entries = []
        
        # 加载daily记忆
        daily_dir = memory_dir / "daily"
        if daily_dir.exists():
            for md_file in daily_dir.glob("*.md"):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取段落作为独立条目
                    paragraphs = re.split(r'\n##+\s+', content)
                    for i, para in enumerate(paragraphs):
                        if len(para.strip()) > 50:  # 过滤短内容
                            entry = MemoryEntry(
                                id=f"daily_{md_file.stem}_{i}",
                                content=para[:1000],  # 限制长度
                                metadata={"file": str(md_file), "section": i},
                                timestamp=datetime.now().timestamp(),
                                source="daily"
                            )
                            entries.append(entry)
        
        # 加载core记忆
        core_dir = memory_dir / "core"
        if core_dir.exists():
            for md_file in core_dir.glob("*.md"):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    entry = MemoryEntry(
                        id=f"core_{md_file.stem}",
                        content=content[:2000],
                        metadata={"file": str(md_file)},
                        timestamp=datetime.now().timestamp(),
                        source="core"
                    )
                    entries.append(entry)
        
        # 批量导入
        if entries:
            count = self.vector_store.add_memories(entries)
            print(f"✅ 导入 {count} 条现有记忆")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索记忆"""
        return self.vector_store.search(query, top_k=top_k)
    
    def add_current_interaction(self, query: str, response: str, metadata: Dict = None):
        """记录当前交互"""
        entry = MemoryEntry(
            id=f"interaction_{datetime.now().timestamp()}",
            content=f"Q: {query}\nA: {response}",
            metadata=metadata or {},
            timestamp=datetime.now().timestamp(),
            source="semantic"
        )
        self.vector_store.add_memory(entry)


# ============ 测试 ============

if __name__ == "__main__":
    print("="*50)
    print("WDai Vector Memory Store - 测试")
    print("="*50)
    
    # 初始化
    store = VectorMemoryStore()
    
    # 添加测试数据
    test_entries = [
        MemoryEntry(
            id="test_1",
            content="用户偏好使用Python进行数据分析，常用pandas和numpy",
            metadata={"type": "preference"},
            timestamp=datetime.now().timestamp(),
            source="core"
        ),
        MemoryEntry(
            id="test_2",
            content="昨天解决了Docker部署问题，使用了docker-compose",
            metadata={"type": "learning"},
            timestamp=datetime.now().timestamp(),
            source="daily"
        ),
        MemoryEntry(
            id="test_3",
            content="GitHub API上传失败时应该改用git push",
            metadata={"type": "error_lesson"},
            timestamp=datetime.now().timestamp(),
            source="semantic"
        ),
    ]
    
    store.add_memories(test_entries)
    print(f"\n✅ 添加 {len(test_entries)} 条测试记忆")
    
    # 测试搜索
    print("\n--- 搜索测试 ---")
    
    queries = [
        "用户喜欢用什么编程语言",
        "Docker部署",
        "GitHub上传失败",
        "数据分析工具",
    ]
    
    for query in queries:
        results = store.search(query, top_k=2)
        print(f"\n🔍 查询: '{query}'")
        for r in results:
            print(f"   得分: {r['score']:.3f} | {r['content'][:60]}...")
    
    # 统计
    print("\n--- 存储统计 ---")
    stats = store.get_stats()
    print(f"向量数量: {stats.get('vectors_count', 0)}")
    print(f"状态: {stats.get('status', 'unknown')}")
    
    print("\n✅ 测试完成")
