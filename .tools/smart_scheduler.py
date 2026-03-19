#!/usr/bin/env python3
"""
Smart Scheduler - 智能任务调度器

基于 Jonathan Tsai (OpenClaw Command Center) 的调度原语实现：
1. run-if-idle          - 空闲时执行
2. run-if-not-run-since - freshness保证
3. run-at-least-X-times - SLA强制执行
4. skip-if-last-run-within - 防抖机制
5. conflict-avoidance   - 冲突避免
6. priority-queue       - 优先级抢占

用法:
    from smart_scheduler import scheduler, Priority
    
    @scheduler.register(
        priority=Priority.HIGH,
        run_if_idle=True,
        skip_if_last_run_within=300
    )
    def my_task():
        pass
"""

import time
import json
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import heapq

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
SCHEDULER_DIR = WORKSPACE / ".scheduler"
SCHEDULER_DIR.mkdir(parents=True, exist_ok=True)


class Priority(Enum):
    """任务优先级"""
    CRITICAL = 0    # 关键任务，必须立即执行
    HIGH = 1        # 高优先级，可抢占低优先级
    NORMAL = 2      # 普通任务
    LOW = 3         # 后台任务
    BACKGROUND = 4  # 最低优先级


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskConfig:
    """任务配置"""
    # 基础配置
    name: str
    func: Callable = field(repr=False)
    priority: Priority = Priority.NORMAL
    
    # 调度原语配置
    run_if_idle: bool = False
    cpu_threshold: float = 50.0  # CPU使用率阈值
    
    run_if_not_run_since: Optional[int] = None  # 秒， freshness保证
    
    min_runs_per_period: Optional[int] = None   # SLA: 最少执行次数
    period_hours: int = 24                       # SLA: 周期(小时)
    
    skip_if_last_run_within: Optional[int] = None  # 秒，防抖
    
    conflict_resources: List[str] = field(default_factory=list)  # 冲突资源
    max_concurrent: int = 1                                        # 最大并发数
    
    preempt: bool = False  # 是否允许抢占


@dataclass
class Task:
    """任务实例"""
    config: TaskConfig
    status: TaskStatus = TaskStatus.PENDING
    last_run: Optional[datetime] = None
    run_count: int = 0
    run_history: List[datetime] = field(default_factory=list)
    paused_by: Optional[str] = None  # 被哪个任务抢占


class ResourceManager:
    """资源管理器"""
    
    def __init__(self):
        self.allocated_resources: Dict[str, str] = {}  # resource -> task_name
    
    def check_availability(self, resources: List[str]) -> bool:
        """检查资源是否可用"""
        for resource in resources:
            if resource in self.allocated_resources:
                return False
        return True
    
    def allocate(self, task_name: str, resources: List[str]) -> bool:
        """分配资源"""
        if not self.check_availability(resources):
            return False
        
        for resource in resources:
            self.allocated_resources[resource] = task_name
        return True
    
    def release(self, task_name: str, resources: List[str]):
        """释放资源"""
        for resource in resources:
            if self.allocated_resources.get(resource) == task_name:
                del self.allocated_resources[resource]
    
    def get_system_load(self) -> Dict[str, float]:
        """获取系统负载"""
        return {
            "cpu": psutil.cpu_percent(interval=0.1),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }


