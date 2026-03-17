# Task Planner Skill

## Overview
任务规划与多模型验证系统，借鉴 ccg-workflow 的规划-执行分离和多模型交叉验证思想。

## Features

### 1. 强制规划模式 (Mandatory Planning)
- 复杂任务（超过一定复杂度阈值）必须先规划
- 生成详细执行计划，用户确认后再执行
- 计划结构化存储，便于追踪和复盘

### 2. 多模型交叉验证 (Multi-Model Validation)
- 关键决策启动多个模型并行分析
- 自动整合多模型输出，提取共识
- 标记分歧点供人工审查

### 3. 约束提取引擎 (Constraint Extraction)
- 将用户模糊需求转化为明确约束
- 自动补全隐含约束
- 约束检查确保执行符合要求

## Commands

### /plan <task>
生成任务执行计划

### /validate <decision>
多模型验证关键决策

### /extract-constraints <requirement>
提取并补全约束

## Usage

```python
from task_planner import TaskPlanner

planner = TaskPlanner()

# 规划任务
plan = await planner.plan("实现用户认证系统")

# 多模型验证
validation = await planner.validate_architecture([
    "使用 JWT",
    "Redis 存储会话",
    "支持 OAuth"
])

# 提取约束
constraints = planner.extract_constraints("做个高性能 API")
```
