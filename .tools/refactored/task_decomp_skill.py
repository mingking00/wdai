#!/usr/bin/env python3
"""
Task Decomposition Skill - CLI-Anything 风格重构
任务分解与执行规划

用法: python3 task_decomp_skill.py [进入REPL模式]
     或在 REPL 中使用: task.create <任务描述>, task.list, task.update 等
"""

import sys
import json
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

# 导入核心框架
sys.path.insert(0, str(Path(__file__).parent))
from skill_generator import (
    command, CommandMetadata, arg, opt,
    CommandContext, CommandResult,
    ArgumentType,
    ReplSkin, CommandRegistry, SessionManager
)

# 配置
PLANS_DIR = Path("/root/.openclaw/workspace") / ".plans"
PLANS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 枚举和数据模型
# ============================================================================

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
    status: str = "pending"
    priority: int = 2
    estimated_minutes: int = 30
    dependencies: List[str] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    output_artifact: str = ""
    notes: str = ""
    completed_at: str = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SubTask":
        return cls(**data)


@dataclass
class ExecutionPlan:
    """执行计划"""
    id: str
    title: str
    description: str
    created_at: str
    status: str = "pending"
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
            "status": self.status,
            "subtasks": [s.to_dict() for s in self.subtasks],
            "total_estimated_minutes": self.total_estimated_minutes,
            "completed_subtasks": self.completed_subtasks,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExecutionPlan":
        plan = cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            created_at=data["created_at"],
            status=data.get("status", "pending"),
            total_estimated_minutes=data.get("total_estimated_minutes", 0),
            completed_subtasks=data.get("completed_subtasks", 0),
            notes=data.get("notes", "")
        )
        plan.subtasks = [SubTask.from_dict(s) for s in data.get("subtasks", [])]
        return plan


# ============================================================================
# 任务分解器
# ============================================================================

