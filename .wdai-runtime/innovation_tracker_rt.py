#!/usr/bin/env python3
"""
wdai Runtime - Innovation Tracker Integration
将创新追踪机制集成到wdai Runtime中

实现:
- 每个Agent执行前检查方法锁定状态
- 失败自动记录到共享状态
- 3次失败自动锁定并阻断
- 与OpenClaw Plugin共享状态文件
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional

class InnovationTracker:
    """
    创新追踪器 - 集成到wdai Runtime
    与OpenClaw Plugin共享状态文件
    """
    
    # 工具名到方法类型的映射
    TOOL_METHOD_MAP = {
        "web_search": "web_search",
        "web_fetch": "web_fetch",
        "browser": "browser_automation",
        "exec": "bash_exec",
        "bash": "bash_exec",
        "read": "file_ops",
        "write": "file_ops",
        "edit": "file_ops",
        "pdf": "pdf_ops",
        "github": "github_api",
        "git": "github_api",
        "canvas": "canvas_ops",
        "cron": "cron_ops",
        "sessions": "sessions_ops",
        "nodes": "nodes_ops",
        "message": "message_ops",
    }
    
    def __init__(self, state_file: Path = None, max_failures: int = 3):
        # 与OpenClaw Plugin使用相同的状态文件
        if state_file is None:
            self.state_file = Path("/root/.openclaw/.claw-status/innovation_state.json")
        else:
            self.state_file = state_file
        self.max_failures = max_failures
        self._state_cache = {}
        self._last_load = 0
        
    def detect_method(self, tool_name: str) -> str:
        """检测工具对应的方法类型"""
        # 直接匹配
        if tool_name in self.TOOL_METHOD_MAP:
            return self.TOOL_METHOD_MAP[tool_name]
        
        # 关键词匹配
        if "github" in tool_name.lower() or "git" in tool_name.lower():
            return "github_api"
        if "search" in tool_name.lower():
            return "web_search"
        if "fetch" in tool_name.lower() or "curl" in tool_name.lower():
            return "web_fetch"
        if "browser" in tool_name.lower() or "page" in tool_name.lower():
            return "browser_automation"
        if "exec" in tool_name.lower() or "bash" in tool_name.lower() or "shell" in tool_name.lower():
            return "bash_exec"
            
        return tool_name
    
    def _load_state(self) -> Dict:
        """加载状态（带缓存）"""
        now = time.time()
        # 每1秒刷新缓存
        if now - self._last_load > 1 or not self._state_cache:
            try:
                if self.state_file.exists():
                    with open(self.state_file, 'r') as f:
                        self._state_cache = json.load(f)
                else:
                    self._state_cache = {}
                self._last_load = now
            except Exception as e:
                print(f"[InnovationTracker] Failed to load state: {e}")
                self._state_cache = {}
        return self._state_cache
    
    def _save_state(self, state: Dict):
        """保存状态"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            self._state_cache = state
            self._last_load = time.time()
        except Exception as e:
            print(f"[InnovationTracker] Failed to save state: {e}")
    
    def is_locked(self, method: str, task_hint: str = None) -> bool:
        """检查方法是否被锁定"""
        state = self._load_state()
        
        # 检查具体任务
        key = f"{task_hint}:{method}" if task_hint else method
        if key in state and state[key].get("count", 0) >= self.max_failures:
            return True
        
        # 检查该方法的所有记录
        for k, v in state.items():
            if k.endswith(f":{method}") and v.get("count", 0) >= self.max_failures:
                return True
                
        return False
    
    def record_failure(self, method: str, task_hint: str = None) -> Dict:
        """记录失败"""
        state = self._load_state()
        key = f"{task_hint}:{method}" if task_hint else method
        now = time.time()
        
        if key not in state:
            state[key] = {
                "count": 0,
                "firstFail": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
                "lastFail": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))
            }
        
        state[key]["count"] += 1
        state[key]["lastFail"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))
        
        self._save_state(state)
        
        return {
            "count": state[key]["count"],
            "locked": state[key]["count"] >= self.max_failures
        }
    
    def record_success(self, method: str, task_hint: str = None):
        """记录成功，重置计数器"""
        state = self._load_state()
        key = f"{task_hint}:{method}" if task_hint else method
        
        if key in state:
            del state[key]
            self._save_state(state)
            return True
        return False
    
    def check_before_execute(self, tool_name: str, task_hint: str = None) -> Optional[str]:
        """
        执行前检查
        返回: None表示允许执行，字符串表示阻断原因
        """
        method = self.detect_method(tool_name)
        
        if self.is_locked(method, task_hint):
            return f"🔒 {method} 已被锁定（{self.max_failures}次失败）。这是强制创新机制，必须换用其他方法！"
        
        return None
    
    def report_after_execute(self, tool_name: str, success: bool, error: str = None, task_hint: str = None) -> Dict:
        """
        执行后报告
        返回: {"count": int, "locked": bool, "message": str}
        """
        method = self.detect_method(tool_name)
        
        if success:
            self.record_success(method, task_hint)
            return {
                "count": 0,
                "locked": False,
                "message": f"✅ {method} 成功，计数器重置"
            }
        else:
            result = self.record_failure(method, task_hint)
            msg = f"⚠️ {method} 失败 ({result['count']}/{self.max_failures})"
            if result["locked"]:
                msg = f"🚨 {method} 已失败{self.max_failures}次！强制锁定，必须换方法！"
            
            return {
                "count": result["count"],
                "locked": result["locked"],
                "message": msg
            }
    
    def unlock(self, method: str = None, task_hint: str = None) -> bool:
        """手动解锁方法"""
        state = self._load_state()
        
        if method:
            key = f"{task_hint}:{method}" if task_hint else method
            if key in state:
                del state[key]
                self._save_state(state)
                print(f"[InnovationTracker] 🔓 Unlocked: {key}")
                return True
        else:
            # 解锁所有
            self._save_state({})
            print("[InnovationTracker] 🔓 All locks cleared")
            return True
        
        return False
    
    def get_locked_methods(self) -> List[str]:
        """获取所有被锁定的方法"""
        state = self._load_state()
        locked = []
        for key, data in state.items():
            if data.get("count", 0) >= self.max_failures:
                locked.append(key)
        return locked
    
    def force_check_and_reload(self) -> bool:
        """强制重新加载状态（解决缓存问题）"""
        self._state_cache = {}
        self._last_load = 0
        return True
        """获取当前锁定状态"""
        state = self._load_state()
        locked_methods = []
        warning_methods = []
        
        for key, data in state.items():
            count = data.get("count", 0)
            if count >= self.max_failures:
                locked_methods.append((key, count))
            elif count > 0:
                warning_methods.append((key, count))
        
        return {
            "locked": locked_methods,
            "warnings": warning_methods,
            "total": len(state)
        }

# 便捷函数
def get_tracker() -> InnovationTracker:
    """获取全局追踪器实例"""
    return InnovationTracker()

if __name__ == "__main__":
    print("=== Innovation Tracker for wdai Runtime ===")
    print()
    
    tracker = InnovationTracker()
    
    # 测试1: 检查状态
    print("测试1: 获取当前锁定状态")
    status = tracker.get_status()
    print(f"  锁定方法数: {len(status['locked'])}")
    print(f"  警告方法数: {len(status['warnings'])}")
    if status['locked']:
        for method, count in status['locked']:
            print(f"  🔒 {method}: {count}次失败")
    print()
    
    # 测试2: 执行前检查
    print("测试2: 执行前检查 github_api")
    result = tracker.check_before_execute("github")
    if result:
        print(f"  阻断: {result}")
    else:
        print(f"  ✅ 允许执行")
    print()
    
    # 测试3: 记录失败
    print("测试3: 记录 web_search 失败")
    result = tracker.report_after_execute("web_search", success=False, error="timeout")
    print(f"  {result['message']}")
    print(f"  计数: {result['count']}")
    print(f"  锁定: {result['locked']}")
    print()
    
    print("测试完成！")
