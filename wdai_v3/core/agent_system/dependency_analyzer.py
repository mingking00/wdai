"""
wdai v3.0 - 代码依赖图分析器

分析代码的import关系、函数调用、类继承，构建依赖图
用于Fresh Eyes的上下文裁剪优化
"""

import ast
import re
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict


@dataclass
class CodeSymbol:
    """代码符号（函数、类、变量）"""
    name: str
    type: str  # 'function', 'class', 'variable', 'import'
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)  # 此符号依赖的其他符号


@dataclass
class ImportInfo:
    """导入信息"""
    module: str           # 导入的模块名
    names: List[str]      # 具体导入的名称
    is_relative: bool     # 是否是相对导入
    line_number: int
    alias: Optional[str] = None


@dataclass
class CallInfo:
    """函数调用信息"""
    callee: str           # 被调用的函数/方法名
    caller: str           # 调用者（所在函数/类）
    line_number: int
    args_count: int = 0


@dataclass
class FileAnalysis:
    """单个文件的分析结果"""
    file_path: str
    imports: List[ImportInfo] = field(default_factory=list)
    defines: List[CodeSymbol] = field(default_factory=list)
    calls: List[CallInfo] = field(default_factory=list)
    inherits: List[Tuple[str, str]] = field(default_factory=list)  # (class, parent)
    
    @property
    def defined_names(self) -> Set[str]:
        """返回此文件定义的所有名称"""
        return {s.name for s in self.defines}
    
    @property
    def imported_modules(self) -> Set[str]:
        """返回导入的所有模块"""
        modules = set()
        for imp in self.imports:
            modules.add(imp.module)
            modules.update(imp.names)
        return modules


class ASTDependencyAnalyzer:
    """
    基于AST的代码依赖分析器
    
    分析Python代码的:
    - import/from...import 语句
    - 函数/类定义
    - 函数调用
    - 类继承关系
    """
    
    def __init__(self):
        self._cache: Dict[str, FileAnalysis] = {}
    
    def analyze_file(self, file_path: str, content: str) -> FileAnalysis:
        """
        分析单个文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            FileAnalysis 分析结果
        """
        # 检查缓存
        cache_key = f"{file_path}:{hash(content)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            # 语法错误时返回空分析
            return FileAnalysis(file_path=file_path)
        
        analysis = FileAnalysis(file_path=file_path)
        
        # 分析导入
        analysis.imports = self._extract_imports(tree)
        
        # 分析定义（函数、类）
        analysis.defines = self._extract_definitions(tree, file_path)
        
        # 分析调用
        analysis.calls = self._extract_calls(tree)
        
        # 分析继承
        analysis.inherits = self._extract_inheritance(tree)
        
        # 缓存
        self._cache[cache_key] = analysis
        
        return analysis
    
    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """提取所有导入语句"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[alias.name],
                        is_relative=False,
                        line_number=node.lineno,
                        alias=alias.asname
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                is_relative = node.level > 0
                
                imports.append(ImportInfo(
                    module=module,
                    names=names,
                    is_relative=is_relative,
                    line_number=node.lineno
                ))
        
        return imports
    
    def _extract_definitions(self, tree: ast.AST, file_path: str) -> List[CodeSymbol]:
        """提取函数和类定义"""
        symbols = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                symbols.append(CodeSymbol(
                    name=node.name,
                    type='function',
                    file_path=file_path,
                    line_number=node.lineno,
                    docstring=docstring
                ))
            
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                # 收集类的方法作为依赖
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
                
                symbols.append(CodeSymbol(
                    name=node.name,
                    type='class',
                    file_path=file_path,
                    line_number=node.lineno,
                    docstring=docstring,
                    dependencies=methods
                ))
        
        return symbols
    
    def _extract_calls(self, tree: ast.AST) -> List[CallInfo]:
        """提取函数调用"""
        calls = []
        
        # 找到当前所在的函数/类
        current_scope = None
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                current_scope = node.name
            
            if isinstance(node, ast.Call):
                callee = self._get_call_name(node.func)
                if callee:
                    calls.append(CallInfo(
                        callee=callee,
                        caller=current_scope or "<module>",
                        line_number=node.lineno,
                        args_count=len(node.args)
                    ))
        
        return calls
    
    def _get_call_name(self, node) -> Optional[str]:
        """获取调用表达式的名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_call_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        return None
    
    def _extract_inheritance(self, tree: ast.AST) -> List[Tuple[str, str]]:
        """提取类继承关系"""
        inherits = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    parent = self._get_call_name(base)
                    if parent:
                        inherits.append((node.name, parent))
        
        return inherits


