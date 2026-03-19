"""
自动会话摘要系统 - 借鉴 Zep 的自动摘要机制

功能：
1. 从对话中提取关键信息（决策、错误、学习、TODO）
2. 生成分类摘要
3. 自动追加到 memory/daily/YYYY-MM-DD.md
4. 支持手动触发和自动触发

使用方式：
    from auto_summarize import SessionSummarizer
    
    summarizer = SessionSummarizer()
    summary = await summarizer.summarize_session(messages)
    summarizer.save_to_memory(summary)
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class SessionSummary:
    """会话摘要数据结构"""
    session_id: str
    timestamp: str
    duration_minutes: float
    
    # 分类内容
    key_decisions: List[Dict[str, str]]  # 关键决策
    errors: List[Dict[str, str]]         # 错误与纠正
    learnings: List[Dict[str, str]]      # 学习点
    todo_items: List[Dict[str, Any]]     # TODO 项
    
    # 元数据
    message_count: int
    user_message_count: int
    assistant_message_count: int
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = [
            f"\n## 会话摘要 [{self.timestamp}]",
            f"",
            f"**会话ID**: `{self.session_id}`  ",
            f"**时长**: {self.duration_minutes:.1f} 分钟  ",
            f"**消息数**: {self.message_count} (用户: {self.user_message_count}, 助手: {self.assistant_message_count})",
            f"",
        ]
        
        # 关键决策
        if self.key_decisions:
            lines.extend([
                "### 🎯 关键决策",
                ""
            ])
            for i, d in enumerate(self.key_decisions, 1):
                lines.append(f"{i}. **{d['title']}**")
                lines.append(f"   - 时间: {d.get('timestamp', 'N/A')}")
                lines.append(f"   - 详情: {d['details']}")
                lines.append("")
        
        # 错误与纠正
        if self.errors:
            lines.extend([
                "### ❌ 错误与纠正",
                ""
            ])
            for i, e in enumerate(self.errors, 1):
                lines.append(f"{i}. **{e['type']}**: {e['description']}")
                if 'correction' in e:
                    lines.append(f"   - 纠正: {e['correction']}")
                lines.append("")
        
        # 学习点
        if self.learnings:
            lines.extend([
                "### 💡 学习点",
                ""
            ])
            for i, l in enumerate(self.learnings, 1):
                lines.append(f"{i}. **{l['category']}**: {l['content']}")
                if 'source' in l:
                    lines.append(f"   - 来源: {l['source']}")
                lines.append("")
        
        # TODO
        if self.todo_items:
            lines.extend([
                "### ✅ TODO",
                ""
            ])
            for i, t in enumerate(self.todo_items, 1):
                status = "[x]" if t.get('completed', False) else "[ ]"
                lines.append(f"{i}. {status} {t['content']}")
                if 'priority' in t:
                    lines.append(f"   - 优先级: {t['priority']}")
                lines.append("")
        
        lines.append("---\n")
        
        return "\n".join(lines)


class ContentExtractor:
    """内容提取器 - 从消息中提取结构化信息"""
    
    # 决策标记词
    DECISION_MARKERS = [
        '决定', '选择', '采用', '使用', '确定', '选定',
        'decide', 'choose', 'select', 'adopt', '确定'
    ]
    
    # 错误标记词
    ERROR_MARKERS = [
        '错误', '失败', '不对', '有问题', 'bug', 'fix',
        'error', 'fail', 'wrong', 'issue', 'problem'
    ]
    
    # 学习标记词
    LEARNING_MARKERS = [
        '学到', '发现', '原来', '意识到', '明白',
        'learn', 'discover', 'realize', 'understand'
    ]
    
    # TODO 标记词
    TODO_MARKERS = [
        'TODO', 'FIXME', 'HACK', '待办', '待完成',
        'todo:', 'fixme:', 'TODO:', 'FIXME:'
    ]
    
    def extract_decisions(self, messages: List[Dict]) -> List[Dict]:
        """提取关键决策"""
        decisions = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            # 检测决策语句
            for marker in self.DECISION_MARKERS:
                if marker in content:
                    # 提取决策上下文
                    lines = content.split('\n')
                    for line in lines:
                        if marker in line and len(line) > 10:
                            decisions.append({
                                'title': self._extract_title(line),
                                'details': line.strip(),
                                'timestamp': msg.get('timestamp', 'N/A'),
                                'marker': marker
                            })
                            break
                    break  # 每个消息只记录一次
        
        # 去重
        seen = set()
        unique = []
        for d in decisions:
            key = d['title'][:30]
            if key not in seen:
                seen.add(key)
                unique.append(d)
        
        return unique[:5]  # 最多5个
    
    def extract_errors(self, messages: List[Dict]) -> List[Dict]:
        """提取错误与纠正"""
        errors = []
        
        for i, msg in enumerate(messages):
            content = msg.get('content', '')
            role = msg.get('role', '')
            
            # 检测错误（通常是用户指出或助手承认）
            if role == 'user':
                for marker in ['不对', '错误', '应该', '不是', 'wrong', 'not correct']:
                    if marker in content:
                        # 查找后续的纠正
                        correction = self._find_correction(messages, i)
                        errors.append({
                            'type': '用户纠正',
                            'description': content[:100],
                            'correction': correction,
                            'timestamp': msg.get('timestamp', 'N/A')
                        })
                        break
            
            elif role == 'assistant':
                for marker in ['错误', '修复', 'fixed', 'corrected']:
                    if marker in content and ('我' in content or 'was' in content):
                        errors.append({
                            'type': '自我纠正',
                            'description': content[:100],
                            'timestamp': msg.get('timestamp', 'N/A')
                        })
                        break
        
        return errors[:5]
    
    def extract_learnings(self, messages: List[Dict]) -> List[Dict]:
        """提取学习点"""
        learnings = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            # 检测学习标记
            for marker in self.LEARNING_MARKERS:
                if marker in content:
                    # 提取学习点
                    lines = content.split('\n')
                    for line in lines:
                        if marker in line and len(line) > 15:
                            learnings.append({
                                'category': self._categorize_learning(line),
                                'content': line.strip(),
                                'source': msg.get('timestamp', 'N/A')
                            })
                            break
                    break
        
        return learnings[:5]
    
    def extract_todos(self, messages: List[Dict]) -> List[Dict]:
        """提取 TODO 项"""
        todos = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            # 检测 TODO 标记
            for marker in self.TODO_MARKERS:
                if marker in content.upper():
                    # 提取 TODO 行
                    lines = content.split('\n')
                    for line in lines:
                        if any(m.upper() in line.upper() for m in self.TODO_MARKERS):
                            if len(line) > 5 and len(line) < 200:
                                todos.append({
                                    'content': line.strip().replace('TODO', '').replace('待办', '').strip('- '),
                                    'priority': 'high' if '重要' in line or 'urgent' in line.lower() else 'normal',
                                    'completed': '[x]' in line or '完成' in line
                                })
                    break
        
        return todos[:10]
    
    def _extract_title(self, line: str) -> str:
        """从行中提取标题"""
        # 取前30个字符作为标题
        line = line.strip()
        if len(line) > 30:
            return line[:30] + "..."
        return line
    
    def _find_correction(self, messages: List[Dict], error_idx: int) -> str:
        """查找错误后的纠正"""
        # 查找助手在错误消息后的回复
        for msg in messages[error_idx+1:]:
            if msg.get('role') == 'assistant':
                return msg.get('content', '')[:100]
        return ""
    
    def _categorize_learning(self, line: str) -> str:
        """分类学习点"""
        if any(w in line for w in ['代码', 'code', '实现', 'implement']):
            return '技术实现'
        elif any(w in line for w in ['原理', '机制', '为什么', 'how']):
            return '原理理解'
        elif any(w in line for w in ['工具', '框架', '库', 'tool', 'framework']):
            return '工具使用'
        elif any(w in line for w in ['最佳实践', '模式', 'pattern', 'best']):
            return '最佳实践'
        else:
            return '一般认知'


class SessionSummarizer:
    """会话摘要器 - 主类"""
    
    def __init__(self, memory_dir: str = None):
        """
        初始化
        
        Args:
            memory_dir: 记忆文件目录，默认 ~/.openclaw/workspace/memory/daily/
        """
        if memory_dir is None:
            self.memory_dir = Path.home() / '.openclaw' / 'workspace' / 'memory' / 'daily'
        else:
            self.memory_dir = Path(memory_dir)
        
        self.extractor = ContentExtractor()
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    async def summarize_session(
        self,
        messages: List[Dict],
        session_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> SessionSummary:
        """
        生成会话摘要
        
        Args:
            messages: 消息列表，每个消息是 {'role': 'user'|'assistant', 'content': '...', 'timestamp': '...'}
            session_id: 会话ID
            start_time: 会话开始时间
            end_time: 会话结束时间
        
        Returns:
            SessionSummary 对象
        """
        if not messages:
            return SessionSummary(
                session_id=session_id or "unknown",
                timestamp=datetime.now().isoformat(),
                duration_minutes=0,
                key_decisions=[],
                errors=[],
                learnings=[],
                todo_items=[],
                message_count=0,
                user_message_count=0,
                assistant_message_count=0
            )
        
        # 计算时间
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds() / 60
        else:
            duration = 0
        
        # 统计消息
        user_count = sum(1 for m in messages if m.get('role') == 'user')
        assistant_count = sum(1 for m in messages if m.get('role') == 'assistant')
        
        # 提取内容
        key_decisions = self.extractor.extract_decisions(messages)
        errors = self.extractor.extract_errors(messages)
        learnings = self.extractor.extract_learnings(messages)
        todo_items = self.extractor.extract_todos(messages)
        
        return SessionSummary(
            session_id=session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            duration_minutes=duration,
            key_decisions=key_decisions,
            errors=errors,
            learnings=learnings,
            todo_items=todo_items,
            message_count=len(messages),
            user_message_count=user_count,
            assistant_message_count=assistant_count
        )
    
    def save_to_memory(self, summary: SessionSummary) -> Path:
        """
        保存摘要到记忆文件
        
        Args:
            summary: 会话摘要
        
        Returns:
            保存的文件路径
        """
        # 确定文件路径
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = self.memory_dir / f"{date_str}.md"
        
        # 生成 Markdown 内容
        content = summary.to_markdown()
        
        # 追加到文件
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    async def summarize_and_save(
        self,
        messages: List[Dict],
        session_id: str = None
    ) -> tuple[SessionSummary, Path]:
        """一键生成摘要并保存"""
        summary = await self.summarize_session(messages, session_id)
        file_path = self.save_to_memory(summary)
        return summary, file_path


# ===== 使用示例 =====

async def demo():
    """演示自动会话摘要"""
    
    print("="*70)
    print("📝 自动会话摘要系统演示")
    print("="*70)
    
    summarizer = SessionSummarizer()
    
    # 模拟会话消息
    messages = [
        {
            'role': 'user',
            'content': '请帮我实现一个自动摘要系统',
            'timestamp': '2026-03-18 10:00:00'
        },
        {
            'role': 'assistant',
            'content': '好的，我决定采用 Zep 的自动摘要机制，使用异步处理。',
            'timestamp': '2026-03-18 10:01:00'
        },
        {
            'role': 'user',
            'content': '不对，应该先设计数据结构',
            'timestamp': '2026-03-18 10:02:00'
        },
        {
            'role': 'assistant',
            'content': '您说得对，我重新设计。学到了：应该先设计数据结构再实现。',
            'timestamp': '2026-03-18 10:03:00'
        },
        {
            'role': 'user',
            'content': '还需要加上 TODO 功能',
            'timestamp': '2026-03-18 10:04:00'
        },
        {
            'role': 'assistant',
            'content': '好的，我添加了 TODO 提取功能。TODO: 后续需要优化性能',
            'timestamp': '2026-03-18 10:05:00'
        }
    ]
    
    print("\n模拟会话消息:")
    for i, msg in enumerate(messages, 1):
        role_emoji = "👤" if msg['role'] == 'user' else "🤖"
        print(f"{i}. {role_emoji} [{msg['role']}] {msg['content'][:40]}...")
    
    # 生成摘要
    print("\n生成摘要中...")
    summary, file_path = await summarizer.summarize_and_save(
        messages,
        session_id="demo_session_001"
    )
    
    print(f"\n✅ 摘要已保存到: {file_path}")
    
    # 显示摘要内容
    print("\n" + "="*70)
    print("生成的摘要内容:")
    print("="*70)
    print(summary.to_markdown())
    
    # 统计
    print("\n统计信息:")
    print(f"  - 关键决策: {len(summary.key_decisions)}")
    print(f"  - 错误/纠正: {len(summary.errors)}")
    print(f"  - 学习点: {len(summary.learnings)}")
    print(f"  - TODO: {len(summary.todo_items)}")


if __name__ == "__main__":
    asyncio.run(demo())
