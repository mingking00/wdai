#!/usr/bin/env python3
"""
wdai Agent 指挥家系统 v3.0
让多Agent真正活起来：任务驱动 + 自适应调度 + 成果沉淀

核心机制:
1. 指挥家(Coordinator)根据目标动态调度Agent
2. Agent执行后有明确成果交付
3. 基于成果质量自适应调整策略
4. 有效成果自动沉淀到MEMORY.md
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import sys

sys.path.insert(0, '/root/.openclaw/workspace/.wdai-runtime')
from zone_manager import ZoneManager
from message_bus import MessageBus

WORKSPACE = Path("/root/.openclaw/workspace")
RUNTIME_DIR = WORKSPACE / ".wdai-runtime"
MEMORY_DIR = WORKSPACE / "memory"

class TaskPriority(Enum):
    CRITICAL = "critical"    # 影响系统运行
    HIGH = "high"            # 重要改进
    MEDIUM = "medium"        # 常规优化
    LOW = "low"              # 锦上添花

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentTask:
    """Agent任务定义"""
    task_id: str
    task_type: str
    description: str
    target_agent: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deliverable: Optional[Dict] = None  # 交付物
    reflection: Optional[Dict] = None   # 反思结果
    parent_task: Optional[str] = None   # 父任务（用于任务分解）

@dataclass  
class Agent:
    """Agent定义"""
    agent_id: str
    role: str
    capabilities: List[str]
    success_rate: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    specialization: List[str] = field(default_factory=list)
    
    def get_confidence(self, task_type: str) -> float:
        """计算对某类任务的信心度"""
        base = self.success_rate if self.tasks_completed > 0 else 0.5
        if task_type in self.specialization:
            base += 0.2
        if task_type in self.capabilities:
            base += 0.1
        return min(base, 1.0)

class AgentConductor:
    """
    Agent指挥家 - 让多Agent系统活起来
    
    职责:
    1. 分析当前系统状态，识别改进机会
    2. 将机会转化为具体任务
    3. 根据Agent能力和历史表现分配任务
    4. 监控执行，收集反馈
    5. 基于反馈调整策略
    """
    
    def __init__(self):
        self.task_queue: List[AgentTask] = []
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[AgentTask] = []
        self.agents: Dict[str, Agent] = {}
        self.message_bus = MessageBus()
        self.zone_manager = ZoneManager()
        self.session_start = datetime.now()
        
        self._init_agents()
        self._setup_message_handlers()
        
    def _init_agents(self):
        """初始化5个Agent"""
        self.agents = {
            "coordinator": Agent(
                agent_id="coordinator",
                role="指挥家",
                capabilities=["task_decomposition", "conflict_resolution", "strategy_planning"],
                specialization=["system_architecture", "evolution_planning"]
            ),
            "coder": Agent(
                agent_id="coder", 
                role="编码实现",
                capabilities=["code_writing", "debugging", "refactoring"],
                specialization=["python", "shell_scripting"]
            ),
            "reviewer": Agent(
                agent_id="reviewer",
                role="审查验证", 
                capabilities=["code_review", "quality_check", "security_audit"],
                specialization=["best_practices", "error_detection"]
            ),
            "reflector": Agent(
                agent_id="reflector",
                role="反思分析",
                capabilities=["insight_extraction", "pattern_recognition", "learning_summarization"],
                specialization=["experience_distillation", "principle_extraction"]
            ),
            "evolution": Agent(
                agent_id="evolution",
                role="系统进化",
                capabilities=["system_update", "architecture_improvement", "documentation"],
                specialization=["memory_management", "skill_evolution"]
            )
        }
        
        # 加载历史表现
        self._load_agent_history()
    
    def _load_agent_history(self):
        """从文件加载Agent历史表现"""
        history_file = RUNTIME_DIR / "agent_history.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
                for agent_id, stats in history.items():
                    if agent_id in self.agents:
                        agent = self.agents[agent_id]
                        agent.tasks_completed = stats.get("completed", 0)
                        agent.tasks_failed = stats.get("failed", 0)
                        total = agent.tasks_completed + agent.tasks_failed
                        if total > 0:
                            agent.success_rate = agent.tasks_completed / total
    
    def _save_agent_history(self):
        """保存Agent历史表现"""
        history = {
            agent_id: {
                "completed": agent.tasks_completed,
                "failed": agent.tasks_failed,
                "success_rate": agent.success_rate
            }
            for agent_id, agent in self.agents.items()
        }
        history_file = RUNTIME_DIR / "agent_history.json"
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _setup_message_handlers(self):
        """设置消息处理器"""
        def on_task_completed(msg):
            task_id = msg.get("task_id")
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                task.deliverable = msg.get("deliverable", {})
                
                # 更新Agent成功率
                agent = self.agents.get(task.target_agent)
                if agent:
                    agent.tasks_completed += 1
                    self._update_success_rate(agent)
                
                # 移动到已完成
                self.completed_tasks.append(task)
                del self.active_tasks[task_id]
                
                # 触发Review
                self._schedule_review(task)
                
        def on_task_failed(msg):
            task_id = msg.get("task_id")
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.FAILED
                
                agent = self.agents.get(task.target_agent)
                if agent:
                    agent.tasks_failed += 1
                    self._update_success_rate(agent)
                
                # 分析失败原因并重新规划
                self._handle_failure(task, msg.get("reason", "unknown"))
        
        self.message_bus.subscribe("task_completed", on_task_completed)
        self.message_bus.subscribe("task_failed", on_task_failed)
    
    def _update_success_rate(self, agent: Agent):
        """更新Agent成功率"""
        total = agent.tasks_completed + agent.tasks_failed
        if total > 0:
            agent.success_rate = agent.tasks_completed / total
        self._save_agent_history()
    
    def _schedule_review(self, task: AgentTask):
        """为完成的任务安排审查"""
        review_task = AgentTask(
            task_id=f"review_{task.task_id}",
            task_type="code_review",
            description=f"审查 {task.task_type}: {task.description}",
            target_agent="reviewer",
            priority=TaskPriority.HIGH,
            parent_task=task.task_id
        )
        self.task_queue.append(review_task)
        print(f"   📋 安排审查: {review_task.task_id}")
    
    def _handle_failure(self, task: AgentTask, reason: str):
        """处理任务失败"""
        print(f"   ❌ 任务失败: {task.task_id} - {reason}")
        
        # 降低该Agent对这类任务的信心度
        agent = self.agents.get(task.target_agent)
        if agent:
            print(f"      {agent.agent_id} 对 {task.task_type} 的信心度降低")
        
        # 重新规划：换一个Agent或分解任务
        if task.priority != TaskPriority.LOW:
            # 尝试用Reflector分析失败原因
            reflect_task = AgentTask(
                task_id=f"reflect_{task.task_id}",
                task_type="failure_analysis",
                description=f"分析失败原因: {reason}",
                target_agent="reflector",
                priority=TaskPriority.HIGH,
                parent_task=task.task_id
            )
            self.task_queue.append(reflect_task)
    
    def identify_improvement_opportunities(self) -> List[Dict]:
        """
        分析系统状态，识别改进机会
        这是指挥家的核心能力：观察 → 思考 → 决策
        """
        opportunities = []
        
        # 1. 检查工具覆盖度
        skills_dir = WORKSPACE / "skills"
        if skills_dir.exists():
            skill_count = len(list(skills_dir.glob("*/SKILL.md")))
            if skill_count < 10:
                opportunities.append({
                    "type": "skill_gap",
                    "description": f"当前只有{skill_count}个技能，需要扩展工具覆盖",
                    "priority": TaskPriority.HIGH,
                    "suggested_agent": "evolution",
                    "estimated_effort": "medium"
                })
        
        # 2. 检查MEMORY.md更新频率
        memory_file = MEMORY_DIR / "daily" / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        if memory_file.exists():
            content = memory_file.read_text()
            if len(content) < 500:
                opportunities.append({
                    "type": "documentation_gap",
                    "description": "今日记忆记录较少，需要加强学习和沉淀",
                    "priority": TaskPriority.MEDIUM,
                    "suggested_agent": "reflector",
                    "estimated_effort": "low"
                })
        
        # 3. 检查代码质量
        runtime_code_dir = RUNTIME_DIR
        py_files = list(runtime_code_dir.glob("*.py"))
        if len(py_files) > 5:
            opportunities.append({
                "type": "code_quality",
                "description": f"运行时有{len(py_files)}个Python文件，需要代码审查和优化",
                "priority": TaskPriority.MEDIUM,
                "suggested_agent": "reviewer",
                "estimated_effort": "medium"
            })
        
        # 4. 检查待学习的GitHub项目
        pending_projects = WORKSPACE / ".scheduler" / "pending_projects.json"
        if pending_projects.exists():
            with open(pending_projects, 'r') as f:
                projects = json.load(f)
            if len(projects) > 0:
                opportunities.append({
                    "type": "learning_opportunity",
                    "description": f"有{len(projects)}个高价值GitHub项目待分析",
                    "priority": TaskPriority.HIGH,
                    "suggested_agent": "reflector",
                    "estimated_effort": "high"
                })
        
        return opportunities
    
    def create_tasks_from_opportunities(self, opportunities: List[Dict]):
        """将改进机会转化为具体任务"""
        for opp in opportunities:
            task = AgentTask(
                task_id=f"task_{datetime.now().strftime('%H%M%S')}_{random.randint(1000,9999)}",
                task_type=opp["type"],
                description=opp["description"],
                target_agent=opp["suggested_agent"],
                priority=opp["priority"]
            )
            self.task_queue.append(task)
            print(f"   📌 创建任务: {task.task_id} -> {task.target_agent}")
    
    def select_best_agent(self, task: AgentTask) -> Optional[str]:
        """
        为任务选择最佳Agent
        考虑: 能力匹配度 + 历史成功率 + 当前负载
        """
        candidates = []
        
        for agent_id, agent in self.agents.items():
            if agent_id == "coordinator":  # 指挥家不执行具体任务
                continue
                
            confidence = agent.get_confidence(task.task_type)
            
            # 检查当前负载
            current_tasks = sum(1 for t in self.active_tasks.values() if t.target_agent == agent_id)
            load_factor = 1.0 / (1 + current_tasks)  # 负载越高，优先级越低
            
            score = confidence * load_factor
            candidates.append((agent_id, score))
        
        if not candidates:
            return None
        
        # 选择得分最高的
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def execute_task(self, task: AgentTask) -> Dict:
        """
        执行单个任务
        模拟Agent执行，实际应调用相应的执行逻辑
        """
        print(f"\n🚀 执行任务: {task.task_id}")
        print(f"   类型: {task.task_type}")
        print(f"   目标Agent: {task.target_agent}")
        print(f"   描述: {task.description}")
        
        task.status = TaskStatus.EXECUTING
        task.started_at = datetime.now().isoformat()
        self.active_tasks[task.task_id] = task
        
        # 模拟执行（实际应调用具体Agent的执行逻辑）
        import time
        time.sleep(0.5)  # 模拟执行时间
        
        # 根据Agent类型生成不同的交付物
        deliverable = self._generate_deliverable(task)
        
        # 广播完成消息
        self.message_bus.publish("task_completed", {
            "task_id": task.task_id,
            "agent": task.target_agent,
            "deliverable": deliverable,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"   ✅ 任务完成: {task.task_id}")
        return deliverable
    
    def _generate_deliverable(self, task: AgentTask) -> Dict:
        """根据任务类型生成交付物"""
        if task.target_agent == "reflector":
            return {
                "type": "insights",
                "content": ["发现模式A", "发现模式B"],
                "recommendations": ["建议1", "建议2"]
            }
        elif task.target_agent == "reviewer":
            return {
                "type": "review_report",
                "issues_found": 2,
                "suggestions": ["改进点1", "改进点2"],
                "approval_status": "conditional"
            }
        elif task.target_agent == "coder":
            return {
                "type": "code",
                "files_created": ["file1.py"],
                "lines_of_code": 100,
                "tests_passed": True
            }
        elif task.target_agent == "evolution":
            return {
                "type": "system_update",
                "files_modified": ["config.json"],
                "memory_updated": True,
                "version_bump": "patch"
            }
        else:
            return {"type": "generic", "content": "执行完成"}
    
    def run_cycle(self):
        """
        运行一个指挥家周期
        完整的 OODA 循环: Observe → Orient → Decide → Act
        """
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║     🎼 Agent 指挥家周期                                     ║")
        print(f"║     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                  ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
        
        # 1. Observe: 观察系统状态
        print("👁️  观察系统状态...")
        opportunities = self.identify_improvement_opportunities()
        print(f"   发现 {len(opportunities)} 个改进机会")
        for opp in opportunities:
            print(f"   - {opp['type']}: {opp['description'][:50]}...")
        print()
        
        # 2. Orient: 分析并创建任务
        print("🧭 分析并创建任务...")
        self.create_tasks_from_opportunities(opportunities)
        print(f"   任务队列: {len(self.task_queue)} 个待处理")
        print()
        
        # 3. Decide & Act: 分配并执行任务
        print("⚡ 分配并执行任务...")
        executed = 0
        while self.task_queue and executed < 3:  # 每周期最多执行3个任务
            # 按优先级排序
            self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
            task = self.task_queue.pop(0)
            
            # 选择最佳Agent
            best_agent = self.select_best_agent(task)
            if best_agent:
                task.target_agent = best_agent
                self.execute_task(task)
                executed += 1
            else:
                print(f"   ⚠️  无法为任务 {task.task_id} 找到合适的Agent")
        
        print()
        
        # 4. 保存状态
        self._save_state()
        
        # 5. 生成周期报告
        self._generate_cycle_report()
    
    def _save_state(self):
        """保存指挥家状态"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "agents": {
                aid: {
                    "role": a.role,
                    "success_rate": a.success_rate,
                    "tasks_completed": a.tasks_completed
                }
                for aid, a in self.agents.items()
            },
            "queue_size": len(self.task_queue),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks)
        }
        
        state_file = RUNTIME_DIR / "conductor_state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _generate_cycle_report(self):
        """生成周期报告"""
        print("├─ 周期报告 ─────────────────────────────────────────────────┤")
        print(f"   活跃任务: {len(self.active_tasks)}")
        print(f"   已完成: {len(self.completed_tasks)}")
        print(f"   队列中: {len(self.task_queue)}")
        print()
        print("   Agent表现:")
        for agent_id, agent in self.agents.items():
            if agent.tasks_completed > 0 or agent.tasks_failed > 0:
                print(f"   - {agent_id}: 完成{agent.tasks_completed} 失败{agent.tasks_failed} 成功率{agent.success_rate:.1%}")
        print()
        print("=" * 65)
        print("✅ 指挥家周期完成")
        print("=" * 65)

def main():
    """主函数"""
    print("🎼 启动 wdai Agent 指挥家系统 v3.0")
    print()
    
    conductor = AgentConductor()
    
    # 运行一个周期演示
    conductor.run_cycle()
    
    print()
    print("💡 使用方式:")
    print("   conductor = AgentConductor()")
    print("   conductor.run_cycle()  # 运行一个指挥家周期")
    print()
    print("   或者持续运行:")
    print("   while True:")
    print("       conductor.run_cycle()")
    print("       time.sleep(3600)  # 每小时运行一次")

if __name__ == '__main__':
    main()
