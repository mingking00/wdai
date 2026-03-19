#!/usr/bin/env python3
"""
AI过载保护执行器
带本地队列和重试机制
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

QUEUE_FILE = Path("/root/.openclaw/workspace/.scheduler/queue.json")
MAX_RETRIES = 3
RETRY_DELAY_MINUTES = [5, 15, 60]  # 渐进式重试间隔


def load_queue():
    """加载任务队列"""
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE, 'r') as f:
            return json.load(f)
    return {"pending": [], "completed": [], "failed": []}


def save_queue(queue):
    """保存任务队列"""
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)


def add_task(task_type, params, priority=1):
    """添加任务到队列"""
    queue = load_queue()
    task = {
        "id": f"{task_type}_{int(time.time())}",
        "type": task_type,
        "params": params,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "retries": 0,
        "status": "pending"
    }
    queue["pending"].append(task)
    queue["pending"].sort(key=lambda x: x["priority"])
    save_queue(queue)
    print(f"✅ 任务已加入队列: {task['id']}")


def execute_with_fallback(task):
    """执行任务，带降级策略"""
    task_type = task["type"]
    params = task["params"]
    
    # 策略1: 尝试完整执行
    try:
        result = execute_full(task_type, params)
        if result["success"]:
            return result
    except Exception as e:
        print(f"⚠️ 完整执行失败: {e}")
    
    # 策略2: 降级执行（简化版）
    if task.get("retries", 0) >= 1:
        print("🔄 尝试降级执行...")
        try:
            result = execute_degraded(task_type, params)
            if result["success"]:
                return result
        except Exception as e:
            print(f"⚠️ 降级执行也失败: {e}")
    
    # 策略3: 仅记录，人工后续处理
    if task.get("retries", 0) >= 2:
        print("📝 记录到人工处理队列")
        return {"success": False, "status": "manual_review_needed"}
    
    raise Exception("所有执行策略都失败")


def execute_full(task_type, params):
    """完整执行（需要AI）"""
    if task_type == "external_loop":
        # 外部反馈循环
        cmd = [
            "python3", "auto_executor.py",
            "--force-external",
            "--chunk-size", str(params.get("chunk_size", 5))
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    
    elif task_type == "paper_study":
        # 论文学习
        cmd = ["python3", "auto_executor.py", "--mode", "single"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return {
            "success": result.returncode == 0,
            "output": result.stdout
        }
    
    return {"success": False, "error": "未知任务类型"}


def execute_degraded(task_type, params):
    """降级执行（减少AI依赖）"""
    if task_type == "external_loop":
        # 降级：只记录状态，不分析
        return {
            "success": True,
            "degraded": True,
            "output": "降级执行：仅记录状态，跳过深度分析"
        }
    
    elif task_type == "ai_news":
        # 降级：只拉取RSS，不生成总结
        return {
            "success": True,
            "degraded": True,
            "output": "降级执行：仅收集链接，未生成总结"
        }
    
    return {"success": False, "error": "无降级策略"}


def process_queue():
    """处理队列中的任务"""
    queue = load_queue()
    
    if not queue["pending"]:
        print("📭 队列为空")
        return
    
    print(f"📋 处理 {len(queue['pending'])} 个待处理任务")
    
    for task in queue["pending"][:]:  # 复制列表避免遍历时修改
        print(f"\n🔨 执行任务: {task['id']}")
        
        try:
            result = execute_with_fallback(task)
            
            if result["success"]:
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                task["result"] = result
                queue["completed"].append(task)
                print(f"✅ 任务完成{' (降级模式)' if result.get('degraded') else ''}")
            else:
                raise Exception(result.get("error", "未知错误"))
                
        except Exception as e:
            task["retries"] += 1
            task["last_error"] = str(e)
            task["last_attempt"] = datetime.now().isoformat()
            
            if task["retries"] >= MAX_RETRIES:
                task["status"] = "failed"
                queue["failed"].append(task)
                queue["pending"].remove(task)
                print(f"❌ 任务失败（已达最大重试次数）: {e}")
            else:
                # 计算下次重试时间
                delay = RETRY_DELAY_MINUTES[task["retries"] - 1]
                next_retry = datetime.now() + timedelta(minutes=delay)
                task["next_retry"] = next_retry.isoformat()
                print(f"⏳ 将在 {delay} 分钟后重试")
        
        # 保存进度
        save_queue(queue)
        
        # 任务间延迟，避免连续触发过载
        time.sleep(10)


def retry_failed_tasks():
    """重试失败的任务"""
    queue = load_queue()
    now = datetime.now()
    
    for task in queue["pending"]:
        if task.get("next_retry"):
            retry_time = datetime.fromisoformat(task["next_retry"])
            if now >= retry_time:
                print(f"🔄 重试任务: {task['id']}")
                # 会在 process_queue 中处理


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: executor_queue.py [process|retry|add]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "process":
        retry_failed_tasks()
        process_queue()
    elif action == "retry":
        retry_failed_tasks()
    elif action == "add" and len(sys.argv) >= 4:
        add_task(sys.argv[2], json.loads(sys.argv[3]))
    else:
        print("未知操作")
