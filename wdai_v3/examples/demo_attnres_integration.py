"""
集成演示：AttnRes 改进的完整工作流

展示如何将以下组件整合：
1. AttentionBasedOrchestrator - 注意力协调
2. DynamicVerificationLayer - 动态验证
3. 与原有 AgentEngineV3 的集成
"""

import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system import (
    # 原有组件
    create_conceptual_agent,
    create_parallel_agent,
    AgentOutput,
    Uncertainty,
    
    # 新增组件（AttnRes 改进）
    create_attention_orchestrator,
    AttentionConfig,
    create_dynamic_verification_layer,
    CheckpointType,
)


async def demo_attention_orchestrator():
    """演示注意力协调器"""
    print("="*70)
    print("演示1: Attention-Based Orchestrator")
    print("="*70)
    
    # 创建配置
    config = AttentionConfig(
        num_blocks=2,              # 分成2个块
        temperature=1.0,
        local_attention_range=3,   # 局部关注最近3个
        enable_skip_connections=True
    )
    
    orchestrator = create_attention_orchestrator()
    orchestrator.config = config
    
    # 注册 Agents（分成2个块）
    # 块0: 规划类
    orchestrator.register_agent("planner", block_id=0)
    orchestrator.register_agent("analyzer", block_id=0)
    
    # 块1: 执行类
    orchestrator.register_agent("coder", block_id=1)
    orchestrator.register_agent("reviewer", block_id=1)
    
    # 执行任务序列
    task = {
        'description': '实现用户登录功能',
        'requirements': ['安全性', '易用性', '可扩展性']
    }
    
    agent_sequence = ["planner", "analyzer", "coder", "reviewer"]
    
    result = await orchestrator.execute_with_attention(task, agent_sequence)
    
    print(f"\n执行完成！")
    print(f"全局置信度: {result.get('global_confidence', 0):.3f}")
    print(f"不确定性链数量: {len(result.get('uncertainty_chain', []))}")
    
    # 可视化注意力
    viz = orchestrator.get_attention_visualization()
    print(f"\n注意力矩阵:")
    for i, weights in enumerate(viz.get('attention_matrix', [])):
        if weights:
            print(f"  Step {i+1}: {weights}")
    
    return result


async def demo_dynamic_verification():
    """演示动态验证层"""
    print("\n" + "="*70)
    print("演示2: Dynamic Verification Layer")
    print("="*70)
    
    verifier = create_dynamic_verification_layer()
    
    # 场景1: 图片分析任务（高风险）
    print("\n--- 场景1: 图片分析任务 ---")
    response1 = "根据图片，这是一个B站视频截图..."
    context1 = {
        'has_image': True,
        'image_verified': False,  # 危险！
        'task_type': 'image_analysis'
    }
    
    result1 = verifier.verify(response1, context1, task_type='image_analysis')
    
    print(f"输入: {response1[:50]}...")
    print(f"是否安全: {result1['is_safe']}")
    if not result1['is_safe']:
        print(f"阻断原因: {result1['block_reason']}")
    
    # 查看权重
    stats = verifier.get_weight_statistics()
    print(f"\n动态权重分配:")
    for name, weights in stats['checkpoint_weights'].items():
        print(f"  {name}: {weights['current']:.3f} "
              f"(attention: {weights['attention_score']:.3f})")
    
    # 场景2: 代码生成任务
    print("\n--- 场景2: 代码生成任务 ---")
    response2 = "这肯定是最佳实现方案。"
    context2 = {
        'has_read_tool': True,
        'tool_used': False,
        'task_type': 'code_generation'
    }
    
    result2 = verifier.verify(response2, context2, task_type='code_generation')
    
    print(f"输入: {response2}")
    print(f"是否安全: {result2['is_safe']}")
    if result2['violations']:
        print(f"发现违规: {len(result2['violations'])} 个")
        for v in result2['violations']:
            print(f"  - {v['checkpoint']} (weight: {v['weight']:.3f})")
    
    # 修正后的响应
    print(f"\n修正后: {result2['corrected_response']}")
    
    return result2


