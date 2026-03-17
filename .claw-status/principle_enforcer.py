#!/usr/bin/env python3
"""
原则执行系统集成器
自动将所有检查点插入工作流
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from principle_engine import get_engine, pre_task_check, resolve_conflict, record_violation
from innovation_trigger import record_failure, check_innovation_required, reset_counter

class PrincipleEnforcer:
    """
    原则执行强制器
    自动包装所有操作，插入检查点
    """
    
    def __init__(self):
        self.engine = get_engine()
        self.current_task = None
        self.method_attempts = {}
    
    def before_task(self, task_description: str) -> dict:
        """
        任务启动前强制检查
        返回检查结果，决定是否继续
        """
        print(f"\n🔍 任务前检查: {task_description[:50]}...")
        
        # 1. 安全检查 (P0)
        if not self._safety_check(task_description):
            raise SecurityException("安全检查未通过")
        
        # 2. 执行原则引擎检查
        passed, checks = pre_task_check(task_description)
        
        print("   检查项:")
        for check in checks:
            print(f"     {check}")
        
        if not passed:
            raise PrincipleViolationException("任务前检查未通过")
        
        # 3. 记录当前任务
        self.current_task = {
            "description": task_description,
            "start_time": __import__('time').time(),
            "methods_used": []
        }
        
        return {"status": "approved", "checks": checks}
    
    def during_execution(self, method_name: str, attempt: int = 1) -> dict:
        """
        执行中检查
        自动检测是否需要触发创新
        """
        task_id = self._get_task_id()
        
        # 检查方法是否被锁定
        if check_innovation_required(method_name, task_id):
            print(f"\n🔒 方法锁定: {method_name} 已失败3次，强制换路！")
            return {
                "status": "BLOCKED",
                "reason": "MUST_INNOVATE",
                "message": f"方法 '{method_name}' 已失败3次，必须换完全不同的方法"
            }
        
        # 记录尝试
        self.method_attempts[method_name] = attempt
        
        return {"status": "CONTINUE"}
    
    def on_failure(self, method_name: str, error: str) -> dict:
        """
        方法失败时自动记录
        检测是否触发创新
        """
        task_id = self._get_task_id()
        
        # 记录失败
        result = record_failure(method_name, task_id)
        
        print(f"\n⚠️ 方法失败: {method_name}")
        print(f"   失败次数: {result['count']}")
        
        if result["trigger"]:
            print(f"\n🚨 强制创新触发！")
            print(f"   {method_name} 已失败{result['count']}次")
            print(f"   必须换完全不同的方法！")
            
            # 返回强制创新指令
            return {
                "status": "MUST_INNOVATE",
                "failed_method": method_name,
                "count": result["count"],
                "suggestions": self._generate_alternatives(method_name)
            }
        
        return {
            "status": "RETRY",
            "attempt": result["count"],
            "max_retries": 3
        }
    
    def on_success(self, method_name: str, output: any) -> dict:
        """
        方法成功时
        重置失败计数 + 验证结果
        """
        task_id = self._get_task_id()
        
        # 重置失败计数
        reset_counter(method_name, task_id)
        
        print(f"\n✅ 方法成功: {method_name}")
        
        # 验证结果
        if not self._verify_output(output):
            print("   ⚠️ 结果验证失败！")
            return {"status": "VERIFY_FAILED", "output": output}
        
        print("   ✓ 结果已验证")
        
        return {"status": "SUCCESS", "verified": True}
    
    def before_delivery(self, output: any) -> dict:
        """
        交付前强制检查
        """
        print(f"\n📦 交付前检查...")
        
        passed, failed = self.engine.pre_delivery_check(output)
        
        if not passed:
            print(f"   ❌ 检查未通过: {', '.join(failed)}")
            
            # 记录违规
            for item in failed:
                record_violation(item, "pre_delivery", severity=2)
            
            return {
                "status": "BLOCKED",
                "failed_checks": failed,
                "message": "交付前检查未通过，请修复后重试"
            }
        
        print("   ✓ 所有检查通过")
        return {"status": "APPROVED"}
    
    def resolve_principle_conflict(self, principles: list, context: dict) -> dict:
        """
        解决原则冲突
        """
        winner = resolve_conflict(context, principles)
        
        print(f"\n⚖️ 原则冲突解决:")
        print(f"   涉及原则: {', '.join(principles)}")
        print(f"   胜出原则: {winner.name} (权重: {winner.weight})")
        
        return {
            "winner": winner.name,
            "weight": winner.weight,
            "reason": f"权重优先: {winner.weight}"
        }
    
    def _safety_check(self, task: str) -> bool:
        """安全检查 (P0)"""
        unsafe_keywords = ['删除所有', '暴露密码', '发送给其他人', 'rm -rf /']
        return not any(kw in task.lower() for kw in unsafe_keywords)
    
    def _get_task_id(self) -> str:
        """获取当前任务ID"""
        if self.current_task:
            return hash(self.current_task["description"]) % 10000
        return "unknown"
    
    def _verify_output(self, output) -> bool:
        """验证输出结果"""
        # 简化验证：检查非空
        if output is None:
            return False
        if isinstance(output, str) and len(output) == 0:
            return False
        return True
    
    def _generate_alternatives(self, failed_method: str) -> list:
        """生成替代方案建议"""
        alternatives = {
            "github_api": [
                "使用 git push 直接推送",
                "使用 GitHub CLI (gh)",
                "使用 SSH 密钥认证",
                "让用户手动上传"
            ],
            "web_fetch": [
                "使用 curl 命令",
                "使用 wget",
                "使用浏览器自动化",
                "使用本地缓存"
            ],
            "npm_install": [
                "使用 yarn",
                "使用 pnpm",
                "使用本地离线包",
                "检查网络代理"
            ]
        }
        
        return alternatives.get(failed_method, [
            "尝试完全不同的工具",
            "换协议或认证方式",
            "分解任务步骤",
            "让用户手动操作部分"
        ])

# 装饰器版本（自动包装函数）
def enforce_principles(func):
    """
    原则执行装饰器
    自动在函数前后插入检查点
    
    用法:
        @enforce_principles
        def deploy_blog():
            # 部署逻辑
            pass
    """
    enforcer = PrincipleEnforcer()
    
    def wrapper(*args, **kwargs):
        task_name = func.__name__
        
        # 任务前检查
        enforcer.before_task(task_name)
        
        # 执行函数
        result = None
        try:
            result = func(*args, **kwargs)
            
            # 成功处理
            enforcer.on_success(task_name, result)
            
        except Exception as e:
            # 失败处理
            enforcer.on_failure(task_name, str(e))
            raise
        
        # 交付前检查
        enforcer.before_delivery(result)
        
        return result
    
    return wrapper

# 全局实例
_enforcer = None

def get_enforcer() -> PrincipleEnforcer:
    """获取原则执行器单例"""
    global _enforcer
    if _enforcer is None:
        _enforcer = PrincipleEnforcer()
    return _enforcer

# 便捷函数
def task_check(task: str) -> dict:
    """任务前检查"""
    return get_enforcer().before_task(task)

def execution_check(method: str, attempt: int = 1) -> dict:
    """执行中检查"""
    return get_enforcer().during_execution(method, attempt)

def failure_handler(method: str, error: str) -> dict:
    """失败处理"""
    return get_enforcer().on_failure(method, error)

def success_handler(method: str, output: any) -> dict:
    """成功处理"""
    return get_enforcer().on_success(method, output)

def delivery_check(output: any) -> dict:
    """交付前检查"""
    return get_enforcer().before_delivery(output)

# 异常类
class SecurityException(Exception):
    """安全异常"""
    pass

class PrincipleViolationException(Exception):
    """原则违规异常"""
    pass

if __name__ == "__main__":
    # 测试运行
    print("=" * 60)
    print("原则执行系统集成器测试")
    print("=" * 60)
    
    enforcer = get_enforcer()
    
    # 测试1: 任务前检查
    print("\n【测试1】任务前检查")
    result = enforcer.before_task("部署博客到GitHub")
    print(f"结果: {result['status']}")
    
    # 测试2: 执行中检查
    print("\n【测试2】执行中检查（新任务）")
    result = enforcer.during_execution("github_api", 1)
    print(f"状态: {result['status']}")
    
    # 测试3: 模拟3次失败
    print("\n【测试3】模拟3次失败触发创新")
    for i in range(1, 4):
        print(f"\n第{i}次失败:")
        result = enforcer.on_failure("github_api", "timeout")
        if result['status'] == 'MUST_INNOVATE':
            print(f"🚨 触发强制创新！")
            print(f"建议: {result['suggestions'][:2]}")
    
    # 测试4: 交付前检查
    print("\n【测试4】交付前检查")
    result = enforcer.before_delivery({"file": "page.tsx", "status": "ok"})
    print(f"结果: {result['status']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
