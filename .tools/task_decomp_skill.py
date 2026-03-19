#!/usr/bin/env python3
"""
Task Decomposition Skill - 智能任务分解与执行规划

用途: 将复杂任务分解为可执行的子任务，并生成执行计划
调用: python3 task_decomp_skill.py "复杂任务描述" [--depth deep]

集成到OpenClaw工作流:
- 复杂任务自动拆解
- 多步骤计划生成
- 执行进度追踪
"""

import sys
import json
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

WORKSPACE = Path("/root/.openclaw/workspace")
PLANS_DIR = WORKSPACE / ".plans"
PLANS_DIR.mkdir(parents=True, exist_ok=True)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SubTask:
    """子任务"""
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_minutes: int = 30
    dependencies: List[str] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    output_artifact: str = ""
    notes: str = ""
    completed_at: str = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SubTask":
        data['status'] = TaskStatus(data['status'])
        data['priority'] = TaskPriority(data['priority'])
        return cls(**data)


@dataclass
class ExecutionPlan:
    """执行计划"""
    id: str
    title: str
    description: str
    created_at: str
    status: TaskStatus = TaskStatus.PENDING
    subtasks: List[SubTask] = field(default_factory=list)
    total_estimated_minutes: int = 0
    completed_subtasks: int = 0
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at,
            "status": self.status.value,
            "subtasks": [s.to_dict() for s in self.subtasks],
            "total_estimated_minutes": self.total_estimated_minutes,
            "completed_subtasks": self.completed_subtasks,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExecutionPlan":
        plan = cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            created_at=data['created_at'],
            status=TaskStatus(data['status']),
            total_estimated_minutes=data.get('total_estimated_minutes', 0),
            completed_subtasks=data.get('completed_subtasks', 0),
            notes=data.get('notes', '')
        )
        plan.subtasks = [SubTask.from_dict(s) for s in data.get('subtasks', [])]
        return plan


