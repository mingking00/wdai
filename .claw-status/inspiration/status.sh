#!/bin/bash
# 灵感摄取系统 - 快速状态查看

WORKSPACE="/root/.openclaw/workspace/.claw-status/inspiration"

echo "=========================================="
echo "🤖 灵感摄取系统 - 快速状态"
echo "=========================================="
echo ""

# 查看最新报告
if [ -f "$WORKSPACE/data/system_report_*.md" ]; then
    LATEST_REPORT=$(ls -t $WORKSPACE/data/system_report_*.md 2>/dev/null | head -1)
    if [ -n "$LATEST_REPORT" ]; then
        echo "📊 最新报告:"
        head -30 "$LATEST_REPORT"
        echo ""
    fi
fi

# 查看运行日志
echo "📋 最近5次运行:"
if [ -f "$WORKSPACE/data/cron.log" ]; then
    tail -50 "$WORKSPACE/data/cron.log" | grep -E "(启动|完成|异常|✅|⚠️)" | tail -10
else
    echo "   暂无运行日志"
fi

echo ""

# 查看数据目录
echo "📁 数据文件:"
ls -lh "$WORKSPACE/data/" 2>/dev/null | tail -10

echo ""
echo "=========================================="
echo "💡 常用命令:"
echo "   ./run.sh           # 手动运行"
echo "   ./status.sh        # 查看状态"
echo "   ./report.sh        # 生成详细报告"
echo "=========================================="
