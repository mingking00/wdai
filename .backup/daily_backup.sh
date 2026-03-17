#!/bin/bash
# wdai 每日自动备份脚本
# 由 cron 任务调用

set -e

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/.backup/backup.log"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建日志目录
mkdir -p "$WORKSPACE/.backup"

echo "[$DATE] 开始每日备份..." >> "$LOG_FILE"

cd "$WORKSPACE"

# 检查是否有更改
if [ -z "$(git status --porcelain)" ]; then
    echo "[$DATE] 没有新更改，跳过备份" >> "$LOG_FILE"
    exit 0
fi

# 添加所有更改
git add -A

# 提交
COMMIT_MSG="Daily backup - $DATE

自动备份wdai系统状态
- 记忆更新
- 系统状态
- 学习记录"

git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1 || {
    echo "[$DATE] 提交失败或无更改" >> "$LOG_FILE"
    exit 0
}

# 推送到GitHub
git push origin master >> "$LOG_FILE" 2>&1 || {
    echo "[$DATE] 推送失败" >> "$LOG_FILE"
    exit 1
}

echo "[$DATE] 备份完成 ✅" >> "$LOG_FILE"

# 记录到memory
DAILY_FILE="$WORKSPACE/memory/daily/$(date +%Y-%m-%d).md"
if [ -f "$DAILY_FILE" ]; then
    echo "" >> "$DAILY_FILE"
    echo "---" >> "$DAILY_FILE"
    echo "" >> "$DAILY_FILE"
    echo "## 🔄 自动备份" >> "$DAILY_FILE"
    echo "" >> "$DAILY_FILE"
    echo "**时间**: $(date '+%Y-%m-%d %H:%M')" >> "$DAILY_FILE"
    echo "" >> "$DAILY_FILE"
    echo "- ✅ GitHub备份完成" >> "$DAILY_FILE"
    echo "- 仓库: https://github.com/mingking00/wdai" >> "$DAILY_FILE"
fi
