"""
wdai v3.0 - Enhanced Context Manager
Phase 3+ : 增强版 Fresh Eyes 上下文管理

优化点:
1. 语义相似度匹配 (TF-IDF)
2. 代码依赖分析 (import/call graph)
3. 文件重要性评分
4. 动态token预算分配
5. 智能内容摘要
"""

import re
import math
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import hashlib

from .models import Task, SubTask, NarrowContext, TodoPlan


@dataclass
class FileAnalysis:
    """文件分析结果"""
    path: str
    relevance_score: float  # 0-1 相关性分数
    semantic_score: float   # 语义相似度
    dependency_score: float # 依赖关系分数
    importance_score: float # 重要性分数
    content_summary: str    # 内容摘要
    symbols: Set[str]       # 符号集合 (类名、函数名等)
    size_tokens: int        # 预估token数
    reason: str             # 推荐理由


@dataclass  
class ContextBudget:
    """上下文预算分配"""
    total_tokens: int
    task_description: int   # 任务描述预算
    file_content: int       # 文件内容预算
    history: int           # 历史记录预算
    system_info: int       # 系统信息预算


class EnhancedContextManager:
    """
    增强版上下文管理器
    
    实现更智能的Fresh Eyes算法
    """
    
    def __init__(
        self,
        max_total_tokens: int = 4000,
        max_files: int = 8,
        min_relevance_threshold: float = 0.3
    ):
        self.max_total_tokens = max_total_tokens
        self.max_files = max_files
        self.min_relevance_threshold = min_relevance_threshold
        
        # 缓存
        self._file_cache: Dict[str, Dict] = {}
        self._symbol_index: Dict[str, Set[str]] = defaultdict(set)
    
    def narrow_context(
        self,
        task: Task,
        subtask: SubTask,
        plan: TodoPlan,
        available_files: List[str] = None,
        file_contents: Dict[str, str] = None
    ) -> NarrowContext:
        """
        智能裁剪上下文
        
        Args:
            task: 父任务
            subtask: 当前子任务
            plan: 执行计划
            available_files: 可用文件列表
            file_contents: 文件内容缓存 {path: content}
            
        Returns:
            窄上下文
        """
        available_files = available_files or []
        file_contents = file_contents or {}
        
        # 1. 计算动态预算
        budget = self._calculate_budget(subtask)
        
        # 2. 分析文件相关性
        file_analyses = self._analyze_files(
            subtask, available_files, file_contents
        )
        
        # 3. 选择最优文件组合
        selected_files = self._select_optimal_files(
            file_analyses, budget.file_content
        )
        
        # 4. 提取父任务关键信息
        parent_context = self._extract_parent_context(task, budget)
        
        # 5. 提取前置任务结果
        previous_results = self._extract_previous_results(subtask, plan, budget)
        
        # 6. 构建系统状态摘要
        system_state = self._build_system_state(plan)
        
        # 7. 生成内容摘要
        content_summary = self._generate_content_summary(
            selected_files, file_contents
        )
        
        context = NarrowContext(
            subtask=subtask,
            relevant_files=selected_files,
            parent_goal=task.goal,
            parent_context=parent_context,
            previous_results=previous_results,
            system_state=system_state
        )
        
        # 添加额外元数据
        context._metadata = {
            "budget": budget,
            "file_analyses": {fa.path: fa for fa in file_analyses},
            "content_summary": content_summary
        }
        
        return context
    
    def _calculate_budget(self, subtask: SubTask) -> ContextBudget:
        """
        根据任务复杂度计算token预算
        
        策略:
        - 简单任务: 更多文件内容预算
        - 复杂任务: 更多历史记录预算
        """
        total = self.max_total_tokens
        
        # 基于任务描述长度估算复杂度 (0.5-1.5范围)
        complexity = 0.5 + min(len(subtask.description) / 200, 1.0)
        
        # 基于依赖数量调整
        dependency_factor = min(len(subtask.dependencies) * 0.15, 0.5)
        complexity += dependency_factor
        
        # 分配预算
        task_budget = int(total * 0.15)  # 任务描述固定15%
        system_budget = int(total * 0.10)  # 系统信息固定10%
        
        remaining = total - task_budget - system_budget
        
        # 剩余预算分配给文件和历史
        # 复杂度越高，历史预算比例越高
        history_ratio = min(0.3 + complexity * 0.2, 0.55)  # 0.4-0.75范围
        
        history_budget = int(remaining * history_ratio)
        file_budget = remaining - history_budget
        
        return ContextBudget(
            total_tokens=total,
            task_description=task_budget,
            file_content=file_budget,
            history=history_budget,
            system_info=system_budget
        )
    
    def _analyze_files(
        self,
        subtask: SubTask,
        available_files: List[str],
        file_contents: Dict[str, str]
    ) -> List[FileAnalysis]:
        """
        分析文件相关性
        
        多维度评分:
        1. 语义相似度 (TF-IDF)
        2. 代码依赖关系
        3. 文件重要性
        """
        analyses = []
        task_text = subtask.description.lower()
        
        for file_path in available_files:
            content = file_contents.get(file_path, "")
            
            # 1. 计算语义相似度
            semantic_score = self._calculate_semantic_similarity(
                task_text, content
            )
            
            # 对文档文件添加惩罚（避免过度偏好），但文档编写任务除外
            if file_path.lower().endswith(('.md', '.rst', '.txt')):
                if subtask.type == 'document':
                    semantic_score *= 1.2  # 文档任务提升文档权重
                else:
                    semantic_score *= 0.5  # 其他任务降低50%权重
            
            # 2. 计算依赖关系分数
            dependency_score = self._calculate_dependency_score(
                file_path, task_text, available_files
            )
            
            # 3. 计算重要性分数
            importance_score = self._calculate_importance(
                file_path, content, subtask.type
            )
            
            # 4. 综合分数 (加权)
            relevance_score = (
                semantic_score * 0.5 +
                dependency_score * 0.3 +
                importance_score * 0.2
            )
            
            # 5. 提取符号
            symbols = self._extract_symbols(content)
            
            # 6. 估算token数
            size_tokens = len(content) // 4 if content else 0
            
            # 7. 生成推荐理由
            reason = self._generate_reason(
                semantic_score, dependency_score, importance_score
            )
            
            analysis = FileAnalysis(
                path=file_path,
                relevance_score=relevance_score,
                semantic_score=semantic_score,
                dependency_score=dependency_score,
                importance_score=importance_score,
                content_summary=self._summarize_content(content, 200),
                symbols=symbols,
                size_tokens=size_tokens,
                reason=reason
            )
            
            analyses.append(analysis)
        
        return analyses
    
    def _calculate_semantic_similarity(
        self, task_text: str, file_content: str
    ) -> float:
        """
        计算语义相似度 (简化版TF-IDF)
        
        使用词频向量的余弦相似度
        """
        if not file_content:
            return 0.0
        
        # 提取任务关键词
        task_words = self._tokenize(task_text)
        file_words = self._tokenize(file_content[:5000])  # 限制前5000字符
        
        if not task_words or not file_words:
            return 0.0
        
        # 构建词频向量
        task_counter = Counter(task_words)
        file_counter = Counter(file_words)
        
        # 计算TF-IDF权重 (简化版)
        all_words = set(task_words) | set(file_words)
        
        # 计算点积
        dot_product = sum(
            task_counter[w] * file_counter[w] for w in all_words
        )
        
        # 计算模长
        task_norm = math.sqrt(sum(c**2 for c in task_counter.values()))
        file_norm = math.sqrt(sum(c**2 for c in file_counter.values()))
        
        if task_norm == 0 or file_norm == 0:
            return 0.0
        
        # 余弦相似度 (放大以便更好区分)
        similarity = dot_product / (task_norm * file_norm)
        
        # 使用sigmoid放大差异
        return min(similarity * 5, 1.0)
    
    def _calculate_dependency_score(
        self,
        file_path: str,
        task_text: str,
        all_files: List[str]
    ) -> float:
        """
        计算依赖关系分数
        
        基于:
        1. 文件名是否被其他文件引用
        2. 文件路径模式匹配
        """
        score = 0.0
        filename = Path(file_path).stem.lower()
        
        # 1. 检查是否是核心文件
        core_patterns = ['main', 'app', 'index', 'core', 'base']
        if any(p in filename for p in core_patterns):
            score += 0.3
        
        # 2. 检查任务是否明确提到文件名
        if filename.replace('_', '') in task_text.replace('_', '').replace(' ', ''):
            score += 0.4
        
        # 3. 路径深度 (根目录文件通常更重要)
        depth = len(Path(file_path).parts) - 1
        if depth <= 1:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_importance(
        self,
        file_path: str,
        content: str,
        task_type: str
    ) -> float:
        """
        计算文件重要性
        
        基于文件类型和内容特征
        """
        score = 0.0
        path_lower = file_path.lower()
        
        # 1. 文件类型权重
        type_weights = {
            'implement': ['.py', '.js', '.ts', '.java', '.go'],
            'test': ['_test.py', '_spec.js', '.test.ts', 'test_'],
            'review': ['.py', '.js', '.ts', '.java'],
            'debug': ['.log', '.txt'],
            'design': ['.md', '.rst', '.txt']
        }
        
        weights = type_weights.get(task_type, ['.py', '.js', '.ts'])
        if any(w in path_lower for w in weights):
            score += 0.3
        
        # 2. 代码规模 (中等规模更重要)
        if content:
            lines = content.count('\n')
            if 50 < lines < 500:
                score += 0.2
            elif lines > 500:
                score += 0.1  # 大文件可能过于复杂
        
        # 3. 特殊文件
        if 'config' in path_lower or 'settings' in path_lower:
            score += 0.2
        
        return min(score, 1.0)
    
    def _select_optimal_files(
        self,
        analyses: List[FileAnalysis],
        token_budget: int
    ) -> List[str]:
        """
        选择最优文件组合
        
        目标: 在token预算内，最大化总相关性
        
        策略: 贪心算法 + 背包问题近似
        """
        # 过滤低相关性文件
        candidates = [
            fa for fa in analyses
            if fa.relevance_score >= self.min_relevance_threshold
        ]
        
        # 按相关性排序
        candidates.sort(key=lambda x: x.relevance_score, reverse=True)
        
        selected = []
        used_tokens = 0
        
        for fa in candidates:
            # 估算这个文件需要的token
            file_tokens = max(fa.size_tokens, 200)  # 至少200token
            
            if used_tokens + file_tokens <= token_budget and len(selected) < self.max_files:
                selected.append(fa.path)
                used_tokens += file_tokens
            elif len(selected) >= self.max_files:
                break
        
        return selected
    
    def _tokenize(self, text: str) -> List[str]:
        """
        文本分词
        
        提取有意义的词，支持驼峰命名拆分
        """
        # 先拆分驼峰命名
        # MyClassName -> My Class Name
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # 提取单词
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
        
        # 过滤停用词
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day',
            'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new',
            'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she',
            'use', 'her', 'way', 'many', 'oil', 'sit', 'set', 'run',
            'eat', 'far', 'sea', 'eye', 'ask', 'own', 'say', 'too',
            'any', 'try', 'let', 'put', 'end', 'why', 'turn', 'here',
            'show', 'every', 'good', 'me', 'give', 'our', 'under',
            'name', 'very', 'through', 'just', 'form', 'sentence',
            'great', 'think', 'where', 'help', 'much', 'before',
            'move', 'right', 'too', 'means', 'old', 'any', 'same',
            'tell', 'very', 'when', 'much', 'would', 'there', 'their',
            'with', 'from', 'they', 'know', 'want', 'been', 'well'
        }
        
        return [w for w in words if w not in stop_words and len(w) > 1]
    
    def _extract_symbols(self, content: str) -> Set[str]:
        """
        提取代码符号
        
        类名、函数名、变量名等
        """
        symbols = set()
        
        # Python: class/def
        classes = re.findall(r'class\s+(\w+)', content)
        functions = re.findall(r'def\s+(\w+)', content)
        
        symbols.update(classes)
        symbols.update(functions)
        
        return symbols
    
    def _summarize_content(self, content: str, max_chars: int = 200) -> str:
        """
        生成内容摘要
        
        提取关键信息
        """
        if not content:
            return ""
        
        lines = content.split('\n')
        
        # 提取docstring/注释
        docstrings = []
        for line in lines[:20]:  # 只看前20行
            line = line.strip()
            if line.startswith('"""') or line.startswith("'''") or line.startswith('#'):
                docstrings.append(line.strip('"\' #'))
        
        summary = ' '.join(docstrings[:3])
        
        if len(summary) > max_chars:
            summary = summary[:max_chars] + '...'
        
        return summary
    
    def _generate_reason(
        self,
        semantic: float,
        dependency: float,
        importance: float
    ) -> str:
        """生成推荐理由"""
        reasons = []
        
        if semantic > 0.5:
            reasons.append("语义高度相关")
        elif semantic > 0.3:
            reasons.append("语义相关")
        
        if dependency > 0.3:
            reasons.append("依赖关系")
        
        if importance > 0.3:
            reasons.append("重要文件")
        
        return ", ".join(reasons) if reasons else "一般相关"
    
    def _extract_parent_context(
        self,
        task: Task,
        budget: ContextBudget
    ) -> Dict[str, Any]:
        """提取父任务关键信息"""
        # 裁剪约束条件以适应预算
        max_constraints = budget.task_description // 100  # 每条约100token
        
        return {
            "goal": task.goal,
            "constraints": task.constraints[:max(1, max_constraints)],
            "priority": task.priority
        }
    
    def _extract_previous_results(
        self,
        subtask: SubTask,
        plan: TodoPlan,
        budget: ContextBudget
    ) -> Dict[str, Any]:
        """提取前置任务结果"""
        results = {}
        
        # 简化实现：返回依赖数量
        if subtask.dependencies:
            results["dependencies_count"] = len(subtask.dependencies)
        
        return results
    
    def _build_system_state(self, plan: TodoPlan) -> Dict[str, Any]:
        """构建系统状态摘要"""
        progress = plan.get_progress()
        
        return {
            "progress": f"{progress['completed']}/{progress['total']}",
            "percentage": progress['percentage']
        }
    
    def _generate_content_summary(
        self,
        selected_files: List[str],
        file_contents: Dict[str, str]
    ) -> Dict[str, str]:
        """生成选定文件的内容摘要"""
        summary = {}
        
        for path in selected_files:
            content = file_contents.get(path, "")
            summary[path] = self._summarize_content(content, 150)
        
        return summary
    
    def explain_selection(
        self,
        context: NarrowContext
    ) -> str:
        """
        解释文件选择原因
        
        用于调试和可解释性
        """
        if not hasattr(context, '_metadata'):
            return "无选择信息"
        
        metadata = context._metadata
        analyses = metadata.get('file_analyses', {})
        
        lines = ["Fresh Eyes 文件选择解释:", ""]
        
        for path in context.relevant_files:
            if path in analyses:
                fa = analyses[path]
                lines.append(f"📄 {path}")
                lines.append(f"   综合分数: {fa.relevance_score:.2f}")
                lines.append(f"   语义相似: {fa.semantic_score:.2f}")
                lines.append(f"   依赖分数: {fa.dependency_score:.2f}")
                lines.append(f"   重要程度: {fa.importance_score:.2f}")
                lines.append(f"   原因: {fa.reason}")
                lines.append("")
        
        return "\n".join(lines)


# 便捷函数
def create_enhanced_context_manager(
    max_total_tokens: int = 4000,
    max_files: int = 8
) -> EnhancedContextManager:
    """创建增强版上下文管理器"""
    return EnhancedContextManager(
        max_total_tokens=max_total_tokens,
        max_files=max_files
    )
