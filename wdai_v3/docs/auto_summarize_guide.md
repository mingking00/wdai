# 自动会话摘要系统 - 使用指南

借鉴 Zep 的自动摘要机制，实现会话结束后的自动信息提取和归档。

---

## 功能特性

| 功能 | 说明 |
|:---|:---|
| **关键决策提取** | 自动识别 "决定"、"选择"、"采用" 等标记的决策点 |
| **错误与纠正** | 检测用户的纠正（"不对"、"错误"）和助手的自我修复 |
| **学习点提取** | 识别 "学到"、"发现"、"意识到" 等学习标记 |
| **TODO 提取** | 提取 TODO、FIXME、待办等任务项 |
| **自动归档** | 保存到 `memory/daily/YYYY-MM-DD.md` |

---

## 快速开始

### 1. 基础使用

```python
import asyncio
from .claw-status.auto_summarize import SessionSummarizer

# 创建摘要器
summarizer = SessionSummarizer()

# 准备消息列表
messages = [
    {'role': 'user', 'content': '请帮我实现一个功能'},
    {'role': 'assistant', 'content': '我决定使用 Zep 的自动摘要机制'},
    {'role': 'user', 'content': '不对，应该先设计数据结构'},
    {'role': 'assistant', 'content': '学到了：应该先设计数据结构再实现'},
]

# 生成摘要
async def main():
    summary, file_path = await summarizer.summarize_and_save(messages)
    print(f"摘要已保存: {file_path}")
    print(summary.to_markdown())

asyncio.run(main())
```

### 2. 手动触发当前会话摘要

```bash
cd /root/.openclaw/workspace/wdai_v3
python3 .claw-status/summarize_session_end.py
```

### 3. 在代码中集成

```python
from .claw-status.summarize_session_end import manual_summarize

# 在会话结束时调用
messages = get_session_messages()  # 你的消息获取函数
markdown = manual_summarize(messages)
print(markdown)
```

---

## 输出格式

生成的摘要保存为 Markdown 格式：

```markdown
## 会话摘要 [2026-03-18T01:56:03]

**会话ID**: `session_001`  
**时长**: 15.5 分钟  
**消息数**: 12 (用户: 6, 助手: 6)

### 🎯 关键决策

1. **采用 Zep 的自动摘要机制**
   - 时间: 2026-03-18 10:01:00
   - 详情: 我决定使用异步处理方式

### ❌ 错误与纠正

1. **用户纠正**: 不对，应该先设计数据结构
   - 纠正: 您说得对，我重新设计...

### 💡 学习点

1. **技术实现**: 应该先设计数据结构再实现
   - 来源: 2026-03-18 10:03:00

### ✅ TODO

1. [ ] 优化性能
   - 优先级: normal

---
```

---

## 提取规则

### 决策标记词
```python
DECISION_MARKERS = [
    '决定', '选择', '采用', '使用', '确定', '选定',
    'decide', 'choose', 'select', 'adopt'
]
```

### 错误标记词
```python
ERROR_MARKERS = [
    '错误', '失败', '不对', '有问题', 'bug', 'fix',
    'error', 'fail', 'wrong', 'issue'
]
```

### 学习标记词
```python
LEARNING_MARKERS = [
    '学到', '发现', '原来', '意识到', '明白',
    'learn', 'discover', 'realize'
]
```

### TODO 标记词
```python
TODO_MARKERS = [
    'TODO', 'FIXME', 'HACK', '待办', '待完成'
]
```

---

## 文件位置

```
wdai_v3/
└── .claw-status/
    ├── auto_summarize.py           # 核心摘要模块
    └── summarize_session_end.py    # 会话结束钩子

memory/
└── daily/
    └── 2026-03-18.md               # 自动生成的摘要
```

---

## 与 Zep 的对比

| 特性 | Zep | 我的实现 |
|:---|:---|:---|
| **架构** | 独立服务 + 数据库 | 文件系统 + 代码集成 |
| **自动化** | 完全自动 | 半自动（需手动触发或集成） |
| **摘要生成** | 使用 LLM | 基于规则的快速提取 |
| **检索** | 向量语义搜索 | 文件读取 |
| **适用场景** | 多用户生产环境 | 单用户个人工作空间 |

**核心借鉴**：
- ✅ 自动摘要概念
- ✅ 分类提取（决策/错误/学习/TODO）
- ✅ 时序归档（按日期存储）

---

## 演示

```bash
cd /root/.openclaw/workspace/wdai_v3
python3 .claw-status/auto_summarize.py
```

---

## 下一步改进

1. **LLM 增强摘要**：使用 LLM 生成更智能的摘要
2. **增量更新**：支持会话进行中实时更新摘要
3. **语义搜索**：对摘要内容建立索引
4. **可视化**：生成会话时间线和决策图谱

---

*实现时间: 2026-03-18*  
*状态: ✅ 可用*
