# Method Fingerprint System - 使用指南

> **解决"成功案例没有被固化"的问题**

## 核心概念

**方法指纹** = 特定任务 + 工具组合 + 参数模式的唯一标识

**系统功能**:
- ✅ 自动记录成功的执行路径
- ✅ 自动标记失败的执行路径（黑名单）
- ✅ 执行前自动查找历史案例
- ✅ 复用成功率>80%的方法

---

## 文件结构

```
.claw-status/
├── method_fingerprints.json    # 指纹数据库
├── method_fingerprint.py       # 核心模块
├── fingerprint_hooks.py        # 工具钩子
└── init_fingerprint.py         # 自动初始化脚本
```

---

## 自动触发（已集成）

**每次会话开始时自动执行**:
```python
python3 .claw-status/init_fingerprint.py
```

输出示例：
```
✅ Method Fingerprint System 已激活

📊 Method Fingerprint System Report
==================================================
Total task types: 3
Success patterns: 3
Blacklisted methods: 2

Active Success Patterns:
  ✓ send_feishu_image: 100% success, 1 executions
  ✓ pptx_generate: 100% success, 1 executions
  ✓ convert_ppt_to_image: 100% success, 2 executions

Blacklisted Methods (avoid):
  ✗ send_feishu_image: Cross-context messaging denied
  ✗ pptx_generate: token_overuse
```

---

## 手动使用

### 查看当前指纹状态
```bash
python3 .claw-status/method_fingerprint.py
```

### 在代码中使用
```python
from fingerprint_hooks import check_before_execute, record_execution

# 1. 执行前检查
task_type = "send_feishu_image"
proposed_method = {
    "tool": "message",
    "action": "send",
    "channel": "feishu"
}

result = check_before_execute(task_type, proposed_method)
# 返回: {"action": "reuse"} | {"action": "block"} | {"action": "proceed"}

# 2. 执行后记录
record_execution(
    task_type=task_type,
    method=proposed_method,
    result={"success": True, "error": None},
    tokens=25000
)
```

---

## 工作原理

### 执行前检查流程
```
用户发起任务
    ↓
推断任务类型 (task_type)
    ↓
检查黑名单 → 如果匹配 → 阻止执行 + 建议替代方案
    ↓
查找成功案例 → 如果成功率>80% → 建议复用参数
    ↓
没有匹配 → 允许新尝试
    ↓
执行工具调用
    ↓
记录执行结果 → 更新指纹数据库
```

### 黑名单机制
- 失败2次 → 标记为 `blacklisted`
- 再次尝试相同方法 → 自动阻止

### 成功复用机制
- 成功率 > 80% → 自动建议参数
- 记录平均Token消耗 → 预估成本

---

## 已记录的指纹（示例）

### ✅ 成功案例
| 任务类型 | 成功方法 | 置信度 |
|---------|---------|--------|
| send_feishu_image | cron + isolated + 简短消息 | 100% |
| pptx_generate | node + 单版本生成 | 100% |
| convert_ppt_to_image | libreoffice → pdftoppm | 100% |

### ❌ 黑名单（避免）
| 任务类型 | 失败方法 | 原因 |
|---------|---------|------|
| send_feishu_image | message.send() | Cross-context denied |
| pptx_generate | 多版本生成 | Token浪费 |

---

## 下次遇到相似任务

**场景**: 用户要求"把图片发到飞书"

**系统自动处理**:
1. 匹配任务类型: `send_feishu_image`
2. 检查黑名单 → 阻止 `message.send`
3. 查找成功案例 → 建议 `cron + 简短消息`
4. 直接复用成功参数
5. **避免**: 重试5次失败的方法

**结果**: 节省 475k tokens（¥70-170）

---

## 更新维护

**每次改进后更新**:
- 新增成功案例 → 系统自动记录
- 发现失败模式 → 系统自动标记
- 定期审查 → 淘汰过时指纹

---

## 关键原则

> **"不再从零开始试错，站在过去的成功上执行。"**

- 复杂任务先查指纹库
- 失败两次自动换路
- 成功案例自动复用
- 黑名单永久避开

---

**版本**: v1.0  
**创建**: 2026-03-18  
**状态**: ✅ 已激活
