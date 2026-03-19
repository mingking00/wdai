"""
Test Multi-Level Reasoning + Verifier Agent
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/kimi-platform/src')

from agents.agent import (
    create_agent, create_verifier_agent, Task
)


def test_reasoning_depths():
    """测试多档推理深度"""
    print("\n" + "="*60)
    print("TEST: Multi-Level Reasoning Depths")
    print("="*60)
    
    task = Task(
        task_id="t1",
        task_type="test",
        description="Test task",
        input_data="hello"
    )
    
    # NoThink
    agent1 = create_agent("a1", "test").set_reasoning_depth("NoThink")
    plan1 = agent1.think(task)
    assert plan1.reasoning == "NoThink: direct response"
    print("✅ NoThink: direct response")
    
    # FastThink (default)
    agent2 = create_agent("a2", "test")  # default is FastThink
    plan2 = agent2.think(task)
    assert "NoThink" not in plan2.reasoning
    print("✅ FastThink: normal reasoning")
    
    # CoreThink
    agent3 = create_agent("a3", "test").set_reasoning_depth("CoreThink")
    plan3 = agent3.think(task)
    assert "[validated]" in plan3.reasoning
    print("✅ CoreThink: with validation")
    
    # DeepThink
    agent4 = create_agent("a4", "test").set_reasoning_depth("DeepThink").set_self_consistency(3)
    plan4 = agent4.think(task)
    assert "DeepThink" in plan4.reasoning and "3 samples" in plan4.reasoning
    print("✅ DeepThink: 3 samples")
    
    return True


def test_verifier_agent():
    """测试Verifier Agent"""
    print("\n" + "="*60)
    print("TEST: Verifier Agent")
    print("="*60)
    
    verifier = create_verifier_agent()
    
    task = Task(
        task_id="t1",
        task_type="test",
        description="Test",
        input_data="data"
    )
    
    # 测试通过情况
    result1 = verifier.verify(task, "Valid output")
    assert result1["passed"] == True
    assert result1["score"] == 1.0
    print("✅ Valid output: passed")
    
    # 测试空输出
    result2 = verifier.verify(task, "")
    assert result2["passed"] == False
    assert len(result2["issues"]) > 0
    print("✅ Empty output: flagged")
    
    # 测试绝对化词语
    result3 = verifier.verify(task, "This is always the best solution")
    assert any("always" in issue for issue in result3["issues"])
    print("✅ Absolute terms: flagged")
    
    # 测试错误输出
    result4 = verifier.verify(task, {"error": "Something failed"})
    assert result4["passed"] == False
    print("✅ Error output: flagged")
    
    return True


def test_integration():
    """测试集成使用"""
    print("\n" + "="*60)
    print("TEST: Integration - Agent + Verifier")
    print("="*60)
    
    from tools.builtin import get_default_tools
    
    # 创建工作Agent（DeepThink模式）
    worker = create_agent("worker", "processor").set_reasoning_depth("DeepThink").set_self_consistency(3)
    
    # 注册工具
    for tool in get_default_tools():
        worker.register_tool(tool)
    
    # 创建Verifier
    verifier = create_verifier_agent()
    
    # 任务
    task = Task(
        task_id="task1",
        task_type="calculator",
        description="Calculate something",
        input_data="",
        context={"expression": "100 + 200"}
    )
    
    # 执行
    result = worker.execute(task)
    
    # 验证
    verification = verifier.verify(task, result)
    
    print(f"Worker result: {result}")
    print(f"Verification: passed={verification['passed']}, score={verification['score']:.2f}")
    
    return True


def run_tests():
    """运行所有测试"""
    print("\n" + "🧠" * 30)
    print("MULTI-LEVEL REASONING + VERIFIER TESTS")
    print("🧠" * 30)
    
    tests = [
        test_reasoning_depths,
        test_verifier_agent,
        test_integration,
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
        print("\n🎉 Learning Round 15 Internalized!")
        print("\nNew capabilities:")
        print("  • Multi-level reasoning: NoThink/FastThink/CoreThink/DeepThink")
        print("  • Self-Consistency: Multiple samples voting")
        print("  • Verifier Agent: Built-in output validation")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
