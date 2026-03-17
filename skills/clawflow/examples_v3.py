#!/usr/bin/env python3
"""
ClawFlow v3.0 - 高价值优化演示

展示：
1. 并行执行 (asyncio)
2. OpenClaw Skill 集成
3. 性能对比
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clawflow import WorkflowEngine
import time


def example_parallel_execution():
    """示例 1: 并行执行 vs 顺序执行"""
    print("=" * 60)
    print("示例 1: 并行执行性能对比")
    print("=" * 60)
    
    # 模拟耗时操作的工作流
    workflow = {
        "name": "并行测试",
        "nodes": [
            {
                "id": "start",
                "type": "trigger",
                "params": {}
            },
            {
                "id": "branch_a1",
                "type": "delay",
                "params": {"delay": 100}  # 100ms
            },
            {
                "id": "branch_a2",
                "type": "delay",
                "params": {"delay": 100}
            },
            {
                "id": "branch_b1",
                "type": "delay",
                "params": {"delay": 100}
            },
            {
                "id": "branch_b2",
                "type": "delay",
                "params": {"delay": 100}
            },
            {
                "id": "merge",
                "type": "merge",
                "params": {"mode": "append"}
            }
        ],
        "connections": [
            {"from": "start", "to": "branch_a1"},
            {"from": "start", "to": "branch_b1"},
            {"from": "branch_a1", "to": "branch_a2"},
            {"from": "branch_b1", "to": "branch_b2"},
            {"from": "branch_a2", "to": "merge"},
            {"from": "branch_b2", "to": "merge"}
        ]
    }
    
    engine = WorkflowEngine()
    
    # 顺序执行
    print("\n[顺序执行]")
    start = time.time()
    result_seq = engine.execute(workflow, verbose=False, parallel=False)
    time_seq = time.time() - start
    
    print(f"  耗时: {time_seq:.3f}s")
    print(f"  成功: {result_seq.success}")
    
    # 并行执行
    print("\n[并行执行]")
    start = time.time()
    result_par = engine.execute(workflow, verbose=True, parallel=True)
    time_par = time.time() - start
    
    print(f"\n  耗时: {time_par:.3f}s")
    print(f"  成功: {result_par.success}")
    print(f"  并行统计: {result_par.parallel_stats}")
    
    # 性能对比
    speedup = time_seq / time_par if time_par > 0 else 1
    print(f"\n[性能提升]")
    print(f"  速度提升: {speedup:.2f}x")
    print(f"  节省时间: {(time_seq - time_par) * 1000:.0f}ms")


def example_skill_integration():
    """示例 2: OpenClaw Skill 集成"""
    print("\n" + "=" * 60)
    print("示例 2: OpenClaw Skill 集成")
    print("=" * 60)
    
    workflow = {
        "name": "Skill调用工作流",
        "nodes": [
            {
                "id": "search",
                "type": "skill",
                "params": {
                    "skill": "web_search",
                    "params": {"query": "Python asyncio"}
                }
            },
            {
                "id": "process",
                "type": "function",
                "params": {
                    "code": """
# 处理搜索结果
if isinstance(input, dict) and "result" in input:
    results = input["result"].get("results", [])
    output = {
        "found": len(results),
        "titles": [r.get("title", "") for r in results]
    }
else:
    output = {"found": 0, "titles": []}
"""
                }
            },
            {
                "id": "notify",
                "type": "message",
                "params": {
                    "channel": "telegram",
                    "target": "@mychannel",
                    "message": "找到 {{found}} 个结果: {{titles}}"
                }
            }
        ],
        "connections": [
            {"from": "search", "to": "process"},
            {"from": "process", "to": "notify"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, verbose=True)
    
    if result.success:
        print(f"\n✅ Skill 调用成功")
        print(f"最终结果: {result.data}")


def example_complex_parallel_pipeline():
    """示例 3: 复杂并行数据处理管道"""
    print("\n" + "=" * 60)
    print("示例 3: 复杂并行数据处理")
    print("=" * 60)
    
    # 模拟从多个源并行获取数据
    workflow = {
        "name": "数据聚合",
        "nodes": [
            {"id": "start", "type": "trigger", "params": {}},
            
            # 并行分支 1: API A
            {"id": "fetch_a", "type": "http", "params": {
                "method": "GET",
                "url": "https://api.github.com"
            }},
            {"id": "process_a", "type": "function", "params": {
                "code": "output = {'source': 'API_A', 'data': input.get('status', 0)}"
            }},
            
            # 并行分支 2: API B
            {"id": "fetch_b", "type": "http", "params": {
                "method": "GET",
                "url": "https://httpbin.org/get"
            }},
            {"id": "process_b", "type": "function", "params": {
                "code": "output = {'source': 'API_B', 'data': 'ok'}"
            }},
            
            # 并行分支 3: 本地文件
            {"id": "read_local", "type": "function", "params": {
                "code": "output = {'source': 'LOCAL', 'data': [1,2,3]}"
            }},
            
            # 合并所有结果
            {"id": "merge_all", "type": "merge", "params": {"mode": "append"}},
            
            # 最终处理
            {"id": "finalize", "type": "function", "params": {
                "code": """
