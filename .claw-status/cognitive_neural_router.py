#!/usr/bin/env python3
"""
WDai 认知-神经混合架构 (Cognitive-Neural Hybrid Architecture)
可解释路由层 + System 1/2 双路径决策
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class RouteType(Enum):
    """路由类型"""
    SYMBOLIC = "symbolic"      # 符号推理 (System 2)
    NEURAL = "neural"          # 神经网络/模式匹配 (System 1)
    HYBRID = "hybrid"          # 混合路径


@dataclass
class RoutingDecision:
    """路由决策记录"""
    query: str
    route_type: RouteType
    confidence: float
    reasoning: str
    execution_time_ms: float
    timestamp: str
    success: Optional[bool] = None


class ExplainableRouter:
    """可解释路由器"""
    
    def __init__(self, workspace: str = "/root/.openclaw/workspace"):
        self.workspace = Path(workspace)
        self.router_dir = self.workspace / ".claw-status" / "router"
        self.router_dir.mkdir(parents=True, exist_ok=True)
        
        # 决策日志
        self.decisions_file = self.router_dir / "routing_decisions.jsonl"
        
        # 规则引擎 (System 2触发条件)
        self.symbolic_triggers = {
            'complex_patterns': [
                r'为什么|原理|解释|分析|对比|比较',
                r'设计|架构|优化|改进|重构',
                r'如果|假设|场景|边界|异常',
            ],
            'multi_step': [
                r'然后|接着|之后|最后|步骤',
                r'先.*再.*最后',
            ],
            'uncertainty': [
                r'可能|也许|不确定|疑问',
                r'如何.*最好|最优|最有效',
            ]
        }
        
        # 快速模式 (System 1触发条件)
        self.neural_triggers = {
            'factual': [
                r'是什么|什么是|定义|概念',
                r'谁|哪里|什么时候',
            ],
            'procedural': [
                r'怎么做|如何|命令|代码',
                r'运行|执行|启动|停止',
            ],
            'retrieval': [
                r'查找|搜索|检索|找到',
                r'之前|上次|以前说过',
            ]
        }
        
        # 统计
        self.stats = {'symbolic': 0, 'neural': 0, 'hybrid': 0}
    
    def route(self, query: str, context: Dict = None) -> Tuple[RouteType, Dict]:
        """
        智能路由决策
        """
        start_time = datetime.now()
        
        # 1. 计算各路径得分
        symbolic_score = self._evaluate_symbolic(query)
        neural_score = self._evaluate_neural(query)
        
        # 2. 决定路由
        route_type, confidence, reasoning = self._decide_route(
            query, symbolic_score, neural_score
        )
        
        # 3. 记录决策
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        decision = RoutingDecision(
            query=query[:100],
            route_type=route_type.value,
            confidence=confidence,
            reasoning=reasoning,
            execution_time_ms=execution_time,
            timestamp=datetime.now().isoformat()
        )
        
        self._log_decision(decision)
        self.stats[route_type.value] += 1
        
        # 4. 返回执行配置
        config = self._get_execution_config(route_type, query, context)
        
        return route_type, config
    
    def _evaluate_symbolic(self, query: str) -> float:
        """评估符号推理适合度 (System 2)"""
        score = 0.0
        
        # 复杂模式匹配
        for category, patterns in self.symbolic_triggers.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    score += 0.3
        
        # 查询长度（长查询更可能需要深度推理）
        if len(query) > 50:
            score += 0.2
        
        # 关键词密度
        complex_words = ['分析', '设计', '优化', '架构', '策略', '方案']
        for word in complex_words:
            if word in query:
                score += 0.15
        
        return min(1.0, score)
    
    def _evaluate_neural(self, query: str) -> float:
        """评估神经网络适合度 (System 1)"""
        score = 0.0
        
        # 快速模式匹配
        for category, patterns in self.neural_triggers.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    score += 0.35
        
        # 短查询更适合快速响应
        if len(query) < 30:
            score += 0.2
        
        return min(1.0, score)
    
    def _decide_route(self, query: str, symbolic_score: float, neural_score: float) -> Tuple[RouteType, float, str]:
        """做出路由决策"""
        
        diff = abs(symbolic_score - neural_score)
        
        if diff < 0.2:
            # 分数接近，使用混合路径
            confidence = (symbolic_score + neural_score) / 2
            reasoning = f"符号得分:{symbolic_score:.2f}, 神经得分:{neural_score:.2f}, 差距小，使用混合路径"
            return RouteType.HYBRID, confidence, reasoning
        
        elif symbolic_score > neural_score:
            # 符号推理更适合
            confidence = symbolic_score
            reasoning = f"检测到复杂模式(得分:{symbolic_score:.2f})，需要深度推理"
            return RouteType.SYMBOLIC, confidence, reasoning
        
        else:
            # 神经网络更适合
            confidence = neural_score
            reasoning = f"匹配快速模式(得分:{neural_score:.2f})，使用快速响应"
            return RouteType.NEURAL, confidence, reasoning
    
    def _get_execution_config(self, route_type: RouteType, query: str, context: Dict) -> Dict:
        """获取执行配置"""
        
        base_config = {
            'query': query,
            'context': context or {},
            'route_type': route_type.value
        }
        
        if route_type == RouteType.SYMBOLIC:
            return {
                **base_config,
                'thinking': 'high',
                'tools': ['memory_search', 'multi_agent_research', 'planning'],
                'max_steps': 10,
                'verification_required': True
            }
        
        elif route_type == RouteType.NEURAL:
            return {
                **base_config,
                'thinking': 'off',
                'tools': ['memory_retrieve', 'quick_search'],
                'max_steps': 3,
                'verification_required': False
            }
        
        else:  # HYBRID
            return {
                **base_config,
                'thinking': 'medium',
                'tools': ['memory_search', 'flexible_retrieval'],
                'max_steps': 6,
                'verification_required': True
            }
    
    def _log_decision(self, decision: RoutingDecision):
        """记录决策日志"""
        with open(self.decisions_file, 'a') as f:
            f.write(json.dumps(asdict(decision)) + '\n')
    
    def update_feedback(self, query: str, route_type: RouteType, success: bool):
        """更新反馈，用于持续优化"""
        # 更新最近匹配的决策
        if self.decisions_file.exists():
            lines = []
            updated = False
            
            with open(self.decisions_file) as f:
                for line in f:
                    decision = json.loads(line)
                    if decision['query'] == query[:100] and not updated:
                        decision['success'] = success
                        updated = True
                    lines.append(json.dumps(decision))
            
            with open(self.decisions_file, 'w') as f:
                f.write('\n'.join(lines) + '\n')
    
    def get_statistics(self) -> Dict:
        """获取路由统计"""
        total = sum(self.stats.values())
        if total == 0:
            return {'total': 0}
        
        return {
            'total': total,
            'symbolic': self.stats['symbolic'],
            'neural': self.stats['neural'],
            'hybrid': self.stats['hybrid'],
            'symbolic_pct': f"{self.stats['symbolic']/total*100:.1f}%",
            'neural_pct': f"{self.stats['neural']/total*100:.1f}%",
            'hybrid_pct': f"{self.stats['hybrid']/total*100:.1f}%"
        }
    
    def analyze_decisions(self, n: int = 100) -> Dict:
        """分析最近决策质量"""
        if not self.decisions_file.exists():
            return {'message': '暂无决策记录'}
        
        decisions = []
        with open(self.decisions_file) as f:
            for line in f:
                decisions.append(json.loads(line))
        
        recent = decisions[-n:]
        
        # 统计成功率
        with_feedback = [d for d in recent if d.get('success') is not None]
        if with_feedback:
            success_rate = sum(d['success'] for d in with_feedback) / len(with_feedback)
        else:
            success_rate = None
        
        # 平均执行时间
        avg_time = sum(d['execution_time_ms'] for d in recent) / len(recent)
        
        return {
            'analyzed': len(recent),
            'success_rate': f"{success_rate*100:.1f}%" if success_rate else 'N/A',
            'avg_execution_ms': f"{avg_time:.1f}",
            'route_distribution': {
                'symbolic': len([d for d in recent if d['route_type'] == 'symbolic']),
                'neural': len([d for d in recent if d['route_type'] == 'neural']),
                'hybrid': len([d for d in recent if d['route_type'] == 'hybrid'])
            }
        }


def main():
    """演示"""
    router = ExplainableRouter()
    
    test_queries = [
        "什么是ReAct模式？",  # 应该走NEURAL
        "为什么ReAct比直接生成更好？",  # 应该走SYMBOLIC
        "帮我找一下之前的代码",  # 应该走NEURAL
        "如何设计一个可扩展的Agent架构？",  # 应该走SYMBOLIC或HYBRID
    ]
    
    print("=" * 60)
    print("认知-神经混合架构演示")
    print("=" * 60)
    
    for query in test_queries:
        route_type, config = router.route(query)
        print(f"\n📝 查询: {query}")
        print(f"   路由: {route_type.value.upper()}")
        print(f"   配置: thinking={config['thinking']}, tools={len(config['tools'])}个")
    
    print(f"\n{'='*60}")
    print("路由统计:")
    stats = router.get_statistics()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
