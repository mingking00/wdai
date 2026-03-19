# Research Report: LLM agents

**Research ID**: RES-1773290044  
**Date**: 2026-03-12T12:34:04+08:00  
**Depth**: deep

## Methodology
- Sources: Academic (arXiv) + Technical + Dynamic
- Evaluation: Four-dimensional (Relevance/Authority/Timeliness/Credibility)

## Four-Dimensional Scores
```json
{
  "relevance": 9,
  "authority": 9,
  "timeliness": 10,
  "credibility": 8,
  "composite": 8.8
}
```

## Executive Summary

LLM-based agents represent a paradigm shift in AI, enabling autonomous systems to plan, reason, use tools, and maintain memory while interacting with dynamic environments. This research covers three major survey papers from 2025 covering: (1) Agentic LLMs general survey, (2) Medical LLM agents, (3) LLM agent evaluation methodologies.

## Key Findings

### 1. Agentic LLM Framework (Plaat et al., 2025)
**arXiv:2503.23037**

Agentic LLMs are defined as LLMs that:
1. **Reason** - reflection, retrieval, decision making
2. **Act** - action models, robots, tools
3. **Interact** - multi-agent systems, collaborative reasoning

**Three Research Categories:**
- Reasoning & Reflection: Improving decision making through chain-of-thought, self-refinement
- Action & Tools: Enabling agents to use APIs, robots, GUI automation
- Multi-Agent Systems: Collaborative problem solving and emergent social behavior

**Key Papers Cited:**
- ReAct (Yao et al., 2023): Synergizing reasoning and acting
- Tree of Thoughts (Yao et al., 2023): Deliberate problem solving
- Self-Refine (Madaan et al., 2023): Iterative refinement with self-feedback
- Buffer of Thoughts (Yang et al., 2024): Thought-augmented reasoning

### 2. Medical LLM Agents (Wang et al., 2025)
**arXiv:2502.11211**

Comprehensive survey of LLM agents in healthcare, examining:
- Clinical diagnosis systems
- Multi-agent frameworks for medical reasoning
- Safety and hallucination challenges (MedHallBench)
- Real-world deployment (AgentClinic benchmark)

**Notable Systems:**
- ClinicalAgent: Clinical trial multi-agent system
- EHRAgent: Complex tabular reasoning on electronic health records
- MedAgents: Zero-shot medical reasoning through collaboration
- FinRobot: Open-source AI agent platform for financial applications

### 3. Evaluation Methodologies (Yehudai et al., 2025)
**arXiv:2503.16416**

First comprehensive survey of evaluation methodologies across four dimensions:
1. **Fundamental capabilities**: Planning, tool use, self-reflection, memory
2. **Application benchmarks**: Web agents (WebVoyager), software engineering (SWE-bench), scientific discovery
3. **Safety evaluation**: Risk awareness, jailbreak resistance
4. **Multi-agent evaluation**: Collaboration, competition, emergent behaviors

**Key Benchmarks:**
- SWE-bench: Real-world GitHub issue resolution
- AgentBoard: Multi-turn LLM agent evaluation
- DiscoveryWorld: Automated scientific discovery
- LiveCodeBench: Holistic code evaluation

## Knowledge Graph
```
[Entity: LLM Agents] --[has_capability]--> [Entity: Reasoning]
[Entity: LLM Agents] --[has_capability]--> [Entity: Tool Use]
[Entity: LLM Agents] --[has_capability]--> [Entity: Multi-Agent]
[Entity: Reasoning] --[techniques]--> [Entity: Chain-of-Thought]
[Entity: Reasoning] --[techniques]--> [Entity: Tree of Thoughts]
[Entity: Reasoning] --[techniques]--> [Entity: Self-Reflection]
[Entity: Tool Use] --[applications]--> [Entity: Code Generation]
[Entity: Tool Use] --[applications]--> [Entity: Web Navigation]
[Entity: Tool Use] --[applications]--> [Entity: API Integration]
[Entity: Multi-Agent] --[behaviors]--> [Entity: Collaboration]
[Entity: Multi-Agent] --[behaviors]--> [Entity: Competition]
[Entity: Multi-Agent] --[behaviors]--> [Entity: Emergence]
[Entity: Medical Agents] --[challenges]--> [Entity: Hallucination]
[Entity: Medical Agents] --[challenges]--> [Entity: Safety]
```

## Confidence Assessment
Based on 4D evaluation:
- **High confidence (>8.0)**: Core framework definitions, major survey papers
- **Medium confidence (6-8)**: Specific benchmark results, emerging techniques
- **Emerging areas needing verification**: Multi-agent social behaviors, long-term memory systems

## Recommended Learning Path

### Phase 1: Foundations (Week 1)
1. Read ReAct paper (reasoning + acting)
2. Study Chain-of-Thought prompting
3. Implement basic tool-use agent

### Phase 2: Advanced Techniques (Week 2)
1. Tree of Thoughts implementation
2. Self-reflection mechanisms
3. Memory systems (short-term & long-term)

### Phase 3: Multi-Agent Systems (Week 3)
1. Multi-agent communication protocols
2. Collaborative problem solving
3. Emergent behavior analysis

### Phase 4: Evaluation & Deployment (Week 4)
1. Benchmark understanding (SWE-bench, AgentBoard)
2. Safety evaluation
3. Real-world deployment considerations

## Sources

### Primary Papers
1. Plaat et al. (2025). "Agentic Large Language Models: A Survey" - arXiv:2503.23037
2. Wang et al. (2025). "A Survey of LLM-based Agents in Medicine" - arXiv:2502.11211
3. Yehudai et al. (2025). "Survey on Evaluation of LLM-based Agents" - arXiv:2503.16416

### Key Technique Papers
- Yao et al. (2023). "ReAct: Synergizing Reasoning and Acting" - arXiv:2210.03629
- Yao et al. (2023). "Tree of Thoughts" - arXiv:2305.10601
- Madaan et al. (2023). "Self-Refine" - NeurIPS 36
- Yang et al. (2024). "Buffer of Thoughts" - arXiv:2406.04271

---
*Research completed: 2026-03-12*  
*Next update: Monitor for new papers weekly*
