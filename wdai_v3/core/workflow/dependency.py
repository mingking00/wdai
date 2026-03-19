"""
wdai v3.0 - Dependency Resolver
SOP工作流引擎 - 依赖解析器

负责解析步骤依赖关系，构建DAG，检测循环依赖
"""

from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, deque
from .models import Workflow, Step, StepStatus


class DependencyGraph:
    """依赖图"""
    
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self._graph: Dict[str, Set[str]] = {}  # step_id -> set of dependencies
        self._reverse_graph: Dict[str, Set[str]] = {}  # step_id -> set of dependents
        self._build_graph()
    
    def _build_graph(self):
        """构建依赖图"""
        for step in self.workflow.steps:
            self._graph[step.id] = set(step.dependencies)
            self._reverse_graph[step.id] = set()
        
        # 构建反向图
        for step in self.workflow.steps:
            for dep_id in step.dependencies:
                if dep_id in self._reverse_graph:
                    self._reverse_graph[dep_id].add(step.id)
    
    def get_dependencies(self, step_id: str) -> Set[str]:
        """获取步骤的直接依赖"""
        return self._graph.get(step_id, set())
    
    def get_all_dependencies(self, step_id: str) -> Set[str]:
        """获取步骤的所有依赖（传递依赖）"""
        all_deps = set()
        to_visit = list(self.get_dependencies(step_id))
        
        while to_visit:
            dep = to_visit.pop()
            if dep not in all_deps:
                all_deps.add(dep)
                to_visit.extend(self.get_dependencies(dep))
        
        return all_deps
    
    def get_dependents(self, step_id: str) -> Set[str]:
        """获取依赖于该步骤的所有步骤"""
        return self._reverse_graph.get(step_id, set())
    
    def topological_sort(self) -> List[str]:
        """
        拓扑排序
        
        返回按执行顺序排列的步骤ID列表
        
        Raises:
            ValueError: 如果存在循环依赖
        """
        # 计算入度
        in_degree = {s.id: len(s.dependencies) for s in self.workflow.steps}
        
        # 找到所有入度为0的节点
        queue = deque([s.id for s in self.workflow.steps if in_degree[s.id] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # 减少依赖该节点的其他节点的入度
            for dependent in self.get_dependents(current):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # 检查是否有环
        if len(result) != len(self.workflow.steps):
            raise ValueError("工作流存在循环依赖")
        
        return result
    
    def find_cycles(self) -> List[List[str]]:
        """查找所有循环依赖"""
        cycles = []
        visited = set()
        rec_stack = []
        rec_set = set()
        
        def dfs(node: str):
            visited.add(node)
            rec_stack.append(node)
            rec_set.add(node)
            
            for neighbor in self._graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_set:
                    # 发现环
                    cycle_start = rec_stack.index(neighbor)
                    cycle = rec_stack[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.pop()
            rec_set.remove(node)
        
        for step_id in self._graph:
            if step_id not in visited:
                dfs(step_id)
        
        return cycles
    
    def get_ready_steps(self, completed_steps: Set[str]) -> List[str]:
        """
        获取可以执行的步骤
        
        返回所有依赖都已完成的步骤ID列表
        
        Args:
            completed_steps: 已完成的步骤ID集合
        """
        ready = []
        for step_id, deps in self._graph.items():
            if step_id not in completed_steps and deps.issubset(completed_steps):
                ready.append(step_id)
        return ready
    
    def get_execution_levels(self) -> List[List[str]]:
        """
        获取执行层级
        
        将步骤按依赖层级分组，同层级可以并行执行
        
        Returns:
            每个内层列表是一组可以并行执行的步骤ID
        """
        levels = []
        remaining = set(self._graph.keys())
        completed = set()
        
        while remaining:
            # 找到当前可以执行的步骤
            ready = []
            for step_id in remaining:
                deps = self._graph[step_id]
                if deps.issubset(completed):
                    ready.append(step_id)
            
            if not ready:
                # 没有可执行的步骤但还有剩余，说明有环
                raise ValueError(f"存在循环依赖，无法解析: {remaining}")
            
            levels.append(ready)
            completed.update(ready)
            remaining -= set(ready)
        
        return levels


class DependencyResolver:
    """依赖解析器"""
    
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.graph = DependencyGraph(workflow)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        验证工作流
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 检查步骤ID唯一性
        step_ids = [s.id for s in self.workflow.steps]
        seen = set()
        duplicates = set()
        for sid in step_ids:
            if sid in seen:
                duplicates.add(sid)
            seen.add(sid)
        
        if duplicates:
            errors.append(f"重复的步骤ID: {duplicates}")
        
        # 检查依赖是否存在
        for step in self.workflow.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    errors.append(f"步骤 '{step.id}' 依赖不存在的步骤 '{dep_id}'")
        
        # 检查循环依赖
        try:
            self.graph.topological_sort()
        except ValueError as e:
            errors.append(str(e))
            # 添加具体的环信息
            cycles = self.graph.find_cycles()
            for i, cycle in enumerate(cycles[:3], 1):  # 最多显示3个环
                errors.append(f"  循环 #{i}: {' -> '.join(cycle)}")
        
        return len(errors) == 0, errors
    
    def get_execution_order(self) -> List[str]:
        """获取执行顺序"""
        return self.graph.topological_sort()
    
    def get_parallel_groups(self) -> List[List[str]]:
        """获取可以并行执行的步骤组"""
        return self.graph.get_execution_levels()
    
    def get_next_executable(self, completed: Set[str], running: Set[str] = None) -> List[str]:
        """
        获取下一个可执行的步骤
        
        Args:
            completed: 已完成的步骤ID集合
            running: 正在运行的步骤ID集合（可选）
        
        Returns:
            可以立即执行的步骤ID列表
        """
        if running is None:
            running = set()
        
        ready = self.graph.get_ready_steps(completed)
        
        # 过滤掉正在运行的
        ready = [s for s in ready if s not in running]
        
        return ready
    
    def can_execute(self, step_id: str, completed: Set[str]) -> bool:
        """检查步骤是否可以执行"""
        deps = self.graph.get_dependencies(step_id)
        return deps.issubset(completed)
    
    def get_critical_path(self) -> List[str]:
        """
        获取关键路径
        
        返回从起点到终点最长的依赖链
        （简化版，假设每个步骤耗时相同）
        """
        # 计算每个节点的最长路径长度
        distances = {s.id: 0 for s in self.workflow.steps}
        order = self.graph.topological_sort()
        
        for step_id in order:
            for dependent in self.graph.get_dependents(step_id):
                distances[dependent] = max(distances[dependent], distances[step_id] + 1)
        
        # 找到最长路径
        if not distances:
            return []
        
        max_dist = max(distances.values())
        end_node = max(distances.keys(), key=lambda k: distances[k])
        
        # 回溯构建路径
        path = [end_node]
        current = end_node
        while distances[current] > 0:
            for dep in self.graph.get_dependencies(current):
                if distances[dep] == distances[current] - 1:
                    path.append(dep)
                    current = dep
                    break
        
        return list(reversed(path))


def resolve_dependencies(workflow: Workflow) -> DependencyResolver:
    """便捷函数：创建依赖解析器"""
    return DependencyResolver(workflow)
