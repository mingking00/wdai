"""
Deep Research Skill for OpenClaw

提供快速、标准、深度三种研究模式
"""

from typing import Any, Dict, List, Literal, Optional
import asyncio

from .research_engine import ResearchEngine, ResearchResult, ResearchConfig

__version__ = "1.0.0"
__all__ = ["run", "research", "ResearchEngine", "ResearchResult"]


# 全局引擎实例（懒加载）
_engine: Optional[ResearchEngine] = None


def _get_engine() -> ResearchEngine:
    """获取或创建全局引擎实例"""
    global _engine
    if _engine is None:
        _engine = ResearchEngine()
    return _engine


async def research(
    query: str,
    depth: Literal["quick", "standard", "deep"] = "standard",
    sources: Optional[List[str]] = None,
    max_results: int = 10
) -> ResearchResult:
    """
    执行研究任务
    
    Args:
        query: 研究问题
        depth: 研究深度 (quick/standard/deep)
        sources: 搜索源列表
        max_results: 最大结果数
    
    Returns:
        ResearchResult: 研究结果
    """
    engine = _get_engine()
    return await engine.research(
        query=query,
        depth=depth,
        sources=sources
    )


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Skill 入口函数
    
    Args:
        params: {
            "query": str,          # 必填
            "depth": str,          # 可选，默认 "standard"
            "sources": List[str],  # 可选
            "max_results": int     # 可选，默认 10
        }
    
    Returns:
        {
            "success": bool,
            "answer": str,
            "references_text": str,
            "citations": List[Dict],
            "sources_count": int,
            "exploration_path": List[Dict],
            "metadata": Dict
        }
    """
    query = params.get("query") or params.get("task")
    depth = params.get("depth", "standard")
    sources = params.get("sources")
    max_results = params.get("max_results", 10)
    
    if not query:
        return {
            "success": False,
            "error": "Missing required parameter: 'query' or 'task'",
            "answer": "",
            "references_text": "",
            "citations": [],
            "sources_count": 0,
            "exploration_path": [],
            "metadata": {}
        }
    
    try:
        result = await research(
            query=query,
            depth=depth,
            sources=sources
        )
        
        return {
            "success": result.success,
            "answer": result.answer,
            "references_text": result.references_text,
            "citations": result.citations,
            "sources_count": len(result.sources),
            "exploration_path": result.exploration_path,
            "metadata": {
                **result.metadata,
                "query": query,
                "requested_depth": depth
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "answer": f"研究执行失败: {str(e)}",
            "references_text": "",
            "citations": [],
            "sources_count": 0,
            "exploration_path": [],
            "metadata": {"error": str(e)}
        }


# 流式接口
async def run_stream(params: Dict[str, Any]):
    """
    流式执行研究任务
    
    Yields:
        Dict: 进度事件
    """
    query = params.get("query") or params.get("task")
    depth = params.get("depth", "standard")
    
    if not query:
        yield {"event": "error", "error": "Missing query parameter"}
        return
    
    engine = _get_engine()
    
    yield {"event": "start", "query": query, "depth": depth}
    
    if depth == "deep":
        # 分解阶段
        seeds = await engine._decompose_query(query)
        yield {"event": "decomposed", "seeds": seeds}
        
        # 层级搜索
        root_results = await engine._search_with_fallback(query)
        yield {"event": "level_complete", "depth": 0, "results": len(root_results)}
        
        seed_results = await asyncio.gather(*[
            engine._search_with_fallback(seed["query"])
            for seed in seeds
        ])
        total = sum(len(r) for r in seed_results)
        yield {"event": "level_complete", "depth": 1, "results": total}
    else:
        results = await engine._search_with_fallback(query)
        yield {"event": "search_complete", "results": len(results)}
    
    # 最终结果
    result = await engine.research(query, depth=depth)
    yield {"event": "complete", "result": result}
