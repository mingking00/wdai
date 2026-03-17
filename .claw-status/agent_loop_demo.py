#!/usr/bin/env python3
"""
Agent配合完整循环演示
Perception → Decision → Execution → Reflection → Evolution
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from multi_agent_coordinator import get_coordinator
from universal_principle_engine import get_engine

def demonstrate_agent_loop():
    """
    演示完整的Agent配合循环
    """
    print("=" * 70)
    print("🔄 Agent配合完整循环演示")
    print("=" * 70)
    
    # 初始化系统
    coord = get_coordinator()
    principle_engine = get_engine("main")
    
    # ========== 阶段1: 感知 (Perception) ==========
    print("\n📡 阶段1: 感知 (Perception)")
    print("-" * 70)
    
    user_request = "部署博客到GitHub"
    print(f"用户请求: {user_request}")
    
    # 协调器感知任务
    task_analysis = {
        "type": "deploy",
        "complexity": "medium",
        "risk": "high"  # 涉及外部服务
    }
    print(f"任务分析: {task_analysis}")
    
    # ========== 阶段2: 决策 (Decision) ==========
    print("\n🎯 阶段2: 决策 (Decision)")
    print("-" * 70)
    
    # 2.1 原则检查
    print("原则检查:")
    check_result = principle_engine.pre_task_check(user_request)
    for check in check_result['checks'][:3]:
        print(f"  ✓ {check}")
    
    # 2.2 Agent选择
    print("\nAgent选择:")
    assignment = coord.assign_task(user_request, "deploy")
    if assignment['status'] == 'assigned':
        print(f"  选定Agent: {assignment['agent_id']} ({assignment['agent_type']})")
        print(f"  任务ID: {assignment['task_id']}")
    
    # ========== 阶段3: 执行 (Execution) ==========
    print("\n⚙️ 阶段3: 执行 (Execution)")
    print("-" * 70)
    
    agent_id = assignment['agent_id']
    task_id = assignment['task_id']
    
    # 模拟执行过程
    print(f"{agent_id} 开始执行任务...")
    
    # 尝试方法1
    print("\n  尝试方法1: GitHub API上传")
    principle_engine.current_task = {'type': 'deploy'}
    result1 = principle_engine.record_method_attempt('github_api', success=False, error='timeout')
    print(f"    结果: {result1['status']} (失败1次)")
    
    # 尝试方法2
    print("\n  尝试方法2: GitHub API上传 (重试)")
    result2 = principle_engine.record_method_attempt('github_api', success=False, error='timeout')
    print(f"    结果: {result2['status']} (失败2次)")
    
    # 尝试方法3
    print("\n  尝试方法3: GitHub API上传 (再试)")
    result3 = principle_engine.record_method_attempt('github_api', success=False, error='timeout')
    print(f"    结果: {result3['status']} (失败3次)")
    
    # 触发创新！
    if result3['status'] == 'MUST_INNOVATE':
        print(f"\n  🚨 强制创新触发！")
        print(f"    原因: github_api 已失败3次")
        print(f"    建议: {result3.get('alternatives', [])}")
        
        # 切换到新方法
        print("\n  切换到: git push")
        result4 = principle_engine.record_method_attempt('git_push', success=True)
        print(f"    结果: {result4['status']} ✓")
    
    # 完成任务
    completion = coord.report_task_complete(task_id, {"method": "git_push", "time": "5s"})
    print(f"\n  任务完成报告: {completion['status']}")
    
    # ========== 阶段4: 反思 (Reflection) ==========
    print("\n🪞 阶段4: 反思 (Reflection)")
    print("-" * 70)
    
    # 检查是否需要反思
    if completion.get('next_action') == 'reflection_triggered':
        print("协调器触发反思Agent...")
        
        # 模拟反思过程
        reflection_insights = [
            "API方法在网络不稳定时不可靠",
            "git push是更稳定的替代方案",
            "应在第2次失败后就考虑换路",
            "验证步骤缺失导致虚假成功风险"
        ]
        
        print("\n  反思洞察:")
        for i, insight in enumerate(reflection_insights, 1):
            print(f"    {i}. {insight}")
        
        # 触发原则更新
        print("\n  提炼核心原则:")
        print("    - 创新能力 = 死局中找到活路")
        print("    - 3次失败强制换路")
        print("    - 验证本能 = 报告前必须验证")
    
    # ========== 阶段5: 进化 (Evolution) ==========
    print("\n🧬 阶段5: 进化 (Evolution)")
    print("-" * 70)
    
    print("进化Agent接收反思结果...")
    
    # 系统更新
    updates = [
        {
            "component": "SOUL.md",
            "change": "添加'创新能力'核心信条",
            "status": "✓ 已更新"
        },
        {
            "component": "AGENTS.md",
            "change": "添加自动加载原则执行系统",
            "status": "✓ 已更新"
        },
        {
            "component": "universal_principle_engine.py",
            "change": "创建通用原则引擎",
            "status": "✓ 已创建"
        },
        {
            "component": "innovation_trigger.py",
            "change": "3次失败自动锁定机制",
            "status": "✓ 已创建"
        },
        {
            "component": "multi_agent_coordinator.py",
            "change": "Agent协调系统",
            "status": "✓ 已创建"
        }
    ]
    
    print("\n  系统更新:")
    for update in updates:
        print(f"    {update['status']} {update['component']}")
        print(f"       └─ {update['change']}")
    
    # ========== 循环闭环 ==========
    print("\n" + "=" * 70)
    print("✅ 循环完成 - 系统已进化")
    print("=" * 70)
    
    # 显示最终状态
    print("\n最终系统状态:")
    status = coord.get_system_status()
    print(f"  Agent: {status['agents']['idle']}空闲 / {status['agents']['busy']}忙碌")
    print(f"  任务: {status['tasks']['completed']}完成 / {status['tasks']['failed']}失败")
    print(f"  冲突: {status['conflicts']}次已仲裁")
    
    print("\n下次交互改进:")
    print("  • 自动验证所有'成功'报告")
    print("  • 3次失败强制切换方法")
    print("  • 重启后自动恢复所有状态")
    print("  • Agent间自动协调任务")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    demonstrate_agent_loop()
