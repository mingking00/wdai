"""
Kimi Multi-Agent Platform - Memory System
Phase 3: Three-layer Memory (Short-term / Long-term / Semantic)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
import os
from pathlib import Path


@dataclass
class MemoryEntry:
    """记忆条目"""
    key: str
    value: Any
    timestamp: float
    metadata: Dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "embedding": self.embedding
        }


class BaseMemory(ABC):
    """记忆基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def store(self, key: str, value: Any, metadata: Dict = None) -> None:
        """存储记忆"""
        pass
    
    @abstractmethod
    def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆"""
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Tuple[str, Any, float]]:
        """搜索记忆 (返回: key, value, score)"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空记忆"""
        pass


class ShortTermMemory(BaseMemory):
    """
    短期记忆 - 当前会话上下文
    
    特点:
    - 内存存储，速度快
    - 会话结束清空
    - 最近使用优先
    """
    
    def __init__(self, max_size: int = 100):
        super().__init__("short_term")
        self.max_size = max_size
        self._storage: Dict[str, MemoryEntry] = {}
        self._access_order: List[str] = []
    
    def store(self, key: str, value: Any, metadata: Dict = None) -> None:
        """存储到短期记忆"""
        # 如果已满且是新key，移除最旧的
        if len(self._storage) >= self.max_size and key not in self._storage:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._storage:
                del self._storage[oldest_key]
        
        entry = MemoryEntry(
            key=key,
            value=value,
            timestamp=datetime.now().timestamp(),
            metadata=metadata or {}
        )
        
        self._storage[key] = entry
        
        # 更新访问顺序
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """从短期记忆检索"""
        if key in self._storage:
            # 更新访问顺序
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._storage[key].value
        return None
    
    def search(self, query: str, limit: int = 5) -> List[Tuple[str, Any, float]]:
        """简单关键词搜索"""
        results = []
        query_lower = query.lower()
        
        for key, entry in self._storage.items():
            score = 0.0
            if query_lower in key.lower():
                score += 0.5
            if isinstance(entry.value, str) and query_lower in entry.value.lower():
                score += 0.5
            
            if score > 0:
                results.append((key, entry.value, score))
        
        # 按分数排序
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:limit]
    
    def get_recent(self, n: int = 10) -> List[Tuple[str, Any]]:
        """获取最近n条记忆"""
        recent_keys = self._access_order[-n:]
        return [(k, self._storage[k].value) for k in recent_keys]
    
    def clear(self) -> None:
        """清空短期记忆"""
        self._storage.clear()
        self._access_order.clear()
    
    def __len__(self) -> int:
        return len(self._storage)


class LongTermMemory(BaseMemory):
    """
    长期记忆 - 持久化存储
    
    特点:
    - 文件存储，持久化
    - 跨会话保留
    - 支持结构化数据
    """
    
    def __init__(self, storage_dir: str = "./memory"):
        super().__init__("long_term")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, MemoryEntry] = {}
    
    def _get_file_path(self, key: str) -> Path:
        """获取存储文件路径"""
        # 使用hash避免特殊字符问题
        key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
        return self.storage_dir / f"{key_hash}.json"
    
    def store(self, key: str, value: Any, metadata: Dict = None) -> None:
        """存储到长期记忆"""
        entry = MemoryEntry(
            key=key,
            value=value,
            timestamp=datetime.now().timestamp(),
            metadata=metadata or {}
        )
        
        # 写入文件
        file_path = self._get_file_path(key)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 更新缓存
        self._cache[key] = entry
    
    def retrieve(self, key: str) -> Optional[Any]:
        """从长期记忆检索"""
        # 先查缓存
        if key in self._cache:
            return self._cache[key].value
        
        # 从文件读取
        file_path = self._get_file_path(key)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                entry = MemoryEntry(**data)
                self._cache[key] = entry
                return entry.value
        
        return None
    
    def search(self, query: str, limit: int = 5) -> List[Tuple[str, Any, float]]:
        """搜索所有存储的文件"""
        results = []
        query_lower = query.lower()
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    entry = MemoryEntry(**data)
                    
                    score = 0.0
                    if query_lower in entry.key.lower():
                        score += 0.5
                    if isinstance(entry.value, str) and query_lower in entry.value.lower():
                        score += 0.5
                    
                    if score > 0:
                        results.append((entry.key, entry.value, score))
            except Exception:
                continue
        
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:limit]
    
    def list_all(self) -> List[str]:
        """列出所有存储的key"""
        keys = []
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    keys.append(data['key'])
            except Exception:
                continue
        return keys
    
    def clear(self) -> None:
        """清空长期记忆"""
        for file_path in self.storage_dir.glob("*.json"):
            file_path.unlink()
        self._cache.clear()


