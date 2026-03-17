# mem0-memory 检索管道详解

## 核心设计原则

检索管道的设计目标是：**在正确的时间，召回最相关的记忆**。

设计原则：
1. **多路召回** - 不同检索策略覆盖不同场景
2. **动态融合** - 根据查询类型自动调整权重
3. **时间感知** - 新记忆优先，旧记忆衰减
4. **精排优化** - 两阶段检索：粗排 + 精排

---

## 四阶段检索流程

```
用户查询
    ↓
[阶段1: 多路召回]  ← 向量检索 + BM25 + 时间范围过滤
    ↓
候选记忆池 (Top 50)
    ↓
[阶段2: 动态融合]  ← RRF融合算法
    ↓
融合排序结果 (Top 20)
    ↓
[阶段3: 精排优化]  ← Cross-Encoder重排
    ↓
精排结果 (Top 10)
    ↓
[阶段4: 时间加权]  ← 衰减 + 访问频率
    ↓
最终记忆列表 → 注入上下文
```

---

## 完整代码实现

### 1. 多路召回引擎 (`retrieval_engines.py`)

```python
"""
Multi-Channel Retrieval Engines
支持多种检索策略，可独立调用或组合使用
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from abc import ABC, abstractmethod

@dataclass
class RetrievalResult:
    """检索结果单元"""
    memory_id: str
    content: str
    score: float           # 该检索通道的原始分数
    source: str            # 来源通道: vector|bm25|temporal|hybrid
    metadata: Dict
    rank: int = 0          # 在该通道中的排名

class BaseRetriever(ABC):
    """检索器基类"""
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

# ============ 通道1: 向量语义检索 ============

class VectorRetriever(BaseRetriever):
    """
    基于Embedding的语义检索
    捕获查询的语义含义，找到概念相关的记忆
    """
    
    def __init__(self, vector_store, embedding_model):
        self.vector_store = vector_store
        self.embedder = embedding_model
        
    @property
    def name(self) -> str:
        return "vector"
    
    def retrieve(self, query: str, user_id: str, top_k: int = 20) -> List[RetrievalResult]:
        """
        向量检索流程:
        1. 查询向量化
        2. 向量数据库近似最近邻搜索 (ANN)
        3. 返回相似度分数
        """
        # 向量化查询
        query_embedding = self.embedder.encode(query)
        
        # ANN搜索 (使用LanceDB或类似)
        results = self.vector_store.search(
            vector=query_embedding,
            user_id=user_id,  # 用户隔离
            top_k=top_k,
            metric="cosine"   # 余弦相似度
        )
        
        return [
            RetrievalResult(
                memory_id=r["id"],
                content=r["content"],
                score=r["score"],           # 余弦相似度 0-1
                source="vector",
                metadata=r["metadata"],
                rank=i+1
            )
            for i, r in enumerate(results)
        ]

# ============ 通道2: BM25关键词检索 ============

class BM25Retriever(BaseRetriever):
    """
    基于BM25的关键词检索
    捕获精确术语匹配，适合技术名词、专有名词
    """
    
    def __init__(self, text_index):
        self.index = text_index  # 如: Whoosh, Elasticsearch, 或自建
        
    @property
    def name(self) -> str:
        return "bm25"
    
    def retrieve(self, query: str, user_id: str, top_k: int = 20) -> List[RetrievalResult]:
        """
        BM25检索流程:
        1. 分词查询
        2. 倒排索引查找
        3. BM25打分
        """
        results = self.index.search(
            query=query,
            user_id=user_id,
            top_k=top_k
        )
        
        # BM25分数通常无上限，归一化到0-1
        max_score = max([r["score"] for r in results], default=1)
        
        return [
            RetrievalResult(
                memory_id=r["id"],
                content=r["content"],
                score=min(r["score"] / max_score, 1.0),  # 归一化
                source="bm25",
                metadata=r["metadata"],
                rank=i+1
            )
            for i, r in enumerate(results)
        ]

# ============ 通道3: 时间范围检索 ============

class TemporalRetriever(BaseRetriever):
    """
    基于时间的检索
    召回最近N天的记忆，保证时效性
    """
    
    def __init__(self, vector_store):
        self.store = vector_store
        
    @property
    def name(self) -> str:
        return "temporal"
    
    def retrieve(self, 
                 query: str, 
                 user_id: str, 
                 days: int = 7, 
                 top_k: int = 20) -> List[RetrievalResult]:
        """
        时间检索流程:
        1. 计算时间窗口
        2. 查询该范围内的记忆
        3. 按时间倒序
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        results = self.store.get_by_timerange(
            user_id=user_id,
            start_date=cutoff_date,
            end_date=datetime.now(),
            limit=top_k
        )
        
        # 时间分数: 越新分数越高 (指数衰减)
        now = datetime.now()
        scored_results = []
        for i, r in enumerate(results):
            age_days = (now - r["created_at"]).days
            time_score = np.exp(-0.1 * age_days)  # 衰减因子
            
            scored_results.append(RetrievalResult(
                memory_id=r["id"],
                content=r["content"],
                score=time_score,
                source="temporal",
                metadata=r["metadata"],
                rank=i+1
            ))
        
        return scored_results

# ============ 通道4: 类别过滤检索 ============

class CategoryRetriever(BaseRetriever):
    """
    基于类别的定向检索
    当查询明确指向某类信息时使用
    """
    
    def __init__(self, vector_store):
        self.store = vector_store
        
    @property
    def name(self) -> str:
        return "category"
    
    def retrieve(self, 
                 query: str, 
                 user_id: str, 
                 category: str, 
                 top_k: int = 10) -> List[RetrievalResult]:
        """
        类别检索: 直接过滤特定类别
        如: "preference", "goal", "constraint"
        """
        results = self.store.get_by_category(
            user_id=user_id,
            category=category,
            limit=top_k
        )
        
        return [
            RetrievalResult(
                memory_id=r["id"],
                content=r["content"],
                score=0.8,  # 类别匹配给予基础高分
                source="category",
                metadata=r["metadata"],
                rank=i+1
            )
            for i, r in enumerate(results)
        ]
```

