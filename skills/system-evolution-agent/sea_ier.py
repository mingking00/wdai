#!/usr/bin/env python3
"""
SEA-IER: System Evolution Agent - Iterative Experience Refinement
系统进化Agent的迭代经验精炼系统

基于ChatDev IER论文，适配SEA场景：
- 代码改进模式提取
- 重构技巧积累
- 设计决策记录
- 失败模式学习
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import re

# IER存储路径
IER_DIR = Path('/root/.openclaw/workspace/skills/system-evolution-agent/ier')
IER_DIR.mkdir(exist_ok=True)

EXPERIENCE_FILE = IER_DIR / 'experiences.json'
TASK_HISTORY_FILE = IER_DIR / 'task_history.json'
REFACTORING_PATTERNS_FILE = IER_DIR / 'refactoring_patterns.json'

def ensure_files():
    """确保文件存在"""
    for f in [EXPERIENCE_FILE, TASK_HISTORY_FILE, REFACTORING_PATTERNS_FILE]:
        if not f.exists():
            with open(f, 'w') as fp:
                json.dump({}, fp)

ensure_files()

class EvolutionExperienceType(Enum):
    """SEA经验类型"""
    REFACTORING = "refactoring"       # 重构模式
    CODE_PATTERN = "code_pattern"     # 代码改进模式
    DESIGN_DECISION = "design_decision"  # 设计决策
    ERROR_FIX = "error_fix"           # 错误修复模式
    PERFORMANCE = "performance"       # 性能优化
    INTEGRATION = "integration"       # 集成模式
    TOOL_USAGE = "tool_usage"         # 工具使用技巧
    ANTI_PATTERN = "anti_pattern"     # 需要避免的做法

class ExperienceStatus(Enum):
    """经验状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    ELIMINATED = "eliminated"

@dataclass
class EvolutionExperience:
    """进化经验条目"""
    id: str
    exp_type: EvolutionExperienceType
    name: str
    description: str
    context: str                        # 适用场景
    before_pattern: str                 # 改进前模式
    after_pattern: str                  # 改进后模式
    code_example: Optional[str] = None
    source_task: Optional[str] = None
    file_types: List[str] = field(default_factory=list)  # 适用文件类型
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    status: ExperienceStatus = ExperienceStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    related_exps: List[str] = field(default_factory=list)
    confidence_score: float = 0.0       # 置信度（基于验证次数）
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['exp_type'] = self.exp_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EvolutionExperience':
        data['exp_type'] = EvolutionExperienceType(data['exp_type'])
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
class EvolutionTask:
    """进化任务记录"""
    task_id: str
    description: str
    target_files: List[str]
    change_type: str                    # improve/refactor/fix/optimize
    created_at: str
    completed_at: Optional[str] = None
    success: bool = False
    experiences_used: List[str] = field(default_factory=list)
    experiences_generated: List[str] = field(default_factory=list)
    rollback_needed: bool = False
    error_info: Optional[str] = None

