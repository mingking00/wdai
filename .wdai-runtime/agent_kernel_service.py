#!/usr/bin/env python3
"""
wdai Agent Kernel Service
5-Agent循环的系统级服务

用法:
  python3 agent_kernel_service.py start    # 启动服务
  python3 agent_kernel_service.py stop     # 停止服务
  python3 agent_kernel_service.py status   # 查看状态
  python3 agent_kernel_service.py submit   # 提交任务
"""

import sys
import os
import json
import signal
import time
import subprocess
from pathlib import Path

# 确保能导入agent_kernel
sys.path.insert(0, str(Path(__file__).parent))
from agent_kernel import get_kernel, AgentKernel, TaskStatus

PID_FILE = Path("/root/.openclaw/workspace/.wdai-runtime/agent_kernel.pid")
SERVICE_LOG = Path("/root/.openclaw/workspace/.wdai-runtime/agent_kernel.log")

def is_running() -> bool:
    """检查服务是否运行"""
    if not PID_FILE.exists():
        return False
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        # 检查进程是否存在
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, OSError):
        return False

def start_service():
    """启动服务"""
    if is_running():
        print("⚠️  Agent Kernel 服务已经在运行")
        return
        
    # 后台启动
    pid = os.fork()
    if pid > 0:
        # 父进程
        print(f"✅ Agent Kernel 服务已启动 (PID: {pid})")
        with open(PID_FILE, 'w') as f:
            f.write(str(pid))
        return
    else:
        # 子进程
        # 重定向输出到日志
        sys.stdout = open(SERVICE_LOG, 'a')
        sys.stderr = open(SERVICE_LOG, 'a')
        
        # 启动内核
        kernel = get_kernel()
        
        def signal_handler(sig, frame):
            print("\n[AgentKernel] Received shutdown signal")
            kernel.stop()
            if PID_FILE.exists():
                PID_FILE.unlink()
            sys.exit(0)
            
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        kernel.start()
        
        # 保持运行
        while True:
            time.sleep(1)

def stop_service():
    """停止服务"""
    if not is_running():
        print("⚠️  Agent Kernel 服务未运行")
        if PID_FILE.exists():
            PID_FILE.unlink()
        return
        
    with open(PID_FILE, 'r') as f:
        pid = int(f.read().strip())
        
    try:
        os.kill(pid, signal.SIGTERM)
        # 等待进程结束
        for _ in range(10):
            if not is_running():
                break
            time.sleep(0.5)
        
        if PID_FILE.exists():
            PID_FILE.unlink()
            
        print("✅ Agent Kernel 服务已停止")
    except ProcessLookupError:
        print("⚠️  进程已不存在")
        if PID_FILE.exists():
            PID_FILE.unlink()

def get_status():
    """获取服务状态"""
    if not is_running():
        print("⚠️  Agent Kernel 服务未运行")
        return
        
    # 从状态文件读取
    state_file = Path("/root/.openclaw/workspace/.wdai-runtime/kernel_state/kernel_state.json")
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = json.load(f)
            
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║              Agent Kernel 服务状态                          ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
        print("📊 Agent 统计:")
        for agent_id, stats in state.get("agent_stats", {}).items():
            print(f"  {agent_id}:")
            for key, value in stats.items():
                print(f"    - {key}: {value}")
        print()
        
        # 读取任务状态
        tasks_file = Path("/root/.openclaw/workspace/.wdai-runtime/kernel_state/tasks.json")
        if tasks_file.exists():
            with open(tasks_file, 'r') as f:
                tasks = json.load(f)
            print(f"📋 任务状态:")
            print(f"  - 待处理: {len(tasks.get('pending', []))}")
            print(f"  - 活跃: {len(tasks.get('active', {}))}")
            print(f"  - 已完成: {len(tasks.get('completed', []))}")
    else:
        print("ℹ️  暂无状态信息")

def submit_task(task_type: str, description: str, payload: str = "{}"):
    """提交任务"""
    if not is_running():
        print("⚠️  Agent Kernel 服务未运行，请先启动")
        return
        
    # 通过文件提交任务
    tasks_dir = Path("/root/.openclaw/workspace/.wdai-runtime/kernel_state/task_submissions")
    tasks_dir.mkdir(exist_ok=True)
    
    task_data = {
        "task_type": task_type,
        "description": description,
        "payload": json.loads(payload),
        "submitted_at": time.time()
    }
    
    task_file = tasks_dir / f"task_{int(time.time()*1000)}.json"
    with open(task_file, 'w') as f:
        json.dump(task_data, f, indent=2)
        
    print(f"✅ 任务已提交: {task_file.name}")
    print(f"   类型: {task_type}")
    print(f"   描述: {description}")

def show_logs(lines: int = 50):
    """显示日志"""
    if not SERVICE_LOG.exists():
        print("ℹ️  暂无日志")
        return
        
    # 读取最后N行
    with open(SERVICE_LOG, 'r') as f:
        all_lines = f.readlines()
        
    for line in all_lines[-lines:]:
        print(line, end='')

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print(f"  {sys.argv[0]} start              # 启动服务")
        print(f"  {sys.argv[0]} stop               # 停止服务")
        print(f"  {sys.argv[0]} status             # 查看状态")
        print(f"  {sys.argv[0]} submit <type> <desc> [payload]  # 提交任务")
        print(f"  {sys.argv[0]} log [lines]        # 查看日志")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "start":
        start_service()
    elif command == "stop":
        stop_service()
    elif command == "status":
        get_status()
    elif command == "submit":
        if len(sys.argv) < 4:
            print("用法: submit <type> <description> [payload]")
            sys.exit(1)
        payload = sys.argv[4] if len(sys.argv) > 4 else "{}"
        submit_task(sys.argv[2], sys.argv[3], payload)
    elif command == "log":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        show_logs(lines)
    else:
        print(f"未知命令: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
