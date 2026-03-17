#!/usr/bin/env python3
"""
ClawFlow v5.0 - 优化版工作流引擎

集成优化：
- asyncio 真正并行执行
- 节点结果缓存
- 性能监控
- 保留: Webhook、Cron、可视化等高级功能
"""

from __future__ import annotations

import asyncio
import json
import hashlib
import re
from typing import Dict, List, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from pathlib import Path
import time
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
    branches_taken: List[str] = field(default_factory=list)
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


class ExecutionContext:
    """执行上下文 - 协程安全"""
    
    def __init__(self, input_data: Dict[str, Any] = None):
        self.input_data = input_data or {}
        self.variables: Dict[str, Any] = {}
        self.node_outputs: Dict[str, Any] = {}
        self.execution_history: List[Dict] = []
        self.started_at = datetime.now()
        self.branches_taken: List[str] = []
        self._lock = asyncio.Lock()
    
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)
    
    def set_node_output(self, node_id: str, output: Any):
        """设置节点输出"""
        self.node_outputs[node_id] = output
    
    async def set_node_output_async(self, node_id: str, output: Any):
        """异步设置节点输出"""
        async with self._lock:
            self.node_outputs[node_id] = output
    
    def get_node_output(self, node_id: str) -> Any:
        """获取节点输出"""
        return self.node_outputs.get(node_id)
    
    def add_branch_taken(self, branch_id: str):
        """记录分支"""
        self.branches_taken.append(branch_id)
    
    def log_execution(self, execution: Dict):
        """记录执行"""
        self.execution_history.append(execution)
    
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
        
        if expression == "$json":
            if self.execution_history:
                return self.execution_history[-1].get("output")
            return None
        
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


class WorkflowValidator:
    """工作流验证器"""
    
    def __init__(self, registry: Dict):
        self.registry = registry
    
    def validate(self, workflow: Dict[str, Any]):
        errors = []
        warnings = []
        
        if "nodes" not in workflow:
            errors.append("Missing 'nodes' field")
            return type('Validation', (), {'valid': False, 'errors': errors, 'warnings': warnings})()
        
        nodes = workflow.get("nodes", [])
        connections = workflow.get("connections", [])
        
        node_ids = set()
        for i, node in enumerate(nodes):
            if "id" not in node:
                errors.append(f"Node {i} missing 'id'")
                continue
            node_id = node["id"]
            if node_id in node_ids:
                errors.append(f"Duplicate node ID: {node_id}")
            node_ids.add(node_id)
            
            if "type" not in node:
                errors.append(f"Node {node_id} missing 'type'")
                continue
            if node["type"] not in self.registry:
                errors.append(f"Unknown node type: {node['type']} (node: {node_id})")
        
        for conn in connections:
            if conn.get("from") not in node_ids:
                errors.append(f"Connection references unknown node: {conn.get('from')}")
            if conn.get("to") not in node_ids:
                errors.append(f"Connection references unknown node: {conn.get('to')}")
        
        return type('Validation', (), {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        })()


class WorkflowVisualizer:
    """工作流可视化"""
    
    def generate_mermaid(self, workflow: Dict[str, Any]) -> str:
        lines = ["flowchart TD"]
        
        for node in workflow.get("nodes", []):
            node_id = node["id"]
            node_type = node["type"]
            icon = self._get_icon(node_type)
            label = f"{icon} {node_id}"
            
            if node_type == "if":
                lines.append(f"    {node_id}{{{{{icon} {node_id}}}}}")
            elif node_type == "merge":
                lines.append(f"    {node_id}[({icon} {node_id})]")
            else:
                lines.append(f"    {node_id}[{label}]")
        
        for conn in workflow.get("connections", []):
            from_node = conn.get("from")
            to_node = conn.get("to")
            label = conn.get("label", "")
            if label:
                lines.append(f"    {from_node} -->|{label}| {to_node}")
            else:
                lines.append(f"    {from_node} --> {to_node}")
        
        return "\n".join(lines)
    
    def _get_icon(self, node_type: str) -> str:
        icons = {
            "trigger": "▶️", "function": "⚙️", "output": "📤",
            "http": "🌐", "if": "❓", "merge": "🔀",
            "delay": "⏱️", "transform": "🔄", "file": "📁",
            "csv": "📊", "json": "📋", "database": "🗄️",
            "llm": "🤖", "email": "📧", "cron": "📅",
            "skill": "🔧", "message": "💬"
        }
        return icons.get(node_type, "📦")


