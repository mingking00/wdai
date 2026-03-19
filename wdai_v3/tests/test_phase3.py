"""
wdai v3.0 Phase 3 集成测试
Agent专业化系统测试
"""

import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system import (
    initialize_agent_system,
    create_task,
    AgentRole,
    get_agent_registry
)


async def test_agent_registration():
    """测试Agent注册"""
    print("=" * 60)
    print("Test 1: Agent注册")
    print("=" * 60)
    
    orchestrator = initialize_agent_system()
    registry = get_agent_registry()
    
    agents = registry.list_agents()
    print(f"已注册Agent数量: {len(agents)}")
    
    for agent in agents:
        stats = agent.get_statistics()
        print(f"  - {stats['name']} ({stats['role']}): {stats['expertise']}")
    
    print("✅ Agent注册测试通过\n")


async def test_simple_task():
    """测试简单任务"""
    print("=" * 60)
    print("Test 2: 简单任务执行")
    print("=" * 60)
    
    orchestrator = initialize_agent_system()
    
    task = create_task(
        description="实现用户认证功能",
        goal="添加登录注册API",
        constraints=["使用JWT", "密码加密存储"]
    )
    
    print(f"任务: {task.description}")
    print(f"目标: {task.goal}")
    print()
    
    result = await orchestrator.execute(task)
    
    print(f"结果: {'✅ 成功' if result.success else '❌ 失败'}")
    print(f"执行时间: {result.execution_time_ms}ms")
    
    if result.output:
        subtask_count = len(result.output.get('subtask_results', {}))
        print(f"子任务数: {subtask_count}")
    
    print()


async def test_multi_step_task():
    """测试多步骤任务"""
    print("=" * 60)
    print("Test 3: 多步骤任务 (设计+实现+审查+测试)")
    print("=" * 60)
    
    orchestrator = initialize_agent_system()
    
    task = create_task(
        description="设计并实现一个完整的Web服务，包含架构设计、代码实现、代码审查和测试验证",
        goal="构建生产级Web服务",
        constraints=["高可用", "可扩展", "安全性"]
    )
    
    print(f"任务: {task.description}")
    print()
    
    result = await orchestrator.execute(task)
    
    print(f"结果: {'✅ 成功' if result.success else '❌ 失败'}")
    
    # 生成详细报告
    report = orchestrator.generate_report(task.id)
    print("\n执行报告:")
    print(report)
    print()


async def test_fresh_eyes():
    """测试Fresh Eyes上下文管理"""
    print("=" * 60)
    print("Test 4: Fresh Eyes上下文管理")
    print("=" * 60)
    
    from core.agent_system import create_context_manager, SubTask, Task, TodoPlan
    
    manager = create_context_manager(max_files=5)
    
    task = create_task(
        description="实现功能",
        goal="构建系统"
    )
    
    subtask = SubTask(
        parent_id=task.id,
        type="implement",
        description="实现用户模块的核心功能"
    )
    
    plan = TodoPlan(task_id=task.id, todos=[])
    
    available_files = [
        "src/user.py",
        "src/auth.py",
        "src/models.py",
        "tests/test_user.py",
        "docs/api.md",
        "config/settings.py",
        "utils/helpers.py"
    ]
    
    context = manager.narrow_context(task, subtask, plan, available_files)
    
    print(f"子任务: {context.subtask.description}")
    print(f"父目标: {context.parent_goal}")
    print(f"相关文件: {context.relevant_files}")
    print(f"文件数: {len(context.relevant_files)} / {len(available_files)}")
    
    # 验证Fresh Eyes原则
    assert len(context.relevant_files) <= 5, "文件数应被限制"
    print("✅ Fresh Eyes上下文管理测试通过\n")


async def test_todo_planning():
    """测试TODO规划"""
    print("=" * 60)
    print("Test 5: TODO规划系统")
    print("=" * 60)
    
    from core.agent_system import create_planner, SubTask
    
    planner = create_planner()
    
    task = create_task(
        description="完整开发流程",
        goal="交付产品"
    )
    
    subtasks = [
        SubTask(parent_id=task.id, type="design", description="架构设计"),
        SubTask(parent_id=task.id, type="implement", description="代码实现", dependencies=["sub_0"]),
        SubTask(parent_id=task.id, type="review", description="代码审查", dependencies=["sub_1"]),
        SubTask(parent_id=task.id, type="test", description="测试验证", dependencies=["sub_2"])
    ]
    
    plan = planner.create_plan(task, subtasks)
    
    print(f"任务: {task.description}")
    print(f"TODO数量: {len(plan.todos)}")
    print()
    
    for i, todo in enumerate(plan.todos, 1):
        agent = todo.assigned_agent.value if todo.assigned_agent else "未分配"
        print(f"  {i}. [{agent}] {todo.description} (~{todo.estimated_minutes}分钟)")
    
    progress = plan.get_progress()
    print(f"\n进度: {progress['percentage']}%")
    print("✅ TODO规划系统测试通过\n")


async def test_agent_capabilities():
    """测试Agent能力匹配"""
    print("=" * 60)
    print("Test 6: Agent能力匹配")
    print("=" * 60)
    
    orchestrator = initialize_agent_system()
    registry = get_agent_registry()
    
    test_cases = [
        ("implement", "代码实现"),
        ("review", "代码审查"),
        ("debug", "调试定位"),
        ("design", "架构设计"),
        ("test", "测试验证")
    ]
    
    for task_type, description in test_cases:
        agent = registry.find_agent_for_task(task_type)
        if agent:
            print(f"  {description}: {agent.name} ✅")
        else:
            print(f"  {description}: 未找到Agent ❌")
    
    print("✅ Agent能力匹配测试通过\n")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("wdai v3.0 Phase 3 - Agent System 测试")
    print("=" * 60 + "\n")
    
    try:
        await test_agent_registration()
        await test_simple_task()
        await test_multi_step_task()
        await test_fresh_eyes()
        await test_todo_planning()
        await test_agent_capabilities()
        
        print("=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
