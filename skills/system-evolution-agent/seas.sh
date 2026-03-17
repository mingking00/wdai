#!/bin/bash
# SEA Service Manager
# System Evolution Agent 服务管理脚本

set -e

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEA_DIR="$SCRIPT_DIR"
PID_FILE="/root/.openclaw/workspace/.system/seas.pid"
STATUS_FILE="/root/.openclaw/workspace/.system/seas_status.json"

show_help() {
    echo "System Evolution Agent Service Manager"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs}"
    echo ""
    echo "基础命令:"
    echo "  start     - 启动 SEA 服务"
    echo "  stop      - 停止 SEA 服务"
    echo "  restart   - 重启 SEA 服务"
    echo "  status    - 查看服务状态"
    echo "  logs      - 查看日志"
    echo "  improve   - 提交改进请求"
    echo "  analyze   - 提交分析请求"
    echo ""
    echo "IER经验系统命令:"
    echo "  ier-stats  - 查看IER统计"
    echo "  ier-list   - 列出经验"
    echo "  ier-maintain - 运行经验维护"
    echo ""
}

start_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}SEA 服务已在运行 (PID: $PID)${NC}"
            return 0
        fi
    fi
    
    echo -e "${GREEN}启动 SEA 服务...${NC}"
    nohup python3 "$SEA_DIR/sea_service.py" start > /dev/null 2>&1 &
    
    # 等待服务启动
    sleep 2
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ SEA 服务已启动 (PID: $PID)${NC}"
    else
        echo -e "${RED}✗ 启动失败${NC}"
        return 1
    fi
}

stop_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}SEA 服务未运行${NC}"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    echo "停止 SEA 服务 (PID: $PID)..."
    
    python3 "$SEA_DIR/sea_service.py" stop
    
    # 确保停止
    sleep 1
    if [ -f "$PID_FILE" ]; then
        kill -9 "$PID" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    
    echo -e "${GREEN}✓ SEA 服务已停止${NC}"
}

restart_service() {
    stop_service
    sleep 2
    start_service
}

show_status() {
    python3 "$SEA_DIR/sea_service.py" status
}

show_logs() {
    LOG_FILE="/root/.openclaw/workspace/.system/logs/sea_$(date +%Y%m%d).log"
    if [ -f "$LOG_FILE" ]; then
        tail -n 50 "$LOG_FILE"
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
}

submit_improvement() {
    if [ $# -lt 2 ]; then
        echo "用法: $0 improve '描述' '文件路径'"
        echo "示例: $0 improve '优化错误处理' 'skills/my_tool/core.py'"
        return 1
    fi
    
    DESCRIPTION="$1"
    FILE_PATH="$2"
    
    # 检查文件是否存在
    if [ ! -f "/root/.openclaw/workspace/$FILE_PATH" ]; then
        echo -e "${RED}文件不存在: $FILE_PATH${NC}"
        return 1
    fi
    
    echo "提交改进请求..."
    echo "  描述: $DESCRIPTION"
    echo "  文件: $FILE_PATH"
    
    # 创建Python脚本来提交请求
    python3 << PYEOF
import sys
sys.path.insert(0, '$SEA_DIR')
from sea_service import submit_improvement_request

with open('/root/.openclaw/workspace/$FILE_PATH', 'r') as f:
    content = f.read()

req_id = submit_improvement_request(
    description='$DESCRIPTION',
    changes={'$FILE_PATH': content}
)

print(f"请求已提交: {req_id}")
print("等待处理...")

from sea_service import get_response
response = get_response(req_id, timeout=60)

if response:
    result = response.get('result', {})
    if result.get('success'):
        print(f"✓ 成功: {result.get('status')}")
        print(f"  得分: {result.get('review_score')}")
    else:
        print(f"✗ 失败: {result.get('message', 'Unknown')}")
else:
    print("等待响应超时，请稍后检查状态")
PYEOF
}

submit_analysis() {
    echo "提交系统分析请求..."
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$SEA_DIR')
from sea_service import submit_analysis_request, get_response

req_id = submit_analysis_request()
print(f"请求已提交: {req_id}")
print("等待分析结果...")

response = get_response(req_id, timeout=30)

if response:
    result = response.get('result', {})
    if result.get('success'):
        analysis = result.get('result', {})
        print("\n分析结果:")
        for finding in analysis.get('findings', []):
            print(f"  ! {finding}")
        for suggestion in analysis.get('suggestions', []):
            print(f"  → {suggestion}")
    else:
        print(f"分析失败: {result.get('message')}")
else:
    print("等待响应超时")
PYEOF
}

# IER命令
ier_stats() {
    echo -e "${GREEN}SEA-IER 迭代经验精炼系统统计${NC}"
    echo ""
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$SEA_DIR')
try:
    from sea_ier import get_sea_experience_manager
    manager = get_sea_experience_manager()
    stats = manager.get_statistics()
    
    print(f"总经验数: {stats['total_experiences']}")
    print(f"活跃经验: {stats['active_experiences']}")
    print(f"可靠经验: {stats['reliable_experiences']}")
    print(f"历史任务: {stats['total_tasks']}")
    print(f"重构模式: {stats['refactoring_patterns']}")
    print("")
    print("按类型分布:")
    for exp_type, count in stats['by_type'].items():
        print(f"  {exp_type}: {count}")
except Exception as e:
    print(f"获取统计失败: {e}")
PYEOF
}

ier_list() {
    exp_type="$1"
    
    echo -e "${GREEN}SEA-IER 经验列表${NC}"
    if [ -n "$exp_type" ]; then
        echo -e "${GREEN}过滤类型: $exp_type${NC}"
    fi
    echo ""
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$SEA_DIR')
try:
    from sea_ier import get_sea_experience_manager
    manager = get_sea_experience_manager()
    
    filter_type = "$exp_type"
    count = 0
    
    for exp_id, exp in manager.experiences.items():
        if filter_type and exp.exp_type.value != filter_type:
            continue
        count += 1
        print(f"ID: {exp.id}")
        print(f"名称: {exp.name}")
        print(f"类型: {exp.exp_type.value}")
        print(f"成功率: {exp.success_rate():.1%} ({exp.success_count}/{exp.usage_count})")
        print(f"置信度: {exp.confidence_score:.2f}")
        print(f"状态: {exp.status.value}")
        print(f"场景: {exp.context[:80]}...")
        print("-" * 50)
    
    if count == 0:
        print("没有找到经验")
    else:
        print(f"\n共 {count} 条经验")
except Exception as e:
    print(f"列出经验失败: {e}")
PYEOF
}

ier_maintain() {
    echo -e "${GREEN}运行SEA-IER经验维护...${NC}"
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$SEA_DIR')
try:
    from sea_ier import get_sea_experience_manager
    manager = get_sea_experience_manager()
    
    eliminated = manager.evaluate_and_eliminate()
    stats = manager.get_statistics()
    
    print(f"淘汰经验数: {len(eliminated)}")
    if eliminated:
        print("被淘汰的经验:")
        for exp_id in eliminated:
            print(f"  - {exp_id}")
    print("")
    print(f"当前状态: {stats['active_experiences']}/{stats['total_experiences']} 活跃经验")
except Exception as e:
    print(f"维护失败: {e}")
PYEOF
}

# 主入口
case "${1:-}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    improve)
        shift
        submit_improvement "$@"
        ;;
    analyze)
        submit_analysis
        ;;
    ier-stats)
        ier_stats
        ;;
    ier-list)
        shift
        ier_list "$@"
        ;;
    ier-maintain)
        ier_maintain
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
