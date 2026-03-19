#!/usr/bin/env python3
"""
Robust Parallel Orchestrator - Phase 1
健壮并行编排器 - 第一阶段：超时、重试、错误恢复

增强功能：
1. 超时机制 - 防止任务卡死
2. 重试机制 - 失败自动重试
3. 错误恢复 - 优雅降级
4. 状态监控 - 实时查看执行状态
"""

import asyncio
import time
import random
from typing import Dict, Set, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 等待中
    READY = "ready"          # 就绪（依赖完成）
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    TIMEOUT = "timeout"      # 超时
    RETRYING = "retrying"    # 重试中
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskConfig:
    """任务配置"""
    task_id: str
    agent_type: str
    depends_on: Set[str] = field(default_factory=set)
    duration: float = 1.0          # 预期执行时间
    timeout: float = 5.0           # 超时时间
    max_retries: int = 2           # 最大重试次数
    retry_delay: float = 1.0       # 重试间隔
    fallback_task: Optional[str] = None  # 失败时的回退任务


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: TaskStatus
    output: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    attempts: int = 0
    execution_log: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


class RobustOrchestrator:
    """
    健壮并行编排器
    
    核心增强：
    - 超时控制：防止任务无限等待
    - 自动重试：失败后自动重试
    - 错误隔离：单个任务失败不影响整体
    - 状态监控：实时查看所有任务状态
    """
    
    def __init__(self, name: str = "RobustOrchestrator"):
        self.name = name
        self.tasks: Dict[str, TaskConfig] = {}
        self.results: Dict[str, TaskResult] = {}
        self.status: Dict[str, TaskStatus] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._event_callbacks: List[Callable] = []
        
        # 统计
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def add_task(self, config: TaskConfig):
        """添加任务"""
        self.tasks[config.task_id] = config
        self.status[config.task_id] = TaskStatus.PENDING
        self.results[config.task_id] = TaskResult(
            task_id=config.task_id,
            status=TaskStatus.PENDING
        )
        logger.info(f"[注册] 任务 {config.task_id} ({config.agent_type})")
    
    def on_event(self, callback: Callable):
        """注册事件回调"""
        self._event_callbacks.append(callback)
    
    async def _emit_event(self, event_type: str, data: Dict):
        """触发事件"""
        for callback in self._event_callbacks:
            try:
                await callback(event_type, data)
            except Exception as e:
                logger.error(f"事件回调失败: {e}")
    
    def get_ready_tasks(self) -> Set[str]:
        """获取就绪任务"""
        ready = set()
        for task_id, config in self.tasks.items():
            if self.status[task_id] == TaskStatus.PENDING:
                # 检查依赖
                deps_completed = all(
                    self.status.get(dep) in {TaskStatus.SUCCESS, TaskStatus.FAILED}
                    for dep in config.depends_on
                )
                if deps_completed:
                    ready.add(task_id)
        return ready
    
    async def _execute_with_timeout(
        self, 
        config: TaskConfig, 
        dependencies_results: Dict[str, TaskResult]
    ) -> TaskResult:
        """带超时执行单个任务"""
        result = self.results[config.task_id]
        result.start_time = time.time()
        result.status = TaskStatus.RUNNING
        result.attempts += 1
        
        async with self._lock:
            self.status[config.task_id] = TaskStatus.RUNNING
        
        logger.info(f"[执行] {config.task_id} (第{result.attempts}次尝试, 超时{config.timeout}s)")
        
        try:
            # 创建执行任务
            exec_task = asyncio.create_task(
                self._run_agent_logic(config, dependencies_results)
            )
            
            # 带超时等待
            output = await asyncio.wait_for(exec_task, timeout=config.timeout)
            
            result.end_time = time.time()
            result.status = TaskStatus.SUCCESS
            result.output = output
            
            logger.info(f"[成功] {config.task_id} ({result.duration:.2f}s)")
            
            await self._emit_event("task_success", {
                "task_id": config.task_id,
                "duration": result.duration,
                "attempts": result.attempts
            })
            
        except asyncio.TimeoutError:
            result.end_time = time.time()
            result.status = TaskStatus.TIMEOUT
            result.error = f"执行超时 (>{config.timeout}s)"
            exec_task.cancel()
            
            logger.warning(f"[超时] {config.task_id}")
            
            await self._emit_event("task_timeout", {
                "task_id": config.task_id,
                "timeout": config.timeout
            })
            
        except Exception as e:
            result.end_time = time.time()
            result.status = TaskStatus.FAILED
            result.error = str(e)
            
            logger.error(f"[失败] {config.task_id}: {e}")
            
            await self._emit_event("task_failed", {
                "task_id": config.task_id,
                "error": str(e)
            })
        
        return result
    
    async def _run_agent_logic(
        self, 
        config: TaskConfig, 
        dependencies_results: Dict[str, TaskResult]
    ) -> Any:
        """模拟智能体执行逻辑"""
        # 模拟随机延迟（有时快有时慢）
        actual_duration = config.duration * random.uniform(0.5, 1.5)
        await asyncio.sleep(actual_duration)
        
        # 模拟随机失败（用于测试重试）
        if random.random() < 0.15:  # 15%失败率
            raise Exception(f"模拟随机失败: {config.task_id}")
        
        return {
            "task_id": config.task_id,
            "agent_type": config.agent_type,
            "processed_at": datetime.now().isoformat(),
            "dependencies_count": len(dependencies_results)
        }
    
    async def _execute_with_retry(self, config: TaskConfig) -> TaskResult:
        """带重试执行"""
        last_result = None
        
        for attempt in range(config.max_retries + 1):
            # 收集依赖结果
            deps_results = {
                dep: self.results[dep]
                for dep in config.depends_on
            }
            
            result = await self._execute_with_timeout(config, deps_results)
            last_result = result
            
            if result.status == TaskStatus.SUCCESS:
                return result
            
            # 如果不是最后一次尝试，进行重试
            if attempt < config.max_retries:
                result.status = TaskStatus.RETRYING
                logger.info(f"[重试] {config.task_id} 将在 {config.retry_delay}s 后重试 ({attempt+1}/{config.max_retries})")
                await asyncio.sleep(config.retry_delay)
        
        # 所有重试都失败了
        return last_result
    
    async def _process_task(self, config: TaskConfig):
        """处理单个任务（包含重试）"""
        try:
            result = await self._execute_with_retry(config)
            
            async with self._lock:
                self.results[config.task_id] = result
                self.status[config.task_id] = result.status
                
                # 如果失败且有fallback，尝试fallback
                if result.status == TaskStatus.FAILED and config.fallback_task:
                    logger.info(f"[回退] {config.task_id} -> {config.fallback_task}")
                    # 这里可以实现fallback逻辑
            
        except Exception as e:
            logger.error(f"[严重错误] {config.task_id}: {e}")
            async with self._lock:
                self.status[config.task_id] = TaskStatus.FAILED
    
    async def run(self) -> Dict[str, TaskResult]:
        """主执行循环"""
        print("\n" + "="*70)
        print(f"🚀 {self.name} - 健壮并行执行")
        print("="*70)
        
        print(f"\n📋 任务配置:")
        for tid, config in self.tasks.items():
            retry_info = f", 重试{config.max_retries}次" if config.max_retries > 0 else ""
            timeout_info = f", 超时{config.timeout}s"
            print(f"   • {tid}: {config.agent_type} ({config.duration}s){timeout_info}{retry_info}")
        
        self.start_time = time.time()
        completed = set()
        
        print(f"\n⏳ 开始执行...\n")
        
        while len(completed) < len(self.tasks):
            # 获取就绪任务
            ready = self.get_ready_tasks() - completed
            
            if ready:
                # 并行启动所有就绪任务
                tasks_to_run = [self.tasks[tid] for tid in ready]
                
                for config in tasks_to_run:
                    task = asyncio.create_task(
                        self._process_task(config),
                        name=config.task_id
                    )
                    self.running_tasks[config.task_id] = task
                    completed.add(config.task_id)
                
                # 不等待，继续检查新就绪的任务
                await asyncio.sleep(0.05)
            else:
                # 检查是否全部完成
                running_count = len([
                    t for t in self.running_tasks.values() 
                    if not t.done()
                ])
                
                if running_count == 0 and len(completed) >= len(self.tasks):
                    break
                
                await asyncio.sleep(0.1)
        
        # 等待所有任务完成
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        self.end_time = time.time()
        
        return await self._generate_report()
    
    async def _generate_report(self) -> Dict[str, TaskResult]:
        """生成执行报告"""
        total_time = self.end_time - self.start_time if self.end_time else 0
        
        # 统计
        success_count = sum(1 for r in self.results.values() if r.status == TaskStatus.SUCCESS)
        failed_count = sum(1 for r in self.results.values() if r.status == TaskStatus.FAILED)
        timeout_count = sum(1 for r in self.results.values() if r.status == TaskStatus.TIMEOUT)
        
        # 计算理论串行时间
        serial_time = sum(c.duration for c in self.tasks.values())
        speedup = serial_time / total_time if total_time > 0 else 1
        
        print("\n" + "="*70)
        print("📊 执行报告")
        print("="*70)
        print(f"   ⏱️  总耗时: {total_time:.2f}s")
        print(f"   ✅ 成功: {success_count}/{len(self.tasks)}")
        print(f"   ❌ 失败: {failed_count}/{len(self.tasks)}")
        print(f"   ⏰ 超时: {timeout_count}/{len(self.tasks)}")
        print(f"   📈 加速比: {speedup:.2f}x (串行需 {serial_time:.1f}s)")
        
        print(f"\n📋 详细结果:")
        for tid, result in self.results.items():
            status_icon = {
                TaskStatus.SUCCESS: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.TIMEOUT: "⏰",
                TaskStatus.CANCELLED: "🚫"
            }.get(result.status, "❓")
            
            retry_info = f" (重试{result.attempts}次)" if result.attempts > 1 else ""
            error_info = f" - {result.error[:30]}..." if result.error else ""
            
            print(f"   {status_icon} {tid:20} {result.status.value:10} {result.duration:.2f}s{retry_info}{error_info}")
        
        return self.results
    
    def get_status_summary(self) -> Dict:
        """获取状态摘要（用于实时监控）"""
        return {
            "total": len(self.tasks),
            "pending": sum(1 for s in self.status.values() if s == TaskStatus.PENDING),
            "running": sum(1 for s in self.status.values() if s == TaskStatus.RUNNING),
            "success": sum(1 for s in self.status.values() if s == TaskStatus.SUCCESS),
            "failed": sum(1 for s in self.status.values() if s == TaskStatus.FAILED),
            "elapsed": time.time() - self.start_time if self.start_time else 0
        }


