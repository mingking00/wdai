#!/usr/bin/env python3
"""
memory_decay.py - 记忆衰减与维护脚本

基于 Mem0 的时间衰减算法实现
功能：
1. 应用时间衰减，降低旧记忆分数
2. 清理过期/低价值记忆
3. 合并重复记忆
4. 生成维护报告
"""

import json
import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import shutil

@dataclass
class Memory:
    """记忆数据模型"""
    id: str
    content: str
    category: str
    importance: float
    confidence: float
    user_id: str
    created_at: str
    updated_at: str
    access_count: int = 0
    last_accessed: Optional[str] = None
    decay_score: float = 1.0  # 当前衰减分数
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Memory":
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            category=data.get("category", "fact"),
            importance=data.get("importance", 0.5),
            confidence=data.get("confidence", 0.8),
            user_id=data.get("user_id", "default"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed"),
            decay_score=data.get("decay_score", 1.0)
        )
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "importance": self.importance,
            "confidence": self.confidence,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "decay_score": self.decay_score
        }

class DecayEngine:
    """
    记忆衰减引擎
    
    衰减公式: score = base * exp(-λ * age) + access_boost
    其中 λ = ln(2) / half_life
    """
    
    def __init__(self, 
                 half_life_days: float = 30.0,
                 access_boost: float = 0.05,
                 min_threshold: float = 0.1):
        self.half_life = half_life_days
        self.access_boost = access_boost
        self.min_threshold = min_threshold
        self.lambda_decay = np.log(2) / half_life_days
        
    def calculate_decay(self, memory: Memory) -> float:
        """
        计算记忆的当前衰减分数
        
        考虑因素：
        1. 基础年龄衰减
        2. 重要性加权（重要记忆衰减更慢）
        3. 访问频率提升
        4. 置信度加权
        """
        try:
            created = datetime.fromisoformat(memory.created_at)
            now = datetime.now()
            age_days = (now - created).days
            
            # 基础指数衰减
            base_decay = np.exp(-self.lambda_decay * age_days)
            
            # 重要性保护 (重要性越高，衰减越慢)
            # importance 0.5 -> 系数 1.0
            # importance 1.0 -> 系数 0.5
            importance_factor = 1.0 - (memory.importance - 0.5) * 0.5
            
            # 访问频率提升
            access_count = memory.access_count
            last_access = memory.last_accessed
            
            access_value = 0.0
            if last_access:
                try:
                    last_access_date = datetime.fromisoformat(last_access)
                    days_since_access = (now - last_access_date).days
                    
                    # 最近访问过的记忆获得临时保护
                    if days_since_access < 7:
                        access_value += 0.2
                except:
                    pass
            
            # 总访问次数提升（但有上限）
            access_value += min(access_count * self.access_boost, 0.3)
            
            # 置信度加权（高置信度记忆衰减更慢）
            confidence_factor = 0.7 + memory.confidence * 0.3
            
            # 综合计算
            final_score = (base_decay * importance_factor * confidence_factor) + access_value
            
            # 确保在合理范围内
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            print(f"Warning: Error calculating decay for {memory.id}: {e}", file=sys.stderr)
            return memory.decay_score
    
    def should_retain(self, memory: Memory, threshold: Optional[float] = None) -> bool:
        """判断是否应保留该记忆"""
        threshold = threshold or self.min_threshold
        
        # 计算当前分数
        current_score = self.calculate_decay(memory)
        
        # 更新记忆分数
        memory.decay_score = current_score
        
        # 保留条件：分数高于阈值
        return current_score >= threshold
    
    def get_retention_reason(self, memory: Memory) -> str:
        """获取保留/删除的原因说明"""
        score = self.calculate_decay(memory)
        
        if score >= 0.8:
            return "high_value"
        elif score >= 0.5:
            return "active"
        elif score >= self.min_threshold:
            return "low_but_retained"
        else:
            return "decayed"

