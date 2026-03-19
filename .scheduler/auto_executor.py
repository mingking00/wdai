#!/usr/bin/env python3
"""
wdai 自动执行调度器 v1.0
时间分配 + 自动执行 + 完整记忆记录
"""

import json
import time
import os
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess

# 调度器目录
SCHEDULER_DIR = Path("/root/.openclaw/workspace/.scheduler")
SCHEDULER_DIR.mkdir(parents=True, exist_ok=True)

class ExecutionMode(Enum):
    """执行模式"""
    MANUAL = "manual"           # 手动触发
    SCHEDULED = "scheduled"     # 定时执行
    EVENT_DRIVEN = "event"      # 事件驱动
    CONTINUOUS = "continuous"   # 持续运行

@dataclass
class TimeAllocation:
    """时间分配配置"""
    external_loop_interval: int = 3600      # 外部循环间隔(秒): 1小时
    internal_loop_interval: int = 1800      # 内部循环间隔(秒): 30分钟
    paper_study_interval: int = 86400       # 论文学习间隔(秒): 1天
    memory_maintenance_interval: int = 7200 # 记忆维护间隔(秒): 2小时
    
    max_continuous_runtime: int = 300       # 单次最大运行时间(秒): 5分钟
    cooldown_period: int = 60               # 冷却时间(秒): 1分钟

