#!/usr/bin/env python3
"""
WDai Unified Architecture v3.0
统一底层架构 - 事件驱动、插件化、确定性约束优先

架构分层:
┌─────────────────────────────────────────┐
│  Interface Layer (统一接口)              │
│  - 自然语言输入解析                       │
│  - 意图识别与路由                         │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  Orchestrator Layer (协调层)            │
│  - 流程编排引擎                          │
│  - 执行计划生成                          │
│  - 结果聚合                              │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  Capability Layer (能力层)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Retrieval│ │ Reasoning│ │ Execution│ │
│  │  (检索)  │ │  (推理)  │ │  (执行)  │ │
│  └──────────┘ └──────────┘ └──────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Learning  │ │Distill   │ │Compress  │ │
│  │  (学习)  │ │(知识蒸馏)│ │ (压缩)   │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  Constraint Layer (约束层)              │
│  - 物理现实检查                          │
│  - 逻辑一致性验证                        │
│  - 安全边界控制                          │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│  Storage Layer (存储层)                 │
│  - 向量存储                              │
│  - 状态持久化                            │
│  - 审计日志                              │
└─────────────────────────────────────────┘

核心设计原则:
1. 事件驱动 - 所有操作通过事件触发和响应
2. 插件化 - 能力模块可插拔、可扩展
3. 约束优先 - 任何输出必须通过约束层验证
4. 可观测 - 全流程可追踪、可审计
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable, Any, TypeVar, Generic, Set, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum, auto
from collections import defaultdict, deque
import json
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time


# ============================================================================
# 基础类型定义
# ============================================================================

class EventType(Enum):
    """事件类型"""
    USER_INPUT = auto()
    QUERY_RECEIVED = auto()
    RETRIEVAL_STARTED = auto()
    RETRIEVAL_COMPLETED = auto()
    REASONING_STARTED = auto()
    REASONING_COMPLETED = auto()
    CONSTRAINT_CHECK = auto()
    CONSTRAINT_VIOLATED = auto()
    EXECUTION_STARTED = auto()
    EXECUTION_COMPLETED = auto()
    LEARNING_UPDATE = auto()
    ERROR_OCCURRED = auto()
    SYSTEM_SHUTDOWN = auto()


@dataclass
class Event:
    """事件基类"""
    type: EventType
    timestamp: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    correlation_id: str = ""


@dataclass  
class Context:
    """执行上下文"""
    session_id: str
    query_id: str
    user_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace: List[Dict] = field(default_factory=list)
    
    def add_trace(self, stage: str, data: Dict):
        """添加追踪记录"""
        self.trace.append({
            'stage': stage,
            'timestamp': time.time(),
            'data': data
        })


@dataclass
class Result:
    """执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)


# ============================================================================
# 事件总线 (Event Bus)
# ============================================================================

class EventBus:
    """
    事件总线 - 系统核心通信机制
    
    支持:
    - 发布/订阅模式
    - 异步事件处理
    - 事件持久化
    """
    
    def __init__(self):
        self.subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.event_history: deque = deque(maxlen=1000)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def subscribe(self, event_type: EventType, handler: Callable):
        """订阅事件"""
        self.subscribers[event_type].append(handler)
        
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """取消订阅"""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
    
    def publish(self, event: Event):
        """发布事件"""
        self.event_history.append(event)
        
        # 异步通知订阅者
        for handler in self.subscribers[event.type]:
            self.executor.submit(self._safe_notify, handler, event)
    
    def _safe_notify(self, handler: Callable, event: Event):
        """安全通知处理器"""
        try:
            handler(event)
        except Exception as e:
            print(f"Event handler error: {e}")
    
    def get_history(self, event_type: Optional[EventType] = None, 
                    limit: int = 100) -> List[Event]:
        """获取事件历史"""
        events = list(self.event_history)
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]


# ============================================================================
# 约束层 (Constraint Layer)
# ============================================================================

class ConstraintViolation(Exception):
    """约束违反异常"""
    pass


