"""
配置管理
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal


@dataclass
class ResearchConfig:
    """研究工具配置"""
    
    # 缓存配置
    cache_memory_max_size: int = 128
    cache_memory_max_bytes: int = 32 * 1024 * 1024  # 32MB
    cache_sqlite_path: str = field(default_factory=lambda: str(
        Path.home() / ".openclaw" / "deep_research_cache.db"
    ))
    cache_ttl_seconds: int = 3600  # 1小时
    
    # 研究深度配置
    max_depth: int = 3
    max_branches: int = 4
    max_nodes: int = 14
    
    # 搜索配置
    default_sources: List[str] = field(default_factory=lambda: ["web"])
    num_results: int = 8
    
    # 抓取配置
    fetch_timeout: int = 30
    auto_fallback: bool = True  # HTTP 失败时自动使用 browser
    max_html_chars: int = 80000
    
    # 压力控制
    pressure_level: Literal["normal", "elevated", "high", "critical"] = "normal"
    
    def __post_init__(self):
        """从环境变量加载配置"""
        # 缓存配置
        if ttl := os.getenv("DEEP_RESEARCH_CACHE_TTL"):
            self.cache_ttl_seconds = int(ttl)
        
        if size := os.getenv("DEEP_RESEARCH_CACHE_SIZE"):
            self.cache_memory_max_size = int(size)
        
        if path := os.getenv("DEEP_RESEARCH_CACHE_PATH"):
            self.cache_sqlite_path = path
        
        # 研究配置
        if depth := os.getenv("DEEP_RESEARCH_MAX_DEPTH"):
            self.max_depth = int(depth)
        
        if branches := os.getenv("DEEP_RESEARCH_MAX_BRANCHES"):
            self.max_branches = int(branches)
        
        # 抓取配置
        if chars := os.getenv("DEEP_RESEARCH_MAX_CHARS"):
            self.max_html_chars = int(chars)
        
        if fallback := os.getenv("DEEP_RESEARCH_AUTO_FALLBACK"):
            self.auto_fallback = fallback.lower() in ("1", "true", "yes", "on")
