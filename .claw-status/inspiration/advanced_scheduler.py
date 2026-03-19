#!/usr/bin/env python3
"""
灵感摄取系统 - 高级调度器 v4.0

基于CS162调度原语:
- 多级别反馈队列 (MLFQ)
- 负载均衡
- 背压控制
- 指数退避

Author: wdai
Version: 4.0
"""

import json
import time
import heapq
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))
sys.path.insert(0, str(CLAW_STATUS / "agents"))

from agents.integration import DualAgentInspirationSystem


class Priority(Enum):
    """任务优先级 (对应MLFQ的队列级别)"""
    CRITICAL = 0    # 最高优先级 - 用户手动触发
    HIGH = 1        # 高优先级 - 产出奖励后的快速恢复
    NORMAL = 2      # 普通优先级 - 常规调度
    LOW = 3         # 低优先级 - 空转后的惩罚降级


@dataclass
class SourceTask:
    """源任务 (可调度单元)"""
    source_id: str
    priority: Priority
    created_at: datetime
    attempts: int = 0
    last_failure: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    
    # MLFQ时间片相关
    time_slice_remaining: int = 0  # 剩余时间片(秒)
    queue_level: int = 0  # 当前所在队列级别
    
    def __lt__(self, other):
        """用于优先级队列比较"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at
    
    def to_dict(self) -> dict:
        return {
            'source_id': self.source_id,
            'priority': self.priority.name,
            'created_at': self.created_at.isoformat(),
            'attempts': self.attempts,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'queue_level': self.queue_level
        }


@dataclass
class SourceMetrics:
    """源性能指标 (用于负载均衡决策)"""
    source_id: str
    
    # 历史统计
    total_crawls: int = 0
    success_count: int = 0
    failure_count: int = 0
    empty_count: int = 0
    
    # 性能指标
    avg_crawl_time_ms: float = 0.0
    last_crawl_time_ms: float = 0.0
    
    # 健康度评分 (0-1)
    health_score: float = 1.0
    
    # 当前负载
    current_load: int = 0
    max_concurrent: int = 3
    
    # 指数退避状态
    consecutive_failures: int = 0
    current_backoff_seconds: float = 0.0
    
    # 产出质量
    avg_quality_score: float = 0.5
    last_quality_score: float = 0.5
    
    def update_health_score(self):
        """更新健康度评分"""
        if self.total_crawls == 0:
            self.health_score = 1.0
            return
        
        success_rate = self.success_count / self.total_crawls
        recency_weight = 0.7  # 近期结果权重更高
        
        # 考虑最近的质量
        quality_factor = (self.avg_quality_score * 0.5 + self.last_quality_score * 0.5)
        
        # 负载因素：负载高时稍微降低健康度
        load_factor = 1.0 - (self.current_load / self.max_concurrent) * 0.2
        
        self.health_score = success_rate * quality_factor * load_factor
    
    def can_accept_task(self) -> bool:
        """检查是否可以接受新任务 (背压控制)"""
        return self.current_load < self.max_concurrent
    
    def record_success(self, crawl_time_ms: float, quality_score: float):
        """记录成功"""
        self.total_crawls += 1
        self.success_count += 1
        self.consecutive_failures = 0
        self.current_backoff_seconds = 0.0
        # 不在这里减少load，由调度器管理
        
        # 更新平均时间
        self.last_crawl_time_ms = crawl_time_ms
        self.avg_crawl_time_ms = (
            self.avg_crawl_time_ms * 0.7 + crawl_time_ms * 0.3
        )
        
        # 更新质量
        self.last_quality_score = quality_score
        self.avg_quality_score = (
            self.avg_quality_score * 0.7 + quality_score * 0.3
        )
        
        self.update_health_score()
    
    def record_failure(self, is_empty: bool = False):
        """记录失败"""
        self.total_crawls += 1
        self.failure_count += 1
        # 不在这里减少load，由调度器管理
        
        if is_empty:
            self.empty_count += 1
        
        # 指数退避
        self.consecutive_failures += 1
        self.current_backoff_seconds = min(
            2 ** self.consecutive_failures * 60,  # 指数增长: 2,4,8,16...分钟
            4 * 60 * 60  # 最大4小时
        )
        
        self.update_health_score()


class LoadBalancer:
    """
    负载均衡器
    
    策略:
    - ROUND_ROBIN: 轮询
    - LEAST_LOADED: 选择负载最低的
    - WEIGHTED_RESPONSE: 基于响应时间的加权
    - HEALTH_SCORE: 基于健康度评分
    """
    
    def __init__(self, strategy: str = "health_score"):
        self.strategy = strategy
        self._round_robin_index = 0
    
    def select_source(self, metrics: Dict[str, SourceMetrics]) -> Optional[str]:
        """选择最优源"""
        if not metrics:
            return None
        
        # 过滤掉过载的源
        available = {
            sid: m for sid, m in metrics.items()
            if m.can_accept_task() and m.current_backoff_seconds == 0
        }
        
        if not available:
            return None
        
        if self.strategy == "round_robin":
            return self._round_robin(list(available.keys()))
        elif self.strategy == "least_loaded":
            return self._least_loaded(available)
        elif self.strategy == "weighted_response":
            return self._weighted_response(available)
        elif self.strategy == "health_score":
            return self._health_score(available)
        else:
            return self._health_score(available)
    
    def _round_robin(self, sources: List[str]) -> str:
        """轮询选择"""
        idx = self._round_robin_index % len(sources)
        self._round_robin_index += 1
        return sources[idx]
    
    def _least_loaded(self, metrics: Dict[str, SourceMetrics]) -> str:
        """选择负载最低的"""
        return min(metrics.items(), key=lambda x: x[1].current_load)[0]
    
    def _weighted_response(self, metrics: Dict[str, SourceMetrics]) -> str:
        """基于响应时间加权 (响应快的高概率)"""
        import random
        
        # 计算权重 (响应时间越短，权重越高)
        weights = []
        sources = []
        for sid, m in metrics.items():
            if m.avg_crawl_time_ms > 0:
                weight = 1.0 / m.avg_crawl_time_ms
            else:
                weight = 1.0
            weights.append(weight)
            sources.append(sid)
        
        # 加权随机选择
        total = sum(weights)
        if total == 0:
            return random.choice(sources)
        
        r = random.uniform(0, total)
        cumulative = 0
        for sid, w in zip(sources, weights):
            cumulative += w
            if r <= cumulative:
                return sid
        
        return sources[-1]
    
    def _health_score(self, metrics: Dict[str, SourceMetrics]) -> str:
        """基于健康度评分选择 (最健康的)"""
        return max(metrics.items(), key=lambda x: x[1].health_score)[0]


class BackpressureController:
    """
    背压控制器
    
    限制系统整体并发，防止过载
    """
    
    def __init__(self, max_concurrent: int = 5, queue_size: int = 20):
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        
        self.active_count = 0
        self.waiting_queue: deque = deque()
        self.rejected_count = 0
        
        self._lock = threading.Lock()
    
    def try_acquire_slot(self, task: SourceTask) -> bool:
        """尝试获取执行槽位"""
        with self._lock:
            if self.active_count < self.max_concurrent:
                self.active_count += 1
                return True
            elif len(self.waiting_queue) < self.queue_size:
                self.waiting_queue.append(task)
                return False  # 进入等待队列
            else:
                self.rejected_count += 1
                return False  # 被拒绝
    
    def release_slot(self) -> Optional[SourceTask]:
        """释放槽位，返回等待队列中的下一个任务"""
        with self._lock:
            self.active_count = max(0, self.active_count - 1)
            
            if self.waiting_queue:
                return self.waiting_queue.popleft()
            return None
    
    def get_stats(self) -> dict:
        """获取统计"""
        with self._lock:
            return {
                'active': self.active_count,
                'waiting': len(self.waiting_queue),
                'rejected': self.rejected_count,
                'utilization': self.active_count / self.max_concurrent
            }


class MLFQScheduler:
    """
    多级别反馈队列调度器 (CS162调度原语)
    
    实现:
    - 4个优先级队列 (CRITICAL > HIGH > NORMAL > LOW)
    - 时间片轮转 (高优先级时间片短，快速响应)
    - 优先级衰减 (长时间运行的任务降低优先级)
    - 优先级提升 (避免饥饿)
    """
    
    # 时间片配置 (秒) - 高优先级短，低优先级长
    TIME_SLICES = {
        Priority.CRITICAL: 30,   # 30秒
        Priority.HIGH: 60,       # 1分钟
        Priority.NORMAL: 120,    # 2分钟
        Priority.LOW: 300,       # 5分钟
    }
    
    # 优先级提升间隔 (防止饥饿)
    PRIORITY_BOOST_INTERVAL_SECONDS = 300  # 5分钟
    
    def __init__(self):
        # 4个优先级队列
        self.queues: Dict[Priority, deque] = {
            p: deque() for p in Priority
        }
        
        # 正在运行的任务
        self.running_task: Optional[SourceTask] = None
        self.running_since: Optional[datetime] = None
        
        # 统计
        self.total_scheduled = 0
        self.total_completed = 0
        self.last_priority_boost = datetime.now()
        
        self._lock = threading.Lock()
    
    def enqueue(self, task: SourceTask):
        """将任务加入队列"""
        with self._lock:
            # 初始化时间片
            task.time_slice_remaining = self.TIME_SLICES[task.priority]
            task.queue_level = task.priority.value
            
            self.queues[task.priority].append(task)
            self.total_scheduled += 1
    
    def dequeue(self) -> Optional[SourceTask]:
        """从队列中取出下一个任务"""
        with self._lock:
            # 检查优先级提升
            self._check_priority_boost()
            
            # 按优先级从高到低查找
            for priority in [Priority.CRITICAL, Priority.HIGH, 
                           Priority.NORMAL, Priority.LOW]:
                if self.queues[priority]:
                    task = self.queues[priority].popleft()
                    self.running_task = task
                    self.running_since = datetime.now()
                    return task
            
            return None
    
    def _check_priority_boost(self):
        """检查并执行优先级提升 (防止饥饿)"""
        now = datetime.now()
        elapsed = (now - self.last_priority_boost).total_seconds()
        
        if elapsed >= self.PRIORITY_BOOST_INTERVAL_SECONDS:
            # 将所有LOW提升到NORMAL，NORMAL提升到HIGH
            for task in list(self.queues[Priority.LOW]):
                task.priority = Priority.NORMAL
                task.time_slice_remaining = self.TIME_SLICES[Priority.NORMAL]
            
            for task in list(self.queues[Priority.NORMAL]):
                task.priority = Priority.HIGH
                task.time_slice_remaining = self.TIME_SLICES[Priority.HIGH]
            
            # 重新组织队列
            self.queues[Priority.NORMAL].extend(self.queues[Priority.LOW])
            self.queues[Priority.LOW].clear()
            
            self.queues[Priority.HIGH].extend(self.queues[Priority.NORMAL])
            self.queues[Priority.NORMAL].clear()
            
            self.last_priority_boost = now
    
    def yield_task(self, task: SourceTask, used_time_ms: int) -> bool:
        """
        任务让出CPU
        
        返回: 是否还有时间片剩余
        """
        with self._lock:
            task.time_slice_remaining -= used_time_ms / 1000
            
            if task.time_slice_remaining <= 0:
                # 时间片用完，降低优先级
                if task.priority == Priority.CRITICAL:
                    task.priority = Priority.HIGH
                elif task.priority == Priority.HIGH:
                    task.priority = Priority.NORMAL
                elif task.priority == Priority.NORMAL:
                    task.priority = Priority.LOW
                # LOW不再降级
                
                # 重新初始化时间片
                task.time_slice_remaining = self.TIME_SLICES[task.priority]
                task.queue_level = task.priority.value
                
                # 放回队列
                self.queues[task.priority].append(task)
                self.running_task = None
                self.running_since = None
                return False
            
            return True
    
    def complete_task(self, task: SourceTask):
        """任务完成"""
        with self._lock:
            self.total_completed += 1
            self.running_task = None
            self.running_since = None
    
    def get_stats(self) -> dict:
        """获取统计"""
        with self._lock:
            return {
                'scheduled': self.total_scheduled,
                'completed': self.total_completed,
                'pending': sum(len(q) for q in self.queues.values()),
                'by_priority': {
                    p.name: len(q) for p, q in self.queues.items()
                },
                'running': self.running_task.source_id if self.running_task else None
            }


class AdvancedScheduler:
    """
    高级调度器 v4.0
    
    集成:
    - MLFQ优先级调度
    - 负载均衡
    - 背压控制
    - 指数退避
    """
    
    CONFIG = {
        # 背压控制
        'max_concurrent': 3,
        'queue_size': 10,
        
        # 负载均衡策略
        'load_balance_strategy': 'health_score',
        
        # 超时设置
        'task_timeout_seconds': 300,
        'max_crawl_time_seconds': 600,
        
        # 监控
        'enable_monitoring': True,
    }
    
    def __init__(self, data_dir: str = "data/scheduler_v4"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 子系统
        self.mlfq = MLFQScheduler()
        self.load_balancer = LoadBalancer(self.CONFIG['load_balance_strategy'])
        self.backpressure = BackpressureController(
            max_concurrent=self.CONFIG['max_concurrent'],
            queue_size=self.CONFIG['queue_size']
        )
        
        # 源指标
        self.metrics: Dict[str, SourceMetrics] = {}
        
        # 数据源配置
        self.sources: Dict[str, dict] = {
            'arxiv': {
                'base_interval': 288,  # 4.8小时
                'priority': Priority.NORMAL,
                'max_concurrent': 2,
            },
            'github': {
                'base_interval': 288,
                'priority': Priority.NORMAL,
                'max_concurrent': 1,
            },
            'twitter': {
                'base_interval': 60,  # 1小时
                'priority': Priority.HIGH,
                'max_concurrent': 2,
            }
        }
        
        # 状态
        self.run_count = 0
        self.last_run_time = None
        self.is_running = False
        
        # 双代理系统
        self.system = None
        
        self._load_state()
        self._init_metrics()
    
    def _load_state(self):
        """加载状态"""
        state_file = self.data_dir / "scheduler_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.run_count = state.get('run_count', 0)
                    self.last_run_time = state.get('last_run_time')
            except Exception as e:
                print(f"[Scheduler] 加载状态失败: {e}")
    
    def _save_state(self):
        """保存状态"""
        state_file = self.data_dir / "scheduler_state.json"
        state = {
            'run_count': self.run_count,
            'last_run_time': self.last_run_time,
            'updated_at': datetime.now().isoformat()
        }
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _init_metrics(self):
        """初始化源指标"""
        for source_id in self.sources:
            self.metrics[source_id] = SourceMetrics(
                source_id=source_id,
                max_concurrent=self.sources[source_id]['max_concurrent']
            )
    
    def schedule_source(self, source_id: str, force: bool = False) -> bool:
        """
        调度一个源
        
        返回: 是否成功加入调度队列
        """
        if source_id not in self.sources:
            return False
        
        # 检查是否处于退避期
        metric = self.metrics[source_id]
        if metric.current_backoff_seconds > 0 and not force:
            next_run = metric.last_failure + timedelta(
                seconds=metric.current_backoff_seconds
            ) if metric.last_failure else datetime.now()
            
            if datetime.now() < next_run:
                print(f"[{source_id}] 处于退避期，下次可运行: {next_run.strftime('%H:%M')}")
                return False
        
        # 确定优先级
        priority = self.sources[source_id]['priority']
        
        # 根据历史表现调整优先级
        if metric.consecutive_failures >= 2:
            # 连续失败降级
            if priority == Priority.NORMAL:
                priority = Priority.LOW
            elif priority == Priority.HIGH:
                priority = Priority.NORMAL
        
        if metric.avg_quality_score > 0.8 and metric.total_crawls > 3:
            # 高质量源升级
            if priority == Priority.NORMAL:
                priority = Priority.HIGH
        
        # 创建任务
        task = SourceTask(
            source_id=source_id,
            priority=priority,
            created_at=datetime.now(),
            attempts=metric.consecutive_failures
        )
        
        # 加入MLFQ
        self.mlfq.enqueue(task)
        print(f"[{source_id}] 已加入调度队列 (优先级: {priority.name})")
        return True
    
    def run_once(self) -> dict:
        """
        运行一次调度循环
        """
        print("\n" + "="*60)
        print("🔄 高级调度器 v4.0 - 调度循环")
        print("="*60)
        
        # 1. 获取下一个任务
        task = self.mlfq.dequeue()
        if not task:
            print("⏹️  没有待调度的任务")
            return {'status': 'no_task'}
        
        source_id = task.source_id
        print(f"\n📋 选中任务: {source_id} (优先级: {task.priority.name})")
        
        # 2. 背压控制 - 获取执行槽位
        if not self.backpressure.try_acquire_slot(task):
            if len(self.backpressure.waiting_queue) >= self.backpressure.queue_size:
                print(f"⚠️  系统过载，任务被拒绝")
                return {'status': 'rejected', 'source': source_id}
            else:
                print(f"⏳ 系统繁忙，任务进入等待队列")
                return {'status': 'queued', 'source': source_id}
        
        # 3. 负载均衡检查
        selected_source = self.load_balancer.select_source(self.metrics)
        if selected_source != source_id:
            print(f"🔄 负载均衡调整: {source_id} -> {selected_source}")
            source_id = selected_source
        
        # 4. 执行
        print(f"🚀 执行任务: {source_id}")
        self.is_running = True
        start_time = time.time()
        
        try:
            # 更新负载
            self.metrics[source_id].current_load += 1
            
            # 执行实际抓取
            result = self._execute_crawl(source_id)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # 5. 处理结果
            if result.get('status') == 'success':
                new_items = result.get('new_items', 0)
                quality = result.get('quality_score', 0.5)
                
                if new_items > 0:
                    # 成功且有产出
                    self.metrics[source_id].record_success(elapsed_ms, quality)
                    print(f"✅ 成功: {new_items} 个新灵感 (质量: {quality:.2f})")
                    
                    # 产出奖励 - 提升优先级
                    self._boost_priority(source_id)
                else:
                    # 成功但无产出 (空转)
                    self.metrics[source_id].record_failure(is_empty=True)
                    print(f"⚠️  空转: 无新灵感")
                
                self.mlfq.complete_task(task)
                
            else:
                # 失败
                self.metrics[source_id].record_failure()
                print(f"❌ 失败: {result.get('error', '未知错误')}")
                self.mlfq.complete_task(task)
            
            # 6. 释放槽位
            self.backpressure.release_slot()
            self.metrics[source_id].current_load -= 1
            
            self.run_count += 1
            self.last_run_time = datetime.now().isoformat()
            self._save_state()
            
            return {
                'status': 'completed',
                'source': source_id,
                'new_items': result.get('new_items', 0),
                'elapsed_ms': elapsed_ms
            }
            
        except Exception as e:
            print(f"❌ 异常: {e}")
            self.metrics[source_id].record_failure()
            self.backpressure.release_slot()
            self.metrics[source_id].current_load -= 1
            self.is_running = False
            return {'status': 'error', 'error': str(e)}
    
    def _execute_crawl(self, source_id: str) -> dict:
        """执行实际抓取 (简化版，实际应调用双代理系统)"""
        # 这里应该调用实际的抓取逻辑
        # 现在返回模拟结果
        import random
        
        time.sleep(0.5)  # 模拟执行时间
        
        # 模拟不同结果
        r = random.random()
        if r < 0.6:
            return {
                'status': 'success',
                'new_items': random.randint(1, 5),
                'quality_score': random.uniform(0.6, 0.95)
            }
        elif r < 0.8:
            return {
                'status': 'success',
                'new_items': 0,
                'quality_score': 0.0
            }
        else:
            return {
                'status': 'error',
                'error': '模拟网络错误'
            }
    
    def _boost_priority(self, source_id: str):
        """提升源的优先级 (产出奖励)"""
        config = self.sources[source_id]
        current = config['priority']
        
        if current == Priority.LOW:
            config['priority'] = Priority.NORMAL
            print(f"🎁 产出奖励: {source_id} 优先级提升为 NORMAL")
        elif current == Priority.NORMAL:
            config['priority'] = Priority.HIGH
            print(f"🎁 产出奖励: {source_id} 优先级提升为 HIGH")
    
    def get_stats(self) -> dict:
        """获取完整统计"""
        return {
            'scheduler': {
                'version': '4.0',
                'run_count': self.run_count,
                'is_running': self.is_running
            },
            'mlfq': self.mlfq.get_stats(),
            'backpressure': self.backpressure.get_stats(),
            'sources': {
                sid: {
                    'health_score': round(m.health_score, 2),
                    'consecutive_failures': m.consecutive_failures,
                    'backoff_seconds': m.current_backoff_seconds,
                    'current_load': m.current_load,
                    'avg_quality': round(m.avg_quality_score, 2)
                }
                for sid, m in self.metrics.items()
            }
        }
    
    def print_stats(self):
        """打印统计"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 调度器统计")
        print("="*60)
        
        print(f"\n运行次数: {stats['scheduler']['run_count']}")
        print(f"MLFQ调度: {stats['mlfq']['completed']}/{stats['mlfq']['scheduled']} 完成")
        print(f"待处理: {stats['mlfq']['pending']}")
        
        print(f"\n背压状态:")
        print(f"  活跃: {stats['backpressure']['active']}/{self.CONFIG['max_concurrent']}")
        print(f"  等待: {stats['backpressure']['waiting']}")
        print(f"  拒绝: {stats['backpressure']['rejected']}")
        print(f"  利用率: {stats['backpressure']['utilization']:.1%}")
        
        print(f"\n源状态:")
        for sid, m in stats['sources'].items():
            print(f"  {sid}:")
            print(f"    健康度: {m['health_score']:.2f}")
            print(f"    连续失败: {m['consecutive_failures']}")
            print(f"    退避: {m['backoff_seconds']:.0f}s")
            print(f"    当前负载: {m['current_load']}")
            print(f"    平均质量: {m['avg_quality']:.2f}")


def test_advanced_scheduler():
    """测试高级调度器"""
    print("="*70)
    print("🧪 测试高级调度器 v4.0 (CS162调度原语)")
    print("="*70)
    
    scheduler = AdvancedScheduler()
    
    # 调度所有源
    print("\n📥 调度所有源...")
    for source_id in scheduler.sources:
        scheduler.schedule_source(source_id)
    
    # 运行多个循环
    print("\n🔄 运行调度循环...")
    results = []
    for i in range(6):
        print(f"\n--- 循环 {i+1} ---")
        result = scheduler.run_once()
        results.append(result)
        
        if result['status'] == 'no_task':
            break
        
        time.sleep(0.2)
    
    # 打印统计
    scheduler.print_stats()
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)
    
    return scheduler, results


if __name__ == "__main__":
    test_advanced_scheduler()
