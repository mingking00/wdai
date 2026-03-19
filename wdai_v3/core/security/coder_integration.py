"""
Security Agent 集成 - 与 Coder Agent 的整合
在代码生成后自动执行安全审查
"""

import asyncio
from typing import Optional
from dataclasses import dataclass

# 延迟导入避免循环依赖
def get_security_orchestrator():
    from wdai_v3.core.security import SecurityOrchestrator
    return SecurityOrchestrator()


@dataclass
class CoderSecurityResult:
    """Coder Agent 安全审查结果"""
    passed: bool
    report_markdown: str
    risk_score: float
    should_block: bool
    auto_fix_suggestions: list


class CoderSecurityIntegration:
    """
    Coder Agent 安全集成
    
    在代码生成流程中自动插入安全检查点:
    
    1. Coder 生成代码
    2. 调用 security_check() 
    3. 根据风险分数决定:
       - 低风险: 继续执行
       - 中风险: 警告但仍可继续
       - 高风险: 阻止，要求修复
    """
    
    # 风险阈值
    BLOCK_THRESHOLD = 0.7      # 超过此值阻止执行
    WARNING_THRESHOLD = 0.3    # 超过此值警告
    
    def __init__(self):
        self._orchestrator = None
    
    @property
    def orchestrator(self):
        if self._orchestrator is None:
            self._orchestrator = get_security_orchestrator()
        return self._orchestrator
    
    async def security_check(self, code: str, file_path: Optional[str] = None) -> CoderSecurityResult:
        """
        对 Coder 生成的代码执行安全检查
        
        Args:
            code: 生成的代码
            file_path: 可选的文件路径（用于上下文）
            
        Returns:
            CoderSecurityResult 包含审查结果和建议
        """
        context = {"file_path": file_path} if file_path else None
        
        # 执行安全审查
        report = await self.orchestrator.review(code, context)
        
        # 判断是否阻止
        should_block = (
            report.overall_risk > self.BLOCK_THRESHOLD or
            report.fast_result.has_critical
        )
        
        # 生成修复建议
        auto_fix_suggestions = self._generate_fixes(report)
        
        return CoderSecurityResult(
            passed=not should_block,
            report_markdown=report.to_markdown(),
            risk_score=report.overall_risk,
            should_block=should_block,
            auto_fix_suggestions=auto_fix_suggestions
        )
    
    async def quick_check(self, code: str) -> bool:
        """快速检查代码是否安全（用于内部循环）"""
        return await self.orchestrator.quick_check(code)
    
    def _generate_fixes(self, report) -> list:
        """根据报告生成修复建议"""
        fixes = []
        
        for finding in report.fast_result.findings:
            if finding.rule_id == "exec-user-input":
                fixes.append({
                    "line": finding.line_number,
                    "problem": "执行用户输入",
                    "fix": "使用参数化命令或白名单验证输入"
                })
            elif finding.rule_id == "sql-string-format":
                fixes.append({
                    "line": finding.line_number,
                    "problem": "SQL 字符串拼接",
                    "fix": "使用参数化查询 (parameterized queries)"
                })
            elif finding.rule_id == "hardcoded-secret":
                fixes.append({
                    "line": finding.line_number,
                    "problem": "硬编码凭据",
                    "fix": "使用环境变量或密钥管理服务"
                })
        
        return fixes


# 全局实例
coder_security = CoderSecurityIntegration()


async def check_code_security(code: str, file_path: Optional[str] = None) -> CoderSecurityResult:
    """
    便捷函数：检查代码安全
    
    使用示例:
        result = await check_code_security(generated_code, "api.py")
        if result.should_block:
            print("发现严重安全问题，已阻止执行")
            print(result.report_markdown)
    """
    return await coder_security.security_check(code, file_path)


# 装饰器模式 - 自动包装 Coder Agent 的代码生成
def with_security_check(func):
    """
    装饰器：自动对生成的代码执行安全检查
    
    使用示例:
        @with_security_check
        async def generate_code(self, task):
            # 生成代码...
            return code
    """
    async def wrapper(*args, **kwargs):
        # 执行原函数获取代码
        code = await func(*args, **kwargs)
        
        # 安全检查
        result = await check_code_security(code)
        
        if result.should_block:
            raise SecurityError(
                f"生成的代码存在严重安全问题（风险分数: {result.risk_score:.2f}），"
                f"已阻止执行。请修复以下问题后再试。\n\n"
                f"{result.report_markdown}"
            )
        
        return code
    
    return wrapper


class SecurityError(Exception):
    """安全错误异常"""
    pass


if __name__ == "__main__":
    # 测试
    test_code = """
import os

def process_user(user_input):
    # 危险代码
    os.system(f"echo {user_input}")
    return True
"""
    
    async def main():
        result = await check_code_security(test_code, "test.py")
        print(f"通过: {result.passed}")
        print(f"阻止: {result.should_block}")
        print(f"风险分数: {result.risk_score:.2f}")
        print("\n报告:")
        print(result.report_markdown)
    
    asyncio.run(main())
