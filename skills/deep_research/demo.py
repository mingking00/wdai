"""
Deep Research Skill 演示版本

直接使用 kimi_search 工具进行搜索
"""

import sys
sys.path.insert(0, '.')

import asyncio
from skills.deep_research import research, run


async def demo_quick():
    """快速研究演示"""
    print("=" * 70)
    print("🔍 Deep Research Skill - Quick Mode Demo")
    print("=" * 70)
    
    result = await run({
        "query": "Python asyncio best practices 2024",
        "depth": "quick"
    })
    
    print(f"\n✅ Success: {result['success']}")
    print(f"📚 Sources: {result['sources_count']}")
    print(f"📝 Citations: {len(result['citations'])}")
    
    print(f"\n📄 Answer:\n{result['answer'][:1000]}")
    
    if result['references_text']:
        print(f"\n🔗 References:\n{result['references_text'][:500]}")
    
    print("\n" + "=" * 70)


async def demo_direct_search():
    """直接搜索测试 - 使用 kimi_search 工具"""
    print("\n" + "=" * 70)
    print("🔍 Direct Search Test (using kimi_search tool)")
    print("=" * 70)
    
    # 直接使用 kimi_search 工具
    try:
        from tools.kimi_search import kimi_search
        
        results = kimi_search("Python asyncio best practices", count=5)
        print(f"\n✅ Search returned {len(results)} results")
        
        for i, item in enumerate(results[:3], 1):
            print(f"\n{i}. {item.get('title', 'N/A')}")
            print(f"   URL: {item.get('url', 'N/A')[:60]}...")
            print(f"   Summary: {item.get('summary', 'N/A')[:100]}...")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        print("Note: kimi_search tool may not be available in this environment")


async def main():
    """运行所有演示"""
    await demo_quick()
    await demo_direct_search()
    
    print("\n✨ Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
