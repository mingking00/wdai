"""
wdai v3.0 - TODO Planner
Phase 3: Agent专业化系统 - TODO规划系统

实现Claude Code风格的TODO-based规划
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from .models import (
    Task, SubTask, TodoItem, TodoPlan, TodoStatus,
    AgentRole, TaskStatus
)

logger = logging.getLogger(__name__)


class TodoPlanner:
    """
    TODO规划器
    
    负责将任务分解为可执行的TODO列表
    """
    
    def __init__(self):
        self._plans: Dict[str, TodoPlan] = {}
    
    def create_plan(self, task: Task, subtasks: List[SubTask]) -> TodoPlan:
        """
        为任务创建TODO计划
        
        Args:
            task: 父任务
            subtasks: 子任务列表
            
        Returns:
            TODO计划
        """
        todos = []
        subtask_to_todo: Dict[str, str] = {}  # subtask_id -> todo_id
        
        # 第一遍：创建所有TODO并建立映射
        for subtask in subtasks:
            # 根据子任务类型确定Agent角色
            agent_role = self._determine_agent_role(subtask)
            
            # 估算时间
            estimated_minutes = self._estimate_effort(subtask)
            
            todo = TodoItem(
                description=subtask.description,
                assigned_agent=agent_role,
                subtask_id=subtask.id,
                dependencies=[],  # 暂时为空，第二遍再设置
                estimated_minutes=estimated_minutes
            )
            
            todos.append(todo)
            subtask_to_todo[subtask.id] = todo.id
            
            # 关联subtask到todo
            subtask.assigned_to = agent_role
        
        # 第二遍：设置依赖关系
        for i, subtask in enumerate(subtasks):
            if subtask.dependencies:
                # 将subtask的依赖转换为todo的依赖
                todo_deps = [
                    subtask_to_todo[dep_id] 
                    for dep_id in subtask.dependencies 
                    if dep_id in subtask_to_todo
                ]
                todos[i].dependencies = todo_deps
        
        plan = TodoPlan(task_id=task.id, todos=todos)
        self._plans[task.id] = plan
        
        logger.info(f"为任务 {task.id} 创建了包含 {len(todos)} 个TODO的计划")
        return plan
    
    def _determine_agent_role(self, subtask: SubTask) -> Optional[AgentRole]:
        """
        根据子任务类型确定Agent角色
        
        映射规则:
        - implement/develop -> CODER
        - review -> REVIEWER
        - debug/fix -> DEBUGGER
        - design/architect -> ARCHITECT
        - test -> TESTER
        - document/doc -> DOC_WRITER
        """
        task_type = subtask.type.lower()
        
        mapping = {
            # 代码实现
            "implement": AgentRole.CODER,
            "develop": AgentRole.CODER,
            "code": AgentRole.CODER,
            "write": AgentRole.CODER,
            
            # 代码审查
            "review": AgentRole.REVIEWER,
            "check": AgentRole.REVIEWER,
            "audit": AgentRole.REVIEWER,
            
            # 调试
            "debug": AgentRole.DEBUGGER,
            "fix": AgentRole.DEBUGGER,
            "troubleshoot": AgentRole.DEBUGGER,
            "investigate": AgentRole.DEBUGGER,
            
            # 架构
            "design": AgentRole.ARCHITECT,
            "architect": AgentRole.ARCHITECT,
            "plan": AgentRole.ARCHITECT,
            
            # 测试
            "test": AgentRole.TESTER,
            "verify": AgentRole.TESTER,
            "validate": AgentRole.TESTER,
            
            # 文档
            "document": AgentRole.DOC_WRITER,
            "doc": AgentRole.DOC_WRITER,
            "explain": AgentRole.DOC_WRITER
        }
        
        return mapping.get(task_type, AgentRole.CODER)
    
    def _estimate_effort(self, subtask: SubTask) -> int:
        """
        估算任务工作量（分钟）
        
        基于任务类型和描述长度简单估算
        """
        base_effort = {
            "implement": 30,
            "develop": 30,
            "code": 30,
            "review": 15,
            "check": 15,
            "debug": 20,
            "fix": 20,
            "design": 25,
            "architect": 25,
            "test": 15,
            "verify": 15,
            "document": 20,
            "doc": 20
        }
        
        task_type = subtask.type.lower()
        base = base_effort.get(task_type, 20)
        
        # 根据描述长度调整
        desc_length = len(subtask.description)
        if desc_length > 200:
            base += 15
        elif desc_length > 100:
            base += 10
        
        # 根据依赖数量调整
        if len(subtask.dependencies) > 2:
            base += 10
        
        return min(base, 120)  # 最大2小时
    
    def get_plan(self, task_id: str) -> Optional[TodoPlan]:
        """获取计划"""
        return self._plans.get(task_id)
    
    def get_next_todo(self, task_id: str) -> Optional[TodoItem]:
        """
        获取下一个可执行的TODO
        
        返回第一个未阻塞且未完成的TODO
        """
        plan = self._plans.get(task_id)
        if not plan:
            return None
        
        completed_ids = {
            t.id for t in plan.todos 
            if t.status == TodoStatus.COMPLETED
        }
        
        for todo in plan.todos:
            if todo.status == TodoStatus.PENDING:
                # 检查依赖
                if not todo.is_blocked(completed_ids):
                    return todo
            elif todo.status == TodoStatus.RUNNING:
                return todo
        
        return None
    
    def update_todo_status(
        self,
        task_id: str,
        todo_id: str,
        status: TodoStatus,
        notes: str = ""
    ) -> bool:
        """更新TODO状态"""
        plan = self._plans.get(task_id)
        if not plan:
            return False
        
        for todo in plan.todos:
            if todo.id == todo_id:
                if status == TodoStatus.RUNNING:
                    todo.mark_started()
                elif status == TodoStatus.COMPLETED:
                    todo.mark_completed(notes)
                elif status == TodoStatus.FAILED:
                    todo.mark_failed(notes)
                else:
                    todo.status = status
                    todo.notes = notes
                
                logger.debug(f"TODO {todo_id} 状态更新为 {status.value}")
                return True
        
        return False
    
    def get_progress(self, task_id: str) -> Dict[str, Any]:
        """获取任务进度"""
        plan = self._plans.get(task_id)
        if not plan:
            return {"total": 0, "completed": 0, "percentage": 0}
        
        return plan.get_progress()
    
    def is_complete(self, task_id: str) -> bool:
        """检查是否全部完成"""
        plan = self._plans.get(task_id)
        if not plan:
            return True
        return plan.is_complete()
    
    def generate_report(self, task_id: str) -> str:
        """生成执行报告"""
        plan = self._plans.get(task_id)
        if not plan:
            return "未找到执行计划"
        
        progress = plan.get_progress()
        
        lines = [
            f"执行进度: {progress['completed']}/{progress['total']} ({progress['percentage']}%)",
            "",
            "TODO列表:"
        ]
        
        for i, todo in enumerate(plan.todos, 1):
            status_icon = {
                TodoStatus.PENDING: "⏳",
                TodoStatus.BLOCKED: "🚫",
                TodoStatus.RUNNING: "▶️",
                TodoStatus.COMPLETED: "✅",
                TodoStatus.FAILED: "❌",
                TodoStatus.SKIPPED: "⏭️"
            }.get(todo.status, "⏳")
            
            agent_name = todo.assigned_agent.value if todo.assigned_agent else "未分配"
            
            lines.append(f"  {i}. {status_icon} [{agent_name}] {todo.description}")
            
            if todo.notes:
                lines.append(f"      备注: {todo.notes}")
        
        return "\n".join(lines)
    
    def adjust_plan(
        self,
        task_id: str,
        new_todos: List[TodoItem],
        insert_after: Optional[str] = None
    ) -> bool:
        """
        动态调整计划
        
        Args:
            task_id: 任务ID
            new_todos: 新的TODO列表
            insert_after: 插入位置（某个TODO ID之后）
        """
        plan = self._plans.get(task_id)
        if not plan:
            return False
        
        if insert_after:
            # 找到插入位置
            for i, todo in enumerate(plan.todos):
                if todo.id == insert_after:
                    plan.todos[i+1:i+1] = new_todos
                    break
        else:
            # 添加到末尾
            plan.todos.extend(new_todos)
        
        logger.info(f"任务 {task_id} 的计划已调整，新增 {len(new_todos)} 个TODO")
        return True


class SimpleTodoPlanner(TodoPlanner):
    """简化版TODO规划器"""
    
    def create_simple_plan(self, task: Task, steps: List[str]) -> TodoPlan:
        """
        从简单步骤列表创建计划
        
        Args:
            task: 任务
            steps: 步骤描述列表
            
        Returns:
            TODO计划
        """
        subtasks = []
        for i, step_desc in enumerate(steps):
            subtask = SubTask(
                id=f"step_{i}",
                parent_id=task.id,
                description=step_desc,
                type="custom"
            )
            subtasks.append(subtask)
        
        return self.create_plan(task, subtasks)


# 便捷函数
def create_planner() -> TodoPlanner:
    """创建TODO规划器"""
    return TodoPlanner()
