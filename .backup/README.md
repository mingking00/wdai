# wdai 自动备份系统

## 概述

wdai系统配置了自动每日备份到GitHub。

## 备份配置

| 项目 | 详情 |
|:---|:---|
| **备份频率** | 每天凌晨 2:00 (Asia/Shanghai) |
| **备份方式** | Git自动提交+推送 |
| **目标仓库** | https://github.com/mingking00/wdai |
| **Cron任务ID** | `25ef3eb4-4aeb-4c3f-a833-17a6464dc45a` |

## 备份内容

自动备份以下更改：
- 记忆文件更新 (`memory/daily/`, `memory/core/`)
- 系统状态更改 (`.claw-status/`, `.state/`)
- 新提案和审批记录 (`.evolution/`)
- 学习任务和洞察 (`.learning/`)
- 任何其他工作空间更改

## 手动触发备份

```bash
# 运行备份脚本
/root/.openclaw/workspace/.backup/daily_backup.sh
```

## 查看备份日志

```bash
# 查看最新备份日志
tail -20 /root/.openclaw/workspace/.backup/backup.log
```

## 管理Cron任务

```bash
# 查看所有cron任务
openclaw cron list

# 禁用每日备份
openclaw cron disable wdai-daily-backup

# 启用每日备份
openclaw cron enable wdai-daily-backup

# 删除备份任务
openclaw cron remove wdai-daily-backup
```

## 备份流程

1. **检查更改**: 检测是否有新文件或修改
2. **自动提交**: 如果有更改，自动创建提交
3. **推送到GitHub**: 推送到远程仓库
4. **记录日志**: 记录备份结果到日志文件
5. **更新记忆**: 在每日记录中标记备份完成

## 首次设置

如果GitHub Token失效，需要重新配置：

```bash
cd /root/.openclaw/workspace

# 更新remote URL（使用新Token）
git remote set-url origin https://USERNAME:TOKEN@github.com/mingking00/wdai.git

# 测试推送
git push

# 恢复干净URL（Token只保存在本地）
git remote set-url origin https://github.com/mingking00/wdai.git
```

## 故障排除

### 推送失败

如果自动备份推送失败：

1. 检查网络连接
2. 验证GitHub Token是否有效
3. 查看备份日志: `cat .backup/backup.log`
4. 手动尝试推送: `git push origin master`

### 权限问题

如果遇到权限错误，可能需要更新Token：

1. 生成新Token: https://github.com/settings/tokens
2. 确保有 `repo` 权限
3. 更新remote URL（见上文）

## 安全说明

- Token仅在推送时使用，不会保存在代码中
- 推送后自动恢复干净的remote URL
- 备份脚本只提交必要的文件（已配置.gitignore）
- 大文件（如.vectordb）已排除在备份外

## 备份历史

备份记录可在以下位置查看：
- GitHub仓库: https://github.com/mingking00/wdai/commits/master
- 本地日志: `.backup/backup.log`
- 每日记忆: `memory/daily/YYYY-MM-DD.md`
