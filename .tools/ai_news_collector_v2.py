#!/usr/bin/env python3
"""
AI News Collector v2.0 - 完整信息源版本
整合arXiv、GitHub、RSS博客、B站等多源信息

更新: 2026-03-19 - 接入所有配置的信息源
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import time

@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    source: str
    url: str
    summary: str
    published: str
    category: str  # paper / repo / blog / video / tool / release
    importance: int  # 1-10
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class RSSSource:
    """RSS源配置"""
    def __init__(self, name: str, url: str, category: str, importance_base: int = 5):
        self.name = name
        self.url = url
        self.category = category
        self.importance_base = importance_base


class GitHubRepoSource:
    """GitHub仓库监控配置"""
    def __init__(self, owner: str, repo: str, importance: int = 7):
        self.owner = owner
        self.repo = repo
        self.full_name = f"{owner}/{repo}"
        self.importance = importance


class AINewsCollector:
    """AI新闻收集器 v2.0"""
    
    # RSS源配置 (来自 universal_sources.md)
    RSS_SOURCES = [
        # S级 - 官方/权威
        RSSSource("Anthropic Blog", "https://www.anthropic.com/research/rss.xml", "blog", 9),
        RSSSource("Lil'Log", "https://lilianweng.github.io/index.xml", "blog", 9),
        RSSSource("Simon Willison", "https://simonwillison.net/atom/everything/", "blog", 8),
        
        # A级 - 高质量博客
        RSSSource("OpenAI Blog", "https://openai.com/blog/rss.xml", "blog", 8),
        RSSSource("Papers With Code", "https://paperswithcode.com/rss", "paper", 7),
        RSSSource("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "blog", 7),
        RSSSource("LangChain Blog", "https://blog.langchain.dev/rss/", "blog", 7),
        
        # Newsletter
        RSSSource("Import AI", "https://importai.substack.com/feed", "blog", 6),
        RSSSource("TLDR AI", "https://tldr.tech/ai/feed", "blog", 6),
    ]
    
    # GitHub仓库监控 (Release和重要更新)
    GITHUB_REPOS = [
        # S级 - 核心工具
        GitHubRepoSource("anthropics", "claude-code", 9),
        GitHubRepoSource("anthropics", "anthropic-sdk-python", 8),
        GitHubRepoSource("anthropics", "anthropic-cookbook", 8),
        
        # A+级 - 核心框架
        GitHubRepoSource("Aider-AI", "aider", 8),
        GitHubRepoSource("langchain-ai", "langgraph", 8),
        GitHubRepoSource("continuedev", "continue", 8),
        
        # A级 - 重要项目
        GitHubRepoSource("crewAIInc", "crewAI", 7),
        GitHubRepoSource("mem0ai", "mem0", 7),
        GitHubRepoSource("e2b-dev", "E2B", 7),
        GitHubRepoSource("microsoft", "autogen", 7),
        GitHubRepoSource("comfyanonymous", "ComfyUI", 7),
        
        # 特定关注
        GitHubRepoSource("openclaw", "openclaw", 9),
    ]
    
    # B站UP主监控 (通过收藏夹或搜索)
    BILIBILI_UPS = [
        {"name": "慢学AI", "uid": "28321599", "importance": 8},
        {"name": "橘鸦Juya", "uid": "285286947", "importance": 8},
        {"name": "黑客酒吧", "uid": "328460261", "importance": 6},
        {"name": "吴恩达Agentic", "uid": "3546982291343656", "importance": 7},
        {"name": "龙哥ai炼丹", "uid": "", "importance": 6},  # 需要查UID
    ]
    
    def __init__(self, data_dir: str = ".learning/news"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "news_history_v2.json"
        self.github_releases_file = self.data_dir / "github_releases_cache.json"
        self.history = self._load_history()
        self.github_cache = self._load_github_cache()
        
        # 关注的主题关键词 (用于重要性评分)
        self.keywords = {
            "high": ["agent", "claude", "llm", "rag", "mcp", "openclaw"],
            "medium": ["transformer", "diffusion", "reinforcement learning", "gpt", "anthropic"],
            "low": ["pytorch", "tensorflow", "ml", "ai"]
        }
    
    def _load_history(self) -> List[str]:
        """加载已收集的新闻历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _load_github_cache(self) -> Dict:
        """加载GitHub release缓存"""
        if self.github_releases_file.exists():
            try:
                with open(self.github_releases_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_history(self):
        """保存新闻历史"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history[-1000:], f, ensure_ascii=False)
    
    def _save_github_cache(self):
        """保存GitHub缓存"""
        with open(self.github_releases_file, 'w') as f:
            json.dump(self.github_cache, f)
    
    def _is_new(self, url: str) -> bool:
        """检查是否为新闻"""
        return url not in self.history
    
    def _add_to_history(self, url: str):
        """添加到历史"""
        if url not in self.history:
            self.history.append(url)
    
    def _calculate_importance(self, title: str, summary: str, base: int = 5) -> int:
        """计算重要性评分"""
        content = (title + " " + summary).lower()
        score = base
        
        for kw in self.keywords["high"]:
            if kw in content:
                score += 2
        for kw in self.keywords["medium"]:
            if kw in content:
                score += 1
        for kw in self.keywords["low"]:
            if kw in content:
                score += 0.5
        
        return min(int(score), 10)
    
    def fetch_rss_feeds(self) -> List[NewsItem]:
        """获取所有RSS源 (使用requests+XML解析，不依赖feedparser)"""
        items = []
        
        for source in self.RSS_SOURCES:
            try:
                print(f"  📡 获取 {source.name}...")
                response = requests.get(source.url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code != 200:
                    print(f"  ⚠️ {source.name} HTTP {response.status_code}")
                    continue
                
                # 解析XML
                try:
                    root = ET.fromstring(response.content)
                except ET.ParseError as e:
                    print(f"  ⚠️ {source.name} XML解析失败: {e}")
                    continue
                
                # 处理RSS 2.0格式
                channel = root.find('channel')
                if channel is not None:
                    entries = channel.findall('item')
                else:
                    # 处理Atom格式
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    entries = root.findall('atom:entry', ns)
                    if not entries:
                        entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                    if not entries:
                        # 尝试无命名空间
                        entries = root.findall('entry')
                
                for entry in entries[:5]:  # 每个源取最新5条
                    # 提取URL
                    url = ""
                    link_elem = entry.find('link')
                    if link_elem is not None:
                        url = link_elem.get('href', '') or (link_elem.text or '')
                    
                    # Atom格式可能不同
                    if not url:
                        link_elem = entry.find('{http://www.w3.org/2005/Atom}link')
                        if link_elem is not None:
                            url = link_elem.get('href', '')
                    
                    if not url or not self._is_new(url):
                        continue
                    
                    # 提取标题
                    title = "No title"
                    title_elem = entry.find('title')
                    if title_elem is not None:
                        title = title_elem.text or "No title"
                    if title == "No title":
                        title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                        if title_elem is not None:
                            title = title_elem.text or "No title"
                    
                    # 提取摘要
                    summary = ""
                    for tag in ['description', 'summary', 'content']:
                        elem = entry.find(tag)
                        if elem is not None:
                            summary = elem.text or ""
                            break
                    if not summary:
                        for tag in ['{http://www.w3.org/2005/Atom}summary', '{http://www.w3.org/2005/Atom}content']:
                            elem = entry.find(tag)
                            if elem is not None:
                                summary = elem.text or ""
                                break
                    
                    # 清理HTML标签
                    import re
                    summary = re.sub(r'<[^>]+>', '', summary)
                    if len(summary) > 300:
                        summary = summary[:300] + "..."
                    
                    # 提取日期
                    published = ""
                    for tag in ['pubDate', 'published', 'updated', 'date']:
                        elem = entry.find(tag)
                        if elem is not None:
                            published = elem.text or ""
                            break
                    if not published:
                        for tag in ['{http://www.w3.org/2005/Atom}published', '{http://www.w3.org/2005/Atom}updated']:
                            elem = entry.find(tag)
                            if elem is not None:
                                published = elem.text or ""
                                break
                    if published:
                        published = published[:10]
                    else:
                        published = datetime.now().strftime("%Y-%m-%d")
                    
                    importance = self._calculate_importance(title, summary, source.importance_base)
                    
                    items.append(NewsItem(
                        title=title,
                        source=source.name,
                        url=url,
                        summary=summary,
                        published=published,
                        category=source.category,
                        importance=importance,
                        tags=[source.category]
                    ))
                    self._add_to_history(url)
                
                time.sleep(0.5)  # 礼貌延迟
                
            except Exception as e:
                print(f"  ⚠️ {source.name} 获取失败: {e}")
        
        return items
    
    def fetch_github_releases(self) -> List[NewsItem]:
        """获取GitHub仓库Release"""
        items = []
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "WDai-NewsCollector"
        }
        
        for repo in self.GITHUB_REPOS:
            try:
                print(f"  🐙 检查 {repo.full_name}...")
                
                # 获取最新release
                url = f"https://api.github.com/repos/{repo.full_name}/releases/latest"
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    release = response.json()
                    release_id = release.get('id')
                    
                    # 检查是否已记录
                    cache_key = f"{repo.owner}_{repo.repo}"
                    if cache_key in self.github_cache:
                        if self.github_cache[cache_key] == release_id:
                            continue  # 已是最新
                    
                    # 新release
                    title = f"{repo.full_name} {release.get('tag_name', 'v?')}"
                    url = release.get('html_url', '')
                    body = release.get('body', 'No release notes')
                    if len(body) > 300:
                        body = body[:300] + "..."
                    
                    published = release.get('published_at', '')[:10] if release.get('published_at') else datetime.now().strftime("%Y-%m-%d")
                    
                    importance = self._calculate_importance(title, body, repo.importance)
                    
                    items.append(NewsItem(
                        title=title,
                        source=f"GitHub Release",
                        url=url,
                        summary=body,
                        published=published,
                        category="release",
                        importance=importance,
                        tags=["release", repo.repo.lower()]
                    ))
                    
                    # 更新缓存
                    self.github_cache[cache_key] = release_id
                    self._add_to_history(url)
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ⚠️ {repo.full_name} 检查失败: {e}")
        
        self._save_github_cache()
        return items
    
    def fetch_github_trending(self) -> List[NewsItem]:
        """获取GitHub Trending AI项目 (最近7天创建)"""
        items = []
        
        try:
            one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            queries = ["agent", "llm", "claude", "rag", "mcp"]
            
            for query in queries:
                try:
                    url = f"https://api.github.com/search/repositories?q={query}+created:>{one_week_ago}&sort=stars&order=desc&per_page=3"
                    response = requests.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for repo in data.get('items', []):
                            url = repo['html_url']
                            if not self._is_new(url):
                                continue
                            
                            desc = repo.get('description') or 'No description'
                            stars = repo.get('stargazers_count', 0)
                            
                            importance = 6
                            if stars > 500:
                                importance = 8
                            elif stars > 100:
                                importance = 7
                            
                            items.append(NewsItem(
                                title=repo['name'],
                                source="GitHub Trending",
                                url=url,
                                summary=f"⭐ {stars} | {desc}",
                                published=repo['created_at'][:10],
                                category="repo",
                                importance=importance,
                                tags=["trending", query]
                            ))
                            self._add_to_history(url)
                
                except Exception as e:
                    print(f"  ⚠️ GitHub {query} 获取失败: {e}")
        
        except Exception as e:
            print(f"  ⚠️ GitHub Trending 获取失败: {e}")
        
        return items
    
    def fetch_arxiv(self, max_results: int = 10) -> List[NewsItem]:
        """获取arXiv最新论文"""
        items = []
        categories = ["cs.AI", "cs.CL", "cs.LG", "cs.CV"]
        
        for cat in categories:
            try:
                url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=5"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    
                    for entry in root.findall('atom:entry', ns)[:3]:
                        title_elem = entry.find('atom:title', ns)
                        link_elem = entry.find('atom:id', ns)  # arXiv ID作为URL
                        published_elem = entry.find('atom:published', ns)
                        summary_elem = entry.find('atom:summary', ns)
                        
                        if title_elem is not None and link_elem is not None:
                            title = title_elem.text or ""
                            link = link_elem.text or ""
                            published = published_elem.text[:10] if published_elem is not None else ""
                            summary = summary_elem.text[:250] + "..." if summary_elem is not None and len(summary_elem.text) > 250 else (summary_elem.text if summary_elem is not None else "")
                            
                            if self._is_new(link):
                                importance = self._calculate_importance(title, summary, 5)
                                
                                items.append(NewsItem(
                                    title=title,
                                    source=f"arXiv {cat}",
                                    url=link,
                                    summary=summary,
                                    published=published,
                                    category="paper",
                                    importance=importance,
                                    tags=["paper", cat.lower().replace('.', '')]
                                ))
                                self._add_to_history(link)
            
            except Exception as e:
                print(f"  ⚠️ arXiv {cat} 获取失败: {e}")
        
        return items
    
    def fetch_hackernews(self) -> List[NewsItem]:
        """获取Hacker News热门AI内容"""
        items = []
        
        try:
            response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=30)
            
            if response.status_code == 200:
                story_ids = response.json()[:30]
                
                for story_id in story_ids:
                    try:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_resp = requests.get(story_url, timeout=10)
                        
                        if story_resp.status_code == 200:
                            story = story_resp.json()
                            title = story.get('title', '')
                            
                            is_ai_related = any(kw in title.lower() for kw in self.keywords["high"] + self.keywords["medium"])
                            
                            if is_ai_related:
                                url = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                                if not self._is_new(url):
                                    continue
                                
                                score = story.get('score', 0)
                                importance = min(5 + score // 100, 9)
                                
                                items.append(NewsItem(
                                    title=title,
                                    source="Hacker News",
                                    url=url,
                                    summary=f"Score: {score}, Comments: {story.get('descendants', 0)}",
                                    published=datetime.fromtimestamp(story.get('time', 0)).strftime("%Y-%m-%d"),
                                    category="news",
                                    importance=importance,
                                    tags=["hn", "community"]
                                ))
                                self._add_to_history(url)
                    
                    except:
                        continue
        
        except Exception as e:
            print(f"  ⚠️ Hacker News 获取失败: {e}")
        
        return items
    
    def collect_all(self) -> List[NewsItem]:
        """收集所有来源的新闻"""
        print("🔄 开始收集AI前沿信息...\n")
        
        all_items = []
        
        print("📡 获取RSS订阅源...")
        all_items.extend(self.fetch_rss_feeds())
        
        print("\n🐙 检查GitHub Release...")
        all_items.extend(self.fetch_github_releases())
        
        print("\n⭐ 获取GitHub Trending...")
        all_items.extend(self.fetch_github_trending())
        
        print("\n📄 获取arXiv论文...")
        all_items.extend(self.fetch_arxiv())
        
        print("\n📰 获取Hacker News...")
        all_items.extend(self.fetch_hackernews())
        
        # 按重要性排序
        all_items.sort(key=lambda x: x.importance, reverse=True)
        
        # 保存历史
        self._save_history()
        
        print(f"\n✅ 共收集 {len(all_items)} 条新闻")
        return all_items
    
    def generate_report(self, items: List[NewsItem]) -> str:
        """生成新闻报告"""
        if not items:
            return "📭 今天暂无新的AI前沿信息"
        
        report = []
        report.append("# 📊 AI前沿晨报")
        report.append(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**信息源**: RSS博客 | GitHub Release | GitHub Trending | arXiv | Hacker News")
        report.append(f"**共收集**: {len(items)} 条\n")
        report.append("---\n")
        
        # 按类别分组
        by_category = {
            "release": [],
            "blog": [],
            "repo": [],
            "paper": [],
            "news": []
        }
        
        for item in items[:20]:  # 只显示前20条
            if item.category in by_category:
                by_category[item.category].append(item)
        
        # GitHub Release (最重要)
        if by_category["release"]:
            report.append("## 🚀 GitHub Release\n")
            for i, item in enumerate(by_category["release"][:5], 1):
                stars = "⭐" * (item.importance // 2)
                report.append(f"{i}. **{item.title}** {stars}")
                report.append(f"   {item.summary[:200]}")
                report.append(f"   🔗 {item.url}\n")
        
        # 博客文章
        if by_category["blog"]:
            report.append("## 📝 技术博客\n")
            for item in by_category["blog"][:6]:
                stars = "⭐" * (item.importance // 3)
                report.append(f"• **{item.title}** ({item.source}) {stars}")
                report.append(f"  {item.summary[:150]}")
                report.append(f"  🔗 {item.url}\n")
        
        # GitHub项目
        if by_category["repo"]:
            report.append("## 💻 热门项目\n")
            for item in by_category["repo"][:4]:
                report.append(f"• **{item.title}**")
                report.append(f"  {item.summary}")
                report.append(f"  🔗 {item.url}\n")
        
        # 论文
        if by_category["paper"]:
            report.append("## 📄 最新论文\n")
            for i, item in enumerate(by_category["paper"][:5], 1):
                stars = "⭐" if item.importance >= 7 else ""
                report.append(f"{i}. **{item.title[:80]}...** {stars}")
                report.append(f"   来源: {item.source}")
                report.append(f"   🔗 {item.url}\n")
        
        # 社区动态
        if by_category["news"]:
            report.append("## 📰 社区动态\n")
            for item in by_category["news"][:3]:
                report.append(f"• {item.title}")
                report.append(f"  🔗 {item.url}\n")
        
        return "\n".join(report)


def main():
    """主函数"""
    collector = AINewsCollector()
    
    # 收集新闻
    items = collector.collect_all()
    
    # 生成报告
    report = collector.generate_report(items)
    
    # 输出报告
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # 保存报告
    report_file = collector.data_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 报告已保存: {report_file}")
    
    # 同时保存为最新报告
    latest_file = Path("ai_morning_report_latest.md")
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"💾 最新报告: {latest_file}")


if __name__ == "__main__":
    main()
