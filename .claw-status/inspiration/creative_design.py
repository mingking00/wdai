#!/usr/bin/env python3
"""
Phase 2: Creative Design Layer - 创造性设计层

核心能力:
1. 架构模式库 - 常见改进模式定义
2. 约束满足求解 - 在约束下寻找最优方案
3. 多目标优化 - 平衡性能/可读性/复杂度
4. 类比推理 - 从相似代码学习改进策略

基于Phase 1的代码理解能力，实现创造性设计而非模板套用

Author: wdai
Version: 1.0 - Phase 2 Implementation
"""

import json
import ast
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
import copy
import sys

# 导入Phase 1的代码理解层
sys.path.insert(0, str(Path(__file__).parent))
try:
    from code_understanding import (
        CodeUnderstandingLayer, ModuleInfo, FunctionInfo, 
        ClassInfo, ImpactAnalysis
    )
    PHASE1_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False


@dataclass
class ArchitecturePattern:
    """架构模式"""
    id: str
    name: str
    description: str
    category: str  # refactoring, optimization, structural
    applicability: Callable[[Any], bool]  # 适用性判断函数
    apply: Callable[[Any, Dict], Any]  # 应用函数
    constraints: List[str]  # 应用约束
    estimated_impact: Dict[str, int]  # 预期影响 {performance: +10, complexity: -5}
    examples: List[str]  # 示例


@dataclass
class DesignCandidate:
    """设计方案候选"""
    id: str
    pattern_id: str
    description: str
    changes: List[Dict]
    objectives: Dict[str, float]  # {performance: 0.8, readability: 0.9}
    constraints_satisfied: bool
    risk_score: int
    confidence: float
    reasoning: str


@dataclass
class Constraint:
    """约束条件"""
    type: str  # hard, soft
    description: str
    check: Callable[[Any], bool]
    weight: float = 1.0  # 软约束的权重


