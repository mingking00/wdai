#!/usr/bin/env python3
"""
执行验证闭环模板

任何操作都必须：执行 → 检查 → 验证 → 报告
"""

import subprocess
import time
from typing import Callable, Any, Tuple

def execute_with_verification(
    cmd: str,
    check_fn: Callable[[], Tuple[bool, str]],
    max_retries: int = 3,
    timeout: int = 30
) -> dict:
    """
    执行命令并验证结果
    
    Args:
        cmd: 要执行的命令
        check_fn: 验证函数，返回 (是否成功, 状态信息)
        max_retries: 最大重试次数
        timeout: 单次超时时间
    """
    for attempt in range(max_retries):
        print(f"\n[尝试 {attempt + 1}/{max_retries}] {cmd}")
        
        # 1. 执行
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, 
                text=True, timeout=timeout
            )
            print(f"  命令返回码: {result.returncode}")
            if result.stdout:
                print(f"  输出: {result.stdout[:200]}")
            if result.stderr:
                print(f"  错误: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ 命令超时")
            result = None
        except Exception as e:
            print(f"  ❌ 执行异常: {e}")
            result = None
        
        # 2. 等待系统稳定
        time.sleep(1)
        
        # 3. 验证结果（关键！）
        print(f"  [验证中...]")
        success, info = check_fn()
        
        if success:
            print(f"  ✅ 验证通过: {info}")
            return {
                "success": True,
                "attempts": attempt + 1,
                "info": info
            }
        else:
            print(f"  ❌ 验证失败: {info}")
            if attempt < max_retries - 1:
                print(f"  等待后重试...")
                time.sleep(2)
    
    return {
        "success": False,
        "attempts": max_retries,
        "error": "达到最大重试次数"
    }


# === Git Push 示例 ===
def git_push_with_auto_fallback():
    """Git推送并自动换路（HTTPS失败自动切SSH）"""
    
    def check_push_status():
        """检查推送是否成功"""
        result = subprocess.run(
            "git status", shell=True, capture_output=True, text=True
        )
        output = result.stdout
        
        if "ahead of" in output or "领先" in output:
            return False, "本地仍有commits未推送"
        elif "Your branch is up to date" in output or "up-to-date" in output:
            return True, "推送成功，本地与远程同步"
        elif "nothing to commit" in output:
            return True, "无变更需要推送"
        else:
            return False, f"未知状态: {output[:100]}"
    
    # 尝试1: HTTPS方式
    print("[尝试1] HTTPS推送...")
    result = execute_with_verification(
        cmd="git push https://github.com/mingking00/wdai.git master",
        check_fn=check_push_status,
        max_retries=2,
        timeout=30
    )
    
    if result["success"]:
        return result
    
    # 尝试2: 诊断网络并自动换路到SSH
    print("[自动换路] HTTPS失败，诊断网络...")
    
    # 检查443端口
    check_443 = subprocess.run(
        "timeout 5 bash -c 'exec 3<>/dev/tcp/github.com/443' 2>/dev/null && echo OK || echo FAIL",
        shell=True, capture_output=True, text=True
    )
    
    # 检查22端口
    check_22 = subprocess.run(
        "timeout 5 bash -c 'exec 3<>/dev/tcp/github.com/22' 2>/dev/null && echo OK || echo FAIL",
        shell=True, capture_output=True, text=True
    )
    
    if "OK" in check_22.stdout and "FAIL" in check_443.stdout:
        print("[自动换路] 443不通但22通，自动切换到SSH...")
        
        # 自动切换到SSH remote
        subprocess.run(
            "git remote set-url origin git@github.com:mingking00/wdai.git",
            shell=True, check=True
        )
        
        # SSH方式推送
        result = execute_with_verification(
            cmd="git push origin master",
            check_fn=check_push_status,
            max_retries=2,
            timeout=60
        )
        
        if result["success"]:
            result["note"] = "自动换路：HTTPS→SSH成功"
        
        return result
    
    # 都失败了，报告
    return {
        "success": False,
        "error": "HTTPS和SSH都失败，需要人工检查网络",
        "diagnosis": f"443: {check_443.stdout.strip()}, 22: {check_22.stdout.strip()}"
    }


# === 文件操作验证示例 ===
def write_file_with_verification(filepath: str, content: str):
    """写文件并验证"""
    
    def check_file_status():
        import os
        if not os.path.exists(filepath):
            return False, "文件不存在"
        
        with open(filepath, 'r') as f:
            actual = f.read()
        
        if actual == content:
            return True, f"文件内容正确 ({len(content)} 字节)"
        else:
            return False, f"内容不匹配: 期望{len(content)}字节, 实际{len(actual)}字节"
    
    # 先写文件
    with open(filepath, 'w') as f:
        f.write(content)
    
    # 再验证
    success, info = check_file_status()
    if not success:
        raise RuntimeError(f"文件写入验证失败: {info}")
    
    return True


if __name__ == "__main__":
    # 演示
    result = git_push_with_verification()
    print(f"\n最终结果: {result}")
