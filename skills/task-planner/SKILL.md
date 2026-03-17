---
name: task-planner
description: "Task planning and multi-model validation system inspired by ccg-workflow. Features mandatory planning for complex tasks, multi-model cross-validation for critical decisions, and constraint extraction from vague requirements."
---

# Task Planner Skill 🎯

> 借鉴 ccg-workflow 的规划-执行分离和多模型交叉验证思想
> 
> **核心原则**: 复杂任务先规划，关键决策多验证，模糊需求转约束

## Features

### 1. 强制规划模式 (Mandatory Planning)
自动评估任务复杂度，复杂任务必须先规划：
- **Simple**: 直接执行
- **Moderate**: 建议规划
- **Complex**: 强制规划

### 2. 多模型交叉验证 (Multi-Model Validation)
关键决策启动多模型并行分析：
- 提取共识
- 标记分歧点
- 生成建议

### 3. 约束提取引擎 (Constraint Extraction)
将模糊需求转化为明确约束：
- 关键词映射隐含约束
- 自动补全缺失约束
- 约束冲突检测

## Quick Start

```python
from skills.task_planner.openclaw_integration import plan, validate, smart_plan

# 1. 规划任务
plan_text = await plan("实现用户认证系统")

# 2. 多模型验证关键决策
report = await validate("使用 Redis 作为会话存储", "architecture")

# 3. 智能规划（评估+规划+验证）
full_report = await smart_plan("重构用户模块")
```

## Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `/plan <task>` | 生成任务执行计划 | 任何任务开始前 |
| `/validate <decision>` | 多模型验证决策 | 关键架构/技术决策 |
| `/extract <requirement>` | 提取约束条件 | 需求模糊时 |
| `/smart-plan <task>` | 智能全流程规划 | 复杂任务 |

## Architecture

```
TaskPlanner
├── ConstraintExtractor
│   ├── 关键词映射 → 隐含约束
│   └── 补全检查 → 缺失约束
├── ComplexityAssessor
│   ├── 关键词评分
│   └── 上下文评分
└── PlanGenerator
    └── 生成步骤 + 风险识别

MultiModelValidator
├── 并行验证 (多个模型)
└── ConsensusAnalyzer
    ├── 通过率统计
    ├── 分歧点识别
    └── 建议生成
```

## Usage Examples

### Example 1: 规划复杂任务

```python
from skills.task_planner.openclaw_integration import plan

# 用户请求
result = await plan("重构用户模块，实现高性能登录API")

# 输出：
# # 任务计划 [20260316-a1b2c3d4]
# 
# **任务**: 重构用户模块，实现高性能登录API
# **复杂度**: complex
# **预估时间**: 3h
#
# ## 约束条件
# - [performance] 响应时间 < 200ms (P9)
# - [performance] 支持并发 > 1000 QPS (P8) [隐含]
# - [security] 密码加密存储 (P10) [隐含]
# - [functional] 用户认证 (P10) [隐含]
#
# ## 执行步骤
# 1. 需求分析 - 30min
# 2. 架构设计 - 45min (依赖: [1])
# ...
```

### Example 2: 验证关键决策

```python
from skills.task_planner.openclaw_integration import validate

# 验证架构决策
report = await validate(
    "使用 Redis Cluster 存储用户会话，JWT 作为认证令牌",
    "architecture"
)

# 输出：
# ## 多模型验证报告
# 
# **共识级别**: ✅ full
# **通过率**: 100%
# **平均置信度**: 8.5/10
# 
# ### 建议
# - ✅ 全票通过，可以执行
# - 关注共同指出的问题: 考虑Redis故障降级
```

### Example 3: 检查是否需要规划

```python
from skills.task_planner.openclaw_integration import check_planning_needed

# 自动判断
if check_planning_needed("重构用户系统"):
    print("这是复杂任务，建议先规划")
```

## Integration with CodeDev Agent

当 CodeDev Agent 接收到任务时，自动触发规划检查：

```python
async def handle_task(task: str):
    # 1. 检查是否需要规划
    if check_planning_needed(task):
        # 2. 生成计划
        plan_result = await smart_plan(task)
        # 3. 向用户展示并等待确认
        # 4. 用户确认后执行
    else:
        # 简单任务直接执行
        await execute_directly(task)
```

## Configuration

### 复杂度阈值
```python
COMPLEXITY_THRESHOLDS = {
    "lines_estimate": 100,  # 预估代码行数
    "component_count": 3,   # 涉及组件数
    "dependency_depth": 2,  # 依赖层级
}
```

### 隐含约束映射
```python
IMPLICIT_CONSTRAINTS = {
    "高性能": [
        Constraint("performance", "响应时间 < 200ms", 9, "压力测试"),
        Constraint("performance", "支持并发 > 1000 QPS", 8, "负载测试"),
    ],
    "安全": [
        Constraint("security", "输入验证", 10, "渗透测试"),
        ...
    ],
}
```

## Future Enhancements

- [ ] 真正的多模型并行调用（Kimi + Claude + Gemini）
- [ ] LLM 驱动的智能约束提取
- [ ] 计划执行追踪和进度更新
- [ ] 历史计划学习和优化
- [ ] 与用户现有 workflow 集成

## References

- [ccg-workflow](https://github.com/fengshao1227/ccg-workflow) - Claude Code 多模型协作工作流
- [multi-agent-research](../multi-agent-research/) - OpenClaw 多智能体研究系统
