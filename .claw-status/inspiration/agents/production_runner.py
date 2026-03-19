#!/usr/bin/env python3
"""
Production Runner - 生产运行器

正式投入生产的双代理系统运行脚本

Author: wdai
Date: 2026-03-19
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
from datetime import datetime

from integration import DualAgentInspirationSystem
from performance_monitor import PerformanceMonitor, LearningFeedback


def run_production_cycle():
    """
    运行生产周期
    
    这是实际投入生产的运行流程
    """
    print("\n" + "="*70)
    print("🚀 双代理系统 - 生产运行")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 初始化监控
    print("\n[1/5] 初始化性能监控...")
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # 2. 创建系统
    print("\n[2/5] 创建双代理系统...")
    system = DualAgentInspirationSystem()
    
    # 3. 启动系统
    print("\n[3/5] 启动系统...")
    start_time = time.time()
    system.start()
    startup_time = time.time() - start_time
    print(f"  ✅ 系统启动完成，耗时: {startup_time:.2f}s")
    
    # 4. 运行周期
    print("\n[4/5] 运行灵感摄取周期...")
    cycle_start = time.time()
    
    try:
        result = system.run_cycle()
        cycle_time = time.time() - cycle_start
        
        # 记录任务
        monitor.record_task('inspiration_cycle', cycle_time, success=True)
        
        print(f"  ✅ 周期完成，耗时: {cycle_time:.2f}s")
        
        # 显示结果摘要
        if result.get('status') == 'success':
            planner_stats = result.get('planner_stats', {})
            executor_stats = result.get('executor_stats', {})
            
            print(f"\n  📊 执行摘要:")
            print(f"    - Planner: {planner_stats.get('completed_tasks', 0)} 任务完成")
            print(f"    - Executor: {executor_stats.get('inspiration_executor_1', {}).get('completed_tasks', 0)} 任务完成")
        
    except Exception as e:
        cycle_time = time.time() - cycle_start
        monitor.record_task('inspiration_cycle', cycle_time, success=False)
        print(f"  ❌ 周期失败: {e}")
        result = {'status': 'failed', 'error': str(e)}
    
    # 5. 停止系统
    print("\n[5/5] 停止系统...")
    system.stop()
    monitor.stop_monitoring()
    
    # 6. 学习反馈
    print("\n[6/6] 记录学习反馈...")
    feedback = LearningFeedback()
    feedback.record_execution(result, monitor.get_report())
    
    # 7. 生成报告
    total_time = time.time() - start_time
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'status': result.get('status', 'unknown'),
        'startup_time': startup_time,
        'cycle_time': cycle_time,
        'total_time': total_time,
        'performance': monitor.get_report(),
        'learning': feedback.get_learning_report()
    }
    
    # 保存报告
    report_dir = Path(__file__).parent.parent / "production_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"production_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # 打印报告
    print("\n" + "="*70)
    print("📊 生产运行报告")
    print("="*70)
    print(f"状态: {'✅ 成功' if report['status'] == 'success' else '❌ 失败'}")
    print(f"启动时间: {startup_time:.2f}s")
    print(f"周期时间: {cycle_time:.2f}s")
    print(f"总时间: {total_time:.2f}s")
    print(f"成功率: {monitor.get_report()['success_rate']*100:.1f}%")
    print(f"报告文件: {report_file}")
    print("="*70)
    
    return report


def main():
    """主函数"""
    try:
        report = run_production_cycle()
        
        if report['status'] == 'success':
            print("\n🎉 生产运行成功完成！")
            return 0
        else:
            print("\n⚠️ 生产运行失败，请检查日志。")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        return 130
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
