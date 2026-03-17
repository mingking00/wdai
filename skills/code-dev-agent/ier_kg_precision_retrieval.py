"""
IER-KG 精准检索策略
从"批量dump"转向"精准狙击"

原则：
- 只返回最相关的 3-5 条经验
- 区分"核心经验"和"参考经验"
- 多跳限制在 2 跳内
- 每次检索附带置信度分数
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """检索结果"""
    exp_id: str
    exp_name: str
    relevance_score: float  # 0-1
    confidence_level: str   # high/medium/low
    hop_count: int
    is_core: bool          # 是否是核心经验
    source: str            # ier/kg/vector


class PrecisionRetriever:
    """精准检索器"""
    
    def __init__(self, adapter):
        self.adapter = adapter
        
        # 检索配置
        self.config = {
            "max_results": 5,          # 最多5条
            "max_hops": 2,             # 最多2跳
            "core_threshold": 0.8,     # 0.8以上为核心
            "min_confidence": 0.5,     # 最低置信度
        }
    
    def retrieve(self, query: str, context: str = "") -> List[RetrievalResult]:
        """
        精准检索
        
        策略：
        1. 直接匹配（IER标签匹配）
        2. 向量语义匹配（Top-3）
        3. 图谱多跳（限制2跳）
        4. 按置信度排序，取Top-5
        5. 标记核心经验
        """
        results = []
        seen_ids = set()
        
        # 1. IER直接匹配（最高优先级）
        ier_results = self._retrieve_ier(query)
        for r in ier_results:
            if r.exp_id not in seen_ids and r.relevance_score >= self.config["min_confidence"]:
                results.append(r)
                seen_ids.add(r.exp_id)
        
        # 2. 向量匹配（语义相似）
        if len(results) < self.config["max_results"]:
            vector_results = self._retrieve_vector(query)
            for r in vector_results:
                if r.exp_id not in seen_ids and len(results) < self.config["max_results"]:
                    results.append(r)
                    seen_ids.add(r.exp_id)
        
        # 3. 图谱多跳（间接关联）
        if len(results) < self.config["max_results"]:
            kg_results = self._retrieve_kg(query, context)
            for r in kg_results:
                if r.exp_id not in seen_ids and len(results) < self.config["max_results"]:
                    if r.hop_count <= self.config["max_hops"]:
                        results.append(r)
                        seen_ids.add(r.exp_id)
        
        # 排序并标记核心
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        for r in results:
            r.is_core = r.relevance_score >= self.config["core_threshold"]
        
        return results[:self.config["max_results"]]
    
    def _retrieve_ier(self, query: str) -> List[RetrievalResult]:
        """IER直接匹配"""
        # 简化的标签匹配
        results = []
        if not self.adapter or not self.adapter.ier_manager:
            return results
        
        keywords = self._extract_keywords(query)
        
        for exp_id, exp in self.adapter.ier_manager.experiences.items():
            score = self._calculate_match_score(exp, keywords)
            if score > 0.5:
                results.append(RetrievalResult(
                    exp_id=exp_id,
                    exp_name=exp.name,
                    relevance_score=score,
                    confidence_level="high" if score > 0.8 else "medium",
                    hop_count=0,
                    is_core=False,
                    source="ier"
                ))
        
        return results
    
    def _retrieve_vector(self, query: str) -> List[RetrievalResult]:
        """向量语义匹配"""
        results = []
        if not self.adapter or not self.adapter.vector_retrieval:
            return results
        
        vector_results = self.adapter.vector_retrieval.search(query, top_k=3)
        
        for exp_id, sim in vector_results:
            results.append(RetrievalResult(
                exp_id=exp_id,
                exp_name=exp_id,  # 简化
                relevance_score=sim,
                confidence_level="high" if sim > 0.8 else "medium",
                hop_count=0,
                is_core=False,
                source="vector"
            ))
        
        return results
    
    def _retrieve_kg(self, query: str, context: str) -> List[RetrievalResult]:
        """图谱多跳检索"""
        results = []
        if not self.adapter or not self.adapter.kg_system:
            return results
        
        kg_results = self.adapter.kg_system.retrieve_experiences(
            query=query,
            code_context=context,
            max_hops=self.config["max_hops"],
            top_k=5
        )
        
        for r in kg_results:
            exp = r.get("experience", {})
            exp_id = getattr(exp, 'id', '')
            score = r.get("relevance_score", 0)
            hop = r.get("hop", 0)
            
            # 跳数衰减
            hop_penalty = hop * 0.15
            adjusted_score = score * (1 - hop_penalty)
            
            results.append(RetrievalResult(
                exp_id=exp_id,
                exp_name=getattr(exp, 'name', ''),
                relevance_score=adjusted_score,
                confidence_level="high" if adjusted_score > 0.7 else "medium",
                hop_count=hop,
                is_core=False,
                source="kg"
            ))
        
        return results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 简单分词，实际可用更复杂的NLP
        words = query.lower().split()
        # 过滤停用词
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', '如何', '怎么', '一个', '这个'}
        return [w for w in words if w not in stopwords and len(w) > 2]
    
    def _calculate_match_score(self, exp, keywords: List[str]) -> float:
        """计算匹配分数"""
        if not keywords:
            return 0.0
        
        text = f"{exp.name} {exp.description} {' '.join(getattr(exp, 'tags', []))}"
        text = text.lower()
        
        matches = sum(1 for kw in keywords if kw in text)
        return matches / len(keywords)
    
    def format_for_prompt(self, results: List[RetrievalResult]) -> str:
        """格式化为Prompt可用的字符串"""
        if not results:
            return ""
        
        lines = ["### 相关经验参考", ""]
        
        core_results = [r for r in results if r.is_core]
        ref_results = [r for r in results if not r.is_core]
        
        if core_results:
            lines.append("**核心经验**:")
            for r in core_results:
                hop_info = f" [via {r.hop_count}跳]" if r.hop_count > 0 else ""
                lines.append(f"- {r.exp_name} ({r.confidence_level}){hop_info}")
            lines.append("")
        
        if ref_results:
            lines.append("**参考资料**:")
            for r in ref_results:
                hop_info = f" [via {r.hop_count}跳]" if r.hop_count > 0 else ""
                lines.append(f"- {r.exp_name}{hop_info}")
            lines.append("")
        
        return "\n".join(lines)


# 便捷函数
def create_precision_retriever(adapter):
    """创建精准检索器"""
    return PrecisionRetriever(adapter)
