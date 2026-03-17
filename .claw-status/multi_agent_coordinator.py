#!/usr/bin/env python3
"""
多Agent协调系统 (Multi-Agent Coordination System)
实现Agent之间的任务分发、冲突仲裁、状态同步
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import threading
import time

@dataclass
class AgentInstance:
    """Agent实例定义"""
    agent_id: str
    agent_type: str  # coordinator, coder, reviewer, researcher, reflector, evolution
    status: str = "idle"  # idle, busy, error
    current_task: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    principles: Dict = field(default_factory=dict)
    last_heartbeat: str = ""
    
@dataclass
class TaskAssignment:
    """任务分配记录"""
    task_id: str
    task_type: str
    description: str
    assigned_to: str
    assigned_by: str
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = ""
    completed_at: Optional[str] = None
    result: Any = None

@dataclass
class ConflictRecord:
    """冲突记录"""
    conflict_id: str
    type: str  # technical, priority, resource
    agent_a: str
    agent_b: str
    description: str
    principles_involved: List[str]
    resolution: Optional[str] = None
    winner: Optional[str] = None
    timestamp: str = ""

class MultiAgentCoordinator:
    """
    多Agent协调器
    负责任务分发、冲突仲裁、状态同步
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentInstance] = {}
        self.tasks: Dict[str, TaskAssignment] = {}
        self.conflicts: List[ConflictRecord] = []
        self.shared_memory: Dict = {}
        
        self.state_dir = "/root/.openclaw/workspace/.claw-status"
        self.state_file = f"{self.state_dir}/multi_agent_coordination.json"
        
        self._init_default_agents()
        self._load_state()
    
    def _init_default_agents(self):
        """初始化默认Agent"""
        default_agents = [
            AgentInstance(
                agent_id="main",
                agent_type="coordinator",
                capabilities=["task_decompose", "conflict_arbitrate", "quality_control"],
                principles={"level": "P1", "weight": 100}
            ),
            AgentInstance(
                agent_id="coder",
                agent_type="coder",
                capabilities=["code_write", "debug", "deploy", "git"],
                principles={"level": "P2", "weight": 50}
            ),
            AgentInstance(
                agent_id="reflector",
                agent_type="reflector",
                capabilities=["reflection", "pattern_extraction", "principle_refinement"],
                principles={"level": "P3", "weight": 30}
            ),
            AgentInstance(
                agent_id="evolution",
                agent_type="evolution",
                capabilities=["system_improve", "skill_creation", "framework_update"],
                principles={"level": "P1", "weight": 90}
            ),
            AgentInstance(
                agent_id="reviewer",
                agent_type="reviewer",
                capabilities=["code_review", "quality_check", "verification"],
                principles={"level": "P2", "weight": 40}
            )
        ]
        
        for agent in default_agents:
            if agent.agent_id not in self.agents:
                self.agents[agent.agent_id] = agent
    
    def register_agent(self, agent_id: str, agent_type: str, capabilities: List[str]) -> bool:
        """注册新Agent"""
        if agent_id in self.agents:
            return False
        
        self.agents[agent_id] = AgentInstance(
            agent_id=agent_id,
            agent_type=agent_type,
            capabilities=capabilities,
            last_heartbeat=datetime.now().isoformat()
        )
        self._save_state()
        return True
    
    def assign_task(self, task_description: str, task_type: str, 
                    preferred_agent: Optional[str] = None) -> Dict:
        """
        分配任务给最适合的Agent
        
        策略:
        1. 如果指定了preferred_agent，优先尝试
        2. 根据任务类型匹配capabilities
        3. 选择当前空闲的Agent
        4. 如果冲突，进行仲裁
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(task_description) % 10000}"
        
        # 1. 如果指定了Agent
        if preferred_agent and preferred_agent in self.agents:
            agent = self.agents[preferred_agent]
            if agent.status == "idle":
                return self._assign_to_agent(task_id, task_description, task_type, agent)
        
        # 2. 根据任务类型匹配
        candidates = self._match_agents_by_task(task_type)
        
        if not candidates:
            return {
                "status": "no_match",
                "message": f"没有找到能处理'{task_type}'任务的Agent",
                "suggestion": "创建专用Agent或分解任务"
            }
        
        # 3. 选择空闲的Agent
        idle_agents = [a for a in candidates if a.status == "idle"]
        
        if idle_agents:
            # 选择能力匹配度最高的
            best_agent = max(idle_agents, 
                           key=lambda a: self._calculate_match_score(a, task_type))
            return self._assign_to_agent(task_id, task_description, task_type, best_agent)
        
        # 4. 所有匹配的Agent都忙，需要等待或仲裁
        return {
            "status": "all_busy",
            "message": "所有匹配的Agent都忙",
            "queue_position": len([t for t in self.tasks.values() if t.status == "pending"]) + 1,
            "alternatives": [a.agent_id for a in candidates]
        }
    
    def _match_agents_by_task(self, task_type: str) -> List[AgentInstance]:
        """根据任务类型匹配Agent"""
        task_capability_map = {
            "code": ["code_write", "debug", "git"],
            "deploy": ["deploy", "git"],
            "research": ["research", "analyze"],
            "reflection": ["reflection", "pattern_extraction"],
            "evolution": ["system_improve", "skill_creation"],
            "review": ["code_review", "quality_check"]
        }
        
        required_caps = task_capability_map.get(task_type, [])
        
        candidates = []
        for agent in self.agents.values():
            if any(cap in agent.capabilities for cap in required_caps):
                candidates.append(agent)
        
        return candidates
    
    def _calculate_match_score(self, agent: AgentInstance, task_type: str) -> int:
        """计算Agent与任务的匹配分数"""
        score = 0
        
        # 历史成功率（简化版）
        agent_tasks = [t for t in self.tasks.values() if t.assigned_to == agent.agent_id]
        if agent_tasks:
            success_rate = len([t for t in agent_tasks if t.status == "completed"]) / len(agent_tasks)
            score += int(success_rate * 100)
        
        # 能力匹配度
        task_caps = {
            "code": ["code_write", "debug"],
            "deploy": ["deploy"],
            "reflection": ["reflection"]
        }.get(task_type, [])
        
        match_count = sum(1 for cap in task_caps if cap in agent.capabilities)
        score += match_count * 50
        
        return score
    
    def _assign_to_agent(self, task_id: str, description: str, task_type: str, 
                        agent: AgentInstance) -> Dict:
        """实际分配任务"""
        assignment = TaskAssignment(
            task_id=task_id,
            task_type=task_type,
            description=description,
            assigned_to=agent.agent_id,
            assigned_by="coordinator",
            created_at=datetime.now().isoformat()
        )
        
        self.tasks[task_id] = assignment
        agent.status = "busy"
        agent.current_task = task_id
        agent.last_heartbeat = datetime.now().isoformat()
        
        self._save_state()
        
        return {
            "status": "assigned",
            "task_id": task_id,
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "message": f"任务已分配给 {agent.agent_id}"
        }
    
    def report_task_complete(self, task_id: str, result: Any, success: bool = True) -> Dict:
        """Agent报告任务完成"""
        if task_id not in self.tasks:
            return {"status": "error", "message": "任务不存在"}
        
        task = self.tasks[task_id]
        task.status = "completed" if success else "failed"
        task.completed_at = datetime.now().isoformat()
        task.result = result
        
        # 更新Agent状态
        agent = self.agents.get(task.assigned_to)
        if agent:
            agent.status = "idle"
            agent.current_task = None
        
        # 触发反思（如果是重要任务）
        if task.task_type in ["code", "deploy", "evolution"]:
            self._trigger_reflection(task)
        
        self._save_state()
        
        return {
            "status": "recorded",
            "task_id": task_id,
            "next_action": "reflection_triggered" if task.task_type in ["code", "deploy"] else "none"
        }
    
    def _trigger_reflection(self, task: TaskAssignment):
        """触发反思Agent"""
        reflector = self.agents.get("reflector")
        if reflector and reflector.status == "idle":
            # 创建反思任务
            reflection_task = TaskAssignment(
                task_id=f"reflection_{task.task_id}",
                task_type="reflection",
                description=f"反思任务: {task.description}",
                assigned_to="reflector",
                assigned_by="coordinator",
                created_at=datetime.now().isoformat()
            )
            self.tasks[reflection_task.task_id] = reflection_task
            reflector.status = "busy"
            reflector.current_task = reflection_task.task_id
            
            print(f"[协调器] 触发反思Agent分析任务 {task.task_id}")
    
    def arbitrate_conflict(self, agent_a_id: str, agent_b_id: str, 
                          conflict_type: str, description: str) -> Dict:
        """
        仲裁Agent之间的冲突
        
        策略:
        1. 领域专家优先
        2. 原则权重比较
        3. 历史成功率
        4. 提出融合方案
        """
        agent_a = self.agents.get(agent_a_id)
        agent_b = self.agents.get(agent_b_id)
        
        if not agent_a or not agent_b:
            return {"status": "error", "message": "Agent不存在"}
        
        conflict_id = f"conflict_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 决策逻辑
        winner = None
        reason = ""
        
        # 1. 原则权重比较
        weight_a = agent_a.principles.get("weight", 0)
        weight_b = agent_b.principles.get("weight", 0)
        
        if weight_a > weight_b + 20:
            winner = agent_a_id
            reason = f"原则权重优先: {weight_a} > {weight_b}"
        elif weight_b > weight_a + 20:
            winner = agent_b_id
            reason = f"原则权重优先: {weight_b} > {weight_a}"
        else:
            # 2. 历史成功率
            tasks_a = [t for t in self.tasks.values() if t.assigned_to == agent_a_id]
            tasks_b = [t for t in self.tasks.values() if t.assigned_to == agent_b_id]
            
            success_rate_a = len([t for t in tasks_a if t.status == "completed"]) / len(tasks_a) if tasks_a else 0.5
            success_rate_b = len([t for t in tasks_b if t.status == "completed"]) / len(tasks_b) if tasks_b else 0.5
            
            if success_rate_a > success_rate_b + 0.2:
                winner = agent_a_id
                reason = f"历史成功率优先: {success_rate_a:.2f} > {success_rate_b:.2f}"
            elif success_rate_b > success_rate_a + 0.2:
                winner = agent_b_id
                reason = f"历史成功率优先: {success_rate_b:.2f} > {success_rate_a:.2f}"
            else:
                # 3. 融合方案
                winner = "hybrid"
                reason = "提出融合方案"
        
        # 记录冲突
        conflict = ConflictRecord(
            conflict_id=conflict_id,
            type=conflict_type,
            agent_a=agent_a_id,
            agent_b=agent_b_id,
            description=description,
            principles_involved=[agent_a.principles.get("level", ""), agent_b.principles.get("level", "")],
            resolution=reason,
            winner=winner,
            timestamp=datetime.now().isoformat()
        )
        
        self.conflicts.append(conflict)
        self._save_state()
        
        return {
            "status": "resolved",
            "conflict_id": conflict_id,
            "winner": winner,
            "reason": reason
        }
    
    def get_system_status(self) -> Dict:
        """获取系统整体状态"""
        return {
            "agents": {
                "total": len(self.agents),
                "idle": len([a for a in self.agents.values() if a.status == "idle"]),
                "busy": len([a for a in self.agents.values() if a.status == "busy"]),
                "details": [
                    {
                        "id": a.agent_id,
                        "type": a.agent_type,
                        "status": a.status,
                        "current_task": a.current_task
                    }
                    for a in self.agents.values()
                ]
            },
            "tasks": {
                "total": len(self.tasks),
                "pending": len([t for t in self.tasks.values() if t.status == "pending"]),
                "running": len([t for t in self.tasks.values() if t.status == "running"]),
                "completed": len([t for t in self.tasks.values() if t.status == "completed"]),
                "failed": len([t for t in self.tasks.values() if t.status == "failed"])
            },
            "conflicts": len(self.conflicts),
            "last_update": datetime.now().isoformat()
        }
    
    def _save_state(self):
        """保存状态"""
        state = {
            "agents": {k: asdict(v) for k, v in self.agents.items()},
            "tasks": {k: asdict(v) for k, v in self.tasks.items()},
            "conflicts": [asdict(c) for c in self.conflicts[-50:]],  # 只保留最近50条
            "updated_at": datetime.now().isoformat()
        }
        
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """加载状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    # 恢复agents状态
                    for k, v in state.get("agents", {}).items():
                        if k not in self.agents:
                            self.agents[k] = AgentInstance(**v)
            except Exception as e:
                print(f"加载协调器状态失败: {e}")

