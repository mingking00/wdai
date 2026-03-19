#!/usr/bin/env python3
"""
Distributed Parallel Orchestrator - Phase 3
分布式并行编排器 - 第三阶段：多进程/多节点执行

支持三种模式：
1. 多进程模式 - 单机多核并行
2. Ray分布式 - 多机集群
3. 网络通信 - 跨机器通信
"""

import asyncio
import multiprocessing as mp
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time
import json
import pickle
import socket
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed

# 尝试导入Ray
try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False


class ExecutionMode(Enum):
    """执行模式"""
    LOCAL = "local"           # 本地asyncio
    MULTIPROCESS = "multiprocess"  # 多进程
    RAY = "ray"               # Ray分布式
    NETWORK = "network"       # 网络分布式


@dataclass
class DistributedTaskConfig:
    """分布式任务配置"""
    task_id: str
    agent_type: str
    depends_on: set = field(default_factory=set)
    duration: float = 1.0
    timeout: float = 5.0
    max_retries: int = 2
    retry_delay: float = 1.0
    # 分布式特定
    preferred_node: Optional[str] = None  # 偏好的执行节点
    resource_requirements: Dict = field(default_factory=dict)  # 资源需求


# ==================== 多进程执行器 ====================

class MultiprocessExecutor:
    """多进程执行器 - 利用多核CPU"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or mp.cpu_count()
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        print(f"🖥️  多进程执行器初始化: {self.max_workers} 个worker")
    
    async def execute_task(self, task_config: Dict) -> Dict:
        """在进程中执行任务"""
        loop = asyncio.get_event_loop()
        
        # 提交到进程池
        future = loop.run_in_executor(
            self.executor,
            self._worker_function,
            task_config
        )
        
        return await future
    
    @staticmethod
    def _worker_function(task_config: Dict) -> Dict:
        """工作进程函数（必须是静态方法）"""
        import time
        import random
        import os
        
        task_id = task_config['task_id']
        duration = task_config.get('duration', 1.0)
        max_retries = task_config.get('max_retries', 2)
        
        start_time = time.time()
        attempts = 0
        
        # 重试逻辑
        while attempts <= max_retries:
            attempts += 1
            try:
                # 模拟工作
                actual_duration = duration * random.uniform(0.5, 1.5)
                time.sleep(actual_duration)
                
                # 模拟随机失败
                if random.random() < 0.1:  # 10%失败率
                    raise Exception(f"随机失败: {task_id}")
                
                return {
                    'task_id': task_id,
                    'status': 'success',
                    'duration': time.time() - start_time,
                    'attempts': attempts,
                    'pid': os.getpid(),  # 进程ID
                    'output': {
                        'processed_at': datetime.now().isoformat(),
                        'worker_pid': os.getpid()
                    }
                }
                
            except Exception as e:
                if attempts > max_retries:
                    return {
                        'task_id': task_id,
                        'status': 'failed',
                        'duration': time.time() - start_time,
                        'attempts': attempts,
                        'pid': os.getpid(),
                        'error': str(e)
                    }
                time.sleep(task_config.get('retry_delay', 1.0))
    
    def shutdown(self):
        """关闭执行器"""
        self.executor.shutdown(wait=True)


# ==================== Ray分布式执行器 ====================

if RAY_AVAILABLE:
    @ray.remote
    class RayAgent:
        """Ray分布式智能体"""
        
        def __init__(self, agent_id: str, agent_type: str):
            self.agent_id = agent_id
            self.agent_type = agent_type
            self.pid = None
        
        def execute(self, task_config: Dict) -> Dict:
            """执行任务"""
            import time
            import random
            import os
            
            self.pid = os.getpid()
            task_id = task_config['task_id']
            duration = task_config.get('duration', 1.0)
            
            start_time = time.time()
            
            # 模拟工作
            actual_duration = duration * random.uniform(0.5, 1.5)
            time.sleep(actual_duration)
            
            return {
                'task_id': task_id,
                'status': 'success',
                'duration': time.time() - start_time,
                'ray_pid': self.pid,
                'output': {
                    'processed_at': datetime.now().isoformat(),
                    'node_id': ray.get_runtime_context().get_node_id()
                }
            }
    
    class RayExecutor:
        """Ray分布式执行器"""
        
        def __init__(self):
            if not ray.is_initialized():
                ray.init(ignore_reinit_error=True)
            print("☁️  Ray分布式执行器初始化完成")
        
        async def execute_task(self, task_config: Dict) -> Dict:
            """在Ray集群上执行任务"""
            agent = RayAgent.remote(
                task_config['task_id'],
                task_config['agent_type']
            )
            
            # 异步执行
            result_ref = agent.execute.remote(task_config)
            result = ray.get(result_ref)
            
            return result
        
        def shutdown(self):
            """关闭Ray"""
            ray.shutdown()


# ==================== 网络分布式执行器 ====================

class NetworkExecutor:
    """
    网络分布式执行器
    
    架构：
    - Master节点：协调任务分配
    - Worker节点：执行具体任务
    - 通信：TCP socket + JSON
    """
    
    def __init__(self, mode: str = "master", host: str = "localhost", port: int = 8765):
        self.mode = mode
        self.host = host
        self.port = port
        self.workers: List[Dict] = []  # 连接的worker
        self.server_socket = None
        self.running = False
        
        if mode == "master":
            print(f"🌐 Master节点: {host}:{port}")
        else:
            print(f"🔧 Worker节点，连接Master: {host}:{port}")
    
    def start_master(self):
        """启动Master节点"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"   Master监听中...")
        
        # 启动接受连接的线程
        accept_thread = threading.Thread(target=self._accept_workers)
        accept_thread.daemon = True
        accept_thread.start()
    
    def _accept_workers(self):
        """接受Worker连接"""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                print(f"   Worker连接: {addr}")
                
                worker = {
                    'conn': conn,
                    'addr': addr,
                    'busy': False
                }
                self.workers.append(worker)
                
                # 启动处理线程
                handler = threading.Thread(
                    target=self._handle_worker,
                    args=(worker,)
                )
                handler.daemon = True
                handler.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"   接受连接错误: {e}")
    
    def _handle_worker(self, worker: Dict):
        """处理Worker通信"""
        conn = worker['conn']
        
        while self.running:
            try:
                # 接收数据
                data = conn.recv(4096)
                if not data:
                    break
                
                message = json.loads(data.decode())
                
                if message.get('type') == 'result':
                    print(f"   收到结果: {message.get('task_id')}")
                    worker['busy'] = False
                
            except Exception as e:
                print(f"   Worker处理错误: {e}")
                break
        
        # 清理
        conn.close()
        self.workers.remove(worker)
    
    async def execute_task(self, task_config: Dict) -> Dict:
        """在Worker上执行任务"""
        # 找到空闲的worker
        worker = self._find_idle_worker()
        
        if not worker:
            return {
                'task_id': task_config['task_id'],
                'status': 'failed',
                'error': 'No available worker'
            }
        
        worker['busy'] = True
        
        # 发送任务
        message = {
            'type': 'task',
            'config': task_config
        }
        
        worker['conn'].send(json.dumps(message).encode())
        
        # 等待结果（简化版，实际应该用异步）
        return {
            'task_id': task_config['task_id'],
            'status': 'dispatched',
            'worker': str(worker['addr'])
        }
    
    def _find_idle_worker(self) -> Optional[Dict]:
        """找到空闲的worker"""
        for worker in self.workers:
            if not worker['busy']:
                return worker
        return None
    
    def shutdown(self):
        """关闭"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


# ==================== 分布式编排器 ====================

class DistributedOrchestrator:
    """分布式编排器 - 支持多种执行模式"""
    
    def __init__(self, mode: ExecutionMode = ExecutionMode.MULTIPROCESS):
        self.mode = mode
        self.executor = None
        self._init_executor()
        
        self.tasks: Dict[str, DistributedTaskConfig] = {}
        self.results: Dict[str, Dict] = {}
        self.completed: set = set()
    
    def _init_executor(self):
        """初始化执行器"""
        if self.mode == ExecutionMode.MULTIPROCESS:
            self.executor = MultiprocessExecutor()
        elif self.mode == ExecutionMode.RAY and RAY_AVAILABLE:
            self.executor = RayExecutor()
        elif self.mode == ExecutionMode.NETWORK:
            self.executor = NetworkExecutor(mode="master")
            self.executor.start_master()
        else:
            # 回退到本地
            print("⚠️  回退到本地执行模式")
            self.mode = ExecutionMode.LOCAL
    
    def add_task(self, config: DistributedTaskConfig):
        """添加任务"""
        self.tasks[config.task_id] = config
    
    def get_ready_tasks(self) -> set:
        """获取就绪任务"""
        ready = set()
        for task_id, config in self.tasks.items():
            if task_id not in self.completed:
                if config.depends_on.issubset(self.completed):
                    ready.add(task_id)
        return ready
    
    async def run(self) -> Dict[str, Dict]:
        """主执行循环"""
        print("\n" + "="*70)
        print(f"🚀 DISTRIBUTED ORCHESTRATOR - {self.mode.value.upper()}")
        print("="*70)
        
        print(f"\n📋 任务配置:")
        for tid, config in self.tasks.items():
            node_info = f" [节点: {config.preferred_node}]" if config.preferred_node else ""
            print(f"   • {tid}: {config.agent_type}{node_info}")
        
        start_time = time.time()
        completed = set()
        running_tasks: Dict[str, asyncio.Task] = {}
        
        print(f"\n⏳ 开始分布式执行...\n")
        
        while len(completed) < len(self.tasks):
            ready = self.get_ready_tasks() - completed
            
            if ready and len(running_tasks) < mp.cpu_count():
                for task_id in ready:
                    if task_id not in running_tasks:
                        config = self.tasks[task_id]
                        
                        # 提交任务
                        task = asyncio.create_task(
                            self._execute_single(config),
                            name=task_id
                        )
                        running_tasks[task_id] = task
                        completed.add(task_id)
                
                await asyncio.sleep(0.05)
            else:
                # 检查完成的任务
                done_tasks = [
                    tid for tid, task in running_tasks.items()
                    if task.done()
                ]
                
                for tid in done_tasks:
                    try:
                        result = running_tasks[tid].result()
                        self.results[tid] = result
                        
                        status = result.get('status', 'unknown')
                        pid = result.get('pid', result.get('ray_pid', 'N/A'))
                        duration = result.get('duration', 0)
                        
                        icon = "✅" if status == "success" else "❌"
                        mode_icon = "🖥️" if 'pid' in result else "☁️" if 'ray_pid' in result else "⚙️"
                        
                        print(f"   {icon} {tid} {mode_icon} PID:{pid} ({duration:.2f}s)")
                        
                    except Exception as e:
                        print(f"   ❌ {tid} 执行异常: {e}")
                        self.results[tid] = {'status': 'error', 'error': str(e)}
                    
                    del running_tasks[tid]
                
                if not done_tasks:
                    await asyncio.sleep(0.1)
        
        # 等待剩余任务
        if running_tasks:
            await asyncio.gather(*running_tasks.values(), return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        # 报告
        print("\n" + "="*70)
        print("📊 执行报告")
        print("="*70)
        print(f"   ⏱️  总耗时: {elapsed:.2f}s")
        print(f"   ✅ 成功: {sum(1 for r in self.results.values() if r.get('status') == 'success')}/{len(self.tasks)}")
        print(f"   🖥️  执行模式: {self.mode.value}")
        
        if self.mode == ExecutionMode.MULTIPROCESS:
            pids = set(r.get('pid') for r in self.results.values() if 'pid' in r)
            print(f"   🔄 使用进程数: {len(pids)}")
        
        return self.results
    
    async def _execute_single(self, config: DistributedTaskConfig) -> Dict:
        """执行单个任务"""
        task_dict = {
            'task_id': config.task_id,
            'agent_type': config.agent_type,
            'duration': config.duration,
            'timeout': config.timeout,
            'max_retries': config.max_retries,
            'retry_delay': config.retry_delay
        }
        
        if self.executor:
            return await self.executor.execute_task(task_dict)
        else:
            # 本地执行
            import time
            time.sleep(config.duration)
            return {
                'task_id': config.task_id,
                'status': 'success',
                'duration': config.duration
            }
    
    def shutdown(self):
        """关闭"""
        if self.executor:
            self.executor.shutdown()


async def demo_multiprocess():
    """演示多进程执行"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🖥️  MULTIPROCESS PARALLEL EXECUTION                                   ║
