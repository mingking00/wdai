"""
wdai Security Agent - 代码安全审查模块

提供三层安全审查能力:
- L1: Fast Check - 毫秒级正则规则检查
- L2: Static Analysis - 静态代码分析  
- L3: AI Review - LLM 深度安全审查

使用示例:
    from wdai_v3.core.security import SecurityOrchestrator, review_code, check_code_security
    
    # 快速检查
    orchestrator = SecurityOrchestrator()
    report = await orchestrator.review(code)
    
    if not report.is_safe():
        print(report.to_markdown())
    
    # Coder Agent 集成
    result = await check_code_security(generated_code, "api.py")
    if result.should_block:
        print("发现安全问题，已阻止")
"""

from .fast_check import (
    FastCheck,
    FastCheckResult,
    SecurityFinding,
    SecurityRule,
    quick_security_check
)

from .security_orchestrator import (
    SecurityOrchestrator,
    SecurityReport,
    StaticAnalysisResult,
    AIReviewResult,
    create_security_orchestrator,
    review_code
)

from .coder_integration import (
    CoderSecurityIntegration,
    CoderSecurityResult,
    check_code_security,
    with_security_check,
    SecurityError
)

__all__ = [
    # Fast Check
    'FastCheck',
    'FastCheckResult', 
    'SecurityFinding',
    'SecurityRule',
    'quick_security_check',
    
    # Orchestrator
    'SecurityOrchestrator',
    'SecurityReport',
    'StaticAnalysisResult',
    'AIReviewResult',
    'create_security_orchestrator',
    'review_code',
    
    # Coder Integration
    'CoderSecurityIntegration',
    'CoderSecurityResult',
    'check_code_security',
    'with_security_check',
    'SecurityError'
]

__version__ = "0.1.0"
