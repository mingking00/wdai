#!/usr/bin/env python3
"""
wdai AutoResearch - 10分钟持续运行模式
自动生成多个研究任务，持续运行，汇总成果
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/.wdai-autoresearch')
from wdai_autoresearch import CoordinatorAgent, ResearchTask

# 研究主题池
RESEARCH_TOPICS = [
    {
        "topic": "向量数据库的最优索引策略",
        "hypothesis": "HNSW索引在亿级数据下比IVF快3倍且召回率>95%",
        "complexity": 7
    },
    {
        "topic": "LLM推理的KV缓存优化",
        "hypothesis": "动态压缩可以减少50%显存占用且不损失生成质量",
        "complexity": 8
    },
    {
        "topic": "多模态嵌入的对齐方法",
        "hypothesis": "对比学习+温度缩放可以提高图文检索准确率15%",
        "complexity": 6
    },
    {
        "topic": "RAG系统的重排序策略",
        "hypothesis": "交叉编码器重排序比双编码器提高20%精确率",
        "complexity": 5
    },
    {
        "topic": "Agent工具调用的延迟优化",
        "hypothesis": "预加载+并行执行可以减少70%工具调用延迟",
        "complexity": 7
    }
]

async def run_continuous_research(duration_minutes: int = 10):
    """持续运行研究任务"""
    
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║     🔬 wdai AutoResearch - 持续运行模式                             ║")
    print(f"║     运行时长: {duration_minutes}分钟 | 自动生成研究任务            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    
    coordinator = CoordinatorAgent()
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    completed_tasks = []
    task_count = 0
    
    print(f"⏱️  开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print(f"⏱️  预计结束: {(datetime.now().timestamp() + duration_minutes * 60)}")
    print(f"📚 研究主题池: {len(RESEARCH_TOPICS)}个主题")
    print()
    
    while time.time() < end_time:
        remaining = end_time - time.time()
        task_count += 1
        
        # 选择主题
        topic_info = RESEARCH_TOPICS[(task_count - 1) % len(RESEARCH_TOPICS)]
        
        print(f"\n{'='*70}")
        print(f"🔄 任务 #{task_count} | 剩余时间: {remaining/60:.1f}分钟")
        print(f"{'='*70}")
        
        try:
            # 创建并运行任务
            task = coordinator.create_task(
                topic=topic_info["topic"],
                hypothesis=topic_info["hypothesis"],
                complexity=topic_info["complexity"]
            )
            
            result = await coordinator.run_research(task)
            completed_tasks.append(result)
            
            print(f"\n✅ 任务 #{task_count} 完成: {result.id}")
            
        except Exception as e:
            print(f"\n❌ 任务 #{task_count} 失败: {e}")
            continue
        
        # 短暂暂停，避免过度消耗
        await asyncio.sleep(1)
    
    # 生成总结报告
    elapsed = time.time() - start_time
    
    print(f"\n\n{'='*70}")
    print("📊 10分钟持续运行成果报告")
    print(f"{'='*70}")
    print(f"实际运行时间: {elapsed/60:.1f}分钟")
    print(f"总任务数: {task_count}")
    print(f"成功完成: {len(completed_tasks)}")
    print(f"成功率: {len(completed_tasks)/task_count*100:.0f}%" if task_count > 0 else "N/A")
    print()
    
    # 统计IER记录
    total_ier = len(coordinator.ier.records)
    print(f"📚 IER学习记录: {total_ier}条")
    
    # 按Phase统计
    phase_counts = {}
    agent_counts = {}
    for record in coordinator.ier.records:
        phase = record['phase']
        agent = record['agent']
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
    
    print()
    print("📊 Phase分布:")
    for phase, count in sorted(phase_counts.items()):
        print(f"   {phase:12}: {count}条")
    
    print()
    print("🤖 Agent活跃度:")
    for agent, count in sorted(agent_counts.items(), key=lambda x: -x[1]):
        print(f"   {agent:12}: {count}次")
    
    print()
    print("📝 完成的任务列表:")
    for i, task in enumerate(completed_tasks, 1):
        print(f"   {i}. [{task.id}] {task.topic[:40]}... ({task.status})")
    
    print()
    print("─" * 70)
    print("💡 关键洞察汇总:")
    print("─" * 70)
    
    # 提取关键洞察
    unique_insights = []
    for record in coordinator.ier.records:
        insight = record['insight']
        if insight not in unique_insights:
            unique_insights.append(insight)
    
    for i, insight in enumerate(unique_insights[:5], 1):
        print(f"   {i}. {insight[:60]}...")
    
    print()
    print("="*70)
    print("✅ 持续运行结束，所有成果已归档")
    print("="*70)
    print()
    print("📁 成果位置:")
    print("   .wdai-autoresearch/program.md          - 研究方向汇总")
    print("   .wdai-autoresearch/ier/records.jsonl   - IER学习记录")
    print("   .wdai-autoresearch/experiments/        - 实验归档")
    
    return {
        "tasks_completed": len(completed_tasks),
        "total_tasks": task_count,
        "ier_records": total_ier,
        "elapsed_minutes": elapsed / 60
    }

if __name__ == '__main__':
    # 运行10分钟
    result = asyncio.run(run_continuous_research(duration_minutes=10))
    
    print(f"\n\n🏁 最终统计:")
    print(f"   完成任务: {result['tasks_completed']}/{result['total_tasks']}")
    print(f"   IER记录: {result['ier_records']}条")
    print(f"   运行时间: {result['elapsed_minutes']:.1f}分钟")
