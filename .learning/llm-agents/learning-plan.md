# 🎯 LLM Agents 学习计划

**研究ID**: RES-1773290044  
**创建时间**: 2026-03-12  
**预计周期**: 4周  
**优先级**: HIGH

---

## 核心目标

掌握LLM-based agents的设计原理、关键技术和评估方法，能够独立开发和部署agent系统。

**当前水平**: 3/10  
**目标水平**: 8/10

---

## 学习阶段

### 📚 Phase 1: 基础认知 (第1周)

**目标**: 理解Agentic LLM的核心概念和基础架构

**任务清单**:
- [ ] 精读 ReAct 论文 (arXiv:2210.03629)
- [ ] 理解 Chain-of-Thought  prompting 原理
- [ ] 阅读 Agentic LLM Survey 第1-2章 (arXiv:2503.23037)
- [ ] 实现基础 Tool-use Agent (Python)

**产出物**:
- 论文笔记 (MEMORY.md)
- 基础Agent代码实现
- 概念验证Demo

---

### 🔧 Phase 2: 进阶技术 (第2周)

**目标**: 掌握推理增强和自我反思机制

**任务清单**:
- [ ] 学习 Tree of Thoughts (arXiv:2305.10601)
- [ ] 研究 Self-Refine 迭代优化 (NeurIPS 2023)
- [ ] 了解 Buffer of Thoughts (arXiv:2406.04271)
- [ ] 实现带记忆系统的Agent

**技术重点**:
- Short-term memory (working memory)
- Long-term memory (retrieval)
- Self-reflection loops

**产出物**:
- ToT算法实现
- 记忆模块代码
- 性能对比实验

---

### 🌐 Phase 3: 多智能体系统 (第3周)

**目标**: 理解多Agent协作和涌现行为

**任务清单**:
- [ ] 学习 Multi-Agent 通信协议
- [ ] 研究协作问题解决机制
- [ ] 了解竞争与博弈场景
- [ ] 实现简单的Multi-Agent系统

**关键概念**:
- Agent communication
- Task delegation
- Consensus building
- Emergent behaviors

**产出物**:
- Multi-Agent系统原型
- 协作场景测试
- 行为分析报告

---

### ✅ Phase 4: 评估与部署 (第4周)

**目标**: 掌握评估方法和实际部署

**任务清单**:
- [ ] 学习主要Benchmark (SWE-bench, AgentBoard)
- [ ] 了解安全评估方法
- [ ] 研究医疗/金融等领域应用
- [ ] 设计自己的Agent评估方案

**评估维度**:
- Planning capability
- Tool use accuracy
- Memory retention
- Safety & robustness

**产出物**:
- 评估框架设计
- Agent性能报告
- 部署方案文档

---

## 关键论文清单

### 必读 (5篇)
1. ✅ **ReAct** - Synergizing Reasoning and Acting (Yao et al., 2023)
2. ✅ **Tree of Thoughts** - Deliberate problem solving (Yao et al., 2023)
3. ✅ **Agentic LLM Survey** - Comprehensive overview (Plaat et al., 2025)
4. ✅ **Self-Refine** - Iterative refinement (Madaan et al., 2023)
5. ✅ **Evaluation Survey** - Benchmarks & metrics (Yehudai et al., 2025)

### 选读 (3篇)
6. Buffer of Thoughts - Thought-augmented reasoning (Yang et al., 2024)
7. Medical Agents Survey - Healthcare applications (Wang et al., 2025)
8. SWE-agent - Automated software engineering (Yang et al., 2024)

---

## 验证标准

**完成标志**:
- [ ] 独立实现一个完整功能的Agent
- [ ] 通过至少1个标准Benchmark测试
- [ ] 撰写技术总结文档
- [ ] 能够解释核心算法原理

**质量指标**:
- 代码可运行且文档完整
- 测试覆盖率达到80%
- 性能达到Baseline水平

---

## 资源链接

- 研究报告: `.research-advanced/RES-1773290044/report.md`
- 代码实现: `learning/llm-agents/`
- 笔记归档: `memory/llm-agents-learning.md`

---

## 进度追踪

| 阶段 | 开始日期 | 完成日期 | 状态 |
|------|----------|----------|------|
| Phase 1 | 2026-03-12 | - | 🔄 进行中 |
| Phase 2 | - | - | ⏳ 等待 |
| Phase 3 | - | - | ⏳ 等待 |
| Phase 4 | - | - | ⏳ 等待 |

---

*学习计划创建完成 - 准备开始学习 Phase 1*
