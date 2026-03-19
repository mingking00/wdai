"""
Kimi Multi-Agent Platform - Core Engine
Phase 1: Workflow Engine with DAG Execution
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from collections import deque


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeType(Enum):
    START = "start"
    END = "end"
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"


@dataclass
class Context:
    """执行上下文"""
    workflow_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    
    def get(self, key: str, default=None):
        return self.variables.get(key, default)
    
    def set(self, key: str, value: Any):
        self.variables[key] = value
    
    def log(self, node_id: str, status: str, data: Any = None):
        self.history.append({
            "node_id": node_id,
            "status": status,
            "timestamp": time.time(),
            "data": data
        })


@dataclass
class NodeResult:
    """节点执行结果"""
    status: NodeStatus
    output: Any = None
    error: Optional[str] = None
    next_nodes: List[str] = field(default_factory=list)


class Node(ABC):
    """工作流节点基类"""
    
    def __init__(self, node_id: str, node_type: NodeType, config: Dict = None):
        self.node_id = node_id
        self.node_type = node_type
        self.config = config or {}
        self.status = NodeStatus.PENDING
        self.input_data: Any = None
        self.output_data: Any = None
    
    @abstractmethod
    def execute(self, context: Context) -> NodeResult:
        """执行节点逻辑"""
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.node_id}, type={self.node_type.value})"


class StartNode(Node):
    """开始节点"""
    
    def __init__(self, node_id: str = "start", config: Dict = None):
        super().__init__(node_id, NodeType.START, config)
    
    def execute(self, context: Context) -> NodeResult:
        print(f"[StartNode] {self.node_id} - Workflow started")
        return NodeResult(
            status=NodeStatus.COMPLETED,
            output=self.config.get("initial_data", {})
        )


class EndNode(Node):
    """结束节点"""
    
    def __init__(self, node_id: str = "end", config: Dict = None):
        super().__init__(node_id, NodeType.END, config)
    
    def execute(self, context: Context) -> NodeResult:
        print(f"[EndNode] {self.node_id} - Workflow completed")
        return NodeResult(
            status=NodeStatus.COMPLETED,
            output=context.variables
        )


class TaskNode(Node):
    """任务节点 - 执行具体任务"""
    
    def __init__(self, node_id: str, config: Dict = None):
        super().__init__(node_id, NodeType.TASK, config)
        self.handler: Optional[Callable] = None
    
    def set_handler(self, handler: Callable):
        """设置任务处理函数"""
        self.handler = handler
    
    def execute(self, context: Context) -> NodeResult:
        print(f"[TaskNode] {self.node_id} - Executing task")
        
        try:
            if self.handler:
                result = self.handler(context, self.config)
                return NodeResult(
                    status=NodeStatus.COMPLETED,
                    output=result
                )
            else:
                # 默认行为：传递输入
                return NodeResult(
                    status=NodeStatus.COMPLETED,
                    output=self.input_data
                )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )


class ConditionNode(Node):
    """条件节点 - 分支判断"""
    
    def __init__(self, node_id: str, config: Dict = None):
        super().__init__(node_id, NodeType.CONDITION, config)
        self.condition_func: Optional[Callable] = None
    
    def set_condition(self, func: Callable):
        """设置条件判断函数"""
        self.condition_func = func
    
    def execute(self, context: Context) -> NodeResult:
        print(f"[ConditionNode] {self.node_id} - Evaluating condition")
        
        try:
            if self.condition_func:
                result = self.condition_func(context, self.config)
                branch = "true" if result else "false"
                print(f"[ConditionNode] Branch: {branch}")
                
                return NodeResult(
                    status=NodeStatus.COMPLETED,
                    output=result,
                    next_nodes=[branch]
                )
            else:
                # 默认条件：检查input是否为真
                result = bool(self.input_data)
                branch = "true" if result else "false"
                return NodeResult(
                    status=NodeStatus.COMPLETED,
                    output=result,
                    next_nodes=[branch]
                )
        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )


class DAG:
    """有向无环图 - 工作流拓扑结构"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[str]] = {}  # from -> [to]
        self.edge_labels: Dict[Tuple[str, str], str] = {}  # (from, to) -> label
    
    def add_node(self, node: Node) -> "DAG":
        """添加节点"""
        self.nodes[node.node_id] = node
        if node.node_id not in self.edges:
            self.edges[node.node_id] = []
        return self
    
    def add_edge(self, from_node: str, to_node: str, label: str = None) -> "DAG":
        """添加边"""
        if from_node not in self.nodes:
            raise ValueError(f"Node {from_node} not found")
        if to_node not in self.nodes:
            raise ValueError(f"Node {to_node} not found")
        
        self.edges[from_node].append(to_node)
        if label:
            self.edge_labels[(from_node, to_node)] = label
        return self
    
    def get_next_nodes(self, node_id: str, branch: str = None) -> List[str]:
        """获取下一个节点"""
        next_nodes = self.edges.get(node_id, [])
        
        if branch and node_id in self.nodes:
            node = self.nodes[node_id]
            if node.node_type == NodeType.CONDITION:
                # 对于条件节点，根据分支选择
                result = []
                for next_node in next_nodes:
                    edge_label = self.edge_labels.get((node_id, next_node))
                    if edge_label == branch:
                        result.append(next_node)
                return result
        
        return next_nodes
    
    def topological_sort(self) -> List[str]:
        """拓扑排序 - 确定执行顺序"""
        in_degree = {node: 0 for node in self.nodes}
        for from_node, to_nodes in self.edges.items():
            for to_node in to_nodes:
                in_degree[to_node] += 1
        
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for next_node in self.edges.get(node, []):
                in_degree[next_node] -= 1
                if in_degree[next_node] == 0:
                    queue.append(next_node)
        
        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected in DAG")
        
        return result
    
    def validate(self) -> bool:
        """验证DAG有效性"""
        # 检查是否有开始节点
        start_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.START]
        if len(start_nodes) == 0:
            raise ValueError("No start node found")
        
        # 检查是否有结束节点
        end_nodes = [n for n in self.nodes.values() if n.node_type == NodeType.END]
        if len(end_nodes) == 0:
            raise ValueError("No end node found")
        
        # 检查是否有环
        try:
            self.topological_sort()
        except ValueError as e:
            raise ValueError(f"Invalid DAG: {e}")
        
        return True
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            "workflow_id": self.workflow_id,
            "nodes": [
                {
                    "id": n.node_id,
                    "type": n.node_type.value,
                    "config": n.config
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "from": from_node,
                    "to": to_node,
                    "label": self.edge_labels.get((from_node, to_node))
                }
                for from_node, to_nodes in self.edges.items()
                for to_node in to_nodes
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DAG":
        """从字典反序列化"""
        dag = cls(data["workflow_id"])
        
        # 创建节点
        for node_data in data["nodes"]:
            node_type = NodeType(node_data["type"])
            if node_type == NodeType.START:
                node = StartNode(node_data["id"], node_data.get("config"))
            elif node_type == NodeType.END:
                node = EndNode(node_data["id"], node_data.get("config"))
            elif node_type == NodeType.TASK:
                node = TaskNode(node_data["id"], node_data.get("config"))
            elif node_type == NodeType.CONDITION:
                node = ConditionNode(node_data["id"], node_data.get("config"))
            else:
                node = TaskNode(node_data["id"], node_data.get("config"))
            
            dag.add_node(node)
        
        # 创建边
        for edge_data in data["edges"]:
            dag.add_edge(
                edge_data["from"],
                edge_data["to"],
                edge_data.get("label")
            )
        
        return dag


class WorkflowEngine:
    """工作流引擎 - 执行DAG"""
    
    def __init__(self):
        self.running_workflows: Dict[str, Context] = {}
    
    def execute(self, dag: DAG, initial_data: Dict = None) -> Dict:
        """
        执行工作流
        
        Args:
            dag: 工作流DAG
            initial_data: 初始数据
        
        Returns:
            执行结果
        """
        # 验证DAG
        dag.validate()
        
        # 创建上下文
        context = Context(
            workflow_id=dag.workflow_id,
            variables=initial_data or {}
        )
        self.running_workflows[dag.workflow_id] = context
        
        print(f"\n[WorkflowEngine] Starting workflow: {dag.workflow_id}")
        print("=" * 50)
        
        # 找到开始节点
        start_nodes = [n for n in dag.nodes.values() if n.node_type == NodeType.START]
        if not start_nodes:
            raise ValueError("No start node found")
        
        # BFS执行
        executed = set()
        queue = deque([start_nodes[0].node_id])
        
        while queue:
            node_id = queue.popleft()
            
            if node_id in executed:
                continue
            
            node = dag.nodes[node_id]
            
            # 检查前置节点是否都已完成
            predecessors = [
                n for n, edges in dag.edges.items()
                if node_id in edges and n not in executed
            ]
            if predecessors:
                queue.append(node_id)
                continue
            
            # 执行节点
            print(f"\n[Executing] {node}")
            node.status = NodeStatus.RUNNING
            context.log(node_id, "started")
            
            result = node.execute(context)
            node.status = result.status
            node.output_data = result.output
            
            executed.add(node_id)
            context.log(node_id, result.status.value, result.output)
            
            print(f"[Result] Status: {result.status.value}")
            if result.output:
                print(f"[Output] {result.output}")
            
            if result.status == NodeStatus.FAILED:
                print(f"[Error] {result.error}")
                break
            
            # 获取下一个节点
            if result.next_nodes:
                # 条件节点的分支
                for branch in result.next_nodes:
                    next_nodes = dag.get_next_nodes(node_id, branch)
                    queue.extend(next_nodes)
            else:
                next_nodes = dag.get_next_nodes(node_id)
                queue.extend(next_nodes)
        
        print("\n" + "=" * 50)
        print(f"[WorkflowEngine] Workflow completed: {dag.workflow_id}")
        
        # 清理
        del self.running_workflows[dag.workflow_id]
        
        return {
            "workflow_id": dag.workflow_id,
            "status": "completed",
            "executed_nodes": list(executed),
            "context": context.variables,
            "history": context.history
        }


# 便捷函数
def create_workflow(workflow_id: str) -> DAG:
    """创建工作流"""
    return DAG(workflow_id)


def run_workflow(dag: DAG, initial_data: Dict = None) -> Dict:
    """运行工作流"""
    engine = WorkflowEngine()
    return engine.execute(dag, initial_data)
