#!/usr/bin/env python3
"""
Hybrid DAG + Actor Parallel Orchestrator
混合并行编排器：DAG依赖图 + Actor消息模型

结合了两种模式的优势：
- DAG: 明确依赖关系，拓扑排序决定执行顺序
- Actor: 消息驱动，松耦合，支持动态通信
"""

import asyncio
import json
from typing import Dict, Any, Set, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time

# 导入Tools
import sys
sys.path.insert(0, '/root/.openclaw/workspace/kimi-mcp-server/src')
from extended_tools import KimiMCPExtendedServer


class MessageType(Enum):
    """消息类型"""
    TASK = "task"           # 新任务
    RESULT = "result"       # 任务完成结果
    ERROR = "error"         # 错误
    STATUS = "status"       # 状态更新
    BROADCAST = "broadcast" # 广播消息


@dataclass
class Message:
    """Actor消息"""
    msg_id: str
    msg_type: MessageType
    sender: str
    receiver: Optional[str]  # None表示广播
    content: Any
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "msg_id": self.msg_id,
            "type": self.msg_type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "timestamp": self.timestamp
        }


class MessageBus:
    """消息总线 - 连接所有Actor"""
    
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: List[Message] = []
    
    def register_actor(self, actor_id: str):
        """注册Actor"""
        if actor_id not in self.queues:
            self.queues[actor_id] = asyncio.Queue()
    
    def subscribe(self, msg_type: MessageType, callback: Callable):
        """订阅消息类型"""
        if msg_type not in self.subscribers:
            self.subscribers[msg_type] = []
        self.subscribers[msg_type].append(callback)
    
    async def send(self, msg: Message):
        """发送消息"""
        self.message_history.append(msg)
        
        # 广播或单发
        if msg.receiver is None:
            # 广播给所有订阅者
            callbacks = self.subscribers.get(msg.msg_type, [])
            for callback in callbacks:
                asyncio.create_task(callback(msg))
        else:
            # 发送给特定Actor
            if msg.receiver in self.queues:
                await self.queues[msg.receiver].put(msg)
    
    async def receive(self, actor_id: str, timeout: float = None) -> Optional[Message]:
        """接收消息"""
        if actor_id not in self.queues:
            return None
        
        try:
            return await asyncio.wait_for(
                self.queues[actor_id].get(), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None


class ActorAgent:
    """
    Actor智能体基类
    
    每个Actor有自己的：
    - 消息队列
    - 状态管理
    - 生命周期（init → run → stop）
    """
    
    def __init__(self, agent_id: str, role: str, bus: MessageBus):
        self.agent_id = agent_id
        self.role = role
        self.bus = bus
        self.server = KimiMCPExtendedServer()
        self.state: Dict[str, Any] = {}
        self.running = False
        self.task_count = 0
        
        # 注册到消息总线
        self.bus.register_actor(agent_id)
    
    def log(self, msg: str):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"   [{timestamp}] 🤖 {self.agent_id}: {msg}")
    
    async def run(self):
        """主循环 - 持续监听消息"""
        self.running = True
        self.log("🚀 Actor started")
        
        while self.running:
            msg = await self.bus.receive(self.agent_id, timeout=1.0)
            
            if msg:
                await self.handle_message(msg)
        
        self.log("🛑 Actor stopped")
    
    async def handle_message(self, msg: Message):
        """处理消息 - 子类可覆盖"""
        if msg.msg_type == MessageType.TASK:
            await self.handle_task(msg)
        elif msg.msg_type == MessageType.BROADCAST:
            await self.handle_broadcast(msg)
    
    async def handle_task(self, msg: Message):
        """处理任务 - 子类实现"""
        raise NotImplementedError
    
    async def handle_broadcast(self, msg: Message):
        """处理广播"""
        pass
    
    async def send_result(self, task_id: str, result: Any, to: str):
        """发送结果"""
        msg = Message(
            msg_id=f"{self.agent_id}_result_{task_id}",
            msg_type=MessageType.RESULT,
            sender=self.agent_id,
            receiver=to,
            content={
                "task_id": task_id,
                "result": result,
                "agent": self.agent_id
            }
        )
        await self.bus.send(msg)
    
    async def send_error(self, task_id: str, error: str, to: str):
        """发送错误"""
        msg = Message(
            msg_id=f"{self.agent_id}_error_{task_id}",
            msg_type=MessageType.ERROR,
            sender=self.agent_id,
            receiver=to,
            content={
                "task_id": task_id,
                "error": error,
                "agent": self.agent_id
            }
        )
        await self.bus.send(msg)
    
    def stop(self):
        """停止Actor"""
        self.running = False


