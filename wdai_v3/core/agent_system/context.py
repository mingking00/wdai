"""
wdai v3.0 - Context Manager
Phase 3: Agent专业化系统 - Fresh Eyes上下文管理

实现Claude Code的Fresh Eyes原则：
- Subagent只接收相关上下文
- 不包含完整工作流信息
- 不包含其他无关任务
"""

import re
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

from .models import Task, SubTask, NarrowContext, TodoPlan


@dataclass
class FileRelevance:
    """文件相关性评分"""
    path: str
    score: float  # 0-1
    reason: str


class ContextManager:
    """
    上下文管理器
    
    负责将完整上下文裁剪为窄上下文 (Fresh Eyes)
    """
    
    def __init__(self, max_files: int = 10, max_context_tokens: int = 3000):
        self.max_files = max_files
        self.max_context_tokens = max_context_tokens
    
    def narrow_context(
        self,
        task: Task,
        subtask: SubTask,
        plan: TodoPlan,
        available_files: List[str] = None
    ) -> NarrowContext:
        """
        裁剪上下文 (Fresh Eyes核心实现)
        
        Args:
            task: 父任务
            subtask: 当前子任务
            plan: 执行计划
            available_files: 可用文件列表
            
        Returns:
            窄上下文
        """
        # 1. 分析相关文件
        relevant_files = self._find_relevant_files(
            subtask, available_files or []
        )
        
        # 2. 提取父任务关键信息（非完整）
        parent_context = self._extract_parent_context(task)
        
        # 3. 提取前置任务结果
        previous_results = self._extract_previous_results(subtask, plan)
        
        # 4. 构建系统状态摘要
        system_state = self._build_system_state(plan)
        
        return NarrowContext(
            subtask=subtask,
            relevant_files=relevant_files,
            parent_goal=task.goal,
            parent_context=parent_context,
            previous_results=previous_results,
            system_state=system_state
        )
    
    def _find_relevant_files(
        self,
        subtask: SubTask,
        available_files: List[str]
    ) -> List[str]:
        """
        查找相关文件
        
        策略:
        1. 关键词匹配
        2. 文件类型匹配
        3. 路径模式匹配
        """
        if not available_files:
            return []
        
        scored_files: List[FileRelevance] = []
        
        for file_path in available_files:
            score = self._calculate_relevance(file_path, subtask)
            if score > 0:
                scored_files.append(FileRelevance(
                    path=file_path,
                    score=score,
                    reason="相关性匹配"
                ))
        
        # 按分数排序，取前N个
        scored_files.sort(key=lambda x: x.score, reverse=True)
        top_files = scored_files[:self.max_files]
        
        return [f.path for f in top_files]
    
    def _calculate_relevance(self, file_path: str, subtask: SubTask) -> float:
        """
        计算文件与任务的相关性分数
        
        Returns:
            0-1之间的分数
        """
        score = 0.0
        desc_lower = subtask.description.lower()
        path_lower = file_path.lower()
        
        # 1. 文件名包含关键词
        filename = Path(file_path).name.lower()
        
        # 提取任务关键词
        keywords = self._extract_keywords(subtask.description)
        
        for keyword in keywords:
            if keyword in filename:
                score += 0.3
            if keyword in path_lower:
                score += 0.2
        
        # 2. 文件类型匹配
        if subtask.type == "implement":
            if file_path.endswith(('.py', '.js', '.ts', '.java', '.cpp')):
                score += 0.2
        elif subtask.type == "test":
            if 'test' in file_path.lower() or file_path.endswith('_test.py'):
                score += 0.3
        elif subtask.type == "review":
            if file_path.endswith(('.py', '.js', '.ts')):
                score += 0.2
        elif subtask.type == "debug":
            if 'log' in file_path.lower() or 'error' in file_path.lower():
                score += 0.3
        
        # 3. 路径模式匹配
        if subtask.type == "implement" and 'src' in file_path:
            score += 0.1
        if subtask.type == "test" and 'test' in file_path:
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """从文本中提取关键词"""
        # 简单的关键词提取
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
        
        # 过滤停用词
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be',
            'this', 'that', 'these', 'those', 'implement', 'create', 'fix',
            'add', 'update', 'delete', 'modify', 'change', 'need', 'should'
        }
        
        keywords = {w for w in words if len(w) > 2 and w not in stop_words}
        return keywords
    
    def _extract_parent_context(self, task: Task) -> Dict[str, Any]:
        """
        提取父任务关键信息（裁剪版）
        
        只保留必要信息，不包含完整上下文
        """
        return {
            "goal": task.goal,
            "constraints": task.constraints[:3],  # 最多3个约束
            "priority": task.priority
        }
    
    def _extract_previous_results(
        self,
        subtask: SubTask,
        plan: TodoPlan
    ) -> Dict[str, Any]:
        """
        提取前置任务的结果
        
        只包含直接依赖的结果
        """
        results = {}
        
        # 这里简化处理，实际可能需要从存储中查询
        # 假设 plan 中包含了之前的结果
        
        return results
    
    def _build_system_state(self, plan: TodoPlan) -> Dict[str, Any]:
        """构建系统状态摘要"""
        progress = plan.get_progress()
        
        return {
            "progress": f"{progress['completed']}/{progress['total']}",
            "percentage": progress['percentage']
        }
    
    def estimate_tokens(self, context: NarrowContext) -> int:
        """
        估算上下文token数
        
        简单估算: 英文约4字符/token，中文约1.5字符/token
        """
        text = context.to_prompt_context()
        
        # 简单估算
        char_count = len(text)
        estimated_tokens = char_count // 4
        
        return estimated_tokens
    
    def is_context_too_large(self, context: NarrowContext) -> bool:
        """检查上下文是否过大"""
        return self.estimate_tokens(context) > self.max_context_tokens
    
    def compress_context(self, context: NarrowContext) -> NarrowContext:
        """
        压缩上下文
        
        策略:
        1. 减少文件数量
        2. 截断长文本
        3. 简化历史
        """
        # 减少文件数量
        if len(context.relevant_files) > 5:
            context.relevant_files = context.relevant_files[:5]
        
        # 简化父上下文
        if len(context.parent_context.get("constraints", [])) > 2:
            context.parent_context["constraints"] = context.parent_context["constraints"][:2]
        
        return context


class SimpleContextManager(ContextManager):
    """简化版上下文管理器"""
    
    def narrow_context(
        self,
        task: Task,
        subtask: SubTask,
        plan: TodoPlan,
        available_files: List[str] = None
    ) -> NarrowContext:
        """简化实现"""
        # 简单过滤：任务描述中的关键词
        relevant_files = []
        
        if available_files:
            keywords = self._extract_keywords(subtask.description)
            for file_path in available_files:
                if any(kw in file_path.lower() for kw in keywords):
                    relevant_files.append(file_path)
            
            relevant_files = relevant_files[:self.max_files]
        
        return NarrowContext(
            subtask=subtask,
            relevant_files=relevant_files,
            parent_goal=task.goal,
            parent_context={"constraints": task.constraints[:2]},
            previous_results={},
            system_state={"progress": f"{plan.get_progress()['completed']}/{plan.get_progress()['total']}"}
        )


# 便捷函数
def create_context_manager(max_files: int = 10) -> ContextManager:
    """创建上下文管理器"""
    return ContextManager(max_files=max_files)
