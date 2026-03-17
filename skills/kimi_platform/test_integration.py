"""
Test OpenClaw Integration
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills')
sys.path.insert(0, '/root/.openclaw/workspace/kimi-platform/src')

def test_import():
    """测试导入"""
    print("\n" + "="*60)
    print("TEST 1: Import Test")
    print("="*60)
    
    # 测试核心导入
    from kimi_platform import create_workflow, create_agent, create_memory_manager
    print("✅ Core imports successful")
    
    # 测试集成导入
    from kimi_platform.integration import (
        quick_research, quick_calculate,
        quick_workflow, quick_remember, quick_recall
    )
    print("✅ Integration imports successful")
    
    return True


def test_quick_functions():
    """测试快速函数"""
    print("\n" + "="*60)
    print("TEST 2: Quick Functions Test")
    print("="*60)
    
    from kimi_platform.integration import (
        quick_calculate, quick_research, execute
    )
    
    # 测试计算
    result = quick_calculate("10 * 5")
    assert result == "50"
    print(f"✅ Calculate: 10 * 5 = {result}")
    
    # 测试统一执行接口
    result = execute("calculate", expression="20 + 30")
    print(f"✅ Execute: 20 + 30 = {result}")
    
    return True


def test_full_api():
    """测试完整API"""
    print("\n" + "="*60)
    print("TEST 3: Full API Test")
    print("="*60)
    
    from kimi_platform import (
        create_workflow, create_agent, get_all_tools
    )
    from engine.workflow import StartNode, EndNode, TaskNode, run_workflow
    
    # 创建工作流
    dag = create_workflow("test_api")
    dag.add_node(StartNode("start"))
    dag.add_node(TaskNode("task"))
    dag.add_node(EndNode("end"))
    dag.add_edge("start", "task")
    dag.add_edge("task", "end")
    
    result = run_workflow(dag)
    print(f"✅ Workflow executed: {result['status']}")
    
    # 创建Agent
    agent = create_agent("test_agent", "test")
    print(f"✅ Agent created: {agent.agent_id}")
    
    # 获取工具
    tools = get_all_tools()
    print(f"✅ Tools available: {len(tools)}")
    
    return True


def run_tests():
    """运行所有测试"""
    print("\n" + "🔗" * 30)
    print("OPENCLAW INTEGRATION TESTS")
    print("🔗" * 30)
    
    tests = [
        test_import,
        test_quick_functions,
        test_full_api,
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
        print("\n🎉 OpenClaw Integration READY!")
        print("\nUsage:")
        print("  from skills.kimi_platform import create_workflow, create_agent")
        print("  from kimi_platform.integration import quick_research, quick_calculate")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
