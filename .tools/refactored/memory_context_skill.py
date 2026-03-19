#!/usr/bin/env python3
"""
Memory Context Skill - CLI-Anything 风格重构
记忆上下文管理

用法: python3 memory_context_skill.py [进入REPL模式]
     或在 REPL 中使用: memory.add <内容>, memory.retrieve <查询> 等
"""

import sys
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import re

# 导入核心框架
sys.path.insert(0, str(Path(__file__).parent))
from skill_generator import (
    command, CommandMetadata, arg, opt,
    CommandContext, CommandResult,
    ArgumentType,
    ReplSkin, CommandRegistry, SessionManager
)

# 配置
MEMORY_DIR = Path("/root/.openclaw/workspace") / ".memory-context"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class ContextEntry:
    """上下文条目"""
    id: str
    content: str
    source: str
    importance: float
    tags: List[str]
    timestamp: str
    session_id: str
    access_count: int = 0
    last_accessed: str = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ContextEntry":
        return cls(**data)


# ============================================================================
# 持久化存储
# ============================================================================

class MemoryStore:
    """内存持久化存储"""
    
    def __init__(self):
        self.context_file = MEMORY_DIR / "current_context.json"
        self.index_file = MEMORY_DIR / "memory_index.json"
    
    def load_entries(self) -> List[ContextEntry]:
        """加载条目"""
        if not self.context_file.exists():
            return []
        
        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ContextEntry.from_dict(e) for e in data.get("entries", [])]
        except:
            return []
    
    def save_entries(self, entries: List[ContextEntry]):
        """保存条目"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in entries]
        }
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_index(self) -> Dict:
        """加载索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"entries": [], "tags": {}, "sessions": []}
    
    def save_index(self, index: Dict):
        """保存索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)


# ============================================================================
# 核心管理器
# ============================================================================

class MemoryManager:
    """内存管理器"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.store = MemoryStore()
        self.entries: List[ContextEntry] = self.store.load_entries()
        self.index = self.store.load_index()
    
    def add(self, content: str, source: str = "conversation",
            importance: float = 5.0, tags: List[str] = None) -> str:
        """添加条目"""
        entry_id = hashlib.md5(f"{content}{datetime.now()}".encode()).hexdigest()[:8]
        
        entry = ContextEntry(
            id=entry_id,
            content=content[:2000],
            source=source,
            importance=max(0, min(10, importance)),
            tags=tags or self._extract_tags(content),
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id
        )
        
        self.entries.append(entry)
        self._update_index(entry)
        self.store.save_entries(self.entries)
        
        return entry_id
    
    def retrieve(self, query: str, top_k: int = 5,
                 min_relevance: float = 0.3) -> List[Tuple[ContextEntry, float]]:
        """检索相关条目"""
        query_terms = set(self._tokenize(query))
        scored = []
        
        for entry in self.entries:
            entry_terms = set(self._tokenize(entry.content))
            tag_terms = set(tag.lower() for tag in entry.tags)
            
            # 计算相似度
            overlap = len(query_terms & entry_terms)
            union = len(query_terms | entry_terms)
            text_sim = overlap / union if union > 0 else 0
            
            tag_overlap = len(query_terms & tag_terms)
            tag_score = tag_overlap / len(query_terms) if query_terms else 0
            
            relevance = text_sim * 0.6 + tag_score * 0.4
            importance_weight = entry.importance / 10.0
            
            age_hours = self._get_age_hours(entry.timestamp)
            recency = max(0, 1 - age_hours / 168)
            access_score = min(entry.access_count / 10, 1.0)
            
            score = (relevance * 0.4 + importance_weight * 0.25 +
                    recency * 0.2 + access_score * 0.15)
            
            if score >= min_relevance:
                scored.append((entry, score))
                entry.access_count += 1
                entry.last_accessed = datetime.now().isoformat()
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
    
    def get_context_for_prompt(self, query: str, max_chars: int = 2000) -> str:
        """获取格式化的上下文"""
        results = self.retrieve(query, top_k=5)
        if not results:
            return ""
        
        parts = ["\n### 相关上下文\n"]
        current_length = 0
        
        for entry, score in results:
            entry_text = f"[{entry.source}] {entry.content[:300]}... (相关度: {score:.2f})\n"
            if current_length + len(entry_text) > max_chars:
                break
            parts.append(entry_text)
            current_length += len(entry_text)
        
        return "".join(parts)
    
    def summarize(self) -> Dict:
        """总结当前状态"""
        if not self.entries:
            return {"message": "无记录"}
        
        by_source = {}
        for entry in self.entries:
            by_source.setdefault(entry.source, []).append(entry)
        
        all_tags = []
        for entry in self.entries:
            all_tags.extend(entry.tags)
        tag_freq = {}
        for tag in all_tags:
            tag_freq[tag] = tag_freq.get(tag, 0) + 1
        top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_entries": len(self.entries),
            "by_source": {k: len(v) for k, v in by_source.items()},
            "top_tags": top_tags,
            "avg_importance": sum(e.importance for e in self.entries) / len(self.entries),
            "time_range": {
                "start": min(e.timestamp for e in self.entries),
                "end": max(e.timestamp for e in self.entries)
            }
        }
    
    def archive(self, name: str = None) -> str:
        """归档当前内容"""
        archive_name = name or f"session_{self.session_id}"
        archive_file = MEMORY_DIR / f"{archive_name}.json"
        
        data = {
            "name": archive_name,
            "session_id": self.session_id,
            "archived_at": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in self.entries]
        }
        
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.entries = []
        self.store.save_entries(self.entries)
        
        return str(archive_file)
    
    def search_archive(self, query: str) -> List[Dict]:
        """搜索归档"""
        results = []
        for archive_file in MEMORY_DIR.glob("session_*.json"):
            try:
                with open(archive_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    content = json.dumps(data).lower()
                    if query.lower() in content:
                        results.append({
                            "file": str(archive_file),
                            "name": data.get("name"),
                            "archived_at": data.get("archived_at"),
                            "entry_count": len(data.get("entries", []))
                        })
            except:
                continue
        return results
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "current_entries": len(self.entries),
            "total_indexed": len(self.index.get("entries", [])),
            "unique_tags": len(self.index.get("tags", {})),
            "sessions": len(self.index.get("sessions", []))
        }
    
    def clear(self):
        """清空当前内容"""
        self.entries = []
        self.store.save_entries(self.entries)
    
    def _update_index(self, entry: ContextEntry):
        """更新索引"""
        self.index["entries"].append({
            "id": entry.id,
            "source": entry.source,
            "timestamp": entry.timestamp
        })
        for tag in entry.tags:
            self.index["tags"].setdefault(tag, []).append(entry.id)
        if entry.session_id not in self.index["sessions"]:
            self.index["sessions"].append(entry.session_id)
        self.store.save_index(self.index)
    
    def _extract_tags(self, content: str) -> List[str]:
        """提取标签"""
        keywords = [
            "task", "todo", "decision", "important", "urgent",
            "research", "code", "bug", "feature", "meeting",
            "idea", "question", "answer", "plan", "review"
        ]
        content_lower = content.lower()
        tags = [kw for kw in keywords if kw in content_lower]
        return tags[:3]
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]+\b', text.lower())
        return [w for w in words if len(w) > 1]
    
    def _get_age_hours(self, timestamp: str) -> float:
        """获取年龄（小时）"""
        try:
            created = datetime.fromisoformat(timestamp)
            age = datetime.now() - created
            return age.total_seconds() / 3600
        except:
            return 0.0


