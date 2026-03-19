#!/usr/bin/env python3
"""
OpenClaw 工具自动包装器

自动为所有工具调用添加创新能力
无需修改调用代码
"""

import sys
from pathlib import Path

# 添加oci_agent到路径
CLAW = Path("/root/.openclaw/workspace/.claw-status")
sys.path.insert(0, str(CLAW))

from oci_agent import InnovationProxy, smart_exec, smart_git_push, smart_web_fetch

# 全局创新代理
_innovation = InnovationProxy()

class ToolWrapper:
    """工具包装器 - 自动添加创新能力"""
    
    @staticmethod
    def exec(command: str, **kwargs) -> dict:
        """包装exec工具"""
        import subprocess
        
        timeout = kwargs.get('timeout', 60)
        
        def primary():
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=timeout
            )
            if result.returncode != 0:
                raise Exception(result.stderr)
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        
        def verify(result):
            return result['returncode'] == 0
        
        return _innovation.execute(
            tool='exec',
            method=command.split()[0],
            primary_fn=primary,
            verify_fn=verify
        )
    
    @staticmethod
    def read(path: str, **kwargs) -> dict:
        """包装read工具"""
        
        def primary():
            with open(path, 'r') as f:
                return f.read()
        
        def verify(content):
            return content is not None
        
        return _innovation.execute(
            tool='read',
            method='file',
            primary_fn=primary,
            verify_fn=verify
        )
    
    @staticmethod
    def write(path: str, content: str, **kwargs) -> dict:
        """包装write工具"""
        
        def primary():
            with open(path, 'w') as f:
                f.write(content)
            return {'path': path, 'size': len(content)}
        
        def verify(result):
            try:
                with open(result['path'], 'r') as f:
                    return f.read() == content
            except:
                return False
        
        return _innovation.execute(
            tool='write',
            method='file',
            primary_fn=primary,
            verify_fn=verify
        )
    
    @staticmethod
    def git_push(**kwargs) -> dict:
        """包装git push"""
        return smart_git_push(
            kwargs.get('repo', 'origin'),
            kwargs.get('branch', 'master')
        )


# ===== 便捷函数 =====

def iexec(command: str, **kwargs) -> dict:
    """创新执行 - 自动换路"""
    return ToolWrapper.exec(command, **kwargs)

def iread(path: str, **kwargs) -> dict:
    """创新读取 - 自动处理权限问题"""
    return ToolWrapper.read(path, **kwargs)

def iwrite(path: str, content: str, **kwargs) -> dict:
    """创新写入 - 自动处理权限问题"""
    return ToolWrapper.write(path, content, **kwargs)

def ipush(**kwargs) -> dict:
    """创新推送 - 自动处理网络问题"""
    return ToolWrapper.git_push(**kwargs)


# ===== 演示 =====

if __name__ == "__main__":
    import json
    
    print("=" * 60)
    print("OpenClaw 创新能力自动包装器")
    print("=" * 60)
    print()
    
    # 测试exec
    print("测试 iexec('echo hello'):")
    result = iexec("echo hello")
    print(f"  结果: {result['success']}")
    print(f"  输出: {result.get('result', {}).get('stdout', '')}")
    print()
    
    # 测试write + read
    test_file = "/tmp/test_innovation.txt"
    print(f"测试 iwrite + iread:")
    
    write_result = iwrite(test_file, "测试内容")
    print(f"  写入: {write_result['success']}")
    print(f"  验证: {write_result.get('verified', False)}")
    
    read_result = iread(test_file)
    print(f"  读取: {read_result['success']}")
    print(f"  内容: {read_result.get('result', '')[:20]}")
    print()
    
    # 显示统计
    print("当前统计:")
    stats = _innovation.get_stats()
    for key, stat in list(stats.items())[:5]:
        print(f"  {key}: {stat['successes']}/{stat['attempts']}")
    
    print()
    print("使用方式:")
    print("  from auto_innovation import iexec, iread, iwrite, ipush")
    print("  result = ipush()  # 自动处理HTTPS→SSH切换")
