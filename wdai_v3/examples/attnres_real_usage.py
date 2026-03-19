"""
实际使用示例：用 AttnRes 改进的 Agent 系统处理真实任务

展示如何在实际场景中使用：
1. AttentionBasedOrchestrator - 处理多 Agent 协作
2. DynamicVerificationLayer - 动态验证输出
"""

import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system import (
    create_attention_orchestrator,
    create_dynamic_verification_layer,
)


class RealWorldExample:
    """真实世界使用示例"""
    
    def __init__(self):
        self.orchestrator = create_attention_orchestrator()
        self.verifier = create_dynamic_verification_layer()
        self._setup_agents()
    
    def _setup_agents(self):
        """设置 Agent 架构"""
        # Block 0: 理解与分析
        self.orchestrator.register_agent("requirement_analyzer", block_id=0)
        self.orchestrator.register_agent("context_gatherer", block_id=0)
        
        # Block 1: 方案设计
        self.orchestrator.register_agent("solution_designer", block_id=1)
        self.orchestrator.register_agent("tech_selector", block_id=1)
        
        # Block 2: 实现与验证
        self.orchestrator.register_agent("code_generator", block_id=2)
        self.orchestrator.register_agent("code_reviewer", block_id=2)
        self.orchestrator.register_agent("test_generator", block_id=2)
    
    async def generate_blog_system(self, requirements: str) -> dict:
        """
        示例1: 生成博客系统
        
        使用注意力协调器，让后面的 Agent 可以选择性关注前面的分析结果
        """
        print("="*70)
        print("📝 任务: 生成博客系统")
        print("="*70)
        print(f"需求: {requirements}")
        
        task = {
            'description': '设计并实现博客系统',
            'requirements': requirements,
            'constraints': ['安全性', '性能', '可维护性']
        }
        
        # 定义执行序列
        sequence = [
            "requirement_analyzer",   # 分析需求
            "context_gatherer",       # 收集上下文
            "solution_designer",      # 设计方案
            "tech_selector",          # 选择技术栈
            "code_generator",         # 生成代码
            "code_reviewer",          # 代码审查
            "test_generator"          # 生成测试
        ]
        
        # 使用注意力协调器执行
        result = await self.orchestrator.execute_with_attention(task, sequence)
        
        print("\n--- 执行结果 ---")
        print(f"全局置信度: {result.get('global_confidence', 0):.3f}")
        print(f"不确定性链: {len(result.get('uncertainty_chain', []))} 项")
        
        # 可视化注意力
        viz = self.orchestrator.get_attention_visualization()
        print("\n--- 注意力分布 ---")
        for i, mem in enumerate(result.get('integrated_outputs', [])):
            print(f"  [{i+1}] {mem['agent']}: weight={mem['weight']:.3f}")
        
        # 对最终输出进行动态验证
        print("\n--- 认知安全验证 ---")
        final_content = str(result.get('integrated_outputs', ''))
        
        verify_result = self.verifier.verify(
            final_content,
            context={'task_type': 'code_generation', 'has_read_tool': True},
            task_type='code_generation'
        )
        
        print(f"验证结果: {'✅ 通过' if verify_result['is_safe'] else '❌ 失败'}")
        
        if verify_result['violations']:
            print(f"发现 {len(verify_result['violations'])} 个违规:")
            for v in verify_result['violations']:
                print(f"  - {v['checkpoint']} (weight: {v['weight']:.3f})")
        
        return {
            'outputs': result.get('integrated_outputs', []),
            'confidence': result.get('global_confidence', 0),
            'is_safe': verify_result['is_safe'],
            'violations': verify_result.get('violations', [])
        }
    
    async def analyze_image_content(self, image_description: str) -> dict:
        """
        示例2: 分析图片内容
        
        验证层会自动提高 external_data 检查点的权重
        """
        print("\n" + "="*70)
        print("🖼️  任务: 分析图片内容")
        print("="*70)
        print(f"图片描述: {image_description}")
        
        # 模拟图片分析任务
        task = {
            'description': '分析图片内容',
            'image_description': image_description
        }
        
        sequence = [
            "context_gatherer",
            "solution_designer"
        ]
        
        result = await self.orchestrator.execute_with_attention(task, sequence)
        
        # 对图片相关内容进行验证
        # 注意：验证层会自动识别这是图片任务，提高 external_data 权重
        print("\n--- 图片内容验证 ---")
        
        # 模拟一个可能包含问题的响应
        response = f"根据图片，{image_description}"
        
        verify_result = self.verifier.verify(
            response,
            context={'has_image': True, 'image_verified': False},  # 未验证的图片！
            task_type='image_analysis'  # 图片任务类型
        )
        
        print(f"验证结果: {'✅ 通过' if verify_result['is_safe'] else '❌ 失败'}")
        
        if not verify_result['is_safe']:
            print(f"⚠️  阻断原因: {verify_result['block_reason']}")
        
        # 显示动态权重
        stats = self.verifier.get_weight_statistics()
        print("\n--- 动态权重分配 (图片任务) ---")
        for name, weights in stats['checkpoint_weights'].items():
            print(f"  {name}: {weights['current']:.3f}")
        
        return {
            'is_safe': verify_result['is_safe'],
            'block_reason': verify_result.get('block_reason'),
            'weights': stats['checkpoint_weights']
        }
    
    async def research_topic(self, topic: str) -> dict:
        """
        示例3: 研究某个主题
        
        展示权重学习：多次研究后，系统会记住哪些检查点更重要
        """
        print("\n" + "="*70)
        print("🔍 任务: 研究主题")
        print("="*70)
        print(f"主题: {topic}")
        
        # 初始权重
        initial_stats = self.verifier.get_weight_statistics()
        initial_external = initial_stats['checkpoint_weights']['external_data_verification']['current']
        print(f"\n初始 external_data 权重: {initial_external:.3f}")
        
        # 模拟多次研究，其中包含未经验证的外部数据引用
        responses = [
            f"根据文献，{topic}是一种...",  # 未标注来源
            f"研究表明，{topic}可以...",     # 未标注来源
            f"{topic}的主要特点是...",       # 未标注来源
        ]
        
        for i, response in enumerate(responses, 1):
            print(f"\n--- 研究 {i} ---")
            print(f"输入: {response}")
            
            verify_result = self.verifier.verify(
                response,
                context={'has_external_ref': True},
                task_type='factual_qa'
            )
            
            print(f"结果: {'✅ 通过' if verify_result['is_safe'] else '⚠️  发现问题'}")
        
        # 查看学习后的权重
        final_stats = self.verifier.get_weight_statistics()
        final_external = final_stats['checkpoint_weights']['external_data_verification']['current']
        print(f"\n最终 external_data 权重: {final_external:.3f}")
        print(f"变化: {final_external - initial_external:+.3f}")
        
        return {
            'weight_change': final_external - initial_external,
            'final_weights': final_stats['checkpoint_weights']
        }
    
    async def compare_with_traditional(self) -> dict:
        """
        示例4: 对比传统方式 vs Attention方式
        """
        print("\n" + "="*70)
        print("⚖️  对比: 传统方式 vs Attention方式")
        print("="*70)
        
        print("\n--- 传统方式 (Linear Chain) ---")
        print("A → B → C → D")
        print("问题:")
        print("  - D 只能看到 C 的输出")
        print("  - A 和 B 的信息可能被稀释")
        print("  - 每个 Agent 都平等对待所有输入")
        
        print("\n--- Attention 方式 (AttnRes) ---")
        print("A → B(attention to A) → C(attention to A,B) → D(attention to A,B,C)")
        print("优势:")
        print("  - D 可以选择性关注 A、B、C 中最相关的")
        print("  - 早期重要信息不会被稀释")
        print("  - 每个 Agent 学习如何加权历史信息")
        
        # 实际演示
        print("\n--- 实际演示 ---")
        
        task = {
            'description': '对比演示',
            'steps': ['分析', '设计', '实现', '验证']
        }
        
        # 重新初始化以获取清晰的注意力分布
        fresh_orchestrator = create_attention_orchestrator()
        fresh_orchestrator.register_agent("step1", block_id=0)
        fresh_orchestrator.register_agent("step2", block_id=0)
        fresh_orchestrator.register_agent("step3", block_id=1)
        fresh_orchestrator.register_agent("step4", block_id=1)
        
        result = await fresh_orchestrator.execute_with_attention(
            task, 
            ['step1', 'step2', 'step3', 'step4']
        )
        
        print("\n注意力权重矩阵:")
        viz = fresh_orchestrator.get_attention_visualization()
        for i, weights in enumerate(viz.get('attention_matrix', [])):
            if weights:
                print(f"  Step {i+1} 关注前面: {weights}")
        
        return {
            'attention_matrix': viz.get('attention_matrix', []),
            'agent_sequence': viz.get('agent_sequence', [])
        }


async def main():
    """主函数：运行所有示例"""
    example = RealWorldExample()
    
    # 示例1: 生成博客系统
    result1 = await example.generate_blog_system(
        "需要一个支持Markdown的博客系统，有用户认证和评论功能"
    )
    
    # 示例2: 分析图片内容（验证层自动提高外部数据权重）
    result2 = await example.analyze_image_content(
        "这张截图显示了一个错误提示"
    )
    
    # 示例3: 研究主题（展示权重学习）
    result3 = await example.research_topic(
        "Attention Residuals"
    )
    
    # 示例4: 对比传统 vs Attention
    result4 = await example.compare_with_traditional()
    
    # 总结
    print("\n" + "="*70)
    print("使用示例完成")
    print("="*70)
    print("\n核心收获:")
    print("1. AttentionBasedOrchestrator 让 Agent 能选择性关注历史")
    print("2. DynamicVerificationLayer 根据任务类型自动调整检查权重")
    print("3. 权重学习让系统从经验中改进")
    print("4. 分块设计平衡了效率和效果")


if __name__ == "__main__":
    asyncio.run(main())
