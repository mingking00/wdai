#!/usr/bin/env python3
"""
SRA-IER: Self-Reflection Agent - Iterative Experience Refinement
自我复盘Agent的迭代经验精炼系统

基于ChatDev IER论文，适配SRA场景：
- 复盘方法提取
- 技巧识别模式
- 错误模式学习
- 进化策略积累
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# IER存储路径
IER_DIR = Path('/root/.openclaw/workspace/skills/self-reflection-agent/ier')
IER_DIR.mkdir(exist_ok=True)

EXPERIENCE_FILE = IER_DIR / 'experiences.json'
TASK_HISTORY_FILE = IER_DIR / 'task_history.json'
REFLECTION_METHODS_FILE = IER_DIR / 'reflection_methods.json'

def ensure_files():
    """确保文件存在"""
    for f in [EXPERIENCE_FILE, TASK_HISTORY_FILE, REFLECTION_METHODS_FILE]:
        if not f.exists():
            with open(f, 'w') as fp:
                json.dump({}, fp)

ensure_files()

class ReflectionExperienceType(Enum):
    """SRA经验类型"""
    REFLECTION_METHOD = "reflection_method"   # 复盘方法
    TIP_EXTRACTION = "tip_extraction"         # 技巧提取模式
    ERROR_PATTERN = "error_pattern"           # 错误识别模式
    EVOLUTION_STRATEGY = "evolution_strategy" # 进化策略
    INSIGHT_PATTERN = "insight_pattern"       # 洞察发现模式
    SOUL_UPDATE = "soul_update"               # SOUL.md更新模式
    CONVERSATION_ANALYSIS = "conversation_analysis"  # 对话分析方法
    LESSON_LEARNED = "lesson_learned"         # 教训总结

class ExperienceStatus(Enum):
    """经验状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    ELIMINATED = "eliminated"

@dataclass
class ReflectionExperience:
    """复盘经验条目"""
    id: str
    exp_type: ReflectionExperienceType
    name: str
    description: str
    context: str                                # 适用场景
    method: str                                 # 方法/技巧内容
    trigger_pattern: str                        # 触发模式（什么情况下使用）
    expected_outcome: str                       # 预期效果
    code_example: Optional[str] = None          # 代码示例（如有）
    source_reflection: Optional[str] = None     # 来源复盘报告ID
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    status: ExperienceStatus = ExperienceStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    related_exps: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.0            # 效果评分
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['exp_type'] = self.exp_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReflectionExperience':
        data['exp_type'] = ReflectionExperienceType(data['exp_type'])
        data['status'] = ExperienceStatus(data['status'])
        return cls(**data)
    
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    def is_reliable(self) -> bool:
        """判断是否可靠"""
        return self.usage_count >= 3 and self.success_rate() >= 0.7

@dataclass
class ReflectionTask:
    """复盘任务记录"""
    task_id: str
    task_type: str                            # daily/weekly/conversation/evolution
    target_date: str
    description: str
    created_at: str
    completed_at: Optional[str] = None
    success: bool = False
    tips_extracted: int = 0
    experiences_used: List[str] = field(default_factory=list)
    experiences_generated: List[str] = field(default_factory=list)
    reflection_quality: float = 0.0           # 复盘质量评分
    error_info: Optional[str] = None

