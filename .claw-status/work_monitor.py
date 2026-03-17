#!/usr/bin/env python3
"""
work_monitor.py - 工作监察员系统

让用户能实时看到我的工作状态、进度和内容。
所有写入到这个系统的内容，用户可以通过文件直接查看。
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading

class WorkStatus(Enum):
    IDLE = "idle"                    # 空闲
    PLANNING = "planning"            # 规划阶段
    EXECUTING = "executing"          # 执行阶段
    WAITING = "waiting"              # 等待（如API响应）
    ERROR = "error"                  # 出错
    COMPLETED = "completed"          # 完成

@dataclass
class WorkSession:
    """工作会话记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    task_description: str = ""
    status: str = "idle"
    
    # 进度追踪
    total_steps: int = 0
    completed_steps: int = 0
    current_step: str = ""
    
    # 详细日志
    logs: List[Dict] = field(default_factory=list)
    
    # 中间产物
    artifacts: List[Dict] = field(default_factory=list)
    
    # 性能指标
    tokens_used: int = 0
    api_calls: int = 0
    elapsed_seconds: float = 0.0

class WorkMonitor:
    """
    工作监察员
    
    实时记录工作状态，写入 .claw-status/ 目录
    用户可以通过 cat .claw-status/current.json 查看
    """
    
    def __init__(self, workspace: Path = None):
        self.workspace = workspace or Path(".claw-status")
        self.workspace.mkdir(exist_ok=True)
        
        self.current_session: Optional[WorkSession] = None
        self.lock = threading.Lock()
        
        # 历史记录
        self.history_file = self.workspace / "history.jsonl"
        
    def start_session(self, task_description: str, total_steps: int = 0) -> str:
        """
        开始一个新的工作会话
        
        用户会立即看到: "开始工作: [任务描述]"
        """
        session_id = str(uuid.uuid4())[:8]
        
        with self.lock:
            # 如果有未完成的会话，先结束
            if self.current_session and self.current_session.status not in ["completed", "error"]:
                self._end_session("interrupted")
            
            self.current_session = WorkSession(
                id=session_id,
                task_description=task_description,
                status="planning",
                total_steps=total_steps
            )
            
            # 写入状态文件
            self._write_status()
            
        self._log("session_start", f"开始工作: {task_description}")
        return session_id
    
    def update_progress(self, 
                       current_step: str, 
                       completed_steps: int = None,
                       total_steps: int = None,
                       message: str = ""):
        """
        更新进度
        
        这是核心方法，应该在每个关键步骤调用
        """
        if not self.current_session:
            return
        
        with self.lock:
            self.current_session.status = "executing"
            self.current_session.current_step = current_step
            
            if completed_steps is not None:
                self.current_session.completed_steps = completed_steps
            if total_steps is not None:
                self.current_session.total_steps = total_steps
            
            self._write_status()
        
        if message:
            self._log("progress", message, {
                "step": current_step,
                "progress": f"{self.current_session.completed_steps}/{self.current_session.total_steps}"
            })
        
        # 控制台实时输出（用户可见）
        print(f"[{self.current_session.id}] {current_step}")
    
    def add_artifact(self, name: str, path: str, description: str = ""):
        """记录中间产物"""
        if not self.current_session:
            return
        
        artifact = {
            "name": name,
            "path": path,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        
        with self.lock:
            self.current_session.artifacts.append(artifact)
            self._write_status()
        
        self._log("artifact", f"创建产物: {name}", artifact)
    
    def waiting(self, reason: str, estimated_seconds: int = 0):
        """
        标记为等待状态
        
        例如：等待API响应、等待用户输入
        """
        if not self.current_session:
            return
        
        with self.lock:
            self.current_session.status = "waiting"
            self._write_status()
        
        msg = f"等待中: {reason}"
        if estimated_seconds > 0:
            msg += f" (预计{estimated_seconds}秒)"
        
        self._log("waiting", msg)
        print(f"⏳ {msg}")
    
    def error(self, error_message: str, recoverable: bool = True):
        """记录错误"""
        if not self.current_session:
            return
        
        with self.lock:
            self.current_session.status = "error"
            self._write_status()
        
        self._log("error", error_message, {"recoverable": recoverable})
        print(f"❌ 错误: {error_message}")
    
    def complete(self, summary: str = ""):
        """完成工作"""
        if not self.current_session:
            return
        
        self._end_session("completed", summary)
    
    def _end_session(self, status: str, summary: str = ""):
        """结束会话"""
        with self.lock:
            self.current_session.status = status
            self.current_session.end_time = datetime.now().isoformat()
            
            # 计算耗时
            try:
                start = datetime.fromisoformat(self.current_session.start_time)
                end = datetime.fromisoformat(self.current_session.end_time)
                self.current_session.elapsed_seconds = (end - start).total_seconds()
            except:
                pass
            
            # 写入最终状态
            self._write_status()
            
            # 归档到历史
            self._archive_session()
            
            # 清空当前会话
            session = self.current_session
            self.current_session = None
        
        # 输出完成信息
        emoji = "✅" if status == "completed" else "⚠️"
        print(f"\n{emoji} 工作完成 ({session.elapsed_seconds:.1f}s): {session.task_description}")
        if summary:
            print(f"   摘要: {summary}")
        
        # 产物列表
        if session.artifacts:
            print(f"   产物:")
            for art in session.artifacts:
                print(f"     - {art['name']}: {art['path']}")
    
    def _write_status(self):
        """写入当前状态到文件"""
        if not self.current_session:
            return
        
        status_file = self.workspace / "current.json"
        
        data = asdict(self.current_session)
        # 添加可读的时间
        data["readable_time"] = datetime.now().strftime("%H:%M:%S")
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _archive_session(self):
        """归档到历史记录"""
        if not self.current_session:
            return
        
        with open(self.history_file, 'a', encoding='utf-8') as f:
            json.dump(asdict(self.current_session), f, ensure_ascii=False)
            f.write('\n')
    
    def _log(self, event_type: str, message: str, metadata: Dict = None):
        """添加日志"""
        if not self.current_session:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message
        }
        
        if metadata:
            log_entry["metadata"] = metadata
        
        with self.lock:
            self.current_session.logs.append(log_entry)
    
    def get_current_status(self) -> Optional[Dict]:
        """获取当前状态"""
        if not self.current_session:
            return None
        return asdict(self.current_session)
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取历史会话"""
        sessions = []
        
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        sessions.append(json.loads(line))
                    except:
                        pass
        
        return sessions[-limit:]

# ============ 全局监察员 ============

_global_monitor: Optional[WorkMonitor] = None

def get_monitor() -> WorkMonitor:
    """获取全局监察员实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = WorkMonitor()
    return _global_monitor

