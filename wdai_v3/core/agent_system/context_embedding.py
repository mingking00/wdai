"""
wdai v3.0 - Embedding-based Context Manager
Phase 3++ : 基于LLM Embedding的 Fresh Eyes

使用向量相似度替代TF-IDF，捕捉深层语义关系
"""

import re
import math
import random
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib

from .models import Task, SubTask, NarrowContext, TodoPlan


# 简单的embedding实现（实际使用时应调用LLM API）
class SimpleEmbeddingModel:
    """
    简化版Embedding模型
    
    用于演示，实际应使用:
    - OpenAI text-embedding-ada-002
    - Sentence-BERT
    - 或其他开源embedding模型
    """
    
    def __init__(self, dim: int = 384):
        self.dim = dim
        self._cache: Dict[str, List[float]] = {}
        
        # 预定义的语义向量（用于演示）
        self._semantic_vectors = self._init_semantic_vectors()
    
    def _init_semantic_vectors(self) -> Dict[str, List[float]]:
        """初始化语义向量（简化版）"""
        # 使用随机但确定的向量表示不同语义概念
        import random
        random.seed(42)
        
        concepts = [
            # 认证相关
            "auth", "login", "password", "credential", "authenticate", "session", "token", "jwt",
            "user", "account", "identity", "verify", "security",
            # 数据库相关
            "database", "db", "sql", "query", "table", "model", "orm", "migration",
            # API相关
            "api", "endpoint", "route", "request", "response", "http", "rest",
            # 测试相关
            "test", "unit", "integration", "mock", "assert", "pytest",
            # 错误相关
            "error", "bug", "exception", "fail", "crash", "log", "debug", "fix",
            # 配置相关
            "config", "setting", "yaml", "json", "env", "environment",
            # 文档相关
            "doc", "readme", "documentation", "guide", "manual", "tutorial",
        ]
        
        vectors = {}
        for concept in concepts:
            # 使用哈希生成确定性随机向量
            hash_val = int(hashlib.md5(concept.encode()).hexdigest(), 16)
            random.seed(hash_val)
            vec = [random.uniform(-1, 1) for _ in range(self.dim)]
            # 归一化
            norm = math.sqrt(sum(x**2 for x in vec))
            vec = [x/norm for x in vec]
            vectors[concept] = vec
        
        return vectors
    
    def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量
        
        简化实现：基于关键词的加权平均
        """
        if text in self._cache:
            return self._cache[text]
        
        # 分词
        words = self._tokenize(text)
        
        if not words:
            # 返回零向量
            return [0.0] * self.dim
        
        # 收集所有匹配概念的向量
        vectors = []
        weights = []
        
        for word in words:
            # 查找最匹配的概念
            best_match = None
            best_score = 0
            
            for concept, vec in self._semantic_vectors.items():
                # 计算词与概念的相似度
                score = self._word_concept_similarity(word, concept)
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = concept
            
            if best_match:
                vectors.append(self._semantic_vectors[best_match])
                weights.append(best_score)
        
        if not vectors:
            # 没有匹配的概念，使用基于字符的哈希
            vec = self._hash_to_vector(text)
            self._cache[text] = vec
            return vec
        
        # 加权平均
        result = [0.0] * self.dim
        total_weight = sum(weights)
        
        for vec, weight in zip(vectors, weights):
            for i in range(self.dim):
                result[i] += vec[i] * weight
        
        # 归一化
        result = [x/total_weight for x in result]
        norm = math.sqrt(sum(x**2 for x in result))
        if norm > 0:
            result = [x/norm for x in result]
        
        self._cache[text] = result
        return result
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        # 拆分驼峰命名
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # 提取单词
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
        
        # 过滤停用词
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
                     'can', 'had', 'her', 'was', 'one', 'our', 'out'}
        
        return [w for w in words if w not in stop_words and len(w) > 2]
    
    def _word_concept_similarity(self, word: str, concept: str) -> float:
        """计算词与概念的相似度"""
        word = word.lower()
        concept = concept.lower()
        
        # 完全匹配
        if word == concept:
            return 1.0
        
        # 包含关系
        if word in concept or concept in word:
            return 0.8
        
        # 编辑距离（简化）
        if self._edit_distance(word, concept) <= 2:
            return 0.6
        
        return 0.0
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _hash_to_vector(self, text: str) -> List[float]:
        """将文本哈希为向量"""
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        random.seed(hash_val)
        vec = [random.uniform(-1, 1) for _ in range(self.dim)]
        norm = math.sqrt(sum(x**2 for x in vec))
        return [x/norm for x in vec]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return max(0.0, min(1.0, (dot_product + 1) / 2))  # 映射到0-1


@dataclass
class EmbeddingFileAnalysis:
    """基于Embedding的文件分析结果"""
    path: str
    relevance_score: float
    vector_similarity: float   # 向量相似度
    context_match: float       # 上下文匹配度
    importance_score: float
    content_summary: str
    embedding: List[float]     # 文件内容的embedding
    size_tokens: int
    reason: str


class EmbeddingContextManager:
    """
    基于LLM Embedding的上下文管理器
    
    使用向量空间中的语义相似度
    """
    
    def __init__(
        self,
        max_total_tokens: int = 4000,
        max_files: int = 8,
        min_relevance_threshold: float = 0.4,
        embedding_model = None
    ):
        self.max_total_tokens = max_total_tokens
        self.max_files = max_files
        self.min_relevance_threshold = min_relevance_threshold
        
        # Embedding模型
        self.embedding_model = embedding_model or SimpleEmbeddingModel()
        
        # 缓存
        self._file_embeddings: Dict[str, List[float]] = {}
    
    def narrow_context(
        self,
        task: Task,
        subtask: SubTask,
        plan: TodoPlan,
        available_files: List[str] = None,
        file_contents: Dict[str, str] = None
    ) -> NarrowContext:
        """智能裁剪上下文（基于Embedding）"""
        available_files = available_files or []
        file_contents = file_contents or {}
        
        # 1. 编码任务为向量
        task_embedding = self.embedding_model.embed(subtask.description)
        
        # 2. 分析文件相关性（基于向量相似度）
        file_analyses = self._analyze_files_with_embedding(
            subtask, available_files, file_contents, task_embedding
        )
        
        # 3. 计算动态预算
        budget = self._calculate_budget(subtask)
        
        # 4. 选择最优文件
        selected_files = self._select_optimal_files(
            file_analyses, budget.file_content
        )
        
        # 5. 构建上下文
        parent_context = self._extract_parent_context(task, budget)
        previous_results = self._extract_previous_results(subtask, plan)
        system_state = self._build_system_state(plan)
        
        context = NarrowContext(
            subtask=subtask,
            relevant_files=selected_files,
            parent_goal=task.goal,
            parent_context=parent_context,
            previous_results=previous_results,
            system_state=system_state
        )
        
        # 添加元数据
        context._metadata = {
            "budget": budget,
            "file_analyses": {fa.path: fa for fa in file_analyses},
            "task_embedding_preview": task_embedding[:5]  # 前5维用于调试
        }
        
        return context
    
    def _analyze_files_with_embedding(
        self,
        subtask: SubTask,
        available_files: List[str],
        file_contents: Dict[str, str],
        task_embedding: List[float]
    ) -> List[EmbeddingFileAnalysis]:
        """
        使用Embedding分析文件相关性
        
        核心：计算文件向量与任务向量的相似度
        """
        analyses = []
        
        for file_path in available_files:
            content = file_contents.get(file_path, "")
            
            # 1. 获取或计算文件embedding
            if file_path in self._file_embeddings:
                file_embedding = self._file_embeddings[file_path]
            else:
                # 编码文件名 + 前1000字符内容
                text_to_embed = f"{file_path}\n{content[:1000]}"
                file_embedding = self.embedding_model.embed(text_to_embed)
                self._file_embeddings[file_path] = file_embedding
            
            # 2. 计算向量相似度（核心指标）
            vector_similarity = self.embedding_model.cosine_similarity(
                task_embedding, file_embedding
            )
            
            # 3. 计算上下文匹配度
            context_match = self._calculate_context_match(
                file_path, content, subtask
            )
            
            # 4. 计算重要性
            importance = self._calculate_importance(file_path, content)
            
            # 5. 综合分数
            relevance = (
                vector_similarity * 0.7 +  # Embedding相似度权重最高
                context_match * 0.2 +
                importance * 0.1
            )
            
            # 6. 生成推荐理由
            reason = self._generate_reason(vector_similarity, context_match)
            
            analysis = EmbeddingFileAnalysis(
                path=file_path,
                relevance_score=relevance,
                vector_similarity=vector_similarity,
                context_match=context_match,
                importance_score=importance,
                content_summary=self._summarize_content(content, 150),
                embedding=file_embedding,
                size_tokens=len(content) // 4 if content else 100,
                reason=reason
            )
            
            analyses.append(analysis)
        
        return analyses
    
    def _calculate_context_match(
        self,
        file_path: str,
        content: str,
        subtask: SubTask
    ) -> float:
        """计算上下文匹配度"""
        score = 0.0
        
        # 1. 任务类型与文件类型匹配
        path_lower = file_path.lower()
        
        type_patterns = {
            "implement": [".py", ".js", ".ts", ".java", "src/"],
            "test": ["test", "spec", "_test.py"],
            "debug": ["log", "error", "debug"],
            "review": [".py", ".js", ".ts"],
            "design": [".md", ".rst", "docs/"]
        }
        
        patterns = type_patterns.get(subtask.type, [])
        if any(p in path_lower for p in patterns):
            score += 0.3
        
        # 2. 文件名与任务关键词匹配
        task_words = set(self.embedding_model._tokenize(subtask.description))
        filename = Path(file_path).stem.lower()
        
        for word in task_words:
            if word in filename:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_importance(self, file_path: str, content: str) -> float:
        """计算文件重要性"""
        score = 0.0
        
        # 1. 核心文件模式
        core_patterns = ['main', 'app', 'index', 'core', 'base', 'init']
        filename = Path(file_path).stem.lower()
        if any(p in filename for p in core_patterns):
            score += 0.3
        
        # 2. 路径深度
        depth = len(Path(file_path).parts) - 1
        if depth <= 1:
            score += 0.2
        
        # 3. 代码规模
        if content:
            lines = content.count('\n')
            if 50 < lines < 500:
                score += 0.2
        
        return min(score, 1.0)
    
    def _select_optimal_files(
        self,
        analyses: List[EmbeddingFileAnalysis],
        token_budget: int
    ) -> List[str]:
        """选择最优文件组合"""
        # 过滤低相关性
        candidates = [
            fa for fa in analyses
            if fa.relevance_score >= self.min_relevance_threshold
        ]
        
        # 按向量相似度排序
        candidates.sort(key=lambda x: x.vector_similarity, reverse=True)
        
        selected = []
        used_tokens = 0
        
        for fa in candidates:
            if used_tokens + fa.size_tokens <= token_budget and len(selected) < self.max_files:
                selected.append(fa.path)
                used_tokens += fa.size_tokens
            elif len(selected) >= self.max_files:
                break
        
        return selected
    
    def _calculate_budget(self, subtask: SubTask):
        """计算Token预算"""
        from .context_enhanced import ContextBudget
        
        total = self.max_total_tokens
        task_budget = int(total * 0.15)
        system_budget = int(total * 0.10)
        remaining = total - task_budget - system_budget
        
        complexity = 0.5 + min(len(subtask.description) / 200, 1.0)
        history_ratio = min(0.3 + complexity * 0.2, 0.55)
        
        history_budget = int(remaining * history_ratio)
        file_budget = remaining - history_budget
        
        return ContextBudget(
            total_tokens=total,
            task_description=task_budget,
            file_content=file_budget,
            history=history_budget,
            system_info=system_budget
        )
    
    def _extract_parent_context(self, task: Task, budget):
        """提取父任务上下文"""
        max_constraints = budget.task_description // 100
        return {
            "goal": task.goal,
            "constraints": task.constraints[:max(1, max_constraints)],
            "priority": task.priority
        }
    
    def _extract_previous_results(self, subtask: SubTask, plan: TodoPlan):
        """提取前置结果"""
        results = {}
        if subtask.dependencies:
            results["dependencies_count"] = len(subtask.dependencies)
        return results
    
    def _build_system_state(self, plan: TodoPlan):
        """构建系统状态"""
        progress = plan.get_progress()
        return {
            "progress": f"{progress['completed']}/{progress['total']}",
            "percentage": progress['percentage']
        }
    
    def _summarize_content(self, content: str, max_chars: int) -> str:
        """生成内容摘要"""
        if not content:
            return ""
        
        lines = content.split('\n')[:20]
        docstrings = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('"""') or line.startswith("'''") or line.startswith('#'):
                docstrings.append(line.strip('"\' #'))
        
        summary = ' '.join(docstrings[:3])
        if len(summary) > max_chars:
            summary = summary[:max_chars] + '...'
        
        return summary
    
    def _generate_reason(self, vector_sim: float, context_match: float) -> str:
        """生成推荐理由"""
        reasons = []
        
        if vector_sim > 0.7:
            reasons.append("语义高度相关")
        elif vector_sim > 0.5:
            reasons.append("语义相关")
        
        if context_match > 0.3:
            reasons.append("上下文匹配")
        
        return ", ".join(reasons) if reasons else "一般相关"
    
    def explain_selection(self, context: NarrowContext) -> str:
        """解释文件选择原因"""
        if not hasattr(context, '_metadata'):
            return "无选择信息"
        
        metadata = context._metadata
        analyses = metadata.get('file_analyses', {})
        
        lines = ["Embedding-based Fresh Eyes 文件选择:", ""]
        
        for path in context.relevant_files:
            if path in analyses:
                fa = analyses[path]
                lines.append(f"📄 {path}")
                lines.append(f"   向量相似度: {fa.vector_similarity:.2f}")
                lines.append(f"   上下文匹配: {fa.context_match:.2f}")
                lines.append(f"   重要程度: {fa.importance_score:.2f}")
                lines.append(f"   综合分数: {fa.relevance_score:.2f}")
                lines.append(f"   原因: {fa.reason}")
                lines.append("")
        
        return "\n".join(lines)


# 便捷函数
def create_embedding_context_manager(
    max_total_tokens: int = 4000,
    max_files: int = 8,
    embedding_model = None
):
    """创建基于Embedding的上下文管理器"""
    return EmbeddingContextManager(
        max_total_tokens=max_total_tokens,
        max_files=max_files,
        embedding_model=embedding_model
    )