class DependencyGraph:
    """
    代码依赖图
    
    使用有向图表示文件间的依赖关系
    """
    
    def __init__(self):
        self._nodes: Dict[str, FileAnalysis] = {}  # file_path -> FileAnalysis
        self._edges: Dict[str, Set[str]] = defaultdict(set)  # from -> {to}
        self._reverse_edges: Dict[str, Set[str]] = defaultdict(set)  # to -> {from}
        self._symbol_index: Dict[str, str] = {}  # symbol_name -> file_path
    
    def add_file(self, analysis: FileAnalysis, resolve_imports: bool = True):
        """
        添加文件到依赖图
        
        Args:
            analysis: 文件分析结果
            resolve_imports: 是否解析导入为文件路径
        """
        self._nodes[analysis.file_path] = analysis
        
        # 索引定义的符号
        for symbol in analysis.defines:
            self._symbol_index[symbol.name] = analysis.file_path
        
        if resolve_imports:
            self._resolve_imports(analysis)
    
    def _resolve_imports(self, analysis: FileAnalysis):
        """解析导入为文件路径依赖"""
        for imp in analysis.imports:
            # 尝试解析模块为文件路径
            resolved = self._resolve_module_to_file(imp.module, analysis.file_path)
            if resolved:
                self._add_edge(analysis.file_path, resolved, "import")
            
            # 尝试解析from导入的模块
            if imp.module and not resolved:
                # from auth.models import User -> 尝试解析 auth/models.py
                parts = imp.module.split('.')
                for i in range(len(parts), 0, -1):
                    candidate = '.'.join(parts[:i])
                    resolved = self._resolve_module_to_file(candidate, analysis.file_path)
                    if resolved:
                        self._add_edge(analysis.file_path, resolved, "import")
                        break
            
            # 解析导入的名称（可能是直接从其他模块导入的类/函数）
            for name in imp.names:
                # 尝试将名称解析为文件
                resolved_name = self._resolve_module_to_file(name, analysis.file_path)
                if resolved_name and resolved_name != resolved:
                    self._add_edge(analysis.file_path, resolved_name, "import")
    
    def _resolve_module_to_file(self, module: str, from_file: str) -> Optional[str]:
        """
        将模块名解析为文件路径（改进版）
        
        支持:
        - 精确匹配: "auth.service" -> "src/auth/service.py"
        - 模糊匹配: "service" -> "src/auth/service.py"
        - 目录匹配: "auth" -> "src/auth/service.py" (如果auth下只有service)
        """
        if not module:
            return None
        
        module = module.strip()
        module_parts = module.split('.')
        module_last = module_parts[-1]
        
        candidates = []
        
        # 1. 精确匹配：完整路径匹配
        for file_path in self._nodes.keys():
            normalized = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            
            # auth.models 匹配 auth/models.py
            if module == normalized or normalized.endswith(module):
                candidates.append((file_path, 1.0))
            
            # 部分匹配
            elif module_last == Path(file_path).stem:
                depth = len(Path(file_path).parts)
                score = 0.8 / depth
                candidates.append((file_path, score))
        
        # 2. 目录匹配: module="auth" 匹配 "src/auth/*.py"
        if len(module_parts) == 1:
            for file_path in self._nodes.keys():
                path_parts = Path(file_path).parts
                if module in path_parts:
                    # 找到包含auth目录的文件
                    idx = path_parts.index(module) if module in path_parts else -1
                    if idx >= 0 and idx < len(path_parts) - 1:
                        # auth/service.py 中的 service.py
                        score = 0.6 / len(path_parts)
                        candidates.append((file_path, score))
        
        # 3. 尝试从当前文件位置推断相对路径
        if from_file and '.' in module:
            from_dir = str(Path(from_file).parent)
            relative_path = from_dir + '/' + '/'.join(module_parts) + '.py'
            if relative_path in self._nodes:
                candidates.append((relative_path, 0.9))
        
        # 4. 尝试添加src/前缀
        src_path = 'src/' + '/'.join(module_parts) + '.py'
        if src_path in self._nodes:
            candidates.append((src_path, 0.7))
        
        if candidates:
            candidates.sort(key=lambda x: -x[1])
            return candidates[0][0]
        
        return None
        
        # auth.models -> auth/models/__init__.py
        possible_paths.append('/'.join(parts) + '/__init__.py')
        
        # 只取最后部分: models -> models.py
        possible_paths.append(parts[-1] + '.py')
        
        # src/auth/models.py (添加src前缀)
        possible_paths.append('src/' + '/'.join(parts) + '.py')
        
        for path in possible_paths:
            if path in self._nodes:
                return path
            # 也检查路径结尾匹配
            for existing_path in self._nodes.keys():
                if existing_path.endswith(path) or path.endswith(existing_path):
                    return existing_path
        
        return None
    
    def _add_edge(self, from_file: str, to_file: str, edge_type: str):
        """添加边"""
        if from_file != to_file:  # 避免自环
            self._edges[from_file].add(to_file)
            self._reverse_edges[to_file].add(from_file)
    
    def get_dependencies(self, file_path: str) -> Set[str]:
        """获取文件依赖的文件列表"""
        return self._edges.get(file_path, set())
    
    def get_dependents(self, file_path: str) -> Set[str]:
        """获取依赖此文件的文件列表"""
        return self._reverse_edges.get(file_path, set())
    
    def get_transitive_dependencies(self, file_path: str, depth: int = 3) -> Set[str]:
        """
        获取传递依赖（递归）
        
        Args:
            file_path: 起始文件
            depth: 最大递归深度
            
        Returns:
            所有依赖的文件
        """
        result = set()
        visited = {file_path}
        queue = [(file_path, 0)]
        
        while queue:
            current, current_depth = queue.pop(0)
            
            if current_depth >= depth:
                continue
            
            for dep in self._edges.get(current, set()):
                if dep not in visited:
                    visited.add(dep)
                    result.add(dep)
                    queue.append((dep, current_depth + 1))
        
        return result
    
    def get_centrality(self, file_path: str) -> float:
        """
        计算文件的中心性（重要性）
        
        基于：被多少文件依赖
        """
        dependents = len(self._reverse_edges.get(file_path, set()))
        total_files = len(self._nodes)
        
        if total_files <= 1:
            return 0.0
        
        return dependents / (total_files - 1)
    
    def get_impact_analysis(self, changed_files: List[str]) -> Dict[str, Any]:
        """
        影响分析：修改这些文件会影响哪些文件？
        
        Args:
            changed_files: 被修改的文件列表
            
        Returns:
            影响分析报告
        """
        directly_affected = set()
        transitively_affected = set()
        
        for file_path in changed_files:
            # 直接依赖此文件的
            direct = self.get_dependents(file_path)
            directly_affected.update(direct)
            
            # 传递影响
            for dep in direct:
                transitive = self.get_transitive_dependencies(dep, depth=2)
                transitively_affected.update(transitive)
        
        transitively_affected -= directly_affected
        transitively_affected -= set(changed_files)
        
        return {
            "changed_files": changed_files,
            "directly_affected": list(directly_affected),
            "transitively_affected": list(transitively_affected),
            "total_affected": len(directly_affected) + len(transitively_affected),
            "critical_paths": self._find_critical_paths(changed_files)
        }
    
    def _find_critical_paths(self, changed_files: List[str]) -> List[List[str]]:
        """找出关键路径"""
        paths = []
        
        for changed in changed_files:
            dependents = self.get_dependents(changed)
            for dep in dependents:
                # 如果依赖者也被很多人依赖，这是关键路径
                if len(self.get_dependents(dep)) > 2:
                    paths.append([changed, dep])
        
        return paths
    
    def get_related_files(self, file_path: str, include_dependencies: bool = True, 
                         include_dependents: bool = True) -> Set[str]:
        """
        获取相关文件
        
        Args:
            file_path: 目标文件
            include_dependencies: 是否包含依赖的文件
            include_dependents: 是否包含依赖此文件的文件
            
        Returns:
            相关文件集合
        """
        related = set()
        
        if include_dependencies:
            related.update(self.get_dependencies(file_path))
            related.update(self.get_transitive_dependencies(file_path, depth=1))
        
        if include_dependents:
            related.update(self.get_dependents(file_path))
        
        return related
    
    def get_modularity_score(self) -> float:
        """
        计算代码库的模块化程度
        
        高模块化 = 依赖关系清晰，没有循环依赖
        """
        # 检测循环依赖
        cycles = self._detect_cycles()
        
        if not self._edges:
            return 1.0
        
        # 简单指标：循环依赖越少越好
        cycle_penalty = len(cycles) * 0.1
        return max(0.0, 1.0 - cycle_penalty)
    
    def _detect_cycles(self) -> List[List[str]]:
        """检测循环依赖"""
        cycles = []
        visited = set()
        
        def dfs(node, path, path_set):
            """
            DFS查找循环
            
            Args:
                node: 当前节点
                path: 当前路径（从起点到当前节点）
                path_set: 当前路径的节点集合（用于O(1)查找）
            """
            path.append(node)
            path_set.add(node)
            
            for neighbor in self._edges.get(node, set()):
                if neighbor in path_set:
                    # 发现循环！提取循环部分
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                elif neighbor not in visited:
                    dfs(neighbor, path, path_set)
            
            path.pop()
            path_set.remove(node)
        
        for node in list(self._nodes.keys()):
            if node not in visited:
                dfs(node, [], set())
                visited.add(node)
        
        # 去重：相同的循环只保留一个
        unique_cycles = []
        seen = set()
        for cycle in cycles:
            # 将循环标准化（从最小元素开始）
            normalized = tuple(min([cycle[i:] + cycle[:i] for i in range(len(cycle) - 1)]))
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(cycle)
        
        return unique_cycles
    
    def visualize_text(self) -> str:
        """文本可视化依赖图"""
        lines = ["代码依赖图:", ""]
        
        # 按中心性排序
        sorted_nodes = sorted(
            self._nodes.keys(),
            key=lambda x: len(self._reverse_edges.get(x, set())),
            reverse=True
        )
        
        for file_path in sorted_nodes[:10]:  # 只显示前10个
            deps = self._edges.get(file_path, set())
            dependents = self._reverse_edges.get(file_path, set())
            
            centrality = len(dependents)
            icon = "🔴" if centrality > 5 else "🟡" if centrality > 2 else "🟢"
            
            lines.append(f"{icon} {file_path}")
            lines.append(f"   依赖: {len(deps)} 个文件")
            lines.append(f"   被依赖: {centrality} 个文件")
            
            if deps:
                lines.append(f"   → {', '.join(list(deps)[:3])}")
            if dependents:
                lines.append(f"   ← {', '.join(list(dependents)[:3])}")
            lines.append("")
        
        return "\n".join(lines)


