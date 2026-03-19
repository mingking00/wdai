#!/usr/bin/env python3
"""
evo-002 多Agent协调 Hooks
自动在任务执行时触发多Agent协作

Author: wdai
Version: 1.0
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution_hook_framework import (
    evolution_hook, EvolutionEvent, EventContext
)
from typing import Dict, Any, List
import json
import time


# ============================================================================
# 多Agent协调Hook实现
# ============================================================================

class MultiAgentHooks:
    """多Agent协调自动触发器"""
    
    def __init__(self):
        self.task_complexity_threshold = 0.7  # 复杂度阈值
        self.active_tasks: Dict[str, Any] = {}
        self.agent_assignments = {
            'coder': ['code', 'implement', 'debug', 'write'],
            'reviewer': ['review', 'check', 'verify', 'validate'],
            'researcher': ['research', 'search', 'find', 'analyze'],
            'reflector': ['reflect', 'learn', 'improve', 'optimize']
        }
    
    def on_task_start(self, ctx: EventContext):
        """
        任务开始时：评估复杂度，决定是否需要多Agent
        """
        task_desc = ctx.data.get('description', '')
        task_type = ctx.data.get('task_type', 'general')
        
        # 评估复杂度
        complexity = self._assess_complexity(task_desc, task_type)
        
        # 简单任务跳过
        if complexity < self.task_complexity_threshold:
            return {
                'action': 'single_agent',
                'reason': '复杂度较低，单Agent处理',
                'complexity': complexity
            }
        
        # 复杂任务：分配多Agent
        agents_needed = self._select_agents(task_desc, task_type)
        
        # 记录任务
        task_id = f"task_{int(time.time())}"
        self.active_tasks[task_id] = {
            'description': task_desc,
            'complexity': complexity,
            'agents': agents_needed,
            'started_at': time.time(),
            'status': 'coordinating'
        }
        
        return {
            'action': 'multi_agent',
            'task_id': task_id,
            'complexity': complexity,
            'recommended_agents': agents_needed,
            'coordination_plan': self._create_plan(agents_needed, task_desc)
        }
    
    def on_task_complete(self, ctx: EventContext):
        """
        任务完成时：触发反思Agent进行复盘
        """
        task_desc = ctx.data.get('description', '')
        result = ctx.data.get('result')
        
        # 自动触发反思
        reflection_prompt = self._generate_reflection(task_desc, result)
        
        return {
            'action': 'trigger_reflection',
            'reflection_prompt': reflection_prompt,
            'suggested_reflector': 'reflector'
        }
    
    def on_tool_failed(self, ctx: EventContext):
        """
        工具失败时：自动请求coder Agent协助
        """
        tool_name = ctx.data.get('tool', '')
        error = ctx.data.get('error', '')
        
        # 如果错误包含代码相关关键词
        if any(kw in error.lower() for kw in ['syntax', 'import', 'module', 'error', 'exception']):
            return {
                'action': 'request_assistance',
                'agent': 'coder',
                'issue': f'{tool_name} 调用失败',
                'error': error[:200],
                'auto_fix_suggestion': True
            }
        
        return {'action': 'logged', 'tool': tool_name}
    
    def _assess_complexity(self, desc: str, task_type: str) -> float:
        """评估任务复杂度 0-1"""
        score = 0.5
        
        # 根据类型
        complex_types = ['architecture', 'design', 'implement', 'refactor', 'optimize']
        if any(t in task_type.lower() for t in complex_types):
            score += 0.2
        
        # 根据描述长度和关键词
        desc_lower = desc.lower()
        if len(desc) > 100:
            score += 0.1
        
        complex_keywords = ['multiple', 'complex', 'integrate', 'system', 'framework']
        for kw in complex_keywords:
            if kw in desc_lower:
                score += 0.05
        
        return min(score, 1.0)
    
    def _select_agents(self, desc: str, task_type: str) -> List[str]:
        """选择需要的Agent"""
        desc_lower = desc.lower()
        selected = ['coordinator']  # 总是需要协调者
        
        for agent, keywords in self.agent_assignments.items():
            if any(kw in desc_lower for kw in keywords):
                selected.append(agent)
        
        # 复杂任务自动加入reviewer
        if len(selected) > 2:
            selected.append('reviewer')
        
        return list(set(selected))
    
    def _create_plan(self, agents: List[str], task: str) -> Dict:
        """创建协调计划"""
        plan = {
            'steps': [],
            'parallel_groups': []
        }
        
        if 'researcher' in agents:
            plan['steps'].append({'agent': 'researcher', 'action': 'gather_info', 'task': task})
        
        if 'coder' in agents:
            plan['steps'].append({'agent': 'coder', 'action': 'implement', 'depends_on': 'researcher' if 'researcher' in agents else None})
        
        if 'reviewer' in agents:
            plan['steps'].append({'agent': 'reviewer', 'action': 'review', 'depends_on': 'coder' if 'coder' in agents else None})
        
        return plan
    
    def _generate_reflection(self, task: str, result: Any) -> str:
        """生成反思提示"""
        return f"""请反思以下任务的执行过程:

任务: {task[:100]}

请分析:
1. 执行过程中遇到了哪些问题?
2. 哪些方法有效?哪些无效?
3. 有什么可以改进的地方?
4. 是否有新的发现或洞察?
5. 如何将经验沉淀为可复用的原则?

请提供结构化的反思报告。"""


# ============================================================================
# 注册Hooks
# ============================================================================

_agent_hooks = MultiAgentHooks()

@evolution_hook(EvolutionEvent.TASK_START, priority=20)
def agent_task_start(ctx: EventContext):
    """任务开始时评估是否需要多Agent"""
    return _agent_hooks.on_task_start(ctx)

@evolution_hook(EvolutionEvent.TASK_COMPLETE, priority=20)
def agent_task_complete(ctx: EventContext):
    """任务完成时触发反思"""
    return _agent_hooks.on_task_complete(ctx)

@evolution_hook(EvolutionEvent.TOOL_FAILED, priority=30)
def agent_tool_failed(ctx: EventContext):
    """工具失败时请求协助"""
    return _agent_hooks.on_tool_failed(ctx)


print(f"[evo-002] 多Agent协调 Hooks 已注册")
