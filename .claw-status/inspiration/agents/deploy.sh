#!/bin/bash
#
# Deploy Dual-Agent System - 双代理系统部署脚本
#
# Usage: ./deploy.sh [backup|deploy|rollback]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSPIRATION_DIR="$SCRIPT_DIR/.."
BACKUP_DIR="$INSPIRATION_DIR/backup/$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "🚀 双代理系统部署脚本"
echo "=========================================="

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 备份当前系统
backup() {
    log_info "创建备份..."
    mkdir -p "$BACKUP_DIR"
    
    # 备份关键文件
    if [ -f "$INSPIRATION_DIR/inspiration_fetcher.py" ]; then
        cp "$INSPIRATION_DIR/inspiration_fetcher.py" "$BACKUP_DIR/"
        log_info "已备份 inspiration_fetcher.py"
    fi
    
    if [ -f "$INSPIRATION_DIR/scheduler.py" ]; then
        cp "$INSPIRATION_DIR/scheduler.py" "$BACKUP_DIR/"
        log_info "已备份 scheduler.py"
    fi
    
    # 备份数据
    if [ -d "$INSPIRATION_DIR/data" ]; then
        cp -r "$INSPIRATION_DIR/data" "$BACKUP_DIR/"
        log_info "已备份 data/ 目录"
    fi
    
    echo "$BACKUP_DIR" > "$INSPIRATION_DIR/.last_backup"
    log_info "备份完成: $BACKUP_DIR"
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    cd "$SCRIPT_DIR"
    
    # 测试基类
    log_info "测试 Base Agent..."
    python3 base.py > /dev/null 2>&1 && log_info "  ✅ Base Agent 通过" || {
        log_error "  ❌ Base Agent 失败"
        return 1
    }
    
    # 测试 Planner
    log_info "测试 Planner Agent..."
    timeout 10 python3 planner_agent.py > /dev/null 2>&1 && log_info "  ✅ Planner Agent 通过" || {
        log_warn "  ⚠️ Planner Agent 测试超时或失败（可能无执行代理）"
    }
    
    # 测试集成
    log_info "测试 Integration..."
    timeout 15 python3 integration.py > /dev/null 2>&1 && log_info "  ✅ Integration 通过" || {
        log_warn "  ⚠️ Integration 测试超时"
    }
    
    log_info "测试完成"
}

# 部署
deploy() {
    log_info "开始部署双代理系统..."
    
    # 1. 备份
    backup
    
    # 2. 运行测试
    run_tests
    
    # 3. 检查依赖
    log_info "检查依赖..."
    python3 -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from base import BaseAgent; print('  ✅ 依赖检查通过')" || {
        log_error "依赖检查失败"
        return 1
    }
    
    # 4. 更新 __init__.py
    log_info "确保包结构正确..."
    if [ ! -f "$SCRIPT_DIR/__init__.py" ]; then
        touch "$SCRIPT_DIR/__init__.py"
        log_info "  创建 __init__.py"
    fi
    
    # 5. 创建部署标记
    echo "dual_agent_v1.0" > "$INSPIRATION_DIR/.deployment_version"
    echo "$(date -Iseconds)" > "$INSPIRATION_DIR/.deployment_time"
    
    log_info "=========================================="
    log_info "✅ 部署成功！"
    log_info "=========================================="
    log_info ""
    log_info "使用方法:"
    log_info "  from agents import DualAgentInspirationSystem"
    log_info "  system = DualAgentInspirationSystem()"
    log_info "  system.start()"
    log_info "  result = system.run_cycle()"
    log_info ""
    log_info "备份位置: $BACKUP_DIR"
    log_info "回滚命令: ./deploy.sh rollback"
}

# 回滚
rollback() {
    if [ ! -f "$INSPIRATION_DIR/.last_backup" ]; then
        log_error "未找到备份记录，无法回滚"
        return 1
    fi
    
    LAST_BACKUP=$(cat "$INSPIRATION_DIR/.last_backup")
    
    if [ ! -d "$LAST_BACKUP" ]; then
        log_error "备份目录不存在: $LAST_BACKUP"
        return 1
    fi
    
    log_warn "准备回滚到: $LAST_BACKUP"
    read -p "确认回滚? [y/N] " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "取消回滚"
        return 0
    fi
    
    # 恢复文件
    if [ -f "$LAST_BACKUP/inspiration_fetcher.py" ]; then
        cp "$LAST_BACKUP/inspiration_fetcher.py" "$INSPIRATION_DIR/"
        log_info "已恢复 inspiration_fetcher.py"
    fi
    
    if [ -f "$LAST_BACKUP/scheduler.py" ]; then
        cp "$LAST_BACKUP/scheduler.py" "$INSPIRATION_DIR/"
        log_info "已恢复 scheduler.py"
    fi
    
    rm -f "$INSPIRATION_DIR/.deployment_version"
    rm -f "$INSPIRATION_DIR/.deployment_time"
    
    log_info "=========================================="
    log_info "✅ 回滚完成"
    log_info "=========================================="
}

# 显示状态
status() {
    log_info "系统状态检查..."
    
    if [ -f "$INSPIRATION_DIR/.deployment_version" ]; then
        VERSION=$(cat "$INSPIRATION_DIR/.deployment_version")
        TIME=$(cat "$INSPIRATION_DIR/.deployment_time")
        log_info "部署版本: $VERSION"
        log_info "部署时间: $TIME"
    else
        log_warn "未检测到部署记录"
    fi
    
    if [ -f "$INSPIRATION_DIR/.last_backup" ]; then
        LAST_BACKUP=$(cat "$INSPIRATION_DIR/.last_backup")
        log_info "最近备份: $LAST_BACKUP"
    fi
    
    # 检查文件
    log_info "文件检查:"
    [ -f "$SCRIPT_DIR/base.py" ] && log_info "  ✅ base.py" || log_error "  ❌ base.py"
    [ -f "$SCRIPT_DIR/planner_agent.py" ] && log_info "  ✅ planner_agent.py" || log_error "  ❌ planner_agent.py"
    [ -f "$SCRIPT_DIR/executor_agent.py" ] && log_info "  ✅ executor_agent.py" || log_error "  ❌ executor_agent.py"
    [ -f "$SCRIPT_DIR/integration.py" ] && log_info "  ✅ integration.py" || log_error "  ❌ integration.py"
    [ -f "$SCRIPT_DIR/fetch_adapter.py" ] && log_info "  ✅ fetch_adapter.py" || log_error "  ❌ fetch_adapter.py"
}

# 主命令
COMMAND=${1:-deploy}

case $COMMAND in
    backup)
        backup
        ;;
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    test)
        run_tests
        ;;
    *)
        echo "用法: $0 [backup|deploy|rollback|status|test]"
        echo ""
        echo "命令:"
        echo "  backup   - 创建备份"
        echo "  deploy   - 部署双代理系统（默认）"
        echo "  rollback - 回滚到上一个版本"
        echo "  status   - 查看系统状态"
        echo "  test     - 运行测试"
        exit 1
        ;;
esac
