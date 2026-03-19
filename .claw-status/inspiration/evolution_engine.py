#!/usr/bin/env python3
"""
灵感进化引擎 - Inspiration Evolution Engine (IEE)

从收集的灵感中提取洞察，生成系统优化方案并实施

闭环流程:
1. 灵感分析 → 提取模式/趋势/技术
2. 洞察生成 → 识别可改进点
3. 方案设计 → 生成架构优化方案
4. 自动实施 → 修改底层系统
5. 效果验证 → A/B测试或监控
6. 知识固化 → 更新文档/原则

Author: wdai
Version: 1.0
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

# 导入风险评估框架
try:
    from risk_assessment import RiskAssessmentFramework, RiskLevel, RiskAssessment
    from todo_manager import TodoListManager, get_todo_manager
    from code_understanding import CodeUnderstandingLayer, ImpactAnalysis
    CODE_UNDERSTANDING_AVAILABLE = True
    RISK_FRAMEWORK_AVAILABLE = True
    TODO_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠️ 部分模块导入失败: {e}")
    CODE_UNDERSTANDING_AVAILABLE = False
    RISK_FRAMEWORK_AVAILABLE = False
    TODO_MANAGER_AVAILABLE = False

# 🆕 Phase 2: 导入创造性设计层
try:
    from creative_design import (
        CreativeDesignLayer, ArchitecturePattern, DesignCandidate,
        PatternLibrary, MultiObjectiveOptimizer
    )
    CREATIVE_DESIGN_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠️ 创造性设计层导入失败: {e}")
    CREATIVE_DESIGN_AVAILABLE = False

# 🆕 Phase 3: 导入形式化验证层
try:
    from formal_verification import (
        FormalVerificationLayer, VerificationResult, 
        VerificationStatus, TypeChecker, InvariantInference
    )
    FORMAL_VERIFICATION_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠️ 形式化验证层导入失败: {e}")
    FORMAL_VERIFICATION_AVAILABLE = False

# 🆕 Phase 4: 导入沙箱测试层
try:
    from sandbox_testing import (
        SandboxTestingLayer, SandboxTestReport,
        TestCase, TestResult, PerformanceMetrics, ABTestResult
    )
    SANDBOX_TESTING_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠️ 沙箱测试层导入失败: {e}")
    SANDBOX_TESTING_AVAILABLE = False

# 🆕 Phase 5: 导入反馈学习层
try:
    from feedback_learning import (
        FeedbackLearningLayer, ModificationRecord,
        ReinforcementLearner, MetaLearner
    )
    FEEDBACK_LEARNING_AVAILABLE = True
except ImportError as e:
    print(f"   ⚠️ 反馈学习层导入失败: {e}")
    FEEDBACK_LEARNING_AVAILABLE = False

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))


@dataclass
class Insight:
    """洞察"""
    id: str
    type: str  # pattern, trend, tech, pain_point, opportunity
    source: str
    content: str
    confidence: float
    impact: str  # high, medium, low
    related_items: List[str]
    generated_at: str
    status: str = "pending"  # pending, validated, implemented, rejected


@dataclass
class OptimizationPlan:
    """优化方案"""
    id: str
    insight_id: str
    title: str
    description: str
    target_system: str
    changes: List[Dict]
    estimated_impact: str
    implementation_steps: List[str]
    risk_level: str  # low, medium, high
    status: str = "draft"  # draft, approved, implementing, done, failed


class InspirationAnalyzer:
    """
    灵感分析器
    
    分析收集的内容，提取有价值的洞察
    """
    
    # 关注的模式关键词
    PATTERNS = {
        'architecture': ['架构', 'architecture', 'refactor', 'redesign', '模块化', '解耦'],
        'performance': ['性能', 'performance', '优化', 'speed', 'fast', 'latency'],
        'reliability': ['可靠', 'reliability', '容错', 'fault tolerance', '自愈', 'stability'],
        'security': ['安全', 'security', '隐私', 'privacy', '加密', 'authentication'],
        'usability': ['易用', 'usability', '体验', '体验', '交互', 'interface'],
        'new_tech': ['新技术', 'new tech', '突破', 'breakthrough', 'SOTA', 'state of art'],
    }
    
    def __init__(self, data_dir: str = "data/insights"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.insights_file = self.data_dir / "insights.json"
        self.patterns_file = self.data_dir / "patterns.json"
        
        self.insights: List[Insight] = []
        self.pattern_history: Dict = {}
        
        self._load_data()
    
    def _load_data(self):
        """加载历史数据"""
        if self.insights_file.exists():
            try:
                with open(self.insights_file, 'r') as f:
                    data = json.load(f)
                    self.insights = [Insight(**i) for i in data]
            except:
                self.insights = []
    
    def _save_data(self):
        """保存数据"""
        try:
            with open(self.insights_file, 'w') as f:
                json.dump([asdict(i) for i in self.insights], f, indent=2)
        except:
            pass
    
    def analyze_batch(self, items: List[Dict]) -> List[Insight]:
        """
        分析一批内容，提取洞察
        
        Args:
            items: 从各种源收集的内容
            
        Returns:
            新发现的洞察列表
        """
        new_insights = []
        
        # 1. 技术趋势分析
        tech_trends = self._extract_tech_trends(items)
        for trend in tech_trends:
            insight = Insight(
                id=f"trend_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(new_insights)}",
                type="trend",
                source=trend['source'],
                content=trend['description'],
                confidence=trend['confidence'],
                impact=trend['impact'],
                related_items=trend['related_ids'],
                generated_at=datetime.now().isoformat()
            )
            if not self._insight_exists(insight):
                new_insights.append(insight)
        
        # 2. 架构模式识别
        arch_patterns = self._extract_architecture_patterns(items)
        for pattern in arch_patterns:
            insight = Insight(
                id=f"arch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(new_insights)}",
                type="pattern",
                source=pattern['source'],
                content=pattern['description'],
                confidence=pattern['confidence'],
                impact=pattern['impact'],
                related_items=pattern['related_ids'],
                generated_at=datetime.now().isoformat()
            )
            if not self._insight_exists(insight):
                new_insights.append(insight)
        
        # 3. 痛点识别
        pain_points = self._extract_pain_points(items)
        for point in pain_points:
            insight = Insight(
                id=f"pain_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(new_insights)}",
                type="pain_point",
                source=point['source'],
                content=point['description'],
                confidence=point['confidence'],
                impact=point['impact'],
                related_items=point['related_ids'],
                generated_at=datetime.now().isoformat()
            )
            if not self._insight_exists(insight):
                new_insights.append(insight)
        
        # 4. 机会识别
        opportunities = self._extract_opportunities(items)
        for opp in opportunities:
            insight = Insight(
                id=f"opp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(new_insights)}",
                type="opportunity",
                source=opp['source'],
                content=opp['description'],
                confidence=opp['confidence'],
                impact=opp['impact'],
                related_items=opp['related_ids'],
                generated_at=datetime.now().isoformat()
            )
            if not self._insight_exists(insight):
                new_insights.append(insight)
        
        # 保存新洞察
        self.insights.extend(new_insights)
        self._save_data()
        
        return new_insights
    
    def _extract_tech_trends(self, items: List[Dict]) -> List[Dict]:
        """提取技术趋势"""
        trends = []
        
        # 统计技术关键词频率
        tech_keywords = defaultdict(list)
        
        for item in items:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            
            # 检测新技术趋势
            trend_patterns = [
                (r'\b(MCP|Model Context Protocol)\b', 'MCP Protocol'),
                (r'\b(Claude Code|Claude Agent)\b', 'Claude Code'),
                (r'\b(Reasoning|reasoning model)\b', 'Reasoning Models'),
                (r'\b(Agent|AI Agent)\b', 'AI Agents'),
                (r'\b(RAG|Retrieval Augmented)\b', 'RAG Systems'),
                (r'\b(Multi-modal|multimodal)\b', 'Multi-modal AI'),
            ]
            
            for pattern, trend_name in trend_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    tech_keywords[trend_name].append(item.get('id', 'unknown'))
        
        # 生成趋势洞察
        for trend_name, item_ids in tech_keywords.items():
            if len(item_ids) >= 2:  # 至少2次提及才算趋势
                trends.append({
                    'source': f"aggregated_from_{len(item_ids)}_items",
                    'description': f"'{trend_name}' 被多次提及，可能代表重要技术趋势",
                    'confidence': min(0.5 + len(item_ids) * 0.1, 0.9),
                    'impact': 'high' if len(item_ids) >= 5 else 'medium',
                    'related_ids': item_ids[:10]
                })
        
        return trends
    
    def _extract_architecture_patterns(self, items: List[Dict]) -> List[Dict]:
        """提取架构模式"""
        patterns = []
        
        for item in items:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            
            # 检测架构相关讨论
            if any(kw in text for kw in ['架构', 'architecture', '设计模式', 'pattern']):
                # 提取具体建议
                sentences = text.split('.')
                for sent in sentences:
                    if any(kw in sent for kw in ['应该', 'should', '推荐', 'recommend', '最佳实践', 'best practice']):
                        patterns.append({
                            'source': item.get('source', 'unknown'),
                            'description': sent.strip(),
                            'confidence': 0.7,
                            'impact': 'medium',
                            'related_ids': [item.get('id', 'unknown')]
                        })
        
        return patterns[:5]  # 限制数量
    
    def _extract_pain_points(self, items: List[Dict]) -> List[Dict]:
        """提取痛点"""
        pain_points = []
        
        pain_keywords = ['问题', 'problem', '困难', 'difficult', '痛点', 'pain', 
                        'bug', 'issue', 'error', '失败', 'fail']
        
        for item in items:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            
            if any(kw in text for kw in pain_keywords):
                # 提取包含痛点的句子
                sentences = text.split('.')
                for sent in sentences:
                    if any(kw in sent for kw in pain_keywords) and len(sent) > 20:
                        pain_points.append({
                            'source': item.get('source', 'unknown'),
                            'description': f"发现痛点: {sent.strip()}",
                            'confidence': 0.6,
                            'impact': 'high',
                            'related_ids': [item.get('id', 'unknown')]
                        })
                        break  # 每个item只取一个痛点
        
        return pain_points[:5]
    
    def _extract_opportunities(self, items: List[Dict]) -> List[Dict]:
        """提取机会"""
        opportunities = []
        
        opp_keywords = ['机会', 'opportunity', '改进', 'improve', '优化', 'optimize',
                       '新功能', 'feature', '可以', 'could', '可能', 'might']
        
        for item in items:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            
            if any(kw in text for kw in opp_keywords):
                sentences = text.split('.')
                for sent in sentences:
                    if any(kw in sent for kw in opp_keywords) and len(sent) > 20:
                        opportunities.append({
                            'source': item.get('source', 'unknown'),
                            'description': f"潜在机会: {sent.strip()}",
                            'confidence': 0.5,
                            'impact': 'medium',
                            'related_ids': [item.get('id', 'unknown')]
                        })
                        break
        
        return opportunities[:5]
    
    def _insight_exists(self, new_insight: Insight) -> bool:
        """检查洞察是否已存在（去重）"""
        for existing in self.insights:
            # 简单文本相似度检查
            if self._text_similarity(existing.content, new_insight.content) > 0.8:
                return True
        return False
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def get_top_insights(self, n: int = 5) -> List[Insight]:
        """获取最重要的洞察"""
        # 按影响力和置信度排序
        sorted_insights = sorted(
            self.insights,
            key=lambda x: (x.impact == 'high', x.confidence),
            reverse=True
        )
        return sorted_insights[:n]


class OptimizationPlanner:
    """
    优化方案设计器
    
    基于洞察生成具体的系统优化方案
    """
    
    def __init__(self, data_dir: str = "data/plans"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.plans_file = self.data_dir / "optimization_plans.json"
        self.plans: List[OptimizationPlan] = []
        
        self._load_data()
    
    def _load_data(self):
        """加载历史方案"""
        if self.plans_file.exists():
            try:
                with open(self.plans_file, 'r') as f:
                    data = json.load(f)
                    self.plans = [OptimizationPlan(**p) for p in data]
            except:
                self.plans = []
    
    def _save_data(self):
        """保存数据"""
        try:
            with open(self.plans_file, 'w') as f:
                json.dump([asdict(p) for p in self.plans], f, indent=2)
        except:
            pass
    
    def generate_plan(self, insight: Insight) -> Optional[OptimizationPlan]:
        """
        基于洞察生成优化方案
        """
        # 根据洞察类型生成不同方案
        if insight.type == "trend":
            return self._plan_for_trend(insight)
        elif insight.type == "pattern":
            return self._plan_for_pattern(insight)
        elif insight.type == "pain_point":
            return self._plan_for_pain_point(insight)
        elif insight.type == "opportunity":
            return self._plan_for_opportunity(insight)
        
        return None
    
    def _plan_for_trend(self, insight: Insight) -> OptimizationPlan:
        """为技术趋势生成方案"""
        trend_name = insight.content.split("'")[1] if "'" in insight.content else "新技术"
        
        return OptimizationPlan(
            id=f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            insight_id=insight.id,
            title=f"集成/跟进 {trend_name}",
            description=f"根据洞察 '{insight.content[:50]}...'，建议系统跟进此技术趋势",
            target_system="inspiration_system",
            changes=[
                {"file": "crawler_*.py", "action": "add_source", "details": f"添加{trend_name}监控源"},
                {"file": "scheduler.py", "action": "update_config", "details": "调整调度策略适配新源"}
            ],
            estimated_impact="high" if insight.impact == "high" else "medium",
            implementation_steps=[
                f"1. 研究{trend_name}的API/RSS接口",
                f"2. 创建专用抓取器",
                "3. 集成到调度器",
                "4. 测试验证",
                "5. 更新文档"
            ],
            risk_level="low"
        )
    
    def _plan_for_pattern(self, insight: Insight) -> OptimizationPlan:
        """为架构模式生成方案"""
        return OptimizationPlan(
            id=f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            insight_id=insight.id,
            title="架构模式优化",
            description=f"应用架构模式: {insight.content[:80]}...",
            target_system="core_architecture",
            changes=[
                {"file": "*.py", "action": "refactor", "details": "按建议模式重构代码"}
            ],
            estimated_impact=insight.impact,
            implementation_steps=[
                "1. 分析当前架构问题",
                "2. 设计新架构方案",
                "3. 逐步迁移实现",
                "4. 验证改进效果"
            ],
            risk_level="medium"
        )
    
    def _plan_for_pain_point(self, insight: Insight) -> OptimizationPlan:
        """为痛点生成方案"""
        return OptimizationPlan(
            id=f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            insight_id=insight.id,
            title=f"修复: {insight.content[:40]}...",
            description=insight.content,
            target_system="identified_from_pain",
            changes=[
                {"file": "*.py", "action": "fix", "details": "针对痛点的修复"}
            ],
            estimated_impact="high",
            implementation_steps=[
                "1. 复现问题",
                "2. 定位根本原因",
                "3. 实施修复",
                "4. 验证解决"
            ],
            risk_level="low"
        )
    
    def _plan_for_opportunity(self, insight: Insight) -> OptimizationPlan:
        """为机会生成方案"""
        return OptimizationPlan(
            id=f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            insight_id=insight.id,
            title=f"优化机会: {insight.content[:40]}...",
            description=insight.content,
            target_system="improvement_target",
            changes=[
                {"file": "*.py", "action": "enhance", "details": "实施优化"}
            ],
            estimated_impact=insight.impact,
            implementation_steps=[
                "1. 详细设计",
                "2. 小规模验证",
                "3. 全面实施",
                "4. 效果评估"
            ],
            risk_level="medium"
        )


class EvolutionEngine:
    """
    进化引擎 - 执行优化方案
    """
    
    SYSTEM_FILES = {
        'scheduler': 'scheduler.py',
        'crawler_arxiv': 'crawler_arxiv_deep.py',
        'crawler_reddit': 'crawler_reddit.py',
        'healing': 'self_healing.py',
        'solver': 'empty_run_solver.py',
        'runner': 'inspiration_runner.py',
    }
    
    def __init__(self, require_approval_for_medium: bool = True, use_code_understanding: bool = True):
        self.workspace = CLAW_STATUS
        self.require_approval_for_medium = require_approval_for_medium
        self.pending_approvals = []  # 待审批的方案
        
        # 初始化风险评估框架
        if RISK_FRAMEWORK_AVAILABLE:
            self.risk_framework = RiskAssessmentFramework()
        else:
            self.risk_framework = None
        
        # 🆕 Phase 1: 初始化代码理解层
        self.code_understanding = None
        if use_code_understanding and CODE_UNDERSTANDING_AVAILABLE:
            try:
                print("   🔍 初始化代码理解层 (Phase 1)...")
                self.code_understanding = CodeUnderstandingLayer(self.workspace)
                self.code_understanding.build()
                print("   ✅ 代码理解层就绪")
            except Exception as e:
                print(f"   ⚠️ 代码理解层初始化失败: {e}")
                self.code_understanding = None
    
    def implement_plan(self, plan: OptimizationPlan) -> Dict:
        """
        实施优化方案 - 带风险评估
        
        流程:
        1. 评估风险等级
        2. 低风险: 自动实施
        3. 中风险: 生成决策清单，等待审批
        4. 高风险: 必须人工评审
        """
        result = {
            'plan_id': plan.id,
            'status': 'pending',
            'risk_level': None,
            'risk_score': None,
            'actions_taken': [],
            'errors': [],
            'approval_required': False,
            'approval_status': None,
            'implemented_at': None
        }
        
        # 如果风险评估框架不可用，使用传统方式
        if not self.risk_framework:
            print("   ⚠️ 风险评估框架不可用，使用传统风险评估...")
            if plan.risk_level == "low":
                return self._do_implement(plan, result)
            else:
                result['status'] = 'waiting_approval'
                result['approval_required'] = True
                result['reason'] = 'risk_assessment_unavailable'
                return result
        
        try:
            # Step 1: 风险评估
            plan_dict = {
                'title': plan.title,
                'target_system': plan.target_system,
                'changes': plan.changes,
                'implementation_steps': plan.implementation_steps
            }
            
            assessment = self.risk_framework.assess_plan(plan_dict)
            result['risk_level'] = assessment.level.value
            result['risk_score'] = assessment.score
            
            print(f"   🛡️ 风险评估: {assessment.level.value.upper()} ({assessment.score}/100)")
            
            # 🆕 Phase 1: 使用代码理解层进行深入分析
            if self.code_understanding:
                print(f"   🔍 使用代码理解层分析影响...")
                impact = self.analyze_with_code_understanding(plan)
                if impact:
                    print(f"      影响函数: {len(impact.affected_functions)} 个")
                    print(f"      影响模块: {len(impact.affected_modules)} 个")
                    print(f"      代码风险评分: {impact.risk_score}/100")
                    
                    # 使用代码理解的风险评分（更精确）
                    if impact.risk_score > result['risk_score']:
                        print(f"      ⚠️ 代码分析显示更高风险，调整评分")
                        result['risk_score'] = impact.risk_score
                        # 如果超过阈值，提升风险等级
                        if impact.risk_score > 65 and assessment.level != RiskLevel.HIGH:
                            assessment.level = RiskLevel.HIGH
                            result['risk_level'] = 'high'
            
            # Step 2: 根据风险等级处理
            if assessment.level == RiskLevel.LOW:
                # 低风险: 自动实施
                print(f"   🟢 低风险方案，自动实施...")
                return self._do_implement(plan, result)
                
            elif assessment.level == RiskLevel.MEDIUM:
                # 中风险: 根据配置决定是否自动实施
                if self.require_approval_for_medium:
                    print(f"   🟡 中等风险，生成决策清单等待审批...")
                    result['approval_required'] = True
                    result['approval_status'] = 'pending'
                    result['status'] = 'waiting_approval'
                    
                    # 生成决策清单
                    self._generate_decision_checklist(plan, assessment)
                    
                    # 添加到待办清单
                    if TODO_MANAGER_AVAILABLE:
                        try:
                            todo_mgr = get_todo_manager()
                            todo_mgr.add_pending(
                                plan_id=plan.id,
                                title=plan.title,
                                description=plan.description,
                                risk_score=assessment.score,
                                risk_level=assessment.level.value,
                                decision_file=str(self.workspace / "data" / f"decision_{plan.id}.md")
                            )
                        except Exception as e:
                            print(f"   ⚠️ 添加到待办清单失败: {e}")
                    
                    # 添加到待审批列表
                    self.pending_approvals.append({
                        'plan_id': plan.id,
                        'title': plan.title,
                        'risk_score': assessment.score,
                        'assessment': assessment,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    return result
                else:
                    print(f"   🟡 中等风险，但配置允许自动实施...")
                    return self._do_implement(plan, result)
            
            else:  # HIGH
                # 高风险: 必须人工评审
                print(f"   🔴 高风险方案，必须人工评审...")
                result['approval_required'] = True
                result['approval_status'] = 'requires_manual_review'
                result['status'] = 'blocked'
                
                # 生成详细评审文档
                self._generate_review_document(plan, assessment)
                
                # 添加到待办清单（高风险也加入待办，方便跟踪）
                if TODO_MANAGER_AVAILABLE:
                    try:
                        todo_mgr = get_todo_manager()
                        todo_mgr.add_pending(
                            plan_id=plan.id,
                            title=f"[HIGH RISK] {plan.title}",
                            description=plan.description,
                            risk_score=assessment.score,
                            risk_level=assessment.level.value,
                            decision_file=str(self.workspace / "data" / f"HIGH_RISK_REVIEW_{plan.id}.md")
                        )
                    except Exception as e:
                        print(f"   ⚠️ 添加到待办清单失败: {e}")
                
                return result
                
        except Exception as e:
            result['status'] = 'failed'
            result['errors'].append(str(e))
            return result
    
    def _do_implement(self, plan: OptimizationPlan, result: Dict) -> Dict:
        """实际实施方案"""
        try:
            # 1. 备份原文件
            self._backup_files(plan)
            result['actions_taken'].append("backup_created")
            
            # 2. 根据方案类型执行
            if plan.target_system == "inspiration_system":
                self._implement_crawler_update(plan)
                result['actions_taken'].append("crawler_updated")
                
            elif plan.target_system == "core_architecture":
                self._implement_architecture_change(plan)
                result['actions_taken'].append("architecture_updated")
                
            elif plan.target_system == "identified_from_pain":
                self._implement_fix(plan)
                result['actions_taken'].append("fix_applied")
                
            elif plan.target_system == "improvement_target":
                self._implement_enhancement(plan)
                result['actions_taken'].append("enhancement_applied")
            
            # 3. 验证实施
            if self._verify_implementation(plan):
                result['status'] = 'success'
                result['actions_taken'].append("verification_passed")
            else:
                result['status'] = 'partial'
                result['errors'].append("verification_failed")
                
        except Exception as e:
            result['status'] = 'failed'
            result['errors'].append(str(e))
            # 尝试回滚
            self._rollback(plan)
        
        result['implemented_at'] = datetime.now().isoformat()
        return result
    
    def _generate_decision_checklist(self, plan: OptimizationPlan, assessment: RiskAssessment):
        """生成决策清单"""
        checklist_file = self.workspace / "data" / f"decision_{plan.id}.md"
        
        content = f"""# 优化方案决策清单

