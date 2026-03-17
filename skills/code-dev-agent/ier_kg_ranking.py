"""
IER-KG 多跳检索置信度排序系统
基于多维度信号计算检索结果置信度

功能：
1. 多跳路径置信度计算
2. 语义相似度评分
3. 经验质量评分
4. 综合置信度排序
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class RetrievalResult:
    """检索结果"""
    exp_id: str
    exp_name: str
    
    # 基础分数
    graph_score: float = 0.0        # 图谱匹配分数
    vector_score: float = 0.0       # 向量相似度分数
    
    # 路径信息
    hop_count: int = 0              # 跳数
    path: List[str] = None          # 检索路径
    path_strength: float = 0.0      # 路径强度
    
    # 经验质量
    exp_quality: float = 0.0        # 经验质量分
    usage_count: int = 0            # 使用次数
    success_rate: float = 0.0       # 成功率
    
    # 综合置信度
    confidence: float = 0.0         # 最终置信度 (0-1)
    confidence_level: str = "low"   # high/medium/low
    
    # 排序因子
    rank_factors: Dict = None       # 各因子得分详情


class ConfidenceCalculator:
    """
    置信度计算器
    
    基于多维度信号计算最终置信度
    """
    
    def __init__(self):
        # 权重配置
        self.weights = {
            "graph_match": 0.25,      # 图谱匹配
            "vector_similarity": 0.25, # 向量相似度
            "path_quality": 0.20,      # 路径质量
            "exp_quality": 0.15,       # 经验质量
            "usage_signal": 0.15       # 使用信号
        }
        
        # 跳数衰减因子
        self.hop_decay = {
            0: 1.0,    # 直接匹配
            1: 0.9,    # 1跳
            2: 0.75,   # 2跳
            3: 0.55    # 3跳+
        }
    
    def calculate_confidence(self, result: RetrievalResult) -> float:
        """
        计算综合置信度
        
        公式:
        confidence = Σ(weight_i * score_i) * hop_decay
        """
        # 基础分数（已归一化到0-1）
        graph_score = min(1.0, result.graph_score)
        vector_score = min(1.0, result.vector_score)
        
        # 路径质量分数
        path_score = self._calculate_path_score(result)
        
        # 经验质量分数
        quality_score = self._calculate_quality_score(result)
        
        # 使用信号分数
        usage_score = self._calculate_usage_score(result)
        
        # 加权求和
        weighted_sum = (
            self.weights["graph_match"] * graph_score +
            self.weights["vector_similarity"] * vector_score +
            self.weights["path_quality"] * path_score +
            self.weights["exp_quality"] * quality_score +
            self.weights["usage_signal"] * usage_score
        )
        
        # 应用跳数衰减
        hop_factor = self.hop_decay.get(result.hop_count, 0.5)
        confidence = weighted_sum * hop_factor
        
        # 记录排序因子
        result.rank_factors = {
            "graph_match": round(graph_score, 3),
            "vector_similarity": round(vector_score, 3),
            "path_quality": round(path_score, 3),
            "exp_quality": round(quality_score, 3),
            "usage_signal": round(usage_score, 3),
            "hop_factor": hop_factor,
            "weighted_sum": round(weighted_sum, 3)
        }
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_path_score(self, result: RetrievalResult) -> float:
        """计算路径质量分数"""
        if result.hop_count == 0:
            return 1.0  # 直接匹配
        
        # 基于路径强度
        base_score = result.path_strength
        
        # 路径长度惩罚
        length_penalty = 1.0 - (result.hop_count * 0.15)
        
        return base_score * length_penalty
    
    def _calculate_quality_score(self, result: RetrievalResult) -> float:
        """计算经验质量分数"""
        score = result.exp_quality
        
        # 成功率加成
        if result.success_rate > 0:
            score = score * 0.7 + result.success_rate * 0.3
        
        return min(1.0, score)
    
    def _calculate_usage_score(self, result: RetrievalResult) -> float:
        """计算使用信号分数"""
        if result.usage_count == 0:
            return 0.5  # 中性分数
        
        # 使用次数越多，分数越高（但有上限）
        # 使用对数压缩
        usage_score = min(1.0, math.log10(result.usage_count + 1) / 2)
        
        return usage_score
    
    def get_confidence_level(self, confidence: float) -> str:
        """获取置信度等级"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"


