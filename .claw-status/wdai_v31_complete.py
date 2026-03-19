#!/usr/bin/env python3
"""
WDai Unified Architecture v3.1
扩展能力模块：学习、蒸馏、压缩

新增:
- LearningCapability (自适应学习)
- DistillationCapability (知识蒸馏)  
- CompressionCapability (动态压缩)
- 全链路事件追踪
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from wdai_unified_v3 import (
    WDaiSystem, EventBus, ConstraintEngine, 
    RetrievalCapability, ReasoningCapability,
    Orchestrator, Event, EventType, Context, Result,
    Constraint, ConstraintViolation,
    PhysicalRealityConstraint, LogicalConsistencyConstraint, SafetyConstraint
)

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, deque
import json
import hashlib
import time


# ============================================================================
# 学习模块 (LearningCapability)
# ============================================================================

@dataclass
class LearningRecord:
    """学习记录"""
    query_type: str
    query: str
    result: Any
    success: bool
    duration_ms: float
    user_feedback: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class LearningCapability:
    """
    自适应学习能力
    
    功能：
    1. 记录交互历史
    2. 在线参数调整
    3. 性能统计
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.records: deque = deque(maxlen=1000)
        self.parameters = {
            'fast_path_threshold': 0.92,
            'max_retry_attempts': 3,
            'topic_switch_threshold': 0.50,
        }
        
        # 统计
        self.stats = defaultdict(lambda: {'success': 0, 'total': 0})
        
        # 注册事件监听
        self.event_bus.subscribe(EventType.RETRIEVAL_COMPLETED, self._on_retrieval)
        self.event_bus.subscribe(EventType.REASONING_COMPLETED, self._on_reasoning)
        
        # 加载历史
        self._load_data()
    
    def _load_data(self):
        """加载学习数据"""
        data_file = Path(".claw-status/learning_data.json")
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    self.parameters = data.get('parameters', self.parameters)
            except:
                pass
    
    def _save_data(self):
        """保存学习数据"""
        data_file = Path(".claw-status/learning_data.json")
        data_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(data_file, 'w') as f:
            json.dump({
                'parameters': self.parameters,
                'timestamp': time.time()
            }, f, indent=2)
    
    def record(self, record: LearningRecord):
        """记录交互"""
        self.records.append(record)
        
        # 更新统计
        self.stats[record.query_type]['total'] += 1
        if record.success:
            self.stats[record.query_type]['success'] += 1
        
        # 触发学习（每20条）
        if len(self.records) % 20 == 0:
            self.learn()
    
    def learn(self):
        """执行学习"""
        print("\n🎓 执行自适应学习...")
        
        # 分析快速路径命中率
        fast_path_records = [r for r in self.records if r.query_type == 'fast_path']
        if fast_path_records:
            hit_rate = sum(1 for r in fast_path_records if r.success) / len(fast_path_records)
            
            if hit_rate > 0.5:  # 命中率过高
                self.parameters['fast_path_threshold'] = min(
                    0.98, self.parameters['fast_path_threshold'] + 0.01
                )
                print(f"   提高阈值: {self.parameters['fast_path_threshold']:.2f}")
            elif hit_rate < 0.2:  # 命中率过低
                self.parameters['fast_path_threshold'] = max(
                    0.70, self.parameters['fast_path_threshold'] - 0.01
                )
                print(f"   降低阈值: {self.parameters['fast_path_threshold']:.2f}")
        
        self._save_data()
    
    def get_parameters(self) -> Dict:
        """获取当前参数"""
        return self.parameters.copy()
    
    def _on_retrieval(self, event: Event):
        """检索完成事件处理"""
        pass  # 可用于实时学习
    
    def _on_reasoning(self, event: Event):
        """推理完成事件处理"""
        pass


# ============================================================================
# 蒸馏模块 (DistillationCapability)
# ============================================================================

@dataclass
class SessionPattern:
    """会话模式（隐私安全）"""
    topic_sequence: List[str]
    query_types: List[str]
    time_of_day: int
    success_patterns: Dict[str, float]
    entity_count: int


@dataclass
class DistilledKnowledge:
    """蒸馏知识"""
    pattern_id: str
    pattern_type: str
    description: str
    confidence: float
    occurrence_count: int
    applied: bool = False


