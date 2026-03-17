#!/usr/bin/env python3
"""
System Evolution Agent - 使用示例
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/system-evolution-agent')

from sea import improve_self, analyze_system, get_improvement_history

def example_safe_improvement():
    """
    示例：安全的系统改进
    这个示例会被通过
    """
    print("=" * 60)
    print("示例：添加一个新工具函数")
    print("=" * 60)
    
    new_code = '''#!/usr/bin/env python3
"""
新的工具模块 - 字符串处理
"""

def safe_truncate(text: str, max_length: int = 100) -> str:
    """
    安全截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        
    Returns:
        截断后的字符串
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化后的字符串 (如 "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
'''
    
    result = improve_self(
        description="添加字符串处理和文件大小格式化工具函数",
        changes={
            ".tools/string_utils.py": new_code
        }
    )
    
    print(f"\n结果: {'✓ 成功' if result['success'] else '✗ 失败'}")
    print(f"状态: {result['status']}")
    if 'review_score' in result:
        print(f"审查得分: {result['review_score']}")
    if 'backup_id' in result:
        print(f"备份ID: {result['backup_id']}")
    
    return result


def example_dangerous_code():
    """
    示例：危险的代码（会被拒绝）
    """
    print("\n" + "=" * 60)
    print("示例：尝试添加危险代码（会被拒绝）")
    print("=" * 60)
    
    dangerous_code = '''#!/usr/bin/env python3
import os

def cleanup_system():
    """清理系统"""
    # 危险！会删除文件
    os.system("rm -rf /tmp/*")
    eval("print('cleaned')")
'''
    
    result = improve_self(
        description="添加系统清理功能",
        changes={
            ".tools/cleanup.py": dangerous_code
        }
    )
    
    print(f"\n结果: {'✓ 成功' if result['success'] else '✗ 失败'}")
    print(f"状态: {result['status']}")
    
    if not result['success'] and 'review' in result:
        print("\n审查发现的问题:")
        for issue in result['review'].get('issues', []):
            print(f"  [{issue['severity']}] {issue['message']}")
    
    return result


def example_with_errors():
    """
    示例：语法错误的代码（会被拒绝）
    """
    print("\n" + "=" * 60)
    print("示例：语法错误的代码（会被拒绝）")
    print("=" * 60)
    
    buggy_code = '''#!/usr/bin/env python3
def broken_function(
    # 缺少右括号
    print("Hello"
    # 缩进错误
       return True
'''
    
    result = improve_self(
        description="添加有bug的函数",
        changes={
            ".tools/buggy.py": buggy_code
        }
    )
    
    print(f"\n结果: {'✓ 成功' if result['success'] else '✗ 失败'}")
    print(f"状态: {result['status']}")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SEA使用示例")
    parser.add_argument("example", choices=["safe", "dangerous", "buggy", "all"], 
                       help="选择示例: safe(安全), dangerous(危险), buggy(有bug), all(全部)")
    
    args = parser.parse_args()
    
    if args.example == "safe":
        example_safe_improvement()
    elif args.example == "dangerous":
        example_dangerous_code()
    elif args.example == "buggy":
        example_with_errors()
    elif args.example == "all":
        print("\n" + "=" * 60)
        print("运行所有示例")
        print("=" * 60)
        
        example_safe_improvement()
        example_dangerous_code()
        example_with_errors()
        
        print("\n" + "=" * 60)
        print("查看改进历史:")
        print("=" * 60)
        history = get_improvement_history()
        print(f"总共有 {len(history)} 次改进记录")
        for h in history[-3:]:  # 最近3条
            print(f"  - {h['id']}: {h['status']} ({h.get('review_score', 'N/A')}分)")
