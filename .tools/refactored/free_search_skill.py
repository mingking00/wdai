#!/usr/bin/env python3
"""
Free Search Skill - CLI-Anything 风格重构
免费联网搜索

用法: python3 free_search_skill.py [进入REPL模式]
     或在 REPL 中使用: search.query <关键词>, search.status 等
"""

import sys
import json
import urllib.request
import urllib.parse
import ssl
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

# 导入核心框架
sys.path.insert(0, str(Path(__file__).parent))
from skill_generator import (
    command, CommandMetadata, arg, opt,
    CommandContext, CommandResult,
    ArgumentType,
    ReplSkin, CommandRegistry, SessionManager
)


# ============================================================================
# 数据模型
# ============================================================================

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


@dataclass
class SearchSession:
    """搜索会话状态"""
    last_query: str = ""
    last_results: List[Dict] = None
    search_count: int = 0
    preferred_backend: str = "auto"
    
    def __post_init__(self):
        if self.last_results is None:
            self.last_results = []


# ============================================================================
# 搜索后端
# ============================================================================

class SearchBackends:
    """搜索后端管理器"""
    
    SEARXNG_INSTANCES = [
        "https://search.sapti.me",
        "https://search.bus-hit.me",
        "https://search.projectsegfault.com",
    ]
    
    def __init__(self):
        self.backends = []
        self._init_backends()
    
    def _init_backends(self):
        """初始化后端"""
        try:
            from ddgs import DDGS
            self.backends.append(("ddgs", self._search_ddgs))
        except ImportError:
            pass
        
        self.backends.append(("searxng", self._search_searxng))
        self.backends.append(("http", self._search_http))
    
    def search(self, query: str, max_results: int = 5,
               timeout: int = 15, backend: str = "auto") -> List[SearchResult]:
        """执行搜索"""
        results = []
        
        # 尝试指定后端或所有后端
        backends_to_try = []
        if backend != "auto" and backend in [b[0] for b in self.backends]:
            backends_to_try = [b for b in self.backends if b[0] == backend]
        else:
            backends_to_try = self.backends
        
        for name, func in backends_to_try:
            try:
                results = func(query, max_results, timeout)
                if results:
                    return results
            except Exception as e:
                print(f"⚠️  {name} 失败: {e}", file=sys.stderr)
                continue
        
        return [SearchResult(
            title="搜索失败",
            href="",
            body="所有搜索后端均不可用。请检查网络连接。",
            source="error"
        )]
    
    def _search_ddgs(self, query: str, max_results: int, timeout: int) -> List[SearchResult]:
        """DuckDuckGo 搜索"""
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
    
    def _search_searxng(self, query: str, max_results: int, timeout: int) -> List[SearchResult]:
        """SearXNG 搜索"""
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
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; Bot/0.1)'}
                )
                
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
                            source=f"searxng"
                        ))
                    
                    if results:
                        return results
                        
            except Exception:
                continue
        
        return []
    
    def _search_http(self, query: str, max_results: int, timeout: int) -> List[SearchResult]:
        """直接 HTTP 搜索"""
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
                
                import re
                results = []
                
                pattern = r'class="result__a" href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</a>'
                matches = re.findall(pattern, html, re.DOTALL)
                
                for href, title, snippet in matches[:max_results]:
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                    
                    results.append(SearchResult(
                        title=title,
                        href=urllib.parse.unquote(href),
                        body=snippet,
                        source="duckduckgo-html"
                    ))
                
                return results
                
        except Exception:
            return []
    
    def list_backends(self) -> List[str]:
        """列出可用后端"""
        return [b[0] for b in self.backends]


# ============================================================================
# 格式化工具
# ============================================================================

class ResultFormatter:
    """结果格式化器"""
    
    @staticmethod
    def format(results: List[SearchResult], format_type: str = "markdown") -> str:
        """格式化结果"""
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


# ============================================================================
# CLI 命令定义
# ============================================================================

