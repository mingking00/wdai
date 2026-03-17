"""
双层缓存系统

- 内存层: LRU 策略，快速访问
- SQLite层: 持久化，跨会话保留
"""

import asyncio
import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: Any
    created_at: float
    expires_at: float
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class MemoryCache:
    """LRU 内存缓存"""
    
    def __init__(self, max_size: int = 128, max_bytes: int = 32 * 1024 * 1024):
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._max_size = max_size
        self._max_bytes = max_bytes
        self._current_bytes = 0
        self._hits = 0
        self._misses = 0
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                self._remove(key)
                self._misses += 1
                return None
            
            # LRU 更新
            self._access_order.remove(key)
            self._access_order.append(key)
            entry.hit_count += 1
            self._hits += 1
            return entry
    
    async def set(self, key: str, data: Any, ttl: int = 3600):
        async with self._lock:
            # 估算大小
            try:
                entry_size = len(json.dumps(data).encode())
            except:
                entry_size = 1024  # 默认值
            
            if entry_size > self._max_bytes:
                return
            
            # 淘汰旧条目
            while (len(self._cache) >= self._max_size or 
                   self._current_bytes + entry_size > self._max_bytes):
                if not self._access_order:
                    break
                oldest = self._access_order.pop(0)
                self._remove(oldest)
            
            # 存储
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=time.time(),
                expires_at=time.time() + ttl,
                hit_count=0
            )
            self._cache[key] = entry
            self._access_order.append(key)
            self._current_bytes += entry_size
    
    def _remove(self, key: str):
        entry = self._cache.pop(key, None)
        if entry:
            try:
                size = len(json.dumps(entry.data).encode())
            except:
                size = 1024
            self._current_bytes = max(0, self._current_bytes - size)
            if key in self._access_order:
                self._access_order.remove(key)
    
    def get_stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "current_bytes": self._current_bytes,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0
        }


class SQLiteCache:
    """SQLite 持久化缓存"""
    
    def __init__(self, db_path: str, max_size: int = 5000):
        self._db_path = db_path
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._init_db()
    
    def _init_db(self):
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS research_cache (
                key TEXT PRIMARY KEY,
                data TEXT,
                created_at REAL,
                expires_at REAL,
                hit_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON research_cache(expires_at)")
        conn.commit()
        conn.close()
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        conn = sqlite3.connect(self._db_path)
        try:
            cursor = conn.execute(
                "SELECT data, created_at, expires_at, hit_count FROM research_cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if not row:
                self._misses += 1
                return None
            
            data, created_at, expires_at, hit_count = row
            if time.time() > expires_at:
                conn.execute("DELETE FROM research_cache WHERE key = ?", (key,))
                conn.commit()
                self._misses += 1
                return None
            
            # 更新命中计数
            conn.execute(
                "UPDATE research_cache SET hit_count = hit_count + 1 WHERE key = ?",
                (key,)
            )
            conn.commit()
            self._hits += 1
            
            return CacheEntry(
                key=key,
                data=json.loads(data),
                created_at=created_at,
                expires_at=expires_at,
                hit_count=hit_count + 1
            )
        finally:
            conn.close()
    
    async def set(self, key: str, data: Any, ttl: int = 3600):
        conn = sqlite3.connect(self._db_path)
        try:
            # 清理过期条目
            conn.execute("DELETE FROM research_cache WHERE expires_at < ?", (time.time(),))
            
            # 检查大小限制
            count = conn.execute("SELECT COUNT(*) FROM research_cache").fetchone()[0]
            if count >= self._max_size:
                # 删除最旧的
                conn.execute("""
                    DELETE FROM research_cache WHERE key = (
                        SELECT key FROM research_cache ORDER BY created_at LIMIT 1
                    )
                """)
            
            # 插入新条目
            conn.execute(
                "INSERT OR REPLACE INTO research_cache VALUES (?, ?, ?, ?, 0)",
                (key, json.dumps(data), time.time(), time.time() + ttl)
            )
            conn.commit()
        finally:
            conn.close()


class TieredCache:
    """双层缓存"""
    
    def __init__(self, config):
        self.memory = MemoryCache(
            max_size=config.cache_memory_max_size,
            max_bytes=config.cache_memory_max_bytes
        )
        self.sqlite = SQLiteCache(
            db_path=config.cache_sqlite_path,
            max_size=5000
        )
    
    async def get(self, key: str) -> Optional[Any]:
        # 先查内存
        entry = await self.memory.get(key)
        if entry:
            return entry.data
        
        # 再查 SQLite
        entry = await self.sqlite.get(key)
        if entry:
            # 回填内存
            ttl = int(entry.expires_at - time.time())
            if ttl > 0:
                await self.memory.set(key, entry.data, ttl)
            return entry.data
        
        return None
    
    async def set(self, key: str, data: Any, ttl: int = 3600):
        await self.memory.set(key, data, ttl)
        await self.sqlite.set(key, data, ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "memory": self.memory.get_stats(),
            "sqlite": {
                "hits": self.sqlite._hits,
                "misses": self.sqlite._misses
            }
        }
