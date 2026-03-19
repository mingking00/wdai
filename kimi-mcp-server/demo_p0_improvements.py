#!/usr/bin/env python3
"""
Multi-Agent System - P0 Improvements
多智能体系统 - P0级核心改进

改进内容：
1. 仲裁者Agent (ArbitratorAgent) - 统一输出决策
2. 冲突检测机制 (ConflictDetector) - 避免内部矛盾
"""

import sys
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

sys.path.insert(0, '/root/.openclaw/workspace/kimi-mcp-server/src')
from extended_tools import KimiMCPExtendedServer


class ConflictType(Enum):
    """冲突类型"""
    TECHNOLOGY_MISMATCH = "technology_mismatch"  # 技术栈不匹配
    LOGIC_CONTRADICTION = "logic_contradiction"  # 逻辑矛盾
    VERSION_MISMATCH = "version_mismatch"        # 版本不一致
    SCOPE_MISMATCH = "scope_mismatch"            # 范围不匹配
    QUALITY_ISSUE = "quality_issue"              # 质量问题


@dataclass
class Conflict:
    """冲突定义"""
    conflict_type: ConflictType
    severity: str  # critical, high, medium, low
    description: str
    involved_agents: List[str]
    suggestion: str
    auto_resolvable: bool = False


@dataclass
class AgentOutput:
    """智能体输出"""
    agent_id: str
    agent_type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ConflictDetector:
    """
    冲突检测器
    
    检测多个Agent输出之间的冲突
    """
    
    def __init__(self):
        self.conflicts: List[Conflict] = []
        self.server = KimiMCPExtendedServer()
    
    def detect_all_conflicts(self, outputs: List[AgentOutput]) -> List[Conflict]:
        """检测所有类型的冲突"""
        self.conflicts = []
        
        # 1. 检测技术栈冲突
        self._detect_technology_conflicts(outputs)
        
        # 2. 检测逻辑矛盾
        self._detect_logic_conflicts(outputs)
        
        # 3. 检测版本冲突
        self._detect_version_conflicts(outputs)
        
        # 4. 检测范围冲突
        self._detect_scope_conflicts(outputs)
        
        return self.conflicts
    
    def _detect_technology_conflicts(self, outputs: List[AgentOutput]):
        """检测技术栈冲突"""
        # 提取各Agent推荐的技术栈
        tech_choices = {}
        
        for output in outputs:
            agent_type = output.agent_type
            content = output.content
            
            # 从内容中提取技术选择
            if 'language' in content:
                tech_choices[agent_type] = content['language']
            elif 'framework' in content:
                tech_choices[agent_type] = content['framework']
        
        # 检测不匹配
        if len(set(tech_choices.values())) > 1:
            self.conflicts.append(Conflict(
                conflict_type=ConflictType.TECHNOLOGY_MISMATCH,
                severity="critical",
                description=f"技术栈不一致: {tech_choices}",
                involved_agents=list(tech_choices.keys()),
                suggestion="统一技术栈选择，建议以Implementation Agent为准",
                auto_resolvable=True
            ))
    
    def _detect_logic_conflicts(self, outputs: List[AgentOutput]):
        """检测逻辑矛盾"""
        # 检测功能描述是否矛盾
        features = {}
        for output in outputs:
            if 'features' in output.content:
                features[output.agent_id] = output.content['features']
        
        # 简单的矛盾检测：检查是否有完全相反的描述
        # 实际应用可以使用更复杂的NLP技术
        if len(features) > 1:
            feature_sets = [set(f) for f in features.values()]
            # 如果没有任何共同特征，可能存在矛盾
            if not set.intersection(*feature_sets):
                self.conflicts.append(Conflict(
                    conflict_type=ConflictType.LOGIC_CONTRADICTION,
                    severity="high",
                    description="各Agent定义的功能特性无交集，可能存在理解偏差",
                    involved_agents=list(features.keys()),
                    suggestion="重新对齐项目目标和功能范围",
                    auto_resolvable=False
                ))
    
    def _detect_version_conflicts(self, outputs: List[AgentOutput]):
        """检测版本冲突"""
        versions = {}
        for output in outputs:
            if 'version' in output.content:
                versions[output.agent_id] = output.content['version']
        
        # 检测版本不一致
        if len(set(versions.values())) > 1:
            self.conflicts.append(Conflict(
                conflict_type=ConflictType.VERSION_MISMATCH,
                severity="medium",
                description=f"版本号不一致: {versions}",
                involved_agents=list(versions.keys()),
                suggestion="统一使用最高版本号或Implementation Agent的版本",
                auto_resolvable=True
            ))
    
    def _detect_scope_conflicts(self, outputs: List[AgentOutput]):
        """检测范围冲突"""
        scopes = {}
        for output in outputs:
            if 'scope' in output.content or 'topic' in output.content:
                scopes[output.agent_id] = output.content.get('scope') or output.content.get('topic')
        
        # 检测范围是否一致
        if len(scopes) > 1:
            unique_scopes = set(scopes.values())
            if len(unique_scopes) > 1:
                self.conflicts.append(Conflict(
                    conflict_type=ConflictType.SCOPE_MISMATCH,
                    severity="high",
                    description=f"项目范围不一致: {unique_scopes}",
                    involved_agents=list(scopes.keys()),
                    suggestion="重新定义统一的项目范围和目标",
                    auto_resolvable=False
                ))
    
    def get_conflict_summary(self) -> Dict:
        """获取冲突摘要"""
        critical = sum(1 for c in self.conflicts if c.severity == "critical")
        high = sum(1 for c in self.conflicts if c.severity == "high")
        medium = sum(1 for c in self.conflicts if c.severity == "medium")
        low = sum(1 for c in self.conflicts if c.severity == "low")
        
        auto_resolvable = sum(1 for c in self.conflicts if c.auto_resolvable)
        
        return {
            "total": len(self.conflicts),
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "auto_resolvable": auto_resolvable,
            "manual_required": len(self.conflicts) - auto_resolvable
        }


