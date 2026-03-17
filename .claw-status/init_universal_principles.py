#!/usr/bin/env python3
"""
通用原则执行系统 - 自动初始化器
适用于所有Agent、所有任务类型
"""

import sys
import json
from pathlib import Path

# 添加到路径
CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

def initialize_universal_principles(agent_id: str = "default"):
    """
    初始化通用原则执行系统
    在每次会话启动时自动调用
    
    Args:
        agent_id: Agent标识符，用于多Agent场景
    """
    try:
        from universal_principle_engine import get_engine, initialize_all_agents
        
        # 加载指定Agent的引擎
        engine = get_engine(agent_id)
        
        # 同时初始化其他Agent
        other_agents = initialize_all_agents()
        
        # 输出状态
        summary = engine.get_summary()
        
        print(f"🔥 通用原则执行系统已激活 [Agent: {agent_id}]")
        print(f"   原则库: {summary['principles_loaded']}条")
        print(f"   追踪方法: {summary['methods_tracked']}个")
        
        if summary['locked_methods']:
            print(f"   ⚠️ 锁定方法: {len(summary['locked_methods'])}个")
            for m in summary['locked_methods'][:3]:
                print(f"      - {m}")
        
        if summary['total_violations'] > 0:
            print(f"   ⚠️ 历史违规: {summary['total_violations']}次")
        
        if other_agents and len(other_agents) > 1:
            print(f"   其他Agent: {len(other_agents)-1}个已同步")
        
        return True, summary
        
    except Exception as e:
        print(f"⚠️ 原则执行系统加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False, {}

def check_method_status(method_name: str, task_type: str = "unknown", agent_id: str = "default") -> dict:
    """
    检查方法状态（是否被锁定）
    在尝试方法前调用
    """
    try:
        from universal_principle_engine import get_engine
        
        engine = get_engine(agent_id)
        key = f"{task_type}:{method_name}"
        
        if key in engine.methods:
            record = engine.methods[key]
            if record.is_locked():
                return {
                    "locked": True,
                    "failures": record.failures,
                    "alternatives": engine._suggest_alternatives(method_name, task_type)
                }
        
        return {"locked": False}
        
    except Exception as e:
        return {"locked": False, "error": str(e)}

def record_attempt(method_name: str, success: bool, task_type: str = "unknown", 
                   error: str = "", agent_id: str = "default") -> dict:
    """
    记录方法执行结果
    """
    try:
        from universal_principle_engine import get_engine
        
        engine = get_engine(agent_id)
        
        # 先设置当前任务类型
        if engine.current_task is None:
            engine.current_task = {"type": task_type}
        
        result = engine.record_method_attempt(method_name, success, error)
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # 被直接运行时初始化
    import argparse
    
    parser = argparse.ArgumentParser(description="通用原则执行系统初始化")
    parser.add_argument("--agent", default="default", help="Agent ID")
    parser.add_argument("--check", help="检查方法是否被锁定")
    parser.add_argument("--task-type", default="unknown", help="任务类型")
    
    args = parser.parse_args()
    
    if args.check:
        # 检查方法状态
        status = check_method_status(args.check, args.task_type, args.agent)
        print(json.dumps(status, indent=2))
    else:
        # 初始化系统
        success, summary = initialize_universal_principles(args.agent)
        sys.exit(0 if success else 1)
