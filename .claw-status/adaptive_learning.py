#!/usr/bin/env python3
"""
WDai Adaptive Learning System
自适应学习系统 v1.0

核心功能:
1. 动态阈值调整 - 根据命中率自动优化
2. 反馈学习 - 从用户满意度学习
3. 模式识别 - 发现使用模式并预加载
4. 参数自动调优 - A/B测试风格优化

学习循环:
执行 → 收集反馈 → 分析效果 → 调整参数 → 验证改进
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import statistics
from collections import defaultdict, deque


@dataclass
class InteractionRecord:
    """交互记录"""
    timestamp: float
    query_type: str  # 'memory_search', 'tool_call', 'reasoning'
    query: str
    params: Dict
    result: Any
    success: bool
    user_feedback: Optional[str]  # 'satisfied', 'dissatisfied', 'neutral'
    performance_metrics: Dict  # 耗时、token等


@dataclass
class ParameterConfig:
    """参数配置"""
    name: str
    current_value: float
    min_value: float
    max_value: float
    adjustment_step: float
    history: List[Tuple[float, float, str]]  # (value, timestamp, reason)


class AdaptiveThresholdOptimizer:
    """
    自适应阈值优化器
    
    优化目标:
    - 快速路径阈值: 平衡命中率和准确率
    - 重试次数: 平衡成功率和延迟
    - 相似度阈值: 平衡召回和精确
    """
    
    def __init__(self, history_window: int = 100):
        self.history_window = history_window
        self.records: deque = deque(maxlen=history_window)
        
        # 可调整参数
        self.parameters: Dict[str, ParameterConfig] = {
            'fast_path_threshold': ParameterConfig(
                name='快速路径相似度阈值',
                current_value=0.92,
                min_value=0.70,
                max_value=0.98,
                adjustment_step=0.01,
                history=[]
            ),
            'cache_hit_target': ParameterConfig(
                name='目标缓存命中率',
                current_value=0.30,  # 目标30%查询走快速路径
                min_value=0.10,
                max_value=0.60,
                adjustment_step=0.05,
                history=[]
            ),
            'max_retry_attempts': ParameterConfig(
                name='最大重试次数',
                current_value=3.0,
                min_value=1.0,
                max_value=5.0,
                adjustment_step=1.0,
                history=[]
            ),
            'topic_switch_threshold': ParameterConfig(
                name='主题切换检测阈值',
                current_value=0.50,
                min_value=0.30,
                max_value=0.80,
                adjustment_step=0.05,
                history=[]
            ),
        }
        
        # 性能统计
        self.stats = {
            'fast_path_hits': 0,
            'fast_path_misses': 0,
            'tool_success': 0,
            'tool_failures': 0,
            'user_satisfied': 0,
            'user_dissatisfied': 0,
        }
    
    def record_interaction(self, record: InteractionRecord):
        """记录交互"""
        self.records.append(record)
        
        # 更新统计
        if record.query_type == 'fast_path':
            if record.success:
                self.stats['fast_path_hits'] += 1
            else:
                self.stats['fast_path_misses'] += 1
        
        if record.query_type == 'tool_call':
            if record.success:
                self.stats['tool_success'] += 1
            else:
                self.stats['tool_failures'] += 1
        
        if record.user_feedback == 'satisfied':
            self.stats['user_satisfied'] += 1
        elif record.user_feedback == 'dissatisfied':
            self.stats['user_dissatisfied'] += 1
    
    def analyze_and_adjust(self) -> List[Dict]:
        """
        分析并调整参数
        
        Returns:
            调整记录列表
        """
        adjustments = []
        
        # 1. 优化快速路径阈值
        adj = self._optimize_fast_path_threshold()
        if adj:
            adjustments.append(adj)
        
        # 2. 优化重试次数
        adj = self._optimize_retry_attempts()
        if adj:
            adjustments.append(adj)
        
        # 3. 优化主题切换阈值
        adj = self._optimize_topic_switch()
        if adj:
            adjustments.append(adj)
        
        return adjustments
    
    def _optimize_fast_path_threshold(self) -> Optional[Dict]:
        """优化快速路径阈值"""
        param = self.parameters['fast_path_threshold']
        target = self.parameters['cache_hit_target'].current_value
        
        # 计算当前命中率
        total = self.stats['fast_path_hits'] + self.stats['fast_path_misses']
        if total < 10:  # 数据不足
            return None
        
        current_rate = self.stats['fast_path_hits'] / total
        
        # 检查用户反馈
        feedback_adjustment = 0
        recent_records = [r for r in self.records if r.query_type == 'fast_path']
        
        for record in recent_records[-20:]:  # 最近20条
            if record.user_feedback == 'dissatisfied' and record.success:
                # 缓存命中但用户不满意 → 阈值太松
                feedback_adjustment += 0.02
            elif record.user_feedback == 'satisfied' and not record.success:
                # 未命中但用户满意 → 阈值太严
                feedback_adjustment -= 0.01
        
        # 综合决策
        old_value = param.current_value
        
        if current_rate < target * 0.8:  # 命中率低于目标20%
            # 降低阈值让更多查询匹配
            param.current_value = max(param.min_value, param.current_value - param.adjustment_step)
            reason = f"命中率{current_rate:.1%}低于目标{target:.1%}"
        elif current_rate > target * 1.2:  # 命中率高于目标20%
            # 提高阈值提高准确率
            param.current_value = min(param.max_value, param.current_value + param.adjustment_step)
            reason = f"命中率{current_rate:.1%}高于目标{target:.1%}"
        elif feedback_adjustment != 0:
            # 根据反馈调整
            param.current_value = max(param.min_value, min(param.max_value, 
                param.current_value + feedback_adjustment))
            reason = f"基于用户反馈调整({feedback_adjustment:+.2f})"
        else:
            return None
        
        # 记录历史
        param.history.append((param.current_value, datetime.now().timestamp(), reason))
        
        return {
            'parameter': param.name,
            'old_value': old_value,
            'new_value': param.current_value,
            'reason': reason,
            'current_hit_rate': current_rate,
            'target_hit_rate': target
        }
    
    def _optimize_retry_attempts(self) -> Optional[Dict]:
        """优化重试次数"""
        param = self.parameters['max_retry_attempts']
        
        total_tool_calls = self.stats['tool_success'] + self.stats['tool_failures']
        if total_tool_calls < 10:
            return None
        
        success_rate = self.stats['tool_success'] / total_tool_calls
        
        old_value = param.current_value
        
        if success_rate < 0.90 and param.current_value < param.max_value:
            # 成功率低，增加重试
            param.current_value = min(param.max_value, param.current_value + param.adjustment_step)
            reason = f"成功率{success_rate:.1%}偏低，增加重试容错"
        elif success_rate > 0.98 and param.current_value > param.min_value:
            # 成功率高，减少重试节省资源
            param.current_value = max(param.min_value, param.current_value - param.adjustment_step)
            reason = f"成功率{success_rate:.1%}优秀，减少重试次数"
        else:
            return None
        
        param.history.append((param.current_value, datetime.now().timestamp(), reason))
        
        return {
            'parameter': param.name,
            'old_value': old_value,
            'new_value': param.current_value,
            'reason': reason,
            'current_success_rate': success_rate
        }
    
    def _optimize_topic_switch(self) -> Optional[Dict]:
        """优化主题切换阈值"""
        param = self.parameters['topic_switch_threshold']
        
        # 分析压缩频率
        compression_records = [r for r in self.records if r.query_type == 'compression']
        if len(compression_records) < 5:
            return None
        
        # 如果压缩太频繁，提高阈值
        recent_compressions = len([r for r in compression_records 
                                   if r.timestamp > datetime.now().timestamp() - 3600])
        
        old_value = param.current_value
        
        if recent_compressions > 10:  # 1小时内压缩超过10次
            param.current_value = min(param.max_value, param.current_value + 0.1)
            reason = f"压缩过于频繁({recent_compressions}次/小时)"
        elif recent_compressions < 2:
            param.current_value = max(param.min_value, param.current_value - 0.05)
            reason = f"压缩频率偏低({recent_compressions}次/小时)"
        else:
            return None
        
        param.history.append((param.current_value, datetime.now().timestamp(), reason))
        
        return {
            'parameter': param.name,
            'old_value': old_value,
            'new_value': param.current_value,
            'reason': reason,
            'recent_compressions': recent_compressions
        }
    
    def get_parameter(self, name: str) -> float:
        """获取参数当前值"""
        if name in self.parameters:
            return self.parameters[name].current_value
        return 0.0
    
    def get_learning_report(self) -> Dict:
        """生成学习报告"""
        total_interactions = len(self.records)
        
        # 计算各类指标
        fast_path_total = self.stats['fast_path_hits'] + self.stats['fast_path_misses']
        fast_path_rate = self.stats['fast_path_hits'] / fast_path_total if fast_path_total > 0 else 0
        
        tool_total = self.stats['tool_success'] + self.stats['tool_failures']
        tool_success_rate = self.stats['tool_success'] / tool_total if tool_total > 0 else 0
        
        feedback_total = self.stats['user_satisfied'] + self.stats['user_dissatisfied']
        satisfaction_rate = self.stats['user_satisfied'] / feedback_total if feedback_total > 0 else 0
        
        return {
            'total_interactions': total_interactions,
            'current_parameters': {
                name: param.current_value 
                for name, param in self.parameters.items()
            },
            'performance_metrics': {
                'fast_path_hit_rate': fast_path_rate,
                'tool_success_rate': tool_success_rate,
                'user_satisfaction': satisfaction_rate,
            },
            'adjustment_history': [
                {
                    'parameter': param.name,
                    'adjustments': len(param.history),
                    'latest': param.history[-1] if param.history else None
                }
                for param in self.parameters.values()
            ]
        }


class PatternRecognizer:
    """
    模式识别器
    
    发现用户使用模式并预测下一步
    """
    
    def __init__(self):
        self.topic_sequences: List[List[str]] = []  # 话题序列历史
        self.query_patterns: Dict[str, List[str]] = defaultdict(list)  # 查询模式
        self.time_patterns: Dict[int, List[str]] = defaultdict(list)  # 时间模式
        
        # 预定义的话题链
        self.known_chains = {
            '向量存储': ['Qdrant配置', 'embedding模型', '相似度算法', '性能优化'],
            '工具调用': ['参数验证', '重试机制', '降级策略', '错误处理'],
            '记忆架构': ['分层设计', '压缩算法', '检索优化', '持久化'],
            '推理优化': ['多路径推理', '一致性检查', '置信度校准', '仲裁策略'],
        }
    
    def record_topic_sequence(self, topics: List[str]):
        """记录话题序列"""
        if len(topics) >= 2:
            self.topic_sequences.append(topics)
    
    def predict_next_topics(self, current_topic: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        预测接下来可能的话题
        
        Returns:
            [(话题, 概率), ...]
        """
        predictions = []
        
        # 1. 基于已知链
        if current_topic in self.known_chains:
            chain = self.known_chains[current_topic]
            for i, topic in enumerate(chain[:top_k]):
                predictions.append((topic, 0.9 - i * 0.1))
        
        # 2. 基于历史模式
        topic_counts = defaultdict(int)
        for sequence in self.topic_sequences:
            if current_topic in sequence:
                idx = sequence.index(current_topic)
                if idx + 1 < len(sequence):
                    next_topic = sequence[idx + 1]
                    topic_counts[next_topic] += 1
        
        # 合并预测
        # Sort by count and get top_k
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:top_k]
        for topic, count in sorted_topics:
            probability = min(0.8, count / len(self.topic_sequences)) if self.topic_sequences else 0.5
            predictions.append((topic, probability))
        
        # 去重并排序
        seen = set()
        unique_predictions = []
        for topic, prob in predictions:
            if topic not in seen and topic != current_topic:
                seen.add(topic)
                unique_predictions.append((topic, prob))
        
        return unique_predictions[:top_k]
    
    def get_time_based_suggestions(self, hour: int = None) -> List[str]:
        """基于时间的建议"""
        if hour is None:
            hour = datetime.now().hour
        
        # 基于历史数据，某时段常做的事
        if self.time_patterns[hour]:
            from collections import Counter
            common = Counter(self.time_patterns[hour]).most_common(3)
            return [item[0] for item in common]
        
        # 默认建议
        time_suggestions = {
            range(6, 12): ['今日计划', '待办事项', '早间学习'],
            range(12, 14): ['午餐', '休息', '轻松阅读'],
            range(14, 18): ['深度工作', '代码开发', '系统优化'],
            range(18, 22): ['总结回顾', '学习笔记', '明日计划'],
            range(22, 6): ['休息', '放松', '明日预览'],
        }
        
        for time_range, suggestions in time_suggestions.items():
            if hour in time_range:
                return suggestions
        
        return []