class TaskDecomposer:
    """任务分解器"""
    
    # 常见任务模式及分解策略
    TASK_PATTERNS = {
        "research": {
            "keywords": ["研究", "调查", "分析", "survey", "research", "analyze"],
            "template": [
                {"title": "定义研究范围", "est": 20, "priority": "CRITICAL"},
                {"title": "收集资料", "est": 60, "priority": "HIGH"},
                {"title": "分析整理", "est": 40, "priority": "HIGH"},
                {"title": "生成报告", "est": 30, "priority": "MEDIUM"}
            ]
        },
        "coding": {
            "keywords": ["实现", "编写", "代码", "开发", "implement", "code", "develop"],
            "template": [
                {"title": "需求分析", "est": 20, "priority": "CRITICAL"},
                {"title": "设计方案", "est": 30, "priority": "HIGH"},
                {"title": "编写代码", "est": 60, "priority": "HIGH"},
                {"title": "测试验证", "est": 30, "priority": "HIGH"},
                {"title": "文档编写", "est": 20, "priority": "MEDIUM"}
            ]
        },
        "debugging": {
            "keywords": ["修复", "调试", "bug", "fix", "debug", "排查"],
            "template": [
                {"title": "问题复现", "est": 15, "priority": "CRITICAL"},
                {"title": "根因分析", "est": 30, "priority": "CRITICAL"},
                {"title": "实施修复", "est": 30, "priority": "HIGH"},
                {"title": "验证测试", "est": 20, "priority": "HIGH"}
            ]
        },
        "writing": {
            "keywords": ["撰写", "写作", "文档", "write", "document", "draft"],
            "template": [
                {"title": "收集素材", "est": 30, "priority": "HIGH"},
                {"title": "大纲设计", "est": 20, "priority": "HIGH"},
                {"title": "内容撰写", "est": 60, "priority": "HIGH"},
                {"title": "审阅修改", "est": 30, "priority": "MEDIUM"}
            ]
        },
        "integration": {
            "keywords": ["集成", "整合", "对接", "integrate", "combine", "merge"],
            "template": [
                {"title": "接口分析", "est": 30, "priority": "CRITICAL"},
                {"title": "集成方案设计", "est": 30, "priority": "HIGH"},
                {"title": "实现集成", "est": 60, "priority": "HIGH"},
                {"title": "联调测试", "est": 40, "priority": "HIGH"}
            ]
        }
    }
    
    def __init__(self):
        self.plans: Dict[str, ExecutionPlan] = {}
        self._load_plans()
    
    def decompose(self, task_description: str, depth: str = "standard") -> ExecutionPlan:
        """
        分解任务
        
        Args:
            task_description: 任务描述
            depth: 分解深度 (standard/deep)
            
        Returns:
            执行计划
        """
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # 识别任务类型
        task_type = self._detect_task_type(task_description)
        
        # 生成子任务
        if task_type and task_type in self.TASK_PATTERNS:
            subtasks = self._generate_from_template(
                task_description, 
                self.TASK_PATTERNS[task_type]["template"],
                depth
            )
        else:
            subtasks = self._generate_generic_subtasks(task_description, depth)
        
        # 设置依赖关系
        subtasks = self._set_dependencies(subtasks)
        
        # 计算总时间
        total_time = sum(s.estimated_minutes for s in subtasks)
        
        plan = ExecutionPlan(
            id=plan_id,
            title=self._extract_title(task_description),
            description=task_description,
            created_at=datetime.now().isoformat(),
            subtasks=subtasks,
            total_estimated_minutes=total_time,
            completed_subtasks=0
        )
        
        # 保存
        self.plans[plan_id] = plan
        self._save_plan(plan)
        
        return plan
    
    def _detect_task_type(self, description: str) -> Optional[str]:
        """检测任务类型"""
        desc_lower = description.lower()
        scores = {}
        
        for task_type, config in self.TASK_PATTERNS.items():
            score = sum(1 for kw in config["keywords"] if kw in desc_lower)
            if score > 0:
                scores[task_type] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return None
    
    def _generate_from_template(self, description: str, 
                                template: List[Dict], depth: str) -> List[SubTask]:
        """基于模板生成子任务"""
        subtasks = []
        
        for i, item in enumerate(template):
            subtask = SubTask(
                id=f"T{i+1:02d}",
                title=item["title"],
                description=f"{item['title']} - {description[:50]}...",
                priority=TaskPriority[item["priority"]],
                estimated_minutes=item["est"],
                tools_required=self._suggest_tools(item["title"])
            )
            subtasks.append(subtask)
            
            # deep模式下进一步分解
            if depth == "deep" and item["est"] > 30:
                sub_subtasks = self._decompose_deep(subtask)
                subtask.dependencies.extend([s.id for s in sub_subtasks])
                subtasks.extend(sub_subtasks)
        
        return subtasks
    
    def _generate_generic_subtasks(self, description: str, depth: str) -> List[SubTask]:
        """通用任务分解"""
        subtasks = [
            SubTask(
                id="T01",
                title="需求理解",
                description=f"理解任务需求: {description[:80]}...",
                priority=TaskPriority.CRITICAL,
                estimated_minutes=15
            ),
            SubTask(
                id="T02",
                title="信息收集",
                description="收集必要的信息和资源",
                priority=TaskPriority.HIGH,
                estimated_minutes=30
            ),
            SubTask(
                id="T03",
                title="方案设计",
                description="设计解决方案",
                priority=TaskPriority.HIGH,
                estimated_minutes=30,
                dependencies=["T01"]
            ),
            SubTask(
                id="T04",
                title="执行实施",
                description="执行具体任务",
                priority=TaskPriority.HIGH,
                estimated_minutes=60,
                dependencies=["T02", "T03"]
            ),
            SubTask(
                id="T05",
                title="验证检查",
                description="验证结果是否符合预期",
                priority=TaskPriority.MEDIUM,
                estimated_minutes=20,
                dependencies=["T04"]
            )
        ]
        
        return subtasks
    
    def _decompose_deep(self, subtask: SubTask) -> List[SubTask]:
        """深度分解子任务"""
        # 简化实现：将大任务拆分为2-3个小任务
        chunks = [
            {"title": f"{subtask.title} - 准备", "est": subtask.estimated_minutes // 3},
            {"title": f"{subtask.title} - 核心", "est": subtask.estimated_minutes // 3},
            {"title": f"{subtask.title} - 收尾", "est": subtask.estimated_minutes // 3}
        ]
        
        deep_subtasks = []
        for i, chunk in enumerate(chunks):
            deep_subtasks.append(SubTask(
                id=f"{subtask.id}.{i+1}",
                title=chunk["title"],
                description=f"深度分解: {subtask.title}",
                priority=subtask.priority,
                estimated_minutes=chunk["est"]
            ))
        
        return deep_subtasks
    
    def _set_dependencies(self, subtasks: List[SubTask]) -> List[SubTask]:
        """设置任务依赖关系"""
        # 简化：顺序依赖
        for i in range(1, len(subtasks)):
            if not subtasks[i].dependencies:
                # 检查优先级
                if subtasks[i].priority.value <= subtasks[i-1].priority.value:
                    subtasks[i].dependencies.append(subtasks[i-1].id)
        
        return subtasks
    
    def _suggest_tools(self, task_title: str) -> List[str]:
        """建议使用的工具"""
        tool_map = {
            "搜索": ["search", "web_fetch"],
            "分析": ["kimi_search", "kimi_fetch"],
            "代码": ["file_editor", "exec"],
            "文档": ["read", "write"],
            "测试": ["exec", "browser"],
            "设计": ["canvas"]
        }
        
        suggested = []
        for keyword, tools in tool_map.items():
            if keyword in task_title:
                suggested.extend(tools)
        
        return suggested[:3]  # 最多3个
    
    def _extract_title(self, description: str) -> str:
        """提取任务标题"""
        # 取前30个字符作为标题
        title = description[:40] if len(description) > 40 else description
        return title.strip()
    
    def update_task_status(self, plan_id: str, task_id: str, 
                          status: TaskStatus, notes: str = ""):
        """更新任务状态"""
        plan = self.plans.get(plan_id)
        if not plan:
            return False
        
        for subtask in plan.subtasks:
            if subtask.id == task_id:
                subtask.status = status
                subtask.notes = notes
                if status == TaskStatus.COMPLETED:
                    subtask.completed_at = datetime.now().isoformat()
                    plan.completed_subtasks += 1
                break
        
        # 更新计划状态
        if plan.completed_subtasks == len(plan.subtasks):
            plan.status = TaskStatus.COMPLETED
        elif plan.completed_subtasks > 0:
            plan.status = TaskStatus.IN_PROGRESS
        
        self._save_plan(plan)
        return True
    
    def get_next_tasks(self, plan_id: str, count: int = 3) -> List[SubTask]:
        """获取接下来要执行的任务"""
        plan = self.plans.get(plan_id)
        if not plan:
            return []
        
        # 找到可执行的任务（依赖已完成）
        executable = []
        for subtask in plan.subtasks:
            if subtask.status == TaskStatus.PENDING:
                # 检查依赖
                deps_satisfied = all(
                    any(s.id == dep and s.status == TaskStatus.COMPLETED 
                        for s in plan.subtasks)
                    for dep in subtask.dependencies
                )
                if deps_satisfied:
                    executable.append(subtask)
        
        # 按优先级排序
        executable.sort(key=lambda x: x.priority.value, reverse=True)
        return executable[:count]
    
    def _load_plans(self):
        """加载计划"""
        for plan_file in PLANS_DIR.glob("plan_*.json"):
            with open(plan_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                plan = ExecutionPlan.from_dict(data)
                self.plans[plan.id] = plan
    
    def _save_plan(self, plan: ExecutionPlan):
        """保存计划"""
        plan_file = PLANS_DIR / f"plan_{plan.id}.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)
    
    def format_plan(self, plan: ExecutionPlan) -> str:
        """格式化计划输出"""
        lines = [
            f"📋 执行计划: {plan.title}",
            f"ID: {plan.id}",
            f"状态: {plan.status.value}",
            f"预计耗时: {plan.total_estimated_minutes} 分钟",
            f"完成进度: {plan.completed_subtasks}/{len(plan.subtasks)}",
            "",
            "子任务列表:",
            "-" * 60
        ]
        
        for subtask in plan.subtasks:
            status_icon = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.BLOCKED: "🚫",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌"
            }.get(subtask.status, "⏳")
            
            priority_icon = "🔴" if subtask.priority == TaskPriority.CRITICAL else \
                          "🟠" if subtask.priority == TaskPriority.HIGH else \
                          "🟡" if subtask.priority == TaskPriority.MEDIUM else "🟢"
            
            deps = f" (依赖: {', '.join(subtask.dependencies)})" if subtask.dependencies else ""
            lines.append(f"{status_icon} [{subtask.id}] {priority_icon} {subtask.title}")
            lines.append(f"   预计: {subtask.estimated_minutes}分钟{deps}")
            if subtask.tools_required:
                lines.append(f"   工具: {', '.join(subtask.tools_required)}")
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Task Decomposition Skill")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # create 命令
    create_parser = subparsers.add_parser("create", help="创建执行计划")
    create_parser.add_argument("task", help="任务描述")
    create_parser.add_argument("--depth", choices=["standard", "deep"], 
                               default="standard", help="分解深度")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出计划")
    list_parser.add_argument("--status", help="按状态过滤")
    
    # update 命令
    update_parser = subparsers.add_parser("update", help="更新任务状态")
    update_parser.add_argument("plan_id", help="计划ID")
    update_parser.add_argument("task_id", help="任务ID")
    update_parser.add_argument("status", choices=["pending", "in_progress", "blocked", 
                                                  "completed", "failed"])
    update_parser.add_argument("--notes", default="", help="备注")
    
    # next 命令
    next_parser = subparsers.add_parser("next", help="获取接下来要执行的任务")
    next_parser.add_argument("plan_id", help="计划ID")
    next_parser.add_argument("--count", type=int, default=3, help="数量")
    
    args = parser.parse_args()
    
    decomposer = TaskDecomposer()
    
    if args.command == "create":
        plan = decomposer.decompose(args.task, args.depth)
        print(decomposer.format_plan(plan))
        print(f"\n💾 计划已保存，ID: {plan.id}")
    
    elif args.command == "list":
        for plan_id, plan in decomposer.plans.items():
            if args.status and plan.status.value != args.status:
                continue
            progress = plan.completed_subtasks / len(plan.subtasks) * 100 if plan.subtasks else 0
            print(f"[{plan.status.value:12}] {plan_id} - {plan.title[:40]}... ({progress:.0f}%)")
    
    elif args.command == "update":
        status = TaskStatus(args.status)
        success = decomposer.update_task_status(args.plan_id, args.task_id, status, args.notes)
        if success:
            print(f"✅ 已更新任务 {args.task_id} 状态为 {status.value}")
        else:
            print(f"❌ 未找到计划或任务")
    
    elif args.command == "next":
        tasks = decomposer.get_next_tasks(args.plan_id, args.count)
        if tasks:
            print(f"🎯 接下来要执行的任务:\n")
            for task in tasks:
                print(f"[{task.id}] {task.title} (优先级: {task.priority.name})")
        else:
            print("没有可执行的任务")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
