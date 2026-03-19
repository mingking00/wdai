#!/bin/bash
# AI过载保护执行包装器

cd /root/.openclaw/workspace/.scheduler

TASK_TYPE=$1
PARAMS=${2:-"{}"}

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 提交任务: $TASK_TYPE"

# 添加任务到队列
python3 executor_queue.py add "$TASK_TYPE" "$PARAMS"

# 立即尝试处理（非阻塞）
# 如果AI过载，任务会留在队列等待下次重试
python3 executor_queue.py process &

echo "✅ 任务已提交到队列，后台处理中"
