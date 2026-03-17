#!/usr/bin/env python3
"""
Agent配合实时状态看板
显示所有Agent的心跳和配合状态
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from multi_agent_coordinator import get_coordinator
from universal_principle_engine import get_engine
import time

def show_agent_dashboard():
    """显示Agent配合看板"""
    
    coord = get_coordinator()
    
    print("╔" + "═" * 70 + "╗")
    print("║" + " " * 20 + "🤖 Agent配合实时看板" + " " * 27 + "║")
    print("╚" + "═" * 70 + "╝")
    print()
    
    # Agent状态
    print("┌─ Agent状态 ───────────────────────────────────────────────────────┐")
    print("│                                                                   │")
    
    status = coord.get_system_status()
    agents = status['agents']['details']
    
    # 使用emoji和进度条显示状态
    for agent in agents:
        emoji = {
            'main': '👑', 
            'coder': '💻', 
            'reflector': '🪞', 
            'evolution': '🧬', 
            'reviewer': '👁️'
        }.get(agent['id'], '🤖')
        
        status_color = '🟢' if agent['status'] == 'idle' else '🔴'
        status_text = '空闲' if agent['status'] == 'idle' else '忙碌'
        
        task_info = f" [任务: {agent['current_task']}]" if agent['current_task'] else ""
        
        line = f"│  {emoji} {agent['id']:12} {status_color} {status_text:8}{' ' * 4}{agent['type']:12}{task_info}"
        line = line[:69] + "│"
        print(line)
    
    print("│                                                                   │")
    print("└───────────────────────────────────────────────────────────────────┘")
    print()
    
    # 任务统计
    print("┌─ 任务统计 ────────────────────────────────────────────────────────┐")
    print("│                                                                   │")
    tasks = status['tasks']
    print(f"│  📊 总任务: {tasks['total']:3}   ⏳ 待执行: {tasks['pending']:2}   ⚙️ 执行中: {tasks['running']:2}        │")
    print(f"│  ✅ 已完成: {tasks['completed']:3}   ❌ 失败: {tasks['failed']:2}   📈 成功率: {((tasks['completed'] / tasks['total'] * 100) if tasks['total'] > 0 else 0):.1f}%        │")
    print("│                                                                   │")
    print("└───────────────────────────────────────────────────────────────────┘")
    print()
    
    # 配合循环状态
    print("┌─ 配合循环 ────────────────────────────────────────────────────────┐")
    print("│                                                                   │")
    
    cycle_steps = [
        ("📡 感知", "Coordinator", "接收请求、分析任务"),
        ("🎯 决策", "Coordinator", "原则检查、Agent选择"),
        ("⚙️ 执行", "Coder", "编码实现、创新触发"),
        ("🪞 反思", "Reflector", "过程分析、原则提炼"),
        ("🧬 进化", "Evolution", "系统更新、能力进化"),
    ]
    
    for i, (step, agent, desc) in enumerate(cycle_steps, 1):
        status_icon = "✅" if i <= 5 else "⏳"
        print(f"│  {status_icon} {step}  →  {agent:12}  │  {desc:30}  │")
    
    print("│                                                                   │")
    print("│                    ⬆️  循环回到感知  ⬆️                            │")
    print("│                                                                   │")
    print("└───────────────────────────────────────────────────────────────────┘")
    print()
    
    # 原则执行系统状态
    print("┌─ 原则执行系统 ────────────────────────────────────────────────────┐")
    print("│                                                                   │")
    
    # 检查各Agent的原则引擎
    main_engine = get_engine("main")
    summary = main_engine.get_summary()
    
    print(f"│  🔥 引擎状态: 运行中   原则库: {summary['principles_loaded']}条              │")
    print(f"│  🔒 锁定方法: {len(summary['locked_methods'])}个   ⚠️ 违规记录: {summary['total_violations']}次                  │")
    
    if summary['locked_methods']:
        print("│                                                                   │")
        print("│  被锁定的方法 (强制换路):                                         │")
        for method in summary['locked_methods'][:2]:
            print(f"│    🔒 {method:56}  │")
    
    print("│                                                                   │")
    print("└───────────────────────────────────────────────────────────────────┘")
    print()
    
    # 最后更新
    print(f"最后更新: {status['last_update']}")
    print()

if __name__ == "__main__":
    show_agent_dashboard()
