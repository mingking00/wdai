#!/usr/bin/env python3
"""
Agent CLI with MoE - 智能路由版本

使用方法:
    python3 agent_cli_moe.py "你的任务描述"
    
示例:
    python3 agent_cli_moe.py "搜索Python教程并保存到笔记"
    python3 agent_cli_moe.py "分析这段代码并生成文档"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from skill_moe import MoEOrchestrator, SkillRouter


def main():
    if len(sys.argv) < 2:
        print("🧠 Agent CLI with MoE (Mixture-of-Experts)")
        print("=" * 60)
        print("用法: python3 agent_cli_moe.py \"你的任务描述\"")
        print("\n示例:")
        print('  python3 agent_cli_moe.py "搜索Python教程"')
        print('  python3 agent_cli_moe.py "分析代码bug"')
        print('  python3 agent_cli_moe.py "阅读PDF并总结"')
        print("\n系统将自动选择最合适的Expert组合来执行任务。")
        return
    
    query = " ".join(sys.argv[1:])
    
    print("=" * 60)
    print("🚀 Agent CLI with MoE - 智能任务执行")
    print("=" * 60)
    print(f"\n📥 任务: {query}\n")
    
    # 使用MoE编排器执行
    orchestrator = MoEOrchestrator()
    result = orchestrator.execute(query)
    
    print("\n" + "=" * 60)
    print("✅ 执行完成")
    print("=" * 60)
    print(f"\n🧠 激活的专家:")
    print(f"   主专家: {result['primary']['expert']} ({result['primary']['type']})")
    if result['supporting']:
        print(f"   协助专家: {', '.join([e['expert'] for e in result['supporting']])}")
    print(f"\n📋 执行策略: {result['execution_plan']}")
    
    # 显示系统状态
    print("\n📊 Expert负载状态:")
    status = orchestrator.get_system_status()
    for expert_name, expert_status in status['router_status'].items():
        load_bar = "█" * int(expert_status['load'] * 10) + "░" * (10 - int(expert_status['load'] * 10))
        print(f"   {expert_name:12} |{load_bar}| {expert_status['load']:.1%}")


if __name__ == "__main__":
    main()
