"""
IER-KG 向量检索系统
基于简单embedding的相似度检索

功能：
1. 经验文本向量化
2. 向量相似度检索
3. 混合检索 (向量+图谱)
4. 语义相似度计算
"""

import json
import math
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
import hashlib


@dataclass
class VectorExperience:
    """向量化经验"""
    exp_id: str
    exp_name: str
    vector: List[float]
    text: str  # 原始文本
    metadata: Dict


class SimpleEmbedding:
    """
    简单Embedding实现
    基于TF-IDF加权的词袋模型
    （无需外部依赖，纯Python实现）
    """
    
    def __init__(self, vocab_size: int = 5000):
        self.vocab_size = vocab_size
        self.word_freq = defaultdict(int)
        self.doc_count = 0
        self.idf = {}
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 转为小写，提取单词
        text = text.lower()
        words = re.findall(r'\b[a-z_][a-z0-9_]*\b', text)
        return words
    
    def _hash_word(self, word: str) -> int:
        """哈希单词到固定维度"""
        return int(hashlib.md5(word.encode()).hexdigest(), 16) % self.vocab_size
    
    def fit(self, texts: List[str]):
        """训练IDF"""
        self.doc_count = len(texts)
        
        # 统计每个词出现的文档数
        doc_freq = defaultdict(int)
        for text in texts:
            words = set(self._tokenize(text))
            for word in words:
                doc_freq[word] += 1
        
        # 计算IDF
        for word, freq in doc_freq.items():
            self.idf[word] = math.log(self.doc_count / (freq + 1)) + 1
    
    def encode(self, text: str) -> List[float]:
        """编码文本为向量"""
        words = self._tokenize(text)
        vector = [0.0] * self.vocab_size
        
        # 统计词频
        word_count = defaultdict(int)
        for word in words:
            word_count[word] += 1
        
        # 构建TF-IDF向量
        for word, count in word_count.items():
            idx = self._hash_word(word)
            tf = count / len(words) if words else 0
            idf = self.idf.get(word, 1.0)
            vector[idx] += tf * idf
        
        # L2归一化
        norm = math.sqrt(sum(x*x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        
        return vector


class VectorRetrievalSystem:
    """
    向量检索系统
    
    支持：
    - 语义相似度检索
    - 与图谱检索结果融合
    - 动态索引更新
    """
    
    def __init__(self, data_dir: str = ".", embedding_dim: int = 5000):
        self.data_dir = Path(data_dir)
        self.index_file = self.data_dir / "ier_kg_vector_index.json"
        
        # Embedding模型
        self.embedding = SimpleEmbedding(vocab_size=embedding_dim)
        
        # 向量索引
        self.vectors: Dict[str, VectorExperience] = {}
        self.is_fitted = False
        
        # 加载已有索引
        self._load_index()
    
    def _load_index(self):
        """加载向量索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                    for exp_id, exp_data in data.items():
                        self.vectors[exp_id] = VectorExperience(
                            exp_id=exp_data["exp_id"],
                            exp_name=exp_data["exp_name"],
                            vector=exp_data["vector"],
                            text=exp_data["text"],
                            metadata=exp_data.get("metadata", {})
                        )
            except Exception as e:
                print(f"[VectorRetrieval] 加载索引失败: {e}")
    
    def _save_index(self):
        """保存向量索引"""
        try:
            data = {}
            for exp_id, ve in self.vectors.items():
                # 只保存可序列化的metadata
                safe_metadata = {}
                for k, v in ve.metadata.items():
                    if isinstance(v, (str, int, float, bool, list, dict)):
                        safe_metadata[k] = v
                    else:
                        safe_metadata[k] = str(v)
                
                data[exp_id] = {
                    "exp_id": ve.exp_id,
                    "exp_name": ve.exp_name,
                    "vector": ve.vector,
                    "text": ve.text,
                    "metadata": safe_metadata
                }
            with open(self.index_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[VectorRetrieval] 保存索引失败: {e}")
    
    def _build_text(self, exp) -> str:
        """构建经验的文本表示"""
        parts = [
            f"name: {exp.name}",
            f"description: {exp.description}",
            f"context: {getattr(exp, 'context', '')}",
            f"solution: {getattr(exp, 'solution', '')}",
            f"tags: {' '.join(getattr(exp, 'tags', []))}"
        ]
        return " ".join(parts)
    
    def build_index(self, experiences: Dict):
        """
        构建向量索引
        
        Args:
            experiences: 经验字典 {id: experience}
        """
        if not experiences:
            return
        
        # 收集所有文本
        texts = []
        exp_list = []
        
        for exp_id, exp in experiences.items():
            text = self._build_text(exp)
            texts.append(text)
            exp_list.append((exp_id, exp, text))
        
        # 训练embedding
        self.embedding.fit(texts)
        self.is_fitted = True
        
        # 编码所有经验
        self.vectors = {}
        for exp_id, exp, text in exp_list:
            vector = self.embedding.encode(text)
            self.vectors[exp_id] = VectorExperience(
                exp_id=exp_id,
                exp_name=exp.name,
                vector=vector,
                text=text,
                metadata={
                    "exp_type": getattr(exp, 'exp_type', 'unknown'),
                    "language": getattr(exp, 'language', 'unknown')
                }
            )
        
        # 保存索引
        self._save_index()
        print(f"[VectorRetrieval] 构建索引完成: {len(self.vectors)} 条经验")
    
    def add_experience(self, exp_id: str, exp):
        """添加单条经验到索引"""
        if not self.is_fitted:
            return
        
        text = self._build_text(exp)
        vector = self.embedding.encode(text)
        
        self.vectors[exp_id] = VectorExperience(
            exp_id=exp_id,
            exp_name=exp.name,
            vector=vector,
            text=text,
            metadata={
                "exp_type": getattr(exp, 'exp_type', 'unknown'),
                "language": getattr(exp, 'language', 'unknown')
            }
        )
        
        self._save_index()
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        向量相似度检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            [(exp_id, similarity), ...]
        """
        if not self.is_fitted or not self.vectors:
            return []
        
        # 编码查询
        query_vector = self.embedding.encode(query)
        
        # 计算相似度
        similarities = []
        for exp_id, ve in self.vectors.items():
            sim = self._cosine_similarity(query_vector, ve.vector)
            similarities.append((exp_id, sim))
        
        # 排序并返回top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def hybrid_search(self, query: str, 
                     graph_results: List[Tuple[str, float]],
                     top_k: int = 10,
                     vector_weight: float = 0.5) -> List[Tuple[str, float, str]]:
        """
        混合检索 (向量 + 图谱)
        
        Args:
            query: 查询文本
            graph_results: 图谱检索结果 [(exp_id, score), ...]
            top_k: 返回数量
            vector_weight: 向量检索权重 (0-1)
            
        Returns:
            [(exp_id, combined_score, source), ...]
            source: "vector" | "graph" | "hybrid"
        """
        # 向量检索
        vector_results = self.search(query, top_k=top_k*2)
        
        # 合并结果
        combined = {}
        
        # 添加图谱结果
        for exp_id, score in graph_results:
            combined[exp_id] = {
                "graph_score": score,
                "vector_score": 0,
                "source": "graph"
            }
        
        # 添加向量结果
        for exp_id, score in vector_results:
            if exp_id in combined:
                combined[exp_id]["vector_score"] = score
                combined[exp_id]["source"] = "hybrid"
            else:
                combined[exp_id] = {
                    "graph_score": 0,
                    "vector_score": score,
                    "source": "vector"
                }
        
        # 计算融合分数
        results = []
        for exp_id, scores in combined.items():
            g_score = scores["graph_score"]
            v_score = scores["vector_score"]
            
            # 加权融合
            if scores["source"] == "hybrid":
                final_score = g_score * (1 - vector_weight) + v_score * vector_weight
            elif scores["source"] == "graph":
                final_score = g_score * (1 - vector_weight)
            else:
                final_score = v_score * vector_weight
            
            results.append((exp_id, final_score, scores["source"]))
        
        # 排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "vector_count": len(self.vectors),
            "is_fitted": self.is_fitted,
            "embedding_dim": self.embedding.vocab_size if hasattr(self.embedding, 'vocab_size') else 0
        }


# 便捷函数
def create_vector_retrieval(data_dir: str = ".") -> VectorRetrievalSystem:
    """创建向量检索系统"""
    return VectorRetrievalSystem(data_dir)


if __name__ == "__main__":
    # 测试
    vr = VectorRetrievalSystem(".")
    
    # 模拟经验
    class MockExp:
        def __init__(self, name, desc):
            self.name = name
            self.description = desc
            self.context = ""
            self.solution = ""
            self.tags = []
    
    experiences = {
        "exp_1": MockExp("使用装饰器", "Python装饰器模式"),
        "exp_2": MockExp("缓存优化", "使用lru_cache"),
        "exp_3": MockExp("异常处理", "try-except最佳实践")
    }
    
    vr.build_index(experiences)
    
    # 搜索
    results = vr.search("装饰器缓存")
    print("搜索结果:", results)
