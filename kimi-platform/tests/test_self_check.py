"""
Test Self-Check System Integration
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/kimi-platform/src')

from utils.self_check import (
    PhysicalRealityChecker, ValidationChecker, 
    OverInferenceChecker, SelfCheckRunner, check_task
)
from agents.agent import create_agent, Task


def test_physical_reality_checker():
    """测试物理现实检查器"""
    print("\n" + "="*60)
    print("TEST 1: Physical Reality Checker")
    print("="*60)
    
    checker = PhysicalRealityChecker()
    
    # 测试1: 人类实时响应
    results = checker.check("让人类立即审核这个方案")
    assert len(results) > 0
    assert results[0].check_name == "human_response_time"
    print(f"✅ Human response check: {results[0].message}")
    
    # 测试2: 资源限制
    results = checker.check("处理所有文件")
    assert any(r.check_name == "resource_constraints" for r in results)
    print(f"✅ Resource check: detected")
    
    # 测试3: 绝对化词语
    results = checker.check("这总是最好的方案")
    assert any(r.check_name == "absolute_terms" for r in results)
    print(f"✅ Absolute terms check: detected")
    
    # 测试4: 通过
    results = checker.check("读取config.json文件")
    assert len(results) == 0
    print(f"✅ Normal task passed")
    
    return True


def test_validation_checker():
    """测试验证流程检查器"""
    print("\n" + "="*60)
    print("TEST 2: Validation Checker")
    print("="*60)
    
    checker = ValidationChecker()
    
    # 需要验证的任务
    assert checker.should_validate("设计一个新的架构") == True
    print(f"✅ Design task needs validation")
    
    # 不需要验证的任务
    assert checker.should_validate("读取文件") == False
    print(f"✅ Simple task no validation needed")
    
    # 检查清单
    checklist = checker.get_validation_checklist()
    assert len(checklist) == 5
    print(f"✅ Validation checklist: {len(checklist)} items")
    
    return True


def test_over_inference_checker():
    """测试过度推断检查器"""
    print("\n" + "="*60)
    print("TEST 3: Over Inference Checker")
    print("="*60)
    
    checker = OverInferenceChecker()
    
    # 测试1: 案例不足
    result = checker.check("这是最佳实践", history_count=1)
    assert result is not None
    print(f"✅ Low history count detected: {result.message}")
    
    # 测试2: 个人经验
    result = checker.check("我觉得这个方案最好")
    assert result is not None
    print(f"✅ Personal experience detected: {result.message}")
    
    # 测试3: 足够案例
    result = checker.check("这是最佳实践", history_count=5)
    assert result is None
    print(f"✅ Sufficient history passed")
    
    return True


def test_self_check_runner():
    """测试自检运行器"""
    print("\n" + "="*60)
    print("TEST 4: Self-Check Runner")
    print("="*60)
    
    runner = SelfCheckRunner()
    
    # 有问题任务
    should_proceed, report = runner.run_all_checks("让人类立即审核", history_count=0)
    assert should_proceed == True  # 只是警告，不阻止
    assert "⚠️" in report or "物理现实检查" in report
    print(f"✅ Problematic task flagged")
    
    # 正常任务
    should_proceed, report = runner.run_all_checks("读取文件", history_count=10)
    assert should_proceed == True
    assert "✅" in report
    print(f"✅ Normal task passed")
    
    return True


def test_agent_integration():
    """测试Agent集成"""
    print("\n" + "="*60)
    print("TEST 5: Agent Integration")
    print("="*60)
    
    agent = create_agent("test", "test")
    
    # 有问题任务 - 应该触发警告
    print("\n[Testing problematic task...]")
    task1 = Task(
        task_id="t1",
        task_type="test",
        description="让人类立即审核所有设计方案",
        input_data="test"
    )
    result1 = agent.execute(task1)
    assert "error" not in result1  # 只是警告，不阻止
    print(f"✅ Warning shown but execution continued")
    
    # 正常任务
    print("\n[Testing normal task...]")
    agent2 = create_agent("test2", "test")  # 新agent，避免历史影响
    task2 = Task(
        task_id="t2",
        task_type="test",
        description="读取配置文件",
        input_data="test"
    )
    result2 = agent2.execute(task2)
    assert result2 is not None
    print(f"✅ Normal task executed")
    
    return True


def test_quick_check():
    """测试快速检查函数"""
    print("\n" + "="*60)
    print("TEST 6: Quick Check Function")
    print("="*60)
    
    # 快速检查
    should_proceed, report = check_task("设计新架构方案", history_count=0)
    print(f"Check result: {should_proceed}")
    print(f"Report preview: {report[:100]}...")
    
    return True


def run_tests():
    """运行所有测试"""
    print("\n" + "🔍" * 30)
    print("SELF-CHECK SYSTEM TESTS")
    print("🔍" * 30)
    
    tests = [
        test_physical_reality_checker,
        test_validation_checker,
        test_over_inference_checker,
        test_self_check_runner,
        test_agent_integration,
        test_quick_check,
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
        print("\n🎉 Self-check system integrated!")
        print("\nNow every Agent execution automatically runs:")
        print("  • Physical reality checks")
        print("  • Validation reminders")
        print("  • Over-inference warnings")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
