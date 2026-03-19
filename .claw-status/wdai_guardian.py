#!/usr/bin/env python3
"""
WDai 系统守护进程 - 过载保护 & 自动恢复
"""

import os
import sys
import json
import time
import signal
from pathlib import Path
from datetime import datetime


class WDaiGuardian:
    """系统守护"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.state_file = self.workspace / ".claw-status" / "guardian_state.json"
        self.overload_threshold = 0.9
        
    def check_overload(self) -> dict:
        """检查系统负载"""
        # 简化实现 - 读取指标文件
        metrics_file = self.workspace / ".claw-status" / "system_metrics.jsonl"
        
        if not metrics_file.exists():
            return {"overload": False, "score": 0.0}
        
        # 读取最后一行
        with open(metrics_file) as f:
            lines = f.readlines()
            if not lines:
                return {"overload": False, "score": 0.0}
            
            last_metric = json.loads(lines[-1])
            return {
                "overload": last_metric.get("overload_score", 0) > self.overload_threshold,
                "score": last_metric.get("overload_score", 0),
                "memory": last_metric.get("memory_percent", 0)
            }
    
    def emergency_save(self):
        """紧急保存状态"""
        print("🚨 触发紧急保存...")
        
        state = {
            "timestamp": datetime.now().isoformat(),
            "workspace": str(self.workspace),
            "active_tasks": [],
            "unsaved_work": []
        }
        
        # 保存到快照文件
        snapshot_file = self.workspace / ".claw-status" / f"snapshot_{int(time.time())}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"   ✅ 状态已保存到: {snapshot_file}")
        return snapshot_file
    
    def graceful_degrade(self):
        """优雅降级"""
        print("⚠️ 执行优雅降级...")
        
        actions = [
            ("暂停非关键任务", self._pause_non_critical),
            ("释放缓存", self._clear_cache),
            ("简化模式", self._enable_simplify_mode),
        ]
        
        for name, action in actions:
            try:
                action()
                print(f"   ✅ {name}")
            except Exception as e:
                print(f"   ❌ {name}: {e}")
    
    def _pause_non_critical(self):
        """暂停非关键任务"""
        flag = self.workspace / ".claw-status" / "PAUSE_NON_CRITICAL"
        flag.write_text("1")
    
    def _clear_cache(self):
        """清除缓存"""
        cache_dir = self.workspace / ".claw-status" / "cache"
        if cache_dir.exists():
            for f in cache_dir.glob("*"):
                f.unlink()
    
    def _enable_simplify_mode(self):
        """启用简化模式"""
        flag = self.workspace / ".claw-status" / "SIMPLIFY_MODE"
        flag.write_text("1")
    
    def recover(self, snapshot_file: Path = None):
        """从快照恢复"""
        print("🔄 系统恢复...")
        
        if snapshot_file and snapshot_file.exists():
            with open(snapshot_file) as f:
                state = json.load(f)
            print(f"   ✅ 从快照恢复: {snapshot_file}")
        
        # 清除降级标志
        for flag in ["PAUSE_NON_CRITICAL", "SIMPLIFY_MODE"]:
            flag_file = self.workspace / ".claw-status" / flag
            if flag_file.exists():
                flag_file.unlink()
        
        print("   ✅ 系统恢复正常")
    
    def monitor_loop(self):
        """监控循环"""
        print("👁️ WDai Guardian 启动监控")
        
        while True:
            status = self.check_overload()
            
            if status["overload"]:
                print(f"🚨 检测到过载: {status['score']:.2f}")
                
                # 紧急保存
                snapshot = self.emergency_save()
                
                # 优雅降级
                self.graceful_degrade()
                
                # 通知
                print("⚠️ 系统已进入降级模式，等待恢复...")
                
                # 等待恢复
                while self.check_overload()["overload"]:
                    time.sleep(10)
                
                # 恢复
                self.recover(snapshot)
            
            time.sleep(30)  # 每30秒检查一次


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--monitor", action="store_true", help="启动监控循环")
    parser.add_argument("--check", action="store_true", help="单次检查")
    parser.add_argument("--recover", type=str, help="从快照恢复")
    
    args = parser.parse_args()
    
    guardian = WDaiGuardian()
    
    if args.monitor:
        guardian.monitor_loop()
    elif args.check:
        status = guardian.check_overload()
        print(f"过载状态: {status}")
    elif args.recover:
        guardian.recover(Path(args.recover))
    else:
        # 默认单次检查
        status = guardian.check_overload()
        if status["overload"]:
            print("🚨 检测到过载，执行保护...")
            guardian.emergency_save()
            guardian.graceful_degrade()
        else:
            print(f"✅ 系统正常 (过载分数: {status['score']:.2f})")


if __name__ == "__main__":
    main()
