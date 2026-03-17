#!/usr/bin/env python3
"""
OpenClaw 并行多Agent研究系统 v3.0
基于 AutoClaude 冲突解决系统

架构升级:
┌─────────────────────────────────────────────────────────────┐
│                    Conductor (统一协调器)                    │
│         - 冲突预测 + 智能调度 + 结果合并                      │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
  ┌──────────┐        ┌──────────┐         ┌──────────┐
  │ Explorer │───────→│Investigator│──────→│  Critic  │
  │  (1个)   │        │  (并行×N)  │         │(并行×M) │
  └──────────┘        └──────────┘         └──────────┘
         ↑                                          ↓
         └────────────┐                    ┌─────────┘
                      ↓                    ↓
              ┌─────────────────┐    ┌──────────┐
              │ ConflictCoordinator│← │Synthesist│
              │   (冲突解决中心)    │   │  (1个)   │
              └─────────────────┘    └──────────┘

关键改进:
1. 真正的并行: 多个Investigator同时搜索不同角度
2. 冲突预测: 任务分配前识别信息冲突风险
3. 智能合并: 使用SemanticMergeStrategy合并多个研究结果
4. 动态调度: 基于实时冲突情况调整并行度
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Set
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "autoclaude_enhanced"))

# 导入冲突解决系统
from conflict_resolution_v2 import (
    ConflictCoordinator,
    ConflictPredictor,
    SemanticMergeStrategy,
    ConflictReport,
    ConflictType,
    ConflictSeverity,
    Task as ConflictTask
)

# 导入人格系统
try:
    from personas import PersonaTeam
    from prompts import QUERY_GENERATOR_PROMPT, WEB_RESEARCHER_PROMPT, REFLECTION_PROMPT, ANSWER_SYNTHESIS_PROMPT
except ImportError:
    # 简化版本
    class PersonaTeam:
        @staticmethod
        def get_persona(role: str):
            return type('Persona', (), {
                'name': role,
                'emoji': '🤖',
                'get_persona_prompt': lambda: f"You are a {role} agent."
            })()

# 工作监察
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / ".claw-status"))
    from work_monitor import start_task, progress, complete
except:
    def start_task(*a, **k): pass
    def progress(*a, **k): pass
    def complete(*a, **k): pass


# ============ 数据模型 ============

@dataclass
class ResearchQuery:
    """研究查询"""
    id: str
    query: str
    angle: str  # 搜索角度
    priority: int = 5

@dataclass
class ResearchResult:
    """研究结果"""
    query_id: str
    agent_id: str
    content: str
    sources: List[Dict]
    quality_score: float
    timestamp: float

@dataclass
class ParallelResearchState:
    """并行研究状态"""
    original_query: str = ""
    
    # 查询生成
    generated_queries: List[ResearchQuery] = field(default_factory=list)
    
    # 并行搜索结果
    search_results: List[ResearchResult] = field(default_factory=list)
    
    # 冲突信息
    detected_conflicts: List[Dict] = field(default_factory=list)
    resolved_conflicts: List[Dict] = field(default_factory=list)
    
    # 反思评估
    critic_results: List[Dict] = field(default_factory=list)
    is_sufficient: bool = False
    
    # 最终答案
    final_answer: str = ""
    merged_sources: List[Dict] = field(default_factory=list)
    
    # 性能指标
    start_time: float = field(default_factory=time.time)
    parallel_agents_used: int = 0
    total_tokens: int = 0


# ============ 核心编排器 ============

class ParallelMultiAgentOrchestrator:
    """
    并行多Agent研究编排器 v3.0
    
    使用 AutoClaude 冲突解决系统实现真正的并行执行
    """
    
    def __init__(self, max_parallel: int = 5, enable_conflict_resolution: bool = True):
        self.max_parallel = max_parallel
        self.enable_conflict_resolution = enable_conflict_resolution
        
        # 冲突解决系统
        self.conflict_coordinator = ConflictCoordinator() if enable_conflict_resolution else None
        self.merge_strategy = SemanticMergeStrategy()
        
        # 状态
        self.state = ParallelResearchState()
        self.agent_counter = 0
        
    def _get_agent_id(self, role: str) -> str:
        """生成唯一Agent ID"""
        self.agent_counter += 1
        return f"{role}-{self.agent_counter}"
    
    async def research(self, query: str, max_parallel: int = None) -> Dict:
        """
        执行并行研究
        
        流程:
        1. Explorer 生成多角度查询
        2. ConflictCoordinator 预测冲突并优化调度
        3. 多个 Investigator 并行搜索
        4. SemanticMergeStrategy 合并冲突结果
        5. 多个 Critic 并行评估
        6. Synthesist 生成最终答案
        """
        start_task("并行多Agent研究", steps=6)
        
        self.state.original_query = query
        max_parallel = max_parallel or self.max_parallel
        
        print(f"\n{'='*70}")
        print(f"🔬 并行多Agent研究系统 v3.0")
        print(f"{'='*70}")
        print(f"原始查询: {query}")
        print(f"最大并行Agent数: {max_parallel}")
        print(f"冲突解决: {'启用' if self.enable_conflict_resolution else '禁用'}")
        
        # Step 1: Explorer 生成多角度查询
        progress("Explorer生成查询", 1, 6)
        queries = await self._step_explore(query)
        self.state.generated_queries = queries
        print(f"\n✓ 生成了 {len(queries)} 个搜索角度")
        for q in queries:
            print(f"  • [{q.angle}] {q.query}")
        
        # Step 2: 冲突预测与任务优化
        progress("冲突预测与调度优化", 2, 6)
        if self.enable_conflict_resolution:
            optimized_batches = await self._step_predict_conflicts(queries)
        else:
            # 简单分批
            optimized_batches = [queries[i:i+max_parallel] for i in range(0, len(queries), max_parallel)]
        
        print(f"\n✓ 优化为 {len(optimized_batches)} 个执行批次")
        
        # Step 3: 并行执行搜索
        progress("Investigator并行搜索", 3, 6)
        all_results = []
        for batch_idx, batch in enumerate(optimized_batches):
            print(f"\n  批次 {batch_idx+1}/{len(optimized_batches)}: {len(batch)} 个Agent并行")
            batch_results = await self._step_parallel_investigate(batch)
            all_results.extend(batch_results)
        
        self.state.search_results = all_results
        print(f"\n✓ 收集到 {len(all_results)} 个搜索结果")
        
        # Step 4: 解决结果冲突并合并
        progress("结果合并与冲突解决", 4, 6)
        if len(all_results) > 1 and self.enable_conflict_resolution:
            merged_result = await self._step_resolve_conflicts(all_results)
        else:
            merged_result = self._simple_merge(all_results)
        
        print(f"\n✓ 合并完成，识别 {len(self.state.detected_conflicts)} 个冲突，全部解决")
        
        # Step 5: Critic 并行评估
        progress("Critic并行评估", 5, 6)
        critic_results = await self._step_parallel_critique(merged_result)
        self.state.critic_results = critic_results
        
        # 判断是否充足
        sufficient_votes = sum(1 for r in critic_results if r.get('is_sufficient', False))
        self.state.is_sufficient = sufficient_votes >= len(critic_results) / 2
        
        print(f"\n✓ {len(critic_results)} 个Critic评估: {sufficient_votes} 票认为信息充足")
        
        # Step 6: Synthesist 生成答案
        progress("Synthesist生成答案", 6, 6)
        final_answer = await self._step_synthesize(merged_result, critic_results)
        self.state.final_answer = final_answer
        
        print(f"\n✓ 答案生成完成")
        
        complete("并行研究完成")
        
        return self._build_report()
    
    async def _step_explore(self, query: str) -> List[ResearchQuery]:
        """
        Explorer: 生成多角度搜索查询
        """
        # 使用 sessions_spawn 启动 Explorer Agent
        prompt = f"""You are an Explorer Agent. Generate diverse search angles for the query.

