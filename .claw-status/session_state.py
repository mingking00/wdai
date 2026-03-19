#!/usr/bin/env python3
"""
WDai Session State Manager
跨会话状态持久化与恢复

功能:
1. 自动保存会话状态 (每5分钟)
2. 重启后自动恢复上下文
3. 用户画像持久化
4. 待办事项追踪
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import threading
import time


@dataclass
class SessionCheckpoint:
    """会话检查点"""
    session_id: str
    user_id: str
    created_at: str
    last_active: str
    current_topic: Optional[str]
    active_entities: List[str]
    pending_tasks: List[Dict]
    context_summary: str
    working_memory_turns: int
    compression_stats: Dict


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    preferences: Dict[str, Any]
    interaction_patterns: Dict[str, Any]
    learned_facts: List[Dict]
    updated_at: str


class SessionStateManager:
    """会话状态管理器"""
    
    def __init__(
        self,
        storage_dir: str = ".claw-status/session_state",
        auto_save_interval: int = 300  # 5分钟
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.sessions_dir = self.storage_dir / "sessions"
        self.users_dir = self.storage_dir / "users"
        self.sessions_dir.mkdir(exist_ok=True)
        self.users_dir.mkdir(exist_ok=True)
        
        self.current_session: Optional[SessionCheckpoint] = None
        self.user_profile: Optional[UserProfile] = None
        self._lock = threading.Lock()
        
        # 启动自动保存
        self._auto_save_thread = threading.Thread(
            target=self._auto_save_loop,
            args=(auto_save_interval,),
            daemon=True
        )
        self._auto_save_thread.start()
        
        print(f"✅ SessionStateManager 初始化完成")
        print(f"   存储路径: {self.storage_dir}")
        print(f"   自动保存: 每{auto_save_interval}秒")
    
    # ==================== 会话管理 ====================
    
    def create_session(self, user_id: str = "default") -> SessionCheckpoint:
        """创建新会话"""
        session_id = f"sess_{int(time.time())}_{user_id[:8]}"
        now = datetime.now().isoformat()
        
        checkpoint = SessionCheckpoint(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_active=now,
            current_topic=None,
            active_entities=[],
            pending_tasks=[],
            context_summary="",
            working_memory_turns=0,
            compression_stats={}
        )
        
        with self._lock:
            self.current_session = checkpoint
        
        # 加载用户画像
        self._load_user_profile(user_id)
        
        return checkpoint
    
    def update_session(self, **kwargs):
        """更新会话状态"""
        with self._lock:
            if self.current_session:
                for key, value in kwargs.items():
                    if hasattr(self.current_session, key):
                        setattr(self.current_session, key, value)
                self.current_session.last_active = datetime.now().isoformat()
    
    def save_session(self):
        """手动保存当前会话"""
        with self._lock:
            if self.current_session:
                self._save_checkpoint_to_disk(self.current_session)
                if self.user_profile:
                    self._save_user_profile_to_disk(self.user_profile)
                print(f"✅ 会话已保存: {self.current_session.session_id}")
    
    def _save_checkpoint_to_disk(self, checkpoint: SessionCheckpoint):
        """保存检查点到磁盘"""
        file_path = self.sessions_dir / f"{checkpoint.session_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(checkpoint), f, ensure_ascii=False, indent=2)
    
    def load_session(self, session_id: str) -> Optional[SessionCheckpoint]:
        """加载会话"""
        file_path = self.sessions_dir / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return SessionCheckpoint(**data)
    
    def get_last_session(self, user_id: str = "default") -> Optional[SessionCheckpoint]:
        """获取用户最近会话"""
        sessions = []
        
        for file_path in self.sessions_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('user_id') == user_id:
                    sessions.append(SessionCheckpoint(**data))
            except:
                continue
        
        if not sessions:
            return None
        
        # 按最后活跃时间排序
        sessions.sort(key=lambda x: x.last_active, reverse=True)
        return sessions[0]
    
    # ==================== 用户画像管理 ====================
    
    def _load_user_profile(self, user_id: str):
        """加载用户画像"""
        file_path = self.users_dir / f"{user_id}.json"
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.user_profile = UserProfile(**data)
        else:
            # 创建新的
            self.user_profile = UserProfile(
                user_id=user_id,
                preferences={},
                interaction_patterns={},
                learned_facts=[],
                updated_at=datetime.now().isoformat()
            )
    
    def _save_user_profile_to_disk(self, profile: UserProfile):
        """保存用户画像"""
        file_path = self.users_dir / f"{profile.user_id}.json"
        profile.updated_at = datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(profile), f, ensure_ascii=False, indent=2)
    
    def update_preference(self, key: str, value: Any, confidence: float = 1.0):
        """更新用户偏好"""
        if not self.user_profile:
            return
        
        self.user_profile.preferences[key] = {
            "value": value,
            "confidence": confidence,
            "updated_at": datetime.now().isoformat()
        }
    
    def learn_fact(self, fact: str, category: str = "general", confidence: float = 0.8):
        """学习关于用户的事实"""
        if not self.user_profile:
            return
        
        # 检查是否已存在
        existing = [f for f in self.user_profile.learned_facts if f["fact"] == fact]
        
        if existing:
            existing[0]["confidence"] = max(existing[0]["confidence"], confidence)
            existing[0]["updated_at"] = datetime.now().isoformat()
        else:
            self.user_profile.learned_facts.append({
                "fact": fact,
                "category": category,
                "confidence": confidence,
                "learned_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好"""
        if not self.user_profile:
            return default
        
        pref = self.user_profile.preferences.get(key)
        if pref:
            return pref.get("value", default)
        return default
    
    # ==================== 上下文恢复 ====================
    
    def build_recovery_context(self) -> Dict:
        """
        构建恢复上下文
        用于会话重启后恢复状态
        """
        context = {
            "has_previous_session": False,
            "greeting": "你好！",
            "context_summary": None,
            "pending_tasks": [],
            "preferences": {},
            "learned_facts": []
        }
        
        if not self.current_session:
            return context
        
        user_id = self.current_session.user_id
        
        # 获取最近的会话
        last_session = self.get_last_session(user_id)
        
        if last_session and last_session.session_id != self.current_session.session_id:
            context["has_previous_session"] = True
            
            # 检查时间间隔
            try:
                last_time = datetime.fromisoformat(last_session.last_active)
                now = datetime.now()
                hours_ago = (now - last_time).total_seconds() / 3600
                
                if hours_ago < 1:
                    context["greeting"] = "继续我们刚才的话题？"
                elif hours_ago < 24:
                    context["greeting"] = f"欢迎回来！你离开{int(hours_ago)}小时了。"
                else:
                    context["greeting"] = f"好久不见！上次会话是{int(hours_ago/24)}天前。"
                
                # 添加上下文摘要
                if last_session.context_summary:
                    context["context_summary"] = last_session.context_summary
                
                # 添加待办事项
                pending = [t for t in last_session.pending_tasks if not t.get("completed")]
                if pending:
                    context["pending_tasks"] = pending
            except:
                pass
        
        # 添加用户偏好
        if self.user_profile:
            context["preferences"] = {
                k: v.get("value") for k, v in self.user_profile.preferences.items()
            }
            
            # 添加高置信度事实
            facts = [
                f for f in self.user_profile.learned_facts
                if f.get("confidence", 0) > 0.6
            ]
            context["learned_facts"] = facts[:5]  # 最多5个
        
        return context
    
    def generate_recovery_summary(self) -> str:
        """生成恢复摘要文本"""
        context = self.build_recovery_context()
        
        if not context["has_previous_session"]:
            return "你好！我是wdai，准备好开始工作了吗？"
        
        parts = [context["greeting"]]
        
        # 添加上下文
        if context["context_summary"]:
            parts.append(f"\n\n上次我们在讨论：{context['context_summary'][:100]}...")
        
        # 添加待办
        if context["pending_tasks"]:
            task_list = "\n".join([
                f"- {t.get('description', '未命名任务')}"
                for t in context["pending_tasks"][:3]
            ])
            parts.append(f"\n\n待办事项：\n{task_list}")
        
        return "\n".join(parts)
    
    # ==================== 自动保存 ====================
    
    def _auto_save_loop(self, interval: int):
        """自动保存循环"""
        while True:
            time.sleep(interval)
            try:
                self.save_session()
            except Exception as e:
                print(f"⚠️ 自动保存失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "current_session": self.current_session.session_id if self.current_session else None,
            "user_id": self.current_session.user_id if self.current_session else None,
            "preferences_count": len(self.user_profile.preferences) if self.user_profile else 0,
            "learned_facts_count": len(self.user_profile.learned_facts) if self.user_profile else 0,
        }


