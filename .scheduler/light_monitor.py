#!/usr/bin/env python3
"""
wdai 轻量监控模式 v1.0
任务驱动替代空转，只做有价值的监控
"""

import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
SCHEDULER_DIR = WORKSPACE / ".scheduler"

def light_monitor():
    """
    轻量监控模式
    只做：GitHub项目发现（有价值的新项目）
    不做：无意义的循环进化
    """
    
    # 检查是否有新的GitHub项目值得学习
    projects_file = SCHEDULER_DIR / "discovered_projects.json"
    if projects_file.exists():
        with open(projects_file, 'r') as f:
            projects = json.load(f)
        
        # 只记录高价值项目
        high_value = [p for p in projects if p.get('stars', 0) >= 5]
        
        if high_value:
            print(f"发现 {len(high_value)} 个高价值项目，等待用户决策")
            # 写入待处理队列，不自动分析
            pending_file = SCHEDULER_DIR / "pending_projects.json"
            with open(pending_file, 'w') as f:
                json.dump(high_value, f, indent=2)
    
    # 记录轻量监控状态
    status = {
        "mode": "light_monitor",
        "timestamp": datetime.now().isoformat(),
        "message": "任务驱动模式，等待用户分配任务",
        "actions": ["github_discovery"],
        "skip": ["evolution_loop", "empty_reflection"]
    }
    
    status_file = SCHEDULER_DIR / "light_monitor_status.json"
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"[{datetime.now().strftime('%H:%M')}] 轻量监控: 空闲，等待任务")

if __name__ == '__main__':
    light_monitor()