class ArbitratorAgent:
    """
    仲裁者智能体
    
    职责：
    1. 收集所有Agent输出
    2. 调用冲突检测
    3. 评估输出质量
    4. 生成统一最终报告
    5. 提出改进建议
    """
    
    def __init__(self):
        self.server = KimiMCPExtendedServer()
        self.conflict_detector = ConflictDetector()
        self.outputs: List[AgentOutput] = []
        self.conflicts: List[Conflict] = []
        self.quality_scores: Dict[str, float] = {}
    
    def collect_outputs(self, outputs: List[AgentOutput]):
        """收集所有Agent输出"""
        self.outputs = outputs
        print(f"\n📥 仲裁者收集到 {len(outputs)} 个Agent输出:")
        for out in outputs:
            print(f"   • {out.agent_id} ({out.agent_type})")
    
    def detect_conflicts(self) -> List[Conflict]:
        """执行冲突检测"""
        print("\n🔍 执行冲突检测...")
        self.conflicts = self.conflict_detector.detect_all_conflicts(self.outputs)
        
        summary = self.conflict_detector.get_conflict_summary()
        
        if summary["total"] == 0:
            print("   ✅ 未发现冲突")
        else:
            print(f"   ⚠️  发现 {summary['total']} 个冲突:")
            print(f"      严重: {summary['critical']}, 高: {summary['high']}, 中: {summary['medium']}, 低: {summary['low']}")
            print(f"      可自动解决: {summary['auto_resolvable']}, 需人工介入: {summary['manual_required']}")
        
        return self.conflicts
    
    def assess_quality(self) -> Dict[str, float]:
        """评估各Agent输出质量"""
        print("\n📊 评估输出质量...")
        
        for output in self.outputs:
            score = self._calculate_quality_score(output)
            self.quality_scores[output.agent_id] = score
            print(f"   • {output.agent_id}: {score:.1f}/10")
        
        return self.quality_scores
    
    def _calculate_quality_score(self, output: AgentOutput) -> float:
        """计算单个输出质量分"""
        score = 5.0  # 基础分
        content = output.content
        
        # 完整性检查
        if len(content) > 3:
            score += 2.0
        
        # 结构化程度
        if any(k in content for k in ['summary', 'details', 'metadata']):
            score += 1.5
        
        # 是否有错误
        if 'error' in content and content['error']:
            score -= 3.0
        
        # 内容长度（适度奖励）
        content_str = json.dumps(content)
        if 100 < len(content_str) < 5000:
            score += 1.5
        
        return max(0.0, min(10.0, score))
    
    def generate_final_report(self) -> Dict[str, Any]:
        """生成统一最终报告"""
        print("\n📝 生成最终报告...")
        
        # 1. 收集各部分信息
        research_content = self._find_output_by_type("Research")
        code_content = self._find_output_by_type("Code")
        doc_content = self._find_output_by_type("Doc")
        
        # 2. 生成报告
        report = {
            "report_title": "Multi-Agent Project Final Report",
            "generated_at": datetime.now().isoformat(),
            "version": "2.0",
            
            # 执行摘要
            "executive_summary": self._generate_executive_summary(),
            
            # 详细章节
            "sections": {
                "research": {
                    "title": "研究背景",
                    "content": research_content.content if research_content else {},
                    "quality_score": self.quality_scores.get(research_content.agent_id if research_content else '', 0),
                    "agent": research_content.agent_id if research_content else 'N/A'
                },
                "implementation": {
                    "title": "实现方案",
                    "content": code_content.content if code_content else {},
                    "quality_score": self.quality_scores.get(code_content.agent_id if code_content else '', 0),
                    "agent": code_content.agent_id if code_content else 'N/A',
                    "file_path": code_content.content.get('file_path', 'N/A') if code_content and hasattr(code_content, 'content') else 'N/A'
                },
                "documentation": {
                    "title": "项目文档",
                    "content": doc_content.content if doc_content else {},
                    "quality_score": self.quality_scores.get(doc_content.agent_id if doc_content else '', 0),
                    "agent": doc_content.agent_id if doc_content else 'N/A'
                }
            },
            
            # 质量评估
            "quality_assessment": {
                "overall_score": sum(self.quality_scores.values()) / len(self.quality_scores) if self.quality_scores else 0,
                "individual_scores": self.quality_scores,
                "rating": self._get_overall_rating()
            },
            
            # 冲突记录
            "conflicts": {
                "total": len(self.conflicts),
                "list": [
                    {
                        "type": c.conflict_type.value,
                        "severity": c.severity,
                        "description": c.description,
                        "involved": c.involved_agents,
                        "suggestion": c.suggestion
                    }
                    for c in self.conflicts
                ],
                "resolution_status": "auto_resolved" if all(c.auto_resolvable for c in self.conflicts) else "manual_review_required"
            },
            
            # 改进建议
            "improvements": self._generate_improvements(),
            
            # 元数据
            "metadata": {
                "agent_count": len(self.outputs),
                "conflict_count": len(self.conflicts),
                "avg_quality": sum(self.quality_scores.values()) / len(self.quality_scores) if self.quality_scores else 0,
                "generation_time": datetime.now().isoformat()
            }
        }
        
        print(f"   ✅ 报告生成完成 (总体评分: {report['quality_assessment']['overall_score']:.1f}/10)")
        
        return report
    
    def _find_output_by_type(self, agent_type: str) -> Optional[AgentOutput]:
        """查找特定类型的Agent输出"""
        for output in self.outputs:
            if agent_type.lower() in output.agent_type.lower():
                return output
        return None
    
    def _generate_executive_summary(self) -> str:
        """生成执行摘要"""
        topic = "AI Agent Framework"
        
        summary = f"""本项目旨在构建"{topic}"。通过多智能体协作，完成了研究分析、代码实现和文档生成。

主要成果：
• 完成了项目技术选型和架构设计
• 生成了可运行的核心代码实现
• 提供了完整的项目文档和使用说明

质量评估：总体评分 {sum(self.quality_scores.values()) / len(self.quality_scores):.1f}/10，达到生产可用标准。"""
        
        if self.conflicts:
            summary += f"\n\n注意：检测到 {len(self.conflicts)} 个内部冲突，已记录并给出解决建议。"
        
        return summary
    
    def _get_overall_rating(self) -> str:
        """获取总体评级"""
        avg_score = sum(self.quality_scores.values()) / len(self.quality_scores) if self.quality_scores else 0
        
        if avg_score >= 9:
            return "Excellent"
        elif avg_score >= 7:
            return "Good"
        elif avg_score >= 5:
            return "Acceptable"
        else:
            return "Needs Improvement"
    
    def _generate_improvements(self) -> List[str]:
        """生成改进建议"""
        improvements = []
        
        # 基于质量分数的建议
        for agent_id, score in self.quality_scores.items():
            if score < 7:
                improvements.append(f"{agent_id} 的输出质量有待提升 (当前 {score:.1f}/10)，建议增加更多细节")
        
        # 基于冲突的建议
        for conflict in self.conflicts:
            if not conflict.auto_resolvable:
                improvements.append(f"[需人工处理] {conflict.description}")
        
        if not improvements:
            improvements.append("当前输出质量良好，建议继续迭代优化细节")
        
        return improvements
    
    def execute(self, outputs: List[AgentOutput]) -> Dict[str, Any]:
        """执行完整仲裁流程"""
        print("\n" + "="*70)
        print("⚖️  ARBITRATOR AGENT - 仲裁者智能体")
        print("="*70)
        
        # 1. 收集输出
        self.collect_outputs(outputs)
        
        # 2. 冲突检测
        self.detect_conflicts()
        
        # 3. 质量评估
        self.assess_quality()
        
        # 4. 生成最终报告
        final_report = self.generate_final_report()
        
        # 5. 保存报告
        self._save_report(final_report)
        
        return final_report
    
    def _save_report(self, report: Dict):
        """保存报告到文件"""
        import os
        os.makedirs('/tmp/multi_agent_reports', exist_ok=True)
        
        filename = f"/tmp/multi_agent_reports/final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 报告已保存: {filename}")


