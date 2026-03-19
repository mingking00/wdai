#!/bin/bash

echo "=================================="
echo "  Vibero Reader - Startup Script"
echo "=================================="
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")"

echo "Working directory: $(pwd)"
echo ""

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python not found!"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "✅ Found Python: $($PYTHON_CMD --version)"
echo ""

# 检查 app.py
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found in: $(pwd)"
    echo "Please run this script from the backend folder."
    exit 1
fi

echo "✅ Found app.py"
echo "✅ Found templates/index.html"
echo ""

# 安装依赖
echo "📦 Checking dependencies..."
$PYTHON_CMD -m pip install -q flask flask-cors requests

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "Please run: $PYTHON_CMD -m pip install flask flask-cors requests"
    exit 1
fi

echo "✅ Dependencies ready"
echo ""

# 启动服务器
echo "=================================="
echo "  🚀 Starting server..."
echo "  http://localhost:5000"
echo "=================================="
echo ""
echo "Press Ctrl+C to stop"
echo ""

$PYTHON_CMD app.py
