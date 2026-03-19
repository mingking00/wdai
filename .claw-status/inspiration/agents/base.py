#!/usr/bin/env python3
"""
Agent Base Classes - 双代理架构基础

Phase 1 Implementation

提供:
1. BaseAgent - 所有代理的基类
2. MessageBus - 代理间消息总线
3. Task - 任务定义
4. AgentCoordinator - 代理协调器

Author: wdai
Date: 2026-03-19
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import queue
import threading
import time
from uuid import uuid4


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(Enum):
    """消息类型"""
    TASK_ASSIGN = "task_assign"          # 分配任务
    TASK_COMPLETE = "task_complete"      # 任务完成
    TASK_FAILED = "task_failed"          # 任务失败
    STATUS_UPDATE = "status_update"      # 状态更新
    RESOURCE_REQUEST = "resource_request" # 资源请求
    STRATEGY_UPDATE = "strategy_update"  # 策略更新


@dataclass
class Task:
    """任务定义"""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    type: str = ""                          # 任务类型: fetch, analyze, generate
    priority: int = 5                       # 1-10, 数字越小优先级越高
    status: TaskStatus = TaskStatus.PENDING
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    assigned_to: Optional[str] = None       # 分配给哪个代理
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type,
            'priority': self.priority,
            'status': self.status.value,
            'payload': self.payload,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'assigned_to': self.assigned_to
        }


@dataclass
class Message:
    """消息定义"""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    type: MessageType = MessageType.STATUS_UPDATE
    sender: str = ""                        # 发送者代理ID
    receiver: str = ""                      # 接收者代理ID (空表示广播)
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'sender': self.sender,
            'receiver': self.receiver,
            'payload': self.payload,
            'timestamp': self.timestamp
        }


class MessageBus:
    """
    代理间消息总线
    
    提供异步消息传递能力
    """
    
    def __init__(self):
        self._queues: Dict[str, queue.Queue] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self._running = False
        self._dispatcher_thread: Optional[threading.Thread] = None
    
    def register_agent(self, agent_id: str):
        """注册代理到总线"""
        with self._lock:
            if agent_id not in self._queues:
                self._queues[agent_id] = queue.Queue()
                self._subscribers[agent_id] = []
                print(f"[MessageBus] 代理 {agent_id} 已注册")
    
    def unregister_agent(self, agent_id: str):
        """注销代理"""
        with self._lock:
            if agent_id in self._queues:
                del self._queues[agent_id]
                del self._subscribers[agent_id]
                print(f"[MessageBus] 代理 {agent_id} 已注销")
    
    def subscribe(self, agent_id: str, callback: Callable[[Message], None]):
        """订阅消息"""
        with self._lock:
            if agent_id in self._subscribers:
                self._subscribers[agent_id].append(callback)
    
    def send(self, message: Message) -> bool:
        """
        发送消息
        
        如果指定了receiver，发送到特定代理
        否则广播给所有代理
        """
        try:
            if message.receiver:
                # 单播
                if message.receiver in self._queues:
                    self._queues[message.receiver].put(message)
                    return True
                else:
                    print(f"[MessageBus] 警告: 接收者 {message.receiver} 不存在")
                    return False
            else:
                # 广播
                with self._lock:
                    for agent_id, q in self._queues.items():
                        if agent_id != message.sender:  # 不发送给自己
                            q.put(message)
                return True
        except Exception as e:
            print(f"[MessageBus] 发送消息失败: {e}")
            return False
    
    def receive(self, agent_id: str, timeout: float = 1.0) -> Optional[Message]:
        """接收消息"""
        if agent_id not in self._queues:
            return None
        
        try:
            return self._queues[agent_id].get(timeout=timeout)
        except queue.Empty:
            return None
    
    def start(self):
        """启动消息分发器"""
        self._running = True
        self._dispatcher_thread = threading.Thread(target=self._dispatch_loop)
        self._dispatcher_thread.daemon = True
        self._dispatcher_thread.start()
        print("[MessageBus] 消息总线已启动")
    
    def stop(self):
        """停止消息分发器"""
        self._running = False
        if self._dispatcher_thread:
            self._dispatcher_thread.join(timeout=2.0)
        print("[MessageBus] 消息总线已停止")
    
    def _dispatch_loop(self):
        """消息分发循环"""
        while self._running:
            try:
                with self._lock:
                    agents = list(self._queues.keys())
                
                for agent_id in agents:
                    try:
                        message = self._queues[agent_id].get_nowait()
                        # 调用订阅者回调
                        with self._lock:
                            callbacks = self._subscribers.get(agent_id, [])
                        for callback in callbacks:
                            try:
                                callback(message)
                            except Exception as e:
                                print(f"[MessageBus] 回调执行失败: {e}")
                    except queue.Empty:
                        continue
                
                time.sleep(0.1)
            except Exception as e:
                print(f"[MessageBus] 分发循环错误: {e}")
                time.sleep(1.0)


class BaseAgent(ABC):
    """
    代理基类
    
    所有具体代理必须继承此类
    """
    
    def __init__(self, agent_id: str, message_bus: MessageBus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._current_task: Optional[Task] = None
        self._task_history: List[Task] = []
        
        # 注册到消息总线
        self.message_bus.register_agent(agent_id)
        self.message_bus.subscribe(agent_id, self._on_message)
    
    @abstractmethod
    def process_task(self, task: Task) -> Dict[str, Any]:
        """
        处理任务 - 子类必须实现
        
        Args:
            task: 要处理的任务
            
        Returns:
            任务结果字典
        """
        pass
    
    def _on_message(self, message: Message):
        """消息处理回调"""
        print(f"[{self.agent_id}] 收到消息: {message.type.value} from {message.sender}")
        
        if message.type == MessageType.TASK_ASSIGN:
            # 收到任务分配
            task_data = message.payload.get('task')
            if task_data:
                task = Task(**task_data)
                self._accept_task(task)
        
        elif message.type == MessageType.STRATEGY_UPDATE:
            # 收到策略更新
            self._on_strategy_update(message.payload)
    
    def _accept_task(self, task: Task):
        """接受任务"""
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = self.agent_id
        # 优先级队列: (priority, timestamp, task)
        self._task_queue.put((task.priority, time.time(), task))
        print(f"[{self.agent_id}] 接受任务: {task.id} (优先级: {task.priority})")
    
    def _on_strategy_update(self, payload: Dict):
        """策略更新 - 子类可覆盖"""
        pass
    
    def start(self):
        """启动代理"""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop)
        self._thread.daemon = True
        self._thread.start()
        print(f"[{self.agent_id}] 代理已启动")
    
    def stop(self):
        """停止代理"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        self.message_bus.unregister_agent(self.agent_id)
        print(f"[{self.agent_id}] 代理已停止")
    
    def _run_loop(self):
        """代理主循环"""
        while self._running:
            try:
                # 检查是否有新消息
                message = self.message_bus.receive(self.agent_id, timeout=0.5)
                if message:
                    self._on_message(message)
                
                # 处理任务队列
                if not self._task_queue.empty() and not self._current_task:
                    _, _, task = self._task_queue.get()
                    self._execute_task(task)
                
                time.sleep(0.1)
            except Exception as e:
                print(f"[{self.agent_id}] 运行循环错误: {e}")
                time.sleep(1.0)
    
    def _execute_task(self, task: Task):
        """执行任务"""
        self._current_task = task
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        
        print(f"[{self.agent_id}] 开始执行任务: {task.id}")
        
        try:
            result = self.process_task(task)
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            print(f"[{self.agent_id}] 任务完成: {task.id}")
            
            # 发送完成消息
            self._send_task_complete(task)
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            print(f"[{self.agent_id}] 任务失败: {task.id}, 错误: {e}")
            
            # 发送失败消息
            self._send_task_failed(task)
        
        finally:
            self._task_history.append(task)
            self._current_task = None
    
    def _send_task_complete(self, task: Task):
        """发送任务完成消息"""
        message = Message(
            type=MessageType.TASK_COMPLETE,
            sender=self.agent_id,
            payload={'task': task.to_dict()}
        )
        self.message_bus.send(message)
    
    def _send_task_failed(self, task: Task):
        """发送任务失败消息"""
        message = Message(
            type=MessageType.TASK_FAILED,
            sender=self.agent_id,
            payload={'task': task.to_dict()}
        )
        self.message_bus.send(message)
    
    def get_status(self) -> Dict[str, Any]:
        """获取代理状态"""
        return {
            'agent_id': self.agent_id,
            'running': self._running,
            'current_task': self._current_task.to_dict() if self._current_task else None,
            'queue_size': self._task_queue.qsize(),
            'completed_tasks': len([t for t in self._task_history if t.status == TaskStatus.COMPLETED]),
            'failed_tasks': len([t for t in self._task_history if t.status == TaskStatus.FAILED])
        }