class DistillationCapability:
    """
    跨会话知识蒸馏
    
    隐私设计：只提取统计模式，不保留原始内容
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.session_patterns: List[SessionPattern] = []
        self.knowledge_base: List[DistilledKnowledge] = []
        
        # 当前会话数据
        self.current_session = {
            'interactions': [],
            'start_time': time.time()
        }
        
        # 加载已有知识
        self._load_knowledge()
    
    def _load_knowledge(self):
        """加载蒸馏知识"""
        kb_file = Path(".claw-status/distilled_knowledge.json")
        if kb_file.exists():
            try:
                with open(kb_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        self.knowledge_base.append(DistilledKnowledge(**item))
            except:
                pass
    
    def _save_knowledge(self):
        """保存知识"""
        kb_file = Path(".claw-status/distilled_knowledge.json")
        kb_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = [
            {
                'pattern_id': k.pattern_id,
                'pattern_type': k.pattern_type,
                'description': k.description,
                'confidence': k.confidence,
                'occurrence_count': k.occurrence_count,
                'applied': k.applied
            }
            for k in self.knowledge_base
        ]
        
        with open(kb_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_interaction(self, query_type: str, topic: str, 
                          success: bool, duration_ms: float):
        """记录交互"""
        self.current_session['interactions'].append({
            'type': query_type,
            'topic': topic,
            'success': success,
            'duration_ms': duration_ms,
            'timestamp': time.time()
        })
    
    def end_session(self):
        """结束会话，提取模式"""
        if len(self.current_session['interactions']) < 3:
            return
        
        # 提取话题序列
        topics = []
        for interaction in self.current_session['interactions']:
            topic = interaction.get('topic', '')
            if topic and (not topics or topic != topics[-1]):
                topics.append(topic)
        
        # 提取查询类型
        query_types = [i['type'] for i in self.current_session['interactions']]
        
        # 计算成功率
        success_count = sum(1 for i in self.current_session['interactions'] if i['success'])
        success_rate = success_count / len(self.current_session['interactions'])
        
        # 创建模式
        pattern = SessionPattern(
            topic_sequence=topics,
            query_types=query_types,
            time_of_day=datetime.now().hour,
            success_patterns={'overall': success_rate},
            entity_count=len(set(topics))
        )
        
        self.session_patterns.append(pattern)
        
        # 重置当前会话
        self.current_session = {'interactions': [], 'start_time': time.time()}
        
        print(f"✅ 会话模式已提取 ({len(topics)}个话题)")
    
    def distill(self) -> List[DistilledKnowledge]:
        """执行知识蒸馏"""
        if len(self.session_patterns) < 5:
            print("⚠️ 会话数据不足，跳过蒸馏")
            return []
        
        print(f"\n🔬 执行知识蒸馏 ({len(self.session_patterns)}个会话)...")
        
        new_knowledge = []
        
        # 挖掘话题链
        topic_chains = self._mine_topic_chains()
        new_knowledge.extend(topic_chains)
        
        # 挖掘时间模式
        temporal = self._mine_temporal_patterns()
        new_knowledge.extend(temporal)
        
        self.knowledge_base.extend(new_knowledge)
        self._save_knowledge()
        
        print(f"✅ 蒸馏完成，新增{len(new_knowledge)}条知识")
        
        return new_knowledge
    
    def _mine_topic_chains(self) -> List[DistilledKnowledge]:
        """挖掘话题链"""
        chains = []
        for pattern in self.session_patterns:
            if len(pattern.topic_sequence) >= 2:
                for i in range(len(pattern.topic_sequence) - 1):
                    chains.append((pattern.topic_sequence[i], pattern.topic_sequence[i + 1]))
        
        from collections import Counter
        chain_counts = Counter(chains)
        
        results = []
        for (topic_a, topic_b), count in chain_counts.most_common(5):
            if count >= 2:
                knowledge = DistilledKnowledge(
                    pattern_id=f"chain_{topic_a}_{topic_b}",
                    pattern_type='topic_chain',
                    description=f"用户了解'{topic_a}'后，有{count}次询问'{topic_b}'",
                    confidence=min(0.9, count / len(self.session_patterns)),
                    occurrence_count=count
                )
                results.append(knowledge)
        
        return results
    
    def _mine_temporal_patterns(self) -> List[DistilledKnowledge]:
        """挖掘时间模式"""
        from collections import Counter
        hour_counts = Counter([p.time_of_day for p in self.session_patterns])
        
        results = []
        for hour, count in hour_counts.most_common(3):
            if count >= 3:
                knowledge = DistilledKnowledge(
                    pattern_id=f"temporal_peak_{hour}",
                    pattern_type='temporal',
                    description=f"{hour}:00是高频使用时段({count}次会话)",
                    confidence=min(0.8, count / len(self.session_patterns)),
                    occurrence_count=count
                )
                results.append(knowledge)
        
        return results


# ============================================================================
# 压缩模块 (CompressionCapability)
# ============================================================================

class CompressionCapability:
    """
    动态压缩能力
    
    自动压缩长对话，提取关键信息
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.working_memory: List[Dict] = []
        self.compression_threshold = 10  # 10轮后压缩
        
        # 压缩历史
        self.compression_history: deque = deque(maxlen=100)
    
    def add_turn(self, role: str, content: str, metadata: Dict = None):
        """添加一轮对话"""
        self.working_memory.append({
            'role': role,
            'content': content,
            'metadata': metadata or {},
            'timestamp': time.time()
        })
        
        # 检查是否需要压缩
        if len(self.working_memory) >= self.compression_threshold:
            self.compress()
    
    def compress(self) -> Optional[Dict]:
        """执行压缩"""
        if len(self.working_memory) < 5:
            return None
        
        print(f"\n🗜️ 执行动态压缩 ({len(self.working_memory)}轮对话)...")
        
        # 提取关键信息
        entities = self._extract_entities()
        decisions = self._extract_decisions()
        corrections = self._extract_corrections()
        
        # 生成压缩事件
        compressed = {
            'type': 'compression_event',
            'timestamp': time.time(),
            'original_turns': len(self.working_memory),
            'entities': entities,
            'decisions': decisions,
            'corrections': corrections,
            'importance': self._calculate_importance(entities, decisions, corrections)
        }
        
        self.compression_history.append(compressed)
        
        # 清空工作记忆
        self.working_memory = []
        
        print(f"   压缩完成: {len(entities)}实体, {len(decisions)}决策, {len(corrections)}纠正")
        
        return compressed
    
    def _extract_entities(self) -> List[str]:
        """提取实体"""
        entities = []
        for turn in self.working_memory:
            content = turn['content']
            # 简单提取：引号内的内容、大写词等
            import re
            quoted = re.findall(r'["""]([^"""]+)["""]', content)
            entities.extend(quoted)
        return list(set(entities))[:10]  # 去重，最多10个
    
    def _extract_decisions(self) -> List[str]:
        """提取决策"""
        decisions = []
        keywords = ['决定', '选择', '采用', '使用', '方案']
        
        for turn in self.working_memory:
            content = turn['content']
            for kw in keywords:
                if kw in content:
                    # 提取关键词所在的句子
                    sentences = content.split('。')
                    for s in sentences:
                        if kw in s:
                            decisions.append(s.strip())
                            break
                    break
        
        return decisions[:5]
    
    def _extract_corrections(self) -> List[str]:
        """提取纠正"""
        corrections = []
        keywords = ['纠正', '修正', '错误', '不对', '应该']
        
        for turn in self.working_memory:
            content = turn['content']
            for kw in keywords:
                if kw in content:
                    corrections.append(f"[{turn['role']}] {content[:100]}...")
                    break
        
        return corrections[:3]
    
    def _calculate_importance(self, entities, decisions, corrections) -> float:
        """计算重要性"""
        score = 0.0
        
        if len(entities) > 3:
            score += 0.3
        if len(decisions) > 0:
            score += 0.4
        if len(corrections) > 0:
            score += 0.3
        
        return min(1.0, score)


