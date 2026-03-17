#!/usr/bin/env python3
"""
原则执行系统自动启动器
在每次会话开始时自动加载
"""

import sys
import os
from pathlib import Path

# 添加到路径
CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

def initialize_principle_system():
    """
    初始化原则执行系统
    在每次会话启动时自动调用
    """
    try:
        from principle_engine import get_engine
        from innovation_trigger import get_status
        
        # 加载引擎（自动恢复状态）
        engine = get_engine()
        
        # 检查是否有锁定的方法
        locked_methods = []
        status = get_status()
        for key, data in status.items():
            if data.get("count", 0) >= 3:
                locked_methods.append(key)
        
        # 输出状态
        print("🔥 原则执行系统已自动加载")
        print(f"   引擎状态: 运行中")
        print(f"   锁定方法: {len(locked_methods)}个")
        
        if locked_methods:
            print("   ⚠️ 以下方法已被锁定（必须换路）:")
            for m in locked_methods[:3]:  # 最多显示3个
                print(f"      - {m}")
        
        # 违规统计
        analysis = engine.analyze_violations()
        if analysis["total_violations"] > 0:
            print(f"   ⚠️ 历史违规: {analysis['total_violations']}次")
        else:
            print("   ✓ 无历史违规")
        
        return True
        
    except Exception as e:
        print(f"⚠️ 原则执行系统加载失败: {e}")
        return False

def get_principle_summary():
    """获取原则执行系统摘要（用于状态显示）"""
    try:
        from innovation_trigger import get_status
        from principle_engine import get_engine
        
        status = get_status()
        locked = [k for k, v in status.items() if v.get("count", 0) >= 3]
        
        engine = get_engine()
        analysis = engine.analyze_violations()
        
        return {
            "active": True,
            "locked_methods": locked,
            "total_violations": analysis["total_violations"],
            "recommendations": analysis.get("recommendations", [])
        }
    except:
        return {"active": False, "error": "系统未加载"}

if __name__ == "__main__":
    # 被直接运行时初始化
    initialize_principle_system()
