"""
引用生成系统

生成 WebRooter 风格的引用格式:
- citations: 结构化引用数据
- references_text: 格式化文本
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def _clean_text(value: str, max_len: int = 280) -> str:
    """清理文本"""
    text = re.sub(r"\s+", " ", (value or "")).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len - 3].rstrip() + "..."


def _get_domain(url: str) -> str:
    """获取域名"""
    host = (urlparse(url or "").hostname or "").lower()
    if host.startswith("www."):
        return host[4:]
    return host


def build_citations(
    results: List[Dict[str, Any]],
    query: str,
    prefix: str = "S"
) -> List[Dict[str, Any]]:
    """
    构建标准化引用
    
    Args:
        results: 搜索结果列表
        query: 原始查询
        prefix: 引用 ID 前缀
    
    Returns:
        引用列表
    """
    citations: List[Dict[str, Any]] = []
    now = datetime.utcnow().isoformat()
    
    for idx, item in enumerate(results, 1):
        url = item.get("url", "")
        domain = _get_domain(url)
        
        citation_id = f"{prefix}{idx}"
        citations.append({
            "id": citation_id,
            "type": "web",
            "query": query,
            "title": _clean_text(item.get("title", "Untitled"), 200),
            "url": url,
            "domain": domain,
            "snippet": _clean_text(item.get("snippet", ""), 280),
            "retrieved_at": now
        })
        
        # 在原始结果中标记引用 ID
        if isinstance(item, dict):
            item["citation_id"] = citation_id
    
    return citations


def format_references(citations: List[Dict[str, Any]], max_items: int = 30) -> str:
    """
    格式化引用文本
    
    Args:
        citations: 引用列表
        max_items: 最大条目数
    
    Returns:
        格式化后的引用文本
    """
    if not citations:
        return ""
    
    lines = ["参考文献 / References:"]
    
    for item in citations[:max_items]:
        cid = item.get("id", "?")
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        domain = item.get("domain", "")
        
        if domain:
            lines.append(f"[{cid}] {title} ({domain}) {url}")
        else:
            lines.append(f"[{cid}] {title} {url}")
    
    return "\n".join(lines)


def build_comparison_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    生成跨来源对比统计
    
    Args:
        results: 搜索结果
    
    Returns:
        统计信息
    """
    by_domain: Dict[str, int] = {}
    
    for item in results:
        url = item.get("url", "")
        domain = _get_domain(url)
        if domain:
            by_domain[domain] = by_domain.get(domain, 0) + 1
    
    return {
        "total_results": len(results),
        "domain_coverage": len(by_domain),
        "top_domains": sorted(by_domain.items(), key=lambda x: x[1], reverse=True)[:10]
    }


def generate_citation_prompt(citations: List[Dict[str, Any]]) -> str:
    """
    生成用于提示词的引用说明
    
    用于指导 LLM 正确使用引用
    """
    if not citations:
        return ""
    
    prompt = """
请在回答中使用以下引用格式标注信息来源：
- 使用 [S1], [S2] 等形式标注引用
- 每个关键事实后都应标注来源
- 文末会自动附上参考文献列表

可用引用：
"""
    
    for c in citations[:10]:
        prompt += f"- [{c['id']}] {c['title']}\n"
    
    return prompt
