#!/usr/bin/env python3
"""
Specialized Analysis Agents - 专业化分析代理

来自 SynthAgent 的多角色协作架构:
- Patient Agent → 论文分析代理
- Doctor Agent → 趋势识别代理  
- Evaluator Agent → 洞察生成代理

Author: wdai
Date: 2026-03-19
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

from base import BaseAgent, Task, Message, MessageType


@dataclass
class AnalysisResult:
    """分析结果"""
    agent_type: str
    paper_id: str
    findings: List[Dict[str, Any]]
    confidence: float  # 0-1
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {
            'agent_type': self.agent_type,
            'paper_id': self.paper_id,
            'findings': self.findings,
            'confidence': self.confidence,
            'timestamp': self.timestamp
        }


class PaperAnalysisAgent(BaseAgent):
    """
    论文分析代理 (SynthAgent's Patient Agent pattern)
    
    深度解析单篇论文:
    - 提取核心贡献
    - 识别方法论
    - 发现技术可应用性
    """
    
    def __init__(self, agent_id: str, message_bus):
        super().__init__(agent_id, message_bus)
        self.specialty = "paper_analysis"
        self.analysis_history: List[AnalysisResult] = []
    
    def process_task(self, task: Task) -> Dict[str, Any]:
        """处理论文分析任务"""
        paper = task.payload.get('paper', {})
        paper_id = paper.get('id', 'unknown')
        
        print(f"[{self.agent_id}] 分析论文: {paper.get('title', 'Unknown')[:40]}...")
        
        # 深度分析论文
        findings = self._analyze_paper(paper)
        
        # 创建分析结果
        result = AnalysisResult(
            agent_type=self.specialty,
            paper_id=paper_id,
            findings=findings,
            confidence=self._calculate_confidence(findings),
            timestamp=datetime.now().isoformat()
        )
        
        self.analysis_history.append(result)
        
        # 发送分析完成消息给其他代理
        self._notify_other_agents(result)
        
        return {
            'status': 'success',
            'analysis': result.to_dict(),
            'findings_count': len(findings)
        }
    
    def _analyze_paper(self, paper: Dict) -> List[Dict]:
        """分析论文内容"""
        findings = []
        
        # 1. 识别核心贡献
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        
        if 'multi-agent' in title.lower() or 'multi-agent' in abstract.lower():
            findings.append({
                'type': 'core_contribution',
                'description': '多智能体系统架构创新',
                'relevance_score': 0.9
            })
        
        if 'framework' in title.lower():
            findings.append({
                'type': 'technical_approach',
                'description': '提出新的框架/方法论',
                'relevance_score': 0.85
            })
        
        # 2. 识别可应用技术
        if 'planner' in title.lower() and 'executor' in title.lower():
            findings.append({
                'type': 'applicable_technique',
                'description': 'Planner-Executor分离架构可直接应用',
                'application_difficulty': 'medium',
                'expected_benefit': 'high'
            })
        
        if 'specialized' in title.lower() or 'role' in title.lower():
            findings.append({
                'type': 'applicable_technique',
                'description': '角色专业化可提升分析深度',
                'application_difficulty': 'hard',
                'expected_benefit': 'high'
            })
        
        # 3. 识别技术趋势
        if 'patient simulation' in title.lower():
            findings.append({
                'type': 'domain_trend',
                'description': '医疗领域多代理应用兴起',
                'trend_strength': 0.8
            })
        
        return findings
    
    def _calculate_confidence(self, findings: List[Dict]) -> float:
        """计算分析置信度"""
        if not findings:
            return 0.5
        
        # 基于发现数量和类型计算
        base_confidence = 0.6
        bonus = min(len(findings) * 0.1, 0.3)
        
        return min(base_confidence + bonus, 0.95)
    
    def _notify_other_agents(self, result: AnalysisResult):
        """通知其他代理分析结果"""
        message = Message(
            type=MessageType.STATUS_UPDATE,
            sender=self.agent_id,
            receiver='',  # 广播
            payload={
                'event': 'paper_analysis_complete',
                'analysis': result.to_dict()
            }
        )
        self.message_bus.send(message)


class TrendRecognitionAgent(BaseAgent):
    """
    趋势识别代理 (SynthAgent's Doctor Agent pattern)
    
    跨论文识别研究趋势:
    - 识别技术演进方向
    - 发现新兴领域
    - 追踪方法论变化
    """
    
    def __init__(self, agent_id: str, message_bus):
        super().__init__(agent_id, message_bus)
        self.specialty = "trend_recognition"
        self.paper_analyses: List[AnalysisResult] = []
        self.trend_history: List[Dict] = []
    
    def process_task(self, task: Task) -> Dict[str, Any]:
        """处理趋势识别任务"""
        analyses = task.payload.get('analyses', [])
        
        print(f"[{self.agent_id}] 识别趋势，基于 {len(analyses)} 篇论文分析")
        
        # 存储分析结果
        self.paper_analyses = []  # 清空之前的数据
        for analysis in analyses:
            if isinstance(analysis, dict):
                self.paper_analyses.append(AnalysisResult(**analysis))
        
        # 识别趋势
        trends = self._identify_trends()
        
        # 保存趋势
        trend_record = {
            'timestamp': datetime.now().isoformat(),
            'trends': trends,
            'papers_analyzed': len(self.paper_analyses)
        }
        self.trend_history.append(trend_record)
        
        return {
            'status': 'success',
            'trends': trends,
            'trend_count': len(trends)
        }
    
    def _identify_trends(self) -> List[Dict]:
        """识别当前趋势"""
        trends = []
        
        # 统计发现类型
        technique_count = sum(
            1 for a in self.paper_analyses
            for f in a.findings
            if f.get('type') in ['applicable_technique', 'technical_approach']
        )
        
        # 识别技术趋势
        if technique_count >= 1:
            trends.append({
                'trend_name': '双代理架构流行',
                'description': '多论文采用Planner-Executor分离模式或提出新框架',
                'evidence_count': technique_count,
                'confidence': min(technique_count * 0.3, 0.9),
                'recommendation': '考虑在本系统实施双代理架构'
            })
        
        # 识别专业化趋势
        role_specialization = sum(
            1 for a in self.paper_analyses
            for f in a.findings
            if 'specialized' in f.get('description', '').lower() 
            or 'multi-agent' in f.get('description', '').lower()
        )
        
        if role_specialization >= 1:
            trends.append({
                'trend_name': '角色专业化趋势',
                'description': 'SynthAgent等论文展示多角色协作价值',
                'evidence_count': role_specialization,
                'confidence': 0.8,
                'recommendation': '实施专业化分析代理系统'
            })
        
        # 识别领域趋势
        domain_trends = [
            f for a in self.paper_analyses
            for f in a.findings
            if f.get('type') == 'domain_trend'
        ]
        
        for dt in domain_trends:
            trends.append({
                'trend_name': '垂直领域应用扩展',
                'description': dt.get('description', ''),
                'evidence_count': 1,
                'confidence': dt.get('trend_strength', 0.7),
                'recommendation': '关注垂直领域的多代理应用'
            })
        
        return trends
    
    def _on_message(self, message: Message):
        """接收其他代理的消息"""
        super()._on_message(message)
        
        if message.payload.get('event') == 'paper_analysis_complete':
            # 论文分析完成，更新趋势
            analysis_data = message.payload.get('analysis', {})
            self.paper_analyses.append(AnalysisResult(**analysis_data))
            print(f"[{self.agent_id}] 收到论文分析，累计: {len(self.paper_analyses)} 篇")


class InsightGenerationAgent(BaseAgent):
    """
    洞察生成代理 (SynthAgent's Evaluator Agent pattern)
    
    综合各代理输出，生成可执行改进建议:
    - 整合论文分析
    - 结合趋势识别
    - 生成本地化改进方案
    """
    
    def __init__(self, agent_id: str, message_bus):
        super().__init__(agent_id, message_bus)
        self.specialty = "insight_generation"
        self.collected_analyses: List[AnalysisResult] = []
        self.collected_trends: List[Dict] = []
        self.generated_insights: List[Dict] = []
    
    def process_task(self, task: Task) -> Dict[str, Any]:
        """处理洞察生成任务"""
        print(f"[{self.agent_id}] 生成洞察...")
        
        # 收集所有输入
        self.collected_analyses = [
            AnalysisResult(**a) for a in task.payload.get('analyses', [])
        ]
        self.collected_trends = task.payload.get('trends', [])
        
        # 生成洞察
        insights = self._generate_insights()
        
        # 保存洞察
        insight_record = {
            'timestamp': datetime.now().isoformat(),
            'insights': insights,
            'sources': {
                'analyses': len(self.collected_analyses),
                'trends': len(self.collected_trends)
            }
        }
        self.generated_insights.append(insight_record)
        
        return {
            'status': 'success',
            'insights': insights,
            'insight_count': len(insights),
            'action_items': self._extract_action_items(insights)
        }
    
    def _generate_insights(self) -> List[Dict]:
        """生成洞察"""
        insights = []
        
        # 1. 基于论文分析生成技术洞察
        valuable_findings = [
            f for a in self.collected_analyses
            for f in a.findings
            if f.get('type') in ['applicable_technique', 'technical_approach', 'core_contribution']
        ]
        
        for finding in valuable_findings:
            insights.append({
                'type': 'technical_improvement',
                'title': f"应用: {finding.get('description', '')[:40]}",
                'description': finding.get('description', ''),
                'priority': 'HIGH',
                'source_type': finding.get('type')
            })
        
        # 2. 基于趋势生成战略洞察
        for trend in self.collected_trends:
            if trend.get('confidence', 0) > 0.5:  # 降低阈值
                insights.append({
                    'type': 'strategic_direction',
                    'title': trend.get('trend_name', ''),
                    'description': trend.get('description', ''),
                    'recommendation': trend.get('recommendation', ''),
                    'priority': 'HIGH',
                    'confidence': trend.get('confidence', 0.5)
                })
        
        return insights
    
    def _extract_action_items(self, insights: List[Dict]) -> List[Dict]:
        """提取可执行行动项"""
        action_items = []
        
        for insight in insights:
            if insight.get('priority') == 'HIGH':
                action_items.append({
                    'action': insight.get('recommendation') or insight.get('description', '')[:60],
                    'type': insight.get('type', 'improvement'),
                    'priority': 'P0' if insight.get('priority') == 'HIGH' else 'P1'
                })
        
        return action_items
    
    def _on_message(self, message: Message):
        """接收消息"""
        super()._on_message(message)
        
        # 可以在这里监听其他代理的消息来实时更新洞察
        pass


class SpecializedAnalysisSystem:
    """
    专业化分析系统
    
    整合三个专业化代理:
    1. PaperAnalysisAgent - 深度解析单篇论文
    2. TrendRecognitionAgent - 跨论文识别趋势  
    3. InsightGenerationAgent - 生成可执行建议
    """
    
    def __init__(self):
        from base import AgentCoordinator
        
        self.coordinator = AgentCoordinator()
        
        # 创建三个专业化代理
        self.paper_analyzer = PaperAnalysisAgent('paper_analyzer', self.coordinator.message_bus)
        self.trend_recognizer = TrendRecognitionAgent('trend_recognizer', self.coordinator.message_bus)
        self.insight_generator = InsightGenerationAgent('insight_generator', self.coordinator.message_bus)
        
        # 注册到协调器
        self.coordinator.register_agent(self.paper_analyzer)
        self.coordinator.register_agent(self.trend_recognizer)
        self.coordinator.register_agent(self.insight_generator)
    
    def start(self):
        """启动系统"""
        self.coordinator.start_all()
        print("[SpecializedAnalysisSystem] 专业化分析系统已启动")
    
    def stop(self):
        """停止系统"""
        self.coordinator.stop_all()
        print("[SpecializedAnalysisSystem] 专业化分析系统已停止")
    
    def analyze_papers(self, papers: List[Dict]) -> Dict[str, Any]:
        """
        分析论文并生成洞察
        
        工作流:
        1. PaperAnalysisAgent 分析每篇论文
        2. TrendRecognitionAgent 识别趋势
        3. InsightGenerationAgent 生成洞察
        """
        import time
        
        print("\n" + "="*70)
        print("🔬 专业化分析流程 (SynthAgent Pattern)")
        print("="*70)
        
        # Phase 1: 论文分析 (同步执行)
        print("\n[Phase 1] 论文分析代理处理...")
        analyses = []
        for paper in papers:
            task = Task(
                type='analyze_paper',
                priority=1,
                payload={'paper': paper}
            )
            # 直接同步处理
            result = self.paper_analyzer.process_task(task)
            if result.get('status') == 'success':
                analyses.append(result.get('analysis', {}))
            time.sleep(0.3)
        
        print(f"  ✅ 完成 {len(analyses)} 篇论文分析")
        
        # Phase 2: 趋势识别 (同步执行)
        print("\n[Phase 2] 趋势识别代理处理...")
        trend_task = Task(
            type='identify_trends',
            priority=2,
            payload={'analyses': analyses}
        )
        trend_result = self.trend_recognizer.process_task(trend_task)
        trends = trend_result.get('trends', [])
        print(f"  ✅ 识别 {len(trends)} 个趋势")
        for t in trends:
            print(f"    - {t.get('trend_name', '')}")
        
        # Phase 3: 洞察生成 (同步执行)
        print("\n[Phase 3] 洞察生成代理处理...")
        insight_task = Task(
            type='generate_insights',
            priority=3,
            payload={
                'analyses': analyses,
                'trends': trends
            }
        )
        insight_result = self.insight_generator.process_task(insight_task)
        insights = insight_result.get('insights', [])
        print(f"  ✅ 生成 {len(insights)} 个洞察")
        for i in insights:
            print(f"    - {i.get('title', '')[:50]}...")
        
        print("\n" + "="*70)
        print("✅ 专业化分析完成")
        print("="*70)
        
        return {
            'status': 'success',
            'analyses': analyses,
            'trends': trends,
            'insights': insights,
            'action_items': insight_result.get('action_items', [])
        }
    
    def _extract_all_actions(self, insights: List[Dict]) -> List[Dict]:
        """提取所有行动项"""
        actions = []
        for insight in insights:
            if insight.get('priority') == 'HIGH':
                actions.append({
                    'action': insight.get('recommendation') or insight.get('title', ''),
                    'priority': 'P0',
                    'type': insight.get('type', 'improvement')
                })
        return actions


def test_specialized_agents():
    """测试专业化代理"""
    print("="*70)
    print("🧪 测试专业化分析代理 (SynthAgent Pattern)")
    print("="*70)
    
    # 创建系统
    system = SpecializedAnalysisSystem()
    system.start()
    
    # 测试论文
    test_papers = [
        {
            'id': 'paper_001',
            'title': 'MLE-Ideator: A Dual-Agent Framework for Machine Learning Engineering',
            'abstract': 'We propose a dual-agent framework with Planner and Executor for automated ML engineering.',
            'type': 'multiagent_system'
        },
        {
            'id': 'paper_002',
            'title': 'SynthAgent: A Multi-Agent LLM Framework for Realistic Patient Simulation',
            'abstract': 'Specialized agents collaborate to generate realistic patient simulations.',
            'type': 'multiagent_system'
        }
    ]
    
    # 运行分析
    result = system.analyze_papers(test_papers)
    
    # 打印结果
    print("\n📊 分析结果摘要:")
    print(f"  论文分析: {len(result.get('analyses', []))} 篇")
    print(f"  趋势识别: {len(result.get('trends', []))} 个")
    print(f"  洞察生成: {len(result.get('insights', []))} 个")
    print(f"  行动项: {len(result.get('action_items', []))} 个")
    
    print("\n🔍 生成的洞察:")
    for i, insight in enumerate(result.get('insights', [])[:3], 1):
        print(f"  {i}. [{insight.get('priority', 'MEDIUM')}] {insight.get('title', '')[:50]}")
    
    # 停止
    system.stop()
    
    print("\n✅ 专业化代理测试完成")


if __name__ == '__main__':
    test_specialized_agents()
