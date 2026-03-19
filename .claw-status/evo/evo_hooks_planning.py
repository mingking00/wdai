#!/usr/bin/env python3
"""
evo-006 Planning Hooks
自动在复杂任务中使用ReAct规划

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
# Planning Hook实现
# ============================================================================

class PlanningHooks:
    """自动规划触发器"""
    
    def __init__(self):
        self.planning_threshold = 0.6
        self.active_plans: Dict[str, Any] = {}
    
    def on_session_start(self, ctx: EventContext):
        """会话开始时预加载规划能力"""
        return {
            'planning_available': True,
            'methods': ['react', 'plan_and_solve', 'tot'],
            'threshold': self.planning_threshold
        }
    
    def on_task_start(self, ctx: EventContext):
        """
        任务开始时：判断是否需要规划
        """
        desc = ctx.data.get('description', '')
        
        # 检查是否需要规划
        needs_planning = self._needs_planning(desc)
        
        if needs_planning:
            plan = self._generate_plan(desc)
            return {
                'action': 'use_planning',
                'method': 'react',
                'plan': plan,
                'reason': '任务复杂，建议使用ReAct规划'
            }
        
        return {'action': 'direct_execution', 'reason': '任务简单，直接执行'}
    
    def on_tool_after(self, ctx: EventContext):
        """
        工具调用后：更新规划状态
        """
        tool = ctx.data.get('tool', '')
        result = ctx.data.get('result')
        
        # 这里可以更新ReAct循环的Observation
        return {
            'observation': f'{tool} 执行完成',
            'result_size': len(str(result)) if result else 0
        }
    
    def on_reflection_trigger(self, ctx: EventContext):
        """
        触发反思时：使用规划框架进行深度分析
        """
        topic = ctx.data.get('topic', '')
        
        # 使用ToT (Tree of Thoughts) 进行多角度反思
        perspectives = [
            '执行效率角度',
            '代码质量角度', 
            '用户体验角度',
            '可维护性角度'
        ]
        
        return {
            'action': 'tot_reflection',
            'topic': topic,
            'perspectives': perspectives,
            'suggested_depth': 3
        }
    
    def _needs_planning(self, desc: str) -> bool:
        """判断任务是否需要规划"""
        desc_lower = desc.lower()
        
        # 关键词触发
        planning_keywords = [
            'implement', 'design', 'create', 'build',
            '实现', '设计', '创建', '构建',
            'architecture', 'framework', 'system',
            'optimize', 'refactor', 'improve'
        ]
        
        for kw in planning_keywords:
            if kw in desc_lower:
                return True
        
        # 复杂度触发
        if len(desc) > 80:
            return True
        
        # 多步骤触发
        multi_step_indicators = ['first', 'then', 'finally', 'step', 'and then']
        if any(ind in desc_lower for ind in multi_step_indicators):
            return True
        
        return False
    
    def _generate_plan(self, desc: str) -> Dict:
        """生成ReAct计划"""
        return {
            'thought': f'分析任务: {desc[:50]}...',
            'steps': [
                {'action': 'understand', 'description': '理解任务需求'},
                {'action': 'analyze', 'description': '分析现有资源和约束'},
                {'action': 'plan', 'description': '制定执行计划'},
                {'action': 'execute', 'description': '执行计划'},
                {'action': 'verify', 'description': '验证结果'},
                {'action': 'reflect', 'description': '反思和记录'}
            ],
            'expected_outcome': '完成任务并沉淀经验'
        }


class AutoLearningHooks:
    """自动学习触发器"""
    
    def __init__(self):
        self.learnings: List[Dict] = []
        self.learning_file = Path(__file__).parent.parent / '.learnings' / 'auto_hooks.json'
        self.learning_file.parent.mkdir(exist_ok=True)
        self._load_learnings()
    
    def _load_learnings(self):
        """加载学习记录"""
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r') as f:
                    self.learnings = json.load(f)
            except:
                self.learnings = []
    
    def _save_learnings(self):
        """保存学习记录"""
        try:
            with open(self.learning_file, 'w') as f:
                json.dump(self.learnings[-100:], f, indent=2)  # 只保留最近100条
        except:
            pass
    
    def on_tool_failed(self, ctx: EventContext):
        """工具失败时：自动提取学习"""
        tool = ctx.data.get('tool', '')
        error = ctx.data.get('error', '')
        
        learning = {
            'timestamp': time.time(),
            'type': 'error',
            'tool': tool,
            'error_pattern': self._extract_pattern(error),
            'context': ctx.data.get('args', {})
        }
        
        self.learnings.append(learning)
        self._save_learnings()
        
        # 检查是否有重复错误模式
        similar = [l for l in self.learnings 
                  if l['type'] == 'error' and l['tool'] == tool
                  and l['error_pattern'] == learning['error_pattern']]
        
        if len(similar) >= 3:
            return {
                'action': 'pattern_detected',
                'pattern': learning['error_pattern'],
                'count': len(similar),
                'suggestion': f'{tool} 的此错误模式已出现{len(similar)}次，建议固化到SOUL.md'
            }
        
        return {'action': 'recorded', 'pattern': learning['error_pattern']}
    
    def on_task_complete(self, ctx: EventContext):
        """任务完成时：提取最佳实践"""
        desc = ctx.data.get('description', '')
        result = ctx.data.get('result')
        
        # 简单提取关键词作为学习
        learning = {
            'timestamp': time.time(),
            'type': 'success',
            'task_type': self._classify_task(desc),
            'task_keywords': self._extract_keywords(desc),
            'outcome': 'success'
        }
        
        self.learnings.append(learning)
        self._save_learnings()
        
        return {'action': 'learning_extracted', 'task_type': learning['task_type']}
    
    def _extract_pattern(self, error: str) -> str:
        """提取错误模式"""
        # 简化错误信息
        error = error.lower()
        
        patterns = {
            'timeout': ['timeout', 'timed out', 'connection'],
            'not_found': ['not found', 'enoent', 'does not exist'],
            'permission': ['permission denied', 'eacces', 'unauthorized'],
            'rate_limit': ['rate limit', 'too many requests', '429']
        }
        
        for pattern_name, keywords in patterns.items():
            if any(kw in error for kw in keywords):
                return pattern_name
        
        return 'unknown'
    
    def _classify_task(self, desc: str) -> str:
        """分类任务类型"""
        desc_lower = desc.lower()
        
        if any(w in desc_lower for w in ['write', 'create', 'generate', 'build']):
            return 'creation'
        elif any(w in desc_lower for w in ['fix', 'debug', 'repair', 'solve']):
            return 'debugging'
        elif any(w in desc_lower for w in ['analyze', 'research', 'investigate']):
            return 'analysis'
        elif any(w in desc_lower for w in ['optimize', 'improve', 'refactor']):
            return 'optimization'
        else:
            return 'general'
    
    def _extract_keywords(self, desc: str) -> List[str]:
        """提取关键词"""
        # 简单实现：返回长度>3的词
        words = desc.lower().split()
        return [w for w in words if len(w) > 3][:5]


# ============================================================================
# 注册Hooks
# ============================================================================

_planning_hooks = PlanningHooks()
_learning_hooks = AutoLearningHooks()

@evolution_hook(EvolutionEvent.SESSION_START, priority=30)
def planning_session_start(ctx: EventContext):
    return _planning_hooks.on_session_start(ctx)

@evolution_hook(EvolutionEvent.TASK_START, priority=15)
def planning_task_start(ctx: EventContext):
    return _planning_hooks.on_task_start(ctx)

@evolution_hook(EvolutionEvent.TOOL_AFTER_CALL, priority=20)
def planning_tool_after(ctx: EventContext):
    return _planning_hooks.on_tool_after(ctx)

@evolution_hook(EvolutionEvent.REFLECTION_TRIGGER, priority=10)
def planning_reflection(ctx: EventContext):
    return _planning_hooks.on_reflection_trigger(ctx)

# 自动学习hooks
@evolution_hook(EvolutionEvent.TOOL_FAILED, priority=40)
def learning_tool_failed(ctx: EventContext):
    return _learning_hooks.on_tool_failed(ctx)

@evolution_hook(EvolutionEvent.TASK_COMPLETE, priority=30)
def learning_task_complete(ctx: EventContext):
    return _learning_hooks.on_task_complete(ctx)


print(f"[evo-006] Planning Hooks 已注册")
print(f"[evo-learning] 自动学习 Hooks 已注册")