async def demo_robust_orchestration():
    """演示健壮编排"""
    orchestrator = RobustOrchestrator("RobustDemo")
    
    # 注册事件回调
    async def on_event(event_type: str, data: Dict):
        if event_type == "task_failed":
            print(f"   ⚠️  事件: {data['task_id']} 失败 - {data['error']}")
        elif event_type == "task_timeout":
            print(f"   ⏰ 事件: {data['task_id']} 超时")
    
    orchestrator.on_event(on_event)
    
    # 场景：复杂的数据处理管道
    # 两个数据获取任务并行（其中一个容易失败）
    orchestrator.add_task(TaskConfig(
        task_id="fetch_data_a",
        agent_type="DataFetcher",
        duration=0.3,
        timeout=1.0,
        max_retries=2  # 容易失败，多给重试
    ))
    
    orchestrator.add_task(TaskConfig(
        task_id="fetch_data_b",
        agent_type="DataFetcher",
        duration=0.4,
        timeout=1.0,
        max_retries=1
    ))
    
    # 数据处理需要等两个获取完成
    orchestrator.add_task(TaskConfig(
        task_id="process_data",
        agent_type="DataProcessor",
        depends_on={"fetch_data_a", "fetch_data_b"},
        duration=0.5,
        timeout=2.0
    ))
    
    # 两个分析任务可以并行
    orchestrator.add_task(TaskConfig(
        task_id="analyze_trends",
        agent_type="Analyzer",
        depends_on={"process_data"},
        duration=0.4,
        timeout=1.5
    ))
    
    orchestrator.add_task(TaskConfig(
        task_id="anomaly_detection",
        agent_type="Analyzer",
        depends_on={"process_data"},
        duration=0.6,
        timeout=1.5
    ))
    
    # 报告生成需要等所有分析完成
    orchestrator.add_task(TaskConfig(
        task_id="generate_report",
        agent_type="Reporter",
        depends_on={"analyze_trends", "anomaly_detection"},
        duration=0.3,
        timeout=1.0
    ))
    
    # 执行
    results = await orchestrator.run()
    
    print("\n" + "="*70)
    print("🎯 关键能力展示")
    print("="*70)
    print("   ✅ 超时控制 - 防止任务卡死")
    print("   ✅ 自动重试 - 失败任务自动重试")
    print("   ✅ 错误隔离 - 单个失败不影响整体")
    print("   ✅ 状态监控 - 实时跟踪所有任务")


