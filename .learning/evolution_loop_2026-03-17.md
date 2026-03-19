# wdai 进化内循环执行记录 - 2026-03-17

## 1. 自我评估（识别问题）

基于Fresh Eyes量化评估结果：

| 问题 | 证据 | 严重程度 |
|:---|:---|:---:|
| 增强版过度偏好文档文件 | 代码审查场景：增强版选docs/过多，F1 0.57 vs 简单版0.89 | 高 |
| 增强版召回率低 | 整体召回率0.524 vs 简单版0.679 | 中 |
| 默认使用增强版不合理 | F1相近(0.553 vs 0.567)，但增强版更慢 | 高 |
| 执行力问题 | 用户明确选择B后仍重复确认 | 高 |

## 2. 目标设定

**P0（立即执行）**：
- [x] 将默认ContextManager改为simple版
- [x] 记录执行力问题教训

**P1（短期）**：
- [ ] 修复增强版文档偏好问题（调整文档权重）
- [ ] 建立用户选择后直接执行的机制

**P2（长期）**：
- [ ] 重新评估是否需要Embedding版
- [ ] 优化代码依赖图分析器的模块解析

## 3. 执行改进

### 已执行
```bash
# P0: 修改默认版本
edit core/agent_system/__init__.py: "enhanced" -> "simple"
edit core/agent_system/orchestrator.py: "enhanced" -> "simple"

# P1: 修复增强版文档偏好
edit core/agent_system/context_enhanced.py:
  # 任务类型感知文档权重
  if file_path.endswith(('.md', '.rst', '.txt')):
      if subtask.type == 'document':
          semantic_score *= 1.2
      else:
          semantic_score *= 0.5

# P2: 修复代码依赖图模块解析
edit core/agent_system/dependency_analyzer.py:
  # 三轮构建确保所有节点先加入
  # 改进模块解析支持目录/模糊/精确匹配
```

### 待验证
- [x] 重新运行评估测试 - 完成（F1差异-0.014，保持simple默认）
- [x] 依赖分析器测试 - 完成（10项全部通过）

### 当前状态
- Fresh Eyes: 默认simple版，保留enhanced/embedding可选
- 增强版: 文档权重已优化，整体F1仍略低于simple
- 依赖分析器: 模块解析已修复，测试全部通过

## 4. 效果验证

| 改进项 | 验证方法 | 状态 |
|:---|:---|:---:|
| 默认改simple | 初始化测试 | ✅ 通过 |
| 教训记录 | 检查MEMORY.md | ✅ 已记录 |

## 5. 知识沉淀

**已沉淀到MEMORY.md**：
- Fresh Eyes评估结论
- 执行力问题教训
- 进化内循环执行记录

**待沉淀**：
- 增强版权重调优后的重新评估

## 6. 下一步行动

1. 执行P1：调整增强版文档权重
2. 重新评估增强版效果
3. 决定是否保留增强版或删除

---
*进化内循环 - 第1轮*  
*执行时间: 2026-03-17 19:10*
