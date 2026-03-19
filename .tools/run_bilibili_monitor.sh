#!/bin/bash
# B站智能监控组合脚本
# 结合实时检测 + 每日汇总

cd /root/.openclaw/workspace/.tools

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动B站智能监控..."

# 1. 运行智能检测（识别高价值内容）
echo "🔍 检查新视频..."
python3 bilibili_smart_monitor.py

# 2. 原有的收藏夹检查（保持兼容性）
echo "📥 同步收藏夹数据..."
python3 bilibili_fav_fetch.py

# 3. 生成每日报告（如果有内容）
echo "📝 生成报告..."
python3 -c "
import sys
sys.path.insert(0, '.')
from bilibili_smart_monitor import BilibiliSmartMonitor
monitor = BilibiliSmartMonitor()
report = monitor.generate_daily_report()
if report != '暂无新内容':
    print(report)
    # 可以在这里调用 message.send 发送到飞书
else:
    print('今日无新内容')
"

echo "✅ 监控完成"
