#!/usr/bin/env python3
"""
OpenClaw Adaptive Multi-Agent System (OCA-MAS)
融合架构 v1.0

核心设计:
├─ Gemini LangGraph: 状态驱动 + 反思迭代 + 固定角色
├─ Kimi Agent Swarm: 动态实例化 + 关键路径优化 + 并行执行  
├─ 第一性原理: 6个核心超能力 (单点极致)
└─ 工作监察: 实时可见性

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    Conductor (系统优化力)                    │
│              - 关键路径分析 + 动态资源调度                    │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    ┌──────────┐      ┌──────────┐         ┌──────────┐
    │ Explorer │─────→│Investigator│───────→│  Critic  │
    │(空间感知)│      │(深度穿透) │ 并行×N  │(真伪判断)│
    └──────────┘      └──────────┘         └──────────┘
         ↑                                        ↓
         └──────────┐                    ┌──────────┘
                   Synthesist (模式编织力)
                          ↓
                   Anchor (心智共情力) → 用户
"""

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
from personas import PersonaTeam, AgentPersona

# 工作监察集成 (容错)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / ".claw-status"))
    from work_monitor import WorkMonitor, start_task, progress, artifact, complete, waiting
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    # 创建空实现
    def start_task(*args, **kwargs): pass
    def progress(*args, **kwargs): pass
    def artifact(*args, **kwargs): pass
    def complete(*args, **kwargs): pass
    def waiting(*args, **kwargs): pass
    class WorkMonitor:
        pass

# ============ 核心数据模型 ============

@dataclass
class AgentTask:
    """任务单元"""
    id: str
    agent_role: str
    competency: str  # 核心能力
    prompt: str
    priority: int = 5  # 1-10, 10最高
    dependencies: List[str] = field(default_factory=list)
    estimated_time: float = 30.0  # 秒
    
@dataclass
class AgentResult:
    """结果单元"""
    task_id: str
    agent_role: str
    content: Any
    quality_score: float  # 0-1
    execution_time: float
    tokens_used: int = 0

@dataclass
class ResearchState:
    """共享状态 (Gemini风格)"""
    query: str = ""
    
    # 并行收集的结果
    search_results: List[Dict] = field(default_factory=list)
    sources: List[Dict] = field(default_factory=list)
    
    # 反思状态
    is_sufficient: bool = False
    knowledge_gap: str = ""
    follow_up_tasks: List[AgentTask] = field(default_factory=list)
    
    # 合成结果
    final_answer: str = ""
    insights: List[str] = field(default_factory=list)
    
    # 性能指标
    total_tokens: int = 0
    parallel_agents: int = 0
    critical_path_time: float = 0.0

# ============ 核心编排器 ============

