"""
Inspiration Agents - 双代理架构

提供:
- BaseAgent: 代理基类
- PlannerAgent: 规划代理
- ExecutorAgent: 执行代理
- AgentCoordinator: 代理协调器
- SpecializedAnalysisSystem: 专业化分析代理系统 (SynthAgent Pattern)

使用方法:
    from agents import PlannerAgent, ExecutorAgent, AgentCoordinator
    from agents import SpecializedAnalysisSystem
    
    # 双代理系统
    coordinator = AgentCoordinator()
    planner = PlannerAgent('planner', coordinator.message_bus)
    executor = ExecutorAgent('executor', coordinator.message_bus)
    
    coordinator.register_agent(planner)
    coordinator.register_agent(executor)
    planner.register_executor('executor')
    
    coordinator.start_all()
    
    # 专业化分析系统
    system = SpecializedAnalysisSystem()
    system.start()
    result = system.analyze_papers(papers)
    system.stop()
"""

from .base import (
    BaseAgent,
    Task,
    TaskStatus,
    Message,
    MessageType,
    MessageBus,
    AgentCoordinator
)

from .planner_agent import PlannerAgent, SourceStrategy
from .executor_agent import ExecutorAgent
from .specialized_agents import (
    SpecializedAnalysisSystem,
    PaperAnalysisAgent,
    TrendRecognitionAgent,
    InsightGenerationAgent,
    AnalysisResult
)

__all__ = [
    'BaseAgent',
    'Task',
    'TaskStatus',
    'Message',
    'MessageType',
    'MessageBus',
    'AgentCoordinator',
    'PlannerAgent',
    'SourceStrategy',
    'ExecutorAgent',
    'SpecializedAnalysisSystem',
    'PaperAnalysisAgent',
    'TrendRecognitionAgent',
    'InsightGenerationAgent',
    'AnalysisResult'
]

__version__ = '1.1.0'
