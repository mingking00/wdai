"""
BM25 Retriever for Tool-DC

基于 BM25 算法的工具检索器
"""

import math
import re
from typing import List, Dict, Tuple
from collections import defaultdict

from ..models import Tool


class BM25Retriever:
    """
    BM25 检索器实现
    
    基于论文使用 BM25 进行初始工具检索
    
    BM25 公式: score(D,Q) = Σ IDF(q_i) * (f(q_i,D) * (k1+1)) / (f(q_i,D) + k1 * (1 - b + b * |D|/avgdl))
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化 BM25 检索器
        
        Args:
            k1: 控制词频饱和度的参数，通常 1.2-2.0
            b: 控制文档长度归一化的参数，通常 0.75
        """
        self.k1 = k1
        self.b = b
        
        # 索引数据
        self.tools: List[Tool] = []
        self.documents: List[List[str]] = []  # 分词后的文档
        self.doc_freqs: Dict[str, int] = defaultdict(int)  # 文档频率
        self.idf: Dict[str, float] = {}  # IDF 值
        self.doc_lengths: List[int] = []  # 文档长度
        self.avgdl: float = 0.0  # 平均文档长度
        self.total_docs: int = 0  # 文档总数
        
    def _tokenize(self, text: str) -> List[str]:
        """
        分词
        
        简单实现：小写 + 字母数字提取
        """
        # 转为小写，提取单词
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9_]+\b', text)
        return tokens
    
    def _tool_to_text(self, tool: Tool) -> str:
        """
        将工具转换为可索引的文本
        
        组合工具名、描述和参数信息
        """
        parts = [
            tool.name,
            tool.description,
        ]
        
        # 添加参数信息
        for param in tool.parameters:
            parts.append(param.name)
            parts.append(param.description)
        
        return " ".join(parts)
    
    def build_index(self, tools: List[Tool]):
        """
        构建 BM25 索引
        
        Args:
            tools: 工具列表
        """
        self.tools = tools
        self.documents = []
        self.doc_freqs = defaultdict(int)
        self.doc_lengths = []
        
        # 分词并统计
        for tool in tools:
            text = self._tool_to_text(tool)
            tokens = self._tokenize(text)
            self.documents.append(tokens)
            self.doc_lengths.append(len(tokens))
            
            # 统计文档频率
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1
        
        # 计算平均文档长度
        self.total_docs = len(tools)
        if self.total_docs > 0:
            self.avgdl = sum(self.doc_lengths) / self.total_docs
        
        # 计算 IDF
        for token, freq in self.doc_freqs.items():
            # IDF = log((N - n(q) + 0.5) / (n(q) + 0.5) + 1)
            idf = math.log(
                (self.total_docs - freq + 0.5) / (freq + 0.5) + 1
            )
            self.idf[token] = idf
        
    def _score_document(self, query_tokens: List[str], doc_idx: int) -> float:
        """
        计算查询与文档的 BM25 分数
        
        Args:
            query_tokens: 查询分词
            doc_idx: 文档索引
            
        Returns:
            float: BM25 分数
        """
        doc_tokens = self.documents[doc_idx]
        doc_length = self.doc_lengths[doc_idx]
        
        # 统计词频
        token_freqs = defaultdict(int)
        for token in doc_tokens:
            token_freqs[token] += 1
        
        # 计算分数
        score = 0.0
        for token in query_tokens:
            if token not in self.idf:
                continue
            
            idf = self.idf[token]
            freq = token_freqs[token]
            
            # BM25 公式
            numerator = freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * (doc_length / self.avgdl))
            
            score += idf * numerator / denominator
        
        return score
    
    def retrieve(self, query: str, tools: List[Tool], top_k: int = 5) -> List[Tool]:
        """
        检索相关工具
        
        Args:
            query: 查询文本
            tools: 候选工具列表
            top_k: 返回前 K 个结果
            
        Returns:
            List[Tool]: 按相关性排序的工具列表
        """
        # 如果索引未构建或工具列表变化，重新构建
        if len(self.tools) != len(tools) or self.tools != tools:
            self.build_index(tools)
        
        if not self.tools:
            return []
        
        # 分词查询
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            return tools[:top_k]
        
        # 计算每个文档的分数
        scores: List[Tuple[int, float]] = []
        for doc_idx in range(self.total_docs):
            score = self._score_document(query_tokens, doc_idx)
            scores.append((doc_idx, score))
        
        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前 K 个
        top_tools = []
        for doc_idx, score in scores[:top_k]:
            if score > 0:  # 只返回有分数的结果
                top_tools.append(self.tools[doc_idx])
        
        return top_tools
    
    def batch_retrieve(
        self, 
        queries: List[str], 
        tools: List[Tool], 
        top_k: int = 5
    ) -> List[List[Tool]]:
        """
        批量检索
        
        Args:
            queries: 查询列表
            tools: 工具列表
            top_k: 每个查询返回的结果数
            
        Returns:
            List[List[Tool]]: 每个查询的检索结果
        """
        results = []
        for query in queries:
            results.append(self.retrieve(query, tools, top_k))
        return results


class SimpleEmbeddingRetriever:
    """
    简单的 Embedding 检索器（占位实现）
    
    实际使用时需要：
    1. 文本嵌入模型（如 sentence-transformers）
    2. 向量索引（如 faiss）
    """
    
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model
        self.tools = []
        self.embeddings = []
    
    def encode(self, text: str) -> List[float]:
        """
        编码文本为向量
        
        实际应调用嵌入模型
        """
        # 占位实现：简单的字符哈希
        # 实际使用时替换为真实嵌入
        vec = [0.0] * 128
        for i, char in enumerate(text[:128]):
            vec[i] = ord(char) / 255.0
        return vec
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    def build_index(self, tools: List[Tool]):
        """构建索引"""
        self.tools = tools
        self.embeddings = []
        
        for tool in tools:
            text = f"{tool.name} {tool.description}"
            emb = self.encode(text)
            self.embeddings.append(emb)
    
    def retrieve(self, query: str, tools: List[Tool], top_k: int = 5) -> List[Tool]:
        """检索"""
        if len(self.tools) != len(tools):
            self.build_index(tools)
        
        query_emb = self.encode(query)
        
        # 计算相似度
        similarities = []
        for i, emb in enumerate(self.embeddings):
            sim = self.cosine_similarity(query_emb, emb)
            similarities.append((i, sim))
        
        # 排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前 K
        return [self.tools[i] for i, _ in similarities[:top_k]]
