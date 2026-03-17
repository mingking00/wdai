#!/usr/bin/env python3
"""
Multi-Model Validator - 多模型交叉验证系统
借鉴 ccg-workflow 的多模型协作思想
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sys

# 添加 workspace 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

@dataclass
class ValidationResult:
    """验证结果"""
    model: str
    decision: str
    approval: bool
    confidence: int  # 1-10
    concerns: List[str]
    suggestions: List[str]

@dataclass
class ConsensusReport:
    """共识报告"""
    decision: str
    consensus_level: str  # full / partial / none
    approval_rate: float
    avg_confidence: float
    common_concerns: List[str]
    divergence_points: List[Dict]
    recommendations: List[str]

class MultiModelValidator:
    """多模型验证器"""
    
    def __init__(self):
        # 定义可用的模型及其特点
        self.models = {
            "k2p5": {
                "name": "Kimi K2.5",
                "strengths": ["代码生成", "长上下文", "逻辑推理"],
                "agent_id": "main"
            },
            # 未来可扩展更多模型
            # "claude-3-5": {"name": "Claude 3.5", "strengths": ["分析", "架构"], ...},
            # "gemini-2": {"name": "Gemini 2.0", "strengths": ["多模态", "检索"], ...},
        }
    
    async def validate(self, decision: str, decision_type: str = "general") -> ConsensusReport:
        """
        多模型验证决策
        
        Args:
            decision: 需要验证的决策描述
            decision_type: 决策类型 (architecture / implementation / security / general)
        
        Returns:
            ConsensusReport: 共识报告
        """
        print(f"🔍 启动多模型验证: {decision[:50]}...")
        
        # 收集各模型验证结果
        results = []
        for model_id, model_info in self.models.items():
            result = await self._validate_with_model(decision, model_id, decision_type)
            results.append(result)
            print(f"  ✅ {model_info['name']}: {'通过' if result.approval else '不通过'} (置信度{result.confidence}/10)")
        
        # 分析共识
        report = self._analyze_consensus(decision, results)
        
        return report
    
    async def _validate_with_model(self, decision: str, model_id: str, decision_type: str) -> ValidationResult:
        """使用指定模型验证"""
        model_info = self.models[model_id]
        
        # 构建验证提示词
        prompt = self._build_validation_prompt(decision, decision_type, model_info)
        
        # 实际环境中应调用 sessions_spawn 或类似机制
        # 这里先模拟结果
        # TODO: 实现真正的多模型调用
        
        # 模拟验证结果（实际应调用模型）
        return ValidationResult(
            model=model_info['name'],
            decision=decision,
            approval=True,  # 模拟
            confidence=8,
            concerns=[],
            suggestions=["考虑边界情况"]
        )
    
    def _build_validation_prompt(self, decision: str, decision_type: str, model_info: Dict) -> str:
        """构建验证提示词"""
        prompts = {
            "architecture": f"""作为架构审查专家，请评估以下架构决策：

决策：{decision}

请从以下维度评估：
1. 可扩展性 - 能否支撑未来增长？
2. 可维护性 - 代码是否易于理解和修改？
3. 性能影响 - 是否存在明显性能瓶颈？
4. 安全考虑 - 是否有安全隐患？
5. 复杂度 - 是否过度设计或过于简单？

输出格式：
- 是否通过：[是/否]
- 置信度：[1-10]
- 关注点：[列出具体问题]
- 建议：[改进建议]""",

            "security": f"""作为安全审查专家，请评估以下决策的安全风险：

决策：{decision}

请检查：
1. 输入验证是否充分
2. 认证授权是否完善
3. 敏感数据处理方式
4. 常见攻击向量防护

输出格式同上。""",

            "implementation": f"""作为代码实现审查专家，请评估以下实现方案：

决策：{decision}

请评估：
1. 代码质量
2. 错误处理
3. 测试覆盖
4. 性能优化

输出格式同上。""",

            "general": f"""作为技术决策审查专家，请评估以下决策：

决策：{decision}

请综合评估其合理性、可行性和潜在风险。

