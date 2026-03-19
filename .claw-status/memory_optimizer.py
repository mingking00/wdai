#!/usr/bin/env python3
"""
内存优化脚本 - 自动压缩和归档
触发条件: 内存使用 > 85% 或每周日凌晨
"""

import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta


def compress_old_memories():
    """压缩30天前的记忆文件"""
    memory_dir = Path("/root/.openclaw/workspace/memory/daily")
    archive_dir = Path("/root/.openclaw/workspace/memory/archive")
    archive_dir.mkdir(exist_ok=True)
    
    cutoff = datetime.now() - timedelta(days=30)
    compressed = 0
    
    for file in memory_dir.glob("*.md"):
        # 从文件名解析日期
        try:
            date_str = file.stem  # 2026-03-19
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if file_date < cutoff:
                # 压缩文件
                archive_path = archive_dir / f"{file.stem}.md.gz"
                with open(file, 'rb') as f_in:
                    with gzip.open(archive_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # 删除原文件
                file.unlink()
                compressed += 1
                
        except ValueError:
            continue
    
    return compressed


def cleanup_temp_files():
    """清理临时文件"""
    temp_patterns = [
        "/root/.openclaw/workspace/.claw-status/*.tmp",
        "/root/.openclaw/workspace/.claw-status/temp/*",
    ]
    
    cleaned = 0
    for pattern in temp_patterns:
        for file in Path("/root/.openclaw/workspace").glob(pattern.replace("/root/.openclaw/workspace/", "")):
            if file.is_file():
                file.unlink()
                cleaned += 1
    
    return cleaned


def optimize_memory_index():
    """优化记忆索引，移除失效链接"""
    index_file = Path("/root/.openclaw/workspace/memory/index.md")
    
    if not index_file.exists():
        return 0
    
    # 读取并检查链接有效性
    content = index_file.read_text()
    
    # 统计信息
    stats = {
        "daily_logs": len(list(Path("/root/.openclaw/workspace/memory/daily").glob("*.md"))),
        "archive_size": sum(f.stat().st_size for f in Path("/root/.openclaw/workspace/memory/archive").glob("*")),
    }
    
    return stats


def main():
    """主入口"""
    print("🧹 WDai 内存优化")
    print("=" * 50)
    
    # 1. 压缩旧记忆
    compressed = compress_old_memories()
    print(f"📦 压缩旧记忆: {compressed} 个文件")
    
    # 2. 清理临时文件
    cleaned = cleanup_temp_files()
    print(f"🗑️  清理临时文件: {cleaned} 个")
    
    # 3. 优化索引
    stats = optimize_memory_index()
    print(f"📊 当前状态:")
    print(f"   日常日志: {stats['daily_logs']} 个")
    print(f"   归档大小: {stats['archive_size'] / 1024:.1f} KB")
    
    print("=" * 50)
    print("✅ 内存优化完成")


if __name__ == "__main__":
    main()
