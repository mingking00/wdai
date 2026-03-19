#!/usr/bin/env python3
"""
Dual-Agent System Integration - 双代理系统集成

将 Planner + Executor 集成到灵感摄取系统

Author: wdai
Date: 2026-03-19
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import PlannerAgent, ExecutorAgent, AgentCoordinator, Task
from typing import Dict, List, Optional, Any
import json


class DualAgentInspirationSystem:
    """
    双代理灵感摄取系统
    
    替代原有的 inspiration_fetcher.py 单体架构
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        # 创建代理协调器
        self.coordinator = AgentCoordinator()
        
        # 创建 Planner
        self.planner = PlannerAgent('inspiration_planner', self.coordinator.message_bus)
        self.coordinator.register_agent(self.planner)
        
        # 创建 Executor（可以创建多个）
        self.executor_1 = ExecutorAgent('inspiration_executor_1', self.coordinator.message_bus)
        self.coordinator.register_agent(self.executor_1)
        
        # 注册执行代理到 Planner
        self.planner.register_executor('inspiration_executor_1')
        
        # 状态
        self._running = False
        
        print("[DualAgentSystem] 双代理系统初始化完成")
        print(f"  - Planner: {self.planner.agent_id}")
        print(f"  - Executors: {[self.executor_1.agent_id]}")
    
    def start(self):
        """启动系统"""
        self.coordinator.start_all()
        self._running = True
        print("[DualAgentSystem] 系统已启动")
    
    def stop(self):
        """停止系统"""
        self.coordinator.stop_all()
        self._running = False
        print("[DualAgentSystem] 系统已停止")
    
    def run_cycle(self) -> Dict[str, Any]:
        """
        运行一个完整的摄取周期
        
        替代原有的 fetch_and_generate() 方法
        """
        if not self._running:
            print("[DualAgentSystem] 错误: 系统未启动")
            return {'status': 'error', 'reason': 'not_running'}
        
        print("\n" + "="*60)
        print("[DualAgentSystem] 开始摄取周期")
        print("="*60)
        
        # 1. Planner 规划抓取任务
        plan_task = Task(
            type='plan_fetch',
            priority=1,
            payload={'cycle_id': 'cycle_001'}
        )
        self.coordinator.assign_task(plan_task, self.planner.agent_id)
        
        # 等待任务完成（实际实现中应该使用事件/回调机制）
        import time
        time.sleep(2.0)
        
        # 2. 获取状态
        status = self.get_status()
        
        print("\n" + "="*60)
        print("[DualAgentSystem] 摄取周期完成")
        print("="*60)
        
        return {
            'status': 'success',
            'planner_stats': status['planner'],
            'executor_stats': status['executors']
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        all_status = self.coordinator.get_all_status()
        
        return {
            'running': self._running,
            'planner': all_status.get(self.planner.agent_id, {}),
            'executors': {
                self.executor_1.agent_id: all_status.get(self.executor_1.agent_id, {})
            }
        }
    
    def get_summary(self) -> str:
        """获取系统摘要"""
        return (
            self.planner.get_strategy_summary() +
            self.executor_1.get_executor_summary()
        )


class HybridInspirationSystem:
    """
    混合架构 - 兼容旧系统的同时引入双代理
    
    用于平滑过渡，可以逐步迁移
    """
    
    def __init__(self, use_dual_agent: bool = False):
        self.use_dual_agent = use_dual_agent
        self.dual_system: Optional[DualAgentInspirationSystem] = None
        
        if use_dual_agent:
            self.dual_system = DualAgentInspirationSystem()
    
    def start(self):
        """启动系统"""
        if self.dual_system:
            self.dual_system.start()
        else:
            print("[HybridSystem] 使用原有单体架构")
    
    def fetch_and_generate(self) -> Dict[str, Any]:
        """
        抓取并生成洞察
        
        兼容旧接口，根据配置选择实现方式
        """
        if self.use_dual_agent and self.dual_system:
            return self.dual_system.run_cycle()
        else:
            # 调用原有实现
            print("[HybridSystem] 使用原有单体架构执行")
            # 这里会调用 inspiration_fetcher.py 的原有功能
            return {'status': 'legacy_mode'}
    
    def stop(self):
        """停止系统"""
        if self.dual_system:
            self.dual_system.stop()


def test_dual_agent_system():
    """测试双代理系统"""
    print("\n" + "="*70)
    print("🧪 双代理系统集成测试")
    print("="*70 + "\n")
    
    # 创建双代理系统
    system = DualAgentInspirationSystem()
    
    # 启动
    system.start()
    
    # 运行一个周期
    result = system.run_cycle()
    
    # 打印状态
    print(system.get_summary())
    
    # 停止
    system.stop()
    
    print("\n✅ 双代理系统集成测试完成")
    print(f"结果: {json.dumps(result, indent=2)}")
    
    return result


def test_hybrid_system():
    """测试混合架构"""
    print("\n" + "="*70)
    print("🧪 混合架构测试")
    print("="*70 + "\n")
    
    # 测试双代理模式
    print("--- 模式1: 双代理模式 ---")
    hybrid = HybridInspirationSystem(use_dual_agent=True)
    hybrid.start()
    result1 = hybrid.fetch_and_generate()
    hybrid.stop()
    
    # 测试原有模式
    print("\n--- 模式2: 原有架构模式 ---")
    hybrid2 = HybridInspirationSystem(use_dual_agent=False)
    hybrid2.start()
    result2 = hybrid2.fetch_and_generate()
    hybrid2.stop()
    
    print("\n✅ 混合架构测试完成")


if __name__ == '__main__':
    # 测试双代理系统
    test_dual_agent_system()
    
    # 测试混合架构
    test_hybrid_system()