### 2. 融合算法 (`fusion.py`)

```python
"""
多路召回结果融合算法
"""

from typing import List, Dict
from collections import defaultdict
import numpy as np

class FusionAlgorithm:
    """
    融合算法基类
    """
    
    def fuse(self, results_by_channel: Dict[str, List[RetrievalResult]]) -> List[RetrievalResult]:
        raise NotImplementedError

class ReciprocalRankFusion(FusionAlgorithm):
    """
    RRF (Reciprocal Rank Fusion)
    
    公式: score = Σ(1 / (k + rank_i))
    
    特点:
    - 不需要归一化不同通道的分数
    - 只使用排名，对分数分布不敏感
    - 参数k控制低排名项目的权重 (通常k=60)
    """
    
    def __init__(self, k: int = 60):
        self.k = k
    
    def fuse(self, results_by_channel: Dict[str, List[RetrievalResult]]) -> List[RetrievalResult]:
        """
        RRF融合
        """
        # 按memory_id聚合分数
        rrf_scores = defaultdict(float)
        memory_data = {}
        
        for channel, results in results_by_channel.items():
            for result in results:
                memory_id = result.memory_id
                
                # RRF公式
                rank = result.rank
                rrf_score = 1.0 / (self.k + rank)
                rrf_scores[memory_id] += rrf_score
                
                # 保留第一个来源的完整数据
                if memory_id not in memory_data:
                    memory_data[memory_id] = result
        
        # 排序
        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 构建结果
        fused_results = []
        for memory_id, score in sorted_ids:
            result = memory_data[memory_id]
            result.score = score
            result.source = "hybrid_rrf"
            fused_results.append(result)
        
        return fused_results

class WeightedScoreFusion(FusionAlgorithm):
    """
    加权分数融合
    
    公式: score = Σ(w_i * normalize(score_i))
    
    特点:
    - 需要归一化各通道分数
    - 可调整权重适应不同场景
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        default_weights = {
            "vector": 0.5,    # 语义最重要
            "bm25": 0.3,      # 关键词次之
            "temporal": 0.15, # 时效性
            "category": 0.05  # 类别过滤
        }
        self.weights = weights or default_weights
    
    def fuse(self, results_by_channel: Dict[str, List[RetrievalResult]]) -> List[RetrievalResult]:
        """
        加权融合
        """
        # 按memory_id聚合
        aggregated = defaultdict(lambda: {"score": 0, "data": None, "channels": []})
        
        for channel, results in results_by_channel.items():
            weight = self.weights.get(channel, 0.1)
            
            for result in results:
                memory_id = result.memory_id
                aggregated[memory_id]["score"] += weight * result.score
                aggregated[memory_id]["channels"].append(channel)
                
                if aggregated[memory_id]["data"] is None:
                    aggregated[memory_id]["data"] = result
        
        # 排序
        sorted_items = sorted(
            aggregated.items(), 
            key=lambda x: x[1]["score"], 
            reverse=True
        )
        
        # 构建结果
        fused_results = []
        for memory_id, item in sorted_items:
            result = item["data"]
            result.score = item["score"]
            result.source = f"hybrid_weighted:{','.join(item['channels'])}"
            fused_results.append(result)
        
        return fused_results

class AdaptiveFusion(FusionAlgorithm):
    """
    自适应融合
    
    根据查询特征自动选择融合策略
    """
    
    def __init__(self):
        self.rrf = ReciprocalRankFusion()
        self.weighted = WeightedScoreFusion()
    
    def analyze_query(self, query: str) -> Dict:
        """
        分析查询特征
        """
        features = {
            "has_technical_terms": bool(re.search(r'\b(python|docker|api|database)\b', query.lower())),
            "is_question": any(q in query.lower() for q in ["what", "how", "why", "when", "where"]),
            "mentions_time": any(t in query.lower() for t in ["recent", "last", "yesterday", "today", "ago"]),
            "length": len(query.split())
        }
        return features
    
    def fuse(self, 
             query: str,
             results_by_channel: Dict[str, List[RetrievalResult]]) -> List[RetrievalResult]:
        """
        根据查询特征选择融合策略
        """
        features = self.analyze_query(query)
        
        # 技术查询: 提高BM25权重 (精确术语)
        if features["has_technical_terms"]:
            self.weighted.weights = {
                "vector": 0.4,
                "bm25": 0.4,      # 提高
                "temporal": 0.15,
                "category": 0.05
            }
            return self.weighted.fuse(results_by_channel)
        
        # 时间相关查询: 提高temporal权重
        if features["mentions_time"]:
            self.weighted.weights = {
                "vector": 0.4,
                "bm25": 0.2,
                "temporal": 0.35,  # 提高
                "category": 0.05
            }
            return self.weighted.fuse(results_by_channel)
        
        # 默认使用RRF (无需调参，更稳定)
        return self.rrf.fuse(results_by_channel)
```

