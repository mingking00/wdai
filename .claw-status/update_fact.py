#!/usr/bin/env python3
"""
时态记忆维护工具

功能：
1. 检查事实有效性
2. 更新验证日期
3. 列出即将过期的事实

使用方式：
    python3 update_fact.py check "Railway"        # 检查事实
    python3 update_fact.py expiring               # 列出即将过期
    python3 update_fact.py verify "Railway"       # 更新验证日期为今天
"""

import sys
import re
from datetime import datetime
from pathlib import Path


def get_memory_file() -> Path:
    """获取时态记忆文件路径"""
    return Path.home() / '.openclaw' / 'workspace' / 'memory' / 'core' / 'temporal_facts.md'


def check_fact(keyword: str):
    """检查事实有效性"""
    sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / '.claw-status'))
    from temporal_memory import check_fact_validity
    
    is_valid, days = check_fact_validity(keyword)
    
    if days is None:
        print(f"'{keyword}': {'✅ 有效' if is_valid else '❌ 无效'} (永久有效)")
    elif days < 0:
        print(f"'{keyword}': ❌ 已过期 ({abs(days)} 天前)")
    else:
        print(f"'{keyword}': {'✅ 有效' if is_valid else '❌ 无效'} (剩余 {days} 天)")


def list_expiring(days: int = 7):
    """列出即将过期的事实"""
    sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / '.claw-status'))
    from temporal_memory import list_expiring_facts
    
    facts = list_expiring_facts(days)
    
    if not facts:
        print(f"✅ 未来 {days} 天内没有即将过期的事实")
        return
    
    print(f"⚠️  未来 {days} 天内过期的事实:")
    for f in facts:
        print(f"  - {f['content'][:50]}... ({f['days_remaining']}天, 置信度: {f['confidence']:.2f})")


def verify_fact(keyword: str):
    """更新事实的验证日期为今天"""
    memory_file = get_memory_file()
    
    if not memory_file.exists():
        print(f"❌ 记忆文件不存在: {memory_file}")
        return
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找包含关键词的行
    lines = content.split('\n')
    found = False
    today = datetime.now().strftime('%Y-%m-%d')
    
    for i, line in enumerate(lines):
        if keyword.lower() in line.lower() and line.strip().startswith('- ['):
            # 检查是否已有 [checked: ...]
            if '[checked:' in line:
                # 替换日期
                lines[i] = re.sub(r'\[checked:\s*\d{4}-\d{2}-\d{2}\]', f'[checked: {today}]', line)
            else:
                # 添加 [checked: today]
                lines[i] = line.rstrip() + f' [checked: {today}]'
            
            found = True
            print(f"✅ 已更新验证日期: {line[:60]}...")
            break
    
    if not found:
        print(f"❌ 未找到包含 '{keyword}' 的事实")
        return
    
    # 写回文件
    with open(memory_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ 已保存到: {memory_file}")


def show_help():
    """显示帮助信息"""
    print("""
时态记忆维护工具

用法:
    python3 update_fact.py check <keyword>      # 检查事实有效性
    python3 update_fact.py expiring [days]     # 列出即将过期的事实
    python3 update_fact.py verify <keyword>    # 更新验证日期为今天
    python3 update_fact.py help                # 显示帮助

示例:
    python3 update_fact.py check Railway
    python3 update_fact.py expiring 7
    python3 update_fact.py verify "Claude API"
    """)


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command == 'check':
        if len(sys.argv) < 3:
            print("Usage: python3 update_fact.py check <keyword>")
            return
        check_fact(sys.argv[2])
    
    elif command == 'expiring':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        list_expiring(days)
    
    elif command == 'verify':
        if len(sys.argv) < 3:
            print("Usage: python3 update_fact.py verify <keyword>")
            return
        verify_fact(sys.argv[2])
    
    elif command == 'help':
        show_help()
    
    else:
        print(f"❌ 未知命令: {command}")
        show_help()


if __name__ == "__main__":
    main()
