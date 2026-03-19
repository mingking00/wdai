#!/usr/bin/env python3
"""
灵感摄取系统 - GitHub监控器
监控GitHub仓库的Release、Commit和Trending
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# 导入系统模块
import sys
CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

from models import InspirationRecord, InspirationSource, CrawlResult
from config_manager import get_config


class GitHubMonitor:
    """
    GitHub项目监控器
    监控GitHub仓库的Release、Trending等动态
    """
    
    API_BASE = "https://api.github.com"
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.token = self.config.github_token()
        self.monitored_repos = self.config.github_monitored_repos()
        self.trending_languages = self.config.github_trending_languages()
        self.min_stars = self.config.github_min_stars()
        
        self.errors: List[str] = []
        self._rate_limit_remaining = None
    
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """发起GitHub API请求"""
        url = f"{self.API_BASE}{endpoint}"
        
        headers = {
            'User-Agent': 'InspirationBot/1.0',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as response:
                # 更新速率限制信息
                self._rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
                data = response.read().decode('utf-8')
                return json.loads(data)
                
        except HTTPError as e:
            if e.code == 404:
                self.errors.append(f"资源不存在: {endpoint}")
            elif e.code == 403:
                self.errors.append(f"API速率限制或权限不足: {endpoint}")
            else:
                self.errors.append(f"HTTP错误 {e.code}: {endpoint}")
            return None
            
        except URLError as e:
            self.errors.append(f"网络错误: {e}")
            return None
        
        except Exception as e:
            self.errors.append(f"请求失败: {e}")
            return None
    
    def crawl(self, crawl_type: str = "all") -> Tuple[CrawlResult, List[InspirationRecord]]:
        """
        执行GitHub抓取
        
        Args:
            crawl_type: 'all', 'releases', 'trending', 'repos'
        
        Returns:
            (CrawlResult, List[InspirationRecord])
        """
        start_time = time.time()
        self.errors = []
        all_inspirations: List[InspirationRecord] = []
        
        print(f"[GitHubMonitor] 开始监控 GitHub...")
        
        # 监控Release
        if crawl_type in ["all", "releases"] and self.config.github_check_releases():
            print("  - 检查仓库Releases...")
            for repo_config in self.monitored_repos:
                if repo_config.get('track_releases', True):
                    inspirations = self._check_repo_releases(
                        repo_config['owner'],
                        repo_config['repo'],
                        repo_config.get('priority', 'medium')
                    )
                    all_inspirations.extend(inspirations)
        
        # 监控Trending
        if crawl_type in ["all", "trending"] and self.config.github_check_trending():
            print("  - 检查Trending榜单...")
            for lang in self.trending_languages:
                inspirations = self._fetch_trending(lang)
                all_inspirations.extend(inspirations)
        
        # 去重
        unique_inspirations = self._deduplicate(all_inspirations)
        
        # 质量评分
        scored_inspirations = self._score_items(unique_inspirations)
        
        duration = time.time() - start_time
        
        print(f"[GitHubMonitor] 监控完成: {len(scored_inspirations)} 条灵感")
        
        return CrawlResult(
            success=len(self.errors) == 0 or len(scored_inspirations) > 0,
            source="github",
            items_found=len(all_inspirations),
            items_new=len(unique_inspirations),
            items_duplicate=len(all_inspirations) - len(unique_inspirations),
            items_filtered=len(scored_inspirations),
            errors=self.errors,
            duration_seconds=duration
        ), scored_inspirations
    
    def _check_repo_releases(self, owner: str, repo: str, priority: str = "medium") -> List[InspirationRecord]:
        """检查仓库的最新Release"""
        endpoint = f"/repos/{owner}/{repo}/releases"
        releases = self._make_request(endpoint)
        
        if not releases:
            return []
        
        inspirations = []
        
        # 只取最新的3个release
        for release in releases[:3]:
            record = InspirationRecord(
                title=f"[{owner}/{repo}] {release.get('name', 'New Release')}",
                url=release.get('html_url', ''),
                source=InspirationSource.GITHUB_RELEASE.value,
                source_type="release",
                summary=release.get('body', '')[:1000] if release.get('body') else "",
                abstract=release.get('body', '')[:500] if release.get('body') else "",
                project_name=repo,
                project_owner=owner,
                published_at=release.get('published_at', ''),
                priority=priority,
                metadata={
                    "release_tag": release.get('tag_name', ''),
                    "is_prerelease": release.get('prerelease', False),
                    "author": release.get('author', {}).get('login', '')
                }
            )
            inspirations.append(record)
        
        return inspirations
    
    def _fetch_trending(self, language: str = "python") -> List[InspirationRecord]:
        """
        获取Trending仓库
        注意: GitHub API没有直接的Trending端点，我们使用搜索API模拟
        """
        # 获取最近一周创建的star增长最多的仓库
        # 这是一个简化的实现
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # 搜索最近更新的高star仓库
        query = f"language:{language} stars:>{self.min_stars} pushed:>{one_week_ago}"
        endpoint = f"/search/repositories?q={query}&sort=updated&order=desc&per_page=10"
        
        result = self._make_request(endpoint)
        
        if not result or 'items' not in result:
            return []
        
        inspirations = []
        
        for item in result['items'][:10]:
            record = InspirationRecord(
                title=f"[Trending] {item.get('full_name', '')}",
                url=item.get('html_url', ''),
                source=InspirationSource.GITHUB_TRENDING.value,
                source_type="repo",
                summary=item.get('description', '') or "",
                abstract=item.get('description', '') or "",
                project_name=item.get('name', ''),
                project_owner=item.get('owner', {}).get('login', ''),
                keywords=[language],
                metadata={
                    "stars": item.get('stargazers_count', 0),
                    "forks": item.get('forks_count', 0),
                    "language": item.get('language', ''),
                    "topics": item.get('topics', []),
                    "language_filter": language
                }
            )
            inspirations.append(record)
        
        return inspirations
    
    def _deduplicate(self, items: List[InspirationRecord]) -> List[InspirationRecord]:
        """根据URL去重"""
        seen_urls = set()
        unique = []
        
        for item in items:
            url_key = item.url.split('?')[0]
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                unique.append(item)
        
        return unique
    
    def _score_items(self, items: List[InspirationRecord]) -> List[InspirationRecord]:
        """为GitHub项目计算质量分数"""
        weights = self.config.quality_weights()
        
        for item in items:
            scores = {}
            metadata = item.metadata
            
            # 相关性评分 - 基于是否在监控列表
            monitored = any(
                item.project_owner == repo.get('owner') and item.project_name == repo.get('repo')
                for repo in self.monitored_repos
            )
            scores['relevance'] = 0.9 if monitored else 0.6
            
            # 新颖性评分
            scores['novelty'] = 0.8 if item.source == InspirationSource.GITHUB_RELEASE.value else 0.6
            
            # 影响力评分 - 基于star数
            stars = metadata.get('stars', 0)
            if stars > 10000:
                scores['impact'] = 1.0
            elif stars > 5000:
                scores['impact'] = 0.9
            elif stars > 1000:
                scores['impact'] = 0.8
            else:
                scores['impact'] = 0.6
            
            # 时效性评分
            scores['timeliness'] = 0.9 if item.source == InspirationSource.GITHUB_RELEASE.value else 0.7
            
            # 计算加权总分
            total = sum(scores[k] * weights.get(k, 0.25) for k in scores)
            item.quality_score = round(total, 2)
            
            # 记录子分数
            item.relevance_score = round(scores['relevance'], 2)
            item.novelty_score = round(scores['novelty'], 2)
            item.impact_score = round(scores['impact'], 2)
            item.timeliness_score = round(scores['timeliness'], 2)
        
        # 按分数排序
        items.sort(key=lambda x: x.quality_score, reverse=True)
        
        return items
    
    def get_rate_limit(self) -> Dict[str, Any]:
        """获取API速率限制信息"""
        result = self._make_request('/rate_limit')
        return result or {}


def test_github_monitor():
    """测试GitHub监控器"""
    print("=" * 60)
    print("测试 GitHub 监控器")
    print("=" * 60)
    
    monitor = GitHubMonitor()
    
    # 检查速率限制
    rate_limit = monitor.get_rate_limit()
    if rate_limit:
        core = rate_limit.get('resources', {}).get('core', {})
        print(f"\nAPI速率限制:")
        print(f"  剩余: {core.get('remaining', 'N/A')}")
        print(f"  重置时间: {datetime.fromtimestamp(core.get('reset', 0))}")
    
    # 执行监控
    result, inspirations = monitor.crawl()
    
    print(f"\n监控结果:")
    print(f"  成功: {result.success}")
    print(f"  发现: {result.items_found} 条")
    print(f"  去重后: {result.items_new} 条")
    print(f"  耗时: {result.duration_seconds:.2f} 秒")
    
    if result.errors:
        print(f"\n错误:")
        for error in result.errors:
            print(f"  - {error}")
    
    print(f"\n前5条灵感:")
    for i, item in enumerate(inspirations[:5], 1):
        print(f"\n{i}. {item.title[:60]}...")
        print(f"   来源: {item.source} | 质量分: {item.quality_score}")
        print(f"   URL: {item.url}")
    
    return result, inspirations


if __name__ == "__main__":
    test_github_monitor()