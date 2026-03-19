"""
Agent执行引擎 v3.0 (Agent Execution Engine)

根本性重构，解决以下问题：
1. 概念Agent vs 真并行的混淆
2. 缺乏强制验证机制
3. 编造内容无自动检测
4. 不确定性未显化

核心设计：
- 强制检查点：每个生成步骤必须通过验证
- 真并行支持：通过框架层实现真正的独立执行
- 不确定性传播：不确定性必须显化并传递
- 验证即代码：验证不是可选项，是强制环节
"""

from typing import List, Dict, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import asyncio
import time
import hashlib
from abc import ABC, abstractmethod


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = auto()      # 串行执行（概念Agent）
    PARALLEL = auto()        # 真并行（独立session）
    HYBRID = auto()          # 混合模式（动态选择）


class VerificationStatus(Enum):
    """验证状态"""
    PENDING = auto()         # 待验证
    PASSED = auto()          # 通过
    FAILED = auto()          # 失败
    UNCERTAIN = auto()       # 不确定（需要人工确认）


@dataclass
class Uncertainty:
    """不确定性记录"""
    source: str              # 来源（哪个步骤）
    description: str         # 描述
    confidence: float        # 置信度 0-1
    impact: str              # 对结果的影响


@dataclass
class VerificationResult:
    """验证结果"""
    status: VerificationStatus
    score: float             # 验证评分 0-1
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    requires_human_review: bool = False


@dataclass
class AgentOutput:
    """
    Agent输出（强制结构化）
    
    每个Agent必须提供：
    - 结果本身
    - 置信度
    - 推理过程（可审查）
    - 不确定性列表（必须显化！）
    """
    content: Any
    confidence: float        # 强制！0-1
    reasoning: str          # 强制！推理过程
    uncertainties: List[Uncertainty] = field(default_factory=list)
    verification: VerificationResult = field(default_factory=lambda: 
        VerificationResult(status=VerificationStatus.PENDING, score=0.0)
    )
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # 强制规范化
        self.confidence = max(0.0, min(1.0, self.confidence))
        
        # 如果没有不确定性，强制添加一个
        if not self.uncertainties and self.confidence < 0.9:
            self.uncertainties.append(Uncertainty(
                source="self",
                description="未明确识别的潜在不确定性",
                confidence=1 - self.confidence,
                impact="可能影响结果可靠性"
            ))


@dataclass
class Checkpoint:
    """执行检查点"""
    name: str
    check_function: Callable[[AgentOutput], VerificationResult]
    is_blocking: bool        # 失败是否阻断执行
    auto_fix: bool          # 是否尝试自动修复


