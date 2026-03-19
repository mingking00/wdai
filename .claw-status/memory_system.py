#!/usr/bin/env python3
"""
WDai Enhanced Memory System - 集成模块
阶段B完成：完整架构升级

集成组件:
1. VectorMemoryStore - 向量存储 (已完成)
2. DynamicCompressionEngine - 动态压缩 (已完成)
3. SessionStateManager - 会话状态 (已完成)
4. SkillFastPath - 技能快速路径 (已完成)

使用方式:
    from memory_system import get_memory_system
    
    memory = get_memory_system()
    memory.on_startup()  # 启动时恢复状态
    
    # 对话中自动压缩
    memory.on_user_message("用户输入")
    memory.on_assistant_response("助手回复")
    
    # 查询时走快速路径
    response = memory.query_with_fast_path("问题")
    
    memory.on_shutdown()  # 关闭时保存状态
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from vector_memory import VectorMemoryStore, MemorySearchEnhanced
from dynamic_compression import DynamicCompressionEngine, CompressionManager
from session_state import SessionStateManager, WDaiState
from skill_fast_path import SkillFastPath, FastPathLLMWrapper
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class WDaiMemorySystem:
    """
    wdai增强记忆系统
    
    统一入口，协调所有记忆组件
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
        
        print("\n" + "="*60)
        print("WDai Enhanced Memory System 初始化")
        print("="*60)
        
        # 1. 向量存储 (阶段A)
        print("\n1. 初始化向量存储...")
        self.vector_search = MemorySearchEnhanced()
        
        # 2. 动态压缩 (阶段B)
        print("2. 初始化动态压缩引擎...")
        self.compression = CompressionManager()
        
        # 3. 会话状态 (阶段B)
        print("3. 初始化会话状态管理...")
        self.session_state = SessionStateManager()
        
        # 4. 技能快速路径 (阶段B)
        print("4. 初始化技能快速路径...")
        self.fast_path = FastPathLLMWrapper()
        
        self._initialized = True
        
        print("\n✅ 所有组件初始化完成")
        print("="*60)
    
    # ==================== 生命周期管理 ====================
    
    def on_startup(self) -> Dict:
        """系统启动时调用"""
        print("\n🚀 系统启动 - 恢复上下文")
        
        # 创建新会话
        self.session_state.create_session()
        
        # 构建恢复上下文
        recovery = self.session_state.build_recovery_context()
        
        # 显示状态
        stats = self.get_stats()
        print(f"\n📊 当前状态:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        return recovery
    
    def on_shutdown(self):
        """系统关闭时调用"""
        print("\n🛑 系统关闭 - 保存状态")
        
        # 保存会话
        self.session_state.save_session()
        
        print("✅ 状态已保存，下次启动可恢复")
    
    # ==================== 对话流程集成 ====================
    
    def on_user_message(self, content: str):
        """用户消息回调"""
        # 1. 添加到压缩引擎
        event = self.compression.on_user_message(content)
        
        # 2. 更新会话状态
        self.session_state.update_session(
            working_memory_turns=len(self.compression.engine.working_memory)
        )
        
        return event
    
    def on_assistant_response(self, content: str, metadata: Dict = None):
        """助手回复回调"""
        # 1. 添加到压缩引擎
        event = self.compression.on_assistant_message(content, metadata)
        
        # 2. 更新会话状态
        turns = len(self.compression.engine.working_memory)
        self.session_state.update_session(
            working_memory_turns=turns
        )
        
        # 3. 学习事实 (简化：自动提取关键词)
        if metadata and metadata.get('learn_fact'):
            self.session_state.learn_fact(
                metadata['learn_fact'],
                metadata.get('category', 'general'),
                metadata.get('confidence', 0.7)
            )
        
        return event
    
    def query_with_fast_path(self, query: str) -> str:
        """
        带快速路径的查询
        
        流程:
        1. 检查快速路径缓存
        2. 命中: 直接返回
        3. 未命中: 从向量存储检索记忆 + LLM生成
        4. 缓存响应
        """
        # 1. 检查快速路径
        cached = self.fast_path.fast_path.lookup(query)
        if cached:
            response, confidence, metadata = cached
            print(f"⚡ 快速路径命中 (置信度: {confidence:.2f})")
            return response
        
        # 2. 从向量存储检索相关记忆
        print(f"🔍 检索相关记忆...")
        memories = self.vector_search.search(query, top_k=3)
        
        # 3. 构建上下文 (简化：直接返回搜索结果)
        if memories and memories[0]['score'] > 0.5:
            context = "\n".join([
                f"- [{m['score']:.2f}] {m['content'][:100]}..."
                for m in memories[:2]
            ])
            response = f"基于记忆检索:\n{context}"
        else:
            response = f"[需要LLM生成响应] {query}"
        
        # 4. 缓存响应
        self.fast_path.fast_path.cache_response(query, response, confidence=0.7)
        
        return response
    
    # ==================== 高级功能 ====================
    
    def search_memories(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索记忆"""
        return self.vector_search.search(query, top_k=top_k)
    
    def force_compress(self):
        """强制压缩当前工作记忆"""
        return self.compression.force_compress()
    
    def add_pending_task(self, description: str):
        """添加待办事项"""
        if self.session_state.current_session:
            self.session_state.current_session.pending_tasks.append({
                "description": description,
                "created_at": datetime.now().isoformat(),
                "completed": False
            })
    
    def complete_task(self, description: str):
        """完成任务"""
        if self.session_state.current_session:
            for task in self.session_state.current_session.pending_tasks:
                if task["description"] == description:
                    task["completed"] = True
                    task["completed_at"] = datetime.now().isoformat()
                    break
    
    def learn_user_fact(self, fact: str, category: str = "general"):
        """学习用户事实"""
        self.session_state.learn_fact(fact, category, confidence=0.8)
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> Dict:
        """获取系统统计"""
        return {
            "vector_memories": self.vector_search.vector_store.get_stats().get('vectors_count', 0),
            "compression_turns": len(self.compression.engine.working_memory),
            "fast_path_hit_rate": self.fast_path.fast_path.get_stats().get('hit_rate', 0),
            "pending_tasks": len(self.session_state.current_session.pending_tasks) if self.session_state.current_session else 0,
            "user_preferences": len(self.session_state.user_profile.preferences) if self.session_state.user_profile else 0,
        }
    
    def print_full_stats(self):
        """打印完整统计"""
        print("\n" + "="*60)
        print("WDai Memory System - 完整统计")
        print("="*60)
        
        # 向量存储
        print("\n📦 向量存储:")
        vs_stats = self.vector_search.vector_store.get_stats()
        for key, value in vs_stats.items():
            print(f"   {key}: {value}")
        
        # 动态压缩
        print("\n🗜️ 动态压缩:")
        comp_stats = self.compression.engine.get_stats()
        for key, value in comp_stats.items():
            print(f"   {key}: {value}")
        
        # 快速路径
        print("\n⚡ 技能快速路径:")
        fp_stats = self.fast_path.fast_path.get_stats()
        for key, value in fp_stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2%}" if 'rate' in key else f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        
        # 会话状态
        print("\n💾 会话状态:")
        ss_stats = self.session_state.get_stats()
        for key, value in ss_stats.items():
            print(f"   {key}: {value}")
        
        print("="*60)


# ==================== 全局访问点 ====================

_memory_system = None

def get_memory_system() -> WDaiMemorySystem:
    """获取全局记忆系统实例"""
    global _memory_system
    if _memory_system is None:
        _memory_system = WDaiMemorySystem()
    return _memory_system


# ==================== 测试 ====================

if __name__ == "__main__":
    print("="*60)
    print("WDai Enhanced Memory System - 集成测试")
    print("="*60)
    
    # 获取系统实例
    memory = get_memory_system()
    
    # 1. 启动恢复
    print("\n1. 系统启动")
    recovery = memory.on_startup()
    print(f"   恢复信息: {recovery.get('greeting', '无')}")
    
    # 2. 模拟对话
    print("\n2. 模拟对话流程")
    
    conversation = [
        ("user", "帮我查一下GitHub仓库状态"),
        ("assistant", "好的，正在检查GitHub仓库... 发现3个仓库需要更新。", {"learn_fact": "用户关注GitHub仓库状态"}),
        ("user", "具体是哪三个？"),
        ("assistant", "wdai-core、vector-memory、session-state 这三个仓库有待处理更新。"),
        ("user", "先更新vector-memory"),
        ("assistant", "好的，开始更新vector-memory仓库... 更新完成。", {"learn_fact": "用户优先处理vector-memory"}),
    ]
    
    for role, content, *meta in conversation:
        print(f"\n   {'👤' if role == 'user' else '🤖'} {content[:50]}...")
        
        if role == "user":
            event = memory.on_user_message(content)
            if event:
                print(f"   ⚡ 触发压缩: {event.event_type}")
        else:
            metadata = meta[0] if meta else {}
            event = memory.on_assistant_response(content, metadata)
            if event:
                print(f"   ⚡ 触发压缩: {event.event_type}")
    
    # 3. 测试快速路径
    print("\n3. 测试快速路径查询")
    queries = [
        "GitHub仓库状态",
        "记忆架构",
        "向量检索",
    ]
    
    for query in queries:
        print(f"\n   查询: '{query}'")
        response = memory.query_with_fast_path(query)
        print(f"   响应: {response[:80]}...")
    
    # 4. 添加上下文恢复测试
    print("\n4. 添加上下文信息")
    memory.session_state.update_session(
        current_topic="GitHub仓库更新",
        active_entities=["wdai-core", "vector-memory", "session-state"],
        context_summary="正在处理GitHub仓库更新任务"
    )
    memory.add_pending_task("更新wdai-core仓库")
    memory.add_pending_task("更新session-state仓库")
    
    # 5. 打印统计
    print("\n5. 系统统计")
    memory.print_full_stats()
    
    # 6. 关闭保存
    print("\n6. 系统关闭")
    memory.on_shutdown()
    
    # 7. 模拟重启恢复
    print("\n7. 模拟重启 - 恢复测试")
    memory2 = get_memory_system()
    recovery2 = memory2.on_startup()
    print(f"   恢复信息: {recovery2.get('greeting', '无')}")
    print(f"   上次话题: {recovery2.get('context_summary', '无')[:60] if recovery2.get('context_summary') else '无'}...")
    print(f"   待办事项: {len(recovery2.get('pending_tasks', []))}个")
    
    print("\n" + "="*60)
    print("✅ 集成测试完成")
    print("="*60)
