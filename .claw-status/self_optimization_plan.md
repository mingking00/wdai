---
type: improvement-plan
title: "WDai 自我优化计划 v1.0"
date: 2026-03-19
system_version: "3.7"
tags: [self-optimization, auto-improvement, context, performance, memory]
---

# WDai 自我优化计划

> 针对5个核心问题的自动改进方案  
> 集成到SEIS自动执行

---

## 问题1: 上下文爆炸

### 症状
- 128k context快速耗尽
- 复杂任务时历史信息冗余
- 关键信息淹没在对话历史中

### 自动优化方案

**任务: auto-ctx-001 对话摘要**
```yaml
trigger: conversation_rounds > 10
action: 
  1. 提取关键决策和结论
  2. 压缩历史对话为摘要
  3. 保留重要上下文，丢弃细节
threshold: 每10轮自动执行
```

**任务: auto-ctx-002 分层记忆迁移**
```yaml
trigger: session_end OR memory_size > 100KB
action:
  1. 短期(当前会话) → 中期(本周)
  2. 中期 → 长期(核心记忆)
  3. 自动更新索引
threshold: 每天23:00执行
```

**任务: auto-ctx-003 关键信息提取**
```yaml
trigger: user_says "记住" OR "重要"
action:
  1. 提取当前轮次关键信息
  2. 写入memory/core/关键决策.md
  3. 添加双向链接
```

### 实施文件
- `.claw-status/auto/context_compressor.py`
- `.claw-status/auto/memory_migrator.py`

---

## 问题2: 重复工作

### 症状
- 每次重启从零加载
- 重复读取相同文件
- 无状态持久化

### 自动优化方案

**任务: auto-state-001 会话快照**
```yaml
trigger: every_30_minutes OR before_restart
action:
  1. 保存当前加载的文件列表
  2. 保存中间计算结果
  3. 保存活跃记忆索引
output: .claw-status/snapshots/session_{timestamp}.json
```

**任务: auto-state-002 热启动加载**
```yaml
trigger: session_start
action:
  1. 读取最近的快照
  2. 预加载常用文件索引
  3. 恢复会话状态
time_limit: < 5 seconds
```

**任务: auto-state-003 增量更新**
```yaml
trigger: file_access
action:
  1. 检查文件mtime
  2. 只读取变化的部分
  3. 更新缓存索引
```

### 实施文件
- `.claw-status/auto/session_snapshot.py`
- `.claw-status/auto/hot_start.py`

---

## 问题3: 响应慢

### 症状
- 复杂任务思考时间长
- 无进度反馈
- 用户体验差

### 自动优化方案

**任务: auto-perf-001 流式输出**
```yaml
trigger: estimated_tokens > 2000
action:
  1. 边生成边输出
  2. 分块发送（每100token）
  3. 显示思考进度
```

**任务: auto-perf-002 Token预估**
```yaml
trigger: before_task_start
action:
  1. 分析任务复杂度
  2. 预估token消耗
  3. 告知用户预计时间
output: "预计消耗X token，约Y分钟"
```

**任务: auto-perf-003 异步处理**
```yaml
trigger: task_type == "background"
action:
  1. 提交到后台队列
  2. 立即返回任务ID
  3. 完成后通知用户
examples: [evo任务, 长时间搜索, 批量处理]
```

### 实施文件
- `.claw-status/auto/streaming_output.py`
- `.claw-status/async_task_queue.py`

---

## 问题4: 记忆检索不准

### 症状
- Semantic search召回不相关
- 缺少用户反馈循环
- 无自学习能力

### 自动优化方案

**任务: auto-retrieval-001 混合检索**
```yaml
trigger: every_memory_search
action:
  1. 关键词检索 (BM25)
  2. 语义检索 (embedding)
  3. 时间衰减加权
  4. RRF融合排序
formula: score = 0.4*BM25 + 0.4*semantic + 0.2*recency
```

**任务: auto-retrieval-002 反馈学习**
```yaml
trigger: user_clicks_result OR user_ignores_result
action:
  1. 记录点击/忽略行为
  2. 更新query-doc相关性矩阵
  3. 微调embedding权重
threshold: 收集100条反馈后更新模型
```

