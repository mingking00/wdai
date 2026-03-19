#!/usr/bin/env python3
"""
WDai 自我优化执行器
自动执行优化任务，监控效果，调整策略
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class OptimizationTask:
    id: str
    name: str
    status: str  # pending/running/completed/failed
    priority: str  # P0/P1/P2
    trigger: str
    last_run: str = ""
    run_count: int = 0
    success_rate: float = 0.0


class SelfOptimizer:
    """自我优化执行器"""
    
    def __init__(self, workspace: str = "/root/.openclaw/workspace"):
        self.workspace = Path(workspace)
        self.tasks_file = self.workspace / ".claw-status" / "optimization_tasks.json"
        self.metrics_dir = self.workspace / ".claw-status" / "metrics"
        self.tasks = self._load_tasks()
        
    def _load_tasks(self) -> List[OptimizationTask]:
        """加载优化任务"""
        default_tasks = [
            # P0 - 高优先级
            OptimizationTask("opt-001", "指标收集", "pending", "P0", "every_response"),
            OptimizationTask("opt-002", "Token预估", "pending", "P0", "before_task"),
            OptimizationTask("opt-003", "流式输出", "pending", "P0", "large_task"),
            
            # P1 - 中优先级
            OptimizationTask("opt-004", "对话摘要", "pending", "P1", "10_rounds"),
            OptimizationTask("opt-005", "混合检索", "pending", "P1", "every_search"),
            OptimizationTask("opt-006", "会话快照", "pending", "P1", "30_minutes"),
            
            # P2 - 低优先级
            OptimizationTask("opt-007", "热启动", "pending", "P2", "session_start"),
            OptimizationTask("opt-008", "反馈学习", "pending", "P2", "daily"),
        ]
        
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file) as f:
                    data = json.load(f)
                    return [OptimizationTask(**t) for t in data]
            except:
                pass
        
        return default_tasks
    
    def save_tasks(self):
        """保存任务状态"""
        with open(self.tasks_file, 'w') as f:
            json.dump([t.__dict__ for t in self.tasks], f, indent=2)
    
    def check_and_run(self) -> List[str]:
        """检查并执行任务"""
        executed = []
        
        for task in self.tasks:
            if self._should_run(task):
                if self._execute_task(task):
                    executed.append(task.id)
        
        self.save_tasks()
        return executed
    
    def _should_run(self, task: OptimizationTask) -> bool:
        """判断是否应该执行任务"""
        # P0任务每次检查都尝试
        if task.priority == "P0":
            return True
        
        # 其他任务根据频率
        if not task.last_run:
            return True
        
        last = datetime.fromisoformat(task.last_run)
        now = datetime.now()
        
        if task.trigger == "30_minutes":
            return (now - last).total_seconds() > 1800
        elif task.trigger == "daily":
            return last.date() != now.date()
        
        return False
    
    def _execute_task(self, task: OptimizationTask) -> bool:
        """执行单个任务"""
        print(f"\n🔄 执行优化任务: {task.name} ({task.id})")
        
        task.status = "running"
        task.last_run = datetime.now().isoformat()
        task.run_count += 1
        
        try:
            # 根据任务ID执行不同逻辑
            if task.id == "opt-001":
                self._run_metrics_collection()
            elif task.id == "opt-002":
                self._run_token_estimation()
            elif task.id == "opt-003":
                self._run_streaming_setup()
            elif task.id == "opt-004":
                self._run_context_summary()
            elif task.id == "opt-005":
                self._run_hybrid_retrieval()
            elif task.id == "opt-006":
                self._run_session_snapshot()
            
            task.status = "completed"
            # 更新成功率
            task.success_rate = (task.success_rate * (task.run_count - 1) + 1) / task.run_count
            print(f"   ✅ 完成")
            return True
            
        except Exception as e:
            task.status = "failed"
            task.success_rate = (task.success_rate * (task.run_count - 1)) / task.run_count
            print(f"   ❌ 失败: {e}")
            return False
    
    def _run_metrics_collection(self):
        """运行指标收集"""
        # 收集基础指标
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": 0,  # 由调用方填充
            "token_usage": 0,
            "context_remaining": 0,
        }
        
        # 保存到文件
        self.metrics_dir.mkdir(exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        metrics_file = self.metrics_dir / f"metrics_{date_str}.jsonl"
        
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(metrics) + "\n")
    
    def _run_token_estimation(self):
        """Token预估逻辑"""
        # 创建预估器标志
        flag = self.workspace / ".claw-status" / "TOKEN_ESTIMATE_ENABLED"
        flag.write_text("1")
    
    def _run_streaming_setup(self):
        """流式输出设置"""
        flag = self.workspace / ".claw-status" / "STREAMING_ENABLED"
        flag.write_text("1")
    
    def _run_context_summary(self):
        """上下文摘要"""
        # 简化实现 - 标记需要摘要
        flag = self.workspace / ".claw-status" / "NEED_CONTEXT_SUMMARY"
        flag.write_text("1")
    
    def _run_hybrid_retrieval(self):
        """混合检索"""
        flag = self.workspace / ".claw-status" / "HYBRID_RETRIEVAL_ENABLED"
        flag.write_text("1")
    
    def _run_session_snapshot(self):
        """会话快照"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "loaded_files": [],
            "active_memory": [],
        }
        
        snapshot_file = self.workspace / ".claw-status" / "snapshots" / f"snapshot_{int(time.time())}.json"
        snapshot_file.parent.mkdir(exist_ok=True)
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
    
    def generate_report(self) -> str:
        """生成优化报告"""
        report = []
        report.append("=" * 60)
        report.append("WDai 自我优化报告")
        report.append("=" * 60)
        
        # 任务状态统计
        p0_total = sum(1 for t in self.tasks if t.priority == "P0")
        p0_completed = sum(1 for t in self.tasks if t.priority == "P0" and t.status == "completed")
        
        report.append(f"\n📊 任务完成情况")
        report.append(f"   P0任务: {p0_completed}/{p0_total}")
        
        for task in self.tasks:
            icon = "✅" if task.status == "completed" else "🔄" if task.status == "running" else "⏳"
            report.append(f"   {icon} {task.name} ({task.priority}) - 成功率: {task.success_rate:.1%}")
        
        # 建议
        report.append(f"\n💡 建议")
        if p0_completed < p0_total:
            report.append("   ⚠️ 还有P0任务未完成，优先处理")
        else:
            report.append("   ✅ P0任务全部完成，可以开始P1任务")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)


def main():
    """主入口"""
    optimizer = SelfOptimizer()
    
    print("🚀 WDai 自我优化执行器启动")
    print("=" * 60)
    
    # 执行检查
    executed = optimizer.check_and_run()
    
    if executed:
        print(f"\n✅ 已执行 {len(executed)} 个优化任务")
    else:
        print("\n⏳ 暂无需要执行的任务")
    
    # 生成报告
    print(optimizer.generate_report())


if __name__ == "__main__":
    main()