class DependencyAwareFreshEyes:
    """
    依赖感知的Fresh Eyes
    
    将代码依赖图分析集成到Fresh Eyes中
    """
    
    def __init__(self, analyzer: ASTDependencyAnalyzer, graph: DependencyGraph):
        self.analyzer = analyzer
        self.graph = graph
    
    def enhance_context_selection(
        self,
        selected_files: List[str],
        all_files: Dict[str, str]
    ) -> List[str]:
        """
        增强文件选择：添加相关依赖文件
        
        Args:
            selected_files: 已选中的文件
            all_files: 所有可用文件 {path: content}
            
        Returns:
            增强后的文件列表
        """
        enhanced = set(selected_files)
        
        for file_path in selected_files:
            # 添加此文件的依赖
            deps = self.graph.get_dependencies(file_path)
            enhanced.update(deps)
            
            # 添加依赖此文件的文件（影响分析）
            dependents = self.graph.get_dependents(file_path)
            # 只添加高重要性的依赖者
            for dep in dependents:
                if len(self.graph.get_dependents(dep)) > 2:
                    enhanced.add(dep)
        
        return list(enhanced)
    
    def score_by_centrality(self, files: List[str]) -> Dict[str, float]:
        """
        基于中心性给文件打分
        
        用于Fresh Eyes的importance_score
        """
        scores = {}
        
        for file_path in files:
            centrality = self.graph.get_centrality(file_path)
            # 归一化到 0-1
            scores[file_path] = min(centrality * 2, 1.0)  # 放大中心性影响
        
        return scores


