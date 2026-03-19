"""
wdai v3.4 推理追踪测试

演示新的推理追踪功能:
1. 自动记录 Agent 推理过程
2. 实时显示工作流状态
3. 结构化思维链
4. 多 Agent 共享推理上下文
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

import asyncio
from typing import Any, Dict

from core.agent_system import (
    # 推理追踪
    ReasoningTracer,
    ReasoningStep,
    ReasoningStepType,
    TaskTrace,
    ConsoleObserver,
    StructuredReasoning,
    tracer,
    # Service Trait
    ServiceAgent,
    ServiceResult,
    TaskType,
    TaskContent,
    SharedStateManager,
    LoggingMiddleware,
    MetricsMiddleware,
)


class TracedAgent(ServiceAgent):
    """
    带推理追踪的 Agent
    
    自动记录每一步推理过程
    """
    
    def __init__(self, name: str):
        super().__init__(name, enable_tracing=True)
        self.add_middleware(LoggingMiddleware())
    
    async def _handle(self, request: Dict[str, Any]) -> ServiceResult:
        """处理请求，同时记录推理过程"""
        task_id = request.get('task_id', 'unknown')
        
        # 使用结构化推理
        reasoning = StructuredReasoning(self.tracer, task_id, self.name)
        
        # 1. 理解任务
        task_type = request.get('task_type', 'unknown')
        content = request.get('content', '')
        reasoning.understand(
            goal=f"处理 {task_type} 任务",
            constraints="必须在10秒内完成",
            success_criteria="返回正确结果"
        )
        
        # 2. 分析
        reasoning.analyze(
            current_state=f"收到任务: {content[:50]}",
            challenges="时间限制、准确性要求",
            resources="可用工具、历史数据"
        )
        
        # 3. 规划
        reasoning.plan([
            "验证输入参数",
            "执行核心逻辑", 
            "验证输出结果"
        ])
        
        # 4. 决策
        reasoning.decide(
            option="直接处理",
            reasoning="任务简单，无需分解",
            risks="可能遗漏边界情况"
        )
        
        # 5. 执行
        reasoning.execute(f"正在处理 {task_type}", "33%")
        await asyncio.sleep(0.1)  # 模拟处理
        
        reasoning.execute(f"验证参数", "66%")
        await asyncio.sleep(0.1)
        
        # 6. 验证
        result = f"处理完成: {content[:30]}..."
        reasoning.verify(
            result=result,
            is_valid=True,
            improvements="可以添加更多边界检查"
        )
        
        return ServiceResult.ok({'result': result, 'task_type': task_type})


async def test_basic_tracing():
    """测试基础推理追踪"""
    print("\n" + "="*60)
    print("测试1: 基础推理追踪")
    print("="*60)
    
    agent = TracedAgent("test-agent")
    
    result = await agent.call({
        'task_type': 'code-review',
        'content': 'Review this Python function for performance issues',
        'metadata': {'priority': 'high'}
    })
    
    # 导出追踪记录
    trace = tracer.get_trace(list(tracer.get_all_traces().keys())[-1])
    if trace:
        print(f"\n📊 任务统计:")
        print(f"  - 总步骤: {len(trace.steps)}")
        print(f"  - 耗时: {trace.end_time - trace.start_time:.3f}s" if trace.end_time else "  - 运行中")
        print(f"  - 状态: {trace.status}")
    
    return result.success


async def test_multi_agent_tracing():
    """测试多 Agent 协作追踪"""
    print("\n" + "="*60)
    print("测试2: 多 Agent 协作追踪")
    print("="*60)
    
    class CoderAgent(TracedAgent):
        async def _handle(self, request):
            task_id = request.get('task_id', 'unknown')
            reasoning = StructuredReasoning(self.tracer, task_id, self.name)
            
            reasoning.understand(goal="编写代码", constraints="符合PEP8")
            reasoning.execute("编写实现", "50%")
            await asyncio.sleep(0.1)
            reasoning.verify("代码完成", True)
            
            return ServiceResult.ok({'code': 'def hello(): pass'})
    
    class ReviewerAgent(TracedAgent):
        async def _handle(self, request):
            task_id = request.get('task_id', 'unknown')
            reasoning = StructuredReasoning(self.tracer, task_id, self.name)
            
            reasoning.understand(goal="审查代码", constraints="找出潜在bug")
            reasoning.execute("静态分析", "50%")
            await asyncio.sleep(0.1)
            reasoning.verify("无严重问题", True)
            
            return ServiceResult.ok({'issues': []})
    
    # 创建 Agent
    coder = CoderAgent("coder")
    reviewer = ReviewerAgent("reviewer")
    
    # 顺序执行
    print("\n📝 Coder 执行:")
    await coder.call({'task_type': 'code', 'content': 'implement feature'})
    
    print("\n🔍 Reviewer 执行:")
    await reviewer.call({'task_type': 'review', 'content': 'review code'})
    
    # 查看所有追踪
    traces = tracer.get_all_traces()
    print(f"\n📊 总任务数: {len(traces)}")
    
    return True


async def test_trace_export():
    """测试追踪记录导出"""
    print("\n" + "="*60)
    print("测试3: 追踪记录导出")
    print("="*60)
    
    agent = TracedAgent("export-agent")
    
    await agent.call({
        'task_type': 'analysis',
        'content': 'Analyze project structure'
    })
    
    # 导出到文件
    output_file = "/tmp/wdai_trace_test.json"
    tracer.export_all(output_file)
    
    print(f"\n💾 追踪记录已导出到: {output_file}")
    
    # 读取并显示摘要
    import json
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    print(f"📄 导出内容摘要:")
    for task_id, trace in list(data.items())[:1]:
        print(f"  任务: {task_id}")
        print(f"  - 类型: {trace['task_type']}")
        print(f"  - 步骤数: {trace['step_count']}")
        print(f"  - 步骤列表:")
        for step in trace['steps'][:3]:  # 只显示前3步
            print(f"    • [{step['step_type']}] {step['content'][:50]}...")
    
    return True


async def test_manual_tracing():
    """测试手动追踪API"""
    print("\n" + "="*60)
    print("测试4: 手动追踪API")
    print("="*60)
    
    # 手动创建任务追踪
    task_id = "manual-task-001"
    tracer.start_task(task_id, "manual-task", "user")
    
    # 手动添加步骤
    tracer.add_step(task_id, ReasoningStepType.UNDERSTAND, 
                   "理解用户请求", "user")
    tracer.add_step(task_id, ReasoningStepType.ANALYZE, 
                   "分析可行性", "user")
    tracer.add_step(task_id, ReasoningStepType.PLAN, 
                   "制定执行计划", "user")
    tracer.add_step(task_id, ReasoningStepType.EXECUTE, 
                   "执行步骤1", "user")
    tracer.add_step(task_id, ReasoningStepType.VERIFY, 
                   "验证结果", "user")
    
    tracer.complete_task(task_id, {"status": "done"})
    
    # 查看结果
    trace = tracer.get_trace(task_id)
    print(f"\n✅ 手动追踪完成:")
    print(f"  - 任务ID: {task_id}")
    print(f"  - 步骤数: {len(trace.steps)}")
    print(f"  - 状态: {trace.status}")
    
    return True


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("wdai v3.4 推理追踪测试套件")
    print("="*70)
    
    results = []
    
    try:
        results.append(("基础推理追踪", await test_basic_tracing()))
    except Exception as e:
        print(f"❌ 基础推理追踪失败: {e}")
        results.append(("基础推理追踪", False))
    
    try:
        results.append(("多Agent协作追踪", await test_multi_agent_tracing()))
    except Exception as e:
        print(f"❌ 多Agent协作追踪失败: {e}")
        results.append(("多Agent协作追踪", False))
    
    try:
        results.append(("追踪记录导出", await test_trace_export()))
    except Exception as e:
        print(f"❌ 追踪记录导出失败: {e}")
        results.append(("追踪记录导出", False))
    
    try:
        results.append(("手动追踪API", await test_manual_tracing()))
    except Exception as e:
        print(f"❌ 手动追踪API失败: {e}")
        results.append(("手动追踪API", False))
    
    # 汇总
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.0f}%)")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
