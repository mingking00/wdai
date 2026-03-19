#!/usr/bin/env python3
"""
OpenClaw 创新能力代理层 (OCI-Agent)

在Agent级别实现系统性创新能力
无需修改OpenClaw核心
"""

import json
import functools
import time
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional
from datetime import datetime

# 配置
CLAW = Path("/root/.openclaw/workspace/.claw-status")
INNOVATION_DB = CLAW / "innovation_patterns.json"
EXEC_LOG = CLAW / "innovation_exec_log.jsonl"

class InnovationProxy:
    """创新能力代理 - 拦截工具调用"""
    
    def __init__(self):
        self.patterns = {}
        self.stats = {}
        self._load_data()
    
    def _load_data(self):
        if INNOVATION_DB.exists():
            with open(INNOVATION_DB) as f:
                data = json.load(f)
                self.patterns = data.get('patterns', {})
                self.stats = data.get('stats', {})
    
    def _save_data(self):
        with open(INNOVATION_DB, 'w') as f:
            json.dump({
                'patterns': self.patterns,
                'stats': self.stats,
                'updated': datetime.now().isoformat()
            }, f, indent=2, default=str)
    
    def _log(self, tool: str, method: str, success: bool, 
             error: str = None, duration_ms: float = 0, metadata: dict = None):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'tool': tool,
            'method': method,
            'success': success,
            'error': error,
            'duration_ms': duration_ms,
            'metadata': metadata or {}
        }
        with open(EXEC_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def execute(self, tool: str, method: str, 
                primary_fn: Callable, 
                fallback_fns: List[Callable] = None,
                verify_fn: Callable = None,
                context: dict = None) -> Dict[str, Any]:
        """
        执行带创新的操作
        
        Args:
            tool: 工具名称
            method: 方法标识
            primary_fn: 主执行函数
            fallback_fns: 备选函数列表
            verify_fn: 验证函数
            context: 上下文信息
        """
        key = f"{tool}:{method}"
        start = time.time()
        
        # 1. 尝试主方法
        try:
            result = primary_fn()
            duration = (time.time() - start) * 1000
            
            # 2. 验证
            if verify_fn:
                verified = verify_fn(result)
                if not verified:
                    raise Exception("验证失败")
            
            self._record_success(key, duration)
            self._log(tool, method, True, duration_ms=duration, 
                     metadata={'verified': True})
            
            return {
                'success': True,
                'result': result,
                'method': key,
                'attempts': 1,
                'verified': True
            }
            
        except Exception as e:
            duration = (time.time() - start) * 1000
            error = str(e)
            self._record_failure(key, error)
            self._log(tool, method, False, error, duration)
            
            print(f"⚠️ {key} 失败: {error}")
            
            # 3. 自动尝试备选
            if fallback_fns:
                return self._try_fallbacks(tool, method, fallback_fns, 
                                          verify_fn, context)
            
            return {
                'success': False,
                'error': error,
                'method': key
            }
    
    def _try_fallbacks(self, tool: str, method: str,
                       fallbacks: List[Callable],
                       verify_fn: Callable,
                       context: dict) -> Dict[str, Any]:
        """尝试备选方案"""
        
        for i, fallback in enumerate(fallbacks, 2):
            fb_key = f"{method}_fallback_{i-1}"
            print(f"  🔄 自动换路: 尝试备选 {i-1}/{len(fallbacks)}...")
            
            try:
                result = fallback()
                
                if verify_fn:
                    verified = verify_fn(result)
                    if not verified:
                        print(f"  ⚠️ 备选 {i-1} 验证失败")
                        continue
                
                self._record_success(fb_key, 0)
                self._log(tool, fb_key, True, metadata={'fallback': True})
                
                return {
                    'success': True,
                    'result': result,
                    'method': fb_key,
                    'attempts': i,
                    'auto_fallback': True,
                    'from': f"{tool}:{method}",
                    'to': fb_key,
                    'verified': True
                }
                
            except Exception as e:
                self._record_failure(fb_key, str(e))
                self._log(tool, fb_key, False, str(e))
                print(f"  ❌ 备选 {i-1} 失败: {e}")
        
        return {
            'success': False,
            'error': '所有方法都失败',
            'attempts': len(fallbacks) + 1
        }
    
    def _record_success(self, key: str, duration_ms: float):
        if key not in self.stats:
            self.stats[key] = {'attempts': 0, 'successes': 0, 'failures': 0}
        self.stats[key]['attempts'] += 1
        self.stats[key]['successes'] += 1
        self.stats[key]['last_success'] = datetime.now().isoformat()
        self._save_data()
    
    def _record_failure(self, key: str, error: str):
        if key not in self.stats:
            self.stats[key] = {'attempts': 0, 'successes': 0, 'failures': 0}
        self.stats[key]['attempts'] += 1
        self.stats[key]['failures'] += 1
        self.stats[key]['last_error'] = error
        self._save_data()
    
    def get_stats(self) -> dict:
        return self.stats
    
    def generate_report(self) -> str:
        lines = ["# 创新能力执行报告", ""]
        lines.append(f"生成时间: {datetime.now().isoformat()}")
        lines.append("")
        
        lines.append("## 方法统计")
        for key, stat in self.stats.items():
            success_rate = stat['successes'] / stat['attempts'] * 100 if stat['attempts'] > 0 else 0
            lines.append(f"- {key}: {stat['successes']}/{stat['attempts']} ({success_rate:.1f}%)")
        
        return "\n".join(lines)


# ===== 便捷使用方式 =====

_innovation = InnovationProxy()

def with_innovation(tool: str, method: str, 
                   fallbacks: List[Callable] = None,
                   verify: Callable = None):
    """装饰器: 为函数添加创新能力"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def primary():
                return func(*args, **kwargs)
            
            return _innovation.execute(
                tool=tool,
                method=method,
                primary_fn=primary,
                fallback_fns=fallbacks or [],
                verify_fn=verify
            )
        return wrapper
    return decorator


# ===== 具体应用场景 =====

def smart_exec(command: str, fallbacks: List[str] = None, 
               timeout: int = 60) -> Dict[str, Any]:
    """
    智能执行shell命令，自动换路
    
    Args:
        command: 主命令
        fallbacks: 备选命令列表
        timeout: 超时时间
    """
    import subprocess
    
    def primary():
        result = subprocess.run(
            command, shell=True, capture_output=True, 
            text=True, timeout=timeout
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        return result.stdout
    
    def make_fallback(cmd):
        def fallback():
            result = subprocess.run(
                cmd, shell=True, capture_output=True,
                text=True, timeout=timeout
            )
            if result.returncode != 0:
                raise Exception(result.stderr)
            return result.stdout
        return fallback
    
    def verify(output):
        # 基础验证：有输出就算成功
        return output is not None
    
    fallback_fns = [make_fallback(cmd) for cmd in (fallbacks or [])]
    
    return _innovation.execute(
        tool='exec',
        method=command.split()[0],
        primary_fn=primary,
        fallback_fns=fallback_fns,
        verify_fn=verify
    )


def smart_git_push(repo: str = "origin", branch: str = "master") -> Dict[str, Any]:
    """智能git推送，自动处理网络问题"""
    import subprocess
    
    workspace = Path("/root/.openclaw/workspace")
    
    def push_https():
        result = subprocess.run(
            ["git", "push", f"https://github.com/mingking00/wdai.git", branch],
            cwd=workspace, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        return result.stdout
    
    def push_ssh():
        # 确保使用SSH remote
        subprocess.run(
            ["git", "remote", "set-url", "origin", "git@github.com:mingking00/wdai.git"],
            cwd=workspace, check=True, capture_output=True
        )
        result = subprocess.run(
            ["git", "push", repo, branch],
            cwd=workspace, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise Exception(result.stderr)
        return result.stdout
    
    def verify_push(output):
        result = subprocess.run(
            ["git", "status"], cwd=workspace,
            capture_output=True, text=True
        )
        return "up to date" in result.stdout or "up-to-date" in result.stdout
    
    return _innovation.execute(
        tool='git',
        method='push',
        primary_fn=push_https,
        fallback_fns=[push_ssh],
        verify_fn=verify_push
    )


def smart_web_fetch(url: str, fallbacks: List[str] = None) -> Dict[str, Any]:
    """智能网页抓取，自动换源"""
    import urllib.request
    import urllib.error
    
    def fetch_primary():
        return urllib.request.urlopen(url, timeout=10).read()
    
    def fetch_with_proxy():
        proxy = urllib.request.ProxyHandler({'http': 'proxy:8080'})
        opener = urllib.request.build_opener(proxy)
        return opener.open(url, timeout=10).read()
    
    def verify_content(data):
        return data and len(data) > 0
    
    fallback_fns = []
    if fallbacks:
        for fb_url in fallbacks:
            fallback_fns.append(lambda u=fb_url: urllib.request.urlopen(u, timeout=10).read())
    else:
        fallback_fns = [fetch_with_proxy]
    
    return _innovation.execute(
        tool='web',
        method='fetch',
        primary_fn=fetch_primary,
        fallback_fns=fallback_fns,
        verify_fn=verify_content
    )


# ===== 主入口 =====

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("OpenClaw 创新能力代理层 (OCI-Agent)")
        print()
        print("用法:")
        print("  python3 oci_agent.py git-push    # 智能git推送")
        print("  python3 oci_agent.py stats       # 查看统计")
        print("  python3 oci_agent.py report      # 生成报告")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "git-push":
        result = smart_git_push()
        print(json.dumps(result, indent=2))
    
    elif cmd == "stats":
        stats = _innovation.get_stats()
        print(json.dumps(stats, indent=2))
    
    elif cmd == "report":
        report = _innovation.generate_report()
        print(report)
        
        # 保存报告
        report_file = CLAW / "innovation_report.md"
        report_file.write_text(report)
        print(f"\n报告已保存: {report_file}")
    
    else:
        print(f"未知命令: {cmd}")
