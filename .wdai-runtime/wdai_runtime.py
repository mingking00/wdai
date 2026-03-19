#!/usr/bin/env python3
"""
wdai Runtime - 独立多Agent运行时系统
不依赖OpenClaw，实现Agent之间直接通信

架构:
- 消息总线 (Message Bus): Agent间通信的核心
- 共享状态 (Shared State): 跨Agent状态同步
- 事件驱动 (Event-Driven): 基于事件的Agent激活
- 分布式锁 (Distributed Lock): 协调资源访问
"""

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import threading
from queue import Queue, Empty

# wdai运行时目录
WDAI_RUNTIME_DIR = Path("/root/.openclaw/workspace/.wdai-runtime")
WDAI_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class AgentMessage:
    """Agent间消息"""
    msg_id: str
    from_agent: str
    to_agent: str  # "*"表示广播
    msg_type: str  # task_request, task_result, state_update, lock_request, event
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    priority: int = 0  # 越高越优先
    
@dataclass  
class AgentState:
    """Agent状态"""
    agent_id: str
    agent_type: str
    status: str  # idle, busy, waiting, error
    current_task: Optional[str] = None
    memory_usage: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=list)
    
class MessageBus:
    """
    消息总线 - Agent间通信的核心
    基于文件系统实现（简单可靠，跨进程）
    """
    def __init__(self, runtime_dir: Path = WDAI_RUNTIME_DIR):
        self.runtime_dir = runtime_dir
        self.inbox_dir = runtime_dir / "inbox"
        self.inbox_dir.mkdir(exist_ok=True)
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self._lock = threading.Lock()
        
    def subscribe(self, agent_id: str, callback: Callable[[AgentMessage], None]):
        """订阅消息"""
        with self._lock:
            if agent_id not in self.subscribers:
                self.subscribers[agent_id] = []
            self.subscribers[agent_id].append(callback)
            
    def unsubscribe(self, agent_id: str, callback: Callable):
        """取消订阅"""
        with self._lock:
            if agent_id in self.subscribers:
                self.subscribers[agent_id] = [c for c in self.subscribers[agent_id] if c != callback]
                
    def send(self, msg: AgentMessage):
        """发送消息"""
        # 写入文件系统（持久化）
        msg_file = self.inbox_dir / f"{msg.to_agent}_{msg.msg_id}.json"
        with open(msg_file, 'w') as f:
            json.dump(asdict(msg), f)
            
        # 内存中直接触发（低延迟）
        if msg.to_agent in self.subscribers:
            for callback in self.subscribers[msg.to_agent]:
                try:
                    callback(msg)
                except Exception as e:
                    print(f"[MessageBus] Callback error: {e}")
                    
    def broadcast(self, from_agent: str, msg_type: str, payload: Dict):
        """广播消息"""
        msg = AgentMessage(
            msg_id=str(uuid.uuid4())[:8],
            from_agent=from_agent,
            to_agent="*",
            msg_type=msg_type,
            payload=payload
        )
        # 写入广播队列
        broadcast_file = self.inbox_dir / f"broadcast_{msg.msg_id}.json"
        with open(broadcast_file, 'w') as f:
            json.dump(asdict(msg), f)
            
    def poll(self, agent_id: str, timeout: float = 0.1) -> Optional[AgentMessage]:
        """轮询消息（文件系统方式）"""
        # 检查个人消息
        pattern = f"{agent_id}_*.json"
        for msg_file in self.inbox_dir.glob(pattern):
            try:
                with open(msg_file, 'r') as f:
                    data = json.load(f)
                msg_file.unlink()  # 删除已读取
                return AgentMessage(**data)
            except Exception as e:
                print(f"[MessageBus] Poll error: {e}")
                
        # 检查广播消息
        for msg_file in self.inbox_dir.glob("broadcast_*.json"):
            try:
                with open(msg_file, 'r') as f:
                    data = json.load(f)
                # 广播消息不删除，由各自Agent记录已读
                return AgentMessage(**data)
            except Exception as e:
                print(f"[MessageBus] Broadcast poll error: {e}")
                
        return None
        
    def start(self):
        """启动消息总线"""
        self.running = True
        print("[MessageBus] Started")
        
    def stop(self):
        """停止消息总线"""
        self.running = False
        print("[MessageBus] Stopped")