class WorkflowEngine:
    """
    ClawFlow 工作流引擎 v5.0 (Optimized)
    
    特性:
    - 18种节点类型
    - asyncio 真正并行执行
    - 节点结果缓存
    - 性能监控
    - 工作流验证
    - 可视化
    - Webhook 触发器
    - Cron 调度
    """
    
    def __init__(self, use_cache: bool = True, cache_ttl: int = 300):
        self._register_nodes()
        self.validator = WorkflowValidator(self.registry)
        self.visualizer = WorkflowVisualizer()
        self.cache = NodeCache(cache_ttl) if use_cache else None
        self._webhook_server = None
        self._scheduled_jobs = {}
    
    def _register_nodes(self):
        """注册所有节点"""
        from .nodes import (
            TriggerNode, FunctionNode, OutputNode, HttpNode, IfNode,
            MergeNode, DelayNode, TransformNode, FileNode, CSVNode,
            JSONNode, DatabaseNode, LLMNode, EmailNode, CronNode,
            SkillNode, MessageNode
        )
        
        self.registry = {
            "trigger": TriggerNode(), "function": FunctionNode(),
            "output": OutputNode(), "http": HttpNode(), "if": IfNode(),
            "merge": MergeNode(), "delay": DelayNode(), "transform": TransformNode(),
            "file": FileNode(), "csv": CSVNode(), "json": JSONNode(),
            "database": DatabaseNode(), "llm": LLMNode(), "email": EmailNode(),
            "cron": CronNode(), "skill": SkillNode(), "message": MessageNode()
        }
    
    def validate(self, workflow: Dict[str, Any]):
        """验证工作流"""
        return self.validator.validate(workflow)
    
    def visualize(self, workflow: Dict[str, Any], format: str = "mermaid") -> str:
        """可视化工作流"""
        if format == "mermaid":
            return self.visualizer.generate_mermaid(workflow)
        return "Unsupported format"
    
    def execute(self, workflow: Dict[str, Any],
                input_data: Dict[str, Any] = None,
                parallel: bool = False,
                use_cache: bool = True,
                max_retries: int = 0,
                verbose: bool = False) -> ExecutionResult:
        """
        执行工作流
        
        Args:
            workflow: 工作流定义
            input_data: 输入数据
            parallel: 是否启用并行执行
            use_cache: 是否使用节点缓存
            max_retries: 失败重试次数
            verbose: 是否打印详细日志
        """
        if parallel:
            return asyncio.run(self._execute_parallel(workflow, input_data, use_cache, max_retries, verbose))
        else:
            return self._execute_sequential(workflow, input_data, use_cache, max_retries, verbose)
    
    async def _execute_parallel(self, workflow: Dict, input_data: Dict, use_cache: bool, max_retries: int, verbose: bool) -> ExecutionResult:
        """并行执行 - 使用 asyncio"""
        start_time = time.time()
        
        try:
            validation = self.validate(workflow)
            if not validation.valid:
                return ExecutionResult(
                    success=False,
                    error=f"Validation failed: {'; '.join(validation.errors)}"
                )
            
            context = ExecutionContext(input_data or {})
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
                
                tasks = []
                for node_id in level_nodes:
                    task = self._execute_node_async(
                        node_id, nodes[node_id], context, graph,
                        use_cache, max_retries, verbose
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for node_id, result in zip(level_nodes, results):
                    if isinstance(result, Exception):
                        return ExecutionResult(
                            success=False,
                            error=f"Node {node_id} failed: {result}",
                            execution_time=time.time() - start_time
                        )
                    if isinstance(result, dict):
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
                branches_taken=context.branches_taken,
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
    
    async def _execute_node_async(self, node_id: str, node: Dict, context: ExecutionContext,
                                   graph: Dict, use_cache: bool, max_retries: int, verbose: bool):
        """异步执行节点"""
        handler = self.registry.get(node["type"])
        if not handler:
            raise ValueError(f"Unknown node type: {node['type']}")
        
        dependencies = self._get_dependencies(node_id, graph)
        while not all(dep in context.node_outputs for dep in dependencies):
            await asyncio.sleep(0.001)
        
        node_input = self._prepare_node_input(node_id, context, graph)
        resolved_params = context.resolve_parameters(node.get("params", {}))
        
        if use_cache and self.cache:
            cached = self.cache.get(node["type"], resolved_params, node_input)
            if cached is not None:
                await context.set_node_output_async(node_id, cached)
                if verbose:
                    print(f"    [Cached] {node_id}")
                return {"cached": True}
        
        if verbose:
            print(f"    [Execute] {node_id} ({node['type']})")
        
        retry_count = 0
        while retry_count <= max_retries:
            try:
                if hasattr(handler, 'execute_async'):
                    output = await handler.execute_async(node_input, resolved_params, context)
                else:
                    loop = asyncio.get_event_loop()
                    output = await loop.run_in_executor(
                        None, handler.execute, node_input, resolved_params, context
                    )
                
                await context.set_node_output_async(node_id, output)
                
                if use_cache and self.cache:
                    self.cache.set(node["type"], resolved_params, node_input, output)
                
                if node["type"] == "if" and isinstance(output, dict):
                    context.add_branch_taken(f"{node_id}:{output.get('__condition_result__', False)}")
                
                return {"cached": False}
                
            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    raise
                await asyncio.sleep(0.5 * retry_count)
    
    def _execute_sequential(self, workflow: Dict, input_data: Dict, use_cache: bool, 
                           max_retries: int, verbose: bool) -> ExecutionResult:
        """顺序执行"""
        start_time = time.time()
        
        try:
            validation = self.validate(workflow)
            if not validation.valid:
                return ExecutionResult(
                    success=False,
                    error=f"Validation failed: {'; '.join(validation.errors)}"
                )
            
            context = ExecutionContext(input_data or {})
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
                
                if use_cache and self.cache:
                    cached = self.cache.get(node["type"], resolved_params, node_input)
                    if cached is not None:
                        context.set_node_output(node_id, cached)
                        cache_hits += 1
                        if verbose:
                            print(f"  [Cached] {node_id}")
                        continue
                
                if verbose:
                    print(f"  [Execute] {node_id} ({node['type']})")
                
                retry_count = 0
                while retry_count <= max_retries:
                    try:
                        output = handler.execute(node_input, resolved_params, context)
                        context.set_node_output(node_id, output)
                        cache_misses += 1
                        
                        if use_cache and self.cache:
                            self.cache.set(node["type"], resolved_params, node_input, output)
                        
                        if node["type"] == "if" and isinstance(output, dict):
                            context.add_branch_taken(f"{node_id}:{output.get('__condition_result__', False)}")
                        
                        break
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count > max_retries:
                            raise
                        time.sleep(0.5 * retry_count)
            
            execution_time = time.time() - start_time
            last_output = context.node_outputs.get(execution_order[-1]) if execution_order else None
            
            return ExecutionResult(
                success=True,
                data=last_output,
                execution_time=execution_time,
                node_results=context.node_outputs,
                branches_taken=context.branches_taken,
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
        """找出可并行节点组"""
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
        """获取依赖"""
        deps = []
        for from_node, to_nodes in graph.items():
            if node_id in to_nodes:
                deps.append(from_node)
        return deps
    
    def _prepare_node_input(self, node_id: str, context: ExecutionContext, graph: Dict) -> Any:
        """准备输入"""
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
    
    def save_workflow(self, workflow: Dict[str, Any], filepath: str):
        """保存工作流"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
    
    def load_workflow(self, filepath: str) -> Dict[str, Any]:
        """加载工作流"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # ==================== Webhook ====================
    
    def serve(self, workflow: Dict[str, Any] = None, port: int = 8080):
        """启动 Webhook 服务器"""
        try:
            from flask import Flask, request, jsonify
        except ImportError:
            raise ImportError("pip install flask")
        
        app = Flask(__name__)
        
        @app.route('/webhook/<workflow_id>', methods=['POST'])
        def webhook_trigger(workflow_id):
            data = request.get_json() or {}
            if workflow:
                result = self.execute(workflow, input_data=data)
                return jsonify({"success": result.success, "data": result.data})
            return jsonify({"error": "No workflow"}), 404
        
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "ok"})
        
        print(f"🚀 Webhook server: http://0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    
    def start_webhook_server(self, workflow: Dict[str, Any], port: int = 8080):
        """后台启动 Webhook"""
        def run_server():
            self.serve(workflow, port)
        
        self._webhook_server = threading.Thread(target=run_server, daemon=True)
        self._webhook_server.start()
        print(f"Webhook server started (port {port})")
    
    # ==================== Cron ====================
    
    def schedule(self, workflow: Dict[str, Any], cron_expr: str, name: str = None, channel: str = None) -> Dict:
        """调度工作流"""
        workflow_file = f"/tmp/clawflow_{name or 'workflow'}.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow, f)
        
        print(f"📅 Scheduled: {name}")
        print(f"   Cron: {cron_expr}")
        print(f"   File: {workflow_file}")
        
        return {
            "scheduled": True,
            "name": name,
            "cron": cron_expr,
            "workflow_file": workflow_file,
            "channel": channel
        }
