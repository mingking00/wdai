---
evo_id: "evo-006"
title: "Planning框架实现"
priority: P0
status: completed
estimated_tokens: 15000
actual_tokens: 8000
start_date: 2026-03-19
target_date: 2026-03-19
tags: [planning, react, completed, P0]
related_patterns: ["Planning", "ReAct"]
book_ref: "Chapter 6, Chapter 17"
prerequisites: []
---

# evo-006: Planning框架实现 ✅

## 目标
实现ReAct (Reasoning + Acting) 最小框架，能跑通3个测试用例

## 交付物

| 文件 | 说明 | 行数 |
|------|------|------|
| `evo-006-react.py` | ReAct核心实现 | 51行 |
| `evo-006-integration.py` | WDai v3.7集成 | 120行 |

## 核心实现

**ReAct循环**:
```
Thought -> Action -> Observation -> (repeat) -> Answer
```

**代码结构**:
```python
class ReActAgent:
    def run(self, task, max_steps=10):
        for step in range(max_steps):
            response = self.llm(prompt)
            parsed = self._parse_response(response)
            if parsed["action"] == "finish":
                return parsed["action_input"]
            observation = self._execute_action(parsed["action"], parsed["action_input"])
            prompt += f"\nObservation: {observation}\n"
```

## 测试用例 (全部通过 ✅)

1. **数学计算**: `(15 + 27) * 3 - 8` → `118`
2. **搜索查询**: "What is ReAct?" → 返回相关信息
3. **多步推理**: 比较ReAct和Planning → 多步骤完成

## 集成到WDai v3.7

**自动判断**是否需要ReAct:
```python
def _needs_planning(self, task: str) -> bool:
    planning_keywords = ["calculate", "and then", "search and", "step by step"]
    return any(kw in task.lower() for kw in planning_keywords)
```

**工具注册**:
- `read_file`: 读取文件
- `write_file`: 写入文件
- `search_memory`: 搜索记忆
- `calculator`: 计算表达式

## 验收标准

- [x] 3个用例全部跑通
- [x] 代码<150行 (实际51行)
- [x] 每步有思考过程输出
- [x] 集成到WDai v3.7 ✅

## 关键学习

1. **MVP优先**: 51行核心代码 > 150行完整实现
2. **mock测试**: 用模拟LLM测试逻辑，不依赖真实API
3. **自动判断**: 关键词匹配决定是否启用ReAct

---

*完成时间: 2026-03-19*  
*实际token: 8k (预估15k)*  
*状态: ✅ 已完成*
