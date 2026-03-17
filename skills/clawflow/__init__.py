#!/usr/bin/env python3
"""
ClawFlow - 轻量级工作流引擎 v5.0 (Optimized)

基于 n8n 架构原理实现的 Python 工作流引擎
- 18种节点类型
- asyncio 真正并行执行
- 节点结果缓存
- 性能监控
- 工作流验证与可视化
- Webhook / Cron 集成

用法:
    from clawflow import WorkflowEngine
    
    workflow = {
        "name": "我的工作流",
        "nodes": [...],
        "connections": [...]
    }
    
    engine = WorkflowEngine()
    
    # 验证
    validation = engine.validate(workflow)
    
    # 顺序执行
    result = engine.execute(workflow)
    
    # 并行执行 (优化)
    result = engine.execute(workflow, parallel=True, use_cache=True)
    
    # 持久化
    engine.save_workflow(workflow, "workflow.json")
    workflow = engine.load_workflow("workflow.json")
"""

__version__ = "5.0.0"

from .engine import WorkflowEngine, ExecutionContext, ExecutionResult, NodeCache

__all__ = [
    "WorkflowEngine",
    "ExecutionContext",
    "ExecutionResult",
    "NodeCache",
]
