#!/usr/bin/env python3
"""
evo-001 自适应RAG Hooks
自动在每次记忆检索前后执行，优化检索质量

Author: wdai
Version: 1.0
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution_hook_framework import (
    evolution_hook, EvolutionEvent, EventContext,
    get_registry
)
from typing import Dict, Any
import json
import time


# ============================================================================
# 自适应RAG Hook实现
# ============================================================================

class AdaptiveRAGHooks:
    """自适应RAG自动触发器"""
    
    def __init__(self):
        self.query_history = []
        self.retrieval_stats = {
            'total_queries': 0,
            'avg_results': 0,
            'low_recall_queries': []
        }
        self._state_file = Path(__file__).parent / '.evo_rag_state.json'
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        if self._state_file.exists():
            try:
                with open(self._state_file, 'r') as f:
                    data = json.load(f)
                    self.retrieval_stats = data.get('stats', self.retrieval_stats)
            except:
                pass
    
    def _save_state(self):
        """保存状态"""
        try:
            with open(self._state_file, 'w') as f:
                json.dump({'stats': self.retrieval_stats}, f, indent=2)
        except:
            pass
    
    def on_memory_before(self, ctx: EventContext):
        """
        memory_search前：分析查询，选择最优策略
        """
        query = ctx.data.get('kwargs', {}).get('query', '')
        if not query:
            return None
        
        # 简单查询分类
        query_type = self._classify_query(query)
        
        # 根据历史调整参数
        if len(self.query_history) > 5:
            similar_queries = [q for q in self.query_history 
                             if self._similarity(q['query'], query) > 0.7]
            if similar_queries and similar_queries[-1].get('recall_low'):
                # 之前类似查询召回率低，建议提高top_k
                return {
                    'action': 'adjust_params',
                    'suggestion': '类似查询历史召回率低，建议增加max_results',
                    'original_max': ctx.data.get('kwargs', {}).get('maxResults', 5),
                    'recommended_max': 10
                }
        
        return {'query_type': query_type, 'action': 'proceed'}
    
    def on_memory_after(self, ctx: EventContext):
        """
        memory_search后：评估检索质量，记录反馈
        """
        query = ctx.data.get('kwargs', {}).get('query', '')
        result = ctx.data.get('result', [])
        
        # 统计
        self.retrieval_stats['total_queries'] += 1
        result_count = len(result) if isinstance(result, list) else 0
        
        # 计算滑动平均
        n = self.retrieval_stats['total_queries']
        old_avg = self.retrieval_stats['avg_results']
        self.retrieval_stats['avg_results'] = (old_avg * (n-1) + result_count) / n
        
        # 检测低召回
        recall_low = result_count < 3 and n > 3
        
        # 记录查询历史
        self.query_history.append({
            'timestamp': time.time(),
            'query': query,
            'results_count': result_count,
            'recall_low': recall_low
        })
        
        # 保持历史长度
        if len(self.query_history) > 50:
            self.query_history = self.query_history[-50:]
        
        # 如果召回率低，记录
        if recall_low:
            self.retrieval_stats['low_recall_queries'].append({
                'query': query,
                'count': result_count,
                'time': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            # 保持列表长度
            if len(self.retrieval_stats['low_recall_queries']) > 10:
                self.retrieval_stats['low_recall_queries'] = \
                    self.retrieval_stats['low_recall_queries'][-10:]
        
        self._save_state()
        
        return {
            'query': query[:50],
            'results': result_count,
            'recall_low': recall_low,
            'stats': {
                'total_queries': self.retrieval_stats['total_queries'],
                'avg_results': round(self.retrieval_stats['avg_results'], 2)
            }
        }
    
    def _classify_query(self, query: str) -> str:
        """简单查询分类"""
        query_lower = query.lower()
        
        if any(w in query_lower for w in ['error', '失败', 'bug', '问题']):
            return 'troubleshooting'
        elif any(w in query_lower for w in ['how', '怎么', '如何', '步骤']):
            return 'procedural'
        elif any(w in query_lower for w in ['what', '什么', '介绍']):
            return 'factual'
        elif any(w in query_lower for w in ['compare', '区别', '对比', 'vs']):
            return 'comparative'
        else:
            return 'general'
    
    def _similarity(self, q1: str, q2: str) -> float:
        """简单相似度计算"""
        set1 = set(q1.lower().split())
        set2 = set(q2.lower().split())
        if not set1 or not set2:
            return 0.0
        intersection = set1 & set2
        return len(intersection) / max(len(set1), len(set2))


# ============================================================================
# 注册Hooks
# ============================================================================

# 创建全局实例
_rag_hooks = AdaptiveRAGHooks()

@evolution_hook(EvolutionEvent.MEMORY_BEFORE_SEARCH, priority=10)
def rag_before_search(ctx: EventContext):
    """memory_search前自动触发"""
    return _rag_hooks.on_memory_before(ctx)

@evolution_hook(EvolutionEvent.MEMORY_AFTER_SEARCH, priority=10)
def rag_after_search(ctx: EventContext):
    """memory_search后自动触发"""
    return _rag_hooks.on_memory_after(ctx)

@evolution_hook(EvolutionEvent.SESSION_START, priority=20)
def rag_session_start(ctx: EventContext):
    """会话开始时加载状态"""
    _rag_hooks._load_state()
    return {
        'status': 'loaded',
        'total_queries': _rag_hooks.retrieval_stats['total_queries'],
        'avg_results': _rag_hooks.retrieval_stats['avg_results']
    }


print(f"[evo-001] 自适应RAG Hooks 已注册")
