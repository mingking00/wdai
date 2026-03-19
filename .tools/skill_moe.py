#!/usr/bin/env python3
"""
Skill-MoE: Mixture-of-Experts for Agent Skills

将MoE架构思维应用到Skill系统：
- Router: 意图识别，动态路由到Top-K Experts
- Experts: 专业化Skill，按需激活
- Load Balancer: 负载均衡，防止单点过载
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))


class ExpertType(Enum):
    """专家类型"""
    SEARCH = "search"           # 搜索专家
    CODE = "code"               # 代码专家
    DOC = "doc"                 # 文档专家
    BROWSER = "browser"         # 浏览器专家
    MEMORY = "memory"           # 记忆专家
    PLAN = "plan"               # 规划专家
    DATA = "data"               # 数据处理专家


@dataclass
class Expert:
    """Skill专家定义"""
    name: str
    expert_type: ExpertType
    description: str
    capabilities: List[str]  # 能处理的任务类型
    activated: bool = False
    load_score: float = 0.0  # 当前负载分数
    success_rate: float = 1.0  # 历史成功率
    
    def can_handle(self, task_type: str) -> float:
        """判断是否能处理某类任务，返回置信度"""
        if task_type in self.capabilities:
            return self.success_rate * (1 - self.load_score)
        return 0.0


@dataclass
class RoutingDecision:
    """路由决策结果"""
    primary_expert: Expert
    supporting_experts: List[Expert]
    routing_confidence: float
    execution_plan: str  # "parallel" | "sequential"


class SkillRouter:
    """
    Skill路由中心
    
    类似MoE中的Router网络，根据用户意图选择Top-K Experts
    """
    
    def __init__(self):
        self.experts: Dict[ExpertType, Expert] = {}
        self._init_experts()
        self.routing_history: List[Dict] = []
    
    def _init_experts(self):
        """初始化所有专家"""
        self.experts = {
            ExpertType.SEARCH: Expert(
                name="SearchExpert",
                expert_type=ExpertType.SEARCH,
                description="搜索和信息检索专家",
                capabilities=["search", "find", "lookup", "query", "web"]
            ),
            ExpertType.CODE: Expert(
                name="CodeExpert",
                expert_type=ExpertType.CODE,
                description="代码分析和生成专家",
                capabilities=["code", "program", "debug", "refactor", "script"]
            ),
            ExpertType.DOC: Expert(
                name="DocExpert",
                expert_type=ExpertType.DOC,
                description="文档处理和分析专家",
                capabilities=["doc", "pdf", "markdown", "read", "analyze"]
            ),
            ExpertType.BROWSER: Expert(
                name="BrowserExpert",
                expert_type=ExpertType.BROWSER,
                description="浏览器自动化专家",
                capabilities=["browse", "visit", "screenshot", "webpage", "crawl"]
            ),
            ExpertType.MEMORY: Expert(
                name="MemoryExpert",
                expert_type=ExpertType.MEMORY,
                description="记忆和上下文管理专家",
                capabilities=["remember", "recall", "context", "history"]
            ),
            ExpertType.PLAN: Expert(
                name="PlanExpert",
                expert_type=ExpertType.PLAN,
                description="任务规划和分解专家",
                capabilities=["plan", "decompose", "schedule", "organize"]
            ),
            ExpertType.DATA: Expert(
                name="DataExpert",
                expert_type=ExpertType.DATA,
                description="数据处理和分析专家",
                capabilities=["data", "csv", "excel", "analyze", "process"]
            )
        }
    
    def analyze_intent(self, query: str) -> Dict[str, float]:
        """
        分析用户意图，返回各任务类型的置信度
        
        类似于MoE中的Router网络前向传播
        """
        query_lower = query.lower()
        scores = {}
        
        # 关键词匹配（简化版，实际可用Embedding）
        keyword_map = {
            "search": ["搜索", "找", "查找", "搜索", "query", "find", "lookup"],
            "code": ["代码", "编程", "debug", "程序", "script", "function", "class"],
            "doc": ["文档", "pdf", "阅读", "分析", "document", "readme", "paper"],
            "browse": ["网页", "浏览", "访问", "网站", "web", "browser", "page"],
            "remember": ["记住", "记忆", "保存", "记录", "recall", "memory"],
            "plan": ["计划", "规划", "分解", "安排", "schedule", "plan", "organize"],
            "data": ["数据", "表格", "csv", "excel", "分析", "data", "table"]
        }
        
        for task_type, keywords in keyword_map.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[task_type] = min(score / 2, 1.0)  # 归一化
        
        return scores
    
    def route(self, query: str, top_k: int = 2) -> RoutingDecision:
        """
        路由决策：选择Top-K Experts
        
        类似MoE中的Top-K Gating机制
        """
        # 分析意图
        intent_scores = self.analyze_intent(query)
        
        # 计算每个专家的综合得分
        expert_scores = []
        for expert in self.experts.values():
            max_score = 0.0
            for task_type, score in intent_scores.items():
                capability_score = expert.can_handle(task_type)
                combined = score * capability_score
                max_score = max(max_score, combined)
            expert_scores.append((expert, max_score))
        
        # 排序选择Top-K
        expert_scores.sort(key=lambda x: x[1], reverse=True)
        
        primary = expert_scores[0][0]
        supporting = [ex[0] for ex in expert_scores[1:top_k] if ex[1] > 0.3]
        
        # 决定执行策略
        execution_plan = "sequential" if len(supporting) > 0 else "parallel"
        
        decision = RoutingDecision(
            primary_expert=primary,
            supporting_experts=supporting,
            routing_confidence=expert_scores[0][1],
            execution_plan=execution_plan
        )
        
        # 记录历史
        self.routing_history.append({
            "query": query,
            "primary": primary.name,
            "supporting": [e.name for e in supporting],
            "confidence": expert_scores[0][1]
        })
        
        # 更新负载
        primary.load_score = min(primary.load_score + 0.1, 1.0)
        for expert in supporting:
            expert.load_score = min(expert.load_score + 0.05, 1.0)
        
        return decision
    
    def get_expert_status(self) -> Dict:
        """获取所有专家状态"""
        return {
            name: {
                "load": expert.load_score,
                "success_rate": expert.success_rate,
                "activated": expert.activated
            }
            for name, expert in self.experts.items()
        }


class MoEOrchestrator:
    """
    MoE编排器
    
    协调多个Expert的执行，实现负载均衡和结果融合
    """
    
    def __init__(self):
        self.router = SkillRouter()
        self.execution_history: List[Dict] = []
    
    def execute(self, query: str) -> Dict[str, Any]:
        """
        执行用户请求
        
        全流程：意图分析 → 专家路由 → 并行/串行执行 → 结果融合
        """
        print(f"🎯 分析意图: {query}")
        
        # 1. 路由决策
        decision = self.router.route(query)
        
        print(f"🧠 主专家: {decision.primary_expert.name} (置信度: {decision.routing_confidence:.2f})")
        if decision.supporting_experts:
            print(f"🤝 协助专家: {[e.name for e in decision.supporting_experts]}")
        print(f"📋 执行策略: {decision.execution_plan}")
        
        # 2. 执行（简化版，实际调用具体Skill）
        results = self._execute_with_experts(decision, query)
        
        # 3. 记录
        self.execution_history.append({
            "query": query,
            "decision": decision,
            "results": results
        })
        
        return results
    
    def _execute_with_experts(self, decision: RoutingDecision, query: str) -> Dict:
        """使用选定的Experts执行任务"""
        # 这里简化处理，实际应调用具体的Skill实现
        results = {
            "primary": {
                "expert": decision.primary_expert.name,
                "type": decision.primary_expert.expert_type.value,
                "status": "activated"
            },
            "supporting": [
                {
                    "expert": e.name,
                    "type": e.expert_type.value,
                    "status": "activated"
                }
                for e in decision.supporting_experts
            ],
            "execution_plan": decision.execution_plan,
            "query": query
        }
        
        return results
    
    def get_system_status(self) -> Dict:
        """获取系统整体状态"""
        return {
            "router_status": {
                name.value: {
                    "load": expert.load_score,
                    "success_rate": expert.success_rate,
                    "activated": expert.activated
                }
                for name, expert in self.router.experts.items()
            },
            "routing_history_count": len(self.router.routing_history),
            "execution_count": len(self.execution_history)
        }


def demo():
    """演示MoE Skill系统"""
    print("=" * 60)
    print("🧠 Skill-MoE: Mixture-of-Experts for Agent Skills")
    print("=" * 60)
    
    orchestrator = MoEOrchestrator()
    
    # 测试用例
    test_queries = [
        "帮我搜索Python教程",
        "分析这段代码的bug",
        "阅读这份PDF文档并总结",
        "访问这个网站并截图",
        "记住我刚才说的重要事项",
        "制定一个学习计划",
        "处理这个CSV文件",
        "搜索代码示例并解释给我听"  # 复合任务
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        result = orchestrator.execute(query)
        print(f"✅ 执行完成")
    
    # 显示系统状态
    print(f"\n{'='*60}")
    print("📊 系统状态")
    print("=" * 60)
    status = orchestrator.get_system_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    demo()
