#!/usr/bin/env python3
"""
wdai 三区安全架构工作流演示
展示如何在实际任务中使用三区架构
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.wdai-runtime')

from zone_manager import ZoneManager

def demo_task_workflow():
    """
    演示一个完整任务的三区工作流
    场景: 用户让AI自主分析代码并提议改进
    """
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     三区架构工作流演示                                      ║")
    print("║     场景: 自主代码分析与改进提议                           ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    zm = ZoneManager()
    
    # === ZONE 1: 人类控制区 ===
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│ 🧑‍💻 ZONE 1: 人类控制区                                      │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    print("用户: '帮我分析 skills/code-dev-agent 的代码，并提出改进建议'")
    print()
    print("AI: 收到。这个任务需要:")
    print("  1. 读取代码文件")
    print("  2. 分析架构问题")  
    print("  3. 生成改进方案")
    print()
    print("⚠️  这涉及文件操作，需要进入AI学习区执行")
    print()
    print("用户: '进入自主模式执行'")
    print()
    
    # 进入AI学习区
    zm.enter_zone("ai_learning", "用户授权分析代码")
    
    # === ZONE 2: AI学习区 ===
    print()
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│ 🤖 ZONE 2: AI学习区                                        │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    print("✅ 权限检查:")
    print(f"   read_memory:  {'✅ 允许' if zm.check_permission('read_memory') else '❌ 拒绝'}")
    print(f"   execute_code: {'✅ 允许' if zm.check_permission('execute_code') else '❌ 拒绝'}")
    print(f"   write_file:   {'✅ 允许' if zm.check_permission('write_file') else '❌ 拒绝'}")
    print(f"   delete_file:  {'❌ 拒绝 (安全限制)'}")
    print()
    
    print("🔄 执行分析任务...")
    print("  1. 读取 codedev.py... ✅")
    print("  2. 分析架构...       ✅")
    print("  3. 生成改进报告...   ✅")
    print()
    
    # 模拟分析结果
    improvements = [
        "添加错误重试机制",
        "优化日志格式",
        "增加配置文件验证"
    ]
    
    print("📊 分析结果:")
    for i, imp in enumerate(improvements, 1):
        print(f"   {i}. {imp}")
    print()
    
    # 准备进入验证区
    print("⏳ 任务完成，准备提交到验证区...")
    print()
    
    zm.enter_zone("validation", "分析完成，等待用户确认")
    
    # === ZONE 3: 验证区 ===
    print()
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│ ✅ ZONE 3: 验证区                                          │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    print("权限状态: 只读模式")
    print("   所有修改操作已暂停，等待用户审查")
    print()
    print("📝 待确认变更:")
    print()
    print("┌─ 改进提案 ─────────────────────────────────────────────────┐")
    for i, imp in enumerate(improvements, 1):
        print(f"│ {i}. {imp:<55} │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    
    # 用户选择
    print("用户选项:")
    print("  [1] 全部应用")
    print("  [2] 选择应用")  
    print("  [3] 修改后应用")
    print("  [4] 取消")
    print()
    
    # 模拟用户选择
    user_choice = "1"
    print(f"用户输入: {user_choice} (全部应用)")
    print()
    
    # 返回人类控制区执行
    zm.enter_zone("human_control", "用户确认应用改进")
    
    # === 回到ZONE 1执行 ===
    print()
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│ 🧑‍💻 ZONE 1: 人类控制区 (执行模式)                           │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    print("✅ 执行改进:")
    for i, imp in enumerate(improvements, 1):
        print(f"   {i}. {imp}... ✅ 已应用")
    print()
    
    print("📝 生成执行报告...")
    print()
    print("┌─ 执行摘要 ─────────────────────────────────────────────────┐")
    print(f"│ 任务类型: 代码分析 + 改进提议                               │")
    print(f"│ 执行模式: 三区安全架构                                      │")
    print(f"│ 总改进数: {len(improvements)}                                              │")
    print(f"│ 状态:     全部完成 ✅                                        │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    
    # 显示区域历史
    print("📊 本次会话区域转换历史:")
    for i, h in enumerate(zm.zone_history, 1):
        arrow = "→" if h['to'] == 'ai_learning' else ("→" if h['to'] == 'validation' else "→")
        print(f"   {i}. {h['from']:<20} {arrow} {h['to']:<20} ({h['reason']})")
    print()
    
    print("="*65)
    print("✅ 三区架构工作流演示完成!")
    print("="*65)
    print()
    print("💡 安全优势:")
    print("  • AI学习区限制了危险操作权限")
    print("  • 所有变更必须经过验证区审查")
    print("  • 用户始终保留最终决策权")

if __name__ == '__main__':
    demo_task_workflow()
