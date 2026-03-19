# Mitchell Hashimoto 16个编码会话深度分析
## Ghostty自动更新UI功能的完整AI辅助开发记录

**来源**: Mitchell Hashimoto博客文章 "Vibing a Non-Trivial Ghostty Feature"
**链接**: https://mitchellh.com/writing/non-trivial-vibing
**分析时间**: 2026-03-13

---

## 📊 项目概览

| 指标 | 数值 |
|------|------|
| **功能** | macOS不打扰自动更新通知UI |
| **会话数** | 16个 |
| **时间跨度** | 2天 |
| **计算机时间** | 约8小时 |
| **Token成本** | $15.98 |
| **产出** | 21个文件的PR |
| **工具** | Amp Code (with "Oracle"模式) |
| **语言** | Swift (macOS UI) |

---

## 🎯 核心洞察：AI不是替代，而是放大器

Mitchell的关键观点：
> "Important: there is a lot of human coding, too. I almost always go in after an AI does work and iterate myself for awhile, too."
>
> "Therefore, you may see some discrepancies between what the AI produced and what ended up in the final code. This is intentional and I believe good AI drivers are experts in their domains and utilize AI as an assistant, not a replacement."

**核心理念**:
- ✅ AI是助手，不是替代
- ✅ 优秀AI使用者首先是领域专家
- ✅ 人工审查和迭代是必须的
- ✅ 不理解代码就不合并

---

## 🔄 16个会话的完整流程分析

### Phase 1: 原型与探索 (会话1)

**目标**: 探索UI原型，获得灵感

**提示词策略**:
```
I want to enable custom, unobtrusive update notifications and installs
by customizing SPUUserDriver. Let's start by planning the custom UI we'll
need. We'll ONLY work on UI. Create a plan for creating SwiftUI views that
can show the various states that are required by SPUUserDriver. I think the
best place for these to show up is in the macOS window titlebars on the
top-right. Create a plan to put it there. Consult the oracle.
```

**关键决策**:
1. **先规划，不编码** - 要求AI先创建计划，审查后再执行
2. **限定范围** - "ONLY work on UI"，避免发散
3. **使用Oracle** - 用更强的模型做规划

**Mitchell的解释**:
> "I don't send the agent off to build the full feature."
> "First and foremost, I still don't even know what I want the UI/UX to be like, so I can't possibly coherently expect an AI to do that for me amongst other changes."
> "Second, smaller chunks of work are easier to review, understand, and iterate on."

**结果**:
- AI生成的UI"方向很好，但有很多打磨问题"
- 给了Mitchell灵感，让他知道想要什么

**关键洞察**:
> "I very often use AI for inspiration. In this case, I ended up keeping a lot (not all) of the UI code it made, but I will very often prompt an agent, throw away everything it did, and redo it myself (manually!)."
>
> "I find the 'zero to one' stage of creation very difficult and time consuming and AI is excellent at being my muse."

---

### Phase 2: 遇到瓶颈 (会话11-14)

**现象**: 
- AI遇到关键bug，反复尝试修复失败
- Mitchell自己也不知道如何修复
- 进入"slop zone"（垃圾代码区）

**Mitchell的应对策略**:
> "I'll often make these few hail mary attempts to fix a bug. If the agent can figure it out, I can study it and learn myself. If it doesn't, it costs me very little."
>
> "If the agent figures it out and I don't understand it, I back it out. I'm not shipping code I don't understand."
>
> "While it's failing, I'm also tabbed out searching the issue and trying to figure it out myself."

**关键决策**:
> "It's at this point that I know I need to step back, review what it did, and come up with my own plans. It's time to educate myself and think critically. AI is no longer the solution; it is a liability."

**洞察**:
- AI不是万能的，遇到瓶颈时需要人工接管
- 不理解代码就不合并
- AI无法替代深度思考和学习

---

### Phase 3: 清理与重构 (会话2-10)

这是Mitchell方法论的精髓：**"Anti-Slop Sessions"（反垃圾代码会议）**

#### 会话2: 代码重组
```
Let's move the pill background, foreground, and badge functions from
@macos/Sources/Features/Update/UpdateAccessoryView.swift to
@macos/Sources/Features/Update/UpdateViewModel.swift and make them more
generic (background, foreground, badge)
```

#### 会话3: 添加文档
```
Update the docs for @UpdateBadge.swift
```

**Mitchell的解释**:
> "Adding documentation is a really important step because it helps reaffirm your own understanding of the code as well as educate future agents that may read and modify this code."
>
> "I find agents do much better when they have both natural language descriptions as well as the code itself."

#### 会话4+: 持续清理
- 移动view model到app-global位置
- 重构类型系统（struct with optionals → tagged union）
- 重命名类型，移动代码

**战略性手动重构示例**:
> "I spent some time manually restructured the view model. This involved switching to a tagged union rather than the struct with a bunch of optionals. I renamed some types, moved stuff around."
>
> "I knew from experience that this small bit of manual work in the middle would set the agents up for success in future sessions for both the frontend and backend."

**重构提示词示例**:
```
Turn each @macos/Sources/Features/Update/UpdatePopoverView.swift case into 
a dedicated fileprivate Swift view that takes the typed value as its parameter 
so that we can remove the guards.
```

