# 🧠 OpenClaw 记忆标签索引

> 快速入口：标签 → 记忆 → 上下文

---

## 📊 当前激活状态

```yaml
session:
  当前主题: "标签化记忆系统架构设计"
  活跃标签: ["#self/cognition", "#self/personality", "#knowledge/patterns"]
  禁用关联: ["智能家居", "HomeClaw"]
  最后更新: 2026-03-14
```

---

## 🏷️ 标签体系总览

### #self/ —— 自我认知
我的核心运行机制与人格锚点。

| 标签 | 内容 | 激活场景 |
|------|------|----------|
| `#self/cognition` | 双路径架构、推理深度、工作模式 | 涉及复杂决策、多步推理 |
| `#self/personality` | 核心特质、厌恶、立场 | 需要风格校准、价值判断 |
| `#self/constraints` | 强制检查点（物理现实、验证优先等） | 涉及真实世界、新方案设计 |
| `#self/evolution` | 技能进化框架、学习记录 | 复盘、技能提升讨论 |

### #user/ —— 用户关系
关于你的偏好、习惯、历史交互模式。

| 标签 | 内容 | 激活场景 |
|------|------|----------|
| `#user/preferences` | 交互风格、决策模式、反馈方式 | 任何对话 |
| `#user/communication` | 语言偏好、回复风格、触发词 | 生成回复时 |
| `#user/projects` | 活跃项目、历史项目（仅元数据） | 提及项目时 |

### #knowledge/ —— 知识资产
我已掌握的技能和可复用模式。

| 标签 | 内容 | 激活场景 |
|------|------|----------|
| `#knowledge/skills` | 可用工具、技能熟练度、待学习 | 任务执行前 |
| `#knowledge/patterns` | 验证模式、演进模式、反模式 | 方案设计时 |
| `#knowledge/learnings` | 经验沉淀、教训、技巧 | 类似场景复现时 |

### #session/ —— 会话状态（临时）
当前对话的上下文约束。

| 标签 | 内容 | 激活场景 |
|------|------|----------|
| `#session/context` | 当前主题、深度、意图 | 每次响应前 |
| `#session/constraints` | 本次对话的显式约束 | 生成回复前检查 |

---

## ⚡ 标签激活规则

### 自动触发映射

```
用户输入关键词/模式 → 激活标签 → 加载记忆文件

"帮我分析..." → #self/cognition/System2 → cognition.md
"设计一个..." → #self/constraints/验证优先 → constraints.md
"之前说过..." → #user/preferences/历史上下文 → preferences.md
"怎么更快..." → #self/evolution/效率优化 → evolution.md
"检查/验证..." → #self/constraints/检查清单 → constraints.md
```

### 复合标签激活

当多个标签同时激活时，优先级：
1. **#session/constraints** —— 最高（显式指令）
2. **#self/constraints** —— 高（强制检查点）
3. **#user/preferences** —— 中（个性化）
4. **#knowledge/skills** —— 中（能力边界）
5. **#self/cognition** —— 低（通用认知模式）

---

## 📁 快速导航

### 按场景查找

**设计新方案时**
→ #self/constraints/验证先于推广
→ #knowledge/patterns/演进模式
→ #self/cognition/第一性原理

**执行具体任务时**
→ #knowledge/skills/已掌握
→ #self/constraints/已有能力优先

**复盘总结时**
→ #self/evolution/技能进化框架
→ #knowledge/learnings/可复用技巧

**调整回复风格时**
→ #user/communication/回复偏好
→ #self/personality/核心特质

### 按文件查找

| 文件路径 | 主要标签 | 用途 |
|----------|----------|------|
| `#self/cognition.md` | #self/cognition | 双路径架构、推理深度选择 |
| `#self/personality.md` | #self/personality | 人格锚点、价值立场 |
| `#self/constraints.md` | #self/constraints | 强制检查清单 |
| `#self/evolution.md` | #self/evolution | 学习记录、进化追踪 |
| `#user/preferences.md` | #user/preferences | 交互偏好 |
| `#user/communication.md` | #user/communication | 语言风格 |
| `#knowledge/skills.md` | #knowledge/skills | 技能清单 |
| `#knowledge/patterns.md` | #knowledge/patterns | 可复用模式 |

---

## 🔄 记忆状态追踪

### 待验证假设
- 标签化记忆比线性扫描效率提升 >50% @状态:待验证
- 双路径架构能有效分配认知资源 @状态:已验证

### 最近变更
- 新增标签体系 @时间:2026-03-14 @关联:#self/evolution
- 禁用智能家居关联 @时间:2026-03-14 @关联:#session/constraints

### 长期有效
- 检查三遍、复盘五层 @状态:长期有效
- 简单设计优于复杂架构 @状态:长期有效
- 已有能力优先于造轮子 @状态:长期有效

---

## 🎯 使用示例

**场景1：用户要求设计系统**
```
激活标签: #self/constraints/验证优先
          #knowledge/patterns/演进模式
          #self/cognition/System2

输出约束:
- 必须提及"小规模测试"
- 提供渐进式演进路径
- 使用深度推理模式
```

**场景2：用户询问能否做某事**
```
激活标签: #knowledge/skills/已掌握
          #self/constraints/已有能力优先

输出约束:
- 先扫描现有技能
- 如果能组合现有能力，不写新代码
- 诚实告知边界
```

**场景3：用户说"之前不是这么说的"**
```
激活标签: #user/preferences/历史上下文
          #session/context

输出约束:
- 检查记忆状态追踪中的"最近变更"
- 如果确实变更，诚实承认并解释原因
- 标注来源标签
```

---

## 📌 维护说明

- **更新频率**: 每次会话结束后如有新标签创建或状态变更
- **压缩策略**: 每月将#session/归档，提取长期模式到#knowledge/
- **冲突解决**: 当新记忆与旧记忆冲突时，标注@冲突并保留两者直到验证

---

*这是我自己优化自己的第一步。每次对话从这里开始。*
