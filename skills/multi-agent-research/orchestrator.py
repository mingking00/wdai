#!/usr/bin/env python3
"""
OpenClaw Multi-Agent System - Based on Gemini LangGraph Quickstart

核心架构（参考: google-gemini/gemini-fullstack-langgraph-quickstart）:
┌─────────────────────────────────────────────────────────────┐
│                    Research Orchestrator                     │
│                    (研究任务编排器)                          │
└─────────────────────────────────────────────────────────────┘
        ↓                    ↓                    ↓
   ┌──────────┐      ┌──────────┐         ┌──────────┐
   │  Query   │      │  Web     │         │Reflection│
   │Generator │─────→│ Research │────────→│  Agent   │
   │ (查询生成)│      │ (网络搜索)│         │(反思评估)│
   └──────────┘      └──────────┘         └──────────┘
                                                ↓
                                         信息不足? 返回继续搜索
                                         信息充足? ↓
                                    ┌──────────┐
                                    │  Answer  │
                                    │Synthesis │
                                    │(答案合成)│
                                    └──────────┘

关键设计借鉴:
1. 状态驱动 (State-Driven) - 通过 ResearchState 共享上下文
2. 并行执行 - 多个搜索查询同时执行 (使用 sessions_spawn)
3. 反思迭代 - Reflection Agent 决定是否继续搜索
4. 带引用输出 - 所有答案附带来源引用
"""

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入人格系统
from personas import PersonaTeam, AgentPersona
from prompts import format_prompt, (
    QUERY_GENERATOR_PROMPT,
    WEB_RESEARCHER_PROMPT,
    REFLECTION_PROMPT,
    ANSWER_SYNTHESIS_PROMPT
)

class AgentRole(Enum):
    """智能体角色定义 (参考 Gemini Quickstart)"""
    QUERY_GENERATOR = "query_generator"      # 查询生成器
    WEB_RESEARCHER = "web_researcher"        # 网络研究员
    REFLECTION = "reflection"                # 反思评估员
    ANSWER_SYNTHESIS = "answer_synthesis"    # 答案合成器
    PROGRESS_REPORTER = "progress_reporter"  # 进度报告员

@dataclass
class ResearchState:
    """
    研究状态 (参考: backend/src/agent/state.py)
    
    所有智能体共享的状态，通过消息传递更新
    """
    # 输入
    original_query: str = ""                    # 原始用户查询
    
    # 中间产物
    search_queries: List[str] = field(default_factory=list)      # 生成的搜索查询
    web_results: List[Dict] = field(default_factory=list)        # 网络搜索结果
    sources_gathered: List[Dict] = field(default_factory=list)   # 收集的引用源
    
    # 反思结果
    is_sufficient: bool = False                 # 信息是否充足
    knowledge_gap: str = ""                     # 知识缺口描述
    follow_up_queries: List[str] = field(default_factory=list)   # 后续查询
    
    # 迭代控制
    research_loop_count: int = 0                # 研究循环次数
    max_research_loops: int = 3                 # 最大循环次数
    
    # 输出
    final_answer: str = ""                      # 最终答案
    citations: List[Dict] = field(default_factory=list)          # 引用列表
    
    # 元数据
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"                     # pending/running/completed/failed

@dataclass
class AgentConfig:
    """智能体配置"""
    role: AgentRole
    model: str = "kimi-coding/k2p5"             # 默认使用 Kimi
    thinking: str = "medium"                    # 思考级别
    timeout: int = 300                          # 超时秒数