---

### Phase 4: 深度审查 (每个会话结束)

**标准结束提示词**:
```
Are there any other improvements you can see to be made with the 
@macos/Sources/Features/Update feature? 

Don't write any code. Consult the oracle. 

Consider parts of the code that can also get more unit tests added.
```

**"Consult the oracle"模式**:
- 使用更昂贵、更强的模型
- 只读模式，不生成代码
- 用于深度思考和审查

---

## 🧠 Mitchell的方法论总结

### 1. 规划优先
> "Creating a comprehensive plan interactively with an agent is a really important first-step for anything non-trivial."
> "I usually also save it out (via the agent) to something like spec.md"

### 2. 小步前进
> "smaller chunks of work are easier to review, understand, and iterate on"

### 3. AI用于灵感
> "I very often use AI for inspiration"
> "I find the 'zero to one' stage of creation very difficult and time consuming and AI is excellent at being my muse."

### 4. 强制清理
> "The cleanup step is really important."
> "To cleanup effectively you have to have a pretty good understanding of the code, so this forces me to not blindly accept AI-written code."
> "Subsequently, better organized and documented code helps future agentic sessions perform better."
> "I sometimes tongue-in-cheek refer to this as the 'anti-slop session'."

### 5. 战略性手动干预
> "I spent some time manually restructured the view model..."
> "I knew from experience that this small bit of manual work in the middle would set the agents up for success in future sessions"

### 6. 文档驱动
> "Adding documentation is a really important step because it helps reaffirm your own understanding of the code"
> "I find agents do much better when they have both natural language descriptions as well as the code itself."

### 7. 知道何时停止用AI
> "It's at this point that I know I need to step back, review what it did, and come up with my own plans."
> "It's time to educate myself and think critically. AI is no longer the solution; it is a liability."

### 8. 不理解不合并
> "If the agent figures it out and I don't understand it, I back it out. I'm not shipping code I don't understand."

---

## 📈 效率分析

### 成本效益
- **Token成本**: $15.98
- **人工时间**: 8小时计算机时间 + Mitchell的审查/清理时间
- **产出**: 21个文件的完整功能

**Mitchell的评估**:
> "Many people on the internet argue whether AI enables you to work faster or not. In this case, I think I shipped this faster than I would have if I had done it all myself, in particular because iterating on minor SwiftUI styling is so tedious and time consuming for me personally and AI does it so well."

### 核心价值
> "I think the faster/slower argument for me personally is missing the thing I like the most: the AI can work for me while I step away to do other things."

---

## 🔧 技术细节：系统级开发的AI应用

### 技术栈
- **语言**: Swift (macOS原生开发)
- **框架**: SwiftUI + AppKit + Sparkle (更新框架)
- **架构**: libghostty核心 + 平台特定UI

### AI在系统级开发中的作用

| 任务类型 | AI作用 | 人工必须 |
|---------|--------|---------|
| UI原型 | ✅ 快速生成多种方案 | 审查、选择、打磨 |
| 框架集成 | ✅ 生成样板代码 | 理解框架原理 |
| 样式调整 | ✅ 自动迭代 | 审美判断 |
| 重构 | ✅ 执行重复性重构 | 架构决策 |
| Bug修复 | ⚠️ 尝试但可能失败 | 深度分析和修复 |
| 文档 | ✅ 生成初稿 | 审查准确性 |
| 类型设计 | ⚠️ 需要指导 | 核心架构决策 |

---

## 💡 给你的实践建议

### 立即可以应用的技巧

1. **会话开始：规划优先**
   ```
   "先创建计划，不编写代码。Consult the oracle."
   ```

2. **会话结束：强制审查**
   ```
   "Are there any other improvements you can see? 
   Don't write any code. Consult the oracle."
   ```

3. **遇到瓶颈：停止用AI**
   - 当AI反复失败时
   - 当你自己也不理解时
   - 切换到手动研究和学习

4. **清理会议： Anti-Slop Session**
   - 每个AI会话后强制30分钟清理
   - 重构、重命名、移动代码
   - 添加文档

5. **战略性手动干预**
   - 在关键架构点手动调整
   - 为后续AI会话铺平道路

---

## 📚 相关资源

- **Mitchell的博客**: https://mitchellh.com/writing
- **原始文章**: https://mitchellh.com/writing/non-trivial-vibing
- **Amp Code**: https://ampcode.com
- **Ghostty项目**: https://ghostty.org
- **最终PR**: https://github.com/ghostty-org/ghostty/pull/9116

---

## 🎯 核心收获

**Mitchell Hashimoto的AI辅助系统级开发方法论**:

1. **AI是助手，专家是主导**
2. **规划优于编码**
3. **清理是不可或缺的步骤**
4. **小步前进，频繁审查**
5. **知道何时停止用AI**
6. **不理解代码就不合并**
7. **文档帮助AI理解代码**
8. **战略性手动干预为AI铺路**

**对于你的意义**:
- 即使是最底层的系统开发（Zig、内核、系统编程），AI也能提供帮助
- 但你需要更强的领域知识和更严格的审查
- 清理步骤比应用层开发更重要
- 不理解代码的后果在系统级开发中更严重
