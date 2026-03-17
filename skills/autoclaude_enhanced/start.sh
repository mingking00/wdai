#!/bin/bash
# AutoClaude 启动脚本

set -e

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  AutoClaude 冲突解决系统${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 需要 Python 3"
    exit 1
fi

# 创建日志目录
mkdir -p .logs

# 默认模式
MODE="${1:-demo}"

echo "启动模式: $MODE"
echo ""

# 运行
python3 autoclaude_production.py --mode "$MODE"
