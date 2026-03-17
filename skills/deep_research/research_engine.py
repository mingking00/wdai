"""
研究引擎核心

整合 WebRooter 设计:
- ResearchKernel: 页面获取与回退
- MindSearchPipeline: 深度研究流程
- Citation System: 引用追溯
"""

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set
from urllib.parse import urlparse

from .cache import TieredCache
from .citation import build_citations, format_references
from .config import ResearchConfig


@dataclass
class ResearchResult:
    """研究结果"""
    success: bool
    answer: str
    citations: List[Dict]
    references_text: str
    sources: List[Dict]
    exploration_path: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class ResearchEngine:
    """
    研究引擎
    
    提供三种研究模式:
    - quick: 仅搜索摘要
    - standard: 搜索 + 抓取详情
    - deep: MindSearch 风格深度研究
    """
    
    def __init__(self, config: Optional[ResearchConfig] = None):
        self.config = config or ResearchConfig()
        self.cache = TieredCache(self.config)
        self._search_semaphore = asyncio.Semaphore(5)  # 并发限制
    
    async def research(
        self,
        query: str,
        depth: Literal["quick", "standard", "deep"] = "standard",
        sources: Optional[List[str]] = None
    ) -> ResearchResult:
        """
        执行研究任务
        
        Args:
            query: 研究问题
            depth: 研究深度
            sources: 搜索源列表
        
        Returns:
            ResearchResult
        """
        try:
            if depth == "quick":
                return await self._quick_research(query)
            elif depth == "deep":
                return await self._deep_research(query)
            else:
                return await self._standard_research(query, sources)
        except Exception as e:
            return ResearchResult(
                success=False,
                answer=f"",
                citations=[],
                references_text="",
                sources=[],
                error=str(e),
                metadata={"error_type": type(e).__name__}
            )
    
    async def _quick_research(self, query: str) -> ResearchResult:
        """快速研究 - 仅搜索摘要"""
        # 检查缓存
        cache_key = f"quick:{hashlib.md5(query.encode()).hexdigest()}"
        cached = await self.cache.get(cache_key)
        if cached:
            return ResearchResult(**cached)
        
        # 搜索
        async with self._search_semaphore:
            search_results = await self._search_with_fallback(query)
        
        # 构建引用
        citations = build_citations(search_results, query)
        references_text = format_references(citations)
        
        # 生成摘要
        answer = self._generate_quick_answer(query, search_results)
        
        result = ResearchResult(
            success=True,
            answer=answer,
            citations=citations,
            references_text=references_text,
            sources=search_results,
            metadata={"mode": "quick", "sources_count": len(search_results)}
        )
        
        await self.cache.set(cache_key, result.__dict__)
        return result
    
    async def _standard_research(
        self,
        query: str,
        sources: Optional[List[str]] = None
    ) -> ResearchResult:
        """标准研究 - 搜索 + 抓取详情"""
        # 搜索
        async with self._search_semaphore:
            search_results = await self._search_with_fallback(query)
        
        if not search_results:
            return ResearchResult(
                success=False,
                answer=f"未找到关于「{query}」的信息",
                citations=[],
                references_text="",
                sources=[],
                metadata={"mode": "standard", "sources_count": 0}
            )
        
        # 并行抓取前 N 个结果
        top_results = search_results[:self.config.num_results]
        fetch_tasks = [
            self._smart_fetch(r.get("url", ""))
            for r in top_results
        ]
        fetched_contents = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        # 合并搜索结果和抓取内容
        enriched_sources = []
        for i, (search_result, fetch_result) in enumerate(zip(top_results, fetched_contents)):
            if isinstance(fetch_result, Exception):
                content = search_result.get("snippet", "")
                fetch_success = False
            else:
                content = fetch_result.get("content", search_result.get("snippet", ""))
                fetch_success = fetch_result.get("success", False)
            
            enriched_sources.append({
                **search_result,
                "full_content": content[:5000],
                "fetch_success": fetch_success
            })
        
        # 构建引用
        citations = build_citations(enriched_sources, query)
        references_text = format_references(citations)
        
        # 生成答案
        answer = self._generate_detailed_answer(query, enriched_sources)
        
        return ResearchResult(
            success=True,
            answer=answer,
            citations=citations,
            references_text=references_text,
            sources=enriched_sources,
            metadata={
                "mode": "standard",
                "fetched_count": len([s for s in enriched_sources if s.get("fetch_success")])
            }
        )
    
    async def _deep_research(self, query: str) -> ResearchResult:
        """深度研究 - MindSearch 风格"""
        # 1. 分解种子查询
        seeds = await self._decompose_query(query)
        
        # 2. 层级执行
        all_sources = []
        all_exploration = []
        
        # 第 0 层：原始查询
        async with self._search_semaphore:
            root_results = await self._search_with_fallback(query)
        all_sources.extend(root_results)
        all_exploration.append({
            "depth": 0,
            "query": query,
            "results_count": len(root_results)
        })
        
        # 第 1 层：种子查询（并行）
        seed_results_list = await asyncio.gather(*[
            self._search_with_fallback(seed["query"])
            for seed in seeds
        ])
        
        for seed, results in zip(seeds, seed_results_list):
            all_sources.extend(results)
            all_exploration.append({
                "depth": 1,
                "query": seed["query"],
                "rationale": seed.get("rationale", ""),
                "results_count": len(results)
            })
        
        # 去重 (基于 URL)
        seen_urls: Set[str] = set()
        unique_sources = []
        for s in all_sources:
            url = s.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(s)
        
        # 构建引用
        citations = build_citations(unique_sources, query)
        references_text = format_references(citations)
        
        # 生成综合答案
        answer = self._generate_comprehensive_answer(query, unique_sources, seeds)
        
        return ResearchResult(
            success=True,
            answer=answer,
            citations=citations,
            references_text=references_text,
            sources=unique_sources,
            exploration_path=all_exploration,
            metadata={
                "mode": "deep",
                "total_sources": len(unique_sources),
                "seeds": len(seeds),
                "exploration_levels": len(all_exploration)
            }
        )
    
    async def _search_with_fallback(self, query: str) -> List[Dict]:
        """搜索并自动回退 - 支持多种搜索源"""
        results = []
        
        # 尝试使用 web_search 工具 (OpenClaw 内置 - 需要 BRAVE_API_KEY)
        try:
            from tools.web_search import web_search
            search_results = web_search(query, count=self.config.num_results)
            if search_results:
                for item in search_results:
                    results.append({
                        "title": item.get("title", "Untitled"),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", item.get("description", "")),
                        "domain": item.get("domain", "")
                    })
                if results:
                    return results
        except Exception:
            pass
        
        # 备选：使用 DuckDuckGo (无需 API Key)
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=self.config.num_results):
                    results.append({
                        "title": r["title"],
                        "url": r["href"],
                        "snippet": r["body"],
                        "domain": r.get("domain", "")
                    })
                if results:
                    return results
        except Exception:
            pass
        
        return results
    
    def _normalize_search_results(self, results: List[Dict]) -> List[Dict]:
        """标准化搜索结果格式"""
        normalized = []
        for i, item in enumerate(results):
            normalized.append({
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", item.get("description", "")),
                "rank": i + 1,
                "domain": item.get("domain", "")
            })
        return normalized
    
    async def _smart_fetch(self, url: str) -> Dict[str, Any]:
        """
        智能抓取：HTTP 优先，失败时自动回退到 Browser
        """
        if not url:
            return {"success": False, "error": "Empty URL"}
        
        # 检查缓存
        cache_key = f"fetch:{hashlib.md5(url.encode()).hexdigest()}"
        cached = await self.cache.get(cache_key)
        if cached:
            return {"success": True, "source": "cache", **cached}
        
        # HTTP 尝试
        try:
            # 尝试 web_fetch (OpenClaw 内置)
            try:
                from tools.web_fetch import web_fetch
                result = web_fetch(url)
                if result and len(result) > 100:
                    data = {
                        "success": True,
                        "content": result[:self.config.max_html_chars],
                        "mode": "http",
                        "url": url
                    }
                    await self.cache.set(cache_key, data)
                    return data
            except ImportError:
                pass
            
            # 尝试 kimi_fetch
            try:
                from kimi_fetch import kimi_fetch
                result = kimi_fetch(url)
                if result and len(result) > 100:
                    data = {
                        "success": True,
                        "content": result[:self.config.max_html_chars],
                        "mode": "http",
                        "url": url
                    }
                    await self.cache.set(cache_key, data)
                    return data
            except ImportError:
                pass
        except Exception:
            pass
        
        # Browser 兜底
        if self.config.auto_fallback:
            try:
                from browser import browser_snapshot
                snapshot = await browser_snapshot(url)
                content = snapshot.get("text", "") if isinstance(snapshot, dict) else str(snapshot)
                data = {
                    "success": True,
                    "content": content[:self.config.max_html_chars],
                    "mode": "browser_fallback",
                    "url": url
                }
                await self.cache.set(cache_key, data)
                return data
            except Exception as e:
                return {"success": False, "error": f"HTTP和Browser都失败: {str(e)}", "url": url}
        
        return {"success": False, "error": "Fetch failed", "url": url}
    
    async def _decompose_query(self, query: str) -> List[Dict[str, str]]:
        """
        分解种子查询
        
        启发式分解，可扩展为 LLM 驱动
        """
        keywords = ["对比", "区别", "vs", "比较", "优劣", "对比分析"]
        
        if any(k in query.lower() for k in keywords):
            # 对比类查询分解
            return [
                {"query": f"{query} 优点优势特点", "rationale": "收集正面信息"},
                {"query": f"{query} 缺点劣势不足", "rationale": "收集反面信息"},
                {"query": f"{query} 使用场景案例", "rationale": "了解适用范围"},
            ]
        
        # 检查是否是技术类查询
        tech_keywords = ["教程", "指南", "入门", "学习"]
        if any(k in query for k in tech_keywords):
            return [
                {"query": f"{query} 基础概念", "rationale": "了解基础知识"},
                {"query": f"{query} 实践教程", "rationale": "获取实践指导"},
                {"query": f"{query} 最佳实践", "rationale": "了解最佳实践"},
            ]
        
        # 默认分解
        return [
            {"query": f"{query} 最新动态", "rationale": "获取最新信息"},
            {"query": f"{query} 详细介绍", "rationale": "获取详细内容"},
        ]
    
    def _generate_quick_answer(self, query: str, sources: List[Dict]) -> str:
        """生成快速答案摘要"""
        if not sources:
            return f"未找到关于「{query}」的信息"
        
        summary = f"关于「{query}」的快速摘要：\n\n"
        for i, s in enumerate(sources[:5], 1):
            title = s.get("title", "Untitled")
            snippet = s.get("snippet", "No snippet")[:200]
            summary += f"{i}. **{title}**\n   {snippet}...\n\n"
        
        summary += f"共找到 {len(sources)} 个来源"
        return summary
    
    def _generate_detailed_answer(self, query: str, sources: List[Dict]) -> str:
        """生成详细答案"""
        if not sources:
            return f"未找到关于「{query}」的详细信息"
        
        summary = f"## 关于「{query}」的研究结果\n\n"
        summary += f"基于 {len(sources)} 个来源的综合分析：\n\n"
        
        for i, s in enumerate(sources[:5], 1):
            title = s.get("title", "Untitled")
            content = s.get("full_content", s.get("snippet", ""))
            domain = s.get("domain", "")
            url = s.get("url", "")
            
            summary += f"### {i}. {title}\n"
            summary += f"{content[:600]}...\n\n"
            if domain:
                summary += f"*来源: [{domain}]({url})*\n\n"
        
        return summary
    
    def _generate_comprehensive_answer(
        self,
        query: str,
        sources: List[Dict],
        seeds: List[Dict]
    ) -> str:
        """生成综合答案 (深度研究)"""
        if not sources:
            return f"未找到关于「{query}」的深度信息"
        
        summary = f"# 「{query}」深度研究报告\n\n"
        
        summary += f"## 研究概况\n"
        summary += f"- **原始查询**: {query}\n"
        summary += f"- **探索维度**: {len(seeds)} 个方向\n"
        summary += f"- **数据来源**: {len(sources)} 个唯一来源\n\n"
        
        summary += f"## 关键发现\n"
        for i, s in enumerate(sources[:10], 1):
            title = s.get("title", "Untitled")
            domain = s.get("domain", "")
            snippet = s.get("snippet", "")
            
            summary += f"{i}. **{title}**"
            if domain:
                summary += f" ([{domain}]({s.get('url', '')}))"
            summary += "\n"
            if snippet:
                summary += f"   - {snippet[:150]}...\n"
        
        summary += f"\n## 探索路径\n"
        for seed in seeds:
            summary += f"- **{seed.get('rationale', '')}**: {seed.get('query', '')}\n"
        
        summary += f"\n---\n"
        summary += f"*研究报告由 Deep Research Skill 生成*\n"
        
        return summary
