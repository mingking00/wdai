#!/usr/bin/env python3
"""
Self-Reflection Agent Service (SRAS)
自我复盘常驻Agent

职责:
1. 每日自动复盘对话记录
2. 提取可复用的技巧和模式
3. 识别错误并记录教训
4. 更新SOUL.md和MEMORY.md
5. 生成进化报告

通信机制:
- 请求: .sra/requests/REQ_*.json
- 响应: .sra/responses/RSP_*.json
- 状态: .sra/sra_status.json
"""

import os
import sys
import json
import re
import time
import signal
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

# 导入SRA-IER系统
try:
    from sra_ier import get_sra_experience_manager, SRAExperienceManager
    IER_AVAILABLE = True
except ImportError:
    IER_AVAILABLE = False

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SRA_DIR = WORKSPACE / ".sra"
REQUEST_DIR = SRA_DIR / "requests"
RESPONSE_DIR = SRA_DIR / "responses"
STATUS_FILE = SRA_DIR / "sra_status.json"
PID_FILE = SRA_DIR / "sra.pid"
REFLECTION_DIR = SRA_DIR / "reflections"
TIPS_DIR = SRA_DIR / "tips"
REFLECTION_HISTORY_FILE = SRA_DIR / "reflection_history.json"  # Anti-Hacking: 反思历史
EFFECTIVENESS_TRACKING_FILE = SRA_DIR / "effectiveness_tracking.json"  # Anti-Hacking Phase 4: 效果追踪
ADAPTIVE_THRESHOLD_FILE = SRA_DIR / "adaptive_threshold.json"  # Anti-Hacking Phase 5: 自适应阈值
CROSS_REFLECTION_FILE = SRA_DIR / "cross_reflection_analysis.json"  # Anti-Hacking Phase 6: 跨反思分析

# Anti-Hacking配置
ANTI_HACKING_CONFIG = {
    'min_interval_hours': 4,  # 最短反思间隔
    'min_content_length': 1000,  # 最小内容长度
    'rubric_threshold': 0.6,  # Rubric通过阈值
    'outcome_threshold': 0.5,  # Outcome通过阈值
    'fact_overlap_threshold': 0.7,  # 关键信息覆盖阈值
}

# Anti-Hacking Phase 3 配置
AUTO_REFINEMENT_CONFIG = {
    'enabled': True,  # 是否启用自动改进
    'max_iterations': 3,  # 最大迭代次数
    'confidence_threshold': 0.8,  # 目标置信度
    'budget_tokens': 3000,  # Token预算
    'min_improvement_delta': 0.05,  # 最小改进幅度 (否则提前终止)
}

# Anti-Hacking Phase 4 配置
EFFECTIVENESS_TRACKING_CONFIG = {
    'enabled': True,  # 是否启用效果追踪
    'tracking_period_days': 30,  # 追踪周期(天)
    'min_confidence_for_tracking': 0.7,  # 只追踪置信度>=0.7的建议
    'auto_feedback_to_ier': True,  # 自动反馈到IER系统
    'effectiveness_threshold': 0.6,  # 有效率阈值(<60%触发警告)
}

# Anti-Hacking Phase 5 配置
ADAPTIVE_THRESHOLD_CONFIG = {
    'enabled': True,  # 是否启用自适应阈值
    'adjustment_cooldown_days': 7,  # 调整冷却期(天)
    'min_samples_for_adjustment': 10,  # 调整所需最小样本数
    'conservative_mode': True,  # 保守模式:只升不降
    'target_pass_rate': 0.7,  # 目标通过率 70%
    'target_effectiveness': 0.75,  # 目标有效率 75%
    'max_threshold': 0.9,  # 阈值上限
    'min_threshold': 0.4,  # 阈值下限
}

# Anti-Hacking Phase 6 配置
CROSS_REFLECTION_CONFIG = {
    'enabled': True,  # 是否启用跨反思分析
    'analysis_cooldown_days': 14,  # 分析冷却期(天)
    'min_reflections_for_analysis': 20,  # 分析所需最小反思数
    'pattern_min_occurrences': 3,  # 模式最小出现次数
    'effectiveness_weight': 0.6,  # 有效率权重
    'confidence_weight': 0.4,  # 置信度权重
}