class MemoryDeduplicator:
    """记忆去重器"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        
    def text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（Jaccard）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def find_duplicates(self, memories: List[Memory]) -> List[Tuple[Memory, Memory, float]]:
        """找出重复的记忆对"""
        duplicates = []
        
        for i, mem1 in enumerate(memories):
            for mem2 in memories[i+1:]:
                similarity = self.text_similarity(mem1.content, mem2.content)
                
                if similarity >= self.threshold:
                    duplicates.append((mem1, mem2, similarity))
                    
        return duplicates
    
    def merge_memories(self, mem1: Memory, mem2: Memory) -> Memory:
        """合并两个相似记忆"""
        # 保留更新的
        try:
            date1 = datetime.fromisoformat(mem1.updated_at)
            date2 = datetime.fromisoformat(mem2.updated_at)
            newer = mem1 if date1 >= date2 else mem2
            older = mem2 if date1 >= date2 else mem1
        except:
            newer = mem1
            older = mem2
        
        # 合并属性
        merged = Memory(
            id=newer.id,
            content=newer.content,  # 保留新内容
            category=newer.category,
            importance=max(mem1.importance, mem2.importance),
            confidence=max(mem1.confidence, mem2.confidence),
            user_id=newer.user_id,
            created_at=older.created_at,  # 保留创建时间
            updated_at=datetime.now().isoformat(),
            access_count=mem1.access_count + mem2.access_count,
            last_accessed=newer.last_accessed or older.last_accessed,
            decay_score=max(mem1.decay_score, mem2.decay_score)
        )
        
        # 添加合并标记
        merged.content += f" [merged from {older.id}]"
        
        return merged

class MemoryMaintenance:
    """记忆维护主类"""
    
    def __init__(self, 
                 memory_dir: Path,
                 half_life_days: float = 30.0,
                 min_threshold: float = 0.1,
                 dry_run: bool = False):
        self.memory_dir = memory_dir
        self.decay_engine = DecayEngine(half_life_days, min_threshold=min_threshold)
        self.deduplicator = MemoryDeduplicator()
        self.dry_run = dry_run
        self.stats = {
            "total": 0,
            "retained": 0,
            "removed": 0,
            "merged": 0,
            "by_category": {},
            "by_action": {}
        }
        
    def load_all_memories(self) -> List[Memory]:
        """加载所有记忆文件"""
        memories = []
        
        for file_path in self.memory_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    for item in data:
                        memories.append(Memory.from_dict(item))
                elif isinstance(data, dict):
                    memories.append(Memory.from_dict(data))
                    
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}", file=sys.stderr)
                
        return memories
    
    def save_memories(self, memories: List[Memory], backup: bool = True):
        """保存记忆到文件"""
        if not memories:
            print("No memories to save")
            return
            
        # 备份原文件
        if backup and not self.dry_run:
            backup_dir = self.memory_dir / ".backup"
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for file_path in self.memory_dir.glob("*.json"):
                if file_path.name.startswith("."):
                    continue
                backup_path = backup_dir / f"{file_path.stem}_{timestamp}.json"
                shutil.copy2(file_path, backup_path)
            print(f"Backup created in {backup_dir}")
        
        # 按类别分组保存
        by_category = {}
        for mem in memories:
            cat = mem.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(mem.to_dict())
        
        if not self.dry_run:
            # 清除旧文件
            for file_path in self.memory_dir.glob("*.json"):
                if not file_path.name.startswith("."):
                    file_path.unlink()
            
            # 写入新文件
            for category, items in by_category.items():
                output_path = self.memory_dir / f"{category}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
                print(f"Saved {len(items)} memories to {output_path}")
        else:
            print(f"[DRY RUN] Would save {len(memories)} memories")
            for category, items in by_category.items():
                print(f"  {category}: {len(items)} memories")
    
    def run_maintenance(self, 
                       deduplicate: bool = True,
                       remove_decayed: bool = True) -> Dict:
        """
        执行完整维护流程
        
        Returns:
            维护统计报告
        """
        print(f"\n{'='*50}")
        print("Memory Maintenance Report")
        print(f"{'='*50}\n")
        
        # 1. 加载所有记忆
        print("Step 1: Loading memories...")
        memories = self.load_all_memories()
        self.stats["total"] = len(memories)
        print(f"  Loaded {len(memories)} memories\n")
        
        if not memories:
            return self.stats
        
        # 2. 去重
        if deduplicate:
            print("Step 2: Deduplicating...")
            duplicates = self.deduplicator.find_duplicates(memories)
            
            if duplicates:
                print(f"  Found {len(duplicates)} duplicate pairs")
                
                # 合并重复
                to_remove = set()
                for mem1, mem2, sim in duplicates:
                    if mem1.id in to_remove or mem2.id in to_remove:
                        continue
                    
                    merged = self.deduplicator.merge_memories(mem1, mem2)
                    
                    # 替换旧记忆
                    memories = [m for m in memories if m.id not in (mem1.id, mem2.id)]
                    memories.append(merged)
                    
                    to_remove.add(mem1.id)
                    to_remove.add(mem2.id)
                    self.stats["merged"] += 1
                    
                    print(f"  Merged (sim={sim:.2f}): {mem1.content[:50]}...")
            else:
                print("  No duplicates found")
            print()
        
        # 3. 应用衰减
        print("Step 3: Applying decay...")
        retained = []
        removed = []
        
        for mem in memories:
            if self.decay_engine.should_retain(mem):
                retained.append(mem)
                self.stats["retained"] += 1
                
                # 更新分类统计
                cat = mem.category
                self.stats["by_category"][cat] = self.stats["by_category"].get(cat, 0) + 1
                
                # 记录保留原因
                reason = self.decay_engine.get_retention_reason(mem)
                self.stats["by_action"][reason] = self.stats["by_action"].get(reason, 0) + 1
            else:
                removed.append(mem)
                self.stats["removed"] += 1
                
        print(f"  Retained: {len(retained)}")
        print(f"  Removed: {len(removed)}\n")
        
        if removed and not self.dry_run:
            # 保存被删除的记忆到归档
            archive_dir = self.memory_dir / ".archive"
            archive_dir.mkdir(exist_ok=True)
            archive_path = archive_dir / f"removed_{datetime.now().strftime('%Y%m%d')}.json"
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump([m.to_dict() for m in removed], f, indent=2)
            print(f"  Archived removed memories to {archive_path}\n")
        
        # 4. 保存结果
        print("Step 4: Saving results...")
        self.save_memories(retained)
        
        return self.stats
    
    def print_report(self):
        """打印维护报告"""
        print(f"\n{'='*50}")
        print("Final Statistics")
        print(f"{'='*50}")
        print(f"Total memories: {self.stats['total']}")
        print(f"Retained: {self.stats['retained']} ({self.stats['retained']/max(self.stats['total'],1)*100:.1f}%)")
        print(f"Removed: {self.stats['removed']} ({self.stats['removed']/max(self.stats['total'],1)*100:.1f}%)")
        print(f"Merged: {self.stats['merged']}")
        
        if self.stats["by_category"]:
            print(f"\nBy category:")
            for cat, count in sorted(self.stats["by_category"].items()):
                print(f"  {cat}: {count}")
        
        if self.stats["by_action"]:
            print(f"\nRetention breakdown:")
            for action, count in sorted(self.stats["by_action"].items(), reverse=True, key=lambda x: x[1]):
                print(f"  {action}: {count}")

def main():
    parser = argparse.ArgumentParser(
        description="Memory decay and maintenance - manage memory lifecycle"
    )
    parser.add_argument(
        "--memory-dir", "-d",
        type=Path,
        default=Path(".memory"),
        help="Directory containing memory files (default: .memory)"
    )
    parser.add_argument(
        "--half-life",
        type=float,
        default=30.0,
        help="Decay half-life in days (default: 30)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.1,
        help="Minimum decay score to retain memory (default: 0.1)"
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Skip deduplication"
    )
    parser.add_argument(
        "--keep-all",
        action="store_true",
        help="Keep all memories (no removal, only decay scoring)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without making changes"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Show detailed report"
    )
    
    args = parser.parse_args()
    
    # 检查目录
    if not args.memory_dir.exists():
        print(f"Creating memory directory: {args.memory_dir}")
        args.memory_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行维护
    maintenance = MemoryMaintenance(
        memory_dir=args.memory_dir,
        half_life_days=args.half_life,
        min_threshold=args.threshold if not args.keep_all else 0.0,
        dry_run=args.dry_run
    )
    
    stats = maintenance.run_maintenance(
        deduplicate=not args.no_dedup,
        remove_decayed=not args.keep_all
    )
    
    # 打印报告
    if args.report or args.dry_run:
        maintenance.print_report()
    
    print(f"\nMaintenance {'simulation' if args.dry_run else 'completed'}!")

if __name__ == "__main__":
    main()