# ============ 系统集成 ============

class WDaiState:
    """
    wdai全局状态管理
    单例模式，系统级访问点
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.session_manager = SessionStateManager()
        self._initialized = True
    
    def on_startup(self):
        """系统启动时调用"""
        print("\n" + "="*60)
        print("WDai 状态恢复")
        print("="*60)
        
        # 创建新会话
        checkpoint = self.session_manager.create_session()
        print(f"✅ 新会话已创建: {checkpoint.session_id[:20]}...")
        
        # 尝试恢复上下文
        recovery = self.session_manager.build_recovery_context()
        
        if recovery["has_previous_session"]:
            print(f"\n📋 发现之前的会话")
            print(f"   恢复信息: {recovery['greeting']}")
            
            if recovery["context_summary"]:
                print(f"   上次话题: {recovery['context_summary'][:60]}...")
            
            if recovery["pending_tasks"]:
                print(f"   待办事项: {len(recovery['pending_tasks'])}个")
            
            if recovery["learned_facts"]:
                print(f"   已知事实: {len(recovery['learned_facts'])}个")
        else:
            print("\n📋 没有找到之前的会话")
        
        print("="*60)
        
        return recovery
    
    def on_shutdown(self):
        """系统关闭时调用"""
        print("\n🔄 保存会话状态...")
        self.session_manager.save_session()
        print("✅ 会话已保存，下次启动可恢复")


# ============ 测试 ============

if __name__ == "__main__":
    print("="*60)
    print("Session State Manager - 测试")
    print("="*60)
    
    # 创建管理器
    manager = SessionStateManager()
    
    # 创建会话
    print("\n1. 创建新会话")
    checkpoint = manager.create_session("test_user")
    print(f"   会话ID: {checkpoint.session_id[:30]}...")
    
    # 更新状态
    print("\n2. 更新会话状态")
    manager.update_session(
        current_topic="分层记忆架构",
        active_entities=["Layer 3", "Layer 2", "向量存储"],
        context_summary="正在实现分层记忆架构的向量存储部分"
    )
    
    # 添加待办
    checkpoint.pending_tasks = [
        {"description": "完成动态压缩引擎", "completed": False},
        {"description": "测试向量检索", "completed": True},
        {"description": "集成到系统", "completed": False}
    ]
    
    # 更新用户偏好
    print("\n3. 更新用户偏好")
    manager.update_preference("code_style", "简洁优先", confidence=1.0)
    manager.update_preference("response_format", "结构化", confidence=0.9)
    
    # 学习事实
    print("\n4. 学习用户事实")
    manager.learn_fact("用户对AI架构底层原理感兴趣", "interests", 0.9)
    manager.learn_fact("用户偏好Python开发", "skills", 0.8)
    
    # 手动保存
    print("\n5. 手动保存")
    manager.save_session()
    
    # 显示统计
    print("\n6. 统计信息")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # 模拟重启 - 加载最后会话
    print("\n7. 模拟重启 - 恢复会话")
    last_session = manager.get_last_session("test_user")
    if last_session:
        print(f"   找到会话: {last_session.session_id[:30]}...")
        print(f"   上次话题: {last_session.current_topic}")
        print(f"   活跃实体: {', '.join(last_session.active_entities)}")
    
    # 生成恢复摘要
    print("\n8. 生成恢复摘要")
    manager.current_session = checkpoint  # 设置当前会话
    summary = manager.generate_recovery_summary()
    print(f"\n{summary}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)