@command(CommandMetadata(
    name="search.query",
    description="执行搜索查询",
    category="search",
    modifies_state=True,
    undoable=False,
    requires_session=True
))
class SearchQueryCommand:
    """搜索命令"""
    
    query = arg("query", ArgumentType.STRING, help="搜索关键词")
    max_results = opt("max-results", ArgumentType.INTEGER, default=5,
                      help="返回结果数量")
    format = opt("format", ArgumentType.STRING, default="markdown",
                 choices=["markdown", "json", "text"],
                 help="输出格式")
    backend = opt("backend", ArgumentType.STRING, default="auto",
                  help="搜索后端: auto, ddgs, searxng, http")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        # 获取搜索会话状态
        search_state = ctx.session.get("search", {})
        session = SearchSession(**search_state) if search_state else SearchSession()
        
        query = ctx.args.get("query", "")
        max_results = int(ctx.options.get("max-results", 5))
        format_type = ctx.options.get("format", "markdown")
        backend = ctx.options.get("backend", "auto")
        
        # 执行搜索
        backends = SearchBackends()
        results = backends.search(query, max_results, timeout=15, backend=backend)
        
        # 更新会话状态
        session.last_query = query
        session.last_results = [r.to_dict() for r in results]
        session.search_count += 1
        ctx.session.set("search", asdict(session))
        
        # 格式化输出
        output = ResultFormatter.format(results, format_type)
        
        return CommandResult(
            success=True,
            message=f"搜索完成，找到 {len(results)} 条结果",
            data={
                "query": query,
                "results_count": len(results),
                "results": [r.to_dict() for r in results],
                "formatted": output
            }
        )


@command(CommandMetadata(
    name="search.backends",
    description="列出可用搜索后端",
    category="search",
    modifies_state=False,
    requires_session=True
))
class SearchBackendsCommand:
    """列出后端"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        backends = SearchBackends()
        
        return CommandResult(
            success=True,
            data={
                "backends": backends.list_backends(),
                "searxng_instances": SearchBackends.SEARXNG_INSTANCES
            }
        )


@command(CommandMetadata(
    name="search.last",
    description="显示上次搜索结果",
    category="search",
    modifies_state=False,
    requires_session=True
))
class SearchLastCommand:
    """显示上次结果"""
    
    format = opt("format", ArgumentType.STRING, default="markdown",
                 help="输出格式")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        search_state = ctx.session.get("search", {})
        
        last_results = search_state.get("last_results", [])
        last_query = search_state.get("last_query", "")
        
        if not last_results:
            return CommandResult(
                success=False,
                error="没有上次的搜索结果"
            )
        
        format_type = ctx.options.get("format", "markdown")
        results = [SearchResult(**r) for r in last_results]
        output = ResultFormatter.format(results, format_type)
        
        return CommandResult(
            success=True,
            message=f"上次查询: {last_query}",
            data={
                "query": last_query,
                "results": last_results,
                "formatted": output
            }
        )


@command(CommandMetadata(
    name="search.stats",
    description="显示搜索统计",
    category="search",
    modifies_state=False,
    requires_session=True
))
class SearchStatsCommand:
    """搜索统计"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        search_state = ctx.session.get("search", {})
        
        return CommandResult(
            success=True,
            data={
                "search_count": search_state.get("search_count", 0),
                "last_query": search_state.get("last_query", ""),
                "preferred_backend": search_state.get("preferred_backend", "auto")
            }
        )


@command(CommandMetadata(
    name="search.clear",
    description="清除搜索历史",
    category="search",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class SearchClearCommand:
    """清除历史"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        ctx.session.set("search", SearchSession().to_dict())
        
        return CommandResult(
            success=True,
            message="搜索历史已清除"
        )


# ============================================================================
# REPL 入口
# ============================================================================

def create_search_skill():
    """创建 Search Skill 注册表"""
    registry = CommandRegistry()
    
    registry.register(SearchQueryCommand)
    registry.register(SearchBackendsCommand)
    registry.register(SearchLastCommand)
    registry.register(SearchStatsCommand)
    registry.register(SearchClearCommand)
    
    return registry


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Free Search Skill")
    parser.add_argument("--interactive", "-i", action="store_true", help="REPL模式")
    parser.add_argument("query", nargs="?", help="搜索关键词")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--format", choices=["markdown", "json", "text"], default="markdown")
    
    args = parser.parse_args()
    
    registry = create_search_skill()
    session_manager = SessionManager()
    
    if args.query:
        # 直接搜索模式
        session = session_manager.create_session("search_cli")
        
        ctx = CommandContext(
            session=session,
            args={"query": args.query},
            options={"max-results": args.max_results, "format": args.format},
            working_dir=Path.cwd()
        )
        
        cmd = SearchQueryCommand()
        result = cmd.execute(ctx)
        
        if result.success:
            print(result.data.get("formatted", ""))
        else:
            print(f"错误: {result.error}")
    else:
        # REPL 模式
        print("🔍 Free Search Skill")
        print("命令: search.query, search.backends, search.last, search.stats, search.clear")
        print("其他: session.create, undo, redo, help, exit\n")
        
        repl = ReplSkin(registry, session_manager)
        repl.run()


if __name__ == "__main__":
    main()