class AutoExecutor:
    """
    自动执行器
    管理时间分配和自动执行循环
    """
    
    def __init__(self):
        self.scheduler_dir = SCHEDULER_DIR
        self.config_file = self.scheduler_dir / "executor_config.json"
        self.log_file = self.scheduler_dir / "execution_log.json"
        self.memory_file = self.scheduler_dir / "execution_memory.json"
        
        self.time_allocation = TimeAllocation()
        self.running = False
        self.last_execution = {
            "external_loop": 0,
            "internal_loop": 0,
            "paper_study": 0,
            "memory_maintenance": 0
        }
        
        self._load_config()
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """设置信号处理"""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """信号处理"""
        print(f"\n[AutoExecutor] 收到信号 {signum}，正在停止...")
        self.running = False
        
    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.last_execution = config.get("last_execution", self.last_execution)
                
    def _save_config(self):
        """保存配置"""
        with open(self.config_file, 'w') as f:
            json.dump({
                "last_execution": self.last_execution,
                "time_allocation": asdict(self.time_allocation)
            }, f, indent=2)
            
    def _log_execution(self, task_type: str, status: str, details: Dict):
        """记录执行日志"""
        log_entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "task_type": task_type,
            "status": status,
            "details": details
        }
        
        logs = []
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
        
        logs.append(log_entry)
        # 只保留最近100条
        logs = logs[-100:]
        
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
    def _record_memory(self, execution_record: Dict):
        """记录到记忆系统"""
        memory_entry = {
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "auto_execution",
            "content": execution_record
        }
        
        memories = []
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                memories = json.load(f)
        
        memories.append(memory_entry)
        
        with open(self.memory_file, 'w') as f:
            json.dump(memories, f, indent=2)
        
        # 同时记录到每日记忆文件
        self._append_to_daily_memory(memory_entry)
        
    def _append_to_daily_memory(self, entry: Dict):
        """追加到每日记忆文件"""
        memory_dir = Path("/root/.openclaw/workspace/memory/daily")
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        today_file = memory_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        
        content = f"\n\n---\n\n## 自动执行记录 - {datetime.now().strftime('%H:%M:%S')}\n\n"
        content += f"**任务类型**: {entry['content'].get('task_type', 'unknown')}\n"
        content += f"**状态**: {entry['content'].get('status', 'unknown')}\n"
        
        if 'summary' in entry['content']:
            content += f"**摘要**: {entry['content']['summary']}\n"
        
        with open(today_file, 'a', encoding='utf-8') as f:
            f.write(content)
            
    def _should_run_external_loop(self) -> bool:
        """检查是否应该运行外部循环"""
        return time.time() - self.last_execution["external_loop"] > self.time_allocation.external_loop_interval
        
    def _should_run_internal_loop(self) -> bool:
        """检查是否应该运行内部循环"""
        return time.time() - self.last_execution["internal_loop"] > self.time_allocation.internal_loop_interval
        
    def _should_run_paper_study(self) -> bool:
        """检查是否应该运行论文学习"""
        return time.time() - self.last_execution["paper_study"] > self.time_allocation.paper_study_interval
        
    def _should_run_memory_maintenance(self) -> bool:
        """检查是否应该运行记忆维护"""
        return time.time() - self.last_execution["memory_maintenance"] > self.time_allocation.memory_maintenance_interval
        
    def run_external_loop(self) -> Dict:
        """执行外部循环"""
        print("\n" + "="*65)
        print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] 执行外部循环")
        print("="*65)
        
        start_time = time.time()
        
        try:
            # 执行外部循环
            result = subprocess.run(
                ["python3", "/root/.openclaw/workspace/.evolution/evolution_loop_v2.py"],
                capture_output=True,
                text=True,
                timeout=self.time_allocation.max_continuous_runtime
            )
            
            duration = time.time() - start_time
            
            execution_record = {
                "task_type": "external_loop",
                "status": "success" if result.returncode == 0 else "failed",
                "duration": duration,
                "output": result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout,
                "summary": f"外部循环执行完成，耗时{duration:.1f}秒"
            }
            
            # 记录日志和记忆
            self._log_execution("external_loop", execution_record["status"], execution_record)
            self._record_memory(execution_record)
            
            # 更新最后执行时间
            self.last_execution["external_loop"] = time.time()
            self._save_config()
            
            print(f"✅ 外部循环完成 ({duration:.1f}s)")
            
            return execution_record
            
        except subprocess.TimeoutExpired:
            execution_record = {
                "task_type": "external_loop",
                "status": "timeout",
                "duration": self.time_allocation.max_continuous_runtime,
                "summary": "执行超时"
            }
            self._log_execution("external_loop", "timeout", execution_record)
            self._record_memory(execution_record)
            print("⚠️  外部循环超时")
            return execution_record
            
        except Exception as e:
            execution_record = {
                "task_type": "external_loop",
                "status": "error",
                "error": str(e),
                "summary": f"执行错误: {str(e)}"
            }
            self._log_execution("external_loop", "error", execution_record)
            self._record_memory(execution_record)
            print(f"❌ 外部循环错误: {e}")
            return execution_record
            
    def run_internal_loop(self) -> Dict:
        """执行内部循环"""
        print(f"\n⚙️  [{datetime.now().strftime('%H:%M:%S')}] 执行内部循环")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["python3", "/root/.openclaw/workspace/.evolution/evolution_loop.py"],
                capture_output=True,
                text=True,
                timeout=self.time_allocation.max_continuous_runtime
            )
            
            duration = time.time() - start_time
            
            execution_record = {
                "task_type": "internal_loop",
                "status": "success" if result.returncode == 0 else "failed",
                "duration": duration,
                "summary": f"内部循环完成，耗时{duration:.1f}秒"
            }
            
            self._log_execution("internal_loop", execution_record["status"], execution_record)
            self._record_memory(execution_record)
            
            self.last_execution["internal_loop"] = time.time()
            self._save_config()
            
            print(f"✅ 内部循环完成 ({duration:.1f}s)")
            
            return execution_record
            
        except Exception as e:
            execution_record = {
                "task_type": "internal_loop",
                "status": "error",
                "error": str(e)
            }
            self._log_execution("internal_loop", "error", execution_record)
            self._record_memory(execution_record)
            return execution_record
            
    def run_paper_study(self) -> Dict:
        """执行论文学习"""
        print(f"\n📚 [{datetime.now().strftime('%H:%M:%S')}] 执行论文学习")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["python3", "/root/.openclaw/workspace/.knowledge/metacognition_papers.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            duration = time.time() - start_time
            
            execution_record = {
                "task_type": "paper_study",
                "status": "success" if result.returncode == 0 else "failed",
                "duration": duration,
                "summary": f"论文学习完成，耗时{duration:.1f}秒"
            }
            
            self._log_execution("paper_study", execution_record["status"], execution_record)
            self._record_memory(execution_record)
            
            self.last_execution["paper_study"] = time.time()
            self._save_config()
            
            print(f"✅ 论文学习完成 ({duration:.1f}s)")
            
            return execution_record
            
        except Exception as e:
            execution_record = {
                "task_type": "paper_study",
                "status": "error",
                "error": str(e)
            }
            self._log_execution("paper_study", "error", execution_record)
            self._record_memory(execution_record)
            return execution_record
            
    def run_memory_maintenance(self) -> Dict:
        """执行记忆维护"""
        print(f"\n🧠 [{datetime.now().strftime('%H:%M:%S')}] 执行记忆维护")
        
        start_time = time.time()
        
        try:
            # 整理记忆文件
            memory_dir = Path("/root/.openclaw/workspace/memory/daily")
            if memory_dir.exists():
                files = list(memory_dir.glob("*.md"))
                
                # 统计记忆文件
                execution_record = {
                    "task_type": "memory_maintenance",
                    "status": "success",
                    "duration": time.time() - start_time,
                    "summary": f"记忆维护完成，共有{len(files)}个记忆文件"
                }
                
                self._log_execution("memory_maintenance", "success", execution_record)
                self._record_memory(execution_record)
                
                self.last_execution["memory_maintenance"] = time.time()
                self._save_config()
                
                print(f"✅ 记忆维护完成 ({len(files)}个文件)")
                
                return execution_record
                
        except Exception as e:
            execution_record = {
                "task_type": "memory_maintenance",
                "status": "error",
                "error": str(e)
            }
            self._log_execution("memory_maintenance", "error", execution_record)
            self._record_memory(execution_record)
            return execution_record
            
    def run_single_cycle(self) -> List[Dict]:
        """运行单次循环 - 检查并执行所有到期任务"""
        results = []
        
        print(f"\n{'='*65}")
        print(f"🤖 wdai AutoExecutor - 单次循环")
        print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*65}")
        
        # 检查并执行外部循环
        if self._should_run_external_loop():
            result = self.run_external_loop()
            results.append(result)
            time.sleep(self.time_allocation.cooldown_period)
        else:
            next_run = self.last_execution["external_loop"] + self.time_allocation.external_loop_interval
            wait_time = next_run - time.time()
            print(f"⏳ 外部循环还需等待 {wait_time/60:.1f} 分钟")
            
        # 检查并执行内部循环
        if self._should_run_internal_loop():
            result = self.run_internal_loop()
            results.append(result)
            time.sleep(self.time_allocation.cooldown_period)
            
        # 检查并执行论文学习
        if self._should_run_paper_study():
            result = self.run_paper_study()
            results.append(result)
            time.sleep(self.time_allocation.cooldown_period)
            
        # 检查并执行记忆维护
        if self._should_run_memory_maintenance():
            result = self.run_memory_maintenance()
            results.append(result)
            
        print(f"\n{'='*65}")
        print(f"✅ 单次循环完成，执行了 {len(results)} 个任务")
        print(f"{'='*65}\n")
        
        return results
        
    def run_continuous(self):
        """持续运行模式"""
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║              wdai AutoExecutor 持续运行模式                  ║")
        print("║     时间分配: 外循环1h | 内循环30m | 论文1d | 记忆2h        ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
        
        self.running = True
        
        while self.running:
            try:
                self.run_single_cycle()
                
                # 等待下次检查
                print(f"💤 进入休眠，{self.time_allocation.cooldown_period}秒后再次检查...")
                time.sleep(self.time_allocation.cooldown_period)
                
            except Exception as e:
                print(f"❌ 循环错误: {e}")
                time.sleep(60)  # 出错后等待1分钟
                
        print("\n[AutoExecutor] 已停止")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="wdai 自动执行调度器")
    parser.add_argument("--mode", choices=["single", "continuous"], default="single",
                       help="执行模式: single(单次) 或 continuous(持续)")
    parser.add_argument("--force-external", action="store_true",
                       help="强制执行外部循环")
    parser.add_argument("--force-internal", action="store_true",
                       help="强制执行内部循环")
    
    args = parser.parse_args()
    
    executor = AutoExecutor()
    
    if args.mode == "continuous":
        executor.run_continuous()
    else:
        # 单次模式
        if args.force_external:
            executor.run_external_loop()
        elif args.force_internal:
            executor.run_internal_loop()
        else:
            executor.run_single_cycle()

if __name__ == "__main__":
    main()
