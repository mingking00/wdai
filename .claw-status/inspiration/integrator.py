#!/usr/bin/env python3
"""
灵感摄取系统 - 知识整合器
负责去重、摘要生成、关联分析
"""

import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from difflib import SequenceMatcher

# 导入系统模块
import sys
CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

from models import InspirationRecord, AnalysisResult
from config_manager import get_config


class KnowledgeIntegrator:
    """
    知识整合器
    - 去重检测
    - 摘要生成
    - 与现有evo关联分析
    """
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.title_threshold = self.config.dedup_title_threshold()
        self.content_threshold = self.config.dedup_content_threshold()
    
    def process(self, records: List[InspirationRecord], 
                existing_records: List[InspirationRecord] = None) -> List[AnalysisResult]:
        """
        处理一批记录
        
        Args:
            records: 新抓取到的记录
            existing_records: 已存在的记录 (用于去重)
        
        Returns:
            处理结果列表
        """
        results = []
        
        for record in records:
            result = self.process_single(record, existing_records or [])
            results.append(result)
        
        return results
    
    def process_single(self, record: InspirationRecord, 
                       existing_records: List[InspirationRecord]) -> AnalysisResult:
        """处理单条记录"""
        # 1. 去重检测
        duplicates = self._detect_duplicates(record, existing_records)
        
        # 2. 生成增强摘要
        enhanced_summary = self._generate_summary(record)
        
        # 3. 提取关键词
        keywords = self._extract_keywords(record)
        
        # 4. 关联现有evo
        related_evo = self._find_related_evo(record)
        
        # 5. 计算趋势分数
        trend_score = self._calculate_trend_score(record)
        
        # 更新记录
        record.summary = enhanced_summary
        record.keywords = keywords
        record.trend_score = round(trend_score, 2)
        if duplicates:
            record.duplicates = duplicates
            record.related_inspirations = duplicates
        if related_evo:
            record.related_evo = related_evo
        
        return AnalysisResult(
            inspiration_id=record.id,
            quality_score=record.quality_score,
            trend_score=trend_score,
            summary=enhanced_summary,
            keywords=keywords,
            related_evo=related_evo,
            duplicates_detected=duplicates
        )
    
    def _detect_duplicates(self, record: InspirationRecord, 
                           existing_records: List[InspirationRecord]) -> List[str]:
        """检测重复记录"""
        duplicates = []
        
        for existing in existing_records:
            # URL精确匹配
            if record.url and record.url == existing.url:
                duplicates.append(existing.id)
                continue
            
            # 标题相似度匹配
            if record.title and existing.title:
                title_sim = self._text_similarity(record.title, existing.title)
                if title_sim >= self.title_threshold:
                    duplicates.append(existing.id)
                    continue
            
            # 内容相似度匹配
            content1 = f"{record.title} {record.abstract}"
            content2 = f"{existing.title} {existing.abstract}"
            content_sim = self._text_similarity(content1, content2)
            if content_sim >= self.content_threshold:
                duplicates.append(existing.id)
        
        return duplicates
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度 (0-1)"""
        if not text1 or not text2:
            return 0.0
        
        # 归一化文本
        text1 = self._normalize_text(text1)
        text2 = self._normalize_text(text2)
        
        # 使用SequenceMatcher计算相似度
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _normalize_text(self, text: str) -> str:
        """归一化文本用于比较"""
        # 转小写
        text = text.lower()
        # 移除标点
        text = re.sub(r'[^\w\s]', '', text)
        # 移除多余空格
        text = ' '.join(text.split())
        return text
    
    def _generate_summary(self, record: InspirationRecord) -> str:
        """生成增强摘要"""
        parts = []
        
        # 标题
        parts.append(f"# {record.title}")
        
        # 来源信息
        source_info = f"来源: {record.source}"
        if record.authors:
            source_info += f" | 作者: {', '.join(record.authors[:3])}"
        if record.project_name:
            source_info += f" | 项目: {record.project_owner}/{record.project_name}"
        parts.append(source_info)
        
        # 摘要
        if record.abstract:
            parts.append(f"\n摘要:\n{record.abstract[:500]}")
        elif record.summary:
            parts.append(f"\n摘要:\n{record.summary[:500]}")
        
        # 关键信息
        metadata = record.metadata
        if metadata:
            info_parts = []
            if 'stars' in metadata:
                info_parts.append(f"⭐ {metadata['stars']}")
            if 'arxiv_id' in metadata:
                info_parts.append(f"arXiv: {metadata['arxiv_id']}")
            if 'release_tag' in metadata:
                info_parts.append(f"版本: {metadata['release_tag']}")
            
            if info_parts:
                parts.append(f"\n关键信息: {' | '.join(info_parts)}")
        
        # 评分
        parts.append(f"\n质量分: {record.quality_score} | 趋势分: {record.trend_score}")
        
        return "\n".join(parts)
    
    def _extract_keywords(self, record: InspirationRecord) -> List[str]:
        """提取/增强关键词"""
        keywords = set(record.keywords or [])
        
        text = f"{record.title} {record.abstract} {record.summary}".lower()
        
        # 技术关键词库
        tech_keywords = [
            "agent", "llm", "rag", "retrieval", "reasoning",
            "multi-agent", "planning", "memory", "tools",
            "prompt", "fine-tuning", "embedding", "vector",
            "chain", "graph", "workflow", "autonomous",
            "safety", "alignment", "evaluation", "benchmark"
        ]
        
        for keyword in tech_keywords:
            if keyword in text:
                keywords.add(keyword)
        
        return list(keywords)[:10]  # 限制数量
    
    def _find_related_evo(self, record: InspirationRecord) -> List[str]:
        """查找相关的evo任务"""
        related = []
        
        # 从keywords推断相关evo
        keywords = set(record.keywords or [])
        
        # evo任务关键词映射 (简化版)
        evo_mapping = {
            "evo-001": ["rag", "retrieval"],
            "evo-002": ["agent", "multi-agent"],
            "evo-003": ["memory", "context"],
            "evo-004": ["planning", "reasoning"],
            "evo-005": ["safety", "alignment"],
            "evo-006": ["react", "tool use"],
            "evo-hooks-rag": ["rag", "retrieval"],
            "evo-hooks-agents": ["agent", "multi-agent"],
            "evo-hooks-planning": ["planning", "workflow"]
        }
        
        for evo_id, evo_keywords in evo_mapping.items():
            if any(kw in keywords for kw in evo_keywords):
                related.append(evo_id)
        
        return related[:3]  # 限制数量
    
    def _calculate_trend_score(self, record: InspirationRecord) -> float:
        """计算趋势分数"""
        base_score = record.quality_score
        
        # 根据来源调整
        if record.source == "github_release":
            base_score *= 1.2  # Release有更高趋势权重
        elif record.source == "github_trending":
            base_score *= 1.1
        
        # 根据相关evo数量调整
        if record.related_evo:
            base_score *= (1 + len(record.related_evo) * 0.05)
        
        return min(base_score, 1.0)
    
    def batch_deduplicate(self, records: List[InspirationRecord]) -> List[InspirationRecord]:
        """批量去重 (在内部去重)"""
        unique = []
        seen_fingerprints = set()
        
        for record in records:
            # 生成内容指纹
            fingerprint = self._generate_fingerprint(record)
            
            if fingerprint not in seen_fingerprints:
                seen_fingerprints.add(fingerprint)
                unique.append(record)
            else:
                # 标记为重复
                record.duplicates.append("internal_duplicate")
        
        return unique
    
    def _generate_fingerprint(self, record: InspirationRecord) -> str:
        """生成记录指纹"""
        # 基于标题和URL生成
        content = f"{record.title}:{record.url}".lower()
        return hashlib.md5(content.encode()).hexdigest()[:16]


def test_integrator():
    """测试知识整合器"""
    print("=" * 60)
    print("测试 知识整合器")
    print("=" * 60)
    
    integrator = KnowledgeIntegrator()
    
    # 创建测试记录
    test_records = [
        InspirationRecord(
            title="AutoGPT: An Autonomous GPT-4 Experiment",
            url="https://github.com/Significant-Gravitas/AutoGPT",
            source="github_trending",
            abstract="An experimental open-source attempt to make GPT-4 fully autonomous.",
            quality_score=0.85,
            keywords=["agent", "autonomous", "gpt"]
        ),
        InspirationRecord(
            title="LangChain: Building applications with LLMs through composability",
            url="https://github.com/langchain-ai/langchain",
            source="github_release",
            abstract="LangChain is a framework for developing applications powered by language models.",
            quality_score=0.92,
            keywords=["framework", "llm", "chain"]
        )
    ]
    
    # 测试处理
    results = integrator.process(test_records)
    
    print(f"\n处理结果:")
    for i, (record, result) in enumerate(zip(test_records, results), 1):
        print(f"\n{i}. {record.title}")
        print(f"   质量分: {result.quality_score}")
        print(f"   趋势分: {result.trend_score}")
        print(f"   关键词: {', '.join(result.keywords)}")
        print(f"   相关evo: {', '.join(result.related_evo) if result.related_evo else '无'}")
        print(f"   重复检测: {len(result.duplicates_detected)} 条")
    
    return results


if __name__ == "__main__":
    test_integrator()