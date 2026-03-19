#!/bin/bash
# Linux系统监控与诊断平台
# 功能: 实时监控系统状态，自动发现异常
# 沉淀技能: 系统监控、问题诊断、自动化检测

set -e

WORKSPACE="$HOME/.openclaw/system-monitor"
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"

echo "======================================"
echo "🔧 Linux系统监控与诊断平台搭建"
echo "======================================"

# ============ 1. 系统信息收集器 ============
cat > system_info.sh << 'EOF'
#!/bin/bash
# 系统信息收集 - 沉淀技能1: 快速了解系统全貌

echo "=== 系统基础信息 ==="
echo "主机名: $(hostname)"
echo "操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "内核版本: $(uname -r)"
echo "架构: $(uname -m)"
echo ""

echo "=== CPU信息 ==="
echo "型号: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d':' -f2 | xargs)"
echo "核心数: $(nproc)"
echo "负载: $(uptime | awk -F'load average:' '{print $2}')"
echo ""

echo "=== 内存信息 ==="
free -h | grep -E "(Mem|Swap)"
echo ""

echo "=== 磁盘使用 ==="
df -h | grep -E "(Filesystem|/dev/)" | head -5
echo ""

echo "=== 网络连接 ==="
echo "活跃连接数: $(netstat -an 2>/dev/null | grep ESTABLISHED | wc -l)"
ip addr show | grep "inet " | head -3
echo ""

echo "=== 当前用户 ==="
who
echo ""

echo "=== 运行时间 ==="
uptime
echo ""
EOF

chmod +x system_info.sh

# ============ 2. 性能监控器 ============
cat > performance_monitor.sh << 'EOF'
#!/bin/bash
# 性能监控 - 沉淀技能2: 发现性能瓶颈

LOG_FILE="$HOME/.openclaw/system-monitor/perf.log"
INTERVAL=${1:-5}  # 默认5秒采集一次

log_metric() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    local disk_io=$(iostat -x 1 1 2>/dev/null | tail -n +4 | head -1 | awk '{print $10}' || echo "N/A")
    
    echo "$timestamp | CPU: ${cpu_usage}% | MEM: ${mem_usage}% | Load: $load_avg | IO: $disk_io"
    echo "$timestamp,$cpu_usage,$mem_usage,$load_avg,$disk_io" >> "$LOG_FILE"
}

echo "开始性能监控 (间隔: ${INTERVAL}秒)"
echo "日志: $LOG_FILE"
echo "按 Ctrl+C 停止"
echo ""

# CSV头
if [ ! -f "$LOG_FILE" ]; then
    echo "timestamp,cpu_usage,mem_usage,load_avg,disk_io" > "$LOG_FILE"
fi

while true; do
    log_metric
    sleep "$INTERVAL"
done
EOF

chmod +x performance_monitor.sh

# ============ 3. 异常检测器 ============
cat > anomaly_detector.sh << 'EOF'
#!/bin/bash
# 异常检测 - 沉淀技能3: 自动发现问题

# 阈值配置
CPU_THRESHOLD=80
MEM_THRESHOLD=85
LOAD_THRESHOLD=$(nproc)  # 核心数
DISK_THRESHOLD=90

LOG_FILE="$HOME/.openclaw/system-monitor/anomalies.log"

