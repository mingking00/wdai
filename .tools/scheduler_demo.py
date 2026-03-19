#!/usr/bin/env python3
"""
Smart Scheduler 实际应用示例

将 Tsai 调度原语应用到我们的 Skill 系统
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from smart_scheduler import scheduler, Priority, TaskStatus
import time


# ==================== 实际 Skill 任务定义 ====================

@scheduler.register(
    priority=Priority.LOW,
    run_if_idle=True,
    cpu_threshold=40.0,
    skip_if_last_run_within=600  # 10分钟内不重复清理
)
def cleanup_old_sessions():
    """
    清理旧会话
    
    调度策略:
    - 低优先级后台任务
    - 只在CPU<40%时执行
    - 10分钟内执行过就跳过
    """
    print("🧹 [cleanup] 清理7天前的旧会话文件...")
    # 实际实现: 删除旧的 .jsonl 文件
    time.sleep(0.5)
    print("✅ [cleanup] 清理完成")


@scheduler.register(
    priority=Priority.HIGH,
    run_if_not_run_since=3600,  # 1小时内必须执行一次
    conflict_resources=["memory_db"]  # 独占内存数据库
)
def memory_consolidation():
    """
    记忆整合
    
    调度策略:
    - 高优先级
    - 1小时内必须执行一次 (freshness)
    - 独占 memory_db 资源
    """
    print("🧠 [memory] 整合短期记忆到长期存储...")
    # 实际实现: 调用 memory_context_skill
    time.sleep(0.8)
    print("✅ [memory] 记忆整合完成")


@scheduler.register(
    priority=Priority.NORMAL,
    min_runs_per_period=3,  # SLA: 每天至少3次
    period_hours=24,
    conflict_resources=["search_api"],
    max_concurrent=2
)
def update_search_index():
    """
    更新搜索索引
    
    调度策略:
    - 每天最少执行3次
    - 共享 search_api 资源 (最多2个并发)
    """
    print("🔍 [search] 更新搜索索引...")
    # 实际实现: 调用 free_search_skill
    time.sleep(1.0)
    print("✅ [search] 索引更新完成")


@scheduler.register(
    priority=Priority.CRITICAL,
    preempt=True,  # 可抢占其他任务
    conflict_resources=["system"]
)
def emergency_save_state():
    """
    紧急状态保存
    
    调度策略:
    - 最高优先级
    - 可抢占其他任务
    - 独占 system 资源
    """
    print("🚨 [emergency] 紧急保存系统状态...")
    # 实际实现: 立即保存所有状态
    time.sleep(0.3)
    print("✅ [emergency] 状态已保存")


@scheduler.register(
    priority=Priority.LOW,
    run_if_idle=True,
    cpu_threshold=20.0  # 非常保守的CPU阈值
)
def generate_daily_report():
    """
    生成日报
    
    调度策略:
    - 后台任务
    - 只在CPU<20%时执行 (非常保守)
    """
    print("📊 [report] 生成每日统计报告...")
    # 实际实现: 统计数据并发送
    time.sleep(1.5)
    print("✅ [report] 报告生成完成")


# ==================== 演示运行 ====================

def run_demo():
    """运行调度演示"""
    print("=" * 70)
    print("🚀 Smart Scheduler + Skills 集成演示")
    print("=" * 70)
    print()
    
    print(f"📋 已注册 {len(scheduler.tasks)} 个 Skill 任务:\n")
    for name, task in scheduler.tasks.items():
        config = task.config
        print(f"  • {name}")
        print(f"    优先级: {config.priority.name}")
        if config.run_if_idle:
            print(f"    条件: CPU<{config.cpu_threshold}%")
        if config.run_if_not_run_since:
            print(f"    SLA: {config.run_if_not_run_since}s 内必须执行")
        if config.skip_if_last_run_within:
            print(f"    防抖: {config.skip_if_last_run_within}s 内跳过")
        if config.conflict_resources:
            print(f"    资源: {config.conflict_resources}")
        print()
    
    # 模拟系统状态
    print("-" * 70)
    print("🖥️  当前系统状态:")
    status = scheduler.get_status()
    load = status['system_load']
    print(f"   CPU: {load['cpu']:.1f}% | 内存: {load['memory']:.1f}% | 磁盘: {load['disk']:.1f}%")
    print()
    
    # 第一轮调度
    print("-" * 70)
    print("▶️  第一轮调度 (所有任务):")
    print("-" * 70)
    scheduler.run_pending()
    
    print()
    
    # 第二轮调度 (测试防抖)
    print("-" * 70)
    print("▶️  第二轮调度 (立即执行 - 测试防抖):")
    print("-" * 70)
    scheduler.run_pending()
    
    print()
    
    # 模拟紧急任务
    print("-" * 70)
    print("▶️  模拟紧急情况 (关键任务抢占):")
    print("-" * 70)
    # 先将一个低优先级任务设为运行中
    from smart_scheduler import TaskStatus
    scheduler.tasks['generate_daily_report'].status = TaskStatus.RUNNING
    scheduler.running_tasks['generate_daily_report'] = scheduler.tasks['generate_daily_report']
    print("   generate_daily_report 正在运行中...")
    print("   emergency_save_state 尝试执行 (可抢占)...")
    scheduler.tasks['emergency_save_state'].status = TaskStatus.PENDING
    scheduler.run_pending()
    
    print()
    print("=" * 70)
    print("📊 最终任务状态")
    print("=" * 70)
    final_status = scheduler.get_status()
    for name, task_status in final_status['tasks'].items():
        icon = {
            'completed': '✅',
            'pending': '⏳',
            'running': '🔄',
            'paused': '⏸️'
        }.get(task_status['status'], '❓')
        print(f"  {icon} {name:25} | {task_status['status']:12} | 运行{task_status['run_count']}次")
    
    print()
    print("💡 调度策略总结:")
    print("  • 高优先级任务自动优先执行")
    print("  • CRITICAL 任务可抢占后台任务")
    print("  • run-if-idle 确保不影响系统性能")
    print("  • skip-if-last-run-within 避免重复执行")
    print("  • conflict-avoidance 防止资源冲突")


if __name__ == "__main__":
    run_demo()