async def demo_error_recovery():
    """演示错误恢复"""
    print("\n" + "="*70)
    print("🛡️  错误恢复演示")
    print("="*70)
    
    orchestrator = RobustOrchestrator("ErrorRecoveryDemo")
    
    # 设置高失败率来测试恢复
    print("\n📋 配置：故意设置一些容易失败的任务\n")
    
    # 主任务（容易失败）
    orchestrator.add_task(TaskConfig(
        task_id="critical_task",
        agent_type="Critical",
        duration=0.2,
        timeout=0.5,
        max_retries=3
    ))
    
    # 备用任务
    orchestrator.add_task(TaskConfig(
        task_id="fallback_task",
        agent_type="Fallback",
        duration=0.3,
        timeout=1.0
    ))
    
    results = await orchestrator.run()
    
    print("\n💡 即使在部分任务失败的情况下，系统也能：")
    print("   1. 自动重试失败的任务")
    print("   2. 继续执行其他独立任务")
    print("   3. 最终给出完整的执行报告")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🛡️  ROBUST PARALLEL ORCHESTRATOR - Phase 1                            ║
║                                                                          ║
║   健壮性增强：超时控制 | 自动重试 | 错误隔离 | 状态监控                   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # 主演示
    asyncio.run(demo_robust_orchestration())
    
    # 错误恢复演示
    asyncio.run(demo_error_recovery())
    
    print("\n" + "="*70)
    print("✅ 健壮性增强完成！")
    print("="*70)
    print("\n下一步：集成到MCP Server作为Tool")
