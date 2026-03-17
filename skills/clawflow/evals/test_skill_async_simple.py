#!/usr/bin/env python3
"""
测试 SkillNode 异步化 - 简化版
"""

import sys
import asyncio
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clawflow.nodes import SkillNode


async def test_skill_node_async():
    """直接测试 SkillNode 的异步方法"""
    
    print("\n" + "="*60)
    print("🧪 SkillNode 异步化测试 (简化版)")
    print("="*60)
    
    node = SkillNode()
    
    # Mock context
    class MockContext:
        def evaluate_expression(self, expr):
            return expr
    
    context = MockContext()
    
    # 测试1: 异步搜索
    print("\n📊 Test 1: _kimi_search_async")
    start = time.time()
    result = await node._kimi_search_async({"query": "Python asyncio", "max_results": 2})
    elapsed = time.time() - start
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Query: {result.get('query')}")
    print(f"  Results: {result.get('total', 0)}")
    print(f"  Source: {result.get('source')}")
    
    # 测试2: 异步执行命令
    print("\n📊 Test 2: _exec_async")
    start = time.time()
    result = await node._exec_async({"command": "echo 'async test'"})
    elapsed = time.time() - start
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Return code: {result.get('returncode')}")
    print(f"  Stdout: {result.get('stdout', '').strip()}")
    
    # 测试3: execute_async 方法
    print("\n📊 Test 3: execute_async method")
    start = time.time()
    result = await node.execute_async(
        input_data={},
        params={
            "skill": "kimi_search",
            "params": {"query": "asyncio tutorial", "max_results": 2}
        },
        context=context
    )
    elapsed = time.time() - start
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Success: {bool(result.get('results'))}")
    
    # 测试4: 并行执行多个搜索
    print("\n📊 Test 4: 并行执行多个搜索")
    queries = ["Python", "asyncio", "coroutine"]
    
    start = time.time()
    tasks = [
        node._kimi_search_async({"query": q, "max_results": 2})
        for q in queries
    ]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    print(f"  Parallel time: {elapsed:.3f}s")
    for i, (q, r) in enumerate(zip(queries, results)):
        print(f"  [{i+1}] {q}: {r.get('total', 0)} results")
    
    # 对比：顺序执行
    print("\n📊 Test 5: 顺序执行多个搜索")
    start = time.time()
    sequential_results = []
    for q in queries:
        r = await node._kimi_search_async({"query": q, "max_results": 2})
        sequential_results.append(r)
    elapsed = time.time() - start
    
    print(f"  Sequential time: {elapsed:.3f}s")
    
    print("\n" + "="*60)
    print("✅ SkillNode async test complete")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_skill_node_async())
