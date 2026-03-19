# 🕐 时态事实记忆 (Temporal Facts)

> 借鉴 Zep 的时序知识图谱，为记忆添加时间维度

---

## 概述

时态记忆解决什么问题：
- 信息会过期（API 费率、工具版本、部署状态）
- 需要追踪有效期限（临时决策、实验性方案）
- 置信度随时间衰减（基于旧数据的学习）

---

## 记忆格式

### 标准格式

```markdown
- [日期] 事实内容 [valid: 有效期] [confidence: 置信度] [source: 来源]
```

### 字段说明

| 字段 | 格式 | 示例 | 说明 |
|:---|:---|:---|:---|
| `valid` | `YYYY-MM-DD` / `N days` / `N months` / `permanent` | `30 days` | 有效期 |
| `confidence` | `0.0-1.0` / `high` `medium` `low` | `0.85` | 置信度 |
| `source` | 任意文本 | `实测` `文档` `推测` | 信息来源 |
| `checked` | `YYYY-MM-DD` | `2026-03-18` | 最后验证日期 |

---

## 当前时态事实

### 🔧 工具与环境

#### 部署状态
- [2026-03-18] Railway 部署正常 [valid: 30 days] [confidence: high] [source: 实测] [checked: 2026-03-18]
- [2026-03-18] OpenClaw 版本 v2.1.0 [valid: until next update] [confidence: high] [source: pip freeze]

#### API 与模型
- [2026-03-18] Claude API 费率 ~$0.03/1K tokens [valid: 7 days] [confidence: medium] [source: 账单估算] [checked: 2026-03-18]
- [2026-03-18] kimi-coding/k2p5 可用 [valid: 30 days] [confidence: high] [source: 实测]

#### 开发环境
- [2026-03-18] Python 3.12 [valid: permanent] [confidence: high] [source: system]
- [2026-03-18] Node.js v22 [valid: permanent] [confidence: high] [source: system]

### 📊 性能基准

#### Hybrid Verification v4.0
- [2026-03-18] Fast Check 延迟 ~0.1ms [valid: 30 days] [confidence: high] [source: 实测] [checked: 2026-03-18]
- [2026-03-18] Slow Check 延迟 ~100ms [valid: 30 days] [confidence: high] [source: 实测]
- [2026-03-18] 平均验证延迟 25ms [valid: 30 days] [confidence: high] [source: benchmark]

### 🧪 实验性方案

#### Attention Residuals 集成
- [2026-03-18] Block AttnRes 复杂度 O(Nd) [valid: 90 days] [confidence: high] [source: 论文]
- [2026-03-18] 零初始化策略稳定 [valid: 30 days] [confidence: medium] [source: 本地测试]

### 🎯 临时决策

#### 当前锁定方法
- [2026-03-18] `github_api` 锁定，强制使用 git CLI [valid: until 3 successes] [confidence: high] [source: 原则执行系统]

---

## 已过期事实（归档）

<details>
<summary>点击查看已过期事实</summary>

*暂无过期记录 - 首次使用时创建*

</details>

---

## 使用指南

### 添加新事实

```markdown
- [YYYY-MM-DD] 事实描述 [valid: 有效期] [confidence: 置信度] [source: 来源]
```

### 检查事实有效性

```python
from temporal_memory import check_fact_validity

is_valid, days_remaining = check_fact_validity("Railway 部署正常")
# 返回: (True, 28)  # 还有28天有效期
```

### 更新验证日期

```markdown
<!-- 更新前 -->
- [2026-03-18] Railway 部署正常 [valid: 30 days] ...

<!-- 更新后 -->
- [2026-03-18] Railway 部署正常 [valid: 30 days] [checked: 2026-03-20]
```

### 标记为过期

```markdown
<!-- 将事实移动到"已过期事实"区域 -->
- [2026-03-18] 某项费率 $0.05/1K [valid: EXPIRED] [confidence: N/A] [note: 已涨价至 $0.08]
```

---

## 维护规则

### 自动检查清单

每周检查一次：
- [ ] 即将过期（7天内）的事实
- [ ] 需要重新验证的事实
- [ ] 可以归档的过期事实

### 置信度衰减

```
事实创建: confidence = 1.0
每过 valid 期的 10%: confidence *= 0.95
超过 valid 期: confidence = 0.0 (标记为过期)
```

### 来源可信度

| 来源 | 基础置信度 | 衰减速度 |
|:---|:---:|:---|
| 实测 | 0.9 | 慢 |
| 官方文档 | 0.85 | 慢 |
| 社区反馈 | 0.7 | 中 |
| 个人推测 | 0.5 | 快 |

---

## 与 Zep 的对比

| 特性 | Zep | 我的实现 |
|:---|:---|:---|
| **时序知识图谱** | 完整的图结构 | Markdown 列表 |
| **自动过期检测** | 自动失效旧事实 | 需手动检查 |
| **置信度衰减** | 自动计算 | 手动维护 |
| **适用场景** | 多用户生产环境 | 单用户个人空间 |

**核心借鉴**：
- ✅ 时间有效性标记 (`valid_until`)
- ✅ 置信度标记
- ✅ 来源追踪
- ✅ 定期验证机制

---

## 相关工具

- `.claw-status/check_temporal_facts.py` - 自动检查事实有效性
- `.claw-status/update_fact.py` - 更新事实验证日期

---

*借鉴 Zep 的时序知识图谱思想，但保持轻量级实现*
