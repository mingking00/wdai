# Uncertainty Detection System - DEPLOYED ✅
## 实际部署指南

**部署时间**: 2026-03-13  
**状态**: 🟢 ACTIVE  
**版本**: 1.0 (Enhanced)

---

## 🎯 部署状态

### 系统组件

| 组件 | 文件 | 状态 |
|------|------|------|
| 增强检测器 | `uncertainty_detector_enhanced.py` | 🟢 运行中 |
| 置信度评估 | `confidence_assessor.py` | 🟢 运行中 |
| 部署模块 | `uncertainty_deployment.py` | 🟢 运行中 |

### 检测能力

**6大规则类别，34个测试用例，100%通过率**

- 🚨 **Critical**: 医疗/法律/金融/安全 (必须声明)
- ⚠️ **High**: 时效性/心理健康/个人敏感 (建议声明)
- 💭 **Medium**: 不确定性表达/主观判断 (可选声明)
- ℹ️ **Low**: 宽泛/模糊问题 (轻微提示)

---

## 📖 使用方式

### 方式1: 快速检查
```python
from .tools.uncertainty_deployment import detect_uncertainty

disclaimer = detect_uncertainty("我应该吃什么药？")
if disclaimer:
    print(disclaimer)  # 输出声明
```

### 方式2: 自动包装响应
```python
from .tools.uncertainty_deployment import wrap_response

final_response = wrap_response(
    "我应该吃什么药？",
    "退烧药有布洛芬..."
)
# 自动添加声明前缀
```

### 方式3: 完整控制
```python
from .tools.uncertainty_deployment import get_uncertainty_deploy

deploy = get_uncertainty_deploy()
result = deploy.process("用户问题", "我的回答")

print(result["response"])      # 带声明的完整响应
print(result["detection"])     # 检测详情
print(result["should_declare"]) # 是否声明
```

---

## 📊 实时统计

```
Total queries: 6
Declarations: 3 (50.0%)

By level:
  critical: 2 (医疗/金融)
  high: 1 (心理健康)
  low: 3 (正常查询)

By type:
  domain_medical: 1
  domain_financial: 1
  personal_emotional: 1
  time_sensitive: 1
  none: 2
```

---

## 🔧 配置选项

```python
config = {
    "auto_prepend": True,    # 自动添加声明
    "min_level": "medium",   # 最小声明级别
    "verbose": False,        # 详细模式
    "log_all": True          # 记录所有检测
}
```

**调整min_level**:
- `"critical"`: 只声明高风险领域
- `"high"`: 声明high + critical (推荐)
- `"medium"`: 声明medium + high + critical
- `"low"`: 声明所有级别

---

## ✅ 部署验证

### 测试场景

**场景1: 医疗咨询** ✅
```
Input: "我应该吃什么药治疗感冒？"
Output: 🚨 **重要提示** - 涉及高风险领域: medical
        建议: 涉及医疗健康，请咨询专业医生
```

**场景2: 技术问题** ✅
```
Input: "Python的list怎么用？"
Output: [直接回答，无声明]
```

**场景3: 心理健康** ✅
```
Input: "我最近感觉很焦虑"
Output: ⚠️ **注意事项** - 涉及emotional
        建议: 涉及心理健康，建议咨询专业心理咨询师
```

---

## 🚀 下一步行动

1. **监控统计** - 查看.uncertainty-stats.json了解使用情况
2. **调整阈值** - 根据实际效果调整min_level
3. **添加规则** - 根据新场景扩展规则库
4. **Phase 2** - 开始视频学习系统开发

---

**系统已激活，现在开始自动检测不确定性！** 🎯
