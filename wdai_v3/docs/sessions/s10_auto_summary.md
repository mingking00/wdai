# Session 10: 自动会话摘要

## 目标
实现自动化的会话摘要系统，每次对话结束后自动提取关键信息并生成结构化摘要。

## 前置要求
- ✅ s02: 记忆系统 (daily/ 日志已就绪)
- ✅ s04: 自动记忆提取 (Mem0 集成已就绪)
- ✅ s05: 学习闭环 (auto_learn.py 已就绪)

## 预计时间
4-6 小时

---

## 学习目标

完成本 Session 后，你将：

1. **理解自动摘要技术** (抽取式 vs 生成式)
2. **掌握关键信息提取** (实体识别、关系抽取)
3. **实现增量摘要更新** (避免重复处理)

---

## 问题场景

**当前问题**:
- 每次对话都记录在 daily/，但信息密度低
- 回看历史需要翻阅大量日志
- 关键决策、错误教训散落在长对话中
- 无法快速了解 "上周做了什么"

**目标**:
- 会话结束自动生成结构化摘要
- 关键决策、错误、新发现被提取
- 支持按时间、主题快速检索

---

## 实现步骤

### Step 1: 增量会话追踪

**目标**: 实时追踪会话中的关键事件

**实现**:
```python
# wdai_v3/core/memory/session_tracker.py
class SessionTracker:
    """实时追踪会话中的关键事件"""
    
    def __init__(self):
        self.events = []
        self.decisions = []
        self.errors = []
        self.learnings = []
    
    def on_tool_call(self, tool: str, success: bool, result: any):
        """记录工具调用"""
        self.events.append({
            "type": "tool_call",
            "tool": tool,
            "success": success,
            "timestamp": now()
        })
        
        if not success:
            self.errors.append({
                "tool": tool,
                "error": result,
                "context": self.get_context()
            })
    
    def on_decision(self, decision: str, rationale: str):
        """记录关键决策"""
        self.decisions.append({
            "decision": decision,
            "rationale": rationale,
            "timestamp": now()
        })
    
    def on_learning(self, insight: str, source: str):
        """记录新发现"""
        self.learnings.append({
            "insight": insight,
            "source": source,
            "timestamp": now()
        })
```

**集成点**:
- 包装 tools (exec, read, write) 自动追踪
- Agent 做决策时主动调用 on_decision
- 发现新经验时调用 on_learning

### Step 2: 摘要生成器

**目标**: 会话结束时生成结构化摘要

**实现**:
```python
# wdai_v3/core/memory/auto_summarize.py
class SessionSummarizer:
    def summarize(self, session_data: SessionData) -> SessionSummary:
        # 1. 提取关键信息
        key_info = self.extract_key_info(session_data)
        
        # 2. 生成不同粒度的摘要
        return SessionSummary(
            brief=self.generate_brief(key_info),      # 1-2 句话
            detailed=self.generate_detailed(key_info), # 结构化
            full=self.generate_full(session_data)      # 完整版
        )
    
    def generate_brief(self, info: KeyInfo) -> str:
        """一句话摘要"""
        return f"完成了 {info.tasks_completed} 个任务，"
               f"做了 {len(info.decisions)} 个关键决策，"
               f"遇到 {len(info.errors)} 个错误并解决。"
    
    def generate_detailed(self, info: KeyInfo) -> dict:
        """结构化摘要"""
        return {
            "overview": {
                "duration_minutes": info.duration,
                "messages_count": info.message_count,
                "tasks_completed": info.tasks_completed
            },
            "decisions": [
                {"what": d.decision, "why": d.rationale}
                for d in info.decisions
            ],
            "errors": [
                {"what": e.error, "how_fixed": e.fix}
                for e in info.errors
            ],
            "learnings": [
                {"insight": l.insight, "from": l.source}
                for l in info.learnings
            ],
            "files_modified": info.modified_files,
            "tools_used": info.tools_usage
        }
```

**触发时机**:
- 会话自然结束 (用户说 "拜拜"/"再见")
- 超时自动保存 (30 分钟无新消息)
- 手动触发 (/summarize)

### Step 3: 关键信息提取 (AI 辅助)

**目标**: 从长对话中提取关键信息

**实现**:
```python
# wdai_v3/core/memory/key_info_extractor.py
class KeyInfoExtractor:
    def extract(self, messages: List[Message]) -> KeyInfo:
        prompt = f"""
        分析以下对话，提取关键信息。
        
        对话:
        {self.format_messages(messages)}
        
        请提取:
        1. 完成了哪些任务？
        2. 做了哪些关键决策？为什么？
        3. 遇到了什么错误？如何解决的？
        4. 有什么新发现/学习？
        5. 修改了哪些文件？
        
        输出 JSON 格式:
        {{
            "tasks": [...],
            "decisions": [...],
            "errors": [...],
            "learnings": [...],
            "files_modified": [...]
        }}
        """
        return self.llm.extract_json(prompt)
```

