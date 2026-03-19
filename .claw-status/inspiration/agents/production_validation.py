#!/usr/bin/env python3
"""
Production Validation - 生产验证测试

Phase 3: 运行完整验证周期，监控性能和稳定性

Author: wdai
Date: 2026-03-19
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import json
from datetime import datetime
from typing import Dict, List, Any

from integration import DualAgentInspirationSystem, HybridInspirationSystem
from evolution_integration import EnhancedEvolutionEngine


class ProductionValidator:
    """
    生产验证器
    
    运行完整的验证周期，收集性能指标
    """
    
    def __init__(self):
        self.results: List[Dict] = []
        self.metrics = {
            'cycles_completed': 0,
            'cycles_failed': 0,
            'total_time': 0,
            'papers_fetched': 0,
            'papers_analyzed': 0,
            'insights_generated': 0
        }
    
    def validate_dual_agent_system(self, num_cycles: int = 1) -> Dict[str, Any]:
        """
        验证双代理系统
        
        Args:
            num_cycles: 运行周期数
        """
        print("\n" + "="*70)
        print("🧪 验证双代理系统")
        print("="*70)
        
        system = DualAgentInspirationSystem()
        
        try:
            # 启动
            print("\n[1/4] 启动系统...")
            system.start()
            
            # 运行多个周期
            for i in range(num_cycles):
                print(f"\n[2/4] 运行周期 {i+1}/{num_cycles}...")
                start_time = time.time()
                
                result = system.run_cycle()
                
                elapsed = time.time() - start_time
                
                # 记录结果
                self.results.append({
                    'cycle': i + 1,
                    'type': 'dual_agent',
                    'status': result.get('status'),
                    'elapsed_seconds': elapsed,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 更新指标
                if result.get('status') == 'success':
                    self.metrics['cycles_completed'] += 1
                else:
                    self.metrics['cycles_failed'] += 1
                
                self.metrics['total_time'] += elapsed
                
                print(f"  ✅ 周期 {i+1} 完成，耗时: {elapsed:.2f}s")
            
            # 获取状态
            print("\n[3/4] 获取系统状态...")
            status = system.get_status()
            
            # 停止
            print("\n[4/4] 停止系统...")
            system.stop()
            
            return {
                'status': 'success',
                'metrics': self.metrics,
                'final_status': status
            }
            
        except Exception as e:
            self.metrics['cycles_failed'] += 1
            system.stop()
            return {
                'status': 'failed',
                'error': str(e),
                'metrics': self.metrics
            }
    
    def validate_enhanced_engine(self) -> Dict[str, Any]:
        """验证增强版进化引擎"""
        print("\n" + "="*70)
        print("🧪 验证增强版进化引擎")
        print("="*70)
        
        engine = EnhancedEvolutionEngine()
        
        try:
            print("\n[1/3] 启动引擎...")
            engine.start()
            
            print("\n[2/3] 运行周期...")
            start_time = time.time()
            result = engine.run_cycle()
            elapsed = time.time() - start_time
            
            print(f"  ✅ 周期完成，耗时: {elapsed:.2f}s")
            
            print("\n[3/3] 获取状态...")
            status = engine.get_system_status()
            
            engine.stop()
            
            return {
                'status': 'success',
                'elapsed_seconds': elapsed,
                'engine_version': result.get('engine_version'),
                'enhancements': result.get('enhancements'),
                'system_status': status
            }
            
        except Exception as e:
            engine.stop()
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def validate_five_stage_integration(self) -> Dict[str, Any]:
        """验证五阶段集成"""
        print("\n" + "="*70)
        print("🧪 验证五阶段集成")
        print("="*70)
        
        from agents.evolution_integration import EvolutionEngineAdapter
        
        adapter = EvolutionEngineAdapter()
        
        try:
            print("\n[1/2] 启动适配器...")
            adapter.start()
            
            print("\n[2/2] 运行五阶段周期...")
            start_time = time.time()
            result = adapter.run_inspiration_cycle()
            elapsed = time.time() - start_time
            
            print(f"  ✅ 五阶段周期完成，耗时: {elapsed:.2f}s")
            
            adapter.stop()
            
            return {
                'status': 'success',
                'elapsed_seconds': elapsed,
                'phases_completed': result.get('phases_completed'),
                'timestamp': result.get('timestamp')
            }
            
        except Exception as e:
            adapter.stop()
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def run_full_validation(self) -> Dict[str, Any]:
        """运行完整验证套件"""
        print("\n" + "="*70)
        print("🚀 开始完整生产验证")
        print("="*70)
        print(f"开始时间: {datetime.now().isoformat()}")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'tests': {}
        }
        
        # 测试 1: 双代理系统
        results['tests']['dual_agent'] = self.validate_dual_agent_system(num_cycles=2)
        
        # 测试 2: 增强引擎
        results['tests']['enhanced_engine'] = self.validate_enhanced_engine()
        
        # 测试 3: 五阶段集成
        results['tests']['five_stage'] = self.validate_five_stage_integration()
        
        # 汇总
        results['end_time'] = datetime.now().isoformat()
        results['summary'] = self._generate_summary(results['tests'])
        
        # 保存报告
        self._save_report(results)
        
        return results
    
    def _generate_summary(self, tests: Dict) -> Dict[str, Any]:
        """生成验证摘要"""
        all_passed = all(t.get('status') == 'success' for t in tests.values())
        
        return {
            'all_tests_passed': all_passed,
            'tests_run': len(tests),
            'tests_passed': sum(1 for t in tests.values() if t.get('status') == 'success'),
            'tests_failed': sum(1 for t in tests.values() if t.get('status') == 'failed'),
            'recommendation': 'PROCEED_TO_PRODUCTION' if all_passed else 'REVIEW_ISSUES'
        }
    
    def _save_report(self, results: Dict):
        """保存验证报告"""
        report_dir = Path(__file__).parent.parent / "validation_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 验证报告已保存: {report_file}")
    
    def print_report(self, results: Dict):
        """打印验证报告"""
        print("\n" + "="*70)
        print("📊 生产验证报告")
        print("="*70)
        
        summary = results.get('summary', {})
        
        print(f"\n总体状态: {'✅ 通过' if summary.get('all_tests_passed') else '❌ 失败'}")
        print(f"测试通过: {summary.get('tests_passed', 0)}/{summary.get('tests_run', 0)}")
        print(f"建议: {summary.get('recommendation', 'UNKNOWN')}")
        
        print("\n详细结果:")
        for test_name, test_result in results.get('tests', {}).items():
            status = test_result.get('status', 'unknown')
            icon = '✅' if status == 'success' else '❌'
            print(f"  {icon} {test_name}: {status}")
            
            if status == 'success' and 'elapsed_seconds' in test_result:
                print(f"     耗时: {test_result['elapsed_seconds']:.2f}s")
            
            if status == 'failed' and 'error' in test_result:
                print(f"     错误: {test_result['error']}")
        
        print("\n" + "="*70)


def main():
    """主函数"""
    validator = ProductionValidator()
    
    # 运行完整验证
    results = validator.run_full_validation()
    
    # 打印报告
    validator.print_report(results)
    
    # 返回退出码
    if results.get('summary', {}).get('all_tests_passed'):
        print("\n🎉 所有测试通过！系统可以投入生产。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查问题。")
        return 1


if __name__ == '__main__':
    exit(main())
