#!/usr/bin/env python3
"""
Performance Monitor - 性能监控器

监控双代理系统的性能和稳定性

Author: wdai
Date: 2026-03-19
"""

import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading


class PerformanceMonitor:
    """
    性能监控器
    
    监控指标:
    - 任务执行时间
    - 成功率
    - 资源使用
    - 错误率
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path(__file__).parent.parent / "metrics"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 指标存储
        self.metrics = {
            'task_times': [],           # 任务执行时间
            'success_count': 0,
            'failure_count': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': None
        }
        
        # 运行状态
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self):
        """开始监控"""
        self._running = True
        self.metrics['start_time'] = datetime.now().isoformat()
        
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        print("[PerformanceMonitor] 性能监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        
        self.metrics['end_time'] = datetime.now().isoformat()
        
        # 保存指标
        self._save_metrics()
        
        print("[PerformanceMonitor] 性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            # 每10秒记录一次系统状态
            time.sleep(10)
            
            if self._running:
                self._record_snapshot()
    
    def _record_snapshot(self):
        """记录系统快照"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': self._calculate_uptime(),
            'success_rate': self._calculate_success_rate(),
            'avg_task_time': self._calculate_avg_task_time()
        }
        
        # 保存快照
        snapshot_file = self.log_dir / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
    
    def record_task(self, task_type: str, elapsed: float, success: bool):
        """记录任务执行"""
        self.metrics['task_times'].append({
            'type': task_type,
            'elapsed': elapsed,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })
        
        if success:
            self.metrics['success_count'] += 1
        else:
            self.metrics['failure_count'] += 1
    
    def record_cache(self, hit: bool):
        """记录缓存命中"""
        if hit:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        total = self.metrics['success_count'] + self.metrics['failure_count']
        if total == 0:
            return 1.0
        return self.metrics['success_count'] / total
    
    def _calculate_avg_task_time(self) -> float:
        """计算平均任务时间"""
        if not self.metrics['task_times']:
            return 0.0
        
        times = [t['elapsed'] for t in self.metrics['task_times']]
        return sum(times) / len(times)
    
    def _calculate_uptime(self) -> float:
        """计算运行时间"""
        if not self.metrics['start_time']:
            return 0.0
        
        start = datetime.fromisoformat(self.metrics['start_time'])
        return (datetime.now() - start).total_seconds()
    
    def get_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'uptime_seconds': self._calculate_uptime(),
            'tasks_completed': self.metrics['success_count'],
            'tasks_failed': self.metrics['failure_count'],
            'success_rate': self._calculate_success_rate(),
            'avg_task_time': self._calculate_avg_task_time(),
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        hits = self.metrics['cache_hits']
        misses = self.metrics['cache_misses']
        total = hits + misses
        
        if total == 0:
            return 0.0
        return hits / total
    
    def _save_metrics(self):
        """保存指标到文件"""
        metrics_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(metrics_file, 'w') as f:
            json.dump({
                'summary': self.get_report(),
                'details': self.metrics
            }, f, indent=2)
        
        print(f"[PerformanceMonitor] 指标已保存: {metrics_file}")
    
    def print_report(self):
        """打印性能报告"""
        report = self.get_report()
        
        print("\n" + "="*60)
        print("📊 性能监控报告")
        print("="*60)
        print(f"运行时间: {report['uptime_seconds']:.1f}s")
        print(f"任务完成: {report['tasks_completed']}")
        print(f"任务失败: {report['tasks_failed']}")
        print(f"成功率: {report['success_rate']*100:.1f}%")
        print(f"平均任务时间: {report['avg_task_time']:.2f}s")
        print(f"缓存命中率: {report['cache_hit_rate']*100:.1f}%")
        print("="*60)