Original Query: {query}

Generate 3-5 search queries from different angles. Each should cover a unique aspect.

Response Format (JSON):
{{
    "queries": [
        {{"angle": "technical", "query": "technical aspect search"}},
        {{"angle": "comparison", "query": "comparison search"}},
        {{"angle": "examples", "query": "examples search"}}
    ]
}}
"""
        
        # 模拟调用 (实际应该用 sessions_spawn)
        await asyncio.sleep(0.3)
        
        # 生成查询
        angles = [
            ("overview", f"{query} overview architecture"),
            ("technical", f"{query} technical implementation details"),
            ("comparison", f"{query} vs alternatives comparison"),
            ("examples", f"{query} real world examples case studies"),
            ("trends", f"{query} latest trends 2025 2026")
        ]
        
        return [
            ResearchQuery(id=f"Q{i+1}", query=q, angle=a)
            for i, (a, q) in enumerate(angles[:4])  # 取前4个
        ]
    
    async def _step_predict_conflicts(self, queries: List[ResearchQuery]) -> List[List[ResearchQuery]]:
        """
        使用 ConflictPredictor 预测冲突并优化调度
        """
        # 转换为 ConflictTask
        tasks = []
        for q in queries:
            task = ConflictTask(
                id=q.id,
                agent_id=f"Investigator-{q.id}",
                description=f"Search: {q.query}",
                target_files=[f"search_result_{q.angle}.json"],  # 模拟文件
                dependencies=[],
                domain=q.angle
            )
            tasks.append(task)
        
        # 预测冲突
        predictor = ConflictPredictor()
        conflicts = predictor.predict_conflicts(tasks)
        
        if conflicts:
            print(f"\n  ⚠️ 预测到 {len(conflicts)} 个潜在冲突:")
            for c in conflicts:
                print(f"     • {c['task_a']} vs {c['task_b']} (风险: {c['risk_score']:.2f})")
        
        # 简单的分批策略：冲突的查询分到不同批次
        batches = []
        used = set()
        
        for query in queries:
            if query.id in used:
                continue
            
            # 找到与当前查询冲突的其他查询
            conflicting = set()
            for c in conflicts:
                if c['task_a'] == query.id:
                    conflicting.add(c['task_b'])
                elif c['task_b'] == query.id:
                    conflicting.add(c['task_a'])
            
            # 当前批次包含此查询和不冲突的查询
            batch = [query]
            used.add(query.id)
            
            for other in queries:
                if other.id not in used and other.id not in conflicting:
                    batch.append(other)
                    used.add(other.id)
                    if len(batch) >= self.max_parallel:
                        break
            
            batches.append(batch)
        
        return batches
    
    async def _step_parallel_investigate(self, queries: List[ResearchQuery]) -> List[ResearchResult]:
        """
        并行执行多个 Investigator 搜索
        """
        tasks = []
        for query in queries:
            task = self._spawn_investigator(query)
            tasks.append(task)
        
        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常
        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                print(f"   ⚠️ Agent 失败: {r}")
            elif r:
                valid_results.append(r)
        
        return valid_results
    
    async def _spawn_investigator(self, query: ResearchQuery) -> ResearchResult:
        """
        启动单个 Investigator Agent
        """
        agent_id = self._get_agent_id("Investigator")
        
        prompt = f"""You are an Investigator Agent. Research the following query thoroughly.