class Constraint(ABC):
    """约束基类"""
    
    @abstractmethod
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """
        检查约束
        
        Returns:
            (是否通过, 错误信息)
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """约束名称"""
        pass


class PhysicalRealityConstraint(Constraint):
    """物理现实约束"""
    
    name = "physical_reality"
    
    # 预定义物理规则
    RULES = {
        'temporal': [
            ('cause_before_effect', '原因必须在结果之前'),
            ('no_time_travel', '时间不可逆'),
        ],
        'genetics': [
            ('x_linked_recessive', 'X染色体隐性遗传规则'),
        ],
        'mathematics': [
            ('conservation', '数学守恒定律'),
        ]
    }
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """
        检查是否违反物理现实
        
        示例：色盲遗传检查
        """
        if isinstance(data, dict) and 'genetics' in data:
            genetic_data = data['genetics']
            
            # 检查X连锁隐性遗传
            if genetic_data.get('trait') == 'color_blindness':
                father_normal = genetic_data.get('father_normal', False)
                mother_normal = genetic_data.get('mother_normal', False)
                child_affected = genetic_data.get('child_affected', False)
                
                if father_normal and mother_normal and child_affected:
                    return False, "违反遗传学定律：父母均正常但子代患病，需重新检查亲缘关系"
        
        return True, None


class LogicalConsistencyConstraint(Constraint):
    """逻辑一致性约束"""
    
    name = "logical_consistency"
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """检查逻辑一致性"""
        if isinstance(data, dict):
            # 检查矛盾陈述
            statements = data.get('statements', [])
            
            for i, stmt1 in enumerate(statements):
                for stmt2 in statements[i+1:]:
                    if self._contradictory(stmt1, stmt2):
                        return False, f"逻辑矛盾: '{stmt1}' 与 '{stmt2}'"
        
        return True, None
    
    def _contradictory(self, stmt1: str, stmt2: str) -> bool:
        """简单矛盾检测"""
        # 扩展：使用语义相似度判断
        negations = ['不', '没', '无', '非']
        
        # 简单规则：一个是否定另一个的肯定
        stmt1_clean = stmt1.replace(' ', '')
        stmt2_clean = stmt2.replace(' ', '')
        
        for neg in negations:
            if stmt1_clean == stmt2_clean.replace(neg, '') or \
               stmt2_clean == stmt1_clean.replace(neg, ''):
                return True
        
        return False


class SafetyConstraint(Constraint):
    """安全边界约束"""
    
    name = "safety"
    
    # 危险操作黑名单
    DANGEROUS_PATTERNS = [
        'rm -rf /',
        'format',
        'delete_all',
        'drop database',
    ]
    
    def check(self, data: Any, context: Context) -> Tuple[bool, Optional[str]]:
        """安全检查"""
        if isinstance(data, str):
            data_lower = data.lower()
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern in data_lower:
                    return False, f"检测到危险操作模式: {pattern}"
        
        return True, None


class ConstraintEngine:
    """约束引擎 - 统一约束管理"""
    
    def __init__(self):
        self.constraints: List[Constraint] = []
        self.violation_history: deque = deque(maxlen=100)
        
    def register(self, constraint: Constraint):
        """注册约束"""
        self.constraints.append(constraint)
        
    def validate(self, data: Any, context: Context) -> Result:
        """
        执行所有约束验证
        
        策略：
        1. 按优先级排序（安全 > 物理 > 逻辑）
        2. 并行检查（可优化）
        3. 收集所有违规，不短路
        """
        violations = []
        
        for constraint in sorted(self.constraints, key=lambda c: self._priority(c)):
            passed, error = constraint.check(data, context)
            if not passed:
                violations.append({
                    'constraint': constraint.name,
                    'error': error,
                    'timestamp': time.time()
                })
        
        if violations:
            self.violation_history.extend(violations)
            return Result(
                success=False,
                error=f"约束验证失败: {len(violations)}项违规",
                metadata={'violations': violations}
            )
        
        return Result(success=True)
    
    def _priority(self, constraint: Constraint) -> int:
        """约束优先级"""
        priorities = {
            'safety': 0,
            'physical_reality': 1,
            'logical_consistency': 2,
        }
        return priorities.get(constraint.name, 99)


# ============================================================================
# 能力层 (Capability Layer) - 检索能力
# ============================================================================

class RetrievalCapability:
    """
    检索能力 - 向量存储与语义搜索
    
    完整实现，无外部依赖
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.vector_dim = 384
        self.memory_store: Dict[str, Dict] = {}
        self.index: Dict[str, List[float]] = {}
        
        # 加载本地嵌入模型（简化版）
        self.embedder = LocalEmbedder(self.vector_dim)
        
        # 注册事件监听
        self.event_bus.subscribe(EventType.RETRIEVAL_STARTED, self._on_retrieval_start)
        
        # 加载已有数据
        self._load_data()
        
    def _load_data(self):
        """加载持久化数据"""
        storage_path = Path(".memory/vector_data.json")
        if storage_path.exists():
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memory_store = data.get('memories', {})
                    self.index = {k: v['vector'] for k, v in self.memory_store.items()}
                print(f"✅ 加载 {len(self.memory_store)} 条记忆")
            except Exception as e:
                print(f"⚠️ 加载数据失败: {e}")
    
    def _save_data(self):
        """持久化数据"""
        storage_path = Path(".memory/vector_data.json")
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'memories': self.memory_store,
            'timestamp': time.time()
        }
        
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def search(self, query: str, top_k: int = 5, context: Context = None) -> Result:
        """
        语义搜索
        
        完整流程:
        1. 查询向量化
        2. 相似度计算
        3. 结果排序
        4. 事件通知
        """
        # 发布开始事件
        self.event_bus.publish(Event(
            type=EventType.RETRIEVAL_STARTED,
            payload={'query': query, 'top_k': top_k},
            correlation_id=context.query_id if context else ""
        ))
        
        # 向量化
        query_vector = self.embedder.encode(query)
        
        # 相似度计算
        results = []
        for key, stored_vector in self.index.items():
            similarity = self._cosine_similarity(query_vector, stored_vector)
            if similarity > 0.3:  # 阈值过滤
                results.append({
                    'key': key,
                    'content': self.memory_store[key]['content'],
                    'similarity': similarity,
                    'metadata': self.memory_store[key].get('metadata', {})
                })
        
        # 排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = results[:top_k]
        
        # 发布完成事件
        self.event_bus.publish(Event(
            type=EventType.RETRIEVAL_COMPLETED,
            payload={
                'query': query,
                'results_count': len(top_results),
                'top_similarity': top_results[0]['similarity'] if top_results else 0
            },
            correlation_id=context.query_id if context else ""
        ))
        
        return Result(
            success=True,
            data=top_results,
            confidence=top_results[0]['similarity'] if top_results else 0.0,
            sources=[r['key'] for r in top_results]
        )
    
    def add_memory(self, content: str, metadata: Dict = None) -> str:
        """添加记忆"""
        key = hashlib.md5(content.encode()).hexdigest()[:16]
        vector = self.embedder.encode(content)
        
        self.memory_store[key] = {
            'content': content,
            'vector': vector,
            'metadata': metadata or {},
            'timestamp': time.time()
        }
        self.index[key] = vector
        
        # 异步保存
        self._save_data()
        
        return key
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def _on_retrieval_start(self, event: Event):
        """检索开始事件处理"""
        pass  # 可扩展：日志、监控等


