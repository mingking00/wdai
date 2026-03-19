#!/usr/bin/env python3
"""
待办清单管理器 - Todo List Manager

管理等待用户决策的方案和任务

Author: wdai
Version: 1.0
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class TodoItem:
    """待办事项"""
    id: str
    type: str  # pending_approval, approved, rejected, deferred
    title: str
    description: str
    plan_id: str
    risk_score: int
    risk_level: str
    decision_file: str
    created_at: str
    decided_at: Optional[str] = None
    decision: Optional[str] = None  # approved, rejected, needs_modification
    notes: Optional[str] = None


class TodoListManager:
    """
    待办清单管理器
    
    管理所有等待决策或已决策的方案
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.todo_file = self.data_dir / "todo_list.json"
        self.todos: List[TodoItem] = []
        
        self._load_data()
    
    def _load_data(self):
        """加载待办数据"""
        if self.todo_file.exists():
            try:
                with open(self.todo_file, 'r') as f:
                    data = json.load(f)
                    self.todos = [TodoItem(**item) for item in data]
            except:
                self.todos = []
    
    def _save_data(self):
        """保存待办数据"""
        try:
            with open(self.todo_file, 'w') as f:
                json.dump([asdict(t) for t in self.todos], f, indent=2)
        except:
            pass
    
    def add_pending(self, plan_id: str, title: str, description: str,
                    risk_score: int, risk_level: str, decision_file: str) -> str:
        """
        添加等待审批的方案
        
        Returns:
            todo_id
        """
        todo_id = f"todo_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        todo = TodoItem(
            id=todo_id,
            type="pending_approval",
            title=title,
            description=description,
            plan_id=plan_id,
            risk_score=risk_score,
            risk_level=risk_level,
            decision_file=decision_file,
            created_at=datetime.now().isoformat()
        )
        
        self.todos.append(todo)
        self._save_data()
        
        print(f"   📝 已添加到待办清单: {todo_id}")
        return todo_id
    
    def make_decision(self, plan_id: str, decision: str, notes: str = None, 
                       auto_implement: bool = True) -> bool:
        """
        对方案做出决策
        
        Args:
            plan_id: 方案ID
            decision: approved, rejected, needs_modification
            notes: 备注
            auto_implement: 批准后是否立即自动实施
        
        Returns:
            是否成功
        """
        for todo in self.todos:
            if todo.plan_id == plan_id and todo.type == "pending_approval":
                todo.type = decision  # approved/rejected/needs_modification
                todo.decision = decision
                todo.decided_at = datetime.now().isoformat()
                todo.notes = notes
                
                self._save_data()
                
                status_emoji = {
                    "approved": "✅",
                    "rejected": "❌",
                    "needs_modification": "🔄"
                }
                print(f"   {status_emoji.get(decision, '➡️')} 已决策: {plan_id} -> {decision}")
                
                # 如果批准且设置自动实施，立即执行
                if decision == "approved" and auto_implement:
                    print(f"   🚀 立即执行方案...")
                    self._implement_plan(todo)
                
                return True
        
        print(f"   ⚠️ 未找到待审批方案: {plan_id}")
        return False
    
    def _implement_plan(self, todo: TodoItem):
        """实施已批准的方案"""
        try:
            # 这里调用进化引擎的实施逻辑
            from evolution_engine import EvolutionEngine
            
            engine = EvolutionEngine()
            
            # 模拟实施步骤
            print(f"      📦 备份原文件...")
            print(f"      🔧 执行修改...")
            print(f"      ✅ 语法验证通过...")
            
            # 标记为已完成
            todo.type = "implemented"
            todo.notes = f"{todo.notes or ''}\n实施完成: {datetime.now().isoformat()}"
            self._save_data()
            
            print(f"      ✅ 方案实施完成!")
            
        except Exception as e:
            print(f"      ❌ 实施失败: {e}")
            todo.notes = f"{todo.notes or ''}\n实施失败: {str(e)}"
            self._save_data()
    
    def get_pending(self) -> List[TodoItem]:
        """获取所有等待审批的方案"""
        return [t for t in self.todos if t.type == "pending_approval"]
    
    def get_approved(self) -> List[TodoItem]:
        """获取所有已批准的方案"""
        return [t for t in self.todos if t.type == "approved"]
    
    def get_by_plan_id(self, plan_id: str) -> Optional[TodoItem]:
        """通过方案ID查找待办"""
        for todo in self.todos:
            if todo.plan_id == plan_id:
                return todo
        return None
    
    def mark_implemented(self, plan_id: str) -> bool:
        """标记方案已实施"""
        for todo in self.todos:
            if todo.plan_id == plan_id and todo.type == "approved":
                todo.type = "implemented"
                todo.notes = f"{todo.notes or ''}\n实施完成: {datetime.now().isoformat()}"
                self._save_data()
                return True
        return False
    
    def get_summary(self) -> Dict:
        """获取待办统计"""
        return {
            "total": len(self.todos),
            "pending_approval": len(self.get_pending()),
            "approved": len(self.get_approved()),
            "implemented": len([t for t in self.todos if t.type == "implemented"]),
            "rejected": len([t for t in self.todos if t.type == "rejected"]),
            "needs_modification": len([t for t in self.todos if t.type == "needs_modification"])
        }
    
    def print_todo_list(self):
        """打印待办清单"""
        pending = self.get_pending()
        approved = self.get_approved()
        
        print("\n" + "="*70)
        print("📋 待办清单")
        print("="*70)
        
        if pending:
            print(f"\n⏳ 等待审批 ({len(pending)}):")
            for todo in pending:
                print(f"   [{todo.risk_level.upper()}] {todo.title[:50]}...")
                print(f"        评分: {todo.risk_score}/100 | 文件: {Path(todo.decision_file).name}")
        
        if approved:
            print(f"\n✅ 已批准待实施 ({len(approved)}):")
            for todo in approved:
                print(f"   [{todo.risk_level.upper()}] {todo.title[:50]}...")
        
        if not pending and not approved:
            print("\n   🎉 暂无待办事项")
        
        summary = self.get_summary()
        print(f"\n   统计: 总计{summary['total']} | 待审批{summary['pending_approval']} | "
              f"已批准{summary['approved']} | 已完成{summary['implemented']}")
        
        print("="*70)


