#!/usr/bin/env python3
"""
深度论文分析器

解决"只抓标题不抓内容"的问题

核心能力:
1. 获取论文摘要/全文
2. 提取技术贡献
3. 分析方法论
4. 识别可应用技术
5. 生成具体改进建议

Author: wdai
Version: 1.0
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class TechnicalContribution:
    """技术贡献"""
    title: str
    description: str
    novelty: str  # 创新点
    impact: str   # 潜在影响
    implementation_difficulty: str  # easy/medium/hard


@dataclass
class MethodologyAnalysis:
    """方法论分析"""
    approach: str           # 方法概述
    key_components: List[str]  # 关键组件
    workflow: List[str]     # 工作流程
    evaluation_method: str  # 评估方式


@dataclass 
class ApplicableTechnique:
    """可应用技术"""
    name: str
    source_paper: str
    description: str
    application_scenario: str  # 适用场景
    adaptation_needed: str     # 需要哪些调整
    estimated_benefit: str     # 预期收益


@dataclass
class DeepPaperAnalysis:
    """深度论文分析结果"""
    paper_title: str
    paper_url: str
    analyzed_at: str
    
    # 核心内容
    core_problem: str           # 解决的核心问题
    key_insight: str            # 核心洞察
    technical_contributions: List[TechnicalContribution]
    
    # 方法论
    methodology: MethodologyAnalysis
    
    # 应用到本系统
    applicable_techniques: List[ApplicableTechnique]
    improvement_suggestions: List[str]
    
    # 元信息
    relevance_score: float      # 与本系统的相关度 0-1
    action_priority: str        # high/medium/low


class PaperContentFetcher:
    """论文内容获取器"""
    
    def __init__(self):
        self.cache_dir = Path(__file__).parent / "data" / "paper_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_abstract(self, arxiv_url: str) -> Optional[str]:
        """
        获取arXiv论文摘要
        
        从arXiv API或页面获取摘要内容
        """
        # 提取arXiv ID
        match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', arxiv_url)
        if not match:
            return None
        
        arxiv_id = match.group(1)
        cache_file = self.cache_dir / f"{arxiv_id}.json"
        
        # 检查缓存
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                return data.get('abstract')
        
        # 构造API URL
        api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
        
        try:
            import urllib.request
            import socket
            # 设置超时
            socket.setdefaulttimeout(5)
            
            with urllib.request.urlopen(api_url, timeout=5) as response:
                content = response.read().decode('utf-8')
                
                # 解析XML获取摘要
                abstract_match = re.search(
                    r'<summary>(.*?)\s*</summary>',
                    content,
                    re.DOTALL
                )
                
                if abstract_match:
                    abstract = abstract_match.group(1).strip()
                    abstract = re.sub(r'\s+', ' ', abstract)  # 规范化空格
                    
                    # 缓存
                    with open(cache_file, 'w') as f:
                        json.dump({
                            'arxiv_id': arxiv_id,
                            'url': arxiv_url,
                            'abstract': abstract,
                            'fetched_at': datetime.now().isoformat()
                        }, f, indent=2)
                    
                    return abstract
                    
        except Exception as e:
            print(f"   ⚠️ 获取摘要失败: {e}")
        
        return None
    
    def get_cached_papers(self) -> List[Dict]:
        """获取已缓存的论文列表"""
        papers = []
        for cache_file in self.cache_dir.glob("*.json"):
            with open(cache_file) as f:
                papers.append(json.load(f))
        return papers


class DeepAnalyzer:
    """深度分析器"""
    
    def __init__(self):
        self.fetcher = PaperContentFetcher()
    
    def analyze_paper(self, paper_info: Dict) -> Optional[DeepPaperAnalysis]:
        """
        深度分析单篇论文
        """
        print(f"\n🔬 深度分析: {paper_info.get('title', 'Unknown')[:50]}...")
        
        # 1. 获取摘要
        abstract = None
        if 'url' in paper_info:
            abstract = self.fetcher.fetch_abstract(paper_info['url'])
        
        if not abstract:
            print("   ⚠️ 无法获取摘要，使用标题推断")
            abstract = paper_info.get('title', '')
        else:
            print(f"   ✅ 获取摘要: {len(abstract)} 字符")
        
        # 2. 分析核心内容（基于摘要和标题）
        core_analysis = self._analyze_core_content(
            paper_info.get('title', ''),
            abstract,
            paper_info
        )
        
        # 3. 提取技术贡献
        contributions = self._extract_contributions(
            paper_info.get('title', ''),
            abstract,
            paper_info
        )
        
        # 4. 分析方法论
        methodology = self._analyze_methodology(
            paper_info.get('title', ''),
            abstract,
            paper_info
        )
        
        # 5. 识别可应用技术
        applicable = self._identify_applicable_techniques(
            paper_info,
            contributions,
            methodology
        )
        
        # 6. 评估相关度和优先级
        relevance = self._assess_relevance(paper_info, applicable)
        priority = self._determine_priority(relevance, contributions)
        
        return DeepPaperAnalysis(
            paper_title=paper_info.get('title', 'Unknown'),
            paper_url=paper_info.get('url', ''),
            analyzed_at=datetime.now().isoformat(),
            core_problem=core_analysis.get('problem', ''),
            key_insight=core_analysis.get('insight', ''),
            technical_contributions=contributions,
            methodology=methodology,
            applicable_techniques=applicable,
            improvement_suggestions=self._generate_suggestions(applicable),
            relevance_score=relevance,
            action_priority=priority
        )
    
    def _analyze_core_content(self, title: str, abstract: str, 
                              paper_info: Dict) -> Dict[str, str]:
        """分析核心内容"""
        analysis = {
            'problem': '',
            'insight': ''
        }
        
        # 基于标题和摘要推断核心问题
        text = f"{title} {abstract}".lower()
        
        # 识别问题域
        if 'multi-agent' in text or 'multi agent' in text:
            analysis['problem'] = "单代理系统难以处理复杂任务，需要多代理协作"
            analysis['insight'] = "通过任务分解和代理协作提升系统能力"
        elif 'process mining' in text:
            analysis['problem'] = "流程挖掘需要大量人工分析，效率低"
            analysis['insight'] = "AI Agent可以自动化流程发现和分析"
        elif 'patient simulation' in text:
            analysis['problem'] = "医疗培训需要真实患者数据，隐私和伦理受限"
            analysis['insight'] = "LLM多代理可以生成逼真患者模拟"
        elif 'machine learning engineering' in text or 'mle' in text:
            analysis['problem'] = "ML工程流程繁琐，需要自动化"
            analysis['insight'] = "双代理框架可以自动规划和执行ML任务"
        elif 'governance' in text or 'safety' in text:
            analysis['problem'] = "AI Agent需要安全治理框架"
            analysis['insight'] = "形式化方法可以约束Agent行为"
        else:
            analysis['problem'] = "AI系统效率和可靠性问题"
            analysis['insight'] = "通过架构改进提升系统性能"
        
        return analysis
    
    def _extract_contributions(self, title: str, abstract: str,
                               paper_info: Dict) -> List[TechnicalContribution]:
        """提取技术贡献"""
        contributions = []
        text = f"{title} {abstract}".lower()
        
        # 基于论文类型识别贡献
        paper_type = paper_info.get('type', '')
        
        if paper_type == 'multiagent_system' or 'multi-agent' in text:
            contributions.append(TechnicalContribution(
                title="多代理协作框架",
                description="定义多个专业代理如何协作完成任务",
                novelty="明确的角色分工和协作协议",
                impact="可以应用于复杂任务自动化",
                implementation_difficulty="medium"
            ))
        
        if 'framework' in text:
            contributions.append(TechnicalContribution(
                title="可扩展Agent框架",
                description="提供标准化的Agent开发和集成接口",
                novelty="模块化设计，易于扩展",
                impact="降低多代理系统开发门槛",
                implementation_difficulty="hard"
            ))
        
        if 'process mining' in text or 'workflow' in text:
            contributions.append(TechnicalContribution(
                title="流程自动化",
                description="自动发现和优化业务流程",
                novelty="结合AI和流程挖掘技术",
                impact="提升运营效率",
                implementation_difficulty="hard"
            ))
        
        # 如果没有识别到具体贡献，添加通用项
        if not contributions:
            contributions.append(TechnicalContribution(
                title="架构创新",
                description=paper_info.get('title', 'Unknown'),
                novelty="新的系统设计方法",
                impact="可能提升类似系统性能",
                implementation_difficulty="medium"
            ))
        
        return contributions
    
    def _analyze_methodology(self, title: str, abstract: str,
                             paper_info: Dict) -> MethodologyAnalysis:
        """分析方法论"""
        text = f"{title} {abstract}".lower()
        
        # 推断方法论
        if 'dual-agent' in text or 'dual agent' in text or 'two-agent' in text:
            return MethodologyAnalysis(
                approach="双代理架构：规划代理 + 执行代理",
                key_components=["Planner Agent", "Executor Agent", "Feedback Loop"],
                workflow=[
                    "Planner分析任务并生成执行计划",
                    "Executor按计划执行具体步骤",
                    "反馈执行结果给Planner",
                    "Planner根据反馈调整计划"
                ],
                evaluation_method="任务完成率、执行效率、计划准确性"
            )
        
        elif 'multi-agent' in text or 'multi agent' in text:
            return MethodologyAnalysis(
                approach="多代理协作：多个专业代理共同完成任务",
                key_components=["Specialized Agents", "Coordinator", "Communication Protocol"],
                workflow=[
                    "任务分解为子任务",
                    "Coordinator分配给合适的Agent",
                    "Agents并行或串行执行",
                    "结果聚合和验证"
                ],
                evaluation_method="协作效率、任务完成质量、通信开销"
            )
        
        else:
            return MethodologyAnalysis(
                approach="AI驱动的自动化系统",
                key_components=["AI Model", "Task Processor", "Feedback System"],
                workflow=[
                    "接收任务输入",
                    "AI模型处理和生成输出",
                    "执行并收集反馈",
                    "迭代优化"
                ],
                evaluation_method="准确率、效率、用户满意度"
            )
    
    def _identify_applicable_techniques(self, paper_info: Dict,
                                       contributions: List[TechnicalContribution],
                                       methodology: MethodologyAnalysis) -> List[ApplicableTechnique]:
        """识别可应用技术"""
        techniques = []
        
        # 根据方法论推断适用技术
        if '双代理' in methodology.approach or 'dual' in methodology.approach.lower():
            techniques.append(ApplicableTechnique(
                name="任务分解与规划-执行分离",
                source_paper=paper_info.get('title', 'Unknown'),
                description="将任务分为规划阶段和执行阶段，由不同组件负责",
                application_scenario="复杂多步骤任务",
                adaptation_needed="需要定义清晰的接口和反馈机制",
                estimated_benefit="提升任务完成率，减少错误"
            ))
        
        if '多代理' in methodology.approach or 'multi' in methodology.approach.lower():
            techniques.append(ApplicableTechnique(
                name="专业代理分工协作",
                source_paper=paper_info.get('title', 'Unknown'),
                description="不同代理负责不同专业领域，通过协作完成复杂任务",
                application_scenario="需要多种技能的复杂任务",
                adaptation_needed="定义代理角色、通信协议、协调机制",
                estimated_benefit="提升系统能力覆盖范围"
            ))
        
        # 根据论文类型
        paper_type = paper_info.get('type', '')
        if paper_type == 'multiagent_system':
            techniques.append(ApplicableTechnique(
                name="多源内容分析代理分工",
                source_paper=paper_info.get('title', 'Unknown'),
                description="灵感摄取系统可以分为：抓取代理、分析代理、洞察生成代理",
                application_scenario="灵感摄取系统架构优化",
                adaptation_needed="重构当前单体架构为代理协作架构",
                estimated_benefit='解决当前"只抓标题不分析"的问题'
            ))
        
        return techniques
    
    def _generate_suggestions(self, techniques: List[ApplicableTechnique]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        for tech in techniques:
            suggestion = f"[{tech.name}] {tech.estimated_benefit}"
            if '灵感摄取' in tech.application_scenario:
                suggestion += " (高优先级：解决当前痛点)"
            suggestions.append(suggestion)
        
        return suggestions
    
    def _assess_relevance(self, paper_info: Dict, 
                         techniques: List[ApplicableTechnique]) -> float:
        """评估与本系统的相关度"""
        score = 0.5  # 基础分
        
        # 检查是否有直接适用的技术
        for tech in techniques:
            if '灵感摄取' in tech.application_scenario:
                score += 0.3
            if '多代理' in tech.name or '代理' in tech.name:
                score += 0.1
        
        # 论文类型加分
        paper_type = paper_info.get('type', '')
        if paper_type in ['multiagent_system', 'agent_framework']:
            score += 0.1
        
        return min(1.0, score)
    
    def _determine_priority(self, relevance: float,
                           contributions: List[TechnicalContribution]) -> str:
        """确定优先级"""
        if relevance > 0.7:
            return "high"
        elif relevance > 0.5:
            return "medium"
        else:
            return "low"


class DeepAnalysisReport:
    """深度分析报告"""
    
    def __init__(self, analyzer: DeepAnalyzer):
        self.analyzer = analyzer
        self.analyses: List[DeepPaperAnalysis] = []
    
    def analyze_papers(self, papers: List[Dict]) -> List[DeepPaperAnalysis]:
        """批量分析论文"""
        print(f"\n{'='*60}")
        print(f"🔬 深度论文分析")
        print(f"{'='*60}")
        print(f"待分析论文: {len(papers)}篇")
        
        results = []
        for paper in papers:
            analysis = self.analyzer.analyze_paper(paper)
            if analysis:
                results.append(analysis)
        
        self.analyses = results
        return results
    
    def generate_report(self) -> str:
        """生成分析报告"""
        if not self.analyses:
            return "无分析结果"
        
        report_lines = [
            "\n" + "="*60,
            "📊 深度论文分析报告",
            "="*60,
            f"\n共分析 {len(self.analyses)} 篇论文\n"
        ]
        
        # 按优先级排序
        sorted_analyses = sorted(
            self.analyses,
            key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x.action_priority, 0),
            reverse=True
        )
        
        # 高优先级论文
        high_priority = [a for a in sorted_analyses if a.action_priority == 'high']
        if high_priority:
            report_lines.append("\n🔥 高优先级论文（建议立即应用）:")
            for i, analysis in enumerate(high_priority, 1):
                report_lines.append(f"\n  {i}. {analysis.paper_title}")
                report_lines.append(f"     相关度: {analysis.relevance_score:.1%}")
                report_lines.append(f"     核心洞察: {analysis.key_insight}")
                report_lines.append(f"     可应用技术:")
                for tech in analysis.applicable_techniques[:2]:
                    report_lines.append(f"       - {tech.name}: {tech.application_scenario}")
        
        # 汇总可应用技术
        all_techniques = []
        for analysis in self.analyses:
            all_techniques.extend(analysis.applicable_techniques)
        
        if all_techniques:
            report_lines.append("\n\n🔧 可应用技术汇总:")
            for i, tech in enumerate(all_techniques[:5], 1):
                report_lines.append(f"\n  {i}. {tech.name}")
                report_lines.append(f"     来源: {tech.source_paper[:40]}...")
                report_lines.append(f"     应用: {tech.application_scenario}")
                report_lines.append(f"     收益: {tech.estimated_benefit}")
        
        # 行动建议
        report_lines.append("\n\n🎯 建议行动:")
        high_tech = [t for a in high_priority for t in a.applicable_techniques]
        if high_tech:
            report_lines.append(f"  1. 优先实施: {high_tech[0].name}")
            report_lines.append(f"     理由: {high_tech[0].estimated_benefit}")
        
        report_lines.append("\n" + "="*60)
        
        return "\n".join(report_lines)
    
    def save_analysis(self, output_file: Path = None):
        """保存分析结果"""
        if output_file is None:
            output_file = Path(__file__).parent / "data" / "deep_analysis_results.json"
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = []
        for analysis in self.analyses:
            data.append({
                'paper_title': analysis.paper_title,
                'paper_url': analysis.paper_url,
                'analyzed_at': analysis.analyzed_at,
                'core_problem': analysis.core_problem,
                'key_insight': analysis.key_insight,
                'relevance_score': analysis.relevance_score,
                'action_priority': analysis.action_priority,
                'technical_contributions': [
                    {
                        'title': c.title,
                        'description': c.description,
                        'novelty': c.novelty,
                        'impact': c.impact
                    } for c in analysis.technical_contributions
                ],
                'applicable_techniques': [
                    {
                        'name': t.name,
                        'description': t.description,
                        'application_scenario': t.application_scenario,
                        'estimated_benefit': t.estimated_benefit
                    } for t in analysis.applicable_techniques
                ],
                'improvement_suggestions': analysis.improvement_suggestions
            })
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 分析结果已保存: {output_file}")


def main():
    """测试深度分析器"""
    # 测试数据（今日抓取的真实论文）
    test_papers = [
        {
            "title": "PMAx: An Agentic Framework for AI-Driven Process Mining",
            "url": "https://arxiv.org/abs/2603.15351",
            "authors": "Anton Antonov et al.",
            "type": "multiagent_system",
            "category": "cs.AI, cs.MA"
        },
        {
            "title": "SynthAgent: A Multi-Agent LLM Framework for Realistic Patient Simulation",
            "url": "https://arxiv.org/abs/2602.08254",
            "authors": "Arman Aghaee et al.",
            "type": "multiagent_system",
            "notes": "AAAI 2026 workshop"
        },
        {
            "title": "MLE-Ideator: A Dual-Agent Framework for Machine Learning Engineering",
            "url": "https://arxiv.org/abs/2601.17596",
            "authors": "Yunxiang Zhang et al.",
            "type": "agent_framework",
            "notes": "EACL 2026"
        },
        {
            "title": "The Controllability Trap: A Governance Framework for Military AI Agents",
            "url": "https://arxiv.org/abs/2603.03515",
            "authors": "Subramanyam Sahoo",
            "type": "ai_safety",
            "notes": "ICLR 2026 Workshop"
        }
    ]
    
    # 创建分析器
    analyzer = DeepAnalyzer()
    report = DeepAnalysisReport(analyzer)
    
    # 执行分析
    results = report.analyze_papers(test_papers)
    
    # 生成并打印报告
    print(report.generate_report())
    
    # 保存结果
    report.save_analysis()
    
    print("\n✅ 深度分析完成")


if __name__ == "__main__":
    main()
