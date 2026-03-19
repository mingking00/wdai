#!/usr/bin/env python3
"""
wdai SearchAgent v1.0 - 优化搜索Agent
基于信息源评估结果，实现高质量、多源、验证的搜索能力
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys

sys.path.insert(0, '/root/.openclaw/workspace/.wdai-runtime')

# 导入IER连接器用于学习优化
from ier_connector_v1 import IERConnector, ReflectionInsight

WORKSPACE = Path("/root/.openclaw/workspace")
SEARCH_AGENT_DIR = WORKSPACE / ".search-agent"
SEARCH_AGENT_DIR.mkdir(exist_ok=True)

class SourcePriority(Enum):
    """信息源优先级"""
    P0 = "p0"  # 最高优先级，必查
    P1 = "p1"  # 高优先级，定期查
    P2 = "p2"  # 参考价值，按需查

@dataclass
class InformationSource:
    """信息源定义"""
    name: str
    url_pattern: str
    priority: SourcePriority
    source_type: str  # newsletter, blog, official, community
    language: str
    strengths: List[str]
    search_method: str  # kimi_search, web_fetch, browser
    reliability_score: float  # 0-1

@dataclass
class SearchResult:
    """搜索结果"""
    query: str
    source: InformationSource
    title: str
    url: str
    content: str
    timestamp: str
    quality_score: float = 0.0
    is_verified: bool = False

@dataclass
class ValidatedInsight:
    """验证后的洞察"""
    insight: str
    sources: List[str]  # 来源列表
    confidence: float  # 可信度
    extracted_at: str


class SourceRegistry:
    """
    信息源注册表
    基于评估结果，维护高质量信息源
    """
    
    def __init__(self):
        self.sources: Dict[str, InformationSource] = {}
        self._initialize_sources()
    
    def _initialize_sources(self):
        """初始化评估后的优质信息源"""
        
        # P0 - 最高优先级
        self.sources["therundown"] = InformationSource(
            name="The Rundown AI",
            url_pattern="therundown.ai",
            priority=SourcePriority.P0,
            source_type="newsletter",
            language="en",
            strengths=["daily_updates", "broad_coverage", "structured_format"],
            search_method="kimi_search",
            reliability_score=0.9
        )
        
        self.sources["tldr_ai"] = InformationSource(
            name="TLDR AI",
            url_pattern="tldr.tech/ai",
            priority=SourcePriority.P0,
            source_type="newsletter",
            language="en",
            strengths=["research_papers", "technical_depth", "concise"],
            search_method="kimi_search",
            reliability_score=0.9
        )
        
        self.sources["zhang_shanyou"] = InformationSource(
            name="张善友",
            url_pattern="cnblogs.com/shanyou",
            priority=SourcePriority.P0,
            source_type="blog",
            language="zh",
            strengths=["independent_analysis", "framework_insights", "dotnet_ai"],
            search_method="kimi_search",
            reliability_score=0.95
        )
        
        self.sources["datacamp"] = InformationSource(
            name="DataCamp",
            url_pattern="datacamp.com",
            priority=SourcePriority.P0,
            source_type="education",
            language="en",
            strengths=["framework_comparison", "hands_on_tutorials", "code_examples"],
            search_method="kimi_search",
            reliability_score=0.85
        )
        
        self.sources["github_blog"] = InformationSource(
            name="GitHub Blog",
            url_pattern="github.blog",
            priority=SourcePriority.P0,
            source_type="official",
            language="en",
            strengths=["first_hand_info", "cutting_edge", "authoritative"],
            search_method="web_fetch",
            reliability_score=0.95
        )
        
        # P1 - 高优先级
        self.sources["jiqizhixin"] = InformationSource(
            name="机器之心",
            url_pattern="jiqizhixin.com",
            priority=SourcePriority.P1,
            source_type="media",
            language="zh",
            strengths=["daily_news", "china_ai_ecosystem"],
            search_method="kimi_search",
            reliability_score=0.8
        )
        
        self.sources["bens_bites"] = InformationSource(
            name="Ben's Bites",
            url_pattern="bensbites.co",
            priority=SourcePriority.P1,
            source_type="newsletter",
            language="en",
            strengths=["startup_focus", "accessible_style", "community"],
            search_method="kimi_search",
            reliability_score=0.8
        )
        
        self.sources["smeuse"] = InformationSource(
            name="smeuse.org",
            url_pattern="blog.smeuse.org",
            priority=SourcePriority.P1,
            source_type="blog",
            language="en",
            strengths=["independent_views", "framework_analysis", "2026_trends"],
            search_method="kimi_search",
            reliability_score=0.85
        )
    
    def get_sources_by_priority(self, priority: SourcePriority) -> List[InformationSource]:
        """按优先级获取信息源"""
        return [s for s in self.sources.values() if s.priority == priority]
    
    def get_source(self, name: str) -> Optional[InformationSource]:
        """获取特定信息源"""
        return self.sources.get(name)


class SearchAgent:
    """
    搜索Agent - 优化搜索质量
    
    核心优化:
    1. 多源搜索 - 同时搜索P0/P1信息源
    2. 交叉验证 - 同一信息需2+来源确认
    3. 质量过滤 - 基于reliability_score筛选
    4. IER学习 - 记录搜索效果，优化未来搜索
    """
    
    def __init__(self):
        self.source_registry = SourceRegistry()
        self.ier_connector = IERConnector()
        self.search_history: List[Dict] = []
        self.validation_threshold = 0.7  # 可信度阈值
        
    async def search_multi_source(self, query: str, max_results_per_source: int = 3) -> List[SearchResult]:
        """
        多源搜索 - 从多个P0信息源搜索
        
        这是核心优化：不再单一搜索，而是从多个可信源获取
        """
        print(f"\n🔍 SearchAgent: 多源搜索 '{query}'")
        
        all_results = []
        
        # 1. 从P0信息源搜索
        p0_sources = self.source_registry.get_sources_by_priority(SourcePriority.P0)
        print(f"   查询 {len(p0_sources)} 个P0信息源...")
        
        for source in p0_sources:
            try:
                # 构建源特定的查询
                source_query = f"{query} site:{source.url_pattern}"
                
                # 模拟搜索（实际应调用kimi_search）
                results = await self._mock_search(source_query, source, max_results_per_source)
                all_results.extend(results)
                
                print(f"   ✓ {source.name}: {len(results)} 条结果")
                
            except Exception as e:
                print(f"   ✗ {source.name}: {e}")
        
        # 2. 质量过滤
        filtered_results = self._filter_by_quality(all_results)
        print(f"   质量过滤后: {len(filtered_results)} 条")
        
        # 3. 记录搜索历史
        self.search_history.append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "sources_queried": len(p0_sources),
            "results_total": len(all_results),
            "results_filtered": len(filtered_results)
        })
        
        return filtered_results
    
    async def _mock_search(self, query: str, source: InformationSource, limit: int) -> List[SearchResult]:
        """模拟搜索 - 实际实现应调用kimi_search"""
        # 这里返回模拟结果，实际应调用:
        # from kimi_search import kimi_search
        # return kimi_search(query, limit=limit, include_content=True)
        
        mock_results = []
        for i in range(min(limit, 2)):  # 模拟2条结果
            mock_results.append(SearchResult(
                query=query,
                source=source,
                title=f"Mock result {i+1} from {source.name}",
                url=f"https://{source.url_pattern}/article-{i}",
                content=f"This is mock content from {source.name} about {query}",
                timestamp=datetime.now().isoformat(),
                quality_score=source.reliability_score
            ))
        return mock_results
    
    def _filter_by_quality(self, results: List[SearchResult]) -> List[SearchResult]:
        """基于质量分数过滤结果"""
        return [r for r in results if r.quality_score >= self.validation_threshold]
    
    def cross_validate(self, results: List[SearchResult]) -> List[ValidatedInsight]:
        """
        交叉验证 - 同一信息需多个来源确认
        
        核心优化：识别被多个来源提及的信息，提高可信度
        """
        print(f"\n🔍 SearchAgent: 交叉验证 {len(results)} 条结果")
        
        # 提取关键洞察（简化版：按内容相似度分组）
        insights = {}
        
        for result in results:
            # 提取关键主题（简化实现）
            key = result.query  # 实际应使用NLP提取主题
            
            if key not in insights:
                insights[key] = {
                    "sources": [],
                    "contents": []
                }
            
            insights[key]["sources"].append(result.source.name)
            insights[key]["contents"].append(result.content)
        
        # 生成验证后的洞察
        validated = []
        for key, data in insights.items():
            # 多来源确认 = 更高可信度
            confidence = min(0.5 + len(data["sources"]) * 0.15, 0.95)
            
            validated.append(ValidatedInsight(
                insight=key,
                sources=data["sources"],
                confidence=confidence,
                extracted_at=datetime.now().isoformat()
            ))
        
        # 只返回高可信度的洞察
        high_confidence = [v for v in validated if v.confidence >= self.validation_threshold]
        print(f"   验证通过: {len(high_confidence)} 条 (confidence >= {self.validation_threshold})")
        
        return high_confidence
    
    async def search_with_validation(self, query: str) -> Dict[str, Any]:
        """
        完整搜索流程：多源搜索 + 质量过滤 + 交叉验证
        
        这是用户调用的主要接口
        """
        print("="*65)
        print(f"🔍 SearchAgent 启动搜索: {query}")
        print("="*65)
        
        # 1. 多源搜索
        results = await self.search_multi_source(query)
        
        if not results:
            return {
                "success": False,
                "query": query,
                "error": "未找到高质量结果",
                "insights": []
            }
        
        # 2. 交叉验证
        validated_insights = self.cross_validate(results)
        
        # 3. IER学习记录
        self.ier_connector.insights.append(ReflectionInsight(
            insight_id=f"search_{datetime.now().strftime('%H%M%S')}",
            source_task_id=f"search_{query[:20]}",
            insight_type="search_pattern",
            content=f"搜索'{query}'获得{len(validated_insights)}条验证洞察",
            confidence=0.8
        ))
        
        # 4. 返回结构化结果
        return {
            "success": True,
            "query": query,
            "results_count": len(results),
            "sources_used": list(set(r.source.name for r in results)),
            "validated_insights": [
                {
                    "insight": v.insight,
                    "confidence": v.confidence,
                    "sources": v.sources
                }
                for v in validated_insights
            ],
            "search_metadata": {
                "timestamp": datetime.now().isoformat(),
                "quality_threshold": self.validation_threshold,
                "sources_queried": len(self.source_registry.get_sources_by_priority(SourcePriority.P0))
            }
        }
    
    def generate_search_report(self, search_result: Dict[str, Any]) -> str:
        """生成可读的搜索报告"""
        if not search_result["success"]:
            return f"❌ 搜索失败: {search_result.get('error', '未知错误')}"
        
        report = f"""