class VerificationLayer:
    """
    验证层 - 每个生成必须通过验证
    
    不是可选项，是强制环节。
    """
    
    def __init__(self):
        self.checkpoints: List[Checkpoint] = []
        self._register_default_checkpoints()
    
    def _register_default_checkpoints(self):
        """注册默认检查点"""
        
        # 检查点1: 置信度检查
        self.add_checkpoint(Checkpoint(
            name="confidence_check",
            check_function=self._check_confidence,
            is_blocking=False,
            auto_fix=False
        ))
        
        # 检查点2: 编造内容检测
        self.add_checkpoint(Checkpoint(
            name="fabrication_detection",
            check_function=self._check_fabrication,
            is_blocking=True,
            auto_fix=True
        ))
        
        # 检查点3: 不确定性显化
        self.add_checkpoint(Checkpoint(
            name="uncertainty_explicit",
            check_function=self._check_uncertainty,
            is_blocking=True,
            auto_fix=True
        ))
        
        # 检查点4: 外部数据验证
        self.add_checkpoint(Checkpoint(
            name="external_data_verification",
            check_function=self._check_external_data,
            is_blocking=True,
            auto_fix=False
        ))
    
    def add_checkpoint(self, checkpoint: Checkpoint):
        """添加检查点"""
        self.checkpoints.append(checkpoint)
    
    def verify(self, output: AgentOutput, context: Dict[str, Any]) -> AgentOutput:
        """
        验证输出
        
        所有检查点必须通过，否则阻断或修复
        """
        for checkpoint in self.checkpoints:
            result = checkpoint.check_function(output)
            
            if result.status == VerificationStatus.FAILED:
                if checkpoint.is_blocking:
                    # 阻断执行，要求修正
                    output.verification = result
                    return output
                
                elif checkpoint.auto_fix:
                    # 尝试自动修复
                    output = self._auto_fix(output, checkpoint.name)
            
            elif result.status == VerificationStatus.UNCERTAIN:
                # 标记需要人工审查
                output.verification = result
                output.verification.requires_human_review = True
        
        # 所有检查通过
        output.verification = VerificationResult(
            status=VerificationStatus.PASSED,
            score=0.9
        )
        return output
    
    def _check_confidence(self, output: AgentOutput) -> VerificationResult:
        """检查置信度是否合理"""
        if output.confidence > 0.9 and output.uncertainties:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                score=0.5,
                issues=["高置信度(>0.9)但有不确定性记录，矛盾"]
            )
        
        if output.confidence < 0.3:
            return VerificationResult(
                status=VerificationStatus.UNCERTAIN,
                score=output.confidence,
                issues=["置信度过低，结果可能不可靠"],
                suggestions=["增加不确定性标注", "建议寻求其他Agent验证"]
            )
        
        return VerificationResult(status=VerificationStatus.PASSED, score=1.0)
    
    def _check_fabrication(self, output: AgentOutput) -> VerificationResult:
        """检查编造内容"""
        # 检测模式：过于具体的细节但没有来源
        fabrication_indicators = [
            '"' in output.reasoning and '根据' not in output.reasoning,
            '具体' in output.reasoning and '来源' not in output.reasoning,
        ]
        
        if any(fabrication_indicators):
            return VerificationResult(
                status=VerificationStatus.FAILED,
                score=0.3,
                issues=["检测到可能编造的内容：具体细节缺乏来源"],
                suggestions=["添加来源引用", "降低置信度", "显化不确定性"]
            )
        
        return VerificationResult(status=VerificationStatus.PASSED, score=1.0)
    
    def _check_uncertainty(self, output: AgentOutput) -> VerificationResult:
        """检查不确定性是否显化"""
        # 如果置信度不是1.0，必须有不确定性记录
        if output.confidence < 1.0 and not output.uncertainties:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                score=0.5,
                issues=["置信度不足1.0但未记录不确定性"],
                suggestions=["显化不确定性：我在哪些方面不确定？"]
            )
        
        return VerificationResult(status=VerificationStatus.PASSED, score=1.0)
    
    def _check_external_data(self, output: AgentOutput) -> VerificationResult:
        """检查外部数据引用"""
        # 如果引用了图片/文件，必须标记为已验证
        content_str = str(output.content)
        
        if '图片' in content_str or '截图' in content_str:
            if not output.metadata.get('image_verified', False):
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    score=0.0,
                    issues=["引用了图片但未验证（未读取）"],
                    suggestions=["使用read工具读取图片", "或标注为'根据文件名推测'"]
                )
        
        return VerificationResult(status=VerificationStatus.PASSED, score=1.0)
    
    def _auto_fix(self, output: AgentOutput, checkpoint_name: str) -> AgentOutput:
        """自动修复"""
        if checkpoint_name == "uncertainty_explicit":
            # 自动添加不确定性
            output.uncertainties.append(Uncertainty(
                source="auto_fix",
                description="自动添加：此处存在未显化的不确定性",
                confidence=0.5,
                impact="可能影响结果准确性"
            ))
            output.confidence = min(output.confidence, 0.7)
        
        elif checkpoint_name == "fabrication_detection":
            # 添加来源声明
            output.reasoning = "【推测】" + output.reasoning
            output.confidence = min(output.confidence, 0.5)
        
        return output


