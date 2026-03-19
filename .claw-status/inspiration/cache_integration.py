#!/usr/bin/env python3
"""
灵感摄取系统 - 缓存集成模块

将SmartCache集成到调度器中，实现:
- 抓取前缓存检查
- 内容指纹去重
- 智能缓存刷新

Author: wdai
Version: 1.0
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))

from smart_cache import SmartCache, ContentFingerprinter
from advanced_scheduler import AdvancedScheduler, SourceTask


class CacheAwareScheduler(AdvancedScheduler):
    """
    缓存感知调度器
    
    集成智能缓存的调度器
    """
    
    def __init__(self, data_dir: str = "data/scheduler_v4"):
        super().__init__(data_dir)
        
        # 智能缓存
        self.cache = SmartCache(
            cache_dir=str(Path(data_dir) / "content_cache"),
            max_size=1000
        )
        
        # 缓存统计
        self.cache_hits = 0
        self.cache_skips = 0
    
    def should_fetch_source(self, source_id: str, url: str = None) -> tuple[bool, Optional[dict]]:
        """
        检查是否应该抓取源
        
        Returns:
            (should_fetch, cache_info)
        """
        cache_key = f"{source_id}:{url}" if url else source_id
        
        # 检查缓存
        entry = self.cache.get(cache_key)
        
        if entry:
            # 缓存命中
            self.cache_hits += 1
            
            # 检查是否需要刷新
            time_since_access = (datetime.now() - entry.last_accessed).total_seconds() if entry.last_accessed else float('inf')
            
            # 如果缓存较新 (1小时内)，跳过抓取
            if time_since_access < 3600:
                self.cache_skips += 1
                return False, {
                    'status': 'cache_hit',
                    'cached_at': entry.created_at.isoformat(),
                    'content_hash': entry.content_hash,
                    'metadata': entry.metadata
                }
            
            # 缓存存在但较旧，尝试条件请求
            return True, {
                'status': 'conditional_fetch',
                'etag': entry.etag,
                'last_modified': entry.last_modified,
                'content_hash': entry.content_hash
            }
        
        # 缓存未命中，需要抓取
        return True, {'status': 'no_cache'}
    
    def cache_fetch_result(self, source_id: str, url: str, content: str,
                          content_type: str, metadata: Dict = None,
                          etag: str = None, last_modified: str = None):
        """
        缓存抓取结果
        """
        cache_key = f"{source_id}:{url}" if url else source_id
        
        entry = self.cache.put(
            key=cache_key,
            content=content,
            content_type=content_type,
            metadata=metadata or {},
            etag=etag,
            last_modified=last_modified
        )
        
        return entry
    
    def check_duplicate_content(self, content: str, threshold: int = 3) -> Optional[str]:
        """
        检查内容是否重复
        
        Returns:
            重复内容的key，如果没有重复返回None
        """
        content_hash = ContentFingerprinter.sha256_hash(content)
        
        # 精确匹配
        entry = self.cache.get_by_hash(content_hash)
        if entry:
            return entry.key
        
        # 相似匹配 (SimHash)
        similar = self.cache.find_similar(content, threshold)
        if similar:
            return similar[0][0]  # 返回最相似的
        
        return None
    
    def run_once_with_cache(self) -> dict:
        """
        运行一次调度循环 (带缓存)
        """
        # 先清理过期缓存
        self.cache.cleanup_expired()
        
        # 获取下一个任务
        task = self.mlfq.dequeue()
        if not task:
            return {'status': 'no_task'}
        
        source_id = task.source_id
        
        # 检查缓存
        should_fetch, cache_info = self.should_fetch_source(source_id)
        
        if not should_fetch:
            print(f"[{source_id}] 💾 缓存命中，跳过抓取")
            self.mlfq.complete_task(task)
            return {
                'status': 'cache_hit',
                'source': source_id,
                'cache_info': cache_info
            }
        
        # 执行抓取
        print(f"[{source_id}] 🌐 缓存{type(cache_info['status'])}, 执行抓取")
        
        # 调用父类的执行逻辑
        result = self.run_once()
        
        # 如果抓取成功，缓存结果
        if result.get('status') == 'completed' and 'content' in result:
            self.cache_fetch_result(
                source_id=source_id,
                url=result.get('url'),
                content=result['content'],
                content_type=result.get('content_type', 'default'),
                metadata=result.get('metadata', {}),
                etag=result.get('etag'),
                last_modified=result.get('last_modified')
            )
        
        return result
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        cache_stats = self.cache.get_stats()
        
        return {
            'cache': cache_stats,
            'scheduler_hits': self.cache_hits,
            'scheduler_skips': self.cache_skips,
            'efficiency': self.cache_skips / max(1, self.cache_hits) * 100
        }
    
    def print_full_stats(self):
        """打印完整统计"""
        # 调度器统计
        self.print_stats()
        
        # 缓存统计
        print("\n" + "="*60)
        print("💾 缓存统计")
        print("="*60)
        
        stats = self.get_cache_stats()
        cache = stats['cache']
        
        print(f"缓存条目: {cache['total_entries']}")
        print(f"活跃: {cache['active_entries']} | 过期: {cache['expired_entries']}")
        print(f"缓存命中率: {cache['hit_rate']:.1%}")
        print(f"调度器跳过量: {stats['scheduler_skips']}")
        print(f"跳过效率: {stats['efficiency']:.1f}%")


def test_cache_integration():
    """测试缓存集成"""
    print("="*70)
    print("🧪 测试缓存集成")
    print("="*70)
    
    scheduler = CacheAwareScheduler()
    
    # 模拟抓取并缓存
    print("\n--- 第1次运行 (无缓存) ---")
    result1 = scheduler.run_once()
    
    # 再次调度同一源
    print("\n--- 第2次运行 (应命中缓存) ---")
    scheduler.schedule_source('arxiv')
    result2 = scheduler.run_once_with_cache()
    
    # 打印统计
    print("\n" + "="*70)
    print("📊 完整统计")
    print("="*70)
    scheduler.print_full_stats()
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == "__main__":
    test_cache_integration()
