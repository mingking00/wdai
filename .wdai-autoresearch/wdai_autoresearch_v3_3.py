#!/usr/bin/env python3
"""
wdai AutoResearch v3.3 - Self-Navigating 经验复用版
整合阿里 AgentEvolver 的 Self-Navigating 机制

核心改进:
- IER记录向量化
- 相似任务检索
- 历史查询复用
- 避免重复探索
"""

import asyncio
import json
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import sys

WORKSPACE = Path("/root/.openclaw/workspace")
AUTORESEARCH_DIR = WORKSPACE / ".wdai-autoresearch"
sys.path.insert(0, str(AUTORESEARCH_DIR))

from wdai_autoresearch_v3 import (
    ResearchTask, ResearchPhase, AgentRole, IERStorage, MockSearchBackend
)


class SimpleEmbedding:
    """简化版文本嵌入（实际应用中使用真实embedding模型）"""
    
    def __init__(self):
        self.cache = {}
    
    def embed(self, text: str) -> np.ndarray:
        """
        生成文本的简单向量表示
        基于词频和哈希（模拟embedding）
        """
        if text in self.cache:
            return self.cache[text]
        
        # 简单的词袋模型 + 哈希
        words = text.lower().split()
        vec = np.zeros(128)
        
        for word in words:
            # 使用哈希将词映射到向量位置
            h = hashlib.md5(word.encode()).hexdigest()
            for i in range(4):  # 每个词影响4个维度
                idx = int(h[i*8:(i+1)*8], 16) % 128
                vec[idx] += 1
        
        # 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        
        self.cache[text] = vec
        return vec
    
    def similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        vec1 = self.embed(text1)
        vec2 = self.embed(text2)
        return float(np.dot(vec1, vec2))


class ExperienceStore:
    """
    Self-Navigating 经验知识库
    存储和检索历史研究经验
    """
    
    def __init__(self, version: str = "v3.3"):
        self.version = version
        self.store_dir = AUTORESEARCH_DIR / "experience_store"
        self.store_dir.mkdir(exist_ok=True)
        
        self.embedding = SimpleEmbedding()
        self.experiences = []
        self._load_experiences()
    
    def _load_experiences(self):
        """加载历史经验"""
        exp_file = self.store_dir / f"experiences_{self.version}.json"
        if exp_file.exists():
            with open(exp_file, 'r') as f:
                self.experiences = json.load(f)
            print(f"   📚 加载了 {len(self.experiences)} 条历史经验")
    
    def _save_experiences(self):
        """保存经验"""
        exp_file = self.store_dir / f"experiences_{self.version}.json"
        with open(exp_file, 'w') as f:
            json.dump(self.experiences, f, ensure_ascii=False, indent=2)
    
    def add_experience(self, task: ResearchTask, queries: List[Dict], 
                       result_summary: Dict):
        """
        添加新的研究经验
        """
        experience = {
            "id": task.id,
            "timestamp": datetime.now().isoformat(),
            "topic": task.topic,
            "hypothesis": task.hypothesis,
            "queries": queries,
            "dimensions": list(result_summary.get("dimensions", {}).keys()),
            "successful_results": result_summary.get("successful", 0),
            "effectiveness_score": self._calculate_effectiveness(queries, result_summary)
        }
        
        self.experiences.append(experience)
        self._save_experiences()
        
        return experience
    
    def _calculate_effectiveness(self, queries: List[Dict], result_summary: Dict) -> float:
        """计算经验有效性分数"""
        query_count = len(queries)
        success_count = result_summary.get("successful", 0)
        dimension_count = len(result_summary.get("dimensions", {}))
        
        # 有效性 = 成功率 * 维度覆盖率
        if query_count > 0:
            success_rate = success_count / (query_count * 2)  # 假设每个查询期望2个结果
            coverage = min(dimension_count / 5, 1.0)  # 5个维度为满分
            return round((success_rate * 0.6 + coverage * 0.4), 2)
        return 0.0
    
    def find_similar_experiences(self, topic: str, top_k: int = 3) -> List[Dict]:
        """
        查找相似的历史经验 (Self-Navigating核心)
        """
        if not self.experiences:
            return []
        
        # 计算与历史经验的相似度
        similarities = []
        for exp in self.experiences:
            sim = self.embedding.similarity(topic, exp["topic"])
            # 考虑有效性分数加权
            weighted_sim = sim * (0.5 + 0.5 * exp.get("effectiveness_score", 0.5))
            similarities.append((exp, weighted_sim))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 返回top_k个相似经验
        return [
            {
                "experience": exp,
                "similarity": round(sim, 3),
                "reusable_queries": self._extract_reusable_queries(exp, topic)
            }
            for exp, sim in similarities[:top_k] if sim > 0.3  # 相似度阈值
        ]
    
    def _extract_reusable_queries(self, exp: Dict, current_topic: str) -> List[Dict]:
        """从经验中提取可复用的查询"""
        reusable = []
        
        for q in exp.get("queries", []):
            # 提取通用的维度查询
            if q.get("dimension") in ["practical", "experience", "curiosity"]:
                # 替换主题词
                modified_query = self._adapt_query(q["query"], exp["topic"], current_topic)
                reusable.append({
                    "original": q["query"],
                    "adapted": modified_query,
                    "dimension": q["dimension"],
                    "priority": q.get("priority", 0.7) * 0.9,  # 复用查询稍降优先级
                    "source_experience": exp["id"],
                    "reuse_type": "adapted"
                })
        
        return reusable
    
    def _adapt_query(self, query: str, old_topic: str, new_topic: str) -> str:
        """将查询从旧主题适配到新主题"""
        # 简单的词替换
        adapted = query.replace(old_topic, new_topic)
        # 如果替换后没变，说明是通用查询
        if adapted == query:
            adapted = f"{new_topic} " + " ".join(query.split()[len(old_topic.split()):])
        return adapted


