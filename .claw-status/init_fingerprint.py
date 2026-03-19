#!/usr/bin/env python3
"""
自动初始化方法指纹系统
在每次会话开始时执行
"""

import sys
from pathlib import Path

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

try:
    from fingerprint_hooks import install_hooks
    from method_fingerprint import get_report
    
    # 安装钩子
    hook = install_hooks()
    
    # 显示当前指纹状态
    print("\n" + get_report())
    print("\n💡 提示: 系统将自动记录成功/失败模式，避免重复试错\n")
    
except Exception as e:
    print(f"⚠️ 方法指纹系统加载失败: {e}")