class SRAExperienceManager:
    """SRA经验管理器"""
    
    def __init__(self):
        self.experiences: Dict[str, ReflectionExperience] = {}
        self.task_history: Dict[str, ReflectionTask] = {}
        self.reflection_methods: Dict[str, Dict] = {}
        self.load()
    
    def load(self):
        """加载经验数据"""
        if EXPERIENCE_FILE.exists():
            with open(EXPERIENCE_FILE, 'r') as f:
                data = json.load(f)
                self.experiences = {
                    k: ReflectionExperience.from_dict(v) for k, v in data.items()
                }
        
        if TASK_HISTORY_FILE.exists():
            with open(TASK_HISTORY_FILE, 'r') as f:
                data = json.load(f)
                self.task_history = {
                    k: ReflectionTask(**v) for k, v in data.items()
                }
        
        if REFLECTION_METHODS_FILE.exists():
            with open(REFLECTION_METHODS_FILE, 'r') as f:
                self.reflection_methods = json.load(f)
    
    def save(self):
        """保存经验数据"""
        with open(EXPERIENCE_FILE, 'w') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.experiences.items()},
                f, indent=2, ensure_ascii=False
            )
        
        with open(TASK_HISTORY_FILE, 'w') as f:
            json.dump(
                {k: asdict(v) for k, v in self.task_history.items()},
                f, indent=2, ensure_ascii=False
            )
        
        with open(REFLECTION_METHODS_FILE, 'w') as f:
            json.dump(self.reflection_methods, f, indent=2, ensure_ascii=False)
    
    # ==================== 1. 经验获取 ====================
    
    def acquire_from_reflection(self, task_id: str, task_type: str,
                                reflection_report: Dict, tips: List[Dict],
                                reflection_success: bool) -> List[ReflectionExperience]:
        """
        从复盘报告中提取经验
        
        Args:
            task_id: 任务ID
            task_type: 任务类型 (daily/weekly/evolution)
            reflection_report: 复盘报告内容
            tips: 提取的技巧列表
            reflection_success: 复盘是否成功
        
        Returns:
            提取的经验列表
        """
        new_experiences = []
        
        # 1. 提取复盘方法
        method_exp = self._extract_reflection_method(
            task_type, reflection_report
        )
        if method_exp:
            new_experiences.append(method_exp)
        
        # 2. 从技巧中提取经验
        for tip in tips:
            tip_exp = self._extract_tip_experience(tip)
            if tip_exp:
                new_experiences.append(tip_exp)
        
        # 3. 提取洞察发现模式
        insight_exp = self._extract_insight_pattern(reflection_report)
        if insight_exp:
            new_experiences.append(insight_exp)
        
        # 4. 提取错误模式（如果有错误）
        if not reflection_success:
            error_exp = self._extract_error_pattern(reflection_report)
            if error_exp:
                new_experiences.append(error_exp)
        
        # 5. 提取进化策略（如果是进化任务）
        if task_type == 'evolution':
            strategy_exp = self._extract_evolution_strategy(reflection_report)
            if strategy_exp:
                new_experiences.append(strategy_exp)
        
        # 保存新经验
        for exp in new_experiences:
            exp.source_reflection = task_id
            exp.effectiveness_score = 1.0 if reflection_success else 0.3
            self.experiences[exp.id] = exp
            self._update_method_index(exp)
        
        # 更新任务记录
        if task_id in self.task_history:
            self.task_history[task_id].experiences_generated = [
                exp.id for exp in new_experiences
            ]
            self.task_history[task_id].tips_extracted = len(tips)
        
        self.save()
        return new_experiences
    
    def _extract_reflection_method(self, task_type: str, report: Dict) -> Optional[ReflectionExperience]:
        """提取复盘方法"""
        # 识别复盘方法
        method_name = ""
        context = ""
        
        if task_type == 'daily':
            method_name = "Daily Reflection"
            context = "每日对话复盘"
        elif task_type == 'weekly':
            method_name = "Weekly Reflection"
            context = "每周总结复盘"
        elif task_type == 'evolution':
            method_name = "Evolution Reflection"
            context = "自我进化复盘"
        elif task_type == 'conversation':
            method_name = "Conversation Analysis"
            context = "单轮对话深度分析"
        else:
            return None
        
        exp_id = f"REFL_{self._hash(method_name + task_type)}"
        
        if exp_id in self.experiences:
            return None
        
        # 从报告中提取方法描述
        approach = report.get('approach', '')
        findings = report.get('findings', [])
        
        return ReflectionExperience(
            id=exp_id,
            exp_type=ReflectionExperienceType.REFLECTION_METHOD,
            name=f"Method: {method_name}",
            description=f"{task_type}类型的复盘方法",
            context=context,
            method=approach[:500] if approach else f"执行{task_type}复盘的标准流程",
            trigger_pattern=f"当需要执行{context}时",
            expected_outcome=f"生成复盘报告，提取{len(findings)}个发现" if findings else "生成完整复盘报告",
            tags=["reflection", task_type]
        )
    
    def _extract_tip_experience(self, tip: Dict) -> Optional[ReflectionExperience]:
        """从技巧中提取经验"""
        tip_category = tip.get('category', 'pattern')
        tip_context = tip.get('context', '')
        tip_technique = tip.get('technique', '')
        
        if not tip_technique:
            return None
        
        exp_id = f"TIP_{self._hash(tip_context + tip_technique)}"
        
        if exp_id in self.experiences:
            return None
        
        # 映射到经验类型
        type_map = {
            'pattern': ReflectionExperienceType.TIP_EXTRACTION,
            'tool': ReflectionExperienceType.LESSON_LEARNED,
            'lesson': ReflectionExperienceType.LESSON_LEARNED,
            'optimization': ReflectionExperienceType.INSIGHT_PATTERN
        }
        
        return ReflectionExperience(
            id=exp_id,
            exp_type=type_map.get(tip_category, ReflectionExperienceType.TIP_EXTRACTION),
            name=f"Tip: {tip_technique[:50]}...",
            description=f"从'{tip_context[:50]}...'中提取的技巧",
            context=tip_context,
            method=tip_technique,
            trigger_pattern=tip_context,
            expected_outcome="提高类似场景的处理效率",
            code_example=tip.get('code_example'),
            tags=["tip", tip_category]
        )
    
    def _extract_insight_pattern(self, report: Dict) -> Optional[ReflectionExperience]:
        """提取洞察发现模式"""
        findings = report.get('findings', [])
        insights = report.get('insights', [])
        
        if not findings and not insights:
            return None
        
        exp_id = f"INSIGHT_{self._hash(str(findings))}"
        
        if exp_id in self.experiences:
            return None
        
        # 识别洞察类型
        insight_text = "; ".join(findings[:3]) if findings else "; ".join(insights[:3])
        
        return ReflectionExperience(
            id=exp_id,
            exp_type=ReflectionExperienceType.INSIGHT_PATTERN,
            name=f"Insight: {insight_text[:40]}...",
            description="从复盘中发现的洞察模式",
            context="对话分析和复盘过程",
            method="通过分析对话历史识别模式和改进点",
            trigger_pattern="对话数量达到一定阈值或发现异常模式",
            expected_outcome="发现可改进的模式和技巧",
            tags=["insight", "pattern"]
        )
    
    def _extract_error_pattern(self, report: Dict) -> Optional[ReflectionExperience]:
        """提取错误模式"""
        errors = report.get('errors', [])
        error_info = report.get('error_info', '')
        
        if not errors and not error_info:
            return None
        
        error_desc = errors[0] if errors else error_info
        exp_id = f"ERROR_{self._hash(error_desc)}"
        
        if exp_id in self.experiences:
            return None
        
        return ReflectionExperience(
            id=exp_id,
            exp_type=ReflectionExperienceType.ERROR_PATTERN,
            name=f"Error: {error_desc[:50]}...",
            description=f"复盘过程中遇到的错误: {error_desc}",
            context="复盘执行过程",
            method="识别并记录错误模式，避免重复",
            trigger_pattern="复盘失败或出现异常",
            expected_outcome="防止类似错误再次发生",
            tags=["error", "lesson"]
        )
    
    def _extract_evolution_strategy(self, report: Dict) -> Optional[ReflectionExperience]:
        """提取进化策略"""
        strategies = report.get('evolution_strategies', [])
        suggestions = report.get('suggestions', [])
        
        if not strategies and not suggestions:
            return None
        
        strategy_text = strategies[0] if strategies else suggestions[0]
        exp_id = f"EVO_{self._hash(strategy_text)}"
        
        if exp_id in self.experiences:
            return None
        
        return ReflectionExperience(
            id=exp_id,
            exp_type=ReflectionExperienceType.EVOLUTION_STRATEGY,
            name=f"Strategy: {strategy_text[:50]}...",
            description="自我进化的有效策略",
            context="自我复盘和进化过程",
            method=strategy_text,
            trigger_pattern="定期进化复盘或发现系统性改进机会",
            expected_outcome="系统性提升能力和效率",
            tags=["evolution", "strategy"]
        )
    
    def _hash(self, text: str) -> str:
        """生成哈希值"""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def _update_method_index(self, exp: ReflectionExperience):
        """更新方法索引"""
        if exp.exp_type == ReflectionExperienceType.REFLECTION_METHOD:
            method_name = exp.name.replace("Method: ", "")
            if method_name not in self.reflection_methods:
                self.reflection_methods[method_name] = {
                    'count': 0,
                    'examples': []
                }
            self.reflection_methods[method_name]['count'] += 1
            self.reflection_methods[method_name]['examples'].append(exp.id)
    
    # ==================== 2. 经验利用 ====================
    
    def retrieve_relevant_experiences(self, task_type: str,
                                     task_description: str,
                                     top_k: int = 5) -> List[ReflectionExperience]:
        """检索与当前复盘任务相关的经验"""
        scores = []
        
        for exp_id, exp in self.experiences.items():
            if exp.status != ExperienceStatus.ACTIVE:
                continue
            
            score = self._calculate_relevance(exp, task_type, task_description)
            scores.append((exp_id, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [self.experiences[exp_id] for exp_id, _ in scores[:top_k]]
    
    def _calculate_relevance(self, exp: ReflectionExperience,
                            task_type: str, task_desc: str) -> float:
        """计算相关性分数"""
        score = 0.0
        desc_lower = task_desc.lower()
        
        # 1. 类型匹配
        type_keywords = {
            'daily': ['daily', '每日', '日复盘'],
            'weekly': ['weekly', '每周', '周复盘'],
            'evolution': ['evolution', '进化', '自我改进'],
            'conversation': ['conversation', '对话', '单轮']
        }
        
        keywords = type_keywords.get(task_type, [])
        for kw in keywords:
            if kw in exp.context.lower() or kw in exp.tags:
                score += 2.0
        
        # 2. 标签匹配
        for tag in exp.tags:
            if tag.lower() in desc_lower:
                score += 1.5
        
        # 3. 触发模式匹配
        if exp.trigger_pattern.lower() in desc_lower:
            score += 2.0
        
        # 4. 成功率加权
        score *= (0.5 + exp.success_rate())
        
        # 5. 可靠性加权
        if exp.is_reliable():
            score *= 1.5
        
        return score
    
    def format_experiences_for_prompt(self, experiences: List[ReflectionExperience]) -> str:
        """将经验格式化为prompt"""
        if not experiences:
            return ""
        
        prompt = "\n\n===== 相关复盘经验参考 =====\n\n"
        
        for i, exp in enumerate(experiences, 1):
            prompt += f"【经验 {i}】{exp.name}\n"
            prompt += f"类型: {exp.exp_type.value}\n"
            prompt += f"场景: {exp.context}\n"
            prompt += f"方法: {exp.method[:200]}...\n" if len(exp.method) > 200 else f"方法: {exp.method}\n"
            prompt += f"触发条件: {exp.trigger_pattern}\n"
            prompt += f"成功率: {exp.success_rate():.1%}\n"
            prompt += "\n"
        
        prompt += "===== 经验参考结束 =====\n"
        return prompt
    
    # ==================== 3. 经验传播 ====================
    
    def propagate_to_similar_tasks(self, exp_id: str, 
                                   similar_task_types: List[str]) -> List[ReflectionExperience]:
        """将经验传播到相似任务类型"""
        if exp_id not in self.experiences:
            return []
        
        source_exp = self.experiences[exp_id]
        new_exps = []
        
        for task_type in similar_task_types:
            new_exp_id = f"{source_exp.id}_V2_{self._hash(task_type)}"
            
            if new_exp_id in self.experiences:
                continue
            
            new_exp = ReflectionExperience(
                id=new_exp_id,
                exp_type=source_exp.exp_type,
                name=f"{source_exp.name} (Adapted for {task_type})",
                description=f"从{source_exp.name}适配到{task_type}场景",
                context=f"适用于{task_type}类型的复盘",
                method=source_exp.method,
                trigger_pattern=f"执行{task_type}类型复盘时",
                expected_outcome=source_exp.expected_outcome,
                related_exps=[exp_id]
            )
            
            new_exps.append(new_exp)
            self.experiences[new_exp_id] = new_exp
        
        if new_exps:
            self.save()
        
        return new_exps
    
    # ==================== 4. 经验淘汰 ====================
    
    def evaluate_and_eliminate(self) -> List[str]:
        """评估并淘汰不合格经验"""
        eliminated = []
        
        for exp_id, exp in list(self.experiences.items()):
            should_eliminate = False
            reason = ""
            
            # 1. 成功率过低
            if exp.usage_count >= 5 and exp.success_rate() < 0.3:
                should_eliminate = True
                reason = f"成功率过低 ({exp.success_rate():.1%})"
            
            # 2. 长期未使用
            last_used = datetime.fromisoformat(exp.updated_at)
            if datetime.now() - last_used > timedelta(days=90) and exp.usage_count < 3:
                should_eliminate = True
                reason = "长期未使用"
            
            # 3. 效果评分过低
            if exp.effectiveness_score < 0.3 and exp.usage_count > 2:
                should_eliminate = True
                reason = "效果评分过低"
            
            if should_eliminate:
                exp.status = ExperienceStatus.ELIMINATED
                eliminated.append(exp_id)
                print(f"[SRA-IER] 淘汰经验: {exp.name} - 原因: {reason}")
        
        if eliminated:
            self.save()
        
        return eliminated
    
    def report_usage_result(self, exp_id: str, success: bool, quality_score: float = 0.5):
        """报告经验使用结果"""
        if exp_id not in self.experiences:
            return
        
        exp = self.experiences[exp_id]
        exp.usage_count += 1
        
        if success:
            exp.success_count += 1
            exp.effectiveness_score = min(1.0, exp.effectiveness_score + quality_score * 0.1)
        else:
            exp.failure_count += 1
            exp.effectiveness_score = max(0.0, exp.effectiveness_score - 0.15)
        
        exp.updated_at = datetime.now().isoformat()
        
        # 调整状态
        if exp.usage_count >= 3:
            if exp.success_rate() < 0.3:
                exp.status = ExperienceStatus.SUSPENDED
            elif exp.success_rate() >= 0.7:
                exp.status = ExperienceStatus.ACTIVE
        
        self.save()
    
    # ==================== 辅助方法 ====================
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = len(self.experiences)
        active = sum(1 for e in self.experiences.values() if e.status == ExperienceStatus.ACTIVE)
        reliable = sum(1 for e in self.experiences.values() if e.is_reliable())
        
        by_type = {}
        for exp in self.experiences.values():
            t = exp.exp_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total_experiences": total,
            "active_experiences": active,
            "reliable_experiences": reliable,
            "by_type": by_type,
            "total_tasks": len(self.task_history),
            "reflection_methods": len(self.reflection_methods)
        }
    
    def list_experiences(self, exp_type: Optional[str] = None) -> List[Dict]:
        """列出经验"""
        exps = []
        for exp in self.experiences.values():
            if exp_type and exp.exp_type.value != exp_type:
                continue
            exps.append({
                'id': exp.id,
                'name': exp.name,
                'type': exp.exp_type.value,
                'context': exp.context[:100],
                'success_rate': exp.success_rate(),
                'usage_count': exp.usage_count,
                'effectiveness': exp.effectiveness_score,
                'status': exp.status.value
            })
        return exps
    
    def record_task_start(self, task_id: str, task_type: str, 
                         target_date: str, description: str):
        """记录任务开始"""
        self.task_history[task_id] = ReflectionTask(
            task_id=task_id,
            task_type=task_type,
            target_date=target_date,
            description=description,
            created_at=datetime.now().isoformat()
        )
        self.save()
    
    def record_task_complete(self, task_id: str, success: bool, 
                            tips_count: int = 0,
                            quality_score: float = 0.0,
                            error_info: str = None):
        """记录任务完成"""
        if task_id in self.task_history:
            task = self.task_history[task_id]
            task.completed_at = datetime.now().isoformat()
            task.success = success
            task.tips_extracted = tips_count
            task.reflection_quality = quality_score
            task.error_info = error_info
            self.save()


# 全局实例
_exp_manager: Optional[SRAExperienceManager] = None

def get_sra_experience_manager() -> SRAExperienceManager:
    """获取SRA经验管理器"""
    global _exp_manager
    if _exp_manager is None:
        _exp_manager = SRAExperienceManager()
    return _exp_manager


if __name__ == "__main__":
    # 测试
    manager = get_sra_experience_manager()
    print("SRA-IER系统测试")
    print(f"当前经验数: {len(manager.experiences)}")
    print(f"统计数据: {manager.get_statistics()}")