class SelfNavigatingResearcher:
    """
    Self-Navigating Researcher
    基于 AgentEvolver 的自主导航机制
    
    核心能力:
    1. 检索相似历史经验
    2. 复用有效的查询策略
    3. 混合策略：经验引导 + 新探索
    """
    
    def __init__(self, ier: IERStorage):
        self.ier = ier
        self.search = MockSearchBackend()
        self.exp_store = ExperienceStore()
    
    async def gather(self, task: ResearchTask) -> Dict[str, Any]:
        """
        Phase 1: Self-Navigating 信息搜集
        """
        print(f"\n📚 Phase 1: GATHER (Self-Navigating Researcher)")
        print(f"   主题: {task.topic}")
        print(f"   假设: {task.hypothesis}")
        print(f"   机制: Self-Navigating 经验引导 (AgentEvolver风格)")
        
        # Step 1: Self-Navigating - 查找相似经验
        print(f"\n   🧭 Self-Navigating: 检索相似历史经验...")
        similar_exps = self.exp_store.find_similar_experiences(task.topic, top_k=3)
        
        if similar_exps:
            print(f"   ✅ 找到 {len(similar_exps)} 个相似经验:")
            for i, exp_info in enumerate(similar_exps, 1):
                exp = exp_info["experience"]
                sim = exp_info["similarity"]
                print(f"      {i}. 主题: {exp['topic'][:40]}...")
                print(f"         相似度: {sim} | 有效性: {exp.get('effectiveness_score', 0)}")
                print(f"         可复用查询: {len(exp_info['reusable_queries'])} 个")
        else:
            print(f"   ℹ️ 无相似历史经验，将使用默认策略")
        
        # Step 2: 混合策略生成查询
        queries = self._generate_mixed_queries(task, similar_exps)
        
        print(f"\n   📝 混合策略生成 {len(queries)} 个查询:")
        print(f"      (新探索: {len([q for q in queries if q.get('source')=='new'])}")
        print(f"       经验复用: {len([q for q in queries if q.get('source')=='reused'])}")
        
        for i, q in enumerate(queries[:5], 1):  # 只显示前5个
            source_tag = "[复用]" if q.get("source") == "reused" else "[新]"
            print(f"      {i}. {source_tag} [{q['dimension'][:8]}] {q['query'][:45]}...")
        
        # Step 3: 执行搜索
        info_sources = []
        dimension_stats = {}
        reused_count = 0
        
        for q_info in queries:
            query = q_info["query"]
            dimension = q_info["dimension"]
            is_reused = q_info.get("source") == "reused"
            
            if is_reused:
                reused_count += 1
            
            dimension_stats[dimension] = dimension_stats.get(dimension, 0) + 1
            
            try:
                results = await self.search.search(query, count=2)
                
                if results:
                    for r in results:
                        info_sources.append({
                            "query": query,
                            "dimension": dimension,
                            "source_type": "reused" if is_reused else "new",
                            "title": r.get('title', ''),
                            "url": r.get('url', ''),
                            "description": r.get('description', '')[:150],
                        })
            except Exception as e:
                pass
        
        task.gathered_info = info_sources
        
        # Step 4: 记录经验
        result_summary = {
            "dimensions": dimension_stats,
            "successful": len([s for s in info_sources if s.get("title")]),
            "reused_queries": reused_count
        }
        
        new_exp = self.exp_store.add_experience(task, queries, result_summary)
        
        print(f"\n   📊 Self-Navigating 统计:")
        print(f"      ├─ 相似经验: {len(similar_exps)} 个")
        print(f"      ├─ 复用查询: {reused_count} 个")
        print(f"      ├─ 新查询: {len(queries) - reused_count} 个")
        print(f"      ├─ 总查询: {len(queries)} 个")
        print(f"      ├─ 成功结果: {result_summary['successful']} 个")
        print(f"      ├─ 维度覆盖: {len(dimension_stats)} 个")
        print(f"      └─ 经验已记录: {new_exp['id']}")
        
        # IER记录
        insight = f"Self-Navigating复用{reused_count}个历史查询，避免重复探索"
        self.ier.record(
            task.id, ResearchPhase.GATHER, AgentRole.RESEARCHER,
            f"Self-Navigating: {len(similar_exps)}相似经验, {reused_count}复用, {len(queries)}总查询",
            insight,
            json.dumps({"similar_experiences": len(similar_exps), "reused": reused_count}, ensure_ascii=False)
        )
        
        print(f"   ✅ Self-Navigating 搜集完成")
        return {
            "sources": info_sources,
            "successful": result_summary["successful"],
            "dimensions": dimension_stats,
            "reused_queries": reused_count,
            "similar_experiences": len(similar_exps)
        }
    
    def _generate_mixed_queries(self, task: ResearchTask, 
                                 similar_exps: List[Dict]) -> List[Dict]:
        """
        混合策略：经验复用 + 新探索
        """
        queries = []
        
        # 1. 复用历史经验中的有效查询 (60%)
        for exp_info in similar_exps:
            for rq in exp_info["reusable_queries"][:3]:  # 每个经验最多复用3个
                queries.append({
                    "query": rq["adapted"],
                    "dimension": rq["dimension"],
                    "priority": rq["priority"],
                    "source": "reused",
                    "source_experience": rq["source_experience"]
                })
        
        # 2. 新探索查询 (40%) - 确保覆盖验证维度
        # 验证假设（最高优先级）
        if task.hypothesis:
            queries.append({
                "query": f"{task.topic} {task.hypothesis[:30]} validation",
                "dimension": "validation",
                "priority": 0.95,
                "source": "new"
            })
        
        # 时效性
        queries.append({
            "query": f"{task.topic} 2024 latest",
            "dimension": "timeliness",
            "priority": 0.9,
            "source": "new"
        })
        
        # 好奇心探索（如果历史经验中没有）
        if not any(q["dimension"] == "curiosity" for q in queries):
            queries.append({
                "query": f"{task.topic} alternatives comparison",
                "dimension": "curiosity",
                "priority": 0.7,
                "source": "new"
            })
        
        # 去重并排序
        seen = set()
        unique_queries = []
        for q in queries:
            if q["query"] not in seen:
                seen.add(q["query"])
                unique_queries.append(q)
        
        unique_queries.sort(key=lambda x: x["priority"], reverse=True)
        
        return unique_queries