class PatternLibrary:
    """
    架构模式库
    
    定义常见的代码改进模式
    """
    
    def __init__(self):
        self.patterns: Dict[str, ArchitecturePattern] = {}
        self._init_patterns()
    
    def _init_patterns(self):
        """初始化内置模式"""
        
        # 模式1: 拆分复杂函数
        self.patterns["split_complex_function"] = ArchitecturePattern(
            id="split_complex_function",
            name="拆分复杂函数",
            description="将圈复杂度超过阈值的大函数拆分为多个小函数",
            category="refactoring",
            applicability=self._check_complex_function,
            apply=self._apply_split_function,
            constraints=["函数有明确的逻辑段落", "拆分后语义清晰"],
            estimated_impact={
                "complexity": -30,
                "readability": +20,
                "testability": +25
            },
            examples=[
                "将200行的数据处理函数拆分为：解析、验证、转换、保存"
            ]
        )
        
        # 模式2: 提取重复代码
        self.patterns["extract_common_code"] = ArchitecturePattern(
            id="extract_common_code",
            name="提取公共代码",
            description="将多处重复的代码提取为公共函数",
            category="refactoring",
            applicability=self._check_duplicate_code,
            apply=self._apply_extract_common,
            constraints=["重复代码逻辑完全相同", "提取后调用点清晰"],
            estimated_impact={
                "maintainability": +25,
                "lines_of_code": -15,
                "complexity": -10
            },
            examples=[
                "多个函数中都有的参数验证逻辑提取为validate_params()"
            ]
        )
        
        # 模式3: 添加缓存机制
        self.patterns["add_caching"] = ArchitecturePattern(
            id="add_caching",
            name="添加缓存机制",
            description="为重复计算或IO操作添加缓存",
            category="optimization",
            applicability=self._check_cacheable,
            apply=self._apply_caching,
            constraints=["函数是纯函数或幂等的", "缓存命中率可预期"],
            estimated_impact={
                "performance": +40,
                "memory": -10,
                "complexity": +5
            },
            examples=[
                "为API调用结果添加LRU缓存，减少重复请求"
            ]
        )
        
        # 模式4: 策略模式替代条件分支
        self.patterns["strategy_pattern"] = ArchitecturePattern(
            id="strategy_pattern",
            name="策略模式替代条件分支",
            description="将复杂的if/elif/else替换为策略模式",
            category="structural",
            applicability=self._check_complex_conditionals,
            apply=self._apply_strategy_pattern,
            constraints=["条件分支基于同一变量", "各分支逻辑相对独立"],
            estimated_impact={
                "extensibility": +35,
                "readability": +20,
                "complexity": -15
            },
            examples=[
                "将不同调度策略的if-else改为Strategy接口+具体策略类"
            ]
        )
        
        # 模式5: 异步化IO操作
        self.patterns["async_io"] = ArchitecturePattern(
            id="async_io",
            name="异步化IO操作",
            description="将同步IO操作改为异步，提高并发性能",
            category="optimization",
            applicability=self._check_sync_io,
            apply=self._apply_async_io,
            constraints=["IO操作可并行化", "调用链支持异步"],
            estimated_impact={
                "performance": +50,
                "throughput": +60,
                "complexity": +20
            },
            examples=[
                "将多个HTTP请求改为asyncio.gather并行执行"
            ]
        )
        
        # 模式6: 依赖注入解耦
        self.patterns["dependency_injection"] = ArchitecturePattern(
            id="dependency_injection",
            name="依赖注入解耦",
            description="将硬编码依赖改为依赖注入，提高可测试性",
            category="structural",
            applicability=self._check_hard_dependencies,
            apply=self._apply_dependency_injection,
            constraints=["依赖可被抽象为接口", "有明确的注入点"],
            estimated_impact={
                "testability": +40,
                "maintainability": +30,
                "coupling": -25
            },
            examples=[
                "将直接实例化的数据库连接改为构造函数注入"
            ]
        )
        
        # 模式7: 批处理优化
        self.patterns["batch_processing"] = ArchitecturePattern(
            id="batch_processing",
            name="批处理优化",
            description="将逐条处理改为批量处理，减少IO开销",
            category="optimization",
            applicability=self._check_item_by_item,
            apply=self._apply_batch_processing,
            constraints=["操作可批量执行", "内存可容纳批量数据"],
            estimated_impact={
                "performance": +35,
                "io_efficiency": +50,
                "memory": -15
            },
            examples=[
                "将逐条插入数据库改为批量插入"
            ]
        )
        
        # 模式8: 错误处理规范化
        self.patterns["standardize_error_handling"] = ArchitecturePattern(
            id="standardize_error_handling",
            name="错误处理规范化",
            description="统一错误处理模式，添加适当的异常类型",
            category="refactoring",
            applicability=self._check_inconsistent_errors,
            apply=self._apply_standardize_errors,
            constraints=["有混乱的错误处理", "可定义清晰的异常层次"],
            estimated_impact={
                "reliability": +30,
                "debuggability": +35,
                "maintainability": +20
            },
            examples=[
                "统一使用自定义异常类，替代裸raise Exception"
            ]
        )
    
    def get_applicable_patterns(self, target: Any, context: Dict = None) -> List[ArchitecturePattern]:
        """获取适用于目标的模式"""
        applicable = []
        for pattern in self.patterns.values():
            try:
                if pattern.applicability(target, context or {}):
                    applicable.append(pattern)
            except:
                pass
        return applicable
    
    def get_pattern(self, pattern_id: str) -> Optional[ArchitecturePattern]:
        """获取指定模式"""
        return self.patterns.get(pattern_id)
    
    # 适用性检查函数
    def _check_complex_function(self, target: Any, context: Dict) -> bool:
        """检查是否是复杂函数"""
        if isinstance(target, dict):
            complexity = target.get('complexity', 0)
            lines = target.get('lines', 0)
            return complexity > 10 or lines > 50
        return False
    
    def _check_duplicate_code(self, target: Any, context: Dict) -> bool:
        """检查是否有重复代码"""
        # 简化版：检查是否有相似函数
        if isinstance(target, ModuleInfo):
            functions = list(target.functions.values())
            for i, f1 in enumerate(functions):
                for f2 in functions[i+1:]:
                    # 简单相似度检查
                    if len(f1.calls & f2.calls) > 3:  # 调用相同函数超过3个
                        return True
        return False
    
    def _check_cacheable(self, target: Any, context: Dict) -> bool:
        """检查是否可缓存"""
        if isinstance(target, FunctionInfo):
            # 检查是否是纯函数（不修改全局状态）
            return target.docstring and 'cache' in target.docstring.lower()
        return False
    
    def _check_complex_conditionals(self, target: Any, context: Dict) -> bool:
        """检查是否有复杂条件分支"""
        if isinstance(target, FunctionInfo):
            return target.complexity > 8  # 简化判断
        return False
    
    def _check_sync_io(self, target: Any, context: Dict) -> bool:
        """检查是否有同步IO"""
        if isinstance(target, FunctionInfo):
            io_calls = {'requests.get', 'open', 'read', 'write', 'sleep'}
            return bool(target.calls & io_calls)
        return False
    
    def _check_hard_dependencies(self, target: Any, context: Dict) -> bool:
        """检查是否有硬编码依赖"""
        if isinstance(target, ClassInfo):
            return len(target.bases) > 0  # 有继承说明可能有依赖
        return False
    
    def _check_item_by_item(self, target: Any, context: Dict) -> bool:
        """检查是否是逐条处理"""
        if isinstance(target, FunctionInfo):
            return 'for' in str(target.calls) and any(
                io in str(target.calls) for io in ['insert', 'update', 'delete']
            )
        return False
    
    def _check_inconsistent_errors(self, target: Any, context: Dict) -> bool:
        """检查错误处理是否不一致"""
        if isinstance(target, ModuleInfo):
            # 检查是否有裸except
            return target.complexity > 20  # 简化判断
        return False
    
    # 模式应用函数（简化版，实际应该生成具体代码）
    def _apply_split_function(self, target: Any, config: Dict) -> List[Dict]:
        """应用拆分函数模式"""
        return [{
            'action': 'refactor',
            'description': f"将{target.get('name', '函数')}拆分为多个子函数",
            'estimated_lines': -20,
            'files_affected': [target.get('file_path', '')]
        }]
    
    def _apply_extract_common(self, target: Any, config: Dict) -> List[Dict]:
        """应用提取公共代码模式"""
        return [{
            'action': 'create',
            'description': "提取公共函数",
            'estimated_lines': -15,
            'files_affected': [target.file_path]
        }]
    
    def _apply_caching(self, target: Any, config: Dict) -> List[Dict]:
        """应用缓存模式"""
        return [{
            'action': 'enhance',
            'description': f"为{target.name}添加缓存装饰器",
            'estimated_lines': +3,
            'files_affected': [target.file_path]
        }]
    
    def _apply_strategy_pattern(self, target: Any, config: Dict) -> List[Dict]:
        """应用策略模式"""
        return [{
            'action': 'refactor',
            'description': "重构为策略模式",
            'estimated_lines': +20,
            'files_affected': [target.file_path]
        }]
    
    def _apply_async_io(self, target: Any, config: Dict) -> List[Dict]:
        """应用异步IO"""
        return [{
            'action': 'refactor',
            'description': "改为异步函数",
            'estimated_lines': +5,
            'files_affected': [target.file_path]
        }]
    
    def _apply_dependency_injection(self, target: Any, config: Dict) -> List[Dict]:
        """应用依赖注入"""
        return [{
            'action': 'refactor',
            'description': "改为依赖注入模式",
            'estimated_lines': +10,
            'files_affected': [target.file_path]
        }]
    
    def _apply_batch_processing(self, target: Any, config: Dict) -> List[Dict]:
        """应用批处理"""
        return [{
            'action': 'refactor',
            'description': "改为批量处理",
            'estimated_lines': +8,
            'files_affected': [target.file_path]
        }]
    
    def _apply_standardize_errors(self, target: Any, config: Dict) -> List[Dict]:
        """应用错误处理规范化"""
        return [{
            'action': 'refactor',
            'description': "规范化错误处理",
            'estimated_lines': +15,
            'files_affected': [target.file_path]
        }]