class AdaptiveLearningManager:
    """
    自适应学习管理器
    
    统一接口，协调所有学习组件
    """
    
    def __init__(self):
        self.threshold_optimizer = AdaptiveThresholdOptimizer()
        self.pattern_recognizer = PatternRecognizer()
        
        # 学习数据存储
        self.storage_path = Path(".claw-status/adaptive_learning")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 加载历史数据
        self._load_data()
        
        print(f"✅ AdaptiveLearningManager 初始化完成")
    
    def _load_data(self):
        """加载历史学习数据"""
        data_file = self.storage_path / "learning_data.json"
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    # 恢复统计数据
                    self.threshold_optimizer.stats = data.get('stats', {})
            except:
                pass
    
    def _save_data(self):
        """保存学习数据"""
        data_file = self.storage_path / "learning_data.json"
        data = {
            'stats': self.threshold_optimizer.stats,
            'timestamp': datetime.now().isoformat()
        }
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record(self, query_type: str, query: str, result: Any, 
               success: bool, **kwargs):
        """
        记录交互
        
        简化接口，自动收集信息
        """
        record = InteractionRecord(
            timestamp=datetime.now().timestamp(),
            query_type=query_type,
            query=query,
            params=kwargs.get('params', {}),
            result=result,
            success=success,
            user_feedback=kwargs.get('feedback'),
            performance_metrics=kwargs.get('metrics', {})
        )
        
        self.threshold_optimizer.record_interaction(record)
        
        # 周期性保存
        if len(self.threshold_optimizer.records) % 10 == 0:
            self._save_data()
    
    def learn(self) -> List[Dict]:
        """
        执行学习
        
        Returns:
            调整记录
        """
        adjustments = self.threshold_optimizer.analyze_and_adjust()
        
        if adjustments:
            print(f"\n🧠 自适应学习调整:")
            for adj in adjustments:
                print(f"   {adj['parameter']}: {adj['old_value']:.2f} → {adj['new_value']:.2f}")
                print(f"   原因: {adj['reason']}")
        
        return adjustments
    
    def get_optimized_parameters(self) -> Dict[str, float]:
        """获取优化后的参数"""
        return {
            'fast_path_threshold': self.threshold_optimizer.get_parameter('fast_path_threshold'),
            'max_retry_attempts': int(self.threshold_optimizer.get_parameter('max_retry_attempts')),
            'topic_switch_threshold': self.threshold_optimizer.get_parameter('topic_switch_threshold'),
        }
    
    def predict_next(self, current_topic: str) -> List[Tuple[str, float]]:
        """预测下一步"""
        return self.pattern_recognizer.predict_next_topics(current_topic)
    
    def get_report(self) -> Dict:
        """获取完整报告"""
        return self.threshold_optimizer.get_learning_report()


