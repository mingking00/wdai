"""
OpenClaw Integration Script for Kimi Platform

Usage in OpenClaw:
    from skills.kimi_platform.integration import quick_research, quick_workflow
"""

import sys
from pathlib import Path

# 添加路径
PLATFORM_PATH = Path(__file__).parent.parent.parent / "kimi-platform" / "src"
sys.path.insert(0, str(PLATFORM_PATH))

from engine.workflow import DAG, StartNode, EndNode, TaskNode, run_workflow
from agents.agent import create_agent, create_orchestrator, Task
from memory.memory import create_memory_manager
from tools.builtin import get_default_tools
import tempfile
import shutil


def quick_research(query: str) -> dict:
    """
    快速研究任务
    
    Args:
        query: 研究主题
    
    Returns:
        研究结果
    """
    print(f"[QuickResearch] Starting research on: {query}")
    
    # 创建研究Agent
    orch = create_orchestrator()
    researcher = create_agent("researcher", "research")
    
    for tool in get_default_tools():
        researcher.register_tool(tool)
    
    orch.register_agent(researcher)
    
    # 执行任务
    task = orch.create_task("research", f"Research: {query}", query)
    agent_id, result = orch.dispatch_task(task)
    
    return {
        "query": query,
        "agent": agent_id,
        "result": result,
        "status": "completed"
    }


def quick_workflow(steps: list, initial_data: dict = None) -> dict:
    """
    快速执行工作流
    
    Args:
        steps: 步骤列表 [{"name": "step1", "handler": func}, ...]
        initial_data: 初始数据
    
    Returns:
        执行结果
    """
    print(f"[QuickWorkflow] Creating workflow with {len(steps)} steps")
    
    # 创建DAG
    dag = DAG("quick_workflow")
    dag.add_node(StartNode("start"))
    
    # 添加任务节点
    prev_node = "start"
    for i, step in enumerate(steps):
        node_id = f"step_{i}"
        node = TaskNode(node_id, {"name": step.get("name", node_id)})
        
        # 设置处理器
        if "handler" in step:
            node.set_handler(step["handler"])
        
        dag.add_node(node)
        dag.add_edge(prev_node, node_id)
        prev_node = node_id
    
    dag.add_node(EndNode("end"))
    dag.add_edge(prev_node, "end")
    
    # 执行
    result = run_workflow(dag, initial_data)
    
    return result


def quick_calculate(expression: str) -> str:
    """
    快速计算
    
    Args:
        expression: 数学表达式
    
    Returns:
        计算结果
    """
    calculator = create_agent("calc", "math")
    calc_tool = [t for t in get_default_tools() if t.name == "calculator"][0]
    calculator.register_tool(calc_tool)
    
    task = Task(
        task_id="calc_1",
        task_type="calculator",
        description="Calculate",
        input_data="",
        context={"expression": expression}
    )
    
    return calculator.execute(task)


def quick_remember(fact: str, importance: str = "normal") -> str:
    """
    快速记忆
    
    Args:
        fact: 要记住的事实
        importance: low/normal/high
    
    Returns:
        记忆ID
    """
    temp_dir = tempfile.mkdtemp()
    try:
        memory = create_memory_manager(temp_dir)
        memory.remember(fact, importance=importance)
        return f"Remembered: {fact[:50]}..."
    finally:
        shutil.rmtree(temp_dir)


def quick_recall(query: str, top_k: int = 3) -> list:
    """
    快速回忆
    
    Args:
        query: 查询内容
        top_k: 返回结果数
    
    Returns:
        相关记忆列表
    """
    temp_dir = tempfile.mkdtemp()
    try:
        memory = create_memory_manager(temp_dir)
        return memory.recall(query, top_k=top_k)
    finally:
        shutil.rmtree(temp_dir)


# 便捷函数映射
QUICK_FUNCTIONS = {
    "research": quick_research,
    "workflow": quick_workflow,
    "calculate": quick_calculate,
    "remember": quick_remember,
    "recall": quick_recall,
}


def execute(task_type: str, **kwargs) -> any:
    """
    统一执行接口
    
    Args:
        task_type: research/workflow/calculate/remember/recall
        **kwargs: 任务参数
    
    Returns:
        执行结果
    """
    if task_type in QUICK_FUNCTIONS:
        return QUICK_FUNCTIONS[task_type](**kwargs)
    else:
        raise ValueError(f"Unknown task type: {task_type}")


__all__ = [
    "quick_research",
    "quick_workflow", 
    "quick_calculate",
    "quick_remember",
    "quick_recall",
    "execute",
    "QUICK_FUNCTIONS",
]