def start_task(description: str, steps: int = 0) -> str:
    """便捷函数：开始任务"""
    return get_monitor().start_session(description, steps)

def progress(step: str, current: int = 0, total: int = 0, msg: str = ""):
    """便捷函数：更新进度"""
    get_monitor().update_progress(step, current, total, msg)

def artifact(name: str, path: str, desc: str = ""):
    """便捷函数：记录产物"""
    get_monitor().add_artifact(name, path, desc)

def complete(summary: str = ""):
    """便捷函数：完成任务"""
    get_monitor().complete(summary)

def waiting(reason: str, eta: int = 0):
    """便捷函数：标记等待"""
    get_monitor().waiting(reason, eta)

# ============ CLI 查看工具 ============

def show_status():
    """显示当前状态"""
    monitor = get_monitor()
    status = monitor.get_current_status()
    
    if not status:
        print("当前没有进行中的工作")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 当前工作状态")
    print(f"{'='*60}")
    print(f"ID: {status['id']}")
    print(f"任务: {status['task_description']}")
    print(f"状态: {status['status']}")
    print(f"开始: {status['start_time']}")
    
    if status['total_steps'] > 0:
        pct = status['completed_steps'] / status['total_steps'] * 100
        print(f"进度: {status['completed_steps']}/{status['total_steps']} ({pct:.0f}%)")
    
    print(f"当前步骤: {status['current_step']}")
    
    if status['artifacts']:
        print(f"\n产物:")
        for art in status['artifacts']:
            print(f"  • {art['name']}: {art['path']}")
    
    if status['logs']:
        print(f"\n最近日志:")
        for log in status['logs'][-5:]:
            time = log['timestamp'].split('T')[1].split('.')[0]
            print(f"  [{time}] {log['type']}: {log['message'][:50]}")
    
    print(f"{'='*60}\n")

def show_history(limit: int = 5):
    """显示历史"""
    monitor = get_monitor()
    history = monitor.get_history(limit)
    
    if not history:
        print("没有历史记录")
        return
    
    print(f"\n{'='*60}")
    print(f"📚 最近 {len(history)} 个工作会话")
    print(f"{'='*60}")
    
    for i, session in enumerate(reversed(history), 1):
        print(f"\n{i}. [{session['id']}] {session['task_description'][:40]}")
        print(f"   状态: {session['status']} | 耗时: {session.get('elapsed_seconds', 0):.1f}s")
        print(f"   步骤: {session['completed_steps']}/{session['total_steps']}")
        print(f"   产物: {len(session['artifacts'])} 个")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "history":
        show_history()
    else:
        show_status()
