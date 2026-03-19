#!/usr/bin/env python3
"""
Phase 5: Feedback Learning Layer - 反馈学习层

核心能力:
1. 运行时监控 - 追踪修改效果和系统状态
2. 效果量化评估 - 客观衡量修改影响
3. 成功/失败归因 - 分析什么因素导致结果
4. 策略学习 - 强化学习优化决策
5. 元学习 - 学习如何学习

这是闭环系统的最后一块拼图：从执行结果中学习，改进未来决策。

Author: wdai
Version: 1.0 - Phase 5 Implementation
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import statistics

# 导入前面的Phase
import sys
sys.path.insert(0, str(Path(__file__).parent))

try:
    from code_understanding import CodeUnderstandingLayer, FunctionInfo
    from creative_design import DesignCandidate
    from formal_verification import FormalVerificationLayer, VerificationResult
    from sandbox_testing import SandboxTestReport, PerformanceMetrics
    PHASE1_AVAILABLE = True
    PHASE2_AVAILABLE = True
    PHASE3_AVAILABLE = True
    PHASE4_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False
    PHASE2_AVAILABLE = False
    PHASE3_AVAILABLE = False
    PHASE4_AVAILABLE = False


@dataclass
class ModificationRecord:
    """修改记录"""
    id: str
    timestamp: str
    design_id: str
    pattern_id: str
    target_file: str
    changes: List[Dict]
    risk_score: int
    
    # 执行结果
    deployed: bool = False
    deployed_at: Optional[str] = None
    
    # 运行时监控数据
    runtime_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 效果评估
    success: Optional[bool] = None
    performance_delta: Dict[str, float] = field(default_factory=dict)
    reliability_delta: Dict[str, float] = field(default_factory=dict)
    
    # 归因分析
    attribution: Dict[str, Any] = field(default_factory=dict)
    
    # 学习反馈
    learned_insights: List[str] = field(default_factory=list)


@dataclass
class RuntimeMetric:
    """运行时指标"""
    timestamp: str
    metric_name: str
    value: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningEpisode:
    """学习片段"""
    id: str
    pattern_id: str
    attempts: int
    successes: int
    failures: int
    avg_performance_gain: float
    confidence: float
    last_updated: str


@dataclass
class StrategyUpdate:
    """策略更新"""
    strategy_name: str
    old_weight: float
    new_weight: float
    reason: str
    evidence: List[str]
    updated_at: str


class RuntimeMonitor:
    """
    运行时监控
    
    追踪系统运行状态和修改效果
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / "data"
        self.metrics: List[RuntimeMetric] = []
        self.active_monitors: Dict[str, Callable] = {}
        
        # 监控埋点
        self.hooks = {
            'pre_execution': [],
            'post_execution': [],
            'on_error': [],
            'on_success': []
        }
    
    def register_monitor(self, name: str, monitor_fn: Callable):
        """注册监控函数"""
        self.active_monitors[name] = monitor_fn
        print(f"   📊 注册监控: {name}")
    
    def record_metric(self, name: str, value: float, context: Dict = None):
        """记录运行时指标"""
        metric = RuntimeMetric(
            timestamp=datetime.now().isoformat(),
            metric_name=name,
            value=value,
            context=context or {}
        )
        self.metrics.append(metric)
        
        # 保存到文件
        self._persist_metric(metric)
    
    def _persist_metric(self, metric: RuntimeMetric):
        """持久化指标"""
        metrics_file = self.data_dir / "runtime_metrics.jsonl"
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metrics_file, 'a') as f:
            f.write(json.dumps({
                'timestamp': metric.timestamp,
                'metric_name': metric.metric_name,
                'value': metric.value,
                'context': metric.context
            }) + '\n')
    
    def start_monitoring(self, modification_id: str):
        """开始监控修改"""
        print(f"   🔍 开始监控修改: {modification_id}")
        
        # 记录基线指标
        self.record_metric(
            f"mod_{modification_id}_baseline",
            0.0,
            {'modification_id': modification_id, 'phase': 'baseline'}
        )
    
    def collect_post_deployment_metrics(self, modification_id: str) -> Dict[str, float]:
        """收集部署后的指标"""
        print(f"   📈 收集部署后指标...")
        
        # 模拟收集指标（实际应该查询监控系统）
        metrics = {
            'execution_time_ms': 100.0,  # 示例
            'error_rate': 0.01,
            'throughput': 1000.0,
            'memory_usage_mb': 50.0
        }
        
        for name, value in metrics.items():
            self.record_metric(
                f"mod_{modification_id}_{name}",
                value,
                {'modification_id': modification_id, 'phase': 'post_deployment'}
            )
        
        return metrics


