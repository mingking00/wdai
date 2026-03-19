#!/usr/bin/env python3
"""
Simplified Hybrid Parallel Orchestrator Demo
简化版混合并行编排器演示
"""

import asyncio
import time
from typing import Dict, Set, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
    """任务定义"""
    task_id: str
    agent_type: str
    depends_on: Set[str]
    duration: float  # 模拟执行时间


class HybridOrchestrator:
    """
    混合并行编排器 (简化版)
    
    核心逻辑:
    1. DAG定义依赖关系
    2. asyncio实现并行
    3. 就绪检测 + 动态调度
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.completed: Set[str] = set()
        self.results: Dict[str, Dict] = {}
        self.execution_log: List[Dict] = []
    
    def add_task(self, task_id: str, agent_type: str, 
                 depends_on: Set[str] = None, duration: float = 1.0):
        """添加任务"""
        self.tasks[task_id] = Task(
            task_id=task_id,
            agent_type=agent_type,
            depends_on=depends_on or set(),
            duration=duration
        )
    
    def get_ready_tasks(self) -> Set[str]:
        """获取就绪任务（所有依赖已完成）"""
        ready = set()
        for task_id, task in self.tasks.items():
            if task_id not in self.completed and task_id not in self.running:
                if task.depends_on.issubset(self.completed):
                    ready.add(task_id)
        return ready
    
    async def execute_agent(self, task: Task):
        """执行单个智能体任务"""
        start = time.time()
        
        print(f"   [{datetime.now().strftime('%H:%M:%S')}] 🚀 {task.task_id} ({task.agent_type}) 开始")
        
        # 模拟执行
        await asyncio.sleep(task.duration)
        
        elapsed = time.time() - start
        
        # 记录结果
        self.results[task.task_id] = {
            "agent_type": task.agent_type,
            "duration": elapsed,
            "completed_at": datetime.now().isoformat()
        }
        self.completed.add(task.task_id)
        
        print(f"   [{datetime.now().strftime('%H:%M:%S')}] ✅ {task.task_id} 完成 ({elapsed:.2f}s)")
        
        return task.task_id
    
    async def run(self):
        """主执行循环"""
        print("\n" + "="*70)
        print("🚀 HYBRID PARALLEL ORCHESTRATION")
        print("="*70)
        
        print(f"\n📋 任务配置:")
        for tid, task in self.tasks.items():
            deps = f" (依赖: {task.depends_on})" if task.depends_on else ""
            print(f"   • {tid}: {task.agent_type}, {task.duration}s{deps}")
        
        self.running: Set[str] = set()
        start_time = time.time()
        
        print(f"\n⏳ 开始并行执行...\n")
        
        while len(self.completed) < len(self.tasks):
            # 获取就绪任务
            ready = self.get_ready_tasks()
            
            if ready:
                # 并行启动所有就绪任务
                tasks_to_run = [self.tasks[tid] for tid in ready]
                
                for task in tasks_to_run:
                    self.running.add(task.task_id)
                
                # 使用asyncio.gather并行执行
                await asyncio.gather(*[
                    self.execute_agent(task) 
                    for task in tasks_to_run
                ])
                
                for task in tasks_to_run:
                    self.running.discard(task.task_id)
            else:
                # 等待一小段时间再检查
                await asyncio.sleep(0.1)
        
        total_elapsed = time.time() - start_time
        
        # 输出总结
        print("\n" + "="*70)
        print("📊 执行总结")
        print("="*70)
        print(f"   ⏱️  总耗时: {total_elapsed:.2f}s")
        print(f"   ✅ 完成任务: {len(self.completed)}/{len(self.tasks)}")
        
        # 计算理论串行时间 vs 实际并行时间
        serial_time = sum(t.duration for t in self.tasks.values())
        speedup = serial_time / total_elapsed if total_elapsed > 0 else 1
        
        print(f"   📈 加速比: {speedup:.2f}x (串行需要 {serial_time:.1f}s)")
        
        return self.results


async def demo_parallel_execution():
    """演示并行执行"""
    
    orchestrator = HybridOrchestrator()
    
    # 场景: 创建一个AI项目
    # 两个研究任务可以并行
    # 代码生成需要等两个研究都完成
    # 文档生成需要等代码完成
    
    orchestrator.add_task("research_github", "Research", duration=0.5)
    orchestrator.add_task("research_arxiv", "Research", duration=0.4)
    orchestrator.add_task("code_gen", "Code", 
                         depends_on={"research_github", "research_arxiv"}, 
                         duration=0.6)
    orchestrator.add_task("doc_gen", "Doc", 
                         depends_on={"code_gen"}, 
                         duration=0.3)
    
    # 添加另一个并行的分支
    orchestrator.add_task("security_audit", "Security", 
                         depends_on={"code_gen"}, 
                         duration=0.4)
    orchestrator.add_task("final_qa", "QA", 
                         depends_on={"doc_gen", "security_audit"}, 
                         duration=0.2)
    
    results = await orchestrator.run()
    
    # 可视化执行时间线
    print("\n📊 执行时间线:")
    print("   " + "-" * 50)
    
    # 简化的甘特图
    for tid in ["research_github", "research_arxiv", "code_gen", 
                "security_audit", "doc_gen", "final_qa"]:
        if tid in results:
            r = results[tid]
            bar = "█" * int(r['duration'] * 20)
            print(f"   {tid:20} │{bar}│ {r['duration']:.2f}s")


async def demo_comparison():
    """对比串行 vs 并行"""
    print("\n" + "="*70)
    print("📊 串行 vs 并行 对比")
    print("="*70)
    
    tasks = [
        ("任务A", 0.3),
        ("任务B", 0.3),
        ("任务C", 0.3),
    ]
    
    # 串行执行
    print("\n串行执行:")
    start = time.time()
    for name, duration in tasks:
        print(f"   开始 {name}...")
        await asyncio.sleep(duration)
        print(f"   完成 {name}")
    serial_time = time.time() - start
    print(f"   总时间: {serial_time:.2f}s")
    
    # 并行执行
    print("\n并行执行:")
    start = time.time()
    
    async def run_task(name, duration):
        print(f"   开始 {name}...")
        await asyncio.sleep(duration)
        print(f"   完成 {name}")
    
    await asyncio.gather(*[
        run_task(name, duration) for name, duration in tasks
    ])
    
    parallel_time = time.time() - start
    print(f"   总时间: {parallel_time:.2f}s")
    
    print(f"\n   并行加速: {serial_time/parallel_time:.1f}x")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🚀 HYBRID PARALLEL ORCHESTRATOR (SIMPLIFIED)                          ║
║                                                                          ║
║   DAG依赖图 + asyncio并行 = 最大化执行效率                               ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # 主演示
    asyncio.run(demo_parallel_execution())
    
    # 对比演示
    asyncio.run(demo_comparison())
    
    print("\n" + "="*70)
    print("✅ 演示完成!")
    print("="*70)
    print("\n核心洞察:")
    print("   • DAG明确定义了哪些任务可以并行")
    print("   • asyncio.gather() 实现真正的并行执行")
    print("   • 依赖驱动调度，无需等待无关任务")
