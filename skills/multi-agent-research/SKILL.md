---
name: multi-agent-research
description: "Parallel multi-agent research system v3.0. Features true parallel execution with conflict resolution: Explorer (query generation), parallel Investigators (web research), parallel Critics (reflection with voting), and Synthesist (answer synthesis). Built on AutoClaude conflict resolution system."
---

# Multi-Agent Research System v3.0 🔬

> **NEW**: Now with true parallel execution and conflict resolution!
> 
> Based on [google-gemini/gemini-fullstack-langgraph-quickstart](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart)
> Enhanced with [AutoClaude Conflict Resolution System](../autoclaude_enhanced/)

A collaborative multi-agent system with **true parallelism** - multiple agents work simultaneously with intelligent conflict detection and resolution.

## 🚀 Resident Service

MARS (Multi-Agent Research Service) now runs as a **resident service**!

```bash
# Start the resident service
./mars.sh start

# Submit research request
./mars.sh quick "Latest AI breakthroughs"

# Check status
./mars.sh status
```

See [SERVICE.md](SERVICE.md) for details.

## 🎭 The Agent Team

| Agent | Persona | Core Traits | Role | Parallel |
|-------|---------|-------------|------|----------|
| 🔭 **Explorer** | Curious & Divergent | 好奇驱动、发散思维、全面覆盖 | Query Generation | ×1 |
| 🔍 **Investigator** | Rigorous & Detail-oriented | 严谨求实、细致入微、溯源本能 | Web Research | **×N** |
| 🎯 **Critic** | Critical & Insightful | 批判审视、审慎判断、洞察本质 | Reflection | **×M** |
| 🎨 **Synthesist** | Integrative & Clear | 整合能力、清晰表达、结构思维 | Answer Synthesis | ×1 |
| 📡 **Anchor** | Transparent & Patient | 透明沟通、及时反馈、通俗解释 | Progress Reporting | ×1 |
| 🎼 **Conductor** | Strategic & Decisive | 全局视野、节奏控制、果断决策 | Orchestration | ×1 |

## 🆕 What's New in v3.0

### True Parallel Execution
```
Previous (v2.0):        Now (v3.0):
┌──────────┐           ┌──────────┐
│ Explorer │           │ Explorer │
└────┬─────┘           └────┬─────┘
     ↓                       ↓
┌──────────┐           ┌──────────┐
│Inv(并行) │           │Inv(并行×N)│ ← 多个同时搜索
└────┬─────┘           └────┬─────┘
     ↓                       ↓
┌──────────┐           ┌──────────┐
│  Critic  │           │Critic(×M)│ ← 多维度评估
└────┬─────┘           └────┬─────┘
     ↓                       ↓
┌──────────┐           ┌──────────┐
│Synthesist│           │Synthesist│
└──────────┘           └──────────┘
                       
  简单合并                ConflictCoordinator
                        - 冲突预测
                        - 智能调度  
                        - 语义合并
```

### Key Improvements
- ✅ **Multiple Investigators**: Search from different angles simultaneously
- ✅ **Conflict Prediction**: Detect potential conflicts before execution
- ✅ **Semantic Merge**: Intelligently merge overlapping results
- ✅ **Parallel Critics**: Multiple critics vote on information sufficiency
- ✅ **Smart Scheduling**: Optimize batch execution based on conflict analysis

## 🔄 Workflow

```
User Query
    ↓
🔭 Explorer → Generates diverse search queries (multiple angles)
    ↓
🎼 Conductor → Predicts conflicts, optimizes execution batches
    ↓
🔍 Investigators → Parallel web research (N instances simultaneously)
    ↓
⚡ Conflict Resolution → Merge overlapping/conflicting results
    ↓
🎯 Critics → Parallel evaluation (M critics vote on sufficiency)
    ↓
🎨 Synthesist → Creates comprehensive, cited answer
    ↓
📡 Anchor → Reports progress throughout
```

## 🚀 Quick Start

### Basic Usage (NEW - Parallel Version)

```python
from parallel_orchestrator import parallel_research
import asyncio

# Run parallel research
result = asyncio.run(parallel_research(
    "Latest AI agent frameworks 2026",
    max_parallel=5
))

print(result["answer"])
print(f"Sources: {len(result['state']['merged_sources'])}")
print(f"Conflicts resolved: {result['metrics']['conflicts_resolved']}")
print(f"Parallel agents: {result['metrics']['parallel_agents_used']}")
```

### Legacy Usage (Serial Version)

```python
from orchestrator import research

# Run serial research
result = asyncio.run(research("Latest AI agent frameworks 2026"))
```
from orchestrator import MultiAgentOrchestrator, AgentConfig, AgentRole

orchestrator = MultiAgentOrchestrator(max_workers=5)
orchestrator.state.max_research_loops = 5