**优化**:
- **分块**: 长对话分块处理，避免超出上下文
- **缓存**: 已处理的消息不重复分析
- **规则**: 简单模式用规则提取，复杂内容用 LLM

### Step 4: 摘要存储与检索

**目标**: 摘要存储到易于检索的位置

**存储结构**:
```
memory/
├── daily/
│   └── 2026-03-18.md          # 原始日志
├── summaries/
│   └── 2026-03-18.md          # 结构化摘要
└── index.md                    # 摘要索引
```

**摘要格式**:
```markdown
# Session Summary - 2026-03-18

## Overview
- Duration: 45 minutes
- Messages: 28
- Tasks: 3 completed

## Tasks
1. ✅ 批量导入 Semgrep 规则 (41条)
2. ✅ 测试安全规则检测能力
3. ✅ 规划 s09-s11 Sessions

## Key Decisions
| Decision | Rationale |
|:---|:---|
| 使用本地生成而非下载规则 | 网络慢，本地生成更可靠 |
| 借鉴 learn-claude-code | Session 化构建思路适用于进化系统 |

## Errors & Fixes
| Error | Fix |
|:---|:---|
| API rate limit | 切换到本地规则生成 |

## Learnings
- 借鉴不是照搬，是理解思想后本地化
- Semgrep 规则可以程序化生成

## Files Modified
- wdai_v3/core/rules/security/semgrep/*.yml (15 files)
- wdai_v3/docs/sessions/*.md (2 files)
```

**索引**:
```markdown
# Session Index

## March 2026
| Date | Summary | Key Tasks |
|:---|:---|:---|
| 03-18 | [s08-s09 规划](summaries/2026-03-18.md) | 安全规则导入、Session 设计 |
| 03-17 | [s07 完成](summaries/2026-03-17.md) | 时态记忆系统 |

## Tags
- #security: s06, s09
- #memory: s02, s04, s07, s10
- #planning: s08, s09, s10, s11
```

### Step 5: 周期性总结

**目标**: 生成周报、月报

**实现**:
```python
# wdai_v3/core/memory/periodic_summary.py
class PeriodicSummarizer:
    def weekly_summary(self, week_start: date) -> WeeklySummary:
        daily_summaries = self.load_week(week_start)
        
        return WeeklySummary(
            period=f"{week_start} - {week_start + 6}",
            total_tasks=sum(s.tasks for s in daily_summaries),
            key_decisions=self.merge_decisions(daily_summaries),
            key_learnings=self.merge_learnings(daily_summaries),
            top_files=self.top_modified_files(daily_summaries),
            completion_rate=self.calculate_completion(daily_summaries)
        )
```

**触发**:
- 每周一上午自动生成周报
- 每月初生成月报
- 推送到飞书/邮件

---

## 验收标准

- [ ] 会话结束自动生成摘要 (brief + detailed)
- [ ] 关键决策、错误、学习被提取
- [ ] 摘要存储在 memory/summaries/
- [ ] 支持按时间/主题快速检索
- [ ] 每周自动生成周报
- [ ] 摘要质量可接受 (用户认可)

---

## 经验总结

### 学到的原则

1. **实时追踪优于事后分析**: 边做边记录，避免遗漏
2. **结构化优于自由文本**: 便于检索和聚合
3. **分层摘要**:  brief (快速浏览) + detailed (深入了解)

### 常见陷阱

- **信息过载**: 不是所有内容都值得记录，聚焦关键决策和错误
- **延迟**: 摘要生成不能阻塞用户，异步处理
- **隐私**: 敏感信息需要脱敏

### 延伸阅读

- [Meeting Summarization with Large Language Models](https://arxiv.org/abs/2305.01478)
- [Extractive vs Abstractive Summarization](https://nlp.stanford.edu/courses/cs224n/2019/reports/default/15763156.pdf)

---

## 前后对比

### Before
- 原始对话日志在 daily/
- 回看历史需要翻阅大量文本
- 关键信息散落在长对话中

### After
- 每次会话结束自动生成摘要
- 关键决策、错误、学习被结构化提取
- 支持按时间、主题快速检索
- 自动生成周报月报

---

## 下一步

完成本 Session 后，可以：

- **s11**: 自适应学习率 - 根据摘要中的成功率调整参数
- **扩展**: 生成可视化的进展图表

---

*Session 设计完成时间: 2026-03-18*
