#!/usr/bin/env python3
"""
SEA自动进化演示 - 测试系统改进流程
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/system-evolution-agent')

from sea_service import submit_improvement_request, submit_analysis_request, get_response
import time

print("=" * 70)
print("🔧 SEA (System Evolution Agent) 自动进化演示")
print("=" * 70)
print()

# 1. 提交分析请求
print("📊 步骤1: 提交系统分析请求...")
analysis_req = submit_analysis_request()
print(f"   请求ID: {analysis_req}")
print()

# 2. 提交改进请求
print("📈 步骤2: 提交系统改进请求...")
test_code = '''
def example_function():
    """示例函数 - 需要优化错误处理"""
    try:
        result = risky_operation()
        return result
    except:
        return None  # 需要更好的错误处理
'''

improve_req = submit_improvement_request(
    description="优化错误处理，添加详细异常信息和日志",
    changes={
        "test_module.py": test_code
    }
)
print(f"   请求ID: {improve_req}")
print()

# 3. 等待并显示结果
print("⏳ 步骤3: 等待处理结果...")
print()

# 检查分析结果
print("   检查分析结果:")
for i in range(5):
    response = get_response(analysis_req, timeout=5)
    if response:
        result = response.get('result', {})
        if result.get('success'):
            analysis = result.get('result', {})
            print(f"   ✅ 分析完成!")
            print(f"      发现: {len(analysis.get('findings', []))} 个问题")
            print(f"      建议: {len(analysis.get('suggestions', []))} 条")
        break
    else:
        print(f"   ... 等待中 ({i+1}/5)")
    time.sleep(2)

print()
print("=" * 70)
print("✅ SEA自动进化系统已启动并运行")
print("=" * 70)
print()
print("📋 可用命令:")
print("   seas.sh status     - 查看服务状态")
print("   seas.sh logs       - 查看运行日志")
print("   seas.sh analyze    - 运行系统分析")
print("   seas.sh improve    - 提交改进请求")
print("   seas.sh ier-stats  - 查看IER统计")
print("=" * 70)
