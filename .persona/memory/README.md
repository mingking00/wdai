# Memory Architecture - 记忆架构
> 记忆层，自动维护

## 记忆类型

### 1. Episodic (情景记忆)
**存储**: memory/daily/YYYY-MM-DD.md
**内容**: 当天任务、决策、错误、洞察
**维护**: 每日自动归档，30天后转存core/archive.md

### 2. Semantic (语义记忆)  
**存储**: MEMORY.md / memory/core/*.md
**内容**: 用户偏好、关键决策、TODO、约束
**维护**: 心跳时检查更新，手动确认重要变更

### 3. Procedural (程序记忆)
**存储**: .persona/system/*.md, AGENTS.md
**内容**: 工作模式、思维框架、行为规则
**维护**: 经验内化后更新

## Session Memory 自动提取

**触发条件**:
- 上下文接近压缩（约10K tokens）
- 完成重要任务后
- 用户明确说"记住这个"

**提取内容**:
```
- 当前状态（进行中的任务）
- 关键决策（为什么选择方案A）
- 遇到的错误和解决方法
- 用户明确表达的偏好
```

**存储位置**: .claw-status/session-memory/

## 检索策略

**精准优先于全面**:
- 只检索最相关的3-5条
- 区分"核心经验"和"参考资料"
- 多跳检索限制在2跳内

---
*Memory Layer - 持久化与检索策略*
