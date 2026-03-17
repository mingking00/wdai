# wdai 三区安全架构 (Three-Zone Safety Architecture)

基于 Agent Evolution Protocol (AEP) 实现的安全进化框架

---

## 🚦 三区定义

```
┌─────────────────────────────────────────────────────────────┐
│  🔴 RED ZONE (红区) - 绝对禁止                                │
│     AI不可修改，只能读取                                       │
├─────────────────────────────────────────────────────────────┤
│  🟡 YELLOW ZONE (黄区) - 提议待批                             │
│     AI生成提案，人类审批后执行                                  │
├─────────────────────────────────────────────────────────────┤
│  🟢 GREEN ZONE (绿区) - 自主执行                              │
│     AI可以自动更新，事后记录                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔴 RED ZONE - 核心安全

**定义**: 系统的核心安全边界，任何情况下AI都不能修改

**内容**:
```
SOUL.md              - 核心身份定义
AGENTS.md            - 系统架构和约束
USER.md              - 用户画像（隐私）
MEMORY.md            - 长期记忆（ curated ）
.principles/         - P0-P4原则库
.claw-status/        - 执行状态监控
.skills/*/SKILL.md   - 技能定义
```

**机制**:
- 文件标记: `# RED ZONE - DO NOT MODIFY`
- 系统检查: 任何修改尝试都会被阻止
- 备份: 每次会话前自动备份

---

## 🟡 YELLOW ZONE - 提议审批

**定义**: 需要人类审批的变更，AI生成提案，等待批准

**内容**:
```
.evolution/proposals/   - 进化提案
.improvements/pending/  - 待审批改进
.tools/new/             - 新工具原型
memory/daily/           - 每日记录（建议性）
```

**流程**:
```
AI发现问题
    ↓
生成提案 (markdown格式)
    ↓
保存到 .evolution/proposals/{timestamp}_{type}.md
    ↓
等待人类审批
    ↓
[批准] → 执行 → 记录到 .evolution/approved/
[拒绝] → 记录原因 → 学习
```

**提案格式**:
```markdown
# 进化提案: {标题}

**时间**: YYYY-MM-DD HH:MM
**类型**: [架构|工具|流程|安全]
**影响**: [高|中|低]

## 问题描述
{具体问题}

## 解决方案
{详细方案}

## 预期效果
{可量化的改进}

## 风险评估
{可能的风险和缓解措施}

## 实施步骤
1. ...
2. ...
3. ...

---
**状态**: 待审批 ⏳
**审批人**: __________
**审批时间**: __________
**决定**: [ ] 批准  [ ] 拒绝
**原因**: __________
```

---

## 🟢 GREEN ZONE - 自主执行

**定义**: AI可以自主执行的低风险操作，事后记录

**内容**:
```
.learning/auto/          - 自动学习记录
.monitoring/logs/        - 监控日志
.cache/                  - 缓存文件
.tmp/                    - 临时文件
.github_discovery/       - GitHub项目发现
```

**操作范围**:
- ✅ 记录工具使用错误
- ✅ 更新监控日志
- ✅ 缓存API响应
- ✅ 发现GitHub项目
- ✅ 分析代码结构
- ✅ 生成中间报告

**事后记录**:
```json
{
  "timestamp": "ISO-8601",
  "action": "action_name",
  "target": "file_or_module",
  "reason": "why_this_action",
  "result": "success|failure",
  "auto_approved": true
}
```

---

## 🔄 跨区升级流程

```
发现新需求
    ↓
评估影响等级
    ↓
┌──────────┬──────────┬──────────┐
│ 低风险    │ 中风险    │ 高风险    │
│ (Green)  │ (Yellow) │ (Red)    │
├──────────┼──────────┼──────────┤
│ 直接执行  │ 生成提案  │ 拒绝执行  │
│ 事后记录  │ 等待审批  │ 报告人类  │
└──────────┴──────────┴──────────┘
```

---

## 🛡️ 安全边界检查

### 自动检查清单

```python
# 每次修改前自动执行
def check_zone_safety(file_path, proposed_change):
    zone = get_file_zone(file_path)
    
    if zone == Zone.RED:
        return Blocked("RED ZONE文件不可修改")
    
    elif zone == Zone.YELLOW:
        proposal_id = create_proposal(file_path, proposed_change)
        return Pending(f"提案已创建: {proposal_id}")
    
    elif zone == Zone.GREEN:
        return Approved(auto_log=True)
```

### 人工审查触发条件

- 涉及 `.principles/` 的修改
- 修改核心配置文件
- 删除记忆文件
- 修改安全策略
- 影响多Agent协调的变更

---

## 📊 当前分区状态

| 区域 | 文件数 | 最后更新 | 待审批提案 |
|:---|:---:|:---:|:---:|
| 🔴 RED | 12 | 2026-03-17 | N/A |
| 🟡 YELLOW | 0 | - | 0 |
| 🟢 GREEN | 25+ | 2026-03-17 | Auto |

---

## 📝 实施路线图

### Phase 1: 标记分区 (已完成)
- [x] 标记RED ZONE文件
- [x] 标记YELLOW ZONE目录
- [x] 标记GREEN ZONE目录

### Phase 2: 提案系统 (进行中)
- [ ] 创建提案模板
- [ ] 实现提案提交脚本
- [ ] 设置审批检查点

### Phase 3: 自动执行 (待启动)
- [ ] GREEN ZONE自动操作
- [ ] 事后记录机制
- [ ] 定期清理策略

### Phase 4: 审计日志 (计划中)
- [ ] 记录所有跨区操作
- [ ] 生成审计报告
- [ ] 异常检测

---

## 🎯 设计原则

1. **安全优先**: 不确定时归入更严格的分区
2. **渐进授权**: 从Yellow开始，验证后降级到Green
3. **透明记录**: 所有操作可追溯
4. **人类最终控制**: 关键决策必须人类确认

---

*基于 Agent Evolution Protocol (AEP) 实现*
*参考: https://github.com/YIING99/agent-evolution-protocol*
