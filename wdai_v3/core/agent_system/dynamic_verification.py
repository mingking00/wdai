"""
动态验证层 - 将 AttnRes 思想应用到认知安全系统

核心思想：
- 不同检查点的重要性不是固定的（不像传统0.5+0.5）
- 根据任务类型、历史违规数据，动态学习权重
- 高风险的检查点自动获得更高权重
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict
import time

# 导入 VerificationStatus
from core.agent_system.agent_engine_v3 import VerificationStatus


class CheckpointType(Enum):
    """检查点类型"""
    EXTERNAL_DATA = "external_data"
    FABRICATION = "fabrication"
    UNCERTAINTY = "uncertainty"
    ABSOLUTE_STATEMENT = "absolute_statement"
    TOOL_USAGE = "tool_usage"
    REASONING_QUALITY = "reasoning_quality"


@dataclass
class ViolationHistory:
    """违规历史记录"""
    checkpoint_type: CheckpointType
    count: int = 0
    last_occurrence: float = 0.0
    severity_scores: List[float] = field(default_factory=list)
    
    def update(self, severity: float):
        """更新违规记录"""
        self.count += 1
        self.last_occurrence = time.time()
        self.severity_scores.append(severity)
        
        # 只保留最近20条
        if len(self.severity_scores) > 20:
            self.severity_scores = self.severity_scores[-20:]
    
    def get_recent_frequency(self, window_seconds: float = 3600) -> float:
        """计算最近时间窗口内的违规频率"""
        current_time = time.time()
        recent_count = sum(
            1 for t in [self.last_occurrence] * self.count  # 简化计算
            if current_time - t < window_seconds
        )
        return recent_count / max(window_seconds / 3600, 1)  # 每小时次数
    
    def get_average_severity(self) -> float:
        """平均严重程度"""
        if not self.severity_scores:
            return 0.0
        return np.mean(self.severity_scores[-10:])  # 最近10次


@dataclass
class DynamicCheckpoint:
    """动态检查点"""
    name: str
    type: CheckpointType
    base_weight: float                    # 基础权重
    check_function: Callable[[Any], Any]
    is_blocking: bool
    auto_fix: bool
    
    # 动态调整的参数
    current_weight: float = field(default=0.0)
    attention_score: float = field(default=0.0)  # 类似 AttnRes 的 attention weight
    
    def __post_init__(self):
        if self.current_weight == 0.0:
            self.current_weight = self.base_weight


class DynamicVerificationLayer:
    """
    动态验证层
    
    改进点：
    1. 检查点权重动态调整（学习历史违规模式）
    2. 根据任务类型自适应（不同任务关注不同风险）
    3. 注意力机制：高风险的检查点获得更多"注意力"
    4. 零初始化策略：初始时均匀权重，逐渐学习
    """
    
    def __init__(self):
        self.checkpoints: Dict[CheckpointType, DynamicCheckpoint] = {}
        self.violation_history: Dict[CheckpointType, ViolationHistory] = {}
        self.task_type_weights: Dict[str, Dict[CheckpointType, float]] = {}
        
        # 学习率
        self.learning_rate = 0.1
        
        # 初始化（零初始化策略）
        self._initialize_checkpoints()
        self._initialize_violation_history()
    
    def _initialize_checkpoints(self):
        """初始化检查点（零初始化：均匀权重）"""
        from core.agent_system.agent_engine_v3 import VerificationResult, VerificationStatus
        
        # 所有检查点初始权重相同（零初始化策略）
        initial_weight = 1.0 / len(CheckpointType)
        
        self.checkpoints[CheckpointType.EXTERNAL_DATA] = DynamicCheckpoint(
            name="external_data_verification",
            type=CheckpointType.EXTERNAL_DATA,
            base_weight=initial_weight,
            check_function=self._check_external_data,
            is_blocking=True,
            auto_fix=False,
            current_weight=initial_weight
        )
        
        self.checkpoints[CheckpointType.FABRICATION] = DynamicCheckpoint(
            name="fabrication_detection",
            type=CheckpointType.FABRICATION,
            base_weight=initial_weight,
            check_function=self._check_fabrication,
            is_blocking=True,
            auto_fix=True,
            current_weight=initial_weight
        )
        
        self.checkpoints[CheckpointType.UNCERTAINTY] = DynamicCheckpoint(
            name="uncertainty_explicit",
            type=CheckpointType.UNCERTAINTY,
            base_weight=initial_weight,
            check_function=self._check_uncertainty,
            is_blocking=True,
            auto_fix=True,
            current_weight=initial_weight
        )
        
        self.checkpoints[CheckpointType.ABSOLUTE_STATEMENT] = DynamicCheckpoint(
            name="absolute_statement",
            type=CheckpointType.ABSOLUTE_STATEMENT,
            base_weight=initial_weight * 0.5,  # 较低优先级
            check_function=self._check_absolute_statements,
            is_blocking=False,
            auto_fix=True,
            current_weight=initial_weight * 0.5
        )
        
        self.checkpoints[CheckpointType.TOOL_USAGE] = DynamicCheckpoint(
            name="tool_usage",
            type=CheckpointType.TOOL_USAGE,
            base_weight=initial_weight,
            check_function=self._check_tool_usage,
            is_blocking=True,
            auto_fix=False,
            current_weight=initial_weight
        )
    
    def _initialize_violation_history(self):
        """初始化违规历史"""
        for cp_type in CheckpointType:
            self.violation_history[cp_type] = ViolationHistory(
                checkpoint_type=cp_type
            )
    
    def verify(
        self, 
        response: str, 
        context: Dict[str, Any],
        task_type: str = "general"
    ) -> Dict[str, Any]:
        """
        动态验证
        
        核心流程：
        1. 根据任务类型和历史数据，计算当前权重
        2. 按权重排序检查点（高风险优先）
        3. 执行检查
        4. 更新权重（学习）
        """
        # 1. 计算动态权重（类似 AttnRes 的 attention weight 计算）
        self._compute_dynamic_weights(task_type, context)
        
        # 2. 按权重排序（高风险优先检查）
        sorted_checkpoints = sorted(
            self.checkpoints.values(),
            key=lambda x: x.current_weight,
            reverse=True
        )
        
        print(f"\n{'='*70}")
        print("Dynamic Verification (AttnRes-style Weighted)")
        print(f"{'='*70}")
        print(f"Task type: {task_type}")
        print(f"Checkpoint weights (attention-based):")
        for cp in sorted_checkpoints:
            print(f"  {cp.name}: {cp.current_weight:.3f} "
                  f"(base: {cp.base_weight:.3f}, attention: {cp.attention_score:.3f})")
        
        # 3. 执行检查
        violations = []
        corrected_response = response
        
        for checkpoint in sorted_checkpoints:
            result = checkpoint.check_function(corrected_response, context)
            
            # 修复：直接比较枚举值，不是 .value
            if result.status == VerificationStatus.FAILED:
                # 记录违规
                self._record_violation(checkpoint.type, result.score)
                
                violations.append({
                    'checkpoint': checkpoint.name,
                    'type': checkpoint.type.value,
                    'weight': checkpoint.current_weight,
                    'issues': result.issues,
                    'is_blocking': checkpoint.is_blocking
                })
                
                # 阻断或修正
                if checkpoint.is_blocking:
                    print(f"\n🚫 Blocking violation: {checkpoint.name} "
                          f"(weight: {checkpoint.current_weight:.3f})")
                    
                    # 更新权重（即使在阻断情况下也要学习）
                    self._update_weights_after_verification(len(violations))
                    
                    return {
                        'is_safe': False,
                        'violations': violations,
                        'corrected_response': corrected_response,
                        'block_reason': f"{checkpoint.name}: {result.issues[0] if result.issues else 'Unknown'}"
                    }
                elif checkpoint.auto_fix:
                    corrected_response = self._auto_fix(
                        corrected_response, 
                        checkpoint.type
                    )
        
        # 4. 通过后，更新权重（学习）
        self._update_weights_after_verification(len(violations))
        
        return {
            'is_safe': len(violations) == 0,
            'violations': violations,
            'corrected_response': corrected_response,
            'block_reason': None
        }
    
    def _compute_dynamic_weights(self, task_type: str, context: Dict[str, Any]):
        """
        计算动态权重（AttnRes 核心思想）
        
        weight = softmax(base_weight + attention_score + task_adjustment + history_adjustment)
        """
        # 计算每个检查点的 attention score
        scores = []
        
        for cp_type, checkpoint in self.checkpoints.items():
            # 基础分数
            base_score = checkpoint.base_weight
            
            # 历史违规调整（如果某类违规频繁发生，提高权重）
            history = self.violation_history[cp_type]
            recent_frequency = history.get_recent_frequency(window_seconds=3600)
            avg_severity = history.get_average_severity()
            history_adjustment = (recent_frequency * 0.1 + avg_severity * 0.2)
            
            # 任务类型调整
            task_adjustment = self._get_task_adjustment(task_type, cp_type)
            
            # 上下文调整
            context_adjustment = self._get_context_adjustment(context, cp_type)
            
            # 总分数（类似 Q · K^T）
            total_score = base_score + history_adjustment + task_adjustment + context_adjustment
            scores.append((cp_type, total_score))
        
        # Softmax 归一化（得到 attention weights）
        scores_array = np.array([s[1] for s in scores])
        exp_scores = np.exp(scores_array - np.max(scores_array))
        weights = exp_scores / np.sum(exp_scores)
        
        # 更新检查点权重
        for (cp_type, _), weight in zip(scores, weights):
            self.checkpoints[cp_type].current_weight = weight
            self.checkpoints[cp_type].attention_score = weight
    
    def _get_task_adjustment(
        self, 
        task_type: str, 
        checkpoint_type: CheckpointType
    ) -> float:
        """根据任务类型调整权重"""
        # 不同任务类型关注不同风险
        task_risk_map = {
            'image_analysis': {
                CheckpointType.EXTERNAL_DATA: 0.5,  # 图片任务更关注外部数据验证
                CheckpointType.FABRICATION: 0.3,
            },
            'code_generation': {
                CheckpointType.TOOL_USAGE: 0.4,     # 代码任务更关注工具使用
                CheckpointType.REASONING_QUALITY: 0.3,
            },
            'factual_qa': {
                CheckpointType.FABRICATION: 0.5,    # 事实问答更关注编造
                CheckpointType.ABSOLUTE_STATEMENT: 0.3,
            },
            'creative_writing': {
                CheckpointType.UNCERTAINTY: 0.2,    # 创意写作可以适当降低某些检查
            }
        }
        
        return task_risk_map.get(task_type, {}).get(checkpoint_type, 0.0)
    
    def _get_context_adjustment(
        self, 
        context: Dict[str, Any], 
        checkpoint_type: CheckpointType
    ) -> float:
        """根据上下文调整权重"""
        adjustment = 0.0
        
        # 如果上下文明确标记了某些风险，提高对应检查点权重
        if checkpoint_type == CheckpointType.EXTERNAL_DATA:
            if context.get('has_image', False) and not context.get('image_verified', False):
                adjustment += 0.5  # 高风险！
        
        if checkpoint_type == CheckpointType.TOOL_USAGE:
            if context.get('has_read_tool', False) and not context.get('tool_used', False):
                adjustment += 0.3
        
        return adjustment
    
    def _record_violation(self, checkpoint_type: CheckpointType, severity: float):
        """记录违规"""
        self.violation_history[checkpoint_type].update(severity)
    
    def _update_weights_after_verification(self, num_violations: int):
        """验证后更新权重（学习）"""
        if num_violations == 0:
            # 全部通过：稍微降低权重（避免过度检查）
            for cp in self.checkpoints.values():
                cp.base_weight *= (1 - self.learning_rate * 0.1)
        else:
            # 有违规：强化对应检查点的权重
            for cp_type, history in self.violation_history.items():
                if history.count > 0:
                    self.checkpoints[cp_type].base_weight *= (1 + self.learning_rate)
                    
                    # 限制最大权重
                    self.checkpoints[cp_type].base_weight = min(
                        self.checkpoints[cp_type].base_weight, 
                        2.0
                    )
    
    def _check_external_data(self, response: str, context: Dict) -> Any:
        """检查外部数据"""
        from core.agent_system.agent_engine_v3 import VerificationResult, VerificationStatus
        
        if '图片' in response or '截图' in response:
            if not context.get('image_verified', False):
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    score=0.0,
                    issues=["引用了图片但未验证"]
                )
        
        return VerificationResult(status=VerificationStatus.PASSED, score=1.0)
    
    def _check_fabrication(self, response: str, context: Dict) -> Any:
        """检查编造"""
        from core.agent_system.agent_engine_v3 import VerificationResult, VerificationStatus
        
        # 简单的编造检测启发式
        if '"' in response and '根据' not in response and '来源' not in response:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                score=0.3,
                issues=["可能包含未标注来源的引用"]
            )
        
        return VerificationResult(status=VerificationStatus.PASSED, score=1.0)
    
    def _check_uncertainty(self, response: str, context: Dict) -> Any:
        """检查不确定性"""
        from core.agent_system.agent_engine_v3 import VerificationResult, VerificationStatus
        
        # 这里简化处理，实际需要解析 AgentOutput
        return VerificationResult(status=VerificationStatus.PASSED, score=1.0)
    
    def _check_absolute_statements(self, response: str, context: Dict) -> Any:
        """检查绝对化表述"""
        from core.agent_system.agent_engine_v3 import VerificationResult, VerificationStatus
        
        absolute_words = ['肯定', '一定', '绝对', '毫无疑问']
        for word in absolute_words:
            if word in response:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    score=0.5,
                    issues=[f"使用了绝对化词汇'{word}'"]
                )
        
        return VerificationResult(status=VerificationStatus.PASSED, score=1.0)
    
    def _check_tool_usage(self, response: str, context: Dict) -> Any:
        """检查工具使用"""
        from core.agent_system.agent_engine_v3 import VerificationResult, VerificationStatus
        
        if context.get('has_read_tool', False) and not context.get('tool_used', False):
            return VerificationResult(
                status=VerificationStatus.FAILED,
                score=0.0,
                issues=["有可用工具但未使用"]
            )
        
        return VerificationResult(status=VerificationStatus.PASSED, score=1.0)
    
    def _auto_fix(self, response: str, checkpoint_type: CheckpointType) -> str:
        """自动修复"""
        if checkpoint_type == CheckpointType.ABSOLUTE_STATEMENT:
            # 替换绝对化词汇
            replacements = {
                '肯定': '推测',
                '一定': '可能',
                '绝对': '相对',
                '毫无疑问': '可能'
            }
            for old, new in replacements.items():
                response = response.replace(old, new)
        
        return response
    
    def get_weight_statistics(self) -> Dict[str, Any]:
        """获取权重统计"""
        return {
            'checkpoint_weights': {
                cp.name: {
                    'base': cp.base_weight,
                    'current': cp.current_weight,
                    'attention_score': cp.attention_score
                }
                for cp in self.checkpoints.values()
            },
            'violation_history': {
                cp_type.value: {
                    'count': hist.count,
                    'avg_severity': hist.get_average_severity()
                }
                for cp_type, hist in self.violation_history.items()
            }
        }


def create_dynamic_verification_layer() -> DynamicVerificationLayer:
    """创建动态验证层"""
    return DynamicVerificationLayer()


__all__ = [
    'DynamicVerificationLayer',
    'DynamicCheckpoint',
    'CheckpointType',
    'ViolationHistory',
    'create_dynamic_verification_layer',
]
