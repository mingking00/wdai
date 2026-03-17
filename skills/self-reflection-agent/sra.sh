#!/bin/bash
# SRA Service Manager
# Self-Reflection Agent 管理脚本

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRA_DIR="$SCRIPT_DIR"
WORKSPACE="/root/.openclaw/workspace"
PID_FILE="$WORKSPACE/.sra/sra.pid"
STATUS_FILE="$WORKSPACE/.sra/sra_status.json"

show_help() {
    echo "Self-Reflection Agent Service Manager"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|reflect|tips|anti-hacking-status|run-all-phases}"
    echo ""
    echo "基础命令:"
    echo "  start      - 启动 SRA 服务"
    echo "  stop       - 停止 SRA 服务"
    echo "  restart    - 重启 SRA 服务"
    echo "  status     - 查看服务状态"
    echo "  logs       - 查看日志"
    echo "  reflect    - 提交复盘请求"
    echo "  tips       - 查看提取的技巧"
    echo ""
    echo "Anti-Hacking命令:"
    echo "  anti-hacking-status - 查看Anti-Hacking统计"
    echo "  run-all-phases      - 手动执行完整六阶段分析"
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
            echo -e "${YELLOW}SRA 服务已在运行 (PID: $PID)${NC}"
            return 0
        fi
    fi
    
    echo -e "${GREEN}启动 SRA 服务...${NC}"
    nohup python3 "$SRA_DIR/sra_service.py" start > /dev/null 2>&1 &
    
    sleep 2
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ SRA 服务已启动 (PID: $PID)${NC}"
        echo -e "${BLUE}  自动复盘: 每天01:30进化复盘, 05:30日复盘${NC}"
    else
        echo -e "${RED}✗ 启动失败${NC}"
        return 1
    fi
}

stop_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}SRA 服务未运行${NC}"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    echo "停止 SRA 服务 (PID: $PID)..."
    
    python3 "$SRA_DIR/sra_service.py" stop 2>/dev/null || true
    
    sleep 1
    if [ -f "$PID_FILE" ]; then
        kill -9 "$PID" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    
    echo -e "${GREEN}✓ SRA 服务已停止${NC}"
}

restart_service() {
    stop_service
    sleep 2
    start_service
}

show_status() {
    python3 "$SRA_DIR/sra_service.py" status
}

show_logs() {
    LOG_FILE="$WORKSPACE/.sra/logs/sra_$(date +%Y%m%d).log"
    if [ -f "$LOG_FILE" ]; then
        tail -n 50 "$LOG_FILE"
    else
        echo "日志文件不存在"
    fi
}

submit_reflect() {
    DATE="${1:-$(date +%Y-%m-%d)}"
    
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}服务未运行，正在启动...${NC}"
        start_service
        sleep 2
    fi
    
    echo "提交复盘请求: $DATE"
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$SRA_DIR')
from sra_service import quick_reflect

result = quick_reflect('$DATE')
print(f"请求ID: {result['request_id']}")
print(f"状态: {result['status']}")
PYEOF
}

show_tips() {
    TIPS_FILE="$WORKSPACE/.sra/tips/extracted_tips.json"
    if [ -f "$TIPS_FILE" ]; then
        echo "提取的技巧:"
        python3 -c "
import json
with open('$TIPS_FILE', 'r') as f:
    tips = json.load(f)
    for i, tip in enumerate(tips[-10:], 1):  # 最近10个
        print(f\"{i}. [{tip['category']}] {tip['technique'][:60]}...\")
    print(f\"\n共 {len(tips)} 个技巧\")
"
    else
        echo "暂无提取的技巧"
    fi
}

show_reflections() {
    REFLECT_DIR="$WORKSPACE/.sra/reflections"
    if [ -d "$REFLECT_DIR" ]; then
        echo "复盘报告:"
        ls -lt "$REFLECT_DIR"/*.md 2>/dev/null | head -5 | while read line; do
            echo "  $line"
        done
    else
        echo "暂无复盘报告"
    fi
}

# IER命令
ier_stats() {
    echo -e "${GREEN}SRA-IER 迭代经验精炼系统统计${NC}"
    echo ""
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$SRA_DIR')
try:
    from sra_ier import get_sra_experience_manager
    manager = get_sra_experience_manager()
    stats = manager.get_statistics()
    
    print(f"总经验数: {stats['total_experiences']}")
    print(f"活跃经验: {stats['active_experiences']}")
    print(f"可靠经验: {stats['reliable_experiences']}")
    print(f"历史任务: {stats['total_tasks']}")
    print(f"复盘方法: {stats['reflection_methods']}")
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
    
    echo -e "${GREEN}SRA-IER 经验列表${NC}"
    if [ -n "$exp_type" ]; then
        echo -e "${GREEN}过滤类型: $exp_type${NC}"
    fi
    echo ""
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$SRA_DIR')
try:
    from sra_ier import get_sra_experience_manager
    manager = get_sra_experience_manager()
    
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
        print(f"效果评分: {exp.effectiveness_score:.2f}")
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
    echo -e "${GREEN}运行SRA-IER经验维护...${NC}"
    
    python3 << PYEOF
import sys
sys.path.insert(0, '$SRA_DIR')
try:
    from sra_ier import get_sra_experience_manager
    manager = get_sra_experience_manager()
    
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
    reflect)
        shift
        submit_reflect "$@"
        ;;
    tips)
        show_tips
        ;;
    list)
        show_reflections
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
    anti-hacking-status)
        python3 "$SRA_DIR/sra_service.py" anti-hacking-status
        ;;
    run-all-phases)
        python3 "$SRA_DIR/sra_service.py" run-all-phases
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
