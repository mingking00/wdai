"""
wdai v3.3 Actix-web模式测试

测试Service Trait、Extractor、中间件链、共享状态
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

import asyncio
from typing import Any

from core.agent_system import (
    # Actix-web模式
    ServiceAgent,
    ServiceResult,
    TaskType,
    TaskContent,
    ContextExtractor,
    SharedStateManager,
    SharedData,
    LoggingMiddleware,
    MetricsMiddleware,
    MiddlewareChain,
    ActixStyleAgent,
    SharedStateMixin,
    # 基础组件
    AgentConfig,
    AgentRole,
    AgentResult,
    SubTask,
    NarrowContext,
)


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add(self, name: str, passed: bool, details: str = ""):
        status = "✅" if passed else "❌"
        self.tests.append(f"{status} {name}")
        if details:
            self.tests.append(f"   {details}")
        if passed:
            self.passed += 1
        else:
            self.failed += 1


async def test_service_trait():
    """测试Service Trait"""
    print("\n" + "="*50)
    print("测试1: Service Trait")
    print("="*50)
    
    results = TestResults()
    
    # 创建测试Agent
    class SimpleAgent(ServiceAgent):
        async def _handle(self, request):
            return ServiceResult.ok({'received': request.get('data')})
    
    agent = SimpleAgent('simple')
    
    # 测试基本调用
    result = await agent.call({'data': 'hello'})
    results.add("Service.call()", result.success and result.data['received'] == 'hello')
    
    # 测试ready
    results.add("Service.ready()", agent.ready())
    
    # 测试错误结果
    class ErrorAgent(ServiceAgent):
        async def _handle(self, request):
            return ServiceResult.err("test error")
    
    err_agent = ErrorAgent('error')
    err_result = await err_agent.call({})
    results.add("Service error", not err_result.success and err_result.error == "test error")
    
    print(f"\nService Trait: {results.passed}/{results.passed + results.failed} 通过")
    return results


async def test_extractor():
    """测试Extractor模式"""
    print("\n" + "="*50)
    print("测试2: Extractor模式")
    print("="*50)
    
    results = TestResults()
    
    request = {
        'task_type': 'code-review',
        'content': 'Review this code',
        'task_id': 'task-123',
        'parent_id': 'task-100',
        'metadata': {'priority': 'high'}
    }
    
    # 测试TaskType提取
    task_type = await TaskType.from_request(request)
    results.add("TaskType提取", task_type.value == 'code-review')
    
    # 测试TaskContent提取
    content = await TaskContent.from_request(request)
    results.add("TaskContent提取", content.value == 'Review this code')
    
    # 测试ContextExtractor
    ctx = await ContextExtractor.from_request(request)
    results.add("ContextExtractor", 
                ctx.task_id == 'task-123' and ctx.parent_id == 'task-100')
    
    print(f"\nExtractor: {results.passed}/{results.passed + results.failed} 通过")
    return results


async def test_shared_state():
    """测试共享状态"""
    print("\n" + "="*50)
    print("测试3: 共享状态 (Data<T>模式)")
    print("="*50)
    
    results = TestResults()
    
    # 测试SharedData
    data = {'count': 0, 'items': []}
    shared = SharedData(data)
    
    # 测试写锁
    with shared.write() as d:
        d['count'] += 1
        d['items'].append('item1')
    
    # 测试读锁
    with shared.read() as d:
        results.add("SharedData读写", d['count'] == 1 and len(d['items']) == 1)
    
    # 测试SharedStateManager
    manager = SharedStateManager()
    manager.register('stats', {'requests': 0})
    
    shared_stats = manager.get('stats')
    with shared_stats.write() as s:
        s['requests'] += 1
    
    with shared_stats.read() as s:
        results.add("SharedStateManager", s['requests'] == 1)
    
    print(f"\n共享状态: {results.passed}/{results.passed + results.failed} 通过")
    return results


async def test_middleware():
    """测试中间件链"""
    print("\n" + "="*50)
    print("测试4: 中间件链")
    print("="*50)
    
    results = TestResults()
    
    # 测试中间件链
    chain = MiddlewareChain()
    metrics = MetricsMiddleware()
    chain.add(LoggingMiddleware()).add(metrics)
    
    async def handler(request):
        return ServiceResult.ok({'processed': True})
    
    result = await chain.execute({'task': 'test'}, handler)
    results.add("中间件链执行", result.success)
    
    # 验证metrics记录
    mw_metrics = metrics.get_metrics()
    results.add("Metrics记录", mw_metrics['request_count'] == 1)
    
    print(f"\n中间件链: {results.passed}/{results.passed + results.failed} 通过")
    return results


async def test_actix_style_agent():
    """测试Actix-style Agent"""
    print("\n" + "="*50)
    print("测试5: Actix-style Agent")
    print("="*50)
    
    results = TestResults()
    
    # 创建配置
    config = AgentConfig(
        role=AgentRole.CODER,
        name='test-coder',
        expertise=['python']
    )
    
    # 创建Actix-style Agent
    class MyAgent(ActixStyleAgent):
        async def process(self, subtask: SubTask, context: NarrowContext) -> Any:
            return {'output': f'Processed: {subtask.description[:20]}'}
        
        def can_handle(self, task_type: str) -> bool:
            return task_type in ['code', 'python']
    
    agent = MyAgent(config)
    agent.add_middleware(LoggingMiddleware())
    
    # 创建测试子任务
    subtask = SubTask(
        id='test-1',
        type='code',
        description='print("hello world")',
        parent_id='parent-1'
    )
    context = NarrowContext(
        subtask=subtask,
        parent_goal='Test goal'
    )
    
    # 测试执行
    result = await agent.execute(subtask, context)
    results.add("ActixAgent.execute()", result.success)
    
    # 测试Service接口
    service_result = await agent.call({
        'subtask': subtask,
        'context': context,
        'task_type': 'code',
        'content': 'print("hello")',
        'task_id': 'test-2'
    })
    results.add("ActixAgent.call()", service_result.success)
    
    print(f"\nActix-style Agent: {results.passed}/{results.passed + results.failed} 通过")
    return results


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("wdai v3.3 Actix-web模式测试套件")
    print("="*60)
    
    all_results = [
        await test_service_trait(),
        await test_extractor(),
        await test_shared_state(),
        await test_middleware(),
        await test_actix_style_agent(),
    ]
    
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total = total_passed + total_failed
    
    print("\n" + "="*60)
    print(f"最终汇总: {total_passed}/{total} 通过 ({total_passed/total*100:.0f}%)")
    print("="*60)
    
    if total_failed == 0:
        print("\n🎉 所有测试通过! Actix-web模式工作正常")
    else:
        print(f"\n⚠️ {total_failed} 个测试失败")
    
    return total_failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