class ParallelResearchAgent(ActorAgent):
    """并行研究智能体"""
    
    def __init__(self, agent_id: str, bus: MessageBus):
        super().__init__(agent_id, "Research", bus)
    
    async def handle_task(self, msg: Message):
        """执行研究任务"""
        task = msg.content
        topic = task.get("topic", "Unknown")
        task_id = task.get("task_id", "unknown")
        
        self.log(f"🔍 开始研究: {topic}")
        
        # 模拟研究过程（实际使用真实API）
        await asyncio.sleep(0.5)  # 模拟耗时
        
        result = {
            "topic": topic,
            "findings": [
                f"Finding 1 about {topic}",
                f"Finding 2 about {topic}"
            ],
            "sources": ["github", "arxiv"],
            "completed_at": datetime.now().isoformat()
        }
        
        self.log(f"✅ 研究完成: {len(result['findings'])} 个发现")
        
        # 发送结果给依赖的下游Agent
        for downstream in task.get("downstream", []):
            await self.send_result(task_id, result, downstream)


class ParallelCodeAgent(ActorAgent):
    """并行代码智能体"""
    
    def __init__(self, agent_id: str, bus: MessageBus):
        super().__init__(agent_id, "Code", bus)
        self.pending_deps: Dict[str, Set[str]] = {}  # 等待的依赖
        self.collected_results: Dict[str, Any] = {}
    
    async def handle_task(self, msg: Message):
        """处理代码任务（可能有依赖）"""
        task = msg.content
        task_id = task.get("task_id", "unknown")
        
        # 检查依赖
        deps = set(task.get("depends_on", []))
        if deps:
            self.pending_deps[task_id] = deps
            self.log(f"⏳ 等待依赖: {deps}")
            return
        
        await self.execute_code_task(task)
    
    async def handle_message(self, msg: Message):
        """处理消息（包括依赖结果）"""
        if msg.msg_type == MessageType.RESULT:
            # 收到上游结果
            await self.handle_dependency_result(msg)
        else:
            await super().handle_message(msg)
    
    async def handle_dependency_result(self, msg: Message):
        """处理依赖完成"""
        sender = msg.sender
        content = msg.content
        
        self.log(f"📨 收到来自 {sender} 的结果")
        self.collected_results[sender] = content.get("result", {})
        
        # 检查是否有任务可以执行
        for task_id, deps in list(self.pending_deps.items()):
            if sender in deps:
                deps.discard(sender)
                
                if not deps:  # 所有依赖都完成了
                    self.log(f"✅ 所有依赖已满足，开始执行任务")
                    del self.pending_deps[task_id]
                    
                    # 执行任务
                    await self.execute_code_task({
                        "task_id": task_id,
                        "dependencies_result": self.collected_results
                    })
    
    async def execute_code_task(self, task: Dict):
        """执行代码任务"""
        task_id = task.get("task_id", "unknown")
        
        self.log(f"💻 开始编写代码...")
        
        await asyncio.sleep(0.5)  # 模拟耗时
        
        # 使用真实Tool创建文件
        result = self.server.call_tool('file_write_text', {
            'path': f'/tmp/parallel_demo/{task_id}_code.py',
            'content': f'# Generated by {self.agent_id}\n# Task: {task_id}\n\nprint("Hello from {task_id}")'
        })
        
        output = {
            "files_created": 1,
            "success": result['success'],
            "task_id": task_id
        }
        
        self.log(f"✅ 代码完成: {output['files_created']} 个文件")
        
        # 发送给下游
        for downstream in task.get("downstream", []):
            await self.send_result(task_id, output, downstream)


