#!/usr/bin/env python3
"""
Fetch Adapter - 抓取适配器

将原有的 inspiration_fetcher.py 功能适配到 Executor Agent

Author: wdai
Date: 2026-03-19
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import re
import time


class FetchAdapter:
    """
    抓取适配器
    
    封装原有的抓取逻辑，供 Executor Agent 调用
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "data" / "fetch_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计
        self.stats = {
            'arxiv_fetched': 0,
            'github_fetched': 0,
            'rss_fetched': 0,
            'cache_hits': 0
        }
    
    def fetch_arxiv(self, keywords: List[str], max_items: int = 10) -> List[Dict]:
        """
        抓取 arXiv 论文
        
        基于原有 inspiration_fetcher.py 的逻辑
        """
        print(f"[FetchAdapter] 抓取 arXiv, 关键词: {keywords}")
        
        # 检查缓存
        cache_key = f"arxiv_{'_'.join(keywords)}_{datetime.now().strftime('%Y%m%d_%H')}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            with open(cache_file) as f:
                cached = json.load(f)
                if cached.get('papers'):
                    self.stats['cache_hits'] += 1
                    print(f"[FetchAdapter] 使用缓存: {len(cached['papers'])} 篇论文")
                    return cached['papers']
        
        # 实际抓取（模拟实现，实际应调用 arXiv API）
        papers = self._simulate_arxiv_fetch(keywords, max_items)
        
        # 缓存结果
        with open(cache_file, 'w') as f:
            json.dump({
                'papers': papers,
                'fetched_at': datetime.now().isoformat(),
                'keywords': keywords
            }, f, indent=2)
        
        self.stats['arxiv_fetched'] += len(papers)
        return papers
    
    def _simulate_arxiv_fetch(self, keywords: List[str], max_items: int) -> List[Dict]:
        """模拟 arXiv 抓取（实际实现应调用 API）"""
        papers = []
        
        # 今日已抓取的数据作为示例
        sample_papers = [
            {
                "title": "PMAx: An Agentic Framework for AI-Driven Process Mining",
                "url": "https://arxiv.org/abs/2603.15351",
                "authors": "Anton Antonov et al.",
                "type": "multiagent_system",
                "category": "cs.AI, cs.MA",
                "abstract": "AI-driven process mining using multi-agent frameworks..."
            },
            {
                "title": "SynthAgent: A Multi-Agent LLM Framework for Realistic Patient Simulation",
                "url": "https://arxiv.org/abs/2602.08254",
                "authors": "Arman Aghaee et al.",
                "type": "multiagent_system",
                "notes": "AAAI 2026 workshop"
            },
            {
                "title": "MLE-Ideator: A Dual-Agent Framework for Machine Learning Engineering",
                "url": "https://arxiv.org/abs/2601.17596",
                "authors": "Yunxiang Zhang et al.",
                "type": "agent_framework",
                "notes": "EACL 2026"
            }
        ]
        
        # 根据关键词筛选
        for paper in sample_papers[:max_items]:
            if any(kw.lower() in paper['title'].lower() for kw in keywords):
                papers.append(paper)
        
        return papers
    
    def fetch_github(self, keywords: List[str], max_items: int = 10) -> List[Dict]:
        """
        抓取 GitHub 项目
        
        基于原有 inspiration_fetcher.py 的逻辑
        """
        print(f"[FetchAdapter] 抓取 GitHub, 关键词: {keywords}")
        
        # 模拟 GitHub 抓取
        repos = [
            {
                "name": "openclaw/openclaw",
                "url": "https://github.com/openclaw/openclaw",
                "description": "OpenClaw - AI Agent Framework",
                "stars": 60000,
                "language": "TypeScript",
                "topics": ["ai", "agent", "automation"]
            },
            {
                "name": "XiaomiMiMo/MiMo",
                "url": "https://github.com/XiaomiMiMo/MiMo",
                "description": "Xiaomi MiMo LLM",
                "stars": 15000,
                "language": "Python",
                "topics": ["llm", "ai", "machine-learning"]
            }
        ]
        
        self.stats['github_fetched'] += len(repos)
        return repos[:max_items]
    
    def fetch_rss(self, feed_url: str, max_items: int = 5) -> List[Dict]:
        """
        抓取 RSS 新闻
        
        基于原有 inspiration_fetcher.py 的逻辑
        """
        print(f"[FetchAdapter] 抓取 RSS: {feed_url}")
        
        # 模拟 RSS 抓取
        news = [
            {
                "title": "DeepSeek V4 Released with 1T Parameters",
                "url": "https://example.com/news/1",
                "source": "AI News",
                "date": datetime.now().isoformat()
            },
            {
                "title": "GPT-5.4 Surpasses Human Performance",
                "url": "https://example.com/news/2",
                "source": "Tech News",
                "date": datetime.now().isoformat()
            }
        ]
        
        self.stats['rss_fetched'] += len(news)
        return news[:max_items]
    
    def fetch(self, source_id: str, source_type: str, 
              max_items: int, keywords: List[str]) -> Dict[str, Any]:
        """
        统一抓取接口
        
        根据源类型调用对应的抓取方法
        """
        start_time = time.time()
        
        if source_type == 'arxiv':
            items = self.fetch_arxiv(keywords, max_items)
        elif source_type == 'github':
            items = self.fetch_github(keywords, max_items)
        elif source_type == 'rss':
            items = self.fetch_rss(keywords[0] if keywords else '', max_items)
        else:
            items = []
        
        elapsed = time.time() - start_time
        
        return {
            'source_id': source_id,
            'source_type': source_type,
            'items': items,
            'count': len(items),
            'elapsed_seconds': elapsed,
            'keywords': keywords
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


def test_fetch_adapter():
    """测试抓取适配器"""
    print("="*60)
    print("测试 Fetch Adapter")
    print("="*60)
    
    adapter = FetchAdapter()
    
    # 测试 arXiv 抓取
    print("\n--- 测试 arXiv ---")
    papers = adapter.fetch_arxiv(['multi-agent', 'llm'], max_items=3)
    print(f"抓取到 {len(papers)} 篇论文")
    for p in papers[:2]:
        print(f"  - {p['title'][:50]}...")
    
    # 测试 GitHub 抓取
    print("\n--- 测试 GitHub ---")
    repos = adapter.fetch_github(['ai', 'agent'], max_items=2)
    print(f"抓取到 {len(repos)} 个项目")
    for r in repos:
        print(f"  - {r['name']}: {r['stars']} stars")
    
    # 查看统计
    print("\n--- 统计 ---")
    print(json.dumps(adapter.get_stats(), indent=2))
    
    print("\n✅ Fetch Adapter 测试完成")


if __name__ == '__main__':
    test_fetch_adapter()
