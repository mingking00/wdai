"""
代码实体重要性评分系统
基于代码结构和依赖关系评估实体重要性

功能：
1. 计算代码实体的重要性分数
2. 识别核心类和关键函数
3. 支持依赖关系分析
4. 生成代码热点图
"""

import json
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math


@dataclass
class EntityImportance:
    """实体重要性评分"""
    entity_id: str
    entity_name: str
    entity_type: str
    
    # 基础指标
    incoming_refs: int = 0  # 被引用次数
    outgoing_refs: int = 0  # 引用其他次数
    
    # 计算指标
    centrality_score: float = 0.0  # 中心性分数
    dependency_depth: int = 0      # 依赖深度
    
    # 综合重要性 (0-100)
    importance_score: float = 0.0
    
    # 重要性等级
    importance_level: str = "normal"  # critical/high/medium/low/normal


class CodeEntityScorer:
    """
    代码实体重要性评分器
    
    算法：
    1. PageRank-like centrality (基于引用关系)
    2. 依赖深度分析 (核心实体通常依赖更少)
    3. 实体类型加权 (class > method > function)
    """
    
    def __init__(self):
        # 类型权重
        self.type_weights = {
            "class": 2.0,
            "method": 1.5,
            "function": 1.0,
            "import": 0.5,
            "variable": 0.3
        }
        
        # 重要性阈值
        self.importance_thresholds = {
            "critical": 80,
            "high": 60,
            "medium": 40,
            "low": 20,
            "normal": 0
        }
    
    def calculate_importance(self, code_graph: Dict) -> Dict[str, EntityImportance]:
        """
        计算所有实体的重要性
        
        Args:
            code_graph: 代码图谱数据
            
        Returns:
            实体重要性映射
        """
        entities = code_graph.get("entities", {})
        relations = code_graph.get("relations", {})
        
        # 构建引用图
        ref_graph = self._build_reference_graph(entities, relations)
        
        # 计算中心性 (PageRank简化版)
        centrality = self._calculate_centrality(ref_graph)
        
        # 计算依赖深度
        dependency_depths = self._calculate_dependency_depths(ref_graph)
        
        # 生成重要性评分
        importance_map = {}
        
        for entity_id, entity in entities.items():
            # 获取引用统计
            incoming = len(ref_graph.get("incoming", {}).get(entity_id, []))
            outgoing = len(ref_graph.get("outgoing", {}).get(entity_id, []))
            
            # 获取中心性和深度
            cent_score = centrality.get(entity_id, 0)
            depth = dependency_depths.get(entity_id, 0)
            
            # 类型权重
            type_weight = self.type_weights.get(entity.get("entity_type", ""), 1.0)
            
            # 计算综合重要性
            # 公式: (centrality * 40 + incoming_refs * 30 + type_weight * 20 + (10-depth) * 10)
            importance = (
                cent_score * 40 +
                min(incoming, 10) * 3 * 30 +  # 限制incoming上限
                type_weight * 20 +
                max(0, 10 - depth) * 10
            )
            
            # 归一化到0-100
            importance = min(100, importance)
            
            # 确定重要性等级
            level = self._get_importance_level(importance)
            
            importance_map[entity_id] = EntityImportance(
                entity_id=entity_id,
                entity_name=entity.get("name", ""),
                entity_type=entity.get("entity_type", ""),
                incoming_refs=incoming,
                outgoing_refs=outgoing,
                centrality_score=cent_score,
                dependency_depth=depth,
                importance_score=importance,
                importance_level=level
            )
        
        return importance_map
    
    def _build_reference_graph(self, entities: Dict, relations: Dict) -> Dict:
        """构建引用图"""
        graph = {
            "incoming": defaultdict(list),  # 被谁引用
            "outgoing": defaultdict(list)   # 引用了谁
        }
        
        for rel_id, rel in relations.items():
            source = rel.get("source_id")
            target = rel.get("target_id")
            rel_type = rel.get("relation_type", "")
            
            # 只考虑引用关系
            if rel_type in ["calls", "uses", "decorates", "inherits"]:
                if source and target:
                    graph["outgoing"][source].append(target)
                    graph["incoming"][target].append(source)
        
        return graph
    
    def _calculate_centrality(self, ref_graph: Dict, iterations: int = 10) -> Dict[str, float]:
        """
        计算中心性 (简化版PageRank)
        """
        incoming = ref_graph.get("incoming", {})
        outgoing = ref_graph.get("outgoing", {})
        
        # 获取所有节点
        all_nodes = set(incoming.keys()) | set(outgoing.keys())
        
        # 初始化分数
        scores = {node: 1.0 for node in all_nodes}
        
        # 迭代计算
        for _ in range(iterations):
            new_scores = {}
            for node in all_nodes:
                # 获取引用该节点的节点
                refs = incoming.get(node, [])
                
                # 计算新分数
                score = 0.15  # 阻尼系数
                for ref in refs:
                    ref_outgoing = len(outgoing.get(ref, []))
                    if ref_outgoing > 0:
                        score += 0.85 * scores[ref] / ref_outgoing
                
                new_scores[node] = score
            
            scores = new_scores
        
        # 归一化
        max_score = max(scores.values()) if scores else 1
        return {k: v / max_score for k, v in scores.items()}
    
    def _calculate_dependency_depths(self, ref_graph: Dict) -> Dict[str, int]:
        """计算依赖深度"""
        outgoing = ref_graph.get("outgoing", {})
        depths = {}
        
        def get_depth(node: str, visited: Set[str]) -> int:
            if node in depths:
                return depths[node]
            if node in visited:
                return 0  # 循环依赖
            
            visited.add(node)
            deps = outgoing.get(node, [])
            
            if not deps:
                depths[node] = 0
            else:
                max_dep_depth = max(get_depth(d, visited) for d in deps)
                depths[node] = max_dep_depth + 1
            
            return depths[node]
        
        for node in outgoing:
            get_depth(node, set())
        
        return depths
    
    def _get_importance_level(self, score: float) -> str:
        """获取重要性等级"""
        for level, threshold in sorted(self.importance_thresholds.items(), 
                                       key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return level
        return "normal"
    
    def get_critical_entities(self, importance_map: Dict[str, EntityImportance],
                             min_level: str = "high") -> List[EntityImportance]:
        """获取关键实体"""
        level_order = ["critical", "high", "medium", "low", "normal"]
        min_index = level_order.index(min_level)
        
        critical = []
        for entity in importance_map.values():
            if level_order.index(entity.importance_level) <= min_index:
                critical.append(entity)
        
        # 按重要性排序
        critical.sort(key=lambda x: x.importance_score, reverse=True)
        return critical
    
    def generate_report(self, importance_map: Dict[str, EntityImportance]) -> Dict:
        """生成重要性分析报告"""
        total = len(importance_map)
        if total == 0:
            return {"message": "No entities to analyze"}
        
        # 等级分布
        level_dist = defaultdict(int)
        for entity in importance_map.values():
            level_dist[entity.importance_level] += 1
        
        # 类型分布
        type_dist = defaultdict(list)
        for entity in importance_map.values():
            type_dist[entity.entity_type].append(entity)
        
        # Top实体
        top_entities = sorted(importance_map.values(), 
                            key=lambda x: x.importance_score, 
                            reverse=True)[:10]
        
        report = {
            "total_entities": total,
            "importance_distribution": dict(level_dist),
            "top_entities": [
                {
                    "name": e.entity_name,
                    "type": e.entity_type,
                    "score": round(e.importance_score, 2),
                    "level": e.importance_level,
                    "refs": e.incoming_refs
                }
                for e in top_entities
            ],
            "type_stats": {
                t: {
                    "count": len(entities),
                    "avg_importance": sum(e.importance_score for e in entities) / len(entities)
                }
                for t, entities in type_dist.items()
            }
        }
        
        return report


# 便捷函数
def analyze_code_importance(code_graph_path: str = "ier_kg/code_graph.json") -> Dict:
    """分析代码重要性"""
    try:
        with open(code_graph_path, 'r') as f:
            code_graph = json.load(f)
        
        scorer = CodeEntityScorer()
        importance_map = scorer.calculate_importance(code_graph)
        report = scorer.generate_report(importance_map)
        
        return report
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # 测试
    report = analyze_code_importance()
    print(json.dumps(report, indent=2))
