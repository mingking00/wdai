"""
wdai v3.4.1 综合示例：推理追踪 + 结构化思维链

展示如何将两个系统集成使用：
1. StructuredCoT 提供结构化推理框架
2. ReasoningTracer 提供实时追踪和记录
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

import asyncio
from typing import Dict, Any

from core.agent_system import (
    # 推理追踪
    ServiceAgent,
    ServiceResult,
    ReasoningStepType,
    tracer,
    # 结构化思维链
    QuickCoT,
)


class EnhancedAgent(ServiceAgent):
    """
    增强版 Agent：结构化思维链 + 推理追踪
    
    每个任务都生成：
    1. 结构化思维链文档 (Markdown)
    2. 实时推理追踪日志
    3. 可导出的完整记录 (JSON)
    """
    
    def __init__(self, name: str):
        super().__init__(name, enable_tracing=True)
    
    async def _handle(self, request: Dict[str, Any]) -> ServiceResult:
        """
        处理请求，同时使用：
        - StructuredCoT 记录结构化思维
        - ReasoningTracer 记录执行过程
        """
        task_id = request.get('task_id', 'unknown')
        
        # 1. 使用结构化思维链框架
        cot = QuickCoT()
        
        # 2. 同时使用推理追踪 (直接使用 tracer)
        
        # ========== 🎯 任务理解 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.UNDERSTAND, 
            "开始分析用户需求", self.name
        )
        
        cot.understand(
            user_intent=request.get('content', '')[:50],
            explicit_requirements=["完成任务", "记录过程"],
            success_criteria=["任务完成", "思维链完整"]
        )
        
        # ========== 🔍 现状分析 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.ANALYZE,
            "分析当前环境和可用资源", self.name
        )
        
        cot.analyze(
            available_data=["代码库", "文档"],
            key_observations=["使用wdai框架", "有推理追踪"]
        )
        
        # ========== 📋 执行规划 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.PLAN,
            "制定执行步骤", self.name
        )
        
        cot.plan(
            approach="结合结构化思维和实时追踪",
            execution_steps=[
                "1. 初始化结构化CoT",
                "2. 记录推理步骤",
                "3. 导出结果"
            ]
        )
        
        # ========== 🎲 决策记录 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.DECISION,
            "选择最优方案", self.name
        )
        
        cot.decide(
            decisions=["使用QuickCoT快速填充", "使用tracer实时记录"],
            reasoning="两者互补，CoT提供结构，tracer提供时间线",
            confidence=90
        )
        
        # ========== ⚙️ 执行过程 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.EXECUTE,
            "执行具体步骤 (33%)", self.name
        )
        
        cot.execute(
            steps_completed=["✓ 初始化CoT", "✓ 填充章节"],
            unexpected_findings=["两个系统配合良好"]
        )
        
        # 模拟处理时间
        await asyncio.sleep(0.1)
        
        self.tracer.add_step(
            task_id, ReasoningStepType.EXECUTE,
            "执行具体步骤 (66%)", self.name
        )
        
        await asyncio.sleep(0.1)
        
        # ========== ✅ 结果验证 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.VERIFY,
            "验证结果", self.name
        )
        
        cot.verify(
            results_delivered=["结构化思维链", "推理追踪日志"],
            criteria_met=["✓ 结构完整", "✓ 记录清晰"],
            overall_quality=95
        )
        
        # ========== 💭 反思总结 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.REFLECT,
            "提炼经验", self.name
        )
        
        cot.reflect(
            key_learnings=["结构化+追踪双管齐下效果更好"],
            reusable_patterns=["QuickCoT.tracer组合模式"]
        )
        
        # 构建最终思维链
        structured_cot = cot.build()
        
        # 导出结果
        result_data = {
            'task_type': request.get('task_type'),
            'cot_summary': {
                'sections_filled': len(structured_cot._filled_sections),
                'progress': structured_cot.get_progress(),
            },
            'trace_summary': {
                'task_id': task_id,
                'steps_recorded': len(tracer.get_trace(task_id).steps) if tracer.get_trace(task_id) else 0
            }
        }
        
        # 保存结构化思维链到文件
        md_output = structured_cot.export("markdown")
        output_file = f"/tmp/wdai_cot_{task_id}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_output)
        
        result_data['output_file'] = output_file
        
        return ServiceResult.ok(result_data)


async def demo_combined_usage():
    """演示组合使用"""
    print("\n" + "="*70)
    print("wdai v3.4.1 综合示例")
    print("="*70)
    
    agent = EnhancedAgent("enhanced-agent")
    
    print("\n🚀 执行任务...\n")
    
    result = await agent.call({
        'task_type': 'analysis',
        'content': '分析代码性能瓶颈并给出优化建议',
        'metadata': {'priority': 'high'}
    })
    
    if result.success:
        data = result.data
        print("\n" + "="*70)
        print("📊 执行结果")
        print("="*70)
        print(f"任务类型: {data['task_type']}")
        print(f"思维链章节: {data['cot_summary']['sections_filled']}/7")
        print(f"推理步骤: {data['trace_summary']['steps_recorded']}")
        print(f"完成度: {data['cot_summary']['progress']['field_progress']*100:.0f}%")
        print(f"输出文件: {data['output_file']}")
        
        # 显示文件内容预览
        with open(data['output_file'], 'r') as f:
            content = f.read()
        
        print(f"\n📝 结构化思维链预览 (前500字符):")
        print(content[:500] + "...")
        
        print("\n✅ 任务完成！")
        return True
    else:
        print(f"\n❌ 任务失败: {result.error}")
        return False


async def demo_comparison():
    """
    对比：三种不同级别的推理透明度
    """
    print("\n" + "="*70)
    print("三种推理透明度级别对比")
    print("="*70)
    
    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │  Level 0: 黑盒推理 (传统AI)                                      │
    │  ─────────────────────────                                       │
    │  用户：分析代码                                                  │
    │  AI：[内部处理...] → 结果                                       │
    │  → 完全不可见                                                    │
    └─────────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────────┐
    │  Level 1: 推理追踪 (v3.4)                                        │
    │  ───────────────────────                                         │
    │  用户：分析代码                                                  │
    │  AI：[🎯] 理解任务                                               │
    │      [🔍] 分析代码                                               │
    │      [⚙️] 执行分析                                               │
    │      [✅] 验证结果                                               │
    │  → 可见步骤类型，但内容不详细                                    │
    └─────────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────────┐
    │  Level 2: 结构化思维链 (v3.4.1) ⭐                               │
    │  ───────────────────────────────                                 │
    │  用户：分析代码                                                  │
    │  AI：                                                            │
    │  ┌──────────────────────────────────────────────┐               │
    │  │ 🎯 任务理解                                   │               │
    │  │   用户意图：优化代码性能                      │               │
    │  │   明确要求：找出瓶颈、提供建议                │               │
    │  │   成功标准：找到≥1个瓶颈                      │               │
    │  ├──────────────────────────────────────────────┤               │
    │  │ 🔍 现状分析                                   │               │
    │  │   可用数据：源代码、测试用例                  │               │
    │  │   关键观察：有嵌套循环，可能是O(n²)           │               │
    │  ├──────────────────────────────────────────────┤               │
    │  │ 🎲 决策记录                                   │               │
    │  │   选择：使用哈希表优化                        │               │
    │  │   理由：可将复杂度降至O(n)                    │               │
    │  │   置信度：90%                                 │               │
    │  └──────────────────────────────────────────────┘               │
    │  → 完整结构化文档，每个字段都可审查                              │
    └─────────────────────────────────────────────────────────────────┘
    """)


async def run_demo():
    """运行所有演示"""
    results = []
    
    try:
        results.append(("组合使用演示", await demo_combined_usage()))
    except Exception as e:
        print(f"\n❌ 组合使用演示失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("组合使用演示", False))
    
    try:
        await demo_comparison()
        results.append(("对比演示", True))
    except Exception as e:
        print(f"\n❌ 对比演示失败: {e}")
        results.append(("对比演示", False))
    
    print("\n" + "="*70)
    print("演示完成")
    print("="*70)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status}: {name}")
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = asyncio.run(run_demo())
    sys.exit(0 if success else 1)