class LearningFeedback:
    """
    学习反馈系统
    
    记录双代理架构的效果，调整策略参数
    """
    
    def __init__(self, feedback_dir: Optional[Path] = None):
        self.feedback_dir = feedback_dir or Path(__file__).parent.parent / "feedback"
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        
        # 反馈记录
        self.feedbacks: List[Dict] = []
        
        # 模式置信度
        self.pattern_confidence = {
            'dual_agent_better': 0.8,      # 双代理比单体好
            'deep_analysis_valuable': 0.9,  # 深度分析有价值
            'auto_insight_works': 0.7       # 自动洞察有效
        }
    
    def record_execution(self, cycle_result: Dict, performance: Dict):
        """记录执行反馈"""
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'cycle_result': cycle_result,
            'performance': performance,
            'patterns_observed': self._analyze_patterns(cycle_result)
        }
        
        self.feedbacks.append(feedback)
        
        # 更新模式置信度
        self._update_confidence(feedback)
        
        # 保存反馈
        self._save_feedback(feedback)
    
    def _analyze_patterns(self, result: Dict) -> List[str]:
        """分析观察到的模式"""
        patterns = []
        
        if result.get('status') == 'success':
            patterns.append('successful_cycle')
        
        if result.get('phases_completed', 0) >= 5:
            patterns.append('all_phases_complete')
        
        planner_stats = result.get('planner_stats', {})
        if planner_stats.get('completed_tasks', 0) > 0:
            patterns.append('tasks_completed')
        
        return patterns
    
    def _update_confidence(self, feedback: Dict):
        """更新模式置信度"""
        patterns = feedback.get('patterns_observed', [])
        
        # 成功则增加置信度，失败则降低
        delta = 0.05 if feedback['cycle_result'].get('status') == 'success' else -0.05
        
        if 'successful_cycle' in patterns:
            self.pattern_confidence['dual_agent_better'] += delta
        
        if 'all_phases_complete' in patterns:
            self.pattern_confidence['deep_analysis_valuable'] += delta
        
        # 限制范围
        for key in self.pattern_confidence:
            self.pattern_confidence[key] = max(0.0, min(1.0, self.pattern_confidence[key]))
    
    def _save_feedback(self, feedback: Dict):
        """保存反馈"""
        feedback_file = self.feedback_dir / f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(feedback_file, 'w') as f:
            json.dump(feedback, f, indent=2)
    
    def get_learning_report(self) -> Dict[str, Any]:
        """获取学习报告"""
        total_feedbacks = len(self.feedbacks)
        successful = sum(1 for f in self.feedbacks if f['cycle_result'].get('status') == 'success')
        
        return {
            'total_executions': total_feedbacks,
            'successful_executions': successful,
            'success_rate': successful / total_feedbacks if total_feedbacks > 0 else 0,
            'pattern_confidence': self.pattern_confidence,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成学习建议"""
        recommendations = []
        
        if self.pattern_confidence['dual_agent_better'] > 0.8:
            recommendations.append("双代理架构效果显著，建议全面采用")
        
        if self.pattern_confidence['deep_analysis_valuable'] > 0.8:
            recommendations.append("深度分析模块效果良好，保持当前配置")
        
        if self.pattern_confidence['auto_insight_works'] < 0.5:
            recommendations.append("自动洞察功能需要优化，考虑调整参数")
        
        return recommendations
    
    def print_report(self):
        """打印学习报告"""
        report = self.get_learning_report()
        
        print("\n" + "="*60)
        print("🧠 学习反馈报告")
        print("="*60)
        print(f"总执行次数: {report['total_executions']}")
        print(f"成功次数: {report['successful_executions']}")
        print(f"成功率: {report['success_rate']*100:.1f}%")
        
        print("\n模式置信度:")
        for pattern, confidence in report['pattern_confidence'].items():
            bar = '█' * int(confidence * 20)
            print(f"  {pattern}: [{bar}] {confidence*100:.1f}%")
        
        print("\n建议:")
        for rec in report['recommendations']:
            print(f"  💡 {rec}")
        
        print("="*60)


def test_monitor_and_feedback():
    """测试监控和反馈"""
    print("="*60)
    print("测试性能监控和学习反馈")
    print("="*60)
    
    # 测试性能监控
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # 模拟一些任务
    for i in range(5):
        time.sleep(0.1)
        monitor.record_task('fetch', 0.5 + i*0.1, success=True)
        monitor.record_cache(hit=i % 2 == 0)
    
    monitor.stop_monitoring()
    monitor.print_report()
    
    # 测试学习反馈
    feedback = LearningFeedback()
    
    # 模拟执行反馈
    feedback.record_execution(
        cycle_result={'status': 'success', 'phases_completed': 5},
        performance={'tasks_completed': 3, 'elapsed': 2.5}
    )
    
    feedback.print_report()
    
    print("\n✅ 监控和反馈测试完成")


if __name__ == '__main__':
    test_monitor_and_feedback()
