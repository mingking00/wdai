#!/usr/bin/env python3
"""
WDai 持续自我校准系统 (Continuous Self-Calibration)
隐式反馈收集 + 自动权重校准
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class FeedbackRecord:
    """反馈记录"""
    query: str
    results_shown: List[str]
    clicked: List[str]  # 用户点击的结果
    ignored: List[str]  # 用户忽略的结果
    dwell_time_ms: Dict[str, int]  # 停留时间
    timestamp: str


class SelfCalibrationSystem:
    """自我校准系统"""
    
    def __init__(self, workspace: str = "/root/.openclaw/workspace"):
        self.workspace = Path(workspace)
        self.calibration_dir = self.workspace / ".claw-status" / "calibration"
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        
        # 反馈记录
        self.feedback_file = self.calibration_dir / "implicit_feedback.jsonl"
        
        # 权重配置
        self.weights_file = self.calibration_dir / "adaptive_weights.json"
        self.weights = self._load_weights()
        
        # 校准参数
        self.learning_rate = 0.05
        self.min_samples = 10  # 最小样本数才校准
        
        # 缓存统计
        self._stats_cache = None
        self._cache_time = None
    
    def _load_weights(self) -> Dict[str, float]:
        """加载自适应权重"""
        if self.weights_file.exists():
            try:
                with open(self.weights_file) as f:
                    data = json.load(f)
                    # 只返回权重字段
                    return {k: v for k, v in data.items() 
                            if k not in ['last_updated', 'calibration_count']}
            except (json.JSONDecodeError, ValueError):
                pass
        
        # 默认权重
        return {
            'immediate': 0.15,
            'session': 0.20,
            'project': 0.30,
            'domain': 0.25,
            'universal': 0.10
        }
    
    def _save_weights(self):
        """保存权重"""
        current_count = self._get_calibration_count()
        with open(self.weights_file, 'w') as f:
            json.dump({
                **self.weights,
                'last_updated': datetime.now().isoformat(),
                'calibration_count': current_count + 1
            }, f, indent=2)
    
    def record_interaction(self, query: str, results: List[Dict], 
                          clicked_indices: List[int] = None,
                          dwell_times: Dict[int, int] = None):
        """
        记录用户交互（隐式反馈）
        
        Args:
            query: 查询内容
            results: 显示的结果列表
            clicked_indices: 用户点击的结果索引
            dwell_times: 各结果的停留时间（毫秒）
        """
        clicked = []
        ignored = []
        dwell_time_dict = {}
        
        for i, result in enumerate(results):
            result_id = f"{result.get('layer', 'unknown')}-{result.get('source', 'unknown')}"
            
            if clicked_indices and i in clicked_indices:
                clicked.append(result_id)
                dwell_time_dict[result_id] = dwell_times.get(i, 1000) if dwell_times else 1000
            else:
                ignored.append(result_id)
                dwell_time_dict[result_id] = dwell_times.get(i, 0) if dwell_times else 0
        
        record = FeedbackRecord(
            query=query,
            results_shown=[f"{r.get('layer')}-{r.get('source')}" for r in results],
            clicked=clicked,
            ignored=ignored,
            dwell_time_ms=dwell_time_dict,
            timestamp=datetime.now().isoformat()
        )
        
        # 追加记录
        with open(self.feedback_file, 'a') as f:
            f.write(json.dumps(asdict(record)) + '\n')
        
        # 触发校准（如果样本足够）
        if self._should_calibrate():
            self.calibrate()
    
    def _should_calibrate(self) -> bool:
        """检查是否应该执行校准"""
        if not self.feedback_file.exists():
            return False
        
        # 计算记录数
        count = sum(1 for _ in open(self.feedback_file))
        return count >= self.min_samples and count % 10 == 0  # 每10条校准一次
    
    def calibrate(self):
        """执行权重校准"""
        print("🔄 执行权重校准...")
        
        feedbacks = self._load_recent_feedback(100)
        
        # 计算各层的点击率
        layer_stats = defaultdict(lambda: {'shown': 0, 'clicked': 0, 'dwell': 0})
        
        for record in feedbacks:
            for result_id in record['results_shown']:
                layer = result_id.split('-')[0]
                layer_stats[layer]['shown'] += 1
            
            for clicked_id in record['clicked']:
                layer = clicked_id.split('-')[0]
                layer_stats[layer]['clicked'] += 1
                layer_stats[layer]['dwell'] += record['dwell_time_ms'].get(clicked_id, 0)
        
        # 计算新的权重
        new_weights = {}
        for layer in ['immediate', 'session', 'project', 'domain', 'universal']:
            stats = layer_stats[layer]
            if stats['shown'] > 0:
                ctr = stats['clicked'] / stats['shown']
                avg_dwell = stats['dwell'] / stats['clicked'] if stats['clicked'] > 0 else 0
                
                # 综合得分：点击率 * 归一化停留时间
                score = ctr * (1 + min(avg_dwell / 5000, 1))  # 5秒为基准
                new_weights[layer] = score
            else:
                new_weights[layer] = self.weights[layer]
        
        # 归一化
        total = sum(new_weights.values())
        if total > 0:
            new_weights = {k: v/total for k, v in new_weights.items()}
        
        # 平滑更新（EMA）
        for layer in self.weights:
            self.weights[layer] = (
                self.weights[layer] * (1 - self.learning_rate) +
                new_weights[layer] * self.learning_rate
            )
        
        # 再次归一化
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
        
        self._save_weights()
        print(f"   ✅ 校准完成，新权重: {self.weights}")
    
    def _load_recent_feedback(self, n: int = 100) -> List[Dict]:
        """加载最近n条反馈"""
        if not self.feedback_file.exists():
            return []
        
        lines = []
        with open(self.feedback_file) as f:
            lines = f.readlines()
        
        # 返回最近n条
        return [json.loads(line) for line in lines[-n:]]
    
    def _get_calibration_count(self) -> int:
        """获取校准次数"""
        if self.weights_file.exists():
            try:
                with open(self.weights_file) as f:
                    data = json.load(f)
                    return data.get('calibration_count', 0)
            except (json.JSONDecodeError, ValueError):
                return 0
        return 0
    
    def get_weights(self) -> Dict[str, float]:
        """获取当前权重"""
        return self.weights.copy()
    
    def get_feedback_stats(self) -> Dict:
        """获取反馈统计"""
        feedbacks = self._load_recent_feedback(1000)
        
        if not feedbacks:
            return {'message': '暂无反馈记录'}
        
        total_queries = len(feedbacks)
        total_clicks = sum(len(f['clicked']) for f in feedbacks)
        total_ignored = sum(len(f['ignored']) for f in feedbacks)
        
        # 计算各层表现
        layer_performance = defaultdict(lambda: {'shown': 0, 'clicked': 0})
        for record in feedbacks:
            for result_id in record['results_shown']:
                layer = result_id.split('-')[0]
                layer_performance[layer]['shown'] += 1
            for clicked_id in record['clicked']:
                layer = clicked_id.split('-')[0]
                layer_performance[layer]['clicked'] += 1
        
        layer_ctr = {}
        for layer, stats in layer_performance.items():
            if stats['shown'] > 0:
                layer_ctr[layer] = f"{stats['clicked']/stats['shown']*100:.1f}%"
        
        return {
            'total_queries': total_queries,
            'total_clicks': total_clicks,
            'total_ignored': total_ignored,
            'avg_clicks_per_query': f"{total_clicks/total_queries:.2f}",
            'layer_ctr': layer_ctr,
            'current_weights': self.weights
        }
    
    def generate_weekly_report(self) -> str:
        """生成周校准报告"""
        # 获取本周反馈
        week_ago = datetime.now() - timedelta(days=7)
        feedbacks = self._load_recent_feedback(1000)
        
        week_feedbacks = [
            f for f in feedbacks 
            if datetime.fromisoformat(f['timestamp']) > week_ago
        ]
        
        if not week_feedbacks:
            return "本周暂无反馈数据"
        
        report = []
        report.append("=" * 60)
        report.append("WDai 周校准报告")
        report.append(f"周期: {week_ago.strftime('%Y-%m-%d')} ~ {datetime.now().strftime('%Y-%m-%d')}")
        report.append("=" * 60)
        
        report.append(f"\n📊 总体统计")
        report.append(f"   查询数: {len(week_feedbacks)}")
        report.append(f"   点击数: {sum(len(f['clicked']) for f in week_feedbacks)}")
        
        report.append(f"\n⚖️ 当前权重")
        for layer, weight in self.weights.items():
            report.append(f"   {layer}: {weight:.3f}")
        
        report.append(f"\n📈 各层点击率")
        stats = self.get_feedback_stats()
        for layer, ctr in stats.get('layer_ctr', {}).items():
            report.append(f"   {layer}: {ctr}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


def main():
    """演示"""
    calibrator = SelfCalibrationSystem()
    
    print("=" * 60)
    print("持续自我校准系统演示")
    print("=" * 60)
    
    # 模拟一些反馈
    print("\n📝 模拟用户交互...")
    
    for i in range(15):
        query = f"测试查询 {i}"
        results = [
            {'layer': 'immediate', 'source': f'imm-{i}'},
            {'layer': 'session', 'source': f'ses-{i}'},
            {'layer': 'project', 'source': f'proj-{i}'},
        ]
        
        # 模拟用户偏好 project 层
        clicked = [2] if i % 3 == 0 else []
        dwell = {2: 8000} if clicked else {}
        
        calibrator.record_interaction(query, results, clicked, dwell)
        print(f"   记录 {i+1}: 点击={len(clicked) > 0}")
    
    print("\n📊 反馈统计:")
    stats = calibrator.get_feedback_stats()
    print(f"   查询数: {stats.get('total_queries', 0)}")
    print(f"   权重: {calibrator.get_weights()}")
    
    print("\n📈 周报告:")
    print(calibrator.generate_weekly_report())
    
    print("=" * 60)


if __name__ == "__main__":
    main()
