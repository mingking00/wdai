#!/usr/bin/env python3
"""
Deep Research Skill 测试脚本
"""

import sys
sys.path.insert(0, '.')

import asyncio
from skills.deep_research import research, run
from skills.deep_research.integration import parse_research_command


async def test_quick_mode():
    """测试快速模式"""
    print("=" * 60)
    print("Test 1: Quick Mode")
    print("=" * 60)
    
    result = await research("Python asyncio tutorial", depth="quick")
    
    print(f"Success: {result.success}")
    print(f"Sources: {len(result.sources)}")
    print(f"Citations: {len(result.citations)}")
    print(f"\nAnswer Preview:\n{result.answer[:300]}...")
    
    if result.references_text:
        print(f"\nReferences Preview:\n{result.references_text[:200]}...")
    
    print("\n✅ Quick mode test completed\n")


async def test_standard_mode():
    """测试标准模式"""
    print("=" * 60)
    print("Test 2: Standard Mode")
    print("=" * 60)
    
    result = await research("OpenClaw AI agent", depth="standard")
    
    print(f"Success: {result.success}")
    print(f"Sources: {len(result.sources)}")
    print(f"Fetched: {result.metadata.get('fetched_count', 0)}")
    
    print("\n✅ Standard mode test completed\n")


async def test_deep_mode():
    """测试深度模式"""
    print("=" * 60)
    print("Test 3: Deep Mode")
    print("=" * 60)
    
    result = await research("AI agent frameworks comparison", depth="deep")
    
    print(f"Success: {result.success}")
    print(f"Sources: {len(result.sources)}")
    print(f"Exploration levels: {len(result.exploration_path)}")
    
    if result.exploration_path:
        print("\nExploration Path:")
        for path in result.exploration_path:
            print(f"  - Depth {path['depth']}: {path.get('rationale', path['query'])}")
    
    print("\n✅ Deep mode test completed\n")


async def test_skill_interface():
    """测试 Skill 接口"""
    print("=" * 60)
    print("Test 4: Skill Interface")
    print("=" * 60)
    
    result = await run({
        "query": "Python best practices",
        "depth": "quick"
    })
    
    print(f"Success: {result['success']}")
    print(f"Answer type: {type(result['answer'])}")
    print(f"Has citations: {len(result.get('citations', []))}")
    print(f"Has references_text: {bool(result.get('references_text'))}")
    
    print("\n✅ Skill interface test completed\n")


def test_command_parser():
    """测试命令解析器"""
    print("=" * 60)
    print("Test 5: Command Parser")
    print("=" * 60)
    
    test_cases = [
        ("研究 Python asyncio", True, "Python asyncio", "standard"),
        ("深度研究 AI frameworks", True, "AI frameworks", "deep"),
        ("快速研究 天气", True, "天气", "quick"),
        ("research Python", True, "Python", "standard"),
        ("查一下 最新新闻", True, "最新新闻", "standard"),
        ("今天吃什么", False, None, None),
    ]
    
    for text, expected_is_research, expected_query, expected_depth in test_cases:
        is_research, query, depth = parse_research_command(text)
        
        status = "✅" if (is_research == expected_is_research and 
                         query == expected_query and 
                         depth == expected_depth) else "❌"
        
        print(f"{status} '{text}'")
        if is_research:
            print(f"   -> query='{query}', depth='{depth}'")
    
    print("\n✅ Command parser test completed\n")


async def test_cache():
    """测试缓存系统"""
    print("=" * 60)
    print("Test 6: Cache System")
    print("=" * 60)
    
    from skills.deep_research.cache import MemoryCache, SQLiteCache, TieredCache
    from skills.deep_research.config import ResearchConfig
    
    config = ResearchConfig()
    cache = TieredCache(config)
    
    # 测试内存缓存
    await cache.memory.set("test_key", {"data": "test"}, ttl=3600)
    entry = await cache.memory.get("test_key")
    
    if entry and entry.data.get("data") == "test":
        print("✅ Memory cache works")
    else:
        print("❌ Memory cache failed")
    
    # 测试 SQLite 缓存
    await cache.sqlite.set("test_sqlite", {"value": 123}, ttl=3600)
    entry = await cache.sqlite.get("test_sqlite")
    
    if entry and entry.data.get("value") == 123:
        print("✅ SQLite cache works")
    else:
        print("❌ SQLite cache failed")
    
    # 测试双层缓存
    await cache.set("tiered_test", {"hello": "world"}, ttl=3600)
    data = await cache.get("tiered_test")
    
    if data and data.get("hello") == "world":
        print("✅ Tiered cache works")
    else:
        print("❌ Tiered cache failed")
    
    print("\n✅ Cache system test completed\n")


async def test_citation():
    """测试引用系统"""
    print("=" * 60)
    print("Test 7: Citation System")
    print("=" * 60)
    
    from skills.deep_research.citation import build_citations, format_references
    
    mock_results = [
        {"title": "Python Tutorial", "url": "https://python.org", "snippet": "Learn Python"},
        {"title": "Asyncio Guide", "url": "https://docs.python.org/async", "snippet": "Async programming"},
    ]
    
    citations = build_citations(mock_results, "Python async")
    
    print(f"Generated {len(citations)} citations")
    for c in citations:
        print(f"  [{c['id']}] {c['title']} ({c['domain']})")
    
    refs = format_references(citations)
    print(f"\nReferences text:\n{refs}")
    
    print("\n✅ Citation system test completed\n")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Deep Research Skill - Test Suite")
    print("=" * 60 + "\n")
    
    # 同步测试
    test_command_parser()
    await test_cache()
    await test_citation()
    
    # 需要外部 API 的测试
    print("=" * 60)
    print("API Tests (require web_search/web_fetch)")
    print("=" * 60 + "\n")
    
    try:
        await test_quick_mode()
    except Exception as e:
        print(f"❌ Quick mode test failed: {e}\n")
    
    try:
        await test_standard_mode()
    except Exception as e:
        print(f"❌ Standard mode test failed: {e}\n")
    
    try:
        await test_deep_mode()
    except Exception as e:
        print(f"❌ Deep mode test failed: {e}\n")
    
    try:
        await test_skill_interface()
    except Exception as e:
        print(f"❌ Skill interface test failed: {e}\n")
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
