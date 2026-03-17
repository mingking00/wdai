#!/usr/bin/env python3
"""
创新机制管理工具
解决当前机制不完善的问题：
1. 无法查看锁定状态
2. 无法手动解锁
3. 状态缓存不同步
"""

import json
import sys
from pathlib import Path

# 可能的状态文件位置
STATE_FILE_LOCATIONS = [
    Path("/root/.openclaw/.claw-status/innovation_state.json"),
    Path("/root/.openclaw/workspace/.claw-status/innovation_state.json"),
    Path(".claw-status/innovation_state.json"),
]

def find_state_files():
    """找到所有状态文件"""
    found = []
    for path in STATE_FILE_LOCATIONS:
        if path.exists():
            found.append(path)
    return found

def read_state(path: Path):
    """读取状态文件"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return {}

def write_state(path: Path, state: dict):
    """写入状态文件"""
    with open(path, 'w') as f:
        json.dump(state, f, indent=2)

def show_status():
    """显示当前锁定状态"""
    print("=== Innovation Tracker 状态 ===")
    print()
    
    files = find_state_files()
    if not files:
        print("⚠️  未找到状态文件")
        return
    
    for path in files:
        print(f"📁 {path}")
        state = read_state(path)
        
        if not state:
            print("   状态为空")
        else:
            locked = []
            warning = []
            for key, data in state.items():
                count = data.get("count", 0)
                if count >= 3:
                    locked.append((key, count))
                elif count > 0:
                    warning.append((key, count))
            
            if locked:
                print(f"   🔒 已锁定 ({len(locked)}个):")
                for key, count in locked:
                    print(f"      - {key}: {count}次失败")
            
            if warning:
                print(f"   ⚠️  警告 ({len(warning)}个):")
                for key, count in warning:
                    print(f"      - {key}: {count}次失败")
        print()

def unlock_method(method: str = None, all_methods: bool = False):
    """解锁方法"""
    files = find_state_files()
    if not files:
        print("⚠️  未找到状态文件")
        return
    
    for path in files:
        state = read_state(path)
        
        if all_methods:
            # 解锁所有
            write_state(path, {})
            print(f"✅ 已清空: {path}")
        elif method:
            # 解锁特定方法
            keys_to_remove = [k for k in state.keys() if method in k]
            for key in keys_to_remove:
                del state[key]
            write_state(path, state)
            print(f"✅ 已解锁 '{method}' 在 {path}")

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print(f"  {sys.argv[0]} status              # 查看锁定状态")
        print(f"  {sys.argv[0]} unlock [method]     # 解锁特定方法")
        print(f"  {sys.argv[0]} unlock --all        # 解锁所有方法")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        show_status()
    elif command == "unlock":
        if len(sys.argv) > 2 and sys.argv[2] == "--all":
            unlock_method(all_methods=True)
        elif len(sys.argv) > 2:
            unlock_method(method=sys.argv[2])
        else:
            print("请指定方法名或使用 --all")
            sys.exit(1)
    else:
        print(f"未知命令: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
