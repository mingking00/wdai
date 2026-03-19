#!/usr/bin/env python3
"""
wdai Runtime 启动脚本
演示完整的多Agent协作系统
"""

import sys
import time
import signal
from pathlib import Path

# 添加运行时目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from wdai_runtime import wdaiRuntime
from wdai_agents import CoordinatorAgent, CoderAgent, ReflectorAgent, EvolutionAgent

def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     wdai Runtime - 独立多Agent运行时系统                   ║")
    print("║     不依赖OpenClaw的底层架构                                ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # 创建运行时
    runtime = wdaiRuntime()
    
    # 创建并注册Agent
    coordinator = CoordinatorAgent()
    coder = CoderAgent()
    reflector = ReflectorAgent()
    evolution = EvolutionAgent()
    
    runtime.register_agent(coordinator)
    runtime.register_agent(coder)
    runtime.register_agent(reflector)
    runtime.register_agent(evolution)
    
    # 启动运行时
    runtime.start()
    
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("🚀 所有Agent已启动并运行")
    print("═══════════════════════════════════════════════════════════════")
    print()
    print("Agent状态:")
    for agent_id, agent in runtime.agents.items():
        print(f"  - {agent_id}: {agent.state.status}")
    print()
    
    # 发送测试任务
    print("📋 发送测试任务: 部署博客到GitHub")
    runtime.send_task(
        from_agent="user",
        to_agent="coordinator",
        task_type="code",
        description="部署博客到GitHub",
        payload={"repo": "my-blog", "method": "github_api"}
    )
    
    # 等待任务完成
    print()
    print("⏳ 等待任务完成...")
    time.sleep(5)
    
    # 检查共享状态
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("📊 共享状态检查")
    print("═══════════════════════════════════════════════════════════════")
    
    reflections = runtime.shared_state.get("reflections", [])
    print(f"Reflections recorded: {len(reflections)}")
    
    best_practices = runtime.shared_state.get("best_practices", [])
    print(f"Best practices evolved: {len(best_practices)}")
    
    if best_practices:
        print()
        print("📚 已进化的最佳实践:")
        for i, practice in enumerate(best_practices, 1):
            print(f"  {i}. {practice.get('content', 'N/A')}")
    
    # 保持运行
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("✅ 系统运行中，按 Ctrl+C 停止")
    print("═══════════════════════════════════════════════════════════════")
    
    def signal_handler(sig, frame):
        print("\n\n🛑 停止运行时...")
        runtime.stop()
        print("✅ 已停止")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # 保持运行
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