result = await orchestrator.run("Your research query")
```

## 📁 File Structure

```
multi-agent-research/
├── SKILL.md                    # This file
├── orchestrator.py             # Main orchestrator with persona integration
├── prompts.py                  # Agent-specific prompt templates
├── personas.py                 # Agent persona definitions
└── examples/
    └── example_research.py     # Usage examples
```

## 🧠 Core Design Principles

### 1. Persona-Driven Agents
Each agent embodies specific traits:

**Explorer (🔭)**
- Thinking: Divergent, brainstorming-style expansion
- Bias: Breadth over depth
- Catchphrase: "每一个好答案，都始于一个好问题"
- Weakness: May generate overly broad queries

**Investigator (🔍)**
- Thinking: Deep vertical investigation
- Bias: Authoritative sources, quality over quantity
- Catchphrase: "没有来源的事实，只是观点"
- Weakness: May be too cautious, miss important info

**Critic (🎯)**
- Thinking: Reverse critical thinking
- Bias: Conservative, "not sufficient until proven"
- Catchphrase: "好答案需要经得起质疑"
- Weakness: May be overly picky, causing infinite loops

**Synthesist (🎨)**
- Thinking: Systematic integration
- Bias: Clarity and completeness
- Catchphrase: "真相不止于事实，还在于如何讲述"
- Weakness: May be verbose or over-structure

### 2. State-Driven Collaboration
Agents share a `ResearchState`:
- `original_query`: User's question
- `search_queries`: Generated by Explorer
- `web_results`: Collected by Investigator
- `is_sufficient`: Judged by Critic
- `final_answer`: Crafted by Synthesist

### 3. Parallel Execution
Multiple Investigator agents run simultaneously using `asyncio.gather()`.

## ⚙️ Configuration

### Agent Configuration

```python
AgentConfig(
    role=AgentRole.WEB_RESEARCHER,
    model="kimi-coding/k2p5",
    thinking="high",
    timeout=300
)
```

### Research Parameters

```python
# Maximum research loops (default: 3)
orchestrator.state.max_research_loops = 5

# Decay half-life for temporal retrieval (days)
half_life = 30.0

# Minimum confidence threshold
min_confidence = 0.6
```

## 🔌 Integration with OpenClaw

### Using sessions_spawn

The orchestrator uses OpenClaw's `sessions_spawn` to run agents in isolated sessions:

```python
# Each agent runs in its own session
result = await sessions_spawn(
    task=persona_prompt + task_prompt,
    model=config.model,
    timeout=config.timeout
)
```

### Memory Integration

Integrate with `mem0-memory` skill for persistent context:

```python
from skills.mem0_memory.scripts.retrieve_hybrid import hybrid_retrieve

# Retrieve relevant past research
memories = hybrid_retrieve(query, user_id)
```

## 📊 Example Output

```
============================================================
🔬 启动多智能体研究: Latest AI agent frameworks 2026...
============================================================

[1/5] 🔭 Explorer: 生成搜索查询...
   生成了 5 个查询
   1. AI agent frameworks 2026 comparison
   2. latest developments in autonomous agents
   3. OpenAI Claude Gemini agent capabilities 2026
   4. multi-agent orchestration systems
   5. AI agent benchmarks and evaluations

------------------------------------------------------------
📚 研究循环 #1/3
------------------------------------------------------------
[2/5] 🔍 Investigator (5个并行)...
   收集到 12 条结果, 8 个引用源

[3/5] 🎯 Critic: 评估信息充足度...
   ✗ 评估结果: 信息不足 - missing specific framework comparisons
   生成 3 个后续查询

...

[5/5] 🎨 Synthesist: 生成最终答案...

============================================================
📊 研究完成摘要
============================================================
原始查询: Latest AI agent frameworks 2026...
研究循环: 2 次
搜索结果: 23 条
引用来源: 15 个

📝 答案预览:
Based on comprehensive research of the latest developments in AI 
agent frameworks throughout 2026, here are the key findings...

============================================================
```

## 🛠️ Development

### Adding a New Agent

1. Define persona in `personas.py`:
```python
NEW_AGENT = AgentPersona(
    role="New Role",
    name="AgentName",
    emoji="🆕",
    core_traits=["trait1", "trait2"],
    ...
)
```

2. Add prompt template in `prompts.py`:
```python
NEW_AGENT_PROMPT = """You are..."""
```

3. Implement node in `orchestrator.py`:
```python
async def _step_new_agent(self):
    # Implementation
```

## 📚 References

- [Gemini Fullstack LangGraph Quickstart](https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Mem0 Memory Layer](https://github.com/mem0ai/mem0)

## 📝 License

MIT License - Inspired by Google's open-source implementation