# 全局协调器实例
_coordinator = None

def get_coordinator() -> MultiAgentCoordinator:
    """获取协调器单例"""
    global _coordinator
    if _coordinator is None:
        _coordinator = MultiAgentCoordinator()
    return _coordinator

if __name__ == "__main__":
    # 测试
    coord = get_coordinator()
    
    print("=" * 60)
    print("多Agent协调系统测试")
    print("=" * 60)
    
    # 显示系统状态
    status = coord.get_system_status()
    print("\n系统状态:")
    print(f"  Agent总数: {status['agents']['total']}")
    print(f"  空闲: {status['agents']['idle']}, 忙碌: {status['agents']['busy']}")
    
    print("\nAgent详情:")
    for agent in status['agents']['details']:
        print(f"  - {agent['id']} ({agent['type']}): {agent['status']}")
    
    # 测试任务分配
    print("\n任务分配测试:")
    result = coord.assign_task("部署博客到GitHub", "deploy")
    print(f"  结果: {result}")
    
    # 测试冲突仲裁
    print("\n冲突仲裁测试:")
    result = coord.arbitrate_conflict("coder", "reviewer", "technical", "React vs Vue")
    print(f"  胜方: {result.get('winner')}")
    print(f"  理由: {result.get('reason')}")
    
    print("\n" + "=" * 60)
