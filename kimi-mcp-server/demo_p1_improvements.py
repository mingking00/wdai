#!/usr/bin/env python3
"""
Multi-Agent System - P1 Improvements
多智能体系统 - P1级改进

改进内容：
1. 迭代改进循环 (Iterative Refinement Loop)
2. 深度质量评估 (Deep Quality Assessment)
3. 自动反馈机制 (Automatic Feedback System)
"""

import sys
import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

sys.path.insert(0, '/root/.openclaw/workspace/kimi-mcp-server/src')
from extended_tools import KimiMCPExtendedServer
from demo_p0_improvements import ArbitratorAgent, ConflictDetector, AgentOutput, Conflict


class ImprovementType(Enum):
    """改进类型"""
    ADD_DETAIL = "add_detail"           # 增加细节
    FIX_ERROR = "fix_error"             # 修复错误
    IMPROVE_CLARITY = "improve_clarity" # 提高清晰度
    ADD_EXAMPLES = "add_examples"       # 添加示例
    OPTIMIZE_STRUCTURE = "optimize_structure"  # 优化结构
    RESOLVE_CONFLICT = "resolve_conflict"      # 解决冲突


@dataclass
class ImprovementFeedback:
    """改进反馈"""
    target_agent: str
    improvement_type: ImprovementType
    priority: str  # high, medium, low
    description: str
    specific_suggestions: List[str]
    expected_improvement: float  # 预期质量提升


@dataclass
class IterationRound:
    """迭代轮次记录"""
    round_number: int
    outputs: List[AgentOutput]
    quality_scores: Dict[str, float]
    conflicts: List[Conflict]
    feedbacks: List[ImprovementFeedback]
    improvements_made: List[str]


class QualityAssessmentAgent:
    """
    深度质量评估智能体
    
    比P0更深入的质量分析：
    - 多维度评分（完整性、准确性、可读性）
    - 具体改进建议
    - 与最佳实践对比
    """
    
    def __init__(self):
        self.server = KimiMCPExtendedServer()
    
    def deep_assess(self, output: AgentOutput) -> Dict[str, Any]:
        """深度评估单个输出"""
        content = output.content
        
        # 多维度评估
        dimensions = {
            "completeness": self._assess_completeness(content),
            "accuracy": self._assess_accuracy(content),
            "readability": self._assess_readability(content),
            "structure": self._assess_structure(content),
            "practicality": self._assess_practicality(content)
        }
        
        # 计算加权总分
        weights = {
            "completeness": 0.25,
            "accuracy": 0.25,
            "readability": 0.20,
            "structure": 0.15,
            "practicality": 0.15
        }
        
        overall_score = sum(
            dimensions[d] * weights[d] for d in dimensions
        ) * 10  # 转换为10分制
        
        # 生成具体改进建议
        improvements = self._generate_improvements(dimensions, content, output.agent_type)
        
        return {
            "agent_id": output.agent_id,
            "agent_type": output.agent_type,
            "overall_score": round(overall_score, 1),
            "dimensions": {k: round(v * 10, 1) for k, v in dimensions.items()},
            "grade": self._score_to_grade(overall_score),
            "improvements": improvements,
            "assessment_time": datetime.now().isoformat()
        }
    
    def _assess_completeness(self, content: Dict) -> float:
        """评估完整性"""
        score = 0.5  # 基础分
        
        # 检查关键字段
        key_fields = ["summary", "details", "metadata", "references"]
        present_fields = sum(1 for f in key_fields if f in content)
        score += (present_fields / len(key_fields)) * 0.5
        
        return min(1.0, score)
    
    def _assess_accuracy(self, content: Dict) -> float:
        """评估准确性"""
        score = 0.8  # 基础分（假设正确）
        
        # 检查是否有错误信息
        if content.get("error"):
            score -= 0.3
        
        # 检查一致性
        if "version" in content and "framework" in content:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _assess_readability(self, content: Dict) -> float:
        """评估可读性"""
        score = 0.6
        
        content_str = json.dumps(content)
        
        # 长度适中
        if 200 < len(content_str) < 5000:
            score += 0.2
        
        # 有结构化格式
        if any(isinstance(v, (list, dict)) for v in content.values()):
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_structure(self, content: Dict) -> float:
        """评估结构"""
        score = 0.5
        
        # 有层次结构
        if len(content) >= 3:
            score += 0.3
        
        # 有清晰的键名
        clear_keys = sum(1 for k in content.keys() if len(k) > 3 and '_' in k)
        if clear_keys >= 2:
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_practicality(self, content: Dict) -> float:
        """评估实用性"""
        score = 0.6
        
        # 有可执行内容
        if "file_path" in content or "code" in content or "commands" in content:
            score += 0.3
        
        # 有使用说明
        if "usage" in content or "example" in content:
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_improvements(
        self, 
        dimensions: Dict[str, float], 
        content: Dict,
        agent_type: str
    ) -> List[ImprovementFeedback]:
        """生成改进建议"""
        improvements = []
        
        # 根据低分项生成建议
        if dimensions["completeness"] < 0.7:
            improvements.append(ImprovementFeedback(
                target_agent=agent_type,
                improvement_type=ImprovementType.ADD_DETAIL,
                priority="high",
                description="内容不够完整，缺少关键信息",
                specific_suggestions=[
                    "添加执行摘要",
                    "包含更多技术细节",
                    "提供参考资料"
                ],
                expected_improvement=1.5
            ))
        
        if dimensions["readability"] < 0.7:
            improvements.append(ImprovementFeedback(
                target_agent=agent_type,
                improvement_type=ImprovementType.IMPROVE_CLARITY,
                priority="medium",
                description="可读性有待提高",
                specific_suggestions=[
                    "使用更清晰的标题",
                    "添加分段说明",
                    "使用列表代替长段落"
                ],
                expected_improvement=1.0
            ))
        
        if dimensions["practicality"] < 0.7:
            improvements.append(ImprovementFeedback(
                target_agent=agent_type,
                improvement_type=ImprovementType.ADD_EXAMPLES,
                priority="medium",
                description="缺少实际示例",
                specific_suggestions=[
                    "添加代码示例",
                    "提供使用场景",
                    "给出具体步骤"
                ],
                expected_improvement=1.2
            ))
        
        return improvements
    
    def _score_to_grade(self, score: float) -> str:
        """分数转等级"""
        if score >= 9:
            return "A+ (卓越)"
        elif score >= 8:
            return "A (优秀)"
        elif score >= 7:
            return "B (良好)"
        elif score >= 6:
            return "C (及格)"
        elif score >= 5:
            return "D (需改进)"
        else:
            return "F (不合格)"


