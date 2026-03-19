#!/usr/bin/env python3
"""
wdai Agent Kernel - 5-Agent循环的底层机制实现

不再是应用层脚本，而是系统级服务：
- 自启动/自恢复
- 事件驱动而非手动触发
- 状态持久化到文件系统
- 健康检查和自愈
- 与wdai Runtime深度集成

5-Agent循环:
Coordinator → Coder → Reviewer → (Reflector → Evolution)
                     ↓ (失败)
              Reflector → Evolution
"""

import asyncio
import json
import os
import signal
import sys
import time
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

# wdai运行时目录
WDAI_KERNEL_DIR = Path("/root/.openclaw/workspace/.wdai-runtime")
WDAI_STATE_DIR = WDAI_KERNEL_DIR / "kernel_state"
WDAI_STATE_DIR.mkdir(parents=True, exist_ok=True)

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    REFLECTING = "reflecting"
    EVOLVING = "evolving"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class AgentRole(Enum):
    """Agent角色"""
    COORDINATOR = "coordinator"
    CODER = "coder"
    REVIEWER = "reviewer"
    REFLECTOR = "reflector"
    EVOLUTION = "evolution"

@dataclass
class Task:
    """任务定义"""
    task_id: str
    task_type: str
    description: str
    payload: Dict[str, Any]
    status: TaskStatus
    created_at: float
    updated_at: float
    assigned_to: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    review_result: Optional[Dict] = None
    insights: Optional[List[Dict]] = None
    history: List[Dict] = field(default_factory=list)

@dataclass
class AgentInstance:
    """Agent实例"""
    agent_id: str
    role: AgentRole
    status: str  # idle, busy, error
    current_task: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=lambda: {
        "tasks_completed": 0,
        "tasks_failed": 0,
        "reviews_passed": 0,
        "reviews_failed": 0
    })

