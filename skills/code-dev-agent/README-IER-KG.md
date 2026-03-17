# IER-KG: 知识图谱增强的迭代经验精炼系统

IER-KG (Iterative Experience Refinement with Knowledge Graph) 是基于RAGFlow GraphRAG架构的增强版经验管理系统。

## 快速开始

```bash
# 查看IER-KG统计
./codedev.sh ier-kg-stats

# 多跳检索测试
./codedev.sh ier-kg-search "装饰器模式"

# 添加经验关系
./codedev.sh ier-kg-link "装饰器模式" "lru_cache" "complements"

# 查询溯源
./codedev.sh ier-kg-trace "装饰器模式"
```

## 四层架构

1. **Code Entity Graph** - AST解析提取代码结构
2. **Experience Relation Graph** - 经验间的语义关系
3. **Multi-hop Retrieval** - 基于图谱的多跳推理
4. **Provenance System** - 经验溯源机制

## 技术文件

- `ier_kg_system.py` - KG核心系统
- `ier_kg_adapter.py` - IER集成适配器
