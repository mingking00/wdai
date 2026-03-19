# 快速接入指南

## 1. OpenAI (推荐)

```bash
# 安装依赖
pip install openai

# 设置环境变量
export OPENAI_API_KEY="sk-..."
export EMBEDDING_PROVIDER="openai"
```

```python
from core.agent_system.llm_embedding_adapters import EmbeddingConfig
from core.agent_system import create_embedding_context_manager

# 自动从环境变量创建适配器
adapter = EmbeddingConfig.create_for_fresh_eyes()

# 创建Embedding版ContextManager
context_mgr = create_embedding_context_manager(embedding_model=adapter)
```

**成本**: ~$0.0001 / 1K tokens (很便宜)

---

## 2. Cohere (多语言支持好)

```bash
pip install cohere
export COHERE_API_KEY="..."
export EMBEDDING_PROVIDER="cohere"
```

---

## 3. 本地模型 (免费，无需API)

```bash
pip install sentence-transformers
export EMBEDDING_PROVIDER="local"
```

```python
from core.agent_system.llm_embedding_adapters import LocalEmbeddingAdapter

adapter = LocalEmbeddingAdapter(
    model_name="sentence-transformers/all-MiniLM-L6-v2",  # 384维
    device="cpu"  # 或 "cuda" 如果你有GPU
)
```

**优点**: 免费、离线、无延迟  
**缺点**: 质量略低于OpenAI

---

## 对比

| 方案 | 成本 | 质量 | 延迟 | 推荐度 |
|:---|:---:|:---:|:---:|:---:|
| **OpenAI** | $ | ⭐⭐⭐⭐⭐ | ~100ms | ⭐⭐⭐⭐⭐ |
| **Cohere** | $ | ⭐⭐⭐⭐ | ~100ms | ⭐⭐⭐⭐ |
| **Local** | 免费 | ⭐⭐⭐ | ~50ms | ⭐⭐⭐ |

---

## 一键切换

我已经在代码里做好了自动检测：

```python
# 什么都不改，自动选择最佳方案
adapter = EmbeddingConfig.create_for_fresh_eyes()
# 优先级: OpenAI > Cohere > Local > 简化版
```

只要有 `OPENAI_API_KEY` 环境变量，自动用OpenAI。
