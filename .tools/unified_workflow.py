#!/usr/bin/env python3
"""
Unified Workflow System - Mitchell + GSD + Infinite Tasks

三层工作流的完美融合:
- Layer 1: Mitchell's 16-Session Methodology (High-level project flow)
- Layer 2: GSD Phase Management (Structured project execution)
- Layer 3: Infinite Task System (Daily task management)

融合哲学:
- 大项目用GSD Phase结构化
- 每个Phase内的任务用无限任务系统管理
- Mitchell方法论指导整个流程
"""

from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set, Union
from enum import Enum
import json

# ==================== Enums ====================

class SessionType(Enum):
    """Mitchell方法论: 5种会话类型"""
    PLANNING = "planning"           # Consult the oracle
    PROTOTYPING = "prototyping"     # 快速原型探索
    CLEANUP = "cleanup"             # Anti-Slop
    REVIEW = "review"               # Consult oracle, no code
    BREAKTHROUGH = "breakthrough"   # 人工研究

class TaskStatus(Enum):
    """无限任务系统: 6层状态"""
    INBOX = "inbox"
    BACKLOG = "backlog"
    TODAY = "today"
    IN_PROGRESS = "progress"
    WAITING = "waiting"
    DONE = "done"

class Priority(Enum):
    """优先级"""
    P0 = "🔴 P0"
    P1 = "🟠 P1"
    P2 = "🟡 P2"
    P3 = "🟢 P3"
    ICEBOX = "⚪ Icebox"

# ==================== Data Models ====================

@dataclass
class MitchellSession:
    """Mitchell Session记录"""
    session_id: str
    session_type: SessionType
    goal: str
    learnings: str
    next_steps: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    gsd_phase_ref: Optional[str] = None  # 关联到GSD Phase

@dataclass
class GSDPhase:
    """GSD Phase - 项目的一个阶段"""
    phase_id: str
    phase_num: int
    title: str
    goal: str
    status: str = "planning"  # planning/executing/verifying/completed
    
    # Mitchell集成
    planning_session: Optional[str] = None
    review_session: Optional[str] = None
    
    # 任务管理
    task_ids: List[str] = field(default_factory=list)
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

@dataclass
class Task:
    """无限任务系统中的任务"""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.INBOX
    priority: Priority = Priority.P2
    
    # GSD关联
    gsd_phase_id: Optional[str] = None
    
    # Mitchell关联 - 这个任务属于哪个Session
    mitchell_session_id: Optional[str] = None
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: Set[str] = field(default_factory=set)
    estimated_minutes: int = 0

