#!/usr/bin/env python3
"""
Free Search Skill - 免费联网搜索技能 (备用版)

使用多后端实现，确保至少有一个能工作：
1. DuckDuckGo (ddgs) - 首选
2. SearXNG 实例 - 备选
3. 直接HTTP请求 - 最后备选

完全免费，无需API Key
"""

import argparse
import json
import sys
import time
from typing import List, Dict, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import urllib.request
import urllib.parse
import ssl


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    href: str
    body: str
    source: str = "unknown"
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)


class FreeSearchSkill:
    """免费联网搜索技能 - 多后端实现"""
    
    # 公共SearXNG实例列表（无需自建）
    SEARXNG_INSTANCES = [
        "https://search.sapti.me",  # 社区实例
        "https://search.bus-hit.me",
        "https://search.projectsegfault.com",
    ]
    
    def __init__(self):
        self.backends = []
        self._init_backends()
    
    def _init_backends(self):
        """初始化所有可用后端"""
        # 尝试 DuckDuckGo
        try:
            from ddgs import DDGS
            self.backends.append(("ddgs", DDGS))
        except ImportError:
            pass
        
        # 始终添加HTTP备选
        self.backends.append(("http", None))
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        timeout: int = 15
    ) -> List[SearchResult]:
        """
        执行搜索 - 自动尝试多个后端
        
        Returns:
            SearchResult 列表
        """
        results = []
        
        # 尝试 DuckDuckGo
        if any(b[0] == "ddgs" for b in self.backends):
            try:
                results = self._search_ddgs(query, max_results, timeout)
                if results:
                    return results
            except Exception as e:
                print(f"⚠️  DuckDuckGo失败: {e}", file=sys.stderr)
        
        # 尝试 SearXNG 实例
        results = self._search_searxng(query, max_results, timeout)
        if results:
            return results
        
        # 最后尝试直接HTTP
        results = self._search_http(query, max_results, timeout)
        if results:
            return results
        
        # 全部失败
        return [SearchResult(
            title="搜索失败",
            href="",
            body="所有搜索后端均不可用。请检查网络连接。",
            source="error"
        )]
    
    def _search_ddgs(self, query: str, max_results: int, timeout: int) -> List[SearchResult]:
        """使用DuckDuckGo搜索"""
        from ddgs import DDGS
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(SearchResult(
                    title=r.get('title', ''),
                    href=r.get('href', ''),
                    body=r.get('body', ''),
                    source="duckduckgo"
                ))
        return results
    
    def _search_searxng(
        self,
        query: str,
        max_results: int,
        timeout: int
    ) -> List[SearchResult]:
        """使用SearXNG实例搜索"""
        for instance in self.SEARXNG_INSTANCES:
            try:
                params = urllib.parse.urlencode({
                    'q': query,
                    'format': 'json',
                    'language': 'zh-CN',
                })
                url = f"{instance}/search?{params}"
                
                req = urllib.request.Request(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; Bot/0.1)'
                    }
                )
                
                # 禁用SSL验证（某些实例证书问题）
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    
                    results = []
                    for r in data.get('results', [])[:max_results]:
                        results.append(SearchResult(
                            title=r.get('title', ''),
                            href=r.get('url', ''),
                            body=r.get('content', '')[:300],
                            source=f"searxng ({instance})"
                        ))
                    
                    if results:
                        return results
                        
            except Exception as e:
                print(f"⚠️  {instance} 失败: {e}", file=sys.stderr)
                continue
        
        return []
    
    def _search_http(self, query: str, max_results: int, timeout: int) -> List[SearchResult]:
        """
        直接抓取DuckDuckGo HTML
        最简单但最不稳定的方案
        """
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
                }
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                html = resp.read().decode('utf-8')
                
                # 简单正则解析
                import re
                results = []
                
                # 匹配结果块
                pattern = r'class="result__a" href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</a>'
                matches = re.findall(pattern, html, re.DOTALL)
                
                for href, title, snippet in matches[:max_results]:
                    # 清理HTML标签
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                    
                    results.append(SearchResult(
                        title=title,
                        href=urllib.parse.unquote(href),
                        body=snippet,
                        source="duckduckgo-html"
                    ))
                
                return results
                
        except Exception as e:
            print(f"⚠️  HTTP搜索失败: {e}", file=sys.stderr)
            return []
    
    def format_results(
        self,
        results: List[SearchResult],
        format_type: str = "markdown"
    ) -> str:
        """格式化搜索结果"""
        if format_type == "json":
            return json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False)
        
        elif format_type == "markdown":
            lines = ["## 搜索结果\n"]
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. **[{r.title}]({r.href})**")
                lines.append(f"   `{r.source}`")
                lines.append(f"   {r.body[:250]}...\n")
            return "\n".join(lines)
        
        else:  # text
            lines = ["搜索结果:", "=" * 60]
            for r in results:
                lines.append(f"\n[{r.source}] {r.title}")
                lines.append(f"URL: {r.href}")
                lines.append(f"摘要: {r.body[:200]}\n")
            return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="免费联网搜索技能",
        epilog="示例: python3 free_search_skill.py 'Python教程' --max-results 5"
    )
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--format", choices=["markdown", "json", "text"], default="text")
    parser.add_argument("--timeout", type=int, default=15, help="超时秒数")
    
    args = parser.parse_args()
    
    print(f"🔍 搜索: {args.query}\n", file=sys.stderr)
    
    skill = FreeSearchSkill()
    results = skill.search(args.query, args.max_results, args.timeout)
    
    output = skill.format_results(results, args.format)
    print(output)


if __name__ == "__main__":
    main()