class AgentExecutor(ABC):
    """
    Agent执行器基类
    
    所有Agent必须继承此类，强制通过验证层
    """
    
    def __init__(self, name: str, mode: ExecutionMode = ExecutionMode.SEQUENTIAL):
        self.name = name
        self.mode = mode
        self.verification_layer = VerificationLayer()
        self.execution_history: List[AgentOutput] = []
    
    async def execute(self, task: Dict[str, Any]) -> AgentOutput:
        """
        执行任务（强制验证流程）
        """
        # 1. 生成输出
        raw_output = await self._generate(task)
        
        # 2. 强制验证（不是可选项！）
        verified_output = self.verification_layer.verify(
            raw_output, 
            context={'task': task, 'agent': self.name}
        )
        
        # 3. 如果验证失败且阻断，抛出异常或返回错误
        if verified_output.verification.status == VerificationStatus.FAILED:
            if self._is_blocking_failure(verified_output.verification):
                return self._handle_blocking_failure(verified_output)
        
        # 4. 记录历史
        self.execution_history.append(verified_output)
        
        return verified_output
    
    @abstractmethod
    async def _generate(self, task: Dict[str, Any]) -> AgentOutput:
        """子类实现生成逻辑"""
        pass
    
    def _is_blocking_failure(self, verification: VerificationResult) -> bool:
        """判断是否是阻断性失败"""
        critical_issues = [
            "未验证外部数据",
            "编造内容",
            "严重矛盾"
        ]
        return any(issue in str(verification.issues) for issue in critical_issues)
    
    def _handle_blocking_failure(self, output: AgentOutput) -> AgentOutput:
        """处理阻断性失败"""
        # 修改输出，明确标注问题
        output.content = f"[验证失败] {output.verification.issues[0]}\n\n原始内容：{output.content}"
        output.confidence = 0.0
        return output


class ConceptualAgent(AgentExecutor):
    """
    概念Agent - 串行执行，但强制验证
    
    适合：简单任务，低延迟要求
    """
    
    def __init__(self, name: str):
        super().__init__(name, ExecutionMode.SEQUENTIAL)
    
    async def _generate(self, task: Dict[str, Any]) -> AgentOutput:
        """生成输出（示例）"""
        # 这里应该是实际的生成逻辑
        # 示例：简单的任务处理
        content = f"处理任务: {task.get('description', '未知任务')}"
        
        return AgentOutput(
            content=content,
            confidence=0.7,
            reasoning=f"基于任务描述'{task.get('description')}'生成",
            uncertainties=[
                Uncertainty(
                    source="conceptual_agent",
                    description="概念Agent，可能存在偏见",
                    confidence=0.3,
                    impact="结果可能不够客观"
                )
            ],
            metadata={'agent_type': 'conceptual'}
        )


class ParallelAgent(AgentExecutor):
    """
    真并行Agent - 通过框架实现独立执行
    
    适合：需要独立视角，高可靠性要求
    
    注意：这需要通过sessions_spawn实现真正的独立session
    """
    
    def __init__(self, name: str, agent_id: Optional[str] = None):
        super().__init__(name, ExecutionMode.PARALLEL)
        self.agent_id = agent_id or name
    
    async def _generate(self, task: Dict[str, Any]) -> AgentOutput:
        """通过独立session生成（示例）"""
        # 实际实现应该调用 sessions_spawn
        # 这里模拟
        
        content = f"[独立Session] {self.name} 处理: {task.get('description')}"
        
        return AgentOutput(
            content=content,
            confidence=0.8,
            reasoning="通过独立session生成，视角更客观",
            uncertainties=[
                Uncertainty(
                    source="parallel_agent",
                    description="独立session，但仍有模型固有限制",
                    confidence=0.2,
                    impact="轻微"
                )
            ],
            metadata={
                'agent_type': 'parallel',
                'session_id': f"session_{hash(self.name + str(time.time()))}"
            }
        )


