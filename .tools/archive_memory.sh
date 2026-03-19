#!/bin/bash
# 记忆归档脚本
# 手动触发记忆归档任务

echo "🗄️  运行记忆自动归档..."
cd /root/.openclaw/workspace
python3 .tools/memory_archiver.py