# ==================== 集成到WDai系统 ====================

class AdaptiveWDaiInterface:
    """
    自适应WDai接口
    
    包装原有功能，添加自适应学习
    """
    
    def __init__(self, wdai_system):
        self.wdai = wdai_system
        self.learning = AdaptiveLearningManager()
        
        # 应用优化后的参数
        self._apply_optimized_params()
    
    def _apply_optimized_params(self):
        """应用优化参数到系统"""
        params = self.learning.get_optimized_parameters()
        
        # 应用到快速路径
        if hasattr(self.wdai, 'fast_path'):
            self.wdai.fast_path.similarity_threshold = params['fast_path_threshold']
        
        print(f"\n📊 已应用优化参数:")
        for name, value in params.items():
            print(f"   {name}: {value}")
    
    def search_memory(self, query: str, top_k: int = 5):
        """自适应记忆搜索"""
        start_time = datetime.now().timestamp()
        
        # 尝试快速路径
        cached = self.wdai.fast_path.fast_path.lookup(query)
        
        if cached:
            # 快速路径命中
            response, confidence, metadata = cached
            
            # 记录 (等待用户反馈)
            self.learning.record(
                query_type='fast_path',
                query=query,
                result=response,
                success=True,
                confidence=confidence
            )
            
            return {'source': 'fast_path', 'data': response, 'confidence': confidence}
        
        # 未命中，走正常搜索
        results = self.wdai.search_memory(query, top_k)
        
        # 记录
        duration = (datetime.now().timestamp() - start_time) * 1000
        self.learning.record(
            query_type='memory_search',
            query=query,
            result=results,
            success=len(results) > 0,
            metrics={'duration_ms': duration}
        )
        
        # 触发学习
        if len(self.learning.threshold_optimizer.records) % 5 == 0:
            self.learning.learn()
            self._apply_optimized_params()
        
        return {'source': 'vector_search', 'data': results}
    
    def provide_feedback(self, query: str, satisfied: bool):
        """用户提供反馈"""
        feedback = 'satisfied' if satisfied else 'dissatisfied'
        
        # 更新最后一条相关记录
        for record in reversed(self.learning.threshold_optimizer.records):
            if record.query == query:
                record.user_feedback = feedback
                break
        
        # 立即学习
        self.learning.learn()
        self._apply_optimized_params()
        
        print(f"✅ 反馈已记录: {'满意' if satisfied else '不满意'}")


