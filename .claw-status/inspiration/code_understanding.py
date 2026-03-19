#!/usr/bin/env python3
"""
Phase 1: Code Understanding Layer - 代码理解层

核心能力:
1. AST解析 - 理解代码结构
2. 依赖图构建 - 函数/类/模块关系
3. 代码嵌入 - 语义表示
4. 影响分析 - 修改影响范围
5. 静态分析 - 质量评估

Author: wdai
Version: 1.0 - Phase 1 Implementation
"""

import ast
import json
import hashlib
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
import sys
import re


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    file_path: str
    line_start: int
    line_end: int
    args: List[str]
    returns: Optional[str]
    docstring: Optional[str]
    complexity: int  # 圈复杂度
    calls: Set[str]  # 调用的其他函数
    called_by: Set[str]  # 被哪些函数调用


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    file_path: str
    line_start: int
    line_end: int
    methods: List[str]
    bases: List[str]  # 继承的基类
    docstring: Optional[str]


@dataclass
class ModuleInfo:
    """模块信息"""
    file_path: str
    functions: Dict[str, FunctionInfo]
    classes: Dict[str, ClassInfo]
    imports: List[str]
    exports: List[str]  # 公开接口
    complexity: int


@dataclass
class ImpactAnalysis:
    """影响分析结果"""
    target: str  # 修改目标
    target_type: str  # function/class/module
    affected_functions: Set[str]
    affected_classes: Set[str]
    affected_modules: Set[str]
    risk_score: int  # 0-100
    breaking_changes: bool
    reasoning: str


class ASTAnalyzer:
    """
    AST分析器 - 解析Python代码结构
    """
    
    def __init__(self):
        self.modules: Dict[str, ModuleInfo] = {}
    
    def analyze_file(self, file_path: Path) -> Optional[ModuleInfo]:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            return self._extract_module_info(tree, file_path, source)
        except Exception as e:
            print(f"   ⚠️ 解析失败 {file_path}: {e}")
            return None
    
    def analyze_directory(self, directory: Path, pattern: str = "*.py") -> Dict[str, ModuleInfo]:
        """分析整个目录"""
        for file_path in directory.rglob(pattern):
            if "__pycache__" in str(file_path):
                continue
            module = self.analyze_file(file_path)
            if module:
                self.modules[str(file_path)] = module
        
        # 构建调用关系
        self._build_call_graph()
        
        return self.modules
    
    def _extract_module_info(self, tree: ast.AST, file_path: Path, source: str) -> ModuleInfo:
        """提取模块信息"""
        functions = {}
        classes = {}
        imports = []
        exports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
            
            elif isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node, file_path, source)
                functions[func_info.name] = func_info
                if not func_info.name.startswith("_"):
                    exports.append(func_info.name)
            
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node, file_path, source)
                classes[class_info.name] = class_info
                exports.append(class_info.name)
        
        return ModuleInfo(
            file_path=str(file_path),
            functions=functions,
            classes=classes,
            imports=imports,
            exports=exports,
            complexity=self._calculate_complexity(tree)
        )
    
    def _extract_function_info(self, node: ast.FunctionDef, file_path: Path, source: str) -> FunctionInfo:
        """提取函数信息"""
        # 获取参数
        args = [arg.arg for arg in node.args.args]
        
        # 获取返回值注解
        returns = None
        if node.returns:
            returns = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        
        # 获取docstring
        docstring = ast.get_docstring(node)
        
        # 计算圈复杂度
        complexity = self._calculate_complexity(node)
        
        # 找出调用的函数
        calls = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.add(child.func.attr)
        
        return FunctionInfo(
            name=node.name,
            file_path=str(file_path),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            args=args,
            returns=returns,
            docstring=docstring,
            complexity=complexity,
            calls=calls,
            called_by=set()
        )
    
    def _extract_class_info(self, node: ast.ClassDef, file_path: Path, source: str) -> ClassInfo:
        """提取类信息"""
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        bases = [ast.unparse(b) if hasattr(ast, 'unparse') else str(b) for b in node.bases]
        docstring = ast.get_docstring(node)
        
        return ClassInfo(
            name=node.name,
            file_path=str(file_path),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            methods=methods,
            bases=bases,
            docstring=docstring
        )
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _build_call_graph(self):
        """构建调用图 - 找出谁调用了谁"""
        # 建立函数名到函数的映射
        all_functions = {}
        for module_path, module in self.modules.items():
            for func_name, func in module.functions.items():
                # 使用 qualified name: module.function
                qualified_name = f"{module_path}:{func_name}"
                all_functions[func_name] = func
                all_functions[qualified_name] = func
        
        # 填充 called_by
        for module_path, module in self.modules.items():
            for func_name, func in module.functions.items():
                for called in func.calls:
                    if called in all_functions:
                        all_functions[called].called_by.add(f"{module_path}:{func_name}")
    
    def get_function(self, qualified_name: str) -> Optional[FunctionInfo]:
        """获取函数信息 (格式: file_path:function_name)"""
        for module_path, module in self.modules.items():
            if qualified_name.startswith(module_path):
                func_name = qualified_name.split(":")[-1]
                return module.functions.get(func_name)
        return None
    
    def find_dependencies(self, file_path: str) -> Set[str]:
        """找出文件的依赖"""
        deps = set()
        module = self.modules.get(file_path)
        if not module:
            return deps
        
        for imp in module.imports:
            # 简化处理：假设import对应文件路径
            parts = imp.split(".")
            candidate = "/".join(parts) + ".py"
            if candidate in self.modules:
                deps.add(candidate)
        
        return deps