### 3. 精排器 (`reranker.py`)

```python
"""
Cross-Encoder精排
两阶段检索: 粗排召回候选 → 精排计算相关性
"""

from typing import List
import numpy as np

class CrossEncoderReranker:
    """
    Cross-Encoder精排器
    
    原理:
    - 双塔模型 (Bi-Encoder): 分别编码查询和文档，计算向量相似度
      优点: 速度快，可预计算
      缺点: 精度较低
    
    - 交叉编码 (Cross-Encoder): 将查询和文档拼接后一起编码
      优点: 精度高，能捕获细粒度交互
      缺点: 速度慢，无法预计算
    
    策略: 双塔快速召回Top 50 → Cross-Encoder精排Top 10
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        模型选择:
        - ms-marco-MiniLM-L-6-v2: 轻量，适合实时
        - ms-marco-MiniLM-L-12-v2: 更准，稍慢
        - ms-marco-electra-base: 高精度
        """
        # 实际应加载模型
        # from sentence_transformers import CrossEncoder
        # self.model = CrossEncoder(model_name)
        self.model = None  # 占位
        
    def rerank(self, 
               query: str, 
               candidates: List[RetrievalResult], 
               top_k: int = 10) -> List[RetrievalResult]:
        """
        精排流程
        
        Args:
            query: 原始查询
            candidates: 粗排候选 (通常20-50个)
            top_k: 最终返回数量
        """
        if not candidates:
            return []
        
        # 准备输入
        pairs = [(query, c.content) for c in candidates]
        
        # Cross-Encoder打分
        # scores = self.model.predict(pairs)
        # 模拟实现:
        scores = self._simulate_scores(query, candidates)
        
        # 绑定分数
        for i, candidate in enumerate(candidates):
            candidate.score = float(scores[i])
            candidate.source = f"reranked:{candidate.source}"
        
        # 排序并返回Top K
        reranked = sorted(candidates, key=lambda x: x.score, reverse=True)
        return reranked[:top_k]
    
    def _simulate_scores(self, query: str, candidates: List[RetrievalResult]) -> np.ndarray:
        """
        模拟Cross-Encoder打分 (实际应使用真实模型)
        """
        # 简单的相关性启发式
        query_words = set(query.lower().split())
        scores = []
        
        for c in candidates:
            content_words = set(c.content.lower().split())
            
            # 词汇重叠
            overlap = len(query_words & content_words)
            score = overlap / max(len(query_words), 1)
            
            # 加上原始分数的权重
            score = score * 0.7 + c.score * 0.3
            
            scores.append(min(score, 1.0))
        
        return np.array(scores)

class LLMReranker:
    """
    LLM-based精排
    
    适用场景: 需要深度语义理解的复杂查询
    缺点: 成本高，延迟大
    """
    
    RERANK_PROMPT = """You are a relevance evaluator. Rate how relevant each memory is to the query.

Query: {query}

Memories:
{memories}

Rate each memory from 0.0 (completely irrelevant) to 1.0 (highly relevant).
Consider:
- Does it directly answer the query?
- Does it provide useful context?
- Is it from the right time period?

Return JSON format:
[{"id": "memory_id", "relevance": 0.95, "reason": "brief explanation"}, ...]
"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def rerank(self, 
               query: str, 
               candidates: List[RetrievalResult], 
               top_k: int = 5) -> List[RetrievalResult]:
        """
        LLM精排 (慢但准)
        """
        # 格式化输入
        memories_text = "\n".join([
            f"{i+1}. [ID: {c.memory_id}] {c.content}"
            for i, c in enumerate(candidates[:20])  # LLM只能处理少量
        ])
        
        prompt = self.RERANK_PROMPT.format(
            query=query,
            memories=memories_text
        )
        
        # 调用LLM
        response = self.llm.complete(prompt, response_format="json")
        ratings = json.loads(response)
        
        # 应用分数
        id_to_score = {r["id"]: r["relevance"] for r in ratings}
        
        for c in candidates:
            if c.memory_id in id_to_score:
                c.score = id_to_score[c.memory_id]
                c.source = f"llm_reranked:{c.source}"
        
        # 排序
        reranked = sorted(candidates, key=lambda x: x.score, reverse=True)
        return reranked[:top_k]
```

