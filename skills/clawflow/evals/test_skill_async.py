#!/usr/bin/env python3
"""
测试 SkillNode 异步化
"""

import sys
import asyncio
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clawflow import WorkflowEngine


def test_skill_async():
    """测试 skill 节点异步执行"""
    
    print("\n" + "="*60)
    print("🧪 SkillNode 异步化测试")
    print("="*60)
    
    # 测试1: 单个 skill 节点
    print("\n📊 Test 1: 单个搜索节点")
    
    workflow = {
        "name": "搜索测试",
        "nodes": [
            {"id": "search", "type": "skill", "params": {
                "skill": "kimi_search",
                "params": {"query": "Python asyncio"}
            }}
        ],
        "connections": []
    }
    
    engine = WorkflowEngine()
    
    # 顺序执行
    print("  [Sequential]")
    start = time.time()
    result_seq = engine.execute(workflow, parallel=False)
    time_seq = time.time() - start
    print(f"    Time: {time_seq:.3f}s")
    print(f"    Success: {result_seq.success}")
    if result_seq.success and result_seq.data:
        print(f"    Results: {result_seq.data.get('total', 0)} items")
    
    # 并行执行（触发异步）
    print("  [Parallel with Async]")
    start = time.time()
    result_par = engine.execute(workflow, parallel=True)
    time_par = time.time() - start
    print(f"    Time: {time_par:.3f}s")
    print(f"    Success: {result_par.success}")
    
    # 测试2: 多个并行 skill 节点
    print("\n📊 Test 2: 多个并行搜索节点")
    
    multi_workflow = {
        "name": "并行搜索测试",
        "nodes": [
            {"id": "search1", "type": "skill", "params": {
                "skill": "kimi_search",
                "params": {"query": "Python"}
            }},
            {"id": "search2", "type": "skill", "params": {
                "skill": "kimi_search",
                "params": {"query": "asyncio"}
            }},
            {"id": "search3", "type": "skill", "params": {
                "skill": "kimi_search",
                "params": {"query": "coroutine"}
            }},
            {"id": "merge", "type": "merge", "params": {"mode": "append"}}
        ],
        "connections": [
            {"from": "search1", "to": "merge"},
            {"from": "search2", "to": "merge"},
            {"from": "search3", "to": "merge"}
        ]
    }
    
    print("  [Sequential - 3 searches]")
    start = time.time()
    result_seq = engine.execute(multi_workflow, parallel=False)
    time_seq = time.time() - start
    print(f"    Time: {time_seq:.3f}s")
    print(f"    Success: {result_seq.success}")
    
    print("  [Parallel - 3 searches async]")
    start = time.time()
    result_par = engine.execute(multi_workflow, parallel=True)
    time_par = time.time() - start
    print(f"    Time: {time_par:.3f}s")
    print(f"    Success: {result_par.success}")
    
    if time_seq > 0 and time_par > 0:
        speedup = time_seq / time_par
        print(f"    🚀 Speedup: {speedup:.2f}x")
    
    # 测试3: 异步 exec 节点
    print("\n📊 Test 3: 异步命令执行")
    
    exec_workflow = {
        "name": "命令测试",
        "nodes": [
            {"id": "cmd1", "type": "skill", "params": {
                "skill": "exec",
                "params": {"command": "echo 'hello 1'"}
            }},
            {"id": "cmd2", "type": "skill", "params": {
                "skill": "exec",
                "params": {"command": "echo 'hello 2'"}
            }},
            {"id": "merge", "type": "merge", "params": {"mode": "append"}}
        ],
        "connections": [
            {"from": "cmd1", "to": "merge"},
            {"from": "cmd2", "to": "merge"}
        ]
    }
    
    print("  [Sequential]")
    start = time.time()
    result_seq = engine.execute(exec_workflow, parallel=False)
    time_seq = time.time() - start
    print(f"    Time: {time_seq:.3f}s")
    
    print("  [Parallel async]")
    start = time.time()
    result_par = engine.execute(exec_workflow, parallel=True)
    time_par = time.time() - start
    print(f"    Time: {time_par:.3f}s")
    
    if time_seq > 0 and time_par > 0:
        speedup = time_seq / time_par
        print(f"    🚀 Speedup: {speedup:.2f}x")
    
    print("\n" + "="*60)
    print("✅ SkillNode async test complete")
    print("="*60)


if __name__ == "__main__":
    test_skill_async()
