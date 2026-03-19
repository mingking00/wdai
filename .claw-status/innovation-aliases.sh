#!/bin/bash
# OpenClaw 创新能力快捷命令
# 让常用操作自动具备创新能力

WORKSPACE="/root/.openclaw/workspace"
CLAW="$WORKSPACE/.claw-status"

# 智能git推送
function git-push-smart() {
    python3 "$CLAW/oci_agent.py" git-push
}

# 智能执行
function iexec() {
    python3 -c "
import sys
sys.path.insert(0, '$CLAW')
from auto_innovation import iexec
result = iexec('$1')
print(result['result']['stdout'] if result['success'] else result['error'])
"
}

# 查看创新统计
function innovation-stats() {
    python3 "$CLAW/oci_agent.py" stats
}

# 生成创新报告
function innovation-report() {
    python3 "$CLAW/oci_agent.py" report
}

# 导出到环境
export -f git-push-smart
export -f iexec
export -f innovation-stats
export -f innovation-report

echo "✅ 创新能力快捷命令已加载"
echo ""
echo "可用命令:"
echo "  git-push-smart     - 智能git推送(自动HTTPS→SSH)"
echo "  iexec <command>    - 智能执行(自动换路)"
echo "  innovation-stats   - 查看创新统计"
echo "  innovation-report  - 生成创新报告"