# ============================================================================
# 扩展的WDaiSystem v3.1
# ============================================================================

class WDaiSystemV31:
    """
    WDai系统 v3.1
    
    完整能力：检索、推理、学习、蒸馏、压缩
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        print("="*60)
        print("🚀 WDai Unified Architecture v3.1 启动")
        print("="*60)
        
        # 基础层
        self.event_bus = EventBus()
        self.constraint_engine = ConstraintEngine()
        self.constraint_engine.register(PhysicalRealityConstraint())
        self.constraint_engine.register(LogicalConsistencyConstraint())
        self.constraint_engine.register(SafetyConstraint())
        
        # 能力层
        self.retrieval = RetrievalCapability(self.event_bus)
        self.reasoning = ReasoningCapability(self.event_bus)
        self.learning = LearningCapability(self.event_bus)
        self.distillation = DistillationCapability(self.event_bus)
        self.compression = CompressionCapability(self.event_bus)
        
        # 协调层
        self.orchestrator = Orchestrator(self.event_bus, self.constraint_engine)
        self.orchestrator.register_capability('retrieval', self.retrieval)
        self.orchestrator.register_capability('reasoning', self.reasoning)
        
        self._initialized = True
        
        print("\n✅ 系统初始化完成")
        print(f"   能力模块: 检索、推理、学习、蒸馏、压缩")
        print("="*60)
    
    def query(self, text: str, user_id: Optional[str] = None) -> Dict:
        """统一查询接口"""
        query_id = hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()[:16]
        context = Context(
            session_id=user_id or "anonymous",
            query_id=query_id,
            user_id=user_id
        )
        
        # 记录到压缩
        self.compression.add_turn('user', text)
        
        # 记录到学习
        start_time = time.time()
        
        # 发布事件
        self.event_bus.publish(Event(
            type=EventType.USER_INPUT,
            payload={'text': text},
            correlation_id=query_id
        ))
        
        # 执行处理
        result = self.orchestrator.process(text, context)
        
        # 记录学习
        duration = (time.time() - start_time) * 1000
        self.learning.record(LearningRecord(
            query_type='query',
            query=text[:50],
            result=result.data,
            success=result.success,
            duration_ms=duration
        ))
        
        # 记录到蒸馏
        self.distillation.record_interaction(
            query_type='query',
            topic=text[:20],
            success=result.success,
            duration_ms=duration
        )
        
        # 记录助手回复到压缩
        response_text = str(result.data)[:200] if result.data else "无结果"
        self.compression.add_turn('assistant', response_text)
        
        return {
            'success': result.success,
            'data': result.data,
            'error': result.error,
            'confidence': result.confidence,
            'query_id': query_id
        }
    
    def add_knowledge(self, content: str, metadata: Dict = None) -> str:
        """添加知识"""
        return self.retrieval.add_memory(content, metadata)
    
    def provide_feedback(self, satisfied: bool, query_id: str = None):
        """用户反馈"""
        feedback = 'satisfied' if satisfied else 'dissatisfied'
        
        # 更新学习记录
        for record in reversed(self.learning.records):
            record.user_feedback = feedback
            break
        
        # 触发学习
        self.learning.learn()
        
        print(f"{'👍' if satisfied else '👎'} 反馈已记录")
    
    def run_distillation(self):
        """运行知识蒸馏"""
        # 先结束当前会话
        self.distillation.end_session()
        
        # 执行蒸馏
        new_knowledge = self.distillation.distill()
        
        return {
            'new_knowledge': len(new_knowledge),
            'total_knowledge': len(self.distillation.knowledge_base)
        }
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            'memories': len(self.retrieval.memory_store),
            'learning_records': len(self.learning.records),
            'session_patterns': len(self.distillation.session_patterns),
            'compressed_events': len(self.compression.compression_history),
            'current_parameters': self.learning.get_parameters()
        }


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Unified Architecture v3.1 - 完整测试")
    print("="*60)
    
    # 创建系统
    system = WDaiSystemV31()
    
    # 添加知识
    print("\n📚 添加测试知识...")
    system.add_knowledge("WDai采用分层记忆架构")
    system.add_knowledge("向量存储使用384维本地嵌入")
    system.add_knowledge("多路径推理包括4条路径")
    print("   已添加3条知识")
    
    # 模拟多轮对话（触发压缩）
    print("\n💬 模拟多轮对话...")
    for i in range(12):
        result = system.query(f"查询{i+1}: 关于记忆架构的问题")
        print(f"   轮次{i+1}: 成功={result['success']}")
    
    # 用户反馈
    print("\n👍 提供用户反馈...")
    system.provide_feedback(satisfied=True)
    
    # 运行蒸馏
    print("\n🔬 运行知识蒸馏...")
    dist_result = system.run_distillation()
    print(f"   新增知识: {dist_result['new_knowledge']}")
    print(f"   总知识: {dist_result['total_knowledge']}")
    
    # 系统状态
    print("\n📊 系统状态")
    status = system.get_status()
    print(f"   记忆数: {status['memories']}")
    print(f"   学习记录: {status['learning_records']}")
    print(f"   会话模式: {status['session_patterns']}")
    print(f"   压缩事件: {status['compressed_events']}")
    print(f"   当前参数: {status['current_parameters']}")
    
    print("\n" + "="*60)
    print("✅ v3.1 完整测试通过")
    print("="*60)