class SemanticMemory(BaseMemory):
    """
    语义记忆 - 基于向量检索
    
    特点:
    - 语义相似度搜索
    - 支持模糊匹配
    - 需要embedding模型
    """
    
    def __init__(self, embedding_model=None):
        super().__init__("semantic")
        self.embedding_model = embedding_model
        self._storage: Dict[str, MemoryEntry] = {}
    
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的embedding向量"""
        if self.embedding_model:
            # 使用真实的embedding模型
            return self.embedding_model.encode(text).tolist()
        else:
            # 简化实现：使用字符频率作为伪embedding
            # 实际应用中应使用OpenAI embedding或本地模型
            vec = [0.0] * 128
            for i, char in enumerate(text[:128]):
                vec[i] = ord(char) / 255.0
            return vec
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def store(self, key: str, value: str, metadata: Dict = None) -> None:
        """存储到语义记忆（value必须是文本）"""
        text = str(value)
        embedding = self._get_embedding(text)
        
        entry = MemoryEntry(
            key=key,
            value=value,
            timestamp=datetime.now().timestamp(),
            metadata=metadata or {},
            embedding=embedding
        )
        
        self._storage[key] = entry
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索语义记忆"""
        if key in self._storage:
            return self._storage[key].value
        return None
    
    def search(self, query: str, limit: int = 5) -> List[Tuple[str, Any, float]]:
        """语义相似度搜索"""
        if not self._storage:
            return []
        
        query_embedding = self._get_embedding(query)
        
        # 计算相似度
        results = []
        for key, entry in self._storage.items():
            if entry.embedding:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                if similarity > 0.5:  # 阈值过滤
                    results.append((key, entry.value, similarity))
        
        # 按相似度排序
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:limit]
    
    def clear(self) -> None:
        """清空语义记忆"""
        self._storage.clear()
    
    def __len__(self) -> int:
        return len(self._storage)


class MemoryManager:
    """
    记忆管理器 - 统一管理三层记忆
    
    使用策略:
    1. 先查短期记忆（当前上下文）
    2. 再查语义记忆（相关内容）
    3. 最后查长期记忆（历史记录）
    """
    
    def __init__(self, storage_dir: str = "./memory", embedding_model=None):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(storage_dir)
        self.semantic = SemanticMemory(embedding_model)
    
    def store(self, key: str, value: Any, level: str = "short_term", metadata: Dict = None) -> None:
        """
        存储记忆
        
        Args:
            level: short_term, long_term, semantic, or all
        """
        if level == "short_term" or level == "all":
            self.short_term.store(key, value, metadata)
        
        if level == "long_term" or level == "all":
            self.long_term.store(key, value, metadata)
        
        if level == "semantic" or level == "all":
            if isinstance(value, str):
                self.semantic.store(key, value, metadata)
    
    def retrieve(self, key: str, level: str = "short_term") -> Optional[Any]:
        """
        检索记忆
        
        搜索顺序: short_term -> long_term
        """
        if level == "short_term":
            result = self.short_term.retrieve(key)
            if result is not None:
                return result
        
        if level in ("short_term", "long_term"):
            result = self.long_term.retrieve(key)
            if result is not None:
                return result
        
        return None
    
    def search(self, query: str, limit: int = 5) -> Dict[str, List[Tuple]]:
        """
        跨层搜索
        
        Returns:
            {
                "short_term": [(key, value, score), ...],
                "long_term": [(key, value, score), ...],
                "semantic": [(key, value, score), ...]
            }
        """
        return {
            "short_term": self.short_term.search(query, limit),
            "long_term": self.long_term.search(query, limit),
            "semantic": self.semantic.search(query, limit)
        }
    
    def remember(self, fact: str, importance: str = "normal") -> None:
        """
        便捷方法：记住一个事实
        
        Args:
            importance: low, normal, high
                - low: 仅短期记忆
                - normal: 短期 + 语义
                - high: 三层全部
        """
        key = f"fact_{datetime.now().timestamp()}"
        
        if importance == "low":
            self.short_term.store(key, fact)
        elif importance == "normal":
            self.short_term.store(key, fact)
            self.semantic.store(key, fact)
        else:  # high
            self.store(key, fact, level="all")
    
    def recall(self, query: str, top_k: int = 3) -> List[str]:
        """
        便捷方法：回忆相关内容
        
        返回最相关的记忆内容列表
        """
        all_results = []
        
        # 收集各层结果
        for level, results in self.search(query, top_k).items():
            for key, value, score in results:
                all_results.append((value, score, level))
        
        # 按分数排序
        all_results.sort(key=lambda x: x[1], reverse=True)
        
        # 去重并返回
        seen = set()
        unique_results = []
        for value, score, level in all_results:
            if value not in seen:
                seen.add(value)
                unique_results.append(f"[{level}] {value}")
        
        return unique_results[:top_k]
    
    def get_context(self, n_recent: int = 5) -> str:
        """获取当前上下文（最近短期记忆）"""
        recent = self.short_term.get_recent(n_recent)
        return "\n".join([f"- {k}: {v}" for k, v in recent])
    
    def clear(self, level: str = "all") -> None:
        """清空记忆"""
        if level == "short_term" or level == "all":
            self.short_term.clear()
        if level == "long_term" or level == "all":
            self.long_term.clear()
        if level == "semantic" or level == "all":
            self.semantic.clear()
    
    def stats(self) -> Dict:
        """获取记忆统计"""
        return {
            "short_term": len(self.short_term),
            "long_term": len(self.long_term.list_all()),
            "semantic": len(self.semantic)
        }


# 便捷函数
def create_memory_manager(storage_dir: str = "./memory") -> MemoryManager:
    """创建记忆管理器"""
    return MemoryManager(storage_dir)