class DependencyGraph:
    """
    依赖图 - 模块/函数/类之间的关系
    """
    
    def __init__(self, analyzer: ASTAnalyzer):
        self.analyzer = analyzer
        self.graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)
    
    def build(self):
        """构建完整依赖图"""
        for module_path, module in self.analyzer.modules.items():
            # 模块依赖
            deps = self.analyzer.find_dependencies(module_path)
            for dep in deps:
                self.graph[module_path].add(dep)
                self.reverse_graph[dep].add(module_path)
            
            # 函数调用依赖
            for func_name, func in module.functions.items():
                qualified_name = f"{module_path}:{func_name}"
                for called in func.calls:
                    # 找到被调用函数的完整路径
                    for mp, m in self.analyzer.modules.items():
                        if called in m.functions:
                            called_qualified = f"{mp}:{called}"
                            self.graph[qualified_name].add(called_qualified)
                            self.reverse_graph[called_qualified].add(qualified_name)
    
    def get_affected(self, target: str, depth: int = 3) -> Set[str]:
        """获取受影响的节点 (广度优先)"""
        affected = set()
        queue = [(target, 0)]
        visited = {target}
        
        while queue:
            current, current_depth = queue.pop(0)
            if current_depth >= depth:
                continue
            
            for neighbor in self.reverse_graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    affected.add(neighbor)
                    queue.append((neighbor, current_depth + 1))
        
        return affected
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """查找循环依赖"""
        cycles = []
        visited = set()
        rec_stack = []
        
        def dfs(node, path):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in self.graph.get(node, []):
                dfs(neighbor, path)
            
            path.pop()
        
        for node in self.graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles


class ImpactAnalyzer:
    """
    影响分析器 - 分析修改的影响范围
    """
    
    def __init__(self, analyzer: ASTAnalyzer, graph: DependencyGraph):
        self.analyzer = analyzer
        self.graph = graph
    
    def analyze_change(self, file_path: str, change_type: str, 
                      change_details: str) -> ImpactAnalysis:
        """
        分析变更的影响
        
        Args:
            file_path: 修改的文件
            change_type: create/modify/delete/refactor
            change_details: 变更详情
        """
        module = self.analyzer.modules.get(file_path)
        
        if not module:
            return ImpactAnalysis(
                target=file_path,
                target_type="unknown",
                affected_functions=set(),
                affected_classes=set(),
                affected_modules=set(),
                risk_score=50,
                breaking_changes=True,
                reasoning="无法分析该文件"
            )
        
        # 获取直接依赖该模块的其他模块
        dependent_modules = self.graph.reverse_graph.get(file_path, set())
        
        # 获取受影响的功能
        affected_functions = set()
        affected_classes = set()
        
        for dep_module in dependent_modules:
            dep_mod = self.analyzer.modules.get(dep_module)
            if dep_mod:
                affected_functions.update(dep_mod.functions.keys())
                affected_classes.update(dep_mod.classes.keys())
        
        # 计算风险评分
        risk_score = self._calculate_risk_score(
            module, change_type, dependent_modules
        )
        
        # 判断是否破坏性变更
        breaking_changes = change_type in ["delete", "refactor"] or \
                          (change_type == "modify" and "signature" in change_details.lower())
        
        # 生成理由
        reasoning = self._generate_reasoning(
            module, change_type, dependent_modules, risk_score
        )
        
        return ImpactAnalysis(
            target=file_path,
            target_type="module",
            affected_functions=affected_functions,
            affected_classes=affected_classes,
            affected_modules=dependent_modules,
            risk_score=risk_score,
            breaking_changes=breaking_changes,
            reasoning=reasoning
        )
    
    def _calculate_risk_score(self, module: ModuleInfo, change_type: str, 
                             dependents: Set[str]) -> int:
        """计算风险评分"""
        score = 0
        
        # 基于依赖数量
        score += min(len(dependents) * 10, 40)
        
        # 基于代码复杂度
        score += min(module.complexity, 20)
        
        # 基于变更类型
        type_scores = {
            "create": 5,
            "modify": 15,
            "refactor": 25,
            "delete": 40
        }
        score += type_scores.get(change_type, 20)
        
        # 基于公开接口数量
        score += min(len(module.exports) * 5, 15)
        
        return min(score, 100)
    
    def _generate_reasoning(self, module: ModuleInfo, change_type: str,
                           dependents: Set[str], risk_score: int) -> str:
        """生成分析理由"""
        lines = []
        lines.append(f"模块 '{module.file_path}' 复杂度: {module.complexity}")
        lines.append(f"公开接口: {len(module.exports)} 个 ({', '.join(module.exports[:5])})")
        lines.append(f"依赖此模块的其他模块: {len(dependents)} 个")
        
        if dependents:
            lines.append(f"受影响模块: {', '.join(list(dependents)[:3])}")
        
        if risk_score > 60:
            lines.append("⚠️ 高风险: 影响范围广，建议仔细测试")
        elif risk_score > 30:
            lines.append("⚡ 中等风险: 有一定影响，建议验证")
        else:
            lines.append("✓ 低风险: 影响有限")
        
        return "\n".join(lines)