### 4. 主检索管道 (`hybrid_retrieve.py`)

```python
"""
主检索管道
整合多路召回、融合、精排
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RetrievalConfig:
    """检索配置"""
    # 召回配置
    vector_top_k: int = 20
    bm25_top_k: int = 20
    temporal_days: int = 7
    temporal_top_k: int = 20
    
    # 融合配置
    fusion_algorithm: str = "rrf"  # rrf|weighted|adaptive
    fusion_top_k: int = 20
    
    # 精排配置
    reranker: str = "cross_encoder"  # cross_encoder|llm|none
    rerank_top_k: int = 10
    
    # 时间加权配置
    enable_decay: bool = True
    decay_half_life_days: float = 30.0
    recency_boost: float = 0.1

class HybridRetriever:
    """
    混合检索主入口
    """
    
    def __init__(self, 
                 vector_store,
                 text_index,
                 embedding_model,
                 llm_client,
                 config: Optional[RetrievalConfig] = None):
        
        self.config = config or RetrievalConfig()
        
        # 初始化各检索器
        self.vector_retriever = VectorRetriever(vector_store, embedding_model)
        self.bm25_retriever = BM25Retriever(text_index)
        self.temporal_retriever = TemporalRetriever(vector_store)
        
        # 初始化融合器
        if self.config.fusion_algorithm == "rrf":
            self.fusion = ReciprocalRankFusion()
        elif self.config.fusion_algorithm == "weighted":
            self.fusion = WeightedScoreFusion()
        else:
            self.fusion = AdaptiveFusion()
        
        # 初始化精排器
        if self.config.reranker == "cross_encoder":
            self.reranker = CrossEncoderReranker()
        elif self.config.reranker == "llm":
            self.reranker = LLMReranker(llm_client)
        else:
            self.reranker = None
    
    def retrieve(self, 
                 query: str, 
                 user_id: str,
                 context: Optional[Dict] = None) -> List[RetrievalResult]:
        """
        执行完整检索流程
        
        Args:
            query: 用户查询
            user_id: 用户标识
            context: 额外上下文 (如当前任务类型)
            
        Returns:
            Top K最相关的记忆
        """
        print(f"[Retrieve] Query: '{query}' | User: {user_id}")
        
        # ========== 阶段1: 多路召回 ==========
        print("[Retrieve] Phase 1: Multi-channel retrieval...")
        
        results_by_channel = {}
        
        # 通道1: 向量语义检索
        vector_results = self.vector_retriever.retrieve(
            query, user_id, top_k=self.config.vector_top_k
        )
        results_by_channel["vector"] = vector_results
        print(f"  - Vector: {len(vector_results)} results")
        
        # 通道2: BM25关键词检索
        bm25_results = self.bm25_retriever.retrieve(
            query, user_id, top_k=self.config.bm25_top_k
        )
        results_by_channel["bm25"] = bm25_results
        print(f"  - BM25: {len(bm25_results)} results")
        
        # 通道3: 时间范围检索 (仅当查询提及时间)
        if any(t in query.lower() for t in ["recent", "last", "ago", "yesterday"]):
            temporal_results = self.temporal_retriever.retrieve(
                query, user_id, 
                days=self.config.temporal_days,
                top_k=self.config.temporal_top_k
            )
            results_by_channel["temporal"] = temporal_results
            print(f"  - Temporal: {len(temporal_results)} results")
        
        # ========== 阶段2: 结果融合 ==========
        print("[Retrieve] Phase 2: Fusing results...")
        
        if isinstance(self.fusion, AdaptiveFusion):
            fused = self.fusion.fuse(query, results_by_channel)
        else:
            fused = self.fusion.fuse(results_by_channel)
        
        fused = fused[:self.config.fusion_top_k]
        print(f"  - Fused: {len(fused)} results")
        
        # ========== 阶段3: 精排优化 ==========
        if self.reranker:
            print("[Retrieve] Phase 3: Reranking...")
            reranked = self.reranker.rerank(
                query, fused, top_k=self.config.rerank_top_k
            )
            print(f"  - Reranked: {len(reranked)} results")
        else:
            reranked = fused[:self.config.rerank_top_k]
        
        # ========== 阶段4: 时间加权 ==========
        if self.config.enable_decay:
            print("[Retrieve] Phase 4: Applying temporal decay...")
            final = self._apply_temporal_weighting(reranked)
        else:
            final = reranked
        
        # 更新访问统计
        self._update_access_stats([r.memory_id for r in final])
        
        print(f"[Retrieve] Done. Returning {len(final)} memories.")
        return final
    
    def _apply_temporal_weighting(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        应用时间衰减加权
        
        公式: final_score = base_score * decay_factor + recency_boost
        """
        now = datetime.now()
        half_life = self.config.decay_half_life_days
        
        for r in results:
            # 获取创建时间
            created_at = r.metadata.get("created_at", now)
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            # 计算年龄
            age_days = (now - created_at).days
            
            # 指数衰减
            decay = np.exp(-0.693 * age_days / half_life)
            
            # 应用衰减
            r.score = r.score * decay
            
            # 访问频率提升
            access_count = r.metadata.get("access_count", 0)
            r.score += min(access_count * self.config.recency_boost, 0.2)
        
        # 重新排序
        return sorted(results, key=lambda x: x.score, reverse=True)
    
    def _update_access_stats(self, memory_ids: List[str]):
        """更新记忆访问统计"""
        # 实际应更新数据库
        pass

# ============ 便捷函数 ============

def quick_retrieve(query: str, user_id: str, top_k: int = 5) -> List[str]:
    """
    快速检索 - 返回记忆内容列表
    """
    # 简化调用
    retriever = HybridRetriever(
        vector_store=None,  # 实际传入
        text_index=None,
        embedding_model=None,
        llm_client=None
    )
    
    results = retriever.retrieve(query, user_id)
    return [r.content for r in results[:top_k]]

def retrieve_with_sources(query: str, user_id: str) -> List[Dict]:
    """
    带来源信息的检索 - 用于调试
    """
    retriever = HybridRetriever(
        vector_store=None,
        text_index=None,
        embedding_model=None,
        llm_client=None
    )
    
    results = retriever.retrieve(query, user_id)
    
    return [
        {
            "content": r.content,
            "score": r.score,
            "source": r.source,
            "created_at": r.metadata.get("created_at"),
            "access_count": r.metadata.get("access_count", 0)
        }
        for r in results
    ]
```

---

## 性能优化策略

### 1. 预过滤
```python
# 在向量搜索前先用metadata过滤
results = vector_store.search(
    vector=query_embedding,
    filter={
        "user_id": user_id,           # 用户隔离
        "category": {"$in": ["preference", "goal"]},  # 类别过滤
        "created_at": {"$gt": cutoff_date}           # 时间过滤
    },
    top_k=20
)
```

### 2. 缓存
```python
# 查询缓存 (相同查询直接返回)
@lru_cache(maxsize=1000)
def cached_retrieve(query_hash: str, user_id: str):
    return retrieve(query_hash, user_id)
```

### 3. 异步并行
```python
async def retrieve_parallel(query: str, user_id: str):
    # 并行执行向量+BM25检索
    vector_task = asyncio.create_task(
        vector_retriever.retrieve(query, user_id)
    )
    bm25_task = asyncio.create_task(
        bm25_retriever.retrieve(query, user_id)
    )
    
    vector_results, bm25_results = await asyncio.gather(
        vector_task, bm25_task
    )
    
    return merge_results(vector_results, bm25_results)
```

---

## 下一步

检索结果进入**注入层** → 决定如何将记忆注入LLM上下文窗口。