class MultiAgentOrchestrator:
    """
    多智能体编排器 (核心控制器)
    
    参考: backend/src/agent/graph.py 中的 StateGraph
    """
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.state = ResearchState()
        
    async def run(self, query: str) -> ResearchState:
        """
        执行完整研究流程
        
        流程: 
        生成查询 → 并行搜索 → 反思评估 → (循环或完成) → 合成答案
        """
        self.state.original_query = query
        self.state.status = "running"
        
        print(f"\n{'='*60}")
        print(f"🔬 启动多智能体研究: {query[:50]}...")
        print(f"{'='*60}\n")
        
        # Step 1: 生成搜索查询
        print("[1/5] Query Generator: 生成搜索查询...")
        await self._step_query_generation()
        
        # 研究循环
        while self.state.research_loop_count < self.state.max_research_loops:
            self.state.research_loop_count += 1
            print(f"\n{'─'*60}")
            print(f"📚 研究循环 #{self.state.research_loop_count}/{self.state.max_research_loops}")
            print(f"{'─'*60}")
            
            # Step 2: 并行网络搜索
            print(f"[2/5] Web Researchers ({len(self.state.search_queries)}个并行)...")
            await self._step_web_research()
            
            # Step 3: 反思评估
            print("[3/5] Reflection Agent: 评估信息充足度...")
            await self._step_reflection()
            
            # Step 4: 决策
            if self.state.is_sufficient:
                print("✅ 信息充足，准备生成答案")
                break
            else:
                print(f"🔄 信息不足，继续搜索: {self.state.knowledge_gap[:100]}...")
                self.state.search_queries = self.state.follow_up_queries
        
        # Step 5: 合成答案
        print("\n[5/5] Answer Synthesis: 生成最终答案...")
        await self._step_answer_synthesis()
        
        self.state.status = "completed"
        
        # 打印结果摘要
        self._print_summary()
        
        return self.state
    
    async def _step_query_generation(self):
        """步骤1: 查询生成 (对应 generate_query node)"""
        
        prompt = f"""You are a Query Generation Agent. Your task is to generate effective search queries.

Original User Query: {self.state.original_query}

Generate 3-5 diverse search queries that will help gather comprehensive information.
Consider different angles and aspects of the question.

Requirements:
1. Each query should be specific and targeted
2. Cover different aspects (what, why, how, examples, comparisons)
3. Use keywords that would appear in authoritative sources

Response Format (JSON):
{{
    "queries": [
        "first search query",
        "second search query",
        "third search query"
    ],
    "reasoning": "brief explanation of why these queries cover the topic comprehensively"
}}
"""
        
        # 使用 sessions_spawn 启动 Query Generator Agent
        result = await self._spawn_agent(
            AgentConfig(AgentRole.QUERY_GENERATOR),
            prompt
        )
        
        try:
            data = json.loads(result)
            self.state.search_queries = data.get("queries", [self.state.original_query])
            print(f"   生成了 {len(self.state.search_queries)} 个查询")
            for i, q in enumerate(self.state.search_queries, 1):
                print(f"   {i}. {q}")
        except:
            # 容错：使用原始查询
            self.state.search_queries = [self.state.original_query]
    
    async def _step_web_research(self):
        """步骤2: 并行网络搜索 (对应 web_research node + parallel branches)"""
        
        # 创建并行搜索任务
        tasks = []
        for idx, search_query in enumerate(self.state.search_queries):
            task = self._spawn_web_researcher(search_query, idx)
            tasks.append(task)
        
        # 并行执行所有搜索
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集结果
        for result in results:
            if isinstance(result, Exception):
                print(f"   ⚠️ 搜索失败: {result}")
                continue
                
            if result:
                self.state.web_results.extend(result.get("results", []))
                self.state.sources_gathered.extend(result.get("sources", []))
        
        print(f"   收集到 {len(self.state.web_results)} 条结果, {len(self.state.sources_gathered)} 个引用源")
    
    async def _spawn_web_researcher(self, query: str, idx: int) -> Dict:
        """启动单个网络研究员 Agent"""
        
        prompt = f"""You are a Web Research Agent. Search for information on the given query.

Search Query: {query}

Your task:
1. Search the web for relevant information
2. Extract key facts, data, and insights
3. Note the source URLs for citation

Response Format (JSON):
{{
    "results": [
        {{
            "title": "result title",
            "content": "key information extracted",
            "relevance": 0.95
        }}
    ],
    "sources": [
        {{
            "url": "https://example.com/article",
            "title": "Source Title",
            "accessed_date": "2026-03-10"
        }}
    ]
}}
"""
        
        result = await self._spawn_agent(
            AgentConfig(AgentRole.WEB_RESEARCHER, timeout=180),
            prompt,
            agent_id=f"web_researcher_{idx}"
        )
        
        try:
            return json.loads(result)
        except:
            return {"results": [], "sources": []}
    
    async def _step_reflection(self):
        """步骤3: 反思评估 (对应 reflection node)"""
        
        # 准备上下文
        research_summary = "\n\n".join([
            f"- {r.get('title', 'Untitled')}: {r.get('content', '')[:200]}..."
            for r in self.state.web_results[:5]  # 取前5条
        ])
        
        prompt = f"""You are a Reflection Agent. Evaluate the research quality and identify knowledge gaps.

Original Query: {self.state.original_query}

Research Results Summary:
{research_summary}

Your Task:
1. Assess if the gathered information is SUFFICIENT to answer the original query
2. Identify any KNOWLEDGE GAPS - what important information is missing?
3. If insufficient, generate FOLLOW-UP QUERIES to fill the gaps

Response Format (JSON):
{{
    "is_sufficient": true/false,
    "knowledge_gap": "description of what's missing or why current info is insufficient",
    "follow_up_queries": ["query 1", "query 2"]  // only if is_sufficient is false
}}

Be critical. If information is incomplete, contradictory, or lacks depth, mark as insufficient.
"""
        
        result = await self._spawn_agent(
            AgentConfig(AgentRole.REFLECTION),
            prompt
        )
        
        try:
            data = json.loads(result)
            self.state.is_sufficient = data.get("is_sufficient", False)
            self.state.knowledge_gap = data.get("knowledge_gap", "")
            self.state.follow_up_queries = data.get("follow_up_queries", [])
            
            if self.state.is_sufficient:
                print(f"   ✓ 评估结果: 信息充足")
            else:
                print(f"   ✗ 评估结果: 信息不足 - {self.state.knowledge_gap[:150]}...")
                print(f"   生成 {len(self.state.follow_up_queries)} 个后续查询")
                
        except Exception as e:
            print(f"   ⚠️ 反思解析失败: {e}, 默认继续")
            self.state.is_sufficient = False
    
    async def _step_answer_synthesis(self):
        """步骤5: 答案合成 (对应 finalize_answer node)"""
        
        # 准备所有收集的信息
        all_content = "\n\n---\n\n".join([
            f"Source {i+1}: {r.get('content', '')}"
            for i, r in enumerate(self.state.web_results)
        ])
        
        sources_formatted = "\n".join([
            f"[{i+1}] {s.get('title', 'Unknown')} - {s.get('url', 'N/A')}"
            for i, s in enumerate(self.state.sources_gathered)
        ])
        
        prompt = f"""You are an Answer Synthesis Agent. Create a comprehensive, well-cited answer.

Original Query: {self.state.original_query}

Research Content:
{all_content[:8000]}  // 限制长度避免超限

Your Task:
1. Synthesize a clear, comprehensive answer
2. Structure with logical flow (introduction, key points, conclusion)
3. CITE sources using [1], [2], etc. format
4. Include only information supported by the research
5. If there are conflicting sources, note the discrepancy

Response Format:
{{
    "answer": "Your comprehensive answer with inline citations like [1], [2]...",
    "key_points": ["point 1", "point 2", "point 3"],
    "confidence": 0.85  // 0-1 confidence in the answer
}}

Sources for citation:
{sources_formatted}
"""
        
        result = await self._spawn_agent(
            AgentConfig(AgentRole.ANSWER_SYNTHESIS, thinking="high"),
            prompt
        )
        
        try:
            data = json.loads(result)
            self.state.final_answer = data.get("answer", "")
            self.state.citations = self.state.sources_gathered
            
            # 添加引用列表到答案末尾
            if self.state.citations:
                self.state.final_answer += "\n\n## Sources\n"
                for i, cite in enumerate(self.state.citations, 1):
                    self.state.final_answer += f"[{i}] {cite.get('title', 'Unknown')} - {cite.get('url', 'N/A')}\n"
                    
        except Exception as e:
            print(f"   ⚠️ 答案合成失败: {e}")
            self.state.final_answer = "Unable to synthesize answer due to processing error."
    
    async def _spawn_agent(self, config: AgentConfig, task_prompt: str, agent_id: str = None) -> str:
        """
        使用 OpenClaw sessions_spawn 启动子智能体 (带人格)
        
        关键：每个Agent有自己的核心特质，符合其职责
        """
        agent_name = agent_id or config.role.value
        
        # 获取人格定义
        persona = PersonaTeam.get_persona(config.role.value)
        if not persona:
            persona = PersonaTeam.get_persona("conductor")  # 默认
        
        # 构建带人格的完整提示词
        full_prompt = f"""{persona.get_persona_prompt()}

{'='*60}
ASSIGNED TASK
{'='*60}

{task_prompt}

{'='*60}
REMEMBER:
- Stay true to your core traits: {', '.join(persona.core_traits[:3])}
- Your catchphrase is: "{persona.catchphrase}"
- Be aware of your weakness: {persona.failure_mode}
- Return ONLY the requested format, but let your personality shine through in how you approach it
"""
        
        print(f"   🤖 Spawning {persona.emoji} {persona.name} for task...")
        
        try:
            # 使用 sessions_spawn 启动子Agent
            # 注意：这是异步调用，多个Agent可以并行
            result = await asyncio.wait_for(
                self._call_sessions_spawn(full_prompt, config),
                timeout=config.timeout
            )
            return result
        except asyncio.TimeoutError:
            print(f"   ⚠️ Agent {persona.name} 超时")
            return "{}"
        except Exception as e:
            print(f"   ⚠️ Agent {persona.name} 错误: {e}")
            return "{}"
    
    async def _call_sessions_spawn(self, task: str, config: AgentConfig) -> str:
        """
        调用 OpenClaw sessions_spawn
        
        实际实现会使用 OpenClaw API
        """
        # 这里是模拟实现
        # 实际应该调用: sessions_spawn(task=task, model=config.model, ...)
        
        # 模拟延迟
        await asyncio.sleep(0.5)
        
        # 返回模拟结果
        return json.dumps({
            "status": "simulated",
            "role": config.role.value,
            "task_preview": task[:100]
        })
    
    def _print_summary(self):
        """打印研究摘要"""
        print(f"\n{'='*60}")
        print("📊 研究完成摘要")
        print(f"{'='*60}")
        print(f"原始查询: {self.state.original_query[:60]}...")
        print(f"研究循环: {self.state.research_loop_count} 次")
        print(f"搜索结果: {len(self.state.web_results)} 条")
        print(f"引用来源: {len(self.state.citations)} 个")
        print(f"\n📝 答案预览:")
        print(f"{self.state.final_answer[:300]}...")
        print(f"\n{'='*60}\n")

# ============ 便捷接口 ============

async def research(query: str, max_loops: int = 3) -> Dict:
    """
    快速研究接口
    
    Example:
        result = await research("What are the latest AI agent frameworks in 2026?")
        print(result["answer"])
    """
    orchestrator = MultiAgentOrchestrator()
    orchestrator.state.max_research_loops = max_loops
    
    final_state = await orchestrator.run(query)
    
    return {
        "query": final_state.original_query,
        "answer": final_state.final_answer,
        "citations": final_state.citations,
        "loops": final_state.research_loop_count,
        "sources_count": len(final_state.citations),
        "raw_state": asdict(final_state)
    }

# ============ CLI 入口 ============

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter research query: ")
    
    print(f"\n🔬 Starting Multi-Agent Research...\n")
    
    result = asyncio.run(research(query))
    
    print("\n" + "="*60)
    print("FINAL ANSWER")
    print("="*60)
    print(result["answer"])
    print("="*60)
    print(f"\n📚 Total sources: {result['sources_count']}")
    print(f"🔄 Research loops: {result['loops']}")
