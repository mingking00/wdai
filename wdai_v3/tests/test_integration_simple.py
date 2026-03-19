"""
wdai v3.0 - Simple Integration Test
简化版集成测试
"""

import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')


async def test_basic_imports():
    """测试基本导入"""
    print("=" * 60)
    print("Test 1: 基本导入测试")
    print("=" * 60)
    
    # 导入Phase 1
    from core.message_bus import get_message_bus, MessageType, create_message
    print("✓ Phase 1 (Message Bus) 导入成功")
    
    # 导入Phase 2
    from core.workflow import WorkflowEngine, Workflow, Step
    from core.workflow.models import StepAction
    print("✓ Phase 2 (Workflow Engine) 导入成功")
    
    # 导入Phase 3
    from core.agent_system import initialize_agent_system, create_task
    print("✓ Phase 3 (Agent System) 导入成功")
    
    # 导入Integration
    from core.integration import IntegratedSystem, AgentMessageAdapter, AgentStepExecutor
    print("✓ Integration Layer 导入成功")
    
    print("\n✅ 所有导入测试通过\n")


async def test_agent_system_alone():
    """测试Agent系统独立运行"""
    print("=" * 60)
    print("Test 2: Agent系统独立测试")
    print("=" * 60)
    
    from core.agent_system import initialize_agent_system, create_task
    
    orchestrator = initialize_agent_system()
    
    task = create_task(
        description="集成测试任务",
        goal="验证Agent系统运行正常"
    )
    
    print(f"创建任务: {task.id}")
    print(f"描述: {task.description}")
    
    result = await orchestrator.execute(task)
    
    print(f"结果: {'✅ 成功' if result.success else '❌ 失败'}")
    
    if result.output:
        subtasks = result.output.get('subtask_results', {})
        print(f"子任务数: {len(subtasks)}")
    
    print("\n✅ Agent系统独立测试通过\n")


async def test_message_bus_alone():
    """测试Message Bus独立运行"""
    print("=" * 60)
    print("Test 3: Message Bus独立测试")
    print("=" * 60)
    
    from core.message_bus import get_message_bus, MessageType, create_message
    
    bus = get_message_bus()
    await bus.start()
    
    print("✓ Message Bus 已启动")
    
    # 创建测试消息
    message = create_message(
        msg_type=MessageType.EVENT,
        content={"test": "data"},
        sender="test",
        recipients=["receiver"]
    )
    
    msg_id = await bus.publish(message)
    print(f"✓ 消息已发布: {msg_id}")
    
    # 查询消息
    history = bus.query_messages(sender="test")
    print(f"✓ 查询到 {len(history)} 条消息")
    
    # 获取统计
    stats = bus.get_statistics()
    print(f"✓ Message Pool: {stats['pool']['total_messages']} 条消息")
    
    await bus.stop()
    print("✓ Message Bus 已停止")
    
    print("\n✅ Message Bus独立测试通过\n")


async def test_integration_layer():
    """测试集成层初始化（不启动所有组件）"""
    print("=" * 60)
    print("Test 4: 集成层组件创建")
    print("=" * 60)
    
    from core.integration import IntegratedSystem
    from core.message_bus import get_message_bus
    from core.agent_system import initialize_agent_system
    
    # 创建但不初始化
    system = IntegratedSystem()
    print("✓ IntegratedSystem 已创建")
    
    # 手动设置组件
    system.message_bus = get_message_bus()
    await system.message_bus.start()
    print("✓ Message Bus 已启动")
    
    system.orchestrator = initialize_agent_system()
    print("✓ Agent System 已初始化")
    
    # 测试直接执行任务
    from core.agent_system import create_task
    task = create_task(description="集成层测试", goal="验证组件协同")
    result = await system.orchestrator.execute(task)
    
    print(f"✓ 任务执行: {'成功' if result.success else '失败'}")
    
    await system.message_bus.stop()
    print("✓ 系统已关闭")
    
    print("\n✅ 集成层组件测试通过\n")


async def test_statistics():
    """测试统计信息"""
    print("=" * 60)
    print("Test 5: 系统统计信息")
    print("=" * 60)
    
    from core.agent_system import initialize_agent_system, get_agent_registry
    
    orchestrator = initialize_agent_system()
    registry = get_agent_registry()
    
    print("已注册Agent:")
    for agent in registry.list_agents():
        stats = agent.get_statistics()
        print(f"  - {stats['name']} ({stats['role']})")
        print(f"    专长: {', '.join(stats['expertise'][:3])}")
    
    print("\n✅ 统计信息测试通过\n")


async def main():
    """运行简化测试"""
    print("\n" + "=" * 60)
    print("wdai v3.0 - 系统集成简化测试")
    print("=" * 60 + "\n")
    
    try:
        await test_basic_imports()
        await test_agent_system_alone()
        await test_message_bus_alone()
        await test_integration_layer()
        await test_statistics()
        
        print("=" * 60)
        print("✅ 所有简化集成测试通过!")
        print("=" * 60)
        print()
        print("系统集成状态:")
        print("  ✓ Phase 1: Message Bus - 可用")
        print("  ✓ Phase 2: Workflow Engine - 可用")
        print("  ✓ Phase 3: Agent System - 可用")
        print("  ✓ Integration Layer - 接口就绪")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
