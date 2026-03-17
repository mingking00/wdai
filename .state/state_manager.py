#!/usr/bin/env python3
"""
wdai 持久状态系统 (Persistent State System)
基于 CIRCE Framework 的文件协议实现

解决核心问题: 每次重启都重新开始，状态丢失
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

class StateManager:
    """
    管理wdai的持久状态
    所有状态存储在 .state/ 目录下
    """
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.path.expanduser("~/.openclaw/workspace"))
        self.state_dir = self.workspace / ".state"
        self.state_dir.mkdir(exist_ok=True)
        
        # 子目录
        self.sessions_dir = self.state_dir / "sessions"
        self.tasks_dir = self.state_dir / "tasks"
        self.context_dir = self.state_dir / "context"
        self.checkpoint_dir = self.state_dir / "checkpoints"
        
        for d in [self.sessions_dir, self.tasks_dir, self.context_dir, self.checkpoint_dir]:
            d.mkdir(exist_ok=True)
    
    # ==================== 会话状态 ====================
    
    def save_session_state(self, session_id: str, state: Dict[str, Any]):
        """保存会话状态"""
        filepath = self.sessions_dir / f"{session_id}.json"
        state['saved_at'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话状态"""
        filepath = self.sessions_dir / f"{session_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_active_sessions(self) -> List[str]:
        """获取所有活动会话ID"""
        return [f.stem for f in self.sessions_dir.glob("*.json")]
    
    # ==================== 任务状态 ====================
    
    def create_task(self, task_type: str, description: str, 
                    metadata: Dict = None) -> str:
        """创建新任务，返回任务ID"""
        task_id = f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = {
            "id": task_id,
            "type": task_type,
            "description": description,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "steps": [],
            "results": {},
            "errors": []
        }
        
        filepath = self.tasks_dir / f"{task_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        
        return task_id
    
    def update_task(self, task_id: str, updates: Dict[str, Any]):
        """更新任务状态"""
        filepath = self.tasks_dir / f"{task_id}.json"
        
        if not filepath.exists():
            raise ValueError(f"Task not found: {task_id}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            task = json.load(f)
        
        task.update(updates)
        task['updated_at'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
    
    def add_task_step(self, task_id: str, step: str, result: Any = None):
        """添加任务步骤"""
        filepath = self.tasks_dir / f"{task_id}.json"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            task = json.load(f)
        
        task['steps'].append({
            "step": step,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        task['updated_at'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务详情"""
        filepath = self.tasks_dir / f"{task_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_tasks(self, status: str = None, task_type: str = None) -> List[Dict]:
        """列出任务"""
        tasks = []
        
        for filepath in self.tasks_dir.glob("*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                task = json.load(f)
            
            if status and task.get('status') != status:
                continue
            if task_type and task.get('type') != task_type:
                continue
            
            tasks.append(task)
        
        return sorted(tasks, key=lambda x: x['created_at'], reverse=True)
    
    # ==================== 上下文记忆 ====================
    
    def save_context(self, name: str, context: Dict[str, Any]):
        """保存上下文"""
        filepath = self.context_dir / f"{name}.json"
        context['saved_at'] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
    
    def load_context(self, name: str) -> Optional[Dict]:
        """加载上下文"""
        filepath = self.context_dir / f"{name}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # ==================== 检查点 ====================
    
    def create_checkpoint(self, name: str, data: Dict[str, Any]) -> str:
        """创建检查点"""
        checkpoint_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filepath = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        checkpoint = {
            "id": checkpoint_id,
            "name": name,
            "data": data,
            "created_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        
        return checkpoint_id
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict]:
        """恢复检查点"""
        filepath = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        return checkpoint.get('data')
    
    def list_checkpoints(self, name: str = None) -> List[Dict]:
        """列出检查点"""
        checkpoints = []
        
        pattern = f"{name}_*.json" if name else "*.json"
        for filepath in self.checkpoint_dir.glob(pattern):
            with open(filepath, 'r', encoding='utf-8') as f:
                checkpoints.append(json.load(f))
        
        return sorted(checkpoints, key=lambda x: x['created_at'], reverse=True)
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取状态管理统计"""
        return {
            "sessions": len(list(self.sessions_dir.glob("*.json"))),
            "tasks": {
                "total": len(list(self.tasks_dir.glob("*.json"))),
                "by_status": self._count_tasks_by_status()
            },
            "contexts": len(list(self.context_dir.glob("*.json"))),
            "checkpoints": len(list(self.checkpoint_dir.glob("*.json")))
        }
    
    def _count_tasks_by_status(self) -> Dict[str, int]:
        """按状态统计任务"""
        counts = {}
        for filepath in self.tasks_dir.glob("*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                task = json.load(f)
            status = task.get('status', 'unknown')
            counts[status] = counts.get(status, 0) + 1
        return counts


# ==================== 便捷函数 ====================

_state_manager = None

def get_state_manager() -> StateManager:
    """获取全局状态管理器实例"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


# 装饰器: 自动保存任务进度
def track_task(task_type: str, description: str = None):
    """装饰器: 自动跟踪任务执行"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            sm = get_state_manager()
            desc = description or func.__name__
            task_id = sm.create_task(task_type, desc)
            
            try:
                sm.update_task(task_id, {"status": "running"})
                result = func(*args, **kwargs)
                sm.update_task(task_id, {
                    "status": "completed",
                    "result": result
                })
                return result
            except Exception as e:
                sm.update_task(task_id, {
                    "status": "failed",
                    "errors": [{"error": str(e), "timestamp": datetime.now().isoformat()}]
                })
                raise
        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试
    sm = StateManager()
    
    # 创建任务
    task_id = sm.create_task("test", "测试持久状态系统")
    print(f"创建任务: {task_id}")
    
    # 添加步骤
    sm.add_task_step(task_id, "步骤1", {"data": "test"})
    sm.add_task_step(task_id, "步骤2", {"data": "test2"})
    
    # 完成任务
    sm.update_task(task_id, {"status": "completed", "result": "成功"})
    
    # 查看任务
    task = sm.get_task(task_id)
    print(f"任务详情: {json.dumps(task, indent=2)}")
    
    # 查看统计
    print(f"统计: {json.dumps(sm.get_stats(), indent=2)}")