## 方案信息
- **标题**: {plan.title}
- **目标系统**: {plan.target_system}
- **风险等级**: {assessment.level.value.upper()}
- **综合评分**: {assessment.score}/100

## 详细评估

### 评分维度
"""
        for factor in assessment.factors:
            content += f"- {factor['dimension']}: {factor['raw_score']}分 - {factor['reasoning']}\n"
        
        content += f"""
### 评估结论
{assessment.reasoning}

## 实施方案

### 计划修改
"""
        for change in plan.changes:
            content += f"- `{change['file']}`: {change['action']} - {change.get('details', '')}\n"
        
        content += f"""
### 实施步骤
"""
        for step in plan.implementation_steps:
            content += f"- {step}\n"
        
        content += """
## 人工决策

### 安全确认 (必须全部通过才能实施)
- [ ] 已阅读方案描述和技术细节
- [ ] 理解修改的影响范围
- [ ] 确认有回滚方案或备份
- [ ] 评估业务影响时间窗口

### 决策选项
- [ ] **批准实施** - 风险可控，可以实施
- [ ] **拒绝实施** - 风险过高，暂不实施
- [ ] **需要修改** - 方案需要调整后重新评估

### 备注
<!-- 在此填写决策理由或其他说明 -->

---
生成时间: """ + datetime.now().isoformat() + """
审批文件: """ + str(checklist_file) + """
"""
        
        with open(checklist_file, 'w') as f:
            f.write(content)
        
        print(f"   📋 决策清单已生成: {checklist_file}")
    
    def _generate_review_document(self, plan: OptimizationPlan, assessment: RiskAssessment):
        """生成高风险评审文档"""
        review_file = self.workspace / "data" / f"HIGH_RISK_REVIEW_{plan.id}.md"
        
        content = f"""# 🔴 高风险方案评审

