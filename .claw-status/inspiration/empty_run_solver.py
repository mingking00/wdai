#!/usr/bin/env python3
"""
灵感摄取系统 - 空转解决方案 (EmptyRun Solver)
不逃避空转，主动创造产出

Author: wdai
Version: 1.0
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import sys

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

# 导入实际抓取器
try:
    from crawler_arxiv_deep import ArxivDeepCrawler
    ARXIV_DEEP_AVAILABLE = True
except ImportError:
    ARXIV_DEEP_AVAILABLE = False

try:
    from crawler_reddit import RedditCrawler
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False


@dataclass
class ContentStrategy:
    """内容获取策略"""
    name: str
    enabled: bool = True
    priority: int = 50
    last_used: Optional[str] = None
    success_count: int = 0


class EmptyRunSolver:
    """
    空转解决器
    
    核心理念: 空转不是问题，问题是"只会一种抓法"
    
    解决策略:
    1. 深度抓取 - RSS没有? 抓正文、抓评论、抓引用
    2. 横向扩展 - 这个源没有? 找相关源、镜像源、翻译源
    3. 纵向挖掘 - 表面没有? 抓历史、抓归档、抓讨论
    4. 主动创造 - 等待没有? 主动搜索、主动询问、主动聚合
    5. 预测抓取 - 基于模式预测新内容时间
    """
    
    def __init__(self, data_dir: str = "data/solver"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.strategies_file = self.data_dir / "strategies.json"
        self.deep_content_cache = self.data_dir / "deep_content.json"
        self.related_sources_cache = self.data_dir / "related_sources.json"
        
        self.strategies: Dict[str, ContentStrategy] = {}
        self.deep_cache: Dict = {}
        self.related_sources: Dict[str, List[str]] = {}
        
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        if self.strategies_file.exists():
            try:
                with open(self.strategies_file, 'r') as f:
                    data = json.load(f)
                    self.strategies = {k: ContentStrategy(**v) for k, v in data.items()}
            except:
                self.strategies = {}
        
        if self.deep_content_cache.exists():
            try:
                with open(self.deep_content_cache, 'r') as f:
                    self.deep_cache = json.load(f)
            except:
                self.deep_cache = {}
        
        if self.related_sources_cache.exists():
            try:
                with open(self.related_sources_cache, 'r') as f:
                    self.related_sources = json.load(f)
            except:
                self.related_sources = {}
        
        # 初始化默认策略
        self._init_default_strategies()
    
    def _init_default_strategies(self):
        """初始化默认策略"""
        defaults = {
            'deep_crawl': ContentStrategy('深度抓取', enabled=True, priority=80),
            'related_sources': ContentStrategy('相关源扩展', enabled=True, priority=70),
            'historical_archive': ContentStrategy('历史归档挖掘', enabled=True, priority=60),
            'active_search': ContentStrategy('主动搜索', enabled=True, priority=90),
            'social_mentions': ContentStrategy('社交媒体提及', enabled=True, priority=50),
            'discussion_forums': ContentStrategy('讨论论坛', enabled=True, priority=40),
            'translation_sources': ContentStrategy('翻译源监控', enabled=True, priority=30),
        }
        
        for key, strategy in defaults.items():
            if key not in self.strategies:
                self.strategies[key] = strategy
    
    def _save_data(self):
        """保存数据"""
        try:
            with open(self.strategies_file, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.strategies.items()}, f, indent=2)
            
            with open(self.deep_content_cache, 'w') as f:
                json.dump(self.deep_cache, f)
            
            with open(self.related_sources_cache, 'w') as f:
                json.dump(self.related_sources, f)
        except:
            pass
    
    def solve_empty_run(self, source_id: str, source_type: str, 
                       consecutive_empty: int, url: str = "") -> List[Dict]:
        """
        解决空转问题，返回替代内容获取方案
        
        Args:
            source_id: 源ID
            source_type: 源类型 (rss/github/blog)
            consecutive_empty: 连续空转次数
            url: 源URL
            
        Returns:
            替代获取方案列表
        """
        solutions = []
        
        # 根据空转次数选择策略
        if consecutive_empty >= 1:
            # 第1次空转: 深度抓取
            solutions.extend(self._strategy_deep_crawl(source_id, url))
        
        if consecutive_empty >= 2:
            # 第2次空转: 相关源扩展
            solutions.extend(self._strategy_related_sources(source_id, source_type))
        
        if consecutive_empty >= 3:
            # 第3次空转: 主动搜索
            solutions.extend(self._strategy_active_search(source_id, source_type))
        
        if consecutive_empty >= 4:
            # 第4次空转: 社交媒体/论坛
            solutions.extend(self._strategy_social_discovery(source_id))
        
        # 按优先级排序
        solutions.sort(key=lambda x: x.get('priority', 50), reverse=True)
        
        return solutions
    
    def _strategy_deep_crawl(self, source_id: str, url: str) -> List[Dict]:
        """
        策略1: 深度抓取
        
        当RSS没有新内容时:
        - 抓取正文页面的评论区
        - 抓取"相关文章"链接
        - 抓取页面内的引用链接
        """
        strategy = self.strategies.get('deep_crawl')
        if not strategy or not strategy.enabled:
            return []
        
        solutions = []
        
        if 'arxiv' in source_id.lower():
            solutions.append({
                'type': 'deep_crawl',
                'action': 'fetch_arxiv_comments',
                'description': '抓取arXiv论文的comments和trackbacks',
                'url_pattern': 'https://arxiv.org/abs/{paper_id}',
                'priority': strategy.priority,
                'expected_items': 3
            })
            solutions.append({
                'type': 'deep_crawl', 
                'action': 'fetch_citations',
                'description': '抓取引用该论文的其他论文',
                'priority': strategy.priority - 10,
                'expected_items': 5
            })
        
        if 'github' in source_id.lower():
            solutions.append({
                'type': 'deep_crawl',
                'action': 'fetch_issues_discussions',
                'description': '抓取issues和discussions中的新想法',
                'priority': strategy.priority,
                'expected_items': 10
            })
            solutions.append({
                'type': 'deep_crawl',
                'action': 'fetch_commit_comments',
                'description': '抓取commit message中的技术洞察',
                'priority': strategy.priority - 5,
                'expected_items': 5
            })
        
        return solutions
    
    def _strategy_related_sources(self, source_id: str, source_type: str) -> List[Dict]:
        """
        策略2: 相关源扩展
        
        当主源没有内容时，寻找相关/镜像源
        """
        strategy = self.strategies.get('related_sources')
        if not strategy or not strategy.enabled:
            return []
        
        solutions = []
        
        # arXiv相关源
        if 'arxiv' in source_id.lower():
            solutions.append({
                'type': 'related_source',
                'action': 'fetch_arxiv_sanity',
                'description': 'arXiv Sanity (Andrej Karpathy筛选)',
                'url': 'http://www.arxiv-sanity.com/',
                'priority': strategy.priority,
                'expected_items': 5
            })
            solutions.append({
                'type': 'related_source',
                'action': 'fetch_papers_with_code',
                'description': 'Papers With Code (带代码实现的论文)',
                'url': 'https://paperswithcode.com/',
                'priority': strategy.priority - 5,
                'expected_items': 8
            })
            solutions.append({
                'type': 'related_source',
                'action': 'fetch_hugging_face_papers',
                'description': 'Hugging Face Daily Papers',
                'url': 'https://huggingface.co/papers',
                'priority': strategy.priority - 10,
                'expected_items': 5
            })
        
        # GitHub相关源
        if 'github' in source_id.lower():
            solutions.append({
                'type': 'related_source',
                'action': 'fetch_product_hunt',
                'description': 'Product Hunt (AI工具发布)',
                'url': 'https://www.producthunt.com/topics/artificial-intelligence',
                'priority': strategy.priority,
                'expected_items': 10
            })
            solutions.append({
                'type': 'related_source',
                'action': 'fetch_hacker_news_show',
                'description': 'Hacker News Show HN',
                'url': 'https://news.ycombinator.com/show',
                'priority': strategy.priority - 5,
                'expected_items': 5
            })
        
        return solutions
    
    def _strategy_active_search(self, source_id: str, source_type: str) -> List[Dict]:
        """
        策略3: 主动搜索
        
        不等待源更新，主动搜索新内容
        """
        strategy = self.strategies.get('active_search')
        if not strategy or not strategy.enabled:
            return []
        
        # 根据源类型确定搜索关键词
        keywords = self._extract_keywords_from_source(source_id)
        
        solutions = []
        
        solutions.append({
            'type': 'active_search',
            'action': 'search_twitter_x',
            'description': f'在X/Twitter搜索 "{keywords[0]}" 相关讨论',
            'keywords': keywords[:3],
            'priority': strategy.priority,
            'expected_items': 15
        })
        
        solutions.append({
            'type': 'active_search',
            'action': 'search_reddit',
            'description': f'在Reddit r/MachineLearning搜索',
            'subreddits': ['MachineLearning', 'LocalLLaMA', 'ClaudeAI'],
            'priority': strategy.priority - 5,
            'expected_items': 10
        })
        
        solutions.append({
            'type': 'active_search',
            'action': 'search_youtube_recent',
            'description': '搜索最近24小时上传的AI相关视频',
            'priority': strategy.priority - 10,
            'expected_items': 8
        })
        
        return solutions
    
    def _strategy_social_discovery(self, source_id: str) -> List[Dict]:
        """
        策略4: 社交媒体/论坛发现
        
        从社区讨论中发现灵感和趋势
        """
        strategy = self.strategies.get('social_mentions')
        if not strategy or not strategy.enabled:
            return []
        
        solutions = []
        
        solutions.append({
            'type': 'social_discovery',
            'action': 'fetch_discord_communities',
            'description': '监控AI相关Discord社区的新讨论',
            'communities': ['Midjourney', 'AutoGPT', 'LangChain'],
            'priority': strategy.priority,
            'expected_items': 10
        })
        
        solutions.append({
            'type': 'social_discovery',
            'action': 'fetch_slack_communities',
            'description': '监控开源项目Slack的新话题',
            'priority': strategy.priority - 10,
            'expected_items': 5
        })
        
        solutions.append({
            'type': 'social_discovery',
            'action': 'fetch_newsletter_archives',
            'description': '抓取Newsletter历史存档中的经典文章',
            'newsletters': ['TLDR AI', 'Import AI', 'The Batch'],
            'priority': strategy.priority - 20,
            'expected_items': 3
        })
        
        return solutions
    
    def _extract_keywords_from_source(self, source_id: str) -> List[str]:
        """从源ID提取关键词"""
        keyword_map = {
            'arxiv': ['AI', 'machine learning', 'deep learning'],
            'github': ['open source', 'AI tool', 'developer'],
            'anthropic': ['Claude', 'AI safety', 'alignment'],
            'openai': ['GPT', 'ChatGPT', 'OpenAI'],
            'huggingface': ['transformers', 'NLP', 'open source AI'],
        }
        
        for key, keywords in keyword_map.items():
            if key in source_id.lower():
                return keywords
        
        return ['AI', 'machine learning']
    
    def execute_solution(self, solution: Dict) -> Dict:
        """
        执行解决方案，返回获取的内容
        
        现在调用实际的抓取器
        """
        action = solution.get('action')
        items = []
        
        # arXiv深度抓取
        if action in ['fetch_arxiv_comments', 'fetch_citations', 'fetch_arxiv_sanity']:
            if ARXIV_DEEP_AVAILABLE:
                try:
                    crawler = ArxivDeepCrawler()
                    if action == 'fetch_arxiv_sanity':
                        papers = crawler.fetch_arxiv_sanity(max_papers=5)
                        items = [self._convert_paper(p) for p in papers]
                    else:
                        # 深度抓取
                        items = crawler.deep_crawl(primary_keywords=["AI", "agent"])
                    return {
                        'action': action,
                        'status': 'success',
                        'items_found': len(items),
                        'items': items[:5],  # 返回前5条
                        'solution_type': solution.get('type')
                    }
                except Exception as e:
                    return {
                        'action': action,
                        'status': 'error',
                        'error': str(e),
                        'items_found': 0
                    }
        
        # Reddit搜索
        if action in ['search_twitter_x', 'search_reddit', 'search_youtube_recent']:
            if REDDIT_AVAILABLE and 'reddit' in action:
                try:
                    crawler = RedditCrawler()
                    keywords = solution.get('keywords', ['AI'])
                    items = crawler.fetch_multi(posts_per_sub=3)
                    return {
                        'action': action,
                        'status': 'success',
                        'items_found': len(items),
                        'items': items[:5],
                        'solution_type': solution.get('type')
                    }
                except Exception as e:
                    return {
                        'action': action,
                        'status': 'error',
                        'error': str(e),
                        'items_found': 0
                    }
        
        # 其他策略返回模拟数据（待实现）
        return {
            'action': action,
            'status': 'simulated',
            'items_found': solution.get('expected_items', 0),
            'solution_type': solution.get('type'),
            'executed_at': datetime.now().isoformat()
        }
    
    def _convert_paper(self, paper) -> Dict:
        """转换论文格式"""
        return {
            'title': getattr(paper, 'title', 'Unknown'),
            'source': getattr(paper, 'source', 'arxiv'),
            'url': getattr(paper, 'url', ''),
            'quality_score': getattr(paper, 'quality_score', 0.5),
            'type': 'arxiv_paper'
        }
    
    def get_solver_report(self) -> Dict:
        """获取解决器报告"""
        return {
            'strategies': {
                k: {
                    'enabled': v.enabled,
                    'priority': v.priority,
                    'success_count': v.success_count,
                    'last_used': v.last_used
                }
                for k, v in self.strategies.items()
            },
            'deep_cache_size': len(self.deep_cache),
            'related_sources_mapped': len(self.related_sources),
            'recommendation': '当空转发生时，优先启用深度抓取和主动搜索'
        }


def main():
    """测试"""
    solver = EmptyRunSolver()
    
    print("="*60)
    print("🔧 空转解决器测试")
    print("="*60)
    
    # 模拟不同空转次数的解决方案
    for empty_count in [1, 2, 3, 4]:
        print(f"\n连续空转 {empty_count} 次时的解决方案:")
        solutions = solver.solve_empty_run(
            source_id='arxiv',
            source_type='rss',
            consecutive_empty=empty_count,
            url='http://arxiv.org/rss/cs.AI'
        )
        
        for i, sol in enumerate(solutions[:3], 1):
            print(f"  {i}. [{sol['type']}] {sol['description']}")
            print(f"     预期产出: {sol.get('expected_items', 0)}条")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
