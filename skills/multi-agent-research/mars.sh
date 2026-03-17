#!/bin/bash
# MARS Service Manager
# Multi-Agent Research Service 管理脚本

set -e

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MARS_DIR="$SCRIPT_DIR"
WORKSPACE="/root/.openclaw/workspace"
PID_FILE="$WORKSPACE/.mars/mars.pid"
STATUS_FILE="$WORKSPACE/.mars/mars_status.json"
RESEARCH_DIR="$WORKSPACE/.mars/research_history"

show_help() {
    echo "Multi-Agent Research Service v3.0 Manager"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|research|list}"
    echo ""
    echo "命令:"
    echo "  start      - 启动 MARS 服务"
    echo "  stop       - 停止 MARS 服务"
    echo "  restart    - 重启 MARS 服务"
    echo "  status     - 查看服务状态"
    echo "  logs       - 查看日志"
    echo "  research   - 提交研究请求"
    echo "  list       - 列出研究报告"
    echo "  quick      - 快速研究（阻塞等待结果）"
    echo ""
    echo "示例:"
    echo "  $0 start                              # 启动服务"
    echo "  $0 research 'Latest AI frameworks'    # 提交研究"
    echo "  $0 quick 'GPT-5 rumors'               # 快速研究"
    echo ""
}

start_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}MARS 服务已在运行 (PID: $PID)${NC}"
            return 0
        fi
    fi
    
    echo -e "${GREEN}启动 MARS 服务 v3.0...${NC}"
    nohup python3 "$MARS_DIR/mars_service.py" start > /dev/null 2>&1 &
echo
    
    sleep 3
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ MARS 服务已启动 (PID: $PID)${NC}"
        echo -e "${BLUE}  并行架构: Explorer → N×Investigator → M×Critic → Synthesist${NC}"
    else
        echo -e "${RED}✗ 启动失败${NC}"
        return 1
    fi
}

stop_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}MARS 服务未运行${NC}"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    echo "停止 MARS 服务 (PID: $PID)..."
    
    python3 "$MARS_DIR/mars_service.py" stop 2>/dev/null || true
    
    sleep 1
    if [ -f "$PID_FILE" ]; then
        kill -9 "$PID" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    
    echo -e "${GREEN}✓ MARS 服务已停止${NC}"
}

restart_service() {
    stop_service
    sleep 2
    start_service
}

show_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}MARS 服务状态: 运行中${NC}"
            echo "  PID: $PID"
            
            if [ -f "$STATUS_FILE" ]; then
                echo ""
                python3 -c "
import json
with open('$STATUS_FILE', 'r') as f:
    s = json.load(f)
print(f\"  启动时间: {s.get('start_time', 'N/A')}\")
print(f\"  最后心跳: {s.get('last_heartbeat', 'N/A')}\")
print(f\"  总请求数: {s.get('total_requests', 0)}\")
print(f\"  待处理: {s.get('pending_requests', 0)}\")
print(f\"  已完成: {s.get('completed_requests', 0)}\")
print(f\"  失败: {s.get('failed_requests', 0)}\")
if s.get('current_task'):
    print(f\"  当前任务: {s['current_task']}\")
"
            fi
        else
            echo -e "${RED}MARS 服务状态: 异常 (PID文件存在但进程不存在)${NC}"
        fi
    else
        echo -e "${YELLOW}MARS 服务状态: 未运行${NC}"
    fi
}

show_logs() {
    echo "服务日志:"
    tail -n 50 "$WORKSPACE/.mars/"*.log 2>/dev/null || echo "无日志文件"
}

submit_research() {
    if [ $# -eq 0 ]; then
        echo "请提供研究查询"
        echo "用法: $0 research '你的研究问题'"
        return 1
    fi
    
    QUERY="$*"
    
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}服务未运行，正在启动...${NC}"
        start_service
        sleep 2
    fi
    
    echo "提交研究请求..."
    echo "  查询: $QUERY"
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$MARS_DIR')
from mars_service import submit_research_request

req_id = submit_research_request('$QUERY')
print(f"请求ID: {req_id}")
print("请求已提交，服务将在后台处理")
print(f"研究报告将保存到: $RESEARCH_DIR/")
PYEOF
}

quick_research() {
    if [ $# -eq 0 ]; then
        echo "请提供研究查询"
        echo "用法: $0 quick '你的研究问题'"
        return 1
    fi
    
    QUERY="$*"
    
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}服务未运行，正在启动...${NC}"
        start_service
        sleep 2
    fi
    
    echo -e "${BLUE}启动并行多Agent研究...${NC}"
    echo "查询: $QUERY"
    echo ""
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$MARS_DIR')
from mars_service import quick_research

result = quick_research('$QUERY', timeout=300)

if result.get('success'):
    print("\n" + "="*70)
    print("研究结论")
    print("="*70)
    print(result.get('final_answer', 'N/A'))
    print("\n" + "="*70)
    print(f"性能: {result.get('performance', {}).get('parallel_agents_used', 0)} 个Agent并行")
    print(f"耗时: {result.get('performance', {}).get('total_duration_seconds', 0):.1f} 秒")
    print(f"冲突解决: {result.get('conflicts_resolved', 0)} 个")
else:
    print(f"\n✗ 研究失败: {result.get('error', 'Unknown')}")
PYEOF
}

list_reports() {
    echo "研究报告列表:"
    echo ""
    
    if [ -d "$RESEARCH_DIR" ]; then
        ls -lt "$RESEARCH_DIR"/*.md 2>/dev/null | head -10 | while read line; do
            echo "  $line"
        done
        
        COUNT=$(ls -1 "$RESEARCH_DIR"/*.md 2>/dev/null | wc -l)
        echo ""
        echo "共 $COUNT 份研究报告"
    else
        echo "暂无研究报告"
    fi
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
    research)
        shift
        submit_research "$@"
        ;;
    quick)
        shift
        quick_research "$@"
        ;;
    list)
        list_reports
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