@dataclass
class UnifiedProject:
    """统一项目 - 融合三层工作流"""
    project_id: str
    name: str
    description: str
    
    # GSD结构
    gsd_phases: Dict[str, GSDPhase] = field(default_factory=dict)
    current_phase: int = 0
    
    # Mitchell记录
    mitchell_sessions: Dict[str, MitchellSession] = field(default_factory=dict)
    
    # 无限任务
    tasks: Dict[str, Task] = field(default_factory=dict)
    
    # 状态
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class UnifiedWorkflow:
    """
    统一工作流系统
    
    融合三层:
    1. Mitchell方法论 - 指导整体流程
    2. GSD Phase - 结构化项目阶段
    3. 无限任务 - 日常任务管理
    """
    
    def __init__(self, base_dir: str = ".learning/unified-workflow"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.projects: Dict[str, UnifiedProject] = {}
        self.current_project: Optional[str] = None
        
        self.focus_limit = 3
    
    # ==================== Layer 1: Mitchell Methodology ====================
    
    def start_mitchell_session(self, session_type: SessionType, goal: str, 
                               gsd_phase_id: Optional[str] = None) -> str:
        """
        启动Mitchell会话
        
        这是最高层的方法论，指导整个工作流
        """
        session_id = f"mitchell-{session_type.value}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        session = MitchellSession(
            session_id=session_id,
            session_type=session_type,
            goal=goal,
            learnings="",
            next_steps="",
            gsd_phase_ref=gsd_phase_id
        )
        
        if self.current_project:
            self.projects[self.current_project].mitchell_sessions[session_id] = session
        
        prompts = {
            SessionType.PLANNING: """
🎯 **Mitchell Planning Session**

**Goal**: {goal}

**Guidelines**:
1. Don't write code yet
2. Consult the oracle (deep reasoning)
3. Create comprehensive plan
4. Save to spec.md

**Questions to answer**:
- What's the core problem?
- What are the constraints?
- How do we verify success?
- What's the minimum viable scope?

**Output**: Planning document, not code
""",
            SessionType.PROTOTYPING: """
🔬 **Mitchell Prototyping Session**

**Goal**: {goal}

**Guidelines**:
1. Quick exploration, not perfection
2. Multiple prototypes if needed
3. Use AI as muse for inspiration
4. May throw away code

**Focus**: Direction over perfection
""",
            SessionType.CLEANUP: """
🧹 **Mitchell Anti-Slop Session**

**Goal**: {goal}

**Guidelines** (Critical!):
1. Review every line of AI-generated code
2. Refactor for clarity
3. Rename variables/functions
4. Add documentation
5. Ensure you understand everything

**Mitchell says**: 
"The cleanup step is really important. To cleanup effectively 
you have to have a pretty good understanding of the code, 
so this forces me to not blindly accept AI-written code."

**Output**: Cleaner, better-organized code
""",
            SessionType.REVIEW: """
👁️ **Mitchell Review Session**

**Goal**: {goal}

**Guidelines**:
1. Don't write any code
2. Consult the oracle for deep analysis
3. Identify improvements
4. Check for missing tests

**Prompt template**:
"Are there any other improvements you can see?
Don't write any code. Consult the oracle.
Consider parts that can get more unit tests added."
""",
            SessionType.BREAKTHROUGH: """
💡 **Mitchell Breakthrough Session**

**Goal**: {goal}

**⚠️ Critical**: AI is no longer the solution; it is a liability

**Steps**:
1. Stop using AI for this problem
2. Step back and review
3. Educate yourself
4. Think critically
5. Manual research
6. Come back with understanding

**Mitchell says**:
"It's at this point that I know I need to step back, 
review what it did, and come up with my own plans."
"""
        }
        
        return prompts.get(session_type, "").format(goal=goal)
    
    # ==================== Layer 2: GSD Phase Management ====================
    
    def create_gsd_phase(self, phase_num: int, title: str, goal: str) -> str:
        """
        创建GSD Phase
        
        每个Phase是项目的一个结构化阶段
        """
        phase_id = f"gsd-phase-{phase_num}"
        
        phase = GSDPhase(
            phase_id=phase_id,
            phase_num=phase_num,
            title=title,
            goal=goal
        )
        
        if self.current_project:
            self.projects[self.current_project].gsd_phases[phase_id] = phase
        
        return f"""
📦 **GSD Phase {phase_num} Created**: {title}

**Goal**: {goal}

**Flow**:
1. `/gsd:discuss-phase {phase_num}` - Discuss details
2. `/gsd:plan-phase {phase_num}` - Create task breakdown (max 3)
3. `/gsd:execute-phase {phase_num}` - Execute with fresh context
4. `/gsd:verify-phase {phase_num}` - Quality gates
5. `/gsd:complete-phase {phase_num}` - Move to next

**Note**: Each phase maps to Mitchell sessions
- Planning → Mitchell Planning Session
- Execution → May include Prototyping/Cleanup
- Verification → Mitchell Review Session
"""
    
    def gsd_execute_phase(self, phase_id: str) -> str:
        """
        执行GSD Phase
        
        核心特性: 每个任务在独立子agent中执行，防止context rot
        """
        if not self.current_project:
            return "❌ No active project"
        
        project = self.projects[self.current_project]
        phase = project.gsd_phases.get(phase_id)
        
        if not phase:
            return f"❌ Phase {phase_id} not found"
        
        # 获取这个Phase的任务
        phase_tasks = [project.tasks[tid] for tid in phase.task_ids 
                      if tid in project.tasks]
        
        # GSD规则: 每个Phase最多3个主要任务
        main_tasks = phase_tasks[:3]
        
        execution_plan = f"""
⚙️ **GSD Execute Phase {phase.phase_num}**: {phase.title}

**Strategy**: Process isolation (prevents context rot)

---

**Task Distribution**:

"""
        for i, task in enumerate(main_tasks, 1):
            execution_plan += f"""
🔧 **Task {i}**: {task.title}
```
[Subagent {i} - Fresh 200K Context]
├─ Input: Task requirements
├─ Context: Clean slate, no pollution
├─ Execution: Independent processing
├─ Output: Completed task + commit
└─ Parent receives: Summary only
```
Status: 🟡 Ready to execute
"""
        
        execution_plan += f"""
---

**Mitchell Integration**:
- Before execution: Anti-Slop review of plan
- During execution: Monitor for Breakthrough signals
- After execution: Cleanup session

**Next**: Run `verify_phase("{phase_id}")` after completion
"""
        
        return execution_plan
    
    # ==================== Layer 3: Infinite Task System ====================
    
    def capture_task(self, title: str, description: str = "",
                     gsd_phase_id: Optional[str] = None,
                     mitchell_session_id: Optional[str] = None) -> str:
        """
        捕获任务到无限任务池
        
        自动关联到GSD Phase和Mitchell Session
        """
        if not self.current_project:
            return "❌ No active project. Create one first."
        
        project = self.projects[self.current_project]
        
        # 生成任务ID
        import hashlib
        task_id = hashlib.md5(f"{title}{datetime.now()}".encode()).hexdigest()[:8]
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.INBOX,
            gsd_phase_id=gsd_phase_id,
            mitchell_session_id=mitchell_session_id
        )
        
        project.tasks[task_id] = task
        
        # 如果指定了GSD Phase，添加到Phase的任务列表
        if gsd_phase_id and gsd_phase_id in project.gsd_phases:
            project.gsd_phases[gsd_phase_id].task_ids.append(task_id)
        
        return f"""
📥 **Task Captured**: {title}

**ID**: `{task_id}`
**Status**: 🟡 Inbox
**GSD Phase**: {gsd_phase_id or "None (orphan task)"}
**Mitchell Session**: {mitchell_session_id or "None"}

**Total Tasks in Project**: {len(project.tasks)}

💡 **Next Steps**:
1. `process_inbox()` - Categorize and prioritize
2. `smart_today()` - Select today's tasks
3. `focus_mode()` - Start focused work
"""
    
    def smart_today(self, max_tasks: int = 5) -> str:
        """
        智能选择今天的任务
        
        算法考虑:
        - 优先级 (GSD Phase的P0任务优先)
        - 当前激活的GSD Phase
        - Mitchell Session的状态
        - 任务年龄
        """
        if not self.current_project:
            return "❌ No active project"
        
        project = self.projects[self.current_project]
        
        # 候选任务
        candidates = []
        for task in project.tasks.values():
            if task.status in [TaskStatus.BACKLOG, TaskStatus.TODAY, TaskStatus.INBOX]:
                # 计算分数
                score = 0
                
                # GSD Phase优先级
                if task.gsd_phase_id:
                    phase = project.gsd_phases.get(task.gsd_phase_id)
                    if phase:
                        # 当前激活的Phase优先
                        if phase.status == "executing":
                            score += 100
                        # 低phase_num优先
                        score += (10 - phase.phase_num) * 10
                
                # Mitchell Session关联
                if task.mitchell_session_id:
                    session = project.mitchell_sessions.get(task.mitchell_session_id)
                    if session:
                        if session.session_type == SessionType.CLEANUP:
                            score += 50  # Cleanup任务重要
                
                # 任务年龄
                created = datetime.fromisoformat(task.created_at)
                age_days = (datetime.now() - created).days
                score += min(age_days * 2, 20)
                
                candidates.append((task, score))
        
        # 排序选择
        candidates.sort(key=lambda x: x[1], reverse=True)
        selected = candidates[:max_tasks]
        
        # 更新状态
        for task, _ in selected:
            task.status = TaskStatus.TODAY
        
        # 生成报告
        report = f"""
🎯 **Smart Today Selection** (Layer 3: Infinite Tasks)

Selected {len(selected)} tasks based on:
- GSD Phase priority
- Mitchell session type
- Task age
- Current project focus

---

**Today's Tasks**:

"""
        for i, (task, score) in enumerate(selected, 1):
            phase_info = ""
            if task.gsd_phase_id and task.gsd_phase_id in project.gsd_phases:
                phase = project.gsd_phases[task.gsd_phase_id]
                phase_info = f" [GSD Phase {phase.phase_num}]"
            
            report += f"""
{i}. **{task.title}**{phase_info}
   Score: {score} | Status: ⭐ TODAY
"""
        
        report += f"""
---

💡 **Next**: Run `focus_mode()` to start working on these
"""
        
        return report
    
    def focus_mode(self) -> str:
        """
        Focus Mode - 限制并发，深度工作
        
        结合三层工作流的信息:
        - 显示当前Mitchell Session
        - 显示所属的GSD Phase
        - 显示任务详情
        """
        if not self.current_project:
            return "❌ No active project"
        
        project = self.projects[self.current_project]
        
        # 获取进行中的任务
        active_tasks = [t for t in project.tasks.values() 
                       if t.status == TaskStatus.IN_PROGRESS][:self.focus_limit]
        
        # 从TODAY补充到FOCUS
        today_tasks = [t for t in project.tasks.values() 
                      if t.status == TaskStatus.TODAY]
        
        slots_available = self.focus_limit - len(active_tasks)
        for task in today_tasks[:slots_available]:
            task.status = TaskStatus.IN_PROGRESS
            active_tasks.append(task)
        
        # 构建Focus视图
        focus_view = f"""
🎯 **UNIFIED FOCUS MODE**
   (Layer 1 + 2 + 3 Combined)

{'=' * 70}
**ACTIVE CONTEXT**
{'=' * 70}

Project: {project.name}
Current GSD Phase: Phase {project.current_phase}
Focus Slots: {len(active_tasks)}/{self.focus_limit}

{'=' * 70}
**FOCUS TASKS** (Max {self.focus_limit})
{'=' * 70}

"""
        for i, task in enumerate(active_tasks, 1):
            # 获取关联信息
            phase_info = ""
            if task.gsd_phase_id and task.gsd_phase_id in project.gsd_phases:
                phase = project.gsd_phases[task.gsd_phase_id]
                phase_info = f"\n   └─ GSD Phase: {phase.title}"
            
            mitchell_info = ""
            if task.mitchell_session_id and task.mitchell_session_id in project.mitchell_sessions:
                session = project.mitchell_sessions[task.mitchell_session_id]
                mitchell_info = f"\n   └─ Mitchell: {session.session_type.value}"
            
            focus_view += f"""
┌{'─' * 68}┐
│ #{i} {task.title[:60]:<60} │
│    Status: 🟢 IN_PROGRESS{' ':43} │
│    Started: {datetime.now().strftime('%H:%M'):<54} │{phase_info}{mitchell_info}
└{'─' * 68}┘
"""
        
        focus_view += f"""
{'=' * 70}
**WAITING QUEUE**
{'=' * 70}

"""
        # 显示等待队列
        waiting = [t for t in project.tasks.values() 
                  if t.status == TaskStatus.TODAY][self.focus_limit:]
        for task in waiting[:5]:
            focus_view += f"  ⏳ {task.title}\n"
        
        focus_view += f"""
{'=' * 70}
**COMMANDS**
{'=' * 70}

Task Management:
  • complete("TASK_ID")     - Complete task, get next
  • park("TASK_ID")         - Park task to waiting
  • next_focus()            - Start next task

Workflow Navigation:
  • current_phase()         - Show GSD Phase details
  • mitchell_status()       - Show Mitchell sessions
  • project_dashboard()     - Full project overview

{'=' * 70}
💡 **Rule**: Complete one to start next. Stay focused!
"""
        
        return focus_view
    
    # ==================== Integration Layer ====================
    
    def unified_dashboard(self) -> str:
        """
        统一仪表板 - 显示三层工作流的全貌
        """
        if not self.current_project:
            return "❌ No active project"
        
        project = self.projects[self.current_project]
        
        # 统计
        total_tasks = len(project.tasks)
        done_tasks = len([t for t in project.tasks.values() if t.status == TaskStatus.DONE])
        completion_rate = (done_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        dashboard = f"""
╔{'═' * 68}╗
║{'UNIFIED WORKFLOW DASHBOARD':^68}║
║{'Mitchell + GSD + Infinite Tasks':^68}║
╚{'═' * 68}╝

📊 **PROJECT OVERVIEW**
   Name: {project.name}
   Created: {project.created_at[:10]}
   Completion: {completion_rate:.1f}%

╔{'═' * 68}╗
║ LAYER 1: MITCHELL METHODOLOGY{' ':33}║
╠{'═' * 68}╣
"""
        
        # Mitchell Sessions
        for session_type in SessionType:
            count = len([s for s in project.mitchell_sessions.values() 
                        if s.session_type == session_type])
            dashboard += f"║  {session_type.value.upper():12} : {count} sessions{' ':42}║\n"
        
        dashboard += f"""╠{'═' * 68}╣
║ LAYER 2: GSD PHASE MANAGEMENT{' ':33}║
╠{'═' * 68}╣
"""
        
        # GSD Phases
        for phase_id, phase in sorted(project.gsd_phases.items(), 
                                      key=lambda x: x[1].phase_num):
            status_icon = {"planning": "🟡", "executing": "🟢", 
                          "verifying": "🔵", "completed": "✅"}.get(phase.status, "⚪")
            task_count = len(phase.task_ids)
            dashboard += f"║  Phase {phase.phase_num}: {phase.title[:40]:<40} {status_icon} {task_count} tasks{' ':4}║\n"
        
        dashboard += f"""╠{'═' * 68}╣
║ LAYER 3: INFINITE TASK SYSTEM{' ':33}║
╠{'═' * 68}╣
"""
        
        # Task stats
        for status in TaskStatus:
            count = len([t for t in project.tasks.values() if t.status == status])
            dashboard += f"║  {status.value.upper():12} : {count:3} tasks{' ':47}║\n"
        
        dashboard += f"""╚{'═' * 68}╝

🎮 **QUICK ACTIONS**

Project Management:
  • create_project("Name", "Description")  - New unified project
  • switch_project("ID")                   - Switch context
  • unified_dashboard()                    - This view

Layer 1 (Mitchell):
  • start_planning("Goal")                 - Consult the oracle
  • start_cleanup("Goal")                  - Anti-Slop session
  • start_review("Goal")                   - Review without code

Layer 2 (GSD):
  • create_gsd_phase(N, "Title", "Goal")   - Create phase
  • gsd_execute_phase("phase-id")          - Execute phase
  • verify_phase("phase-id")               - Quality gates

Layer 3 (Tasks):
  • capture_task("Title")                  - Capture idea
  • smart_today()                          - Select today's tasks
  • focus_mode()                           - Start deep work

💡 **Workflow**: Mitchell guides → GSD structures → Tasks execute
"""
        
        return dashboard


def demo_unified_workflow():
    """
    演示完整的统一工作流
    """
    print("=" * 70)
    print("🚀 Unified Workflow Demo")
    print("   Mitchell Methodology + GSD + Infinite Tasks")
    print("=" * 70)
    
    workflow = UnifiedWorkflow()
    
    # 1. 创建项目
    print("\n📦 STEP 1: Create Unified Project")
    print("-" * 70)
    
    project = UnifiedProject(
        project_id="proj-001",
        name="AI Assistant Self-Improvement",
        description="系统性改进AI助手的核心能力"
    )
    workflow.projects["proj-001"] = project
    workflow.current_project = "proj-001"
    
    print(f"✅ Project created: {project.name}")
    
    # 2. Mitchell Planning Session
    print("\n🎯 STEP 2: Mitchell Planning Session")
    print("-" * 70)
    
    planning = workflow.start_mitchell_session(
        SessionType.PLANNING,
        "设计无限任务与GSD的集成架构",
        gsd_phase_id="gsd-phase-1"
    )
    print(planning[:500] + "...")
    
    # 3. 创建GSD Phase
    print("\n📦 STEP 3: Create GSD Phase")
    print("-" * 70)
    
    phase1 = workflow.create_gsd_phase(
        1,
        "架构设计与规划",
        "设计三层工作流的集成架构"
    )
    print(phase1)
    
    # 4. 捕获无限任务
    print("\n📥 STEP 4: Capture Infinite Tasks")
    print("-" * 70)
    
    tasks = [
        ("研究Mitchell的16-session方法论", "gsd-phase-1"),
        ("分析GSD的核心机制", "gsd-phase-1"),
        ("设计无限任务系统架构", "gsd-phase-1"),
        ("实现任务捕获功能", "gsd-phase-1"),
        ("实现智能优先级算法", "gsd-phase-1"),
        ("集成三层工作流", "gsd-phase-1"),
        ("编写文档和示例", "gsd-phase-1"),
        ("Anti-Slop清理代码", "gsd-phase-1"),
    ]
    
    for title, phase_id in tasks:
        result = workflow.capture_task(title, gsd_phase_id=phase_id)
        print(f"  ✓ {title}")
    
    print(f"\n  Total tasks captured: {len(tasks)}")
    
    # 5. Smart Today
    print("\n🎯 STEP 5: Smart Today Selection")
    print("-" * 70)
    
    # 设置一些任务为BACKLOG
    for task in list(project.tasks.values())[:5]:
        task.status = TaskStatus.BACKLOG
    
    today = workflow.smart_today(max_tasks=5)
    print(today)
    
    # 6. Focus Mode
    print("\n🎯 STEP 6: Focus Mode")
    print("-" * 70)
    
    focus = workflow.focus_mode()
    print(focus)
    
    # 7. Unified Dashboard
    print("\n📊 STEP 7: Unified Dashboard")
    print("-" * 70)
    
    dashboard = workflow.unified_dashboard()
    print(dashboard)
    
    print("\n" + "=" * 70)
    print("✅ Unified Workflow Demo Complete!")
    print("=" * 70)
    print("\n🎯 Key Integration Points:")
    print("1. Mitchell Sessions guide GSD Phases")
    print("2. GSD Phases contain Infinite Tasks")
    print("3. Tasks can reference Mitchell Sessions")
    print("4. Focus Mode shows all 3 layers")
    print("5. Unified Dashboard tracks everything")


if __name__ == "__main__":
    demo_unified_workflow()
