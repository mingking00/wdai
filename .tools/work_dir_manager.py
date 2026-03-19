#!/usr/bin/env python3
"""
工作目录管理器 - 防止临时文件丢失

教训来源: 2026-03-16 B站字幕提取任务失败
- 问题: 转录结果保存在/tmp/，进程被杀后丢失
- 解决: 强制使用workspace/下的持久目录
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 获取workspace根目录
WORKSPACE = Path(__file__).parent.parent.resolve()
WORK_DIR = WORKSPACE / ".work"

def get_persistent_dir(task_name: str, create: bool = True) -> Path:
    """
    获取持久化工作目录
    
    禁止使用 /tmp/ 或 /var/tmp/，强制使用 workspace/.work/
    
    Args:
        task_name: 任务名称，用于创建子目录
        create: 是否自动创建目录
        
    Returns:
        Path: 持久化目录路径
        
    Example:
        >>> work_dir = get_persistent_dir("bilibili-subtitle")
        >>> output_file = work_dir / "segment_000.srt"
    """
    # 清理任务名称，确保可用作目录名
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in task_name)
    task_dir = WORK_DIR / safe_name
    
    if create:
        task_dir.mkdir(parents=True, exist_ok=True)
        # 创建.meta文件记录任务信息
        meta_file = task_dir / ".meta"
        if not meta_file.exists():
            meta_file.write_text(
                f"task: {task_name}\n"
                f"created: {datetime.now().isoformat()}\n"
                f"pid: {os.getpid()}\n",
                encoding='utf-8'
            )
    
    return task_dir

def check_path_persistent(path: str | Path) -> Dict[str, Any]:
    """
    检查路径是否是持久化路径
    
    Returns:
        {
            "is_persistent": bool,
            "warning": str | None,
            "suggested_path": Path | None
        }
    """
    path = Path(path).resolve()
    
    # 检查是否是临时目录
    temp_prefixes = ['/tmp', '/var/tmp', '/dev/shm']
    path_str = str(path)
    
    for prefix in temp_prefixes:
        if path_str.startswith(prefix):
            return {
                "is_persistent": False,
                "warning": f"⚠️ 禁止将结果保存在临时目录: {path}",
                "suggested_path": WORK_DIR / path.name
            }
    
    # 检查是否在workspace下
    try:
        path.relative_to(WORKSPACE)
        return {
            "is_persistent": True,
            "warning": None,
            "suggested_path": None
        }
    except ValueError:
        return {
            "is_persistent": False,
            "warning": f"⚠️ 路径不在workspace下，建议移动到: {WORK_DIR / path.name}",
            "suggested_path": WORK_DIR / path.name
        }

def append_result(output_file: Path, content: str, flush: bool = True):
    """
    追加保存结果到文件（实时持久化）
    
    用于长时间任务的分段保存，确保中断后可恢复
    
    Args:
        output_file: 输出文件路径
        content: 要追加的内容
        flush: 是否立即刷新到磁盘
    """
    # 检查路径
    check = check_path_persistent(output_file)
    if not check["is_persistent"]:
        print(f"❌ {check['warning']}")
        print(f"💡 建议路径: {check['suggested_path']}")
        output_file = check["suggested_path"]
    
    # 确保目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 追加写入
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(content)
        if flush:
            f.flush()
            os.fsync(f.fileno())
    
    print(f"✅ 已保存到: {output_file}")

def estimate_task_duration(num_segments: int, duration_per_segment: float) -> Dict[str, Any]:
    """
    预估任务耗时并给出建议
    
    Args:
        num_segments: 分段数量
        duration_per_segment: 每段预计耗时（分钟）
        
    Returns:
        {
            "total_minutes": float,
            "warning": str | None,
            "suggestions": list[str]
        }
    """
    total = num_segments * duration_per_segment
    
    if total <= 10:
        return {
            "total_minutes": total,
            "warning": None,
            "suggestions": []
        }
    elif total <= 15:
        return {
            "total_minutes": total,
            "warning": "⚠️ 任务预计10-15分钟，注意保存进度",
            "suggestions": ["每完成一段立即保存", "使用append模式追加"]
        }
    else:
        return {
            "total_minutes": total,
            "warning": f"⚠️ 任务预计{total:.0f}分钟，可能被系统清理！",
            "suggestions": [
                "缩短分段（减少单段时长）",
                "并行处理多个分段",
                "换更快的方法（如换更小的模型）",
                "使用分段实时保存机制"
            ]
        }

def recover_from_checkpoint(task_name: str) -> Optional[Path]:
    """
    从断点恢复任务
    
    检查是否存在未完成的任务，返回最后一个完成的文件
    
    Args:
        task_name: 任务名称
        
    Returns:
        最后一个完成的文件路径，如果没有则返回None
    """
    task_dir = get_persistent_dir(task_name, create=False)
    
    if not task_dir.exists():
        return None
    
    # 查找所有结果文件
    result_files = list(task_dir.glob("*.srt")) + list(task_dir.glob("*.txt"))
    
    if not result_files:
        return None
    
    # 按修改时间排序
    result_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    print(f"🔍 发现未完成的任务: {task_name}")
    print(f"📁 工作目录: {task_dir}")
    print(f"📄 最后完成: {result_files[0].name}")
    print(f"⏰ 修改时间: {datetime.fromtimestamp(result_files[0].stat().st_mtime)}")
    
    return result_files[0]

def cleanup_old_tasks(days: int = 7):
    """
    清理过期的任务目录
    
    Args:
        days: 保留天数，默认7天
    """
    if not WORK_DIR.exists():
        return
    
    cutoff = datetime.now().timestamp() - (days * 24 * 3600)
    
    for task_dir in WORK_DIR.iterdir():
        if not task_dir.is_dir():
            continue
            
        # 检查最后修改时间
        last_modified = max(
            (f.stat().st_mtime for f in task_dir.rglob("*") if f.is_file()),
            default=0
        )
        
        if last_modified < cutoff:
            print(f"🗑️ 清理过期任务: {task_dir.name}")
            import shutil
            shutil.rmtree(task_dir)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="工作目录管理器")
    parser.add_argument("--check", type=str, help="检查路径是否是持久化路径")
    parser.add_argument("--task", type=str, help="获取任务工作目录")
    parser.add_argument("--recover", type=str, help="从断点恢复任务")
    parser.add_argument("--cleanup", action="store_true", help="清理过期任务")
    
    args = parser.parse_args()
    
    if args.check:
        result = check_path_persistent(args.check)
        print(f"持久化: {'✅' if result['is_persistent'] else '❌'}")
        if result['warning']:
            print(f"警告: {result['warning']}")
        if result['suggested_path']:
            print(f"建议路径: {result['suggested_path']}")
    
    elif args.task:
        work_dir = get_persistent_dir(args.task)
        print(f"工作目录: {work_dir}")
    
    elif args.recover:
        last_file = recover_from_checkpoint(args.recover)
        if last_file:
            print(f"可恢复文件: {last_file}")
        else:
            print("无可恢复文件")
    
    elif args.cleanup:
        cleanup_old_tasks()
    
    else:
        parser.print_help()