class ParallelDocAgent(ActorAgent):
    """并行文档智能体"""
    
    def __init__(self, agent_id: str, bus: MessageBus):
        super().__init__(agent_id, "Documentation", bus)
        self.collected_data = {}
    
    async def handle_task(self, msg: Message):
        """处理文档任务"""
        task = msg.content
        task_id = task.get("task_id", "unknown")
        
        self.log(f"📝 开始生成文档...")
        
        # 收集所有上游数据
        research_data = self.collected_data.get("research", {})
        code_data = self.collected_data.get("code", {})
        
        await asyncio.sleep(0.3)  # 模拟耗时
        
        doc = f"""# Project Documentation

Generated by {self.agent_id}
Task: {task_id}

## Research Summary
{research_data.get('findings', [])}

## Code Output
{code_data.get('files_created', 0)} files created

Generated at: {datetime.now().isoformat()}
"""
        
        result = self.server.call_tool('file_write_text', {
            'path': f'/tmp/parallel_demo/{task_id}_README.md',
            'content': doc
        })
        
        output = {
            "document_length": len(doc),
            "success": result['success']
        }
        
        self.log(f"✅ 文档完成: {output['document_length']} 字符")
        
        # 通知完成
        await self.send_result(task_id, output, "orchestrator")
    
    async def handle_message(self, msg: Message):
        """收集上游数据"""
        if msg.msg_type == MessageType.RESULT:
            sender = msg.sender
            content = msg.content
            
            if "research" in sender.lower():
                self.collected_data["research"] = content.get("result", {})
                self.log(f"📥 收到研究数据")
            elif "code" in sender.lower():
                self.collected_data["code"] = content.get("result", {})
                self.log(f"📥 收到代码数据")
        
        await super().handle_message(msg)


