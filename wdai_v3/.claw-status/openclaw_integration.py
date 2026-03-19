"""
OpenClaw 会话集成模块

自动集成到 OpenClaw 的会话系统，无需手动调用。

使用方法：
    1. 将本文件放在 .claw-status/ 目录
    2. 在 OpenClaw 初始化时导入
    3. 自动追踪所有会话消息

集成代码（添加到 OpenClaw 初始化）：
    import sys
    sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3/.claw-status')
    from openclaw_integration import setup_auto_tracking
    setup_auto_tracking()
"""

import sys
import functools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from session_hooks import get_tracker, track_user, track_assistant


class OpenClawIntegration:
    """
    OpenClaw 集成类
    
    自动包装 OpenClaw 的消息处理函数
    """
    
    def __init__(self):
        self.tracker = get_tracker()
        self._original_process_message = None
        self._enabled = False
    
    def setup(self):
        """
        设置自动追踪
        
        这将包装 OpenClaw 的消息处理，自动记录所有消息
        """
        if self._enabled:
            print("✅ 自动追踪已启用")
            return
        
        try:
            # 尝试导入 OpenClaw 的核心模块
            # 注意：这需要根据实际的 OpenClaw 结构调整
            self._patch_openclaw_handlers()
            self._enabled = True
            print("✅ OpenClaw 自动追踪已启用")
            
        except ImportError as e:
            print(f"⚠️  无法自动集成 OpenClaw: {e}")
            print("   将使用手动追踪模式")
            self._setup_manual_mode()
    
    def _patch_openclaw_handlers(self):
        """
        打补丁到 OpenClaw 消息处理器
        
        这里需要根据实际的 OpenClaw 代码结构调整
        """
        # 尝试几种可能的导入路径
        try:
            from openclaw.core.session import Session
            self._patch_session_class(Session)
        except ImportError:
            pass
        
        try:
            from openclaw.agent import Agent
            self._patch_agent_class(Agent)
        except ImportError:
            pass
    
    def _patch_session_class(self, SessionClass):
        """打补丁到 Session 类"""
        original_add_message = SessionClass.add_message
        
        @functools.wraps(original_add_message)
        def patched_add_message(self, role, content, **kwargs):
            # 先调用原始方法
            result = original_add_message(self, role, content, **kwargs)
            
            # 然后追踪消息
            if role == 'user':
                track_user(content)
            elif role == 'assistant':
                track_assistant(content)
            
            return result
        
        SessionClass.add_message = patched_add_message
        print("   ✓ 已包装 Session.add_message")
    
    def _patch_agent_class(self, AgentClass):
        """打补丁到 Agent 类"""
        original_send = AgentClass.send_message
        
        @functools.wraps(original_send)
        def patched_send(self, content, **kwargs):
            # 追踪助手消息
            track_assistant(content)
            
            # 调用原始方法
            return original_send(self, content, **kwargs)
        
        AgentClass.send_message = patched_send
        print("   ✓ 已包装 Agent.send_message")
    
    def _setup_manual_mode(self):
        """设置手动模式（当自动集成失败时）"""
        print("   手动追踪模式可用:")
        print("   - track_user(content): 追踪用户消息")
        print("   - track_assistant(content): 追踪助手消息")


def setup_auto_tracking():
    """
    设置自动追踪
    
    在 OpenClaw 初始化时调用此函数
    """
    integration = OpenClawIntegration()
    integration.setup()
    return integration


# ===== 快捷函数（用于手动集成） =====

def on_user_message(content: str):
    """
    用户消息钩子
    
    在 OpenClaw 处理用户消息时调用
    """
    track_user(content)


def on_assistant_message(content: str):
    """
    助手消息钩子
    
    在 OpenClaw 发送助手消息时调用
    """
    track_assistant(content)


def on_session_end():
    """
    会话结束钩子
    
    在 OpenClaw 会话结束时调用
    """
    import asyncio
    from session_hooks import end_current_session
    
    try:
        asyncio.run(end_current_session())
    except RuntimeError:
        # 如果已经在事件循环中
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(end_current_session())
        else:
            loop.run_until_complete(end_current_session())


# ===== 使用示例 =====

def demo_manual_integration():
    """
    演示手动集成
    
    在无法自动集成时使用此方式
    """
    print("="*70)
    print("🔌 OpenClaw 手动集成示例")
    print("="*70)
    
    print("\n在 OpenClaw 的消息处理代码中添加:")
    print("-"*70)
    print("""
# 在文件顶部导入
import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3/.claw-status')
from openclaw_integration import on_user_message, on_assistant_message, on_session_end

# 在处理用户消息时调用
async def handle_user_message(content):
    on_user_message(content)  # 追踪用户消息
    # ... 原有处理逻辑

# 在发送助手消息时调用
async def send_assistant_message(content):
    # ... 原有发送逻辑
    on_assistant_message(content)  # 追踪助手消息

# 在会话结束时调用
async def end_session():
    # ... 原有清理逻辑
    on_session_end()  # 生成摘要
    """)
    print("-"*70)
    
    print("\n✅ 集成完成！会话将自动追踪并生成摘要。")


if __name__ == "__main__":
    demo_manual_integration()
