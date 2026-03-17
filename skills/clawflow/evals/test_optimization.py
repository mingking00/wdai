#!/usr/bin/env python3
"""
ClawFlow Optimized Evaluator
测试优化后的引擎
"""

import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clawflow import WorkflowEngine


def run_comparison_test():
    """对比测试：旧版 vs 优化版"""
    
    print("\n" + "="*60)
    print("🚀 ClawFlow Optimization Test")
    print("="*60)
    
    # 测试1: 并行执行
    print("\n📊 Test 1: Parallel Execution")
    
    parallel_workflow = {
        "name": "并行测试",
        "nodes": [
            {"id": "start", "type": "trigger", "params": {}},
            {"id": "a", "type": "delay", "params": {"delay": 100}},
            {"id": "b", "type": "delay", "params": {"delay": 100}},
            {"id": "c", "type": "delay", "params": {"delay": 100}},
            {"id": "merge", "type": "merge", "params": {"mode": "append"}}
        ],
        "connections": [
            {"from": "start", "to": "a"},
            {"from": "start", "to": "b"},
            {"from": "start", "to": "c"},
            {"from": "a", "to": "merge"},
            {"from": "b", "to": "merge"},
            {"from": "c", "to": "merge"}
        ]
    }
    
    engine = WorkflowEngine()
    
    # 顺序执行
    print("  [Sequential]")
    start = time.time()
    result_seq = engine.execute(parallel_workflow, parallel=False, use_cache=False)
    time_seq = time.time() - start
    print(f"    Time: {time_seq:.3f}s")
    print(f"    Success: {result_seq.success}")
    
    # 并行执行（优化后）
    print("  [Parallel - Optimized]")
    start = time.time()
    result_par = engine.execute(parallel_workflow, parallel=True, use_cache=False)
    time_par = time.time() - start
    print(f"    Time: {time_par:.3f}s")
    print(f"    Success: {result_par.success}")
    print(f"    Stats: {result_par.parallel_stats}")
    
    if time_seq > 0 and time_par > 0:
        speedup = time_seq / time_par
        print(f"    🚀 Speedup: {speedup:.2f}x")
    
    # 测试2: 缓存
    print("\n📊 Test 2: Node Caching")
    
    cache_workflow = {
        "name": "缓存测试",
        "nodes": [
            {"id": "compute", "type": "function", "params": {
                "code": "import time; time.sleep(0.05); output = {'result': 42}"
            }}
        ],
        "connections": []
    }
    
    # 第一次执行（无缓存）
    print("  [First run - No cache]")
    start = time.time()
    result1 = engine.execute(cache_workflow, use_cache=True)
    time1 = time.time() - start
    print(f"    Time: {time1:.3f}s")
    print(f"    Cache hits: {result1.cache_hits}, misses: {result1.cache_misses}")
    
    # 第二次执行（有缓存）
    print("  [Second run - With cache]")
    start = time.time()
    result2 = engine.execute(cache_workflow, use_cache=True)
    time2 = time.time() - start
    print(f"    Time: {time2:.3f}s")
    print(f"    Cache hits: {result2.cache_hits}, misses: {result2.cache_misses}")
    
    if time1 > 0 and time2 > 0:
        cache_speedup = time1 / time2
        print(f"    ⚡ Cache speedup: {cache_speedup:.2f}x")
    
    # 测试3: 复杂工作流
    print("\n📊 Test 3: Complex Workflow")
    
    complex_workflow = {
        "name": "复杂测试",
        "nodes": [
            {"id": "input", "type": "function", "params": {
                "code": "output = {'data': list(range(10))}"
            }},
            {"id": "branch1", "type": "function", "params": {
                "code": "output = [x*2 for x in input['data']]"
            }},
            {"id": "branch2", "type": "function", "params": {
                "code": "output = [x**2 for x in input['data']]"
            }},
            {"id": "combine", "type": "function", "params": {
                "code": "output = {'doubled': input.get('__merged__', [])[0] if isinstance(input, dict) and '__merged__' in input else [], 'squared': input.get('__merged__', [])[1] if isinstance(input, dict) and '__merged__' in input and len(input.get('__merged__', [])) > 1 else []}"
            }},
            {"id": "output", "type": "output", "params": {}}
        ],
        "connections": [
            {"from": "input", "to": "branch1"},
            {"from": "input", "to": "branch2"},
            {"from": "branch1", "to": "combine"},
            {"from": "branch2", "to": "combine"},
            {"from": "combine", "to": "output"}
        ]
    }
    
    print("  [Sequential]")
    start = time.time()
    result_seq = engine.execute(complex_workflow, parallel=False)
    time_seq = time.time() - start
    print(f"    Time: {time_seq:.3f}s")
    
    print("  [Parallel]")
    start = time.time()
    result_par = engine.execute(complex_workflow, parallel=True)
    time_par = time.time() - start
    print(f"    Time: {time_par:.3f}s")
    
    if time_seq > 0 and time_par > 0:
        speedup = time_seq / time_par
        print(f"    🚀 Speedup: {speedup:.2f}x")
    
    print("\n" + "="*60)
    print("✅ Optimization test complete")
    print("="*60)


if __name__ == "__main__":
    run_comparison_test()
