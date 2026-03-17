"""
Deep Research Skill 使用示例
"""

import asyncio
from skills.deep_research import run, research, run_stream


async def demo_quick():
    """快速研究示例"""
    print("=== Quick Research Demo ===")
    
    result = await run({
        "query": "Python asyncio best practices",
        "depth": "quick"
    })
    
    print(f"Success: {result['success']}")
    print(f"Answer:\n{result['answer'][:500]}...")
    print(f"\nReferences:\n{result['references_text'][:300]}...")
    print(f"\nSources: {result['sources_count']}")


async def demo_standard():
    """标准研究示例"""
    print("\n=== Standard Research Demo ===")
    
    result = await run({
        "query": "OpenClaw AI agent framework",
        "depth": "standard"
    })
    
    print(f"Success: {result['success']}")
    print(f"Answer:\n{result['answer'][:800]}...")
    print(f"\nCitations: {len(result['citations'])}")


async def demo_deep():
    """深度研究示例"""
    print("\n=== Deep Research Demo ===")
    
    result = await run({
        "query": "AI agent frameworks comparison 2026",
        "depth": "deep"
    })
    
    print(f"Success: {result['success']}")
    print(f"Answer:\n{result['answer'][:1000]}...")
    print(f"\nExploration Path:")
    for path in result.get('exploration_path', []):
        print(f"  - Depth {path['depth']}: {path.get('rationale', path['query'])}")
    print(f"\nTotal Sources: {result['sources_count']}")


async def demo_stream():
    """流式研究示例"""
    print("\n=== Stream Research Demo ===")
    
    async for event in run_stream({
        "query": "Latest AI developments 2026",
        "depth": "deep"
    }):
        print(f"Event: {event['event']}")
        if event['event'] == 'complete':
            result = event['result']
            print(f"Completed with {len(result.citations)} citations")


async def demo_direct():
    """直接使用 research 函数"""
    print("\n=== Direct Research Demo ===")
    
    result = await research(
        query="Machine learning deployment patterns",
        depth="standard"
    )
    
    print(f"Success: {result.success}")
    print(f"Answer preview:\n{result.answer[:400]}...")
    print(f"\nReferences:\n{result.references_text[:250]}")


async def main():
    """运行所有示例"""
    await demo_quick()
    await demo_standard()
    # await demo_deep()  # 耗时较长，默认注释
    # await demo_stream()
    await demo_direct()


if __name__ == "__main__":
    asyncio.run(main())