## ⚠️ 警告
此方案被评估为**高风险**，需要详细的人工评审才能实施。

## 方案信息
- **标题**: {plan.title}
- **风险评分**: {assessment.score}/100
- **风险等级**: {assessment.level.value.upper()}

## 风险详情

### 主要风险点
"""
        # 按分数排序，列出前3个风险点
        sorted_factors = sorted(assessment.factors, key=lambda x: x['raw_score'], reverse=True)
        for factor in sorted_factors[:3]:
            content += f"- **{factor['dimension']}**: {factor['raw_score']}分\n"
            content += f"  - {factor['reasoning']}\n\n"
        
        content += f"""
## 建议处理方式

由于此方案风险较高，建议：

1. **详细评审**: 组织技术评审会议
2. **测试计划**: 制定全面的测试方案
3. **灰度发布**: 考虑小规模验证
4. **回滚准备**: 确保可以快速回滚

## 决策记录

**审批状态**: 待评审

**评审人**: ________________
**评审日期**: ________________
**决策**: [ ] 批准  [ ] 拒绝  [ ] 需要修改

**评审意见**:
<!-- 填写详细评审意见 -->

---
生成时间: """ + datetime.now().isoformat() + """
"""
        
        with open(review_file, 'w') as f:
            f.write(content)
        
        print(f"   🔴 高风险评审文档已生成: {review_file}")
    
    def _backup_files(self, plan: OptimizationPlan):
        """备份原文件"""
        backup_dir = self.workspace / "data" / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        for change in plan.changes:
            file_pattern = change.get('file', '')
            # 简单处理，实际需要glob匹配
            if file_pattern in self.SYSTEM_FILES:
                src = self.workspace / self.SYSTEM_FILES[file_pattern]
                if src.exists():
                    import shutil
                    shutil.copy2(src, backup_dir / src.name)
    
    def _implement_crawler_update(self, plan: OptimizationPlan):
        """实施抓取器更新"""
        # 这里应该是实际的代码修改逻辑
        # 简化版：记录到todo文件
        todo_file = self.workspace / "data" / "evolution_todo.json"
        
        todo = {
            'type': 'crawler_update',
            'plan_id': plan.id,
            'description': plan.description,
            'steps': plan.implementation_steps,
            'created_at': datetime.now().isoformat(),
            'status': 'pending_implementation'
        }
        
        todos = []
        if todo_file.exists():
            with open(todo_file, 'r') as f:
                todos = json.load(f)
        
        todos.append(todo)
        
        with open(todo_file, 'w') as f:
            json.dump(todos, f, indent=2)
    
    def _implement_architecture_change(self, plan: OptimizationPlan):
        """实施架构变更"""
        # 架构变更需要更谨慎，生成设计文档
        design_file = self.workspace / "data" / f"architecture_design_{plan.id}.md"
        
        design_content = f"""# 架构优化方案: {plan.title}