║                                                                          ║
║   使用多进程充分利用多核CPU                                             ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    orchestrator = DistributedOrchestrator(ExecutionMode.MULTIPROCESS)
    
    # 添加任务
    orchestrator.add_task(DistributedTaskConfig("data_fetch_1", "DataFetcher", duration=0.5))
    orchestrator.add_task(DistributedTaskConfig("data_fetch_2", "DataFetcher", duration=0.6))
    orchestrator.add_task(DistributedTaskConfig("data_process", "Processor", depends_on={"data_fetch_1", "data_fetch_2"}, duration=0.7))
    orchestrator.add_task(DistributedTaskConfig("analysis_1", "Analyzer", depends_on={"data_process"}, duration=0.4))
    orchestrator.add_task(DistributedTaskConfig("analysis_2", "Analyzer", depends_on={"data_process"}, duration=0.5))
    orchestrator.add_task(DistributedTaskConfig("report", "Reporter", depends_on={"analysis_1", "analysis_2"}, duration=0.3))
    
    await orchestrator.run()
    orchestrator.shutdown()


async def demo_ray():
    """演示Ray分布式执行"""
    if not RAY_AVAILABLE:
        print("\n⚠️  Ray未安装，跳过Ray演示")
        print("   安装: pip install ray")
        return
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ☁️  RAY DISTRIBUTED EXECUTION                                         ║
║                                                                          ║
║   使用Ray框架实现多机分布式执行                                          ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    orchestrator = DistributedOrchestrator(ExecutionMode.RAY)
    
    orchestrator.add_task(DistributedTaskConfig("task_1", "Worker", duration=0.3))
    orchestrator.add_task(DistributedTaskConfig("task_2", "Worker", duration=0.4))
    orchestrator.add_task(DistributedTaskConfig("task_3", "Worker", depends_on={"task_1"}, duration=0.5))
    
    await orchestrator.run()
    orchestrator.shutdown()


