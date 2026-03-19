#!/usr/bin/env python3
"""
WDai 柔性权重记忆检索系统
Flexible Weight Memory Retrieval System
基于DeepMind多尺度记忆研究
"""

import re
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    source: str
    layer: str
    score: float
    timestamp: str
    tags: List[str]


class FlexibleWeightRetriever:
    """柔性权重检索器"""
    
    def __init__(self, workspace: str = "/root/.openclaw/workspace"):
        self.workspace = Path(workspace)
        self.memory_dir = self.workspace / "memory"
        
        # 基础权重配置
        self.base_weights = {
            'immediate': 0.1,
            'session': 0.2,
            'project': 0.3,
            'domain': 0.25,
            'universal': 0.15
        }
        
        # 时间衰减系数
        self.decay_rates = {
            'immediate': 0.1,   # 4小时衰减
            'session': 0.3,     # 7天衰减
            'project': 0.5,     # 30天衰减
            'domain': 0.7,      # 90天衰减
            'universal': 0.9    # 几乎不衰减
        }
        
        # 查询类型关键词
        self.query_patterns = {
            'immediate': ['现在', '当前', '刚才', '立刻', '马上', '正在'],
            'session': ['今天', '刚才', '最近', '之前说过'],
            'project': ['evo', '任务', '项目', '这个功能', '那个问题'],
            'domain': ['原理', '模式', '为什么', '最佳实践', '技巧'],
            'universal': ['原则', '规则', '总是', '应该', '核心', '本质']
        }
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        柔性权重检索主入口
        """
        print(f"\n🔍 柔性检索: '{query[:30]}...'")
        
        # 1. 分析查询，动态调整权重
        dynamic_weights = self._analyze_query(query)
        print(f"   动态权重: {dynamic_weights}")
        
        # 2. 各层独立检索
        all_results = []
        for layer, weight in dynamic_weights.items():
            layer_results = self._search_layer(query, layer)
            
            # 应用层权重
            for result in layer_results:
                result.score *= weight
                all_results.append(result)
        
        # 3. RRF融合排序
        fused_results = self._reciprocal_rank_fusion(all_results)
        
        # 4. 时间衰减调整
        final_results = self._apply_time_decay(fused_results)
        
        # 5. 返回Top K
        return final_results[:top_k]
    
    def _analyze_query(self, query: str) -> Dict[str, float]:
        """
        分析查询，返回动态权重
        """
        weights = self.base_weights.copy()
        query_lower = query.lower()
        
        # 检测时间关键词
        for layer, keywords in self.query_patterns.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            if matches > 0:
                # 提升匹配层的权重
                boost = min(0.3, matches * 0.1)
                weights[layer] = min(0.6, weights[layer] + boost)
                
                # 重新归一化
                total = sum(weights.values())
                weights = {k: v/total for k, v in weights.items()}
        
        # 特殊处理
        if any(w in query_lower for w in ['代码', 'code', '实现']):
            weights['project'] = min(0.5, weights['project'] + 0.2)
        
        if any(w in query_lower for w in ['设计', '架构', '优化']):
            weights['domain'] = min(0.45, weights['domain'] + 0.2)
        
        # 再次归一化
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}
    
    def _search_layer(self, query: str, layer: str) -> List[RetrievalResult]:
        """
        在指定层进行检索
        """
        layer_dir = self.memory_dir / layer
        if not layer_dir.exists():
            return []
        
        results = []
        query_terms = set(query.lower().split())
        
        # 遍历该层所有文件
        for file in layer_dir.rglob("*.md"):
            content = file.read_text()
            
            # 计算BM25-like分数
            score = self._calculate_bm25(query_terms, content)
            
            if score > 0:
                results.append(RetrievalResult(
                    content=content[:500],  # 截取前500字符
                    source=str(file.relative_to(self.workspace)),
                    layer=layer,
                    score=score,
                    timestamp=self._extract_timestamp(content),
                    tags=self._extract_tags(content)
                ))
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:10]  # 每层最多10个
    
    def _calculate_bm25(self, query_terms: set, content: str) -> float:
        """
        简化的BM25分数计算
        """
        content_terms = set(content.lower().split())
        
        # 计算交集
        overlap = query_terms & content_terms
        
        if not overlap:
            return 0.0
        
        # 简化BM25
        k1 = 1.5
        b = 0.75
        doc_len = len(content_terms)
        avg_doc_len = 100  # 假设平均长度
        
        score = 0
        for term in overlap:
            tf = content.lower().count(term)
            idf = 1.0  # 简化IDF
            
            # BM25公式简化版
            term_score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
            score += term_score
        
        return score
    
    def _reciprocal_rank_fusion(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        RRF融合排序
        """
        # 按层分组
        by_layer = {}
        for r in results:
            if r.layer not in by_layer:
                by_layer[r.layer] = []
            by_layer[r.layer].append(r)
        
        # 计算RRF分数
        k = 60  # RRF常数
        rrf_scores = {}
        
        for layer, layer_results in by_layer.items():
            for rank, result in enumerate(layer_results, 1):
                if result.source not in rrf_scores:
                    rrf_scores[result.source] = {'result': result, 'score': 0}
                rrf_scores[result.source]['score'] += 1.0 / (k + rank)
        
        # 排序
        sorted_results = sorted(
            rrf_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return [item['result'] for item in sorted_results]
    
    def _apply_time_decay(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        应用时间衰减
        """
        now = datetime.now()
        
        for result in results:
            try:
                # 解析时间戳
                if result.timestamp:
                    t = datetime.fromisoformat(result.timestamp)
                    age_days = (now - t).days
                    
                    # 获取衰减率
                    decay_rate = self.decay_rates.get(result.layer, 0.5)
                    
                    # 应用指数衰减
                    decay_factor = decay_rate ** (age_days / 30)
                    result.score *= decay_factor
            except:
                pass
        
        # 重新排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    def _extract_timestamp(self, content: str) -> str:
        """从内容中提取时间戳"""
        # 匹配日期格式
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}/\d{2}/\d{2})'
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return ""
    
    def _extract_tags(self, content: str) -> List[str]:
        """从内容中提取标签"""
        # 匹配 **Tags**: xxx, yyy
        match = re.search(r'\*\*Tags\*\*:?\s*(.+)', content)
        if match:
            tags = match.group(1).split(',')
            return [t.strip() for t in tags]
        return []
    
    def update_weights_from_feedback(self, query: str, clicked_results: List[str], ignored_results: List[str]):
        """
        根据用户反馈更新权重
        """
        # 点击的结果 → 提升相关层的权重
        for source in clicked_results:
            layer = source.split('/')[1]  # memory/project/xxx.md
            if layer in self.base_weights:
                self.base_weights[layer] = min(0.5, self.base_weights[layer] * 1.05)
        
        # 忽略的结果 → 降低权重
        for source in ignored_results:
            layer = source.split('/')[1]
            if layer in self.base_weights:
                self.base_weights[layer] = max(0.05, self.base_weights[layer] * 0.95)
        
        # 归一化
        total = sum(self.base_weights.values())
        self.base_weights = {k: v/total for k, v in self.base_weights.items()}
        
        # 保存
        self._save_weights()
    
    def _save_weights(self):
        """保存权重配置"""
        weights_file = self.workspace / ".claw-status" / "retrieval_weights.json"
        with open(weights_file, 'w') as f:
            json.dump({
                'base_weights': self.base_weights,
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)
    
    def load_weights(self):
        """加载权重配置"""
        weights_file = self.workspace / ".claw-status" / "retrieval_weights.json"
        if weights_file.exists():
            with open(weights_file) as f:
                data = json.load(f)
                self.base_weights = data.get('base_weights', self.base_weights)


def main():
    """主入口 - 演示"""
    retriever = FlexibleWeightRetriever()
    
    # 演示查询
    test_queries = [
        "现在有什么优化建议？",  # 应提升 immediate/session
        "evo-006实现了什么？",   # 应提升 project
        "Planning的最佳实践是什么？",  # 应提升 domain
        "核心原则是什么？",      # 应提升 universal
    ]
    
    print("=" * 60)
    print("柔性权重检索系统演示")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n{'='*60}")
        results = retriever.retrieve(query, top_k=3)
        
        print(f"\n📊 检索结果:")
        for i, r in enumerate(results, 1):
            print(f"   {i}. [{r.layer}] {r.source}")
            print(f"      分数: {r.score:.3f} | 时间: {r.timestamp or 'N/A'}")
            print(f"      预览: {r.content[:60]}...")
    
    print(f"\n{'='*60}")
    print("柔性权重检索系统演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
