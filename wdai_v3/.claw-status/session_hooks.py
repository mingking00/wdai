"""
会话自动追踪与摘要钩子

集成到 OpenClaw 会话系统，实现：
1. 自动追踪当前会话消息
2. 会话结束时自动触发摘要生成
3. 支持手动触发和自动触发

使用方式：
    # 在会话开始时初始化
    from session_hooks import SessionTracker
    tracker = SessionTracker()
    
    # 每次消息自动记录（集成到消息处理流程）
    tracker.add_message(role='user', content='...')
    tracker.add_message(role='assistant', content='...')
    
    # 会话结束时自动摘要
    await tracker.end_session()
"""

import asyncio
import json
import atexit
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from auto_summarize import SessionSummarizer, SessionSummary


class SessionTracker:
    """
    会话追踪器 - 自动记录消息并在会话结束时生成摘要
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式，确保全局只有一个会话追踪器"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.messages: List[Dict[str, Any]] = []
        self.summarizer = SessionSummarizer()
        self._active = True
        self._initialized = True
        
        # 注册程序退出时的清理
        atexit.register(self._on_exit)
        
        print(f"✅ 会话追踪器已启动: {self.session_id}")
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """
        添加消息到当前会话
        
        Args:
            role: 'user' 或 'assistant'
            content: 消息内容
            metadata: 额外元数据
        """
        if not self._active:
            print("⚠️  会话已结束，消息未记录")
            return
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.messages.append(message)
        
        # 实时保存到文件（防止崩溃丢失）
        self._persist_messages()
    
    def add_user_message(self, content: str, metadata: Dict = None):
        """添加用户消息"""
        self.add_message('user', content, metadata)
    
    def add_assistant_message(self, content: str, metadata: Dict = None):
        """添加助手消息"""
        self.add_message('assistant', content, metadata)
    
    async def end_session(self, force_summary: bool = False) -> Optional[SessionSummary]:
        """
        结束会话并生成摘要
        
        Args:
            force_summary: 强制生成摘要（即使消息很少）
        
        Returns:
            SessionSummary 对象，如果消息太少返回 None
        """
        if not self._active:
            print("ℹ️  会话已经结束")
            return None
        
        # 检查是否有足够消息
        if len(self.messages) < 3 and not force_summary:
            print(f"ℹ️  消息太少 ({len(self.messages)} 条)，跳过摘要")
            self._active = False
            return None
        
        print(f"\n📝 生成会话摘要 ({len(self.messages)} 条消息)...")
        
        end_time = datetime.now()
        
        # 生成摘要
        summary = await self.summarizer.summarize_session(
            messages=self.messages,
            session_id=self.session_id,
            start_time=self.start_time,
            end_time=end_time
        )
        
        # 保存到文件
        file_path = self.summarizer.save_to_memory(summary)
        
        # 同时保存 JSON 格式（便于程序读取）
        json_path = self._save_json_summary(summary)
        
        self._active = False
        
        print(f"✅ 摘要已保存:")
        print(f"   Markdown: {file_path}")
        print(f"   JSON: {json_path}")
        print(f"\n📊 统计:")
        print(f"   关键决策: {len(summary.key_decisions)}")
        print(f"   错误/纠正: {len(summary.errors)}")
        print(f"   学习点: {len(summary.learnings)}")
        print(f"   TODO: {len(summary.todo_items)}")
        
        return summary
    
    def get_stats(self) -> Dict:
        """获取当前会话统计"""
        user_count = sum(1 for m in self.messages if m['role'] == 'user')
        assistant_count = sum(1 for m in self.messages if m['role'] == 'assistant')
        duration = (datetime.now() - self.start_time).total_seconds() / 60
        
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'duration_minutes': duration,
            'total_messages': len(self.messages),
            'user_messages': user_count,
            'assistant_messages': assistant_count,
            'is_active': self._active
        }
    
    def print_stats(self):
        """打印会话统计"""
        stats = self.get_stats()
        print(f"\n📊 会话统计 [{stats['session_id']}]")
        print(f"   时长: {stats['duration_minutes']:.1f} 分钟")
        print(f"   消息: {stats['total_messages']} 条")
        print(f"   用户: {stats['user_messages']} | 助手: {stats['assistant_messages']}")
        print(f"   状态: {'🟢 进行中' if stats['is_active'] else '🔴 已结束'}")
    
    def _persist_messages(self):
        """持久化消息到文件（防止崩溃丢失）"""
        session_file = Path.home() / '.openclaw' / 'workspace' / '.claw-status' / 'current_session.json'
        session_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'messages': self.messages,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_json_summary(self, summary: SessionSummary) -> Path:
        """保存 JSON 格式的摘要"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        json_dir = Path.home() / '.openclaw' / 'workspace' / '.claw-status' / 'summaries'
        json_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = json_dir / f"{self.session_id}.json"
        
        data = {
            'session_id': summary.session_id,
            'timestamp': summary.timestamp,
            'duration_minutes': summary.duration_minutes,
            'stats': {
                'total_messages': summary.message_count,
                'user_messages': summary.user_message_count,
                'assistant_messages': summary.assistant_message_count
            },
            'key_decisions': summary.key_decisions,
            'errors': summary.errors,
            'learnings': summary.learnings,
            'todo_items': summary.todo_items
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return json_path
    
    def _on_exit(self):
        """程序退出时的清理"""
        if self._active and len(self.messages) > 0:
            print(f"\n⚠️  程序退出，正在保存会话摘要...")
            try:
                # 使用同步方式（异步在 atexit 中可能有问题）
                import asyncio
                asyncio.run(self.end_session())
            except Exception as e:
                print(f"❌ 生成摘要失败: {e}")
                # 至少保存原始消息
                self._persist_messages()


class AutoTrackDecorator:
    """
    自动追踪装饰器
    
    装饰函数，自动记录输入和输出
    """
    
    def __init__(self, tracker: SessionTracker = None):
        self.tracker = tracker or SessionTracker()
    
    def __call__(self, func):
        """装饰函数"""
        async def async_wrapper(*args, **kwargs):
            # 记录输入
            self.tracker.add_user_message(
                content=f"调用 {func.__name__}({', '.join(map(str, args))})",
                metadata={'type': 'function_call', 'function': func.__name__}
            )
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 记录输出
            self.tracker.add_assistant_message(
                content=str(result)[:500],  # 截断长结果
                metadata={'type': 'function_result', 'function': func.__name__}
            )
            
            return result
        
        return async_wrapper


# ===== 快捷函数 =====

_tracker = None

def get_tracker() -> SessionTracker:
    """获取全局会话追踪器"""
    global _tracker
    if _tracker is None:
        _tracker = SessionTracker()
    return _tracker


def track_message(role: str, content: str):
    """快捷函数：追踪消息"""
    tracker = get_tracker()
    tracker.add_message(role, content)


def track_user(content: str):
    """快捷函数：追踪用户消息"""
    track_message('user', content)


def track_assistant(content: str):
    """快捷函数：追踪助手消息"""
    track_message('assistant', content)


async def end_current_session(force: bool = False) -> Optional[SessionSummary]:
    """快捷函数：结束当前会话"""
    tracker = get_tracker()
    return await tracker.end_session(force_summary=force)


# ===== 演示 =====

async def demo_auto_track():
    """演示自动追踪"""
    
    print("="*70)
    print("🎯 会话自动追踪演示")
    print("="*70)
    
    # 获取追踪器（会自动初始化）
    tracker = get_tracker()
    
    # 模拟对话
    print("\n模拟对话...")
    
    track_user("请帮我研究 Attention Residuals 论文")
    await asyncio.sleep(0.5)
    
    track_assistant("好的，我决定搜索 Kimi 的 Attention Residuals 技术报告。")
    await asyncio.sleep(0.5)
    
    track_user("不对，应该先理解核心思想")
    await asyncio.sleep(0.5)
    
    track_assistant("您说得对，我学到了：应该先理解核心思想再搜索细节。")
    await asyncio.sleep(0.5)
    
    track_user("实现出来")
    await asyncio.sleep(0.5)
    
    track_assistant("好的，我实现了 AttentionBasedOrchestrator。TODO: 后续需要添加测试。")
    await asyncio.sleep(0.5)
    
    # 查看统计
    tracker.print_stats()
    
    # 结束会话
    print("\n结束会话并生成摘要...")
    summary = await end_current_session(force=True)
    
    if summary:
        print("\n生成的摘要内容:")
        print("="*70)
        print(summary.to_markdown())


if __name__ == "__main__":
    asyncio.run(demo_auto_track())
