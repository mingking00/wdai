#!/usr/bin/env python3
"""
通用执行中间层 (Universal Execution Middleware)

拦截所有工具调用，自动添加创新能力
"""

import functools
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Callable
from datetime import datetime

CLAW = Path("/root/.openclaw/workspace/.claw-status")
EXEC_LOG = CLAW / "universal_exec_log.jsonl"

class UniversalExecutor:
    """通用执行器 - 拦截所有操作"""
    
    def __init__(self):
        self.method_stats = {}
        self.patterns = []
        self._load_stats()
    
    def _load_stats(self):
        stats_file = CLAW / "universal_method_stats.json"
        if stats_file.exists():
            with open(stats_file) as f:
                self.method_stats = json.load(f)
    
    def _save_stats(self):
        stats_file = CLAW / "universal_method_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.method_stats, f, indent=2)
    
    def _log_execution(self, tool: str, method: str, success: bool, 
                       error: str = None, duration_ms: float = 0):
        """记录执行日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool,
            "method": method,
            "success": success,
            "error": error,
            "duration_ms": duration_ms
        }
        with open(EXEC_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def execute(self, tool: str, method: str, execute_fn: Callable,
                fallbacks: List[Callable] = None, 
                verify_fn: Callable = None) -> Dict[str, Any]:
        """
        通用执行 - 带自动创新
        
        Args:
            tool: 工具名称 (exec, browser, etc.)
            method: 方法标识
            execute_fn: 主执行函数
            fallbacks: 备选函数列表
            verify_fn: 验证函数
        """
        key = f"{tool}:{method}"
        
        # 尝试1: 主方法
        print(f"[执行] {key}")
        start = time.time()
        
        try:
            result = execute_fn()
            duration = (time.time() - start) * 1000
            
            # 验证
            if verify_fn:
                verified = verify_fn(result)
                if not verified:
                    raise Exception("验证失败")
            
            self._record_success(key, duration)
            self._log_execution(tool, method, True, duration_ms=duration)
            
            return {"success": True, "result": result, "method": key}
            
        except Exception as e:
            duration = (time.time() - start) * 1000
            error = str(e)
            self._record_failure(key, error)
            self._log_execution(tool, method, False, error, duration)
            
            # 自动换路
            if fallbacks:
                return self._try_fallbacks(tool, method, fallbacks, verify_fn)
            
            return {"success": False, "error": error, "method": key}
    
    def _record_success(self, key: str, duration_ms: float):
        if key not in self.method_stats:
            self.method_stats[key] = {"attempts": 0, "successes": 0, "failures": 0}
        self.method_stats[key]["attempts"] += 1
        self.method_stats[key]["successes"] += 1
        self.method_stats[key]["last_success"] = datetime.now().isoformat()
        self._save_stats()
    
    def _record_failure(self, key: str, error: str):
        if key not in self.method_stats:
            self.method_stats[key] = {"attempts": 0, "successes": 0, "failures": 0}
        self.method_stats[key]["attempts"] += 1
        self.method_stats[key]["failures"] += 1
        self.method_stats[key]["last_error"] = error
        self._save_stats()
    
    def _try_fallbacks(self, tool: str, method: str, 
                       fallbacks: List[Callable], verify_fn) -> Dict:
        """尝试备选方案"""
        for i, fallback in enumerate(fallbacks, 2):
            fb_key = f"{method}_fallback_{i-1}"
            print(f"[自动换路] 尝试备选方案 {i-1}/{len(fallbacks)}: {fb_key}")
            
            try:
                result = fallback()
                
                if verify_fn:
                    verified = verify_fn(result)
                    if not verified:
                        continue
                
                self._record_success(fb_key, 0)
                return {
                    "success": True, 
                    "result": result, 
                    "method": fb_key,
                    "note": f"自动换路: {method} → {fb_key}"
                }
            except Exception as e:
                self._record_failure(fb_key, str(e))
        
        return {"success": False, "error": "所有方法都失败"}


# ===== 装饰器模式 - 自动拦截 =====

def auto_innovate(tool: str, method: str, fallbacks: List[Callable] = None, 
                  verify: Callable = None):
    """自动创新装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            executor = UniversalExecutor()
            
            def execute():
                return func(*args, **kwargs)
            
            return executor.execute(
                tool=tool,
                method=method,
                execute_fn=execute,
                fallbacks=fallbacks or [],
                verify_fn=verify
            )
        return wrapper
    return decorator


# ===== 具体应用示例 =====

def example_git_push():
    """Git推送示例"""
    import subprocess
    
    executor = UniversalExecutor()
    
    def push_https():
        result = subprocess.run(
            ["git", "push", "https://github.com/mingking00/wdai.git", "master"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        return result.stdout
    
    def push_ssh():
        subprocess.run(
            ["git", "remote", "set-url", "origin", 
             "git@github.com:mingking00/wdai.git"],
            check=True, capture_output=True
        )
        result = subprocess.run(
            ["git", "push", "origin", "master"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        return result.stdout
    
    def verify_push(output):
        result = subprocess.run(
            ["git", "status"], capture_output=True, text=True
        )
        return "up to date" in result.stdout or "up-to-date" in result.stdout
    
    return executor.execute(
        tool="exec",
        method="git_push",
        execute_fn=push_https,
        fallbacks=[push_ssh],
        verify_fn=verify_push
    )


def example_web_fetch():
    """网页抓取示例 - 自动换源"""
    
    executor = UniversalExecutor()
    
    def fetch_primary():
        # 主方法: 直接抓取
        import urllib.request
        return urllib.request.urlopen("https://example.com", timeout=10).read()
    
    def fetch_with_proxy():
        # 备选1: 使用代理
        import urllib.request
        proxy = urllib.request.ProxyHandler({'http': 'proxy:8080'})
        opener = urllib.request.build_opener(proxy)
        return opener.open("https://example.com", timeout=10).read()
    
    def fetch_from_cache():
        # 备选2: 从缓存读取
        cache_file = Path("/tmp/cache/example.html")
        if cache_file.exists():
            return cache_file.read_bytes()
        raise Exception("缓存不存在")
    
    return executor.execute(
        tool="web",
        method="fetch",
        execute_fn=fetch_primary,
        fallbacks=[fetch_with_proxy, fetch_from_cache]
    )


if __name__ == "__main__":
    # 演示
    print("=" * 60)
    print("通用执行中间层")
    print("=" * 60)
    
    result = example_git_push()
    print(f"\n结果: {result}")
