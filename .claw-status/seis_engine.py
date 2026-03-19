#!/usr/bin/env python3
"""
WDai 自执行改进系统 (SEIS - Self-Executing Improvement System)
自动监控、分析、执行改进任务
"""

import json
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class SystemMetric:
    """系统指标"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    active_tasks: int
    last_error: Optional[str]
    response_time_ms: float
    overload_score: float  # 0-1, >0.7表示过载


@dataclass  
class ImprovementTask:
    """改进任务"""
    id: str
    title: str
    trigger: str  # 触发条件
    action: str   # 执行动作
    auto_execute: bool
    last_run: Optional[str]
    run_count: int
    status: str   # pending/running/completed/failed


class SelfImprovementEngine:
    """自改进引擎 - 监控、分析、执行"""
    
    def __init__(self, workspace: str = "/root/.openclaw/workspace"):
        self.workspace = Path(workspace)
        self.metrics_file = self.workspace / ".claw-status" / "system_metrics.jsonl"
        self.tasks_file = self.workspace / ".claw-status" / "improvement_tasks.json"
        self.overload_threshold = 0.7
        self.stuck_threshold_minutes = 30
        
        # 初始化改进任务
        self.tasks = self._load_tasks()
        
    def _load_tasks(self) -> List[ImprovementTask]:
        """加载改进任务清单"""
        default_tasks = [
            ImprovementTask(
                id="imp-001",
                title="过载时自动简化输出",
                trigger="overload_score > 0.7",
                action="启用极简模式：结论先行，单点输出",
                auto_execute=True,
                last_run=None,
                run_count=0,
                status="pending"
            ),
            ImprovementTask(
                id="imp-002", 
                title="卡住时自动搜索",
                trigger="no_progress > 15min",
                action="执行网络搜索获取新思路",
                auto_execute=True,
                last_run=None,
                run_count=0,
                status="pending"
            ),
            ImprovementTask(
                id="imp-003",
                title="架构瓶颈时重构",
                trigger="error_count > 3 in 1hour",
                action="分析错误模式，提出架构优化",
                auto_execute=True,
                last_run=None,
                run_count=0,
                status="pending"
            ),
            ImprovementTask(
                id="imp-004",
                title="每日自动评估",
                trigger="daily at 00:00",
                action="评估当日evo完成率，调整优先级",
                auto_execute=True,
                last_run=None,
                run_count=0,
                status="pending"
            ),
            ImprovementTask(
                id="imp-005",
                title="Memory溢出时压缩",
                trigger="memory_percent > 85",
                action="触发记忆压缩，归档旧数据",
                auto_execute=True,
                last_run=None,
                run_count=0,
                status="pending"
            ),
        ]
        
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file) as f:
                    data = json.load(f)
                    return [ImprovementTask(**t) for t in data]
            except:
                pass
        
        return default_tasks
    
    def save_tasks(self):
        """保存任务状态"""
        with open(self.tasks_file, 'w') as f:
            json.dump([asdict(t) for t in self.tasks], f, indent=2)
    
    def collect_metrics(self) -> SystemMetric:
        """收集系统指标"""
        # 简化版 - 实际可以读取真实系统数据
        import random
        
        metric = SystemMetric(
            timestamp=datetime.now().isoformat(),
            cpu_percent=random.uniform(10, 60),
            memory_percent=random.uniform(30, 70),
            active_tasks=random.randint(0, 5),
            last_error=None,
            response_time_ms=random.uniform(100, 2000),
            overload_score=0.0
        )
        
        # 计算过载分数
        metric.overload_score = self._calculate_overload(metric)
        
        # 保存指标
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(asdict(metric)) + "\n")
        
        return metric
    
    def _calculate_overload(self, metric: SystemMetric) -> float:
        """计算过载分数"""
        score = 0.0
        if metric.response_time_ms > 1000: score += 0.3
        if metric.memory_percent > 80: score += 0.3
        if metric.active_tasks > 3: score += 0.2
        if metric.cpu_percent > 70: score += 0.2
        return min(score, 1.0)
    
    def check_triggers(self, metric: SystemMetric) -> List[ImprovementTask]:
        """检查触发的任务"""
        triggered = []
        
        for task in self.tasks:
            if task.status == "running":
                continue
                
            # 检查触发条件
            if self._eval_trigger(task.trigger, metric):
                triggered.append(task)
        
        return triggered
    
    def _eval_trigger(self, trigger: str, metric: SystemMetric) -> bool:
        """评估触发条件"""
        if "overload_score" in trigger:
            threshold = float(trigger.split(">")[1].strip())
            return metric.overload_score > threshold
        
        if "memory_percent" in trigger:
            threshold = float(trigger.split(">")[1].strip())
            return metric.memory_percent > threshold
        
        if "daily at" in trigger:
            # 简化检查
            return False
        
        return False
    
    def execute_task(self, task: ImprovementTask) -> bool:
        """执行任务"""
        print(f"\n🔄 执行任务: {task.title}")
        print(f"   动作: {task.action}")
        
        task.status = "running"
        task.last_run = datetime.now().isoformat()
        task.run_count += 1
        
        try:
            # 根据任务类型执行不同动作
            if "简化" in task.action:
                self._action_simplify()
            elif "搜索" in task.action:
                self._action_search()
            elif "重构" in task.action:
                self._action_refactor()
            elif "压缩" in task.action:
                self._action_compress()
            
            task.status = "completed"
            print(f"   ✅ 完成")
            return True
            
        except Exception as e:
            task.status = "failed"
            print(f"   ❌ 失败: {e}")
            return False
    
    def _action_simplify(self):
        """执行简化动作"""
        # 设置系统标志，让后续输出自动简化
        flag_file = self.workspace / ".claw-status" / "SIMPLIFY_MODE"
        flag_file.write_text("1")
        print("   已启用极简模式")
    
    def _action_search(self):
        """执行搜索动作"""
        # 这里可以集成搜索API
        print("   执行搜索获取新思路...")
        # subprocess.run(["python3", "search_helper.py"])
    
    def _action_refactor(self):
        """执行重构分析"""
        print("   分析错误模式...")
        # 分析最近的错误日志
    
    def _action_compress(self):
        """执行压缩动作"""
        print("   触发记忆压缩...")
        # 归档旧记忆
    
    def generate_report(self) -> str:
        """生成系统报告"""
        report = []
        report.append("=" * 60)
        report.append("WDai 自执行改进系统报告")
        report.append("=" * 60)
        
        # 最新指标
        metric = self.collect_metrics()
        report.append(f"\n📊 当前状态")
        report.append(f"   过载分数: {metric.overload_score:.2f} {'⚠️' if metric.overload_score > 0.7 else '✅'}")
        report.append(f"   内存使用: {metric.memory_percent:.1f}%")
        report.append(f"   响应时间: {metric.response_time_ms:.0f}ms")
        
        # 任务状态
        report.append(f"\n📋 改进任务")
        for task in self.tasks:
            icon = "✅" if task.status == "completed" else "🔄" if task.status == "running" else "⏳"
            auto = "自动" if task.auto_execute else "手动"
            report.append(f"   {icon} {task.id}: {task.title} ({auto})")
        
        # 建议
        report.append(f"\n💡 建议")
        if metric.overload_score > 0.7:
            report.append("   ⚠️ 系统过载，建议启用极简模式")
        if metric.memory_percent > 80:
            report.append("   ⚠️ 内存使用高，建议触发记忆压缩")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)
    
    def run_cycle(self):
        """运行一个监控周期"""
        print("\n" + "=" * 60)
        print("SEIS 监控周期", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)
        
        # 1. 收集指标
        metric = self.collect_metrics()
        print(f"📊 指标: 过载={metric.overload_score:.2f}, 内存={metric.memory_percent:.1f}%")
        
        # 2. 检查触发
        triggered = self.check_triggers(metric)
        
        # 3. 执行任务
        for task in triggered:
            if task.auto_execute:
                self.execute_task(task)
            else:
                print(f"⏳ 任务待手动执行: {task.title}")
        
        # 4. 保存状态
        self.save_tasks()
        
        if not triggered:
            print("✅ 系统正常，无触发任务")
        
        return len(triggered)


def main():
    """主入口"""
    engine = SelfImprovementEngine()
    
    # 单次运行模式
    triggered = engine.run_cycle()
    print(engine.generate_report())
    
    return triggered


if __name__ == "__main__":
    main()
