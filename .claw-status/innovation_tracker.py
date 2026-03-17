#!/usr/bin/env python3
"""
Innovation Tracker - 创新追踪器（简化版）
每次工具调用后使用，自动记录失败/成功

使用方法:
    from innovation_tracker import track_tool
    
    # 工具调用后
    result = track_tool("web_search", success=True)  # 成功
    result = track_tool("web_search", success=False, error="timeout")  # 失败
    
    # 如果返回 locked=True，必须换方法
    if result.get("locked"):
        print("必须换方法！")
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from innovation_trigger import record_failure, check_innovation_required, reset_counter

# 常见工具到方法的映射
TOOL_MAP = {
    # 搜索
    "web_search": "web_search",
    "kimi_search": "web_search",
    "web_fetch": "web_fetch",
    "kimi_fetch": "web_fetch",
    
    # GitHub/Git
    "github": "github_api",
    "git": "github_api",
    
    # 执行
    "exec": "bash_exec",
    "bash": "bash_exec",
    
    # 浏览器
    "browser": "browser_automation",
    
    # 文件
    "read": "file_ops",
    "write": "file_ops",
    "edit": "file_ops",
}

def track_tool(tool_name, success, error=None, task_hint=None):
    """
    追踪工具调用结果
    
    Args:
        tool_name: 工具名 (如 "web_search", "exec")
        success: 是否成功
        error: 错误信息（失败时）
        task_hint: 任务标识（可选）
    
    Returns:
        {
            "method": 识别的方法,
            "count": 当前失败计数,
            "locked": 是否被锁定,
            "triggered": 是否触发创新（3次失败）,
            "message": 状态消息
        }
    """
    method = TOOL_MAP.get(tool_name, tool_name)
    task = task_hint or tool_name
    
    # 检查是否已锁定
    if check_innovation_required(method, task):
        return {
            "method": method,
            "count": 3,
            "locked": True,
            "triggered": True,
            "message": f"🔒 {method} 已锁定（3次失败），必须换方法！"
        }
    
    # 记录结果
    if success:
        reset_counter(method, task)
        return {
            "method": method,
            "count": 0,
            "locked": False,
            "triggered": False,
            "message": f"✅ {method} 成功，计数器重置"
        }
    else:
        result = record_failure(method, task)
        count = result["count"]
        triggered = result["trigger"]
        
        msg = f"⚠️ {method} 失败 ({count}/3)"
        if triggered:
            msg = f"🚨 {method} 已失败3次！强制锁定，必须换方法！"
        
        return {
            "method": method,
            "count": count,
            "locked": triggered,
            "triggered": triggered,
            "message": msg
        }

def check_tool(tool_name, task_hint=None):
    """检查工具是否可用（执行前调用）"""
    method = TOOL_MAP.get(tool_name, tool_name)
    
    # 检查所有该方法的记录（不限制task）
    from innovation_trigger import get_status
    state = get_status()
    
    max_count = 0
    for key, data in state.items():
        if method in key or key.endswith(f":{method}"):
            max_count = max(max_count, data.get('count', 0))
    
    if max_count >= 3:
        return {
            "can_use": False,
            "method": method,
            "count": max_count,
            "message": f"🔒 {method} 已锁定（{max_count}次失败），建议换用: {suggest_alternative(method)}"
        }
    
    return {
        "can_use": True,
        "method": method,
        "count": max_count,
        "message": f"✅ {method} 可用（失败计数: {max_count}/3）"
    }

def suggest_alternative(method):
    """建议替代方法"""
    alternatives = {
        "web_search": "kimi_search",
        "web_fetch": "browser + 抓取",
        "github_api": "git CLI 本地操作",
        "bash_exec": "Python脚本替代",
        "browser_automation": "API直接调用",
        "file_ops": "批量操作工具",
    }
    return alternatives.get(method, "完全不同的方法")

# 便捷函数
def ok(tool_name, task_hint=None):
    """标记工具调用成功"""
    return track_tool(tool_name, success=True, task_hint=task_hint)

def fail(tool_name, error=None, task_hint=None):
    """标记工具调用失败"""
    return track_tool(tool_name, success=False, error=error, task_hint=task_hint)

def status(tool_name=None):
    """查看状态"""
    from innovation_trigger import get_status
    state = get_status()
    
    if tool_name:
        method = TOOL_MAP.get(tool_name, tool_name)
        return {k: v for k, v in state.items() if method in k}
    return state

if __name__ == "__main__":
    print("=== Innovation Tracker 测试 ===\n")
    
    # 测试1: 成功
    print("测试1: 标记 web_search 成功")
    r = ok("web_search")
    print(f"  {r['message']}\n")
    
    # 测试2: 失败
    print("测试2: 标记 web_search 失败")
    r = fail("web_search", "timeout")
    print(f"  {r['message']}")
    print(f"  失败次数: {r['count']}")
    print(f"  是否锁定: {r['locked']}\n")
    
    # 测试3: 检查被锁定的 github_api
    print("测试3: 检查 github_api 状态")
    r = check_tool("github")
    print(f"  可用: {r['can_use']}")
    print(f"  消息: {r['message']}\n")
    
    # 测试4: 查看所有状态
    print("测试4: 当前所有锁定状态")
    all_status = status()
    if all_status:
        for key, data in all_status.items():
            locked = "🔒" if data['count'] >= 3 else "⚠️"
            print(f"  {locked} {key}: {data['count']}次失败")
    else:
        print("  暂无记录")
