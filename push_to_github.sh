#!/bin/bash
# wdai GitHub推送脚本
# 使用方法: ./push_to_github.sh <你的GitHub用户名>

set -e

GITHUB_USER=$1
REPO_NAME="wdai"

if [ -z "$GITHUB_USER" ]; then
    echo "Usage: ./push_to_github.sh <你的GitHub用户名>"
    echo ""
    echo "例如: ./push_to_github.sh myusername"
    exit 1
fi

echo "=========================================="
echo "wdai 系统 GitHub 推送脚本"
echo "=========================================="
echo ""

# 检查GitHub CLI
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI 已安装"
    USE_GH=true
else
    echo "⚠️  GitHub CLI 未安装，将使用HTTPS方式"
    USE_GH=false
fi

# 检查Git状态
echo ""
echo "📋 检查Git状态..."
git status --short

# 创建GitHub仓库
echo ""
echo "🌐 在GitHub上创建仓库..."
if [ "$USE_GH" = true ]; then
    gh repo create "$REPO_NAME" --public --source=. --remote=origin --push || {
        echo "⚠️  仓库可能已存在，尝试添加远程..."
        git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git" 2>/dev/null || true
    }
else
    echo ""
    echo "请手动在GitHub上创建仓库:"
    echo "1. 访问 https://github.com/new"
    echo "2. 仓库名: $REPO_NAME"
    echo "3. 选择 Public 或 Private"
    echo "4. 不要勾选 'Initialize this repository with a README'"
    echo ""
    read -p "按Enter继续..."
    
    # 添加远程仓库
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git" 2>/dev/null || {
        git remote set-url origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    }
fi

# 推送代码
echo ""
echo "📤 推送代码到GitHub..."
git branch -M master
git push -u origin master

echo ""
echo "=========================================="
echo "✅ 推送完成！"
echo "=========================================="
echo ""
echo "仓库地址: https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "后续更新命令:"
echo "  git add ."
echo "  git commit -m '更新说明'"
echo "  git push"
