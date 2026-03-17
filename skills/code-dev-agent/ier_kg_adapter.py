#!/usr/bin/env python3
"""
IER-KG Integration Adapter
IER知识图谱集成适配器

将新的知识图谱系统与现有IER系统集成
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json

# 导入原始IER系统
from ier_system import (
    ExperienceManager, Experience, ExperienceType, 
    TaskRecord, ExperienceStatus
)

# 导入知识图谱系统
from ier_kg_system import (
    IERKnowledgeGraphSystem, ExperienceEntityType, 
    ExperienceRelationType, CodeEntity, CodeRelation
)

# 导入去重系统
from ier_kg_deduplication import IERKGDeduplicationService, create_deduplicator

# 导入使用频率追踪系统
from ier_kg_usage_tracker import ExperienceUsageTracker, get_usage_tracker

# 导入代码实体评分系统
from ier_kg_entity_scorer import CodeEntityScorer, analyze_code_importance

# 导入向量检索系统
from ier_kg_vector_retrieval import VectorRetrievalSystem, create_vector_retrieval

# 导入经验摘要系统
from ier_kg_summarizer import ExperienceSummarizer, BatchSummarizer, summarize_experience

# 导入置信度排序系统
from ier_kg_ranking import MultiHopRanker, RetrievalResult, rank_retrieval_results

class IERKGIntegrationAdapter:
    """
    IER-KG集成适配器
    桥接传统IER系统和知识图谱增强系统
    """
    
    def __init__(self, use_kg: bool = True):
        """
        初始化适配器
        
        Args:
            use_kg: 是否启用知识图谱增强
        """
        self.use_kg = use_kg
        
        # 原始IER管理器
        self.ier_manager = ExperienceManager()
        
        # 知识图谱系统（可选）
        self.kg_system = None
        if use_kg:
            try:
                self.kg_system = IERKnowledgeGraphSystem(use_neo4j=False)
                print("[IER-KG Adapter] Knowledge graph system initialized")
            except Exception as e:
                print(f"[IER-KG Adapter] KG init failed: {e}, falling back to basic IER")
                self.use_kg = False
        
        # 去重服务
        self.dedup_service = None
        if use_kg and self.kg_system:
            try:
                self.dedup_service = IERKGDeduplicationService(self)
                print("[IER-KG Adapter] Deduplication service initialized")
            except Exception as e:
                print(f"[IER-KG Adapter] Deduplication init failed: {e}")
        
        # 使用频率追踪服务
        self.usage_tracker = None
        try:
            self.usage_tracker = get_usage_tracker(".")
            print("[IER-KG Adapter] Usage tracker initialized")
        except Exception as e:
            print(f"[IER-KG Adapter] Usage tracker init failed: {e}")
        
        # 向量检索服务
        self.vector_retrieval = None
        try:
            self.vector_retrieval = create_vector_retrieval(".")
            print("[IER-KG Adapter] Vector retrieval initialized")
        except Exception as e:
            print(f"[IER-KG Adapter] Vector retrieval init failed: {e}")
        
        # 经验摘要服务
        self.summarizer = None
        try:
            self.summarizer = ExperienceSummarizer()
            print("[IER-KG Adapter] Summarizer initialized")
        except Exception as e:
            print(f"[IER-KG Adapter] Summarizer init failed: {e}")
        
        # 置信度排序服务
        self.ranker = None
        try:
            self.ranker = MultiHopRanker(self.usage_tracker)
            print("[IER-KG Adapter] Ranker initialized")
        except Exception as e:
            print(f"[IER-KG Adapter] Ranker init failed: {e}")
    
    # ==================== 经验类型映射 ====================
    
    EXP_TYPE_MAPPING = {
        # IER -> KG
        ExperienceType.SHORTCUT: ExperienceEntityType.SHORTCUT,
        ExperienceType.PATTERN: ExperienceEntityType.PATTERN,
        ExperienceType.ANTI_PATTERN: ExperienceEntityType.ANTI_PATTERN,
        ExperienceType.TOOL: ExperienceEntityType.TOOL,
        ExperienceType.LESSON: ExperienceEntityType.LESSON,
        ExperienceType.OPTIMIZATION: ExperienceEntityType.OPTIMIZATION,
    }
    
    EXP_TYPE_REVERSE_MAPPING = {v: k for k, v in EXP_TYPE_MAPPING.items()}
    
    def _convert_exp_type_to_kg(self, ier_type: ExperienceType) -> ExperienceEntityType:
        """将IER经验类型转换为KG类型"""
        return self.EXP_TYPE_MAPPING.get(ier_type, ExperienceEntityType.PATTERN)
    
    def _convert_exp_type_from_kg(self, kg_type: ExperienceEntityType) -> ExperienceType:
        """将KG经验类型转换为IER类型"""
        return self.EXP_TYPE_REVERSE_MAPPING.get(kg_type, ExperienceType.PATTERN)
    
    # ==================== 增强的经验获取 ====================
    
    def acquire_experience(self, task_id: str, task_description: str,
                          chain_result: Dict, code_output: str,
                          file_path: str = "generated.py") -> Dict[str, Any]:
        """
        增强的经验获取 - 同时更新IER和KG
        
        Returns:
            包含IER经验和KG经验信息的字典
        """
        # 1. 使用原始IER系统提取经验
        ier_experiences = self.ier_manager.acquire_from_task(
            task_id, task_description, chain_result, code_output
        )
        
        result = {
            "ier_experiences": ier_experiences,
            "kg_experiences": [],
            "code_entities": [],
            "relations": []
        }
        
        # 2. 如果使用KG，提取代码实体并创建图谱经验
        if self.use_kg and self.kg_system:
            # 提取代码实体
            entities, relations = self.kg_system.extract_and_index_code(
                code_output, file_path, task_id
            )
            result["code_entities"] = entities
            result["relations"] = relations
            
            # 将IER经验转换为KG经验（带溯源）
            for ier_exp in ier_experiences:
                # 检查是否重复
                if self.dedup_service:
                    should_add, dup_id, sim_score = self.dedup_service.check_before_add({
                        'name': ier_exp.name,
                        'description': ier_exp.description,
                        'context': ier_exp.context,
                        'tags': ier_exp.tags
                    })
                    if not should_add:
                        print(f"[IER-KG Deduplication] Skipping duplicate: {ier_exp.name} "
                              f"(similarity: {sim_score:.2f}, matches: {dup_id})")
                        continue
                
                kg_exp_data = self._create_kg_experience_from_ier(
                    ier_exp, task_id, file_path, code_output, entities
                )
                result["kg_experiences"].append(kg_exp_data)
        
        return result
    
    def _create_kg_experience_from_ier(self, ier_exp: Experience, task_id: str,
                                       file_path: str, source_code: str,
                                       code_entities: List[CodeEntity]) -> Dict:
        """从IER经验创建KG经验"""
        kg_type = self._convert_exp_type_to_kg(ier_exp.exp_type)
        
        return self.kg_system.create_experience_with_provenance(
            exp_type=kg_type,
            name=ier_exp.name,
            description=ier_exp.description,
            context=ier_exp.context,
            solution=ier_exp.solution,
            code_example=ier_exp.code_example,
            task_id=task_id,
            file_path=file_path,
            source_code=source_code,
            tags=ier_exp.tags
        )
    
    # ==================== 增强的经验检索 ====================
    
    def retrieve_for_task(self, task_description: str, 
                         code_context: Optional[str] = None,
                         language: str = "python",
                         max_hops: int = 2) -> Dict[str, Any]:
        """
        增强的经验检索 - 结合IER标签匹配和KG多跳检索
        
        Returns:
            融合后的经验列表
        """
        # 1. 原始IER检索（基于标签）
        ier_results = self.ier_manager.retrieve_relevant_experiences(task_description, language)
        
        # 2. KG多跳检索
        kg_results = []
        if self.use_kg and self.kg_system:
            kg_results = self.kg_system.retrieve_experiences(
                query=task_description,
                code_context=code_context,
                max_hops=max_hops,
                top_k=10
            )
        
        # 3. 融合结果
        return self._merge_retrieval_results(ier_results, kg_results)
    
    def _merge_retrieval_results(self, ier_results: List[Experience],
                                  kg_results: List[Dict]) -> Dict[str, Any]:
        """
        融合IER和KG的检索结果
        
        策略：
        1. IER结果作为基础（高置信度）
        2. KG结果补充（特别是多跳发现的间接经验）
        3. 去重并按综合分数排序
        """
        merged = []
        seen_ids = set()
        
        # 添加IER结果
        for exp in ier_results:
            merged.append({
                "source": "ier",
                "experience": exp,
                "score": exp.reliability_score() if hasattr(exp, 'reliability_score') else exp.success_rate(),
                "hop": 0,
                "path": [exp.name]
            })
            seen_ids.add(exp.id)
        
        # 添加KG结果（去重）
        for kg_result in kg_results:
            kg_exp = kg_result["experience"]
            if kg_exp.id not in seen_ids:
                # 记录访问
                if self.usage_tracker:
                    self.usage_tracker.record_access(
                        kg_exp.id,
                        kg_exp.name,
                        context="retrieval",
                        source="kg_multihop" if kg_result.get('hop', 0) > 0 else "kg_direct"
                    )
                
                # 尝试找到对应的IER经验
                ier_equivalent = self._find_ier_equivalent(kg_exp)
                
                merged.append({
                    "source": "kg",
                    "experience": ier_equivalent or kg_exp,
                    "score": kg_result["relevance_score"],
                    "hop": kg_result.get("hop", 0),
                    "path": kg_result.get("path", [kg_exp.name]),
                    "retrieval_method": kg_result.get("retrieval_method", "graph")
                })
                seen_ids.add(kg_exp.id)
        
        # 排序：分数降序，跳数升序
        merged.sort(key=lambda x: (-x["score"], x["hop"]))
        
        return {
            "experiences": merged[:10],  # Top-10
            "ier_count": len([m for m in merged if m["source"] == "ier"]),
            "kg_count": len([m for m in merged if m["source"] == "kg"]),
            "multihop_count": len([m for m in merged if m.get("hop", 0) > 0])
        }
    
    def _find_ier_equivalent(self, kg_exp) -> Optional[Experience]:
        """查找KG经验对应的IER经验"""
        # 通过ID哈希匹配
        for ier_exp in self.ier_manager.experiences.values():
            if ier_exp.name == kg_exp.name:
                return ier_exp
        return None
    
    # ==================== 格式化经验为Prompt ====================
    
    def format_experiences_for_prompt(self, retrieval_result: Dict) -> str:
        """
        将检索结果格式化为Prompt可用的字符串
        
        增强版：包含关系路径信息
        """
        if not retrieval_result.get("experiences"):
            return ""
        
        lines = [
            "=" * 60,
            "📚 相关经验参考 (IER-KG增强)",
            "=" * 60,
            ""
        ]
        
        for i, item in enumerate(retrieval_result["experiences"], 1):
            exp = item["experience"]
            source_indicator = "🎯" if item["source"] == "ier" else "🔗"
            hop_indicator = f"[{item.get('hop', 0)}跳]" if item.get("hop", 0) > 0 else ""
            
            lines.extend([
                f"{source_indicator} 经验 #{i} {hop_indicator}",
                f"   名称: {exp.name}",
                f"   类型: {exp.exp_type.value if hasattr(exp, 'exp_type') else 'experience'}",
                f"   相关度: {item['score']:.2f}",
                f"   描述: {exp.description[:100]}..." if len(exp.description) > 100 else f"   描述: {exp.description}",
            ])
            
            # 如果是KG来源，显示路径
            if item["source"] == "kg" and "path" in item:
                path_str = " → ".join(str(p) for p in item["path"])
                lines.append(f"   发现路径: {path_str}")
            
            if exp.code_example:
                lines.extend([
                    "   代码示例:",
                    "   ```python",
                    f"   {exp.code_example[:200]}..." if len(exp.code_example) > 200 else f"   {exp.code_example}",
                    "   ```"
                ])
            
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    # ==================== 记录经验使用结果 ====================
    
    def record_experience_usage(self, task_id: str, exp_id: str, success: bool):
        """
        记录经验使用结果
        同时更新IER和KG系统
        """
        # 更新IER
        self.ier_manager.record_usage(exp_id, success)
        
        # 更新KG（如果启用）
        if self.use_kg and self.kg_system:
            if exp_id in self.kg_system.exp_manager.experiences:
                kg_exp = self.kg_system.exp_manager.experiences[exp_id]
                kg_exp.usage_count += 1
                if success:
                    kg_exp.success_count += 1
                    kg_exp.reliability_score = min(1.0, kg_exp.reliability_score + 0.05)
                else:
                    kg_exp.reliability_score = max(0.0, kg_exp.reliability_score - 0.1)
                
                self.kg_system.exp_manager.save()
    
    # ==================== 经验关系管理 ====================
    
    def add_experience_relation(self, source_exp_name: str, target_exp_name: str,
                                relation_type: str, strength: float = 1.0) -> bool:
        """
        添加经验之间的关系
        
        Args:
            source_exp_name: 源经验名称
            target_exp_name: 目标经验名称
            relation_type: 关系类型 (solves/causes/requires/complements/replaces)
            strength: 关系强度 0-1
        
        Returns:
            是否成功添加
        """
        if not self.use_kg or not self.kg_system:
            print("[IER-KG] Knowledge graph not enabled")
            return False
        
        # 查找经验
        source_exp = None
        target_exp = None
        
        for exp in self.kg_system.exp_manager.experiences.values():
            if exp.name == source_exp_name:
                source_exp = exp
            if exp.name == target_exp_name:
                target_exp = exp
        
        if not source_exp or not target_exp:
            print(f"[IER-KG] Experience not found: {source_exp_name} or {target_exp_name}")
            return False
        
        # 映射关系类型
        rel_type_map = {
            "solves": ExperienceRelationType.SOLVES,
            "causes": ExperienceRelationType.CAUSES,
            "prevents": ExperienceRelationType.PREVENTS,
            "requires": ExperienceRelationType.REQUIRES,
            "complements": ExperienceRelationType.COMPLEMENTS,
            "replaces": ExperienceRelationType.REPLACES,
            "conflicts": ExperienceRelationType.CONFLICTS_WITH,
            "similar": ExperienceRelationType.SIMILAR_TO,
        }
        
        rel_type = rel_type_map.get(relation_type.lower())
        if not rel_type:
            print(f"[IER-KG] Unknown relation type: {relation_type}")
            return False
        
        # 添加关系
        self.kg_system.add_experience_relation(
            source_exp.id, target_exp.id, rel_type, strength
        )
        print(f"[IER-KG] Added relation: {source_exp_name} --{relation_type}--> {target_exp_name}")
        return True
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取集成系统的统计信息"""
        ier_stats = self.ier_manager.get_statistics()
        
        result = {
            "ier": ier_stats,
            "kg_enabled": self.use_kg,
        }
        
        if self.use_kg and self.kg_system:
            kg_stats = self.kg_system.get_statistics()
            result["kg"] = kg_stats
            
            # 计算增强指标
            result["enhancement"] = {
                "code_entities_indexed": kg_stats.get("code_entities", 0),
                "experiences_with_provenance": kg_stats.get("experiences", 0),
                "provenance_chains": kg_stats.get("provenance_chains", 0),
                "multihop_retrieval_ready": True
            }
        
        return result
    
    # ==================== 可视化导出 ====================
    
    def export_graph_for_visualization(self, output_file: Optional[str] = None) -> str:
        """导出图谱数据用于可视化"""
        if not self.use_kg or not self.kg_system:
            return "{\"error\": \"Knowledge graph not enabled\"}"
        
        data = self.kg_system.export_for_visualization()
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return output_file
        
        return json.dumps(data, indent=2)
    
    # ==================== 溯源查询 ====================
    
    def trace_experience_provenance(self, exp_name: str) -> Dict:
        """查询经验的溯源信息"""
        if not self.use_kg or not self.kg_system:
            return {"error": "Knowledge graph not enabled"}
        
        # 查找经验
        for exp in self.kg_system.exp_manager.experiences.values():
            if exp.name == exp_name:
                return self.kg_system.get_experience_context(exp.id)
        
        return {"error": f"Experience '{exp_name}' not found"}
    
    # ==================== 去重功能 ====================
    
    def run_deduplication_check(self) -> Dict:
        """
        运行经验去重检查
        
        返回去重统计信息
        """
        if not self.dedup_service:
            return {"error": "Deduplication service not available"}
        
        print("[IER-KG Deduplication] Running deduplication check...")
        stats = self.dedup_service.run_deduplication_job()
        
        print(f"[IER-KG Deduplication] Results:")
        print(f"  - Checked pairs: {stats['checked']}")
        print(f"  - Duplicates found: {stats['duplicates_found']}")
        
        if stats['similar_pairs']:
            print(f"  - Similar pairs (top 5):")
            for pair in sorted(stats['similar_pairs'], 
                             key=lambda x: x['similarity'], reverse=True)[:5]:
                print(f"    • {pair['exp1']} ~ {pair['exp2']}: {pair['similarity']:.2f}")
        
        return stats
    
    def check_experience_duplicate(self, exp_data: Dict) -> Dict:
        """
        检查单个经验是否重复
        
        Args:
            exp_data: 经验数据字典
            
        Returns:
            去重检查结果
        """
        if not self.dedup_service:
            return {"error": "Deduplication service not available"}
        
        should_add, dup_id, sim_score = self.dedup_service.check_before_add(exp_data)
        
        return {
            "should_add": should_add,
            "duplicate_id": dup_id,
            "similarity_score": sim_score,
            "is_duplicate": not should_add
        }
    
    # ==================== 使用频率追踪 ====================
    
    def get_usage_statistics(self) -> Dict:
        """
        获取使用频率统计报告
        
        Returns:
            使用统计报告
        """
        if not self.usage_tracker:
            return {"error": "Usage tracker not available"}
        
        report = self.usage_tracker.generate_report()
        
        # 如果暂无数据，返回默认结构
        if "message" in report:
            return {
                "total_experiences": 0,
                "total_accesses": 0,
                "frequency_distribution": {},
                "top_experiences": [],
                "expired_count": 0,
                "avg_activity_score": 0,
                "message": report["message"]
            }
        
        return report
    
    def mark_low_frequency_experiences(self) -> Dict:
        """
        标记低频经验
        
        自动将使用次数<3次的经验标记为低频
        
        Returns:
            标记结果统计
        """
        if not self.usage_tracker or not self.kg_system:
            return {"error": "Required services not available"}
        
        marked_count = 0
        metrics = self.usage_tracker.get_all_metrics()
        
        for exp_id, metric in metrics.items():
            if metric.frequency_class == "low" or metric.frequency_class == "archived":
                # 在KG系统中标记
                if exp_id in self.kg_system.exp_manager.experiences:
                    exp = self.kg_system.exp_manager.experiences[exp_id]
                    exp.metadata["archived"] = True
                    exp.metadata["archive_reason"] = f"low_frequency ({metric.total_accesses} accesses)"
                    marked_count += 1
        
        # 保存更新
        self.kg_system.exp_manager._save_experiences()
        
        return {
            "marked_count": marked_count,
            "frequency_distribution": self.usage_tracker.get_frequency_distribution()
        }
    
    def get_top_experiences(self, n: int = 10) -> List[Dict]:
        """
        获取Top N活跃经验
        
        Args:
            n: 数量
            
        Returns:
            活跃经验列表
        """
        if not self.usage_tracker:
            return []
        
        top_metrics = self.usage_tracker.get_top_experiences(n)
        
        return [
            {
                "id": m.experience_id,
                "name": m.experience_name,
                "accesses": m.total_accesses,
                "activity_score": round(m.activity_score, 2),
                "frequency_class": m.frequency_class
            }
            for m in top_metrics
        ]
    
    # ==================== 代码实体重要性评分 ====================
    
    def analyze_code_entity_importance(self) -> Dict:
        """
        分析代码实体重要性
        
        Returns:
            重要性分析报告
        """
        if not self.kg_system:
            return {"error": "KG system not available"}
        
        scorer = CodeEntityScorer()
        
        # 构建代码图谱
        code_graph = {
            "entities": {},
            "relations": {}
        }
        
        # 从KG系统获取代码实体和关系
        if hasattr(self.kg_system, 'code_entities'):
            for entity_id, entity in self.kg_system.code_entities.items():
                code_graph["entities"][entity_id] = {
                    "id": entity.id,
                    "name": entity.name,
                    "entity_type": entity.entity_type
                }
        
        if hasattr(self.kg_system, 'code_relations'):
            for rel_id, rel in self.kg_system.code_relations.items():
                code_graph["relations"][rel_id] = {
                    "source_id": rel.source_id,
                    "target_id": rel.target_id,
                    "relation_type": rel.relation_type.value if hasattr(rel.relation_type, 'value') else str(rel.relation_type)
                }
        
        # 如果代码图谱为空，尝试从文件加载
        if not code_graph["entities"]:
            try:
                import json
                with open('ier_kg/code_graph.json', 'r') as f:
                    file_graph = json.load(f)
                    code_graph["entities"] = file_graph.get("entities", {})
                    code_graph["relations"] = file_graph.get("relations", {})
            except:
                pass
        
        if not code_graph["entities"]:
            return {
                "total_entities": 0,
                "importance_distribution": {},
                "top_entities": [],
                "type_stats": {},
                "message": "暂无代码实体数据"
            }
        
        importance_map = scorer.calculate_importance(code_graph)
        report = scorer.generate_report(importance_map)
        
        return report
    
    def get_critical_code_entities(self, min_level: str = "high") -> List[Dict]:
        """
        获取关键代码实体
        
        Args:
            min_level: 最低重要性等级 (critical/high/medium)
            
        Returns:
            关键实体列表
        """
        report = self.analyze_code_entity_importance()
        
        if "error" in report:
            return []
        
        return [e for e in report.get("top_entities", []) 
                if e.get("level") in ["critical", "high"] or 
                (min_level == "medium" and e.get("level") == "medium")]
    
    # ==================== 向量检索增强 ====================
    
    def build_vector_index(self) -> Dict:
        """
        构建经验向量索引
        
        Returns:
            构建结果
        """
        if not self.vector_retrieval:
            return {"error": "Vector retrieval not available"}
        
        # 收集所有经验
        experiences = {}
        
        # 从IER系统获取
        if self.ier_manager:
            experiences.update(self.ier_manager.experiences)
        
        # 从KG系统获取
        if self.kg_system and hasattr(self.kg_system, 'exp_manager'):
            experiences.update(self.kg_system.exp_manager.experiences)
        
        if not experiences:
            return {"message": "No experiences to index"}
        
        # 构建索引
        self.vector_retrieval.build_index(experiences)
        
        return {
            "indexed_count": len(experiences),
            "vector_dim": self.vector_retrieval.embedding.vocab_size
        }
    
    def search_with_vector(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        向量语义检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            检索结果列表
        """
        if not self.vector_retrieval or not self.vector_retrieval.is_fitted:
            return []
        
        results = self.vector_retrieval.search(query, top_k)
        
        return [
            {
                "exp_id": exp_id,
                "similarity": round(sim, 3),
                "source": "vector"
            }
            for exp_id, sim in results
        ]
    
    def hybrid_retrieve(self, task_description: str, 
                       code_context: Optional[str] = None,
                       top_k: int = 10) -> Dict:
        """
        混合检索 (图谱 + 向量)
        
        Args:
            task_description: 任务描述
            code_context: 代码上下文
            top_k: 返回数量
            
        Returns:
            融合后的检索结果
        """
        # 1. 图谱检索
        graph_results = self.retrieve_for_task(
            task_description, code_context, max_hops=2
        )
        
        # 2. 向量检索
        vector_results = []
        if self.vector_retrieval and self.vector_retrieval.is_fitted:
            query = f"{task_description} {code_context or ''}"
            vector_results = self.vector_retrieval.search(query, top_k=top_k*2)
        
        # 3. 构建KG结果列表
        kg_list = graph_results.get("experiences", [])
        
        # 4. 使用排序器融合并排序
        if self.ranker:
            ranked_results = self.ranker.merge_and_rank(
                kg_list, vector_results, top_k=top_k
            )
            
            return {
                "results": [
                    {
                        "exp_id": r.exp_id,
                        "exp_name": r.exp_name,
                        "confidence": round(r.confidence, 3),
                        "level": r.confidence_level,
                        "hop": r.hop_count,
                        "graph_score": round(r.graph_score, 3),
                        "vector_score": round(r.vector_score, 3),
                        "source": "hybrid"
                    }
                    for r in ranked_results
                ],
                "graph_count": len(kg_list),
                "vector_count": len(vector_results),
                "merged_count": len(ranked_results)
            }
        
        # 回退：简单合并
        return {
            "results": [
                {
                    "exp_id": r.get("experience", {}).id if hasattr(r.get("experience"), 'id') else "",
                    "exp_name": r.get("experience", {}).name if hasattr(r.get("experience"), 'name') else "",
                    "source": r.get("source", "unknown"),
                    "score": r.get("score", 0)
                }
                for r in kg_list[:top_k]
            ],
            "graph_count": len(kg_list),
            "vector_count": 0,
            "merged_count": len(kg_list)
        }
    
    # ==================== 经验自动摘要 ====================
    
    def generate_experience_summary(self, exp_id: str, 
                                   format_type: str = "markdown") -> str:
        """
        生成单条经验摘要
        
        Args:
            exp_id: 经验ID
            format_type: 输出格式 (markdown/text/json)
            
        Returns:
            格式化的摘要文本
        """
        if not self.summarizer:
            return "Summarizer not available"
        
        # 查找经验
        exp = None
        if self.ier_manager and exp_id in self.ier_manager.experiences:
            exp = self.ier_manager.experiences[exp_id]
        elif self.kg_system and exp_id in self.kg_system.exp_manager.experiences:
            exp = self.kg_system.exp_manager.experiences[exp_id]
        
        if not exp:
            return f"Experience {exp_id} not found"
        
        # 生成摘要
        summary = self.summarizer.generate_summary(exp)
        return self.summarizer.format_summary(summary, format_type)
    
    def batch_generate_summaries(self) -> Dict:
        """
        批量生成所有经验摘要
        
        Returns:
            摘要统计报告
        """
        if not self.summarizer:
            return {"error": "Summarizer not available"}
        
        # 收集所有经验
        experiences = {}
        if self.ier_manager:
            experiences.update(self.ier_manager.experiences)
        if self.kg_system:
            experiences.update(self.kg_system.exp_manager.experiences)
        
        # 批量生成
        batch = BatchSummarizer()
        report = batch.generate_summary_report(experiences)
        
        return report
    
    def get_top_summaries(self, n: int = 5) -> List[str]:
        """
        获取完整度最高的经验摘要
        
        Args:
            n: 数量
            
        Returns:
            摘要文本列表
        """
        if not self.summarizer:
            return []
        
        # 收集经验
        experiences = {}
        if self.ier_manager:
            experiences.update(self.ier_manager.experiences)
        if self.kg_system:
            experiences.update(self.kg_system.exp_manager.experiences)
        
        # 生成所有摘要
        batch = BatchSummarizer()
        summaries = batch.summarize_all(experiences)
        
        # 按完整度排序
        sorted_summaries = sorted(
            summaries.values(),
            key=lambda x: x.completeness,
            reverse=True
        )
        
        # 格式化输出
        return [
            self.summarizer.format_summary(s, "markdown")
            for s in sorted_summaries[:n]
        ]
    
    # ==================== 置信度排序分析 ====================
    
    def explain_retrieval_ranking(self, task_description: str) -> List[str]:
        """
        解释检索结果的排序原因
        
        Args:
            task_description: 任务描述
            
        Returns:
            排序解释列表
        """
        if not self.ranker:
            return ["Ranker not available"]
        
        # 执行混合检索
        results = self.hybrid_retrieve(task_description)
        
        explanations = []
        for r in results.get("results", [])[:5]:
            exp_id = r.get("exp_id")
            if exp_id:
                # 重建RetrievalResult以获取详细解释
                rr = RetrievalResult(
                    exp_id=exp_id,
                    exp_name=r.get("exp_name", ""),
                    graph_score=r.get("graph_score", 0),
                    vector_score=r.get("vector_score", 0),
                    hop_count=r.get("hop", 0),
                    confidence=r.get("confidence", 0)
                )
                explanations.append(self.ranker.explain_ranking(rr))
        
        return explanations
    
    def get_ranking_statistics(self) -> Dict:
        """
        获取排序统计信息
        
        Returns:
            排序统计报告
        """
        if not self.ranker:
            return {"error": "Ranker not available"}
        
        # 获取所有经验作为模拟结果
        experiences = {}
        if self.ier_manager:
            experiences.update(self.ier_manager.experiences)
        if self.kg_system:
            experiences.update(self.kg_system.exp_manager.experiences)
        
        # 构建模拟结果
        mock_results = []
        for exp_id, exp in experiences.items():
            rr = RetrievalResult(
                exp_id=exp_id,
                exp_name=getattr(exp, 'name', exp_id),
                graph_score=0.7,
                vector_score=0.6,
                hop_count=0
            )
            mock_results.append(rr)
        
        # 排序
        ranked = self.ranker.rank_results(mock_results)
        
        # 生成报告
        report_gen = RankingReportGenerator()
        return report_gen.generate_report(ranked)
    
    # ==================== 关闭资源 ====================
    
    def close(self):
        """关闭资源"""
        if self.kg_system:
            self.kg_system.close()


# ==================== 便捷函数 ====================

def create_ier_kg_adapter(use_kg: bool = True) -> IERKGIntegrationAdapter:
    """创建IER-KG适配器实例"""
    return IERKGIntegrationAdapter(use_kg=use_kg)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("IER-KG Integration Adapter - Test Mode")
    print("=" * 60)
    
    # 创建适配器
    adapter = create_ier_kg_adapter(use_kg=True)
    
    print("\n1. System Statistics:")
    stats = adapter.get_statistics()
    print(json.dumps(stats, indent=2, default=str))
    
    print("\n2. Test Retrieval:")
    results = adapter.retrieve_for_task(
        task_description="如何使用装饰器实现缓存",
        code_context="@lru_cache\ndef process(data): pass",
        max_hops=2
    )
    print(f"Found {len(results['experiences'])} experiences")
    print(f"  IER: {results['ier_count']}")
    print(f"  KG: {results['kg_count']}")
    print(f"  Multihop: {results['multihop_count']}")
    
    adapter.close()
    print("\n✓ Test completed")
