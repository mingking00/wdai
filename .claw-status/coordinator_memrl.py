#!/usr/bin/env python3
"""
MemRL 增强的 Coordinator Agent
在原有 Coordinator 基础上添加 MemRL 集成

集成点:
1. 任务分配时检索相关记忆 (带Q值)
2. 任务完成时自动更新记忆Q值
3. 利用高Q值记忆优化Agent选择
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from multi_agent_coordinator import MultiAgentCoordinator, get_coordinator
from memrl_integration import get_memrl_integration
from memrl_memory import get_memrl_memory
from typing import Dict, List, Optional, Any

class MemRLCoordinator:
    """
    MemRL 增强的 Coordinator
    包装原有 Coordinator，添加记忆学习和反馈功能
    """
    
    def __init__(self):
        # 基础协调器
        self.base_coord = get_coordinator()
        
        # MemRL 集成
        self.memrl_integration = get_memrl_integration()
        self.memrl_memory = get_memrl_memory()
        
        print("🧠 MemRL Coordinator 初始化完成")
    
    def assign_task(self, task_description: str, task_type: str,
                    preferred_agent: Optional[str] = None) -> Dict:
        """
        分配任务 (MemRL 增强版)
        
        增强功能:
        1. 检索相关记忆 (带Q值)
        2. 利用高Q值记忆优化Agent选择
        3. 开始追踪任务
        """
        # 1. 检索相关记忆
        print(f"\n🔍 [Coordinator] 检索相关记忆...")
        relevant_memories = self.memrl_integration.enhanced_memory_search(
            task_description, 
            max_results=3
        )
        
        if relevant_memories:
            print(f"   找到 {len(relevant_memories)} 条相关记忆:")
            for i, mem in enumerate(relevant_memories[:2], 1):
                print(f"   {i}. Q值:{mem.get('q_value', 0):.2f} {mem.get('content', '')[:50]}...")
        
        # 2. 调用基础协调器分配任务
        result = self.base_coord.assign_task(task_description, task_type, preferred_agent)
        
        if result.get("status") == "assigned":
            task_id = result["task_id"]
            
            # 3. 开始 MemRL 任务追踪
            self.memrl_integration.start_task(
                task_id=task_id,
                task_type=task_type,
                description=task_description
            )
            
            # 记录使用了哪些记忆
            for mem in relevant_memories:
                skill_id = mem.get("skill_id")
                if skill_id:
                    # 这里可以记录记忆使用情况
                    pass
            
            # 增强返回结果
            result["relevant_memories"] = [
                {
                    "skill_id": m.get("skill_id"),
                    "q_value": m.get("q_value"),
                    "content_preview": m.get("content", "")[:80]
                }
                for m in relevant_memories[:3]
            ]
        
        return result
    
    def report_task_complete(self, task_id: str, result: Dict) -> Dict:
        """
        报告任务完成 (MemRL 增强版)
        
        增强功能:
        1. 自动计算奖励
        2. 更新相关记忆的Q值
        3. 如成功，添加新经验
        """
        # 1. 获取任务状态
        task = self.base_coord.tasks.get(task_id)
        if not task:
            return {"status": "error", "message": "任务不存在"}
        
        # 2. 准备 MemRL 结果格式
        memrl_result = {
            "success": result.get("success", True),
            "verified": result.get("verified", False),
            "user_confirmed": result.get("user_confirmed", False),
            "experience": result.get("experience", result.get("summary", "")),
            "lesson_learned": result.get("lesson_learned", "")
        }
        
        # 3. 完成 MemRL 任务追踪 (自动更新Q值)
        print(f"\n📝 [Coordinator] 更新记忆Q值...")
        memrl_feedback = self.memrl_integration.complete_task(
            task_id=task_id,
            result=memrl_result
        )
        
        # 4. 调用基础协调器完成流程
        success = memrl_result["success"]
        base_result = self.base_coord.report_task_complete(task_id, result, success)
        
        # 5. 增强返回结果
        base_result["memrl_feedback"] = {
            "reward": memrl_feedback.get("reward"),
            "memory_updates": len(memrl_feedback.get("updates", [])),
            "duration": memrl_feedback.get("duration")
        }
        
        print(f"   奖励: {memrl_feedback.get('reward')}")
        print(f"   更新了 {len(memrl_feedback.get('updates', []))} 条记忆的Q值")
        
        return base_result
    
    def get_system_status(self) -> Dict:
        """获取系统状态 (包含 MemRL 统计)"""
        # 基础状态
        base_status = self.base_coord.get_system_status()
        
        # MemRL 统计
        memrl_stats = self.memrl_integration.get_learning_stats()
        
        # 合并
        base_status["memrl"] = {
            "memory_count": memrl_stats.get("count", 0),
            "avg_q_value": memrl_stats.get("avg_q", 0),
            "high_q_skills": memrl_stats.get("high_q_skills", 0),
            "total_usage": memrl_stats.get("total_usage", 0)
        }
        
        return base_status
    
    def search_memories(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        搜索记忆 (便捷方法)
        """
        return self.memrl_integration.enhanced_memory_search(query, max_results)
    
    def add_experience(self, query: str, experience: str, 
                       reward: float = 0.5) -> str:
        """
        手动添加经验
        """
        return self.memrl_memory.add_experience(query, experience, reward)
    
    def export_learning_report(self) -> str:
        """
        导出学习报告
        """
        return self.memrl_integration.export_report()
    
    # 透传基础协调器的方法
    def register_agent(self, *args, **kwargs):
        return self.base_coord.register_agent(*args, **kwargs)
    
    def arbitrate_conflict(self, *args, **kwargs):
        return self.base_coord.arbitrate_conflict(*args, **kwargs)


