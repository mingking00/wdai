#!/usr/bin/env python3
"""
灵感摄取系统 - 智能缓存管理器 v1.0

功能:
- 内容指纹去重 (避免重复抓取)
- TTL缓存管理 (时间衰减)
- ETag/Last-Modified支持 (条件请求)
- LRU缓存淘汰

Author: wdai
Version: 1.0
"""

import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, asdict
from collections import OrderedDict
import threading


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str                    # 缓存键
    content_hash: str          # 内容指纹 (SHA256)
    raw_content: Optional[str]  # 原始内容 (可选)
    metadata: Dict[str, Any]   # 元数据
    created_at: datetime       # 创建时间
    expires_at: datetime       # 过期时间
    etag: Optional[str] = None # ETag
    last_modified: Optional[str] = None  # Last-Modified
    access_count: int = 0      # 访问次数
    last_accessed: Optional[datetime] = None  # 最后访问时间
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() > self.expires_at
    
    def touch(self):
        """更新访问时间"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'key': self.key,
            'content_hash': self.content_hash,
            'raw_content': self.raw_content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'etag': self.etag,
            'last_modified': self.last_modified,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntry':
        return cls(
            key=data['key'],
            content_hash=data['content_hash'],
            raw_content=data.get('raw_content'),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
            etag=data.get('etag'),
            last_modified=data.get('last_modified'),
            access_count=data.get('access_count', 0),
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None
        )


class ContentFingerprinter:
    """
    内容指纹生成器
    
    使用多种算法生成内容指纹，用于快速去重
    """
    
    @staticmethod
    def sha256_hash(content: str) -> str:
        """SHA256哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def simhash(content: str, hashbits: int = 64) -> str:
        """
        SimHash - 局部敏感哈希
        
        相似内容产生相似的哈希值，用于模糊去重
        """
        import re
        
        # 分词
        tokens = re.findall(r'\w+', content.lower())
        
        # 计算每个词的权重 (简单使用词频)
        weights = {}
        for token in tokens:
            weights[token] = weights.get(token, 0) + 1
        
        # 初始化向量
        v = [0] * hashbits
        
        # 对每个词计算哈希并加权
        for token, weight in weights.items():
            # 使用内置hash (简化版)
            hash_val = hash(token) & ((1 << hashbits) - 1)
            
            for i in range(hashbits):
                bitmask = 1 << i
                if hash_val & bitmask:
                    v[i] += weight
                else:
                    v[i] -= weight
        
        # 生成指纹
        fingerprint = 0
        for i in range(hashbits):
            if v[i] > 0:
                fingerprint |= 1 << i
        
        return format(fingerprint, f'0{hashbits//4}x')
    
    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """计算汉明距离"""
        x = int(hash1, 16) ^ int(hash2, 16)
        return bin(x).count('1')
    
    @staticmethod
    def is_similar(hash1: str, hash2: str, threshold: int = 3) -> bool:
        """
        判断两个内容是否相似
        
        Args:
            threshold: 汉明距离阈值，小于此值认为相似
        """
        return ContentFingerprinter.hamming_distance(hash1, hash2) <= threshold


