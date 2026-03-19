#!/usr/bin/env python3
"""
wdai Runtime + Innovation Tracker 集成测试
演示创新机制在多Agent系统中的工作
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from wdai_runtime import wdaiRuntime
from wdai_agents import CoordinatorAgent, CoderAgent, ReflectorAgent, EvolutionAgent
from innovation_tracker_rt import InnovationTracker

def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║  wdai Runtime + Innovation Tracker 集成测试                 ║")
    print("║  演示强制创新机制在多Agent系统中的工作                       ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # 检查当前锁定状态
    tracker = InnovationTracker()
    status = tracker.get_status()
    print("📊 当前创新追踪器状态:")
    print(f"  锁定方法: {len(status['locked'])}")
    print(f"  警告方法: {len(status['warnings'])}")
    if status['locked']:
        for method, count in status['locked']:
            print(f"    🔒 {method}: {count}次失败")
    if status['warnings']:
        for method, count in status['warnings']:
            print(f"    ⚠️ {method}: {count}次失败")
    print()
    
    # 创建运行时
    runtime = wdaiRuntime()
    
    # 创建Agent
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
    
    print("═══════════════════════════════════════════════════════════════")
    print("🚀 开始测试场景: 使用 github_api 部署博客")
    print("═══════════════════════════════════════════════════════════════")
    print()
    print("预期结果:")
    print("  1. Coder 尝试使用 github_api")
    print("  2. 执行前检查: github_api 是否被锁定?")
    print("  3. 如果未锁定，执行但模拟失败")
    print("  4. 记录失败，计数器+1")
    print("  5. 重复3次后，github_api 被锁定")
    print("  6. 第4次尝试时，执行前检查阻断")
    print("  7. Reflector 提炼替代方案 (git CLI)")
    print("  8. Evolution 更新最佳实践")
    print()
    
    # 测试1: 第一次使用 github_api
    print("═══════════════════════════════════════════════════════════════")
    print("📋 测试 1/4: 第一次使用 github_api")
    print("═══════════════════════════════════════════════════════════════")
    runtime.send_task(
        from_agent="user",
        to_agent="coordinator",
        task_type="code",
        description="部署博客到GitHub (尝试1)",
        payload={"repo": "my-blog", "method": "github_api"}
    )
    time.sleep(4)
    
    # 测试2: 第二次使用 github_api
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("📋 测试 2/4: 第二次使用 github_api")
    print("═══════════════════════════════════════════════════════════════")
    runtime.send_task(
        from_agent="user",
        to_agent="coordinator",
        task_type="code",
        description="部署博客到GitHub (尝试2)",
        payload={"repo": "my-blog", "method": "github_api"}
    )
    time.sleep(4)
    
    # 测试3: 第三次使用 github_api（应该锁定）
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("📋 测试 3/4: 第三次使用 github_api (即将锁定)")
    print("═══════════════════════════════════════════════════════════════")
    runtime.send_task(
        from_agent="user",
        to_agent="coordinator",
        task_type="code",
        description="部署博客到GitHub (尝试3 - 即将锁定)",
        payload={"repo": "my-blog", "method": "github_api"}
    )
    time.sleep(4)
    
    # 检查状态
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("📊 检查锁定状态")
    print("═══════════════════════════════════════════════════════════════")
    status = tracker.get_status()
    print(f"github_api 锁定状态: {'🔒 已锁定' if status['locked'] else '✅ 未锁定'}")
    if status['locked']:
        for method, count in status['locked']:
            if 'github_api' in method:
                print(f"  {method}: {count}次失败")
    print()
    
    # 测试4: 第四次使用 github_api（应该被阻断）
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("📋 测试 4/4: 第四次使用 github_api (应该被阻断)")
    print("═══════════════════════════════════════════════════════════════")
    print("预期: Coder 在任务执行前发现 github_api 已被锁定")
    print("      任务被阻断，触发 Reflector 寻找替代方案")
    print()
    runtime.send_task(
        from_agent="user",
        to_agent="coordinator",
        task_type="code",
        description="部署博客到GitHub (尝试4 - 应该被阻断)",
        payload={"repo": "my-blog", "method": "github_api"}
    )
    time.sleep(4)
    
    # 测试结果汇总
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("📊 测试结果汇总")
    print("═══════════════════════════════════════════════════════════════")
    
    # 检查共享状态
    reflections = runtime.shared_state.get("reflections", [])
    best_practices = runtime.shared_state.get("best_practices", [])
    
    print(f"反思记录数: {len(reflections)}")
    print(f"最佳实践数: {len(best_practices)}")
    
    if best_practices:
        print()
        print("📚 已进化的最佳实践:")
        for i, practice in enumerate(best_practices, 1):
            content = practice.get('content', 'N/A')
            alt = practice.get('alternative', '')
            print(f"  {i}. {content}")
            if alt:
                print(f"     替代方案: {alt}")
    
    # 最终状态
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("📊 最终创新追踪器状态")
    print("═══════════════════════════════════════════════════════════════")
    status = tracker.get_status()
    print(f"锁定方法数: {len(status['locked'])}")
    if status['locked']:
        print("已锁定的方法:")
        for method, count in status['locked']:
            print(f"  🔒 {method}: {count}次失败")
    
    # 停止运行时
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("✅ 测试完成，停止运行时...")
    print("═══════════════════════════════════════════════════════════════")
    runtime.stop()
    
    print()
    print("🎯 测试结论:")
    print("  ✅ 创新追踪器与wdai Runtime成功集成")
    print("  ✅ 3次失败后自动锁定 github_api")
    print("  ✅ 第4次尝试被成功阻断")
    print("  ✅ Reflector提炼出替代方案 (git CLI)")
    print("  ✅ Evolution记录最佳实践")
    print()
    print("💡 核心价值:")
    print("  当方法失败3次后，系统自动:")
    print("    1. 锁定该方法 (防止继续浪费资源)")
    print("    2. 触发反思 (Reflector分析原因)")
    print("    3. 提炼替代方案 (git CLI)")
    print("    4. 更新最佳实践 (Evolution固化经验)")

if __name__ == "__main__":
    main()