detect_anomalies() {
    local alerts=()
    
    # CPU检查
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d'.' -f1)
    if [ "$cpu_usage" -gt "$CPU_THRESHOLD" ]; then
        alerts+=("⚠️  CPU使用率过高: ${cpu_usage}% (阈值: ${CPU_THRESHOLD}%)")
    fi
    
    # 内存检查
    local mem_usage=$(free | grep Mem | awk '{printf "%d", $3/$2 * 100.0}')
    if [ "$mem_usage" -gt "$MEM_THRESHOLD" ]; then
        alerts+=("⚠️  内存使用率过高: ${mem_usage}% (阈值: ${MEM_THRESHOLD}%)")
    fi
    
    # 负载检查
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    local load_int=$(echo "$load_avg" | cut -d'.' -f1)
    if [ "$load_int" -gt "$LOAD_THRESHOLD" ]; then
        alerts+=("⚠️  系统负载过高: $load_avg (核心数: $LOAD_THRESHOLD)")
    fi
    
    # 磁盘检查
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
    if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
        alerts+=("⚠️  磁盘空间不足: ${disk_usage}% (阈值: ${DISK_THRESHOLD}%)")
    fi
    
    # 僵尸进程检查
    local zombie_count=$(ps aux | grep -c '\<Z\>' || echo 0)
    if [ "$zombie_count" -gt 0 ]; then
        alerts+=("⚠️  发现僵尸进程: $zombie_count 个")
    fi
    
    # 输出结果
    if [ ${#alerts[@]} -eq 0 ]; then
        echo "✅ 系统状态正常 ($(date '+%H:%M:%S'))"
    else
        echo "🚨 发现异常 ($(date '+%H:%M:%S'))"
        for alert in "${alerts[@]}"; do
            echo "  $alert"
            echo "$(date '+%Y-%m-%d %H:%M:%S') $alert" >> "$LOG_FILE"
        done
    fi
}

echo "开始异常检测 (按 Ctrl+C 停止)"
echo "日志: $LOG_FILE"
echo ""

while true; do
    detect_anomalies
    sleep 10
done
EOF

chmod +x anomaly_detector.sh

# ============ 4. 进程分析器 ============
cat > process_analyzer.sh << 'EOF'
#!/bin/bash
# 进程分析 - 沉淀技能4: 定位问题进程

echo "=== 资源占用TOP进程 ==="
echo ""

echo "🔥 CPU占用TOP10:"
ps aux --sort=-%cpu | head -11 | tail -10 | awk '{printf "  %-8s %5s %5s %s\n", $1, $3, $4, $11}'
echo ""

echo "🧠 内存占用TOP10:"
ps aux --sort=-%mem | head -11 | tail -10 | awk '{printf "  %-8s %5s %5s %s\n", $1, $3, $4, $11}'
echo ""

echo "⏱️  运行时间最长的进程:"
ps aux --sort=-etime | head -6 | tail -5 | awk '{printf "  %-8s %10s %s\n", $1, $10, $11}'
echo ""

echo "🔍 当前用户进程数:"
echo "  $(ps aux | wc -l) 个进程"
echo ""

echo "🧵 线程数TOP5进程:"
ps -eLf | awk '{print $11}' | sort | uniq -c | sort -rn | head -5 | awk '{printf "  %4s threads: %s\n", $1, $2}'
echo ""
EOF

chmod +x process_analyzer.sh

# ============ 5. 网络诊断器 ============
cat > network_diagnoser.sh << 'EOF'
#!/bin/bash
# 网络诊断 - 沉淀技能5: 网络问题定位

echo "=== 网络诊断 ==="
echo ""

echo "🌐 网络接口状态:"
ip -s link | grep -E "(^[0-9]|RX:|TX:)" | head -20
echo ""

echo "📡 监听端口:"
ss -tlnp | head -10
echo ""

echo "🔗 活跃连接:"
ss -s
echo ""

echo "🌍 DNS测试:"
ping -c 1 8.8.8.8 > /dev/null 2>&1 && echo "  ✅ 外网连接正常" || echo "  ❌ 外网连接失败"

echo "  DNS解析测试:"
nslookup google.com > /dev/null 2>&1 && echo "    ✅ DNS解析正常" || echo "    ❌ DNS解析失败"
echo ""

echo "📊 网络流量统计:"
cat /proc/net/dev | tail -n +3 | awk '{printf "  %-8s RX: %12s  TX: %12s\n", $1, $2, $10}'
echo ""
EOF

chmod +x network_diagnoser.sh

# ============ 6. 一键诊断报告 ============
cat > full_diagnosis.sh << 'EOF'
#!/bin/bash
# 完整系统诊断报告

REPORT_FILE="$HOME/.openclaw/system-monitor/diagnosis_$(date +%Y%m%d_%H%M%S).txt"

echo "生成完整诊断报告..."
{
    echo "======================================"
    echo "🖥️  Linux系统诊断报告"
    echo "生成时间: $(date)"
    echo "======================================"
    echo ""
    
    ./system_info.sh
    echo ""
    
    ./process_analyzer.sh
    echo ""
    
    ./network_diagnoser.sh
    echo ""
    
    echo "======================================"
    echo "🔍 异常检测快照"
    echo "======================================"
    ./anomaly_detector.sh 2>/dev/null | head -1
    
} > "$REPORT_FILE"

echo "✅ 报告已生成: $REPORT_FILE"
cat "$REPORT_FILE"
EOF

chmod +x full_diagnosis.sh

# ============ 7. 主控面板 ============
cat > monitor.sh << 'EOF'
#!/bin/bash
# 系统监控主控面板

WORKSPACE="$HOME/.openclaw/system-monitor"
cd "$WORKSPACE"

show_menu() {
    clear
    echo "======================================"
    echo "🔧 Linux系统监控与诊断平台"
    echo "======================================"
    echo ""
    echo "1. 📊 系统概览 (快速了解系统)"
    echo "2. 📈 性能监控 (实时监控CPU/内存/IO)"
    echo "3. 🚨 异常检测 (自动发现问题)"
    echo "4. 🔍 进程分析 (定位资源占用)"
    echo "5. 🌐 网络诊断 (检查网络状态)"
    echo "6. 📋 完整报告 (生成诊断报告)"
    echo "7. ❌ 退出"
    echo ""
    echo "======================================"
}

while true; do
    show_menu
    read -p "选择功能 [1-7]: " choice
    
    case $choice in
        1)
            echo ""
            ./system_info.sh
            read -p "按回车继续..."
            ;;
        2)
            echo ""
            echo "启动性能监控 (按Ctrl+C停止)..."
            ./performance_monitor.sh
            read -p "按回车继续..."
            ;;
        3)
            echo ""
            echo "启动异常检测 (按Ctrl+C停止)..."
            ./anomaly_detector.sh
            read -p "按回车继续..."
            ;;
        4)
            echo ""
            ./process_analyzer.sh
            read -p "按回车继续..."
            ;;
        5)
            echo ""
            ./network_diagnoser.sh
            read -p "按回车继续..."
            ;;
        6)
            echo ""
            ./full_diagnosis.sh
            read -p "按回车继续..."
            ;;
        7)
            echo "再见!"
            exit 0
            ;;
        *)
            echo "无效选择"
            sleep 1
            ;;
    esac
done
EOF

chmod +x monitor.sh

echo ""
echo "======================================"
echo "✅ 搭建完成!"
echo "======================================"
echo ""
echo "📁 项目位置: $WORKSPACE"
echo ""
echo "🚀 启动方式:"
echo "  cd $WORKSPACE && ./monitor.sh"
echo ""
echo "📚 沉淀的技能:"
echo "  1. 系统信息收集 - 快速了解系统全貌"
echo "  2. 性能监控 - 发现性能瓶颈"  
echo "  3. 异常检测 - 自动发现问题"
echo "  4. 进程分析 - 定位问题进程"
echo "  5. 网络诊断 - 网络问题定位"
echo ""
echo "💡 使用建议:"
echo "  - 日常检查: 运行 ./system_info.sh"
echo "  - 性能问题: 运行 ./performance_monitor.sh"
echo "  - 系统异常: 运行 ./anomaly_detector.sh"
echo "  - 全面诊断: 运行 ./full_diagnosis.sh"
echo ""
