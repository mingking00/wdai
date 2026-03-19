"""
完整解决方案：Attention-Based Agent System with Hybrid Verification v4.0

集成：
1. AttentionBasedOrchestrator (AttnRes 思想) - Agent 协调
2. HybridVerificationLayer (Percepta 思想) - 快/慢验证
3. 白盒报告系统 - 可解释轨迹

使用方式：
    from complete_solution import AgentSystem
    
    system = AgentSystem()
    result = await system.process("你的任务")
    
    print(result['response'])  # 验证后的响应
    print(result['verification_report'])  # 白盒验证报告
"""

import asyncio
import sys
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system import create_attention_orchestrator
from core.agent_system.hybrid_verification_v4 import HybridVerificationLayer


class AgentSystem:
    """
    完整 Agent 系统 - 生产就绪版本
    
    架构：
        Input → [Attention Orchestrator] → [Hybrid Verification] → Output
                            ↓                        ↓
                    Agent 动态协调            Fast/Slow 验证
                    (AttnRes思想)            (Percepta思想)
    """
    
    def __init__(self):
        # 初始化核心组件
        self.orchestrator = create_attention_orchestrator()
        self.verifier = HybridVerificationLayer()
        
        # 设置默认 Agent 架构
        self._setup_default_agents()
        
        # 性能统计
        self.stats = {
            'total_requests': 0,
            'avg_latency_ms': 0,
            'fast_check_ratio': 0,
            'verification_pass_rate': 0
        }
    
    def _setup_default_agents(self):
        """设置默认 Agent 架构 (3-Block 设计)"""
        
        # Block 0: 输入理解
        self.orchestrator.register_agent("input_parser", block_id=0)
        self.orchestrator.register_agent("intent_analyzer", block_id=0)
        
        # Block 1: 处理
        self.orchestrator.register_agent("knowledge_retriever", block_id=1)
        self.orchestrator.register_agent("reasoning_engine", block_id=1)
        
        # Block 2: 输出
        self.orchestrator.register_agent("response_generator", block_id=2)
        self.orchestrator.register_agent("format_checker", block_id=2)
    
    async def process(
        self,
        user_input: str,
        task_type: str = "general",
        context: Optional[Dict] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        处理用户输入 - 完整流程
        
        Args:
            user_input: 用户输入文本
            task_type: 任务类型 (general/factual_qa/image_analysis/...)
            context: 额外上下文 (如 has_image, image_verified 等)
            verbose: 是否输出详细日志
        
        Returns:
            {
                'success': bool,
                'response': str,  # 验证后的响应
                'original_response': str,  # 原始响应
                'verification_passed': bool,
                'verification_report': str,  # 白盒报告
                'latency_ms': float,
                'metrics': {...}
            }
        """
        start_time = time.time()
        context = context or {}
        
        if verbose:
            print(f"🚀 Processing: {user_input[:50]}...")
        
        # ===== Phase 1: Attention-Based Execution =====
        if verbose:
            print("  [1/3] Executing with Attention Orchestrator...")
        
        task = {
            'description': user_input,
            'type': task_type
        }
        
        agent_sequence = [
            "input_parser",
            "intent_analyzer",
            "knowledge_retriever", 
            "reasoning_engine",
            "response_generator",
            "format_checker"
        ]
        
        execution_result = await self.orchestrator.execute_with_attention(
            task, agent_sequence
        )
        
        original_response = str(execution_result.get('integrated_outputs', ''))
        
        if verbose:
            print(f"  ✓ Generated response ({len(original_response)} chars)")
        
        # ===== Phase 2: Hybrid Verification =====
        if verbose:
            print("  [2/3] Running Hybrid Verification...")
        
        verify_context = {
            'task_type': task_type,
            'has_image': context.get('has_image', False) or '图片' in user_input,
            'image_verified': context.get('image_verified', False),
            **context
        }
        
        verify_result = await self.verifier.verify(
            original_response, verify_context
        )
        
        if verbose:
            fast_count = sum(1 for t in verify_result.traces if t.check_type == 'fast')
            slow_count = sum(1 for t in verify_result.traces if t.check_type == 'slow')
            print(f"  ✓ Fast checks: {fast_count}, Slow checks: {slow_count}")
        
        # ===== Phase 3: Generate Report =====
        if verbose:
            print("  [3/3] Generating report...")
        
        latency_ms = (time.time() - start_time) * 1000
        
        # 更新统计
        self._update_stats(latency_ms, verify_result)
        
        return {
            'success': verify_result.is_safe,
            'response': verify_result.final_response,
            'original_response': original_response,
            'verification_passed': verify_result.is_safe,
            'verification_report': verify_result.explain(),
            'latency_ms': latency_ms,
            'metrics': {
                'total_checks': verify_result.summary['total_checks'],
                'fast_checks': verify_result.summary['fast_checks'],
                'slow_checks': verify_result.summary['slow_checks'],
                'violations_found': verify_result.summary['violations_found'],
                'auto_fixed': verify_result.summary['auto_fixed']
            }
        }
    
    def _update_stats(self, latency_ms: float, verify_result):
        """更新性能统计"""
        self.stats['total_requests'] += 1
        
        # 滚动平均
        n = self.stats['total_requests']
        self.stats['avg_latency_ms'] = (
            (self.stats['avg_latency_ms'] * (n-1) + latency_ms) / n
        )
        
        # Fast check 比例
        total = verify_result.summary['total_checks']
        fast = verify_result.summary['fast_checks']
        if total > 0:
            ratio = fast / total
            self.stats['fast_check_ratio'] = (
                (self.stats['fast_check_ratio'] * (n-1) + ratio) / n
            )
        
        # 验证通过率
        passed = 1 if verify_result.is_safe else 0
        self.stats['verification_pass_rate'] = (
            (self.stats['verification_pass_rate'] * (n-1) + passed) / n
        )
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        return self.stats.copy()
    
    def print_stats(self):
        """打印性能统计"""
        print("\n" + "="*60)
        print("📊 System Performance Stats")
        print("="*60)
        print(f"Total Requests:     {self.stats['total_requests']}")
        print(f"Avg Latency:        {self.stats['avg_latency_ms']:.1f}ms")
        print(f"Fast Check Ratio:   {self.stats['fast_check_ratio']*100:.1f}%")
        print(f"Verification Pass:  {self.stats['verification_pass_rate']*100:.1f}%")
        print("="*60)


# ===== 使用示例 =====

async def demo():
    """完整使用演示"""
    
    print("="*70)
    print("🎯 Complete Solution Demo - Agent System v4.0")
    print("="*70)
    print("\n集成：Attention Orchestrator + Hybrid Verification")
    
    system = AgentSystem()
    
    # 测试用例
    test_cases = [
        {
            'input': '请解释什么是机器学习',
            'type': 'explanation',
            'expected': 'pass'
        },
        {
            'input': '根据最新研究，AI将在2025年超越人类',
            'type': 'factual_qa',
            'expected': 'fail'
        },
        {
            'input': '根据这张截图，系统肯定是正常的',
            'type': 'image_analysis',
            'context': {'has_image': True, 'image_verified': False},
            'expected': 'fail'
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_cases)}: {test['input'][:40]}...")
        print(f"Expected: {test['expected']}")
        print('='*70)
        
        result = await system.process(
            test['input'],
            task_type=test['type'],
            context=test.get('context', {}),
            verbose=True
        )
        
        # 验证结果
        actual = 'pass' if result['verification_passed'] else 'fail'
        match = '✅' if actual == test['expected'] else '❌'
        
        print(f"\n{match} Result: {actual} (latency: {result['latency_ms']:.1f}ms)")
        print(f"   Fast: {result['metrics']['fast_checks']}, "
              f"Slow: {result['metrics']['slow_checks']}, "
              f"Violations: {result['metrics']['violations_found']}")
        
        if not result['verification_passed']:
            print(f"\n📝 Verification Report:")
            print(result['verification_report'][:500] + "...")
        
        results.append({
            'test': test['input'][:30],
            'expected': test['expected'],
            'actual': actual,
            'match': actual == test['expected'],
            'latency_ms': result['latency_ms']
        })
    
    # 总结
    print("\n" + "="*70)
    print("📋 Test Summary")
    print("="*70)
    
    correct = sum(1 for r in results if r['match'])
    total = len(results)
    avg_latency = sum(r['latency_ms'] for r in results) / len(results)
    
    print(f"Accuracy: {correct}/{total} ({correct/total*100:.0f}%)")
    print(f"Avg Latency: {avg_latency:.1f}ms")
    
    for r in results:
        status = '✅' if r['match'] else '❌'
        print(f"  {status} {r['test'][:30]}...: {r['expected']} → {r['actual']}")
    
    # 性能统计
    system.print_stats()
    
    print("\n✨ Demo completed!")


if __name__ == "__main__":
    asyncio.run(demo())
