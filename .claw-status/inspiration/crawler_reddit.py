#!/usr/bin/env python3
"""
Reddit抓取器 - 主动搜索社交媒体内容

当主源空转时，从Reddit获取AI相关讨论

Author: wdai
Version: 1.0
"""

import requests
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class RedditPost:
    """Reddit帖子"""
    id: str
    title: str
    subreddit: str
    author: str
    url: str
    permalink: str
    score: int
    num_comments: int
    created_utc: float
    selftext: str
    source: str = "reddit"
    quality_score: float = 0.5


class RedditCrawler:
    """
    Reddit抓取器
    
    使用Reddit JSON API（不需要API key）
    或使用PRAW库（需要注册app但功能更强）
    """
    
    # 默认监控的子版块
    DEFAULT_SUBREDDITS = [
        'MachineLearning',
        'LocalLLaMA',
        'ClaudeAI',
        'OpenAI',
        'singularity',
        'artificial',
    ]
    
    BASE_URL = "https://www.reddit.com"
    
    def __init__(self, data_dir: str = "data/reddit"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AcademicResearch/1.0)'
        })
    
    def fetch_subreddit(self, subreddit: str, sort: str = "hot", 
                       limit: int = 10, time_filter: str = "day") -> List[RedditPost]:
        """
        抓取指定子版块的帖子
        
        Args:
            subreddit: 子版块名称
            sort: 排序方式 (hot, new, top)
            limit: 获取数量
            time_filter: 时间过滤 (hour, day, week, month, year, all)
        """
        posts = []
        
        try:
            # 使用Reddit JSON API
            url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
            params = {'limit': limit}
            if sort == 'top':
                params['t'] = time_filter
            
            resp = self.session.get(url, params=params, timeout=30)
            
            if resp.status_code == 429:
                print(f"   Reddit限流，跳过")
                return []
            
            resp.raise_for_status()
            data = resp.json()
            
            # 解析帖子
            for child in data.get('data', {}).get('children', []):
                post_data = child.get('data', {})
                
                # 过滤掉非AI相关内容
                title = post_data.get('title', '').lower()
                selftext = post_data.get('selftext', '').lower()
                
                # 简单的AI相关性检查
                ai_keywords = ['ai', 'llm', 'gpt', 'claude', 'model', 'training', 
                              'neural', 'deep learning', 'ml', 'agent', 'mcp']
                is_ai_related = any(kw in title or kw in selftext for kw in ai_keywords)
                
                # 如果是讨论性质的帖子，提高权重
                is_discussion = post_data.get('num_comments', 0) > 5
                quality = 0.6 if is_ai_related else 0.3
                if is_discussion and is_ai_related:
                    quality = 0.75
                
                post = RedditPost(
                    id=post_data.get('id'),
                    title=post_data.get('title', ''),
                    subreddit=post_data.get('subreddit', ''),
                    author=post_data.get('author', ''),
                    url=post_data.get('url', ''),
                    permalink=f"{self.BASE_URL}{post_data.get('permalink', '')}",
                    score=post_data.get('score', 0),
                    num_comments=post_data.get('num_comments', 0),
                    created_utc=post_data.get('created_utc', 0),
                    selftext=post_data.get('selftext', '')[:500],  # 限制长度
                    source=f"reddit_{subreddit}",
                    quality_score=quality
                )
                posts.append(post)
            
            return posts
            
        except Exception as e:
            print(f"   抓取r/{subreddit}失败: {e}")
            return []
    
    def search_reddit(self, query: str, limit: int = 10) -> List[RedditPost]:
        """
        搜索Reddit内容
        
        使用Reddit搜索API
        """
        posts = []
        
        try:
            # 搜索URL
            url = f"{self.BASE_URL}/search.json"
            params = {
                'q': query,
                'limit': limit,
                'sort': 'new',
                't': 'week'  # 最近一周
            }
            
            resp = self.session.get(url, params=params, timeout=30)
            
            if resp.status_code == 429:
                print(f"   Reddit搜索限流")
                return []
            
            resp.raise_for_status()
            data = resp.json()
            
            for child in data.get('data', {}).get('children', []):
                post_data = child.get('data', {})
                
                post = RedditPost(
                    id=post_data.get('id'),
                    title=post_data.get('title', ''),
                    subreddit=post_data.get('subreddit', ''),
                    author=post_data.get('author', ''),
                    url=post_data.get('url', ''),
                    permalink=f"{self.BASE_URL}{post_data.get('permalink', '')}",
                    score=post_data.get('score', 0),
                    num_comments=post_data.get('num_comments', 0),
                    created_utc=post_data.get('created_utc', 0),
                    selftext=post_data.get('selftext', '')[:500],
                    source="reddit_search",
                    quality_score=0.7
                )
                posts.append(post)
            
            return posts
            
        except Exception as e:
            print(f"   搜索失败: {e}")
            return []
    
    def fetch_multi(self, subreddits: List[str] = None, posts_per_sub: int = 5) -> List[Dict]:
        """
        从多个子版块抓取内容
        
        主入口函数
        """
        if subreddits is None:
            subreddits = self.DEFAULT_SUBREDDITS
        
        all_posts = []
        
        print(f"   🔍 抓取Reddit内容...")
        
        for subreddit in subreddits[:3]:  # 限制数量避免请求过多
            print(f"      - r/{subreddit}")
            posts = self.fetch_subreddit(subreddit, limit=posts_per_sub)
            all_posts.extend(posts)
        
        # 转换为统一格式
        results = [self._post_to_dict(p) for p in all_posts]
        
        # 按质量分数排序
        results.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        print(f"   ✅ Reddit抓取完成: {len(results)}条讨论")
        return results
    
    def _post_to_dict(self, post: RedditPost) -> Dict:
        """转换为字典格式"""
        return {
            'id': post.id,
            'title': post.title,
            'source': post.source,
            'subreddit': post.subreddit,
            'author': post.author,
            'url': post.url if post.url != post.permalink else post.permalink,
            'permalink': post.permalink,
            'score': post.score,
            'num_comments': post.num_comments,
            'created_utc': post.created_utc,
            'content': post.selftext[:300] if post.selftext else "",
            'quality_score': post.quality_score,
            'type': 'reddit_post',
            'published': datetime.fromtimestamp(post.created_utc).isoformat() if post.created_utc else datetime.now().isoformat()
        }


def test_crawler():
    """测试抓取器"""
    print("="*60)
    print("🧪 Reddit抓取器测试")
    print("="*60)
    
    crawler = RedditCrawler()
    
    # 测试1: 单个子版块
    print("\n1. 抓取r/MachineLearning")
    posts = crawler.fetch_subreddit('MachineLearning', limit=3)
    print(f"   获取 {len(posts)} 条帖子")
    for p in posts[:2]:
        print(f"   - {p.title[:60]}... (👍{p.score} 💬{p.num_comments})")
    
    # 测试2: 搜索
    print("\n2. 搜索 'MCP protocol'")
    search_results = crawler.search_reddit('MCP protocol', limit=3)
    print(f"   搜索到 {len(search_results)} 条结果")
    for p in search_results[:2]:
        print(f"   - {p.title[:60]}...")
    
    # 测试3: 批量抓取
    print("\n3. 批量抓取多个子版块")
    multi_results = crawler.fetch_multi(posts_per_sub=2)
    print(f"   总共获取 {len(multi_results)} 条讨论")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_crawler()
