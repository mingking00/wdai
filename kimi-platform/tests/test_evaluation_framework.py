"""
Test Evaluation Framework (Learning Round 16)
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/kimi-platform/src')

from utils.evaluation import (
    EvaluationFramework, TaskCompletionMetric, ToolCorrectnessMetric,
    LatencyMetric, TokenEfficiencyMetric
)


def test_task_completion_metric():
    """测试任务完成度指标"""
    print("\n" + "="*60)
    print("TEST 1: Task Completion Metric")
    print("="*60)
    
    metric = TaskCompletionMetric(threshold=0.8)
    
    # 测试成功
    result1 = metric.evaluate("task1", "completed successfully")
    assert result1.score == 1.0
    assert result1.passed == True
    print("✅ Successful completion: score=1.0")
    
    # 测试空输出
    result2 = metric.evaluate("task2", "")
    assert result2.score == 0.0
    assert result2.passed == False
    print("✅ Empty output: score=0.0")
    
    # 测试错误
    result3 = metric.evaluate("task3", {"error": "Failed"})
    assert result3.score == 0.0
    print("✅ Error output: score=0.0")
    
    return True


def test_tool_correctness_metric():
    """测试工具正确性指标"""
    print("\n" + "="*60)
    print("TEST 2: Tool Correctness Metric")
    print("="*60)
    
    metric = ToolCorrectnessMetric(threshold=0.8)
    
    # 测试完全匹配
    context1 = {
        "expected_tool": "calculator",
        "actual_tool": "calculator",
        "expected_params": {"a": 1, "b": 2},
        "actual_params": {"a": 1, "b": 2}
    }
    result1 = metric.evaluate("task1", "output", context1)
    assert result1.score == 1.0
    print("✅ Perfect match: score=1.0")
    
    # 测试工具不匹配
    context2 = {
        "expected_tool": "calculator",
        "actual_tool": "web_search",
        "expected_params": {},
        "actual_params": {}
    }
    result2 = metric.evaluate("task2", "output", context2)
    assert result2.score == 0.4  # 工具不匹配得0分，但参数默认1.0，所以0.0 + 0.4*1.0 = 0.4
    print("✅ Tool mismatch: score=0.4")
    
    # 测试部分匹配
    context3 = {
        "expected_tool": "calculator",
        "actual_tool": "calculator",
        "expected_params": {"a": 1, "b": 2},
        "actual_params": {"a": 1, "b": 3}  # b不匹配
    }
    result3 = metric.evaluate("task3", "output", context3)
    assert 0.6 < result3.score < 1.0
    print(f"✅ Partial match: score={result3.score:.2f}")
    
    return True


def test_latency_metric():
    """测试延迟指标"""
    print("\n" + "="*60)
    print("TEST 3: Latency Metric")
    print("="*60)
    
    metric = LatencyMetric(max_latency_ms=1000)
    
    # 测试正常延迟
    result1 = metric.evaluate("task1", "output", {"latency_ms": 500})
    assert result1.score == 1.0
    print("✅ Normal latency (500ms): score=1.0")
    
    # 测试边界延迟
    result2 = metric.evaluate("task2", "output", {"latency_ms": 1000})
    assert result2.score == 1.0
    print("✅ Boundary latency (1000ms): score=1.0")
    
    # 测试超标延迟
    result3 = metric.evaluate("task3", "output", {"latency_ms": 1500})
    assert result3.score < 1.0
    print(f"✅ High latency (1500ms): score={result3.score:.2f}")
    
    return True


def test_token_efficiency_metric():
    """测试Token效率指标"""
    print("\n" + "="*60)
    print("TEST 4: Token Efficiency Metric")
    print("="*60)
    
    metric = TokenEfficiencyMetric(max_tokens=1000)
    
    # 测试高效
    result1 = metric.evaluate("task1", "output", {"tokens_used": 500})
    assert result1.score == 1.0
    print("✅ Efficient (500 tokens): score=1.0")
    
    # 测试超标
    result2 = metric.evaluate("task2", "output", {"tokens_used": 1500})
    assert result2.score < 1.0
    print(f"✅ Inefficient (1500 tokens): score={result2.score:.2f}")
    
    return True


def test_full_framework():
    """测试完整框架"""
    print("\n" + "="*60)
    print("TEST 5: Full Evaluation Framework")
    print("="*60)
    
    framework = EvaluationFramework()
    framework.add_metric(TaskCompletionMetric())
    framework.add_metric(ToolCorrectnessMetric())
    framework.add_metric(LatencyMetric(max_latency_ms=1000))
    framework.add_metric(TokenEfficiencyMetric(max_tokens=2000))
    
    # 模拟一个Agent执行
    task = {"type": "calculator", "expression": "2+2"}
    output = "4"
    context = {
        "latency_ms": 500,
        "tokens_used": 100,
        "expected_tool": "calculator",
        "actual_tool": "calculator",
        "expected_params": {"expression": "2+2"},
        "actual_params": {"expression": "2+2"}
    }
    
    result = framework.evaluate(task, output, context)
    
    print(f"\nOverall Score: {result['overall_score']:.2f}")
    print(f"Status: {'✅ PASSED' if result['passed'] else '❌ FAILED'}")
    print("\nCategory Scores:")
    for cat, score in result['category_scores'].items():
        print(f"  • {cat}: {score:.2f}")
    
    assert result['overall_score'] > 0.8
    assert result['passed'] == True
    
    # 打印详细报告
    report = framework.print_report(result)
    print("\n" + report)
    
    return True


def test_default_framework():
    """测试默认框架"""
    print("\n" + "="*60)
    print("TEST 6: Default Framework")
    print("="*60)
    
    framework = EvaluationFramework.get_default_framework()
    
    assert len(framework.metrics) == 4
    print(f"✅ Default framework has {len(framework.metrics)} metrics")
    
    return True


def run_tests():
    """运行所有测试"""
    print("\n" + "📊" * 30)
    print("EVALUATION FRAMEWORK TESTS")
    print("📊" * 30)
    
    tests = [
        test_task_completion_metric,
        test_tool_correctness_metric,
        test_latency_metric,
        test_token_efficiency_metric,
        test_full_framework,
        test_default_framework,
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
    
    if failed == 0:
        print("\n🎉 Evaluation Framework Implemented!")
        print("\nFeatures:")
        print("  • Task Completion metric")
        print("  • Tool Correctness metric")
        print("  • Latency metric")
        print("  • Token Efficiency metric")
        print("  • Category-based scoring")
        print("  • Comprehensive reporting")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
