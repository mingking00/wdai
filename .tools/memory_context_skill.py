#!/usr/bin/env python3
"""
Memory Context Skill - 智能记忆上下文管理

用途: 在对话中自动管理上下文，检索相关信息，避免重复
调用: python3 memory_context_skill.py [command] [options]

集成到OpenClaw工作流:
- 自动检索相关历史信息
- 上下文压缩和摘要
- 跨会话记忆持久化
"""

import sys
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import re

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / ".memory-context"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
CONTEXT_FILE = MEMORY_DIR / "current_context.json"
INDEX_FILE = MEMORY_DIR / "memory_index.json"


@dataclass
class ContextEntry:
    """上下文条目"""
    id: str
    content: str
    source: str  # 来源: conversation, file, tool_result
    importance: float  # 0-10
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


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.entries: List[ContextEntry] = []
        self.index: Dict[str, Any] = {}
        self._load_index()
        self._load_current_context()
    
    def _load_index(self):
        """加载记忆索引"""
        if INDEX_FILE.exists():
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
        else:
            self.index = {"entries": [], "tags": {}, "sessions": []}
    
    def _save_index(self):
        """保存记忆索引"""
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
    
    def _load_current_context(self):
        """加载当前上下文"""
        if CONTEXT_FILE.exists():
            with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.entries = [ContextEntry.from_dict(e) for e in data.get("entries", [])]
    
    def _save_current_context(self):
        """保存当前上下文"""
        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in self.entries]
        }
        with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add(self, content: str, source: str = "conversation", 
            importance: float = 5.0, tags: List[str] = None) -> str:
        """
        添加上下文条目
        
        Args:
            content: 内容文本
            source: 来源类型
            importance: 重要性 (0-10)
            tags: 标签列表
            
        Returns:
            条目ID
        """
        entry_id = hashlib.md5(f"{content}{datetime.now()}".encode()).hexdigest()[:8]
        
        entry = ContextEntry(
            id=entry_id,
            content=content[:2000],  # 限制长度
            source=source,
            importance=importance,
            tags=tags or self._extract_tags(content),
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id
        )
        
        self.entries.append(entry)
        
        # 更新索引
        self._update_index(entry)
        
        # 保存
        self._save_current_context()
        
        return entry_id
    
    def retrieve(self, query: str, top_k: int = 5, 
                 min_relevance: float = 0.3) -> List[Tuple[ContextEntry, float]]:
        """
        检索相关上下文
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            min_relevance: 最小相关性阈值
            
        Returns:
            (条目, 相关度) 列表
        """
        query_terms = set(self._tokenize(query))
        scored = []
        
        for entry in self.entries:
            # 计算相关性
            entry_terms = set(self._tokenize(entry.content))
            tag_terms = set(tag.lower() for tag in entry.tags)
            
            # Jaccard相似度
            overlap = len(query_terms & entry_terms)
            union = len(query_terms | entry_terms)
            text_sim = overlap / union if union > 0 else 0
            
            # 标签匹配
            tag_overlap = len(query_terms & tag_terms)
            tag_score = tag_overlap / len(query_terms) if query_terms else 0
            
            # 综合相关性
            relevance = text_sim * 0.6 + tag_score * 0.4
            
            # 重要性加权
            importance_weight = entry.importance / 10.0
            
            # 时间衰减
            age_hours = self._get_age_hours(entry.timestamp)
            recency = max(0, 1 - age_hours / 168)  # 一周内满值
            
            # 访问频率
            access_score = min(entry.access_count / 10, 1.0)
            
            # 最终得分
            score = (relevance * 0.4 + importance_weight * 0.25 + 
                    recency * 0.2 + access_score * 0.15)
            
            if score >= min_relevance:
                scored.append((entry, score))
                
                # 更新访问计数
                entry.access_count += 1
                entry.last_accessed = datetime.now().isoformat()
        
        # 排序并返回
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
    
    def get_context_for_prompt(self, query: str, max_tokens: int = 2000) -> str:
        """
        获取格式化的上下文用于Prompt
        
        Args:
            query: 当前查询
            max_tokens: 最大token数 (估算)
            
        Returns:
            格式化上下文字符串
        """
        results = self.retrieve(query, top_k=5)
        
        if not results:
            return ""
        
        context_parts = ["\n### 相关上下文\n"]
        current_length = 0
        
        for entry, score in results:
            # 估算token数 (粗略: 1 token ≈ 4 chars)
            entry_text = f"[{entry.source}] {entry.content[:300]}... (相关度: {score:.2f})\n"
            entry_tokens = len(entry_text) // 4
            
            if current_length + entry_tokens > max_tokens:
                break
            
            context_parts.append(entry_text)
            current_length += entry_tokens
        
        return "\n".join(context_parts)
    
    def summarize_session(self) -> Dict:
        """总结当前会话"""
        if not self.entries:
            return {"message": "当前会话无记录"}
        
        # 按来源分组
        by_source = {}
        for entry in self.entries:
            by_source.setdefault(entry.source, []).append(entry)
        
        # 提取关键标签
        all_tags = []
        for entry in self.entries:
            all_tags.extend(entry.tags)
        tag_freq = {}
        for tag in all_tags:
            tag_freq[tag] = tag_freq.get(tag, 0) + 1
        top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "session_id": self.session_id,
            "total_entries": len(self.entries),
            "by_source": {k: len(v) for k, v in by_source.items()},
            "top_tags": top_tags,
            "avg_importance": sum(e.importance for e in self.entries) / len(self.entries),
            "time_range": {
                "start": min(e.timestamp for e in self.entries),
                "end": max(e.timestamp for e in self.entries)
            }
        }
    
    def archive_session(self, session_name: str = None) -> str:
        """归档当前会话"""
        name = session_name or f"session_{self.session_id}"
        archive_file = MEMORY_DIR / f"{name}.json"
        
        data = {
            "name": name,
            "session_id": self.session_id,
            "archived_at": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in self.entries]
        }
        
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 清空当前上下文
        self.entries = []
        self._save_current_context()
        
        return str(archive_file)
    
    def search_archive(self, query: str) -> List[Dict]:
        """搜索归档的会话"""
        results = []
        
        for archive_file in MEMORY_DIR.glob("session_*.json"):
            with open(archive_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 简单搜索
                content = json.dumps(data).lower()
                if query.lower() in content:
                    results.append({
                        "file": str(archive_file),
                        "name": data.get("name"),
                        "archived_at": data.get("archived_at"),
                        "entry_count": len(data.get("entries", []))
                    })
        
        return results
    
    def _update_index(self, entry: ContextEntry):
        """更新索引"""
        self.index["entries"].append({
            "id": entry.id,
            "source": entry.source,
            "timestamp": entry.timestamp,
            "session_id": entry.session_id
        })
        
        for tag in entry.tags:
            self.index["tags"].setdefault(tag, []).append(entry.id)
        
        if entry.session_id not in self.index["sessions"]:
            self.index["sessions"].append(entry.session_id)
        
        self._save_index()
    
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
        # 简单分词
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]+\b', text.lower())
        return [w for w in words if len(w) > 1]
    
    def _get_age_hours(self, timestamp: str) -> float:
        """获取条目年龄（小时）"""
        try:
            created = datetime.fromisoformat(timestamp)
            age = datetime.now() - created
            return age.total_seconds() / 3600
        except:
            return 0.0
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "current_entries": len(self.entries),
            "total_indexed": len(self.index.get("entries", [])),
            "unique_tags": len(self.index.get("tags", {})),
            "sessions": len(self.index.get("sessions", [])),
            "memory_dir": str(MEMORY_DIR)
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Context Skill")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # add 命令
    add_parser = subparsers.add_parser("add", help="添加上下文")
    add_parser.add_argument("content", help="内容")
    add_parser.add_argument("--source", default="conversation", help="来源")
    add_parser.add_argument("--importance", type=float, default=5.0, help="重要性")
    add_parser.add_argument("--tags", help="标签，逗号分隔")
    
    # retrieve 命令
    retrieve_parser = subparsers.add_parser("retrieve", help="检索上下文")
    retrieve_parser.add_argument("query", help="查询")
    retrieve_parser.add_argument("--top-k", type=int, default=5, help="返回数量")
    
    # context 命令
    context_parser = subparsers.add_parser("context", help="获取Prompt上下文")
    context_parser.add_argument("query", help="当前查询")
    
    # summarize 命令
    subparsers.add_parser("summarize", help="总结当前会话")
    
    # archive 命令
    archive_parser = subparsers.add_parser("archive", help="归档会话")
    archive_parser.add_argument("--name", help="归档名称")
    
    # stats 命令
    subparsers.add_parser("stats", help="显示统计")
    
    args = parser.parse_args()
    
    manager = ContextManager()
    
    if args.command == "add":
        tags = args.tags.split(",") if args.tags else None
        entry_id = manager.add(args.content, args.source, args.importance, tags)
        print(f"✅ 已添加: {entry_id}")
    
    elif args.command == "retrieve":
        results = manager.retrieve(args.query, top_k=args.top_k)
        print(f"🔍 检索 '{args.query}':\n")
        for entry, score in results:
            print(f"[{score:.2f}] {entry.source}: {entry.content[:100]}...")
    
    elif args.command == "context":
        context = manager.get_context_for_prompt(args.query)
        print(context)
    
    elif args.command == "summarize":
        summary = manager.summarize_session()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    elif args.command == "archive":
        path = manager.archive_session(args.name)
        print(f"💾 已归档到: {path}")
    
    elif args.command == "stats":
        stats = manager.get_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
