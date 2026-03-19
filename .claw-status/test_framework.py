#!/usr/bin/env python3
"""
Universal Framework 综合测试
演示框架的各项功能
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from framework import UniversalFramework, ToolContext, TaskContext
import json

print("=" * 60)
print("🧪 Universal Framework 综合测试")
print("=" * 60)

# 初始化框架
framework = UniversalFramework(
    config_path="/root/.openclaw/workspace/.claw-status/config/framework.json"
)
framework.discover_plugins("/root/.openclaw/workspace/.claw-status/plugins")

# 测试1: 原则引擎 - 安全检查
print("\n【测试1】原则引擎 - 安全检查")
print("-" * 40)

result1 = framework.tool_call(
    "exec",
    command="rm -rf /tmp/test"
)
print(f"危险命令检测: {'🚫 已阻止' if not result1['success'] else '✅ 允许'}")
if not result1['success']:
    print(f"  原因: {result1.get('error', 'N/A')[:50]}")

result1b = framework.tool_call(
    "read",
    file_path="/tmp/test.txt"
)
print(f"正常命令检测: {'✅ 允许' if result1b['success'] else '🚫 阻止'}")

# 测试2: 方法指纹 - 自动学习和复用
print("\n【测试2】方法指纹 - 自动学习和复用")
print("-" * 40)

# 第一次调用：新任务类型
result2a = framework.tool_call(
    "browser",
    action="navigate",
    url="https://example.com"
)
print(f"第一次调用 (新任务): {'✅ 成功' if result2a['success'] else '❌ 失败'}")

# 第二次调用：应该复用成功模式
result2b = framework.tool_call(
    "browser",
    action="navigate", 
    url="https://another.com"
)
print(f"第二次调用 (应复用): {'✅ 成功' if result2b['success'] else '❌ 失败'}")

# 测试3: 学习系统 - 错误记录
print("\n【测试3】学习系统 - 错误记录")
print("-" * 40)

# 获取学习插件
learning_plugin = None
for plugin in framework.event_bus.plugins:
    if plugin.name == "auto_learning":
        learning_plugin = plugin
        break

if learning_plugin:
    # 模拟记录纠正
    learning_plugin.record_correction(
        original="应该这样做",
        correction="不对，应该那样做",
        context="测试任务"
    )
    print("✅ 已记录用户纠正")
    
    # 模拟记录最佳实践
    learning_plugin.record_best_practice(
        practice="使用cron而不是直接发送消息",
        tags=["messaging", "feishu"]
    )
    print("✅ 已记录最佳实践")

# 测试4: 记忆系统 - 信息提取
print("\n【测试4】记忆系统 - 信息提取")
print("-" * 40)

# 模拟完成任务，触发记忆提取
context = TaskContext(
    task_id="test_001",
    task_type="message_send",
    description="发送消息到飞书"
)

# 添加工具调用
context.tool_calls.append(ToolContext(
    tool_name="cron",
    params={"action": "add", "channel": "feishu"}
))

context.success = True
framework.complete_task(context, {"status": "sent"})
print("✅ 任务完成，已触发记忆提取")

# 测试5: 查看各个系统的状态
print("\n" + "=" * 60)
print("📊 各系统状态报告")
print("=" * 60)

# 指纹系统报告
fp_plugin = None
for p in framework.event_bus.plugins:
    if p.name == "fingerprint_system":
        fp_plugin = p
        break

if fp_plugin:
    report = fp_plugin.get_report()
    print(f"\n🎯 方法指纹系统:")
    print(f"  任务类型: {report['total_task_types']}")
    print(f"  成功模式: {report['total_success_patterns']}")
    print(f"  黑名单: {report['total_blacklisted']}")
    print(f"  任务列表: {', '.join(report['task_types'][:5])}")

# 记忆系统报告
mem_plugin = None
for p in framework.event_bus.plugins:
    if p.name == "memory_system":
        mem_plugin = p
        break

if mem_plugin:
    stats = mem_plugin.get_stats()
    print(f"\n🧠 记忆系统:")
    print(f"  总记忆数: {stats['total_memories']}")
    print(f"  策略: {stats['strategy']}")

# 学习系统报告
if learning_plugin:
    report = learning_plugin.get_learning_report()
    print(f"\n📚 学习系统:")
    print(f"  错误记录: {report['total_errors']}")
    print(f"  用户纠正: {report['total_corrections']}")
    print(f"  最佳实践: {report['total_best_practices']}")
    if report['recommendations']:
        print(f"  改进建议: {len(report['recommendations'])}条")

print("\n" + "=" * 60)
print("✅ 所有测试完成!")
print("=" * 60)
print("\n💡 框架优势:")
print("  1. 统一事件总线 - 所有插件协调工作")
print("  2. 配置驱动 - 规则在配置中，不在代码中")
print("  3. 自动发现 - 新插件自动加载")
print("  4. 动态学习 - 自动记录成功/失败模式")
