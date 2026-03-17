# SEA-IER: System Evolution Agent 迭代经验精炼系统

基于ChatDev IER论文实现，专门针对SEA（系统进化Agent）场景设计的经验管理系统。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEA-IER 迭代经验精炼系统                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Experience Acquisition (经验获取)                            │
│     └── 从代码变更中提取经验                                      │
│         ├── Refactoring经验：重构模式（提取方法、重命名等）       │
│         ├── Code Pattern经验：代码改进模式                        │
│         ├── Design Decision经验：架构设计决策                     │
│         ├── Error Fix经验：错误修复模式                           │
│         └── Performance经验：性能优化模式                         │
│                                                                  │
│  2. Experience Utilization (经验利用)                            │
│     └── 检索相关经验 → 注入改进请求Prompt                         │
│         ├── 标签匹配                                              │
│         ├── 文件类型匹配                                          │
│         ├── 改进类型匹配                                          │
│         └── 成功率加权                                            │
│                                                                  │
│  3. Experience Propagation (经验传播)                            │
│     └── 将经验传播到相似文件                                      │
│                                                                  │
│  4. Experience Elimination (经验淘汰)                            │
│     └── 成功率过低/长期未使用/低置信度                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 经验类型

| 类型 | 说明 | 触发条件 |
|------|------|----------|
| **Refactoring** | 重构模式 | 代码结构变化 |
| **Code Pattern** | 代码改进 | 日志/配置/错误处理改进 |
| **Design Decision** | 设计决策 | 架构/模块化/解耦相关 |
| **Error Fix** | 错误修复 | 空值/索引/类型错误修复 |
| **Performance** | 性能优化 | 缓存/异步/批处理相关 |
| **Integration** | 集成模式 | 系统集成经验 |
| **Tool Usage** | 工具技巧 | 工具使用经验 |
| **Anti-Pattern** | 反模式 | 需要避免的做法 |

## 使用方式

### 1. 自动经验获取

当SEA执行改进请求时，IER自动工作：

```python
# 提交改进请求
./seas.sh improve "优化错误处理" "skills/my_tool/core.py"

# IER自动执行：
# 1. 检索相关经验
# 2. 注入到改进Prompt
# 3. 执行改进
# 4. 提取新经验
# 5. 记录任务结果
```

### 2. IER命令

```bash
cd skills/system-evolution-agent

# 查看IER统计
./seas.sh ier-stats

# 列出所有经验
./seas.sh ier-list

# 列出特定类型经验
./seas.sh ier-list refactoring
./seas.sh ier-list code_pattern
./seas.sh ier-list error_fix

# 运行经验维护（淘汰过时经验）
./seas.sh ier-maintain
```

### 3. 编程接口

```python
from sea_ier import get_sea_experience_manager

manager = get_sea_experience_manager()

# 手动检索经验
exps = manager.retrieve_relevant_experiences(
    task_description="优化错误处理",
    target_file="skills/my_tool/core.py",
    change_type="improve"
)

# 格式化经验为Prompt
prompt = manager.format_experiences_for_prompt(exps)

# 从变更提取经验
new_exps = manager.acquire_from_change(
    task_id="TASK_001",
    description="添加日志记录",
    change_diff="...",
    file_path="core.py",
    change_success=True
)

# 获取统计
stats = manager.get_statistics()
print(f"活跃经验: {stats['active_experiences']}")
```

## 经验可靠性评估

### 置信度评分
- **初始值**: 1.0 (成功) / 0.3 (失败)
- **成功使用**: +0.1
- **失败**: -0.2

### 可靠性标准
- **可靠经验**: usage >= 3 AND success_rate >= 70%
- **暂停经验**: usage >= 3 AND success_rate < 30%
- **淘汰条件**:
  - 成功率 < 30% 且使用次数 >= 5
  - 90天未使用且使用次数 < 3
  - 置信度 < 0.5 且失败次数 > 2

## 数据存储

```
skills/system-evolution-agent/ier/
├── experiences.json          # 经验数据
├── task_history.json         # 任务历史
└── refactoring_patterns.json # 重构模式索引
```

## 与SEA集成流程

```
用户: "优化SEA的错误处理机制"
    ↓
[SEA-IER] 检索相关经验:
  - Refactoring: Extract Method
  - Pattern: Error Handling
  - Fix: Null Safety
    ↓
[经验注入] 添加到改进Prompt
    ↓
[SEA执行] 生成改进代码
    ↓
[SEA-IER] 提取新经验:
  - Refactoring: Simplify Conditional
  - Pattern: Logging
    ↓
[SEA-IER] 记录任务成功
    ↓
下次类似任务 → 使用这些经验
```

## 与CodeDev IER的区别

| 特性 | SEA-IER | CodeDev-IER |
|------|---------|-------------|
| **场景** | 系统/技能进化 | 新代码开发 |
| **经验类型** | Refactoring/Design/Fix | Pattern/Shortcut/Tool |
| **触发点** | 改进请求 | 开发请求 |
| **输出** | before/after模式 | 解决方案 |
| **传播** | 相似文件 | 相似任务 |

## 配置文件

IER系统自动加载，无需额外配置。经验数据持久化存储在 `ier/` 目录下。