# ============ 便捷函数 ============

def build_dependency_graph(file_contents: Dict[str, str]) -> DependencyGraph:
    """
    从文件内容构建依赖图
    
    Args:
        file_contents: {file_path: file_content}
        
    Returns:
        DependencyGraph 依赖图
    """
    analyzer = ASTDependencyAnalyzer()
    graph = DependencyGraph()
    
    # 第一轮：分析所有文件
    analyses = {}
    for file_path, content in file_contents.items():
        if file_path.endswith('.py'):
            analysis = analyzer.analyze_file(file_path, content)
            analyses[file_path] = analysis
    
    # 第二轮：添加所有节点（不解析导入）
    for file_path, analysis in analyses.items():
        graph.add_file(analysis, resolve_imports=False)
    
    # 第三轮：解析所有导入（此时所有节点都已存在）
    for file_path, analysis in analyses.items():
        graph._resolve_imports(analysis)
    
    return graph


def analyze_code_dependencies(file_path: str, content: str) -> FileAnalysis:
    """分析单个文件的依赖"""
    analyzer = ASTDependencyAnalyzer()
    return analyzer.analyze_file(file_path, content)


# ============ 与Fresh Eyes集成 ============

def integrate_with_fresh_eyes(
    context_manager,
    file_contents: Dict[str, str]
) -> DependencyGraph:
    """
    将依赖分析集成到Fresh Eyes
    
    用法:
        graph = integrate_with_fresh_eyes(context_mgr, file_contents)
        # context_mgr 现在可以使用 graph 进行依赖感知的文件选择
    """
    graph = build_dependency_graph(file_contents)
    
    # 将graph附加到context_manager
    context_manager._dependency_graph = graph
    
    return graph
