#!/usr/bin/env python3
"""
成长检查工具
- 检查当日成长记录
- 提醒执行内化流程
- 快速查看成长状态

用法:
    python3 growth_check.py              # 检查今日状态
    python3 growth_check.py --task-done  # 任务完成后触发
    python3 growth_check.py --weekly     # 周度内化检查
"""

import os
import sys
import glob
import argparse
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory" / "daily"
GROWTH_FILE = WORKSPACE / ".persona" / "system" / "GROWTH.md"


def get_today_file():
    """获取今日记忆文件路径"""
    today = datetime.now().strftime("%Y-%m-%d")
    return MEMORY_DIR / f"{today}.md"


def count_growth_records(filepath):
    """统计成长记录数量"""
    if not filepath.exists():
        return 0
    content = filepath.read_text(encoding='utf-8')
    return content.count("## 成长记录")


def check_today_status():
    """检查今日成长状态"""
    today_file = get_today_file()
    record_count = count_growth_records(today_file)
    
    print("=" * 50)
    print(f"📊 成长状态检查 - {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 50)
    
    if record_count == 0:
        print("⚠️  今日暂无成长记录")
        print("   建议: 完成当前任务后执行成长检查")
    else:
        print(f"✅ 今日已有 {record_count} 条成长记录")
    
    # 检查本周
    week_count = 0
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        file_path = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        if file_path.exists():
            week_count += count_growth_records(file_path)
    
    print(f"📈 本周累计: {week_count} 条成长记录")
    
    # 检查是否该做周度内化
    if datetime.now().weekday() == 6:  # 周日
        print("🔄 今天是周日，建议执行周度内化流程")
        print("   查看: .persona/system/GROWTH.md")
    
    print("=" * 50)
    return record_count


def task_done_checklist():
    """任务完成后的检查清单"""
    print("\n" + "=" * 50)
    print("✅ 任务完成 - 成长检查清单")
    print("=" * 50)
    
    checklist = [
        ("关键决策", "做了什么选择？为什么？"),
        ("错误/纠正", "犯了什么错？怎么解决的？"),
        ("意外发现", "有什么超出预期的收获？"),
        ("用户偏好", "用户表达了什么偏好/习惯？"),
        ("模式识别", "这个任务和以前哪个类似？"),
        ("资产沉淀", "产出了什么可复用的？"),
        ("记忆更新", "是否更新了MEMORY/USER？"),
        ("预测未来", "下次可以做得更好的？"),
    ]
    
    for i, (title, desc) in enumerate(checklist, 1):
        print(f"\n{i}. {title}")
        print(f"   {desc}")
    
    print("\n" + "=" * 50)
    print("💡 记录方式:")
    print(f"   追加到: {get_today_file()}")
    print("   模板: .persona/system/GROWTH.md")
    print("=" * 50)


def weekly_internalization():
    """周度内化检查"""
    print("\n" + "=" * 50)
    print("🔄 周度内化流程")
    print("=" * 50)
    
    # 收集本周记录
    week_records = []
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        file_path = MEMORY_DIR / f"{date.strftime('%Y-%m-%d')}.md"
        if file_path.exists():
            count = count_growth_records(file_path)
            if count > 0:
                week_records.append((date.strftime('%Y-%m-%d'), count))
    
    if not week_records:
        print("⚠️  本周暂无成长记录，无法执行内化")
        return
    
    print(f"\n📋 本周成长记录 ({len(week_records)} 天):")
    for date, count in week_records:
        print(f"   {date}: {count} 条")
    
    print("\n🔄 内化步骤:")
    steps = [
        "回顾本周所有成长记录",
        "提炼跨任务的通用原则",
        "验证这些原则是否成立",
        "固化到 memory/core/principles.md",
        "更新 SOUL.md (如必要)",
    ]
    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step}")
    
    print("\n✅ 内化完成后:")
    print("   - 原则被验证并固化")
    print("   - 技能被改进或新增")
    print("   - 本能反应更加准确")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description='成长检查工具')
    parser.add_argument('--task-done', action='store_true', 
                       help='任务完成后显示检查清单')
    parser.add_argument('--weekly', action='store_true',
                       help='执行周度内化检查')
    args = parser.parse_args()
    
    if args.task_done:
        task_done_checklist()
    elif args.weekly:
        weekly_internalization()
    else:
        check_today_status()


if __name__ == "__main__":
    main()
