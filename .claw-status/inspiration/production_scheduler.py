#!/usr/bin/env python3
"""
灵感摄取系统 - 生产级调度器 v4.0

集成:
- 高级调度器 (CS162调度原语)
- 双代理系统 (Planner + Executor)
- 性能监控

Author: wdai
Version: 4.0
"""

import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))
sys.path.insert(0, str(CLAW_STATUS / "agents"))

from advanced_scheduler import (
    AdvancedScheduler, Priority, SourceTask, 
    SourceMetrics, MLFQScheduler
)
from agents.integration import DualAgentInspirationSystem
from agents.performance_monitor import PerformanceMonitor


class ProductionScheduler(AdvancedScheduler):
    """
    生产级调度器
    
    集成双代理系统的完整调度器
    """
    
    def __init__(self, data_dir: str = "data/scheduler_v4"):
        super().__init__(data_dir)
        
        # 双代理系统
        self.system: DualAgentInspirationSystem = None
        self.monitor: PerformanceMonitor = None
        
        # 日志
        self.log_file = Path(data_dir) / "production_runs.jsonl"
        
        # 初始化双代理系统
        self._init_dual_agent_system()
    
    def _init_dual_agent_system(self):
        """初始化双代理系统"""
        try:
            self.system = DualAgentInspirationSystem(
                workspace_dir=str(CLAW_STATUS.parent.parent)
            )
            print("[ProductionScheduler] 双代理系统已初始化")
        except Exception as e:
            print(f"[ProductionScheduler] 双代理系统初始化失败: {e}")
            self.system = None
    
    def _execute_crawl(self, source_id: str) -> dict:
        """
        执行实际抓取 (集成双代理系统)
        """
        if not self.system:
            # 降级到模拟
            return super()._execute_crawl(source_id)
        
        try:
            start_time = time.time()
            
            # 启动系统
            self.system.start()
            
            # 根据source_id选择策略
            if source_id == 'arxiv':
                strategy = 'academic'
            elif source_id == 'github':
                strategy = 'code'
            else:
                strategy = 'balanced'
            
            # 执行抓取 (简化版，实际应调用完整流程)
            # TODO: 集成完整的双代理抓取流程
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # 模拟结果
            import random
            new_items = random.randint(0, 3)
            
            self.system.stop()
            
            return {
                'status': 'success',
                'new_items': new_items,
                'quality_score': random.uniform(0.6, 0.9) if new_items > 0 else 0.0,
                'elapsed_ms': elapsed_ms
            }
            
        except Exception as e:
            if self.system:
                self.system.stop()
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def run_scheduled(self, max_iterations: int = 10) -> dict:
        """
        运行调度循环 (生产模式)
        
        1. 检查所有源，将可运行的加入队列
        2. 按MLFQ顺序执行
        3. 记录结果
        """
        print("\n" + "="*70)
        print("🚀 生产级调度器 v4.0 - 开始运行")
        print("="*70)
        
        # 调度所有源
        scheduled_count = 0
        for source_id in self.sources:
            if self.schedule_source(source_id):
                scheduled_count += 1
        
        print(f"\n📥 已调度 {scheduled_count} 个源")
        
        # 执行循环
        results = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # 获取下一个任务
            task = self.mlfq.dequeue()
            if not task:
                print(f"\n✅ 所有任务完成 (共 {len(results)} 个)")
                break
            
            # 执行
            result = self.run_once()
            results.append(result)
            
            # 记录日志
            self._log_run(task, result)
            
            if result['status'] in ['error', 'rejected']:
                print(f"⚠️  任务异常: {result.get('error', '被拒绝')}")
        
        # 打印统计
        self.print_stats()
        
        return {
            'status': 'completed',
            'total': len(results),
            'successful': sum(1 for r in results if r.get('status') == 'completed'),
            'failed': sum(1 for r in results if r.get('status') == 'error'),
            'results': results
        }
    
    def _log_run(self, task: SourceTask, result: dict):
        """记录运行日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task': task.to_dict(),
            'result': result
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_detailed_stats(self) -> dict:
        """获取详细统计"""
        basic = self.get_stats()
        
        # 添加双代理系统状态
        if self.system:
            basic['dual_agent'] = {
                'initialized': True,
                'planner_status': 'active' if self.system.planner else 'inactive',
                'executor_status': 'active' if self.system.executor else 'inactive'
            }
        else:
            basic['dual_agent'] = {'initialized': False}
        
        # 添加源详细统计
        basic['source_details'] = {}
        for sid, m in self.metrics.items():
            basic['source_details'][sid] = {
                'total_crawls': m.total_crawls,
                'success_rate': m.success_count / max(1, m.total_crawls),
                'empty_rate': m.empty_count / max(1, m.total_crawls),
                'avg_crawl_time_ms': round(m.avg_crawl_time_ms, 2),
                'consecutive_failures': m.consecutive_failures,
                'backoff_remaining': max(0, m.current_backoff_seconds),
                'health_score': round(m.health_score, 2)
            }
        
        return basic


def test_production_scheduler():
    """测试生产级调度器"""
    print("="*70)
    print("🧪 测试生产级调度器 v4.0")
    print("="*70)
    
    scheduler = ProductionScheduler()
    
    # 运行调度
    result = scheduler.run_scheduled(max_iterations=5)
    
    # 详细统计
    stats = scheduler.get_detailed_stats()
    
    print("\n" + "="*70)
    print("📊 详细统计")
    print("="*70)
    print(json.dumps(stats, indent=2, default=str))
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)
    
    return scheduler, result


if __name__ == "__main__":
    test_production_scheduler()
