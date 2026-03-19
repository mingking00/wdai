#!/usr/bin/env python3
"""
Universal Fingerprint System 使用示例
展示如何通用化地使用方法指纹
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from universal_fingerprint import check, execute, record, stats

print("=" * 60)
print("🌐 Universal Method Fingerprint System 演示")
print("=" * 60)

# === 示例1: 检查任意工具调用 ===
print("\n【示例1】检查各种工具调用")
print("-" * 40)

# 1.1 检查发飞书图片（已有成功记录）
result1 = check("cron", {
    "action": "add",
    "channel": "feishu",
    "payload": {"filePath": "/tmp/test.png"}
})
print(f"✓ send_feishu_image: {result1['message']}")

# 1.2 检查直接发消息（已知失败）
result2 = check("message", {
    "action": "send",
    "channel": "feishu",
    "filePath": "/tmp/test.png"
})
print(f"✗ message.send: {result2.get('message', 'N/A')[:50]}...")

# 1.3 检查全新的工具调用
result3 = check("browser", {
    "action": "navigate",
    "url": "https://example.com"
})
print(f"? browser.navigate: {result3['message']}")

# === 示例2: 模拟工具执行并记录 ===
print("\n【示例2】模拟执行并自动记录")
print("-" * 40)

# 模拟一次成功的 browser 调用
def mock_browser_navigate(url):
    """模拟浏览器导航"""
    return {"status": "success", "title": "Example Domain"}

result = execute(
    "browser",
    {"action": "navigate", "url": "https://example.com"},
    mock_browser_navigate,
    "https://example.com"
)

print(f"执行结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
print(f"是否复用指纹: {result['used_fingerprint']}")
print(f"估算Token: {result['tokens']}")

# === 示例3: 再次检查（现在有记录了）===
print("\n【示例3】再次检查（现在有历史记录）")
print("-" * 40)

result4 = check("browser", {
    "action": "navigate",
    "url": "https://another.com"
})
print(f"browser.navigate: {result4['message']}")

# === 示例4: 统计信息 ===
print("\n【示例4】系统统计")
print("-" * 40)

system_stats = stats()
print(f"任务类型总数: {system_stats['total_task_types']}")
print(f"成功模式数: {system_stats['total_success_patterns']}")
print(f"黑名单数: {system_stats['total_blacklisted']}")
print(f"\n已记录的任务类型:")
for task_type in system_stats['task_types']:
    print(f"  - {task_type}")

print("\n" + "=" * 60)
print("✅ 通用指纹系统演示完成！")
print("=" * 60)
print("\n💡 核心优势:")
print("  1. 自动推断任务类型 - 无需手动指定")
print("  2. 自动拦截失败模式 - 避免重复犯错")
print("  3. 自动建议成功路径 - 直接复用经验")
print("  4. 通用所有工具 - message/exec/read/write/...")
