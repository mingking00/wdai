"""
OpenClaw Integration for Task Planner
与 OpenClaw 系统集成
"""

import asyncio
from pathlib import Path
from typing import Dict, Optional

# 直接导入（避免相对导入问题）
try:
    from planner import TaskPlanner, TaskComplexity, plan_task, extract_constraints
    from validator import MultiModelValidator, validate_decision
except ImportError:
    # 如果从 codedev_service 导入，使用绝对路径
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from planner import TaskPlanner, TaskComplexity, plan_task, extract_constraints
    from validator import MultiModelValidator, validate_decision

class TaskPlannerService:
    """任务规划服务 - OpenClaw 集成版"""
    
    def __init__(self):
        self.planner = TaskPlanner()
        self.validator = MultiModelValidator()
    
    async def plan_and_prompt(self, task: str, context: Dict = None) -> str:
        """
        规划任务并返回用户确认的提示
        
        使用方式：
        1. 调用此方法获取计划
        2. 向用户展示计划
        3. 用户确认后执行
        """
        plan = await self.planner.generate_plan(task, context)
        
        formatted = self.planner.format_plan(plan)
        
        # 如果是复杂任务，添加确认提示
        if plan.complexity == TaskComplexity.COMPLEX:
            formatted += "\n\n---\n⚠️ 这是复杂任务，建议确认计划后再执行。是否继续？(Y/N)"
        
        return formatted
    
    async def validate_with_models(self, decision: str, decision_type: str = "general") -> str:
        """
        多模型验证并返回格式化报告
        """
        report = await self.validator.validate(decision, decision_type)
        return self.validator.format_report(report)
    
    def should_plan_first(self, task: str, context: Dict = None) -> bool:
        """
        判断是否应该先规划再执行
        
        用于在执行前自动检查
        """
        complexity = self.planner.assess_complexity(task, context)
        return complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]
    
    async def smart_execute(self, task: str, context: Dict = None) -> Dict:
        """
        智能执行任务
        
        流程：
        1. 评估复杂度
        2. 如果复杂，先规划
        3. 关键决策多模型验证
        4. 执行
        """
        result = {
            "planned": False,
            "validated": False,
            "plan": None,
            "validation": None,
            "suggestion": ""
        }
        
        # 评估复杂度
        complexity = self.planner.assess_complexity(task, context)
        
        if complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]:
            # 生成计划
            plan = await self.planner.generate_plan(task, context)
            result["planned"] = True
            result["plan"] = plan
            
            # 生成建议
            result["suggestion"] = f"""此任务为 {complexity.value} 级别，建议：
1. 先审查生成的计划
2. 确认关键步骤
3. 分阶段执行"""
            
            # 如果是复杂任务，建议验证架构决策
            if complexity == TaskComplexity.COMPLEX:
                # 提取架构相关决策
                arch_decisions = self._extract_architecture_decisions(plan)
                if arch_decisions:
                    validation = await self.validator.validate(
                        arch_decisions[0], 
                        "architecture"
                    )
                    result["validated"] = True
                    result["validation"] = validation
        
        return result
    
    def _extract_architecture_decisions(self, plan) -> list:
        """从计划中提取架构决策"""
        decisions = []
        
        # 从约束中提取
        for c in plan.constraints:
            if c.category in ["architecture", "performance", "security"]:
                decisions.append(c.description)
        
        return decisions

# 全局服务实例
_service: Optional[TaskPlannerService] = None

def get_service() -> TaskPlannerService:
    """获取服务实例"""
    global _service
    if _service is None:
        _service = TaskPlannerService()
    return _service

# 便捷函数（供 OpenClaw 调用）
async def plan(task: str, context: Dict = None) -> str:
    """
    规划任务
    
    示例：
    /plan 实现用户认证系统
    """
    service = get_service()
    return await service.plan_and_prompt(task, context)

async def validate(decision: str, type: str = "general") -> str:
    """
    多模型验证决策
    
    示例：
    /validate 使用Redis存储会话 tokens
    """
    service = get_service()
    return await service.validate_with_models(decision, type)

async def extract(req: str) -> str:
    """
    提取约束
    
    示例：
    /extract 开发高性能用户管理API
    """
    constraints = extract_constraints(req)
    
    lines = ["## 提取的约束条件", ""]
    for c in constraints:
        implicit = " [隐含]" if c.implicit else ""
        lines.append(f"- [{c.category}] {c.description} (P{c.priority}){implicit}")
    
    if not constraints:
        lines.append("(未识别到明确约束)")
    
    return "\n".join(lines)

async def smart_plan(task: str) -> str:
    """
    智能规划（评估 + 规划 + 建议）
    
    示例：
    /smart-plan 重构现有用户模块
    """
    service = get_service()
    result = await service.smart_execute(task)
    
    output = []
    
    if result["planned"] and result["plan"]:
        output.append(service.planner.format_plan(result["plan"]))
    
    if result["suggestion"]:
        output.append("\n" + result["suggestion"])
    
    if result["validated"] and result["validation"]:
        output.append("\n" + service.validator.format_report(result["validation"]))
    
    return "\n".join(output)

# 检查是否需要规划
def check_planning_needed(task: str) -> bool:
    """
    检查任务是否需要先规划
    
    用于执行前自动判断
    """
    service = get_service()
    return service.should_plan_first(task)

__all__ = [
    'TaskPlannerService',
    'get_service',
    'plan',
    'validate',
    'extract',
    'smart_plan',
    'check_planning_needed',
]
