#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from method_fingerprint import check_before_execute, get_fingerprint_system, record_execution
from fingerprint_hooks import FingerprintHook

print("=" * 60)
print("🧪 Method Fingerprint System 测试")
print("=" * 60)

hook = FingerprintHook()

# 测试场景1: 尝试已知失败的方法（应该被阻止）
print("\n【测试1】尝试已知失败的方法")
print("-" * 40)
method1 = {
    "tool": "message",
    "action": "send",
    "channel": "feishu",
    "filePath": "/tmp/test.png"
}
result1 = hook.before_tool_call("message", method1)
print(f"方法: message.send(channel='feishu')")
print(f"结果: {result1.get('should_proceed', True)}")
if not result1.get('should_proceed', True):
    print(f"🚫 已阻止: {result1.get('message', 'N/A')}")
if result1.get('alternative'):
    print(f"💡 建议替代: 使用cron任务")

# 测试场景2: 尝试成功的方法（应该建议复用）
print("\n【测试2】查找成功案例")
print("-" * 40)
method2 = {
    "tool": "cron",
    "action": "add",
    "session_target": "isolated"
}
result2 = check_before_execute("send_feishu_image", method2)
print(f"任务类型: send_feishu_image")
print(f"结果: {result2['action'].upper()}")
print(f"原因: {result2.get('reason', 'N/A')}")
if result2.get('suggested_params'):
    print(f"✅ 建议参数: {result2['suggested_params']}")
    print(f"📊 置信度: {result2.get('confidence', 0):.0%}")

# 测试场景3: 全新方法（没有历史记录）
print("\n【测试3】全新方法（无历史记录）")
print("-" * 40)
method3 = {
    "tool": "web_search",
    "query": "测试查询"
}
result3 = check_before_execute("unknown_task", method3)
print(f"任务类型: unknown_task")
print(f"结果: {result3['action'].upper()}")
print(f"原因: {result3.get('reason', 'N/A')}")

# 测试场景4: 记录新的执行结果
print("\n【测试4】记录执行结果")
print("-" * 40)

# 模拟一次成功的web搜索
record_execution(
    task_type="web_search",
    method={"tool": "web_search", "query": "AI agents 2026"},
    result={"success": True, "error": None},
    tokens=15000
)
print("✅ 已记录: web_search 成功 (15k tokens)")

# 模拟一次失败的web搜索（API限流）
record_execution(
    task_type="web_search",
    method={"tool": "web_search", "query": "大数据量查询"},
    result={"success": False, "error": "API rate limit exceeded"},
    tokens=5000
)
print("✅ 已记录: web_search 失败 (API限流)")

# 显示更新后的报告
print("\n" + "=" * 60)
print("📊 更新后的指纹报告")
print("=" * 60)
from method_fingerprint import get_report
print(get_report())

print("\n✅ 测试完成！")
