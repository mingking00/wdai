#!/usr/bin/env python3
"""
Auto-Tool Wrapper - 工具调用自动包装器
自动执行创新机制：失败计数、3次锁定、强制换路
"""

import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# 添加路径
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

try:
    from innovation_trigger import record_failure, check_innovation_required, reset_counter
except ImportError:
    print("⚠️ innovation_trigger 未找到，创新机制不可用")
    def record_failure(m, t): return {"count": 0, "trigger": False}
    def check_innovation_required(m, t): return False
    def reset_counter(m, t): pass

# 方法识别映射
METHOD_MAPPING = {
    # Web/API 工具
    "web_search": ["web_search", "kimi_search", "search"],
    "web_fetch": ["web_fetch", "kimi_fetch", "fetch", "curl", "wget"],
    "github_api": ["github", "gh ", "git push", "git pull", "api.github.com"],
    
    # 文件工具
    "file_write": ["write", ">", ">>", "tee", "cat >"],
    "file_read": ["read", "cat ", "head ", "tail ", "less "],
    "file_edit": ["edit", "sed", "awk", "patch"],
    
    # 执行工具
    "bash_exec": ["bash", "sh ", "exec", "python3", "node", "npm"],
    "docker": ["docker", "kubectl", "helm"],
    
    # 网络工具
    "ssh": ["ssh", "scp", "rsync"],
    "database": ["psql", "mysql", "mongo", "redis"],
    
    # 其他
    "browser": ["browser", "agent-browser", "playwright"],
    "message": ["message", "send", "notify"],
}

def detect_method(command_or_tool):
    """从命令或工具名识别方法类型"""
    cmd_lower = command_or_tool.lower()
    
    for method, patterns in METHOD_MAPPING.items():
        for pattern in patterns:
            if pattern in cmd_lower:
                return method
    
    # 默认分类
    if any(x in cmd_lower for x in ["python", "py", ".py"]):
        return "python_exec"
    if any(x in cmd_lower for x in ["node", "js", ".js", "npm"]):
        return "node_exec"
    
    return "generic_exec"

def detect_task(command):
    """从命令提取任务标识"""
    # 使用命令的前50个字符作为任务标识
    task_id = command[:50].replace(" ", "_").replace("/", "_")
    return task_id

def auto_exec(command, task_hint=None, timeout=60, **kwargs):
    """
    自动执行命令，集成创新机制
    
    使用方式:
        result = auto_exec("git push origin main", task_hint="deploy_blog")
        if result["innovation_triggered"]:
            print("必须换方法！")
    
    返回值:
        {
            "success": bool,
            "stdout": str,
            "stderr": str,
            "method": str,
            "task": str,
            "failure_count": int,
            "innovation_triggered": bool,
            "locked": bool
        }
    """
    method = detect_method(command)
    task = task_hint or detect_task(command)
    
    # 检查是否被锁定
    if check_innovation_required(method, task):
        return {
            "success": False,
            "stdout": "",
            "stderr": f"🔒 方法 '{method}' 已失败3次，被强制锁定！必须换路。",
            "method": method,
            "task": task,
            "failure_count": 3,
            "innovation_triggered": True,
            "locked": True
        }
    
    # 执行命令
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            **kwargs
        )
        
        success = result.returncode == 0
        
        # 自动记录结果
        if success:
            reset_counter(method, task)
            failure_count = 0
            innovation_triggered = False
        else:
            record_result = record_failure(method, task)
            failure_count = record_result["count"]
            innovation_triggered = record_result["trigger"]
        
        return {
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "method": method,
            "task": task,
            "failure_count": failure_count,
            "innovation_triggered": innovation_triggered,
            "locked": False
        }
        
    except subprocess.TimeoutExpired:
        record_result = record_failure(method, task)
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "method": method,
            "task": task,
            "failure_count": record_result["count"],
            "innovation_triggered": record_result["trigger"],
            "locked": False
        }
    except Exception as e:
        record_result = record_failure(method, task)
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "method": method,
            "task": task,
            "failure_count": record_result["count"],
            "innovation_triggered": record_result["trigger"],
            "locked": False
        }

