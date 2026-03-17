#!/usr/bin/env python3
"""
记忆系统自动维护脚本
功能：压缩、归档、统计
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")


def scan_memories():
    """扫描所有记忆文件"""
    stats = {
        "total_files": 0,
        "by_type": {},
        "by_folder": {},
        "access_count_total": 0
    }
    
    for root, dirs, files in os.walk(MEMORY_DIR):
        # 跳过隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        folder = Path(root).relative_to(MEMORY_DIR)
        stats["by_folder"][str(folder)] = len(files)
        
        for file in files:
            if file.endswith('.md'):
                stats["total_files"] += 1
                filepath = Path(root) / file
                
                # 解析元数据
                meta = parse_metadata(filepath)
                if meta.get('type'):
                    stats["by_type"][meta.get('type')] = stats["by_type"].get(meta.get('type'), 0) + 1
                
                stats["access_count_total"] += meta.get('access_count', 0)
    
    return stats


def parse_metadata(filepath):
    """解析文件元数据"""
    meta = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # 只读前1000字符
            
            # 提取created
            match = re.search(r'created:\s*(\d{4}-\d{2}-\d{2})', content)
            if match:
                meta['created'] = match.group(1)
            
            # 提取type
            match = re.search(r'type:\s*(\w+)', content)
            if match:
                meta['type'] = match.group(1)
            
            # 提取access_count
            match = re.search(r'access_count:\s*(\d+)', content)
            if match:
                meta['access_count'] = int(match.group(1))
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    
    return meta


def archive_old_memories(days=30):
    """归档旧记忆"""
    short_term_dir = MEMORY_DIR / "short_term"
    archive_dir = short_term_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    cutoff_date = datetime.now() - timedelta(days=days)
    archived = 0
    
    for folder in short_term_dir.glob("2026-*"):
        if folder.is_dir():
            # 解析文件夹日期
            try:
                folder_date = datetime.strptime(folder.name, "%Y-%m")
                if folder_date < cutoff_date:
                    # 移动到归档
                    target = archive_dir / folder.name
                    if not target.exists():
                        os.rename(folder, target)
                        archived += 1
                        print(f"Archived: {folder.name}")
            except ValueError:
                continue
    
    return archived


def generate_report():
    """生成记忆系统报告"""
    stats = scan_memories()
    
    report = f"""# 记忆系统报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 统计概览

| 指标 | 数值 |
|------|------|
| 总文件数 | {stats['total_files']} |
| 总访问次数 | {stats['access_count_total']} |

## 按类型分布

| 类型 | 数量 |
|------|------|
"""
    
    for mem_type, count in sorted(stats['by_type'].items()):
        report += f"| {mem_type} | {count} |\n"
    
    report += "\n## 按文件夹分布\n\n| 文件夹 | 文件数 |\n|--------|--------|\n"
    
    for folder, count in sorted(stats['by_folder'].items()):
        report += f"| {folder} | {count} |\n"
    
    # 保存报告
    report_path = MEMORY_DIR / ".reports" / f"report_{datetime.now().strftime('%Y%m%d')}.md"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report saved: {report_path}")
    return report


def main():
    """主函数"""
    print("=" * 50)
    print("🧠 记忆系统自动维护")
    print("=" * 50)
    
    # 1. 扫描统计
    print("\n📊 扫描记忆文件...")
    stats = scan_memories()
    print(f"   发现 {stats['total_files']} 个记忆文件")
    
    # 2. 归档旧记忆
    print("\n📦 归档旧记忆...")
    archived = archive_old_memories()
    print(f"   归档了 {archived} 个文件夹")
    
    # 3. 生成报告
    print("\n📝 生成报告...")
    generate_report()
    
    print("\n✅ 维护完成!")


if __name__ == "__main__":
    main()