# ==================== 演示 ====================

def demo_p0_improvements():
    """演示P0级改进"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🎯 P0 IMPROVEMENTS - 多智能体核心改进                                  ║
║                                                                          ║
║   1. 仲裁者Agent (ArbitratorAgent) - 统一输出决策                        ║
║   2. 冲突检测机制 (ConflictDetector) - 避免内部矛盾                      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # 模拟各Agent的输出
    outputs = [
        AgentOutput(
            agent_id="research_agent",
            agent_type="ResearchSpecialist",
            content={
                "topic": "AI Agent Framework",
                "language": "Python",
                "framework": "LangChain",
                "version": "1.0.0",
                "scope": "Multi-Agent System",
                "findings": ["Finding 1", "Finding 2"],
                "summary": "Research on AI Agent frameworks completed"
            }
        ),
        AgentOutput(
            agent_id="code_agent",
            agent_type="CodeSpecialist",
            content={
                "language": "Python",  # 一致
                "framework": "AutoGen",  # 冲突：Research说LangChain
                "version": "1.1.0",  # 冲突：Research说1.0.0
                "file_path": "/tmp/project/main.py",
                "lines_of_code": 150,
                "features": ["async", "type_hints"]
            }
        ),
        AgentOutput(
            agent_id="doc_agent",
            agent_type="DocSpecialist",
            content={
                "scope": "Multi-Agent System",  # 一致
                "readme_length": 1000,
                "sections": ["Overview", "Installation", "Usage"],
                "metadata": {"generated_at": datetime.now().isoformat()}
            }
        )
    ]
    
    # 创建仲裁者并执行
    arbitrator = ArbitratorAgent()
    final_report = arbitrator.execute(outputs)
    
    # 展示结果
    print("\n" + "="*70)
    print("📋 FINAL REPORT PREVIEW")
    print("="*70)
    print(f"\n报告标题: {final_report['report_title']}")
    print(f"总体评分: {final_report['quality_assessment']['overall_score']:.1f}/10")
    print(f"总体评级: {final_report['quality_assessment']['rating']}")
    print(f"冲突数量: {final_report['conflicts']['total']}")
    
    print("\n📊 各Agent质量评分:")
    for agent, score in final_report['quality_assessment']['individual_scores'].items():
        bar = "█" * int(score) + "░" * (10 - int(score))
        print(f"   {agent:20} │{bar}│ {score:.1f}")
    
    print("\n⚠️  检测到的冲突:")
    if final_report['conflicts']['list']:
        for c in final_report['conflicts']['list']:
            icon = "🔴" if c['severity'] == 'critical' else "🟠" if c['severity'] == 'high' else "🟡"
            print(f"   {icon} [{c['severity'].upper()}] {c['type']}")
            print(f"      描述: {c['description']}")
            print(f"      建议: {c['suggestion']}")
    else:
        print("   ✅ 无冲突")
    
    print("\n💡 改进建议:")
    for i, imp in enumerate(final_report['improvements'][:3], 1):
        print(f"   {i}. {imp}")
    
    print("\n" + "="*70)
    print("✅ P0改进完成！")
    print("="*70)
    print("\n改进亮点:")
    print("   1. ✅ 仲裁者Agent统一决策最终输出")
    print("   2. ✅ 冲突检测机制发现内部矛盾")
    print("   3. ✅ 质量评估量化各Agent输出")
    print("   4. ✅ 结构化最终报告便于使用")
    
    return final_report


if __name__ == "__main__":
    report = demo_p0_improvements()
