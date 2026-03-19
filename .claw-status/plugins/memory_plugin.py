"""
Memory Plugin - 记忆系统插件
自动提取和存储关键信息
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from framework import UniversalPlugin, ToolContext, TaskContext
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import json
import re


class MemoryPlugin(UniversalPlugin):
    """
    记忆系统插件
    自动从任务中提取关键事实
    """
    
    name = "memory_system"
    version = "2.0.0"
    priority = 30
    
    DB_PATH = Path("/root/.openclaw/workspace/.claw-status/data/memories.json")
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.db = self._load_db()
        self.strategy = self.config.get("extract_strategy", "semantic")
        self.templates = self.config.get("templates", self._default_templates())
    
    def _load_db(self) -> Dict:
        """加载记忆数据库"""
        if self.DB_PATH.exists():
            with open(self.DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "2.0",
            "memories": [],
            "index": {}
        }
    
    def _save_db(self):
        """保存记忆数据库"""
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)
    
    def _default_templates(self) -> List[Dict]:
        """默认提取模板"""
        return [
            {
                "name": "user_preference",
                "pattern": r"(我喜欢|我不喜欢|我偏好|我讨厌|我习惯)(.+)",
                "type": "preference"
            },
            {
                "name": "error_lesson",
                "pattern": r"(错误|问题|教训|失败)(.+?)(因为|由于|原因是)(.+)",
                "type": "lesson"
            },
            {
                "name": "success_pattern",
                "pattern": r"(成功|有效|可行|解决了)(.+?)(通过|使用|借助)(.+)",
                "type": "pattern"
            }
        ]
    
    def on_task_complete(self, context: TaskContext):
        """
        任务完成时提取记忆
        """
        # 构建任务文本
        task_text = self._build_task_text(context)
        
        # 根据策略提取
        if self.strategy == "semantic":
            facts = self._semantic_extract(task_text)
        elif self.strategy == "keyword":
            facts = self._keyword_extract(task_text)
        elif self.strategy == "template":
            facts = self._template_extract(task_text)
        else:
            facts = []
        
        # 存储记忆
        for fact in facts:
            self._store_memory(fact, context)
        
        if facts:
            self.logger(f"📝 提取了 {len(facts)} 条记忆")
    
    def on_tool_after(self, context: ToolContext, result: Any):
        """
        工具调用后检查是否有值得记忆的信息
        """
        # 如果结果包含重要信息，记录
        if isinstance(result, dict):
            if "error" in result and result["error"]:
                # 记录错误
                self._store_memory({
                    "type": "error",
                    "content": f"{context.tool_name} 失败: {result['error']}",
                    "tool": context.tool_name,
                    "timestamp": datetime.now().isoformat()
                }, None)
    
    def _build_task_text(self, context: TaskContext) -> str:
        """构建任务文本用于提取"""
        parts = [
            f"任务类型: {context.task_type}",
            f"描述: {context.description}",
            f"结果: {'成功' if context.success else '失败'}"
        ]
        
        # 添加工具调用信息
        for tool_call in context.tool_calls:
            parts.append(f"工具: {tool_call.tool_name}")
            parts.append(f"参数: {json.dumps(tool_call.params, ensure_ascii=False)}")
        
        return "\n".join(parts)
    
    def _semantic_extract(self, text: str) -> List[Dict]:
        """语义提取（简化版）"""
        facts = []
        
        # 提取用户偏好
        pref_patterns = [
            r"(用户|你|我).*?(喜欢|偏好|习惯|讨厌).*?(?P<content>.+?)(?:\.|$)",
            r"(?P<content>.+?)是(我的|用户的)(偏好|习惯|要求)"
        ]
        
        for pattern in pref_patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                content = match.group("content") if "content" in match.groupdict() else match.group(0)
                facts.append({
                    "type": "preference",
                    "content": content.strip(),
                    "confidence": 0.7
                })
        
        # 提取教训/学习
        lesson_patterns = [
            r"(教训|学到|发现|意识到)(.+?)(应该|需要|必须)(.+)",
            r"(下次|以后|将来)(.+?)(应该|可以|需要)(.+)"
        ]
        
        for pattern in lesson_patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                facts.append({
                    "type": "lesson",
                    "content": match.group(0).strip(),
                    "confidence": 0.6
                })
        
        return facts
    
    def _keyword_extract(self, text: str) -> List[Dict]:
        """关键词提取"""
        facts = []
        
        keywords = {
            "TODO": r"TODO[:\s]+(.+)",
            "重要": r"(重要|关键|核心)[:\s]*(.+)",
            "记住": r"(记住|记得|别忘了)[:\s]*(.+)"
        }
        
        for key, pattern in keywords.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                facts.append({
                    "type": "keyword",
                    "keyword": key,
                    "content": match.group(1).strip() if match.groups() else match.group(0),
                    "confidence": 0.8
                })
        
        return facts
    
    def _template_extract(self, text: str) -> List[Dict]:
        """模板提取"""
        facts = []
        
        for template in self.templates:
            pattern = template.get("pattern", "")
            for match in re.finditer(pattern, text, re.DOTALL):
                groups = match.groups()
                facts.append({
                    "type": template.get("type", "unknown"),
                    "template": template.get("name"),
                    "content": " ".join(groups) if groups else match.group(0),
                    "confidence": 0.75
                })
        
        return facts
    
    def _store_memory(self, fact: Dict, context: Optional[TaskContext]):
        """存储记忆"""
        memory = {
            "id": f"mem_{len(self.db['memories']) + 1:04d}",
            "type": fact.get("type", "general"),
            "content": fact.get("content", ""),
            "confidence": fact.get("confidence", 0.5),
            "timestamp": datetime.now().isoformat(),
            "task_id": context.task_id if context else None,
            "metadata": {
                "strategy": self.strategy,
                **fact.get("metadata", {})
            }
        }
        
        # 检查重复（简单内容匹配）
        for existing in self.db["memories"]:
            if existing["content"] == memory["content"]:
                # 更新置信度
                existing["confidence"] = max(existing["confidence"], memory["confidence"])
                existing["access_count"] = existing.get("access_count", 0) + 1
                return
        
        self.db["memories"].append(memory)
        self._save_db()
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索记忆"""
        # 简单关键词匹配
        query_terms = query.lower().split()
        scored = []
        
        for memory in self.db["memories"]:
            content = memory.get("content", "").lower()
            score = sum(1 for term in query_terms if term in content)
            score *= memory.get("confidence", 0.5)
            
            if score > 0:
                scored.append((score, memory))
        
        # 排序并返回top_k
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:top_k]]
    
    def get_stats(self) -> Dict:
        """获取统计"""
        memories = self.db.get("memories", [])
        by_type = {}
        for m in memories:
            t = m.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total_memories": len(memories),
            "by_type": by_type,
            "strategy": self.strategy
        }


if __name__ == "__main__":
    # 测试
    plugin = MemoryPlugin()
    
    # 模拟任务文本
    test_text = """
    任务类型: 发送消息
    描述: 发送PPT到飞书
    结果: 成功
    工具: message.send
    用户说他喜欢简洁的消息
    教训是应该先用cron而不是直接发送
    """
    
    facts = plugin._semantic_extract(test_text)
    print(f"提取到 {len(facts)} 条记忆:")
    for f in facts:
        print(f"  - {f['type']}: {f['content'][:50]}")
    
    print(plugin.get_stats())
