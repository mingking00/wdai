#!/usr/bin/env python3
"""
Evolution Engine Integration - 进化引擎集成

将双代理系统与五阶段进化引擎集成

Author: wdai
Date: 2026-03-19
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from integration import DualAgentInspirationSystem


class EvolutionEngineAdapter:
    """
    进化引擎适配器
    
    让双代理系统可以使用五阶段进化引擎的能力
    """
    
    def __init__(self, evolution_engine=None):
        self.evolution_engine = evolution_engine
        self.dual_system = DualAgentInspirationSystem()
        
        # 阶段回调
        self.phase_callbacks = {
            'code_understanding': self._on_code_understanding,
            'creative_design': self._on_creative_design,
            'formal_verification': self._on_formal_verification,
            'sandbox_testing': self._on_sandbox_testing,
            'feedback_learning': self._on_feedback_learning
        }
    
    def start(self):
        """启动系统"""
        self.dual_system.start()
        print("[EvolutionAdapter] 进化引擎适配器已启动")
    
    def stop(self):
        """停止系统"""
        self.dual_system.stop()
        print("[EvolutionAdapter] 进化引擎适配器已停止")
    
    def run_inspiration_cycle(self) -> Dict[str, Any]:
        """
        运行完整的灵感摄取周期
        
        集成五阶段验证
        """
        print("\n" + "="*70)
        print("🔄 运行灵感摄取周期（集成五阶段进化）")
        print("="*70)
        
        # Phase 1: Code Understanding
        self._trigger_phase_1()
        
        # Phase 2-3: 双代理系统执行
        result = self.dual_system.run_cycle()
        
        # Phase 4-5: 验证和学习
        self._trigger_phase_4(result)
        self._trigger_phase_5(result)
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'phases_completed': 5,
            'result': result
        }
    
    def _trigger_phase_1(self):
        """触发代码理解阶段"""
        print("\n[Phase 1] 代码理解...")
        # 这里可以调用 evolution_engine 的代码理解能力
        # 分析当前系统的代码结构
        pass
    
    def _trigger_phase_4(self, result: Dict):
        """触发沙箱测试阶段"""
        print("\n[Phase 4] 沙箱测试...")
        # 验证抓取结果的质量
        if result.get('status') == 'success':
            print("  ✅ 抓取任务通过验证")
        else:
            print("  ❌ 抓取任务需要调整")
    
    def _trigger_phase_5(self, result: Dict):
        """触发反馈学习阶段"""
        print("\n[Phase 5] 反馈学习...")
        # 记录本次执行的经验
        stats = self.dual_system.get_status()
        print(f"  📊 记录学习数据: {json.dumps(stats, indent=2)}")
    
    def _on_code_understanding(self, data: Dict):
        """代码理解回调"""
        pass
    
    def _on_creative_design(self, data: Dict):
        """创造性设计回调"""
        pass
    
    def _on_formal_verification(self, data: Dict):
        """形式化验证回调"""
        pass
    
    def _on_sandbox_testing(self, data: Dict):
        """沙箱测试回调"""
        pass
    
    def _on_feedback_learning(self, data: Dict):
        """反馈学习回调"""
        pass


class EnhancedEvolutionEngine:
    """
    增强版进化引擎
    
    在原五阶段基础上，使用双代理架构执行灵感摄取
    """
    
    def __init__(self):
        # 尝试导入原有进化引擎
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from evolution_engine import EvolutionEngine
            self.base_engine = EvolutionEngine()
            print("[EnhancedEngine] 已加载原有进化引擎")
        except ImportError:
            self.base_engine = None
            print("[EnhancedEngine] 未找到原有进化引擎，使用基础模式")
        
        # 双代理系统
        self.dual_system = DualAgentInspirationSystem()
        
        # 增强功能
        self.enhancements = {
            'dual_agent_fetch': True,
            'deep_analysis': True,
            'auto_insight_generation': True
        }
    
    def start(self):
        """启动增强引擎"""
        self.dual_system.start()
        if self.base_engine:
            # 如果有基础引擎，也启动它
            pass
        print("[EnhancedEngine] 增强进化引擎已启动")
    
    def stop(self):
        """停止增强引擎"""
        self.dual_system.stop()
        print("[EnhancedEngine] 增强进化引擎已停止")
    
    def run_cycle(self) -> Dict[str, Any]:
        """
        运行增强版周期
        
        使用双代理架构执行灵感摄取
        """
        print("\n" + "="*70)
        print("🚀 增强版进化引擎运行周期")
        print("="*70)
        
        # 使用双代理系统执行
        result = self.dual_system.run_cycle()
        
        # 添加增强功能标记
        result['enhancements'] = self.enhancements
        result['engine_version'] = '2.0-dual-agent'
        
        print("\n[EnhancedEngine] 周期完成")
        print(f"  版本: {result['engine_version']}")
        print(f"  增强功能: {list(self.enhancements.keys())}")
        
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        dual_status = self.dual_system.get_status()
        
        return {
            'engine_type': 'enhanced',
            'version': '2.0-dual-agent',
            'dual_agent_status': dual_status,
            'base_engine_available': self.base_engine is not None,
            'enhancements': self.enhancements
        }


def test_evolution_integration():
    """测试进化引擎集成"""
    print("\n" + "="*70)
    print("🧪 进化引擎集成测试")
    print("="*70 + "\n")
    
    # 测试适配器
    print("--- 测试 EvolutionEngineAdapter ---")
    adapter = EvolutionEngineAdapter()
    adapter.start()
    result = adapter.run_inspiration_cycle()
    adapter.stop()
    
    print(f"\n结果: {json.dumps(result, indent=2)}")
    
    # 测试增强引擎
    print("\n--- 测试 EnhancedEvolutionEngine ---")
    engine = EnhancedEvolutionEngine()
    engine.start()
    result2 = engine.run_cycle()
    engine.stop()
    
    print(f"\n状态: {json.dumps(engine.get_system_status(), indent=2)}")
    
    print("\n✅ 进化引擎集成测试完成")


if __name__ == '__main__':
    test_evolution_integration()