class AgentCoordinator:
    """
    代理协调器
    
    管理多个代理的生命周期和协作
    """
    
    def __init__(self):
        self.message_bus = MessageBus()
        self.agents: Dict[str, BaseAgent] = {}
        self._lock = threading.Lock()
    
    def register_agent(self, agent: BaseAgent):
        """注册代理"""
        with self._lock:
            self.agents[agent.agent_id] = agent
            print(f"[Coordinator] 代理 {agent.agent_id} 已注册")
    
    def unregister_agent(self, agent_id: str):
        """注销代理"""
        with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                print(f"[Coordinator] 代理 {agent_id} 已注销")
    
    def start_all(self):
        """启动所有代理"""
        self.message_bus.start()
        with self._lock:
            for agent in self.agents.values():
                agent.start()
        print("[Coordinator] 所有代理已启动")
    
    def stop_all(self):
        """停止所有代理"""
        with self._lock:
            for agent in self.agents.values():
                agent.stop()
        self.message_bus.stop()
        print("[Coordinator] 所有代理已停止")
    
    def get_all_status(self) -> Dict[str, Any]:
        """获取所有代理状态"""
        with self._lock:
            return {
                agent_id: agent.get_status()
                for agent_id, agent in self.agents.items()
            }
    
    def assign_task(self, task: Task, agent_id: str) -> bool:
        """分配任务给指定代理"""
        if agent_id not in self.agents:
            print(f"[Coordinator] 错误: 代理 {agent_id} 不存在")
            return False
        
        message = Message(
            type=MessageType.TASK_ASSIGN,
            sender='coordinator',
            receiver=agent_id,
            payload={'task': task.to_dict()}
        )
        return self.message_bus.send(message)