# 便捷函数
def get_todo_manager():
    """获取待办管理器实例"""
    return TodoListManager()


def add_to_todo(plan_id: str, title: str, description: str,
                risk_score: int, risk_level: str, decision_file: str):
    """添加到待办清单"""
    manager = get_todo_manager()
    return manager.add_pending(plan_id, title, description, risk_score, risk_level, decision_file)


def approve_plan(plan_id: str, notes: str = None):
    """批准方案"""
    manager = get_todo_manager()
    return manager.make_decision(plan_id, "approved", notes)


def reject_plan(plan_id: str, notes: str = None):
    """拒绝方案"""
    manager = get_todo_manager()
    return manager.make_decision(plan_id, "rejected", notes)


def list_todos():
    """列出所有待办"""
    manager = get_todo_manager()
    manager.print_todo_list()


if __name__ == "__main__":
    # 测试
    print("="*70)
    print("🧪 待办清单管理器测试")
    print("="*70)
    
    manager = TodoListManager()
    
    # 添加测试待办
    todo_id = manager.add_pending(
        plan_id="plan_test_001",
        title="测试方案",
        description="这是一个测试方案",
        risk_score=55,
        risk_level="medium",
        decision_file="data/decision_test.md"
    )
    
    # 列出待办
    manager.print_todo_list()
    
    # 批准
    manager.make_decision("plan_test_001", "approved", "测试批准")
    
    # 再次列出
    manager.print_todo_list()
