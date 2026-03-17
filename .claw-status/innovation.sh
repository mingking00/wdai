#!/bin/bash
# 创新机制管理脚本
# 绕过 Python 直接操作状态文件

echo "=== Innovation Tracker 管理工具 ==="
echo ""

# 状态文件位置
STATE_FILES=(
    "/root/.openclaw/.claw-status/innovation_state.json"
    "/root/.openclaw/workspace/.claw-status/innovation_state.json"
)

# 显示状态
show_status() {
    for file in "${STATE_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo "📁 $file"
            if [ -s "$file" ]; then
                cat "$file" | python3 -m json.tool 2>/dev/null || cat "$file"
            else
                echo "   (空文件)"
            fi
            echo ""
        fi
    done
}

# 解锁所有方法
unlock_all() {
    for file in "${STATE_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo '{}' > "$file"
            echo "✅ 已清空: $file"
        fi
    done
    echo ""
    echo "📝 提示: 如果插件仍在运行，可能需要重启 OpenClaw Gateway"
}

# 主逻辑
case "$1" in
    status)
        show_status
        ;;
    unlock)
        unlock_all
        ;;
    *)
        echo "用法:"
        echo "  $0 status    # 查看状态"
        echo "  $0 unlock    # 解锁所有方法"
        ;;
esac