class IterativeImprovementOrchestrator:
    """
    迭代改进编排器
    
    实现循环改进：
    1. 初始执行
    2. 质量评估
    3. 生成反馈
    4. 针对性改进
    5. 重新评估
    6. 直到达标或达到最大轮次
    """
    
    def __init__(self, max_rounds: int = 3, quality_threshold: float = 8.0):
        self.max_rounds = max_rounds
        self.quality_threshold = quality_threshold
        self.assessment_agent = QualityAssessmentAgent()
        self.conflict_detector = ConflictDetector()
        self.iteration_history: List[IterationRound] = []
        self.server = KimiMCPExtendedServer()
    
    async def execute_with_improvement(
        self, 
        initial_outputs: List[AgentOutput],
        agent_factories: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        执行带迭代改进的多智能体工作流
        
        Args:
            initial_outputs: 初始Agent输出
            agent_factories: Agent工厂函数，用于重新生成
        """
        print("\n" + "="*70)
        print("🔄 ITERATIVE IMPROVEMENT ORCHESTRATOR")
        print("="*70)
        print(f"配置: 最大{self.max_rounds}轮迭代, 质量阈值{self.quality_threshold}/10")
        
        current_outputs = initial_outputs
        
        for round_num in range(1, self.max_rounds + 1):
            print(f"\n{'━'*70}")
            print(f"🔄 ROUND {round_num}/{self.max_rounds}")
            print("━"*70)
            
            # 1. 深度质量评估
            print("\n📊 深度质量评估...")
            assessments = []
            for output in current_outputs:
                assessment = self.assessment_agent.deep_assess(output)
                assessments.append(assessment)
                print(f"   {output.agent_id}: {assessment['overall_score']}/10 ({assessment['grade']})")
            
            # 2. 冲突检测
            print("\n🔍 冲突检测...")
            conflicts = self.conflict_detector.detect_all_conflicts(current_outputs)
            if conflicts:
                print(f"   ⚠️  发现 {len(conflicts)} 个冲突")
            else:
                print("   ✅ 无冲突")
            
            # 3. 检查是否达标
            avg_quality = sum(a['overall_score'] for a in assessments) / len(assessments)
            print(f"\n📈 平均质量分: {avg_quality:.1f}/10")
            
            if avg_quality >= self.quality_threshold and not conflicts:
                print(f"\n✅ 质量达标！提前结束迭代")
                return self._create_final_result(
                    current_outputs, assessments, conflicts, round_num
                )
            
            if round_num == self.max_rounds:
                print(f"\n⏹️  达到最大迭代次数，结束")
                break
            
            # 4. 收集所有反馈
            print("\n💡 生成改进反馈...")
            all_feedbacks = []
            for assessment in assessments:
                all_feedbacks.extend(assessment['improvements'])
            
            print(f"   共 {len(all_feedbacks)} 条改进建议")
            for fb in all_feedbacks[:3]:  # 只显示前3条
                print(f"   • [{fb.priority.upper()}] {fb.description}")
            
            # 5. 执行改进
            print("\n🔧 执行改进...")
            improved_outputs = await self._apply_improvements(
                current_outputs, 
                all_feedbacks, 
                agent_factories
            )
            
            # 6. 记录本轮
            self.iteration_history.append(IterationRound(
                round_number=round_num,
                outputs=current_outputs,
                quality_scores={a['agent_id']: a['overall_score'] for a in assessments},
                conflicts=conflicts,
                feedbacks=all_feedbacks,
                improvements_made=[fb.description for fb in all_feedbacks]
            ))
            
            current_outputs = improved_outputs
        
        # 最终评估
        final_assessments = [self.assessment_agent.deep_assess(o) for o in current_outputs]
        final_conflicts = self.conflict_detector.detect_all_conflicts(current_outputs)
        
        return self._create_final_result(
            current_outputs, 
            final_assessments, 
            final_conflicts, 
            len(self.iteration_history) + 1
        )
    
    async def _apply_improvements(
        self,
        current_outputs: List[AgentOutput],
        feedbacks: List[ImprovementFeedback],
        agent_factories: Dict[str, Callable]
    ) -> List[AgentOutput]:
        """应用改进"""
        improved_outputs = []
        
        for output in current_outputs:
            # 找出针对该Agent的反馈
            agent_feedbacks = [f for f in feedbacks if f.target_agent == output.agent_type]
            
            if not agent_feedbacks:
                # 没有反馈，保持原样
                improved_outputs.append(output)
                continue
            
            # 模拟改进（实际应用中调用Agent重新生成）
            print(f"   改进 {output.agent_id}...")
            
            # 改进内容（模拟）
            improved_content = dict(output.content)
            improved_content['improved'] = True
            improved_content['improvement_round'] = improved_content.get('improvement_round', 0) + 1
            
            # 根据反馈类型添加内容
            for fb in agent_feedbacks:
                if fb.improvement_type == ImprovementType.ADD_DETAIL:
                    improved_content['additional_details'] = 'Added based on feedback'
                elif fb.improvement_type == ImprovementType.ADD_EXAMPLES:
                    improved_content['examples'] = ['Example 1', 'Example 2']
            
            improved_outputs.append(AgentOutput(
                agent_id=output.agent_id,
                agent_type=output.agent_type,
                content=improved_content
            ))
        
        return improved_outputs
    
    def _create_final_result(
        self,
        outputs: List[AgentOutput],
        assessments: List[Dict],
        conflicts: List[Conflict],
        total_rounds: int
    ) -> Dict[str, Any]:
        """创建最终结果"""
        return {
            "final_outputs": [
                {
                    "agent_id": o.agent_id,
                    "agent_type": o.agent_type,
                    "content": o.content
                }
                for o in outputs
            ],
            "final_quality": {
                "individual_scores": {a['agent_id']: a['overall_score'] for a in assessments},
                "average_score": sum(a['overall_score'] for a in assessments) / len(assessments),
                "detailed_assessments": assessments
            },
            "final_conflicts": [
                {
                    "type": c.conflict_type.value,
                    "severity": c.severity,
                    "description": c.description
                }
                for c in conflicts
            ],
            "iteration_summary": {
                "total_rounds": total_rounds,
                "max_rounds_reached": total_rounds >= self.max_rounds,
                "quality_improvement": self._calculate_improvement(),
                "iteration_history": [
                    {
                        "round": r.round_number,
                        "avg_quality": sum(r.quality_scores.values()) / len(r.quality_scores),
                        "conflicts": len(r.conflicts)
                    }
                    for r in self.iteration_history
                ]
            },
            "completion_time": datetime.now().isoformat()
        }
    
    def _calculate_improvement(self) -> float:
        """计算质量改进"""
        if len(self.iteration_history) < 2:
            return 0.0
        
        first_round = self.iteration_history[0]
        last_round = self.iteration_history[-1]
        
        first_avg = sum(first_round.quality_scores.values()) / len(first_round.quality_scores)
        last_avg = sum(last_round.quality_scores.values()) / len(last_round.quality_scores)
        
        return last_avg - first_avg


async def demo_p1_improvements():
    """演示P1级改进"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🎯 P1 IMPROVEMENTS - 深度质量评估 + 迭代改进循环                         ║
║                                                                          ║
║   1. 深度质量评估 (多维度评分)                                            ║
║   2. 迭代改进循环 (自动优化直到达标)                                        ║
║   3. 自动反馈机制 (针对性改进建议)                                          ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # 初始输出（质量较低，需要改进）
    initial_outputs = [
        AgentOutput(
            agent_id="research_agent",
            agent_type="ResearchSpecialist",
            content={
                "topic": "AI Agent Framework",
                "language": "Python",
                "summary": "Research completed"
                # 缺少：details, metadata, references
            }
        ),
        AgentOutput(
            agent_id="code_agent",
            agent_type="CodeSpecialist",
            content={
                "language": "Python",
                "file_path": "/tmp/main.py",
                "lines": 100
                # 缺少：examples, usage说明
            }
        ),
        AgentOutput(
            agent_id="doc_agent",
            agent_type="DocSpecialist",
            content={
                "title": "Documentation",
                "sections": ["Intro"]
                # 内容太少
            }
        )
    ]
    
    # 创建迭代改进编排器
    orchestrator = IterativeImprovementOrchestrator(
        max_rounds=3,
        quality_threshold=8.0
    )
    
    # 执行带迭代改进的工作流
    result = await orchestrator.execute_with_improvement(
        initial_outputs,
        agent_factories={}  # 简化演示，不实际重新生成
    )
    
    # 展示结果
    print("\n" + "="*70)
    print("📊 P1改进完成总结")
    print("="*70)
    
    print(f"\n🔄 迭代统计:")
    print(f"   总轮次: {result['iteration_summary']['total_rounds']}")
    print(f"   质量提升: +{result['iteration_summary']['quality_improvement']:.1f}分")
    
    print(f"\n📈 最终质量:")
    for agent, score in result['final_quality']['individual_scores'].items():
        print(f"   {agent}: {score}/10")
    print(f"   平均分: {result['final_quality']['average_score']:.1f}/10")
    
    print(f"\n📋 详细评估维度示例:")
    sample_assessment = result['final_quality']['detailed_assessments'][0]
    print(f"   Agent: {sample_assessment['agent_id']}")
    print(f"   总分: {sample_assessment['overall_score']}/10 ({sample_assessment['grade']})")
    print(f"   各维度:")
    for dim, score in sample_assessment['dimensions'].items():
        print(f"      {dim}: {score}/10")
    
    print(f"\n💡 改进建议示例:")
    for imp in sample_assessment['improvements'][:2]:
        print(f"   • [{imp.priority.upper()}] {imp.description}")
    
    print("\n" + "="*70)
    print("✅ P1改进完成！")
    print("="*70)
    print("\n改进亮点:")
    print("   1. ✅ 多维度深度质量评估 (5个维度)")
    print("   2. ✅ 自动迭代改进循环")
    print("   3. ✅ 针对性反馈生成")
    print("   4. ✅ 质量提升量化追踪")


if __name__ == "__main__":
    asyncio.run(demo_p1_improvements())
