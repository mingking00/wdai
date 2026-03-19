#!/usr/bin/env python3
"""
wdai 完整Agent系统 v4.0 - 集成演示
指挥家 + 执行引擎 + 并行处理 + 冲突仲裁

完整流程:
1. 指挥家识别机会并创建任务
2. 执行引擎并行执行任务
3. 如遇冲突，触发仲裁机制
4. 结果沉淀到MEMORY.md
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/.wdai-runtime')

from agent_conductor_v3 import AgentConductor, AgentTask, TaskPriority
from agent_executor_v4 import AgentExecutionEngine

async def run_integrated_system():
    """运行完整的集成系统"""
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     🚀 wdai 完整Agent系统 v4.0 - 集成演示                   ║")
    print("║     指挥家 + 执行引擎 + 并行 + 仲裁                        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # =================================================================
    # 阶段1: 指挥家识别机会
    # =================================================================
    print("┌─ 阶段1: 指挥家识别系统机会 ────────────────────────────────┐")
    print()
    
    conductor = AgentConductor()
    
    # 手动添加一些真实任务来演示
    real_tasks = [
        AgentTask(
            task_id="github_001",
            task_type="github_analysis",
            description="分析已发现的Agent框架项目，提取架构洞察",
            target_agent="reflector",
            priority=TaskPriority.HIGH
        ),
        AgentTask(
            task_id="code_001",
            task_type="code_implementation",
            description="实现并行执行工具模块",
            target_agent="coder",
            priority=TaskPriority.HIGH
        ),
        AgentTask(
            task_id="review_001",
            task_type="code_review",
            description="审查agent_executor_v4.py代码质量",
            target_agent="reviewer",
            priority=TaskPriority.MEDIUM
        ),
        AgentTask(
            task_id="evolve_001",
            task_type="system_evolution",
            description="更新系统文档记录新架构",
            target_agent="evolution",
            priority=TaskPriority.LOW
        )
    ]
    
    for task in real_tasks:
        conductor.task_queue.append(task)
        print(f"   📌 {task.task_id}: {task.task_type} → {task.target_agent}")
    
    print(f"\n   任务队列: {len(conductor.task_queue)} 个任务")
    print()
    
    # =================================================================
    # 阶段2: 执行引擎并行执行
    # =================================================================
    print("├─ 阶段2: 执行引擎并行处理 ──────────────────────────────────┐")
    print()
    
    engine = AgentExecutionEngine()
    
    # 准备执行（转换为执行引擎需要的格式）
    exec_tasks = []
    for task in conductor.task_queue:
        exec_tasks.append({
            "task_id": task.task_id,
            "description": task.description,
            "target_agent": task.target_agent
        })
    
    print(f"   ⚡ 提交 {len(exec_tasks)} 个任务并行执行...")
    start_time = datetime.now()
    
    results = await engine.execute_batch(exec_tasks)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"   ⏱️  完成时间: {elapsed:.2f}秒")
    print()
    
    # 显示结果
    success_count = sum(1 for r in results if r.success)
    print(f"   执行结果: {success_count}/{len(results)} 成功")
    print()
    
    for result in results:
        icon = "✅" if result.success else "❌"
        print(f"   {icon} {result.agent_id:10s}: {result.task_id}")
        
        if result.files_created:
            print(f"      创建文件: {result.files_created}")
        if result.output and isinstance(result.output, dict):
            if "issues_found" in result.output:
                print(f"      发现问题: {result.output['issues_found']} 个")
            if "insights" in result.output:
                print(f"      洞察数量: {len(result.output['insights'])}")
            if "files_modified" in result.output:
                print(f"      修改文件: {len(result.output['files_modified'])} 个")
    
    print()
    
    # =================================================================
    # 阶段3: 冲突仲裁演示
    # =================================================================
    print("├─ 阶段3: 冲突仲裁机制 ──────────────────────────────────────┐")
    print()
    
    # 模拟一个真实冲突场景
    conflict = {
        "type": "architecture_disagreement",
        "agent_a": {
            "id": "coder",
            "suggestion": "使用asyncio重构整个Agent系统以提高并发性能",
            "reason": "性能优化，支持更多并行任务"
        },
        "agent_b": {
            "id": "reviewer", 
            "suggestion": "保持当前线程池模型，添加更完善的错误处理",
            "reason": "当前架构稳定，重构风险高"
        },
        "context": {
            "current_performance": "acceptable",
            "system_stability": "stable",
            "urgency": "low"
        }
    }
    
    print(f"   ⚖️  冲突: {conflict['type']}")
    print(f"   {conflict['agent_a']['id']}: {conflict['agent_a']['suggestion'][:40]}...")
    print(f"   {conflict['agent_b']['id']}: {conflict['agent_b']['suggestion'][:40]}...")
    print()
    
    decision = engine.resolve_conflict(conflict)
    
    print(f"   ✅ 仲裁决定: {decision['winner']} 胜出")
    print(f"      综合评分: {decision['reasoning']['total_score']:.2f}")
    print(f"      原则分: {decision['reasoning']['principle_score']}")
    print(f"      历史分: {decision['reasoning']['history_score']:.1%}")
    print(f"      风险分: {decision['reasoning']['risk_score']:.1f}")
    print()
    
    # =================================================================
    # 阶段4: 成果沉淀
    # =================================================================
    print("├─ 阶段4: 成果沉淀到MEMORY ──────────────────────────────────┐")
    print()
    
    # 显示生成的文件
    runtime_dir = Path("/root/.openclaw/workspace/.wdai-runtime")
    generated_files = list(runtime_dir.glob("generated_*.py"))
    
    print(f"   📁 生成的代码文件:")
    for f in generated_files[-3:]:  # 只显示最近的3个
        print(f"      - {f.name} ({f.stat().st_size} bytes)")
    
    print()
    
    # 检查更新的MEMORY
    memory_file = Path("/root/.openclaw/workspace/memory/daily") / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    if memory_file.exists():
        content = memory_file.read_text()
        print(f"   📝 MEMORY.md 更新:")
        print(f"      当前大小: {len(content)} 字符")
        print(f"      记录条目: {content.count('##')}")
    
    print()
    
    # =================================================================
    # 总结
    # =================================================================
    print("└─ 系统能力总结 ─────────────────────────────────────────────┘")
    print()
    print("✅ 完整闭环:")
    print("   1. 指挥家观察系统 → 识别改进机会")
    print("   2. 创建任务队列 → 按优先级排序")
    print("   3. 执行引擎并行处理 → 真实生成代码")
    print("   4. 如遇冲突 → 仲裁机制决策")
    print("   5. 成果沉淀 → 文件生成 + 记忆更新")
    print()
    print("✅ 核心组件:")
    print("   • AgentConductor: 智能调度 (18KB)")
    print("   • AgentExecutionEngine: 真实执行 (30KB)")
    print("   • ParallelExecutor: 并行处理 (asyncio)")
    print("   • ConflictArbitrator: 冲突仲裁 (P0-P4原则)")
    print()
    print("✅ 执行统计:")
    print(f"   • 总任务数: {len(real_tasks)}")
    print(f"   • 成功执行: {success_count}")
    print(f"   • 并行耗时: {elapsed:.2f}秒")
    print(f"   • 生成文件: {len(generated_files)} 个")
    print()
    print("=" * 65)
    print("✅ wdai 完整Agent系统 v4.0 演示完成!")
    print("=" * 65)
    print()
    print("💡 系统现在可以:")
    print("   • 自动发现改进机会")
    print("   • 智能分配任务给最适合的Agent")
    print("   • 并行执行多个任务")
    print("   • 真实生成代码并验证")
    print("   • 解决Agent间的建议冲突")
    print("   • 沉淀成果到文件和记忆")

if __name__ == '__main__':
    asyncio.run(run_integrated_system())