def test_base_classes():
    """测试基类功能"""
    print("="*60)
    print("测试 Agent 基类")
    print("="*60)
    
    # 创建协调器
    coordinator = AgentCoordinator()
    
    # 创建测试代理
    class TestAgent(BaseAgent):
        def process_task(self, task: Task) -> Dict[str, Any]:
            print(f"[TestAgent] 处理任务: {task.id}, 类型: {task.type}")
            time.sleep(0.5)  # 模拟工作
            return {'status': 'success', 'data': f'处理结果: {task.payload}'}
    
    # 注册代理
    agent1 = TestAgent('test_agent_1', coordinator.message_bus)
    coordinator.register_agent(agent1)
    
    # 启动
    coordinator.start_all()
    
    # 分配任务
    task1 = Task(type='fetch', priority=1, payload={'url': 'https://arxiv.org'})
    coordinator.assign_task(task1, 'test_agent_1')
    
    task2 = Task(type='analyze', priority=2, payload={'paper_id': '123'})
    coordinator.assign_task(task2, 'test_agent_1')
    
    # 等待任务完成
    time.sleep(2.0)
    
    # 查看状态
    print("\n代理状态:")
    print(json.dumps(coordinator.get_all_status(), indent=2))
    
    # 停止
    coordinator.stop_all()
    
    print("\n✅ 基类测试完成")


if __name__ == '__main__':
    test_base_classes()