输出格式同上。"""
        }
        
        return prompts.get(decision_type, prompts["general"])
    
    def _analyze_consensus(self, decision: str, results: List[ValidationResult]) -> ConsensusReport:
        """分析共识"""
        if not results:
            return ConsensusReport(
                decision=decision,
                consensus_level="none",
                approval_rate=0,
                avg_confidence=0,
                common_concerns=[],
                divergence_points=[],
                recommendations=["无法获取验证结果"]
            )
        
        # 统计
        approvals = sum(1 for r in results if r.approval)
        approval_rate = approvals / len(results)
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        # 收集所有关注点
        all_concerns = []
        for r in results:
            all_concerns.extend(r.concerns)
        
        # 统计常见关注点（出现次数 > 1）
        concern_counts = {}
        for c in all_concerns:
            concern_counts[c] = concern_counts.get(c, 0) + 1
        common_concerns = [c for c, count in concern_counts.items() if count > 1]
        
        # 识别分歧点
        divergence_points = []
        if approval_rate > 0 and approval_rate < 1:
            divergence_points.append({
                "type": "approval分歧",
                "description": f"{approvals}/{len(results)} 模型通过",
                "severity": "high" if approval_rate < 0.5 else "medium"
            })
        
        # 置信度分歧
        confidences = [r.confidence for r in results]
        if max(confidences) - min(confidences) >= 3:
            divergence_points.append({
                "type": "confidence分歧",
                "description": f"置信度差异: {min(confidences)}-{max(confidences)}",
                "severity": "medium"
            })
        
        # 确定共识级别
        if approval_rate == 1 and avg_confidence >= 7:
            consensus_level = "full"
        elif approval_rate >= 0.5:
            consensus_level = "partial"
        else:
            consensus_level = "none"
        
        # 生成建议
        recommendations = []
        if consensus_level == "full":
            recommendations.append("✅ 全票通过，可以执行")
        elif consensus_level == "partial":
            recommendations.append("⚠️ 部分通过，建议人工审查分歧点")
        else:
            recommendations.append("❌ 未通过，需要重新设计")
        
        if common_concerns:
            recommendations.append(f"关注共同指出的问题: {', '.join(common_concerns[:3])}")
        
        return ConsensusReport(
            decision=decision,
            consensus_level=consensus_level,
            approval_rate=approval_rate,
            avg_confidence=avg_confidence,
            common_concerns=common_concerns,
            divergence_points=divergence_points,
            recommendations=recommendations
        )
    
    def format_report(self, report: ConsensusReport) -> str:
        """格式化报告"""
        consensus_emoji = {
            "full": "✅",
            "partial": "⚠️",
            "none": "❌"
        }
        
        lines = [
            f"## 多模型验证报告",
            f"",
            f"**决策**: {report.decision[:100]}...",
            f"**共识级别**: {consensus_emoji.get(report.consensus_level, '?')} {report.consensus_level}",
            f"**通过率**: {report.approval_rate*100:.0f}%",
            f"**平均置信度**: {report.avg_confidence:.1f}/10",
            f"",
            f"### 建议",
        ]
        
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        
        if report.common_concerns:
            lines.extend([
                f"",
                f"### 共同关注点",
            ])
            for c in report.common_concerns:
                lines.append(f"- {c}")
        
        if report.divergence_points:
            lines.extend([
                f"",
                f"### 分歧点",
            ])
            for d in report.divergence_points:
                lines.append(f"- [{d['severity']}] {d['type']}: {d['description']}")
        
        return "\n".join(lines)

# 便捷函数
async def validate_decision(decision: str, decision_type: str = "general") -> ConsensusReport:
    """快速验证决策"""
    validator = MultiModelValidator()
    return await validator.validate(decision, decision_type)

if __name__ == "__main__":
    async def test():
        validator = MultiModelValidator()
        
        # 测试验证
        report = await validator.validate(
            "使用 Redis 作为会话存储，JWT 作为认证令牌",
            "architecture"
        )
        
        print(validator.format_report(report))
    
    asyncio.run(test())
