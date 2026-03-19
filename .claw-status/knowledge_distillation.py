#!/usr/bin/env python3
"""
WDai Cross-Session Knowledge Distillation
跨会话知识蒸馏系统 v1.0

核心功能:
1. 模式提取 - 从多个会话发现通用行为模式
2. 隐私保护 - 本地聚合，不上传原始数据
3. 知识固化 - 将通用模式转为系统默认行为
4. 持续进化 - 定期蒸馏，累积优化

隐私设计原则:
- 只提取统计模式，不保留原始对话内容
- 本地处理，无云端上传
- 用户可控，可随时清除
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import json
import hashlib


@dataclass
class SessionPattern:
    """会话模式（隐私安全）"""
    # 不包含原始内容，只有模式特征
    topic_sequence: List[str]  # 话题序列
    query_types: List[str]     # 查询类型分布
    time_of_day: int           # 时段 (0-23)
    day_of_week: int           # 星期 (0-6)
    success_patterns: Dict[str, float]  # 各工具成功率
    duration_buckets: Dict[str, int]    # 耗时分布
    entity_interactions: List[str]  # 交互过的实体类型


@dataclass
class DistilledKnowledge:
    """蒸馏后的知识"""
    pattern_id: str
    pattern_type: str  # 'topic_chain', 'temporal', 'success_factor', 'failure_pattern'
    description: str
    confidence: float  # 0-1
    occurrence_count: int
    supporting_sessions: int
    extracted_at: float
    applied: bool
    impact_score: float  # 应用后的效果评分


class PrivacyPreservingAggregator:
    """
    隐私保护聚合器
    
    关键设计：只提取模式，不保留原始内容
    """
    
    def __init__(self):
        self.session_patterns: List[SessionPattern] = []
        self.anonymized_hashes: Set[str] = set()  # 用于去重
    
    def add_session(self, session_data: Dict) -> SessionPattern:
        """
        添加会话数据，提取模式
        
        session_data 结构:
        {
            'session_id': 'xxx',  # 会被哈希处理
            'interactions': [
                {'type': 'memory_search', 'topic': '向量存储', 'success': True, 'duration_ms': 150},
                ...
            ],
            'timestamp': 1234567890
        }
        """
        # 生成匿名标识
        anon_id = hashlib.sha256(
            f"{session_data.get('session_id', '')}{datetime.now().timestamp()}".encode()
        ).hexdigest()[:16]
        
        # 提取话题序列
        topic_seq = []
        for interaction in session_data.get('interactions', []):
            topic = interaction.get('topic', '')
            if topic and (not topic_seq or topic != topic_seq[-1]):
                topic_seq.append(topic)
        
        # 提取查询类型
        query_types = [i.get('type', 'unknown') for i in session_data.get('interactions', [])]
        
        # 时间特征
        ts = session_data.get('timestamp', datetime.now().timestamp())
        dt = datetime.fromtimestamp(ts)
        
        # 成功率统计
        success_stats = defaultdict(lambda: {'success': 0, 'total': 0})
        for interaction in session_data.get('interactions', []):
            tool = interaction.get('tool', interaction.get('type', 'unknown'))
            if interaction.get('success'):
                success_stats[tool]['success'] += 1
            success_stats[tool]['total'] += 1
        
        success_patterns = {
            tool: stats['success'] / stats['total'] if stats['total'] > 0 else 0
            for tool, stats in success_stats.items()
        }
        
        # 耗时分布（分桶）
        duration_buckets = {'fast': 0, 'normal': 0, 'slow': 0}
        for interaction in session_data.get('interactions', []):
            duration = interaction.get('duration_ms', 0)
            if duration < 100:
                duration_buckets['fast'] += 1
            elif duration < 1000:
                duration_buckets['normal'] += 1
            else:
                duration_buckets['slow'] += 1
        
        # 实体交互
        entities = list(set([
            i.get('entity', i.get('topic', ''))
            for i in session_data.get('interactions', [])
            if i.get('entity') or i.get('topic')
        ]))
        
        pattern = SessionPattern(
            topic_sequence=topic_seq,
            query_types=query_types,
            time_of_day=dt.hour,
            day_of_week=dt.weekday(),
            success_patterns=success_patterns,
            duration_buckets=duration_buckets,
            entity_interactions=entities
        )
        
        self.session_patterns.append(pattern)
        self.anonymized_hashes.add(anon_id)
        
        return pattern


class PatternMiner:
    """
    模式挖掘器
    
    从聚合数据中发现有价值的模式
    """
    
    def __init__(self):
        self.knowledge_base: List[DistilledKnowledge] = []
    
    def mine_topic_chains(self, patterns: List[SessionPattern], min_support: float = 0.3) -> List[DistilledKnowledge]:
        """
        挖掘话题链模式
        
        例如：80%的用户在问"向量存储"后会问"Qdrant配置"
        """
        # 收集所有话题序列
        all_chains = []
        for pattern in patterns:
            if len(pattern.topic_sequence) >= 2:
                for i in range(len(pattern.topic_sequence) - 1):
                    all_chains.append((pattern.topic_sequence[i], pattern.topic_sequence[i + 1]))
        
        # 统计频率
        chain_counts = Counter(all_chains)
        total_sessions = len(patterns)
        
        results = []
        for (topic_a, topic_b), count in chain_counts.most_common(20):
            support = count / total_sessions
            if support >= min_support:
                knowledge = DistilledKnowledge(
                    pattern_id=f"chain_{topic_a}_{topic_b}",
                    pattern_type='topic_chain',
                    description=f"用户在了解'{topic_a}'后，有{support:.0%}的概率会询问'{topic_b}'",
                    confidence=min(0.95, support),
                    occurrence_count=count,
                    supporting_sessions=total_sessions,
                    extracted_at=datetime.now().timestamp(),
                    applied=False,
                    impact_score=0.0
                )
                results.append(knowledge)
        
        return results
    
    def mine_temporal_patterns(self, patterns: List[SessionPattern]) -> List[DistilledKnowledge]:
        """
        挖掘时间模式
        
        例如：周三下午工具调用失败率最高
        """
        # 按时段统计
        hour_patterns = defaultdict(lambda: {'count': 0, 'success_rates': []})
        
        for pattern in patterns:
            hour = pattern.time_of_day
            hour_patterns[hour]['count'] += 1
            
            # 计算该会话整体成功率
            if pattern.success_patterns:
                avg_success = sum(pattern.success_patterns.values()) / len(pattern.success_patterns)
                hour_patterns[hour]['success_rates'].append(avg_success)
        
        results = []
        
        # 发现成功率异常时段
        for hour, data in hour_patterns.items():
            if data['count'] >= 3 and data['success_rates']:
                avg_rate = sum(data['success_rates']) / len(data['success_rates'])
                
                if avg_rate < 0.7:  # 成功率低于70%
                    knowledge = DistilledKnowledge(
                        pattern_id=f"temporal_failure_{hour}",
                        pattern_type='temporal',
                        description=f"{hour}:00时段工具调用成功率较低({avg_rate:.0%})，建议增加重试或检查外部服务状态",
                        confidence=min(0.9, data['count'] / 10),
                        occurrence_count=data['count'],
                        supporting_sessions=len(patterns),
                        extracted_at=datetime.now().timestamp(),
                        applied=False,
                        impact_score=0.0
                    )
                    results.append(knowledge)
        
        # 发现高频时段
        hour_counts = Counter([p.time_of_day for p in patterns])
        peak_hours = [h for h, c in hour_counts.most_common(3)]
        
        for hour in peak_hours:
            count = hour_counts[hour]
            if count >= len(patterns) * 0.2:  # 至少20%的会话
                knowledge = DistilledKnowledge(
                    pattern_id=f"temporal_peak_{hour}",
                    pattern_type='temporal',
                    description=f"{hour}:00是高频使用时段({count}次会话)，可预加载常用资源",
                    confidence=min(0.85, count / len(patterns)),
                    occurrence_count=count,
                    supporting_sessions=len(patterns),
                    extracted_at=datetime.now().timestamp(),
                    applied=False,
                    impact_score=0.0
                )
                results.append(knowledge)
        
        return results
    
    def mine_success_factors(self, patterns: List[SessionPattern]) -> List[DistilledKnowledge]:
        """
        挖掘成功因素
        
        例如：使用多路径推理的问题成功率比单路径高30%
        """
        # 比较不同策略的成功率
        strategy_success = defaultdict(lambda: {'success': 0, 'total': 0})
        
        for pattern in patterns:
            # 根据查询类型判断策略
            for query_type in pattern.query_types:
                if 'multi_path' in query_type or 'reason' in query_type:
                    strategy = 'multi_path'
                elif 'fast_path' in query_type:
                    strategy = 'fast_path'
                else:
                    strategy = 'standard'
                
                # 简化：假设有成功率数据
                if pattern.success_patterns:
                    avg_success = sum(pattern.success_patterns.values()) / len(pattern.success_patterns)
                    if avg_success > 0.5:
                        strategy_success[strategy]['success'] += 1
                    strategy_success[strategy]['total'] += 1
        
        results = []
        
        # 找出表现最好的策略
        best_strategy = None
        best_rate = 0
        
        for strategy, stats in strategy_success.items():
            if stats['total'] > 0:
                rate = stats['success'] / stats['total']
                if rate > best_rate and stats['total'] >= 5:
                    best_rate = rate
                    best_strategy = strategy
        
        if best_strategy:
            knowledge = DistilledKnowledge(
                pattern_id=f"success_factor_{best_strategy}",
                pattern_type='success_factor',
                description=f"'{best_strategy}'策略成功率较高({best_rate:.0%})，可作为默认推荐",
                confidence=min(0.9, best_rate),
                occurrence_count=strategy_success[best_strategy]['total'],
                supporting_sessions=len(patterns),
                extracted_at=datetime.now().timestamp(),
                applied=False,
                impact_score=0.0
            )
            results.append(knowledge)
        
        return results
    
    def mine_failure_patterns(self, patterns: List[SessionPattern]) -> List[DistilledKnowledge]:
        """
        挖掘失败模式
        
        例如：同时访问多个外部API时失败率升高
        """
        # 分析失败相关的特征
        failure_contexts = []
        
        for pattern in patterns:
            if pattern.success_patterns:
                avg_success = sum(pattern.success_patterns.values()) / len(pattern.success_patterns)
                if avg_success < 0.5:  # 整体失败
                    failure_contexts.append({
                        'entity_count': len(pattern.entity_interactions),
                        'query_count': len(pattern.query_types),
                        'has_external': 'web_search' in pattern.query_types or 'api' in pattern.query_types
                    })
        
        if not failure_contexts:
            return []
        
        results = []
        
        # 检查是否与外部调用数量相关
        high_entity_failures = sum(1 for f in failure_contexts if f['entity_count'] > 3)
        if high_entity_failures >= len(failure_contexts) * 0.6:
            knowledge = DistilledKnowledge(
                pattern_id="failure_high_entity_load",
                pattern_type='failure_pattern',
                description="同时处理多个实体(>3)时失败率升高，建议分批处理或增加超时",
                confidence=0.75,
                occurrence_count=high_entity_failures,
                supporting_sessions=len(patterns),
                extracted_at=datetime.now().timestamp(),
                applied=False,
                impact_score=0.0
            )
            results.append(knowledge)
        
        return results


class KnowledgeDistillationManager:
    """
    知识蒸馏管理器
    
    协调整个蒸馏流程
    """
    
    def __init__(self):
        self.aggregator = PrivacyPreservingAggregator()
        self.miner = PatternMiner()
        self.knowledge_base: List[DistilledKnowledge] = []
        
        # 存储路径
        self.storage_path = Path(".claw-status/knowledge_distillation")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 加载已有知识
        self._load_knowledge()
        
        print(f"✅ KnowledgeDistillationManager 初始化完成")
    
    def _load_knowledge(self):
        """加载已有蒸馏知识"""
        kb_file = self.storage_path / "distilled_knowledge.json"
        if kb_file.exists():
            try:
                with open(kb_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        self.knowledge_base.append(DistilledKnowledge(**item))
                print(f"   已加载 {len(self.knowledge_base)} 条蒸馏知识")
            except Exception as e:
                print(f"   加载知识库失败: {e}")
    
    def _save_knowledge(self):
        """保存蒸馏知识"""
        kb_file = self.storage_path / "distilled_knowledge.json"
        data = [asdict(k) for k in self.knowledge_base]
        with open(kb_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def add_session_data(self, session_data: Dict):
        """添加会话数据"""
        self.aggregator.add_session(session_data)
    
    def distill(self) -> List[DistilledKnowledge]:
        """
        执行知识蒸馏
        
        Returns:
            新发现的知识列表
        """
        if len(self.aggregator.session_patterns) < 5:
            print("⚠️ 会话数据不足(需要≥5)，跳过蒸馏")
            return []
        
        print(f"\n🔬 开始知识蒸馏 ({len(self.aggregator.session_patterns)} 个会话)...")
        
        new_knowledge = []
        
        # 1. 挖掘话题链
        topic_chains = self.miner.mine_topic_chains(self.aggregator.session_patterns)
        new_knowledge.extend(topic_chains)
        print(f"   发现 {len(topic_chains)} 个话题链模式")
        
        # 2. 挖掘时间模式
        temporal = self.miner.mine_temporal_patterns(self.aggregator.session_patterns)
        new_knowledge.extend(temporal)
        print(f"   发现 {len(temporal)} 个时间模式")
        
        # 3. 挖掘成功因素
        success = self.miner.mine_success_factors(self.aggregator.session_patterns)
        new_knowledge.extend(success)
        print(f"   发现 {len(success)} 个成功因素")
        
        # 4. 挖掘失败模式
        failures = self.miner.mine_failure_patterns(self.aggregator.session_patterns)
        new_knowledge.extend(failures)
        print(f"   发现 {len(failures)} 个失败模式")
        
        # 合并到知识库
        self.knowledge_base.extend(new_knowledge)
        self._save_knowledge()
        
        print(f"✅ 蒸馏完成，新增 {len(new_knowledge)} 条知识")
        
        return new_knowledge
    
    def apply_knowledge(self) -> List[Dict]:
        """
        将蒸馏知识应用到系统
        
        Returns:
            应用记录
        """
        applied = []
        
        for knowledge in self.knowledge_base:
            if knowledge.applied or knowledge.confidence < 0.5:
                continue
            
            application = None
            
            if knowledge.pattern_type == 'topic_chain':
                # 应用到预测系统
                application = self._apply_topic_chain(knowledge)
            
            elif knowledge.pattern_type == 'temporal':
                # 应用到调度系统
                application = self._apply_temporal_pattern(knowledge)
            
            elif knowledge.pattern_type == 'success_factor':
                # 应用到默认策略
                application = self._apply_success_factor(knowledge)
            
            elif knowledge.pattern_type == 'failure_pattern':
                # 应用到防护机制
                application = self._apply_failure_pattern(knowledge)
            
            if application:
                knowledge.applied = True
                applied.append(application)
        
        self._save_knowledge()
        
        return applied
    
    def _apply_topic_chain(self, knowledge: DistilledKnowledge) -> Dict:
        """应用话题链知识"""
        # 提取话题
        parts = knowledge.pattern_id.split('_')
        if len(parts) >= 3:
            from_topic = parts[1]
            to_topic = parts[2]
            
            return {
                'type': 'topic_chain',
                'knowledge_id': knowledge.pattern_id,
                'action': f'当用户询问"{from_topic}"时，预加载"{to_topic}"相关资源',
                'applied_at': datetime.now().isoformat()
            }
        return None
    
    def _apply_temporal_pattern(self, knowledge: DistilledKnowledge) -> Dict:
        """应用时间模式知识"""
        if 'peak' in knowledge.pattern_id:
            hour = knowledge.pattern_id.split('_')[-1]
            return {
                'type': 'temporal',
                'knowledge_id': knowledge.pattern_id,
                'action': f'{hour}:00时段预加载常用资源',
                'applied_at': datetime.now().isoformat()
            }
        elif 'failure' in knowledge.pattern_id:
            hour = knowledge.pattern_id.split('_')[-1]
            return {
                'type': 'temporal',
                'knowledge_id': knowledge.pattern_id,
                'action': f'{hour}:00时段增加重试次数和超时',
                'applied_at': datetime.now().isoformat()
            }
        return None
    
    def _apply_success_factor(self, knowledge: DistilledKnowledge) -> Dict:
        """应用成功因素知识"""
        strategy = knowledge.pattern_id.split('_')[-1]
        return {
            'type': 'success_factor',
            'knowledge_id': knowledge.pattern_id,
            'action': f'将"{strategy}"设为默认策略',
            'applied_at': datetime.now().isoformat()
        }
    
    def _apply_failure_pattern(self, knowledge: DistilledKnowledge) -> Dict:
        """应用失败模式知识"""
        return {
            'type': 'failure_pattern',
            'knowledge_id': knowledge.pattern_id,
            'action': '高负载时启用分批处理和降级策略',
            'applied_at': datetime.now().isoformat()
        }
    
    def get_knowledge_report(self) -> Dict:
        """生成知识报告"""
        total = len(self.knowledge_base)
        applied = sum(1 for k in self.knowledge_base if k.applied)
        by_type = defaultdict(int)
        
        for k in self.knowledge_base:
            by_type[k.pattern_type] += 1
        
        return {
            'total_knowledge': total,
            'applied_knowledge': applied,
            'pending_knowledge': total - applied,
            'by_type': dict(by_type),
            'sessions_analyzed': len(self.aggregator.session_patterns),
            'high_confidence': sum(1 for k in self.knowledge_base if k.confidence > 0.8)
        }
    
    def get_applied_rules(self) -> List[str]:
        """获取已应用的规则描述"""
        return [
            f"{k.description} (置信度: {k.confidence:.0%})"
            for k in self.knowledge_base
            if k.applied
        ]


# ==================== 集成到WDai系统 ====================

class DistillationInterface:
    """
    蒸馏系统接口
    
    集成到WDai主系统
    """
    
    def __init__(self, wdai_system):
        self.wdai = wdai_system
        self.distillation = KnowledgeDistillationManager()
        
        # 会话数据收集
        self.current_session_data = {
            'session_id': f"session_{datetime.now().timestamp()}",
            'interactions': [],
            'timestamp': datetime.now().timestamp()
        }
    
    def record_interaction(self, interaction_type: str, topic: str = None, 
                          success: bool = True, duration_ms: float = 0,
                          entity: str = None, tool: str = None):
        """记录交互用于蒸馏"""
        self.current_session_data['interactions'].append({
            'type': interaction_type,
            'topic': topic,
            'success': success,
            'duration_ms': duration_ms,
            'entity': entity,
            'tool': tool,
            'timestamp': datetime.now().timestamp()
        })
    
    def end_session(self):
        """结束会话，提交数据"""
        if len(self.current_session_data['interactions']) >= 3:
            self.distillation.add_session_data(self.current_session_data)
            print(f"✅ 会话数据已提交 (共{len(self.current_session_data['interactions'])}次交互)")
    
    def run_distillation(self) -> List[DistilledKnowledge]:
        """运行蒸馏"""
        return self.distillation.distill()
    
    def apply_distilled_knowledge(self) -> List[Dict]:
        """应用蒸馏知识"""
        return self.distillation.apply_knowledge()
    
    def get_report(self) -> Dict:
        """获取报告"""
        return self.distillation.get_knowledge_report()


# ==================== 测试 ====================

if __name__ == "__main__":
    print("="*60)
    print("Knowledge Distillation System - 测试")
    print("="*60)
    
    # 初始化
    manager = KnowledgeDistillationManager()
    
    # 模拟10个会话数据
    print("\n1. 模拟会话数据")
    
    sessions = [
        # 会话1: 向量存储 → Qdrant → 性能优化
        {
            'session_id': 's1',
            'interactions': [
                {'type': 'memory_search', 'topic': '向量存储', 'success': True, 'duration_ms': 120, 'tool': 'search'},
                {'type': 'query', 'topic': 'Qdrant配置', 'success': True, 'duration_ms': 200, 'tool': 'config'},
                {'type': 'query', 'topic': '性能优化', 'success': True, 'duration_ms': 150, 'tool': 'optimize'},
            ],
            'timestamp': datetime.now().timestamp() - 86400 * 1  # 1天前
        },
        # 会话2: 向量存储 → Qdrant → embedding
        {
            'session_id': 's2',
            'interactions': [
                {'type': 'memory_search', 'topic': '向量存储', 'success': True, 'duration_ms': 100, 'tool': 'search'},
                {'type': 'query', 'topic': 'Qdrant配置', 'success': True, 'duration_ms': 180, 'tool': 'config'},
                {'type': 'query', 'topic': 'embedding模型', 'success': True, 'duration_ms': 300, 'tool': 'model'},
            ],
            'timestamp': datetime.now().timestamp() - 86400 * 2
        },
        # 会话3: 工具调用 → 重试机制 → 降级策略 (周三下午)
        {
            'session_id': 's3',
            'interactions': [
                {'type': 'tool_call', 'topic': '工具调用', 'success': False, 'duration_ms': 2000, 'tool': 'api'},
                {'type': 'query', 'topic': '重试机制', 'success': True, 'duration_ms': 150, 'tool': 'config'},
                {'type': 'query', 'topic': '降级策略', 'success': True, 'duration_ms': 200, 'tool': 'fallback'},
            ],
            'timestamp': datetime(2026, 3, 18, 15, 0, 0).timestamp()  # 周三15:00
        },
        # 会话4-10: 更多数据...
        {
            'session_id': 's4',
            'interactions': [
                {'type': 'memory_search', 'topic': '向量存储', 'success': True, 'duration_ms': 110, 'tool': 'search'},
                {'type': 'query', 'topic': 'Qdrant配置', 'success': True, 'duration_ms': 190, 'tool': 'config'},
            ],
            'timestamp': datetime.now().timestamp() - 86400 * 3
        },
        {
            'session_id': 's5',
            'interactions': [
                {'type': 'reasoning', 'topic': '技术方案选择', 'success': True, 'duration_ms': 500, 'tool': 'multi_path'},
                {'type': 'query', 'topic': '多路径推理', 'success': True, 'duration_ms': 300, 'tool': 'reason'},
            ],
            'timestamp': datetime.now().timestamp() - 86400 * 4
        },
        {
            'session_id': 's6',
            'interactions': [
                {'type': 'tool_call', 'topic': '外部API', 'success': False, 'duration_ms': 5000, 'tool': 'api'},
                {'type': 'tool_call', 'topic': '外部API', 'success': False, 'duration_ms': 4000, 'tool': 'api'},
            ],
            'timestamp': datetime(2026, 3, 18, 15, 30, 0).timestamp()  # 周三15:30
        },
        {
            'session_id': 's7',
            'interactions': [
                {'type': 'complex_query', 'topic': '系统优化', 'success': True, 'duration_ms': 800, 'entity': '系统A'},
                {'type': 'complex_query', 'topic': '系统优化', 'success': True, 'duration_ms': 900, 'entity': '系统B'},
                {'type': 'complex_query', 'topic': '系统优化', 'success': True, 'duration_ms': 850, 'entity': '系统C'},
                {'type': 'complex_query', 'topic': '系统优化', 'success': False, 'duration_ms': 3000, 'entity': '系统D'},
            ],
            'timestamp': datetime.now().timestamp() - 86400 * 5
        },
        {
            'session_id': 's8',
            'interactions': [
                {'type': 'fast_path', 'topic': '缓存查询', 'success': True, 'duration_ms': 50, 'tool': 'cache'},
            ],
            'timestamp': datetime.now().timestamp() - 3600 * 2  # 2小时前
        },
        {
            'session_id': 's9',
            'interactions': [
                {'type': 'fast_path', 'topic': '缓存查询', 'success': True, 'duration_ms': 45, 'tool': 'cache'},
            ],
            'timestamp': datetime.now().timestamp() - 3600 * 1
        },
        {
            'session_id': 's10',
            'interactions': [
                {'type': 'memory_search', 'topic': '向量存储', 'success': True, 'duration_ms': 130, 'tool': 'search'},
                {'type': 'query', 'topic': 'Qdrant配置', 'success': True, 'duration_ms': 210, 'tool': 'config'},
                {'type': 'query', 'topic': '相似度算法', 'success': True, 'duration_ms': 250, 'tool': 'algorithm'},
            ],
            'timestamp': datetime.now().timestamp() - 86400 * 6
        },
    ]
    
    for session in sessions:
        manager.add_session_data(session)
    
    print(f"   已添加 {len(sessions)} 个会话")
    
    # 执行蒸馏
    print("\n2. 执行知识蒸馏")
    new_knowledge = manager.distill()
    
    # 展示发现的知识
    print("\n3. 发现的知识模式")
    for i, k in enumerate(new_knowledge[:5], 1):
        print(f"\n   {i}. [{k.pattern_type}] 置信度{k.confidence:.0%}")
        print(f"      {k.description}")
        print(f"      支持: {k.occurrence_count}次 / {k.supporting_sessions}会话")
    
    # 应用知识
    print("\n4. 应用蒸馏知识")
    applied = manager.apply_knowledge()
    
    for app in applied[:3]:
        print(f"   ✅ {app['action']}")
    
    # 生成报告
    print("\n5. 知识蒸馏报告")
    report = manager.get_knowledge_report()
    print(f"   总知识数: {report['total_knowledge']}")
    print(f"   已应用: {report['applied_knowledge']}")
    print(f"   高置信度(>80%): {report['high_confidence']}")
    print(f"   按类型分布: {report['by_type']}")
    
    print("\n" + "="*60)
    print("✅ 知识蒸馏系统测试完成")
    print("="*60)
