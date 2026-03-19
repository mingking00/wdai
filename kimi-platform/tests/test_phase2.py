"""
Phase 2 Test - Agent系统
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/kimi-platform/src')

from agents.agent import (
    Agent, SimpleAgent, AgentOrchestrator, 
    Task, ActionPlan, create_agent, create_orchestrator
)
from tools.builtin import get_default_tools


def test_1_agent_creation():
    """测试1: Agent创建"""
    print("\n" + "="*60)
    print("TEST 1: Agent创建")
    print("="*60)
    
    agent = create_agent("researcher", "research", "Research specialist")
    
    # 注册工具
    tools = get_default_tools()
    for tool in tools:
        agent.register_tool(tool)
    
    print(f"Created: {agent}")
    print(f"Tools: {len(agent.tools)}")
    
    assert agent.agent_id == "researcher"
    assert agent.role == "research"
    assert len(agent.tools) == 6
    
    print("✅ Test 1 PASSED")
    return True


def test_2_agent_execution():
    """测试2: Agent执行"""
    print("\n" + "="*60)
    print("TEST 2: Agent执行")
    print("="*60)
    
    agent = create_agent("calculator", "math", "Math specialist")
    agent.register_tool([t for t in get_default_tools() if t.name == "calculator"][0])
    
    # 创建任务
    task = Task(
        task_id="t1",
        task_type="calculator",
        description="Calculate 2+2",
        input_data="2+2",
        context={"expression": "2+2"}  # 使用expression参数
    )
    
    # 执行
    result = agent.execute(task)
    
    print(f"Result: {result}")
    assert task.status == "completed"
    assert result == "4"
    
    print("✅ Test 2 PASSED")
    return True


def test_3_orchestrator_dispatch():
    """测试3: 编排器任务分派"""
    print("\n" + "="*60)
    print("TEST 3: 编排器任务分派")
    print("="*60)
    
    orch = create_orchestrator()
    
    # 创建Agent
    research_agent = create_agent("researcher", "research")
    code_agent = create_agent("coder", "code")
    
    research_agent.register_tool([t for t in get_default_tools() if t.name == "web_search"][0])
    code_agent.register_tool([t for t in get_default_tools() if t.name == "code_executor"][0])
    
    orch.register_agent(research_agent)
    orch.register_agent(code_agent)
    
    # 创建任务
    task = orch.create_task("research", "Search for AI news", "AI trends")
    
    # 分派
    agent_id, result = orch.dispatch_task(task)
    
    print(f"Dispatched to: {agent_id}")
    print(f"Result: {result}")
    
    assert agent_id == "researcher"  # 应该匹配research
    
    print("✅ Test 3 PASSED")
    return True


def test_4_multi_agent_workflow():
    """测试4: 多Agent工作流"""
    print("\n" + "="*60)
    print("TEST 4: 多Agent工作流")
    print("="*60)
    
    orch = create_orchestrator()
    
    # 创建Agent
    agent1 = create_agent("agent1", "step1")
    agent2 = create_agent("agent2", "step2")
    
    orch.register_agent(agent1)
    orch.register_agent(agent2)
    
    # 定义工作流
    task1 = orch.create_task("step1", "First step", "data1")
    task2 = orch.create_task("step2", "Second step", "data2")
    
    workflow = [
        {"agent": "agent1", "task": task1},
        {"agent": "agent2", "task": task2, "depends_on": "agent1"},
    ]
    
    # 执行
    results = orch.coordinate(workflow)
    
    print(f"Results: {results}")
    
    assert "agent1" in results
    assert "agent2" in results
    
    print("✅ Test 4 PASSED")
    return True


def test_5_agent_messaging():
    """测试5: Agent消息传递"""
    print("\n" + "="*60)
    print("TEST 5: Agent消息传递")
    print("="*60)
    
    orch = create_orchestrator()
    
    agent1 = create_agent("sender", "sender")
    agent2 = create_agent("receiver", "receiver")
    
    orch.register_agent(agent1)
    orch.register_agent(agent2)
    
    # 发送消息
    orch.send_message("sender", "receiver", "Hello from sender!")
    
    print(f"Receiver inbox: {len(agent2.inbox)} messages")
    assert len(agent2.inbox) == 1
    assert agent2.inbox[0].content == "Hello from sender!"
    
    print("✅ Test 5 PASSED")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("KIMI PLATFORM - PHASE 2 TESTS")
    print("🧪" * 30)
    
    tests = [
        test_1_agent_creation,
        test_2_agent_execution,
        test_3_orchestrator_dispatch,
        test_4_multi_agent_workflow,
        test_5_agent_messaging,
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
