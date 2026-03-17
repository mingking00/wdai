#!/usr/bin/env python3
"""
cleanup.py - 清理过期的工作记录

只保留最近 N 天的记录，自动删除旧文件。
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
STATUS_DIR = WORKSPACE / ".claw-status"

def parse_date_from_filename(filename):
    """从文件名解析日期"""
    # 尝试提取日期格式: daily-check-YYYYMMDD.json 或 evolution-report-YYYYMMDD.md
    import re
    match = re.search(r'(\d{8})', filename)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y%m%d')
        except:
            pass
    return None

def cleanup_reports(days=10):
    """清理报告文件"""
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted = []
    kept = []
    
    # 清理 .claw-status/reports/ 目录
    reports_dir = STATUS_DIR / "reports"
    if reports_dir.exists():
        for subdir in ["daily", "weekly"]:
            subdir_path = reports_dir / subdir
            if not subdir_path.exists():
                continue
                
            for file in subdir_path.iterdir():
                if file.is_file():
                    file_date = parse_date_from_filename(file.name)
                    if file_date and file_date < cutoff_date:
                        file.unlink()
                        deleted.append(file.name)
                    else:
                        kept.append(file.name)
    
    # 清理 .learning/daily-checks/ 目录
    daily_checks_dir = WORKSPACE / ".learning" / "daily-checks"
    if daily_checks_dir.exists():
        for file in daily_checks_dir.iterdir():
            if file.is_file():
                file_date = parse_date_from_filename(file.name)
                if file_date and file_date < cutoff_date:
                    file.unlink()
                    deleted.append(file.name)
                else:
                    kept.append(file.name)
    
    # 清理 history.jsonl - 只保留最近 N 天的记录
    history_file = STATUS_DIR / "history.jsonl"
    if history_file.exists():
        temp_file = STATUS_DIR / "history.jsonl.tmp"
        kept_lines = []
        removed_count = 0
        
        with open(history_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    session = json.loads(line)
                    start_time = session.get('start_time', '')
                    if start_time:
                        try:
                            session_date = datetime.fromisoformat(start_time.replace('Z', '+00:00').replace('+00:00', ''))
                            if session_date >= cutoff_date:
                                kept_lines.append(line)
                            else:
                                removed_count += 1
                        except:
                            kept_lines.append(line)  # 保留无法解析的行
                    else:
                        kept_lines.append(line)
                except:
                    pass
        
        # 写回文件
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.writelines(kept_lines)
        
        temp_file.replace(history_file)
        
        if removed_count > 0:
            deleted.append(f"history.jsonl 中的 {removed_count} 条旧记录")
    
    return deleted, kept

def main():
    parser = argparse.ArgumentParser(description='清理旧的工作记录')
    parser.add_argument('--days', type=int, default=10, help='保留最近 N 天的记录')
    parser.add_argument('--dry-run', action='store_true', help='试运行，不实际删除')
    args = parser.parse_args()
    
    print(f"🧹 清理任务开始 (保留最近 {args.days} 天)")
    print("=" * 50)
    
    if args.dry_run:
        print("[试运行模式 - 不会实际删除文件]")
    
    deleted, kept = cleanup_reports(args.days)
    
    if deleted:
        print(f"\n🗑️  已删除 {len(deleted)} 项:")
        for item in deleted[:10]:  # 最多显示10项
            print(f"  - {item}")
        if len(deleted) > 10:
            print(f"  ... 还有 {len(deleted) - 10} 项")
    else:
        print("\n✅ 没有需要清理的旧记录")
    
    print(f"\n📦 保留 {len(kept)} 项")
    print("=" * 50)
    print("清理完成")

if __name__ == "__main__":
    main()
