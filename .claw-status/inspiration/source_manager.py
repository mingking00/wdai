#!/usr/bin/env python3
"""
灵感摄取系统 - 源管理器 (Source Manager)
自动评估源质量 + 智能发现新源

Author: wdai
Version: 1.0
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import sys

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))


@dataclass
class SourceCandidate:
    """候选源"""
    url: str
    name: str
    category: str  # rss / github / blog
    discovery_method: str
    quality_signals: Dict = None
    
    def __post_init__(self):
        if self.quality_signals is None:
            self.quality_signals = {}


class SourceManager:
    """
    源管理器
    
    职责:
    1. 持续评估现有源质量
    2. 自动发现潜在高质量源
    3. 维护源白名单/黑名单
    4. 推荐源扩展方向
    """
    
    # 源质量评估标准
    QUALITY_CRITERIA = {
        'min_acceptable_quality': 0.3,
        'promote_threshold': 0.7,
        'demote_threshold': 0.3,
        'remove_threshold': 0.2,
        'evaluation_min_runs': 5,  # 最少运行次数才评估
    }
    
    # 已知高质量源模板 (用于发现类似源)
    SOURCE_PATTERNS = {
        'rss': [
            {'domain': 'anthropic.com', 'path': '/research', 'weight': 1.0},
            {'domain': 'openai.com', 'path': '/blog', 'weight': 0.9},
            {'domain': 'huggingface.co', 'path': '/blog', 'weight': 0.8},
            {'domain': 'lilianweng.github.io', 'path': '', 'weight': 0.9},
            {'domain': 'simonwillison.net', 'path': '', 'weight': 0.8},
        ],
        'github': [
            {'owner_keywords': ['anthropics', 'openai', 'langchain-ai', 'microsoft'], 'weight': 0.9},
            {'topic_keywords': ['agent', 'llm', 'rag', 'mcp'], 'weight': 0.8},
        ]
    }
    
    def __init__(self, data_dir: str = "data/source_manager"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.whitelist_file = self.data_dir / "whitelist.json"
        self.blacklist_file = self.data_dir / "blacklist.json"
        self.candidates_file = self.data_dir / "candidates.json"
        self.evaluation_log_file = self.data_dir / "evaluation_log.json"
        
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self.candidates: List[SourceCandidate] = []
        self.evaluation_log: List[Dict] = []
        
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        if self.whitelist_file.exists():
            try:
                with open(self.whitelist_file, 'r') as f:
                    self.whitelist = set(json.load(f))
            except:
                self.whitelist = set()
        
        if self.blacklist_file.exists():
            try:
                with open(self.blacklist_file, 'r') as f:
                    self.blacklist = set(json.load(f))
            except:
                self.blacklist = set()
        
        if self.candidates_file.exists():
            try:
                with open(self.candidates_file, 'r') as f:
                    data = json.load(f)
                    self.candidates = [SourceCandidate(**c) for c in data]
            except:
                self.candidates = []
        
        if self.evaluation_log_file.exists():
            try:
                with open(self.evaluation_log_file, 'r') as f:
                    self.evaluation_log = json.load(f)
            except:
                self.evaluation_log = []
    
    def _save_data(self):
        """保存数据"""
        try:
            with open(self.whitelist_file, 'w') as f:
                json.dump(list(self.whitelist), f, indent=2)
            
            with open(self.blacklist_file, 'w') as f:
                json.dump(list(self.blacklist), f, indent=2)
            
            with open(self.candidates_file, 'w') as f:
                json.dump([asdict(c) for c in self.candidates], f, indent=2)
            
            with open(self.evaluation_log_file, 'w') as f:
                json.dump(self.evaluation_log[-100:], f, indent=2)  # 只保留最近100条
        except:
            pass
    
    def evaluate_source(self, source_id: str, metrics: Dict) -> Dict:
        """
        评估单个源的质量
        
        Args:
            source_id: 源标识
            metrics: 来自scheduler的指标
            
        Returns:
            评估结果和建议
        """
        result = {
            'source_id': source_id,
            'evaluated_at': datetime.now().isoformat(),
            'grade': 'F',
            'quality_score': 0.0,
            'recommendation': 'insufficient_data',
            'actions': []
        }
        
        total_crawls = metrics.get('total_crawls', 0)
        if total_crawls < self.QUALITY_CRITERIA['evaluation_min_runs']:
            result['recommendation'] = 'continue_monitoring'
            result['reason'] = f'运行次数不足 ({total_crawls}/{self.QUALITY_CRITERIA["evaluation_min_runs"]})'
            return result
        
        # 计算综合质量分
        quality_score = self._calculate_quality_score(metrics)
        result['quality_score'] = round(quality_score, 2)
        
        # 确定等级
        if quality_score >= 0.8:
            result['grade'] = 'A'
        elif quality_score >= 0.6:
            result['grade'] = 'B'
        elif quality_score >= 0.4:
            result['grade'] = 'C'
        elif quality_score >= 0.2:
            result['grade'] = 'D'
        else:
            result['grade'] = 'F'
        
        # 生成建议
        if quality_score >= self.QUALITY_CRITERIA['promote_threshold']:
            result['recommendation'] = 'promote'
            result['actions'] = ['增加监控频率', '考虑扩展相关源']
            self.whitelist.add(source_id)
        elif quality_score < self.QUALITY_CRITERIA['remove_threshold']:
            result['recommendation'] = 'remove'
            result['actions'] = ['停止监控', '移入黑名单']
            self.blacklist.add(source_id)
            if source_id in self.whitelist:
                self.whitelist.remove(source_id)
        elif quality_score < self.QUALITY_CRITERIA['demote_threshold']:
            result['recommendation'] = 'demote'
            result['actions'] = ['降低监控频率', '观察改进']
        else:
            result['recommendation'] = 'maintain'
            result['actions'] = ['保持当前配置']
        
        # 记录日志
        self.evaluation_log.append(result)
        self._save_data()
        
        return result
    
    def _calculate_quality_score(self, metrics: Dict) -> float:
        """计算综合质量分"""
        # 权重配置
        weights = {
            'relevance': 0.3,      # 相关性
            'freshness': 0.25,     # 新鲜度
            'stability': 0.2,      # 稳定性
            'yield_rate': 0.25     # 产出率
        }
        
        scores = {}
        
        # 相关性分数 (基于avg_quality_score)
        scores['relevance'] = metrics.get('avg_quality_score', 0)
        
        # 新鲜度分数 (基于平均间隔，越频繁越高)
        interval = metrics.get('current_interval_hours', 12)
        scores['freshness'] = max(0, 1 - (interval / 24))
        
        # 稳定性分数 (基于成功率)
        scores['stability'] = metrics.get('success_rate', 1.0)
        
        # 产出率分数 (每次抓取平均产出)
        total_items = metrics.get('new_items_found', 0)
        total_crawls = max(metrics.get('total_crawls', 1), 1)
        yield_per_crawl = total_items / total_crawls
        scores['yield_rate'] = min(yield_per_crawl / 3, 1.0)  # 假设3条/次是满分
        
        # 加权求和
        total_score = sum(scores[k] * weights[k] for k in weights)
        return total_score
    
    def discover_candidates(self, sources_list: List[Dict]) -> List[SourceCandidate]:
        """
        基于现有源发现潜在候选源
        
        策略:
        1. 从高质量源的引用中发现
        2. 从GitHub相关推荐中发现
        3. 从社区讨论中发现
        """
        candidates = []
        
        # 分析现有高质量源的模式
        high_quality_sources = [
            s for s in sources_list 
            if s.get('quality_score', 0) > 0.7
        ]
        
        # 基于模式匹配推荐相似源
        for pattern in self.SOURCE_PATTERNS.get('rss', []):
            # 检查是否已存在
            exists = any(
                pattern['domain'] in s.get('url', '') 
                for s in sources_list
            )
            if not exists:
                candidate = SourceCandidate(
                    url=f"https://{pattern['domain']}{pattern['path']}/rss.xml",
                    name=f"{pattern['domain']} Blog",
                    category='rss',
                    discovery_method='pattern_matching',
                    quality_signals={'pattern_weight': pattern['weight']}
                )
                candidates.append(candidate)
        
        return candidates
    
    def recommend_expansion(self, current_sources: List[Dict]) -> Dict:
        """
        推荐源扩展方向
        
        基于:
        1. 当前覆盖的盲点
        2. 热门领域缺失
        3. 用户兴趣变化
        """
        
        # 分析当前覆盖的领域
        covered_areas = set()
        for src in current_sources:
            tags = src.get('tags', [])
            covered_areas.update(tags)
        
        # 推荐缺失的热门领域
        hot_areas = {
            'mcp': {'name': 'Model Context Protocol', 'priority': 'high'},
            'computer_use': {'name': 'Computer Use Agents', 'priority': 'high'},
            'voice': {'name': 'Voice/Audio LLM', 'priority': 'medium'},
            'multimodal': {'name': 'Multimodal Models', 'priority': 'medium'},
            'reasoning': {'name': 'Reasoning Models', 'priority': 'high'},
            'efficiency': {'name': 'Model Efficiency', 'priority': 'medium'},
        }
        
        missing_areas = {
            k: v for k, v in hot_areas.items() 
            if k not in covered_areas
        }
        
        # 生成推荐源
        recommendations = []
        
        if 'mcp' in missing_areas:
            recommendations.append({
                'area': 'MCP',
                'suggested_sources': [
                    {'name': 'MCP Spec', 'url': 'https://spec.modelcontextprotocol.io', 'type': 'docs'},
                    {'name': 'Claude MCP', 'url': 'https://github.com/anthropics/anthropic-cookbook', 'type': 'github'},
                ]
            })
        
        if 'reasoning' in missing_areas:
            recommendations.append({
                'area': 'Reasoning',
                'suggested_sources': [
                    {'name': 'OpenAI Research', 'url': 'https://openai.com/research', 'type': 'rss'},
                    {'name': 'DeepMind Blog', 'url': 'https://deepmind.google/blog/', 'type': 'rss'},
                ]
            })
        
        return {
            'generated_at': datetime.now().isoformat(),
            'covered_areas': list(covered_areas),
            'missing_hot_areas': list(missing_areas.keys()),
            'recommendations': recommendations,
            'candidate_sources': [asdict(c) for c in self.discover_candidates(current_sources)]
        }
    
    def get_source_health_report(self) -> Dict:
        """获取源健康度报告"""
        return {
            'total_whitelist': len(self.whitelist),
            'total_blacklist': len(self.blacklist),
            'pending_candidates': len(self.candidates),
            'recent_evaluations': len([e for e in self.evaluation_log 
                                      if datetime.fromisoformat(e['evaluated_at']) > datetime.now() - timedelta(days=7)]),
            'whitelist': list(self.whitelist),
            'blacklist': list(self.blacklist),
        }


def main():
    """测试"""
    manager = SourceManager()
    
    print("="*60)
    print("🔍 源管理器报告")
    print("="*60)
    
    health = manager.get_source_health_report()
    print(f"\n📊 源健康度:")
    print(f"   白名单: {health['total_whitelist']}")
    print(f"   黑名单: {health['total_blacklist']}")
    print(f"   候选源: {health['pending_candidates']}")
    
    # 模拟评估
    print(f"\n🧪 模拟源评估:")
    test_metrics = {
        'total_crawls': 10,
        'new_items_found': 25,
        'avg_quality_score': 0.75,
        'success_rate': 0.95,
        'current_interval_hours': 6
    }
    result = manager.evaluate_source('test_source', test_metrics)
    print(f"   源: {result['source_id']}")
    print(f"   等级: {result['grade']}")
    print(f"   质量分: {result['quality_score']}")
    print(f"   建议: {result['recommendation']}")
    print(f"   行动: {result['actions']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
