#!/usr/bin/env python3
"""
灵感摄取系统 - 双代理调度器 v3.0

集成双代理架构的生产调度器

Author: wdai
Version: 3.0
"""

import json
import time
import sys
from datetime import datetime
from pathlib import Path

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))
sys.path.insert(0, str(CLAW_STATUS / "agents"))

from agents.integration import DualAgentInspirationSystem
from agents.performance_monitor import PerformanceMonitor, LearningFeedback


class DualAgentScheduler:
    """
    双代理调度器 v3.0
    
    使用 Planner + Executor 架构运行灵感摄取
    """
    
    CONFIG = {
        'min_interval_minutes': 15,
        'max_crawl_time_seconds': 600,
        'enable_monitoring': True,
        'enable_learning': True,
    }
    
    def __init__(self, data_dir: str = "data/scheduler"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.data_dir / "dual_agent_runs.jsonl"
        self.state_file = self.data_dir / "dual_agent_state.json"
        
        # 双代理系统
        self.system: DualAgentInspirationSystem = None
        self.monitor: PerformanceMonitor = None
        self.feedback: LearningFeedback = None
        
        # 状态
        self.run_count = 0
        self.last_run_time = None
        
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.run_count = state.get('run_count', 0)
                    self.last_run_time = state.get('last_run_time')
            except Exception as e:
                print(f"[Scheduler] 加载状态失败: {e}")
    
    def _save_state(self):
        """保存状态"""
        state = {
            'run_count': self.run_count,
            'last_run_time': self.last_run_time,
            'updated_at': datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _log_run(self, result: dict):
        """记录运行日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'run_number': self.run_count,
            'result': result
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def should_run(self) -> bool:
        """检查是否应该运行"""
        if not self.last_run_time:
            return True
        
        last = datetime.fromisoformat(self.last_run_time)
        elapsed = (datetime.now() - last).total_seconds() / 60
        
        return elapsed >= self.CONFIG['min_interval_minutes']
    
    def initialize(self):
        """初始化双代理系统"""
        print("[Scheduler] 初始化双代理系统...")
        
        # 创建系统
        self.system = DualAgentInspirationSystem()
        
        # 初始化监控
        if self.CONFIG['enable_monitoring']:
            self.monitor = PerformanceMonitor()
        
        # 初始化学习反馈
        if self.CONFIG['enable_learning']:
            self.feedback = LearningFeedback()
        
        print("[Scheduler] 初始化完成")
    
    def run_cycle(self) -> dict:
        """
        运行一个摄取周期
        
        这是调度器的主要入口
        """
        print("\n" + "="*70)
        print(f"🚀 双代理调度器 - 运行 #{self.run_count + 1}")
        print("="*70)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查是否应该运行
        if not self.should_run():
            last = datetime.fromisoformat(self.last_run_time)
            elapsed = (datetime.now() - last).total_seconds() / 60
            remaining = self.CONFIG['min_interval_minutes'] - elapsed
            
            print(f"\n⏱️ 距离上次运行仅 {elapsed:.1f} 分钟")
            print(f"   需要等待 {remaining:.1f} 分钟后再次运行")
            
            return {
                'status': 'skipped',
                'reason': 'too_soon',
                'elapsed_minutes': elapsed,
                'wait_minutes': remaining
            }
        
        # 初始化（如果未初始化）
        if self.system is None:
            self.initialize()
        
        # 开始监控
        if self.monitor:
            self.monitor.start_monitoring()
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 启动系统
            print("\n[1/3] 启动双代理系统...")
            self.system.start()
            
            # 运行周期
            print("\n[2/3] 运行摄取周期...")
            result = self.system.run_cycle()
            
            # 停止系统
            print("\n[3/3] 停止系统...")
            self.system.stop()
            
            elapsed = time.time() - start_time
            
            # 记录监控
            if self.monitor:
                self.monitor.record_task('inspiration_cycle', elapsed, success=True)
                self.monitor.stop_monitoring()
            
            # 记录学习反馈
            if self.feedback and self.monitor:
                self.feedback.record_execution(
                    result,
                    self.monitor.get_report()
                )
            
            # 更新状态
            self.run_count += 1
            self.last_run_time = datetime.now().isoformat()
            self._save_state()
            
            # 记录日志
            run_result = {
                'status': 'success',
                'elapsed_seconds': elapsed,
                'result': result
            }
            self._log_run(run_result)
            
            # 打印摘要
            print("\n" + "="*70)
            print("📊 运行摘要")
            print("="*70)
            print(f"状态: ✅ 成功")
            print(f"耗时: {elapsed:.2f}s")
            print(f"运行次数: {self.run_count}")
            
            if self.monitor:
                perf = self.monitor.get_report()
                print(f"成功率: {perf['success_rate']*100:.1f}%")
            
            print("="*70)
            
            return run_result
            
        except Exception as e:
            elapsed = time.time() - start_time
            
            # 停止系统
            if self.system:
                self.system.stop()
            
            # 记录监控
            if self.monitor:
                self.monitor.record_task('inspiration_cycle', elapsed, success=False)
                self.monitor.stop_monitoring()
            
            # 记录错误
            error_result = {
                'status': 'failed',
                'error': str(e),
                'elapsed_seconds': elapsed
            }
            self._log_run(error_result)
            
            print(f"\n❌ 运行失败: {e}")
            import traceback
            traceback.print_exc()
            
            return error_result
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        return {
            'run_count': self.run_count,
            'last_run_time': self.last_run_time,
            'system_ready': self.system is not None,
            'monitoring_enabled': self.monitor is not None,
            'learning_enabled': self.feedback is not None
        }
    
    def print_summary(self):
        """打印运行摘要"""
        print("\n" + "="*70)
        print("📊 双代理调度器摘要")
        print("="*70)
        print(f"总运行次数: {self.run_count}")
        print(f"上次运行: {self.last_run_time or '无'}")
        print(f"系统状态: {'已初始化' if self.system else '未初始化'}")
        print(f"监控状态: {'启用' if self.monitor else '禁用'}")
        print(f"学习状态: {'启用' if self.feedback else '禁用'}")
        print("="*70)


def main():
    """主函数"""
    print("="*70)
    print("🚀 双代理调度器 v3.0")
    print("="*70)
    
    scheduler = DualAgentScheduler()
    
    # 运行周期
    result = scheduler.run_cycle()
    
    # 打印摘要
    scheduler.print_summary()
    
    # 返回状态码
    if result.get('status') in ['success', 'skipped']:
        return 0
    else:
        return 1


if __name__ == '__main__':
    exit(main())
