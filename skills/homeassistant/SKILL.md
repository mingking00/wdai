---
name: homeassistant
description: 控制Home Assistant智能家居设备，执行自动化任务
version: 1.0.0
author: Smart Home Assistant
license: MIT
allowed-tools: Bash(curl:*) Read Write exec
---

# Home Assistant 智能家居控制

## 功能概述

通过OpenClaw控制Home Assistant管理的所有智能设备，支持：
- 灯光、开关、插座控制
- 空调、温控器调节
- 窗帘、门锁操作
- 场景和自动化触发
- 传感器数据查询
- 历史数据分析

## 适用场景

当用户提到以下需求时激活：
- "打开/关闭灯"
- "设置温度"
- "执行场景"
- "查询传感器"
- "运行自动化"
- "查看设备状态"

## 配置要求

需要设置以下环境变量：
```bash
export HA_URL="http://homeassistant.local:8123"
export HA_TOKEN="你的长访问令牌"
```

获取Token：
1. 进入Home Assistant → 用户资料 → 长期访问令牌
2. 创建新令牌，复制保存

## API 使用模式

### 获取设备状态
```bash
curl -H "Authorization: Bearer $HA_TOKEN" \
  "$HA_URL/api/states/light.living_room"
```

### 控制设备（开灯）
```bash
curl -X POST \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "light.living_room"}' \
  "$HA_URL/api/services/light/turn_on"
```

### 调用场景
```bash
curl -X POST \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "scene.bedtime"}' \
  "$HA_URL/api/services/scene/turn_on"
```

### 获取所有设备列表
```bash
curl -H "Authorization: Bearer $HA_TOKEN" \
  "$HA_URL/api/states" | jq '.[] | select(.entity_id | startswith("light.")) | {entity_id: .entity_id, state: .state}'
```

## 工作流程

### 1. 解析用户指令
识别意图：
- 控制意图："开灯"、"关空调"
- 查询意图："温度多少"、"灯开着吗"
- 场景意图："晚安模式"、"离家场景"

### 2. 查找设备实体ID
- 使用记忆缓存常用设备映射
- 模糊匹配设备名称
- 必要时询问用户确认

### 3. 执行操作
- 构建正确的服务调用
- 发送API请求
- 验证执行结果

### 4. 反馈结果
- 报告成功/失败
- 提供当前状态
- 建议下一步操作

## 安全建议

- Token只保存在环境变量或加密配置中
- 不要记录敏感设备操作日志
- 高风险操作（门锁）需要二次确认
- 定期检查设备访问日志

## 示例对话

用户: "打开客厅灯"
→ 识别: light.living_room → turn_on → "客厅灯已打开"

用户: "设置空调26度"
→ 识别: climate.bedroom → set_temperature 26 → "卧室空调已设置为26°C"

用户: "执行晚安场景"
→ 识别: scene.bedtime → turn_on → "晚安场景已启动：关闭所有灯，设置空调睡眠模式"

用户: "查看所有开着灯"
→ 查询所有 light.* 状态为 on → "客厅灯、厨房灯当前开着"