class ConstraintSatisfactionSolver:
    """
    约束满足求解器
    
    在约束条件下寻找最优设计方案
    """
    
    def __init__(self):
        self.constraints: List[Constraint] = []
    
    def add_constraint(self, constraint: Constraint):
        """添加约束"""
        self.constraints.append(constraint)
    
    def solve(self, candidates: List[DesignCandidate]) -> List[DesignCandidate]:
        """
        求解最优候选方案
        
        返回满足所有硬约束，且软约束得分最高的方案
        """
        valid_candidates = []
        
        for candidate in candidates:
            hard_satisfied = True
            soft_score = 0.0
            
            for constraint in self.constraints:
                try:
                    satisfied = constraint.check(candidate)
                    if constraint.type == "hard":
                        if not satisfied:
                            hard_satisfied = False
                            break
                    else:  # soft constraint
                        if satisfied:
                            soft_score += constraint.weight
                except:
                    # 检查失败，保守处理
                    if constraint.type == "hard":
                        hard_satisfied = False
                        break
            
            if hard_satisfied:
                candidate.constraints_satisfied = True
                # 将软约束得分融入目标函数
                candidate.objectives['constraint_satisfaction'] = soft_score
                valid_candidates.append(candidate)
        
        return valid_candidates


class MultiObjectiveOptimizer:
    """
    多目标优化器
    
    在多目标间寻找Pareto最优解
    """
    
    def __init__(self, objectives: Dict[str, float]):
        """
        Args:
            objectives: 目标权重 {performance: 0.4, readability: 0.3, ...}
        """
        self.objectives = objectives
    
    def optimize(self, candidates: List[DesignCandidate]) -> List[DesignCandidate]:
        """
        对候选方案进行多目标优化排序
        
        返回按综合得分排序的方案列表
        """
        scored_candidates = []
        
        for candidate in candidates:
            score = self._calculate_score(candidate)
            scored_candidates.append((score, candidate))
        
        # 按得分降序排序
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        return [c for _, c in scored_candidates]
    
    def _calculate_score(self, candidate: DesignCandidate) -> float:
        """计算综合得分"""
        score = 0.0
        
        for obj_name, weight in self.objectives.items():
            if obj_name in candidate.objectives:
                score += weight * candidate.objectives[obj_name]
        
        # 惩罚高风险
        score -= (candidate.risk_score / 100) * 0.2
        
        return score
    
    def find_pareto_front(self, candidates: List[DesignCandidate]) -> List[DesignCandidate]:
        """
        找到Pareto前沿（不被其他方案全面超越的方案）
        """
        pareto = []
        
        for c1 in candidates:
            dominated = False
            for c2 in candidates:
                if c1 == c2:
                    continue
                # 检查c1是否被c2全面超越
                if self._dominates(c2, c1):
                    dominated = True
                    break
            if not dominated:
                pareto.append(c1)
        
        return pareto
    
    def _dominates(self, c1: DesignCandidate, c2: DesignCandidate) -> bool:
        """检查c1是否全面优于c2"""
        better_in_one = False
        
        for obj_name in self.objectives:
            v1 = c1.objectives.get(obj_name, 0)
            v2 = c2.objectives.get(obj_name, 0)
            
            if v1 < v2:
                return False  # c1在某个目标上更差
            if v1 > v2:
                better_in_one = True
        
        return better_in_one


