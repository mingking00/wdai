"""
AttnRes 集成实现验证测试
全面测试所有核心功能
"""

import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system import (
    create_attention_orchestrator,
    AttentionConfig,
    create_dynamic_verification_layer,
    CheckpointType,
)


class AttnResImplementationValidator:
    """AttnRes 实现验证器"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name: str, condition: bool, details: str = ""):
        """记录测试结果"""
        if condition:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"
        
        self.tests.append({
            'name': name,
            'status': status,
            'details': details
        })
        
        print(f"{status}: {name}")
        if details and not condition:
            print(f"    Details: {details}")
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*70)
        print("测试总结")
        print("="*70)
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"总计: {self.passed + self.failed}")
        print(f"通过率: {self.passed/(self.passed+self.failed)*100:.1f}%")
        
        if self.failed == 0:
            print("\n🎉 所有测试通过！实现验证成功。")
        else:
            print(f"\n⚠️ 有 {self.failed} 个测试失败，需要检查。")


async def validate_attention_orchestrator():
    """验证 AttentionBasedOrchestrator"""
    print("\n" + "="*70)
    print("测试1: AttentionBasedOrchestrator")
    print("="*70)
    
    validator = AttnResImplementationValidator()
    
    # 测试1.1: 创建
    try:
        orchestrator = create_attention_orchestrator()
        validator.test("创建协调器", True)
    except Exception as e:
        validator.test("创建协调器", False, str(e))
        return validator
    
    # 测试1.2: 配置
    try:
        config = AttentionConfig(num_blocks=2, temperature=1.0)
        orchestrator.config = config
        validator.test("设置配置", orchestrator.config.num_blocks == 2)
    except Exception as e:
        validator.test("设置配置", False, str(e))
    
    # 测试1.3: 注册Agent
    try:
        orchestrator.register_agent("agent1", block_id=0)
        orchestrator.register_agent("agent2", block_id=0)
        orchestrator.register_agent("agent3", block_id=1)
        validator.test("注册Agent", len(orchestrator.agent_states) == 3)
    except Exception as e:
        validator.test("注册Agent", False, str(e))
    
    # 测试1.4: 分块结构
    try:
        validator.test("分块结构", 
                      0 in orchestrator.blocks and 1 in orchestrator.blocks)
    except Exception as e:
        validator.test("分块结构", False, str(e))
    
    # 测试1.5: 零初始化
    try:
        state = orchestrator.agent_states["agent1"]
        # 查询向量应该初始化为0
        import numpy as np
        is_zero_init = np.allclose(state.query_vector, 0)
        validator.test("零初始化", is_zero_init)
    except Exception as e:
        validator.test("零初始化", False, str(e))
    
    # 测试1.6: 执行带注意力
    try:
        task = {'description': '测试任务'}
        sequence = ["agent1", "agent2", "agent3"]
        result = await orchestrator.execute_with_attention(task, sequence)
        validator.test("执行带注意力", 'integrated_outputs' in result)
    except Exception as e:
        validator.test("执行带注意力", False, str(e))
    
    # 测试1.7: 注意力矩阵
    try:
        viz = orchestrator.get_attention_visualization()
        validator.test("注意力可视化", 
                      'attention_matrix' in viz and 'agent_sequence' in viz)
    except Exception as e:
        validator.test("注意力可视化", False, str(e))
    
    # 测试1.8: 权重计算
    try:
        if orchestrator.output_memory:
            weights = orchestrator.output_memory[0].get('attention_weights', [])
            # 权重应该归一化（和为1）
            import numpy as np
            if weights:
                is_normalized = abs(sum(weights) - 1.0) < 0.01
                validator.test("权重归一化", is_normalized)
            else:
                validator.test("权重归一化", True, "首个Agent无权重")
        else:
            validator.test("权重归一化", False, "无输出记忆")
    except Exception as e:
        validator.test("权重归一化", False, str(e))
    
    validator.print_summary()
    return validator


async def validate_dynamic_verification():
    """验证 DynamicVerificationLayer"""
    print("\n" + "="*70)
    print("测试2: DynamicVerificationLayer")
    print("="*70)
    
    validator = AttnResImplementationValidator()
    
    # 测试2.1: 创建
    try:
        verifier = create_dynamic_verification_layer()
        validator.test("创建验证层", True)
    except Exception as e:
        validator.test("创建验证层", False, str(e))
        return validator
    
    # 测试2.2: 检查点初始化
    try:
        validator.test("检查点初始化", 
                      len(verifier.checkpoints) > 0)
    except Exception as e:
        validator.test("检查点初始化", False, str(e))
    
    # 测试2.3: 零初始化权重
    try:
        initial_weights = [cp.current_weight for cp in verifier.checkpoints.values()]
        # 零初始化时权重应该比较均匀
        import numpy as np
        std = np.std(initial_weights)
        validator.test("零初始化权重", std < 0.1, f"标准差: {std}")
    except Exception as e:
        validator.test("零初始化权重", False, str(e))
    
    # 测试2.4: 验证功能
    try:
        result = verifier.verify("测试文本", {}, 'general')
        validator.test("基本验证", 'is_safe' in result)
    except Exception as e:
        validator.test("基本验证", False, str(e))
    
    # 测试2.5: 任务类型自适应
    try:
        # 图片任务
        result1 = verifier.verify("根据图片...", 
                                  {'has_image': True, 'image_verified': False},
                                  'image_analysis')
        
        # 代码任务
        result2 = verifier.verify("这肯定是对的",
                                  {'has_read_tool': True, 'tool_used': False},
                                  'code_generation')
        
        stats1 = verifier.get_weight_statistics()
        external_weight_img = stats1['checkpoint_weights']['external_data_verification']['current']
        tool_weight_code = stats1['checkpoint_weights']['tool_usage']['current']
        
        # 图片任务中 external_data 权重应该较高
        validator.test("任务类型自适应", 
                      external_weight_img > 0.25 or tool_weight_code > 0.25,
                      f"img_ext={external_weight_img:.3f}, code_tool={tool_weight_code:.3f}")
    except Exception as e:
        validator.test("任务类型自适应", False, str(e))
    
    # 测试2.6: 违规记录
    try:
        # 创建会触发违规的场景
        verifier2 = create_dynamic_verification_layer()
        result = verifier2.verify("这绝对是正确的",
                                  {},
                                  'general')
        
        stats = verifier2.get_weight_statistics()
        has_history = any(h['count'] > 0 for h in stats['violation_history'].values())
        validator.test("违规记录", has_history)
    except Exception as e:
        validator.test("违规记录", False, str(e))
    
    # 测试2.7: 权重学习
    try:
        verifier3 = create_dynamic_verification_layer()
        initial_stats = verifier3.get_weight_statistics()
        initial_external = initial_stats['checkpoint_weights']['external_data_verification']['base']
        
        # 多次违规
        for _ in range(3):
            verifier3.verify("根据图片...", 
                            {'has_image': True, 'image_verified': False},
                            'image_analysis')
        
        final_stats = verifier3.get_weight_statistics()
        final_external = final_stats['checkpoint_weights']['external_data_verification']['base']
        
        # 基础权重应该有所变化（学习效果）
        validator.test("权重学习", 
                      abs(final_external - initial_external) > 0.001,
                      f"初始: {initial_external:.3f}, 最终: {final_external:.3f}")
    except Exception as e:
        validator.test("权重学习", False, str(e))
    
    # 测试2.8: Softmax归一化
    try:
        stats = verifier.get_weight_statistics()
        weights = [w['current'] for w in stats['checkpoint_weights'].values()]
        import numpy as np
        is_normalized = abs(sum(weights) - 1.0) < 0.01
        validator.test("Softmax归一化", is_normalized, f"权重和: {sum(weights):.3f}")
    except Exception as e:
        validator.test("Softmax归一化", False, str(e))
    
    validator.print_summary()
    return validator


async def validate_integration():
    """验证集成"""
    print("\n" + "="*70)
    print("测试3: 集成测试")
    print("="*70)
    
    validator = AttnResImplementationValidator()
    
    # 测试3.1: 组合使用
    try:
        orchestrator = create_attention_orchestrator()
        verifier = create_dynamic_verification_layer()
        
        orchestrator.register_agent("agent1", 0)
        orchestrator.register_agent("agent2", 0)
        
        result = await orchestrator.execute_with_attention(
            {'description': '测试'},
            ['agent1', 'agent2']
        )
        
        # 对结果进行验证
        verify_result = verifier.verify(
            str(result),
            {'task_type': 'test'},
            'general'
        )
        
        validator.test("组合使用", 
                      'integrated_outputs' in result and 'is_safe' in verify_result)
    except Exception as e:
        validator.test("组合使用", False, str(e))
    
    # 测试3.2: 块间通信
    try:
        orch = create_attention_orchestrator()
        orch.config.num_blocks = 2
        
        orch.register_agent("a1", block_id=0)
        orch.register_agent("a2", block_id=0)
        orch.register_agent("a3", block_id=1)  # 不同块
        
        result = await orch.execute_with_attention(
            {'description': '测试块间'},
            ['a1', 'a2', 'a3']
        )
        
        validator.test("块间通信", 'attention_history' in result)
    except Exception as e:
        validator.test("块间通信", False, str(e))
    
    # 测试3.3: 性能测试
    try:
        import time
        orch = create_attention_orchestrator()
        verifier = create_dynamic_verification_layer()
        
        # 注册多个agent
        for i in range(5):
            orch.register_agent(f"agent{i}", block_id=i % 2)
        
        start = time.time()
        
        result = await orch.execute_with_attention(
            {'description': '性能测试'},
            ['agent0', 'agent1', 'agent2', 'agent3', 'agent4']
        )
        
        elapsed = time.time() - start
        
        validator.test("性能可接受", elapsed < 1.0, f"耗时: {elapsed:.3f}s")
    except Exception as e:
        validator.test("性能可接受", False, str(e))
    
    validator.print_summary()
    return validator


async def run_all_validations():
    """运行所有验证"""
    print("="*70)
    print("AttnRes 实现验证")
    print("="*70)
    
    v1 = await validate_attention_orchestrator()
    v2 = await validate_dynamic_verification()
    v3 = await validate_integration()
    
    # 总总结
    total_passed = v1.passed + v2.passed + v3.passed
    total_failed = v1.failed + v2.failed + v3.failed
    total = total_passed + total_failed
    
    print("\n" + "="*70)
    print("最终验证结果")
    print("="*70)
    print(f"总测试数: {total}")
    print(f"通过: {total_passed} ✅")
    print(f"失败: {total_failed} ❌")
    print(f"通过率: {total_passed/total*100:.1f}%")
    
    if total_failed == 0:
        print("\n🎉🎉🎉 AttnRes 集成实现验证完全成功！🎉🎉🎉")
        print("\n实现特性:")
        print("  ✅ Attention-Based Orchestrator - Agent可选择性关注历史")
        print("  ✅ Dynamic Verification Layer - 检查点权重自适应")
        print("  ✅ Block Communication - 分块降低复杂度")
        print("  ✅ Zero Initialization - 零初始化策略")
        print("  ✅ Online Learning - 在线学习权重")
        print("  ✅ Softmax Normalization - 权重归一化")
    else:
        print(f"\n⚠️ 有 {total_failed} 个测试失败，请检查实现。")


if __name__ == "__main__":
    asyncio.run(run_all_validations())
