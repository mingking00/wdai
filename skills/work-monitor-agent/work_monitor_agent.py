#!/usr/bin/env python3
"""
work_monitor_agent.py - 工作监察 Agent 主程序

这个脚本作为独立的 Agent 运行，负责：
1. 监控工作状态
2. 生成报告
3. 发送提醒
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
STATUS_DIR = WORKSPACE / ".claw-status"

def read_current_status():
    """读取当前工作状态"""
    current_file = STATUS_DIR / "current.json"
    
    if not current_file.exists():
        return None
    
    try:
        with open(current_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def read_history(limit=10):
    """读取历史记录"""
    history_file = STATUS_DIR / "history.jsonl"
    
    if not history_file.exists():
        return []
    
    sessions = []
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    sessions.append(json.loads(line))
                except:
                    pass
    except:
        pass
    
    return sessions[-limit:]

def generate_status_report():
    """生成当前状态报告"""
    status = read_current_status()
    
    if not status:
        return "🤖 当前没有进行中的工作\n\n系统空闲，等待新任务。"
    
    report = []
    report.append("🤖 工作状态报告")
    report.append("=" * 50)
    report.append(f"\n📋 当前任务: {status.get('task_description', '未知')}")
    report.append(f"🆔 会话ID: {status.get('id', 'N/A')}")
    report.append(f"📊 状态: {status.get('status', 'unknown')}")
    
    # 进度
    total = status.get('total_steps', 0)
    completed = status.get('completed_steps', 0)
    if total > 0:
        pct = completed / total * 100
        report.append(f"📈 进度: {completed}/{total} ({pct:.0f}%)")
    
    report.append(f"🔄 当前步骤: {status.get('current_step', '无')}")
    
    # 耗时
    start_time = status.get('start_time')
    if start_time:
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            elapsed = datetime.now() - start
            report.append(f"⏱️  已耗时: {elapsed.seconds // 60} 分钟")
        except:
            pass
    
    # 产物
    artifacts = status.get('artifacts', [])
    if artifacts:
        report.append(f"\n📦 产物 ({len(artifacts)} 个):")
        for art in artifacts:
            report.append(f"  • {art.get('name', '未命名')}: {art.get('path', '无路径')}")
    
    # 最近日志
    logs = status.get('logs', [])
    if logs:
        report.append(f"\n📝 最近日志:")
        for log in logs[-3:]:
            msg = log.get('message', '')[:40]
            report.append(f"  • {log.get('type', 'log')}: {msg}")
    
    report.append("\n" + "=" * 50)
    
    return "\n".join(report)

def generate_daily_report():
    """生成今日日报"""
    history = read_history(20)
    today = datetime.now().date()
    
    # 筛选今日任务
    today_tasks = []
    for session in history:
        try:
            start = datetime.fromisoformat(session.get('start_time', '').replace('Z', '+00:00'))
            if start.date() == today:
                today_tasks.append(session)
        except:
            pass
    
    report = []
    report.append(f"📅 {today.strftime('%Y-%m-%d')} 工作日报")
    report.append("=" * 50)
    report.append(f"\n今日完成任务: {len(today_tasks)} 个")
    
    total_time = sum(s.get('elapsed_seconds', 0) for s in today_tasks)
    report.append(f"总工作时长: {total_time // 60} 分钟")
    
    if today_tasks:
        report.append("\n📋 任务列表:")
        for i, task in enumerate(reversed(today_tasks), 1):
            desc = task.get('task_description', '未命名任务')[:30]
            elapsed = task.get('elapsed_seconds', 0) // 60
            status = task.get('status', 'unknown')
            report.append(f"  {i}. {desc}... ({elapsed}分钟) - {status}")
        
        # 统计产物
        all_artifacts = []
        for task in today_tasks:
            all_artifacts.extend(task.get('artifacts', []))
        
        if all_artifacts:
            report.append(f"\n📦 今日产出 ({len(all_artifacts)} 个):")
            for art in all_artifacts[-5:]:
                report.append(f"  • {art.get('name', '未命名')}")
    else:
        report.append("\n今日暂无完成任务记录")
    
    report.append("\n" + "=" * 50)
    
    return "\n".join(report)

def check_alerts():
    """检查是否有需要提醒的事项"""
    status = read_current_status()
    alerts = []
    
    if not status:
        return alerts
    
    # 检查是否卡住太久
    if status.get('status') == 'waiting':
        try:
            start = datetime.fromisoformat(status.get('start_time', '').replace('Z', '+00:00'))
            elapsed = datetime.now() - start
            if elapsed > timedelta(minutes=30):
                alerts.append(f"⚠️ 任务 '{status.get('task_description', '未知')}' 已等待 {elapsed.seconds // 60} 分钟")
        except:
            pass
    
    return alerts

def check_and_report():
    """检查状态并返回报告和警告"""
    report = generate_status_report()
    alerts = check_alerts()
    return report, alerts

def generate_feishu_report():
    """生成适合飞书的日报格式"""
    history = read_history(20)
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # 筛选昨日任务（因为日报是早上8点发，统计前一天）
    yesterday_tasks = []
    for session in history:
        try:
            start = datetime.fromisoformat(session.get('start_time', '').replace('Z', '+00:00'))
            if start.date() == yesterday:
                yesterday_tasks.append(session)
        except:
            pass
    
    lines = []
    lines.append(f"📅 {yesterday.strftime('%Y-%m-%d')} 工作日报")
    lines.append("")
    
    total_time = sum(s.get('elapsed_seconds', 0) for s in yesterday_tasks)
    lines.append(f"完成任务: {len(yesterday_tasks)} 个")
    lines.append(f"总工作时长: {total_time // 60} 分钟")
    lines.append("")
    
    if yesterday_tasks:
        lines.append("📋 任务列表:")
        for i, task in enumerate(reversed(yesterday_tasks), 1):
            desc = task.get('task_description', '未命名任务')[:25]
            elapsed = task.get('elapsed_seconds', 0) // 60
            status = "✅" if task.get('status') == 'completed' else "⚠️"
            lines.append(f"{i}. {status} {desc}... ({elapsed}min)")
        
        # 统计产物
        all_artifacts = []
        for task in yesterday_tasks:
            all_artifacts.extend(task.get('artifacts', []))
        
        if all_artifacts:
            lines.append("")
            lines.append(f"📦 产出 ({len(all_artifacts)} 个):")
            for art in all_artifacts[-5:]:
                lines.append(f"  • {art.get('name', '未命名')}")
    else:
        lines.append("昨日暂无完成任务记录")
    
    # 检查当前进行中的任务
    current = read_current_status()
    if current and current.get('status') not in ['completed', 'error']:
        lines.append("")
        lines.append("🔄 当前进行中的任务:")
        lines.append(f"  {current.get('task_description', '未知')[:30]}...")
        lines.append(f"  进度: {current.get('completed_steps', 0)}/{current.get('total_steps', 0)}")
    
    return "\n".join(lines)

def main():
    """主函数 - 根据参数执行不同操作"""
    if len(sys.argv) < 2:
        # 默认：生成状态报告
        print(generate_status_report())
        return
    
    command = sys.argv[1]
    
    if command == "check":
        report, alerts = check_and_report()
        print(report)
        
        if alerts:
            print("\n🚨 需要关注:")
            for alert in alerts:
                print(f"  {alert}")
    
    elif command == "daily":
        print(generate_daily_report())
    
    elif command == "feishu":
        # 生成飞书格式的日报
        print(generate_feishu_report())
    
    elif command == "history":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        history = read_history(limit)
        
        print(f"📚 最近 {len(history)} 个工作会话")
        print("=" * 50)
        
        for i, session in enumerate(reversed(history), 1):
            desc = session.get('task_description', '未命名')[:40]
            status = session.get('status', 'unknown')
            elapsed = session.get('elapsed_seconds', 0)
            print(f"\n{i}. [{session.get('id', 'N/A')}] {desc}")
            print(f"   状态: {status} | 耗时: {elapsed:.0f}秒")
            print(f"   步骤: {session.get('completed_steps', 0)}/{session.get('total_steps', 0)}")
    
    else:
        print(f"未知命令: {command}")
        print("可用命令: check, daily, feishu, history [N]")

if __name__ == "__main__":
    main()