class SharedState:
    """
    共享状态 - 跨Agent状态同步
    基于内存+文件系统实现
    """
    def __init__(self, runtime_dir: Path = WDAI_RUNTIME_DIR):
        self.runtime_dir = runtime_dir
        self.state_file = runtime_dir / "shared_state.json"
        self.state: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._load()
        
    def _load(self):
        """从文件加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            except:
                self.state = {}
                
    def _save(self):
        """保存状态到文件"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
            
    def get(self, key: str, default=None) -> Any:
        """获取状态"""
        with self._lock:
            return self.state.get(key, default)
            
    def set(self, key: str, value: Any):
        """设置状态"""
        with self._lock:
            self.state[key] = value
            self._save()
            
    def update(self, updates: Dict[str, Any]):
        """批量更新"""
        with self._lock:
            self.state.update(updates)
            self._save()
            
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """获取Agent状态"""
        with self._lock:
            data = self.state.get(f"agent:{agent_id}")
            if data:
                return AgentState(**data)
            return None
            
    def set_agent_state(self, agent_id: str, state: AgentState):
        """设置Agent状态"""
        with self._lock:
            self.state[f"agent:{agent_id}"] = asdict(state)
            self._save()

class DistributedLock:
    """
    分布式锁 - 协调资源访问
    基于文件锁实现
    """
    def __init__(self, runtime_dir: Path = WDAI_RUNTIME_DIR):
        self.locks_dir = runtime_dir / "locks"
        self.locks_dir.mkdir(exist_ok=True)
        
    def acquire(self, resource: str, agent_id: str, timeout: float = 10.0) -> bool:
        """获取锁"""
        lock_file = self.locks_dir / f"{resource}.lock"
        start = time.time()
        
        while time.time() - start < timeout:
            if not lock_file.exists():
                # 创建锁文件
                lock_data = {
                    "agent_id": agent_id,
                    "acquired_at": time.time()
                }
                with open(lock_file, 'w') as f:
                    json.dump(lock_data, f)
                return True
            # 等待
            time.sleep(0.1)
            
        return False
        
    def release(self, resource: str, agent_id: str) -> bool:
        """释放锁"""
        lock_file = self.locks_dir / f"{resource}.lock"
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    data = json.load(f)
                if data.get("agent_id") == agent_id:
                    lock_file.unlink()
                    return True
            except:
                pass
        return False
        
    def is_locked(self, resource: str) -> bool:
        """检查是否被锁定"""
        lock_file = self.locks_dir / f"{resource}.lock"
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    data = json.load(f)
                # 检查锁是否过期（30秒）
                if time.time() - data.get("acquired_at", 0) > 30:
                    lock_file.unlink()
                    return False
                return True
            except:
                pass
        return False

class wdaiRuntime:
    """
    wdai运行时 - 独立多Agent运行时系统
    """
    def __init__(self):
        self.runtime_dir = WDAI_RUNTIME_DIR
        self.message_bus = MessageBus(self.runtime_dir)
        self.shared_state = SharedState(self.runtime_dir)
        self.distributed_lock = DistributedLock(self.runtime_dir)
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.running = False
        self._main_loop_task = None
        
    def register_agent(self, agent: 'BaseAgent'):
        """注册Agent"""
        self.agents[agent.agent_id] = agent
        agent.runtime = self
        # 订阅消息
        self.message_bus.subscribe(agent.agent_id, agent._on_message)
        print(f"[wdaiRuntime] Registered agent: {agent.agent_id} ({agent.agent_type})")
        
    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            self.message_bus.unsubscribe(agent_id, agent._on_message)
            del self.agents[agent_id]
            print(f"[wdaiRuntime] Unregistered agent: {agent_id}")
            
    def start(self):
        """启动运行时"""
        self.running = True
        self.message_bus.start()
        
        # 启动所有Agent
        for agent in self.agents.values():
            agent.start()
            
        print(f"[wdaiRuntime] Started with {len(self.agents)} agents")
        
    def stop(self):
        """停止运行时"""
        self.running = False
        
        # 停止所有Agent
        for agent in self.agents.values():
            agent.stop()
            
        self.message_bus.stop()
        print("[wdaiRuntime] Stopped")
        
    def send_task(self, from_agent: str, to_agent: str, task_type: str, description: str, payload: Dict = None):
        """发送任务"""
        msg = AgentMessage(
            msg_id=str(uuid.uuid4())[:8],
            from_agent=from_agent,
            to_agent=to_agent,
            msg_type="task_request",
            payload={
                "task_type": task_type,
                "description": description,
                "data": payload or {}
            }
        )
        self.message_bus.send(msg)
        
    def broadcast_event(self, from_agent: str, event_type: str, data: Dict):
        """广播事件"""
        self.message_bus.broadcast(from_agent, "event", {
            "event_type": event_type,
            "data": data
        })