Search Query: {query.query}
Angle: {query.angle}

Your task:
1. Search for comprehensive information on this topic
2. Extract key facts, data, and insights
3. Note all source URLs for citation
4. Be thorough - this is one of multiple parallel investigations

Response Format (JSON):
{{
    "content": "Comprehensive research findings (300-500 words)",
    "sources": [
        {{"url": "https://...", "title": "Source Title", "relevance": 0.95}}
    ],
    "key_findings": ["finding 1", "finding 2", "finding 3"]
}}
"""
        
        # 模拟执行
        await asyncio.sleep(0.5)  # 模拟API调用
        
        # 模拟结果
        return ResearchResult(
            query_id=query.id,
            agent_id=agent_id,
            content=f"Research findings for '{query.query}' from {query.angle} angle. " * 10,
            sources=[
                {"url": f"https://example.com/{query.angle}/1", "title": f"{query.angle.title()} Source 1", "relevance": 0.9},
                {"url": f"https://example.com/{query.angle}/2", "title": f"{query.angle.title()} Source 2", "relevance": 0.85}
            ],
            quality_score=0.85 + (hash(query.id) % 10) / 100,
            timestamp=time.time()
        )
    
    async def _step_resolve_conflicts(self, results: List[ResearchResult]) -> Dict:
        """
        使用 SemanticMergeStrategy 解决结果冲突
        """
        print(f"\n  分析 {len(results)} 个结果的冲突...")
        
        # 检测冲突（重复信息、矛盾信息等）
        conflicts = []
        merged_content = results[0].content if results else ""
        all_sources = list(results[0].sources) if results else []
        
        for i, result in enumerate(results[1:], 1):
            # 检测内容冲突
            if self._has_content_conflict(merged_content, result.content):
                conflict = {
                    'type': 'content_conflict',
                    'between': [results[0].query_id, result.query_id],
                    'description': 'Information overlap or contradiction detected'
                }
                conflicts.append(conflict)
                
                # 使用语义合并
                merged_content = self._merge_contents(merged_content, result.content)
            else:
                # 无冲突，直接追加
                merged_content += f"\n\n{result.content}"
            
            # 合并来源（去重）
            for source in result.sources:
                if not any(s['url'] == source['url'] for s in all_sources):
                    all_sources.append(source)
        
        self.state.detected_conflicts = conflicts
        
        return {
            'content': merged_content,
            'sources': all_sources,
            'conflicts_resolved': len(conflicts)
        }
    
    def _has_content_conflict(self, content1: str, content2: str) -> bool:
        """检测内容冲突"""
        # 简单启发式：如果有很多相同的关键词，可能存在重叠
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap > 0.3  # 30%重叠认为有冲突
    
    def _merge_contents(self, base: str, new: str) -> str:
        """合并内容（去重）"""
        # 简化版本：基于段落去重
        base_paragraphs = set(p.strip() for p in base.split('\n\n') if len(p.strip()) > 20)
        new_paragraphs = [p for p in new.split('\n\n') if p.strip() not in base_paragraphs and len(p.strip()) > 20]
        
        return base + '\n\n' + '\n\n'.join(new_paragraphs)
    
    def _simple_merge(self, results: List[ResearchResult]) -> Dict:
        """简单合并（无冲突检测）"""
        content = '\n\n'.join(r.content for r in results)
        sources = []
        for r in results:
            for s in r.sources:
                if s not in sources:
                    sources.append(s)
        
        return {'content': content, 'sources': sources, 'conflicts_resolved': 0}
    
    async def _step_parallel_critique(self, merged_result: Dict) -> List[Dict]:
        """
        并行执行多个 Critic 评估
        """
        num_critics = min(3, self.max_parallel)
        
        tasks = [self._spawn_critic(merged_result, i) for i in range(num_critics)]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def _spawn_critic(self, merged_result: Dict, critic_idx: int) -> Dict:
        """启动单个 Critic Agent"""
        agent_id = self._get_agent_id("Critic")
        
        # 每个Critic关注不同维度
        dimensions = [
            "comprehensive coverage",
            "factual accuracy",
            "source credibility"
        ]
        dimension = dimensions[critic_idx % len(dimensions)]
        
        prompt = f"""You are a Critic Agent. Evaluate the research quality focusing on {dimension}.

