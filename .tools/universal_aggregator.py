#!/usr/bin/env python3
"""
通用信息源聚合器
支持多平台内容抓取和统一评分
"""

import json
import requests
from pathlib import Path

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    print("⚠️ feedparser 未安装，RSS功能暂不可用")
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

BASE_DIR = Path("/root/.openclaw/workspace")
SOURCES_FILE = BASE_DIR / "memory/core/universal_sources.md"
TASTE_MODEL = BASE_DIR / ".claw-status/data/taste_model.json"
QUEUE_DIR = BASE_DIR / ".claw-status/data/queues"

@dataclass
class ContentItem:
    """统一内容格式"""
    id: str
    title: str
    author: str
    platform: str  # bilibili, youtube, hackernews, etc.
    url: str
    summary: str
    published_at: str
    score: float = 0.0
    notify_strategy: str = "weekly"  # immediate, daily, weekly
    
    def to_dict(self):
        return asdict(self)


class TasteScorer:
    """统一的品味评分器"""
    
    def __init__(self):
        self.keywords = {
            # P0 强信号
            "agent": 1.0, "claude": 1.0, "llm": 1.0, 
            "multi-agent": 1.0, "autonomous": 1.0,
            "openclaw": 1.0, "claude code": 1.0,
            # P1 高信号
            "architecture": 0.8, "framework": 0.8,
            "efficiency": 0.8, "automation": 0.8,
            "practice": 0.8, "case study": 0.8,
            # 中文关键词
            "架构": 0.8, "系统": 0.8, "框架": 0.8,
            "效率": 0.8, "自动化": 0.8, "实践": 0.8,
        }
        self.trusted_sources = self._load_trusted_sources()
    
    def _load_trusted_sources(self) -> Dict[str, float]:
        """加载信任的来源列表"""
        return {
            # B站
            "慢学AI": 0.5, "易-ZX": 0.4, "GitHub很棒": 0.4,
            # YouTube (待添加)
            # Newsletter (待添加)
        }
    
    def score(self, item: ContentItem) -> float:
        """给内容打分"""
        score = 0.0
        text = (item.title + " " + item.summary).lower()
        
        # 关键词匹配
        for kw, weight in self.keywords.items():
            if kw in text:
                score += weight
        
        # 来源信任度
        if item.author in self.trusted_sources:
            score += self.trusted_sources[item.author]
        
        return min(score, 2.0)
    
    def get_strategy(self, score: float) -> str:
        if score >= 1.2:
            return "immediate"
        elif score >= 0.7:
            return "daily"
        return "weekly"


class SourceConnector:
    """信息源连接器基类"""
    
    def fetch(self, source_config: Dict) -> List[ContentItem]:
        raise NotImplementedError


class BilibiliConnector(SourceConnector):
    """B站连接器"""
    
    def fetch(self, config: Dict) -> List[ContentItem]:
        """从收藏夹获取"""
        import sys
        sys.path.insert(0, str(BASE_DIR / ".tools"))
        
        try:
            with open(BASE_DIR / "tools/bilibili_favorites.json", 'r') as f:
                videos = json.load(f)
            
            cutoff = (datetime.now() - timedelta(days=1)).timestamp()
            items = []
            
            for v in videos:
                if v.get("收藏时间", 0) > cutoff:
                    items.append(ContentItem(
                        id=f"bili_{v['Bvid']}",
                        title=v["标题"],
                        author=v["UP主"],
                        platform="bilibili",
                        url=v["链接"],
                        summary=v.get("简介", "")[:200],
                        published_at=datetime.fromtimestamp(v["收藏时间"]).isoformat()
                    ))
            
            return items
        except Exception as e:
            print(f"B站获取失败: {e}")
            return []


class RSSConnector(SourceConnector):
    """RSS通用连接器"""
    
    def fetch(self, config: Dict) -> List[ContentItem]:
        """从RSS feed获取"""
        if not FEEDPARSER_AVAILABLE:
            print("⚠️ RSS功能需要 feedparser: pip install feedparser")
            return []
        
        url = config.get("url")
        platform = config.get("platform", "rss")
        
        try:
            feed = feedparser.parse(url)
            items = []
            
            for entry in feed.entries[:10]:  # 最近10条
                published = entry.get("published", "")
                items.append(ContentItem(
                    id=f"{platform}_{entry.get('id', '')}",
                    title=entry.get("title", ""),
                    author=entry.get("author", config.get("name", "unknown")),
                    platform=platform,
                    url=entry.get("link", ""),
                    summary=entry.get("summary", "")[:300],
                    published_at=published
                ))
            
            return items
        except Exception as e:
            print(f"RSS获取失败 ({url}): {e}")
            return []


