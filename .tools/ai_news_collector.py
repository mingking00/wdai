#!/usr/bin/env python3
"""
AI News Collector - AI前沿信息收集器
整合arXiv、GitHub、技术博客等多源信息
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    source: str
    url: str
    summary: str
    published: str
    category: str  # paper / repo / blog / tool
    importance: int  # 1-10

class AINewsCollector:
    """AI新闻收集器"""
    
    def __init__(self, data_dir: str = ".learning/news"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "news_history.json"
        self.history = self._load_history()
        
        # 关注的主题
        self.keywords = [
            "transformer", "llm", "agent", "diffusion", "reinforcement learning",
            "openai", "anthropic", "claude", "gpt", "mcp", "rag"
        ]
    
    def _load_history(self) -> List[str]:
        """加载已收集的新闻历史"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_history(self):
        """保存新闻历史"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history[-500:], f, ensure_ascii=False)  # 保留最近500条
    
    def _is_new(self, url: str) -> bool:
        """检查是否为新闻"""
        return url not in self.history
    
    def _add_to_history(self, url: str):
        """添加到历史"""
        self.history.append(url)
    
    def fetch_arxiv(self, max_results: int = 10) -> List[NewsItem]:
        """
        获取arXiv最新论文
        关注: cs.AI, cs.CL, cs.LG
        """
        items = []
        
        # arXiv API (使用requests直接获取XML)
        categories = ["cs.AI", "cs.CL", "cs.LG", "cs.CV"]
        
        for cat in categories:
            try:
                url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending&max_results=5"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    # 解析XML
                    root = ET.fromstring(response.content)
                    
                    # arXiv atom命名空间
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    
                    for entry in root.findall('atom:entry', ns)[:3]:
                        title_elem = entry.find('atom:title', ns)
                        link_elem = entry.find('atom:link', ns)
                        published_elem = entry.find('atom:published', ns)
                        summary_elem = entry.find('atom:summary', ns)
                        
                        if title_elem is not None and link_elem is not None:
                            title = title_elem.text or ""
                            link = link_elem.get('href', '')
                            published = published_elem.text[:10] if published_elem is not None else ""
                            summary = summary_elem.text[:200] + "..." if summary_elem is not None and len(summary_elem.text) > 200 else (summary_elem.text if summary_elem is not None else "")
                            
                            if self._is_new(link):
                                # 计算重要性
                                importance = 5
                                content = (title + " " + summary).lower()
                                for kw in self.keywords:
                                    if kw in content:
                                        importance += 1
                                
                                items.append(NewsItem(
                                    title=title,
                                    source=f"arXiv {cat}",
                                    url=link,
                                    summary=summary,
                                    published=published,
                                    category="paper",
                                    importance=min(importance, 10)
                                ))
                                self._add_to_history(link)
            
            except Exception as e:
                print(f"arXiv {cat} 获取失败: {e}")
        
        return items
    
    def fetch_github_trending(self) -> List[NewsItem]:
        """
        获取GitHub Trending AI项目
        """
        items = []
        
        try:
            # GitHub搜索API（按star排序，最近一周）
            one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            queries = [
                "llm agents",
                "transformer",
                "diffusion model",
                "openclaw"
            ]
            
            for query in queries:
                try:
                    url = f"https://api.github.com/search/repositories?q={query}+created:>{one_week_ago}&sort=stars&order=desc&per_page=3"
                    response = requests.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for repo in data.get('items', []):
                            if self._is_new(repo['html_url']):
                                items.append(NewsItem(
                                    title=repo['name'],
                                    source="GitHub",
                                    url=repo['html_url'],
                                    summary=repo.get('description', 'No description') or 'No description',
                                    published=repo['created_at'][:10],
                                    category="repo",
                                    importance=7 if repo['stargazers_count'] > 100 else 5
                                ))
                                self._add_to_history(repo['html_url'])
                
                except Exception as e:
                    print(f"GitHub {query} 获取失败: {e}")
        
        except Exception as e:
            print(f"GitHub Trending 获取失败: {e}")
        
        return items
    
    def fetch_tech_blogs(self) -> List[NewsItem]:
        """
        获取技术博客更新
        """
        items = []
        
        # 一些AI公司的博客RSS
        blog_feeds = [
            ("OpenAI Blog", "https://openai.com/blog/rss.xml"),
        ]
        
        for name, feed_url in blog_feeds:
            try:
                response = requests.get(feed_url, timeout=30)
                if response.status_code == 200:
                    # 解析XML
                    root = ET.fromstring(response.content)
                    
                    # 查找item元素
                    items_elem = root.findall('.//item')
                    
                    for entry in items_elem[:3]:
                        title = entry.find('title')
                        link = entry.find('link')
                        pub_date = entry.find('pubDate')
                        description = entry.find('description')
                        
                        if title is not None and link is not None:
                            title_text = title.text or ""
                            link_text = link.text or ""
                            
                            if self._is_new(link_text):
                                items.append(NewsItem(
                                    title=title_text,
                                    source=name,
                                    url=link_text,
                                    summary=(description.text[:150] if description is not None and description.text else "..."),
                                    published=(pub_date.text[:10] if pub_date is not None else "") ,
                                    category="blog",
                                    importance=8  # 公司博客重要性较高
                                ))
                                self._add_to_history(link_text)
            
            except Exception as e:
                print(f"{name} 获取失败: {e}")
        
        return items
    
    def fetch_hackernews(self) -> List[NewsItem]:
        """
        获取Hacker News热门AI相关内容
        """
        items = []
        
        try:
            # 获取热门故事
            response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=30)
            
            if response.status_code == 200:
                story_ids = response.json()[:30]  # 取前30个
                
                for story_id in story_ids:
                    try:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_resp = requests.get(story_url, timeout=10)
                        
                        if story_resp.status_code == 200:
                            story = story_resp.json()
                            title = story.get('title', '')
                            
                            # 检查是否AI相关
                            is_ai_related = any(kw in title.lower() for kw in self.keywords)
                            
                            if is_ai_related and self._is_new(f"hn_{story_id}"):
                                items.append(NewsItem(
                                    title=title,
                                    source="Hacker News",
                                    url=story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                                    summary=f"Score: {story.get('score', 0)}, Comments: {story.get('descendants', 0)}",
                                    published=datetime.fromtimestamp(story.get('time', 0)).strftime("%Y-%m-%d"),
                                    category="news",
                                    importance=min(5 + story.get('score', 0) // 50, 10)
                                ))
                                self._add_to_history(f"hn_{story_id}")
                    
                    except Exception as e:
                        continue
        
        except Exception as e:
            print(f"Hacker News 获取失败: {e}")
        
        return items
    
    def collect_all(self) -> List[NewsItem]:
        """收集所有来源的新闻"""
        print("🔄 开始收集AI前沿信息...")
        
        all_items = []
        
        print("  📄 获取arXiv论文...")
        all_items.extend(self.fetch_arxiv())
        
        print("  💻 获取GitHub项目...")
        all_items.extend(self.fetch_github_trending())
        
        print("  📝 获取技术博客...")
        all_items.extend(self.fetch_tech_blogs())
        
        print("  📰 获取Hacker News...")
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
        report.append("📊 **AI前沿晨报**")
        report.append(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**来源**: arXiv | GitHub | Tech Blogs | Hacker News")
        report.append(f"**共收集**: {len(items)} 条\n")
        report.append("---\n")
        
        # 按类别分组
        by_category = {
            "paper": [],
            "repo": [],
            "blog": [],
            "news": []
        }
        
        for item in items[:15]:  # 只显示前15条
            by_category[item.category].append(item)
        
        # 论文
        if by_category["paper"]:
            report.append("### 📄 最新论文\n")
            for i, item in enumerate(by_category["paper"][:5], 1):
                stars = "⭐" * (item.importance // 2)
                report.append(f"{i}. **{item.title}** {stars}")
                report.append(f"   来源: {item.source}")
                report.append(f"   摘要: {item.summary}")
                report.append(f"   🔗 {item.url}\n")
        
        # GitHub项目
        if by_category["repo"]:
            report.append("### 💻 热门项目\n")
            for i, item in enumerate(by_category["repo"][:4], 1):
                report.append(f"{i}. **{item.title}**")
                report.append(f"   {item.summary}")
                report.append(f"   🔗 {item.url}\n")
        
        # 博客
        if by_category["blog"]:
            report.append("### 📝 技术博客\n")
            for item in by_category["blog"][:3]:
                report.append(f"• **{item.title}** ({item.source})")
                report.append(f"  🔗 {item.url}\n")
        
        # 新闻
        if by_category["news"]:
            report.append("### 📰 行业动态\n")
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
    report_file = collector.data_dir / f"report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 报告已保存: {report_file}")


if __name__ == "__main__":
    main()
