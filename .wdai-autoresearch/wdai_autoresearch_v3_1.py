#!/usr/bin/env python3
"""
wdai AutoResearch v3.1 - Brave Search 真实API版
使用真实的 Brave Search API 进行搜索
"""

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

WORKSPACE = Path("/root/.openclaw/workspace")
AUTORESEARCH_DIR = WORKSPACE / ".wdai-autoresearch"

# 加载环境变量
env_file = AUTORESEARCH_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().strip().split('\n'):
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key] = value

sys.path.insert(0, str(AUTORESEARCH_DIR))

import aiohttp
from wdai_autoresearch_v3 import (
    ResearchTask, Experiment, ResearchPhase, AgentRole,
    IERStorage, StrategistAgentV3, ArchitectAgentV3,
    CoderAgentV3, ReviewerAgentV3, EvolutionAgentV3,
    CoordinatorAgentV3
)


class RealBraveSearchBackend:
    """真实的 Brave Search API 后端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('BRAVE_API_KEY')
        if not self.api_key:
            raise ValueError("Brave API key required. Set BRAVE_API_KEY env var.")
    
    async def search(self, query: str, count: int = 3) -> List[Dict]:
        """使用 Brave Search API 搜索"""
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        params = {
            "q": query,
            "count": min(count, 20),
            "offset": 0,
            "mkt": "en-US",
            "safesearch": "moderate",
            "freshness": "py",
            "text_decorations": "False",
            "text_snippets": "True"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    
                    web_results = data.get("web", {}).get("results", [])
                    for item in web_results[:count]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "description": item.get("description", "")[:500],
                            "age": item.get("age", ""),
                            "page_age": item.get("page_age", "")
                        })
                    
                    return results
                else:
                    error_text = await resp.text()
                    print(f"   ⚠️ Brave API 错误 {resp.status}: {error_text[:100]}")
                    return []
    
    async def fetch(self, url: str, max_chars: int = 2000) -> str:
        """获取网页内容 (简化版)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; wdai-research/1.0)"
                }) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        # 简单清理HTML标签
                        import re
                        text = re.sub(r'<[^>]+>', ' ', text)
                        text = re.sub(r'\s+', ' ', text)
                        return text[:max_chars]
                    return f"HTTP {resp.status}"
        except Exception as e:
            return f"Error: {str(e)[:100]}"


class RealResearcherAgentV3_1:
    """Researcher v3.1 - 真实 Brave Search"""
    
    def __init__(self, ier: IERStorage, search_backend: RealBraveSearchBackend):
        self.ier = ier
        self.search = search_backend
    
    async def gather(self, task: ResearchTask) -> Dict[str, Any]:
        """Phase 1: 真实 Brave Search"""
        print(f"\n📚 Phase 1: GATHER (Researcher) - Brave Search API")
        print(f"   主题: {task.topic}")
        print(f"   假设: {task.hypothesis}")
        
        queries = [
            f"{task.topic} 2024",
            f"{task.topic} best practices tutorial",
        ]
        
        info_sources = []
        
        for query in queries:
            try:
                print(f"   🔍 Brave搜索: {query[:50]}...")
                
                results = await self.search.search(query, count=2)
                
                if results:
                    for r in results:
                        print(f"   📄 结果: {r['title'][:60]}...")
                        info_sources.append({
                            "query": query,
                            "title": r.get('title', ''),
                            "url": r.get('url', ''),
                            "description": r.get('description', '')[:300],
                            "source": "brave_search"
                        })
                else:
                    info_sources.append({
                        "query": query,
                        "source": "brave_search",
                        "status": "no_results"
                    })
                    
            except Exception as e:
                print(f"   ⚠️ 错误: {str(e)[:80]}")
                info_sources.append({
                    "query": query,
                    "source": "error",
                    "error": str(e)[:100]
                })
        
        task.gathered_info = info_sources
        
        successful = len([s for s in info_sources if s.get('title')])
        
        self.ier.record(
            task.id, ResearchPhase.GATHER, AgentRole.RESEARCHER,
            f"Brave Search完成: {len(queries)}个查询, {successful}个结果",
            "v3.1: 真实Brave Search API调用",
            json.dumps(info_sources[:2], ensure_ascii=False)
        )
        
        print(f"   ✅ 搜索完成: {successful}个结果")
        return {"sources": info_sources, "successful": successful}


class CoordinatorAgentV3_1:
    """Coordinator v3.1 - 真实Brave Search版"""
    
    def __init__(self):
        self.ier = IERStorage("v3.1")
        
        # 使用真实 Brave Search
        try:
            brave_backend = RealBraveSearchBackend()
            self.researcher = RealResearcherAgentV3_1(self.ier, brave_backend)
            self.using_real_search = True
        except ValueError as e:
            print(f"⚠️ Brave API 未配置: {e}")
            from wdai_autoresearch_v3 import MockSearchBackend, ResearcherAgentV3
            self.researcher = ResearcherAgentV3(self.ier, MockSearchBackend())
            self.using_real_search = False
        
        self.strategist = StrategistAgentV3(self.ier)
        self.architect = ArchitectAgentV3(self.ier)
        self.coder = CoderAgentV3(self.ier)
        self.reviewer = ReviewerAgentV3(self.ier)
        self.evolution = EvolutionAgentV3(self.ier)
        self.tasks = {}
    
    def create_task(self, topic: str, hypothesis: str, complexity: int = 5) -> ResearchTask:
        task = ResearchTask(
            id=str(uuid.uuid4())[:8],
            topic=topic,
            hypothesis=hypothesis,
            complexity=complexity
        )
        self.tasks[task.id] = task
        
        backend_type = "Brave Search API" if self.using_real_search else "Mock"
        print(f"\n{'='*70}")
        print(f"🔬 wdai AutoResearch v3.1: 任务 #{task.id}")
        print(f"   后端: {backend_type}")
        print(f"{'='*70}")
        print(f"   主题: {topic}")
        print(f"   假设: {hypothesis}")
        
        return task
    
    async def run_research(self, task: ResearchTask) -> ResearchTask:
        print(f"\n🚀 启动v3.1研究流程 (Brave Search)")
        
        await self.researcher.gather(task)
        await self.strategist.formulate(task)
        await self.architect.design(task)
        
        experiments = await self.coder.implement_and_run(task)
        await self.reviewer.validate(task, experiments)
        await self.evolution.evolve(task)
        
        print(f"\n{'='*70}")
        print(f"✅ 任务 #{task.id} 完成 (v3.1)")
        print(f"{'='*70}")
        
        return task


async def demo():
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║     🔬 wdai AutoResearch v3.1 - Brave Search 真实API版              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    
    # 检查API key
    api_key = os.environ.get('BRAVE_API_KEY', '未设置')
    masked_key = api_key[:4] + '****' + api_key[-4:] if len(api_key) > 8 else '****'
    print(f"   API Key: {masked_key}")
    print()
    
    coordinator = CoordinatorAgentV3_1()
    
    task = coordinator.create_task(
        topic="Python asyncio并发性能优化",
        hypothesis="asyncio.gather可以显著提高I/O密集型任务性能",
        complexity=7
    )
    
    await coordinator.run_research(task)
    
    print(f"\n📊 v3.1 完成:")
    if coordinator.using_real_search:
        print("   ✅ 使用真实 Brave Search API")
        print("   ✅ 获取真实搜索结果")
    else:
        print("   ⚠️ 使用Mock后端 (API key未配置)")


if __name__ == '__main__':
    asyncio.run(demo())