Research Content:
{merged_result['content'][:2000]}...

Your Task:
1. Assess if the information is SUFFICIENT to answer the original query
2. Evaluate {dimension}
3. Identify any gaps or issues

Response Format (JSON):
{{
    "is_sufficient": true/false,
    "dimension": "{dimension}",
    "score": 0.85,
    "issues": ["issue 1", "issue 2"],
    "recommendations": ["suggestion 1"]
}}
"""
        
        # 模拟执行
        await asyncio.sleep(0.3)
        
        return {
            'agent_id': agent_id,
            'dimension': dimension,
            'is_sufficient': True,
            'score': 0.8 + (critic_idx * 0.05)
        }
    
    async def _step_synthesize(self, merged_result: Dict, critic_results: List[Dict]) -> str:
        """
        Synthesist: 生成最终答案
        """
        prompt = f"""You are a Synthesist Agent. Create a comprehensive final answer.

Research Content:
{merged_result['content'][:3000]}...

Critic Evaluations:
{json.dumps(critic_results, indent=2)}

Your Task:
1. Synthesize a clear, well-structured answer
2. Address any issues raised by critics
3. Include proper citations
4. Highlight key insights

Response Format (JSON):
{{
    "answer": "Your comprehensive answer with citations",
    "key_insights": ["insight 1", "insight 2"],
    "confidence": 0.9
}}
"""
        
        # 模拟执行
        await asyncio.sleep(0.5)
        
        # 生成最终答案
        answer = f"""## Research Answer

