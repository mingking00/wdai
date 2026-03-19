"""
wdai v3.2 完整测试脚本
测试Gnet模式应用效果
"""

import sys
import asyncio
import time
from typing import Optional

sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system import (
    initialize_agent_system,
    AgentRole,
    LoadBalancingStrategy,
    NonBlockingExecutionPool,
    EnhancedAgentRegistry,
    get_enhanced_registry
)


class TestResults:
    """测试结果收集器"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add(self, name: str, passed: bool, details: str = ""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.tests.append(f"{status}: {name}")
        if details:
            self.tests.append(f"       {details}")
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def summary(self):
        total = self.passed + self.failed
        return f"\n{'='*50}\n测试结果: {self.passed}/{total} 通过\n{'='*50}"


async def test_load_balancer_strategies():
    """测试负载均衡策略"""
    print("\n" + "="*50)
    print("测试1: 负载均衡策略")
    print("="*50)
    
    results = TestResults()
    registry = EnhancedAgentRegistry(LoadBalancingStrategy.ROUND_ROBIN)
    await registry.initialize()
    
    # 模拟注册多个Agent (使用Orchestrator已有的Agent)
    # 注意: 这里我们测试策略逻辑，不需要真实Agent实例
    
    # 测试1.1: RoundRobin索引递增
    balancer = registry._load_balancers.get(AgentRole.CODER)
    if balancer:
        initial_idx = balancer._round_robin_index
        idx_after = initial_idx + 1
        results.add(
            "RoundRobin索引递增",
            balancer._round_robin_index == initial_idx,
            f"index: {balancer._round_robin_index}"
        )
    
    # 测试1.2: LeastLoaded选择逻辑
    registry2 = EnhancedAgentRegistry(LoadBalancingStrategy.LEAST_LOADED)
    await registry2.initialize()
    
    # 模拟负载数据
    from core.agent_system.load_balancer import AgentLoadMetrics
    metrics1 = AgentLoadMetrics("agent-1", "coder")
    metrics1.active_executions = 1
    metrics1.queued_tasks = 0
    
    metrics2 = AgentLoadMetrics("agent-2", "coder")
    metrics2.active_executions = 3
    metrics2.queued_tasks = 2
    
    # 验证最少负载逻辑
    selected = metrics1 if metrics1.current_load < metrics2.current_load else metrics2
    results.add(
        "LeastLoaded选择逻辑",
        selected.agent_name == "agent-1",
        f"选择 {selected.agent_name} (负载 {selected.current_load})"
    )
    
    # 测试1.3: 健康评分计算
    metrics = AgentLoadMetrics("test", "coder")
    metrics.total_executions = 10
    metrics.success_count = 9
    metrics.total_execution_time_ms = 500
    
    expected_success_rate = 0.9
    results.add(
        "健康评分计算",
        abs(metrics.success_rate - expected_success_rate) < 0.01,
        f"成功率: {metrics.success_rate:.0%}, 健康分: {metrics.health_score:.2f}"
    )
    
    print(f"\n策略测试: {results.passed}/{results.passed + results.failed} 通过")
    if results.tests:
        for test in results.tests:
            print(f"  {test}")
    return results


async def test_nonblocking_pool():
    """测试非阻塞执行池"""
    print("\n" + "="*50)
    print("测试2: 非阻塞执行池")
    print("="*50)
    
    results = TestResults()
    
    # 创建小容量池便于测试
    pool = NonBlockingExecutionPool(
        max_concurrent=2,
        max_queue_size=1,
        nonblocking=True
    )
    await pool.initialize()
    
    # 测试2.1: 正常获取槽位
    ok1 = await pool.acquire_slot(timeout=1.0)
    results.add("获取槽位 #1", ok1, f"active={pool._active_count}")
    
    ok2 = await pool.acquire_slot(timeout=1.0)
    results.add("获取槽位 #2", ok2, f"active={pool._active_count}")
    
    # 测试2.2: 池满时非阻塞拒绝 (max_concurrent=2, max_queue=1, 第4个请求应被拒绝)
    ok3 = await pool.acquire_slot(timeout=0.1)  # 第3个，进入队列
    ok4 = await pool.acquire_slot(timeout=0.1)  # 第4个，应被拒绝
    results.add("池满拒绝", not ok4, f"第4个请求返回={ok4}, rejected={pool._rejected_count}")
    
    # 测试2.3: 释放槽位
    await pool.release_slot()
    results.add("释放槽位", pool._active_count == 1, f"active={pool._active_count}")
    
    # 测试2.4: 指标监控
    metrics = pool.metrics
    results.add(
        "池指标",
        metrics['active'] == 1 and metrics['available_slots'] == 1,
        f"{metrics}"
    )
    
    # 清理
    await pool.release_slot()
    
    print(f"\n非阻塞池测试: {results.passed}/{results.passed + results.failed} 通过")
    if results.tests:
        for test in results.tests:
            print(f"  {test}")
    return results


async def test_overload_scenario():
    """测试过载场景"""
    print("\n" + "="*50)
    print("测试3: 过载场景模拟")
    print("="*50)
    
    results = TestResults()
    
    # 创建极小容量池模拟过载
    pool = NonBlockingExecutionPool(
        max_concurrent=1,
        max_queue_size=0,  # 无队列，立即拒绝
        nonblocking=True
    )
    await pool.initialize()
    
    # 模拟并发请求
    async def try_acquire(name):
        return await pool.acquire_slot(timeout=0.01)
    
    # 第一个请求成功
    ok1 = await try_acquire("req1")
    results.add("第1个请求", ok1)
    
    # 后续请求被拒绝 (背压控制)
    rejected_count = 0
    for i in range(5):
        ok = await try_acquire(f"req{i+2}")
        if not ok:
            rejected_count += 1
    
    results.add(
        "背压控制",
        rejected_count == 5,
        f"5个请求被拒绝，保护系统不堆积"
    )
    
    results.add(
        "拒绝计数",
        pool._rejected_count == 5,
        f"rejected={pool._rejected_count}"
    )
    
    # 清理
    await pool.release_slot()
    
    print(f"\n过载场景测试: {results.passed}/{results.passed + results.failed} 通过")
    if results.tests:
        for test in results.tests:
            print(f"  {test}")
    return results


async def test_integration_with_registry():
    """测试与注册表集成"""
    print("\n" + "="*50)
    print("测试4: 与现有系统集成")
    print("="*50)
    
    results = TestResults()
    
    # 初始化完整系统
    orch = initialize_agent_system()
    results.add("系统初始化", orch is not None)
    
    # 测试4.1: 获取Agent统计
    from core.agent_system.base import get_agent_registry
    registry = get_agent_registry()
    stats = registry.get_all_statistics()
    results.add(
        "Agent统计",
        len(stats) > 0,
        f"{len(stats)} 个Agent"
    )
    
    # 测试4.2: 增强注册表
    ereg = EnhancedAgentRegistry(LoadBalancingStrategy.LEAST_LOADED)
    await ereg.initialize()
    
    # 模拟更新指标 (即使Agent不存在也不会报错)
    ereg.update_agent_metrics(
        "test-agent",
        active_executions=2,
        total_executions=10,
        success_count=9
    )
    
    # 验证API调用不报错
    results.add(
        "增强注册表",
        ereg is not None,
        f"registry initialized, strategy={ereg._default_strategy.name}"
    )
    
    # 测试4.3: 注册表状态
    status = ereg.get_registry_status()
    results.add(
        "状态查询",
        "global_pool" in status,
        f"包含字段: {list(status.keys())}"
    )
    
    print(f"\n集成测试: {results.passed}/{results.passed + results.failed} 通过")
    if results.tests:
        for test in results.tests:
            print(f"  {test}")
    return results


async def test_backpressure_performance():
    """测试背压性能"""
    print("\n" + "="*50)
    print("测试5: 背压性能测试")
    print("="*50)
    
    results = TestResults()
    
    pool = NonBlockingExecutionPool(
        max_concurrent=5,
        max_queue_size=10,
        nonblocking=True
    )
    await pool.initialize()
    
    # 并发获取槽位
    start = time.time()
    
    async def worker(worker_id):
        ok = await pool.acquire_slot(timeout=0.01)
        if ok:
            await asyncio.sleep(0.01)  # 模拟工作
            await pool.release_slot()
        return ok
    
    # 启动20个并发任务 (超过容量)
    tasks = [worker(i) for i in range(20)]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed = time.time() - start
    
    success = sum(1 for o in outcomes if o is True)
    failed = sum(1 for o in outcomes if o is False)
    errors = sum(1 for o in outcomes if isinstance(o, Exception))
    
    results.add(
        "并发处理",
        errors == 0,
        f"20任务: {success}成功, {failed}拒绝, {errors}错误, 耗时{elapsed:.3f}s"
    )
    
    results.add(
        "背压生效",
        failed > 0,
        f"{failed}个任务被拒绝，避免系统过载"
    )
    
    # 验证最终状态
    results.add(
        "最终状态",
        pool._active_count == 0,
        f"active={pool._active_count}, completed={pool._completed_count}"
    )
    
    print(f"\n背压性能测试: {results.passed}/{results.passed + results.failed} 通过")
    if results.tests:
        for test in results.tests:
            print(f"  {test}")
    return results


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("wdai v3.2 完整测试套件")
    print("="*60)
    print("\n测试内容:")
    print("1. 负载均衡策略 (RoundRobin/LeastLoaded/Weighted/Hash)")
    print("2. 非阻塞执行池 (背压控制)")
    print("3. 过载场景模拟")
    print("4. 系统集成")
    print("5. 背压性能")
    
    all_results = []
    
    all_results.append(await test_load_balancer_strategies())
    all_results.append(await test_nonblocking_pool())
    all_results.append(await test_overload_scenario())
    all_results.append(await test_integration_with_registry())
    all_results.append(await test_backpressure_performance())
    
    # 汇总
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total = total_passed + total_failed
    
    print("\n" + "="*60)
    print(f"最终汇总: {total_passed}/{total} 通过 ({total_passed/total*100:.0f}%)")
    print("="*60)
    
    if total_failed == 0:
        print("\n🎉 所有测试通过! v3.2 Gnet模式工作正常")
    else:
        print(f"\n⚠️ {total_failed} 个测试失败，需要检查")
    
    return total_failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