class TaskDecomposer:
    """任务分解器"""
    
    TASK_PATTERNS = {
        "research": {
            "keywords": ["研究", "调查", "分析", "survey", "research", "analyze"],
            "template": [
                {"title": "定义研究范围", "est": 20, "priority": 4},
                {"title": "收集资料", "est": 60, "priority": 3},
                {"title": "分析整理", "est": 40, "priority": 3},
                {"title": "生成报告", "est": 30, "priority": 2}
            ]
        },
        "coding": {
            "keywords": ["实现", "编写", "代码", "开发", "implement", "code", "develop"],
            "template": [
                {"title": "需求分析", "est": 20, "priority": 4},
                {"title": "设计方案", "est": 30, "priority": 3},
                {"title": "编写代码", "est": 60, "priority": 3},
                {"title": "测试验证", "est": 30, "priority": 3},
                {"title": "文档编写", "est": 20, "priority": 2}
            ]
        },
        "debugging": {
            "keywords": ["修复", "调试", "bug", "fix", "debug", "排查"],
            "template": [
                {"title": "问题复现", "est": 15, "priority": 4},
                {"title": "根因分析", "est": 30, "priority": 4},
                {"title": "实施修复", "est": 30, "priority": 3},
                {"title": "验证测试", "est": 20, "priority": 3}
            ]
        },
        "writing": {
            "keywords": ["撰写", "写作", "文档", "write", "document", "draft"],
            "template": [
                {"title": "收集素材", "est": 30, "priority": 3},
                {"title": "大纲设计", "est": 20, "priority": 3},
                {"title": "内容撰写", "est": 60, "priority": 3},
                {"title": "审阅修改", "est": 30, "priority": 2}
            ]
        },
        "integration": {
            "keywords": ["集成", "整合", "对接", "integrate", "combine", "merge"],
            "template": [
                {"title": "接口分析", "est": 30, "priority": 4},
                {"title": "集成方案设计", "est": 30, "priority": 3},
                {"title": "实现集成", "est": 60, "priority": 3},
                {"title": "联调测试", "est": 40, "priority": 3}
            ]
        }
    }
    
    def __init__(self):
        self.plans: Dict[str, ExecutionPlan] = {}
        self._load_plans()
    
    def decompose(self, task_description: str, depth: str = "standard") -> ExecutionPlan:
        """分解任务"""
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        task_type = self._detect_task_type(task_description)
        
        if task_type and task_type in self.TASK_PATTERNS:
            subtasks = self._generate_from_template(
                task_description,
                self.TASK_PATTERNS[task_type]["template"],
                depth
            )
        else:
            subtasks = self._generate_generic_subtasks(task_description, depth)
        
        subtasks = self._set_dependencies(subtasks)
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
        """基于模板生成"""
        subtasks = []
        
        for i, item in enumerate(template):
            subtask = SubTask(
                id=f"T{i+1:02d}",
                title=item["title"],
                description=f"{item['title']} - {description[:50]}...",
                priority=item["priority"],
                estimated_minutes=item["est"],
                tools_required=self._suggest_tools(item["title"])
            )
            subtasks.append(subtask)
            
            if depth == "deep" and item["est"] > 30:
                sub_subtasks = self._decompose_deep(subtask)
                subtask.dependencies.extend([s.id for s in sub_subtasks])
                subtasks.extend(sub_subtasks)
        
        return subtasks
    
    def _generate_generic_subtasks(self, description: str, depth: str) -> List[SubTask]:
        """通用分解"""
        return [
            SubTask(id="T01", title="需求理解", description=f"理解任务: {description[:80]}...",
                   priority=4, estimated_minutes=15),
            SubTask(id="T02", title="信息收集", description="收集必要信息",
                   priority=3, estimated_minutes=30, dependencies=["T01"]),
            SubTask(id="T03", title="方案设计", description="设计解决方案",
                   priority=3, estimated_minutes=30, dependencies=["T02"]),
            SubTask(id="T04", title="执行实施", description="执行具体任务",
                   priority=3, estimated_minutes=60, dependencies=["T03"]),
            SubTask(id="T05", title="验证检查", description="验证结果",
                   priority=2, estimated_minutes=20, dependencies=["T04"])
        ]
    
    def _decompose_deep(self, subtask: SubTask) -> List[SubTask]:
        """深度分解"""
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
        """设置依赖"""
        for i in range(1, len(subtasks)):
            if not subtasks[i].dependencies:
                if subtasks[i].priority <= subtasks[i-1].priority:
                    subtasks[i].dependencies.append(subtasks[i-1].id)
        return subtasks
    
    def _suggest_tools(self, task_title: str) -> List[str]:
        """建议工具"""
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
        
        return suggested[:3]
    
    def _extract_title(self, description: str) -> str:
        """提取标题"""
        return description[:40].strip() if len(description) > 40 else description.strip()
    
    def update_task_status(self, plan_id: str, task_id: str,
                          status: str, notes: str = "") -> bool:
        """更新任务状态"""
        plan = self.plans.get(plan_id)
        if not plan:
            return False
        
        for subtask in plan.subtasks:
            if subtask.id == task_id:
                subtask.status = status
                subtask.notes = notes
                if status == "completed":
                    subtask.completed_at = datetime.now().isoformat()
                    plan.completed_subtasks += 1
                break
        
        if plan.completed_subtasks == len(plan.subtasks):
            plan.status = "completed"
        elif plan.completed_subtasks > 0:
            plan.status = "in_progress"
        
        self._save_plan(plan)
        return True
    
    def get_next_tasks(self, plan_id: str, count: int = 3) -> List[SubTask]:
        """获取接下来要执行的任务"""
        plan = self.plans.get(plan_id)
        if not plan:
            return []
        
        executable = []
        for subtask in plan.subtasks:
            if subtask.status == "pending":
                deps_satisfied = all(
                    any(s.id == dep and s.status == "completed" for s in plan.subtasks)
                    for dep in subtask.dependencies
                )
                if deps_satisfied:
                    executable.append(subtask)
        
        executable.sort(key=lambda x: x.priority, reverse=True)
        return executable[:count]
    
    def _load_plans(self):
        """加载计划"""
        for plan_file in PLANS_DIR.glob("plan_*.json"):
            try:
                with open(plan_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    plan = ExecutionPlan.from_dict(data)
                    self.plans[plan.id] = plan
            except:
                continue
    
    def _save_plan(self, plan: ExecutionPlan):
        """保存计划"""
        plan_file = PLANS_DIR / f"plan_{plan.id}.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)


# ============================================================================
# CLI 命令定义
# ============================================================================

@command(CommandMetadata(
    name="task.create",
    description="创建执行计划",
    category="task",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class TaskCreateCommand:
    """创建计划"""
    
    description = arg("description", ArgumentType.STRING, help="任务描述")
    depth = opt("depth", ArgumentType.STRING, default="standard",
                help="分解深度: standard, deep")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        decomposer = TaskDecomposer()
        plan = decomposer.decompose(
            ctx.args.get("description", ""),
            ctx.options.get("depth", "standard")
        )
        
        # 保存到 session
        plans = ctx.session.get("plans", {})
        plans[plan.id] = plan.to_dict()
        ctx.session.set("plans", plans)
        ctx.session.set("active_plan", plan.id)
        
        return CommandResult(
            success=True,
            message=f"创建计划: {plan.id}",
            data=plan.to_dict()
        )


@command(CommandMetadata(
    name="task.list",
    description="列出所有计划",
    category="task",
    modifies_state=False,
    requires_session=True
))
class TaskListCommand:
    """列出计划"""
    
    status = opt("status", ArgumentType.STRING, default=None,
                 help="按状态过滤")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        decomposer = TaskDecomposer()
        status_filter = ctx.options.get("status")
        
        plans = []
        for plan_id, plan in decomposer.plans.items():
            if status_filter and plan.status != status_filter:
                continue
            progress = plan.completed_subtasks / len(plan.subtasks) * 100 if plan.subtasks else 0
            plans.append({
                "id": plan_id,
                "title": plan.title[:40],
                "status": plan.status,
                "progress": f"{progress:.0f}%",
                "total_tasks": len(plan.subtasks)
            })
        
        return CommandResult(
            success=True,
            data={"plans": plans, "count": len(plans)}
        )


@command(CommandMetadata(
    name="task.show",
    description="显示计划详情",
    category="task",
    modifies_state=False,
    requires_session=True
))
class TaskShowCommand:
    """显示详情"""
    
    plan_id = arg("plan_id", ArgumentType.STRING, help="计划ID")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        decomposer = TaskDecomposer()
        plan_id = ctx.args.get("plan_id", "")
        plan = decomposer.plans.get(plan_id)
        
        if not plan:
            return CommandResult(
                success=False,
                error=f"未找到计划: {plan_id}"
            )
        
        return CommandResult(
            success=True,
            data=plan.to_dict()
        )


@command(CommandMetadata(
    name="task.update",
    description="更新任务状态",
    category="task",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class TaskUpdateCommand:
    """更新状态"""
    
    plan_id = arg("plan_id", ArgumentType.STRING, help="计划ID")
    task_id = arg("task_id", ArgumentType.STRING, help="任务ID")
    status = arg("status", ArgumentType.STRING, help="新状态")
    notes = opt("notes", ArgumentType.STRING, default="", help="备注")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        decomposer = TaskDecomposer()
        success = decomposer.update_task_status(
            ctx.args.get("plan_id", ""),
            ctx.args.get("task_id", ""),
            ctx.args.get("status", ""),
            ctx.options.get("notes", "")
        )
        
        if success:
            return CommandResult(
                success=True,
                message=f"已更新任务状态"
            )
        else:
            return CommandResult(
                success=False,
                error="未找到计划或任务"
            )


@command(CommandMetadata(
    name="task.next",
    description="获取接下来要执行的任务",
    category="task",
    modifies_state=False,
    requires_session=True
))
class TaskNextCommand:
    """获取下一个任务"""
    
    plan_id = arg("plan_id", ArgumentType.STRING, help="计划ID")
    count = opt("count", ArgumentType.INTEGER, default=3, help="数量")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        decomposer = TaskDecomposer()
        tasks = decomposer.get_next_tasks(
            ctx.args.get("plan_id", ""),
            int(ctx.options.get("count", 3))
        )
        
        return CommandResult(
            success=True,
            data={
                "tasks": [
                    {"id": t.id, "title": t.title, "priority": t.priority}
                    for t in tasks
                ],
                "count": len(tasks)
            }
        )


@command(CommandMetadata(
    name="task.delete",
    description="删除计划",
    category="task",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class TaskDeleteCommand:
    """删除计划"""
    
    plan_id = arg("plan_id", ArgumentType.STRING, help="计划ID")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        plan_id = ctx.args.get("plan_id", "")
        plan_file = PLANS_DIR / f"plan_{plan_id}.json"
        
        if plan_file.exists():
            plan_file.unlink()
            return CommandResult(
                success=True,
                message=f"已删除计划: {plan_id}"
            )
        else:
            return CommandResult(
                success=False,
                error=f"未找到计划: {plan_id}"
            )


# ============================================================================
# REPL 入口
# ============================================================================

def create_task_skill():
    """创建 Task Skill 注册表"""
    registry = CommandRegistry()
    
    registry.register(TaskCreateCommand)
    registry.register(TaskListCommand)
    registry.register(TaskShowCommand)
    registry.register(TaskUpdateCommand)
    registry.register(TaskNextCommand)
    registry.register(TaskDeleteCommand)
    
    return registry


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Task Decomposition Skill")
    parser.add_argument("--interactive", "-i", action="store_true", help="REPL模式")
    parser.add_argument("command", nargs="?", help="命令")
    parser.add_argument("args", nargs="*", help="参数")
    
    args = parser.parse_args()
    
    registry = create_task_skill()
    session_manager = SessionManager()
    
    if args.interactive or not args.command:
        print("📋 Task Decomposition Skill")
        print("命令: task.create, task.list, task.show, task.update, task.next, task.delete")
        print("其他: session.create, undo, redo, help, exit\n")
        
        repl = ReplSkin(registry, session_manager)
        repl.run()
    else:
        print("使用 --interactive 启动 REPL 模式")


if __name__ == "__main__":
    main()
