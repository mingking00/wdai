#!/bin/bash
# Install Innovation Tracker Plugin for OpenClaw
# Usage: ./install.sh

set -e

PLUGIN_NAME="innovation-tracker"
PLUGIN_SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查 OpenClaw 是否安装
if ! command -v openclaw &> /dev/null; then
    echo "❌ Error: openclaw command not found"
    echo "Please install OpenClaw first: npm install -g openclaw"
    exit 1
fi

# 获取 OpenClaw 配置目录
OPENCLAW_DIR="${HOME}/.openclaw"
WORKSPACE_DIR="${OPENCLAW_DIR}/workspace"

# 确定安装位置
# 优先安装到工作区，这样可以从工作区加载
if [ -d "${WORKSPACE_DIR}" ]; then
    TARGET_DIR="${WORKSPACE_DIR}/.openclaw/extensions/${PLUGIN_NAME}"
    echo "📦 Installing to workspace: ${TARGET_DIR}"
else
    TARGET_DIR="${OPENCLAW_DIR}/extensions/${PLUGIN_NAME}"
    echo "📦 Installing globally: ${TARGET_DIR}"
fi

# 创建目录
mkdir -p "$(dirname "${TARGET_DIR}")"

# 复制文件
echo "📋 Copying plugin files..."
cp -r "${PLUGIN_SOURCE_DIR}"/* "${TARGET_DIR}/"

# 确保 TypeScript 文件存在
if [ ! -f "${TARGET_DIR}/index.ts" ]; then
    echo "❌ Error: index.ts not found in source directory"
    exit 1
fi

# 检查是否需要构建
echo "🔧 Checking if plugin needs building..."

# 启用插件
echo "⚡ Enabling plugin..."
if openclaw plugins enable "${PLUGIN_NAME}" 2>/dev/null; then
    echo "✅ Plugin enabled successfully"
else
    echo "⚠️  Could not enable plugin automatically"
    echo "   You may need to enable it manually: openclaw plugins enable ${PLUGIN_NAME}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Innovation Tracker Plugin installed!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Restart OpenClaw Gateway:"
echo "     openclaw gateway restart"
echo ""
echo "  2. Or start with verbose mode to see tracker logs:"
echo "     openclaw gateway --verbose"
echo ""
echo "  3. Test by running a tool that will fail 3 times"
echo ""
echo "Configuration:"
echo "  State file: .claw-status/innovation_state.json"
echo "  Max failures before lock: 3"
echo ""
echo "To uninstall:"
echo "  openclaw plugins uninstall ${PLUGIN_NAME}"
echo ""