class CodeQualityAnalyzer:
    """
    代码质量分析器
    """
    
    def analyze(self, file_path: Path) -> Dict[str, Any]:
        """分析代码质量"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            return {
                'lines': len(source.split('\n')),
                'complexity': self._calculate_complexity(tree),
                'function_count': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                'class_count': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                'import_count': len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
                'issues': self._find_issues(tree, source)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    def _find_issues(self, tree: ast.AST, source: str) -> List[Dict]:
        """查找代码问题"""
        issues = []
        
        for node in ast.walk(tree):
            # 检测过长的函数
            if isinstance(node, ast.FunctionDef):
                length = (node.end_lineno or node.lineno) - node.lineno
                if length > 50:
                    issues.append({
                        'type': 'long_function',
                        'line': node.lineno,
                        'message': f"函数 '{node.name}' 过长 ({length} 行)，建议拆分"
                    })
                
                # 检测过多参数
                if len(node.args.args) > 5:
                    issues.append({
                        'type': 'too_many_args',
                        'line': node.lineno,
                        'message': f"函数 '{node.name}' 参数过多 ({len(node.args.args)} 个)"
                    })
            
            # 检测裸except
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        'type': 'bare_except',
                        'line': node.lineno,
                        'message': "使用裸except，建议指定具体异常类型"
                    })
        
        return issues


class CodeUnderstandingLayer:
    """
    代码理解层 - 主入口
    
    整合所有分析能力
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.analyzer = ASTAnalyzer()
        self.graph: Optional[DependencyGraph] = None
        self.impact_analyzer: Optional[ImpactAnalyzer] = None
        self.quality_analyzer = CodeQualityAnalyzer()
    
    def build(self):
        """构建完整的代码理解"""
        print("🔍 Phase 1: 构建代码理解层...")
        print("   1. AST解析所有Python文件...")
        self.analyzer.analyze_directory(self.project_path)
        print(f"      解析了 {len(self.analyzer.modules)} 个模块")
        
        print("   2. 构建依赖图...")
        self.graph = DependencyGraph(self.analyzer)
        self.graph.build()
        print(f"      发现了 {len(self.graph.graph)} 个依赖关系")
        
        print("   3. 初始化影响分析器...")
        self.impact_analyzer = ImpactAnalyzer(self.analyzer, self.graph)
        
        # 检查循环依赖
        cycles = self.graph.find_circular_dependencies()
        if cycles:
            print(f"   ⚠️ 发现 {len(cycles)} 个循环依赖")
        else:
            print("   ✓ 未发现循环依赖")
        
        print("   ✅ 代码理解层构建完成")
    
    def analyze_impact(self, file_path: str, change_type: str, 
                      change_details: str) -> ImpactAnalysis:
        """分析变更影响"""
        if not self.impact_analyzer:
            raise RuntimeError("请先调用build()")
        
        return self.impact_analyzer.analyze_change(
            file_path, change_type, change_details
        )
    
    def get_module_info(self, file_path: str) -> Optional[ModuleInfo]:
        """获取模块信息"""
        return self.analyzer.modules.get(file_path)
    
    def find_similar_functions(self, func_name: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """查找相似函数 (简化版，基于调用模式)"""
        target_func = None
        for module in self.analyzer.modules.values():
            if func_name in module.functions:
                target_func = module.functions[func_name]
                break
        
        if not target_func:
            return []
        
        # 基于调用模式计算相似度
        similarities = []
        for module in self.analyzer.modules.values():
            for name, func in module.functions.items():
                if name == func_name:
                    continue
                
                # Jaccard相似度
                intersection = len(target_func.calls & func.calls)
                union = len(target_func.calls | func.calls)
                similarity = intersection / union if union > 0 else 0
                
                if similarity > 0:
                    similarities.append((f"{module.file_path}:{name}", similarity))
        
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
    
    def generate_report(self) -> str:
        """生成项目分析报告"""
        lines = []
        lines.append("="*70)
        lines.append("📊 代码理解层分析报告")
        lines.append("="*70)
        
        total_functions = sum(len(m.functions) for m in self.analyzer.modules.values())
        total_classes = sum(len(m.classes) for m in self.analyzer.modules.values())
        total_complexity = sum(m.complexity for m in self.analyzer.modules.values())
        
        lines.append(f"\n项目概况:")
        lines.append(f"   模块数量: {len(self.analyzer.modules)}")
        lines.append(f"   函数数量: {total_functions}")
        lines.append(f"   类数量: {total_classes}")
        lines.append(f"   总复杂度: {total_complexity}")
        lines.append(f"   平均复杂度: {total_complexity / max(len(self.analyzer.modules), 1):.1f}")
        
        # 最复杂的函数
        all_functions = []
        for module in self.analyzer.modules.values():
            for func in module.functions.values():
                all_functions.append((f"{module.file_path}:{func.name}", func.complexity))
        
        if all_functions:
            lines.append(f"\n最复杂的5个函数:")
            for path, complexity in sorted(all_functions, key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"   {path}: 复杂度 {complexity}")
        
        lines.append("\n" + "="*70)
        return "\n".join(lines)


def main():
    """测试代码理解层"""
    import sys
    
    # 分析当前目录
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path(__file__).parent
    
    print(f"\n分析项目: {project_path}\n")
    
    layer = CodeUnderstandingLayer(project_path)
    layer.build()
    
    # 生成报告
    print(layer.generate_report())
    
    # 示例: 分析一个假设的修改
    print("\n" + "="*70)
    print("🧪 影响分析示例")
    print("="*70)
    
    # 找一个实际存在的文件
    test_file = None
    for file_path in layer.analyzer.modules.keys():
        if file_path.endswith('.py'):
            test_file = file_path
            break
    
    if test_file:
        print(f"\n假设修改: {test_file}")
        impact = layer.analyze_impact(test_file, "modify", "重构核心逻辑")
        print(f"\n影响分析:")
        print(f"   风险评分: {impact.risk_score}/100")
        print(f"   破坏性变更: {'是' if impact.breaking_changes else '否'}")
        print(f"   受影响函数: {len(impact.affected_functions)} 个")
        print(f"   受影响模块: {len(impact.affected_modules)} 个")
        print(f"\n分析理由:\n{impact.reasoning}")


if __name__ == "__main__":
    main()
