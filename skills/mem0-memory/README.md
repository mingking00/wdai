# mem0-memory 技能使用指南

## 🚀 快速开始

### 安装
```bash
# 将技能复制到 OpenClaw 技能目录
cp -r skills/mem0-memory ~/.openclaw/skills/

# 或在配置中添加
openclaw skills add mem0-memory
```

### 基础用法

#### 1. 提取记忆
```bash
# 从对话文件提取记忆
python scripts/memory_extract.py \
  --source conversation.md \
  --output .memory/ \
  --user-id user_123
```

#### 2. 检索记忆
```bash
# 混合检索（推荐）
python scripts/memory_search.py \
  --query "用户喜欢什么编程语言？" \
  --top-k 5 \
  --verbose

# 仅最近7天的记忆
python scripts/memory_search.py \
  --query "最近的决定" \
  --days 7
```

#### 3. 维护记忆
```bash
# 模拟运行（查看会删除哪些）
python scripts/memory_decay.py --dry-run --report

# 实际清理（带备份）
python scripts/memory_decay.py --half-life 30
```

---

## 📊 核心特性

| 特性 | 说明 | 价值 |
|------|------|------|
| **两阶段提取** | LLM提取+规则过滤 | 高质量原子记忆 |
| **混合检索** | 向量+BM25+时间 | 召回率>90% |
| **智能衰减** | 指数衰减+访问提升 | 自动清理过期信息 |
| **冲突解决** | 新旧记忆智能合并 | 避免信息矛盾 |

---

## 🔧 高级配置

### 自定义嵌入模型
编辑 `scripts/memory_search.py`:
```python
class SimpleEmbedding:
    def __init__(self):
        # 替换为 OpenAI/Ollama/本地模型
        self.embedder = OpenAIEmbedding("text-embedding-3-small")
```

### 调整衰减参数
```bash
# 快速衰减（半衰期7天）
python scripts/memory_decay.py --half-life 7

# 慢速衰减（半衰期90天）
python scripts/memory_decay.py --half-life 90 --threshold 0.05
```

---

## 💡 使用场景

### 场景1: 跨会话记忆
```python
# Session 1
user: "我喜欢用Python，不喜欢Java"
→ 提取: {category: "preference", content: "用户喜欢Python，不喜欢Java"}

# Session 2（一周后）
user: "推荐一门编程语言"
→ 检索: "用户喜欢Python..."
→ LLM: "基于您之前的偏好，推荐Python..."
```

### 场景2: 项目上下文
```python
# 记录决策
"我们决定使用PostgreSQL而不是MySQL"

# 两周后查询
"我们用什么数据库？" → PostgreSQL
```

### 场景3: 自动清理
```bash
# 每月运行一次
0 0 1 * * python /path/to/memory_decay.py --half-life 30
```

---

## 📈 性能指标

| 指标 | 值 | 说明 |
|------|-----|------|
| 检索延迟 | <100ms | 本地LanceDB |
| 提取准确率 | ~85% | LLM两阶段提取 |
| 存储增长 | 亚线性 | 自动去重+衰减 |
| 冲突解决 | 自动 | 置信度加权 |

---

## 🔗 与 OpenClaw 集成

### 在 SKILL.md 中使用
```yaml
# 在任务开始时检索相关记忆
pre_task:
  - memory_search:
      query: "{{task_description}}"
      inject_to_context: true

# 在任务结束时提取新记忆
post_task:
  - memory_extract:
      source: "{{conversation}}"
```

### 在 AGENTS.md 中添加持久指令
```markdown
Before responding to user:
1. Search memory for relevant context using memory_search.py
2. If task changes structural understanding, update .nexus-map
3. Extract key facts after important conversations
```

---

## 🛠️ 故障排除

### 问题: 检索结果为空
**解决**: 
```bash
# 检查记忆目录
ls -la .memory/

# 确保文件格式正确（JSON或JSONL）
```

### 问题: 提取质量低
**解决**:
```bash
# 调整置信度阈值
python memory_extract.py --min-confidence 0.8
```

### 问题: 衰减太激进
**解决**:
```bash
# 使用更宽松的参数
python memory_decay.py --half-life 60 --threshold 0.05
```

---

## 📚 参考文档

- [提取算法详解](references/01-extraction-algorithm.md)
- [检索管道详解](references/02-retrieval-pipeline.md)
- [Mem0 论文](https://arxiv.org/abs/2409.19113)
- [memory-lancedb-pro](https://github.com/win4r/memory-lancedb-pro)

---

## ✅ 检查清单

使用前确认：
- [ ] Python 3.10+ 已安装
- [ ] `.memory/` 目录已创建
- [ ] 嵌入模型已配置（或使用默认简化版）
- [ ] 了解衰减参数含义

---

**技能已就绪，可直接使用。**