class AnalogicalReasoning:
    """
    类比推理
    
    从相似代码中学习改进策略
    """
    
    def __init__(self, case_library: List[Dict] = None):
        self.case_library = case_library or []
    
    def add_case(self, case: Dict):
        """添加案例到库"""
        self.case_library.append(case)
    
    def find_similar_cases(self, target: Any, top_k: int = 3) -> List[Tuple[Dict, float]]:
        """
        查找相似案例
        
        基于代码特征计算相似度
        """
        similarities = []
        
        for case in self.case_library:
            similarity = self._calculate_similarity(target, case)
            if similarity > 0.3:  # 相似度阈值
                similarities.append((case, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def _calculate_similarity(self, target: Any, case: Dict) -> float:
        """计算目标与案例的相似度"""
        features = []
        
        # 基于代码特征计算
        if isinstance(target, FunctionInfo) and 'function' in case:
            case_func = case['function']
            
            # 复杂度相似度
            if 'complexity' in case_func:
                complexity_diff = abs(target.complexity - case_func['complexity'])
                complexity_sim = max(0, 1 - complexity_diff / 20)
                features.append(complexity_sim)
            
            # 调用模式相似度
            if 'calls' in case_func:
                target_calls = set(target.calls)
                case_calls = set(case_func['calls'])
                if target_calls and case_calls:
                    intersection = len(target_calls & case_calls)
                    union = len(target_calls | case_calls)
                    call_sim = intersection / union if union > 0 else 0
                    features.append(call_sim)
        
        return sum(features) / len(features) if features else 0.0
    
    def adapt_solution(self, target: Any, case: Dict) -> Dict:
        """
        适配案例解决方案到目标
        
        基于案例的成功经验，生成适合目标的方案
        """
        base_solution = case.get('solution', {})
        
        # 根据目标特征调整
        adapted = copy.deepcopy(base_solution)
        
        if isinstance(target, FunctionInfo):
            adapted['target_name'] = target.name
            adapted['target_file'] = target.file_path
            adapted['adapted_from'] = case.get('id', 'unknown')
        
        return adapted


class CreativeDesignLayer:
    """
    创造性设计层 - 主入口
    
    整合所有设计能力，实现创造性改进方案生成
    """
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path(__file__).parent
        self.pattern_lib = PatternLibrary()
        self.constraint_solver = ConstraintSatisfactionSolver()
        self.optimizer = MultiObjectiveOptimizer({
            'performance': 0.25,
            'readability': 0.25,
            'maintainability': 0.25,
            'testability': 0.15,
            'complexity': 0.10
        })
        self.analogy = AnalogicalReasoning()
        
        # 代码理解层（Phase 1）
        self.code_understanding = None
        if PHASE1_AVAILABLE and project_path:
            try:
                self.code_understanding = CodeUnderstandingLayer(project_path)
                self.code_understanding.build()
            except Exception as e:
                print(f"   ⚠️ 代码理解层初始化失败: {e}")
    
    def generate_improvements(self, target_file: str = None, 
                             constraints: List[Constraint] = None) -> List[DesignCandidate]:
        """
        生成改进方案
        
        Args:
            target_file: 目标文件（可选，None则分析整个项目）
            constraints: 额外约束
        
        Returns:
            按优先级排序的设计方案列表
        """
        print("🔮 Phase 2: 创造性设计...")
        
        candidates = []
        
        # 1. 获取代码理解信息
        if self.code_understanding:
            if target_file:
                module = self.code_understanding.get_module_info(target_file)
                targets = [module] if module else []
            else:
                targets = list(self.code_understanding.analyzer.modules.values())
        else:
            targets = []
        
        # 2. 为每个目标生成候选方案
        for target in targets:
            # 获取适用的模式
            applicable_patterns = self.pattern_lib.get_applicable_patterns(target)
            
            for pattern in applicable_patterns:
                # 生成候选
                changes = pattern.apply(target, {})
                
                candidate = DesignCandidate(
                    id=f"candidate_{pattern.id}_{target.file_path.replace('/', '_')}",
                    pattern_id=pattern.id,
                    description=f"应用{pattern.name}改进{target.file_path}",
                    changes=changes,
                    objectives=self._estimate_objectives(pattern),
                    constraints_satisfied=False,
                    risk_score=self._estimate_risk(target, pattern),
                    confidence=0.7,
                    reasoning=f"基于模式{pattern.name}，预期改善{pattern.estimated_impact}"
                )
                
                candidates.append(candidate)
        
        # 3. 应用类比推理（如果有案例库）
        if self.analogy.case_library:
            for target in targets:
                if isinstance(target, ModuleInfo):
                    for func in target.functions.values():
                        similar_cases = self.analogy.find_similar_cases(func)
                        for case, similarity in similar_cases:
                            adapted = self.analogy.adapt_solution(func, case)
                            
                            candidate = DesignCandidate(
                                id=f"candidate_analogy_{func.name}",
                                pattern_id="analogical_reasoning",
                                description=f"基于案例{case.get('id')}的类比改进",
                                changes=[adapted],
                                objectives=case.get('objectives', {}),
                                constraints_satisfied=False,
                                risk_score=case.get('risk_score', 50),
                                confidence=similarity,
                                reasoning=f"与案例相似度{similarity:.2f}"
                            )
                            
                            candidates.append(candidate)
        
        # 4. 约束满足求解
        if constraints:
            for c in constraints:
                self.constraint_solver.add_constraint(c)
        
        # 添加默认约束
        self.constraint_solver.add_constraint(Constraint(
            type="hard",
            description="风险不超过70",
            check=lambda c: c.risk_score <= 70
        ))
        
        valid_candidates = self.constraint_solver.solve(candidates)
        
        # 5. 多目标优化排序
        optimized = self.optimizer.optimize(valid_candidates)
        
        print(f"   生成了 {len(candidates)} 个候选方案")
        print(f"   满足约束: {len(valid_candidates)} 个")
        print(f"   最终推荐: {len(optimized)} 个")
        
        return optimized
    
    def _estimate_objectives(self, pattern: ArchitecturePattern) -> Dict[str, float]:
        """估计目标函数值"""
        objectives = {}
        for key, value in pattern.estimated_impact.items():
            # 归一化到0-1
            objectives[key] = min(max((value + 50) / 100, 0), 1)
        return objectives
    
    def _estimate_risk(self, target: Any, pattern: ArchitecturePattern) -> int:
        """估计风险"""
        base_risk = 30
        
        # 基于目标复杂度
        if isinstance(target, ModuleInfo):
            base_risk += min(target.complexity / 10, 30)
        
        # 基于模式风险
        if pattern.category == "structural":
            base_risk += 15
        elif pattern.category == "optimization":
            base_risk += 10
        
        return min(int(base_risk), 100)
    
    def explain_design(self, candidate: DesignCandidate) -> str:
        """解释设计方案"""
        pattern = self.pattern_lib.get_pattern(candidate.pattern_id)
        
        lines = []
        lines.append(f"# 设计方案: {candidate.description}")
        lines.append(f"\n**基于模式**: {pattern.name if pattern else '类比推理'}")
        lines.append(f"**置信度**: {candidate.confidence:.2f}")
        lines.append(f"**风险评分**: {candidate.risk_score}/100")
        lines.append(f"\n## 预期影响")
        for obj, value in candidate.objectives.items():
            lines.append(f"- {obj}: {value:.2f}")
        lines.append(f"\n## 推理过程")
        lines.append(candidate.reasoning)
        
        if pattern and pattern.examples:
            lines.append(f"\n## 参考案例")
            for ex in pattern.examples:
                lines.append(f"- {ex}")
        
        return "\n".join(lines)


def main():
    """测试创造性设计层"""
    import sys
    
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path(__file__).parent
    
    print(f"\n分析项目: {project_path}\n")
    
    # 初始化创造性设计层
    design_layer = CreativeDesignLayer(project_path)
    
    # 生成改进方案
    candidates = design_layer.generate_improvements()
    
    # 显示前5个方案
    print("\n" + "="*70)
    print("📋 Top 5 改进方案")
    print("="*70)
    
    for i, candidate in enumerate(candidates[:5], 1):
        print(f"\n{i}. {candidate.description}")
        print(f"   模式: {candidate.pattern_id}")
        print(f"   风险: {candidate.risk_score}/100")
        print(f"   置信度: {candidate.confidence:.2f}")
        print(f"   主要收益: {max(candidate.objectives.items(), key=lambda x: x[1])}")


if __name__ == "__main__":
    main()
