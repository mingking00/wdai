#!/usr/bin/env python3
"""
Task Planner - 任务规划与多模型验证系统
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

class TaskComplexity(Enum):
    """任务复杂度等级"""
    SIMPLE = "simple"      # 简单任务，直接执行
    MODERATE = "moderate"  # 中等任务，建议规划
    COMPLEX = "complex"    # 复杂任务，强制规划

@dataclass
class Constraint:
    """约束定义"""
    category: str          # 类别：performance/security/functional/etc
    description: str       # 描述
    priority: int          # 优先级 1-10
    verification: str      # 如何验证
    implicit: bool = False # 是否隐含约束

@dataclass
class PlanStep:
    """计划步骤"""
    step_id: int
    description: str
    estimated_time: str
    dependencies: List[int]
    validation_criteria: List[str]
    artifacts: List[str]

@dataclass
class TaskPlan:
    """任务计划"""
    task_id: str
    task_description: str
    complexity: TaskComplexity
    constraints: List[Constraint]
    steps: List[PlanStep]
    risks: List[str]
    total_estimate: str
    created_at: str
    validated: bool = False

class ConstraintExtractor:
    """约束提取引擎"""
    
    # 常见隐含约束映射
    IMPLICIT_CONSTRAINTS = {
        "高性能": [
            Constraint("performance", "响应时间 < 200ms", 9, "压力测试"),
            Constraint("performance", "支持并发 > 1000 QPS", 8, "负载测试"),
        ],
        "安全": [
            Constraint("security", "输入验证", 10, "渗透测试"),
            Constraint("security", "SQL注入防护", 10, "安全扫描"),
            Constraint("security", "XSS防护", 9, "安全扫描"),
        ],
        "用户": [
            Constraint("functional", "用户认证", 10, "功能测试"),
            Constraint("functional", "权限管理", 9, "功能测试"),
        ],
        "登录": [
            Constraint("security", "密码加密存储", 10, "代码审查"),
            Constraint("security", "登录失败限制", 8, "功能测试"),
        ],
        "API": [
            Constraint("functional", "RESTful 规范", 7, "API测试"),
            Constraint("functional", "文档生成", 6, "文档检查"),
        ],
    }
    
    def extract(self, requirement: str) -> List[Constraint]:
        """从需求中提取约束"""
        constraints = []
        
        # 关键词匹配
        for keyword, implicit in self.IMPLICIT_CONSTRAINTS.items():
            if keyword in requirement:
                for c in implicit:
                    c_copy = Constraint(
                        c.category, c.description, c.priority, 
                        c.verification, implicit=True
                    )
                    constraints.append(c_copy)
        
        # TODO: 使用 LLM 进行更智能的约束提取
        
        return constraints
    
    def complete_constraints(self, constraints: List[Constraint]) -> List[Constraint]:
        """补全约束（检查冲突、补全缺失）"""
        completed = list(constraints)
        
        # 如果有用户相关约束，自动补全安全约束
        has_user = any(c.description == "用户认证" for c in constraints)
        has_security = any(c.category == "security" for c in constraints)
        
        if has_user and not has_security:
            completed.append(Constraint(
                "security", "会话管理安全", 9, "安全审计", implicit=True
            ))
        
        return completed

class TaskPlanner:
    """任务规划器"""
    
    COMPLEXITY_THRESHOLDS = {
        "lines_estimate": 100,  # 预估代码行数
        "component_count": 3,   # 涉及组件数
        "dependency_depth": 2,  # 依赖层级
    }
    
    def __init__(self, plans_dir: str = ".learning/plans"):
        self.plans_dir = Path(plans_dir)
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.constraint_extractor = ConstraintExtractor()
    
    def assess_complexity(self, task: str, context: Dict = None) -> TaskComplexity:
        """评估任务复杂度"""
        score = 0
        
        # 基于关键词评分
        complex_keywords = ["系统", "架构", "重构", "优化", "集成", "迁移"]
        for kw in complex_keywords:
            if kw in task:
                score += 1
        
        # 基于上下文评分
        if context:
            if context.get("estimated_lines", 0) > self.COMPLEXITY_THRESHOLDS["lines_estimate"]:
                score += 2
            if context.get("components", 0) > self.COMPLEXITY_THRESHOLDS["component_count"]:
                score += 1
        
        if score >= 3:
            return TaskComplexity.COMPLEX
        elif score >= 1:
            return TaskComplexity.MODERATE
        return TaskComplexity.SIMPLE
    
    async def generate_plan(self, task: str, context: Dict = None) -> TaskPlan:
        """生成任务计划"""
        from datetime import datetime
        
        # 生成任务ID
        task_hash = hashlib.md5(task.encode()).hexdigest()[:8]
        task_id = f"{datetime.now().strftime('%Y%m%d')}-{task_hash}"
        
        # 评估复杂度
        complexity = self.assess_complexity(task, context)
        
        # 提取约束
        constraints = self.constraint_extractor.extract(task)
        constraints = self.constraint_extractor.complete_constraints(constraints)
        
        # 生成计划步骤（简化版，实际应由 LLM 生成）
        steps = self._generate_steps(task, complexity)
        
        plan = TaskPlan(
            task_id=task_id,
            task_description=task,
            complexity=complexity,
            constraints=constraints,
            steps=steps,
            risks=self._identify_risks(task, constraints),
            total_estimate=self._estimate_time(steps),
            created_at=datetime.now().isoformat()
        )
        
        # 保存计划
        self._save_plan(plan)
        
        return plan
    
    def _generate_steps(self, task: str, complexity: TaskComplexity) -> List[PlanStep]:
        """生成计划步骤"""
        # 这里简化处理，实际应调用 LLM
        if complexity == TaskComplexity.SIMPLE:
            return [
                PlanStep(1, "分析需求", "10min", [], ["需求明确"], ["analysis.md"]),
                PlanStep(2, "实现功能", "30min", [1], ["功能完成"], ["code"]),
                PlanStep(3, "验证测试", "15min", [2], ["测试通过"], ["test_report"]),
            ]
        else:
            return [
                PlanStep(1, "需求分析", "30min", [], ["需求文档"], ["requirements.md"]),
                PlanStep(2, "架构设计", "45min", [1], ["设计文档"], ["design.md"]),
                PlanStep(3, "接口定义", "30min", [2], ["API文档"], ["api.md"]),
                PlanStep(4, "核心实现", "2h", [3], ["代码完成"], ["code"]),
                PlanStep(5, "集成测试", "1h", [4], ["测试通过"], ["test_report"]),
                PlanStep(6, "文档完善", "30min", [5], ["文档完整"], ["docs"]),
            ]
    
    def _identify_risks(self, task: str, constraints: List[Constraint]) -> List[str]:
        """识别风险"""
        risks = []
        
        high_priority = [c for c in constraints if c.priority >= 9]
        if len(high_priority) > 3:
            risks.append("约束过多可能导致开发周期延长")
        
        if any(c.category == "performance" for c in constraints):
            risks.append("性能优化可能需要多次迭代")
        
        return risks
    
    def _estimate_time(self, steps: List[PlanStep]) -> str:
        """估算总时间"""
        # 简化处理
        total_hours = len(steps) * 0.5
        return f"{total_hours}h"
    
    def _save_plan(self, plan: TaskPlan):
        """保存计划到文件"""
        plan_file = self.plans_dir / f"{plan.task_id}.json"
        
        # 转换为可序列化的字典
        data = {
            'task_id': plan.task_id,
            'task_description': plan.task_description,
            'complexity': plan.complexity.value,
            'constraints': [
                {
                    'category': c.category,
                    'description': c.description,
                    'priority': c.priority,
                    'verification': c.verification,
                    'implicit': c.implicit
                }
                for c in plan.constraints
            ],
            'steps': [
                {
                    'step_id': s.step_id,
                    'description': s.description,
                    'estimated_time': s.estimated_time,
                    'dependencies': s.dependencies,
                    'validation_criteria': s.validation_criteria,
                    'artifacts': s.artifacts
                }
                for s in plan.steps
            ],
            'risks': plan.risks,
            'total_estimate': plan.total_estimate,
            'created_at': plan.created_at,
            'validated': plan.validated
        }
        
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_plan(self, task_id: str) -> Optional[TaskPlan]:
        """加载计划"""
        plan_file = self.plans_dir / f"{task_id}.json"
        if not plan_file.exists():
            return None
        
        with open(plan_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 转换回对象
            data['complexity'] = TaskComplexity(data['complexity'])
            data['constraints'] = [Constraint(**c) for c in data['constraints']]
            data['steps'] = [PlanStep(**s) for s in data['steps']]
            return TaskPlan(**data)
    
    def format_plan(self, plan: TaskPlan) -> str:
        """格式化计划为可读文本"""
        lines = [
            f"# 任务计划 [{plan.task_id}]",
            f"",
            f"**任务**: {plan.task_description}",
            f"**复杂度**: {plan.complexity.value}",
            f"**预估时间**: {plan.total_estimate}",
            f"",
            f"## 约束条件",
        ]
        
        for c in plan.constraints:
            implicit_tag = " [隐含]" if c.implicit else ""
            lines.append(f"- [{c.category}] {c.description} (P{c.priority}){implicit_tag}")
        
        lines.extend([
            f"",
            f"## 执行步骤",
        ])
        
        for s in plan.steps:
            deps = f" (依赖: {s.dependencies})" if s.dependencies else ""
            lines.append(f"{s.step_id}. {s.description} - {s.estimated_time}{deps}")
        
        if plan.risks:
            lines.extend([
                f"",
                f"## 风险识别",
            ])
            for r in plan.risks:
                lines.append(f"- ⚠️ {r}")
        
        return "\n".join(lines)

class MultiModelValidator:
    """多模型验证器"""
    
    def __init__(self):
        self.models = ["k2p5"]  # 可扩展更多模型
    
    async def validate(self, decision: str, context: Dict = None) -> Dict:
        """多模型验证决策"""
        # 简化版：实际应调用 sessions_spawn 启动多个模型
        results = {
            "decision": decision,
            "validations": [],
            "consensus": None,
            "divergence": []
        }
        
        # TODO: 实现多模型并行验证
        
        return results

# 便捷函数
async def plan_task(task: str, context: Dict = None) -> TaskPlan:
    """快速规划任务"""
    planner = TaskPlanner()
    return await planner.generate_plan(task, context)

def extract_constraints(requirement: str) -> List[Constraint]:
    """快速提取约束"""
    extractor = ConstraintExtractor()
    return extractor.extract(requirement)

if __name__ == "__main__":
    # 测试
    async def test():
        planner = TaskPlanner()
        
        # 测试约束提取
        print("=== 约束提取测试 ===")
        constraints = planner.constraint_extractor.extract("实现高性能用户登录API")
        for c in constraints:
            print(f"  [{c.category}] {c.description} (P{c.priority})")
        
        # 测试复杂度评估
        print("\n=== 复杂度评估 ===")
        tasks = [
            "修复bug",
            "重构用户系统",
            "设计微服务架构"
        ]
        for t in tasks:
            comp = planner.assess_complexity(t)
            print(f"  {t}: {comp.value}")
        
        # 测试计划生成
        print("\n=== 计划生成 ===")
        plan = await planner.generate_plan("实现用户认证系统")
        print(planner.format_plan(plan))
    
    asyncio.run(test())
