"""
DuckDuckGo 搜索适配器

无需 API Key 的搜索方案
"""

from typing import List, Dict


def search_duckduckgo(query: str, count: int = 8) -> List[Dict]:
    """
    使用 DuckDuckGo 搜索
    
    优点：
    - 无需 API Key
    - 免费使用
    - 隐私友好
    
    缺点：
    - 可能有速率限制
    - 结果质量略低于专业搜索引擎
    
    Args:
        query: 搜索查询
        count: 结果数量
    
    Returns:
        搜索结果列表
    """
    try:
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=count):
                results.append({
                    "title": r["title"],
                    "url": r["href"],
                    "snippet": r["body"],
                    "domain": r.get("domain", "")
                })
        
        return results
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
        return []


# 添加到 research_engine.py 的备选方案
# 在 _search_with_fallback 方法中添加：
"""
try:
    from .duckduckgo_adapter import search_duckduckgo
    results = search_duckduckgo(query, count=self.config.num_results)
    if results:
        return results
except Exception:
    pass
"""