class DAG:
    """DAG依赖图"""
    
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, Set[str]] = {}  # node -> 依赖的nodes
        self.reverse_edges: Dict[str, Set[str]] = {}  # node -> 被依赖的nodes
    
    def add_node(self, node_id: str):
        """添加节点"""
        self.nodes.add(node_id)
        if node_id not in self.edges:
            self.edges[node_id] = set()
        if node_id not in self.reverse_edges:
            self.reverse_edges[node_id] = set()
    
    def add_edge(self, from_node: str, to_node: str):
        """添加边：from_node 完成后 to_node 才能开始"""
        self.add_node(from_node)
        self.add_node(to_node)
        self.edges[to_node].add(from_node)
        self.reverse_edges[from_node].add(to_node)
    
    def get_dependencies(self, node_id: str) -> Set[str]:
        """获取节点的依赖"""
        return self.edges.get(node_id, set())
    
    def get_dependents(self, node_id: str) -> Set[str]:
        """获取依赖此节点的节点"""
        return self.reverse_edges.get(node_id, set())
    
    def get_ready_nodes(self, completed: Set[str]) -> Set[str]:
        """获取就绪节点（所有依赖已完成）"""
        ready = set()
        for node in self.nodes:
            if node not in completed:
                deps = self.get_dependencies(node)
                if deps.issubset(completed):
                    ready.add(node)
        return ready
    
    def topological_sort(self) -> List[str]:
        """拓扑排序"""
        in_degree = {node: len(self.edges[node]) for node in self.nodes}
        queue = [n for n in self.nodes if in_degree[n] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in self.reverse_edges[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result


class HybridOrchestrator:
    """
    混合编排器
    
    DAG决定执行顺序
    Actor实现并行通信
    """
    
    def __init__(self):
        self.bus = MessageBus()
        self.dag = DAG()
        self.agents: Dict[str, ActorAgent] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        self.completed: Set[str] = set()
        self.results: Dict[str, Any] = {}
    
    def add_agent(self, agent: ActorAgent, depends_on: List[str] = None):
        """添加智能体"""
        self.agents[agent.agent_id] = agent
        self.dag.add_node(agent.agent_id)
        
        if depends_on:
            for dep in depends_on:
                self.dag.add_edge(dep, agent.agent_id)
    
    async def start_all_agents(self):
        """启动所有Agent"""
        for agent_id, agent in self.agents.items():
            self.agent_tasks[agent_id] = asyncio.create_task(agent.run())
    
    async def execute(self, initial_task: Dict) -> Dict[str, Any]:
        """执行工作流"""
        print("\n" + "="*70)
        print("🚀 HYBRID PARALLEL EXECUTION (DAG + Actor)")
        print("="*70)
        
        # 启动所有Agent
        await self.start_all_agents()
        
        print(f"\n📊 工作流配置:")
        print(f"   • 智能体数量: {len(self.agents)}")
        print(f"   • 依赖关系: {sum(len(d) for d in self.dag.edges.values())} 条边")
        print(f"   • 拓扑顺序: {' → '.join(self.dag.topological_sort())}")
        
        print(f"\n⏳ 开始执行...\n")
        start_time = time.time()
        
        # 启动初始任务（给无依赖的Agent）
        ready_agents = self.dag.get_ready_nodes(self.completed)
        
        for agent_id in ready_agents:
            await self._assign_task(agent_id, initial_task)
        
        # 等待所有完成
        while len(self.completed) < len(self.agents):
            await asyncio.sleep(0.1)
            
            # 检查新就绪的Agent
            new_ready = self.dag.get_ready_nodes(self.completed) - set(
                agent_id for agent_id in self.agents 
                if agent_id not in self.completed
            )
            
            for agent_id in new_ready:
                # 收集依赖结果
                deps = self.dag.get_dependencies(agent_id)
                dep_results = {dep: self.results.get(dep, {}) for dep in deps}
                
                await self._assign_task(agent_id, {
                    **initial_task,
                    "dependencies_result": dep_results
                })
        
        # 停止所有Agent
        for agent in self.agents.values():
            agent.stop()
        
        # 等待Agent停止
        await asyncio.gather(*self.agent_tasks.values(), return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*70)
        print("📊 EXECUTION SUMMARY")
        print("="*70)
        print(f"   ⏱️  总耗时: {elapsed:.3f}s")
        print(f"   ✅ 完成: {len(self.completed)}/{len(self.agents)}")
        print(f"   📁 产出: {len(self.results)} 个结果")
        
        return self.results
    
    async def _assign_task(self, agent_id: str, task: Dict):
        """分配任务给Agent"""
        msg = Message(
            msg_id=f"task_{agent_id}_{time.time()}",
            msg_type=MessageType.TASK,
            sender="orchestrator",
            receiver=agent_id,
            content={
                **task,
                "downstream": list(self.dag.get_dependents(agent_id))
            }
        )
        await self.bus.send(msg)
    
    def on_agent_complete(self, agent_id: str, result: Any):
        """Agent完成回调"""
        self.completed.add(agent_id)
        self.results[agent_id] = result


async def demo_hybrid_parallel():
    """演示混合并行执行"""
    orchestrator = HybridOrchestrator()
    
    # 创建智能体
    research1 = ParallelResearchAgent("research_1", orchestrator.bus)
    research2 = ParallelResearchAgent("research_2", orchestrator.bus)
    code = ParallelCodeAgent("code_gen", orchestrator.bus)
    doc = ParallelDocAgent("doc_gen", orchestrator.bus)
    
    # 添加Agent到编排器（定义DAG）
    # 两个研究Agent并行 -> 代码Agent -> 文档Agent
    orchestrator.add_agent(research1)
    orchestrator.add_agent(research2)
    orchestrator.add_agent(code, depends_on=["research_1", "research_2"])
    orchestrator.add_agent(doc, depends_on=["code_gen"])
    
    # 执行任务
    results = await orchestrator.execute({
        "topic": "AI Agent Framework",
        "task_id": "demo_task_001"
    })
    
    print("\n📁 生成的文件:")
    import os
    output_dir = '/tmp/parallel_demo'
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            print(f"   • {f}")


if __name__ == "__main__":
    # 创建输出目录
    import os
    os.makedirs('/tmp/parallel_demo', exist_ok=True)
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🚀 HYBRID PARALLEL ORCHESTRATOR DEMO                                  ║
║                                                                          ║
║   DAG依赖图 + Actor消息模型 = 真正并行化                                 ║
║                                                                          ║
║   架构: Research1 ─┐                                                     ║
║           (并行)   ├─→ Code ─→ Doc                                       ║
║           Research2─┘                                                    ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(demo_hybrid_parallel())
