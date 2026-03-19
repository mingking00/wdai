#!/usr/bin/env python3
"""
Executor Agent - 执行代理

负责:
1. 实际内容抓取
2. 深度内容分析
3. 洞察生成

Author: wdai
Date: 2026-03-19
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import BaseAgent, Task, TaskStatus, Message, MessageType


class ExecutorAgent(BaseAgent):
    """
    执行代理
    
    执行具体的抓取、分析、生成任务
    """
    
    def __init__(self, agent_id: str, message_bus):
        super().__init__(agent_id, message_bus)
        
        # 执行能力注册
        self.capabilities = {
            'fetch': self._execute_fetch,
            'deep_analyze': self._execute_deep_analyze,
            'generate_insight': self._execute_generate_insight,
            'test_design': self._execute_test_design
        }
        
        # 统计信息
        self.stats = {
            'tasks_executed': 0,
            'tasks_succeeded': 0,
            'tasks_failed': 0,
            'papers_fetched': 0,
            'papers_analyzed': 0
        }
        
        # 缓存
        self.cache: Dict[str, Any] = {}
        
        print(f"[{self.agent_id}] 执行代理初始化完成，支持 {len(self.capabilities)} 种任务")
    
    def process_task(self, task: Task) -> Dict[str, Any]:
        """
        执行任务
        
        根据任务类型调用对应的执行方法
        """
        task_type = task.type
        self.stats['tasks_executed'] += 1
        
        print(f"[{self.agent_id}] 执行任务: {task.id}, 类型: {task_type}")
        
        if task_type in self.capabilities:
            try:
                result = self.capabilities[task_type](task.payload)
                self.stats['tasks_succeeded'] += 1
                return result
            except Exception as e:
                self.stats['tasks_failed'] += 1
                raise e
        else:
            self.stats['tasks_failed'] += 1
            raise ValueError(f"未知任务类型: {task_type}")
    
    def _execute_fetch(self, payload: Dict) -> Dict[str, Any]:
        """
        执行抓取任务
        
        使用 FetchAdapter 进行实际抓取
        """
        from fetch_adapter import FetchAdapter
        
        source_id = payload.get('source_id')
        source_type = payload.get('source_type')
        max_items = payload.get('max_items', 10)
        keywords = payload.get('keywords', [])
        
        print(f"[{self.agent_id}] 抓取 {source_id} ({source_type}), 关键词: {keywords}")
        
        # 使用适配器进行抓取
        adapter = FetchAdapter()
        result = adapter.fetch(source_id, source_type, max_items, keywords)
        
        # 更新统计
        items = result.get('items', [])
        self.stats['papers_fetched'] += len(items)
        
        # 缓存抓取结果
        cache_key = f"fetch_{source_id}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        self.cache[cache_key] = result
        
        return {
            'status': 'success',
            'source_id': source_id,
            'source_type': source_type,
            'papers': items,
            'count': len(items),
            'elapsed_seconds': result.get('elapsed_seconds', 0)
        }
    
    def _execute_deep_analyze(self, payload: Dict) -> Dict[str, Any]:
        """
        执行深度分析任务
        
        调用 deep_paper_analyzer.py 进行深度分析
        """
        paper = payload.get('paper', {})
        analysis_depth = payload.get('analysis_depth', 'standard')
        
        print(f"[{self.agent_id}] 深度分析论文: {paper.get('title', 'Unknown')[:50]}...")
        
        # 尝试调用深度分析器
        try:
            from deep_paper_analyzer import DeepAnalyzer
            
            analyzer = DeepAnalyzer()
            
            # 构建论文信息
            paper_info = {
                'title': paper.get('title', ''),
                'url': paper.get('url', ''),
                'type': paper.get('type', 'unknown'),
                'authors': paper.get('authors', [])
            }
            
            # 执行深度分析
            analysis = analyzer.analyze_paper(paper_info)
            
            if analysis:
                self.stats['papers_analyzed'] += 1
                
                return {
                    'status': 'success',
                    'paper_title': analysis.paper_title,
                    'core_insight': analysis.key_insight,
                    'relevance_score': analysis.relevance_score,
                    'action_priority': analysis.action_priority,
                    'techniques': [
                        {'name': t.name, 'benefit': t.estimated_benefit}
                        for t in analysis.applicable_techniques
                    ],
                    'suggestions': analysis.improvement_suggestions
                }
            else:
                return {
                    'status': 'failed',
                    'error': '分析返回空结果'
                }
                
        except Exception as e:
            print(f"[{self.agent_id}] 深度分析失败: {e}")
            
            # 降级为简单分析
            return {
                'status': 'degraded',
                'paper_title': paper.get('title', ''),
                'core_insight': '基于标题的简单推断',
                'relevance_score': 0.5,
                'action_priority': 'low',
                'error': str(e)
            }
    
    def _execute_generate_insight(self, payload: Dict) -> Dict[str, Any]:
        """
        执行洞察生成任务
        
        综合多个分析结果生成洞察
        """
        analyses = payload.get('analyses', [])
        
        print(f"[{self.agent_id}] 生成洞察，基于 {len(analyses)} 个分析结果")
        
        # 筛选高优先级洞察
        high_priority = [a for a in analyses if a.get('action_priority') == 'high']
        
        insights = []
        for analysis in high_priority[:3]:  # 最多3个高优先级
            insights.append({
                'source': analysis.get('paper_title', '')[:50],
                'insight': analysis.get('core_insight', ''),
                'techniques': analysis.get('techniques', []),
                'priority': 'high'
            })
        
        return {
            'status': 'success',
            'insights_count': len(insights),
            'insights': insights,
            'summary': f"从 {len(analyses)} 篇论文中提取 {len(insights)} 个高优先级洞察"
        }
    
    def _execute_test_design(self, payload: Dict) -> Dict[str, Any]:
        """
        执行设计测试任务
        
        在沙箱中测试设计方案
        """
        design = payload.get('design', {})
        
        print(f"[{self.agent_id}] 测试设计方案: {design.get('title', 'Unknown')}")
        
        # 模拟沙箱测试
        time.sleep(0.5)  # 模拟测试时间
        
        return {
            'status': 'success',
            'design_id': design.get('id'),
            'test_result': 'passed',
            'risk_score': 25,
            'recommendation': '可以实施'
        }
    
    def get_capabilities(self) -> List[str]:
        """获取支持的任务类型"""
        return list(self.capabilities.keys())
    
    def get_executor_summary(self) -> str:
        """获取执行摘要"""
        lines = [
            f"\n{'='*50}",
            f"[{self.agent_id}] 执行摘要",
            f"{'='*50}",
            f"支持任务: {', '.join(self.get_capabilities())}",
            f"执行任务: {self.stats['tasks_executed']}",
            f"成功: {self.stats['tasks_succeeded']} | 失败: {self.stats['tasks_failed']}",
            f"抓取论文: {self.stats['papers_fetched']}",
            f"深度分析: {self.stats['papers_analyzed']}",
            f"缓存大小: {len(self.cache)}",
            f"{'='*50}\n"
        ]
        return '\n'.join(lines)


def test_executor():
    """测试 Executor Agent"""
    print("="*60)
    print("测试 Executor Agent")
    print("="*60)
    
    from base import AgentCoordinator
    
    # 创建协调器
    coordinator = AgentCoordinator()
    
    # 创建 Executor
    executor = ExecutorAgent('executor_1', coordinator.message_bus)
    coordinator.register_agent(executor)
    
    # 启动
    coordinator.start_all()
    
    # 测试抓取任务
    print("\n--- 测试抓取任务 ---")
    fetch_task = Task(
        type='fetch',
        priority=1,
        payload={
            'source_id': 'arxiv_papers',
            'source_type': 'arxiv',
            'max_items': 3,
            'keywords': ['multi-agent', 'llm']
        }
    )
    coordinator.assign_task(fetch_task, 'executor_1')
    
    time.sleep(1.5)
    
    # 测试分析任务
    print("\n--- 测试分析任务 ---")
    analyze_task = Task(
        type='deep_analyze',
        priority=2,
        payload={
            'paper': {
                'title': 'Test Paper on Multi-Agent Systems',
                'url': 'https://arxiv.org/abs/2603.00001',
                'type': 'multiagent_system'
            },
            'analysis_depth': 'full'
        }
    )
    coordinator.assign_task(analyze_task, 'executor_1')
    
    time.sleep(2.0)
    
    # 查看状态
    print(executor.get_executor_summary())
    
    # 停止
    coordinator.stop_all()
    
    print("\n✅ Executor Agent 测试完成")


if __name__ == '__main__':
    test_executor()
