"""
Agent执行引擎 v3.0 演示

展示底层机制的根本性改变：
1. 强制验证（不是可选项）
2. 不确定性显化（不是可隐藏）
3. 概念Agent vs 真并行Agent 的明确区分
4. 验证链：生成 → 验证 → 修正
"""

import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system.agent_engine_v3 import (
    create_conceptual_agent,
    create_parallel_agent,
    create_orchestrator,
    AgentOutput,
    Uncertainty,
    VerificationStatus,
)


async def demo_mandatory_verification():
    """演示强制验证机制"""
    print("="*70)
    print("演示1: 强制验证机制（不再能跳过）")
    print("="*70)
    
    # 创建Agent
    agent = create_conceptual_agent("demo-agent")
    
    # 任务：引用图片但未读取
    task = {
        'description': '分析这张图片',
        'image_path': '/path/to/image.jpg',
        'image_verified': False  # 关键：未验证
    }
    
    print(f"\n任务: {task['description']}")
    print(f"图片路径: {task['image_path']}")
    print(f"图片已验证: {task['image_verified']}")
    
    # 执行（强制验证会失败）
    result = await agent.execute(task)
    
    print(f"\n验证状态: {result.verification.status.name}")
    print(f"验证评分: {result.verification.score}")
    
    if result.verification.status == VerificationStatus.FAILED:
        print(f"\n❌ 验证失败！")
        print(f"问题: {result.verification.issues}")
        print(f"\n输出被阻断/修正:")
        print(result.content)
    
    print("\n" + "-"*70)
    
    # 修正后的任务
    print("\n修正：先读取图片，再分析")
    task['image_verified'] = True
    task['description'] = '根据已读取的图片内容分析'  # 明确标注
    
    result2 = await agent.execute(task)
    print(f"\n验证状态: {result2.verification.status.name}")
    
    if result2.verification.status == VerificationStatus.PASSED:
        print("✅ 验证通过！")


async def demo_uncertainty_explicit():
    """演示不确定性显化"""
    print("\n" + "="*70)
    print("演示2: 不确定性必须显化")
    print("="*70)
    
    orchestrator = create_orchestrator()
    
    # 注册多个Agent
    orchestrator.register_agent(create_conceptual_agent("agent-a"))
    orchestrator.register_agent(create_conceptual_agent("agent-b"))
    
    task = {'description': '评估这个方案'}
    
    print(f"\n任务: {task['description']}")
    print("并行执行两个Agent...")
    
    # 并行执行
    results = await orchestrator.execute_parallel(['agent-a', 'agent-b'], task)
    
    for i, result in enumerate(results, 1):
        print(f"\nAgent-{i} 输出:")
        print(f"  内容: {result.content}")
        print(f"  置信度: {result.confidence}")
        print(f"  不确定性:")
        for u in result.uncertainties:
            print(f"    - {u.description} (影响: {u.impact})")
    
    # 整合
    print(f"\n整合输出...")
    integrated = orchestrator.integrate_outputs(results, strategy="confidence_weighted")
    
    print(f"\n整合结果:")
    print(f"  内容: {integrated.content}")
    print(f"  置信度: {integrated.confidence}")
    print(f"  不确定性（包含整合过程的不确定性）:")
    for u in integrated.uncertainties:
        print(f"    - {u.description}")


async def demo_verification_chain():
    """演示验证链：生成 → 验证 → 修正"""
    print("\n" + "="*70)
    print("演示3: 验证链模式")
    print("="*70)
    
    orchestrator = create_orchestrator()
    
    # 注册Agent
    orchestrator.register_agent(create_conceptual_agent("coder"))
    orchestrator.register_agent(create_conceptual_agent("reviewer-1"))
    orchestrator.register_agent(create_conceptual_agent("reviewer-2"))
    
    task = {'description': '实现文件上传功能'}
    
    print(f"\n任务: {task['description']}")
    print("\n执行流程:")
    print("  1. Coder 生成代码")
    print("  2. Reviewer-1 并行审查")
    print("  3. Reviewer-2 并行审查")
    print("  4. 整合审查结果")
    
    result = await orchestrator.execute_with_verification_chain(
        task=task,
        executor_agent='coder',
        verifier_agents=['reviewer-1', 'reviewer-2']
    )
    
    print(f"\n最终结果:")
    print(f"  状态: {result.verification.status.name}")
    print(f"  置信度: {result.confidence}")
    
    if result.verification.issues:
        print(f"  发现的问题: {result.verification.issues}")