# ==================== 测试 ====================

if __name__ == "__main__":
    print("="*60)
    print("Adaptive Learning System - 测试")
    print("="*60)
    
    # 初始化
    learning = AdaptiveLearningManager()
    
    # 模拟交互记录
    print("\n1. 模拟交互记录")
    
    # 场景1: 快速路径经常命中但用户不满意
    for i in range(10):
        learning.record(
            query_type='fast_path',
            query=f'查询{i}',
            result='结果',
            success=True,
            feedback='dissatisfied' if i < 5 else 'satisfied'
        )
    
    # 场景2: 工具调用成功率低
    for i in range(10):
        learning.record(
            query_type='tool_call',
            query=f'工具{i}',
            result='结果',
            success=i < 7  # 70%成功率
        )
    
    # 执行学习
    print("\n2. 执行自适应学习")
    adjustments = learning.learn()
    
    # 获取参数
    print("\n3. 优化后的参数")
    params = learning.get_optimized_parameters()
    for name, value in params.items():
        print(f"   {name}: {value}")
    
    # 生成报告
    print("\n4. 学习报告")
    report = learning.get_report()
    print(f"   总交互数: {report['total_interactions']}")
    print(f"   快速路径命中率: {report['performance_metrics']['fast_path_hit_rate']:.1%}")
    print(f"   工具成功率: {report['performance_metrics']['tool_success_rate']:.1%}")
    print(f"   用户满意度: {report['performance_metrics']['user_satisfaction']:.1%}")
    
    # 模式预测
    print("\n5. 话题预测")
    recognizer = PatternRecognizer()
    recognizer.record_topic_sequence(['向量存储', 'Qdrant配置', 'embedding模型'])
    recognizer.record_topic_sequence(['向量存储', '相似度算法', '性能优化'])
    
    predictions = recognizer.predict_next_topics('向量存储')
    print(f"   当前话题: 向量存储")
    print(f"   预测下一步:")
    for topic, prob in predictions:
        print(f"      {topic}: {prob:.0%}")
    
    print("\n" + "="*60)
    print("✅ 自适应学习系统测试完成")
    print("="*60)