class AdaptiveOrchestrator:
    """
    自适应编排器
    
    融合设计:
    - 固定角色 (Gemini): Explorer, Investigator, Critic, Synthesist, Anchor
    - 动态实例 (Kimi): Investigator可克隆多个并行实例
    - 关键路径优化 (Kimi): 识别并优化最长依赖链
    - 核心能力驱动 (第一性): 每个Agent只负责一个维度
    """
    
    def __init__(self, max_parallel: int = 5, enable_monitoring: bool = True):
        self.max_parallel = max_parallel
        self.state = ResearchState()
        self.task_queue: List[AgentTask] = []
        self.results: Dict[str, AgentResult] = {}
        self.monitor = WorkMonitor() if enable_monitoring else None
        
    async def execute(self, query: str) -> Dict:
        """
        执行完整研究流程
        
        流程:
        1. Explorer生成搜索任务 (关键路径起点)
        2. 并行执行多个Investigator (动态实例化)
        3. Critic评估 (关键路径检查点)
        4. 如需补充,循环2-3 (关键路径延长)
        5. Synthesist合成 (关键路径终点)
        6. Anchor报告 (并行进行)
        """
        if self.monitor:
            start_task(f"研究: {query[:40]}", steps=5)
        
        self.state.query = query
        start_time = time.time()
        
        # Phase 1: 探索 (空间感知)
        progress("Phase 1: Explorer 空间感知", 1, 5)
        explorer_tasks = await self._run_explorer(query)
        
        # Phase 2: 并行调查 (深度穿透) - 关键路径
        progress("Phase 2: Investigator 并行深度穿透", 2, 5)
        await self._run_parallel_investigators(explorer_tasks)
        
        # Phase 3-4: 反思循环 (真伪判断)
        loop_count = 0
        max_loops = 3
        
        while loop_count < max_loops:
            loop_count += 1
            progress(f"Phase 3: Critic 真伪判断 (循环{loop_count})", 2 + loop_count, 5)
            
            is_sufficient, gap = await self._run_critic()
            
            if is_sufficient:
                break
            
            if loop_count < max_loops:
                # 动态创建补充调查任务
                progress(f"动态补充调查: {gap[:50]}...", 2 + loop_count, 5)
                await self._run_supplemental_investigation(gap)
        
        # Phase 5: 合成 (模式编织)
        progress("Phase 5: Synthesist 模式编织", 4, 5)
        await self._run_synthesist()
        
        # Phase 6: 报告 (心智共情)
        progress("Phase 6: Anchor 心智共情", 5, 5)
        await self._run_anchor()
        
        total_time = time.time() - start_time
        self.state.critical_path_time = total_time
        
        if self.monitor:
            artifact("研究结果", "result.json")
            complete(f"完成研究，耗时{total_time:.1f}s")
        
        return self._format_output()
    
    async def _run_explorer(self, query: str) -> List[AgentTask]:
        """
        Explorer: 空间感知
        产出: N个搜索任务，每个指向不同的信息空间坐标
        """
        persona = PersonaTeam.get_persona("explorer")
        
        # 模拟调用Explorer Agent
        # 实际应使用: sessions_spawn(task=..., model=...)
        search_queries = [
            f"{query} best practices 2026",
            f"{query} comparison analysis",
            f"{query} common pitfalls",
            f"{query} expert recommendations",
            f"{query} latest developments"
        ]
        
        tasks = []
        for i, q in enumerate(search_queries):
            task = AgentTask(
                id=f"investigate_{i}",
                agent_role="investigator",
                competency="深度穿透力",
                prompt=q,
                priority=8 if i < 2 else 5,  # 前2个高优先级
                estimated_time=25.0
            )
            tasks.append(task)
        
        return tasks
    
    async def _run_parallel_investigators(self, tasks: List[AgentTask]):
        """
        Investigator: 深度穿透 (并行×N)
        
        Kimi风格: 动态创建多个实例，关键路径并行化
        """
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def run_with_limit(task: AgentTask):
            async with semaphore:
                return await self._execute_agent(task)
        
        # 关键路径: 所有Investigator并行执行
        start = time.time()
        results = await asyncio.gather(*[run_with_limit(t) for t in tasks])
        parallel_time = time.time() - start
        
        # 收集结果
        for result in results:
            if result and result.content:
                self.state.search_results.append(result.content)
                self.results[result.task_id] = result
        
        self.state.parallel_agents = len(tasks)
        print(f"   并行{len(tasks)}个Investigator，耗时{parallel_time:.1f}s")
    
    async def _execute_agent(self, task: AgentTask) -> Optional[AgentResult]:
        """执行单个Agent任务"""
        persona = PersonaTeam.get_persona(task.agent_role)
        
        # 模拟执行 (实际应调用 sessions_spawn)
        await asyncio.sleep(0.1)  # 模拟延迟
        
        # 模拟结果
        content = {
            "query": task.prompt,
            "data": f"Research data for: {task.prompt[:30]}...",
            "sources": ["source1.com", "source2.com"]
        }
        
        return AgentResult(
            task_id=task.id,
            agent_role=task.agent_role,
            content=content,
            quality_score=0.85,
            execution_time=0.1,
            tokens_used=500
        )
    
    async def _run_critic(self) -> tuple[bool, str]:
        """
        Critic: 真伪判断
        检查: 信息是否充足? 质量是否达标?
        """
        # 模拟评估
        if len(self.state.search_results) >= 3:
            self.state.is_sufficient = True
            return True, ""
        else:
            self.state.is_sufficient = False
            return False, "信息覆盖不足，需要补充技术细节"
    
    async def _run_supplemental_investigation(self, gap: str):
        """动态补充调查 (Kimi风格动态任务创建)"""
        supplemental_task = AgentTask(
            id=f"supplemental_{time.time()}",
            agent_role="investigator",
            competency="深度穿透力",
            prompt=gap,
            priority=9,  # 高优先级补充
            estimated_time=20.0
        )
        
        result = await self._execute_agent(supplemental_task)
        if result:
            self.state.search_results.append(result.content)
    
    async def _run_synthesist(self):
        """Synthesist: 模式编织"""
        # 模拟合成
        insights = [
            "发现趋势A: 向量化成为主流",
            "发现趋势B: 多模态融合加速",
            "洞察: 未来6个月将迎来突破"
        ]
        
        self.state.insights = insights
        self.state.final_answer = f"基于{len(self.state.search_results)}个来源的综合分析:\n" + "\n".join(insights)
    
    async def _run_anchor(self):
        """Anchor: 心智共情 - 调整输出格式"""
        # 根据复杂度调整输出长度
        if len(self.state.final_answer) > 1000:
            self.state.final_answer = self.state.final_answer[:1000] + "\n\n[详细内容已保存到文件]"
    
    def _format_output(self) -> Dict:
        """格式化最终输出"""
        return {
            "query": self.state.query,
            "answer": self.state.final_answer,
            "insights": self.state.insights,
            "sources_count": len(self.state.search_results),
            "parallel_agents": self.state.parallel_agents,
            "critical_path_time": self.state.critical_path_time,
            "total_tokens": self.state.total_tokens
        }

# ============ 便捷接口 ============

async def research(query: str, max_parallel: int = 5) -> Dict:
    """
    一键研究接口
    
    Example:
        result = await research("AI agent frameworks 2026")
        print(result["answer"])
    """
    orchestrator = AdaptiveOrchestrator(max_parallel=max_parallel)
    return await orchestrator.execute(query)

# ============ CLI 入口 ============

if __name__ == "__main__":
    import sys
    
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Latest AI agent frameworks"
    
    print(f"\n🔬 OpenClaw Adaptive Multi-Agent System")
    print(f"Query: {query}\n")
    
    result = asyncio.run(research(query))
    
    print("\n" + "="*60)
    print("RESULT")
    print("="*60)
    print(result["answer"])
    print("\n" + "="*60)
    print(f"⏱️  Critical path: {result['critical_path_time']:.1f}s")
    print(f"🔀 Parallel agents: {result['parallel_agents']}")
    print(f"📚 Sources: {result['sources_count']}")