async def demo_conceptual_vs_parallel():
    """演示概念Agent vs 真并行Agent的区别"""
    print("\n" + "="*70)
    print("演示4: 概念Agent vs 真并行Agent")
    print("="*70)
    
    orchestrator = create_orchestrator()
    
    # 概念Agent（串行，我扮演）
    conceptual = create_conceptual_agent("conceptual-analyzer")
    
    # 真并行Agent（独立session）
    parallel = create_parallel_agent("parallel-analyzer", agent_id="parallel-1")
    
    orchestrator.register_agent(conceptual)
    orchestrator.register_agent(parallel)
    
    task = {'description': '分析这个技术方案'}
    
    print(f"\n任务: {task['description']}")
    
    print("\n概念Agent执行（串行）:")
    print("  特点：快速，但视角可能不独立")
    result_c = await orchestrator.execute_single('conceptual-analyzer', task)
    print(f"  结果: {result_c.content[:50]}...")
    print(f"  置信度: {result_c.confidence}")
    print(f"  不确定性: {len(result_c.uncertainties)} 个")
    
    print("\n真并行Agent执行（独立session）:")
    print("  特点：延迟稍高，但视角真正独立")
    result_p = await orchestrator.execute_single('parallel-analyzer', task)
    print(f"  结果: {result_p.content[:50]}...")
    print(f"  置信度: {result_p.confidence}")
    print(f"  不确定性: {len(result_p.uncertainties)} 个")
    print(f"  Session ID: {result_p.metadata.get('session_id', 'N/A')}")
    
    print("\n对比:")
    print(f"  概念Agent适合：简单任务，低延迟")
    print(f"  真并行Agent适合：需要独立视角，高可靠性")


async def demo_failure_recovery():
    """演示失败后的恢复机制"""
    print("\n" + "="*70)
    print("演示5: 失败检测与恢复")
    print("="*70)
    
    agent = create_conceptual_agent("fragile-agent")
    
    # 任务：高风险的描述（可能编造）
    task = {
        'description': '根据文件名分析图片内容',  # 危险！
        'image_verified': False
    }
    
    print(f"\n危险任务: {task['description']}")
    print("（引用图片但未读取，容易编造）")
    
    result = await agent.execute(task)
    
    print(f"\n执行结果:")
    print(f"  验证状态: {result.verification.status.name}")
    
    if result.verification.status == VerificationStatus.FAILED:
        print(f"  ❌ 检测到风险！")
        print(f"  问题: {result.verification.issues[0]}")
        print(f"\n  系统行为:")
        print(f"    - 阻断危险输出")
        print(f"    - 要求修正")
        print(f"    - 置信度设为0")
        
        print(f"\n  修正方案:")
        print(f"    1. 先读取图片")
        print(f"    2. 基于实际内容分析")
        print(f"    3. 重新执行")


async def run_all_demos():
    """运行所有演示"""
    await demo_mandatory_verification()
    await demo_uncertainty_explicit()
    await demo_verification_chain()
    await demo_conceptual_vs_parallel()
    await demo_failure_recovery()
    
    print("\n" + "="*70)
    print("演示完成")
    print("="*70)
    print("\n核心改进:")
    print("1. 强制验证 - 不再是可选项")
    print("2. 不确定性显化 - 必须记录")
    print("3. 验证链 - 生成→验证→修正")
    print("4. 明确区分 - 概念Agent vs 真并行Agent")


if __name__ == "__main__":
    asyncio.run(run_all_demos())
