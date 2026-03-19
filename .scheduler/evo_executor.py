#!/usr/bin/env python3
"""
EVO任务执行器 - 供定时任务调用
简化版，只完成核心工作
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
SCHEDULER = WORKSPACE / ".scheduler"
EVO_DIR = WORKSPACE / ".claw-status" / "evo"

def load_todo():
    """加载今日待办"""
    todo_file = SCHEDULER / "daily-todo.json"
    if todo_file.exists():
        return json.loads(todo_file.read_text())
    return {"p0_tasks": [], "p1_tasks": [], "completed_today": []}

def save_todo(todo):
    """保存待办状态"""
    todo_file = SCHEDULER / "daily-todo.json"
    todo_file.write_text(json.dumps(todo, indent=2, ensure_ascii=False))

def scan_evo_tasks():
    """扫描evo目录，返回任务列表"""
    tasks = {"p0": [], "p1": [], "p2": []}
    
    if not EVO_DIR.exists():
        return tasks
    
    for f in EVO_DIR.glob("evo-*.md"):
        content = f.read_text()
        task_id = f.stem
        
        # 简单解析优先级和状态
        priority = "p2"
        if "P0" in content or "优先级: 0" in content:
            priority = "p0"
        elif "P1" in content or "优先级: 1" in content:
            priority = "p1"
        
        status = "pending"
        if "✅" in content or "状态: 完成" in content or "已完成" in content:
            status = "completed"
        elif "🚧" in content or "状态: 进行中" in content:
            status = "in_progress"
        
        tasks[priority].append({
            "id": task_id,
            "file": str(f),
            "status": status,
            "priority": priority
        })
    
    return tasks

def mark_task_completed(task_id, files_changed=None):
    """标记任务完成"""
    todo = load_todo()
    
    # 从待办移到已完成
    for p in ["p0_tasks", "p1_tasks", "p2_tasks"]:
        for task in todo.get(p, []):
            if task["id"] == task_id:
                todo[p].remove(task)
                task["completed_at"] = datetime.now().isoformat()
                task["files_changed"] = files_changed or []
                todo["completed_today"].append(task)
                break
    
    save_todo(todo)
    
    # 更新evo文件状态
    evo_file = EVO_DIR / f"{task_id}.md"
    if evo_file.exists():
        content = evo_file.read_text()
        if "状态:" in content:
            content = content.replace("状态: 待开始", "状态: 已完成")
            content = content.replace("状态: 进行中", "状态: 已完成")
        elif "**状态**" in content:
            content = content.replace("**状态**: 待开始", "**状态**: 已完成 ✅")
            content = content.replace("**状态**: 进行中", "**状态**: 已完成 ✅")
        evo_file.write_text(content)

def log_error(task_id, error_msg):
    """记录错误"""
    error_file = SCHEDULER / "errors" / f"{datetime.now():%Y%m%d_%H%M%S}_{task_id}.log"
    error_file.write_text(f"""
Task: {task_id}
Time: {datetime.now()}
Error: {error_msg}
""")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    
    if cmd == "scan":
        tasks = scan_evo_tasks()
        todo = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "generated_at": datetime.now().strftime("%H:%M"),
            "p0_tasks": tasks["p0"],
            "p1_tasks": tasks["p1"],
            "p2_tasks": tasks["p2"],
            "completed_today": [],
            "failed_today": [],
            "stats": {
                "total_evo": len(tasks["p0"]) + len(tasks["p1"]) + len(tasks["p2"]),
                "completed": 0,
                "pending": len(tasks["p0"]) + len(tasks["p1"]) + len(tasks["p2"]),
                "completion_rate": 0
            }
        }
        save_todo(todo)
        print(f"发现 {todo['stats']['total_evo']} 个evo任务")
        print(f"  P0: {len(tasks['p0'])}, P1: {len(tasks['p1'])}, P2: {len(tasks['p2'])}")
    
    elif cmd == "complete":
        task_id = sys.argv[2]
        files = sys.argv[3:] if len(sys.argv) > 3 else None
        mark_task_completed(task_id, files)
        print(f"已标记 {task_id} 为完成")
    
    else:
        print(f"未知命令: {cmd}")
        print("用法: evo_executor.py [scan|complete TASK_ID]")