# 全局实例
_memrl_coord_instance = None

def get_memrl_coordinator() -> MemRLCoordinator:
    """获取 MemRL Coordinator 单例"""
    global _memrl_coord_instance
    if _memrl_coord_instance is None:
        _memrl_coord_instance = MemRLCoordinator()
    return _memrl_coord_instance


# ═══════════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════════

def assign_task_with_learning(task_description: str, task_type: str) -> Dict:
    """
    便捷函数: 分配任务并启用 MemRL 学习
    """
    coord = get_memrl_coordinator()
    return coord.assign_task(task_description, task_type)

def complete_task_with_feedback(task_id: str, result: Dict) -> Dict:
    """
    便捷函数: 完成任务并更新记忆
    """
    coord = get_memrl_coordinator()
    return coord.report_task_complete(task_id, result)


if __name__ == "__main__":
    # 测试 MemRL Coordinator
    print("=" * 60)
    print("MemRL Coordinator 测试")
    print("=" * 60)
    
    coord = get_memrl_coordinator()
    
    # 测试1: 分配任务
    print("\n1. 分配任务")
    result = coord.assign_task("部署博客到GitHub", "deploy")
    print(f"   状态: {result.get('status')}")
    print(f"   分配给: {result.get('agent_id')}")
    
    if result.get("status") == "assigned":
        task_id = result["task_id"]
        
        # 测试2: 完成任务
        print("\n2. 完成任务")
        complete_result = coord.report_task_complete(task_id, {
            "success": True,
            "verified": True,
            "experience": "用 git push 比 API 更稳定"
        })
        print(f"   状态: {complete_result.get('status')}")
        
        memrl = complete_result.get("memrl_feedback", {})
        print(f"   MemRL奖励: {memrl.get('reward')}")
        print(f"   记忆更新: {memrl.get('memory_updates')}")
    
    # 测试3: 系统状态
    print("\n3. 系统状态")
    status = coord.get_system_status()
    print(f"   Agent: {status['agents']['total']}个")
    if "memrl" in status:
        print(f"   MemRL记忆: {status['memrl']['memory_count']}条")
        print(f"   平均Q值: {status['memrl']['avg_q_value']:.2f}")
    
    print("\n✅ 测试完成")