async def demo_self_navigating():
    """
    演示 Self-Navigating 效果
    第一轮：新主题，无历史经验
    第二轮：相似主题，复用历史经验
    """
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║     🧭 wdai AutoResearch v3.3 - Self-Navigating 演示               ║")
    print("║     经验复用 vs 从头探索 (AgentEvolver风格)                          ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    
    ier = IERStorage("v3.3")
    researcher = SelfNavigatingResearcher(ier)
    
    # 第一轮：新主题（无历史经验）
    print("═" * 70)
    print("🔄 第一轮：全新主题（无历史经验）")
    print("═" * 70)
    
    task1 = ResearchTask(
        id="task001",
        topic="Python asyncio并发性能优化",
        hypothesis="asyncio可以提高I/O密集型任务性能",
        complexity=7
    )
    
    result1 = await researcher.gather(task1)
    
    print("\n" + "─" * 70)
    print("📝 经验已记录到知识库")
    print("─" * 70)
    
    # 第二轮：相似主题（应该复用历史经验）
    print("\n" + "═" * 70)
    print("🔄 第二轮：相似主题（预期复用历史经验）")
    print("═" * 70)
    print("   注意: 'Python threading并发' 与 'Python asyncio并发' 相似")
    print("   预期: 从第一轮经验中复用有效查询")
    print()
    
    task2 = ResearchTask(
        id="task002",
        topic="Python threading并发性能优化",
        hypothesis="threading可以提高CPU密集型任务性能",
        complexity=7
    )
    
    result2 = await researcher.gather(task2)
    
    # 对比
    print("\n" + "=" * 70)
    print("📊 Self-Navigating 效果对比")
    print("=" * 70)
    print()
    print("第一轮 (asyncio) - 无历史经验:")
    print(f"   相似经验: {result1['similar_experiences']}")
    print(f"   复用查询: {result1['reused_queries']}")
    print(f"   总查询: {result1.get('query_count', 'N/A')}")
    print()
    print("第二轮 (threading) - 有历史经验:")
    print(f"   相似经验: {result2['similar_experiences']}")
    print(f"   复用查询: {result2['reused_queries']} ⬅️ 自动复用!")
    print(f"   总查询: {result2.get('query_count', 'N/A')}")
    print()
    print("效果:")
    if result2['reused_queries'] > 0:
        print(f"   ✅ 成功复用 {result2['reused_queries']} 个历史查询")
        print(f"   ✅ 避免重复探索，提升效率")
    else:
        print(f"   ℹ️ 相似度不够高，未触发复用")
    print()
    print("经验知识库:")
    print(f"   当前共有 {len(researcher.exp_store.experiences)} 条经验")


if __name__ == '__main__':
    asyncio.run(demo_self_navigating())
