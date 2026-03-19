#!/bin/bash
# 灵感摄取系统 - 生成详细报告

WORKSPACE="/root/.openclaw/workspace/.claw-status/inspiration"

echo "=========================================="
echo "📊 生成灵感摄取系统报告..."
echo "=========================================="
echo ""

cd "$WORKSPACE"

# 生成报告
python3 inspiration_runner.py --mode=report 2>&1

echo ""
echo "✅ 报告已生成"

# 显示报告位置
LATEST_REPORT=$(ls -t data/system_report_*.md 2>/dev/null | head -1)
if [ -n "$LATEST_REPORT" ]; then
    echo "📄 报告文件: $LATEST_REPORT"
    echo ""
    echo "报告预览:"
    cat "$LATEST_REPORT" | head -50
fi