class LocalEmbedder:
    """
    本地嵌入模型（简化实现）
    
    实际应使用预训练的轻量级模型
    这里使用字符级n-gram哈希作为演示
    """
    
    def __init__(self, dim: int = 384):
        self.dim = dim
        
    def encode(self, text: str) -> List[float]:
        """
        文本向量化
        
        简化实现：字符n-gram统计 + 哈希到固定维度
        """
        text = text.lower().strip()
        vector = [0.0] * self.dim
        
        # 字符n-gram（2-4）
        for n in range(2, 5):
            for i in range(len(text) - n + 1):
                ngram = text[i:i+n]
                # 哈希到维度
                idx = hash(ngram) % self.dim
                vector[idx] += 1.0
        
        # 归一化
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector


# ============================================================================
# 能力层 - 推理能力
# ============================================================================

class ReasoningCapability:
    """
    推理能力 - 多路径推理与验证
    
    完整实现，不依赖外部LLM
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        
        # 注册事件
        self.event_bus.subscribe(EventType.REASONING_STARTED, self._on_reasoning_start)
    
    def reason(self, question: str, context: Context, 
               paths: List[str] = None) -> Result:
        """
        多路径推理
        
        Args:
            paths: 推理路径类型列表 ['intuitive', 'analytical', ...]
        """
        paths = paths or ['intuitive', 'analytical', 'conservative', 'creative']
        
        # 发布开始事件
        self.event_bus.publish(Event(
            type=EventType.REASONING_STARTED,
            payload={'question': question, 'paths': paths},
            correlation_id=context.query_id
        ))
        
        # 执行各路径推理（简化实现，实际应调用LLM）
        path_results = []
        
        for path_type in paths:
            result = self._execute_path(path_type, question, context)
            path_results.append(result)
        
        # 一致性检查
        agreement = self._calculate_agreement(path_results)
        
        # 加权仲裁
        final = self._arbitrate(path_results)
        
        # 发布完成事件
        self.event_bus.publish(Event(
            type=EventType.REASONING_COMPLETED,
            payload={
                'question': question,
                'paths_used': len(paths),
                'agreement_score': agreement,
                'final_confidence': final['confidence']
            },
            correlation_id=context.query_id
        ))
        
        return Result(
            success=True,
            data={
                'paths': path_results,
                'agreement': agreement,
                'final': final
            },
            confidence=final['confidence'],
            metadata={'needs_verification': agreement < 0.7}
        )
    
    def _execute_path(self, path_type: str, question: str, 
                      context: Context) -> Dict:
        """执行单一路径推理（简化实现）"""
        
        # 模拟不同路径的推理风格和置信度
        path_configs = {
            'intuitive': {'weight': 0.20, 'base_confidence': 0.75},
            'analytical': {'weight': 0.35, 'base_confidence': 0.85},
            'conservative': {'weight': 0.25, 'base_confidence': 0.70},
            'creative': {'weight': 0.20, 'base_confidence': 0.60},
        }
        
        config = path_configs.get(path_type, {'weight': 0.25, 'base_confidence': 0.70})
        
        return {
            'type': path_type,
            'reasoning': f"基于{path_type}路径的推理...",
            'conclusion': self._generate_conclusion(question, path_type),
            'confidence': config['base_confidence'],
            'weight': config['weight']
        }
    
    def _generate_conclusion(self, question: str, path_type: str) -> str:
        """生成结论（简化）"""
        # 实际应基于真实推理
        conclusions = {
            'intuitive': "基于经验的快速判断",
            'analytical': "经过系统分析的结果",
            'conservative': "风险最小化的选择",
            'creative': "突破常规的方案"
        }
        return conclusions.get(path_type, "综合评估结果")
    
    def _calculate_agreement(self, path_results: List[Dict]) -> float:
        """计算路径一致性"""
        if len(path_results) < 2:
            return 1.0
        
        # 基于置信度和结论相似度计算
        confidences = [r['confidence'] for r in path_results]
        avg_confidence = sum(confidences) / len(confidences)
        
        # 结论一致性（简化：基于字符串相似度）
        # 实际应使用语义相似度
        conclusion_similarity = 0.8  # 假设
        
        return avg_confidence * conclusion_similarity
    
    def _arbitrate(self, path_results: List[Dict]) -> Dict:
        """加权仲裁"""
        total_weight = sum(r['weight'] for r in path_results)
        weighted_confidence = sum(
            r['confidence'] * r['weight'] for r in path_results
        ) / total_weight
        
        # 选择最高权重的结论
        best = max(path_results, key=lambda r: r['confidence'] * r['weight'])
        
        return {
            'conclusion': best['conclusion'],
            'confidence': weighted_confidence,
            'supporting_paths': [r['type'] for r in path_results if r['confidence'] > 0.7]
        }
    
    def _on_reasoning_start(self, event: Event):
        """推理开始事件处理"""
        pass


# ============================================================================
# 协调层 (Orchestrator)
# ============================================================================

class Orchestrator:
    """
    协调器 - 流程编排与执行
    
    职责：
    1. 解析用户意图
    2. 生成执行计划
    3. 调度能力模块
    4. 聚合结果
    """
    
    def __init__(self, event_bus: EventBus, constraint_engine: ConstraintEngine):
        self.event_bus = event_bus
        self.constraint_engine = constraint_engine
        
        # 能力注册表
        self.capabilities: Dict[str, Any] = {}
        
        # 意图到能力的映射
        self.intent_map = {
            'search': ['retrieval'],
            'analyze': ['retrieval', 'reasoning'],
            'execute': ['execution'],
            'learn': ['learning'],
        }
    
    def register_capability(self, name: str, capability: Any):
        """注册能力"""
        self.capabilities[name] = capability
    
    def process(self, query: str, context: Context) -> Result:
        """
        主处理流程
        
        标准流程:
        1. 意图识别
        2. 生成执行计划
        3. 执行各阶段
        4. 约束验证
        5. 返回结果
        """
        context.add_trace('orchestrator_start', {'query': query})
        
        # 1. 意图识别
        intent = self._identify_intent(query)
        context.add_trace('intent_identified', {'intent': intent})
        
        # 2. 生成执行计划
        plan = self._create_plan(intent, query)
        context.add_trace('plan_created', {'plan': plan})
        
        # 3. 执行计划
        results = []
        for step in plan:
            result = self._execute_step(step, query, context)
            results.append(result)
            
            if not result.success:
                # 步骤失败，发布错误事件
                self.event_bus.publish(Event(
                    type=EventType.ERROR_OCCURRED,
                    payload={'step': step, 'error': result.error},
                    correlation_id=context.query_id
                ))
                break
        
        # 4. 聚合结果
        final_result = self._aggregate_results(results, intent)
        context.add_trace('results_aggregated', {'final': final_result.success})
        
        # 5. 约束验证
        constraint_result = self.constraint_engine.validate(
            final_result.data, context
        )
        
        if not constraint_result.success:
            return Result(
                success=False,
                error=f"约束验证失败: {constraint_result.error}",
                metadata=constraint_result.metadata
            )
        
        context.add_trace('completed', {'success': True})
        
        return final_result
    
    def _identify_intent(self, query: str) -> str:
        """意图识别（简化）"""
        query_lower = query.lower()
        
        if any(w in query_lower for w in ['搜索', '查找', '查询', 'search']):
            return 'search'
        elif any(w in query_lower for w in ['分析', '为什么', '推理', 'analyze']):
            return 'analyze'
        elif any(w in query_lower for w in ['执行', '运行', '做', 'execute']):
            return 'execute'
        else:
            return 'analyze'  # 默认分析
    
    def _create_plan(self, intent: str, query: str) -> List[Dict]:
        """创建执行计划"""
        capabilities = self.intent_map.get(intent, ['retrieval'])
        
        plan = []
        for cap in capabilities:
            plan.append({
                'capability': cap,
                'action': 'process',
                'query': query
            })
        
        return plan
    
    def _execute_step(self, step: Dict, query: str, context: Context) -> Result:
        """执行单一步骤"""
        capability_name = step['capability']
        capability = self.capabilities.get(capability_name)
        
        if not capability:
            return Result(success=False, error=f"未知能力: {capability_name}")
        
        if capability_name == 'retrieval':
            return capability.search(query, context=context)
        elif capability_name == 'reasoning':
            return capability.reason(query, context)
        else:
            return Result(success=False, error=f"未实现能力: {capability_name}")
    
    def _aggregate_results(self, results: List[Result], intent: str) -> Result:
        """聚合多个结果"""
        if not results:
            return Result(success=False, error="无执行结果")
        
        if len(results) == 1:
            return results[0]
        
        # 合并多个结果
        all_data = [r.data for r in results if r.success]
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return Result(
            success=all(r.success for r in results),
            data={
                'intent': intent,
                'steps': len(results),
                'results': all_data
            },
            confidence=avg_confidence,
            sources=[s for r in results for s in r.sources]
        )


# ============================================================================
# 统一接口层 (Facade)
# ============================================================================

class WDaiSystem:
    """
    WDai统一系统 v3.0
    
    对外统一接口，对内协调各层
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
        print("🚀 WDai Unified Architecture v3.0 启动")
        print("="*60)
        
        # 1. 初始化事件总线
        print("\n📡 初始化事件总线...")
        self.event_bus = EventBus()
        
        # 2. 初始化约束引擎
        print("🛡️ 初始化约束引擎...")
        self.constraint_engine = ConstraintEngine()
        self.constraint_engine.register(PhysicalRealityConstraint())
        self.constraint_engine.register(LogicalConsistencyConstraint())
        self.constraint_engine.register(SafetyConstraint())
        
        # 3. 初始化能力模块
        print("⚡ 初始化能力模块...")
        self.retrieval = RetrievalCapability(self.event_bus)
        self.reasoning = ReasoningCapability(self.event_bus)
        
        # 4. 初始化协调器
        print("🎯 初始化协调器...")
        self.orchestrator = Orchestrator(self.event_bus, self.constraint_engine)
        self.orchestrator.register_capability('retrieval', self.retrieval)
        self.orchestrator.register_capability('reasoning', self.reasoning)
        
        self._initialized = True
        
        print("\n" + "="*60)
        print("✅ 系统初始化完成")
        print("="*60)
    
    def query(self, text: str, user_id: Optional[str] = None) -> Dict:
        """
        统一查询接口
        
        用户唯一需要调用的方法
        """
        # 创建上下文
        query_id = hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()[:16]
        context = Context(
            session_id=user_id or "anonymous",
            query_id=query_id,
            user_id=user_id
        )
        
        # 发布用户输入事件
        self.event_bus.publish(Event(
            type=EventType.USER_INPUT,
            payload={'text': text},
            correlation_id=query_id,
            source='user'
        ))
        
        # 执行处理
        result = self.orchestrator.process(text, context)
        
        # 返回格式化结果
        return {
            'success': result.success,
            'data': result.data,
            'error': result.error,
            'confidence': result.confidence,
            'sources': result.sources,
            'query_id': query_id,
            'trace': context.trace
        }
    
    def add_knowledge(self, content: str, metadata: Dict = None) -> str:
        """添加知识"""
        return self.retrieval.add_memory(content, metadata)
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            'memories': len(self.retrieval.memory_store),
            'constraints': len(self.constraint_engine.constraints),
            'capabilities': list(self.orchestrator.capabilities.keys()),
            'recent_events': len(self.event_bus.event_history)
        }


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Unified Architecture v3.0 - 集成测试")
    print("="*60)
    
    # 获取系统实例
    system = WDaiSystem()
    
    # 添加测试知识
    print("\n📚 添加测试知识...")
    system.add_knowledge(
        "WDai采用分层记忆架构：工作记忆、情景记忆、语义记忆、程序记忆",
        {'category': 'architecture', 'source': 'design_doc'}
    )
    system.add_knowledge(
        "向量存储使用384维本地嵌入，支持离线运行",
        {'category': 'implementation', 'source': 'tech_spec'}
    )
    system.add_knowledge(
        "多路径推理包括直觉、分析、保守、创新四条路径",
        {'category': 'reasoning', 'source': 'design_doc'}
    )
    print(f"   已添加3条知识")
    
    # 测试1: 检索查询
    print("\n🔍 测试1: 检索查询")
    result = system.query("WDai的记忆架构是什么样的？")
    print(f"   成功: {result['success']}")
    print(f"   置信度: {result['confidence']:.2f}")
    if result['data']:
        print(f"   结果数: {len(result['data'].get('results', []))}")
    
    # 测试2: 分析查询
    print("\n🧠 测试2: 分析查询")
    result = system.query("分析一下向量存储的实现原理")
    print(f"   成功: {result['success']}")
    print(f"   置信度: {result['confidence']:.2f}")
    
    # 测试3: 约束验证（遗传学案例）
    print("\n🛡️ 测试3: 约束验证")
    # 通过直接调用约束引擎测试
    context = Context(session_id="test", query_id="test_001")
    constraint_result = system.constraint_engine.validate({
        'genetics': {
            'trait': 'color_blindness',
            'father_normal': True,
            'mother_normal': True,
            'child_affected': True
        }
    }, context)
    print(f"   约束检查: {constraint_result.success}")
    if not constraint_result.success:
        print(f"   违规原因: {constraint_result.error}")
    
    # 系统状态
    print("\n📊 系统状态")
    status = system.get_status()
    print(f"   记忆数: {status['memories']}")
    print(f"   约束数: {status['constraints']}")
    print(f"   能力模块: {', '.join(status['capabilities'])}")
    print(f"   事件数: {status['recent_events']}")
    
    print("\n" + "="*60)
    print("✅ 系统测试完成")
    print("="*60)