class MultiHopRanker:
    """
    多跳检索结果排序器
    
    整合多种信号，生成排序后的检索结果
    """
    
    def __init__(self, usage_tracker=None):
        self.confidence_calc = ConfidenceCalculator()
        self.usage_tracker = usage_tracker
    
    def rank_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        对检索结果进行排序
        
        步骤：
        1. 计算每条结果的置信度
        2. 按置信度排序
        3. 添加置信度等级
        """
        # 计算置信度
        for result in results:
            result.confidence = self.confidence_calc.calculate_confidence(result)
            result.confidence_level = self.confidence_calc.get_confidence_level(
                result.confidence
            )
        
        # 排序：置信度降序，跳数升序
        results.sort(key=lambda x: (-x.confidence, x.hop_count))
        
        return results
    
    def filter_by_confidence(self, results: List[RetrievalResult],
                            min_confidence: float = 0.5) -> List[RetrievalResult]:
        """按置信度过滤结果"""
        return [r for r in results if r.confidence >= min_confidence]
    
    def diversify_results(self, results: List[RetrievalResult],
                         max_per_level: int = 3) -> List[RetrievalResult]:
        """
        结果多样化
        
        确保不同置信度等级的结果都有代表
        """
        diversified = []
        level_counts = defaultdict(int)
        
        for result in results:
            level = result.confidence_level
            if level_counts[level] < max_per_level:
                diversified.append(result)
                level_counts[level] += 1
        
        # 如果数量不足，补充剩余结果
        if len(diversified) < 10:
            existing_ids = {r.exp_id for r in diversified}
            for result in results:
                if result.exp_id not in existing_ids:
                    diversified.append(result)
                    if len(diversified) >= 10:
                        break
        
        return diversified
    
    def create_result_from_kg(self, kg_result: Dict, 
                             vector_score: float = 0.0) -> RetrievalResult:
        """
        从KG检索结果创建RetrievalResult
        
        Args:
            kg_result: KG检索结果字典
            vector_score: 向量相似度分数
        """
        exp = kg_result.get("experience", {})
        exp_id = getattr(exp, 'id', '')
        exp_name = getattr(exp, 'name', 'Unknown')
        
        # 获取使用统计
        usage_count = 0
        success_rate = 0.0
        if self.usage_tracker:
            metrics = self.usage_tracker.get_metrics(exp_id)
            if metrics:
                usage_count = metrics.total_accesses
                # 简化成功率计算
                success_rate = min(1.0, usage_count / 10)
        
        result = RetrievalResult(
            exp_id=exp_id,
            exp_name=exp_name,
            graph_score=kg_result.get("relevance_score", 0),
            vector_score=vector_score,
            hop_count=kg_result.get("hop", 0),
            path=kg_result.get("path", []),
            path_strength=1.0 - (kg_result.get("hop", 0) * 0.1),
            exp_quality=getattr(exp, 'quality_score', 0.5),
            usage_count=usage_count,
            success_rate=success_rate
        )
        
        return result
    
    def merge_and_rank(self, 
                      kg_results: List[Dict],
                      vector_results: List[Tuple[str, float]],
                      top_k: int = 10) -> List[RetrievalResult]:
        """
        合并并排序KG和向量检索结果
        
        Args:
            kg_results: 图谱检索结果
            vector_results: 向量检索结果 [(exp_id, score), ...]
            top_k: 返回数量
            
        Returns:
            排序后的RetrievalResult列表
        """
        # 构建向量结果字典
        vector_dict = {exp_id: score for exp_id, score in vector_results}
        
        # 合并结果
        merged_results = []
        processed_ids = set()
        
        # 处理KG结果
        for kg_result in kg_results:
            exp_id = getattr(kg_result.get("experience"), 'id', '')
            if exp_id in processed_ids:
                continue
            
            vector_score = vector_dict.get(exp_id, 0.0)
            result = self.create_result_from_kg(kg_result, vector_score)
            merged_results.append(result)
            processed_ids.add(exp_id)
        
        # 添加仅向量检索到的结果
        for exp_id, score in vector_results:
            if exp_id not in processed_ids:
                result = RetrievalResult(
                    exp_id=exp_id,
                    exp_name=exp_id,  # 临时名称
                    graph_score=0.0,
                    vector_score=score,
                    hop_count=0,
                    path=[],
                    path_strength=0.5
                )
                merged_results.append(result)
        
        # 计算置信度并排序
        ranked = self.rank_results(merged_results)
        
        # 多样化
        diversified = self.diversify_results(ranked)
        
        return diversified[:top_k]
    
    def explain_ranking(self, result: RetrievalResult) -> str:
        """解释排序原因"""
        if not result.rank_factors:
            return "暂无排序解释"
        
        factors = result.rank_factors
        lines = [
            f"【{result.exp_name}】置信度分析",
            f"综合置信度: {result.confidence:.2f} ({result.confidence_level})",
            "",
            "排序因子:",
            f"  • 图谱匹配: {factors['graph_match']:.3f} (权重25%)",
            f"  • 向量相似: {factors['vector_similarity']:.3f} (权重25%)",
            f"  • 路径质量: {factors['path_quality']:.3f} (权重20%)",
            f"  • 经验质量: {factors['exp_quality']:.3f} (权重15%)",
            f"  • 使用信号: {factors['usage_signal']:.3f} (权重15%)",
            f"  • 跳数衰减: {factors['hop_factor']:.2f}",
            "",
            f"加权总分: {factors['weighted_sum']:.3f}",
        ]
        
        if result.hop_count > 0:
            lines.append(f"检索路径: {' → '.join(result.path)}")
        
        return "\n".join(lines)


class RankingReportGenerator:
    """排序报告生成器"""
    
    def generate_report(self, results: List[RetrievalResult]) -> Dict:
        """生成排序统计报告"""
        if not results:
            return {"message": "无检索结果"}
        
        total = len(results)
        
        # 置信度分布
        conf_dist = {"high": 0, "medium": 0, "low": 0}
        for r in results:
            conf_dist[r.confidence_level] += 1
        
        # 跳数分布
        hop_dist = defaultdict(int)
        for r in results:
            hop_dist[r.hop_count] += 1
        
        # 来源分布
        source_dist = {"graph_only": 0, "vector_only": 0, "hybrid": 0}
        for r in results:
            if r.graph_score > 0 and r.vector_score > 0:
                source_dist["hybrid"] += 1
            elif r.graph_score > 0:
                source_dist["graph_only"] += 1
            else:
                source_dist["vector_only"] += 1
        
        # 平均置信度
        avg_confidence = sum(r.confidence for r in results) / total
        
        return {
            "total_results": total,
            "avg_confidence": round(avg_confidence, 3),
            "confidence_distribution": conf_dist,
            "hop_distribution": dict(hop_dist),
            "source_distribution": source_dist,
            "top_results": [
                {
                    "name": r.exp_name[:30],
                    "confidence": round(r.confidence, 3),
                    "level": r.confidence_level,
                    "hop": r.hop_count
                }
                for r in results[:5]
            ]
        }


# 便捷函数
def rank_retrieval_results(results: List[Dict], 
                          usage_tracker=None) -> List[RetrievalResult]:
    """便捷函数：排序检索结果"""
    ranker = MultiHopRanker(usage_tracker)
    
    retrieval_results = []
    for r in results:
        rr = ranker.create_result_from_kg(r)
        retrieval_results.append(rr)
    
    return ranker.rank_results(retrieval_results)


if __name__ == "__main__":
    # 测试
    results = [
        RetrievalResult(
            exp_id="exp_1",
            exp_name="装饰器模式",
            graph_score=0.9,
            vector_score=0.85,
            hop_count=0,
            exp_quality=0.8,
            usage_count=5
        ),
        RetrievalResult(
            exp_id="exp_2",
            exp_name="缓存优化",
            graph_score=0.7,
            vector_score=0.6,
            hop_count=1,
            path=["装饰器模式", "lru_cache"],
            exp_quality=0.7,
            usage_count=3
        ),
        RetrievalResult(
            exp_id="exp_3",
            exp_name="工厂模式",
            graph_score=0.5,
            vector_score=0.4,
            hop_count=2,
            path=["装饰器模式", "设计模式", "工厂模式"],
            exp_quality=0.6,
            usage_count=1
        )
    ]
    
    ranker = MultiHopRanker()
    ranked = ranker.rank_results(results)
    
    print("排序结果:")
    for r in ranked:
        print(f"  {r.exp_name}: {r.confidence:.3f} ({r.confidence_level})")