# ============================================================================
# CLI 命令定义
# ============================================================================

@command(CommandMetadata(
    name="memory.add",
    description="添加记忆条目",
    category="memory",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class MemoryAddCommand:
    """添加条目"""
    
    content = arg("content", ArgumentType.STRING, help="内容文本")
    source = opt("source", ArgumentType.STRING, default="conversation",
                 help="来源: conversation, file, tool_result")
    importance = opt("importance", ArgumentType.FLOAT, default=5.0,
                     help="重要性 0-10")
    tags = opt("tags", ArgumentType.STRING, default=None,
               help="标签，逗号分隔")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        # 从 session 获取 manager 或创建新的
        memory_state = ctx.session.get("memory", {})
        manager = MemoryManager(ctx.session.session_id)
        manager.entries = memory_state.get("entries", [])
        
        content = ctx.args.get("content", "")
        tags = ctx.options.get("tags")
        tag_list = tags.split(",") if tags else None
        
        entry_id = manager.add(
            content=content,
            source=ctx.options.get("source", "conversation"),
            importance=float(ctx.options.get("importance", 5.0)),
            tags=tag_list
        )
        
        # 保存回 session
        ctx.session.set("memory", {
            "entries": [e.to_dict() for e in manager.entries],
            "last_added": entry_id
        })
        
        return CommandResult(
            success=True,
            message=f"已添加条目: {entry_id}",
            data={"entry_id": entry_id, "content_preview": content[:50]}
        )


@command(CommandMetadata(
    name="memory.retrieve",
    description="检索相关记忆",
    category="memory",
    modifies_state=False,
    requires_session=True
))
class MemoryRetrieveCommand:
    """检索条目"""
    
    query = arg("query", ArgumentType.STRING, help="查询文本")
    top_k = opt("top-k", ArgumentType.INTEGER, default=5, help="返回数量")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        manager = MemoryManager(ctx.session.session_id)
        memory_state = ctx.session.get("memory", {})
        if memory_state.get("entries"):
            manager.entries = [ContextEntry.from_dict(e) for e in memory_state["entries"]]
        
        results = manager.retrieve(
            ctx.args.get("query", ""),
            top_k=int(ctx.options.get("top-k", 5))
        )
        
        return CommandResult(
            success=True,
            data={
                "results": [
                    {"id": e.id, "content": e.content[:100], "score": s}
                    for e, s in results
                ],
                "count": len(results)
            }
        )


@command(CommandMetadata(
    name="memory.context",
    description="获取格式化的上下文",
    category="memory",
    modifies_state=False,
    requires_session=True
))
class MemoryContextCommand:
    """获取上下文"""
    
    query = arg("query", ArgumentType.STRING, help="当前查询")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        manager = MemoryManager(ctx.session.session_id)
        memory_state = ctx.session.get("memory", {})
        if memory_state.get("entries"):
            manager.entries = [ContextEntry.from_dict(e) for e in memory_state["entries"]]
        
        context = manager.get_context_for_prompt(ctx.args.get("query", ""))
        
        return CommandResult(
            success=True,
            message=f"获取到 {len(context)} 字符上下文",
            data={"context": context}
        )


@command(CommandMetadata(
    name="memory.summarize",
    description="总结当前记忆",
    category="memory",
    modifies_state=False,
    requires_session=True
))
class MemorySummarizeCommand:
    """总结"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        manager = MemoryManager(ctx.session.session_id)
        memory_state = ctx.session.get("memory", {})
        if memory_state.get("entries"):
            manager.entries = [ContextEntry.from_dict(e) for e in memory_state["entries"]]
        
        summary = manager.summarize()
        
        return CommandResult(
            success=True,
            data=summary
        )


@command(CommandMetadata(
    name="memory.archive",
    description="归档当前记忆",
    category="memory",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class MemoryArchiveCommand:
    """归档"""
    
    name = opt("name", ArgumentType.STRING, default=None, help="归档名称")
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        manager = MemoryManager(ctx.session.session_id)
        memory_state = ctx.session.get("memory", {})
        if memory_state.get("entries"):
            manager.entries = [ContextEntry.from_dict(e) for e in memory_state["entries"]]
        
        path = manager.archive(ctx.options.get("name"))
        ctx.session.set("memory", {"entries": []})
        
        return CommandResult(
            success=True,
            message=f"已归档到: {path}",
            data={"archive_path": path}
        )


@command(CommandMetadata(
    name="memory.stats",
    description="显示记忆统计",
    category="memory",
    modifies_state=False,
    requires_session=True
))
class MemoryStatsCommand:
    """统计"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        manager = MemoryManager(ctx.session.session_id)
        stats = manager.get_stats()
        
        return CommandResult(
            success=True,
            data=stats
        )


@command(CommandMetadata(
    name="memory.clear",
    description="清空当前记忆",
    category="memory",
    modifies_state=True,
    undoable=True,
    requires_session=True
))
class MemoryClearCommand:
    """清空"""
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        manager = MemoryManager(ctx.session.session_id)
        manager.clear()
        ctx.session.set("memory", {"entries": []})
        
        return CommandResult(
            success=True,
            message="记忆已清空"
        )


# ============================================================================
# REPL 入口
# ============================================================================

def create_memory_skill():
    """创建 Memory Skill 注册表"""
    registry = CommandRegistry()
    
    registry.register(MemoryAddCommand)
    registry.register(MemoryRetrieveCommand)
    registry.register(MemoryContextCommand)
    registry.register(MemorySummarizeCommand)
    registry.register(MemoryArchiveCommand)
    registry.register(MemoryStatsCommand)
    registry.register(MemoryClearCommand)
    
    return registry


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Context Skill")
    parser.add_argument("--interactive", "-i", action="store_true", help="REPL模式")
    parser.add_argument("command", nargs="?", help="命令")
    parser.add_argument("args", nargs="*", help="参数")
    
    args = parser.parse_args()
    
    registry = create_memory_skill()
    session_manager = SessionManager()
    
    if args.interactive or not args.command:
        print("🧠 Memory Context Skill")
        print("命令: memory.add, memory.retrieve, memory.context, memory.summarize")
        print("      memory.archive, memory.stats, memory.clear")
        print("其他: session.create, undo, redo, help, exit\n")
        
        repl = ReplSkin(registry, session_manager)
        repl.run()
    else:
        # 单命令模式
        print("使用 --interactive 启动 REPL 模式")


if __name__ == "__main__":
    main()
