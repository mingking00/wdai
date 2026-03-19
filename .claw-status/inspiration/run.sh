#!/bin/bash
# 灵感摄取系统 - 运行脚本
# 由cron调用

WORKSPACE="/root/.openclaw/workspace/.claw-status/inspiration"
LOG_FILE="$WORKSPACE/data/cron.log"
RUN_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建日志目录
mkdir -p "$WORKSPACE/data"

# 写入开始标记
echo "========================================" >> "$LOG_FILE"
echo "🤖 灵感摄取系统启动 - $(date)" >> "$LOG_FILE"
echo "Run ID: $RUN_TIMESTAMP" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 切换到工作目录
cd "$WORKSPACE" || exit 1

# 运行主程序
python3 inspiration_runner.py --mode=auto >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

# 写入结束标记
echo "" >> "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 运行完成 - $(date)" >> "$LOG_FILE"
else
    echo "⚠️ 运行异常 (退出码: $EXIT_CODE) - $(date)" >> "$LOG_FILE"
fi
echo "" >> "$LOG_FILE"

# 保留最近1000行日志
tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"

# 发送通知（可选）
# 如果有新内容，可以在这里调用通知脚本

exit $EXIT_CODE