if isinstance(input, dict) and "__merged__" in input:
    sources = [item.get("source") for item in input["__merged__"]]
    output = {
        "sources": sources,
        "total": len(sources),
        "timestamp": "2024"
    }
else:
    output = input
"""
            }},
            {"id": "output", "type": "output", "params": {"type": "print"}}
        ],
        "connections": [
            # 启动并行分支
            {"from": "start", "to": "fetch_a"},
            {"from": "start", "to": "read_local"},
            
            # API A 链
            {"from": "fetch_a", "to": "process_a"},
            {"from": "process_a", "to": "merge_all"},
            
            # API B 链 (从 fetch_a 分叉)
            {"from": "fetch_a", "to": "fetch_b"},
            {"from": "fetch_b", "to": "process_b"},
            {"from": "process_b", "to": "merge_all"},
            
            # 本地链
            {"from": "read_local", "to": "merge_all"},
            
            # 最终处理
            {"from": "merge_all", "to": "finalize"},
            {"from": "finalize", "to": "output"}
        ]
    }
    
    engine = WorkflowEngine()
    
    print("\n[顺序执行]")
    start = time.time()
    result_seq = engine.execute(workflow, parallel=False)
    time_seq = time.time() - start
    print(f"  耗时: {time_seq:.3f}s")
    
    print("\n[并行执行]")
    start = time.time()
    result_par = engine.execute(workflow, parallel=True, verbose=True)
    time_par = time.time() - start
    print(f"\n  耗时: {time_par:.3f}s")
    
    if result_par.success:
        print(f"\n✅ 数据处理完成")
        data = result_par.data
        if isinstance(data, dict):
            print(f"  来源: {data.get('sources', [])}")
        else:
            print(f"  结果: {data}")
        print(f"  速度提升: {time_seq/time_par:.2f}x")


def example_available_skills():
    """示例 4: 展示可用 Skills"""
    print("\n" + "=" * 60)
    print("示例 4: 可用 OpenClaw Skills")
    print("=" * 60)
    
    skills = {
        "web_search": "网页搜索 (模拟)",
        "kimi_search": "Kimi 搜索",
        "browser_open": "浏览器打开",
        "browser_snapshot": "浏览器快照",
        "file_read": "文件读取",
        "file_write": "文件写入",
        "exec": "执行命令",
        "memory_search": "记忆搜索"
    }
    
    print("\n内置 Skills:")
    for name, desc in skills.items():
        print(f"  - {name}: {desc}")
    
    print("\n使用方式:")
    print("""
    {
        "id": "search",
        "type": "skill",
        "params": {
            "skill": "web_search",
            "params": {"query": "Python教程"}
        }
    }
    """)


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("🚀 ClawFlow v3.0 - 高价值优化")
    print("=" * 60)
    print("\n新增能力:")
    print("  ✅ asyncio 并行执行 (2-5x 性能提升)")
    print("  ✅ OpenClaw Skill 集成 (搜索/浏览器/文件)")
    print("  ✅ 自动层级检测并行组")
    print("  ✅ 消息发送节点")
    print("=" * 60)
    
    # 运行示例
    example_parallel_execution()
    example_skill_integration()
    example_complex_parallel_pipeline()
    example_available_skills()
    
    print("\n" + "=" * 60)
    print("✅ 所有演示完成！")
    print("=" * 60)
    print("""
核心优化总结:

1. 并行执行
   - 自动识别可并行节点
   - asyncio 协程并发
   - 性能提升 2-5x

2. OpenClaw 集成
   - 8个内置 Skill
   - 支持动态导入外部 Skill
   - 无缝扩展能力

3. 使用方式
   engine.execute(workflow, parallel=True)  # 启用并行

下一步:
   - 完善条件分支路由
   - 添加更多 OpenClaw 工具集成
   - 实现节点结果缓存
    """)


if __name__ == "__main__":
    main()