class SmartCache:
    """
    智能缓存管理器
    
    特性:
    - LRU淘汰策略
    - TTL自动过期
    - 内容指纹去重
    - 线程安全
    """
    
    DEFAULT_TTL_HOURS = {
        'arxiv_paper': 24,      # 论文缓存24小时
        'github_repo': 12,      # GitHub仓库12小时
        'twitter_post': 2,      # Twitter帖子2小时
        'news_article': 6,      # 新闻文章6小时
        'default': 6            # 默认6小时
    }
    
    def __init__(self, cache_dir: str = "data/cache", max_size: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.fingerprints: Dict[str, str] = {}  # hash -> key 映射
        
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        
        self._load_cache()
    
    def _load_cache(self):
        """从磁盘加载缓存"""
        cache_file = self.cache_dir / "cache_index.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    for key, entry_data in data.items():
                        entry = CacheEntry.from_dict(entry_data)
                        if not entry.is_expired():
                            self.cache[key] = entry
                            self.fingerprints[entry.content_hash] = key
                print(f"[SmartCache] 加载 {len(self.cache)} 条缓存")
            except Exception as e:
                print(f"[SmartCache] 加载缓存失败: {e}")
    
    def _save_cache(self):
        """保存缓存到磁盘"""
        cache_file = self.cache_dir / "cache_index.json"
        try:
            with open(cache_file, 'w') as f:
                data = {k: v.to_dict() for k, v in self.cache.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[SmartCache] 保存缓存失败: {e}")
    
    def _get_ttl(self, content_type: str) -> int:
        """获取TTL (小时)"""
        return self.DEFAULT_TTL_HOURS.get(content_type, self.DEFAULT_TTL_HOURS['default'])
    
    def _evict_if_needed(self):
        """LRU淘汰"""
        while len(self.cache) >= self.max_size:
            # 移除最久未访问的
            oldest_key = next(iter(self.cache))
            entry = self.cache.pop(oldest_key)
            self.fingerprints.pop(entry.content_hash, None)
            print(f"[SmartCache] LRU淘汰: {oldest_key}")
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """
        获取缓存
        
        Returns:
            CacheEntry if found and not expired, else None
        """
        with self._lock:
            entry = self.cache.get(key)
            
            if not entry:
                self._misses += 1
                return None
            
            if entry.is_expired():
                # 过期，删除
                self.cache.pop(key)
                self.fingerprints.pop(entry.content_hash, None)
                self._misses += 1
                return None
            
            # 更新访问时间
            entry.touch()
            
            # 移到末尾 (LRU)
            self.cache.move_to_end(key)
            
            self._hits += 1
            return entry
    
    def get_by_hash(self, content_hash: str) -> Optional[CacheEntry]:
        """通过内容哈希查找缓存"""
        key = self.fingerprints.get(content_hash)
        if key:
            return self.get(key)
        return None
    
    def put(self, key: str, content: str, content_type: str = 'default',
            metadata: Dict = None, etag: str = None, 
            last_modified: str = None, ttl_hours: int = None) -> CacheEntry:
        """
        存入缓存
        
        Args:
            key: 缓存键
            content: 内容
            content_type: 内容类型 (用于确定TTL)
            metadata: 元数据
            etag: HTTP ETag
            last_modified: HTTP Last-Modified
            ttl_hours: 自定义TTL (覆盖默认值)
        """
        with self._lock:
            # 检查是否已存在相同内容
            content_hash = ContentFingerprinter.sha256_hash(content)
            
            if content_hash in self.fingerprints:
                existing_key = self.fingerprints[content_hash]
                if existing_key in self.cache:
                    # 更新现有条目
                    entry = self.cache[existing_key]
                    entry.touch()
                    print(f"[SmartCache] 命中重复内容: {key} -> {existing_key}")
                    return entry
            
            # LRU淘汰
            self._evict_if_needed()
            
            # 确定TTL
            ttl = ttl_hours or self._get_ttl(content_type)
            
            # 创建条目
            entry = CacheEntry(
                key=key,
                content_hash=content_hash,
                raw_content=content[:10000] if len(content) > 10000 else content,  # 限制大小
                metadata=metadata or {},
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=ttl),
                etag=etag,
                last_modified=last_modified
            )
            
            # 存入缓存
            self.cache[key] = entry
            self.cache.move_to_end(key)
            self.fingerprints[content_hash] = key
            
            print(f"[SmartCache] 新增缓存: {key} (TTL: {ttl}h)")
            
            return entry
    
    def check_freshness(self, key: str, etag: str = None, 
                       last_modified: str = None) -> Tuple[bool, Optional[CacheEntry]]:
        """
        检查缓存新鲜度 (用于条件请求)
        
        Returns:
            (is_fresh, entry) - is_fresh为True表示缓存仍有效
        """
        entry = self.get(key)
        
        if not entry:
            return False, None
        
        # 检查ETag
        if etag and entry.etag == etag:
            return True, entry
        
        # 检查Last-Modified
        if last_modified and entry.last_modified == last_modified:
            return True, entry
        
        return False, entry
    
    def find_similar(self, content: str, threshold: int = 3) -> List[Tuple[str, int]]:
        """
        查找相似内容
        
        Returns:
            List of (key, hamming_distance)
        """
        target_hash = ContentFingerprinter.simhash(content)
        
        similar = []
        for entry in self.cache.values():
            # 计算与缓存内容的SimHash距离
            cached_hash = ContentFingerprinter.simhash(
                entry.raw_content or entry.content_hash
            )
            distance = ContentFingerprinter.hamming_distance(target_hash, cached_hash)
            
            if distance <= threshold:
                similar.append((entry.key, distance))
        
        # 按相似度排序
        similar.sort(key=lambda x: x[1])
        return similar
    
    def invalidate(self, key: str) -> bool:
        """使缓存失效"""
        with self._lock:
            entry = self.cache.pop(key, None)
            if entry:
                self.fingerprints.pop(entry.content_hash, None)
                print(f"[SmartCache] 缓存失效: {key}")
                return True
            return False
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """按模式使缓存失效"""
        import re
        
        with self._lock:
            keys_to_remove = [
                k for k in self.cache.keys()
                if re.search(pattern, k)
            ]
            
            for key in keys_to_remove:
                entry = self.cache.pop(key)
                self.fingerprints.pop(entry.content_hash, None)
            
            print(f"[SmartCache] 批量失效: {len(keys_to_remove)} 条")
            return len(keys_to_remove)
    
    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        with self._lock:
            expired_keys = [
                k for k, e in self.cache.items()
                if e.is_expired()
            ]
            
            for key in expired_keys:
                entry = self.cache.pop(key)
                self.fingerprints.pop(entry.content_hash, None)
            
            print(f"[SmartCache] 清理过期: {len(expired_keys)} 条")
            return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        with self._lock:
            total = len(self.cache)
            expired = sum(1 for e in self.cache.values() if e.is_expired())
            
            # 按类型统计
            by_type = {}
            for entry in self.cache.values():
                content_type = entry.metadata.get('content_type', 'unknown')
                by_type[content_type] = by_type.get(content_type, 0) + 1
            
            hit_rate = self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
            
            return {
                'total_entries': total,
                'expired_entries': expired,
                'active_entries': total - expired,
                'unique_fingerprints': len(self.fingerprints),
                'hit_count': self._hits,
                'miss_count': self._misses,
                'hit_rate': round(hit_rate, 2),
                'max_size': self.max_size,
                'utilization': round(total / self.max_size, 2),
                'by_type': by_type
            }
    
    def print_stats(self):
        """打印统计"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 智能缓存统计")
        print("="*60)
        print(f"总条目: {stats['total_entries']}")
        print(f"活跃: {stats['active_entries']} | 过期: {stats['expired_entries']}")
        print(f"命中率: {stats['hit_rate']:.1%} ({stats['hit_count']}/{stats['hit_count']+stats['miss_count']})")
        print(f"利用率: {stats['utilization']:.1%} ({stats['total_entries']}/{stats['max_size']})")
        print(f"唯一指纹: {stats['unique_fingerprints']}")
        
        if stats['by_type']:
            print(f"\n按类型分布:")
            for t, c in stats['by_type'].items():
                print(f"  {t}: {c}")
    
    def save(self):
        """手动保存缓存"""
        self._save_cache()


def test_smart_cache():
    """测试智能缓存"""
    print("="*70)
    print("🧪 测试智能缓存管理器")
    print("="*70)
    
    cache = SmartCache(max_size=100)
    
    # 测试1: 基本存取
    print("\n--- 测试1: 基本存取 ---")
    entry = cache.put('paper_001', 'This is a paper about AI', 'arxiv_paper')
    print(f"存入: {entry.key}, 哈希: {entry.content_hash[:16]}...")
    
    retrieved = cache.get('paper_001')
    if retrieved:
        print(f"获取: {retrieved.key}, 访问次数: {retrieved.access_count}")
    
    # 测试2: 去重
    print("\n--- 测试2: 内容去重 ---")
    entry2 = cache.put('paper_001_duplicate', 'This is a paper about AI', 'arxiv_paper')
    print(f"重复内容检测到: {entry2.key}")
    print(f"缓存条目数: {len(cache.cache)} (应仍为1)")
    
    # 测试3: 相似内容检测
    print("\n--- 测试3: 相似内容检测 ---")
    similar_content = 'This is a paper about artificial intelligence'
    similar = cache.find_similar(similar_content, threshold=5)
    print(f"相似内容: {similar}")
    
    # 测试4: 统计
    print("\n--- 测试4: 统计 ---")
    cache.print_stats()
    
    # 保存
    cache.save()
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == "__main__":
    test_smart_cache()
