#!/usr/bin/env python3
"""
arXiv深度抓取器 - 解决空转问题

当RSS没有新内容时，抓取：
1. 论文页面的trackbacks（引用）
2. 论文页面的comments
3. arXiv Sanity精选
4. 相关论文推荐

Author: wdai
Version: 1.0
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ArxivPaper:
    """arXiv论文"""
    id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    pdf_url: str
    published: str
    source: str  # 发现来源: main_rss, trackback, sanity, related
    quality_score: float = 0.5


class ArxivDeepCrawler:
    """
    arXiv深度抓取器
    
    不依赖RSS，直接抓取页面获取更深层次内容
    """
    
    BASE_URL = "https://arxiv.org"
    SANITY_URL = "http://www.arxiv-sanity.com"
    
    # 感兴趣的分类
    CATEGORIES = ['cs.AI', 'cs.CL', 'cs.LG', 'cs.RO']
    
    def __init__(self, data_dir: str = "data/arxiv_deep"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AcademicResearch/1.0)'
        })
    
    def fetch_recent_papers(self, category: str = "cs.AI", max_results: int = 10) -> List[ArxivPaper]:
        """
        从arXiv列表页抓取最新论文
        
        不依赖RSS，直接爬列表页
        """
        url = f"{self.BASE_URL}/list/{category}/recent"
        
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            papers = []
            
            # 找到论文条目
            entries = soup.find_all('dt')
            
            for entry in entries[:max_results]:
                try:
                    # 提取论文ID
                    arxiv_link = entry.find('a', href=re.compile(r'/abs/'))
                    if not arxiv_link:
                        continue
                    
                    paper_id = arxiv_link.text.strip().replace('arXiv:', '')
                    
                    # 获取标题和作者（在下一个<dd>中）
                    dd = entry.find_next_sibling('dd')
                    if not dd:
                        continue
                    
                    title_elem = dd.find('div', class_='list-title')
                    title = title_elem.text.replace('Title:', '').strip() if title_elem else "Unknown"
                    
                    authors_elem = dd.find('div', class_='list-authors')
                    authors = []
                    if authors_elem:
                        authors = [a.text.strip() for a in authors_elem.find_all('a')]
                    
                    # 摘要（需要单独请求）
                    abstract = self._fetch_abstract(paper_id)
                    
                    paper = ArxivPaper(
                        id=paper_id,
                        title=title,
                        authors=authors,
                        abstract=abstract[:500] if abstract else "",
                        url=f"{self.BASE_URL}/abs/{paper_id}",
                        pdf_url=f"{self.BASE_URL}/pdf/{paper_id}",
                        published=datetime.now().isoformat(),
                        source="arxiv_list"
                    )
                    papers.append(paper)
                    
                except Exception as e:
                    print(f"   解析条目失败: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            print(f"   抓取失败: {e}")
            return []
    
    def _fetch_abstract(self, paper_id: str) -> str:
        """获取论文摘要"""
        try:
            url = f"{self.BASE_URL}/abs/{paper_id}"
            resp = self.session.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            abstract_elem = soup.find('blockquote', class_='abstract')
            if abstract_elem:
                return abstract_elem.text.replace('Abstract:', '').strip()
            
            # 备用选择器
            abstract_elem = soup.find('meta', {'name': 'description'})
            if abstract_elem:
                return abstract_elem.get('content', '')
            
            return ""
        except:
            return ""
    
    def fetch_trackbacks(self, paper_id: str) -> List[Dict]:
        """
        抓取论文的trackbacks（引用该论文的其他文章）
        
        这在arXiv abstract页面的下方
        """
        url = f"{self.BASE_URL}/abs/{paper_id}"
        trackbacks = []
        
        try:
            resp = self.session.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找trackbacks部分
            trackback_section = soup.find('div', {'id': 'trackback'})
            if not trackback_section:
                # 尝试其他选择器
                trackback_section = soup.find('h3', string=re.compile('trackback', re.I))
                if trackback_section:
                    trackback_section = trackback_section.find_next_sibling()
            
            if trackback_section:
                links = trackback_section.find_all('a', href=True)
                for link in links:
                    trackbacks.append({
                        'title': link.text.strip(),
                        'url': link['href'],
                        'source_paper': paper_id
                    })
            
            return trackbacks
            
        except Exception as e:
            print(f"   抓取trackbacks失败: {e}")
            return []
    
    def fetch_arxiv_sanity(self, max_papers: int = 10) -> List[ArxivPaper]:
        """
        从arXiv Sanity抓取精选论文
        
        arXiv Sanity是Andrej Karpathy做的论文筛选平台
        """
        papers = []
        
        try:
            # 获取top papers
            url = f"{self.SANITY_URL}/top"
            resp = self.session.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找论文条目
            entries = soup.find_all('div', class_='paper')
            
            for entry in entries[:max_papers]:
                try:
                    # 提取标题
                    title_elem = entry.find('div', class_='title')
                    title = title_elem.text.strip() if title_elem else "Unknown"
                    
                    # 提取arXiv ID
                    link_elem = entry.find('a', href=re.compile(r'/abs/'))
                    if link_elem:
                        paper_id = link_elem['href'].split('/abs/')[-1]
                    else:
                        continue
                    
                    # 提取作者
                    authors_elem = entry.find('div', class_='authors')
                    authors = []
                    if authors_elem:
                        authors = [a.strip() for a in authors_elem.text.split(',')]
                    
                    paper = ArxivPaper(
                        id=paper_id,
                        title=title,
                        authors=authors,
                        abstract="",  # arxiv-sanity不显示摘要
                        url=f"{self.BASE_URL}/abs/{paper_id}",
                        pdf_url=f"{self.BASE_URL}/pdf/{paper_id}",
                        published=datetime.now().isoformat(),
                        source="arxiv_sanity",
                        quality_score=0.8  # Sanity精选质量更高
                    )
                    papers.append(paper)
                    
                except Exception as e:
                    continue
            
            return papers
            
        except Exception as e:
            print(f"   抓取arXiv Sanity失败: {e}")
            return []
    
    def search_by_keywords(self, keywords: List[str], max_results: int = 10) -> List[ArxivPaper]:
        """
        使用arXiv搜索API按关键词搜索
        
        arXiv有简单的搜索接口
        """
        papers = []
        query = '+AND+'.join(keywords)
        
        try:
            # arXiv搜索URL
            url = f"{self.BASE_URL}/search/?query={query}&searchtype=all&abstracts=show&order=-announced_date_first&size={max_results}"
            
            resp = self.session.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 解析搜索结果
            results = soup.find_all('li', class_='arxiv-result')
            
            for result in results[:max_results]:
                try:
                    # 提取标题
                    title_elem = result.find('p', class_='title')
                    title = title_elem.text.strip() if title_elem else "Unknown"
                    
                    # 提取ID
                    link_elem = result.find('a', href=re.compile(r'/abs/'))
                    if link_elem:
                        paper_id = link_elem['href'].split('/abs/')[-1].split('v')[0]
                    else:
                        continue
                    
                    # 提取作者
                    authors_elem = result.find('p', class_='authors')
                    authors = []
                    if authors_elem:
                        authors = [a.text.strip() for a in authors_elem.find_all('a')]
                    
                    # 提取摘要
                    abstract_elem = result.find('span', class_='abstract-short')
                    abstract = abstract_elem.text.strip() if abstract_elem else ""
                    
                    paper = ArxivPaper(
                        id=paper_id,
                        title=title,
                        authors=authors,
                        abstract=abstract[:500],
                        url=f"{self.BASE_URL}/abs/{paper_id}",
                        pdf_url=f"{self.BASE_URL}/pdf/{paper_id}",
                        published=datetime.now().isoformat(),
                        source="arxiv_search",
                        quality_score=0.6
                    )
                    papers.append(paper)
                    
                except Exception:
                    continue
            
            return papers
            
        except Exception as e:
            print(f"   搜索失败: {e}")
            return []
    
    def deep_crawl(self, primary_keywords: List[str] = None) -> List[Dict]:
        """
        深度抓取 - 主入口
        
        综合多个来源获取内容
        """
        all_items = []
        
        print("   🔍 深度抓取arXiv...")
        
        # 1. 抓取最新论文（列表页）
        print("      - 抓取列表页最新论文")
        recent = self.fetch_recent_papers(max_results=5)
        for p in recent:
            all_items.append(self._paper_to_dict(p))
        
        # 2. 抓取arXiv Sanity精选
        print("      - 抓取arXiv Sanity精选")
        sanity = self.fetch_arxiv_sanity(max_papers=5)
        for p in sanity:
            all_items.append(self._paper_to_dict(p))
        
        # 3. 关键词搜索
        if primary_keywords:
            print(f"      - 搜索关键词: {primary_keywords}")
            search_results = self.search_by_keywords(primary_keywords, max_results=5)
            for p in search_results:
                all_items.append(self._paper_to_dict(p))
        
        # 去重
        seen_ids = set()
        unique_items = []
        for item in all_items:
            if item['id'] not in seen_ids:
                seen_ids.add(item['id'])
                unique_items.append(item)
        
        print(f"   ✅ 深度抓取完成: {len(unique_items)}篇论文")
        return unique_items
    
    def _paper_to_dict(self, paper: ArxivPaper) -> Dict:
        """转换为字典格式"""
        return {
            'id': paper.id,
            'title': paper.title,
            'authors': paper.authors,
            'abstract': paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract,
            'url': paper.url,
            'pdf_url': paper.pdf_url,
            'published': paper.published,
            'source': paper.source,
            'quality_score': paper.quality_score,
            'type': 'arxiv_paper'
        }


def test_crawler():
    """测试抓取器"""
    print("="*60)
    print("🧪 arXiv深度抓取器测试")
    print("="*60)
    
    crawler = ArxivDeepCrawler()
    
    # 测试1: 抓取列表页
    print("\n1. 抓取arXiv列表页")
    papers = crawler.fetch_recent_papers(max_results=3)
    print(f"   获取 {len(papers)} 篇论文")
    for p in papers[:2]:
        print(f"   - {p.title[:60]}... [{p.id}]")
    
    # 测试2: arXiv Sanity
    print("\n2. 抓取arXiv Sanity")
    sanity_papers = crawler.fetch_arxiv_sanity(max_papers=3)
    print(f"   获取 {len(sanity_papers)} 篇精选论文")
    for p in sanity_papers[:2]:
        print(f"   - {p.title[:60]}...")
    
    # 测试3: 关键词搜索
    print("\n3. 关键词搜索")
    search_results = crawler.search_by_keywords(["AI", "agent"], max_results=3)
    print(f"   搜索到 {len(search_results)} 篇论文")
    for p in search_results[:2]:
        print(f"   - {p.title[:60]}...")
    
    # 测试4: 深度抓取
    print("\n4. 完整深度抓取")
    deep_results = crawler.deep_crawl(primary_keywords=["MCP", "Claude"])
    print(f"   总共获取 {len(deep_results)} 篇论文（去重后）")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_crawler()