class BaseAgent:
    """
    基础Agent类
    所有Agent继承此类
    """
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.runtime: Optional[wdaiRuntime] = None
        self.state = AgentState(
            agent_id=agent_id,
            agent_type=agent_type,
            status="idle"
        )
        self._running = False
        self._message_queue: Queue = Queue()
        self._thread: Optional[threading.Thread] = None
        
    def start(self):
        """启动Agent"""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop)
        self._thread.start()
        self.state.status = "idle"
        self._update_state()
        print(f"[Agent:{self.agent_id}] Started")
        
    def stop(self):
        """停止Agent"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        self.state.status = "stopped"
        self._update_state()
        print(f"[Agent:{self.agent_id}] Stopped")
        
    def _run_loop(self):
        """主循环"""
        while self._running:
            try:
                # 处理消息
                msg = self._message_queue.get(timeout=0.1)
                self._handle_message(msg)
            except Empty:
                # 执行Agent特定的逻辑
                self._tick()
                
    def _tick(self):
        """每个tick执行的操作（子类重写）"""
        time.sleep(0.1)
        
    def _on_message(self, msg: AgentMessage):
        """收到消息（由MessageBus调用）"""
        self._message_queue.put(msg)
        
    def _handle_message(self, msg: AgentMessage):
        """处理消息（子类重写）"""
        print(f"[Agent:{self.agent_id}] Received {msg.msg_type} from {msg.from_agent}")
        
    def _update_state(self):
        """更新状态到共享存储"""
        if self.runtime:
            self.runtime.shared_state.set_agent_state(self.agent_id, self.state)
            
    def send_message(self, to_agent: str, msg_type: str, payload: Dict):
        """发送消息"""
        if self.runtime:
            msg = AgentMessage(
                msg_id=str(uuid.uuid4())[:8],
                from_agent=self.agent_id,
                to_agent=to_agent,
                msg_type=msg_type,
                payload=payload
            )
            self.runtime.message_bus.send(msg)
            
    def acquire_lock(self, resource: str, timeout: float = 10.0) -> bool:
        """获取资源锁"""
        if self.runtime:
            return self.runtime.distributed_lock.acquire(resource, self.agent_id, timeout)
        return False
        
    def release_lock(self, resource: str) -> bool:
        """释放资源锁"""
        if self.runtime:
            return self.runtime.distributed_lock.release(resource, self.agent_id)
        return False
        
    def get_shared(self, key: str, default=None):
        """获取共享状态"""
        if self.runtime:
            return self.runtime.shared_state.get(key, default)
        return default
        
    def set_shared(self, key: str, value: Any):
        """设置共享状态"""
        if self.runtime:
            self.runtime.shared_state.set(key, value)

# 导出
__all__ = [
    'wdaiRuntime', 'BaseAgent', 'AgentMessage', 'AgentState',
    'MessageBus', 'SharedState', 'DistributedLock'
]

if __name__ == "__main__":
    print("=== wdai Runtime System ===")
    print(f"Runtime directory: {WDAI_RUNTIME_DIR}")
    print("Components:")
    print("  - MessageBus: Agent间通信")
    print("  - SharedState: 跨Agent状态")
    print("  - DistributedLock: 资源协调")
    print()
    print("Usage:")
    print("  from wdai_runtime import wdaiRuntime, BaseAgent")
    print("  runtime = wdaiRuntime()")
    print("  runtime.register_agent(MyAgent('agent1', 'coder'))")
    print("  runtime.start()")
