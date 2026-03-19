#!/usr/bin/env python3
"""
会话结束自动摘要钩子

使用方法：
    # 在会话结束时调用
    python3 .claw-status/summarize_session_end.py

或者 Python 代码中：
    from summarize_session_end import auto_summarize_current_session
    await auto_summarize_current_session()
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from auto_summarize import SessionSummarizer


async def auto_summarize_current_session():
    """
    自动摘要当前会话
    
    从当前会话历史中提取消息并生成摘要
    """
    summarizer = SessionSummarizer()
    
    # 尝试从当前会话读取消息
    # 这里模拟从会话历史读取，实际使用时应从真实的会话存储读取
    messages = []
    
    # 如果有会话历史文件，读取它
    session_file = Path.home() / '.openclaw' / 'workspace' / '.claw-status' / 'current_session.json'
    if session_file.exists():
        with open(session_file, 'r') as f:
            data = json.load(f)
            messages = data.get('messages', [])
    
    if not messages:
        print("ℹ️  当前会话没有消息需要摘要")
        return
    
    # 生成摘要
    summary, file_path = await summarizer.summarize_and_save(
        messages,
        session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    print(f"✅ 会话摘要已保存: {file_path}")
    print(f"\n摘要统计:")
    print(f"  - 关键决策: {len(summary.key_decisions)}")
    print(f"  - 错误/纠正: {len(summary.errors)}")
    print(f"  - 学习点: {len(summary.learnings)}")
    print(f"  - TODO: {len(summary.todo_items)}")
    
    return summary, file_path


def manual_summarize(messages: list) -> str:
    """
    手动摘要 - 从消息列表生成
    
    用于在代码中手动调用
    
    Args:
        messages: 消息列表，格式 [{role: 'user'|'assistant', content: '...'}]
    
    Returns:
        摘要 Markdown 字符串
    """
    import asyncio
    
    async def _summarize():
        summarizer = SessionSummarizer()
        summary = await summarizer.summarize_session(messages)
        return summary.to_markdown()
    
    return asyncio.run(_summarize())


if __name__ == "__main__":
    asyncio.run(auto_summarize_current_session())