async def demo_integrated_workflow():
    """演示完整集成工作流"""
    print("\n" + "="*70)
    print("演示3: 完整集成工作流 (AttnRes + Dynamic Verification)")
    print("="*70)
    
    # 创建组件
    attention_orchestrator = create_attention_orchestrator()
    dynamic_verifier = create_dynamic_verification_layer()
    
    # 注册 Agents
    attention_orchestrator.register_agent("understander", block_id=0)
    attention_orchestrator.register_agent("planner", block_id=0)
    attention_orchestrator.register_agent("executor", block_id=1)
    attention_orchestrator.register_agent("verifier", block_id=1)
    
    # 任务
    task = {
        'description': '分析用户需求并生成解决方案',
        'user_input': '我想做一个博客系统'
    }
    
    print(f"任务: {task['description']}")
    print(f"用户输入: {task['user_input']}")
    
    # 执行序列
    sequence = ["understander", "planner", "executor", "verifier"]
    
    # 步骤1: 使用注意力协调器执行
    print(f"\n--- 步骤1: Attention-Based Execution ---")
    attention_result = await attention_orchestrator.execute_with_attention(
        task, sequence
    )
    
    # 步骤2: 对最终输出进行动态验证
    print(f"\n--- 步骤2: Dynamic Verification ---")
    
    # 构建上下文
    context = {
        'task_type': 'analysis_and_generation',
        'num_agents': len(sequence),
        'global_confidence': attention_result.get('global_confidence', 0.5)
    }
    
    # 整合后的输出作为验证输入
    final_content = str(attention_result.get('integrated_outputs', ''))
    
    verification_result = dynamic_verifier.verify(
        final_content,
        context,
        task_type='analysis_and_generation'
    )
    
    print(f"验证结果: {'✅ 通过' if verification_result['is_safe'] else '❌ 失败'}")
    
    if verification_result['violations']:
        print(f"发现 {len(verification_result['violations'])} 个违规:")
        for v in verification_result['violations']:
            print(f"  - {v['checkpoint']} (weight: {v['weight']:.3f})")
    
    # 步骤3: 最终输出
    print(f"\n--- 步骤3: 最终结果 ---")
    
    final_output = {
        'attention_result': attention_result,
        'verification_result': verification_result,
        'is_fully_safe': verification_result['is_safe'],
        'metadata': {
            'attention_weights': attention_orchestrator.get_attention_visualization(),
            'verification_weights': dynamic_verifier.get_weight_statistics()
        }
    }
    
    print(f"完全安全: {final_output['is_fully_safe']}")
    print(f"不确定性链: {len(attention_result.get('uncertainty_chain', []))} 项")
    
    return final_output


async def demo_block_communication():
    """演示分块通信机制"""
    print("\n" + "="*70)
    print("演示4: Block Communication (Block AttnRes 思想)")
    print("="*70)
    
    orchestrator = create_attention_orchestrator()
    
    # 设置3个块
    # 块0: 输入处理
    orchestrator.register_agent("input_parser", block_id=0)
    orchestrator.register_agent("intent_classifier", block_id=0)
    
    # 块1: 核心处理
    orchestrator.register_agent("reasoning_engine", block_id=1)
    orchestrator.register_agent("knowledge_retriever", block_id=1)
    
    # 块2: 输出生成
    orchestrator.register_agent("response_generator", block_id=2)
    orchestrator.register_agent("quality_checker", block_id=2)
    
    print("块结构:")
    for block_id, agents in orchestrator.blocks.items():
        print(f"  Block {block_id}: {', '.join(agents)}")
    
    print("\n通信规则:")
    print("  - 同一块内: 全连接（密集通信）")
    print("  - 不同块间: 稀疏连接（通过attention选择）")
    print("  - 块间权重降低 70%（模拟 Block AttnRes）")
    
    task = {'description': '复杂查询处理'}
    sequence = [
        "input_parser", 
        "intent_classifier", 
        "reasoning_engine",
        "knowledge_retriever",
        "response_generator",
        "quality_checker"
    ]
    
    result = await orchestrator.execute_with_attention(task, sequence)
    
    viz = orchestrator.get_attention_visualization()
    print(f"\n实际注意力分布:")
    print(f"  块内通信 vs 块间通信比例可分析")
    
    return result


async def demo_learning_weights():
    """演示权重学习过程"""
    print("\n" + "="*70)
    print("演示5: 权重学习过程 (零初始化 → 自适应)")
    print("="*70)
    
    verifier = create_dynamic_verification_layer()
    
    print("初始状态 (零初始化):")
    stats = verifier.get_weight_statistics()
    for name, weights in stats['checkpoint_weights'].items():
        print(f"  {name}: {weights['current']:.3f}")
    
    # 模拟多次违规，观察权重变化
    print("\n--- 模拟多次外部数据违规 ---")
    
    for i in range(3):
        response = f"根据图片{i+1}..."
        context = {'has_image': True, 'image_verified': False}
        
        result = verifier.verify(response, context, task_type='image_analysis')
        
        print(f"\n第{i+1}次验证:")
        print(f"  是否安全: {result['is_safe']}")
        
        stats = verifier.get_weight_statistics()
        external_weight = stats['checkpoint_weights']['external_data_verification']['current']
        print(f"  外部数据检查点权重: {external_weight:.3f}")
    
    print("\n观察: 违规次数增加 → 对应检查点权重自动提高")
    
    return verifier.get_weight_statistics()


async def run_all_demos():
    """运行所有演示"""
    await demo_attention_orchestrator()
    await demo_dynamic_verification()
    await demo_integrated_workflow()
    await demo_block_communication()
    await demo_learning_weights()
    
    print("\n" + "="*70)
    print("集成演示完成")
    print("="*70)
    print("\n核心改进总结:")
    print("1. Attention-Based Orchestrator")
    print("   - Agent可以'回头看'前面所有Agent的输出")
    print("   - 用softmax attention动态加权聚合")
    print("   - 支持分块(Block)降低复杂度")
    print("")
    print("2. Dynamic Verification Layer")
    print("   - 检查点权重不是固定的")
    print("   - 根据任务类型和历史违规自适应调整")
    print("   - 高风险检查点获得更多'注意力'")
    print("")
    print("3. 整体设计思想")
    print("   - 零初始化: 初始均匀权重")
    print("   - 学习适应: 根据经验调整")
    print("   - 选择性关注: 重要的多关注，不重要的少关注")


if __name__ == "__main__":
    asyncio.run(run_all_demos())
