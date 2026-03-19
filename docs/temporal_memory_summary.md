# 时态记忆系统 - 实现完成

借鉴 Zep 的时序知识图谱，为 MEMORY.md 系统添加 `valid_until` 字段支持。

---

## 已实现功能

| 功能 | 状态 | 说明 |
|:---|:---:|:---|
| **valid_until 标记** | ✅ | `[valid: 30 days]` / `[valid: permanent]` |
| **置信度标记** | ✅ | `[confidence: high/medium/low]` 或 `[confidence: 0.85]` |
| **来源标记** | ✅ | `[source: 实测/文档/推测]` |
| **验证日期** | ✅ | `[checked: 2026-03-18]` |
| **自动检查工具** | ✅ | 检查有效性和过期状态 |
| **置信度衰减** | ✅ | 随时间自动衰减 |

---

## 文件位置

```
memory/
├── index.md                      # 添加时态记忆入口
└── core/
    └── temporal_facts.md         # 时态事实记忆 (新)

.claw-status/
├── temporal_memory.py            # 核心管理模块 (11KB)
└── update_fact.py                # 命令行工具 (3KB)
```

---

## 使用方式

### 1. 查看时态记忆状态

```bash
python3 .claw-status/temporal_memory.py
```

输出：
```
======================================================================
🕐 时态记忆状态
======================================================================

总事实数: 15
  ✅ 有效: 14
  ⚠️  即将过期: 1
  ❌ 已过期: 0

⚠️  即将过期的事实（7天内）:
  - Claude API 费率 ~$0.03/1K tokens... (6天)
```

### 2. 检查特定事实

```bash
python3 .claw-status/update_fact.py check "Railway"
```

输出：
```
'Railway': ✅ 有效 (剩余 29 天)
```

### 3. 列出即将过期的事实

```bash
python3 .claw-status/update_fact.py expiring 7
```

### 4. 更新验证日期

```bash
python3 .claw-status/update_fact.py verify "Claude API"
```

更新后：
```markdown
- [2026-03-18] Claude API 费率 ~$0.03/1K tokens [valid: 7 days] [confidence: medium] [source: 账单估算] [checked: 2026-03-18]
```

---

## 记忆格式

### 标准格式

```markdown
- [日期] 事实内容 [valid: 有效期] [confidence: 置信度] [source: 来源] [checked: 验证日期]
```

### 示例

```markdown
- [2026-03-18] Railway 部署正常 [valid: 30 days] [confidence: high] [source: 实测] [checked: 2026-03-18]
- [2026-03-18] OpenClaw 版本 v2.1.0 [valid: until next update] [confidence: high] [source: pip freeze]
- [2026-03-18] Claude API 费率 ~$0.03/1K tokens [valid: 7 days] [confidence: medium] [source: 账单估算] [checked: 2026-03-18]
```

### 有效期格式

| 格式 | 示例 | 说明 |
|:---|:---|:---|
| `N days` | `[valid: 30 days]` | N 天后过期 |
| `N months` | `[valid: 3 months]` | N 个月后过期 |
| `permanent` | `[valid: permanent]` | 永久有效 |
| `until next update` | `[valid: until next update]` | 直到下次更新 |

### 置信度格式

| 格式 | 示例 | 数值 |
|:---|:---|:---:|
| 等级 | `[confidence: high]` | 0.9 |
| 等级 | `[confidence: medium]` | 0.7 |
| 等级 | `[confidence: low]` | 0.5 |
| 数值 | `[confidence: 0.85]` | 0.85 |

---

## 置信度衰减公式

```
事实创建: confidence = 1.0
每过 valid 期的 10%: confidence *= 0.95
超过 valid 期: confidence = 0.0 (标记为过期)

示例:
  有效期 30 天，初始置信度 0.9
  第 3 天: 0.9 * 0.95 = 0.855
  第 6 天: 0.855 * 0.95 = 0.812
  第 30 天: 0.9 * (0.95^10) = 0.54
```

---

## 当前时态事实

### 工具与环境
- Railway 部署正常 [valid: 30 days] [confidence: high]
- Claude API 费率 ~$0.03/1K [valid: 7 days] [confidence: medium]
- Python 3.12 [valid: permanent] [confidence: high]

### 性能基准
- Fast Check 延迟 ~0.1ms [valid: 30 days] [confidence: high]
- Hybrid Verification 平均 25ms [valid: 30 days] [confidence: high]

### 临时决策
- `github_api` 锁定 [valid: until 3 successes] [confidence: high]

---

## 与 Zep 的对比

| 特性 | Zep | 我的实现 |
|:---|:---|:---|
| **时序知识图谱** | 完整的图结构 | Markdown 列表 |
| **自动过期检测** | ✅ 自动 | ✅ 工具检查 |
| **置信度衰减** | ✅ 自动计算 | ✅ 查询时计算 |
| **自动更新** | ✅ 系统集成 | ❌ 手动更新 |
| **适用场景** | 多用户生产环境 | 单用户个人空间 |

**核心借鉴**：
- ✅ `valid_until` 时间有效性标记
- ✅ `confidence` 置信度标记
- ✅ `source` 来源追踪
- ✅ 定期验证机制

---

## 维护建议

### 每周检查
```bash
# 检查即将过期的事实
python3 .claw-status/update_fact.py expiring 7

# 验证并更新
python3 .claw-status/update_fact.py verify "Claude API"
```

### 添加新事实
```markdown
- [YYYY-MM-DD] 事实描述 [valid: 30 days] [confidence: high] [source: 实测]
```

---

## 集成到记忆系统

在 `memory/index.md` 中添加：
- 标签: `#knowledge/temporal`
- 场景: 验证信息时效性时
- 快速导航: 使用外部 API/工具时

---

*实现时间: 2026-03-18*  
*借鉴: Zep 时序知识图谱*  
*状态: ✅ 可用*
