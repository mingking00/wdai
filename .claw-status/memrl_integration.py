#!/usr/bin/env python3
"""
MemRL 记忆系统集成
基于技能的MemRL系统，提供语义检索和Q值学习
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib

class MemRLMemory:
    """MemRL语义记忆系统"""
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.path.expanduser("~/.openclaw/workspace"))
        self.memory_dir = self.workspace / ".claw-status" / "memrl"
        self.memory_file = self.memory_dir / "memories.json"
        
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载记忆
        self.memories = self._load_memories()
    
    def _load_memories(self) -> Dict[str, Dict]:
        """加载记忆数据库"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_memories(self):
        """保存记忆数据库"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, indent=2, ensure_ascii=False)
    
    def _generate_id(self, content: str) -> str:
        """生成记忆ID"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def add_memory(self, 
                   content: str, 
                   context: str = "",
                   tags: List[str] = None,
                   source: str = "manual",
                   initial_q: float = 0.5) -> str:
        """
        添加新记忆
        
        Args:
            content: 记忆内容
            context: 上下文
            tags: 标签
            source: 来源
            initial_q: 初始Q值 (0-1)
        
        Returns:
            memory_id
        """
        memory_id = self._generate_id(content)
        
        if memory_id in self.memories:
            # 记忆已存在，更新访问次数
            self.memories[memory_id]["access_count"] += 1
            self.memories[memory_id]["last_accessed"] = datetime.now().isoformat()
            self._save_memories()
            return memory_id
        
        memory = {
            "id": memory_id,
            "content": content,
            "context": context,
            "tags": tags or [],
            "source": source,
            "q_value": initial_q,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 1,
            "success_count": 0,
            "failure_count": 0
        }
        
        self.memories[memory_id] = memory
        self._save_memories()
        
        return memory_id
    
    def update_q_value(self, memory_id: str, reward: float, learning_rate: float = 0.1):
        """
        更新记忆的Q值
        
        Args:
            memory_id: 记忆ID
            reward: 奖励值 (1.0=成功, 0.0=失败, 0.5=中性)
            learning_rate: 学习率
        """
        if memory_id not in self.memories:
            return
        
        memory = self.memories[memory_id]
        old_q = memory["q_value"]
        
        # Q-learning更新
        new_q = old_q + learning_rate * (reward - old_q)
        memory["q_value"] = round(min(1.0, max(0.0, new_q)), 3)
        
        # 更新成功/失败计数
        if reward >= 0.8:
            memory["success_count"] += 1
        elif reward <= 0.2:
            memory["failure_count"] += 1
        
        memory["last_accessed"] = datetime.now().isoformat()
        self._save_memories()
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        检索相关记忆
        
        使用简单的关键词匹配 + Q值排序
        实际部署时可替换为向量检索
        
        Args:
            query: 查询
            top_k: 返回数量
        
        Returns:
            按相关性+Q值排序的记忆列表
        """
        query_words = set(query.lower().split())
        results = []
        
        for memory_id, memory in self.memories.items():
            content = memory["content"].lower()
            tags = [t.lower() for t in memory.get("tags", [])]
            context = memory.get("context", "").lower()
            
            # 计算相关性分数
            relevance = 0
            for word in query_words:
                if word in content:
                    relevance += 0.3
                if word in context:
                    relevance += 0.2
                if any(word in t for t in tags):
                    relevance += 0.5
            
            if relevance > 0:
                # 综合分数 = 相关性 * 0.6 + Q值 * 0.4
                combined_score = relevance * 0.6 + memory["q_value"] * 0.4
                results.append({
                    **memory,
                    "relevance": round(relevance, 3),
                    "combined_score": round(combined_score, 3)
                })
        
        # 按综合分数排序
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # 更新访问计数
        for r in results[:top_k]:
            self.memories[r["id"]]["access_count"] += 1
            self.memories[r["id"]]["last_accessed"] = datetime.now().isoformat()
        
        self._save_memories()
        
        return results[:top_k]
    
    def find_conflicts(self, new_content: str) -> List[Tuple[Dict, float]]:
        """
        查找与现有记忆的冲突
        
        Returns:
            冲突记忆列表，每项为 (记忆, 冲突分数)
        """
        conflicts = []
        new_words = set(new_content.lower().split())
        
        for memory_id, memory in self.memories.items():
            content_words = set(memory["content"].lower().split())
            
            # 计算重叠度
            overlap = len(new_words & content_words)
            if overlap > 0:
                similarity = overlap / max(len(new_words), len(content_words))
                if similarity > 0.5:  # 相似度阈值
                    conflicts.append((memory, similarity))
        
        return sorted(conflicts, key=lambda x: x[1], reverse=True)
    
    def merge_or_replace(self, new_memory_id: str, conflicting_ids: List[str]):
        """
        合并或替换冲突记忆
        
        策略:
        - 如果新记忆Q值更高，替换旧记忆
        - 否则保留旧记忆，但记录关联
        """
        if new_memory_id not in self.memories:
            return
        
        new_memory = self.memories[new_memory_id]
        
        for old_id in conflicting_ids:
            if old_id not in self.memories:
                continue
            
            old_memory = self.memories[old_id]
            
            if new_memory["q_value"] > old_memory["q_value"]:
                # 新记忆更好，标记旧记忆为已合并
                old_memory["merged_into"] = new_memory_id
                old_memory["q_value"] *= 0.5  # 衰减
            else:
                # 旧记忆更好，记录关联
                if "related_memories" not in old_memory:
                    old_memory["related_memories"] = []
                old_memory["related_memories"].append(new_memory_id)
                
                # 新记忆降低Q值
                new_memory["q_value"] *= 0.8
        
        self._save_memories()
    
    def get_stats(self) -> Dict:
        """获取记忆统计"""
        if not self.memories:
            return {"total": 0, "avg_q": 0, "high_q": 0}
        
        q_values = [m["q_value"] for m in self.memories.values()]
        
        return {
            "total": len(self.memories),
            "avg_q": round(sum(q_values) / len(q_values), 3),
            "high_q": len([q for q in q_values if q >= 0.7]),
            "low_q": len([q for q in q_values if q < 0.3])
        }
    
    def generate_report(self) -> str:
        """生成记忆系统报告"""
        stats = self.get_stats()
        
        report = f"""# MemRL记忆系统报告

