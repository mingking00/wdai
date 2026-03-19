#!/usr/bin/env python3
"""
Planner Agent - 规划代理

负责:
1. 制定抓取策略
2. 任务调度与分配
3. 资源管理
4. 监控执行状态

Author: wdai
Date: 2026-03-19
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import time

# 修正导入路径
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from base import BaseAgent, Task, TaskStatus, Message, MessageType, AgentCoordinator


class SourceStrategy:
    """源策略配置"""
    
    def __init__(self, source_id: str, source_type: str):
        self.source_id = source_id
        self.source_type = source_type  # arxiv, github, rss
        self.enabled = True
        self.fetch_interval_minutes = 15
        self.priority_keywords: List[str] = []
        self.max_items_per_fetch = 10
        self.last_fetch_time: Optional[str] = None
        self.success_rate: float = 1.0  # 历史成功率
        
    def to_dict(self) -> Dict:
        return {
            'source_id': self.source_id,
            'source_type': self.source_type,
            'enabled': self.enabled,
            'fetch_interval_minutes': self.fetch_interval_minutes,
            'priority_keywords': self.priority_keywords,
            'max_items_per_fetch': self.max_items_per_fetch,
            'last_fetch_time': self.last_fetch_time,
            'success_rate': self.success_rate
        }
    
    def should_fetch(self) -> bool:
        """检查是否应该抓取"""
        if not self.enabled:
            return False
        
        if not self.last_fetch_time:
            return True
        
        last = datetime.fromisoformat(self.last_fetch_time)
        interval = timedelta(minutes=self.fetch_interval_minutes)
        
        return datetime.now() - last >= interval


class PlannerAgent(BaseAgent):
    """
    规划代理
    
    制定策略、分配任务、协调资源
    """
    
    def __init__(self, agent_id: str, message_bus):
        super().__init__(agent_id, message_bus)
        
        # 源配置
        self.sources: Dict[str, SourceStrategy] = {}
        self._init_default_sources()
        
        # 执行代理列表
        self.executor_agents: List[str] = []
        
        # 任务队列管理
        self.pending_tasks: List[Task] = []
        self.task_assignments: Dict[str, str] = {}  # task_id -> executor_id
        
        # 统计信息
        self.stats = {
            'tasks_created': 0,
            'tasks_assigned': 0,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
    
    def _init_default_sources(self):
        """初始化默认源配置"""
        # arXiv 论文源
        arxiv = SourceStrategy('arxiv_papers', 'arxiv')
        arxiv.priority_keywords = [
            'multi-agent', 'agent framework', 'llm agent',
            'autonomous system', 'ai safety', 'agent governance'
        ]
        self.sources['arxiv_papers'] = arxiv
        
        # GitHub 项目源
        github = SourceStrategy('github_repos', 'github')
        github.priority_keywords = [
            'agent', 'mcp', 'claude', 'openai', 'autonomous'
        ]
        self.sources['github_repos'] = github
        
        # RSS 新闻源
        rss = SourceStrategy('ai_news_rss', 'rss')
        rss.fetch_interval_minutes = 30
        self.sources['ai_news_rss'] = rss
        
        print(f"[{self.agent_id}] 已初始化 {len(self.sources)} 个源")
    
    def process_task(self, task: Task) -> Dict[str, Any]:
        """
        处理规划任务
        
        Planner 的主要工作是制定策略和分配任务，
        而不是执行具体的抓取/分析
        """
        task_type = task.type
        
        if task_type == 'plan_fetch':
            return self._plan_fetch_task(task)
        
        elif task_type == 'plan_analyze':
            return self._plan_analyze_task(task)
        
        elif task_type == 'update_strategy':
            return self._update_strategy(task)
        
        elif task_type == 'monitor':
            return self._monitor_status(task)
        
        else:
            return {'status': 'unknown_task_type', 'type': task_type}
    
    def _plan_fetch_task(self, task: Task) -> Dict[str, Any]:
        """规划抓取任务"""
        print(f"[{self.agent_id}] 规划抓取任务")
        
        fetch_tasks = []
        
        for source_id, source in self.sources.items():
            if source.should_fetch():
                # 创建抓取任务
                fetch_task = Task(
                    type='fetch',
                    priority=1 if source.success_rate > 0.8 else 3,
                    payload={
                        'source_id': source_id,
                        'source_type': source.source_type,
                        'max_items': source.max_items_per_fetch,
                        'keywords': source.priority_keywords
                    }
                )
                fetch_tasks.append(fetch_task)
                self.stats['tasks_created'] += 1
                
                # 更新最后抓取时间
                source.last_fetch_time = datetime.now().isoformat()
        
        # 分配给执行代理
        assigned_count = self._distribute_tasks(fetch_tasks)
        
        return {
            'status': 'planned',
            'fetch_tasks_created': len(fetch_tasks),
            'tasks_assigned': assigned_count,
            'sources_checked': len(self.sources)
        }
    
    def _plan_analyze_task(self, task: Task) -> Dict[str, Any]:
        """规划分析任务"""
        print(f"[{self.agent_id}] 规划分析任务")
        
        # 获取需要分析的内容
        papers = task.payload.get('papers', [])
        
        analyze_tasks = []
        for paper in papers:
            analyze_task = Task(
                type='deep_analyze',
                priority=2,
                payload={
                    'paper': paper,
                    'analysis_depth': 'full'  # 深度分析
                }
            )
            analyze_tasks.append(analyze_task)
            self.stats['tasks_created'] += 1
        
        assigned_count = self._distribute_tasks(analyze_tasks)
        
        return {
            'status': 'planned',
            'analyze_tasks_created': len(analyze_tasks),
            'tasks_assigned': assigned_count
        }
    
    def _distribute_tasks(self, tasks: List[Task]) -> int:
        """分配任务给执行代理"""
        if not self.executor_agents:
            print(f"[{self.agent_id}] 警告: 没有可用的执行代理")
            return 0
        
        assigned = 0
        for i, task in enumerate(tasks):
            # 轮询分配给执行代理
            executor_id = self.executor_agents[i % len(self.executor_agents)]
            
            # 发送任务分配消息
            message = Message(
                type=MessageType.TASK_ASSIGN,
                sender=self.agent_id,
                receiver=executor_id,
                payload={'task': task.to_dict()}
            )
            
            if self.message_bus.send(message):
                self.task_assignments[task.id] = executor_id
                self.stats['tasks_assigned'] += 1
                assigned += 1
                print(f"[{self.agent_id}] 分配任务 {task.id} 给 {executor_id}")
            else:
                print(f"[{self.agent_id}] 分配任务 {task.id} 失败")
        
        return assigned
    
    def _update_strategy(self, task: Task) -> Dict[str, Any]:
        """更新策略"""
        updates = task.payload.get('updates', {})
        
        for source_id, config in updates.get('sources', {}).items():
            if source_id in self.sources:
                # 更新源配置
                for key, value in config.items():
                    if hasattr(self.sources[source_id], key):
                        setattr(self.sources[source_id], key, value)
        
        # 更新执行代理列表
        if 'executors' in updates:
            self.executor_agents = updates['executors']
        
        return {
            'status': 'updated',
            'sources_count': len(self.sources),
            'executors_count': len(self.executor_agents)
        }
    
    def _monitor_status(self, task: Task) -> Dict[str, Any]:
        """监控状态"""
        return {
            'status': 'monitoring',
            'sources': {sid: s.to_dict() for sid, s in self.sources.items()},
            'executors': self.executor_agents,
            'pending_tasks': len(self.pending_tasks),
            'stats': self.stats
        }
    
    def _on_message(self, message: Message):
        """处理消息"""
        super()._on_message(message)
        
        if message.type == MessageType.TASK_COMPLETE:
            # 任务完成
            task_data = message.payload.get('task', {})
            task_id = task_data.get('id')
            
            if task_id in self.task_assignments:
                del self.task_assignments[task_id]
                self.stats['tasks_completed'] += 1
                print(f"[{self.agent_id}] 任务 {task_id} 已完成")
                
                # 如果是抓取任务完成，自动规划分析任务
                if task_data.get('type') == 'fetch' and task_data.get('result'):
                    papers = task_data['result'].get('papers', [])
                    if papers:
                        self._trigger_analyze_planning(papers)
        
        elif message.type == MessageType.TASK_FAILED:
            # 任务失败
            task_data = message.payload.get('task', {})
            task_id = task_data.get('id')
            
            if task_id in self.task_assignments:
                executor_id = self.task_assignments[task_id]
                del self.task_assignments[task_id]
                self.stats['tasks_failed'] += 1
                
                # 更新源成功率
                source_id = task_data.get('payload', {}).get('source_id')
                if source_id and source_id in self.sources:
                    self.sources[source_id].success_rate *= 0.9  # 降低成功率
                    print(f"[{self.agent_id}] 源 {source_id} 成功率降至 {self.sources[source_id].success_rate:.2f}")
    
    def _trigger_analyze_planning(self, papers: List[Dict]):
        """触发分析规划"""
        print(f"[{self.agent_id}] 触发分析规划，{len(papers)} 篇论文待分析")
        
        analyze_plan_task = Task(
            type='plan_analyze',
            priority=2,
            payload={'papers': papers}
        )
        
        # 直接处理（因为是Planner自己的任务）
        self._task_queue.put((analyze_plan_task.priority, time.time(), analyze_plan_task))
    
    def register_executor(self, executor_id: str):
        """注册执行代理"""
        if executor_id not in self.executor_agents:
            self.executor_agents.append(executor_id)
            print(f"[{self.agent_id}] 注册执行代理: {executor_id}")
    
    def get_strategy_summary(self) -> str:
        """获取策略摘要"""
        lines = [
            f"\n{'='*50}",
            f"[{self.agent_id}] 策略摘要",
            f"{'='*50}",
            f"源数量: {len(self.sources)}",
            f"执行代理: {len(self.executor_agents)}",
            f"待处理任务: {len(self.pending_tasks)}",
            f"统计: 创建{self.stats['tasks_created']} | "
            f"分配{self.stats['tasks_assigned']} | "
            f"完成{self.stats['tasks_completed']} | "
            f"失败{self.stats['tasks_failed']}",
            f"{'='*50}\n"
        ]
        return '\n'.join(lines)


def test_planner():
    """测试 Planner Agent"""
    print("="*60)
    print("测试 Planner Agent")
    print("="*60)
    
    from base import AgentCoordinator, MessageBus
    
    # 创建协调器
    coordinator = AgentCoordinator()
    
    # 创建 Planner
    planner = PlannerAgent('planner_1', coordinator.message_bus)
    coordinator.register_agent(planner)
    
    # 注册一个虚拟的执行代理
    planner.register_executor('executor_1')
    
    # 启动
    coordinator.start_all()
    
    # 触发规划任务
    plan_task = Task(type='plan_fetch', priority=1, payload={})
    coordinator.assign_task(plan_task, 'planner_1')
    
    # 等待
    time.sleep(2.0)
    
    # 查看状态
    print(planner.get_strategy_summary())
    
    # 停止
    coordinator.stop_all()
    
    print("\n✅ Planner Agent 测试完成")


if __name__ == '__main__':
    test_planner()
