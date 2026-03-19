#!/bin/bash
# wdai 安全检查脚本
# 在备份前运行，确保没有敏感信息

set -e

WORKSPACE="/root/.openclaw/workspace"
EXIT_CODE=0

echo "=========================================="
echo "wdai 安全检查"
echo "=========================================="
echo ""

cd "$WORKSPACE"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_passed() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_failed() {
    echo -e "${RED}❌ $1${NC}"
    EXIT_CODE=1
}

check_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "🔍 检查敏感信息..."
echo ""

# 1. 检查GitHub Token
if grep -r "ghp_[a-zA-Z0-9]\{36,\}" --include="*.md" --include="*.txt" --include="*.json" --include="*.sh" --include="*.py" . 2>/dev/null | grep -v ".git/" | grep -v "SECURITY_GUIDE" | head -5; then
    check_failed "发现GitHub Token明文存储"
else
    check_passed "未发现GitHub Token明文"
fi

# 2. 检查API Keys
if grep -r "sk-[a-zA-Z0-9]\{20,\}" --include="*.md" --include="*.txt" --include="*.json" --include="*.sh" --include="*.py" . 2>/dev/null | grep -v ".git/" | head -5; then
    check_failed "发现API Key"
else
    check_passed "未发现API Key"
fi

# 3. 检查密码
if grep -ri "password\|passwd" --include="*.json" --include="*.sh" . 2>/dev/null | grep -v ".git/" | grep -v "security\|check" | head -3; then
    check_warning "发现可能的密码字段，请检查"
else
    check_passed "未发现明显密码"
fi

# 4. 检查.env文件
if find . -name ".env" -o -name ".env.local" 2>/dev/null | grep -q "."; then
    if git check-ignore -q .env 2>/dev/null; then
        check_passed ".env文件已被.gitignore排除"
    else
        check_failed ".env文件存在但未被.gitignore排除"
    fi
else
    check_passed "无.env文件"
fi

# 5. 检查Token文件
if find . -name "token.txt" -o -name "tokens.json" -o -name "*.token" 2>/dev/null | grep -q "."; then
    check_failed "发现Token文件"
else
    check_passed "未发现Token文件"
fi

# 6. 检查Git历史
echo ""
echo "🔍 检查Git历史..."
if git log --all --oneline | grep -i "token\|key\|password\|secret" | head -3; then
    check_warning "Git历史中发现敏感关键词"
else
    check_passed "Git历史看起来安全"
fi

# 7. 检查即将提交的内容
echo ""
echo "🔍 检查即将提交的文件..."
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || echo "")
if [ -n "$STAGED_FILES" ]; then
    echo "即将提交的文件:"
    echo "$STAGED_FILES"
    
    # 检查暂存区内容
    if git diff --cached | grep -i "ghp_\|sk-\|api_key\|password" | head -3; then
        check_failed "暂存区中发现敏感信息"
    else
        check_passed "暂存区看起来安全"
    fi
else
    check_passed "没有暂存的更改"
fi

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 安全检查通过${NC}"
    echo "可以安全地执行备份"
else
    echo -e "${RED}❌ 安全检查未通过${NC}"
    echo "请修复上述问题后再备份"
fi
echo "=========================================="

exit $EXIT_CODE