**生成时间**: {datetime.now().isoformat()}

## 📊 统计概览

| 指标 | 数值 |
|:---|:---:|
| 总记忆数 | {stats['total']} |
| 平均Q值 | {stats['avg_q']} |
| 高Q值记忆 | {stats['high_q']} |
| 低Q值记忆 | {stats['low_q']} |

## 🏆 高价值记忆 (Q≥0.7)

"""
        high_value = [
            m for m in self.memories.values()
            if m["q_value"] >= 0.7
        ]
        high_value.sort(key=lambda x: x["q_value"], reverse=True)
        
        if high_value:
            for m in high_value[:5]:
                report += f"- **{m['content'][:50]}...** (Q={m['q_value']})\n"
        else:
            report += "_暂无高价值记忆_\n"
        
        report += "\n## 📈 最近添加的记忆\n\n"
        recent = sorted(
            self.memories.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )[:5]
        
        for m in recent:
            report += f"- {m['content'][:50]}... (Q={m['q_value']})\n"
        
        return report


# ==================== 全局实例 ====================

_memrl = None

def get_memrl_memory() -> MemRLMemory:
    """获取全局MemRL实例"""
    global _memrl
    if _memrl is None:
        _memrl = MemRLMemory()
    return _memrl


# ==================== CLI接口 ====================

if __name__ == "__main__":
    memrl = MemRLMemory()
    
    if len(sys.argv) < 2:
        print(memrl.generate_report())
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "add" and len(sys.argv) >= 3:
        content = sys.argv[2]
        tags = sys.argv[3].split(",") if len(sys.argv) > 3 else []
        memory_id = memrl.add_memory(content, tags=tags)
        print(f"✅ 记忆已添加: {memory_id}")
    
    elif command == "search" and len(sys.argv) >= 3:
        query = sys.argv[2]
        results = memrl.retrieve(query)
        print(f"查询: '{query}'\n")
        for r in results:
            print(f"[{r['combined_score']:.2f}] {r['content'][:80]}...")
            print(f"   Q={r['q_value']}, 相关={r['relevance']}, 来源={r['source']}")
            print()
    
    elif command == "stats":
        stats = memrl.get_stats()
        print(f"记忆统计:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    
    elif command == "report":
        print(memrl.generate_report())
    
    else:
        print(f"Unknown command: {command}")
