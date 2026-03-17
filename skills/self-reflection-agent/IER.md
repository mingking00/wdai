# SRA-IER: Self-Reflection Agent 迭代经验精炼系统

基于ChatDev IER论文实现，专门针对SRA（自我复盘Agent）场景设计的经验管理系统。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                   SRA-IER 迭代经验精炼系统                        │
├─────────────────────────────────────────────────────────────────┤
│  1. 经验获取 (Experience Acquisition)                            │
│     └── 从复盘报告中提取经验                                      │
│         ├── Reflection Method经验：日复盘/周复盘/进化复盘方法     │
│         ├── Tip Extraction经验：技巧提取模式                      │
│         ├── Insight Pattern经验：洞察发现模式                     │
│         ├── Error Pattern经验：错误识别和避免模式                 │
│         └── Evolution Strategy经验：自我进化策略                  │
│                                                                  │
│  2. 经验利用 (Experience Utilization)                            │
│     └── 检索相关经验 → 注入复盘Prompt                             │
│         ├── 类型匹配（daily/evolution/conversation）              │
│         ├── 标签匹配                                              │
│         ├── 触发模式匹配                                          │
│         └── 成功率+效果评分加权                                   │
│                                                                  │
│  3. 经验传播 (Experience Propagation)                            │
│     └── 将经验传播到相似任务类型                                  │
│                                                                  │
│  4. 经验淘汰 (Experience Elimination)                            │
│     └── 成功率/使用频率/效果评分多维度评估                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 经验类型

| 类型 | 说明 | 触发条件 |
|------|------|----------|
| **Reflection Method** | 复盘方法 | 每次执行复盘任务 |
| **Tip Extraction** | 技巧提取模式 | 从对话中提取技巧 |
| **Insight Pattern** | 洞察发现模式 | 识别工作中的模式 |
| **Error Pattern** | 错误模式 | 复盘失败或发现错误 |
| **Evolution Strategy** | 进化策略 | 执行进化复盘 |
| **SOUL Update** | SOUL.md更新模式 | 识别需要内化的内容 |
| **Conversation Analysis** | 对话分析方法 | 深度分析对话 |
| **Lesson Learned** | 教训总结 | 从失败中学习 |

## 使用方式

### 1. 自动经验获取

SRA执行复盘任务时，IER自动工作：

```
# 自动触发（每天05:30）
[日复盘] → 检索经验 → 执行复盘 → 提取新方法 → 记录结果

# 自动触发（每天01:30）
[进化复盘] → 检索经验 → 深度分析 → 提取技巧 → 更新SOUL.md建议
```

### 2. IER命令

```bash
cd skills/self-reflection-agent

# 查看IER统计
./sra.sh ier-stats

# 列出所有经验
./sra.sh ier-list

# 列出特定类型经验
./sra.sh ier-list reflection_method
./sra.sh ier-list tip_extraction
./sra.sh ier-list insight_pattern

# 运行经验维护（淘汰过时经验）
./sra.sh ier-maintain
```

### 3. 编程接口

```python
from sra_ier import get_sra_experience_manager

manager = get_sra_experience_manager()

# 手动检索经验
exps = manager.retrieve_relevant_experiences(
    task_type="daily",
    task_description="复盘今日对话",
    top_k=5
)

# 格式化经验为Prompt
prompt = manager.format_experiences_for_prompt(exps)

# 从复盘报告提取经验
new_exps = manager.acquire_from_reflection(
    task_id="REFL_001",
    task_type="daily",
    reflection_report={...},
    tips=[...],
    reflection_success=True
)

# 获取统计
stats = manager.get_statistics()
print(f"复盘方法: {stats['reflection_methods']}")
```

## 效果评分系统

SRA-IER特有的效果评分机制：

| 事件 | 评分变化 |
|------|----------|
| 初始值（成功） | 1.0 |
| 初始值（失败） | 0.3 |
| 成功使用 | +0.1 * quality_score |
| 失败 | -0.15 |

## 经验可靠性评估

- **可靠经验**: usage >= 3 AND success_rate >= 70% AND effectiveness >= 0.5
- **暂停经验**: usage >= 3 AND success_rate < 30%
- **淘汰条件**:
  - 成功率 < 30% 且使用次数 >= 5
  - 90天未使用且使用次数 < 3
  - 效果评分 < 0.3 且使用次数 > 2

## 数据存储

```
skills/self-reflection-agent/ier/
├── experiences.json          # 经验数据
├── task_history.json         # 任务历史
└── reflection_methods.json   # 复盘方法索引
```

## 与SRA集成流程

```
定时触发: 每天22:00日复盘
    ↓
[SRA-IER] 检索相关复盘方法
    ↓
[经验注入] 添加到分析Prompt
    ↓
[SRA执行] 分析对话 → 提取技巧
    ↓
[SRA-IER] 提取新经验:
  - Reflection Method: 日复盘流程
  - Tip Extraction: 技巧识别模式
  - Insight Pattern: 对话模式发现
    ↓
[SRA-IER] 记录任务完成，更新效果评分
    ↓
下次复盘 → 使用这些经验
```

## 与其他IER系统的区别

| 特性 | SRA-IER | SEA-IER | CodeDev-IER |
|------|---------|---------|-------------|
| **场景** | 自我复盘/进化 | 系统进化 | 新代码开发 |
| **经验焦点** | 复盘方法/技巧提取 | before/after重构模式 | 解决方案/设计模式 |
| **特殊功能** | 效果评分系统、触发模式匹配 | 文件类型匹配、置信度评分 | 多角色经验共享 |
| **触发点** | 定时复盘任务 | 改进请求 | 开发请求 |
| **经验类型** | 8种（侧重方法/洞察） | 8种（侧重重构/设计） | 6种（侧重模式/工具） |

## 应用场景示例

### 场景1: 进化复盘优化

```
第1次进化复盘:
- 手动分析对话
- 提取3个技巧
- 记录复盘方法

第2次进化复盘:
- IER检索到上次的方法
- 使用相同流程
- 提取效率提高
- 记录优化后的方法

第N次进化复盘:
- 使用经过验证的最佳复盘方法
- 提取技巧效率持续提高
```

### 场景2: 错误模式学习

```
复盘失败 → IER提取Error Pattern
    ↓
下次复盘前 → IER提示注意事项
    ↓
避免同样错误 → 成功率提高
```

## 意义

1. **复盘方法进化**: SRA能从每次复盘中学习方法，不断提高复盘质量
2. **技巧提取优化**: 识别最有效的技巧提取模式
3. **自我改进闭环**: 复盘→学习→改进→更好的复盘
4. **知识沉淀**: 将隐性复盘经验显性化、可复用