class UniversalAggregator:
    """通用信息聚合器"""
    
    def __init__(self):
        self.scorer = TasteScorer()
        self.connectors = {
            "bilibili": BilibiliConnector(),
            "rss": RSSConnector(),
            "hackernews": RSSConnector(),
            "youtube": RSSConnector(),
        }
        self.sources = self._load_sources()
    
    def _load_sources(self) -> List[Dict]:
        """加载配置的来源列表"""
        # 从markdown解析（简化版）
        return [
            {
                "name": "B站收藏夹",
                "type": "bilibili",
                "enabled": True,
                "config": {}
            },
            # 待添加更多来源...
        ]
    
    def add_source(self, source_config: Dict) -> bool:
        """添加新信息源"""
        required = ["name", "type", "config"]
        if not all(k in source_config for k in required):
            print(f"❌ 缺少必要字段: {required}")
            return False
        
        self.sources.append(source_config)
        print(f"✅ 已添加信息源: {source_config['name']}")
        print(f"   类型: {source_config['type']}")
        print(f"   下次同步时生效")
        return True
    
    def fetch_all(self) -> List[ContentItem]:
        """抓取所有来源的内容"""
        all_items = []
        
        for source in self.sources:
            if not source.get("enabled", True):
                continue
            
            source_type = source.get("type")
            connector = self.connectors.get(source_type)
            
            if connector:
                try:
                    items = connector.fetch(source.get("config", {}))
                    all_items.extend(items)
                    print(f"✅ {source['name']}: {len(items)} 条新内容")
                except Exception as e:
                    print(f"❌ {source['name']}: {e}")
        
        return all_items
    
    def process(self) -> Dict:
        """处理所有内容"""
        items = self.fetch_all()
        
        # 评分
        for item in items:
            item.score = self.scorer.score(item)
            item.notify_strategy = self.scorer.get_strategy(item.score)
        
        # 排序
        items.sort(key=lambda x: x.score, reverse=True)
        
        # 分类
        immediate = [i for i in items if i.notify_strategy == "immediate"]
        daily = [i for i in items if i.notify_strategy == "daily"]
        weekly = [i for i in items if i.notify_strategy == "weekly"]
        
        # 保存队列
        self._save_queues(immediate, daily, weekly)
        
        return {
            "total": len(items),
            "immediate": len(immediate),
            "daily": len(daily),
            "weekly": len(weekly),
            "top_items": [i.to_dict() for i in items[:5]]
        }
    
    def _save_queues(self, immediate: List[ContentItem], 
                     daily: List[ContentItem], 
                     weekly: List[ContentItem]):
        """保存到队列"""
        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        
        for name, items in [("immediate", immediate), 
                           ("daily", daily), 
                           ("weekly", weekly)]:
            file_path = QUEUE_DIR / f"{name}_queue.json"
            
            existing = []
            if file_path.exists():
                with open(file_path, 'r') as f:
                    existing = json.load(f)
            
            # 添加新内容（去重）
            existing_ids = {e.get("id") for e in existing}
            for item in items:
                if item.id not in existing_ids:
                    existing.append(item.to_dict())
            
            with open(file_path, 'w') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
    
    def list_sources(self) -> List[Dict]:
        """列出所有来源"""
        return self.sources


def main():
    """主函数"""
    print("🌐 通用信息源聚合器")
    print("=" * 50)
    
    aggregator = UniversalAggregator()
    
    # 显示当前来源
    print("\n📡 监控中的来源:")
    for s in aggregator.list_sources():
        status = "✅" if s.get("enabled") else "⏸️"
        print(f"  {status} {s['name']} ({s['type']})")
    
    # 抓取和处理
    print("\n🔍 开始抓取...")
    result = aggregator.process()
    
    print(f"\n📊 处理结果:")
    print(f"  总计: {result['total']} 条")
    print(f"  立即推送: {result['immediate']} 条")
    print(f"  每日汇总: {result['daily']} 条")
    print(f"  周报: {result['weekly']} 条")
    
    if result['top_items']:
        print(f"\n🏆 高分内容 TOP 5:")
        for i, item in enumerate(result['top_items'], 1):
            print(f"  {i}. [{item['score']:.2f}] {item['title'][:40]}...")
            print(f"     来源: {item['platform']} | 作者: {item['author']}")


if __name__ == "__main__":
    main()
