#!/usr/bin/env python3
"""
Iterative Experience Refinement (IER) - 迭代经验精炼系统

基于ChatDev论文: https://arxiv.org/abs/2405.04219

核心概念：
1. Experience Acquisition - 经验获取：从任务执行中提取经验
2. Experience Utilization - 经验利用：在新任务中应用已有经验
3. Experience Propagation - 经验传播：在Agent间共享经验
4. Experience Elimination - 经验淘汰：移除过时或错误的经验

经验类型：
- Shortcut Experience: 针对特定场景的快捷解决方案
- Pattern Experience: 可复用的设计模式
- Anti-Pattern Experience: 需要避免的反模式
- Tool Experience: 工具使用技巧
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

# 经验存储路径
IER_DIR = Path('/root/.openclaw/workspace/skills/code-dev-agent/ier')
IER_DIR.mkdir(exist_ok=True)

EXPERIENCE_FILE = IER_DIR / 'experiences.json'
EXPERIENCE_INDEX_FILE = IER_DIR / 'experience_index.json'
TASK_HISTORY_FILE = IER_DIR / 'task_history.json'

def ensure_files():
    """确保文件存在"""
    for f in [EXPERIENCE_FILE, EXPERIENCE_INDEX_FILE, TASK_HISTORY_FILE]:
        if not f.exists():
            with open(f, 'w') as fp:
                json.dump({}, fp)

ensure_files()

class ExperienceType(Enum):
    """经验类型"""
    SHORTCUT = "shortcut"           # 快捷方案：特定场景的快速解决方案
    PATTERN = "pattern"             # 设计模式：可复用的架构/代码模式
    ANTI_PATTERN = "anti_pattern"   # 反模式：需要避免的做法
    TOOL = "tool"                   # 工具技巧：工具使用经验
    LESSON = "lesson"               # 教训：从错误中学到的
    OPTIMIZATION = "optimization"   # 优化：性能/代码优化技巧

class ExperienceStatus(Enum):
    """经验状态"""
    ACTIVE = "active"               # 活跃：正在使用
    SUSPENDED = "suspended"         # 暂停：待验证
    DEPRECATED = "deprecated"       # 废弃：已过时
    ELIMINATED = "eliminated"       # 淘汰：已删除

@dataclass
class Experience:
    """经验条目"""
    id: str
    exp_type: ExperienceType
    name: str
    description: str
    context: str                                # 适用场景
    solution: str                               # 解决方案/经验内容
    code_example: Optional[str] = None          # 代码示例
    source_task: Optional[str] = None           # 来源任务ID
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0                        # 使用次数
    success_count: int = 0                      # 成功次数
    failure_count: int = 0                      # 失败次数
    status: ExperienceStatus = ExperienceStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    related_exps: List[str] = field(default_factory=list)  # 相关经验ID
    version: int = 1                            # 版本号
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['exp_type'] = self.exp_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Experience':
        data['exp_type'] = ExperienceType(data['exp_type'])
        data['status'] = ExperienceStatus(data['status'])
        return cls(**data)
    
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    def is_reliable(self) -> bool:
        """判断是否可靠（使用次数足够且成功率高）"""
        return self.usage_count >= 3 and self.success_rate() >= 0.7

@dataclass
class TaskRecord:
    """任务记录"""
    task_id: str
    description: str
    language: str
    created_at: str
    completed_at: Optional[str] = None
    success: bool = False
    experiences_used: List[str] = field(default_factory=list)
    experiences_generated: List[str] = field(default_factory=list)
    error_info: Optional[str] = None

class ExperienceManager:
    """经验管理器"""
    
    def __init__(self):
        self.experiences: Dict[str, Experience] = {}
        self.task_history: Dict[str, TaskRecord] = {}
        self.index: Dict[str, List[str]] = {}  # 标签索引
        self.load()
    
    def load(self):
        """加载经验数据"""
        # 加载经验
        if EXPERIENCE_FILE.exists():
            with open(EXPERIENCE_FILE, 'r') as f:
                data = json.load(f)
                self.experiences = {
                    k: Experience.from_dict(v) for k, v in data.items()
                }
        
        # 加载任务历史
        if TASK_HISTORY_FILE.exists():
            with open(TASK_HISTORY_FILE, 'r') as f:
                data = json.load(f)
                self.task_history = {
                    k: TaskRecord(**v) for k, v in data.items()
                }
        
        # 加载索引
        if EXPERIENCE_INDEX_FILE.exists():
            with open(EXPERIENCE_INDEX_FILE, 'r') as f:
                self.index = json.load(f)
    
    def save(self):
        """保存经验数据"""
        # 保存经验
        with open(EXPERIENCE_FILE, 'w') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.experiences.items()},
                f, indent=2, ensure_ascii=False
            )
        
        # 保存任务历史
        with open(TASK_HISTORY_FILE, 'w') as f:
            json.dump(
                {k: asdict(v) for k, v in self.task_history.items()},
                f, indent=2, ensure_ascii=False
            )
        
        # 保存索引
        with open(EXPERIENCE_INDEX_FILE, 'w') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
    
    # ==================== 1. 经验获取 (Experience Acquisition) ====================
    
    def acquire_from_task(self, task_id: str, task_description: str, 
                         chain_result: Dict, code_output: str) -> List[Experience]:
        """
        从任务执行中提取经验
        
        Args:
            task_id: 任务ID
            task_description: 任务描述
            chain_result: ChatChain执行结果
            code_output: 生成的代码
        
        Returns:
            提取的经验列表
        """
        new_experiences = []
        
        # 1. 提取Pattern经验（设计模式）
        pattern_exp = self._extract_pattern_experience(
            task_description, chain_result, code_output
        )
        if pattern_exp:
            new_experiences.append(pattern_exp)
        
        # 2. 提取Shortcut经验（针对特定场景的快捷方案）
        shortcut_exp = self._extract_shortcut_experience(
            task_description, code_output
        )
        if shortcut_exp:
            new_experiences.append(shortcut_exp)
        
        # 3. 提取Tool经验（工具使用技巧）
        tool_exp = self._extract_tool_experience(chain_result)
        if tool_exp:
            new_experiences.append(tool_exp)
        
        # 4. 提取Optimization经验（优化技巧）
        opt_exp = self._extract_optimization_experience(
            task_description, code_output
        )
        if opt_exp:
            new_experiences.append(opt_exp)
        
        # 保存新经验
        for exp in new_experiences:
            self.experiences[exp.id] = exp
            self._update_index(exp)
        
        # 更新任务记录
        if task_id in self.task_history:
            self.task_history[task_id].experiences_generated = [
                exp.id for exp in new_experiences
            ]
        
        self.save()
        return new_experiences
    
    def _extract_pattern_experience(self, task_desc: str, 
                                    chain_result: Dict, code: str) -> Optional[Experience]:
        """提取设计模式经验"""
        # 识别代码中的设计模式
        patterns = self._detect_patterns(code)
        
        if not patterns:
            return None
        
        pattern_name = patterns[0]
        exp_id = f"PAT_{self._hash(task_desc + pattern_name)}"
        
        # 检查是否已存在类似经验
        if exp_id in self.experiences:
            return None
        
        return Experience(
            id=exp_id,
            exp_type=ExperienceType.PATTERN,
            name=f"Pattern: {pattern_name}",
            description=f"在'{task_desc[:50]}...'场景中使用{pattern_name}模式",
            context=f"适用于需要{pattern_name}模式的场景",
            solution=f"使用{pattern_name}模式解决此类问题",
            code_example=self._extract_relevant_code(code),
            tags=["pattern", pattern_name.lower()]
        )
    
    def _extract_shortcut_experience(self, task_desc: str, code: str) -> Optional[Experience]:
        """提取快捷方案经验"""
        # 识别特定的解决方案
        shortcut_hint = self._detect_shortcut(task_desc, code)
        
        if not shortcut_hint:
            return None
        
        exp_id = f"SCT_{self._hash(task_desc)}"
        
        if exp_id in self.experiences:
            return None
        
        return Experience(
            id=exp_id,
            exp_type=ExperienceType.SHORTCUT,
            name=f"Shortcut: {shortcut_hint['name']}",
            description=shortcut_hint['description'],
            context=shortcut_hint['context'],
            solution=shortcut_hint['solution'],
            code_example=shortcut_hint.get('code'),
            tags=["shortcut"] + shortcut_hint.get('tags', [])
        )
    
    def _extract_tool_experience(self, chain_result: Dict) -> Optional[Experience]:
        """提取工具使用经验"""
        # 从执行过程中提取工具使用技巧
        # 这里简化处理，实际可以从对话中提取
        return None
    
    def _extract_optimization_experience(self, task_desc: str, code: str) -> Optional[Experience]:
        """提取优化经验"""
        # 识别优化技巧
        opt_hints = self._detect_optimizations(code)
        
        if not opt_hints:
            return None
        
        exp_id = f"OPT_{self._hash(task_desc)}"
        
        if exp_id in self.experiences:
            return None
        
        return Experience(
            id=exp_id,
            exp_type=ExperienceType.OPTIMIZATION,
            name=f"Optimization: {opt_hints['name']}",
            description=opt_hints['description'],
            context=opt_hints['context'],
            solution=opt_hints['solution'],
            code_example=opt_hints.get('code'),
            tags=["optimization"] + opt_hints.get('tags', [])
        )
    
    def _detect_patterns(self, code: str) -> List[str]:
        """检测代码中的设计模式"""
        patterns = []
        
        # 简单的模式检测
        if 'class' in code and 'def __init__' in code:
            if 'factory' in code.lower() or 'create' in code.lower():
                patterns.append("Factory")
            if 'singleton' in code.lower():
                patterns.append("Singleton")
            if 'observer' in code.lower():
                patterns.append("Observer")
        
        if '@' in code and 'decorator' in code.lower():
            patterns.append("Decorator")
        
        if 'with' in code and ('__enter__' in code or '__exit__' in code):
            patterns.append("Context Manager")
        
        return patterns
    
    def _detect_shortcut(self, task_desc: str, code: str) -> Optional[Dict]:
        """检测快捷方案"""
        shortcuts = []
        
        # 列表推导式
        if re.search(r'\[.*for.*in.*\]', code):
            shortcuts.append({
                'name': 'List Comprehension',
                'description': '使用列表推导式替代循环',
                'context': '需要创建列表的场景',
                'solution': '使用[x for x in iterable]语法',
                'code': '[x * 2 for x in data]',
                'tags': ['list', 'comprehension']
            })
        
        # 生成器表达式
        if re.search(r'\(.*for.*in.*\)', code) and 'yield' in code:
            shortcuts.append({
                'name': 'Generator Expression',
                'description': '使用生成器表达式节省内存',
                'context': '处理大数据集的场景',
                'solution': '使用(x for x in iterable)语法',
                'code': 'sum(x for x in data if x > 0)',
                'tags': ['generator', 'memory']
            })
        
        # functools.lru_cache
        if 'lru_cache' in code or 'cache' in code.lower():
            shortcuts.append({
                'name': 'LRU Cache',
                'description': '使用LRU缓存优化递归/重复计算',
                'context': '函数结果被重复调用的场景',
                'solution': '使用@functools.lru_cache装饰器',
                'code': '@functools.lru_cache(maxsize=128)\ndef fib(n): ...',
                'tags': ['cache', 'performance', 'recursion']
            })
        
        return shortcuts[0] if shortcuts else None
    
    def _detect_optimizations(self, code: str) -> Optional[Dict]:
        """检测优化技巧"""
        # 简化的优化检测
        if 'lru_cache' in code:
            return {
                'name': 'Memoization',
                'description': '使用缓存避免重复计算',
                'context': '递归函数或计算密集型函数',
                'solution': '使用functools.lru_cache装饰器',
                'code': '@functools.lru_cache(maxsize=None)',
                'tags': ['memoization', 'cache', 'performance']
            }
        
        if 'set' in code and 'in' in code:
            return {
                'name': 'Set Lookup',
                'description': '使用set替代list进行成员检查',
                'context': '频繁成员检查的场景',
                'solution': '将list转换为set，O(n) -> O(1)',
                'code': 'items_set = set(items)\nif x in items_set: ...',
                'tags': ['set', 'lookup', 'performance']
            }
        
        return None
    
    def _extract_relevant_code(self, code: str) -> str:
        """提取相关代码片段"""
        # 提取前1000个字符作为示例
        return code[:1000] if len(code) > 1000 else code
    
    def _hash(self, text: str) -> str:
        """生成哈希值"""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    # ==================== 2. 经验利用 (Experience Utilization) ====================
    
    def retrieve_relevant_experiences(self, task_description: str, 
                                     language: str = "python",
                                     top_k: int = 5) -> List[Experience]:
        """
        检索与当前任务相关的经验
        
        Args:
            task_description: 任务描述
            language: 编程语言
            top_k: 返回最相关的k条经验
        
        Returns:
            相关经验列表
        """
        scores = []
        
        for exp_id, exp in self.experiences.items():
            if exp.status != ExperienceStatus.ACTIVE:
                continue
            
            # 计算相关性分数
            score = self._calculate_relevance(exp, task_description, language)
            scores.append((exp_id, score))
        
        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 返回top_k
        return [self.experiences[exp_id] for exp_id, _ in scores[:top_k]]
    
    def _calculate_relevance(self, exp: Experience, 
                            task_desc: str, language: str) -> float:
        """计算经验与任务的相关性"""
        score = 0.0
        task_lower = task_desc.lower()
        
        # 1. 标签匹配
        for tag in exp.tags:
            if tag.lower() in task_lower:
                score += 2.0
        
        # 2. 上下文关键词匹配
        context_words = exp.context.lower().split()
        for word in context_words:
            if len(word) > 3 and word in task_lower:
                score += 1.0
        
        # 3. 成功率加权
        score *= (0.5 + exp.success_rate())
        
        # 4. 可靠性加权
        if exp.is_reliable():
            score *= 1.5
        
        # 5. 使用次数加权（避免过度依赖单一经验）
        if exp.usage_count > 10:
            score *= 0.9  # 稍微降低高频经验权重，鼓励多样性
        
        return score
    
    def format_experiences_for_prompt(self, experiences: List[Experience]) -> str:
        """将经验格式化为prompt"""
        if not experiences:
            return ""
        
        prompt = "\n\n===== 相关经验参考 =====\n\n"
        
        for i, exp in enumerate(experiences, 1):
            prompt += f"【经验 {i}】{exp.name}\n"
            prompt += f"类型: {exp.exp_type.value}\n"
            prompt += f"场景: {exp.context}\n"
            prompt += f"方案: {exp.solution}\n"
            prompt += f"成功率: {exp.success_rate():.1%} ({exp.success_count}/{exp.usage_count})\n"
            
            if exp.code_example:
                prompt += f"代码示例:\n```python\n{exp.code_example[:500]}\n```\n"
            
            prompt += "\n"
        
        prompt += "===== 经验参考结束 =====\n"
        
        return prompt
    
    # ==================== 3. 经验传播 (Experience Propagation) ====================
    
    def propagate_experience(self, exp_id: str, target_contexts: List[str]) -> List[Experience]:
        """
        将经验传播到新的上下文
        
        Args:
            exp_id: 经验ID
            target_contexts: 目标上下文列表
        
        Returns:
            新创建的经验列表
        """
        if exp_id not in self.experiences:
            return []
        
        source_exp = self.experiences[exp_id]
        new_exps = []
        
        for context in target_contexts:
            # 创建适配新上下文的经验
            new_exp_id = f"{source_exp.id}_V{source_exp.version + 1}_{self._hash(context)}"
            
            if new_exp_id in self.experiences:
                continue
            
            new_exp = Experience(
                id=new_exp_id,
                exp_type=source_exp.exp_type,
                name=f"{source_exp.name} (Adapted)",
                description=f"从'{source_exp.name}'适配到新上下文",
                context=context,
                solution=source_exp.solution,  # 可以在这里进行适配
                code_example=source_exp.code_example,
                related_exps=[exp_id],
                version=source_exp.version + 1
            )
            
            new_exps.append(new_exp)
            self.experiences[new_exp_id] = new_exp
            self._update_index(new_exp)
        
        if new_exps:
            self.save()
        
        return new_exps
    
    def merge_experiences(self, exp_ids: List[str]) -> Optional[Experience]:
        """合并多条相关经验"""
        exps = [self.experiences[eid] for eid in exp_ids if eid in self.experiences]
        
        if len(exps) < 2:
            return None
        
        # 创建合并后的经验
        merged_id = f"MERGED_{self._hash(''.join(exp_ids))}"
        
        merged_exp = Experience(
            id=merged_id,
            exp_type=exps[0].exp_type,
            name=f"Merged: {exps[0].name}",
            description=f"合并了{len(exps)}条相关经验",
            context="; ".join([e.context for e in exps]),
            solution="\n\n".join([e.solution for e in exps]),
            code_example="\n\n".join([e.code_example or "" for e in exps]),
            related_exps=exp_ids,
            tags=list(set([tag for e in exps for tag in e.tags]))
        )
        
        self.experiences[merged_id] = merged_exp
        self._update_index(merged_exp)
        self.save()
        
        return merged_exp
    
    # ==================== 4. 经验淘汰 (Experience Elimination) ====================
    
    def evaluate_and_eliminate(self) -> List[str]:
        """
        评估所有经验，淘汰不合格的
        
        Returns:
            被淘汰的经验ID列表
        """
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
            
            # 3. 已被更好的经验替代
            if exp.related_exps:
                for related_id in exp.related_exps:
                    if related_id in self.experiences:
                        related = self.experiences[related_id]
                        if related.version > exp.version and related.is_reliable():
                            should_eliminate = True
                            reason = f"被更好的版本替代 ({related_id})"
                            break
            
            if should_eliminate:
                exp.status = ExperienceStatus.ELIMINATED
                eliminated.append(exp_id)
                print(f"[IER] 淘汰经验: {exp.name} - 原因: {reason}")
        
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
        else:
            exp.failure_count += 1
        
        exp.updated_at = datetime.now().isoformat()
        
        # 根据成功率调整状态
        if exp.usage_count >= 3:
            if exp.success_rate() < 0.3:
                exp.status = ExperienceStatus.SUSPENDED
            elif exp.success_rate() >= 0.7:
                exp.status = ExperienceStatus.ACTIVE
        
        self.save()
    
    # ==================== 辅助方法 ====================
    
    def _update_index(self, exp: Experience):
        """更新经验索引"""
        for tag in exp.tags:
            if tag not in self.index:
                self.index[tag] = []
            if exp.id not in self.index[tag]:
                self.index[tag].append(exp.id)
    
    def get_statistics(self) -> Dict:
        """获取经验统计信息"""
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
            "total_tasks": len(self.task_history)
        }
    
    def record_task_start(self, task_id: str, description: str, language: str):
        """记录任务开始"""
        self.task_history[task_id] = TaskRecord(
            task_id=task_id,
            description=description,
            language=language,
            created_at=datetime.now().isoformat()
        )
        self.save()
    
    def record_task_complete(self, task_id: str, success: bool, error_info: str = None):
        """记录任务完成"""
        if task_id in self.task_history:
            self.task_history[task_id].completed_at = datetime.now().isoformat()
            self.task_history[task_id].success = success
            self.task_history[task_id].error_info = error_info
            self.save()


# 全局经验管理器实例
_experience_manager: Optional[ExperienceManager] = None

def get_experience_manager() -> ExperienceManager:
    """获取经验管理器实例"""
    global _experience_manager
    if _experience_manager is None:
        _experience_manager = ExperienceManager()
    return _experience_manager


if __name__ == "__main__":
    # 测试
    manager = get_experience_manager()
    
    print("IER系统测试")
    print(f"当前经验数: {len(manager.experiences)}")
    print(f"统计数据: {manager.get_statistics()}")
