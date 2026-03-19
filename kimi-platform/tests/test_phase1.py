"""
Phase 1 Test - 验证核心引擎
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/kimi-platform/src')

from engine.workflow import (
    DAG, WorkflowEngine, StartNode, EndNode, TaskNode, ConditionNode,
    create_workflow, run_workflow, Context
)


def test_1_simple_linear_workflow():
    """测试1: 简单线性工作流"""
    print("\n" + "="*60)
    print("TEST 1: 简单线性工作流")
    print("="*60)
    
    # 创建DAG: Start -> Task1 -> Task2 -> End
    dag = create_workflow("test_linear")
    
    # 添加节点
    dag.add_node(StartNode("start"))
    dag.add_node(TaskNode("task1", {"name": "Data Preparation"}))
    dag.add_node(TaskNode("task2", {"name": "Data Processing"}))
    dag.add_node(EndNode("end"))
    
    # 添加边
    dag.add_edge("start", "task1")
    dag.add_edge("task1", "task2")
    dag.add_edge("task2", "end")
    
    # 设置任务处理器
    dag.nodes["task1"].set_handler(
        lambda ctx, cfg: f"Prepared: {cfg.get('name')}"
    )
    dag.nodes["task2"].set_handler(
        lambda ctx, cfg: f"Processed: {cfg.get('name')}"
    )
    
    # 执行
    result = run_workflow(dag, {"input": "test_data"})
    
    print(f"\n[Result] {result['status']}")
    print(f"[Executed] {result['executed_nodes']}")
    
    assert result['status'] == 'completed'
    assert len(result['executed_nodes']) == 4
    print("✅ Test 1 PASSED")
    return True


def test_2_branching_workflow():
    """测试2: 分支工作流"""
    print("\n" + "="*60)
    print("TEST 2: 分支工作流 (条件判断)")
    print("="*60)
    
    dag = create_workflow("test_branching")
    
    # 添加节点
    dag.add_node(StartNode("start"))
    dag.add_node(TaskNode("input_task", {"value": 75}))
    dag.add_node(ConditionNode("check_score"))
    dag.add_node(TaskNode("pass_task", {"msg": "Passed!"}))
    dag.add_node(TaskNode("fail_task", {"msg": "Failed!"}))
    dag.add_node(EndNode("end"))
    
    # 添加边
    dag.add_edge("start", "input_task")
    dag.add_edge("input_task", "check_score")
    dag.add_edge("check_score", "pass_task", label="true")
    dag.add_edge("check_score", "fail_task", label="false")
    dag.add_edge("pass_task", "end")
    dag.add_edge("fail_task", "end")
    
    # 设置条件判断 (score >= 60 通过)
    dag.nodes["check_score"].set_condition(
        lambda ctx, cfg: ctx.get("score", 0) >= 60
    )
    
    dag.nodes["input_task"].set_handler(
        lambda ctx, cfg: ctx.set("score", cfg.get("value", 0))
    )
    dag.nodes["pass_task"].set_handler(
        lambda ctx, cfg: f"✅ {cfg.get('msg')} Score: {ctx.get('score')}"
    )
    dag.nodes["fail_task"].set_handler(
        lambda ctx, cfg: f"❌ {cfg.get('msg')} Score: {ctx.get('score')}"
    )
    
    # 执行
    result = run_workflow(dag)
    
    print(f"\n[Result] {result['status']}")
    print(f"[Context] Score: {result['context'].get('score')}")
    
    assert result['status'] == 'completed'
    assert result['context'].get('score') == 75
    print("✅ Test 2 PASSED")
    return True


def test_3_parallel_workflow():
    """测试3: 并行工作流"""
    print("\n" + "="*60)
    print("TEST 3: 并行工作流")
    print("="*60)
    
    dag = create_workflow("test_parallel")
    
    # 创建并行结构: Start -> TaskA & TaskB -> Merge -> End
    dag.add_node(StartNode("start"))
    dag.add_node(TaskNode("task_a", {"name": "Task A"}))
    dag.add_node(TaskNode("task_b", {"name": "Task B"}))
    dag.add_node(TaskNode("merge", {"name": "Merge Results"}))
    dag.add_node(EndNode("end"))
    
    # 添加边 (并行)
    dag.add_edge("start", "task_a")
    dag.add_edge("start", "task_b")
    dag.add_edge("task_a", "merge")
    dag.add_edge("task_b", "merge")
    dag.add_edge("merge", "end")
    
    # 设置处理器
    dag.nodes["task_a"].set_handler(
        lambda ctx, cfg: ctx.set("result_a", "A_done")
    )
    dag.nodes["task_b"].set_handler(
        lambda ctx, cfg: ctx.set("result_b", "B_done")
    )
    dag.nodes["merge"].set_handler(
        lambda ctx, cfg: f"Merged: {ctx.get('result_a')} + {ctx.get('result_b')}"
    )
    
    # 执行
    result = run_workflow(dag)
    
    print(f"\n[Result] {result['status']}")
    print(f"[Context] {result['context']}")
    
    assert result['status'] == 'completed'
    assert result['context'].get('result_a') == 'A_done'
    assert result['context'].get('result_b') == 'B_done'
    print("✅ Test 3 PASSED")
    return True


def test_4_dag_serialization():
    """测试4: DAG序列化/反序列化"""
    print("\n" + "="*60)
    print("TEST 4: DAG序列化")
    print("="*60)
    
    # 创建工作流
    dag = create_workflow("test_serialize")
    dag.add_node(StartNode("start"))
    dag.add_node(TaskNode("task1"))
    dag.add_node(EndNode("end"))
    dag.add_edge("start", "task1")
    dag.add_edge("task1", "end")
    
    # 序列化
    data = dag.to_dict()
    print(f"\n[Serialized] {data}")
    
    # 反序列化
    dag2 = DAG.from_dict(data)
    data2 = dag2.to_dict()
    
    assert data['workflow_id'] == data2['workflow_id']
    assert len(data['nodes']) == len(data2['nodes'])
    assert len(data['edges']) == len(data2['edges'])
    
    print("✅ Test 4 PASSED")
    return True


def test_5_error_handling():
    """测试5: 错误处理"""
    print("\n" + "="*60)
    print("TEST 5: 错误处理")
    print("="*60)
    
    dag = create_workflow("test_error")
    dag.add_node(StartNode("start"))
    dag.add_node(TaskNode("fail_task"))
    dag.add_node(EndNode("end"))
    dag.add_edge("start", "fail_task")
    dag.add_edge("fail_task", "end")
    
    # 设置会抛出异常的处理器
    dag.nodes["fail_task"].set_handler(
        lambda ctx, cfg: 1/0  # 除以零错误
    )
    
    # 执行
    result = run_workflow(dag)
    
    print(f"\n[Result] {result['status']}")
    # 应该执行了start和fail_task（失败）
    assert "start" in result['executed_nodes']
    assert "fail_task" in result['executed_nodes']
    assert "end" not in result['executed_nodes']  # 不应该执行到end
    
    print("✅ Test 5 PASSED")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("KIMI PLATFORM - PHASE 1 TESTS")
    print("🧪" * 30)
    
    tests = [
        test_1_simple_linear_workflow,
        test_2_branching_workflow,
        test_3_parallel_workflow,
        test_4_dag_serialization,
        test_5_error_handling,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
