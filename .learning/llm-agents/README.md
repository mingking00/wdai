# LLM Agents 学习代码库

**研究ID**: RES-1773290044  
**阶段**: Phase 1 - 基础认知

---

## 📁 文件结构

```
.learning/llm-agents/
├── README.md              # 本文件
├── learning-plan.md       # 完整学习计划
├── react_agent.py         # ReAct基础实现
├── memory_agent.py        # 带记忆系统的进阶实现
├── experiments/           # 实验脚本
└── notes/                 # 学习笔记
```

---

## 🚀 快速开始

### 1. 运行基础ReAct Agent

```bash
cd /root/.openclaw/workspace/.learning/llm-agents
python3 react_agent.py
```

**输出示例:**
```
🤖 ReAct Agent Demo
==================================================

任务1: 简单计算
==================================================
🎯 任务: 计算 15 * 23 等于多少
--- 迭代 1 ---
💭 Thought: 用户需要计算，我应该使用calculator工具。
🔧 Action: calculator({'expression': '2 + 2'})
👁️ Observation: 计算结果: 4...
```

### 2. 运行带记忆系统的Agent

```bash
python3 memory_agent.py
```

**输出示例:**
```
============================================================
🧠 Advanced Agent with Memory System
============================================================
🎯 执行任务: 计算 25 * 16
📚 检索到相关记忆:
✅ 结果: 使用calculator工具完成计算

📊 记忆系统状态
{
  "short_term_count": 7,
  "long_term_count": 3,
  "avg_importance": 7.5
}
```

---

## 📚 核心概念

### ReAct 模式

```
┌─────────┐     ┌─────────┐     ┌─────────────┐
│ Thought │ ──▶ │ Action  │ ──▶ │ Observation │
│  (思考) │     │  (行动) │     │   (观察)    │
└────┬────┘     └─────────┘     └──────┬──────┘
     │                                  │
     └──────────────────────────────────┘
                    循环直到完成
```

**三要素:**
1. **Thought** - 分析当前状态，规划下一步
2. **Action** - 调用工具执行具体操作
3. **Observation** - 获取执行结果，更新状态

### 记忆系统架构

```
┌─────────────────────────────────────────┐
│           记忆系统 (MemorySystem)        │
├──────────────────┬──────────────────────┤
│   短期记忆        │      长期记忆         │
│  (Short-term)    │   (Long-term)        │
│                  │                      │
│ • 容量: 5-7条    │  • 容量: 100条       │
│ • 快速访问       │  • 持久存储          │
│ • 当前上下文     │  • 可检索历史        │
│ • 自动衰减       │  • 重要性加权        │
└──────────────────┴──────────────────────┘
           │
           ▼
    ┌──────────────┐
    │   记忆巩固    │  (定期将重要短期记忆
    │ Consolidate  │   转移到长期存储)
    └──────────────┘
```

**记忆特性:**
- **时间衰减**: 旧记忆相关性降低
- **访问频率**: 常用记忆更容易被检索
- **重要性加权**: 重要事件记忆更深刻
- **标签系统**: 便于分类和检索

---

## 🔧 扩展指南

### 添加新工具

```python
from react_agent import Tool

class MyTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="工具描述",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            }
        )
    
    def execute(self, param1: str) -> str:
        # 实现工具逻辑
        return f"结果: {param1}"

# 使用
my_tool = MyTool()
agent = ReActAgent(tools=[my_tool, calculator, search])
```

### 集成真实LLM

当前代码使用模拟思考，集成真实LLM:

```python
# OpenAI 示例
def think(self, prompt: str) -> str:
    import openai
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是一个ReAct Agent"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
```

### 向量记忆检索

当前使用关键词匹配，可升级为向量相似度:

```python
from sentence_transformers import SentenceTransformer

class VectorMemory(MemorySystem):
    def __init__(self):
        super().__init__()
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.vectors = {}
    
    def add(self, content: str):
        entry_id = super().add(content)
        self.vectors[entry_id] = self.encoder.encode(content)
    
    def retrieve(self, query: str, top_k: int = 3):
        query_vec = self.encoder.encode(query)
        # 计算余弦相似度...
```

---

## 📖 学习路径

### Phase 1: 理解ReAct (本周)
- [ ] 阅读 `react_agent.py`，理解ReAct循环
- [ ] 运行demo，观察Thought-Action-Observation流程
- [ ] 尝试添加新工具

### Phase 2: 理解记忆系统 (下周)
- [ ] 阅读 `memory_agent.py`
- [ ] 理解短期/长期记忆的区别
- [ ] 观察记忆巩固过程

### Phase 3: 实战练习
- [ ] 实现一个完整任务Agent
- [ ] 集成真实LLM API
- [ ] 设计评估实验

---

## 🔗 参考资源

**论文:**
- ReAct: arXiv:2210.03629
- Tree of Thoughts: arXiv:2305.10601
- Agentic LLM Survey: arXiv:2503.23037

**相关代码:**
- LangChain: https://github.com/langchain-ai/langchain
- AutoGPT: https://github.com/Significant-Gravitas/AutoGPT

---

## 📝 更新日志

**2026-03-12**: 创建基础ReAct Agent和记忆系统实现

---

*持续更新中...*
