"""
Kimi Multi-Agent Platform - OpenClaw Integration

提供多智能体协作、工作流编排、记忆管理功能
"""

import sys
from pathlib import Path

# 添加平台路径
PLATFORM_PATH = Path(__file__).parent.parent.parent / "kimi-platform" / "src"
sys.path.insert(0, str(PLATFORM_PATH))

# 导出核心组件
from engine.workflow import (
    DAG, WorkflowEngine, 
    StartNode, EndNode, TaskNode, ConditionNode,
    create_workflow, run_workflow
)

from agents.agent import (
    Agent, SimpleAgent, AgentOrchestrator, VerifierAgent,
    Task, ActionPlan, Tool,
    create_agent, create_verifier_agent, create_orchestrator
)

from memory.memory import (
    ShortTermMemory, LongTermMemory, SemanticMemory,
    MemoryManager, create_memory_manager
)

from tools.builtin import get_default_tools, get_all_tools
from tools.extended import get_extended_tools

# 便捷函数
__all__ = [
    # 工作流
    "DAG", "WorkflowEngine",
    "StartNode", "EndNode", "TaskNode", "ConditionNode",
    "create_workflow", "run_workflow",
    
    # Agent
    "Agent", "SimpleAgent", "AgentOrchestrator",
    "Task", "ActionPlan", "Tool",
    "create_agent", "create_orchestrator",
    
    # 记忆
    "ShortTermMemory", "LongTermMemory", "SemanticMemory",
    "MemoryManager", "create_memory_manager",
    
    # 工具
    "get_default_tools", "get_extended_tools", "get_all_tools",
]