def auto_tool_call(tool_name, params, task_hint=None):
    """
    自动工具调用包装器（用于OpenClaw工具）
    
    由于无法真正拦截工具调用，这里提供标准化的调用后检查
    
    使用方式:
        # 在工具调用后手动调用（当前方案）
        result = auto_tool_call("web_search", {"query": "AI"}, "research_task")
        if result["should_innovate"]:
            print("必须换方法！")
    """
    method = detect_method(tool_name)
    task = task_hint or tool_name
    
    # 检查是否被锁定
    if check_innovation_required(method, task):
        return {
            "should_innovate": True,
            "locked": True,
            "message": f"🔒 工具 '{tool_name}' 已失败3次，被强制锁定！",
            "alternative_suggestions": suggest_alternatives(method)
        }
    
    return {
        "should_innovate": False,
        "locked": False,
        "method": method,
        "task": task
    }

def suggest_alternatives(method):
    """提供替代方案建议"""
    alternatives = {
        "web_search": ["kimi_search", "browser + 抓取", "RSS feed"],
        "web_fetch": ["kimi_fetch", "browser snapshot", "curl with retry"],
        "github_api": ["git CLI", "GitHub CLI (gh)", "本地文件操作后手动上传"],
        "bash_exec": ["python脚本", "docker容器", "远程服务器执行"],
        "docker": ["podman", "本地执行", "云服务"],
        "ssh": ["ansible", "本地执行", "云IDE"],
    }
    return alternatives.get(method, ["尝试完全不同的方法", "分解任务", "寻求用户输入"])

def report_tool_result(tool_name, success, error_msg=None, task_hint=None):
    """
    工具调用后报告结果，自动记录
    
    这是当前最实用的方案：每次工具调用后手动调用此函数
    """
    method = detect_method(tool_name)
    task = task_hint or tool_name
    
    if success:
        reset_counter(method, task)
        return {
            "recorded": True,
            "action": "reset",
            "failure_count": 0
        }
    else:
        result = record_failure(method, task)
        return {
            "recorded": True,
            "action": "increment",
            "failure_count": result["count"],
            "innovation_triggered": result["trigger"],
            "message": f"⚠️ {method} 已失败 {result['count']} 次" + 
                      ("，强制换路！" if result["trigger"] else "")
        }

# 便捷函数
def check_before_exec(command, task_hint=None):
    """执行前检查，返回是否应该继续"""
    method = detect_method(command)
    task = task_hint or detect_task(command)
    
    if check_innovation_required(method, task):
        print(f"🔒 阻断！{method} 已失败3次，被锁定")
        print(f"   建议替代方案: {suggest_alternatives(method)}")
        return False
    return True

def log_after_exec(command, success, error=None, task_hint=None):
    """执行后记录"""
    result = report_tool_result(command, success, error, task_hint)
    if result.get("innovation_triggered"):
        print(f"🚨 创新触发！{result['message']}")
    return result

if __name__ == "__main__":
    # 测试
    print("=== Auto-Tool Wrapper 测试 ===")
    print()
    
    # 测试方法识别
    test_commands = [
        "web_search 'AI agents'",
        "git push origin main",
        "docker build -t app .",
        "python3 script.py"
    ]
    
    for cmd in test_commands:
        method = detect_method(cmd)
        print(f"命令: {cmd[:30]:30} -> 方法: {method}")
    
    print()
    print("=== 锁定状态检查 ===")
    
    # 检查 github_api 是否被锁定
    if check_innovation_required("github_api", "8423"):
        print("🔒 github_api 已被锁定，测试替代方案建议:")
        print(f"   {suggest_alternatives('github_api')}")
