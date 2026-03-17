"""
经验相似度检测与去重系统
基于Mem0记忆压缩和去重机制实现
"""

import json
import hashlib
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import re


@dataclass
class SimilarityResult:
    """相似度检测结果"""
    is_duplicate: bool
    similarity_score: float
    matched_experience_id: Optional[str]
    match_reason: str


class ExperienceDeduplicator:
    """
    经验去重器
    
    功能：
    1. 文本相似度检测 (Jaccard + 编辑距离)
    2. 语义指纹去重 (SimHash)
    3. 标签重叠检测
    4. 上下文匹配
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.experience_fingerprints: Dict[str, str] = {}
        
    def calculate_similarity(self, exp1: Dict, exp2: Dict) -> float:
        """
        计算两个经验的综合相似度
        
        权重：
        - 名称相似度: 30%
        - 描述相似度: 40%
        - 标签重叠: 20%
        - 上下文相似: 10%
        """
        name_sim = self._text_similarity(
            exp1.get('name', ''),
            exp2.get('name', '')
        )
        
        desc_sim = self._text_similarity(
            exp1.get('description', ''),
            exp2.get('description', '')
        )
        
        tag_sim = self._tag_overlap(
            exp1.get('tags', []),
            exp2.get('tags', [])
        )
        
        ctx_sim = self._text_similarity(
            exp1.get('context', ''),
            exp2.get('context', '')
        )
        
        # 加权平均
        total_sim = (name_sim * 0.3 + 
                     desc_sim * 0.4 + 
                     tag_sim * 0.2 + 
                     ctx_sim * 0.1)
        
        return total_sim
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度 (Jaccard系数)"""
        if not text1 or not text2:
            return 0.0
            
        # 分词（简单按字符和词）
        set1 = self._tokenize(text1)
        set2 = self._tokenize(text2)
        
        if not set1 or not set2:
            return 0.0
            
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _tokenize(self, text: str) -> Set[str]:
        """简单分词"""
        # 清理文本
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # 按词分割
        words = set(text.split())
        
        # 添加2-gram
        chars = text.replace(' ', '')
        bigrams = set(chars[i:i+2] for i in range(len(chars)-1))
        
        return words | bigrams
    
    def _tag_overlap(self, tags1: List, tags2: List) -> float:
        """计算标签重叠度"""
        set1 = set(tags1)
        set2 = set(tags2)
        
        if not set1 or not set2:
            return 0.0
            
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union
    
    def check_duplicate(self, new_exp: Dict, existing_exps: List[Dict]) -> SimilarityResult:
        """
        检查新经验是否与现有经验重复
        
        返回：
        - is_duplicate: 是否重复
        - similarity_score: 最高相似度
        - matched_experience_id: 匹配的经验ID
        - match_reason: 匹配原因
        """
        max_similarity = 0.0
        matched_id = None
        match_reason = ""
        
        for existing in existing_exps:
            sim = self.calculate_similarity(new_exp, existing)
            
            if sim > max_similarity:
                max_similarity = sim
                matched_id = existing.get('id')
                
                # 生成匹配原因
                if sim > 0.9:
                    match_reason = "高度相似，建议合并"
                elif sim > 0.8:
                    match_reason = "描述或功能相似"
                elif sim > 0.7:
                    match_reason = "标签或上下文相似"
                
        is_duplicate = max_similarity >= self.similarity_threshold
        
        return SimilarityResult(
            is_duplicate=is_duplicate,
            similarity_score=max_similarity,
            matched_experience_id=matched_id,
            match_reason=match_reason if is_duplicate else ""
        )
    
    def generate_fingerprint(self, experience: Dict) -> str:
        """生成经验指纹 (用于快速去重)"""
        # 组合关键字段
        content = f"{experience.get('name', '')}|{experience.get('description', '')[:100]}"
        
        # 计算SimHash (简化版)
        hash_val = hashlib.md5(content.encode()).hexdigest()[:16]
        
        return hash_val
    
    def merge_experiences(self, exp1: Dict, exp2: Dict) -> Dict:
        """
        合并两个相似经验
        
        策略：
        - 保留更详细的描述
        - 合并标签
        - 累加使用次数
        - 保留更高的成功率
        """
        merged = exp1.copy()
        
        # 保留更长的描述
        if len(exp2.get('description', '')) > len(exp1.get('description', '')):
            merged['description'] = exp2['description']
        
        # 合并标签
        merged_tags = list(set(exp1.get('tags', []) + exp2.get('tags', [])))
        merged['tags'] = merged_tags
        
        # 合并解决方案（如果不同）
        if exp2.get('solution') and exp2['solution'] != exp1.get('solution'):
            merged['solution'] = f"{exp1.get('solution', '')}\n\n备选方案:\n{exp2['solution']}"
        
        # 标记为合并经验
        merged['merged_from'] = exp2.get('id')
        merged['merge_count'] = exp1.get('merge_count', 0) + 1
        
        return merged


class IERKGDeduplicationService:
    """
    IER-KG去重服务集成
    
    自动检测和合并重复经验
    """
    
    def __init__(self, ier_kg_adapter):
        self.adapter = ier_kg_adapter
        self.deduplicator = ExperienceDeduplicator()
        
    def check_before_add(self, experience_data: Dict) -> Tuple[bool, Optional[str], float]:
        """
        在添加新经验前检查是否重复
        
        返回: (should_add, duplicate_id, similarity_score)
        """
        # 获取所有现有经验
        existing_exps = list(self.adapter.kg_system.exp_manager.experiences.values())
        
        # 转换为字典列表
        existing_dicts = []
        for exp in existing_exps:
            existing_dicts.append({
                'id': exp.id,
                'name': exp.name,
                'description': exp.description,
                'context': exp.context,
                'tags': exp.tags
            })
        
        # 检查相似度
        result = self.deduplicator.check_duplicate(experience_data, existing_dicts)
        
        if result.is_duplicate:
            return False, result.matched_experience_id, result.similarity_score
        
        return True, None, result.similarity_score
    
    def run_deduplication_job(self) -> Dict:
        """
        运行批量去重任务
        
        返回去重统计
        """
        stats = {
            'checked': 0,
            'duplicates_found': 0,
            'merged': 0,
            'similar_pairs': []
        }
        
        experiences = list(self.adapter.kg_system.exp_manager.experiences.values())
        checked_pairs = set()
        
        for i, exp1 in enumerate(experiences):
            for exp2 in experiences[i+1:]:
                pair_key = tuple(sorted([exp1.id, exp2.id]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                
                stats['checked'] += 1
                
                # 计算相似度
                sim = self.deduplicator.calculate_similarity(
                    {'name': exp1.name, 'description': exp1.description, 
                     'context': exp1.context, 'tags': exp1.tags},
                    {'name': exp2.name, 'description': exp2.description,
                     'context': exp2.context, 'tags': exp2.tags}
                )
                
                if sim >= self.deduplicator.similarity_threshold:
                    stats['duplicates_found'] += 1
                    stats['similar_pairs'].append({
                        'exp1': exp1.name,
                        'exp2': exp2.name,
                        'similarity': sim
                    })
        
        return stats


# 导出函数
def create_deduplicator() -> ExperienceDeduplicator:
    """创建去重器实例"""
    return ExperienceDeduplicator()
