#!/usr/bin/env python3
"""
Auto-Learn Hook - 自动学习记录系统
在工具调用失败/用户纠正时自动触发
"""

import json
import sys
from datetime import datetime
from pathlib import Path

LEARNINGS_DIR = Path("/root/.openclaw/workspace/.learnings")

def log_error(tool_name: str, error_msg: str, context: str = ""):
    """自动记录错误"""
    error_file = LEARNINGS_DIR / "ERRORS.md"
    
    entry = f"""
## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **工具**: {tool_name}
- **错误**: {error_msg}
- **上下文**: {context or 'N/A'}
- **状态**: 待分析

"""
    
    with open(error_file, "a", encoding="utf-8") as f:
        f.write(entry)
    
    print(f"📝 错误已记录到 ERRORS.md: {tool_name}")

def log_learning(category: str, fact: str, source: str = "auto"):
    """自动记录学习"""
    learning_file = LEARNINGS_DIR / "LEARNINGS.md"
    
    entry = f"""
## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **类型**: {category}
- **内容**: {fact}
- **来源**: {source}
- **验证状态**: 待验证

"""
    
    with open(learning_file, "a", encoding="utf-8") as f:
        f.write(entry)
    
    print(f"📝 学习已记录到 LEARNINGS.md: {category}")

def log_correction(original: str, correction: str, context: str = ""):
    """记录用户纠正"""
    log_learning(
        category="用户纠正",
        fact=f"原理解: {original} → 纠正: {correction}",
        source="user_correction"
    )

def review_and_promote():
    """每日回顾：检查是否有可提升到 SOUL.md/AGENTS.md 的学习"""
    errors = parse_errors()
    learnings = parse_learnings()
    
    # 统计模式
    error_patterns = {}
    for e in errors:
        key = e['tool']
        error_patterns[key] = error_patterns.get(key, 0) + 1
    
    # 出现3次以上的错误 → 需要系统级修复
    frequent_errors = {k: v for k, v in error_patterns.items() if v >= 3}
    
    return {
        "total_errors": len(errors),
        "total_learnings": len(learnings),
        "frequent_errors": frequent_errors,
        "recommendations": generate_recommendations(errors, learnings)
    }

def parse_errors():
    """解析错误记录"""
    error_file = LEARNINGS_DIR / "ERRORS.md"
    if not error_file.exists():
        return []
    
    # 简单解析，实际可改进
    content = error_file.read_text()
    # 返回最近10条
    return [{"tool": "extracted", "error": "parsed"}]  # 简化版

def parse_learnings():
    """解析学习记录"""
    learning_file = LEARNINGS_DIR / "LEARNINGS.md"
    if not learning_file.exists():
        return []
    return []

def generate_recommendations(errors, learnings):
    """生成改进建议"""
    return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: auto_learn.py [error|learning|correction|review] ...")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "error" and len(sys.argv) >= 4:
        log_error(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "learning" and len(sys.argv) >= 4:
        log_learning(sys.argv[2], sys.argv[3])
    elif cmd == "correction" and len(sys.argv) >= 4:
        log_correction(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "review":
        result = review_and_promote()
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown command: {cmd}")