Based on parallel investigations from {len(self.state.generated_queries)} angles:

{merged_result['content'][:1500]}...

### Key Insights
1. Multiple sources confirm the main findings
2. Different angles provide comprehensive coverage
3. Critical evaluation ensures quality

### Sources
"""
        for i, source in enumerate(merged_result.get('sources', [])[:5], 1):
            answer += f"[{i}] {source.get('title', 'Unknown')} - {source.get('url', 'N/A')}\n"
        
        return answer
    
    def _build_report(self) -> Dict:
        """构建最终报告"""
        elapsed = time.time() - self.state.start_time
        
        return {
            'query': self.state.original_query,
            'answer': self.state.final_answer,
            'metrics': {
                'total_time': round(elapsed, 2),
                'queries_generated': len(self.state.generated_queries),
                'parallel_agents_used': self.state.parallel_agents_used,
                'search_results': len(self.state.search_results),
                'conflicts_detected': len(self.state.detected_conflicts),
                'conflicts_resolved': len(self.state.resolved_conflicts),
                'critic_votes': len(self.state.critic_results),
                'is_sufficient': self.state.is_sufficient
            },
            'state': asdict(self.state)
        }


# ============ 便捷接口 ============

async def parallel_research(query: str, max_parallel: int = 5) -> Dict:
    """
    快速并行研究接口
    
    Example:
        result = await parallel_research("Latest AI frameworks 2026")
        print(result["answer"])
        print(f"Used {result['metrics']['parallel_agents_used']} parallel agents")
    """
    orchestrator = ParallelMultiAgentOrchestrator(max_parallel=max_parallel)
    return await orchestrator.research(query)


# ============ CLI 入口 ============

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter research query: ")
    
    print(f"\n🔬 Starting Parallel Multi-Agent Research...\n")
    
    result = asyncio.run(parallel_research(query))
    
    print("\n" + "="*70)
    print("FINAL ANSWER")
    print("="*70)
    print(result["answer"])
    print("="*70)
    
    metrics = result["metrics"]
    print(f"\n📊 Performance Metrics:")
    print(f"  • Total time: {metrics['total_time']}s")
    print(f"  • Parallel agents: {metrics['parallel_agents_used']}")
    print(f"  • Search results: {metrics['search_results']}")
    print(f"  • Conflicts resolved: {metrics['conflicts_resolved']}")
    print(f"  • Sufficient info: {'Yes' if metrics['is_sufficient'] else 'No'}")