def demo_network_architecture():
    """演示网络分布式架构"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🌐 NETWORK DISTRIBUTED ARCHITECTURE                                   ║
║                                                                          ║
║   多机分布式架构设计                                                     ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

架构设计:
┌─────────────────────────────────────────────────────────────┐
│                         Master节点                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ 任务调度器   │  │ 状态管理    │  │ 结果聚合器          │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────┘  │
└─────────┼───────────────────────────────────────────────────┘
          │ TCP/WebSocket
          │
    ┌─────┴─────┬─────────────┬─────────────┐
    │           │             │             │
┌───▼───┐  ┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│Worker1│  │Worker2│    │Worker3│    │Worker4│
│(GPU)  │  │(CPU)  │    │(CPU)  │    │(GPU)  │
└───────┘  └───────┘    └───────┘    └───────┘

通信协议:
  Master -> Worker: 分配任务 (Task Assignment)
  Worker -> Master: 汇报状态 (Status Update)
  Worker -> Master: 返回结果 (Result Return)
  Master -> Worker: 心跳检测 (Health Check)

特性:
  ✅ 动态扩容 - Worker可随时加入/退出
  ✅ 容错机制 - Worker故障自动重分配
  ✅ 负载均衡 - 根据Worker负载分配任务
  ✅ 资源感知 - GPU/CPU任务分配优化

启动方式:
  # Master节点
  python3 -c "from distributed_orchestrator import *; start_master()"
  
  # Worker节点
  python3 -c "from distributed_orchestrator import *; start_worker('master_ip:port')"
""")


if __name__ == "__main__":
    # 演示1：多进程
    asyncio.run(demo_multiprocess())
    
    # 演示2：Ray（如果可用）
    asyncio.run(demo_ray())
    
    # 演示3：网络架构
    demo_network_architecture()
    
    print("\n" + "="*70)
    print("✅ 分布式执行完成！")
    print("="*70)
    print("\n支持的模式:")
    print("   🖥️  Multiprocess - 单机多核 (已演示)")
    print("   ☁️  Ray - 多机集群 (需安装ray)")
    print("   🌐  Network - 网络分布式 (架构设计)")
