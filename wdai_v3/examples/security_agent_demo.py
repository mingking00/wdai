"""
wdai Security Agent - P0 演示
展示 Fast Check + Orchestrator 的基础能力
"""

import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wdai_v3.core.security import (
    SecurityOrchestrator,
    review_code,
    check_code_security,
    quick_security_check
)


# 示例代码 - 干净代码
CLEAN_CODE = '''
def greet_user(name: str) -> str:
    """安全地向用户问好"""
    # 使用白名单验证
    allowed_names = ["Alice", "Bob", "Charlie"]
    if name not in allowed_names:
        return "Hello, guest!"
    return f"Hello, {name}!"
'''

# 示例代码 - 危险代码
DANGEROUS_CODE = '''
import os
import pickle

def process_request(user_input, user_data):
    """处理用户请求 - 包含多个安全问题"""
    # TODO: fix security vulnerability here
    
    # 1. 命令注入
    os.system(f"echo {user_input}")
    
    # 2. 反序列化漏洞  
    data = pickle.loads(user_data)
    
    # 3. 硬编码密码
    password = "super_secret_password_123"
    
    # 4. 关闭 SSL 验证
    import requests
    response = requests.get(url, verify=False)
    
    return data
'''

# 示例代码 - SQL 注入
SQL_INJECTION_CODE = '''
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # 危险的字符串拼接
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    return cursor.fetchone()
'''


async def demo_fast_check():
    """演示 Fast Check 能力"""
    print("=" * 60)
    print("🚀 P0 安全审查 Agent - Fast Check 演示")
    print("=" * 60)
    
    print("\n1️⃣ 干净代码检查")
    print("-" * 40)
    result = quick_security_check(CLEAN_CODE)
    print(f"✅ 风险分数: {result.risk_score:.2f}")
    print(f"✅ 发现问题: {len(result.findings)} 个")
    print(f"✅ 耗时: {result.elapsed_ms:.3f} ms")
    
    print("\n2️⃣ 危险代码检查")
    print("-" * 40)
    result = quick_security_check(DANGEROUS_CODE)
    print(f"🔴 风险分数: {result.risk_score:.2f}")
    print(f"🔴 发现问题: {len(result.findings)} 个")
    print(f"🔴 耗时: {result.elapsed_ms:.3f} ms")
    print("\n发现问题:")
    for f in result.findings:
        emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(f.severity, "⚪")
        print(f"  {emoji} [{f.severity.upper()}] 第{f.line_number}行: {f.message}")
    
    print("\n3️⃣ SQL 注入检查")
    print("-" * 40)
    result = quick_security_check(SQL_INJECTION_CODE)
    print(f"🟠 风险分数: {result.risk_score:.2f}")
    print(f"🟠 发现问题: {len(result.findings)} 个")
    print(f"🟠 耗时: {result.elapsed_ms:.3f} ms")


async def demo_orchestrator():
    """演示 Orchestrator 能力"""
    print("\n" + "=" * 60)
    print("🎯 Security Orchestrator 演示")
    print("=" * 60)
    
    orchestrator = SecurityOrchestrator()
    
    print("\n📋 对危险代码生成完整报告...")
    report = await orchestrator.review(DANGEROUS_CODE, {"file_path": "api.py"})
    
    print(f"\n📊 审查摘要:")
    print(f"  - 总体风险: {'🔴 极高' if report.overall_risk > 0.8 else '🟠 高' if report.overall_risk > 0.5 else '🟡 中'}")
    print(f"  - 风险分数: {report.overall_risk:.2f}")
    print(f"  - 是否安全: {'✅ 是' if report.is_safe() else '❌ 否'}")
    print(f"  - L1 发现: {len(report.fast_result.findings)} 个问题")
    print(f"  - L1 耗时: {report.fast_result.elapsed_ms:.3f} ms")
    
    print(f"\n💡 建议:")
    for rec in report.recommendations:
        print(f"  {rec}")
    
    # 保存完整报告
    report_path = Path(__file__).parent / "security_report_demo.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report.to_markdown())
    print(f"\n📝 完整报告已保存: {report_path}")


async def demo_coder_integration():
    """演示 Coder Agent 集成"""
    print("\n" + "=" * 60)
    print("🔧 Coder Agent 集成演示")
    print("=" * 60)
    
    from wdai_v3.core.security.coder_integration import check_code_security
    
    print("\n模拟 Coder Agent 生成代码后的安全检查...")
    result = await check_code_security(DANGEROUS_CODE, "api.py")
    
    print(f"\n📊 检查结果:")
    print(f"  - 是否通过: {'✅ 通过' if result.passed else '❌ 未通过'}")
    print(f"  - 风险分数: {result.risk_score:.2f}")
    print(f"  - 是否阻止: {'🚨 是' if result.should_block else '✋ 否'}")
    
    if result.auto_fix_suggestions:
        print(f"\n🔧 自动修复建议:")
        for fix in result.auto_fix_suggestions:
            print(f"  第{fix['line']}行: {fix['problem']}")
            print(f"    → {fix['fix']}")


async def demo_performance():
    """性能测试"""
    print("\n" + "=" * 60)
    print("⚡ 性能测试")
    print("=" * 60)
    
    import time
    
    # 测试 1000 行代码
    large_code = DANGEROUS_CODE * 100  # 约 1200 行
    
    start = time.perf_counter()
    result = quick_security_check(large_code)
    elapsed = (time.perf_counter() - start) * 1000
    
    print(f"\n代码规模: {len(large_code)} 字符, {result.checked_lines} 行")
    print(f"检查耗时: {elapsed:.3f} ms")
    print(f"发现问题: {len(result.findings)} 个")
    print(f"平均速度: {elapsed / result.checked_lines:.4f} ms/行")
    print(f"每秒可处理: {result.checked_lines / (elapsed/1000):.0f} 行")


async def main():
    """主演示"""
    print("\n" + "🛡️" * 30)
    print("  wdai Security Agent - P0 演示")
    print("  三层安全审查系统 (L1 已实现)")
    print("🛡️" * 30 + "\n")
    
    await demo_fast_check()
    await demo_orchestrator()
    await demo_coder_integration()
    await demo_performance()
    
    print("\n" + "=" * 60)
    print("✅ P0 演示完成")
    print("=" * 60)
    print("\n已实现:")
    print("  ✅ L1 - Fast Check (毫秒级正则检查)")
    print("  ✅ Security Orchestrator (三层协调)")
    print("  ✅ Coder Agent 集成")
    print("  ✅ 15+ 安全规则")
    print("\n待实现 (P1/P2):")
    print("  ⏳ L2 - Static Analysis (Semgrep)")
    print("  ⏳ L3 - AI Review (LLM 深度分析)")


if __name__ == "__main__":
    asyncio.run(main())