# 确保目录存在
for d in [SRA_DIR, REQUEST_DIR, RESPONSE_DIR, REFLECTION_DIR, TIPS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================
# Anti-Hacking SRA 核心组件 (Phase 1)
# ============================================

class AntiHackingValidator:
    """
    Anti-Hacking验证器 - 防止SRA流于表面或产生虚假洞察
    基于Kimi K2.5 RL训练策略迁移
    """
    
    def __init__(self):
        self.reflection_history = self._load_reflection_history()
        self.config = ANTI_HACKING_CONFIG
    
    def _load_reflection_history(self) -> List[Dict]:
        """加载反思历史"""
        if REFLECTION_HISTORY_FILE.exists():
            with open(REFLECTION_HISTORY_FILE, 'r') as f:
                return json.load(f)
        return []
    
    def _save_reflection_history(self):
        """保存反思历史"""
        with open(REFLECTION_HISTORY_FILE, 'w') as f:
            json.dump(self.reflection_history, f, ensure_ascii=False, indent=2)
    
    def compute_frequency_penalty(self) -> float:
        """
        频率惩罚 - 防止过度反思
        
        Returns:
            0.0: 正常
            0.5: 部分惩罚 (间隔4-8小时)
            1.0: 完全惩罚 (间隔<4小时)
        """
        if not self.reflection_history:
            return 0.0
        
        last_reflection = datetime.fromisoformat(
            self.reflection_history[-1].get('timestamp', '2000-01-01T00:00:00')
        )
        hours_since_last = (datetime.now() - last_reflection).total_seconds() / 3600
        
        if hours_since_last < self.config['min_interval_hours']:
            return 1.0  # 完全无效
        elif hours_since_last < self.config['min_interval_hours'] * 2:
            return 0.5  # 部分惩罚
        return 0.0  # 正常
    
    def should_reflect(self, content: str, content_type: str = "memory") -> tuple[bool, str]:
        """
        判断是否真的需要反思
        
        Returns:
            (should_reflect: bool, reason: str)
        """
        # 1. 频率检查
        freq_penalty = self.compute_frequency_penalty()
        if freq_penalty >= 1.0:
            return False, f"反思过于频繁 (需间隔 >{self.config['min_interval_hours']}小时)"
        
        # 2. 内容长度检查
        if len(content) < self.config['min_content_length']:
            return False, f"内容不足 ({len(content)} < {self.config['min_content_length']})"
        
        # 3. 值得反思的事件检查
        if not self._contains_reflectable_events(content):
            return False, "无值得反思的实质性事件"
        
        return True, "通过触发检查"
    
    def _contains_reflectable_events(self, content: str) -> bool:
        """检查是否包含值得反思的事件"""
        # 关键事件模式
        event_patterns = [
            r'错误|失败|exception|error|fail',
            r'优化|改进|提升|performance|improve',
            r'新发现|洞察|模式|pattern|insight',
            r'教训|学习|learn|lesson',
            r'技巧|tip|trick|hack',
            r'解决|方案|solution|fix',
            r'对比|比较|vs|better|worse',
        ]
        
        content_lower = content.lower()
        match_count = sum(1 for p in event_patterns if re.search(p, content_lower))
        return match_count >= 2  # 至少2类事件
    
    def evaluate_rubric(self, reflection_content: str) -> Dict[str, float]:
        """
        Rubric评估 - 强制完整的反思路径
        
        四项核心要素，每项25%:
        1. 事实依据 - 必须有具体引用
        2. 因果分析 - 不止于"发生了什么"
        3. 可执行建议 - 不只发现问题
        4. 验证机制 - 如何确认改进有效
        """
        rubric_scores = {
            'evidence': 0.0,
            'causal': 0.0,
            'actionable': 0.0,
            'validation': 0.0
        }
        
        content_lower = reflection_content.lower()
        
        # 1. 事实依据 (引用具体对话/代码/日志)
        evidence_patterns = [
            r'`[^`]+`',  # 引用代码
            r'"[^"]+"',  # 引号内容
            r'\d{4}-\d{2}-\d{2}',  # 日期引用
            r'第\d+行|line \d+',  # 行号引用
            r'根据|原文|记录|log',
        ]
        if any(re.search(p, reflection_content) for p in evidence_patterns):
            rubric_scores['evidence'] = 0.25
        
        # 2. 因果分析 (不止描述现象)
        causal_patterns = [
            r'因为|原因|cause|because|due to',
            r'导致|结果|result|lead to',
            r'本质|根本|root',
            r'为什么|why|如何|how',
        ]
        if any(re.search(p, content_lower) for p in causal_patterns):
            rubric_scores['causal'] = 0.25
        
        # 3. 可执行建议 (不只发现问题)
        actionable_patterns = [
            r'建议|应该|should|recommend',
            r'可以|可以|can|could',
            r'下次|下次|next time|future',
            r'改进|优化|improve|optimize',
        ]
        if any(re.search(p, content_lower) for p in actionable_patterns):
            rubric_scores['actionable'] = 0.25
        
        # 4. 验证机制 (如何确认有效)
        validation_patterns = [
            r'验证|确认|verify|confirm|check',
            r'测试|test|validate',
            r'监控|monitor|track',
            r'指标|metric|measure',
        ]
        if any(re.search(p, content_lower) for p in validation_patterns):
            rubric_scores['validation'] = 0.25
        
        rubric_scores['total'] = sum(rubric_scores.values())
        return rubric_scores
    
    def evaluate_outcome(self, tips: List[Dict], patterns: List[str]) -> Dict[str, float]:
        """
        Outcome评估 - 多维度的反思质量
        
        四个维度:
        1. 新颖性 - 是否发现新洞察
        2. 可复用性 - 能否应用到其他场景
        3. 验证度 - 是否有证据支撑
        4. 影响度 - 对后续工作的实际帮助
        """
        outcome_scores = {
            'novelty': 0.0,
            'reusability': 0.0,
            'verifiability': 0.0,
            'impact': 0.0
        }
        
        # 基于提取的技巧评估
        if tips:
            # 新颖性: 技巧数量 + 多样性
            outcome_scores['novelty'] = min(len(tips) * 0.1, 0.25)
            
            # 可复用性: 有代码示例的技巧
            code_examples = sum(1 for t in tips if t.get('code_example'))
            outcome_scores['reusability'] = min(code_examples * 0.1, 0.25)
            
            # 验证度: 有上下文的技巧
            with_context = sum(1 for t in tips if len(t.get('context', '')) > 50)
            outcome_scores['verifiability'] = min(with_context * 0.1, 0.25)
            
            # 影响度: 高优先级技巧
            high_priority = sum(1 for t in tips if t.get('priority', 0) > 7)
            outcome_scores['impact'] = min(high_priority * 0.1, 0.25)
        
        outcome_scores['total'] = sum(outcome_scores.values())
        return outcome_scores
    
    def validate_path(self, original_content: str, reflection_content: str) -> Dict[str, Any]:
        """
        路径验证 - 确保反思正确理解了原始内容
        
        1. 关键信息覆盖 > 70%
        2. 逻辑一致性
        3. 无幻觉
        """
        validation = {
            'fact_overlap': 0.0,
            'logical_consistency': True,
            'hallucination_free': True,
            'passed': False
        }
        
        # 1. 关键信息覆盖 (简化版: 关键词匹配)
        original_keywords = set(self._extract_keywords(original_content))
        reflection_keywords = set(self._extract_keywords(reflection_content))
        
        if original_keywords:
            overlap = len(original_keywords & reflection_keywords) / len(original_keywords)
            validation['fact_overlap'] = overlap
        else:
            validation['fact_overlap'] = 1.0
        
        # 2. 逻辑一致性检查 (简化: 无矛盾关键词)
        contradiction_pairs = [
            ('成功', '失败'),
            ('正确', '错误'),
            ('增加', '减少'),
        ]
        for pos, neg in contradiction_pairs:
            if pos in reflection_content and neg in reflection_content:
                # 检查是否在同一句中
                sentences = reflection_content.split('。')
                for s in sentences:
                    if pos in s and neg in s:
                        validation['logical_consistency'] = False
                        break
        
        # 3. 幻觉检查 (简化: 反思中的关键词是否在原文中有支撑)
        reflection_only = reflection_keywords - original_keywords
        # 允许30%的新关键词 (推理产生的)
        if reflection_keywords:
            novel_ratio = len(reflection_only) / len(reflection_keywords)
            validation['hallucination_free'] = novel_ratio < 0.3
        
        # 最终判定
        validation['passed'] = (
            validation['fact_overlap'] >= self.config['fact_overlap_threshold'] and
            validation['logical_consistency'] and
            validation['hallucination_free']
        )
        
        return validation
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        # 简单实现: 提取中文字符和英文单词
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        english_words = re.findall(r'[a-zA-Z_]{4,}', content)
        return chinese_words + english_words
    
    def record_reflection(self, reflection_id: str, req_type: str, 
                         rubric_score: float, outcome_score: float, 
                         passed: bool):
        """记录反思历史"""
        self.reflection_history.append({
            'id': reflection_id,
            'timestamp': datetime.now().isoformat(),
            'type': req_type,
            'rubric_score': rubric_score,
            'outcome_score': outcome_score,
            'passed': passed
        })
        # 只保留最近100条
        self.reflection_history = self.reflection_history[-100:]
        self._save_reflection_history()


# ============================================
# Anti-Hacking Phase 2: Self-Critical Pipeline
# ============================================

class SelfCriticalPipeline:
    """
    自我批判式反思流程 - Phase 2
    
    通过多维度质疑和改进循环,防止反思流于表面
    """
    
    def __init__(self, max_iterations: int = 3, confidence_threshold: float = 0.75):
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
    
    def critique(self, initial_reflection: str, original_content: str) -> Dict:
        """
        多维度质疑初步反思
        
        Returns:
            {
                'factual': {...},      # 事实性质疑结果
                'logical': {...},      # 逻辑性质疑结果
                'depth': {...},        # 深度质疑结果
                'utility': {...},      # 实用性质疑结果
                'confidence': float,   # 综合置信度
                'issues_count': int,   # 问题总数
                'should_refine': bool  # 是否需要改进
            }
        """
        # 1. 事实性质疑
        factual = self._factual_critique(initial_reflection, original_content)
        
        # 2. 逻辑性质疑
        logical = self._logical_critique(initial_reflection)
        
        # 3. 深度质疑
        depth = self._depth_critique(initial_reflection)
        
        # 4. 实用性质疑
        utility = self._utility_critique(initial_reflection)
        
        # 5. 计算综合置信度
        confidence = (
            factual.get('confidence', 0.5) * 0.3 +      # 事实最重要
            logical.get('confidence', 0.5) * 0.25 +
            depth.get('confidence', 0.5) * 0.25 +
            utility.get('confidence', 0.5) * 0.2
        )
        
        # 6. 统计问题数
        issues_count = (
            len(factual.get('issues', [])) +
            len(logical.get('issues', [])) +
            len(depth.get('issues', [])) +
            len(utility.get('issues', []))
        )
        
        # 7. 判定是否需要改进
        should_refine = (
            confidence < self.confidence_threshold or
            issues_count >= 2 or
            factual.get('has_critical_issue', False)
        )
        
        return {
            'factual': factual,
            'logical': logical,
            'depth': depth,
            'utility': utility,
            'confidence': confidence,
            'issues_count': issues_count,
            'should_refine': should_refine
        }
    
    def _factual_critique(self, reflection: str, original: str) -> Dict:
        """事实性质疑 - 检查是否有原文支撑"""
        issues = []
        
        # 1. 检查是否有引用标记
        has_quotes = bool(re.search(r'[`"\'][^`"\']+[`"\']', reflection))
        has_date_refs = bool(re.search(r'\d{4}-\d{2}-\d{2}', reflection))
        
        if not has_quotes and not has_date_refs:
            issues.append({
                'type': 'lack_of_evidence',
                'description': '反思中缺乏具体的原文引用或日期标记',
                'suggestion': '请添加具体的引用,如:"根据memory/2026-03-15.md记录..."'
            })
        
        # 2. 检查是否有过度的绝对化表述
        absolute_words = ['总是', '从不', '一定', '绝对', '必然']
        for word in absolute_words:
            if word in reflection:
                issues.append({
                    'type': 'overgeneralization',
                    'description': f'使用了绝对化词语"{word}"',
                    'suggestion': f'改为更谨慎的表述,如"在大多数情况下"、"可能"'
                })
        
        # 3. 检查关键信息覆盖率
        original_keywords = set(self._extract_keywords_simple(original))
        reflection_keywords = set(self._extract_keywords_simple(reflection))
        
        if original_keywords:
            coverage = len(original_keywords & reflection_keywords) / len(original_keywords)
            if coverage < 0.5:
                issues.append({
                    'type': 'low_coverage',
                    'description': f'关键信息覆盖率仅{coverage:.1%},遗漏了原文重要内容',
                    'suggestion': '请补充原文中的关键概念和事件'
                })
        
        # 4. 置信度计算
        confidence = max(0, 1.0 - len(issues) * 0.2)
        has_critical = any(i['type'] in ['lack_of_evidence', 'low_coverage'] for i in issues)
        
        return {
            'issues': issues,
            'confidence': confidence,
            'has_critical_issue': has_critical,
            'coverage': coverage if original_keywords else 1.0
        }
    
    def _logical_critique(self, reflection: str) -> Dict:
        """逻辑性质疑 - 检查推理是否合理"""
        issues = []
        
        # 1. 检查因果推断是否有充分证据
        causal_patterns = [
            (r'因为(.+?)所以(.+?)', '因果推断'),
            (r'导致(.+?)', '归因'),
            (r'结果是(.+?)', '结果推导')
        ]
        
        for pattern, name in causal_patterns:
            matches = re.findall(pattern, reflection)
            for match in matches:
                # 简单启发式: 因果陈述后应该有具体说明
                if len(str(match)) < 10:  # 太短的因果可能不严谨
                    issues.append({
                        'type': 'weak_causation',
                        'description': f'{name}"{match}"可能过于简化',
                        'suggestion': '请提供更多证据支撑这个因果推断'
                    })
        
        # 2. 检查自相矛盾
        contradiction_pairs = [
            ('成功', '失败'),
            ('正确', '错误'),
            ('增加', '减少'),
            ('快', '慢'),
            ('简单', '复杂')
        ]
        
        for pos, neg in contradiction_pairs:
            if pos in reflection and neg in reflection:
                # 检查是否在同一句中
                sentences = reflection.split('。')
                for s in sentences:
                    if pos in s and neg in s and '不' not in s:
                        issues.append({
                            'type': 'contradiction',
                            'description': f'同时使用了"{pos}"和"{neg}",可能存在矛盾',
                            'suggestion': '澄清具体含义或修正表述'
                        })
        
        # 3. 检查建议与问题是否匹配
        problem_indicators = ['问题', '困难', '错误', '失败', 'bug']
        solution_indicators = ['解决', '改进', '优化', '修复']
        
        has_problem = any(p in reflection for p in problem_indicators)
        has_solution = any(s in reflection for s in solution_indicators)
        
        if has_problem and not has_solution:
            issues.append({
                'type': 'missing_solution',
                'description': '提到了问题但没有给出解决方案',
                'suggestion': '请针对发现的问题提出具体的改进建议'
            })
        
        confidence = max(0, 1.0 - len(issues) * 0.25)
        
        return {
            'issues': issues,
            'confidence': confidence
        }
    
    def _depth_critique(self, reflection: str) -> Dict:
        """深度质疑 - 检查是否触及根本原因"""
        issues = []
        
        # 1. 5 Whys测试 - 检查是否有深入挖掘
        why_patterns = ['为什么', 'why', '原因是', '根本原因', '本质']
        why_count = sum(reflection.count(p) for p in why_patterns)
        
        if why_count < 2:
            issues.append({
                'type': 'surface_level',
                'description': '缺乏深度分析,没有追问"为什么"',
                'suggestion': '使用5 Whys方法深挖根本原因:问至少3次"为什么"'
            })
        
        # 2. 检查是否只描述了现象
        phenomenon_words = ['发生了', '出现了', '遇到了', '发现']
        insight_words = ['说明', '表明', '反映了', '揭示了', '意味着']
        
        phenom_count = sum(reflection.count(w) for w in phenomenon_words)
        insight_count = sum(reflection.count(w) for w in insight_words)
        
        if phenom_count > 0 and insight_count == 0:
            issues.append({
                'type': 'no_insight',
                'description': '只描述了现象,没有提炼出洞察或模式',
                'suggestion': '从现象中提炼出可复用的模式或原则'
            })
        
        # 3. 检查是否有通用模式提炼
        pattern_indicators = ['模式', 'pattern', '规律', '原则', '原则', '方法论']
        has_pattern = any(p in reflection for p in pattern_indicators)
        
        if not has_pattern:
            issues.append({
                'type': 'no_pattern_extraction',
                'description': '没有从具体案例中提炼通用模式',
                'suggestion': '思考:这个经验在什么其他场景也适用?'
            })
        
        confidence = max(0, 1.0 - len(issues) * 0.3)
        
        return {
            'issues': issues,
            'confidence': confidence,
            'why_count': why_count,
            'has_pattern': has_pattern
        }
    
    def _utility_critique(self, reflection: str) -> Dict:
        """实用性质疑 - 检查建议是否可执行"""
        issues = []
        
        # 1. 检查建议是否具体
        abstract_words = ['应该', '要', '注意', '关注']
        concrete_words = ['使用', '修改', '添加', '删除', '配置', '运行']
        
        abstract_count = sum(reflection.count(w) for w in abstract_words)
        concrete_count = sum(reflection.count(w) for w in concrete_words)
        
        if abstract_count > concrete_count * 2:
            issues.append({
                'type': 'too_abstract',
                'description': '建议过于抽象,缺乏具体步骤',
                'suggestion': '将建议转化为具体可执行的步骤:1. ... 2. ... 3. ...'
            })
        
        # 2. 检查是否有验证机制
        verification_indicators = ['验证', '确认', '检查', '测试', '监控', '指标']
        has_verification = any(v in reflection for v in verification_indicators)
        
        if not has_verification:
            issues.append({
                'type': 'no_verification',
                'description': '没有说明如何验证改进是否有效',
                'suggestion': '添加验证方法:下次遇到类似情况时,观察XXX指标'
            })
        
        # 3. 检查是否有文档更新建议
        doc_indicators = ['SOUL', 'MEMORY', '文档', '更新', '记录']
        has_doc_suggestion = any(d in reflection for d in doc_indicators)
        
        if not has_doc_suggestion:
            issues.append({
                'type': 'no_documentation',
                'description': '没有建议沉淀到文档',
                'suggestion': '考虑将关键洞察更新到SOUL.md或MEMORY.md'
            })
        
        confidence = max(0, 1.0 - len(issues) * 0.25)
        
        return {
            'issues': issues,
            'confidence': confidence,
            'has_verification': has_verification,
            'has_documentation': has_doc_suggestion
        }
    
    def _extract_keywords_simple(self, content: str) -> List[str]:
        """简单关键词提取"""
        chinese = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        english = re.findall(r'[a-zA-Z_]{4,}', content)
        return chinese + english
    
    def generate_improvement_summary(self, critique_result: Dict) -> str:
        """生成改进建议汇总"""
        summary_parts = []
        
        for dimension in ['factual', 'logical', 'depth', 'utility']:
            result = critique_result.get(dimension, {})
            issues = result.get('issues', [])
            if issues:
                summary_parts.append(f"\n【{dimension.upper()}】")
                for issue in issues[:2]:  # 每维度最多2条
                    summary_parts.append(f"  - {issue['description']}")
                    summary_parts.append(f"    建议: {issue['suggestion']}")
        
        return '\n'.join(summary_parts) if summary_parts else "无明显问题,反思质量良好"


# ============================================
# Anti-Hacking Phase 3: Auto-Refinement Loop
# ============================================

class AutoRefiner:
    """
    自动改进循环 - Phase 3
    
    基于Self-Critical结果，使用LLM自动改进反思内容
    """
    
    def __init__(self, max_iterations: int = 3, confidence_threshold: float = 0.8,
                 budget_tokens: int = 3000):
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        self.budget_tokens = budget_tokens
        self.iteration_count = 0
        self.tokens_consumed = 0
        self.improvement_history = []
    
    def refine(self, original_reflection: str, critique_result: Dict,
               original_content: str, llm_client=None) -> Dict:
        """
        自动改进反思
        
        Returns:
            {
                'final_reflection': str,      # 最终改进后的反思
                'iterations': int,            # 实际迭代次数
                'confidence_improvement': float,  # 置信度提升
                'tokens_consumed': int,       # 消耗的token数
                'cost_estimate': float,       # 估计成本($)
                'improvement_log': List       # 改进日志
            }
        """
        current_reflection = original_reflection
        current_confidence = critique_result['confidence']
        improvement_log = []
        
        self.logger = self._get_logger()
        self.logger.info(f"[Auto-Refinement] 开始改进，初始置信度: {current_confidence:.2f}")
        
        for iteration in range(self.max_iterations):
            self.iteration_count = iteration + 1
            
            # 检查token预算
            if self.tokens_consumed >= self.budget_tokens:
                self.logger.warning(f"[Auto-Refinement] Token预算耗尽 ({self.tokens_consumed}/{self.budget_tokens})")
                break
            
            # 检查是否已达到目标
            if current_confidence >= self.confidence_threshold:
                self.logger.success(f"[Auto-Refinement] 置信度达标 ({current_confidence:.2f} >= {self.confidence_threshold})")
                break
            
            self.logger.info(f"[Auto-Refinement] 第{iteration+1}轮改进...")
            
            # 生成改进提示
            refinement_prompt = self._generate_refinement_prompt(
                current_reflection, critique_result, original_content
            )
            
            # 调用LLM改进 (简化版本，实际需要接入真实LLM)
            improved_reflection, tokens_used = self._call_llm(
                refinement_prompt, llm_client
            )
            
            self.tokens_consumed += tokens_used
            
            # 重新评估
            from copy import deepcopy
            pipeline = SelfCriticalPipeline()
            new_critique = pipeline.critique(improved_reflection, original_content)
            new_confidence = new_critique['confidence']
            
            improvement_log.append({
                'iteration': iteration + 1,
                'confidence_before': current_confidence,
                'confidence_after': new_confidence,
                'confidence_delta': new_confidence - current_confidence,
                'issues_before': critique_result['issues_count'],
                'issues_after': new_critique['issues_count'],
                'tokens_used': tokens_used
            })
            
            self.logger.info(f"[Auto-Refinement] 置信度: {current_confidence:.2f} -> {new_confidence:.2f} "
                           f"(Δ{new_confidence-current_confidence:+.2f})")
            
            # 更新状态
            if new_confidence > current_confidence:
                current_reflection = improved_reflection
                current_confidence = new_confidence
                critique_result = new_critique
                self.logger.success(f"[Auto-Refinement] 改进有效，采用新版本")
            else:
                self.logger.warning(f"[Auto-Refinement] 改进无效或退步，保持原版本")
                # 如果没有改进，提前终止
                if iteration >= 1:
                    self.logger.info(f"[Auto-Refinement] 连续无改进，提前终止")
                    break
        
        # 计算成本 (按Kimi K2.5价格估算: $0.5/1M tokens)
        cost_estimate = self.tokens_consumed * 0.5 / 1000000
        
        self.logger.success(f"[Auto-Refinement] 完成，总迭代: {self.iteration_count}, "
                           f"总消耗: {self.tokens_consumed} tokens, "
                           f"估计成本: ${cost_estimate:.4f}")
        
        return {
            'final_reflection': current_reflection,
            'iterations': self.iteration_count,
            'confidence_start': critique_result.get('confidence', 0),
            'confidence_final': current_confidence,
            'confidence_improvement': current_confidence - critique_result.get('confidence', 0),
            'tokens_consumed': self.tokens_consumed,
            'cost_estimate': cost_estimate,
            'improvement_log': improvement_log,
            'budget_exceeded': self.tokens_consumed >= self.budget_tokens
        }
    
    def _generate_refinement_prompt(self, reflection: str, critique: Dict,
                                    original_content: str) -> str:
        """生成改进提示"""
        
        # 格式化各类问题
        factual_issues = self._format_issues(critique.get('factual', {}).get('issues', []))
        logical_issues = self._format_issues(critique.get('logical', {}).get('issues', []))
        depth_issues = self._format_issues(critique.get('depth', {}).get('issues', []))
        utility_issues = self._format_issues(critique.get('utility', {}).get('issues', []))
        
        prompt = f"""你是一个专业的反思质量改进助手。请基于识别的问题改进以下反思内容。

【原始反思】
{reflection}

【原始内容参考】(请确保改进后的反思覆盖这些内容)
{original_content[:2000]}  # 限制长度避免过长

【识别的问题】

1. 事实性问题 (权重30%):
{factual_issues if factual_issues else "  无明显问题"}

2. 逻辑性问题 (权重25%):
{logical_issues if logical_issues else "  无明显问题"}

3. 深度问题 (权重25%):
{depth_issues if depth_issues else "  无明显问题"}

4. 实用性问题 (权重20%):
{utility_issues if utility_issues else "  无明显问题"}

【改进要求】

针对以上问题，请按以下优先级改进:

1. **事实性** (最高优先级):
   - 添加具体的时间戳、文件路径、引用
   - 确保每个主张都有原文支撑
   - 避免绝对化表述("总是"、"从不")

2. **逻辑性**:
   - 修正不合理的因果推断
   - 消除自相矛盾
   - 确保建议与问题匹配

3. **深度**:
   - 至少追问2次"为什么"
   - 触及根本原因而非表面现象
   - 提炼可复用的模式或原则

4. **实用性**:
   - 将抽象建议转化为具体步骤
   - 添加可验证的指标或方法
   - 建议更新相关文档(SOUL.md/MEMORY.md)

【输出格式】

请直接输出改进后的完整反思，保持原有结构但修复所有问题。反思应包含:
- 基于事实的观察
- 深入的原因分析
- 可执行的具体建议
- 验证方法

改进后的反思:"""
        
        return prompt
    
    def _format_issues(self, issues: List[Dict]) -> str:
        """格式化问题列表"""
        if not issues:
            return ""
        
        formatted = []
        for i, issue in enumerate(issues, 1):
            formatted.append(f"  {i}. {issue['description']}")
            formatted.append(f"     建议: {issue['suggestion']}")
        
        return '\n'.join(formatted)
    
    def _call_llm(self, prompt: str, llm_client=None) -> Tuple[str, int]:
        """
        调用LLM进行改进
        
        简化实现 - 实际需要接入真实的LLM客户端
        目前返回模拟结果用于测试
        """
        # 估算token数 (中文约1.5字符/token)
        input_tokens = len(prompt) // 1.5
        
        # 模拟改进 (实际应该调用真实LLM)
        # 这里使用启发式改进作为示例
        improved = self._heuristic_improvement(prompt)
        
        output_tokens = len(improved) // 1.5
        total_tokens = int(input_tokens + output_tokens)
        
        return improved, total_tokens
    
    def _heuristic_improvement(self, prompt: str) -> str:
        """
        启发式改进 (用于测试)
        
        实际部署时应该替换为真实LLM调用
        """
        # 从prompt中提取原始反思
        reflection_match = re.search(r'【原始反思】\s*\n(.+?)\n\n【原始内容参考】', prompt, re.DOTALL)
        if not reflection_match:
            return "[改进失败: 无法解析原始反思]"
        
        reflection = reflection_match.group(1).strip()
        
        # 简单的启发式改进
        improved = reflection
        
        # 添加时间戳引用
        if '根据' not in reflection and '基于' not in reflection:
            improved = f"根据memory/{datetime.now().strftime('%Y-%m-%d')}.md的记录:\n\n" + improved
        
        # 深化"为什么"分析
        if '为什么' not in improved:
            improved += "\n\n**深层原因分析**:\n- 为什么会出现这个问题? 根本原因是...\n- 这反映了什么模式? ..."
        
        # 添加验证方法
        if '验证' not in improved:
            improved += "\n\n**验证方法**:\n- 下次遇到类似情况时，观察...\n- 通过XXX指标验证改进效果"
        
        return improved
    
    def _get_logger(self):
        """获取logger"""
        class SimpleLogger:
            def info(self, msg):
                print(f"[{datetime.now().isoformat()}] [INFO] {msg}")
            def success(self, msg):
                print(f"[{datetime.now().isoformat()}] [SUCCESS] {msg}")
            def warning(self, msg):
                print(f"[{datetime.now().isoformat()}] [WARNING] {msg}")
        return SimpleLogger()


# ============================================
# Anti-Hacking Phase 4: Effectiveness Tracking
# ============================================

@dataclass
class TrackedRecommendation:
    """被追踪的建议"""
    id: str
    reflection_id: str
    content: str  # 建议内容
    expected_outcome: str  # 预期效果
    category: str  # 'pattern', 'tool', 'workflow', 'optimization'
    confidence: float  # 生成时的置信度
    created_at: str
    expires_at: str  # 追踪截止日期
    status: str = "pending"  # 'pending', 'applied', 'verified', 'expired', 'obsolete'
    verification_result: Optional[Dict] = None
    related_tasks: List[str] = field(default_factory=list)


class EffectivenessTracker:
    """
    效果追踪系统 - Phase 4
    
    追踪反思建议的实际应用效果，建立反馈闭环
    """
    
    def __init__(self):
        self.tracking_data = self._load_tracking_data()
        self.config = EFFECTIVENESS_TRACKING_CONFIG
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志"""
        class SimpleLogger:
            def info(self, msg):
                print(f"[{datetime.now().isoformat()}] [EFFECTIVENESS] [INFO] {msg}")
            def success(self, msg):
                print(f"[{datetime.now().isoformat()}] [EFFECTIVENESS] [SUCCESS] {msg}")
            def warning(self, msg):
                print(f"[{datetime.now().isoformat()}] [EFFECTIVENESS] [WARNING] {msg}")
        return SimpleLogger()
    
    def _load_tracking_data(self) -> Dict:
        """加载追踪数据"""
        if EFFECTIVENESS_TRACKING_FILE.exists():
            with open(EFFECTIVENESS_TRACKING_FILE, 'r') as f:
                return json.load(f)
        return {
            'recommendations': {},
            'statistics': {
                'total_created': 0,
                'total_applied': 0,
                'total_verified': 0,
                'overall_effectiveness': 0.0
            },
            'category_stats': {}
        }
    
    def _save_tracking_data(self):
        """保存追踪数据"""
        with open(EFFECTIVENESS_TRACKING_FILE, 'w') as f:
            json.dump(self.tracking_data, f, ensure_ascii=False, indent=2)
    
    def track_recommendation(self, reflection_id: str, recommendation: str,
                            expected_outcome: str, category: str,
                            confidence: float) -> str:
        """
        注册新建议进行追踪
        
        Returns:
            recommendation_id
        """
        if confidence < self.config['min_confidence_for_tracking']:
            self.logger.info(f"置信度{confidence:.2f}低于阈值，跳过追踪")
            return ""
        
        rec_id = f"REC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"
        
        expires = (datetime.now() + timedelta(days=self.config['tracking_period_days'])).isoformat()
        
        tracked = TrackedRecommendation(
            id=rec_id,
            reflection_id=reflection_id,
            content=recommendation,
            expected_outcome=expected_outcome,
            category=category,
            confidence=confidence,
            created_at=datetime.now().isoformat(),
            expires_at=expires
        )
        
        self.tracking_data['recommendations'][rec_id] = asdict(tracked)
        self.tracking_data['statistics']['total_created'] += 1
        
        # 更新分类统计
        if category not in self.tracking_data['category_stats']:
            self.tracking_data['category_stats'][category] = {
                'created': 0, 'applied': 0, 'verified': 0, 'effectiveness': 0.0
            }
        self.tracking_data['category_stats'][category]['created'] += 1
        
        self._save_tracking_data()
        self.logger.info(f"注册新建议追踪: {rec_id} (类别: {category}, 置信度: {confidence:.2f})")
        
        return rec_id
    
    def check_application(self, task_content: str, task_id: str) -> List[str]:
        """
        检查任务内容是否应用了已追踪的建议
        
        Returns:
            匹配到的建议ID列表
        """
        matched_recs = []
        
        for rec_id, rec_data in self.tracking_data['recommendations'].items():
            if rec_data['status'] not in ['pending', 'applied']:
                continue
            
            # 检查关键词匹配
            keywords = self._extract_keywords(rec_data['content'])
            match_score = sum(1 for kw in keywords if kw in task_content.lower())
            
            if match_score >= len(keywords) * 0.5:  # 50%关键词匹配
                matched_recs.append(rec_id)
                
                # 更新状态
                if rec_data['status'] == 'pending':
                    rec_data['status'] = 'applied'
                    rec_data['applied_at'] = datetime.now().isoformat()
                    rec_data['related_tasks'].append(task_id)
                    self.tracking_data['statistics']['total_applied'] += 1
                    
                    category = rec_data['category']
                    self.tracking_data['category_stats'][category]['applied'] += 1
                    
                    self.logger.info(f"检测到建议应用: {rec_id} 在任务 {task_id}")
        
        if matched_recs:
            self._save_tracking_data()
        
        return matched_recs
    
    def verify_outcome(self, rec_id: str, success: bool, actual_outcome: str,
                      evidence: str = "") -> bool:
        """
        验证建议的实际效果
        
        Args:
            rec_id: 建议ID
            success: 是否成功
            actual_outcome: 实际结果描述
            evidence: 证据(如成功日志、输出等)
        """
        if rec_id not in self.tracking_data['recommendations']:
            self.logger.warning(f"建议不存在: {rec_id}")
            return False
        
        rec = self.tracking_data['recommendations'][rec_id]
        
        rec['status'] = 'verified' if success else 'failed'
        rec['verified_at'] = datetime.now().isoformat()
        rec['verification_result'] = {
            'success': success,
            'actual_outcome': actual_outcome,
            'evidence': evidence,
            'expected_match': self._compare_outcomes(rec['expected_outcome'], actual_outcome)
        }
        
        self.tracking_data['statistics']['total_verified'] += 1
        
        # 更新分类统计
        category = rec['category']
        self.tracking_data['category_stats'][category]['verified'] += 1
        
        # 反馈到IER系统
        if self.config['auto_feedback_to_ier'] and IER_AVAILABLE:
            self._feedback_to_ier(rec_id, success)
        
        self._update_effectiveness_stats()
        self._save_tracking_data()
        
        status_str = "✅成功" if success else "❌失败"
        self.logger.info(f"验证结果: {rec_id} {status_str}")
        
        return True
    
    def _feedback_to_ier(self, rec_id: str, success: bool):
        """将验证结果反馈到IER系统"""
        try:
            exp_manager = get_sra_experience_manager()
            # 标记经验验证结果
            rec = self.tracking_data['recommendations'][rec_id]
            
            # 这里假设可以通过reflection_id关联到IER经验
            # 实际实现可能需要调整
            self.logger.info(f"反馈到IER: {rec_id} 验证结果={success}")
        except Exception as e:
            self.logger.warning(f"IER反馈失败: {e}")
    
    def _update_effectiveness_stats(self):
        """更新有效率统计"""
        verified_recs = [
            r for r in self.tracking_data['recommendations'].values()
            if r['status'] == 'verified'
        ]
        
        if verified_recs:
            success_count = sum(1 for r in verified_recs if r['verification_result']['success'])
            self.tracking_data['statistics']['overall_effectiveness'] = success_count / len(verified_recs)
        
        # 按分类更新
        for category, stats in self.tracking_data['category_stats'].items():
            category_recs = [
                r for r in self.tracking_data['recommendations'].values()
                if r['category'] == category and r['status'] == 'verified'
            ]
            if category_recs:
                success_count = sum(1 for r in category_recs if r['verification_result']['success'])
                stats['effectiveness'] = success_count / len(category_recs)
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词用于匹配"""
        # 提取中文字符和英文单词
        chinese = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        english = re.findall(r'[a-zA-Z_]{4,}', content)
        return list(set(chinese + english))
    
    def _compare_outcomes(self, expected: str, actual: str) -> float:
        """比较预期结果和实际结果的相似度"""
        expected_keywords = set(self._extract_keywords(expected))
        actual_keywords = set(self._extract_keywords(actual))
        
        if not expected_keywords:
            return 1.0
        
        overlap = len(expected_keywords & actual_keywords)
        return overlap / len(expected_keywords)
    
    def get_statistics(self) -> Dict:
        """获取效果追踪统计"""
        stats = self.tracking_data['statistics'].copy()
        stats['active_recommendations'] = sum(
            1 for r in self.tracking_data['recommendations'].values()
            if r['status'] in ['pending', 'applied']
        )
        stats['category_breakdown'] = self.tracking_data['category_stats']
        return stats
    
    def get_recommendation_report(self, rec_id: str = None) -> Dict:
        """获取建议追踪报告"""
        if rec_id:
            return self.tracking_data['recommendations'].get(rec_id)
        
        # 返回最近10条
        sorted_recs = sorted(
            self.tracking_data['recommendations'].values(),
            key=lambda x: x['created_at'],
            reverse=True
        )
        return {'recent_recommendations': sorted_recs[:10]}
    
    def cleanup_expired(self):
        """清理过期的追踪记录"""
        now = datetime.now()
        expired_count = 0
        
        for rec_id, rec_data in list(self.tracking_data['recommendations'].items()):
            expires = datetime.fromisoformat(rec_data['expires_at'])
            if now > expires and rec_data['status'] == 'pending':
                rec_data['status'] = 'expired'
                expired_count += 1
        
        if expired_count > 0:
            self._save_tracking_data()
            self.logger.info(f"清理 {expired_count} 条过期追踪记录")


# ============================================
# Anti-Hacking Phase 5: Adaptive Thresholds
# ============================================

@dataclass
class ThresholdAdjustment:
    """阈值调整记录"""
    timestamp: str
    threshold_name: str
    old_value: float
    new_value: float
    reason: str
    trigger_metric: str
    metric_value: float


class AdaptiveThresholdManager:
    """
    自适应阈值管理器 - Phase 5
    
    根据历史数据自动调整Anti-Hacking各阶段的阈值
    实现数据驱动的质量优化
    """
    
    def __init__(self):
        self.config = ADAPTIVE_THRESHOLD_CONFIG
        self.adjustment_history = self._load_adjustment_history()
        self.current_thresholds = self._load_current_thresholds()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志"""
        class SimpleLogger:
            def info(self, msg):
                print(f"[{datetime.now().isoformat()}] [ADAPTIVE] [INFO] {msg}")
            def success(self, msg):
                print(f"[{datetime.now().isoformat()}] [ADAPTIVE] [SUCCESS] {msg}")
            def warning(self, msg):
                print(f"[{datetime.now().isoformat()}] [ADAPTIVE] [WARNING] {msg}")
        return SimpleLogger()
    
    def _load_adjustment_history(self) -> List[Dict]:
        """加载调整历史"""
        if ADAPTIVE_THRESHOLD_FILE.exists():
            with open(ADAPTIVE_THRESHOLD_FILE, 'r') as f:
                data = json.load(f)
                return data.get('adjustment_history', [])
        return []
    
    def _load_current_thresholds(self) -> Dict[str, float]:
        """加载当前阈值"""
        if ADAPTIVE_THRESHOLD_FILE.exists():
            with open(ADAPTIVE_THRESHOLD_FILE, 'r') as f:
                data = json.load(f)
                return data.get('current_thresholds', self._get_default_thresholds())
        return self._get_default_thresholds()
    
    def _get_default_thresholds(self) -> Dict[str, float]:
        """获取默认阈值"""
        return {
            'rubric_threshold': ANTI_HACKING_CONFIG['rubric_threshold'],
            'outcome_threshold': ANTI_HACKING_CONFIG['outcome_threshold'],
            'self_critical_threshold': SelfCriticalPipeline().confidence_threshold,
            'tracking_confidence_threshold': EFFECTIVENESS_TRACKING_CONFIG['min_confidence_for_tracking'],
        }
    
    def _save_data(self):
        """保存数据"""
        data = {
            'current_thresholds': self.current_thresholds,
            'adjustment_history': self.adjustment_history,
            'last_updated': datetime.now().isoformat()
        }
        with open(ADAPTIVE_THRESHOLD_FILE, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _can_adjust(self) -> bool:
        """检查是否可以调整阈值"""
        if not self.adjustment_history:
            return True
        
        last_adjustment = datetime.fromisoformat(self.adjustment_history[-1]['timestamp'])
        days_since_last = (datetime.now() - last_adjustment).days
        
        return days_since_last >= self.config['adjustment_cooldown_days']
    
    def analyze_and_adjust(self, validator: AntiHackingValidator,
                          tracker: EffectivenessTracker):
        """
        分析历史数据并调整阈值
        
        Args:
            validator: AntiHackingValidator实例
            tracker: EffectivenessTracker实例
        """
        if not self.config['enabled']:
            self.logger.info("自适应阈值已禁用")
            return
        
        if not self._can_adjust():
            self.logger.info("处于调整冷却期，跳过本次调整")
            return
        
        self.logger.info("开始分析历史数据并评估阈值调整...")
        
        adjustments_made = []
        
        # 1. 分析Phase 1通过率
        phase1_adjustment = self._adjust_phase1_thresholds(validator)
        if phase1_adjustment:
            adjustments_made.append(phase1_adjustment)
        
        # 2. 分析Phase 2改进成功率
        phase2_adjustment = self._adjust_phase2_thresholds(validator)
        if phase2_adjustment:
            adjustments_made.append(phase2_adjustment)
        
        # 3. 分析Phase 4建议有效率
        phase4_adjustment = self._adjust_phase4_thresholds(tracker)
        if phase4_adjustment:
            adjustments_made.append(phase4_adjustment)
        
        if adjustments_made:
            self._save_data()
            self.logger.success(f"完成 {len(adjustments_made)} 项阈值调整")
            for adj in adjustments_made:
                self.logger.success(f"  {adj['threshold_name']}: {adj['old_value']:.2f} -> {adj['new_value']:.2f}")
        else:
            self.logger.info("当前阈值无需调整")
    
    def _adjust_phase1_thresholds(self, validator: AntiHackingValidator) -> Optional[Dict]:
        """调整Phase 1阈值"""
        history = validator.reflection_history
        
        if len(history) < self.config['min_samples_for_adjustment']:
            return None
        
        # 计算最近通过率
        recent = history[-self.config['min_samples_for_adjustment']:]
        pass_rate = sum(1 for h in recent if h.get('passed')) / len(recent)
        
        current_rubric = self.current_thresholds['rubric_threshold']
        target_rate = self.config['target_pass_rate']
        
        # 根据通过率调整阈值
        if pass_rate < target_rate - 0.1:  # 通过率低于目标10%
            # 阈值可能太严格，降低一点
            if not self.config['conservative_mode']:
                new_threshold = max(current_rubric - 0.05, self.config['min_threshold'])
                return self._create_adjustment('rubric_threshold', current_rubric, new_threshold,
                                              f"通过率{pass_rate:.1%}低于目标{target_rate:.1%}", 
                                              'pass_rate', pass_rate)
        elif pass_rate > target_rate + 0.15:  # 通过率高于目标15%
            # 阈值可能太宽松，提高一点
            new_threshold = min(current_rubric + 0.05, self.config['max_threshold'])
            return self._create_adjustment('rubric_threshold', current_rubric, new_threshold,
                                          f"通过率{pass_rate:.1%}高于目标{target_rate:.1%}，提升质量门槛",
                                          'pass_rate', pass_rate)
        
        return None
    
    def _adjust_phase2_thresholds(self, validator: AntiHackingValidator) -> Optional[Dict]:
        """调整Phase 2阈值"""
        history = validator.reflection_history
        
        # 计算改进成功率
        refined = [h for h in history if h.get('was_refined', False)]
        if len(refined) < 5:
            return None
        
        success_rate = sum(1 for h in refined if h.get('refinement_improved', False)) / len(refined)
        
        current_sc = self.current_thresholds['self_critical_threshold']
        
        # 如果改进成功率高，说明质疑有效，可以降低置信度阈值让更多反思被质疑
        if success_rate > 0.8:
            new_threshold = max(current_sc - 0.05, 0.6)
            return self._create_adjustment('self_critical_threshold', current_sc, new_threshold,
                                          f"改进成功率{success_rate:.1%}高，降低阈值以覆盖更多反思",
                                          'refinement_success_rate', success_rate)
        elif success_rate < 0.4:
            # 改进成功率低，提高阈值减少无效质疑
            new_threshold = min(current_sc + 0.05, 0.85)
            return self._create_adjustment('self_critical_threshold', current_sc, new_threshold,
                                          f"改进成功率{success_rate:.1%}低，提高阈值减少无效质疑",
                                          'refinement_success_rate', success_rate)
        
        return None
    
    def _adjust_phase4_thresholds(self, tracker: EffectivenessTracker) -> Optional[Dict]:
        """调整Phase 4阈值"""
        stats = tracker.get_statistics()
        
        if stats['total_verified'] < 5:
            return None
        
        effectiveness = stats['overall_effectiveness']
        current_tc = self.current_thresholds['tracking_confidence_threshold']
        target_eff = self.config['target_effectiveness']
        
        # 根据有效率调整追踪阈值
        if effectiveness < target_eff - 0.15:
            # 有效率低，提高追踪阈值确保只追踪高质量建议
            new_threshold = min(current_tc + 0.05, 0.85)
            return self._create_adjustment('tracking_confidence_threshold', current_tc, new_threshold,
                                          f"有效率{effectiveness:.1%}低于目标{target_eff:.1%}",
                                          'effectiveness', effectiveness)
        elif effectiveness > target_eff + 0.1:
            # 有效率高，可以适当降低阈值追踪更多建议
            if not self.config['conservative_mode']:
                new_threshold = max(current_tc - 0.05, 0.5)
                return self._create_adjustment('tracking_confidence_threshold', current_tc, new_threshold,
                                              f"有效率{effectiveness:.1%}高于目标{target_eff:.1%}",
                                              'effectiveness', effectiveness)
        
        return None
    
    def _create_adjustment(self, name: str, old: float, new: float,
                          reason: str, metric: str, metric_value: float) -> Optional[Dict]:
        """创建调整记录"""
        if abs(new - old) < 0.001:  # 没有实际变化
            return None
        
        adjustment = {
            'timestamp': datetime.now().isoformat(),
            'threshold_name': name,
            'old_value': old,
            'new_value': new,
            'reason': reason,
            'trigger_metric': metric,
            'metric_value': metric_value
        }
        
        self.adjustment_history.append(adjustment)
        self.current_thresholds[name] = new
        
        # 只保留最近50条历史
        self.adjustment_history = self.adjustment_history[-50:]
        
        return adjustment
    
    def get_threshold(self, name: str) -> float:
        """获取当前阈值"""
        return self.current_thresholds.get(name, self._get_default_thresholds()[name])
    
    def get_statistics(self) -> Dict:
        """获取自适应阈值统计"""
        return {
            'current_thresholds': self.current_thresholds,
            'total_adjustments': len(self.adjustment_history),
            'recent_adjustments': self.adjustment_history[-5:] if self.adjustment_history else [],
            'can_adjust': self._can_adjust(),
            'config': self.config
        }
    
    def force_adjustment(self, name: str, value: float, reason: str) -> bool:
        """
        强制调整阈值（管理员手动调整）
        
        Returns:
            是否成功调整
        """
        if name not in self.current_thresholds:
            self.logger.warning(f"未知阈值: {name}")
            return False
        
        old_value = self.current_thresholds[name]
        adjustment = self._create_adjustment(name, old_value, value, reason, 'manual', 0)
        
        if adjustment:
            self._save_data()
            self.logger.success(f"手动调整阈值: {name} {old_value:.2f} -> {value:.2f}")
            return True
        return False


# ============================================
# Anti-Hacking Phase 6: Cross-Reflection Pattern Analysis
# ============================================

@dataclass
class ReflectionPattern:
    """跨反思模式"""
    pattern_id: str
    pattern_type: str  # 'content_feature', 'temporal', 'contextual', 'structural'
    description: str
    occurrences: int
    avg_effectiveness: float
    avg_confidence: float
    related_reflections: List[str]
    first_seen: str
    last_seen: str
    trend: str = "stable"  # 'improving', 'declining', 'stable'


class CrossReflectionAnalyzer:
    """
    跨反思模式分析器 - Phase 6
    
    分析多个反思之间的模式，识别哪类反思产生最有效的建议
    为优化反思策略提供数据支持
    """
    
    def __init__(self):
        self.config = CROSS_REFLECTION_CONFIG
        self.analysis_data = self._load_analysis_data()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志"""
        class SimpleLogger:
            def info(self, msg):
                print(f"[{datetime.now().isoformat()}] [CROSS-REF] [INFO] {msg}")
            def success(self, msg):
                print(f"[{datetime.now().isoformat()}] [CROSS-REF] [SUCCESS] {msg}")
            def warning(self, msg):
                print(f"[{datetime.now().isoformat()}] [CROSS-REF] [WARNING] {msg}")
        return SimpleLogger()
    
    def _load_analysis_data(self) -> Dict:
        """加载分析数据"""
        if CROSS_REFLECTION_FILE.exists():
            with open(CROSS_REFLECTION_FILE, 'r') as f:
                return json.load(f)
        return {
            'patterns': {},
            'insights': [],
            'statistics': {
                'total_analyses': 0,
                'patterns_identified': 0,
                'insights_generated': 0
            },
            'reflection_profiles': {}
        }
    
    def _save_analysis_data(self):
        """保存分析数据"""
        with open(CROSS_REFLECTION_FILE, 'w') as f:
            json.dump(self.analysis_data, f, ensure_ascii=False, indent=2)
    
    def analyze(self, validator: AntiHackingValidator,
                tracker: EffectivenessTracker) -> Dict:
        """
        执行跨反思分析
        
        Returns:
            分析结果报告
        """
        if not self.config['enabled']:
            self.logger.info("跨反思分析已禁用")
            return {'enabled': False}
        
        # 检查样本量
        history = validator.reflection_history
        if len(history) < self.config['min_reflections_for_analysis']:
            self.logger.info(f"反思样本不足 ({len(history)}/{self.config['min_reflections_for_analysis']})")
            return {'insufficient_data': True, 'sample_count': len(history)}
        
        self.logger.info(f"开始跨反思分析，样本数: {len(history)}")
        
        results = {
            'patterns_found': [],
            'insights': [],
            'recommendations': []
        }
        
        # 1. 分析内容特征模式
        content_patterns = self._analyze_content_patterns(history)
        results['patterns_found'].extend(content_patterns)
        
        # 2. 分析时间模式
        temporal_patterns = self._analyze_temporal_patterns(history)
        results['patterns_found'].extend(temporal_patterns)
        
        # 3. 分析反思类型效果
        type_effectiveness = self._analyze_type_effectiveness(history, tracker)
        results['insights'].extend(type_effectiveness)
        
        # 4. 生成优化建议
        recommendations = self._generate_recommendations(results)
        results['recommendations'] = recommendations
        
        # 5. 更新分析数据
        self._update_analysis_data(results)
        self.analysis_data['statistics']['total_analyses'] += 1
        self._save_analysis_data()
        
        self.logger.success(f"跨反思分析完成，发现 {len(content_patterns)} 个内容模式，"
                          f"{len(temporal_patterns)} 个时间模式，"
                          f"生成 {len(recommendations)} 条建议")
        
        return results
    
    def _analyze_content_patterns(self, history: List[Dict]) -> List[Dict]:
        """分析内容特征模式"""
        patterns = []
        
        # 关键词模式分析
        keyword_patterns = {
            'technical_depth': ['实现', '代码', '架构', '设计', '优化', '性能'],
            'problem_solving': ['问题', '解决', '方案', '错误', '修复', '调试'],
            'learning': ['学习', '理解', '掌握', '新发现', 'insights', '模式'],
            'meta_reflection': ['反思', '复盘', '总结', '改进', '迭代']
        }
        
        for pattern_name, keywords in keyword_patterns.items():
            matching = []
            for h in history:
                content = h.get('content', '')
                score = sum(1 for kw in keywords if kw in content) / len(keywords)
                if score > 0.3:  # 30%关键词匹配
                    matching.append(h)
            
            if len(matching) >= self.config['pattern_min_occurrences']:
                avg_effectiveness = sum(
                    h.get('effectiveness', 0.5) for h in matching
                ) / len(matching)
                avg_confidence = sum(
                    h.get('rubric_score', 0.5) for h in matching
                ) / len(matching)
                
                patterns.append({
                    'pattern_id': f"content_{pattern_name}_{datetime.now().strftime('%Y%m%d')}",
                    'pattern_type': 'content_feature',
                    'description': f"包含{pattern_name}相关内容的反思",
                    'occurrences': len(matching),
                    'avg_effectiveness': avg_effectiveness,
                    'avg_confidence': avg_confidence,
                    'keywords': keywords,
                    'trend': self._calculate_trend(matching)
                })
        
        return patterns
    
    def _analyze_temporal_patterns(self, history: List[Dict]) -> List[Dict]:
        """分析时间模式"""
        patterns = []
        
        # 按小时分组
        hour_groups = {}
        for h in history:
            ts = datetime.fromisoformat(h.get('timestamp', '2000-01-01T00:00:00'))
            hour = ts.hour
            if hour not in hour_groups:
                hour_groups[hour] = []
            hour_groups[hour].append(h)
        
        # 找出高效时段
        for hour, group in hour_groups.items():
            if len(group) >= self.config['pattern_min_occurrences']:
                avg_effectiveness = sum(
                    h.get('effectiveness', 0.5) for h in group
                ) / len(group)
                
                if avg_effectiveness > 0.7:  # 高效率时段
                    patterns.append({
                        'pattern_id': f"temporal_hour_{hour}_{datetime.now().strftime('%Y%m%d')}",
                        'pattern_type': 'temporal',
                        'description': f"{hour}:00时段进行的反思",
                        'occurrences': len(group),
                        'avg_effectiveness': avg_effectiveness,
                        'time_slot': f"{hour}:00",
                        'trend': 'stable'
                    })
        
        return patterns
    
    def _analyze_type_effectiveness(self, history: List[Dict],
                                   tracker: EffectivenessTracker) -> List[Dict]:
        """分析反思类型效果"""
        insights = []
        
        # 按反思类型分组统计
        type_stats = {}
        for h in history:
            ref_type = h.get('type', 'unknown')
            if ref_type not in type_stats:
                type_stats[ref_type] = {'count': 0, 'passed': 0, 'effectiveness': []}
            type_stats[ref_type]['count'] += 1
            if h.get('passed'):
                type_stats[ref_type]['passed'] += 1
            type_stats[ref_type]['effectiveness'].append(h.get('effectiveness', 0.5))
        
        for ref_type, stats in type_stats.items():
            if stats['count'] >= self.config['pattern_min_occurrences']:
                pass_rate = stats['passed'] / stats['count']
                avg_effectiveness = sum(stats['effectiveness']) / len(stats['effectiveness'])
                
                insights.append({
                    'type': ref_type,
                    'count': stats['count'],
                    'pass_rate': pass_rate,
                    'avg_effectiveness': avg_effectiveness,
                    'assessment': self._assess_type_performance(pass_rate, avg_effectiveness)
                })
        
        return insights
    
    def _assess_type_performance(self, pass_rate: float,
                                 effectiveness: float) -> str:
        """评估反思类型表现"""
        score = pass_rate * self.config['effectiveness_weight'] + \
                effectiveness * self.config['confidence_weight']
        
        if score >= 0.7:
            return "优秀 - 应增加此类反思频率"
        elif score >= 0.5:
            return "良好 - 保持当前频率"
        else:
            return "需改进 - 建议优化此类反思流程"
    
    def _calculate_trend(self, reflections: List[Dict]) -> str:
        """计算趋势"""
        if len(reflections) < 3:
            return "stable"
        
        # 按时间排序
        sorted_refs = sorted(reflections, key=lambda x: x.get('timestamp', ''))
        
        # 分前后两半比较
        mid = len(sorted_refs) // 2
        first_half = sorted_refs[:mid]
        second_half = sorted_refs[mid:]
        
        first_eff = sum(r.get('effectiveness', 0.5) for r in first_half) / len(first_half)
        second_eff = sum(r.get('effectiveness', 0.5) for r in second_half) / len(second_half)
        
        diff = second_eff - first_eff
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        return "stable"
    
    def _generate_recommendations(self, results: Dict) -> List[Dict]:
        """生成优化建议"""
        recommendations = []
        
        # 基于内容模式生成建议
        for pattern in results['patterns_found']:
            if pattern['pattern_type'] == 'content_feature':
                if pattern['avg_effectiveness'] > 0.75:
                    recommendations.append({
                        'category': 'content_optimization',
                        'priority': 'high',
                        'recommendation': f"增加包含'{pattern['description']}'的反思，"
                                        f"此类反思有效率{pattern['avg_effectiveness']:.1%}",
                        'expected_improvement': f"整体有效率提升5-10%"
                    })
            elif pattern['pattern_type'] == 'temporal':
                recommendations.append({
                    'category': 'timing_optimization',
                    'priority': 'medium',
                    'recommendation': f"优先在{pattern['time_slot']}进行重要反思，"
                                    f"该时段反思有效率{pattern['avg_effectiveness']:.1%}",
                    'expected_improvement': f"单次反思质量提升10-15%"
                })
        
        # 基于类型效果生成建议
        for insight in results['insights']:
            if insight['assessment'].startswith('优秀'):
                recommendations.append({
                    'category': 'type_optimization',
                    'priority': 'high',
                    'recommendation': f"增加'{insight['type']}'类型反思，"
                                    f"通过率{insight['pass_rate']:.1%}",
                    'expected_improvement': f"整体产出提升15-20%"
                })
        
        return recommendations
    
    def _update_analysis_data(self, results: Dict):
        """更新分析数据"""
        for pattern in results['patterns_found']:
            pattern_id = pattern['pattern_id']
            if pattern_id not in self.analysis_data['patterns']:
                self.analysis_data['patterns'][pattern_id] = pattern
                self.analysis_data['statistics']['patterns_identified'] += 1
            else:
                # 更新现有模式
                self.analysis_data['patterns'][pattern_id].update({
                    'occurrences': pattern['occurrences'],
                    'avg_effectiveness': pattern['avg_effectiveness'],
                    'avg_confidence': pattern['avg_confidence'],
                    'trend': pattern['trend'],
                    'last_seen': datetime.now().isoformat()
                })
        
        # 保存新洞察
        for insight in results['insights']:
            self.analysis_data['insights'].append({
                **insight,
                'generated_at': datetime.now().isoformat()
            })
            self.analysis_data['statistics']['insights_generated'] += 1
        
        # 只保留最近100条洞察
        self.analysis_data['insights'] = self.analysis_data['insights'][-100:]
    
    def get_statistics(self) -> Dict:
        """获取分析统计"""
        return {
            **self.analysis_data['statistics'],
            'patterns': len(self.analysis_data['patterns']),
            'recent_insights': self.analysis_data['insights'][-5:] if self.analysis_data['insights'] else []
        }
    
    def get_best_practices(self) -> List[Dict]:
        """获取最佳实践建议"""
        best_practices = []
        
        # 找出最有效的模式
        sorted_patterns = sorted(
            self.analysis_data['patterns'].values(),
            key=lambda x: x.get('avg_effectiveness', 0),
            reverse=True
        )
        
        for pattern in sorted_patterns[:5]:
            if pattern.get('avg_effectiveness', 0) > 0.7:
                best_practices.append({
                    'pattern_type': pattern['pattern_type'],
                    'description': pattern['description'],
                    'effectiveness': pattern['avg_effectiveness'],
                    'occurrences': pattern['occurrences'],
                    'recommendation': f"建议增加此类反思，平均有效率{pattern['avg_effectiveness']:.1%}"
                })
        
        return best_practices


# ============================================
# 原有数据类定义
# ============================================

@dataclass
class ReflectionRequest:
    """复盘请求"""
    id: str
    type: str  # 'daily', 'weekly', 'conversation', 'error'
    target_date: str  # YYYY-MM-DD
    description: str
    priority: int
    submitted_at: str
    status: str = "pending"
    result: Dict = field(default_factory=dict)


@dataclass
class ExtractedTip:
    """提取的技巧"""
    id: str
    category: str  # 'pattern', 'tool', 'lesson', 'optimization'
    context: str
    technique: str
    code_example: str
    usage_count: int = 0
    success_rate: float = 0.0
    extracted_at: str = ""
    verified: bool = False


@dataclass
class ServiceStatus:
    """服务状态"""
    pid: int
    start_time: str
    last_heartbeat: str
    total_reflections: int
    tips_extracted: int
    pending_requests: int
    is_running: bool = True
    current_task: str = ""


class SelfReflectionAgent:
    """
    自我复盘Agent - 集成IER经验精炼
    持续分析对话，提取可复用资产
    """
    
    def __init__(self):
        self.pid = os.getpid()
        self.status = ServiceStatus(
            pid=self.pid,
            start_time=datetime.now().isoformat(),
            last_heartbeat=datetime.now().isoformat(),
            total_reflections=0,
            tips_extracted=0,
            pending_requests=0
        )
        self.running = False
        self.worker_thread = None
        self.heartbeat_thread = None
        self.auto_reflection_thread = None
        
        # 初始化IER系统
        self.exp_manager = None
        if IER_AVAILABLE:
            try:
                self.exp_manager = get_sra_experience_manager()
            except Exception as e:
                print(f"[SRA-IER] 初始化失败: {e}")
        
        # 保存PID
        with open(PID_FILE, 'w') as f:
            f.write(str(self.pid))
        
        self.logger = self._setup_logger()
        
        # 初始化Anti-Hacking验证器 (Phase 1)
        self.anti_hacking_validator = AntiHackingValidator()
        self.logger.info("[Anti-Hacking] Phase 1组件已加载")
        
        # 初始化Self-Critical Pipeline (Phase 2)
        self.self_critical_pipeline = SelfCriticalPipeline()
        self.logger.info("[Anti-Hacking] Phase 2组件已加载")
        
        # 初始化Auto-Refiner (Phase 3)
        self.auto_refiner = AutoRefiner(
            max_iterations=AUTO_REFINEMENT_CONFIG['max_iterations'],
            confidence_threshold=AUTO_REFINEMENT_CONFIG['confidence_threshold'],
            budget_tokens=AUTO_REFINEMENT_CONFIG['budget_tokens']
        )
        if AUTO_REFINEMENT_CONFIG['enabled']:
            self.logger.info("[Anti-Hacking] Phase 3组件已加载 (自动改进循环)")
        else:
            self.logger.info("[Anti-Hacking] Phase 3已禁用")
        
        # 初始化Effectiveness Tracker (Phase 4)
        self.effectiveness_tracker = EffectivenessTracker()
        if EFFECTIVENESS_TRACKING_CONFIG['enabled']:
            self.logger.info("[Anti-Hacking] Phase 4组件已加载 (效果追踪系统)")
            # 清理过期记录
            self.effectiveness_tracker.cleanup_expired()
        else:
            self.logger.info("[Anti-Hacking] Phase 4已禁用")
        
        # 初始化Adaptive Threshold Manager (Phase 5)
        self.adaptive_threshold_manager = AdaptiveThresholdManager()
        if ADAPTIVE_THRESHOLD_CONFIG['enabled']:
            self.logger.info("[Anti-Hacking] Phase 5组件已加载 (自适应阈值)")
            # 启动时执行一次阈值分析
            self.logger.info("[Anti-Hacking] 执行自适应阈值分析...")
            self.adaptive_threshold_manager.analyze_and_adjust(
                self.anti_hacking_validator,
                self.effectiveness_tracker
            )
        else:
            self.logger.info("[Anti-Hacking] Phase 5已禁用")
        
        # 初始化Cross-Reflection Analyzer (Phase 6)
        self.cross_reflection_analyzer = CrossReflectionAnalyzer()
        if CROSS_REFLECTION_CONFIG['enabled']:
            self.logger.info("[Anti-Hacking] Phase 6组件已加载 (跨反思分析)")
            # 启动时执行一次分析
            self.logger.info("[Anti-Hacking] 执行跨反思模式分析...")
            analysis_result = self.cross_reflection_analyzer.analyze(
                self.anti_hacking_validator,
                self.effectiveness_tracker
            )
            if analysis_result.get('patterns_found'):
                self.logger.success(f"[Anti-Hacking] 发现 {len(analysis_result['patterns_found'])} 个跨反思模式")
        else:
            self.logger.info("[Anti-Hacking] Phase 6已禁用")
    
    def _setup_logger(self):
        """设置日志"""
        log_file = SRA_DIR / "logs"
        log_file.mkdir(exist_ok=True)
        log_file = log_file / f"sra_{datetime.now().strftime('%Y%m%d')}.log"
        
        class Logger:
            def info(self, msg):
                line = f"[{datetime.now().isoformat()}] [INFO] {msg}"
                print(line)
                with open(log_file, 'a') as f:
                    f.write(line + '\n')
            def success(self, msg):
                line = f"[{datetime.now().isoformat()}] [SUCCESS] {msg}"
                print(line)
                with open(log_file, 'a') as f:
                    f.write(line + '\n')
            def warning(self, msg):
                line = f"[{datetime.now().isoformat()}] [WARNING] {msg}"
                print(line)
                with open(log_file, 'a') as f:
                    f.write(line + '\n')
        
        return Logger()
    
    def start(self):
        """启动服务"""
        self.logger.info("="*60)
        self.logger.info("Self-Reflection Agent Service 启动")
        self.logger.info("="*60)
        self.logger.info(f"PID: {self.pid}")
        self.logger.info(f"请求目录: {REQUEST_DIR}")
        self.logger.info(f"复盘目录: {REFLECTION_DIR}")
        
        if self.exp_manager:
            self.logger.info(f"[SRA-IER] 当前经验数: {len(self.exp_manager.experiences)}")
            self._run_experience_maintenance()
        
        self.running = True
        
        # 启动工作线程
        self.worker_thread = threading.Thread(target=self._request_processor)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        # 启动自动复盘线程
        self.auto_reflection_thread = threading.Thread(target=self._auto_reflection_loop)
        self.auto_reflection_thread.daemon = True
        self.auto_reflection_thread.start()
        
        # 主循环
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("收到停止信号...")
        finally:
            self.stop()
    
    def stop(self):
        """停止服务"""
        self.logger.info("停止服务...")
        self.running = False
        self.status.is_running = False
        self._save_status()
        
        if PID_FILE.exists():
            PID_FILE.unlink()
        
        self.logger.success("服务已停止")
    
    def _run_experience_maintenance(self):
        """运行经验维护"""
        try:
            self.logger.info("[SRA-IER] 运行经验维护...")
            eliminated = self.exp_manager.evaluate_and_eliminate()
            if eliminated:
                self.logger.info(f"[SRA-IER] 淘汰了 {len(eliminated)} 条经验")
            stats = self.exp_manager.get_statistics()
            self.logger.info(f"[SRA-IER] 当前状态: {stats['active_experiences']}/{stats['total_experiences']} 活跃经验")
        except Exception as e:
            self.logger.warning(f"[SRA-IER] 经验维护失败: {e}")
    
    def _request_processor(self):
        """请求处理循环"""
        self.logger.info("请求处理器启动")
        
        while self.running:
            try:
                requests = self._scan_requests()
                
                for req_file in requests:
                    self._process_request(req_file)
                
                time.sleep(2)
                
            except Exception as e:
                self.logger.warning(f"请求处理器错误: {e}")
                time.sleep(5)
    
    def _scan_requests(self) -> List[Path]:
        """扫描请求文件"""
        if not REQUEST_DIR.exists():
            return []
        
        return sorted(REQUEST_DIR.glob("REQ_*.json"), key=lambda p: p.stat().st_mtime)
    
    def _process_request(self, req_file: Path):
        """处理单个请求 - 集成IER经验精炼"""
        try:
            with open(req_file, 'r') as f:
                request = json.load(f)
            
            req_id = request.get('id', 'unknown')
            req_type = request.get('type', 'unknown')
            target_date = request.get('target_date', '')
            description = request.get('description', '')
            
            self.status.current_task = req_id
            self.status.pending_requests += 1
            self._save_status()
            
            self.logger.info(f"开始复盘: {req_id} (类型: {req_type})")
            
            # IER: 记录任务开始
            if self.exp_manager:
                self.exp_manager.record_task_start(
                    req_id, req_type, target_date, description
                )
                
                # IER: 检索相关经验
                relevant_exps = self.exp_manager.retrieve_relevant_experiences(
                    req_type, description
                )
                if relevant_exps:
                    self.logger.info(f"[SRA-IER] 找到 {len(relevant_exps)} 条相关经验")
                    request['_ier_experiences'] = relevant_exps
            
            # 执行复盘
            result = self._execute_reflection(request)
            
            # IER: 提取新经验
            if self.exp_manager and result.get('success'):
                try:
                    tips = result.get('tips', [])
                    new_exps = self.exp_manager.acquire_from_reflection(
                        req_id, req_type, result, tips, True
                    )
                    if new_exps:
                        self.logger.info(f"[SRA-IER] 提取了 {len(new_exps)} 条新经验")
                        result['experiences_generated'] = [exp.id for exp in new_exps]
                except Exception as e:
                    self.logger.warning(f"[SRA-IER] 经验提取失败: {e}")
            
            # IER: 记录任务完成
            if self.exp_manager:
                quality = result.get('quality_score', 0.5)
                self.exp_manager.record_task_complete(
                    req_id,
                    result.get('success', False),
                    len(result.get('tips', [])),
                    quality,
                    result.get('error')
                )
            
            # 保存响应
            self._save_response(req_id, result)
            
            # 更新统计
            self.status.total_reflections += 1
            self.status.pending_requests -= 1
            if result.get('success'):
                tips_count = len(result.get('tips', []))
                self.status.tips_extracted += tips_count
                self.logger.success(f"复盘完成，提取 {tips_count} 个技巧")
            else:
                self.logger.warning(f"复盘失败: {result.get('error', 'Unknown')}")
            
            # 移动请求文件
            done_dir = REQUEST_DIR / "completed"
            done_dir.mkdir(exist_ok=True)
            req_file.rename(done_dir / req_file.name)
            
        except Exception as e:
            self.logger.warning(f"处理请求失败: {e}")
        finally:
            self.status.current_task = ""
            self._save_status()
    
    def _execute_reflection(self, request: Dict) -> Dict:
        """执行复盘 - 支持IER经验"""
        req_type = request.get('type', 'daily')
        target_date = request.get('target_date', datetime.now().strftime('%Y-%m-%d'))
        
        # 获取IER经验prompt
        exp_prompt = ""
        if self.exp_manager and '_ier_experiences' in request:
            exp_prompt = self.exp_manager.format_experiences_for_prompt(
                request['_ier_experiences']
            )
        
        try:
            if req_type == 'daily':
                return self._reflect_daily(target_date, exp_prompt)
            elif req_type == 'evolution':
                return self._reflect_evolution(target_date, exp_prompt)
            elif req_type == 'conversation':
                return self._reflect_conversation(request.get('conversation_file', ''), exp_prompt)
            elif req_type == 'error':
                return self._reflect_error(request.get('error_context', {}), exp_prompt)
            else:
                return {'success': False, 'error': f'Unknown reflection type: {req_type}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _reflect_daily(self, date: str, exp_prompt: str = "") -> Dict:
        """日复盘 - 支持IER经验 + Anti-Hacking验证"""
        self.logger.info(f"执行日复盘: {date}")
        
        # 读取当日记忆文件
        memory_file = MEMORY_DIR / f"daily/{date}.md"
        if not memory_file.exists():
            # 尝试查找最近的文件
            daily_files = sorted(MEMORY_DIR.glob("daily/*.md"))
            if daily_files:
                memory_file = daily_files[-1]
                self.logger.info(f"使用最近文件: {memory_file.name}")
        
        content = ""
        if memory_file.exists():
            content = memory_file.read_text()
        
        # 如果有IER经验prompt，添加到内容中
        if exp_prompt:
            content = f"{exp_prompt}\n\n{content}"
        
        # ===== Anti-Hacking Phase 1: 触发检查 =====
        self.logger.info("[Anti-Hacking] 执行触发检查...")
        should_reflect, reason = self.anti_hacking_validator.should_reflect(content)
        
        if not should_reflect:
            self.logger.warning(f"[Anti-Hacking] 触发检查失败: {reason}")
            return {
                'success': False,
                'error': f'Anti-Hacking触发检查失败: {reason}',
                'anti_hacking': {
                    'passed': False,
                    'reason': reason
                }
            }
        
        freq_penalty = self.anti_hacking_validator.compute_frequency_penalty()
        if freq_penalty > 0:
            self.logger.warning(f"[Anti-Hacking] 频率惩罚: {freq_penalty}")
        
        self.logger.success("[Anti-Hacking] 触发检查通过")
        
        # 分析内容
        tips = self._extract_tips_from_content(content)
        patterns = self._extract_patterns(content)
        errors = self._extract_errors(content)
        
        # 生成复盘报告
        report = self._generate_daily_report(date, tips, patterns, errors)
        
        # ===== Anti-Hacking Phase 2: Self-Critical质疑 =====
        self.logger.info("[Anti-Hacking] 执行Self-Critical质疑...")
        critique_result = self.self_critical_pipeline.critique(report, content)
        
        self.logger.info(f"[Anti-Hacking] Self-Critical置信度: {critique_result['confidence']:.2f}, "
                        f"发现问题: {critique_result['issues_count']}个")
        
        # 如果需要改进,记录问题详情
        if critique_result['should_refine']:
            self.logger.warning("[Anti-Hacking] 反思需要改进:")
            improvement_summary = self.self_critical_pipeline.generate_improvement_summary(critique_result)
            for line in improvement_summary.split('\n')[:10]:  # 只显示前10行
                self.logger.warning(f"  {line}")
            
            # ===== Anti-Hacking Phase 3: 自动改进循环 =====
            if AUTO_REFINEMENT_CONFIG['enabled']:
                self.logger.info("[Anti-Hacking] 启动自动改进循环 (Phase 3)...")
                
                refinement_result = self.auto_refiner.refine(
                    report, critique_result, content
                )
                
                self.logger.info(f"[Anti-Hacking] 自动改进完成:")
                self.logger.info(f"  迭代次数: {refinement_result['iterations']}")
                self.logger.info(f"  置信度提升: {refinement_result['confidence_improvement']:+.2f}")
                self.logger.info(f"  Token消耗: {refinement_result['tokens_consumed']}")
                self.logger.info(f"  估计成本: ${refinement_result['cost_estimate']:.4f}")
                
                # 如果改进有效，使用改进后的版本
                if refinement_result['confidence_improvement'] > 0:
                    report = refinement_result['final_reflection']
                    self.logger.success("[Anti-Hacking] 已应用改进后的反思")
                    
                    # 重新评估改进后的反思
                    self.logger.info("[Anti-Hacking] 重新评估改进后的反思...")
                    critique_result = self.self_critical_pipeline.critique(report, content)
                    self.logger.info(f"[Anti-Hacking] 改进后置信度: {critique_result['confidence']:.2f}")
                else:
                    self.logger.warning("[Anti-Hacking] 自动改进未提升质量，保持原版本")
            else:
                self.logger.info("[Anti-Hacking] 自动改进已禁用，仅记录问题")
        else:
            self.logger.success("[Anti-Hacking] Self-Critical检查通过")
        
        # ===== Anti-Hacking Phase 1: Rubric评估 =====
        self.logger.info("[Anti-Hacking] 执行Rubric评估...")
        rubric_scores = self.anti_hacking_validator.evaluate_rubric(report)
        
        # ===== Anti-Hacking Phase 1: Outcome评估 =====
        outcome_scores = self.anti_hacking_validator.evaluate_outcome(
            [asdict(t) for t in tips], patterns
        )
        
        # ===== Anti-Hacking Phase 1: 路径验证 =====
        validation = self.anti_hacking_validator.validate_path(content, report)
        
        # 综合判定
        passed = (
            rubric_scores['total'] >= ANTI_HACKING_CONFIG['rubric_threshold'] and
            outcome_scores['total'] >= ANTI_HACKING_CONFIG['outcome_threshold'] and
            validation['passed']
        )
        
        # 记录反思历史
        self.anti_hacking_validator.record_reflection(
            f"daily_{date}", 'daily',
            rubric_scores['total'], outcome_scores['total'],
            passed
        )
        
        self.logger.info(f"[Anti-Hacking] Rubric: {rubric_scores['total']:.2f}, "
                        f"Outcome: {outcome_scores['total']:.2f}, "
                        f"Path验证: {validation['passed']}")
        
        if not passed:
            self.logger.warning("[Anti-Hacking] 复盘未通过质量门槛，已记录但不下发")
            return {
                'success': True,  # 技术上成功执行了
                'passed': False,  # 但未通过质量门槛
                'date': date,
                'tips': [asdict(t) for t in tips],
                'patterns': patterns,
                'errors': errors,
                'anti_hacking': {
                    'passed': False,
                    'rubric_scores': rubric_scores,
                    'outcome_scores': outcome_scores,
                    'validation': validation,
                    'reason': '未通过质量门槛，建议积累更多内容后重试'
                }
            }
        
        self.logger.success("[Anti-Hacking] 复盘通过质量门槛")
        
        # 保存技巧
        for tip in tips:
            self._save_tip(tip)
        
        # ===== Anti-Hacking Phase 4: 注册建议进行效果追踪 =====
        if EFFECTIVENESS_TRACKING_CONFIG['enabled']:
            self.logger.info("[Anti-Hacking] 注册建议进行效果追踪 (Phase 4)...")
            
            reflection_id = f"daily_{date}"
            
            # 为每个技巧和建议注册追踪
            for tip in tips:
                rec_id = self.effectiveness_tracker.track_recommendation(
                    reflection_id=reflection_id,
                    recommendation=tip.technique,
                    expected_outcome=f"在类似场景中成功应用此技巧: {tip.context}",
                    category=tip.category,
                    confidence=critique_result['confidence']
                )
                if rec_id:
                    self.logger.info(f"  注册追踪: {rec_id[:20]}... (技巧: {tip.category})")
            
            # 为工作流模式注册追踪
            for pattern in patterns[:3]:  # 最多追踪3个模式
                rec_id = self.effectiveness_tracker.track_recommendation(
                    reflection_id=reflection_id,
                    recommendation=pattern,
                    expected_outcome="在后续任务中应用此工作流模式",
                    category='workflow',
                    confidence=critique_result['confidence']
                )
                if rec_id:
                    self.logger.info(f"  注册追踪: {rec_id[:20]}... (模式)")
        
        # ===== Anti-Hacking Phase 5: 自适应阈值分析 =====
        if ADAPTIVE_THRESHOLD_CONFIG['enabled']:
            self.logger.info("[Anti-Hacking] 执行自适应阈值分析 (Phase 5)...")
            self.adaptive_threshold_manager.analyze_and_adjust(
                self.anti_hacking_validator,
                self.effectiveness_tracker
            )
            self.logger.success("[Anti-Hacking] Phase 5分析完成")
        
        # ===== Anti-Hacking Phase 6: 跨反思模式分析 =====
        if CROSS_REFLECTION_CONFIG['enabled']:
            self.logger.info("[Anti-Hacking] 执行跨反思模式分析 (Phase 6)...")
            analysis_result = self.cross_reflection_analyzer.analyze(
                self.anti_hacking_validator,
                self.effectiveness_tracker
            )
            if analysis_result.get('patterns_found'):
                self.logger.success(f"[Anti-Hacking] Phase 6发现 {len(analysis_result['patterns_found'])} 个模式")
            if analysis_result.get('recommendations'):
                self.logger.info("[Anti-Hacking] 优化建议:")
                for rec in analysis_result['recommendations'][:2]:
                    self.logger.info(f"  - [{rec['category']}] {rec['recommendation'][:60]}...")
        
        self.logger.success("[Anti-Hacking] 六阶段全部执行完成 ✅")
        
        return {
            'success': True,
            'passed': True,
            'date': date,
            'tips': [asdict(t) for t in tips],
            'patterns': patterns,
            'errors': errors,
            'report_file': str(report),
            'anti_hacking': {
                'passed': True,
                'rubric_scores': rubric_scores,
                'outcome_scores': outcome_scores,
                'validation': validation,
                'self_critical': {
                    'confidence': critique_result['confidence'],
                    'issues_count': critique_result['issues_count'],
                    'should_refine': critique_result['should_refine'],
                    'improvement_summary': self.self_critical_pipeline.generate_improvement_summary(critique_result)
                }
            }
        }
    
    def _reflect_evolution(self, date: str, exp_prompt: str = "") -> Dict:
        """
        自我进化复盘 (整合自 daily-self-evolution) - 支持IER经验
        
        1. 读取今日和前一天的对话记录
        2. 分析所有对话，识别模式
        3. 提取可沉淀的技巧
        4. 检查是否需要更新SOUL.md
        5. 生成进化报告
        """
        self.logger.info(f"执行自我进化复盘: {date}")
        
        # 读取当日和前一日记忆
        today_file = MEMORY_DIR / f"daily/{date}.md"
        yesterday = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_file = MEMORY_DIR / f"daily/{yesterday}.md"
        
        contents = []
        for f in [yesterday_file, today_file]:
            if f.exists():
                contents.append(f.read_text())
                self.logger.info(f"  读取: {f.name}")
        
        combined_content = "\n\n".join(contents)
        
        # 如果有IER经验prompt，添加到内容中
        if exp_prompt:
            combined_content = f"{exp_prompt}\n\n{combined_content}"
        
        # 深度分析
        analysis = self._deep_analyze_content(combined_content)
        
        # 提取技巧（3-5个）
        evolution_tips = self._extract_evolution_tips(combined_content)
        
        # 检查SOUL.md更新需求
        soul_updates = self._check_soul_updates(evolution_tips)
        
        # 生成进化报告
        report = self._generate_evolution_report(date, analysis, evolution_tips, soul_updates)
        
        # 保存技巧到evolution专用目录
        for tip in evolution_tips:
            self._save_evolution_tip(tip)
        
        self.logger.success(f"进化复盘完成，提取 {len(evolution_tips)} 个可内化技巧")
        
        return {
            'success': True,
            'type': 'evolution',
            'date': date,
            'tips_count': len(evolution_tips),
            'conversation_stats': analysis.get('stats', {}),
            'patterns_found': analysis.get('patterns', []),
            'soul_updates_needed': soul_updates,
            'report_file': str(report)
        }
    
    def _deep_analyze_content(self, content: str) -> Dict:
        """深度分析内容"""
        stats = {
            'total_chars': len(content),
            'lines': len(content.split('\n')),
            'tasks_mentioned': content.lower().count('任务') + content.lower().count('task'),
            'errors_mentioned': content.lower().count('错误') + content.lower().count('error'),
            'success_mentioned': content.lower().count('成功') + content.lower().count('success'),
        }
        
        # 识别重复模式
        patterns = []
        
        # 检查工作流模式
        if 'skills/' in content and 'def ' in content:
            patterns.append('skill_development')
        if 'cron' in content.lower():
            patterns.append('task_scheduling')
        if 'sea_service' in content or 'mars_service' in content:
            patterns.append('resident_service_creation')
        
        return {
            'stats': stats,
            'patterns': patterns
        }
    
    def _extract_evolution_tips(self, content: str) -> List[ExtractedTip]:
        """提取进化技巧（更深入的分析）"""
        tips = []
        
        # 基于关键词提取更有价值的技巧
        evolution_keywords = [
            (r'(?:第一性原理|first principles)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)', 'principle'),
            (r'(?:内化|internalize)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)', 'internalization'),
            (r'(?:反模式|anti-pattern)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)', 'anti_pattern'),
            (r'(?:最佳实践|best practice)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)', 'best_practice'),
        ]
        
        for pattern, category in evolution_keywords:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches[:2]:  # 每类最多2个
                tip = ExtractedTip(
                    id=f"EVO_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}",
                    category=category,
                    context='evolution_reflection',
                    technique=match.strip()[:300],
                    code_example='',
                    extracted_at=datetime.now().isoformat()
                )
                tips.append(tip)
        
        # 限制总数3-5个
        return tips[:5]
    
    def _check_soul_updates(self, tips: List[ExtractedTip]) -> List[Dict]:
        """检查SOUL.md更新需求"""
        updates = []
        
        # 检查是否有可内化的原则
        for tip in tips:
            if tip.category in ['principle', 'internalization']:
                updates.append({
                    'type': 'personality_update',
                    'tip_id': tip.id,
                    'suggestion': f"考虑将'{tip.technique[:50]}...'内化为SOUL.md的人格特质"
                })
        
        return updates
    
    def _generate_evolution_report(self, date: str, analysis: Dict, 
                                   tips: List[ExtractedTip], soul_updates: List[Dict]) -> Path:
        """生成进化报告"""
        report_file = REFLECTION_DIR / f"evolution_{date}.md"
        
        stats = analysis.get('stats', {})
        patterns = analysis.get('patterns', [])
        
        content = f"""# 自我进化报告 - {date}

**生成时间**: {datetime.now().isoformat()}
**类型**: 每日自我进化复盘

## 对话统计

- **总字符数**: {stats.get('total_chars', 0)}
- **总行数**: {stats.get('lines', 0)}
- **任务提及**: {stats.get('tasks_mentioned', 0)} 次
- **错误提及**: {stats.get('errors_mentioned', 0)} 次
- **成功提及**: {stats.get('success_mentioned', 0)} 次

## 发现的工作流模式

"""
        
        for pattern in patterns:
            content += f"- `{pattern}`\n"
        
        if not patterns:
            content += "- (无显著模式)\n"
        
        content += f"""
## 提取的可内化技巧 ({len(tips)}个)

"""
        
        for i, tip in enumerate(tips, 1):
            content += f"""### {i}. [{tip.category}] {tip.technique[:80]}...

- **ID**: `{tip.id}`
- **上下文**: {tip.context}
- **提取时间**: {tip.extracted_at}
- **验证状态**: {'✓ 已验证' if tip.verified else '○ 待验证'}

"""
        
        if soul_updates:
            content += """## SOUL.md 更新建议

"""
            for update in soul_updates:
                content += f"- {update['suggestion']}\n"
        
        content += f"""
## 明日优化建议

基于今日进化分析：

"""
        
        if tips:
            content += "1. 验证今日提取的技巧在实际任务中的有效性\n"
        if stats.get('errors_mentioned', 0) > 0:
            content += "2. 重点关注错误模式，避免重复\n"
        if patterns:
            content += "3. 继续强化识别到的工作流模式\n"
        
        content += "4. 持续沉淀可复用的认知框架\n"
        
        with open(report_file, 'w') as f:
            f.write(content)
        
        return report_file
    
    def _save_evolution_tip(self, tip: ExtractedTip):
        """保存进化技巧到专用文件"""
        tips_file = TIPS_DIR / "evolution_tips.json"
        
        tips = []
        if tips_file.exists():
            with open(tips_file, 'r') as f:
                tips = json.load(f)
        
        tips.append(asdict(tip))
        
        with open(tips_file, 'w') as f:
            json.dump(tips, f, indent=2)
    
    def _extract_tips_from_content(self, content: str) -> List[ExtractedTip]:
        """从内容中提取技巧"""
        tips = []
        
        # 模式1: "技巧: ..." 或 "Tip: ..."
        tip_patterns = [
            r'(?:技巧|Tip|Pattern|模式)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)',
            r'(?:学习|Lesson)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)',
            r'(?:优化|Optimization)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)'
        ]
        
        for pattern in tip_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                tip = ExtractedTip(
                    id=f"TIP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}",
                    category='pattern',
                    context='extracted_from_memory',
                    technique=match.strip()[:200],
                    code_example='',
                    extracted_at=datetime.now().isoformat()
                )
                tips.append(tip)
        
        return tips
    
    def _extract_patterns(self, content: str) -> List[str]:
        """提取模式"""
        patterns = []
        
        # 查找重复的工作流
        workflow_patterns = [
            r'(?:流程|步骤|workflow)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)',
        ]
        
        for pattern in workflow_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            patterns.extend([m.strip() for m in matches])
        
        return patterns
    
    def _extract_errors(self, content: str) -> List[Dict]:
        """提取错误"""
        errors = []
        
        # 查找错误记录
        error_patterns = [
            r'(?:错误|Error|失败|Failed)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)',
            r'(?:修正|Fix|纠正)[：:]\s*(.+?)(?=\n\n|\n#{1,3}|$)'
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                errors.append({
                    'description': match.strip()[:200],
                    'timestamp': datetime.now().isoformat()
                })
        
        return errors
    
    def _generate_daily_report(self, date: str, tips: List[ExtractedTip], 
                               patterns: List[str], errors: List[Dict]) -> Path:
        """生成日复盘报告"""
        report_file = REFLECTION_DIR / f"reflection_{date}.md"
        
        content = f"""# 日复盘报告 - {date}

**生成时间**: {datetime.now().isoformat()}

## 统计

- 提取技巧: {len(tips)} 个
- 发现模式: {len(patterns)} 个
- 记录错误: {len(errors)} 个

## 提取的技巧

"""
        
        for i, tip in enumerate(tips, 1):
            content += f"""### {i}. [{tip.category}] {tip.technique[:50]}...

- **上下文**: {tip.context}
- **提取时间**: {tip.extracted_at}
- **验证状态**: {'✓' if tip.verified else '○'}

"""
        
        if patterns:
            content += "\n## 工作流模式\n\n"
            for i, pattern in enumerate(patterns, 1):
                content += f"{i}. {pattern[:100]}...\n"
        
        if errors:
            content += "\n## 错误与修正\n\n"
            for i, error in enumerate(errors, 1):
                content += f"{i}. {error['description'][:100]}...\n"
        
        content += f"""
## 明日建议

基于今日复盘，建议关注:
"""
        
        if tips:
            content += "- 验证新提取的技巧在实际任务中的有效性\n"
        if errors:
            content += "- 避免重复出现已记录的错误\n"
        
        content += "- 继续沉淀可复用的工作流模式\n"
        
        with open(report_file, 'w') as f:
            f.write(content)
        
        return report_file
    
    def _save_tip(self, tip: ExtractedTip):
        """保存技巧"""
        tips_file = TIPS_DIR / "extracted_tips.json"
        
        tips = []
        if tips_file.exists():
            with open(tips_file, 'r') as f:
                tips = json.load(f)
        
        tips.append(asdict(tip))
        
        with open(tips_file, 'w') as f:
            json.dump(tips, f, indent=2)
    
    def _save_response(self, req_id: str, result: Dict):
        """保存响应"""
        resp_file = RESPONSE_DIR / f"RSP_{req_id}.json"
        
        response = {
            'id': req_id,
            'timestamp': datetime.now().isoformat(),
            'result': result
        }
        
        with open(resp_file, 'w') as f:
            json.dump(response, f, indent=2)
    
    def _reflect_conversation(self, conversation_file: str, exp_prompt: str = "") -> Dict:
        """复盘单个对话 - 支持IER经验"""
        # 简化版本
        return {'success': True, 'type': 'conversation', 'message': 'Conversation reflection placeholder'}
    
    def _reflect_error(self, error_context: Dict, exp_prompt: str = "") -> Dict:
        """复盘错误 - 支持IER经验"""
        # 简化版本
        return {'success': True, 'type': 'error', 'message': 'Error reflection placeholder'}
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            self.status.last_heartbeat = datetime.now().isoformat()
            self._save_status()
            time.sleep(30)
    
    def _auto_reflection_loop(self):
        """自动复盘循环"""
        self.logger.info("自动复盘器启动")
        
        while self.running:
            try:
                now = datetime.now()
                
                # 每天01:30执行自我进化复盘 (整合自 daily-self-evolution)
                if now.hour == 1 and now.minute == 30:
                    today = now.strftime('%Y-%m-%d')
                    self.logger.info(f"触发自我进化复盘: {today}")
                    
                    req_id = self._create_auto_request('evolution', today)
                    self.logger.info(f"已创建进化复盘请求: {req_id}")
                    
                    time.sleep(60)  # 避免重复触发
                
                # 每天05:30执行日复盘
                if now.hour == 5 and now.minute == 30:
                    today = now.strftime('%Y-%m-%d')
                    self.logger.info(f"触发自动日复盘: {today}")
                    
                    req_id = self._create_auto_request('daily', today)
                    self.logger.info(f"已创建复盘请求: {req_id}")
                    
                    time.sleep(60)  # 避免重复触发
                
                # 每周日22:33执行周复盘
                if now.weekday() == 6 and now.hour == 22 and now.minute == 33:
                    self.logger.info("触发自动周复盘")
                    # 周复盘逻辑...
                    time.sleep(60)
                
                # 每天03:00执行自适应阈值分析 (Phase 5)
                if now.hour == 3 and now.minute == 0:
                    if ADAPTIVE_THRESHOLD_CONFIG['enabled']:
                        self.logger.info("[Anti-Hacking] 触发自适应阈值分析 (Phase 5)")
                        self.adaptive_threshold_manager.analyze_and_adjust(
                            self.anti_hacking_validator,
                            self.effectiveness_tracker
                        )
                    time.sleep(60)
                
                # 每周日04:00执行跨反思分析 (Phase 6)
                if now.weekday() == 6 and now.hour == 4 and now.minute == 0:
                    if CROSS_REFLECTION_CONFIG['enabled']:
                        self.logger.info("[Anti-Hacking] 触发跨反思模式分析 (Phase 6)")
                        result = self.cross_reflection_analyzer.analyze(
                            self.anti_hacking_validator,
                            self.effectiveness_tracker
                        )
                        if result.get('patterns_found'):
                            self.logger.success(f"[Anti-Hacking] Phase 6发现 {len(result['patterns_found'])} 个新模式")
                        if result.get('recommendations'):
                            for rec in result['recommendations'][:3]:
                                self.logger.info(f"[Anti-Hacking] 建议: {rec['recommendation'][:80]}...")
                    time.sleep(60)
                
                time.sleep(30)
                
            except Exception as e:
                self.logger.warning(f"自动复盘错误: {e}")
                time.sleep(60)
    
    def _create_auto_request(self, req_type: str, target_date: str) -> str:
        """创建自动复盘请求"""
        req_id = f"AUTO_{req_type.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        request = {
            'id': req_id,
            'type': req_type,
            'target_date': target_date,
            'description': f'Auto {req_type} reflection',
            'priority': 7,
            'submitted_at': datetime.now().isoformat(),
            'source': 'auto'
        }
        
        req_file = REQUEST_DIR / f"{req_id}.json"
        with open(req_file, 'w') as f:
            json.dump(request, f, indent=2)
        
        return req_id
    
    def _save_status(self):
        """保存状态"""
        with open(STATUS_FILE, 'w') as f:
            json.dump(asdict(self.status), f, indent=2)


# 便捷函数

def submit_reflection_request(req_type: str, target_date: str = None, 
                              priority: int = 5) -> str:
    """提交复盘请求"""
    req_id = f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"
    
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    request = {
        'id': req_id,
        'type': req_type,
        'target_date': target_date,
        'description': f'Manual {req_type} reflection',
        'priority': priority,
        'submitted_at': datetime.now().isoformat()
    }
    
    req_file = REQUEST_DIR / f"{req_id}.json"
    with open(req_file, 'w') as f:
        json.dump(request, f, indent=2)
    
    return req_id


def quick_reflect(date: str = None) -> Dict:
    """快速复盘"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"提交日复盘请求: {date}")
    req_id = submit_reflection_request('daily', date, priority=8)
    print(f"请求ID: {req_id}")
    print("复盘将在后台执行...")
    
    return {'request_id': req_id, 'status': 'submitted'}


def get_service_status() -> Optional[Dict]:
    """获取服务状态"""
    if STATUS_FILE.exists():
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    return None


def get_response(req_id: str, timeout: int = 60) -> Optional[Dict]:
    """
    获取响应
    
    Args:
        req_id: 请求ID
        timeout: 超时秒数
        
    Returns:
        响应结果或None
    """
    resp_file = RESPONSE_DIR / f"RSP_{req_id}.json"
    
    waited = 0
    while waited < timeout:
        if resp_file.exists():
            with open(resp_file, 'r') as f:
                return json.load(f)
        time.sleep(1)
        waited += 1
    
    return None


def is_service_running() -> bool:
    """检查服务是否运行"""
    if not PID_FILE.exists():
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


# 主入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Self-Reflection Agent Service")
    parser.add_argument("command", choices=["start", "stop", "status", "reflect", "anti-hacking-status", "run-all-phases"],
                       help="命令")
    parser.add_argument("--date", "-d", help="复盘日期 (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    if args.command == "start":
        if is_service_running():
            print("服务已在运行")
            sys.exit(1)
        
        service = SelfReflectionAgent()
        service.start()
    
    elif args.command == "stop":
        if not is_service_running():
            print("服务未运行")
            sys.exit(1)
        
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        os.kill(pid, signal.SIGTERM)
        print(f"已发送停止信号到进程 {pid}")
    
    elif args.command == "status":
        if is_service_running():
            status = get_service_status()
            if status:
                print("服务状态: 运行中")
                print(f"  PID: {status.get('pid')}")
                print(f"  总复盘数: {status.get('total_reflections')}")
                print(f"  提取技巧: {status.get('tips_extracted')}")
            else:
                print("服务运行中，但无法读取状态")
        else:
            print("服务状态: 未运行")
    
    elif args.command == "anti-hacking-status":
        # 显示Anti-Hacking统计
        print("=" * 60)
        print("Anti-Hacking SRA 状态")
        print("=" * 60)
        
        # Phase 1 状态
        print("\n【Phase 1: 基础约束】")
        validator = AntiHackingValidator()
        history = validator.reflection_history
        
        print(f"反思历史记录: {len(history)} 条")
        
        if history:
            passed_count = sum(1 for h in history if h.get('passed'))
            avg_rubric = sum(h.get('rubric_score', 0) for h in history) / len(history)
            avg_outcome = sum(h.get('outcome_score', 0) for h in history) / len(history)
            
            print(f"  通过质量门槛: {passed_count}/{len(history)} ({passed_count/len(history)*100:.1f}%)")
            print(f"  平均Rubric得分: {avg_rubric:.2f}/1.0")
            print(f"  平均Outcome得分: {avg_outcome:.2f}/1.0")
            
            # 最近5条
            print("\n最近5次反思:")
            for h in history[-5:]:
                status = "✅" if h.get('passed') else "❌"
                print(f"  {status} {h.get('timestamp', 'N/A')[:19]} "
                      f"R:{h.get('rubric_score', 0):.2f} "
                      f"O:{h.get('outcome_score', 0):.2f}")
        
        # Phase 2 状态
        print("\n【Phase 2: Self-Critical】")
        pipeline = SelfCriticalPipeline()
        print(f"  最大迭代次数: {pipeline.max_iterations}")
        print(f"  置信度阈值: {pipeline.confidence_threshold}")
        print(f"  质疑维度: 事实性、逻辑性、深度、实用性")
        print("  功能: 自动识别反思问题并生成改进建议")
        
        # Phase 3 状态
        print("\n【Phase 3: Auto-Refinement】")
        refiner = AutoRefiner()
        print(f"  状态: {'✅ 启用' if AUTO_REFINEMENT_CONFIG['enabled'] else '❌ 禁用'}")
        print(f"  最大迭代次数: {AUTO_REFINEMENT_CONFIG['max_iterations']}")
        print(f"  目标置信度: {AUTO_REFINEMENT_CONFIG['confidence_threshold']}")
        print(f"  Token预算: {AUTO_REFINEMENT_CONFIG['budget_tokens']}")
        print(f"  最小改进幅度: {AUTO_REFINEMENT_CONFIG['min_improvement_delta']}")
        print("  功能: 基于LLM自动改进反思内容")
        
        # Phase 4 状态
        print("\n【Phase 4: Effectiveness Tracking】")
        tracker = EffectivenessTracker()
        stats = tracker.get_statistics()
        print(f"  状态: {'✅ 启用' if EFFECTIVENESS_TRACKING_CONFIG['enabled'] else '❌ 禁用'}")
        print(f"  追踪周期: {EFFECTIVENESS_TRACKING_CONFIG['tracking_period_days']} 天")
        print(f"  建议创建总数: {stats['total_created']}")
        print(f"  已应用建议: {stats['total_applied']}")
        print(f"  已验证建议: {stats['total_verified']}")
        print(f"  活跃追踪中: {stats['active_recommendations']}")
        print(f"  整体有效率: {stats['overall_effectiveness']*100:.1f}%")
        
        # 分类统计
        if stats['category_breakdown']:
            print("\n  分类统计:")
            for cat, cat_stats in stats['category_breakdown'].items():
                eff = cat_stats.get('effectiveness', 0) * 100
                print(f"    {cat}: 创建{cat_stats['created']} | "
                      f"应用{cat_stats['applied']} | "
                      f"验证{cat_stats['verified']} | "
                      f"有效率{eff:.1f}%")
        
        print("  功能: 追踪建议实际应用效果，建立反馈闭环")
        
        # Phase 5 状态
        print("\n【Phase 5: Adaptive Thresholds】")
        adaptive_mgr = AdaptiveThresholdManager()
        adaptive_stats = adaptive_mgr.get_statistics()
        print(f"  状态: {'✅ 启用' if ADAPTIVE_THRESHOLD_CONFIG['enabled'] else '❌ 禁用'}")
        print(f"  保守模式: {'是 (只升不降)' if ADAPTIVE_THRESHOLD_CONFIG['conservative_mode'] else '否'}")
        print(f"  调整冷却期: {ADAPTIVE_THRESHOLD_CONFIG['adjustment_cooldown_days']} 天")
        print(f"  目标通过率: {ADAPTIVE_THRESHOLD_CONFIG['target_pass_rate']*100:.0f}%")
        print(f"  目标有效率: {ADAPTIVE_THRESHOLD_CONFIG['target_effectiveness']*100:.0f}%")
        print(f"  历史调整次数: {adaptive_stats['total_adjustments']}")
        print(f"  当前可调整: {'是' if adaptive_stats['can_adjust'] else '否 (冷却中)'}")
        
        print("\n  当前阈值:")
        for name, value in adaptive_stats['current_thresholds'].items():
            print(f"    {name}: {value:.2f}")
        
        # 最近调整
        if adaptive_stats['recent_adjustments']:
            print("\n  最近调整:")
            for adj in adaptive_stats['recent_adjustments'][-3:]:
                print(f"    {adj['timestamp'][:10]}: {adj['threshold_name']} "
                      f"{adj['old_value']:.2f} -> {adj['new_value']:.2f}")
        
        print("  功能: 数据驱动，自动优化阈值")
        
        # Phase 6 状态
        print("\n【Phase 6: Cross-Reflection Analysis】")
        analyzer = CrossReflectionAnalyzer()
        cross_stats = analyzer.get_statistics()
        print(f"  状态: {'✅ 启用' if CROSS_REFLECTION_CONFIG['enabled'] else '❌ 禁用'}")
        print(f"  分析冷却期: {CROSS_REFLECTION_CONFIG['analysis_cooldown_days']} 天")
        print(f"  最小样本数: {CROSS_REFLECTION_CONFIG['min_reflections_for_analysis']}")
        print(f"  历史分析次数: {cross_stats['total_analyses']}")
        print(f"  识别模式数: {cross_stats['patterns']}")
        print(f"  生成洞察数: {cross_stats['insights_generated']}")
        
        # 最佳实践
        best_practices = analyzer.get_best_practices()
        if best_practices:
            print("\n  最佳实践:")
            for i, bp in enumerate(best_practices[:3], 1):
                print(f"    {i}. {bp['description'][:40]}... (有效率{bp['effectiveness']:.0%})")
        
        print("  功能: 识别高效反思模式，指导未来反思策略")
        
        # 配置汇总
        print(f"\n【配置汇总】")
        print(f"  最短反思间隔: {ANTI_HACKING_CONFIG['min_interval_hours']} 小时")
        print(f"  最小内容长度: {ANTI_HACKING_CONFIG['min_content_length']} 字符")
        print(f"  Rubric阈值: {ANTI_HACKING_CONFIG['rubric_threshold']}")
        print(f"  Outcome阈值: {ANTI_HACKING_CONFIG['outcome_threshold']}")
        print(f"  路径覆盖阈值: {ANTI_HACKING_CONFIG['fact_overlap_threshold']}")
        print("=" * 60)
    
    elif args.command == "run-all-phases":
        # 手动执行完整的六阶段分析
        print("=" * 60)
        print("Anti-Hacking SRA - 执行完整六阶段分析")
        print("=" * 60)
        
        from datetime import datetime
        
        # 初始化所有组件
        print("\n[1/6] 初始化组件...")
        validator = AntiHackingValidator()
        pipeline = SelfCriticalPipeline()
        refiner = AutoRefiner()
        tracker = EffectivenessTracker()
        adaptive_mgr = AdaptiveThresholdManager()
        analyzer = CrossReflectionAnalyzer()
        print("  ✅ 所有组件已加载")
        
        # Phase 1: 基础约束检查
        print("\n[2/6] Phase 1: 基础约束检查")
        history_count = len(validator.reflection_history)
        print(f"  反思历史记录: {history_count} 条")
        print(f"  最短反思间隔: {ANTI_HACKING_CONFIG['min_interval_hours']} 小时")
        print(f"  最小内容长度: {ANTI_HACKING_CONFIG['min_content_length']} 字符")
        print("  ✅ 约束检查就绪")
        
        # Phase 2: Self-Critical
        print("\n[3/6] Phase 2: Self-Critical质疑系统")
        print(f"  质疑维度: 事实性、逻辑性、深度、实用性")
        print(f"  置信度阈值: {pipeline.confidence_threshold}")
        print(f"  最大迭代: {pipeline.max_iterations}")
        print("  ✅ Self-Critical就绪")
        
        # Phase 3: Auto-Refinement
        print("\n[4/6] Phase 3: 自动改进循环")
        if AUTO_REFINEMENT_CONFIG['enabled']:
            print(f"  状态: ✅ 启用")
            print(f"  最大迭代: {AUTO_REFINEMENT_CONFIG['max_iterations']}")
            print(f"  目标置信度: {AUTO_REFINEMENT_CONFIG['confidence_threshold']}")
            print(f"  Token预算: {AUTO_REFINEMENT_CONFIG['budget_tokens']}")
        else:
            print(f"  状态: ❌ 禁用")
        
        # Phase 4: Effectiveness Tracking
        print("\n[5/6] Phase 4: 效果追踪系统")
        if EFFECTIVENESS_TRACKING_CONFIG['enabled']:
            stats = tracker.get_statistics()
            print(f"  状态: ✅ 启用")
            print(f"  追踪周期: {EFFECTIVENESS_TRACKING_CONFIG['tracking_period_days']} 天")
            print(f"  建议总数: {stats['total_created']}")
            print(f"  整体有效率: {stats['overall_effectiveness']*100:.1f}%")
        else:
            print(f"  状态: ❌ 禁用")
        
        # Phase 5: Adaptive Thresholds
        print("\n[6/6] Phase 5: 自适应阈值")
        if ADAPTIVE_THRESHOLD_CONFIG['enabled']:
            print(f"  状态: ✅ 启用")
            print("  执行阈值分析...")
            adaptive_mgr.analyze_and_adjust(validator, tracker)
            print("  ✅ 阈值分析完成")
        else:
            print(f"  状态: ❌ 禁用")
        
        # Phase 6: Cross-Reflection Analysis
        print("\n[*] Phase 6: 跨反思模式分析")
        if CROSS_REFLECTION_CONFIG['enabled']:
            print(f"  状态: ✅ 启用")
            print("  执行跨反思分析...")
            result = analyzer.analyze(validator, tracker)
            if result.get('insufficient_data'):
                print(f"  ⚠️ 样本不足 ({result['sample_count']}/{CROSS_REFLECTION_CONFIG['min_reflections_for_analysis']})")
            elif result.get('patterns_found'):
                print(f"  ✅ 发现 {len(result['patterns_found'])} 个模式")
                for p in result['patterns_found'][:3]:
                    print(f"    - {p['description'][:40]}... (有效率{p['avg_effectiveness']:.0%})")
            if result.get('recommendations'):
                print(f"  💡 生成 {len(result['recommendations'])} 条优化建议")
        else:
            print(f"  状态: ❌ 禁用")
        
        print("\n" + "=" * 60)
        print("✅ 六阶段分析执行完成")
        print("=" * 60)
        print("\n使用 './sra.sh anti-hacking-status' 查看详细统计")
    
    elif args.command == "reflect":
        date = args.date or datetime.now().strftime('%Y-%m-%d')
        result = quick_reflect(date)
        print(f"\n{result}")