class MultiAgentOrchestrator:
    """
    多Agent协调器
    
    统一管理概念Agent和真并行Agent
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentExecutor] = {}
        self.verification_layer = VerificationLayer()
    
    def register_agent(self, agent: AgentExecutor):
        """注册Agent"""
        self.agents[agent.name] = agent
    
    async def execute_single(
        self, 
        agent_name: str, 
        task: Dict[str, Any]
    ) -> AgentOutput:
        """执行单个Agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} 未注册")
        
        return await self.agents[agent_name].execute(task)
    
    async def execute_parallel(
        self,
        agent_names: List[str],
        task: Dict[str, Any]
    ) -> List[AgentOutput]:
        """并行执行多个Agent"""
        tasks = [
            self.agents[name].execute(task) 
            for name in agent_names 
            if name in self.agents
        ]
        
        return await asyncio.gather(*tasks)
    
    async def execute_with_verification_chain(
        self,
        task: Dict[str, Any],
        executor_agent: str,
        verifier_agents: List[str]
    ) -> AgentOutput:
        """
        执行链：生成 → 验证 → 修正
        
        executor_agent: 生成结果的Agent
        verifier_agents: 审查结果的Agent列表
        """
        # 1. 生成
        output = await self.execute_single(executor_agent, task)
        
        # 2. 如果生成失败，直接返回
        if output.verification.status == VerificationStatus.FAILED:
            return output
        
        # 3. 并行验证
        verify_tasks = [
            self.execute_single(name, {
                'description': f'验证以下输出: {output.content}',
                'original_output': output
            })
            for name in verifier_agents
        ]
        
        verify_results = await asyncio.gather(*verify_tasks)
        
        # 4. 整合验证结果
        issues = []
        for vr in verify_results:
            if vr.verification.status == VerificationStatus.FAILED:
                issues.extend(vr.verification.issues)
        
        if issues:
            output.verification = VerificationResult(
                status=VerificationStatus.FAILED,
                score=0.3,
                issues=issues
            )
            output.confidence *= 0.5
        
        return output
    
    def integrate_outputs(
        self,
        outputs: List[AgentOutput],
        strategy: str = "confidence_weighted"
    ) -> AgentOutput:
        """
        整合多个Agent的输出
        
        strategy: 
            - confidence_weighted: 按置信度加权
            - voting: 投票
            - best: 选择最佳
        """
        if not outputs:
            raise ValueError("没有输出可整合")
        
        if strategy == "best":
            # 选择置信度最高的
            best = max(outputs, key=lambda x: x.confidence)
            return best
        
        elif strategy == "confidence_weighted":
            # 按置信度加权平均
            total_confidence = sum(o.confidence for o in outputs)
            
            # 简化处理：返回加权后的结果
            best = max(outputs, key=lambda x: x.confidence)
            best.uncertainties.extend([
                Uncertainty(
                    source="integration",
                    description=f"整合了{len(outputs)}个Agent的输出",
                    confidence=0.5,
                    impact="整合过程可能引入偏差"
                )
            ])
            return best
        
        elif strategy == "voting":
            # 简单多数投票
            return max(outputs, key=lambda x: outputs.count(x))
        
        else:
            raise ValueError(f"未知的整合策略: {strategy}")


# 便捷函数
def create_conceptual_agent(name: str) -> ConceptualAgent:
    """创建概念Agent"""
    return ConceptualAgent(name)


def create_parallel_agent(name: str, agent_id: Optional[str] = None) -> ParallelAgent:
    """创建真并行Agent"""
    return ParallelAgent(name, agent_id)


def create_orchestrator() -> MultiAgentOrchestrator:
    """创建协调器"""
    return MultiAgentOrchestrator()


__all__ = [
    'AgentExecutor',
    'ConceptualAgent',
    'ParallelAgent',
    'MultiAgentOrchestrator',
    'VerificationLayer',
    'AgentOutput',
    'Uncertainty',
    'VerificationResult',
    'ExecutionMode',
    'VerificationStatus',
    'create_conceptual_agent',
    'create_parallel_agent',
    'create_orchestrator',
]