class SEAExperienceManager:
    """SEA经验管理器"""
    
    def __init__(self):
        self.experiences: Dict[str, EvolutionExperience] = {}
        self.task_history: Dict[str, EvolutionTask] = {}
        self.refactoring_patterns: Dict[str, Dict] = {}
        self.load()
    
    def load(self):
        """加载经验数据"""
        if EXPERIENCE_FILE.exists():
            with open(EXPERIENCE_FILE, 'r') as f:
                data = json.load(f)
                self.experiences = {
                    k: EvolutionExperience.from_dict(v) for k, v in data.items()
                }
        
        if TASK_HISTORY_FILE.exists():
            with open(TASK_HISTORY_FILE, 'r') as f:
                data = json.load(f)
                self.task_history = {
                    k: EvolutionTask(**v) for k, v in data.items()
                }
        
        if REFACTORING_PATTERNS_FILE.exists():
            with open(REFACTORING_PATTERNS_FILE, 'r') as f:
                self.refactoring_patterns = json.load(f)
    
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
        
        with open(REFACTORING_PATTERNS_FILE, 'w') as f:
            json.dump(self.refactoring_patterns, f, indent=2, ensure_ascii=False)
    
    # ==================== 1. 经验获取 ====================
    
    def acquire_from_change(self, task_id: str, description: str,
                           change_diff: str, file_path: str,
                           change_success: bool) -> List[EvolutionExperience]:
        """
        从代码变更中提取经验
        
        Args:
            task_id: 任务ID
            description: 改进描述
            change_diff: 代码diff
            file_path: 修改的文件路径
            change_success: 变更是否成功
        
        Returns:
            提取的经验列表
        """
        new_experiences = []
        
        # 1. 提取重构模式
        refactoring_exp = self._extract_refactoring_experience(
            description, change_diff, file_path
        )
        if refactoring_exp:
            new_experiences.append(refactoring_exp)
        
        # 2. 提取代码改进模式
        code_pattern_exp = self._extract_code_pattern_experience(
            description, change_diff, file_path
        )
        if code_pattern_exp:
            new_experiences.append(code_pattern_exp)
        
        # 3. 提取设计决策
        design_exp = self._extract_design_decision(description, change_diff)
        if design_exp:
            new_experiences.append(design_exp)
        
        # 4. 如果是修复，提取错误修复模式
        if 'fix' in description.lower() or '修复' in description:
            fix_exp = self._extract_error_fix_pattern(description, change_diff)
            if fix_exp:
                new_experiences.append(fix_exp)
        
        # 5. 提取性能优化模式
        if 'performance' in description.lower() or '优化' in description:
            perf_exp = self._extract_performance_pattern(description, change_diff)
            if perf_exp:
                new_experiences.append(perf_exp)
        
        # 保存新经验
        for exp in new_experiences:
            exp.source_task = task_id
            exp.confidence_score = 1.0 if change_success else 0.3
            self.experiences[exp.id] = exp
            self._update_refactoring_index(exp)
        
        # 更新任务记录
        if task_id in self.task_history:
            self.task_history[task_id].experiences_generated = [
                exp.id for exp in new_experiences
            ]
        
        self.save()
        return new_experiences
    
    def _extract_refactoring_experience(self, desc: str, diff: str, 
                                        file_path: str) -> Optional[EvolutionExperience]:
        """提取重构经验"""
        # 识别重构类型
        refactoring_types = self._detect_refactoring_type(diff)
        
        if not refactoring_types:
            return None
        
        ref_type = refactoring_types[0]
        exp_id = f"REF_{self._hash(desc + ref_type)}"
        
        if exp_id in self.experiences:
            return None
        
        # 提取变更前后
        before, after = self._extract_before_after(diff)
        
        return EvolutionExperience(
            id=exp_id,
            exp_type=EvolutionExperienceType.REFACTORING,
            name=f"Refactoring: {ref_type}",
            description=f"在{file_path}中应用{ref_type}重构",
            context=f"适用于需要{ref_type}重构的场景",
            before_pattern=before[:500] if before else "",
            after_pattern=after[:500] if after else "",
            code_example=after[:1000] if after else None,
            file_types=[Path(file_path).suffix],
            tags=["refactoring", ref_type.lower().replace(' ', '_')]
        )
    
    def _extract_code_pattern_experience(self, desc: str, diff: str,
                                         file_path: str) -> Optional[EvolutionExperience]:
        """提取代码改进模式"""
        # 识别代码改进类型
        patterns = []
        
        # 错误处理改进
        if 'try' in diff and 'except' in diff:
            patterns.append({
                'name': 'Error Handling',
                'desc': '改进错误处理逻辑',
                'context': '需要健壮错误处理的场景'
            })
        
        # 日志改进
        if 'logging' in diff.lower() or 'logger' in diff.lower():
            patterns.append({
                'name': 'Logging',
                'desc': '添加或改进日志记录',
                'context': '需要可观测性的场景'
            })
        
        # 配置改进
        if 'config' in diff.lower() or 'setting' in diff.lower():
            patterns.append({
                'name': 'Configuration',
                'desc': '改进配置管理',
                'context': '需要灵活配置的场景'
            })
        
        if not patterns:
            return None
        
        pattern = patterns[0]
        exp_id = f"PAT_{self._hash(desc + pattern['name'])}"
        
        if exp_id in self.experiences:
            return None
        
        before, after = self._extract_before_after(diff)
        
        return EvolutionExperience(
            id=exp_id,
            exp_type=EvolutionExperienceType.CODE_PATTERN,
            name=f"Pattern: {pattern['name']}",
            description=pattern['desc'],
            context=pattern['context'],
            before_pattern=before[:500] if before else "",
            after_pattern=after[:500] if after else "",
            file_types=[Path(file_path).suffix],
            tags=["pattern", pattern['name'].lower()]
        )
    
    def _extract_design_decision(self, desc: str, diff: str) -> Optional[EvolutionExperience]:
        """提取设计决策"""
        # 识别架构/设计决策
        design_keywords = ['architecture', 'design', '模块化', '解耦', '分层']
        
        if not any(kw in desc.lower() for kw in design_keywords):
            return None
        
        exp_id = f"DES_{self._hash(desc)}"
        
        if exp_id in self.experiences:
            return None
        
        # 提取设计理由（从描述中）
        rationale = self._extract_rationale(desc)
        
        return EvolutionExperience(
            id=exp_id,
            exp_type=EvolutionExperienceType.DESIGN_DECISION,
            name=f"Design: {desc[:50]}...",
            description=desc,
            context="架构设计决策",
            before_pattern="",
            after_pattern=rationale,
            tags=["design", "architecture"]
        )
    
    def _extract_error_fix_pattern(self, desc: str, diff: str) -> Optional[EvolutionExperience]:
        """提取错误修复模式"""
        # 识别常见错误模式
        error_patterns = []
        
        if 'NoneType' in diff or 'None' in desc:
            error_patterns.append({
                'name': 'Null Safety',
                'desc': '添加空值检查',
                'context': '处理可能为None的值'
            })
        
        if 'index' in diff.lower() or 'range' in diff.lower():
            error_patterns.append({
                'name': 'Index Safety',
                'desc': '修复索引越界',
                'context': '列表/数组访问'
            })
        
        if 'type' in diff.lower() or isinstance(diff, str) and 'str' in diff:
            error_patterns.append({
                'name': 'Type Safety',
                'desc': '修复类型错误',
                'context': '类型转换和检查'
            })
        
        if not error_patterns:
            return None
        
        pattern = error_patterns[0]
        exp_id = f"FIX_{self._hash(desc)}"
        
        if exp_id in self.experiences:
            return None
        
        before, after = self._extract_before_after(diff)
        
        return EvolutionExperience(
            id=exp_id,
            exp_type=EvolutionExperienceType.ERROR_FIX,
            name=f"Fix: {pattern['name']}",
            description=pattern['desc'],
            context=pattern['context'],
            before_pattern=before[:500] if before else "",
            after_pattern=after[:500] if after else "",
            tags=["fix", pattern['name'].lower().replace(' ', '_')]
        )
    
    def _extract_performance_pattern(self, desc: str, diff: str) -> Optional[EvolutionExperience]:
        """提取性能优化模式"""
        perf_indicators = ['cache', 'async', 'parallel', 'lazy', 'batch']
        
        if not any(ind in diff.lower() for ind in perf_indicators):
            return None
        
        exp_id = f"PERF_{self._hash(desc)}"
        
        if exp_id in self.experiences:
            return None
        
        before, after = self._extract_before_after(diff)
        
        return EvolutionExperience(
            id=exp_id,
            exp_type=EvolutionExperienceType.PERFORMANCE,
            name=f"Performance: {desc[:40]}...",
            description=desc,
            context="性能优化场景",
            before_pattern=before[:500] if before else "",
            after_pattern=after[:500] if after else "",
            tags=["performance", "optimization"]
        )
    
    def _detect_refactoring_type(self, diff: str) -> List[str]:
        """检测重构类型"""
        types = []
        
        # 提取方法
        if 'def ' in diff and 'moved' not in diff.lower():
            types.append("Extract Method")
        
        # 内联方法
        if 'def ' not in diff and len(diff) < 500:
            types.append("Inline Method")
        
        # 重命名
        if any(kw in diff for kw in ['renamed', '改名', '重命名']):
            types.append("Rename")
        
        # 移动
        if 'moved' in diff.lower() or '移动' in diff:
            types.append("Move Method")
        
        # 简化条件
        if 'if' in diff and any(kw in diff for kw in ['simplify', '合并']):
            types.append("Simplify Conditional")
        
        return types if types else ["General Refactoring"]
    
    def _extract_before_after(self, diff: str) -> Tuple[str, str]:
        """从diff提取变更前后"""
        before_lines = []
        after_lines = []
        
        for line in diff.split('\n'):
            if line.startswith('-') and not line.startswith('---'):
                before_lines.append(line[1:])
            elif line.startswith('+') and not line.startswith('+++'):
                after_lines.append(line[1:])
        
        return '\n'.join(before_lines), '\n'.join(after_lines)
    
    def _extract_rationale(self, desc: str) -> str:
        """提取设计理由"""
        # 简单实现：返回描述的后半部分作为理由
        parts = desc.split('，')
        if len(parts) > 1:
            return '，'.join(parts[1:])
        return desc
    
    def _hash(self, text: str) -> str:
        """生成哈希值"""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def _update_refactoring_index(self, exp: EvolutionExperience):
        """更新重构索引"""
        if exp.exp_type == EvolutionExperienceType.REFACTORING:
            pattern_name = exp.name.replace("Refactoring: ", "")
            if pattern_name not in self.refactoring_patterns:
                self.refactoring_patterns[pattern_name] = {
                    'count': 0,
                    'examples': []
                }
            self.refactoring_patterns[pattern_name]['count'] += 1
            self.refactoring_patterns[pattern_name]['examples'].append(exp.id)
    
    # ==================== 2. 经验利用 ====================
    
    def retrieve_relevant_experiences(self, task_description: str,
                                     target_file: str = "",
                                     change_type: str = "") -> List[EvolutionExperience]:
        """
        检索与当前改进任务相关的经验
        """
        scores = []
        
        for exp_id, exp in self.experiences.items():
            if exp.status != ExperienceStatus.ACTIVE:
                continue
            
            score = self._calculate_relevance(exp, task_description, target_file, change_type)
            scores.append((exp_id, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [self.experiences[exp_id] for exp_id, _ in scores[:5]]
    
    def _calculate_relevance(self, exp: EvolutionExperience,
                            task_desc: str, target_file: str,
                            change_type: str) -> float:
        """计算相关性分数"""
        score = 0.0
        task_lower = task_desc.lower()
        
        # 1. 标签匹配
        for tag in exp.tags:
            if tag.lower() in task_lower:
                score += 2.0
        
        # 2. 文件类型匹配
        if target_file and exp.file_types:
            target_ext = Path(target_file).suffix
            if target_ext in exp.file_types:
                score += 1.5
        
        # 3. 改进类型匹配
        if change_type:
            type_map = {
                'refactor': EvolutionExperienceType.REFACTORING,
                'improve': EvolutionExperienceType.CODE_PATTERN,
                'fix': EvolutionExperienceType.ERROR_FIX,
                'optimize': EvolutionExperienceType.PERFORMANCE
            }
            if exp.exp_type == type_map.get(change_type):
                score += 1.0
        
        # 4. 成功率加权
        score *= (0.5 + exp.success_rate())
        
        # 5. 可靠性加权
        if exp.is_reliable():
            score *= 1.5
        
        return score
    
    def format_experiences_for_prompt(self, experiences: List[EvolutionExperience]) -> str:
        """将经验格式化为prompt"""
        if not experiences:
            return ""
        
        prompt = "\n\n===== 相关改进经验参考 =====\n\n"
        
        for i, exp in enumerate(experiences, 1):
            prompt += f"【经验 {i}】{exp.name}\n"
            prompt += f"类型: {exp.exp_type.value}\n"
            prompt += f"场景: {exp.context}\n"
            prompt += f"成功率: {exp.success_rate():.1%}\n"
            
            if exp.before_pattern and exp.after_pattern:
                prompt += f"改进示例:\n"
                prompt += f"  之前: {exp.before_pattern[:200]}...\n"
                prompt += f"  之后: {exp.after_pattern[:200]}...\n"
            
            prompt += "\n"
        
        prompt += "===== 经验参考结束 =====\n"
        return prompt
    
    # ==================== 3. 经验传播 ====================
    
    def propagate_to_similar_files(self, exp_id: str, 
                                   similar_files: List[str]) -> List[EvolutionExperience]:
        """将经验传播到相似文件"""
        if exp_id not in self.experiences:
            return []
        
        source_exp = self.experiences[exp_id]
        new_exps = []
        
        for file_path in similar_files:
            new_exp_id = f"{source_exp.id}_V{source_exp.version + 1}_{self._hash(file_path)}"
            
            if new_exp_id in self.experiences:
                continue
            
            new_exp = EvolutionExperience(
                id=new_exp_id,
                exp_type=source_exp.exp_type,
                name=f"{source_exp.name} (Applied to {Path(file_path).name})",
                description=f"从{source_exp.name}应用到{file_path}",
                context=f"适用于{file_path}的类似场景",
                before_pattern=source_exp.before_pattern,
                after_pattern=source_exp.after_pattern,
                code_example=source_exp.code_example,
                file_types=[Path(file_path).suffix],
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
            
            # 3. 低置信度且失败
            if exp.confidence_score < 0.5 and exp.failure_count > 2:
                should_eliminate = True
                reason = "低置信度且多次失败"
            
            if should_eliminate:
                exp.status = ExperienceStatus.ELIMINATED
                eliminated.append(exp_id)
                print(f"[SEA-IER] 淘汰经验: {exp.name} - 原因: {reason}")
        
        if eliminated:
            self.save()
        
        return eliminated
    
    def report_usage_result(self, exp_id: str, success: bool):
        """报告经验使用结果"""
        if exp_id not in self.experiences:
            return
        
        exp = self.experiences[exp_id]
        exp.usage_count += 1
        
        if success:
            exp.success_count += 1
            # 成功使用增加置信度
            exp.confidence_score = min(1.0, exp.confidence_score + 0.1)
        else:
            exp.failure_count += 1
            # 失败降低置信度
            exp.confidence_score = max(0.0, exp.confidence_score - 0.2)
        
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
            "refactoring_patterns": len(self.refactoring_patterns)
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
                'confidence': exp.confidence_score,
                'status': exp.status.value
            })
        return exps
    
    def record_task_start(self, task_id: str, description: str, 
                         target_files: List[str], change_type: str):
        """记录任务开始"""
        self.task_history[task_id] = EvolutionTask(
            task_id=task_id,
            description=description,
            target_files=target_files,
            change_type=change_type,
            created_at=datetime.now().isoformat()
        )
        self.save()
    
    def record_task_complete(self, task_id: str, success: bool, 
                            rollback_needed: bool = False,
                            error_info: str = None):
        """记录任务完成"""
        if task_id in self.task_history:
            task = self.task_history[task_id]
            task.completed_at = datetime.now().isoformat()
            task.success = success
            task.rollback_needed = rollback_needed
            task.error_info = error_info
            self.save()
    
    def find_similar_files(self, file_path: str, pattern: str) -> List[str]:
        """查找相似文件（用于经验传播）"""
        similar = []
        base_dir = Path(file_path).parent
        target_ext = Path(file_path).suffix
        
        for f in base_dir.rglob(f"*{target_ext}"):
            if f != Path(file_path):
                try:
                    content = f.read_text()
                    if pattern in content:
                        similar.append(str(f))
                except:
                    pass
        
        return similar[:5]  # 限制数量


# 全局实例
_exp_manager: Optional[SEAExperienceManager] = None

def get_sea_experience_manager() -> SEAExperienceManager:
    """获取SEA经验管理器"""
    global _exp_manager
    if _exp_manager is None:
        _exp_manager = SEAExperienceManager()
    return _exp_manager


if __name__ == "__main__":
    # 测试
    manager = get_sea_experience_manager()
    print("SEA-IER系统测试")
    print(f"当前经验数: {len(manager.experiences)}")
    print(f"统计数据: {manager.get_statistics()}")
