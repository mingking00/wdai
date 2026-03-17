#!/usr/bin/env python3
"""
Deep Research Skill - 演示模式

使用模拟数据展示 Skill 功能
"""

import sys
sys.path.insert(0, '.')

import asyncio
from skills.deep_research import research, run
from skills.deep_research.research_engine import ResearchEngine, ResearchResult
from skills.deep_research.citation import build_citations, format_references


# 模拟搜索结果
MOCK_SEARCH_RESULTS = {
    "Python asyncio best practices": [
        {
            "title": "Python Asyncio Best Practices - Real Python",
            "url": "https://realpython.com/python-asyncio/",
            "snippet": "Async IO is a concurrent programming design that has received dedicated support in Python...",
            "domain": "realpython.com"
        },
        {
            "title": "Asyncio Tutorial - Python Documentation",
            "url": "https://docs.python.org/3/library/asyncio.html",
            "snippet": "The asyncio library is the standard library for writing concurrent code using the async/await syntax...",
            "domain": "docs.python.org"
        },
        {
            "title": "High-performance Asyncio networking - Python.org",
            "url": "https://discuss.python.org/t/high-performance-asyncio/73420",
            "snippet": "The official docs suggest that working with socket objects directly is more convenient...",
            "domain": "discuss.python.org"
        },
        {
            "title": "Asyncio best practices - Async-SIG",
            "url": "https://discuss.python.org/t/asyncio-best-practices/12576",
            "snippet": "Async functions are not necessarily asynchronous. I've noticed that coroutines shall run in order...",
            "domain": "discuss.python.org"
        },
    ],
    "AI agent frameworks 2026": [
        {
            "title": "OpenClaw - AI Agent Framework",
            "url": "https://github.com/openclaw/openclaw",
            "snippet": "OpenClaw is an open-source AI agent framework for building intelligent applications...",
            "domain": "github.com"
        },
        {
            "title": "AutoGen - Microsoft Research",
            "url": "https://github.com/microsoft/autogen",
            "snippet": "AutoGen is a framework that enables the development of LLM applications using multiple agents...",
            "domain": "github.com"
        },
        {
            "title": "LangChain - Building applications with LLMs",
            "url": "https://langchain.com",
            "snippet": "LangChain is a framework for developing applications powered by language models...",
            "domain": "langchain.com"
        },
    ]
}


class DemoResearchEngine(ResearchEngine):
    """演示版研究引擎 - 使用模拟数据"""
    
    async def _search_with_fallback(self, query: str):
        """返回模拟搜索结果"""
        # 查找匹配的模拟数据
        for key, results in MOCK_SEARCH_RESULTS.items():
            if any(kw in query.lower() for kw in key.lower().split()):
                return results
        
        # 默认返回通用结果
        return [
            {
                "title": f"Search results for: {query}",
                "url": "https://example.com/result",
                "snippet": f"This is a simulated search result for '{query}'. In production, this would be real search results from web_search or DuckDuckGo.",
                "domain": "example.com"
            }
        ]
    
    async def _smart_fetch(self, url: str):
        """演示模式不抓取详情"""
        return {"success": False, "content": "", "mode": "demo"}


async def demo_quick_mode():
    """演示快速模式"""
    print("=" * 70)
    print("🚀 Deep Research Skill - Quick Mode Demo (Mock Data)")
    print("=" * 70)
    
    engine = DemoResearchEngine()
    result = await engine.research("Python asyncio best practices", depth="quick")
    
    print(f"\n✅ Success: {result.success}")
    print(f"📚 Sources: {len(result.sources)}")
    print(f"📝 Citations: {len(result.citations)}")
    
    print(f"\n📄 Answer:\n{result.answer}")
    
    if result.references_text:
        print(f"\n🔗 References:\n{result.references_text}")
    
    print("\n" + "=" * 70)


async def demo_standard_mode():
    """演示标准模式"""
    print("\n" + "=" * 70)
    print("🚀 Deep Research Skill - Standard Mode Demo (Mock Data)")
    print("=" * 70)
    
    engine = DemoResearchEngine()
    result = await engine.research("AI agent frameworks 2026", depth="standard")
    
    print(f"\n✅ Success: {result.success}")
    print(f"📚 Sources: {len(result.sources)}")
    print(f"📝 Citations: {len(result.citations)}")
    print(f"📊 Metadata: {result.metadata}")
    
    print(f"\n📄 Answer Preview:\n{result.answer[:500]}...")
    
    if result.references_text:
        print(f"\n🔗 References Preview:\n{result.references_text[:400]}...")
    
    print("\n" + "=" * 70)


async def demo_deep_mode():
    """演示深度模式"""
    print("\n" + "=" * 70)
    print("🚀 Deep Research Skill - Deep Mode Demo (Mock Data)")
    print("=" * 70)
    
    engine = DemoResearchEngine()
    result = await engine.research("AI agent frameworks comparison", depth="deep")
    
    print(f"\n✅ Success: {result.success}")
    print(f"📚 Sources: {len(result.sources)}")
    print(f"🗺️  Exploration Path: {len(result.exploration_path)} levels")
    
    if result.exploration_path:
        print("\n📍 Exploration Path:")
        for path in result.exploration_path:
            print(f"   Depth {path['depth']}: {path.get('rationale', path['query'])}")
    
    print(f"\n📄 Answer Preview:\n{result.answer[:800]}...")
    
    print("\n" + "=" * 70)


async def demo_citation_system():
    """演示引用系统"""
    print("\n" + "=" * 70)
    print("🚀 Citation System Demo")
    print("=" * 70)
    
    sources = [
        {
            "title": "Python Asyncio Best Practices",
            "url": "https://realpython.com/asyncio",
            "snippet": "Best practices for using asyncio in Python applications"
        },
        {
            "title": "Asyncio Documentation",
            "url": "https://docs.python.org/3/library/asyncio.html",
            "snippet": "Official Python documentation for asyncio"
        },
        {
            "title": "High Performance Python",
            "url": "https://example.com/performance",
            "snippet": "Performance tips for Python applications"
        }
    ]
    
    citations = build_citations(sources, "Python asyncio")
    refs = format_references(citations)
    
    print(f"\n📚 Generated {len(citations)} citations:")
    for c in citations:
        print(f"   [{c['id']}] {c['title']} ({c['domain']})")
    
    print(f"\n📝 References Text:\n{refs}")
    
    print("\n" + "=" * 70)


async def main():
    """运行所有演示"""
    print("\n" + "🎯" * 35)
    print("  Deep Research Skill - Full Demo")
    print("🎯" * 35 + "\n")
    
    await demo_quick_mode()
    await demo_standard_mode()
    await demo_deep_mode()
    await demo_citation_system()
    
    print("\n" + "✨" * 35)
    print("  Demo completed!")
    print("  To use with real search, configure BRAVE_API_KEY")
    print("  See: skills/deep_research/SETUP.md")
    print("✨" * 35 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