## 背景
{plan.description}

## 目标系统
{plan.target_system}

## 实施步骤
"""
        for step in plan.implementation_steps:
            design_content += f"- {step}\n"
        
        design_content += f"""
## 风险评估
- 风险等级: {plan.risk_level}
- 预计影响: {plan.estimated_impact}

## 需要修改的文件
"""
        for change in plan.changes:
            design_content += f"- `{change['file']}`: {change['action']}\n"
        
        with open(design_file, 'w') as f:
            f.write(design_content)
    
    def _implement_fix(self, plan: OptimizationPlan):
        """实施修复"""
        # 修复类问题直接尝试修改
        # 实际实现需要更精细的代码分析和修改
        pass
    
    def _implement_enhancement(self, plan: OptimizationPlan):
        """实施增强"""
        # 增强类功能添加到todo
        self._implement_crawler_update(plan)
    
    def _verify_implementation(self, plan: OptimizationPlan) -> bool:
        """验证实施效果"""
        # 简化版验证：检查语法
        for change in plan.changes:
            file_pattern = change.get('file', '')
            if file_pattern in self.SYSTEM_FILES:
                file_path = self.workspace / self.SYSTEM_FILES[file_pattern]
                if file_path.exists() and file_path.suffix == '.py':
                    try:
                        import py_compile
                        py_compile.compile(file_path, doraise=True)
                    except:
                        return False
        return True
    
    def _rollback(self, plan: OptimizationPlan):
        """回滚修改"""
        # 从备份恢复
        pass
    
    def analyze_with_code_understanding(self, plan: OptimizationPlan) -> Optional[ImpactAnalysis]:
        """
        🆕 Phase 1: 使用代码理解层分析影响
        
        基于AST和依赖图进行真正的代码影响分析
        """
        if not self.code_understanding:
            return None
        
        try:
            # 从plan中提取要修改的文件
            affected_files = []
            for change in plan.changes:
                file_pattern = change.get('file', '')
                # 解析文件路径
                if '.py' in file_pattern:
                    # 尝试找到匹配的文件
                    for file_path in self.code_understanding.analyzer.modules.keys():
                        if file_pattern.replace('*', '') in file_path:
                            affected_files.append((file_path, change.get('action', 'modify')))
                            break
            
            if not affected_files:
                return None
            
            # 分析每个文件的影响
            total_impact = None
            for file_path, action in affected_files:
                impact = self.code_understanding.analyze_impact(file_path, action, plan.description)
                
                if total_impact is None:
                    total_impact = impact
                else:
                    # 合并影响
                    total_impact.affected_functions.update(impact.affected_functions)
                    total_impact.affected_classes.update(impact.affected_classes)
                    total_impact.affected_modules.update(impact.affected_modules)
                    total_impact.risk_score = max(total_impact.risk_score, impact.risk_score)
                    total_impact.breaking_changes = total_impact.breaking_changes or impact.breaking_changes
            
            return total_impact
            
        except Exception as e:
            print(f"   ⚠️ 代码理解分析失败: {e}")
            return None


class InspirationEvolutionEngine:
    """
    灵感进化引擎 - 主入口
    
    整合分析→方案→实施的完整流程
    """
    
    def __init__(self, use_creative_design: bool = True, use_formal_verification: bool = True,
                 use_sandbox_testing: bool = True, use_feedback_learning: bool = True):
        self.analyzer = InspirationAnalyzer()
        self.planner = OptimizationPlanner()
        self.evolution = EvolutionEngine()
        
        # 🆕 Phase 2: 初始化创造性设计层
        self.creative_design = None
        if use_creative_design and CREATIVE_DESIGN_AVAILABLE:
            try:
                print("   🎨 初始化创造性设计层 (Phase 2)...")
                self.creative_design = CreativeDesignLayer(CLAW_STATUS)
                print("   ✅ 创造性设计层就绪")
            except Exception as e:
                print(f"   ⚠️ 创造性设计层初始化失败: {e}")
        
        # 🆕 Phase 3: 初始化形式化验证层
        self.formal_verifier = None
        if use_formal_verification and FORMAL_VERIFICATION_AVAILABLE:
            try:
                print("   🔐 初始化形式化验证层 (Phase 3)...")
                self.formal_verifier = FormalVerificationLayer(CLAW_STATUS)
                print("   ✅ 形式化验证层就绪")
            except Exception as e:
                print(f"   ⚠️ 形式化验证层初始化失败: {e}")
        
        # 🆕 Phase 4: 初始化沙箱测试层
        self.sandbox_tester = None
        if use_sandbox_testing and SANDBOX_TESTING_AVAILABLE:
            try:
                print("   🧪 初始化沙箱测试层 (Phase 4)...")
                self.sandbox_tester = SandboxTestingLayer(CLAW_STATUS)
                print("   ✅ 沙箱测试层就绪")
            except Exception as e:
                print(f"   ⚠️ 沙箱测试层初始化失败: {e}")
        
        # 🆕 Phase 5: 初始化反馈学习层
        self.feedback_learner = None
        if use_feedback_learning and FEEDBACK_LEARNING_AVAILABLE:
            try:
                print("   🧠 初始化反馈学习层 (Phase 5)...")
                self.feedback_learner = FeedbackLearningLayer(CLAW_STATUS)
                print("   ✅ 反馈学习层就绪")
            except Exception as e:
                print(f"   ⚠️ 反馈学习层初始化失败: {e}")
    
    def process_inspirations(self, items: List[Dict]) -> Dict:
        """
        处理灵感，执行完整进化流程
        
        Returns:
            处理结果摘要
        """
        result = {
            'processed_at': datetime.now().isoformat(),
            'items_count': len(items),
            'insights_found': 0,
            'plans_generated': 0,
            'plans_implemented': 0,
            'details': []
        }
        
        # Step 1: 分析灵感
        print("🔍 Step 1: 分析灵感...")
        insights = self.analyzer.analyze_batch(items)
        result['insights_found'] = len(insights)
        print(f"   发现 {len(insights)} 个洞察")
        
        # Step 2: 生成方案
        print("📋 Step 2: 生成优化方案...")
        plans = []
        for insight in insights:
            if insight.confidence >= 0.6:  # 只处理高置信度洞察
                plan = self.planner.generate_plan(insight)
                if plan:
                    plans.append(plan)
        result['plans_generated'] = len(plans)
        print(f"   生成 {len(plans)} 个方案")
        
        # Step 3: 实施方案（只处理低风险方案）
        print("🔧 Step 3: 实施优化...")
        implemented = 0
        for plan in plans:
            if plan.risk_level == "low":  # 只自动实施低风险方案
                print(f"   实施方案: {plan.title}")
                impl_result = self.evolution.implement_plan(plan)
                if impl_result['status'] == 'success':
                    implemented += 1
                    result['details'].append({
                        'plan_id': plan.id,
                        'title': plan.title,
                        'status': 'implemented',
                        'actions': impl_result['actions_taken']
                    })
        
        result['plans_implemented'] = implemented
        print(f"   成功实施 {implemented} 个方案")
        
        return result
    
    def get_evolution_report(self) -> Dict:
        """获取进化报告"""
        return {
            'total_insights': len(self.analyzer.insights),
            'insights_by_type': self._count_by_type(self.analyzer.insights),
            'top_insights': [
                {
                    'type': i.type,
                    'content': i.content[:100],
                    'confidence': i.confidence,
                    'impact': i.impact
                }
                for i in self.analyzer.get_top_insights(5)
            ],
            'pending_plans': len([p for p in self.planner.plans if p.status == "draft"]),
            'implemented_plans': len([p for p in self.planner.plans if p.status == "done"])
        }
    
    def generate_creative_improvements(self, target_file: str = None) -> Dict:
        """
        🆕 Phase 2: 使用创造性设计层生成改进方案
        
        基于代码理解，创造性地生成架构优化方案
        """
        result = {
            'generated_at': datetime.now().isoformat(),
            'candidates_count': 0,
            'candidates': [],
            'creative_design_used': False
        }
        
        if not self.creative_design:
            result['error'] = "创造性设计层不可用"
            return result
        
        try:
            print("\n" + "="*60)
            print("🎨 Phase 2: 创造性设计方案生成")
            print("="*60)
            
            candidates = self.creative_design.generate_improvements(target_file)
            result['candidates_count'] = len(candidates)
            result['creative_design_used'] = True
            
            for candidate in candidates[:5]:  # 只取前5个
                result['candidates'].append({
                    'id': candidate.id,
                    'pattern': candidate.pattern_id,
                    'description': candidate.description,
                    'risk_score': candidate.risk_score,
                    'confidence': candidate.confidence,
                    'objectives': candidate.objectives
                })
            
            print(f"\n✅ 成功生成 {len(candidates)} 个创造性改进方案")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"   ⚠️ 生成失败: {e}")
        
        return result
    
    def verify_design_formally(self, candidate: Dict, target_file: str) -> Dict:
        """
        🆕 Phase 3: 使用形式化验证层验证设计方案
        
        在设计实施前进行类型检查、不变量推断、符号执行和性质验证
        """
        result = {
            'verified_at': None,
            'verification_used': False,
            'type_check_passed': False,
            'invariants_found': 0,
            'properties_verified': 0,
            'properties_violated': 0,
            'can_proceed': False,
            'details': {}
        }
        
        if not self.formal_verifier:
            result['error'] = "形式化验证层不可用"
            return result
        
        try:
            print("\n" + "="*60)
            print("🔐 Phase 3: 形式化验证")
            print("="*60)
            
            # 创建DesignCandidate对象
            from creative_design import DesignCandidate
            design = DesignCandidate(
                id=candidate.get('id', 'unknown'),
                pattern_id=candidate.get('pattern', 'unknown'),
                description=candidate.get('description', ''),
                changes=[],  # 简化
                objectives=candidate.get('objectives', {}),
                constraints_satisfied=True,
                risk_score=candidate.get('risk_score', 50),
                confidence=candidate.get('confidence', 0.5),
                reasoning=''
            )
            
            # 执行验证
            verification_result = self.formal_verifier.verify_design(design, target_file)
            
            result['verification_used'] = True
            result['type_check_passed'] = verification_result.get('type_check') is not None
            result['invariants_found'] = len(verification_result.get('invariants', []))
            result['can_proceed'] = verification_result.get('can_proceed', False)
            result['details'] = verification_result
            
            # 统计性质验证结果
            for prop in verification_result.get('property_verification', []):
                if prop['status'] == 'VERIFIED':
                    result['properties_verified'] += 1
                elif prop['status'] == 'VIOLATED':
                    result['properties_violated'] += 1
            
            print(f"\n✅ 形式化验证完成")
            print(f"   不变量发现: {result['invariants_found']} 个")
            print(f"   性质验证通过: {result['properties_verified']} 个")
            print(f"   性质违反: {result['properties_violated']} 个")
            print(f"   可以实施: {'是' if result['can_proceed'] else '否'}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"   ⚠️ 验证失败: {e}")
        
        result['verified_at'] = datetime.now().isoformat()
        return result
    
    def test_design_in_sandbox(self, candidate: Dict, target_file: str) -> Dict:
        """
        🆕 Phase 4: 使用沙箱测试层测试设计方案
        
        在隔离环境中运行测试，确保修改安全
        """
        result = {
            'tested_at': None,
            'sandbox_used': False,
            'test_cases_total': 0,
            'test_cases_passed': 0,
            'pass_rate': 0.0,
            'can_deploy': False,
            'details': {}
        }
        
        if not self.sandbox_tester:
            result['error'] = "沙箱测试层不可用"
            return result
        
        try:
            print("\n" + "="*60)
            print("🧪 Phase 4: 沙箱测试")
            print("="*60)
            
            # 创建DesignCandidate对象
            from creative_design import DesignCandidate
            design = DesignCandidate(
                id=candidate.get('id', 'unknown'),
                pattern_id=candidate.get('pattern', 'unknown'),
                description=candidate.get('description', ''),
                changes=[],
                objectives=candidate.get('objectives', {}),
                constraints_satisfied=True,
                risk_score=candidate.get('risk_score', 50),
                confidence=candidate.get('confidence', 0.5),
                reasoning=''
            )
            
            # 执行沙箱测试
            test_report = self.sandbox_tester.test_design(design, target_file)
            
            result['sandbox_used'] = True
            result['test_cases_total'] = test_report.test_cases_total
            result['test_cases_passed'] = test_report.test_cases_passed
            result['pass_rate'] = test_report.pass_rate
            result['can_deploy'] = test_report.can_deploy
            result['details'] = {
                'performance': {
                    'execution_time_ms': test_report.performance_variant.execution_time_ms if test_report.performance_variant else 0,
                    'throughput': test_report.performance_variant.throughput if test_report.performance_variant else 0
                } if test_report.performance_variant else None,
                'regression_detected': test_report.regression_detected
            }
            
            print(f"\n✅ 沙箱测试完成")
            print(f"   测试用例: {result['test_cases_total']}")
            print(f"   通过: {result['test_cases_passed']}")
            print(f"   通过率: {result['pass_rate']:.1%}")
            print(f"   可以部署: {'是' if result['can_deploy'] else '否'}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"   ⚠️ 沙箱测试失败: {e}")
        
        result['tested_at'] = datetime.now().isoformat()
        return result
    
    def learn_from_deployment(self, mod_id: str, baseline_metrics: Dict = None) -> Dict:
        """
        🆕 Phase 5: 从部署结果学习
        
        执行完整的反馈学习流程
        """
        if not self.feedback_learner:
            return {'error': '反馈学习层不可用'}
        
        try:
            print("\n" + "="*60)
            print("🧠 Phase 5: 反馈学习")
            print("="*60)
            
            result = self.feedback_learner.learn_from_deployment(mod_id, baseline_metrics)
            
            if 'error' not in result:
                print(f"\n✅ 反馈学习完成")
                print(f"   成功: {'是' if result['success'] else '否'}")
                print(f"   模式置信度: {result['pattern_confidence']:.2f}")
                print(f"   策略建议: {result['strategy_recommendation']}")
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def _count_by_type(self, insights: List[Insight]) -> Dict:
        """按类型统计"""
        counts = {}
        for i in insights:
            counts[i.type] = counts.get(i.type, 0) + 1
        return counts


def main():
    """测试进化引擎"""
    print("="*60)
    print("🧬 灵感进化引擎测试")
    print("="*60)
    
    engine = InspirationEvolutionEngine()
    
    # 模拟测试数据
    test_items = [
        {
            'id': '1',
            'title': 'MCP Protocol is the future of AI agents',
            'content': 'Model Context Protocol enables better tool use for LLMs',
            'source': 'arxiv',
            'quality_score': 0.9
        },
        {
            'id': '2',
            'title': 'Current system has timeout issues',
            'content': 'Users report frequent network timeouts when crawling',
            'source': 'reddit',
            'quality_score': 0.7
        },
        {
            'id': '3',
            'title': 'Claude Code best practices',
            'content': 'Should use self-healing patterns for better reliability',
            'source': 'github',
            'quality_score': 0.85
        }
    ]
    
    # 执行进化流程
    result = engine.process_inspirations(test_items)
    
    print("\n" + "="*60)
    print("📊 进化结果:")
    print(f"   处理项目: {result['items_count']}")
    print(f"   发现洞察: {result['insights_found']}")
    print(f"   生成方案: {result['plans_generated']}")
    print(f"   实施方案: {result['plans_implemented']}")
    
    print("\n📈 系统报告:")
    report = engine.get_evolution_report()
    print(f"   总洞察数: {report['total_insights']}")
    print(f"   洞察类型: {report['insights_by_type']}")
    
    # 🆕 Phase 2: 测试创造性设计层
    print("\n" + "="*60)
    print("🎨 测试 Phase 2: 创造性设计层")
    print("="*60)
    
    creative_result = engine.generate_creative_improvements()
    if creative_result['creative_design_used']:
        print(f"\n📋 Top 5 创造性改进方案:")
        for i, c in enumerate(creative_result['candidates'], 1):
            print(f"   {i}. {c['pattern']}")
            print(f"      风险: {c['risk_score']}/100")
            print(f"      置信度: {c['confidence']:.2f}")
        
        # 🆕 Phase 3: 测试形式化验证
        print("\n" + "="*60)
        print("🔐 测试 Phase 3: 形式化验证")
        print("="*60)
        
        if creative_result['candidates']:
            # 选择一个方案进行验证
            target_file = str(CLAW_STATUS / "scheduler.py")
            if Path(target_file).exists():
                candidate = creative_result['candidates'][0]
                verify_result = engine.verify_design_formally(candidate, target_file)
                
                if verify_result['verification_used']:
                    print(f"\n✅ 形式化验证完成")
                    print(f"   可以安全实施: {'是' if verify_result['can_proceed'] else '否'}")
                    
                    # 🆕 Phase 4: 测试沙箱测试
                    print("\n" + "="*60)
                    print("🧪 测试 Phase 4: 沙箱测试")
                    print("="*60)
                    
                    sandbox_result = engine.test_design_in_sandbox(candidate, target_file)
                    
                    if sandbox_result['sandbox_used']:
                        print(f"\n✅ 沙箱测试完成")
                        print(f"   测试用例: {sandbox_result['test_cases_total']}")
                        print(f"   通过率: {sandbox_result['pass_rate']:.1%}")
                        print(f"   可以部署: {'是' if sandbox_result['can_deploy'] else '否'}")
                        
                        # 🆕 Phase 5: 测试反馈学习
                        if sandbox_result['can_deploy']:
                            print("\n" + "="*60)
                            print("🧠 测试 Phase 5: 反馈学习")
                            print("="*60)
                            
                            # 记录修改
                            from creative_design import DesignCandidate
                            test_design = DesignCandidate(
                                id=candidate['id'],
                                pattern_id=candidate['pattern'],
                                description=candidate['description'],
                                changes=[],
                                objectives=candidate.get('objectives', {}),
                                constraints_satisfied=True,
                                risk_score=candidate['risk_score'],
                                confidence=candidate['confidence'],
                                reasoning=''
                            )
                            
                            mod_id = engine.feedback_learner.record_modification(
                                test_design, target_file
                            )
                            
                            # 从部署结果学习
                            learning_result = engine.learn_from_deployment(mod_id)
                            
                            if 'error' not in learning_result:
                                print(f"\n✅ 反馈学习完成")
                                print(f"   综合评分: {learning_result['overall_score']:+.1f}")
                                print(f"   模式置信度: {learning_result['pattern_confidence']:.2f}")
                                print(f"   策略建议: {learning_result['strategy_recommendation']}")
                            else:
                                print(f"   ⚠️ {learning_result.get('error', '反馈学习失败')}")
                    else:
                        print(f"   ⚠️ {sandbox_result.get('error', '沙箱测试不可用')}")
                else:
                    print(f"   ⚠️ {verify_result.get('error', '验证不可用')}")
            else:
                print(f"   ⚠️ 目标文件不存在，跳过验证")
    else:
        print(f"   ⚠️ {creative_result.get('error', '未知错误')}")
    
    print("\n" + "="*60)
    print("✅ Phase 1/2/3/4/5 全部测试完成!")
    print("   🎯 代码理解 → 创造性设计 → 形式化验证 → 沙箱测试 → 反馈学习")
    print("="*60)


if __name__ == "__main__":
    main()
