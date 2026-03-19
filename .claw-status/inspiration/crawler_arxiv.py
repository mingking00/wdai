#!/usr/bin/env python3
"""
灵感摄取系统 - 论文抓取器
从arXiv RSS抓取AI/ML相关论文
"""

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError
import hashlib

# 导入系统模块
import sys
CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

from models import InspirationRecord, InspirationSource, CrawlResult
from config_manager import get_config


class ArxivCrawler:
    """
    arXiv论文抓取器
    从arXiv RSS Feed抓取AI相关论文
    """
    
    RSS_URL_TEMPLATE = "http://rss.arxiv.org/rss/{category}"
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.categories = self.config.arxiv_categories()
        self.keywords = [k.lower() for k in self.config.arxiv_keywords()]
        self.exclude_keywords = [k.lower() for k in self.config.arxiv_exclude_keywords()]
        self.min_quality_score = self.config.arxiv_min_quality_score()
        self.max_papers = self.config.arxiv_max_papers()
        self.download_pdf = self.config.arxiv_download_pdf()
        
        self.errors: List[str] = []
        self.session = None
    
    def crawl(self) -> CrawlResult:
        """
        执行抓取
        
        Returns:
            CrawlResult: 抓取结果统计
        """
        start_time = time.time()
        self.errors = []
        
        all_papers: List[InspirationRecord] = []
        
        print(f"[ArxivCrawler] 开始抓取 {len(self.categories)} 个分类...")
        
        for category in self.categories:
            try:
                papers = self._fetch_category(category)
                all_papers.extend(papers)
                print(f"  ✓ {category}: {len(papers)} 篇论文")
            except Exception as e:
                error_msg = f"抓取 {category} 失败: {e}"
                self.errors.append(error_msg)
                print(f"  ✗ {category}: {e}")
        
        # 去重
        unique_papers = self._deduplicate(all_papers)
        
        # 关键词过滤
        filtered_papers = self._filter_by_keywords(unique_papers)
        
        # 质量评分
        scored_papers = self._score_papers(filtered_papers)
        
        # 按分数排序
        scored_papers.sort(key=lambda x: x.quality_score, reverse=True)
        
        # 限制数量
        final_papers = scored_papers[:self.max_papers]
        
        duration = time.time() - start_time
        
        print(f"[ArxivCrawler] 抓取完成: {len(final_papers)} 篇论文通过筛选")
        
        return CrawlResult(
            success=len(self.errors) == 0 or len(final_papers) > 0,
            source="arxiv",
            items_found=len(all_papers),
            items_new=len(unique_papers),
            items_duplicate=len(all_papers) - len(unique_papers),
            items_filtered=len(final_papers),
            errors=self.errors,
            duration_seconds=duration
        ), final_papers
    
    def _fetch_category(self, category: str) -> List[InspirationRecord]:
        """抓取单个分类的RSS Feed"""
        url = self.RSS_URL_TEMPLATE.format(category=category)
        
        try:
            req = Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; InspirationBot/1.0)'
                }
            )
            
            with urlopen(req, timeout=30) as response:
                data = response.read()
        except URLError as e:
            raise Exception(f"网络请求失败: {e}")
        
        # 解析XML
        try:
            root = ET.fromstring(data)
        except ET.ParseError as e:
            raise Exception(f"XML解析失败: {e}")
        
        # 提取论文
        papers = []
        ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
        
        for item in root.findall('.//item'):
            paper = self._parse_item(item, category, ns)
            if paper:
                papers.append(paper)
        
        return papers
    
    def _parse_item(self, item: ET.Element, category: str, ns: Dict) -> Optional[InspirationRecord]:
        """解析RSS条目为论文记录"""
        try:
            title = item.find('title')
            title_text = title.text if title is not None else ""
            
            link = item.find('link')
            url = link.text if link is not None else ""
            
            description = item.find('description')
            abstract = description.text if description is not None else ""
            
            # 提取作者
            authors = []
            for creator in item.findall('dc:creator', ns):
                if creator.text:
                    authors.append(creator.text)
            
            # 提取日期
            pub_date = item.find('pubDate')
            published_at = pub_date.text if pub_date is not None else ""
            
            # 提取arXiv ID
            arxiv_id = self._extract_arxiv_id(url)
            
            # 构建记录
            record = InspirationRecord(
                title=title_text.strip(),
                url=url,
                source=InspirationSource.ARXIV.value,
                source_type="paper",
                abstract=abstract.strip() if abstract else "",
                summary=abstract.strip()[:500] if abstract else "",
                authors=authors,
                published_at=published_at,
                keywords=[],
                metadata={
                    "arxiv_id": arxiv_id,
                    "category": category,
                    "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None
                }
            )
            
            return record
            
        except Exception as e:
            self.errors.append(f"解析条目失败: {e}")
            return None
    
    def _extract_arxiv_id(self, url: str) -> Optional[str]:
        """从URL提取arXiv ID"""
        # 匹配 /abs/1234.56789 或 /abs/cs/1234567
        match = re.search(r'/abs/(\d+\.\d+|[^/]+/\d+)', url)
        if match:
            return match.group(1)
        return None
    
    def _deduplicate(self, papers: List[InspirationRecord]) -> List[InspirationRecord]:
        """根据URL去重"""
        seen_urls = set()
        unique = []
        
        for paper in papers:
            url_key = paper.url.split('?')[0]  # 移除查询参数
            if url_key not in seen_urls:
                seen_urls.add(url_key)
                unique.append(paper)
        
        return unique
    
    def _filter_by_keywords(self, papers: List[InspirationRecord]) -> List[InspirationRecord]:
        """基于关键词过滤论文"""
        if not self.keywords:
            return papers
        
        filtered = []
        
        for paper in papers:
            text_to_check = f"{paper.title} {paper.abstract}".lower()
            
            # 检查排除关键词
            excluded = any(excl in text_to_check for excl in self.exclude_keywords)
            if excluded:
                continue
            
            # 检查包含关键词
            matched = any(keyword in text_to_check for keyword in self.keywords)
            if matched:
                # 记录匹配的关键词
                paper.keywords = [k for k in self.keywords if k in text_to_check]
                filtered.append(paper)
        
        return filtered
    
    def _score_papers(self, papers: List[InspirationRecord]) -> List[InspirationRecord]:
        """为论文计算质量分数"""
        weights = self.config.quality_weights()
        
        for paper in papers:
            scores = {}
            
            # 相关性评分 - 基于关键词匹配数量
            scores['relevance'] = min(len(paper.keywords) / 3, 1.0) if paper.keywords else 0.3
            
            # 新颖性评分 - 基于发布日期
            scores['novelty'] = self._calculate_novelty(paper.published_at)
            
            # 影响力评分 - 基于标题/摘要中的影响力指标
            scores['impact'] = self._estimate_impact(paper.title, paper.abstract)
            
            # 时效性评分 - 越新分数越高
            scores['timeliness'] = self._calculate_timeliness(paper.published_at)
            
            # 计算加权总分
            total = sum(scores[k] * weights.get(k, 0.25) for k in scores)
            paper.quality_score = round(total, 2)
            
            # 记录子分数
            paper.relevance_score = round(scores['relevance'], 2)
            paper.novelty_score = round(scores['novelty'], 2)
            paper.impact_score = round(scores['impact'], 2)
            paper.timeliness_score = round(scores['timeliness'], 2)
        
        return papers
    
    def _calculate_novelty(self, published_at: str) -> float:
        """计算新颖性分数 (基于是否是最新研究)"""
        # 这里简化处理，实际应该解析日期
        # 返回一个基础分数
        return 0.7
    
    def _estimate_impact(self, title: str, abstract: str) -> float:
        """估计影响力分数"""
        text = f"{title} {abstract}".lower()
        
        # 影响力指标
        impact_indicators = [
            "state-of-the-art", "sota", "new", "novel",
            "improve", "outperform", "benchmark", "dataset",
            "framework", "system", "approach"
        ]
        
        score = 0.5
        for indicator in impact_indicators:
            if indicator in text:
                score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_timeliness(self, published_at: str) -> float:
        """计算时效性分数"""
        # 简化处理，返回基础分数
        # 实际应该解析日期计算距今时间
        return 0.8
    
    def download_paper_pdf(self, arxiv_id: str, output_dir: Path) -> Optional[Path]:
        """下载论文PDF"""
        if not arxiv_id:
            return None
        
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        output_path = output_dir / f"{arxiv_id}.pdf"
        
        try:
            req = Request(pdf_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=60) as response:
                data = response.read()
                
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(data)
            
            return output_path
            
        except Exception as e:
            self.errors.append(f"下载PDF失败 {arxiv_id}: {e}")
            return None


def test_crawler():
    """测试抓取器"""
    print("=" * 60)
    print("测试 arXiv 论文抓取器")
    print("=" * 60)
    
    crawler = ArxivCrawler()
    result, papers = crawler.crawl()
    
    print(f"\n抓取结果:")
    print(f"  成功: {result.success}")
    print(f"  发现: {result.items_found} 篇")
    print(f"  去重后: {result.items_new} 篇")
    print(f"  通过筛选: {result.items_filtered} 篇")
    print(f"  耗时: {result.duration_seconds:.2f} 秒")
    
    if result.errors:
        print(f"\n错误:")
        for error in result.errors:
            print(f"  - {error}")
    
    print(f"\n前5篇论文:")
    for i, paper in enumerate(papers[:5], 1):
        print(f"\n{i}. {paper.title[:60]}...")
        print(f"   质量分: {paper.quality_score} | 关键词: {', '.join(paper.keywords[:3])}")
        print(f"   URL: {paper.url}")
    
    return result, papers


if __name__ == "__main__":
    test_crawler()