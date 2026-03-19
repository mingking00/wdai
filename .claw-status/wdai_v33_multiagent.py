#!/usr/bin/env python3
"""
WDai Multi-Agent v3.3 (evo-002集成)
集成多Agent协作框架
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from wdai_v32_adaptive import WDaiSystemV32
from multi_agent_collab import (
    MultiAgentCollaboration, AGENT_TEMPLATES,
    create_code_review_workflow, create_research_workflow,
    Task
)
import hashlib
import time


class WDaiSystemV33(WDaiSystemV32):
    """
    WDai v3.3
    新增：多Agent协作框架 (evo-002)
    """
    
    _instance = None
    
    def __init__(self):
        if self._initialized:
            return
        
        # 先初始化父类（v3.2）
        super().__init__()
        
        print("\n" + "="*60)
        print("🔥 升级至 WDai v3.3")
        print("="*60)
        
        # 初始化多Agent协作
        print("🚀 启用多Agent协作框架...")
        self.multi_agent = MultiAgentCollaboration()
        
        # 注册默认Agents
        for name, role in AGENT_TEMPLATES.items():
            self.multi_agent.register_agent(name, role)
        
        print(f"✅ 已注册 {len(AGENT_TEMPLATES)} 个Agent角色")
        print("   - researcher: 专业研究员")
        print("   - developer: 软件工程师")
        print("   - reviewer: 代码审查专家")
        print("   - planner: 项目规划专家")
        print("   - writer: 技术文档专家")
        
        print("="*60)
    
    def create_collaborative_task(self, description: str, 
                                  workflow_type: str = "code_review",
                                  context: str = "",
                                  expected_output: str = "") -> dict:
        """
        创建多Agent协作任务
        
        Args:
            description: 任务描述
            workflow_type: 工作流类型 (code_review, research)
            context: 任务上下文
            expected_output: 期望输出
        
        Returns:
            任务执行结果
        """
        # 创建任务
        task = self.multi_agent.create_task(
            description=description,
            context=context,
            expected_output=expected_output
        )
        
        # 选择工作流
        if workflow_type == "code_review":
            workflow = create_code_review_workflow()
        elif workflow_type == "research":
            workflow = create_research_workflow()
        else:
            workflow = create_code_review_workflow()
        
        # 执行协作任务
        result = self.multi_agent.execute_collaborative_task(task, workflow)
        
        return {
            'task_id': task.id,
            'workflow': workflow_type,
            'steps': result['iterations'],
            'conversation': result['conversation_summary'],
            'participants': list(workflow.steps.values())[0].agent_role if workflow.steps else None
        }
    
    def delegate_to_agent(self, task_id: str, from_agent: str, to_agent: str) -> bool:
        """委托任务给其他Agent"""
        try:
            self.multi_agent.delegate_task(task_id, from_agent, to_agent)
            return True
        except Exception as e:
            print(f"委托失败: {e}")
            return False
    
    def get_multi_agent_stats(self) -> dict:
        """获取多Agent统计"""
        return self.multi_agent.get_stats()


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Multi-Agent v3.3 - 集成测试")
    print("="*60)
    
    # 创建系统
    system = WDaiSystemV33()
    
    # 测试1: 代码审查协作
    print("\n🧪 测试: 代码审查多Agent协作")
    result = system.create_collaborative_task(
        description="实现用户认证模块，包含登录、注册、密码重置功能",
        workflow_type="code_review",
        context="WDai系统需要用户管理功能",
        expected_output="完整的用户认证模块代码和单元测试"
    )
    
    print(f"\n✅ 协作完成!")
    print(f"   任务ID: {result['task_id']}")
    print(f"   工作流: {result['workflow']}")
    print(f"   执行步骤: {result['steps']}")
    
    # 测试2: 研究协作
    print("\n🧪 测试: 深度研究多Agent协作")
    result2 = system.create_collaborative_task(
        description="调研AI Agent安全性的最新研究进展",
        workflow_type="research",
        expected_output="研究报告，包含至少3种安全攻击模式和防御策略"
    )
    
    print(f"\n✅ 协作完成!")
    print(f"   任务ID: {result2['task_id']}")
    print(f"   执行步骤: {result2['steps']}")
    
    # 统计
    print("\n📊 多Agent统计")
    stats = system.get_multi_agent_stats()
    print(f"   注册Agents: {stats['registered_agents']}")
    print(f"   已完成任务: {stats['completed_tasks']}")
    
    print("\n" + "="*60)
    print("✅ v3.3 多Agent协作集成测试完成")
    print("="*60)
