"""
Kimi Multi-Agent Platform - Integration Demo
演示: Workflow + Agent + Memory 协同工作
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/kimi-platform/src')

from engine.workflow import DAG, StartNode, EndNode, TaskNode, run_workflow
from agents.agent import create_agent, create_orchestrator, Task
from tools.builtin import get_default_tools
from memory.memory import create_memory_manager
import tempfile
import shutil


def demo_research_workflow():
    """
    演示: 研究任务工作流
    
    流程:
    1. 从记忆中检索相关背景
    2. Agent执行研究任务
    3. 存储研究结果到记忆
    4. 生成报告
    """
    print("\n" + "="*70)
    print("🚀 INTEGRATION DEMO: Research Workflow with Memory")
    print("="*70)
    
    # 创建临时存储目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 1. 初始化系统组件
        print("\n[1] Initializing components...")
        
        # 记忆系统
        memory = create_memory_manager(temp_dir)
        memory.remember("User is interested in AI and Machine Learning", importance="high")
        memory.remember("Previous research: Deep Learning basics", importance="normal")
        
        # Agent编排器
        orch = create_orchestrator()
        
        # 创建研究Agent
        researcher = create_agent("researcher", "research", "Research specialist")
        for tool in get_default_tools():
            researcher.register_tool(tool)
        orch.register_agent(researcher)
        
        print("  ✓ Memory manager initialized")
        print("  ✓ Research agent created with tools")
        
        # 2. 创建工作流
        print("\n[2] Creating workflow...")
        
        dag = DAG("research_workflow")
        dag.add_node(StartNode("start"))
        dag.add_node(TaskNode("recall_context", {"name": "Recall Context"}))
        dag.add_node(TaskNode("do_research", {"name": "Research"}))
        dag.add_node(TaskNode("store_result", {"name": "Store Result"}))
        dag.add_node(EndNode("end"))
        
        dag.add_edge("start", "recall_context")
        dag.add_edge("recall_context", "do_research")
        dag.add_edge("do_research", "store_result")
        dag.add_edge("store_result", "end")
        
        print("  ✓ Workflow DAG created")
        
        # 3. 设置任务处理器
        print("\n[3] Setting up task handlers...")
        
        # 上下文检索
        def recall_handler(ctx, cfg):
            context = memory.get_context(3)
            ctx.set("context", context)
            return f"Recalled context:\n{context}"
        
        dag.nodes["recall_context"].set_handler(recall_handler)
        
        # 研究任务
        def research_handler(ctx, cfg):
            # 创建任务给Agent
            task = Task(
                task_id="research_1",
                task_type="research",
                description="Research AI trends",
                input_data="Latest AI developments 2025",
                context={"background": ctx.get("context", "")}
            )
            
            # 执行研究
            result = researcher.execute(task)
            ctx.set("research_result", result)
            return result
        
        dag.nodes["do_research"].set_handler(research_handler)
        
        # 存储结果
        def store_handler(ctx, cfg):
            result = ctx.get("research_result")
            memory.remember(f"Research result: {result}", importance="high")
            return "Result stored to memory"
        
        dag.nodes["store_result"].set_handler(store_handler)
        
        print("  ✓ Task handlers configured")
        
        # 4. 执行工作流
        print("\n[4] Executing workflow...")
        print("-" * 50)
        
        result = run_workflow(dag)
        
        print("-" * 50)
        
        # 5. 验证结果
        print("\n[5] Results:")
        print(f"  Workflow status: {result['status']}")
        print(f"  Executed nodes: {result['executed_nodes']}")
        print(f"  Memory stats: {memory.stats()}")
        
        # 回忆新存储的内容
        print("\n[6] Recall stored research:")
        recall = memory.recall("AI research", top_k=2)
        for item in recall:
            print(f"  • {item}")
        
        print("\n" + "="*70)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print("="*70)
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


def demo_multi_agent_with_memory():
    """
    演示: 多Agent协作 + 共享记忆
    """
    print("\n" + "="*70)
    print("🚀 DEMO: Multi-Agent Collaboration with Shared Memory")
    print("="*70)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 初始化
        memory = create_memory_manager(temp_dir)
        orch = create_orchestrator()
        
        # 创建两个Agent
        agent_a = create_agent("agent_a", "data_processor", "Process raw data")
        agent_b = create_agent("agent_b", "report_generator", "Generate reports")
        
        # 给Agent A添加工具
        agent_a.register_tool([t for t in get_default_tools() if t.name == "calculator"][0])
        
        orch.register_agent(agent_a)
        orch.register_agent(agent_b)
        
        print("\n[1] Agents registered:")
        print(f"  • {agent_a}")
        print(f"  • {agent_b}")
        
        # Agent A处理数据并存储
        print("\n[2] Agent A processing data...")
        task_a = Task(
            task_id="process_1",
            task_type="calculator",
            description="Calculate metrics",
            input_data="",
            context={"expression": "100 + 200 + 300"}
        )
        result_a = agent_a.execute(task_a)
        
        # 存储到共享记忆
        memory.store("processed_data", result_a, level="all")
        print(f"  Result: {result_a}")
        print(f"  Stored to shared memory")
        
        # Agent B读取记忆并生成报告
        print("\n[3] Agent B generating report...")
        data = memory.retrieve("processed_data")
        task_b = Task(
            task_id="report_1",
            task_type="report",
            description="Generate report",
            input_data=f"Data: {data}",
            context={}
        )
        result_b = agent_b.execute(task_b)
        print(f"  Report: {result_b}")
        
        # 消息传递
        print("\n[4] Agent messaging:")
        orch.send_message("agent_a", "agent_b", "Data processing completed")
        print(f"  Agent B received: {agent_b.inbox[-1].content}")
        
        print("\n" + "="*70)
        print("✅ MULTI-AGENT DEMO COMPLETED")
        print("="*70)
        
        return True
        
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("\n" + "🔥" * 35)
    print("KIMI PLATFORM - FULL SYSTEM DEMO")
    print("🔥" * 35)
    
    try:
        demo_research_workflow()
        demo_multi_agent_with_memory()
        
        print("\n\n" + "🎉" * 35)
        print("ALL DEMOS PASSED!")
        print("System Status: WORKFLOW ✅ AGENT ✅ MEMORY ✅")
        print("🎉" * 35)
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
