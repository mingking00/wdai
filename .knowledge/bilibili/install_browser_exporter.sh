#!/bin/bash
# B站收藏夹浏览器自动化导出 - 安装脚本

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     B站收藏夹浏览器自动化导出工具 - 安装向导               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd /root/.openclaw/workspace/.knowledge/bilibili

# 检查Python
echo "📋 检查Python环境..."
python3 --version || { echo "❌ Python3未安装"; exit 1; }

# 安装Playwright
echo ""
echo "📦 安装Playwright..."
pip3 install playwright

# 安装Chromium浏览器
echo ""
echo "🌐 安装Chromium浏览器..."
playwright install chromium

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用方法:"
echo "  1. 交互模式 (显示浏览器窗口):"
echo "     python3 browser_exporter.py --visible"
echo ""
echo "  2. 无头模式 (后台运行):"
echo "     python3 browser_exporter.py --headless"
echo ""
echo "  3. 导出特定收藏夹:"
echo "     python3 browser_exporter.py --fav 'q'"