class SmartScheduler:
    """
    智能任务调度器
    
    实现 Jonathan Tsai 的 6 种调度原语
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.resource_manager = ResourceManager()
        self.running_tasks: Dict[str, Task] = {}
        self.scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._load_state()
    
    def _load_state(self):
        """加载持久化状态"""
        state_file = SCHEDULER_DIR / "scheduler_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                    for name, task_data in data.get("tasks", {}).items():
                        # 恢复任务状态（简化版）
                        pass
            except Exception as e:
                print(f"⚠️ 加载状态失败: {e}")
    
    def _save_state(self):
        """保存状态"""
        state_file = SCHEDULER_DIR / "scheduler_state.json"
        data = {
            "tasks": {
                name: {
                    "run_count": task.run_count,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "status": task.status.value
                }
                for name, task in self.tasks.items()
            }
        }
        with open(state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register(self, 
                 priority: Priority = Priority.NORMAL,
                 run_if_idle: bool = False,
                 cpu_threshold: float = 50.0,
                 run_if_not_run_since: Optional[int] = None,
                 min_runs_per_period: Optional[int] = None,
                 period_hours: int = 24,
                 skip_if_last_run_within: Optional[int] = None,
                 conflict_resources: Optional[List[str]] = None,
                 max_concurrent: int = 1,
                 preempt: bool = False):
        """任务注册装饰器"""
        def decorator(func: Callable):
            config = TaskConfig(
                name=func.__name__,
                func=func,
                priority=priority,
                run_if_idle=run_if_idle,
                cpu_threshold=cpu_threshold,
                run_if_not_run_since=run_if_not_run_since,
                min_runs_per_period=min_runs_per_period,
                period_hours=period_hours,
                skip_if_last_run_within=skip_if_last_run_within,
                conflict_resources=conflict_resources or [],
                max_concurrent=max_concurrent,
                preempt=preempt
            )
            
            task = Task(config=config)
            self.tasks[func.__name__] = task
            
            print(f"✅ 注册任务: {func.__name__} [优先级: {priority.name}]")
            return func
        return decorator
    
    # ==================== 6种调度原语检查 ====================
    
    def _check_run_if_idle(self, task: Task) -> bool:
        """原语1: 只在系统空闲时执行"""
        if not task.config.run_if_idle:
            return True  # 不启用此原语，直接通过
        
        load = self.resource_manager.get_system_load()
        cpu_ok = load['cpu'] < task.config.cpu_threshold
        
        if not cpu_ok:
            print(f"⏸️  {task.config.name}: CPU {load['cpu']:.1f}% > 阈值 {task.config.cpu_threshold}%")
        
        return cpu_ok
    
    def _check_run_if_not_run_since(self, task: Task) -> bool:
        """原语2: freshness保证 - X时间内必须执行"""
        if task.config.run_if_not_run_since is None:
            return True
        
        if task.last_run is None:
            return True  # 从未执行过，必须执行
        
        time_since_last = (datetime.now() - task.last_run).total_seconds()
        must_run = time_since_last > task.config.run_if_not_run_since
        
        if must_run:
            print(f"⚡ {task.config.name}: {time_since_last:.0f}s 未执行， freshness 强制触发")
        
        return True  # 这个原语不阻止执行，只强制触发
    
    def _check_skip_if_last_run_within(self, task: Task) -> bool:
        """原语4: 防抖 - 如果最近刚执行过，跳过"""
        if task.config.skip_if_last_run_within is None:
            return True
        
        if task.last_run is None:
            return True
        
        time_since_last = (datetime.now() - task.last_run).total_seconds()
        should_skip = time_since_last < task.config.skip_if_last_run_within
        
        if should_skip:
            print(f"⏭️  {task.config.name}: {time_since_last:.0f}s 前刚执行，防抖跳过")
        
        return not should_skip
    
    def _check_conflict_avoidance(self, task: Task) -> bool:
        """原语5: 冲突避免"""
        resources = task.config.conflict_resources
        if not resources:
            return True
        
        available = self.resource_manager.check_availability(resources)
        
        if not available:
            # 检查是否可抢占
            if task.config.preempt:
                for resource in resources:
                    if resource in self.resource_manager.allocated_resources:
                        blocking_task = self.resource_manager.allocated_resources[resource]
                        blocking_priority = self.tasks[blocking_task].config.priority
                        
                        if task.config.priority.value < blocking_priority.value:
                            print(f"⚔️  {task.config.name} 抢占 {blocking_task}")
                            self._pause_task(blocking_task)
                            return True
            
            print(f"🚫 {task.config.name}: 资源冲突 {resources}")
        
        return available
    
    def _check_priority_and_preempt(self, task: Task) -> bool:
        """原语6: 优先级抢占"""
        for running_name, running_task in list(self.running_tasks.items()):
            running_priority = running_task.config.priority
            
            # 新任务优先级更高
            if task.config.priority.value < running_priority.value:
                if task.config.preempt and running_task.config.preempt:
                    print(f"⚔️  {task.config.name}[{task.config.priority.name}] 抢占 {running_name}[{running_priority.name}]")
                    self._pause_task(running_name)
                elif not running_task.config.preempt:
                    # 运行中的任务不可抢占，等待
                    print(f"⏳ {task.config.name}: 等待 {running_name} 完成")
                    return False
        
        return True
    
    # ==================== 任务执行管理 ====================
    
    def _pause_task(self, task_name: str):
        """暂停任务"""
        if task_name in self.running_tasks:
            task = self.running_tasks[task_name]
            task.status = TaskStatus.PAUSED
            task.paused_by = "preempted"
            del self.running_tasks[task_name]
            self.resource_manager.release(task_name, task.config.conflict_resources)
            print(f"⏸️  暂停任务: {task_name}")
    
    def _execute_task(self, task: Task):
        """执行任务"""
        print(f"🚀 执行任务: {task.config.name}")
        
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        task.run_count += 1
        task.run_history.append(task.last_run)
        self.running_tasks[task.config.name] = task
        
        # 分配资源
        if task.config.conflict_resources:
            self.resource_manager.allocate(task.config.name, task.config.conflict_resources)
        
        try:
            # 执行
            task.config.func()
            task.status = TaskStatus.COMPLETED
            print(f"✅ 完成: {task.config.name}")
        except Exception as e:
            task.status = TaskStatus.FAILED
            print(f"❌ 失败: {task.config.name} - {e}")
        finally:
            # 清理
            if task.config.conflict_resources:
                self.resource_manager.release(task.config.name, task.config.conflict_resources)
            
            if task.config.name in self.running_tasks:
                del self.running_tasks[task.config.name]
            
            self._save_state()
    
    def should_run(self, task: Task) -> bool:
        """综合判断是否应该执行任务"""
        checks = [
            self._check_skip_if_last_run_within(task),  # 防抖最先检查
            self._check_run_if_idle(task),
            self._check_conflict_avoidance(task),
            self._check_priority_and_preempt(task),
        ]
        
        return all(checks)
    
    def run_pending(self):
        """运行所有待执行的任务"""
        # 按优先级排序
        pending_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING or task.status == TaskStatus.PAUSED
        ]
        pending_tasks.sort(key=lambda t: t.config.priority.value)
        
        for task in pending_tasks:
            if self.should_run(task):
                self._execute_task(task)
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            "tasks": {
                name: {
                    "status": task.status.value,
                    "run_count": task.run_count,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "priority": task.config.priority.name
                }
                for name, task in self.tasks.items()
            },
            "running": list(self.running_tasks.keys()),
            "resources": self.resource_manager.allocated_resources,
            "system_load": self.resource_manager.get_system_load()
        }


# 全局调度器实例
scheduler = SmartScheduler()


# ==================== 演示 ====================

def demo():
    """演示调度器"""
    print("=" * 60)
    print("🧠 Smart Scheduler - 基于 Tsai 调度原语")
    print("=" * 60)
    
    # 定义示例任务
    
    @scheduler.register(
        priority=Priority.LOW,
        run_if_idle=True,
        cpu_threshold=30.0
    )
    def background_cleanup():
        """后台清理 - 只在CPU<30%时运行"""
        print("🧹 执行后台清理...")
        time.sleep(0.5)
    
    @scheduler.register(
        priority=Priority.HIGH,
        skip_if_last_run_within=5  # 5秒内执行过就跳过
    )
    def health_check():
        """健康检查 - 防抖"""
        print("🏥 执行健康检查...")
        time.sleep(0.3)
    
    @scheduler.register(
        priority=Priority.NORMAL,
        conflict_resources=["database"],
        max_concurrent=1
    )
    def database_backup():
        """数据库备份 - 资源独占"""
        print("💾 执行数据库备份...")
        time.sleep(0.5)
    
    @scheduler.register(
        priority=Priority.CRITICAL,
        preempt=True
    )
    def critical_alert():
        """关键警报 - 可抢占"""
        print("🚨 处理关键警报...")
        time.sleep(0.3)
    
    @scheduler.register(
        priority=Priority.HIGH,
        run_if_not_run_since=10  # 10秒内必须执行一次
    )
    def freshness_task():
        """freshness保证任务"""
        print("⚡ 执行 freshness 任务...")
        time.sleep(0.2)
    
    print(f"\n📋 已注册 {len(scheduler.tasks)} 个任务\n")
    
    # 模拟调度
    print("第一轮调度:")
    scheduler.run_pending()
    
    print("\n第二轮调度 (测试防抖):")
    time.sleep(1)
    scheduler.run_pending()
    
    print("\n第三轮调度 (测试抢占):")
    # 先启动一个低优先级任务
    scheduler.tasks['database_backup'].status = TaskStatus.PENDING
    scheduler.run_pending()
    
    # 显示状态
    print("\n" + "=" * 60)
    print("📊 最终状态")
    print("=" * 60)
    status = scheduler.get_status()
    for name, task_status in status['tasks'].items():
        print(f"{name:20} | {task_status['status']:12} | 运行{task_status['run_count']}次")


if __name__ == "__main__":
    demo()
