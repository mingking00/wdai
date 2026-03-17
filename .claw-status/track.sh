#!/bin/bash
# Innovation Tracker CLI - 创新追踪器命令行工具
# 使用方法: ./track.sh [ok|fail|check|status] <tool_name> [error_msg]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="/root/.openclaw/workspace"

cd "$WORKSPACE_DIR"

case "$1" in
    ok)
        # 追踪成功: ./track.sh ok web_search
        if [ -z "$2" ]; then
            echo "Usage: ./track.sh ok <tool_name>"
            exit 1
        fi
        python3 -c "
import sys
sys.path.insert(0, '.claw-status')
from innovation_tracker import ok
result = ok('$2')
print(result['message'])
"
        ;;
    fail)
        # 追踪失败: ./track.sh fail web_search "timeout"
        if [ -z "$2" ]; then
            echo "Usage: ./track.sh fail <tool_name> [error_msg]"
            exit 1
        fi
        ERROR="${3:-unknown error}"
        python3 -c "
import sys
sys.path.insert(0, '.claw-status')
from innovation_tracker import fail
result = fail('$2', '$ERROR')
print(result['message'])
if result['locked']:
    print('🚨 强制换路！该方法已锁定！')
    from innovation_tracker import suggest_alternative
    print('建议:', suggest_alternative(result['method']))
"
        ;;
    check)
        # 检查状态: ./track.sh check web_search
        if [ -z "$2" ]; then
            echo "Usage: ./track.sh check <tool_name>"
            exit 1
        fi
        python3 -c "
import sys
sys.path.insert(0, '.claw-status')
from innovation_tracker import check_tool, suggest_alternative
result = check_tool('$2')
print(result['message'])
if not result['can_use']:
    print('建议:', suggest_alternative(result['method']))
"
        ;;
    status|st)
        # 查看所有状态
        python3 .claw-status/innovation_tracker.py
        ;;
    *)
        echo "Innovation Tracker CLI"
        echo ""
        echo "Usage:"
        echo "  ./track.sh ok <tool_name>              # 标记成功"
        echo "  ./track.sh fail <tool_name> [error]    # 标记失败"
        echo "  ./track.sh check <tool_name>           # 检查是否可用"
        echo "  ./track.sh status                      # 查看所有状态"
        echo ""
        echo "Examples:"
        echo "  ./track.sh ok web_search"
        echo "  ./track.sh fail github_api 'timeout'"
        echo "  ./track.sh check web_search"
        echo "  ./track.sh status"
        ;;
esac