class EffectivenessEvaluator:
    """
    效果量化评估
    
    客观衡量修改的影响
    """
    
    def __init__(self, monitor: RuntimeMonitor):
        self.monitor = monitor
    
    def evaluate_modification(self, record: ModificationRecord,
                             baseline_metrics: Dict[str, float],
                             current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        评估修改效果
        
        返回量化的效果评估结果
        """
        print(f"   📊 评估修改效果...")
        
        evaluation = {
            'modification_id': record.id,
            'evaluated_at': datetime.now().isoformat(),
            'performance_delta': {},
            'reliability_delta': {},
            'maintainability_delta': {},
            'overall_score': 0.0,
            'success': False
        }
        
        # 1. 性能变化
        if 'execution_time_ms' in baseline_metrics and 'execution_time_ms' in current_metrics:
            baseline_time = baseline_metrics['execution_time_ms']
            current_time = current_metrics['execution_time_ms']
            
            if baseline_time > 0:
                time_change = (baseline_time - current_time) / baseline_time * 100
                evaluation['performance_delta']['execution_time'] = time_change
                print(f"      执行时间变化: {time_change:+.1f}%")
        
        if 'throughput' in baseline_metrics and 'throughput' in current_metrics:
            baseline_tp = baseline_metrics['throughput']
            current_tp = current_metrics['throughput']
            
            if baseline_tp > 0:
                tp_change = (current_tp - baseline_tp) / baseline_tp * 100
                evaluation['performance_delta']['throughput'] = tp_change
                print(f"      吞吐量变化: {tp_change:+.1f}%")
        
        # 2. 可靠性变化
        if 'error_rate' in baseline_metrics and 'error_rate' in current_metrics:
            baseline_err = baseline_metrics['error_rate']
            current_err = current_metrics['error_rate']
            
            if baseline_err > 0:
                err_change = (baseline_err - current_err) / baseline_err * 100
                evaluation['reliability_delta']['error_rate'] = err_change
                print(f"      错误率变化: {err_change:+.1f}%")
        
        # 3. 综合评分
        score = 0.0
        weights = {
            'performance': 0.4,
            'reliability': 0.4,
            'maintainability': 0.2
        }
        
        # 性能评分（吞吐量提升为正）
        perf_score = evaluation['performance_delta'].get('throughput', 0)
        score += perf_score * weights['performance']
        
        # 可靠性评分（错误率降低为正）
        rel_score = evaluation['reliability_delta'].get('error_rate', 0)
        score += rel_score * weights['reliability']
        
        evaluation['overall_score'] = score
        
        # 4. 判断是否成功（简化：综合评分>0认为成功）
        evaluation['success'] = score > 0
        
        print(f"      综合评分: {score:+.1f}")
        print(f"      评估结果: {'✅ 成功' if evaluation['success'] else '❌ 失败'}")
        
        return evaluation


class AttributionAnalyzer:
    """
    归因分析器
    
    分析什么因素导致了成功或失败
    """
    
    def analyze(self, record: ModificationRecord, 
                evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析成功/失败的原因
        
        返回归因分析结果
        """
        print(f"   🔍 归因分析...")
        
        attribution = {
            'modification_id': record.id,
            'analyzed_at': datetime.now().isoformat(),
            'success_factors': [],
            'failure_factors': [],
            'pattern_effectiveness': 0.5,
            'risk_accuracy': 0.5
        }
        
        # 1. 分析风险评分准确性
        predicted_risk = record.risk_score
        actual_success = evaluation['success']
        
        # 如果预测高风险但实际成功，或预测低风险但实际失败，说明风险评估不准确
        if predicted_risk > 50 and actual_success:
            attribution['risk_accuracy'] = 0.3
            attribution['success_factors'].append("实际比预期更安全")
        elif predicted_risk < 30 and not actual_success:
            attribution['risk_accuracy'] = 0.3
            attribution['failure_factors'].append("风险评估低估")
        else:
            attribution['risk_accuracy'] = 0.8
        
        # 2. 分析模式有效性
        if actual_success:
            attribution['pattern_effectiveness'] = 0.8
            attribution['success_factors'].append(f"模式 {record.pattern_id} 有效")
        else:
            attribution['pattern_effectiveness'] = 0.2
            attribution['failure_factors'].append(f"模式 {record.pattern_id} 不适用")
        
        # 3. 分析其他因素
        if evaluation['performance_delta'].get('throughput', 0) < -10:
            attribution['failure_factors'].append("性能严重下降")
        
        if evaluation['reliability_delta'].get('error_rate', -100) < -50:
            attribution['failure_factors'].append("可靠性恶化")
        
        print(f"      模式有效性: {attribution['pattern_effectiveness']:.1%}")
        print(f"      风险准确性: {attribution['risk_accuracy']:.1%}")
        print(f"      成功因素: {len(attribution['success_factors'])}")
        print(f"      失败因素: {len(attribution['failure_factors'])}")
        
        return attribution


class ReinforcementLearner:
    """
    强化学习器
    
    基于反馈优化决策策略
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / "data"
        self.episodes: Dict[str, LearningEpisode] = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        
        # 加载历史学习记录
        self._load_episodes()
    
    def _load_episodes(self):
        """加载学习历史"""
        episodes_file = self.data_dir / "learning_episodes.json"
        if episodes_file.exists():
            with open(episodes_file) as f:
                data = json.load(f)
                for ep_data in data:
                    episode = LearningEpisode(**ep_data)
                    self.episodes[episode.pattern_id] = episode
    
    def _save_episodes(self):
        """保存学习历史"""
        episodes_file = self.data_dir / "learning_episodes.json"
        episodes_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(episodes_file, 'w') as f:
            json.dump([asdict(ep) for ep in self.episodes.values()], f, indent=2)
    
    def update_from_outcome(self, record: ModificationRecord,
                           evaluation: Dict[str, Any],
                           attribution: Dict[str, Any]):
        """
        从执行结果更新学习
        
        强化学习更新
        """
        print(f"   🧠 强化学习更新...")
        
        pattern_id = record.pattern_id
        
        # 获取或创建学习片段
        if pattern_id not in self.episodes:
            self.episodes[pattern_id] = LearningEpisode(
                id=self._generate_id(),
                pattern_id=pattern_id,
                attempts=0,
                successes=0,
                failures=0,
                avg_performance_gain=0.0,
                confidence=0.5,
                last_updated=datetime.now().isoformat()
            )
        
        episode = self.episodes[pattern_id]
        
        # 更新统计
        episode.attempts += 1
        if evaluation['success']:
            episode.successes += 1
        else:
            episode.failures += 1
        
        # 更新平均性能增益（移动平均）
        perf_gain = evaluation['performance_delta'].get('throughput', 0)
        episode.avg_performance_gain = (
            episode.avg_performance_gain * 0.9 + perf_gain * 0.1
        )
        
        # 更新置信度（基于成功率）
        success_rate = episode.successes / episode.attempts if episode.attempts > 0 else 0.5
        episode.confidence = 0.5 + (success_rate - 0.5) * 0.8  # 映射到0.1-0.9
        
        episode.last_updated = datetime.now().isoformat()
        
        print(f"      模式: {pattern_id}")
        print(f"      尝试次数: {episode.attempts}")
        print(f"      成功率: {success_rate:.1%}")
        print(f"      平均性能增益: {episode.avg_performance_gain:+.1f}%")
        print(f"      置信度: {episode.confidence:.2f}")
        
        # 保存
        self._save_episodes()
    
    def get_pattern_confidence(self, pattern_id: str) -> float:
        """获取模式的置信度"""
        if pattern_id in self.episodes:
            return self.episodes[pattern_id].confidence
        return 0.5  # 默认值
    
    def get_strategy_recommendation(self, pattern_id: str) -> str:
        """获取策略建议"""
        if pattern_id not in self.episodes:
            return "没有历史数据，建议小规模试验"
        
        episode = self.episodes[pattern_id]
        
        if episode.confidence > 0.7:
            return f"模式表现优秀（置信度{episode.confidence:.2f}），可以放心使用"
        elif episode.confidence < 0.3:
            return f"模式表现不佳（置信度{episode.confidence:.2f}），建议避免或大幅修改"
        else:
            return f"模式表现一般（置信度{episode.confidence:.2f}），需要更多数据"
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return hashlib.md5(
            f"{time.time()}".encode()
        ).hexdigest()[:12]


class MetaLearner:
    """
    元学习器
    
    学习如何学习 - 改进学习策略本身
    """
    
    def __init__(self, learner: ReinforcementLearner):
        self.learner = learner
        self.meta_strategies: Dict[str, float] = {
            'exploration_rate': 0.3,  # 探索率
            'risk_aversion': 0.5,     # 风险厌恶
            'learning_rate': 0.1,     # 学习率
        }
    
    def analyze_learning_effectiveness(self) -> Dict[str, Any]:
        """
        分析学习效果
        
        评估当前学习策略是否有效
        """
        print(f"   🔬 元学习分析...")
        
        analysis = {
            'total_episodes': len(self.learner.episodes),
            'avg_confidence': 0.0,
            'high_confidence_patterns': 0,
            'low_confidence_patterns': 0,
            'suggestions': []
        }
        
        if not self.learner.episodes:
            analysis['suggestions'].append("数据不足，需要更多学习样本")
            return analysis
        
        # 统计
        confidences = [ep.confidence for ep in self.learner.episodes.values()]
        analysis['avg_confidence'] = statistics.mean(confidences)
        analysis['high_confidence_patterns'] = sum(1 for c in confidences if c > 0.7)
        analysis['low_confidence_patterns'] = sum(1 for c in confidences if c < 0.3)
        
        print(f"      总片段数: {analysis['total_episodes']}")
        print(f"      平均置信度: {analysis['avg_confidence']:.2f}")
        print(f"      高置信度模式: {analysis['high_confidence_patterns']}")
        print(f"      低置信度模式: {analysis['low_confidence_patterns']}")
        
        # 生成改进建议
        if analysis['avg_confidence'] < 0.5:
            analysis['suggestions'].append("整体置信度偏低，建议提高探索率以收集更多数据")
            self.meta_strategies['exploration_rate'] = min(0.5, self.meta_strategies['exploration_rate'] + 0.1)
        
        if analysis['low_confidence_patterns'] > analysis['high_confidence_patterns']:
            analysis['suggestions'].append("低置信度模式过多，建议加强风险评估")
            self.meta_strategies['risk_aversion'] = min(0.8, self.meta_strategies['risk_aversion'] + 0.1)
        
        if analysis['total_episodes'] > 10 and analysis['avg_confidence'] > 0.6:
            analysis['suggestions'].append("学习效果良好，可以适当降低探索率")
            self.meta_strategies['exploration_rate'] = max(0.1, self.meta_strategies['exploration_rate'] - 0.05)
        
        for suggestion in analysis['suggestions']:
            print(f"      💡 {suggestion}")
        
        return analysis
    
    def suggest_learning_improvements(self) -> List[str]:
        """
        建议学习系统的改进
        
        基于元学习分析提出系统改进建议
        """
        suggestions = []
        
        # 分析当前策略参数
        if self.meta_strategies['exploration_rate'] > 0.4:
            suggestions.append("探索率过高，可能浪费资源在低潜力模式上")
        
        if self.meta_strategies['risk_aversion'] < 0.3:
            suggestions.append("风险厌恶过低，可能过于激进")
        
        if len(self.learner.episodes) < 5:
            suggestions.append("学习样本不足，建议增加监控范围")
        
        return suggestions


class FeedbackLearningLayer:
    """
    反馈学习层 - 主入口
    
    整合所有学习能力
    """
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path(__file__).parent
        self.data_dir = self.project_path / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.monitor = RuntimeMonitor(self.data_dir)
        self.evaluator = EffectivenessEvaluator(self.monitor)
        self.attribution_analyzer = AttributionAnalyzer()
        self.learner = ReinforcementLearner(self.data_dir)
        self.meta_learner = MetaLearner(self.learner)
        
        # 修改记录存储
        self.modifications: Dict[str, ModificationRecord] = {}
        self._load_modifications()
    
    def _load_modifications(self):
        """加载历史修改记录"""
        mods_file = self.data_dir / "modifications.json"
        if mods_file.exists():
            with open(mods_file) as f:
                data = json.load(f)
                for mod_data in data:
                    record = ModificationRecord(**mod_data)
                    self.modifications[record.id] = record
    
    def _save_modifications(self):
        """保存修改记录"""
        mods_file = self.data_dir / "modifications.json"
        with open(mods_file, 'w') as f:
            json.dump([asdict(m) for m in self.modifications.values()], f, indent=2, default=str)
    
    def record_modification(self, design: Any, target_file: str) -> str:
        """
        记录一个修改
        
        在修改实施前调用
        """
        mod_id = self._generate_id()
        
        record = ModificationRecord(
            id=mod_id,
            timestamp=datetime.now().isoformat(),
            design_id=getattr(design, 'id', 'unknown'),
            pattern_id=getattr(design, 'pattern_id', 'unknown'),
            target_file=target_file,
            changes=[],
            risk_score=getattr(design, 'risk_score', 50)
        )
        
        self.modifications[mod_id] = record
        self._save_modifications()
        
        # 开始监控
        self.monitor.start_monitoring(mod_id)
        
        print(f"   📝 记录修改: {mod_id}")
        return mod_id
    
    def learn_from_deployment(self, mod_id: str, 
                             baseline_metrics: Dict[str, float] = None) -> Dict[str, Any]:
        """
        🆕 Phase 5: 从部署结果学习
        
        在修改部署后调用，进行完整的反馈学习
        """
        print("\n🧠 Phase 5: 反馈学习...")
        
        if mod_id not in self.modifications:
            return {'error': f'修改记录不存在: {mod_id}'}
        
        record = self.modifications[mod_id]
        
        # 1. 收集部署后指标
        print("   1. 收集运行时指标...")
        current_metrics = self.monitor.collect_post_deployment_metrics(mod_id)
        
        if baseline_metrics is None:
            # 使用模拟基线
            baseline_metrics = {
                'execution_time_ms': 110.0,
                'error_rate': 0.02,
                'throughput': 900.0,
                'memory_usage_mb': 55.0
            }
        
        record.runtime_metrics = current_metrics
        
        # 2. 评估效果
        print("   2. 评估修改效果...")
        evaluation = self.evaluator.evaluate_modification(
            record, baseline_metrics, current_metrics
        )
        
        record.success = evaluation['success']
        record.performance_delta = evaluation['performance_delta']
        
        # 3. 归因分析
        print("   3. 归因分析...")
        attribution = self.attribution_analyzer.analyze(record, evaluation)
        record.attribution = attribution
        
        # 4. 强化学习更新
        print("   4. 更新学习策略...")
        self.learner.update_from_outcome(record, evaluation, attribution)
        
        # 5. 生成学习洞察
        insights = self._generate_insights(record, evaluation, attribution)
        record.learned_insights = insights
        
        # 6. 元学习分析
        print("   5. 元学习分析...")
        meta_analysis = self.meta_learner.analyze_learning_effectiveness()
        
        # 更新记录
        record.deployed = True
        record.deployed_at = datetime.now().isoformat()
        self._save_modifications()
        
        # 返回学习结果
        result = {
            'modification_id': mod_id,
            'success': evaluation['success'],
            'overall_score': evaluation['overall_score'],
            'performance_delta': evaluation['performance_delta'],
            'reliability_delta': evaluation['reliability_delta'],
            'pattern_confidence': self.learner.get_pattern_confidence(record.pattern_id),
            'strategy_recommendation': self.learner.get_strategy_recommendation(record.pattern_id),
            'learned_insights': insights,
            'meta_suggestions': meta_analysis.get('suggestions', [])
        }
        
        print(f"\n✅ 反馈学习完成")
        print(f"   模式置信度: {result['pattern_confidence']:.2f}")
        print(f"   策略建议: {result['strategy_recommendation']}")
        
        return result
    
    def _generate_insights(self, record: ModificationRecord,
                          evaluation: Dict[str, Any],
                          attribution: Dict[str, Any]) -> List[str]:
        """生成学习洞察"""
        insights = []
        
        # 基于结果生成洞察
        if evaluation['success']:
            insights.append(f"模式 '{record.pattern_id}' 在本次场景中表现良好")
            
            if evaluation['performance_delta'].get('throughput', 0) > 10:
                insights.append("该模式能显著提升吞吐量")
        else:
            insights.append(f"模式 '{record.pattern_id}' 在本次场景中表现不佳")
            
            if attribution['failure_factors']:
                insights.append(f"主要原因: {', '.join(attribution['failure_factors'])}")
        
        # 风险评估洞察
        if attribution['risk_accuracy'] < 0.5:
            insights.append("风险评估需要校准")
        
        return insights
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """获取学习总结"""
        return {
            'total_modifications': len(self.modifications),
            'successful_modifications': sum(1 for m in self.modifications.values() if m.success),
            'failed_modifications': sum(1 for m in self.modifications.values() if m.success == False),
            'pattern_episodes': len(self.learner.episodes),
            'avg_pattern_confidence': statistics.mean(
                [ep.confidence for ep in self.learner.episodes.values()]
            ) if self.learner.episodes else 0.5
        }
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return hashlib.md5(
            f"{time.time()}".encode()
        ).hexdigest()[:12]


def main():
    """测试反馈学习层"""
    import sys
    
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path(__file__).parent
    
    print(f"\n分析项目: {project_path}\n")
    
    # 初始化反馈学习层
    learning_layer = FeedbackLearningLayer(project_path)
    
    # 创建测试设计方案
    from creative_design import DesignCandidate
    
    test_design = DesignCandidate(
        id="test_design_001",
        pattern_id="add_caching",
        description="添加缓存机制",
        changes=[],
        objectives={'performance': 0.8, 'maintainability': 0.2},
        constraints_satisfied=True,
        risk_score=30,
        confidence=0.8,
        reasoning="缓存能显著提升性能"
    )
    
    # 测试完整流程
    print("="*60)
    print("🧠 测试 Phase 5: 反馈学习层")
    print("="*60)
    
    # 1. 记录修改
    mod_id = learning_layer.record_modification(test_design, "scheduler.py")
    
    # 2. 从部署结果学习
    result = learning_layer.learn_from_deployment(mod_id)
    
    print("\n" + "="*60)
    print("📊 学习结果")
    print("="*60)
    print(f"修改ID: {result['modification_id']}")
    print(f"成功: {'是' if result['success'] else '否'}")
    print(f"综合评分: {result['overall_score']:+.1f}")
    print(f"性能变化: {result['performance_delta']}")
    print(f"模式置信度: {result['pattern_confidence']:.2f}")
    print(f"策略建议: {result['strategy_recommendation']}")
    print(f"学习洞察: {result['learned_insights']}")
    
    # 3. 学习总结
    print("\n" + "="*60)
    print("📈 学习总结")
    print("="*60)
    summary = learning_layer.get_learning_summary()
    print(f"总修改数: {summary['total_modifications']}")
    print(f"成功: {summary['successful_modifications']}")
    print(f"失败: {summary['failed_modifications']}")
    print(f"模式片段: {summary['pattern_episodes']}")
    print(f"平均置信度: {summary['avg_pattern_confidence']:.2f}")
    
    print("\n" + "="*60)
    print("✅ Phase 5 反馈学习层测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
