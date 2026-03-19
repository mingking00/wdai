#!/usr/bin/env python3
"""
灵感摄取系统 - 数据模型
定义InspirationRecord和相关数据类
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
import uuid
import json

class InspirationStatus(Enum):
    """灵感记录状态"""
    NEW = "new"              # 新发现，待处理
    PENDING = "pending"      # 待人工审核
    APPROVED = "approved"    # 已批准，待进化
    REJECTED = "rejected"    # 已拒绝
    EVOLVED = "evolved"      # 已完成evo任务创建
    ARCHIVED = "archived"    # 已归档

class InspirationSource(Enum):
    """灵感来源"""
    ARXIV = "arxiv"
    GITHUB_REPO = "github_repo"
    GITHUB_TRENDING = "github_trending"
    GITHUB_RELEASE = "github_release"
    NEWS = "news"
    TWITTER = "twitter"
    OTHER = "other"

class Priority(Enum):
    """优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class InspirationRecord:
    """
    灵感记录数据类
    存储从各种来源获取的灵感信息
    """
    # 基础信息
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    url: str = ""
    source: str = ""
    source_type: str = ""
    
    # 内容
    summary: str = ""
    abstract: str = ""
    content: str = ""
    keywords: List[str] = field(default_factory=list)
    
    # 作者/项目信息
    authors: List[str] = field(default_factory=list)
    author_profiles: Dict[str, str] = field(default_factory=dict)
    project_name: str = ""
    project_owner: str = ""
    
    # 评分
    quality_score: float = 0.0
    relevance_score: float = 0.0
    novelty_score: float = 0.0
    impact_score: float = 0.0
    timeliness_score: float = 0.0
    trend_score: float = 0.0
    
    # 状态和元数据
    status: str = field(default_factory=lambda: InspirationStatus.NEW.value)
    priority: str = field(default_factory=lambda: Priority.MEDIUM.value)
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    published_at: str = ""
    reviewed_at: Optional[str] = None
    evolved_at: Optional[str] = None
    archived_at: Optional[str] = None
    
    # 审核信息
    reviewer: Optional[str] = None
    review_note: str = ""
    
    # 关联
    related_evo: List[str] = field(default_factory=list)
    related_inspirations: List[str] = field(default_factory=list)
    duplicates: List[str] = field(default_factory=list)
    
    # Evo集成
    evo_task_id: Optional[str] = None
    evo_task_created: bool = False
    
    # 额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InspirationRecord':
        """从字典创建实例"""
        # 过滤掉不存在的字段
        valid_fields = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'InspirationRecord':
        """从JSON字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_quality_breakdown(self) -> Dict[str, float]:
        """获取质量分数详细分解"""
        return {
            "relevance": self.relevance_score,
            "novelty": self.novelty_score,
            "impact": self.impact_score,
            "timeliness": self.timeliness_score,
            "overall": self.quality_score
        }
    
    def approve(self, reviewer: str, note: str = ""):
        """批准此灵感"""
        self.status = InspirationStatus.APPROVED.value
        self.reviewer = reviewer
        self.review_note = note
        self.reviewed_at = datetime.now().isoformat()
    
    def reject(self, reviewer: str, note: str = ""):
        """拒绝此灵感"""
        self.status = InspirationStatus.REJECTED.value
        self.reviewer = reviewer
        self.review_note = note
        self.reviewed_at = datetime.now().isoformat()
    
    def mark_evolved(self, evo_task_id: str):
        """标记为已完成进化"""
        self.status = InspirationStatus.EVOLVED.value
        self.evo_task_id = evo_task_id
        self.evo_task_created = True
        self.evolved_at = datetime.now().isoformat()
    
    def archive(self):
        """归档此灵感"""
        self.status = InspirationStatus.ARCHIVED.value
        self.archived_at = datetime.now().isoformat()
    
    def is_duplicate_of(self, other: 'InspirationRecord') -> bool:
        """检查是否与另一条记录重复"""
        # URL精确匹配
        if self.url and self.url == other.url:
            return True
        # ID匹配
        if self.id == other.id:
            return True
        return False
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, InspirationRecord):
            return False
        return self.id == other.id


@dataclass
class CrawlResult:
    """抓取结果"""
    success: bool
    source: str
    items_found: int
    items_new: int
    items_duplicate: int
    items_filtered: int
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AnalysisResult:
    """分析结果"""
    inspiration_id: str
    quality_score: float
    trend_score: float
    summary: str = ""
    keywords: List[str] = field(default_factory=list)
    related_evo: List[str] = field(default_factory=list)
    duplicates_detected: List[str] = field(default_factory=list)
    processed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class QueueStats:
    """队列统计"""
    total: int = 0
    new: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    evolved: int = 0
    archived: int = 0
    by_source: Dict[str, int] = field(default_factory=dict)
    by_priority: Dict[str, int] = field(default_factory=dict)
    avg_quality_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SystemHealth:
    """系统健康状态"""
    status: str = "unknown"
    last_crawl: Optional[str] = None
    last_analysis: Optional[str] = None
    queue_size: int = 0
    storage_usage_mb: float = 0.0
    api_quota_remaining: Optional[int] = None
    errors_last_24h: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)