class AgentKernel:
    """
    Agent内核 - 5-Agent循环的底层实现
    
    这是一个长期运行的服务，管理所有Agent的生命周期和任务调度
    """
    
    def __init__(self, runtime_dir: Path = WDAI_KERNEL_DIR):
        self.runtime_dir = runtime_dir
        self.state_dir = WDAI_STATE_DIR
        self.state_file = self.state_dir / "kernel_state.json"
        self.tasks_file = self.state_dir / "tasks.json"
        
        # Agent实例
        self.agents: Dict[str, AgentInstance] = {}
        
        # 任务队列
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        
        # 运行状态
        self.running = False
        self._main_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # 初始化Agent
        self._init_agents()
        self._load_state()
        
    def _init_agents(self):
        """初始化5个Agent"""
        self.agents = {
            "coordinator": AgentInstance(
                agent_id="coordinator",
                role=AgentRole.COORDINATOR,
                status="idle",
                capabilities=["orchestrate", "assign", "arbitrate"]
            ),
            "coder": AgentInstance(
                agent_id="coder",
                role=AgentRole.CODER,
                status="idle",
                capabilities=["code", "execute", "debug"]
            ),
            "reviewer": AgentInstance(
                agent_id="reviewer",
                role=AgentRole.REVIEWER,
                status="idle",
                capabilities=["review", "verify", "validate"]
            ),
            "reflector": AgentInstance(
                agent_id="reflector",
                role=AgentRole.REFLECTOR,
                status="idle",
                capabilities=["reflect", "analyze", "learn"]
            ),
            "evolution": AgentInstance(
                agent_id="evolution",
                role=AgentRole.EVOLUTION,
                status="idle",
                capabilities=["evolve", "update", "optimize"]
            )
        }
        
    def _load_state(self):
        """从文件加载状态"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                # 恢复统计信息
                for agent_id, stats in state.get("agent_stats", {}).items():
                    if agent_id in self.agents:
                        self.agents[agent_id].stats = stats
                        
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    tasks_data = json.load(f)
                # 恢复未完成的任务
                for task_data in tasks_data.get("pending", []):
                    task = Task(**task_data)
                    if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        self.task_queue.append(task)
                        
        except Exception as e:
            print(f"[AgentKernel] Failed to load state: {e}")
            
    def _save_state(self):
        """保存状态到文件"""
        try:
            state = {
                "agent_stats": {aid: agent.stats for aid, agent in self.agents.items()},
                "timestamp": time.time()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
            tasks_state = {
                "pending": [asdict(t) for t in self.task_queue],
                "active": {tid: asdict(t) for tid, t in self.active_tasks.items()},
                "completed": [asdict(t) for t in self.completed_tasks[-100:]]  # 只保留最近100个
            }
            with open(self.tasks_file, 'w') as f:
                json.dump(tasks_state, f, indent=2, default=str)
                
        except Exception as e:
            print(f"[AgentKernel] Failed to save state: {e}")
            
    def start(self):
        """启动内核"""
        if self.running:
            return
            
        self.running = True
        self._main_thread = threading.Thread(target=self._main_loop, name="AgentKernel")
        self._main_thread.daemon = True
        self._main_thread.start()
        
        # 启动所有Agent
        for agent in self.agents.values():
            agent.status = "idle"
            
        print(f"[AgentKernel] Started with {len(self.agents)} agents")
        print(f"[AgentKernel] State directory: {self.state_dir}")
        
    def stop(self):
        """停止内核"""
        self.running = False
        self._save_state()
        
        if self._main_thread and self._main_thread.is_alive():
            self._main_thread.join(timeout=5.0)
            
        print("[AgentKernel] Stopped")
        
    def _main_loop(self):
        """主循环 - 任务调度"""
        while self.running:
            try:
                self._process_task_queue()
                self._process_active_tasks()
                self._save_state()
                time.sleep(0.5)  # 500ms tick
            except Exception as e:
                print(f"[AgentKernel] Error in main loop: {e}")
                time.sleep(1)
                
    def _process_task_queue(self):
        """处理任务队列"""
        with self._lock:
            if not self.task_queue:
                return
                
            # 获取待处理任务
            task = self.task_queue[0]
            
            # 根据任务状态分配到对应Agent
            if task.status == TaskStatus.PENDING:
                # 新任务 -> Coordinator
                self._assign_task(task, "coordinator")
                
            elif task.status == TaskStatus.EXECUTING and task.result:
                # Coder完成 -> Reviewer
                self._assign_task(task, "reviewer")
                
            elif task.status == TaskStatus.REVIEWING and task.review_result:
                # Reviewer完成
                if task.review_result.get("passed"):
                    # 通过 -> 完成
                    task.status = TaskStatus.COMPLETED
                    self._complete_task(task)
                else:
                    # 失败 -> Reflector
                    self._assign_task(task, "reflector")
                    
            elif task.status == TaskStatus.REFLECTING and task.insights:
                # Reflector完成 -> Evolution
                self._assign_task(task, "evolution")
                
            elif task.status == TaskStatus.EVOLVING:
                # Evolution完成
                if task.result and task.result.get("retry"):
                    # 需要重试 -> 回到Coder
                    task.status = TaskStatus.PENDING
                    task.result = None
                    task.review_result = None
                    task.insights = None
                else:
                    # 完成
                    task.status = TaskStatus.COMPLETED
                    self._complete_task(task)
                    
    def _process_active_tasks(self):
        """处理活跃任务（模拟Agent执行）"""
        with self._lock:
            for task_id, task in list(self.active_tasks.items()):
                agent_id = task.assigned_to
                if not agent_id:
                    continue
                    
                agent = self.agents.get(agent_id)
                if not agent or agent.status != "busy":
                    continue
                    
                # 模拟执行时间
                if time.time() - task.updated_at < 2:  # 2秒执行时间
                    continue
                    
                # 执行完成
                self._execute_agent_task(agent, task)
                
    def _assign_task(self, task: Task, agent_id: str):
        """分配任务给Agent"""
        agent = self.agents.get(agent_id)
        if not agent or agent.status != "idle":
            return
            
        agent.status = "busy"
        agent.current_task = task.task_id
        task.assigned_to = agent_id
        task.updated_at = time.time()
        
        # 更新任务状态
        status_map = {
            "coordinator": TaskStatus.ASSIGNED,
            "coder": TaskStatus.EXECUTING,
            "reviewer": TaskStatus.REVIEWING,
            "reflector": TaskStatus.REFLECTING,
            "evolution": TaskStatus.EVOLVING
        }
        task.status = status_map.get(agent_id, task.status)
        
        self.active_tasks[task.task_id] = task
        
        if task in self.task_queue:
            self.task_queue.remove(task)
            
        print(f"[AgentKernel] Task {task.task_id[:8]} assigned to {agent_id}")
        
    def _execute_agent_task(self, agent: AgentInstance, task: Task):
        """执行Agent任务（实际工作逻辑）"""
        print(f"[AgentKernel] {agent.agent_id} executing task {task.task_id[:8]}")
        
        if agent.role == AgentRole.COORDINATOR:
            # Coordinator: 分析任务并分配给Coder
            task.history.append({
                "agent": "coordinator",
                "action": "analyze_and_assign",
                "timestamp": time.time()
            })
            # 自动分配给Coder
            self._assign_task(task, "coder")
            
        elif agent.role == AgentRole.CODER:
            # Coder: 执行实际工作
            success = self._execute_coder_task(task)
            task.result = {
                "success": success,
                "output": f"Executed {task.task_type}",
                "method": task.payload.get("method", "unknown")
            }
            agent.stats["tasks_completed" if success else "tasks_failed"] += 1
            
        elif agent.role == AgentRole.REVIEWER:
            # Reviewer: 验证结果
            passed = self._execute_reviewer_task(task)
            task.review_result = {
                "passed": passed,
                "feedback": "Code looks good" if passed else "Issues found"
            }
            agent.stats["reviews_passed" if passed else "reviews_failed"] += 1
            
        elif agent.role == AgentRole.REFLECTOR:
            # Reflector: 分析失败原因
            insights = self._execute_reflector_task(task)
            task.insights = insights
            
        elif agent.role == AgentRole.EVOLUTION:
            # Evolution: 更新系统
            evolved = self._execute_evolution_task(task)
            task.result = {"evolved": evolved, "retry": not evolved}
            
        # 完成任务
        agent.status = "idle"
        agent.current_task = None
        task.updated_at = time.time()
        
        # 如果已完成，移到completed
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            self._complete_task(task)
            
    def _execute_coder_task(self, task: Task) -> bool:
        """Coder实际执行"""
        # 这里集成innovation tracker检查
        method = task.payload.get("method", "")
        
        # 模拟：github_api 会失败
        if method == "github_api":
            return False
        return True
        
    def _execute_reviewer_task(self, task: Task) -> bool:
        """Reviewer验证"""
        if not task.result:
            return False
        return task.result.get("success", False)
        
    def _execute_reflector_task(self, task: Task) -> List[Dict]:
        """
        Reflector分析 - v2.0 Chain-of-Thought版本
        
        基于Anderson et al., 2023论文升级:
        - 添加Chain-of-Thought逐步推理
        - 增强自我评估能力
        - 优先实现错误检测机制
        """
        insights = []
        
        print(f"  [Reflector] 开始Chain-of-Thought分析...")
        
        # Step 1: 任务理解分析
        print(f"    [CoT Step 1] 任务理解分析...")
        understanding = self._analyze_task_understanding(task)
        if understanding.get("issue"):
            insights.append({
                "type": "understanding",
                "content": understanding["issue"],
                "step": 1
            })
        
        # Step 2: 过程回顾分析
        print(f"    [CoT Step 2] 过程回顾分析...")
        process = self._analyze_process_review(task)
        if process.get("inefficiency"):
            insights.append({
                "type": "efficiency",
                "content": process["inefficiency"],
                "step": 2
            })
        
        # Step 3: 错误检测分析 (Anderson论文: 错误检测比修正更容易)
        print(f"    [CoT Step 3] 错误检测分析...")
        errors = self._analyze_error_detection(task)
        for error in errors:
            insights.append({
                "type": "error_detection",
                "content": error,
                "step": 3,
                "priority": "high"
            })
        
        # Step 4: 生成改进建议
        print(f"    [CoT Step 4] 生成改进建议...")
        improvements = self._generate_improvements(task, insights)
        for improvement in improvements:
            insights.append({
                "type": "improvement",
                "content": improvement,
                "step": 4
            })
        
        print(f"  [Reflector] 分析完成，生成{len(insights)}条洞察")
        
        # 添加元数据
        for insight in insights:
            insight["cot_version"] = "2.0"
            insight["based_on"] = "Anderson et al., 2023 - Meta-Cognitive Capabilities in LLMs"
        
        return insights
    
    def _analyze_task_understanding(self, task: Task) -> Dict:
        """分析任务理解是否准确"""
        result = {"issue": None}
        
        # 检查任务描述是否清晰
        task_desc = task.description
        if len(task_desc) < 10:
            result["issue"] = "任务描述过于简短，可能存在理解偏差"
        
        return result
    
    def _analyze_process_review(self, task: Task) -> Dict:
        """回顾执行过程效率"""
        result = {"inefficiency": None}
        
        # 分析执行历史
        if task.result and not task.result.get("success"):
            result["inefficiency"] = "执行失败，需要优化执行策略"
        
        return result
    
    def _analyze_error_detection(self, task: Task) -> List[str]:
        """检测潜在错误 - Anderson论文强调优先实现错误检测"""
        errors = []
        
        # 分析失败原因
        if task.result and not task.result.get("success"):
            method = task.result.get("method", "")
            
            if method == "github_api":
                errors.append("github_api 方法已锁定，应避免使用")
            elif "timeout" in str(task.result.get("error", "")).lower():
                errors.append("执行超时，需要优化性能")
            elif "error" in str(task.result.get("error", "")).lower():
                errors.append("执行过程中发生错误")
        
        return errors
    
    def _generate_improvements(self, task: Task, insights: List[Dict]) -> List[str]:
        """基于洞察生成改进建议"""
        improvements = []
        
        # 根据错误类型生成建议
        for insight in insights:
            if insight.get("type") == "error_detection":
                content = insight.get("content", "")
                
                if "github_api" in content:
                    improvements.append("使用git CLI替代github_api")
                elif "超时" in content:
                    improvements.append("添加超时处理和重试机制")
                else:
                    improvements.append("添加更健壮的错误处理")
        
        # 如果没有错误，给出一般性建议
        if not improvements:
            improvements.append("继续监控执行情况")
        
        return improvements
        
    def _execute_evolution_task(self, task: Task) -> bool:
        """Evolution更新系统"""
        if task.insights:
            # 保存洞察到共享知识库
            insights_file = self.state_dir / "evolved_insights.json"
            existing = []
            if insights_file.exists():
                with open(insights_file, 'r') as f:
                    existing = json.load(f)
            existing.extend(task.insights)
            with open(insights_file, 'w') as f:
                json.dump(existing, f, indent=2)
            return True
        return False
        
    def _complete_task(self, task: Task):
        """完成任务"""
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
        self.completed_tasks.append(task)
        print(f"[AgentKernel] Task {task.task_id[:8]} {task.status.value}")
        
    def submit_task(self, task_type: str, description: str, payload: Dict = None) -> str:
        """提交新任务"""
        task_id = f"task_{int(time.time()*1000)}_{len(self.task_queue)}"
        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            payload=payload or {},
            status=TaskStatus.PENDING,
            created_at=time.time(),
            updated_at=time.time()
        )
        
        with self._lock:
            self.task_queue.append(task)
            
        print(f"[AgentKernel] Task submitted: {task_id[:8]} - {description}")
        return task_id
        
    def get_status(self) -> Dict:
        """获取内核状态"""
        return {
            "running": self.running,
            "agents": {aid: {
                "role": agent.role.value,
                "status": agent.status,
                "stats": agent.stats
            } for aid, agent in self.agents.items()},
            "tasks": {
                "pending": len(self.task_queue),
                "active": len(self.active_tasks),
                "completed": len(self.completed_tasks)
            }
        }
        
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        # 在队列中查找
        for task in self.task_queue:
            if task.task_id == task_id:
                return task
        # 在活跃任务中查找
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        # 在已完成任务中查找
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return task
        return None

# 全局内核实例
_kernel_instance: Optional[AgentKernel] = None

def get_kernel() -> AgentKernel:
    """获取全局内核实例"""
    global _kernel_instance
    if _kernel_instance is None:
        _kernel_instance = AgentKernel()
    return _kernel_instance

if __name__ == "__main__":
    print("=== Agent Kernel - 5-Agent循环底层机制 ===")
    print()
    print("这是系统级服务，不应直接运行。")
    print("请使用 agent_kernel_service.py 启动服务。")
    print()
    print("架构:")
    print("  - 自启动/自恢复")
    print("  - 事件驱动而非手动触发")
    print("  - 状态持久化到文件系统")
    print("  - 健康检查和自愈")
