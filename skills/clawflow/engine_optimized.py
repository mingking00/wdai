#!/usr/bin/env python3
"""
ClawFlow v5.0 - Optimized

优化内容：
1. 真正的asyncio并行执行
2. 节点结果缓存
3. 性能监控
4. 优化的SkillNode调用
"""

from __future__ import annotations

import asyncio
import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from pathlib import Path
import threading


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    node_results: Dict[str, Any] = field(default_factory=dict)
    execution_log: List[Dict] = field(default_factory=list)
    parallel_stats: Dict = field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0


class NodeCache:
    """节点执行结果缓存"""
    
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, Dict] = {}
        self._ttl = ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, node_type: str, params: Dict, input_data: Any) -> str:
        """生成缓存键"""
        key_data = {
            "type": node_type,
            "params": params,
            "input": input_data
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()
    
    def get(self, node_type: str, params: Dict, input_data: Any) -> Optional[Any]:
        """获取缓存结果"""
        key = self._make_key(node_type, params, input_data)
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self._ttl:
                self.hits += 1
                return entry["result"]
            else:
                del self._cache[key]
        self.misses += 1
        return None
    
    def set(self, node_type: str, params: Dict, input_data: Any, result: Any):
        """设置缓存"""
        key = self._make_key(node_type, params, input_data)
        self._cache[key] = {
            "result": result,
            "timestamp": time.time()
        }
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self.hits = 0
        self.misses = 0


class OptimizedExecutionContext:
    """优化的执行上下文 - 协程安全"""
    
    def __init__(self, input_data: Dict[str, Any] = None):
        self.input_data = input_data or {}
        self.variables: Dict[str, Any] = {}
        self.node_outputs: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self.started_at = datetime.now()
    
    async def set_node_output_async(self, node_id: str, output: Any):
        """异步设置节点输出"""
        async with self._lock:
            self.node_outputs[node_id] = output
    
    def get_node_output(self, node_id: str) -> Any:
        return self.node_outputs.get(node_id)
    
    def evaluate_expression(self, expression: str) -> Any:
        """评估表达式"""
        if not expression.startswith("$"):
            return expression
        
        if expression.startswith("$input."):
            path = expression[7:].split(".")
            data = self.input_data
            for key in path:
                if isinstance(data, dict):
                    data = data.get(key)
                else:
                    return None
            return data
        
        if expression.startswith("$node."):
            parts = expression[6:].split(".")
            if len(parts) >= 2:
                node_id = parts[0]
                field_path = parts[1:]
                data = self.node_outputs.get(node_id)
                for key in field_path:
                    if isinstance(data, dict):
                        data = data.get(key)
                    else:
                        return None
                return data
            return self.node_outputs.get(parts[0])
        
        if expression.startswith("$var."):
            return self.variables.get(expression[5:])
        
        return expression
    
    def resolve_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """解析参数中的表达式"""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                resolved[key] = self.evaluate_expression(value)
            elif isinstance(value, dict):
                resolved[key] = self.resolve_parameters(value)
            elif isinstance(value, list):
                resolved[key] = [
                    self.evaluate_expression(item) 
                    if isinstance(item, str) and item.startswith("$") 
                    else item 
                    for item in value
                ]
            else:
                resolved[key] = value
        return resolved


class OptimizedWorkflowEngine:
    """优化版工作流引擎 v5.0"""
    
    def __init__(self, use_cache: bool = True, cache_ttl: int = 300):
        from .nodes import (
            TriggerNode, FunctionNode, OutputNode, HttpNode, IfNode, 
            MergeNode, DelayNode, TransformNode, FileNode, CSVNode, 
            JSONNode, DatabaseNode, LLMNode, EmailNode, CronNode,
            SkillNode, MessageNode
        )
        
        self.registry = {}
        self.cache = NodeCache(cache_ttl) if use_cache else None
        
        # 注册节点
        nodes = [
            ("trigger", TriggerNode()), ("function", FunctionNode()),
            ("output", OutputNode()), ("http", HttpNode()), ("if", IfNode()),
            ("merge", MergeNode()), ("delay", DelayNode()), ("transform", TransformNode()),
            ("file", FileNode()), ("csv", CSVNode()), ("json", JSONNode()),
            ("database", DatabaseNode()), ("llm", LLMNode()), ("email", EmailNode()),
            ("cron", CronNode()), ("skill", SkillNode()), ("message", MessageNode())
        ]
        for node_type, handler in nodes:
            self.registry[node_type] = handler
    
    def execute(self, workflow: Dict[str, Any],
                input_data: Dict[str, Any] = None,
                parallel: bool = False,
                use_cache: bool = True,
                verbose: bool = False) -> ExecutionResult:
        """执行工作流"""
        if parallel:
            return asyncio.run(self._execute_async(workflow, input_data, use_cache, verbose))
        else:
            return self._execute_sync(workflow, input_data, use_cache, verbose)
    
    async def _execute_async(self, workflow: Dict, input_data: Dict, use_cache: bool, verbose: bool) -> ExecutionResult:
        """异步执行 - 真正的并行"""
        start_time = time.time()
        
        try:
            context = OptimizedExecutionContext(input_data or {})
            nodes = {n["id"]: n for n in workflow.get("nodes", [])}
            connections = workflow.get("connections", [])
            
            graph = self._build_graph(nodes, connections)
            parallel_groups = self._find_parallel_groups(graph, list(nodes.keys()))
            
            if verbose:
                print(f"[Parallel] {len(parallel_groups)} execution levels")
            
            cache_hits = 0
            cache_misses = 0
            
            for level_idx, level_nodes in enumerate(parallel_groups):
                if verbose:
                    print(f"  Level {level_idx + 1}: {len(level_nodes)} nodes")
                
                # 创建任务
                tasks = []
                for node_id in level_nodes:
                    task = self._execute_node_async(
                        node_id, nodes[node_id], context, graph, 
                        use_cache, verbose
                    )
                    tasks.append(task)
                
                # 真正并行执行
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                for node_id, result in zip(level_nodes, results):
                    if isinstance(result, Exception):
                        return ExecutionResult(
                            success=False,
                            error=f"Node {node_id} failed: {result}",
                            execution_time=time.time() - start_time
                        )
                    if result.get("cached"):
                        cache_hits += 1
                    else:
                        cache_misses += 1
            
            execution_time = time.time() - start_time
            last_output = context.node_outputs.get(list(nodes.keys())[-1]) if nodes else None
            
            return ExecutionResult(
                success=True,
                data=last_output,
                execution_time=execution_time,
                node_results=context.node_outputs,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                parallel_stats={
                    "levels": len(parallel_groups),
                    "total_nodes": len(nodes),
                    "cache_efficiency": cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
                }
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _execute_node_async(self, node_id: str, node: Dict,
                                   context: OptimizedExecutionContext,
                                   graph: Dict, use_cache: bool, verbose: bool) -> Dict:
        """异步执行单个节点"""
        handler = self.registry.get(node["type"])
        if not handler:
            raise ValueError(f"Unknown node type: {node['type']}")
        
        # 等待依赖完成
        dependencies = self._get_dependencies(node_id, graph)
        while not all(dep in context.node_outputs for dep in dependencies):
            await asyncio.sleep(0.001)
        
        # 准备输入
        node_input = self._prepare_node_input(node_id, context, graph)
        resolved_params = context.resolve_parameters(node.get("params", {}))
        
        # 检查缓存
        if use_cache and self.cache:
            cached = self.cache.get(node["type"], resolved_params, node_input)
            if cached is not None:
                await context.set_node_output_async(node_id, cached)
                return {"cached": True}
        
        if verbose:
            print(f"    [Execute] {node_id} ({node['type']})")
        
        # 执行节点
        if hasattr(handler, 'execute_async'):
            output = await handler.execute_async(node_input, resolved_params, context)
        else:
            # 同步节点在线程池中执行
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None, handler.execute, node_input, resolved_params, context
            )
        
        # 保存结果
        await context.set_node_output_async(node_id, output)
        
        # 缓存结果
        if use_cache and self.cache:
            self.cache.set(node["type"], resolved_params, node_input, output)
        
        return {"cached": False}
    
    def _execute_sync(self, workflow: Dict, input_data: Dict, use_cache: bool, verbose: bool) -> ExecutionResult:
        """同步执行"""
        start_time = time.time()
        
        try:
            context = OptimizedExecutionContext(input_data or {})
            nodes = {n["id"]: n for n in workflow.get("nodes", [])}
            connections = workflow.get("connections", [])
            
            graph = self._build_graph(nodes, connections)
            execution_order = self._topological_sort(graph)
            
            cache_hits = 0
            cache_misses = 0
            
            for node_id in execution_order:
                node = nodes[node_id]
                handler = self.registry.get(node["type"])
                
                if not handler:
                    raise ValueError(f"Unknown node type: {node['type']}")
                
                node_input = self._prepare_node_input(node_id, context, graph)
                resolved_params = context.resolve_parameters(node.get("params", {}))
                
                # 检查缓存
                if use_cache and self.cache:
                    cached = self.cache.get(node["type"], resolved_params, node_input)
                    if cached is not None:
                        context.node_outputs[node_id] = cached
                        cache_hits += 1
                        continue
                
                # 执行
                output = handler.execute(node_input, resolved_params, context)
                context.node_outputs[node_id] = output
                cache_misses += 1
                
                # 缓存
                if use_cache and self.cache:
                    self.cache.set(node["type"], resolved_params, node_input, output)
            
            execution_time = time.time() - start_time
            last_output = context.node_outputs.get(execution_order[-1]) if execution_order else None
            
            return ExecutionResult(
                success=True,
                data=last_output,
                execution_time=execution_time,
                node_results=context.node_outputs,
                cache_hits=cache_hits,
                cache_misses=cache_misses
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _build_graph(self, nodes: Dict, connections: List[Dict]) -> Dict:
        """构建执行图"""
        graph = {node_id: [] for node_id in nodes}
        for conn in connections:
            from_node = conn.get("from")
            to_node = conn.get("to")
            if from_node in graph and to_node in graph:
                graph[from_node].append(to_node)
        return graph
    
    def _topological_sort(self, graph: Dict) -> List[str]:
        """拓扑排序"""
        in_degree = {node: 0 for node in graph}
        for node, neighbors in graph.items():
            for neighbor in neighbors:
                in_degree[neighbor] += 1
        
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def _find_parallel_groups(self, graph: Dict, node_ids: List[str]) -> List[List[str]]:
        """找出可以并行执行的节点组"""
        in_degree = {node: 0 for node in node_ids}
        for node, neighbors in graph.items():
            for neighbor in neighbors:
                in_degree[neighbor] += 1
        
        levels = []
        remaining = set(node_ids)
        
        while remaining:
            current_level = [n for n in remaining if in_degree[n] == 0]
            if not current_level:
                break
            
            levels.append(current_level)
            remaining -= set(current_level)
            
            for node in current_level:
                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
        
        return levels
    
    def _get_dependencies(self, node_id: str, graph: Dict) -> List[str]:
        """获取节点的所有依赖"""
        deps = []
        for from_node, to_nodes in graph.items():
            if node_id in to_nodes:
                deps.append(from_node)
        return deps
    
    def _prepare_node_input(self, node_id: str, context: OptimizedExecutionContext, graph: Dict) -> Any:
        """准备节点输入"""
        predecessors = []
        for from_node, to_nodes in graph.items():
            if node_id in to_nodes:
                pred_output = context.get_node_output(from_node)
                if pred_output is not None:
                    predecessors.append(pred_output)
        
        if not predecessors:
            return context.input_data
        if len(predecessors) == 1:
            return predecessors[0]
        return {"__merged__": predecessors}
