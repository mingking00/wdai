#!/usr/bin/env python3
"""
wdai SearchAgent v1.0 - 与IER连接器集成版本
搜索 → 验证 → 学习 → 优化 完整闭环
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/.wdai-runtime')

from search_agent_v1 import SearchAgent
from ier_connector_v1 import IERConnector, IntegratedAgentSystem

async def integrated_search_demo():
    """集成搜索演示"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     🔗 集成搜索系统演示                                     ║")
    print("║     SearchAgent + IER连接器 + 执行引擎                      ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # 1. 创建SearchAgent
    search_agent = SearchAgent()
    
    # 2. 执行搜索
    query = "AI Agent framework comparison 2025"
    search_result = await search_agent.search_with_validation(query)
    
    print(f"✅ 搜索完成: {search_result['results_count']} 条结果")
    print(f"   验证洞察: {len(search_result['validated_insights'])} 条")
    print()
    
    # 3. IER学习 - 从搜索结果中提取经验
    print("[IER] 从搜索结果学习...")
    
    # 创建模拟执行结果用于IER学习
    from ier_connector_v1 import ExecutionResult
    
    task = {
        "task_id": f"search_{query[:20]}",
        "task_type": "research",
        "description": query
    }
    
    execution_result = ExecutionResult(
        success=search_result["success"],
        task_id=task["task_id"],
        agent_id="search_agent",
        output=search_result,
        logs=[f"搜索完成: {search_result['results_count']} 条结果"]
    )
    
    # 4. 触发IER后处理
    ier_result = search_agent.ier_connector.post_execution_pipeline(
        execution_result,
        task
    )
    
    print(f"[IER] 学习完成: {ier_result['insights_extracted']} 条新洞察")
    print()
    
    # 5. 下次搜索将使用这些经验
    print("💡 下次搜索时，SearchAgent将:")
    print("   • 优先使用验证通过的信息源")
    print("   • 根据历史成功率调整源权重")
    print("   • 避开低可信度的来源")
    print()
    
    print("="*65)
    print("✅ 集成搜索系统演示完成")
    print("="*65)

if __name__ == '__main__':
    asyncio.run(integrated_search_demo())
