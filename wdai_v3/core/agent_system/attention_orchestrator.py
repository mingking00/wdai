"""
注意力协调器 - Attention Residuals 思想的应用

将 AttnRes 的核心思想应用到 MultiAgent 系统：
- 后续 Agent 可以选择性地"回头看"前面所有 Agent 的输出
- 用注意力机制动态加权，而非简单的链式传递
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import numpy as np
from enum import Enum
import asyncio


@dataclass
class AttentionConfig:
    """注意力配置"""
    num_blocks: int = 4                    # 分块数（类似 Block AttnRes）
    temperature: float = 1.0               # softmax温度
    local_attention_range: int = 2         # 局部关注范围
    enable_skip_connections: bool = True   # 是否允许跳跃连接
    learned_weights: bool = True           # 是否使用学习的权重


@dataclass
class AgentAttentionState:
    """Agent的注意力状态"""
    agent_id: str
    block_id: int                          # 所属块
    query_vector: np.ndarray               # 查询向量（类似 AttnRes 的 w_l）
    key_vector: np.ndarray                 # 键向量
    historical_weights: List[float] = field(default_factory=list)


class AttentionBasedOrchestrator:
    """
    基于注意力的协调器
    
    核心改进：
    1. 所有 Agent 输出存储在"记忆池"中
    2. 每个 Agent 可以 attention 到前面所有 Agent 的输出
    3. 支持分块（Block）降低复杂度
    4. 支持跳跃连接（skip connections）
    """
    
    def __init__(self, config: AttentionConfig = None):
        self.config = config or AttentionConfig()
        self.agent_states: Dict[str, AgentAttentionState] = {}
        self.output_memory: List[Dict[str, Any]] = []  # 类似 AttnRes 的层输出缓存
        self.blocks: Dict[int, List[str]] = {}         # 块映射
        self.experience_weights: Dict[str, float] = {} # 学习到的权重
        
    def register_agent(self, agent_id: str, block_id: int = 0):
        """注册 Agent 并初始化注意力状态"""
        # 初始化查询向量（类似 AttnRes 的零初始化）
        query_dim = 64
        query_vector = np.zeros(query_dim)
        
        self.agent_states[agent_id] = AgentAttentionState(
            agent_id=agent_id,
            block_id=block_id,
            query_vector=query_vector,
            key_vector=np.random.randn(query_dim) * 0.01  # 小随机初始化
        )
        
        # 添加到块
        if block_id not in self.blocks:
            self.blocks[block_id] = []
        self.blocks[block_id].append(agent_id)
    
    async def execute_with_attention(
        self,
        task: Dict[str, Any],
        agent_sequence: List[str]
    ) -> Dict[str, Any]:
        """
        执行 Agent 序列，使用注意力机制聚合信息
        
        对比传统模式：
        - 传统：A → B → C （C 只能看到 B 的输出）
        - 注意力：A → B(attention to A) → C(attention to A,B)
        """
        print(f"\n{'='*70}")
        print("🧠 Attention-Based Agent Execution")
        print(f"{'='*70}")
        print(f"Task: {task.get('description', 'Unknown')}")
        print(f"Agent sequence: {' -> '.join(agent_sequence)}")
        
        # 清空记忆池
        self.output_memory = []
        
        # 逐个执行 Agent，但每个都可以 access 前面所有的输出
        for i, agent_id in enumerate(agent_sequence):
            print(f"\n--- Step {i+1}: {agent_id} ---")
            
            # 1. 计算注意力权重（AttnRes 核心）
            attention_weights = self._compute_attention_weights(i, agent_id)
            
            print(f"Attention weights over previous outputs:")
            for j, (mem, weight) in enumerate(zip(self.output_memory, attention_weights)):
                print(f"  [{j}] {mem.get('agent_id', 'unknown')}: {weight:.3f}")
            
            # 2. 聚合历史信息（加权求和）
            aggregated_context = self._aggregate_with_attention(attention_weights)
            
            # 3. 执行当前 Agent（带注意力聚合的上下文）
            output = await self._execute_agent(
                agent_id, 
                task, 
                aggregated_context,
                attention_weights
            )
            
            # 4. 存储到记忆池
            self.output_memory.append({
                'agent_id': agent_id,
                'output': output,
                'step': i,
                'attention_weights': attention_weights.tolist()
            })
            
            # 5. 更新查询向量（学习）
            self._update_query_vector(agent_id, output)
        
        # 最终整合：对所有 Agent 输出做全局 attention
        final_output = self._global_attention_integration()
        
        print(f"\n{'='*70}")
        print("Final Integration (Global Attention)")
        print(f"{'='*70}")
        
        return final_output
    
    def _compute_attention_weights(
        self, 
        current_step: int, 
        current_agent_id: str
    ) -> np.ndarray:
        """
        计算对前面所有 Agent 输出的注意力权重
        
        这是 AttnRes 的核心：softmax(Q · K^T)
        """
        if current_step == 0:
            return np.array([])  # 第一个 Agent 没有历史
        
        state = self.agent_states[current_agent_id]
        query = state.query_vector
        
        # 获取前面所有 Agent 的 key vectors
        keys = []
        for mem in self.output_memory:
            prev_agent_id = mem['agent_id']
            if prev_agent_id in self.agent_states:
                key = self.agent_states[prev_agent_id].key_vector
                keys.append(key)
            else:
                # 未注册 Agent 用随机 key
                keys.append(np.random.randn(len(query)) * 0.01)
        
        if not keys:
            return np.array([])
        
        keys = np.array(keys)
        
        # 计算 attention scores: Q · K^T
        scores = np.dot(keys, query)
        
        # Block AttnRes：如果是不同块，应用掩码
        scores = self._apply_block_mask(current_agent_id, scores)
        
        # Local attention：只关注最近的 k 个
        if self.config.local_attention_range > 0:
            scores = self._apply_local_mask(scores)
        
        # Softmax 归一化
        if len(scores) > 0:
            # 除以 temperature
            scores = scores / self.config.temperature
            # 数值稳定性处理
            scores = scores - np.max(scores)
            exp_scores = np.exp(scores)
            weights = exp_scores / np.sum(exp_scores)
        else:
            weights = np.array([])
        
        return weights
    
    def _apply_block_mask(
        self, 
        current_agent_id: str, 
        scores: np.ndarray
    ) -> np.ndarray:
        """
        应用块掩码（Block AttnRes）
        
        同一块内：全连接（dense）
        不同块间：稀疏连接（sparse）
        """
        if not self.config.num_blocks or len(scores) == 0:
            return scores
        
        current_block = self.agent_states[current_agent_id].block_id
        
        for i, mem in enumerate(self.output_memory):
            prev_agent_id = mem['agent_id']
            if prev_agent_id in self.agent_states:
                prev_block = self.agent_states[prev_agent_id].block_id
                
                if prev_block != current_block:
                    # 不同块：降低权重（但不是完全屏蔽）
                    scores[i] *= 0.3
        
        return scores
    
    def _apply_local_mask(self, scores: np.ndarray) -> np.ndarray:
        """局部注意力掩码：只关注最近的 k 个"""
        if len(scores) <= self.config.local_attention_range:
            return scores
        
        # 远距离的 score 置为很小的值（但不完全屏蔽，允许跳跃）
        mask = np.ones_like(scores) * -1e9
        mask[-self.config.local_attention_range:] = 0
        
        return scores + mask
    
    def _aggregate_with_attention(
        self, 
        weights: np.ndarray
    ) -> Dict[str, Any]:
        """用注意力权重聚合历史输出"""
        if len(weights) == 0 or len(self.output_memory) == 0:
            return {}
        
        # 加权聚合不确定性
        aggregated_uncertainties = []
        total_confidence = 0.0
        
        for mem, weight in zip(self.output_memory, weights):
            output = mem['output']
            if hasattr(output, 'uncertainties'):
                for u in output.uncertainties:
                    # 根据 attention weight 调整不确定性影响
                    weighted_u = {
                        'source': u.source,
                        'description': u.description,
                        'impact': u.impact,
                        'attention_weight': float(weight),
                        'effective_uncertainty': u.confidence * weight
                    }
                    aggregated_uncertainties.append(weighted_u)
            
            if hasattr(output, 'confidence'):
                total_confidence += output.confidence * weight
        
        return {
            'aggregated_uncertainties': aggregated_uncertainties,
            'weighted_confidence': total_confidence,
            'num_sources': len(self.output_memory)
        }
    
    async def _execute_agent(
        self,
        agent_id: str,
        task: Dict[str, Any],
        aggregated_context: Dict[str, Any],
        attention_weights: np.ndarray
    ) -> Any:
        """执行单个 Agent（示例实现）"""
        # 这里应该调用实际的 Agent 执行逻辑
        # 示例：模拟 Agent 输出
        
        from core.agent_system.agent_engine_v3 import AgentOutput, Uncertainty
        
        # 基于 attention weights 调整置信度
        # 如果关注了很多历史，置信度可能更高（信息更充分）
        # 但也可能因为信息冲突而降低
        base_confidence = 0.7
        if len(attention_weights) > 0:
            # 注意力熵：分布越均匀，信息越充分
            entropy = -np.sum(attention_weights * np.log(attention_weights + 1e-10))
            max_entropy = np.log(len(attention_weights))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            
            confidence_adjustment = (normalized_entropy - 0.5) * 0.2
            final_confidence = base_confidence + confidence_adjustment
        else:
            final_confidence = base_confidence
        
        return AgentOutput(
            content=f"Output from {agent_id} with attention to {len(attention_weights)} previous outputs",
            confidence=final_confidence,
            reasoning=f"Aggregated context from {aggregated_context.get('num_sources', 0)} sources",
            uncertainties=[
                Uncertainty(
                    source=f"attention_to_history",
                    description=f"This output depends on {len(attention_weights)} previous outputs",
                    confidence=1 - final_confidence,
                    impact="May inherit errors from previous agents"
                )
            ]
        )
    
    def _update_query_vector(self, agent_id: str, output: Any):
        """更新查询向量（学习过程）"""
        state = self.agent_states[agent_id]
        
        # 简单的在线学习：根据输出质量调整
        if hasattr(output, 'confidence'):
            # 高置信度 → 增强当前方向
            # 低置信度 → 探索新方向
            learning_rate = 0.01
            noise = np.random.randn(len(state.query_vector)) * 0.001
            
            if output.confidence > 0.8:
                # 强化当前查询方向
                state.query_vector += learning_rate * state.query_vector
            else:
                # 添加探索噪声
                state.query_vector += noise
        
        # 记录历史
        state.historical_weights.append(output.confidence if hasattr(output, 'confidence') else 0.5)
    
    def _global_attention_integration(self) -> Dict[str, Any]:
        """全局注意力整合：对所有 Agent 输出做最终聚合"""
        if not self.output_memory:
            return {'error': 'No outputs to integrate'}
        
        # 对所有输出做全局 attention
        n = len(self.output_memory)
        
        # 简单的均匀权重（可以改进为基于质量的权重）
        weights = np.ones(n) / n
        
        # 加权聚合
        integrated_content = []
        total_confidence = 0.0
        all_uncertainties = []
        
        for mem, weight in zip(self.output_memory, weights):
            output = mem['output']
            integrated_content.append({
                'agent': mem['agent_id'],
                'content': output.content if hasattr(output, 'content') else str(output),
                'weight': float(weight),
                'step': mem['step']
            })
            
            if hasattr(output, 'confidence'):
                total_confidence += output.confidence * weight
            
            if hasattr(output, 'uncertainties'):
                all_uncertainties.extend(output.uncertainties)
        
        return {
            'integrated_outputs': integrated_content,
            'global_confidence': total_confidence,
            'uncertainty_chain': all_uncertainties,
            'attention_history': [
                {
                    'step': mem['step'],
                    'agent': mem['agent_id'],
                    'attention_weights': mem.get('attention_weights', [])
                }
                for mem in self.output_memory
            ]
        }
    
    def get_attention_visualization(self) -> Dict[str, Any]:
        """获取注意力可视化数据"""
        if not self.output_memory:
            return {}
        
        return {
            'num_steps': len(self.output_memory),
            'attention_matrix': [
                mem.get('attention_weights', [])
                for mem in self.output_memory
            ],
            'agent_sequence': [mem['agent_id'] for mem in self.output_memory],
            'blocks': {
                block_id: agent_ids
                for block_id, agent_ids in self.blocks.items()
            }
        }


# 便捷函数
def create_attention_orchestrator(
    num_blocks: int = 4,
    temperature: float = 1.0
) -> AttentionBasedOrchestrator:
    """创建注意力协调器"""
    config = AttentionConfig(
        num_blocks=num_blocks,
        temperature=temperature
    )
    return AttentionBasedOrchestrator(config)


__all__ = [
    'AttentionBasedOrchestrator',
    'AttentionConfig',
    'AgentAttentionState',
    'create_attention_orchestrator',
]
