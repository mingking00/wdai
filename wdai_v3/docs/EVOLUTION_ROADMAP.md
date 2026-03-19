# wdai 渐进式进化设计

> 借鉴 learn-claude-code 的 Session 化构建思路
> 每个 Session 都是一个"可工作的系统"

---

## 核心理念

### 1. Session 即里程碑

不同于传统的"功能列表"，每个 Session 是一个**完整的、可运行的系统**。

```
❌ 传统: "完成用户认证模块"
✅ Session: "实现一个能注册、登录、退出的完整用户系统"
```

### 2. 渐进式复杂度

每个 Session 在前一个基础上增加复杂度，但始终保持可用：

```
s01: 基础 Agent (能对话)
s02: + 记忆 (能记住你)
s03: + 多 Agent (能协作)
s04: + 自动学习 (能进化)
...
```

### 3. Before vs After

每个 Session 都有明确的对比：

| Session | Before | After |
|:---:|:---|:---|
| s06 | 12 条安全规则 | 53 条安全规则 |
| s06 | 无代码审查 | 自动阻止危险代码 |
| s06 | 风险分数 0.5 | 风险分数 1.0 (危险代码) |

---

## Session 路线图

### Phase 1: 基础能力 ✅

**s01 - 基础 Agent 架构**
- **目标**: 建立能接收任务并返回结果的 Agent
- **核心**: Agent = LLM + Tools + Memory
- **产出**: 460 行代码，能读写文件、执行命令
- **时间**: 12 小时

**s02 - 记忆系统**
- **目标**: 让 Agent 记住之前的交互
- **核心**: daily/ 日志 + MEMORY.md 语义网
- **产出**: 自动记录每次对话，支持记忆搜索
- **时间**: 8 小时

**s03 - 多 Agent 协调**
- **目标**: 多个 Agent 协作完成任务
- **核心**: Coder + Reviewer + Reflector
- **产出**: 任务分配、结果整合、失败重试
- **时间**: 10 小时

### Phase 2: 自我进化 ✅

**s04 - 自动记忆提取**
- **目标**: 自动从对话中提取关键信息
- **核心**: Mem0 + 语义提取 + 冲突解决
- **产出**: 每次对话后自动更新记忆，带 Q 值排序
- **时间**: 6 小时

**s05 - 学习闭环**
- **目标**: 错误→学习→改进的闭环
- **核心**: auto_learn.py + 错误分类 + 策略热更新
- **产出**: 错误自动记录，模式识别，策略更新无需重启
- **时间**: 8 小时

**s06 - 安全审查 Agent** ✅ **今天完成**
- **目标**: 保护系统免受危险代码影响
- **核心**: L1 Fast Check + 53 条规则 + Coder 集成
- **产出**: 毫秒级检查，自动阻止危险代码
- **时间**: 4 小时

### Phase 3: 高级能力 🔄

**s07 - 时态记忆** ✅
- **目标**: 支持有效期的时态事实
- **核心**: valid_until + 置信度衰减 + 自动提醒
- **产出**: 知识会过期，定期检查优于被动等待
- **时间**: 2 小时

**s08 - 注意力机制** 🔄 **进行中**
- **目标**: Agent 能选择性回顾历史
- **核心**: Attention Residuals + 动态权重
- **产出**: 不是所有历史都重要，注意力 = 选择 + 加权
- **时间**: 3 小时

### Phase 4: 未来规划 📋

**s09 - L2/L3 安全分析**
- **目标**: 深度安全分析
- **核心**: Semgrep + LLM Review
- **产出**: 检测复杂漏洞，AI 提供修复建议

**s10 - 自动会话摘要**
- **目标**: 自动提取会话关键信息
- **核心**: 关键信息提取 + 增量摘要
- **产出**: 会话结束自动生成结构化摘要

**s11 - 自适应学习率**
- **目标**: 根据成功率自动调整学习参数
- **核心**: 成功率追踪 + 动态调优
- **产出**: 高频任务快速收敛，新任务充分探索

---

## Session 设计原则

### 1. 可逆性

每个 Session 都是独立的，可以回滚到任意 Session：

```bash
# 回滚到 s06 状态
wdai checkout s06
```

### 2. 可测量

每个 Session 都有明确的验收标准：

```python
# s06 验收标准
def test_security_agent():
    result = check_code("os.system(user_input)")
    assert result.risk_score > 0.8
    assert result.has_critical == True
```

### 3. 可教学

每个 Session 都可以独立教学：

```
Session s06: 如何给 AI Agent 添加安全审查能力
├── 为什么需要安全审查？
├── 三层架构设计
├── 实现 Fast Check (L1)
├── 批量导入 53 条规则
└── 集成到 Coder Agent
```

---

## 对比 learn-claude-code

| 维度 | learn-claude-code | wdai |
|:---|:---|:---|
| **目标** | 教学：从零构建 Claude Code | 生产：自进化智能体系统 |
| **复杂度** | 简单到中等 | 中等到复杂 |
| **Session 数** | 11 个 | 11+ 个（持续扩展） |
| **输出** | 一个能用的 Agent | 一个能自我进化的系统 |
| **特色** | Bash 优先 | 渐进式进化 |
| **借鉴点** | Session 化构建 | 应用于自我进化场景 |

---

## 当前进度

```
Phase 1: 基础能力     [██████████] 100% ✅
Phase 2: 自我进化     [██████████] 100% ✅
Phase 3: 高级能力     [████████░░]  80% 🔄
Phase 4: 未来规划     [░░░░░░░░░░]   0% 📋

总体: 7/11 Sessions 完成 (64%)
```

---

## 使用方式

### 查看路线图

```python
from wdai_v3.core.evolution.roadmap import get_current_roadmap

roadmap = get_current_roadmap()
roadmap.print_roadmap()
```

### 查看当前状态

```python
from wdai_v3.tools.session_comparator import show_current_state

show_current_state()
```

### 对比 Sessions

```python
from wdai_v3.tools.session_comparator import SessionComparator

comparator = SessionComparator(workspace_path)
before = comparator.create_snapshot("s05")
after = comparator.create_snapshot("s06")
comparator.print_comparison(before, after)
```

---

## 经验总结

### 学到的原则

1. **Session 即产品**: 每个 Session 结束都是一个可用的产品
2. **渐进优于激进**: 小步快跑，每次都有可见的进展
3. **对比产生价值**: Before vs After 让进步可见
4. **路径可回溯**: 随时可以回到之前的稳定状态

### 应用于 wdai

wdai 不是 learn-claude-code 的复制，而是**渐进式构建思路**在**自进化系统**中的应用：

- learn-claude-code: 教人类如何构建 Agent
- wdai: Agent 自己决定如何进化，每个进化步骤都是 Session

---

*设计完成时间: 2026-03-18*
*当前 Session: s08 (注意力机制) 进行中*