**任务: auto-retrieval-003 负样本挖掘**
```yaml
trigger: daily
action:
  1. 分析被忽略的搜索结果
  2. 构建负样本对
  3. 对比学习微调
```

### 实施文件
- `.claw-status/auto/hybrid_retrieval.py`
- `.claw-status/auto/feedback_learner.py`

---

## 问题5: 缺乏自我监控

### 症状
- 不知道自己表现如何
- 无A/B测试框架
- 异常行为无检测

### 自动优化方案

**任务: auto-metrics-001 实时指标收集**
```yaml
trigger: every_response
metrics:
  - response_time_ms
  - token_usage
  - context_utilization
  - user_satisfaction (implicit)
  - task_success_rate
storage: .claw-status/metrics/daily_{date}.jsonl
```

**任务: auto-metrics-002 A/B测试框架**
```yaml
trigger: new_strategy_deployed
action:
  1. 50%流量使用新策略
  2. 50%使用旧策略(control)
  3. 收集对比指标
  4. 统计显著性检验
duration: 7 days or 100 samples
```

**任务: auto-metrics-003 异常检测**
```yaml
trigger: every_hour
action:
  1. 计算指标z-score
  2. 检测异常波动 (>3σ)
  3. 自动报警并降级
alert_channel: log + user_notify
```

### 实施文件
- `.claw-status/auto/metrics_collector.py`
- `.claw-status/auto/ab_testing.py`
- `.claw-status/auto/anomaly_detector.py`

---

## 自动执行配置

### 添加到SEIS

```python
# seis_engine.py 新增任务
self_optimization_tasks = [
    {"id": "auto-ctx", "freq": "every_10_rounds", "priority": "P1"},
    {"id": "auto-state", "freq": "every_30min", "priority": "P1"},
    {"id": "auto-perf", "freq": "every_response", "priority": "P0"},
    {"id": "auto-retrieval", "freq": "every_search", "priority": "P1"},
    {"id": "auto-metrics", "freq": "every_response", "priority": "P0"},
]
```

### 定时任务

```bash
# 添加到crontab
*/5 * * * * cd /root/.openclaw/workspace && python3 .claw-status/auto/metrics_collector.py --flush
0 23 * * * cd /root/.openclaw/workspace && python3 .claw-status/auto/memory_migrator.py
0 */6 * * * cd /root/.openclaw/workspace && python3 .claw-status/auto/anomaly_detector.py
```

---

## 优先级排序

| 优先级 | 任务 | 影响 | 难度 |
|--------|------|------|------|
| P0 | auto-perf-001 流式输出 | 用户体验 | 中 |
| P0 | auto-metrics-001 指标收集 | 可观测性 | 低 |
| P1 | auto-ctx-001 对话摘要 | 上下文效率 | 中 |
| P1 | auto-retrieval-001 混合检索 | 召回质量 | 中 |
| P2 | auto-state-001 会话快照 | 启动速度 | 低 |
| P2 | auto-metrics-002 A/B测试 | 策略优化 | 高 |

---

## 实施路线图

### 本周 (v3.7.1)
- [ ] auto-metrics-001 实时指标
- [ ] auto-perf-002 Token预估
- [ ] auto-ctx-001 对话摘要基础版

### 下周 (v3.7.2)
- [ ] auto-perf-001 流式输出
- [ ] auto-retrieval-001 混合检索
- [ ] auto-state-001 会话快照

### 持续 (v3.8)
- [ ] auto-metrics-002 A/B测试
- [ ] auto-retrieval-002 反馈学习
- [ ] 所有任务的自动化集成

---

## 验收标准

- [ ] 响应时间P95 < 1s
- [ ] 上下文利用率 > 80%
- [ ] 记忆召回准确率 > 85%
- [ ] 冷启动时间 < 3s
- [ ] 有完整的指标看板

---

*计划版本: 1.0*  
*创建时间: 2026-03-19*  
*预计完成: v3.8 (2周后)*
