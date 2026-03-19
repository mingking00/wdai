# 自动会话追踪系统 - 完整实现

借鉴 Zep 的自动摘要机制，实现会话自动追踪和摘要生成。

---

## 已实现功能

| 功能 | 状态 | 说明 |
|:---|:---:|:---|
| **消息自动追踪** | ✅ | 单例模式，全局统一追踪 |
| **实时持久化** | ✅ | 消息实时保存到 JSON 文件 |
| **程序退出保护** | ✅ | atexit 钩子，防止崩溃丢失 |
| **自动摘要生成** | ✅ | 会话结束时自动生成 |
| **Markdown 归档** | ✅ | 保存到 memory/daily/ |
| **JSON 备份** | ✅ | 结构化数据便于程序读取 |

---

## 核心文件

```
.claw-status/
├── auto_summarize.py          # 摘要生成核心 (14KB)
├── session_hooks.py           # 会话追踪钩子 (10KB)
└── openclaw_integration.py    # OpenClaw 集成 (5KB)

memory/daily/
└── 2026-03-18.md              # 自动生成的摘要

.claw-status/summaries/
└── session_*.json             # JSON 格式摘要
```

---

## 使用方式

### 方式 1: 快捷函数（最简单）

```python
from .claw-status.session_hooks import track_user, track_assistant, end_current_session

# 追踪消息
track_user("用户输入内容")
track_assistant("助手回复内容")

# 会话结束
try:
    await end_current_session()
except:
    pass  # 程序退出时会自动调用
```

### 方式 2: SessionTracker 类（更灵活）

```python
from .claw-status.session_hooks import SessionTracker

# 获取追踪器（单例）
tracker = SessionTracker()

# 添加消息
tracker.add_user_message("用户输入")
tracker.add_assistant_message("助手回复")

# 查看统计
tracker.print_stats()

# 结束会话
summary = await tracker.end_session()
print(summary.to_markdown())
```

### 方式 3: OpenClaw 集成（自动追踪）

在 OpenClaw 初始化时添加：

```python
import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3/.claw-status')
from openclaw_integration import on_user_message, on_assistant_message, on_session_end

# 在消息处理中调用
async def handle_message(role, content):
    if role == 'user':
        on_user_message(content)
    else:
        on_assistant_message(content)
    # ... 原有处理

# 会话结束
async def cleanup():
    on_session_end()
```

---

## 演示

```bash
# 运行演示
cd /root/.openclaw/workspace/wdai_v3
python3 .claw-status/session_hooks.py

# 查看生成的摘要
cat memory/daily/2026-03-18.md
```

---

## 输出示例

### Markdown 格式（人类可读）

```markdown
## 会话摘要 [2026-03-18T01:59:15]

**会话ID**: `session_20260318_015912`  
**时长**: 0.1 分钟  
**消息数**: 6 (用户: 3, 助手: 3)

### 🎯 关键决策

1. **好的，我决定搜索 Kimi 的 Attention Residuals 技术报告。**
   - 时间: 2026-03-18T01:59:13
   - 详情: 好的，我决定搜索 Kimi 的 Attention Residuals 技术报告。

### ❌ 错误与纠正

1. **用户纠正**: 不对，应该先理解核心思想
   - 纠正: 您说得对，我学到了...

### 💡 学习点

1. **一般认知**: 您说得对，我学到了：应该先理解核心思想再搜索细节。
   - 来源: 2026-03-18T01:59:14

### ✅ TODO

1. [ ] 后续需要添加测试
   - 优先级: normal

---
```

### JSON 格式（程序可读）

```json
{
  "session_id": "session_20260318_015912",
  "timestamp": "2026-03-18T01:59:15",
  "duration_minutes": 0.1,
  "stats": {
    "total_messages": 6,
    "user_messages": 3,
    "assistant_messages": 3
  },
  "key_decisions": [...],
  "errors": [...],
  "learnings": [...],
  "todo_items": [...]
}
```

---

## 与 Zep 的对比

| 特性 | Zep | 我的实现 |
|:---|:---|:---|
| **架构** | 独立服务 + 数据库 | 代码集成 + 文件系统 |
| **追踪方式** | API 调用 | 函数调用 / 自动钩子 |
| **摘要生成** | LLM 异步生成 | 规则提取 (O(1)) |
| **持久化** | 数据库存储 | 文件系统 |
| **检索** | 向量语义搜索 | 文件读取 |
| **集成难度** | 需要部署 | 一行代码导入 |

**核心借鉴**：
- ✅ 自动追踪概念
- ✅ 会话结束摘要
- ✅ 分类提取（决策/错误/学习/TODO）
- ✅ 时序归档（按日期存储）
- ✅ 程序退出保护

---

## 自动触发机制

### 1. 消息追踪
```python
# 每次调用 track_user / track_assistant
# 自动追加到内存列表
# 实时保存到 current_session.json
```

### 2. 会话结束触发
```python
# 方式 A: 手动调用 await end_current_session()
# 方式 B: 程序退出时 atexit 自动调用
# 方式 C: 消息数量达到阈值时自动触发
```

### 3. 摘要生成
```python
# 1. 提取关键信息（决策/错误/学习/TODO）
# 2. 生成 Markdown 保存到 memory/daily/
# 3. 生成 JSON 保存到 .claw-status/summaries/
# 4. 清空 current_session.json
```

---

## 注意事项

1. **单例模式**：SessionTracker 是单例，全局只有一个实例
2. **消息阈值**：默认少于 3 条消息不生成摘要（可用 `force=True` 覆盖）
3. **实时保存**：消息会实时保存到文件，防止崩溃丢失
4. **自动清理**：程序退出时会自动尝试生成摘要

---

## 下一步改进

1. **LLM 增强摘要**：使用 LLM 生成更智能的摘要
2. **增量更新**：会话进行中实时更新摘要
3. **语义搜索**：对历史摘要建立索引
4. **可视化界面**：Web 界面查看历史会话

---

*实现时间: 2026-03-18*  
*状态: ✅ 生产就绪*
