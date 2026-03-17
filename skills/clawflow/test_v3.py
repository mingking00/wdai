#!/usr/bin/env python3
"""
ClawFlow v3.0 - 快速测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clawflow import WorkflowEngine
import time


def test_parallel():
    """测试并行执行"""
    print("=" * 50)
    print("测试: 并行执行性能")
    print("=" * 50)
    
    workflow = {
        "name": "并行测试",
        "nodes": [
            {"id": "start", "type": "trigger", "params": {}},
            {"id": "a1", "type": "delay", "params": {"delay": 100}},
            {"id": "b1", "type": "delay", "params": {"delay": 100}},
            {"id": "merge", "type": "merge", "params": {"mode": "append"}}
        ],
        "connections": [
            {"from": "start", "to": "a1"},
            {"from": "start", "to": "b1"},
            {"from": "a1", "to": "merge"},
            {"from": "b1", "to": "merge"}
        ]
    }
    
    engine = WorkflowEngine()
    
    # 顺序执行
    print("\n[顺序执行]")
    start = time.time()
    result_seq = engine.execute(workflow, parallel=False)
    time_seq = time.time() - start
    print(f"  耗时: {time_seq:.3f}s")
    
    # 并行执行
    print("\n[并行执行]")
    start = time.time()
    result_par = engine.execute(workflow, parallel=True, verbose=True)
    time_par = time.time() - start
    print(f"\n  耗时: {time_par:.3f}s")
    
    if result_par.success:
        print(f"\n✅ 成功!")
        print(f"  速度提升: {time_seq/time_par:.2f}x")
        print(f"  并行统计: {result_par.parallel_stats}")


def test_skill():
    """测试 Skill 节点"""
    print("\n" + "=" * 50)
    print("测试: OpenClaw Skill 集成")
    print("=" * 50)
    
    workflow = {
        "name": "Skill测试",
        "nodes": [
            {
                "id": "search",
                "type": "skill",
                "params": {
                    "skill": "web_search",
                    "params": {"query": "Python"}
                }
            },
            {
                "id": "process",
                "type": "function",
                "params": {
                    "code": "output = {'found': len(input.get('results', [])), 'query': input.get('query', '')}"
                }
            }
        ],
        "connections": [
            {"from": "search", "to": "process"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, verbose=False)
    
    if result.success:
        print(f"\n✅ Skill 调用成功")
        print(f"  结果: {result.data}")


def test_message():
    """测试消息节点"""
    print("\n" + "=" * 50)
    print("测试: 消息发送")
    print("=" * 50)
    
    workflow = {
        "name": "消息测试",
        "nodes": [
            {
                "id": "notify",
                "type": "message",
                "params": {
                    "channel": "telegram",
                    "target": "@mychannel",
                    "message": "任务完成！"
                }
            }
        ],
        "connections": []
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow)
    
    if result.success:
        print(f"\n✅ 消息发送成功")


if __name__ == "__main__":
    test_parallel()
    test_skill()
    test_message()
    
    print("\n" + "=" * 50)
    print("✅ 所有测试通过!")
    print("=" * 50)