# 搜索报告: {search_result['query']}

## 概览
- 查询时间: {search_result['search_metadata']['timestamp']}
- 结果数量: {search_result['results_count']}
- 使用信息源: {', '.join(search_result['sources_used'])}

## 验证后的洞察
"""
        for i, insight in enumerate(search_result['validated_insights'], 1):
            report += f"""
### {i}. {insight['insight']}
- 可信度: {insight['confidence']:.0%}
- 来源: {', '.join(insight['sources'])}
"""
        
        report += """
## 来源说明
本次搜索使用了以下P0级信息源：
- The Rundown AI: 每日AI动态，覆盖广
- TLDR AI: 研究论文，技术深度
- 张善友: 独立分析，框架洞察
- DataCamp: 框架对比，实操教程
- GitHub Blog: 官方发布，前沿技术
"""
        
        return report


async def demo_search_agent():
    """演示优化后的SearchAgent"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     🔍 SearchAgent v1.0 - 优化搜索演示                      ║")
    print("║     多源搜索 + 质量过滤 + 交叉验证                          ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    agent = SearchAgent()
    
    # 演示搜索
    query = "AI Agent framework comparison 2025"
    result = await agent.search_with_validation(query)
    
    # 生成报告
    report = agent.generate_search_report(result)
    print(report)
    
    print("\n" + "="*65)
    print("✅ SearchAgent演示完成")
    print("="*65)
    print()
    print("💡 核心优化:")
    print("   • 多源搜索: 同时查询5个P0级信息源")
    print("   • 质量过滤: reliability_score >= 0.7")
    print("   • 交叉验证: 多来源确认的信息可信度更高")
    print("   • IER学习: 自动记录搜索模式，持续优化")


if __name__ == '__main__':
    asyncio.run(demo_search_agent())
