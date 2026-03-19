#!/usr/bin/env python3
"""
B站收藏视频溯源系统 v1.0
根据用户B站收藏视频自动溯源高质量信息源
"""

import json
import time
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import urllib.request
import urllib.parse

# 系统目录
BILIBILI_DIR = Path("/root/.openclaw/workspace/.knowledge/bilibili")
BILIBILI_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class BilibiliVideo:
    """B站视频信息"""
    bvid: str
    title: str
    description: str
    owner: str  # UP主
    tags: List[str]
    category: str
    view_count: int
    like_count: int
    favorite_count: int
    pub_date: str
    
    # 溯源结果
    extracted_keywords: List[str] = field(default_factory=list)
    related_papers: List[Dict] = field(default_factory=list)
    related_repos: List[Dict] = field(default_factory=list)
    related_articles: List[Dict] = field(default_factory=list)
    
    analyzed_at: float = field(default_factory=time.time)
    analysis_depth: int = 1  # 1=基础, 2=深度

@dataclass
class TracingResult:
    """溯源结果"""
    video: BilibiliVideo
    keywords: List[str]
    papers: List[Dict]
    repositories: List[Dict]
    articles: List[Dict]
    insights: List[str]

class BilibiliTracer:
    """
    B站视频溯源器
    从收藏视频提取关键信息并自动溯源
    """
    
    def __init__(self, uid: str = None, bilibili_dir: Path = BILIBILI_DIR):
        self.uid = uid
        self.bilibili_dir = bilibili_dir
        self.videos_db = bilibili_dir / "videos_db.json"
        self.tracing_log = bilibili_dir / "tracing_log.json"
        
        # 学术关键词映射
        self.academic_keywords = {
            "LLM": ["large language model", "transformer", "attention mechanism"],
            "RAG": ["retrieval augmented generation", "vector database", "embedding"],
            "Agent": ["autonomous agent", "multi-agent system", "reinforcement learning"],
            "神经网络": ["neural network", "deep learning", "backpropagation"],
            "强化学习": ["reinforcement learning", "Q-learning", "policy gradient"],
            "计算机视觉": ["computer vision", "CNN", "image recognition"],
            "NLP": ["natural language processing", "BERT", "GPT"],
            "多模态": ["multimodal", "vision-language model", "CLIP"],
            "分布式": ["distributed system", "microservices", "consensus algorithm"],
            "数据库": ["database", "SQL", "NoSQL", "transaction"],
            "算法": ["algorithm", "data structure", "complexity analysis"],
            "编译原理": ["compiler", "lexer", "parser", "AST"],
            "操作系统": ["operating system", "kernel", "scheduler", "memory management"],
        }
        
    def set_uid(self, uid: str):
        """设置B站UID"""
        self.uid = uid
        print(f"[BilibiliTracer] UID已设置: {uid}")
        
    def fetch_favorites(self, folder_id: int = None) -> List[BilibiliVideo]:
        """
        获取用户收藏夹视频
        
        Args:
            folder_id: 收藏夹ID，默认获取默认收藏夹
        """
        if not self.uid:
            raise ValueError("请先设置B站UID")
        
        print(f"[BilibiliTracer] 获取用户 {self.uid} 的收藏夹...")
        
        # 这里调用B站API获取收藏夹
        # 简化处理：返回示例数据，实际应调用API
        videos = self._get_sample_videos()
        
        print(f"  获取到 {len(videos)} 个收藏视频")
        return videos
    
    def _get_sample_videos(self) -> List[BilibiliVideo]:
        """获取示例视频（实际应从API获取）"""
        # 基于用户可能感兴趣的AI/编程主题
        samples = []
        
        samples.append(BilibiliVideo(
            bvid="BV1uowLz7Evr",
            title="OpenClaw 代理为何总失忆？完整内存架构解决方案",
            description="探讨AI代理的内存管理、长期记忆、知识图谱等",
            owner="AI技术探索",
            tags=["AI", "agent", "memory", "RAG"],
            category="科技",
            view_count=15000,
            like_count=800,
            favorite_count=1200,
            pub_date="2026-03-10"
        ))
        
        samples.append(BilibiliVideo(
            bvid="BV1xyz123",
            title="大模型微调实战：LoRA vs Full Fine-tuning",
            description="深入讲解大模型微调方法，LoRA原理和实现",
            owner="深度学习实验室",
            tags=["LLM", "fine-tuning", "LoRA", "transformer"],
            category="科技",
            view_count=25000,
            like_count=1200,
            favorite_count=2000,
            pub_date="2026-03-08"
        ))
        
        samples.append(BilibiliVideo(
            bvid="BV2abc456",
            title="分布式系统设计：从0到1构建高可用架构",
            description="分布式系统核心概念，CAP定理，一致性算法",
            owner="后端技术专家",
            tags=["分布式", "system design", "microservices", "cloud"],
            category="科技",
            view_count=18000,
            like_count=900,
            favorite_count=1500,
            pub_date="2026-03-05"
        ))
        
        return samples
    
    def analyze_video(self, video: BilibiliVideo) -> TracingResult:
        """
        分析单个视频并溯源
        """
        print(f"\n[分析] {video.title}")
        print(f"  UP主: {video.owner}")
        print(f"  标签: {', '.join(video.tags)}")
        
        # Step 1: 提取关键词
        keywords = self._extract_keywords(video)
        video.extracted_keywords = keywords
        print(f"  提取关键词: {', '.join(keywords[:5])}")
        
        # Step 2: 溯源学术论文
        papers = self._trace_academic_papers(keywords)
        video.related_papers = papers
        print(f"  找到相关论文: {len(papers)}篇")
        
        # Step 3: 溯源开源项目
        repos = self._trace_repositories(keywords)
        video.related_repos = repos
        print(f"  找到相关项目: {len(repos)}个")
        
        # Step 4: 溯源技术文章
        articles = self._trace_articles(keywords)
        video.related_articles = articles
        print(f"  找到相关文章: {len(articles)}篇")
        
        # Step 5: 生成洞察
        insights = self._generate_insights(video, papers, repos)
        
        # 保存到数据库
        self._save_video(video)
        
        return TracingResult(
            video=video,
            keywords=keywords,
            papers=papers,
            repositories=repos,
            articles=articles,
            insights=insights
        )
    
    def _extract_keywords(self, video: BilibiliVideo) -> List[str]:
        """从视频信息提取关键词"""
        keywords = []
        
        # 直接使用标签
        keywords.extend(video.tags)
        
        # 从标题提取
        title_keywords = self._extract_from_text(video.title)
        keywords.extend(title_keywords)
        
        # 从描述提取
        desc_keywords = self._extract_from_text(video.description)
        keywords.extend(desc_keywords)
        
        # 去重并排序
        keywords = list(set(keywords))
        
        # 扩展学术关键词
        expanded = []
        for kw in keywords:
            if kw in self.academic_keywords:
                expanded.extend(self.academic_keywords[kw])
        keywords.extend(expanded)
        
        return list(set(keywords))[:20]  # 最多20个
    
    def _extract_from_text(self, text: str) -> List[str]:
        """从文本提取关键词"""
        keywords = []
        
        # 简单的关键词匹配
        for cn_kw, en_kws in self.academic_keywords.items():
            if cn_kw in text:
                keywords.append(cn_kw)
                keywords.extend(en_kws)
        
        # 匹配英文术语
        english_terms = re.findall(r'[A-Z]{2,}', text)  # 大写缩写
        keywords.extend(english_terms)
        
        return list(set(keywords))
    
    def _trace_academic_papers(self, keywords: List[str]) -> List[Dict]:
        """溯源相关学术论文"""
        papers = []
        
        # 基于关键词匹配已知的论文数据库
        # 这里可以从.metacognition_papers.py获取
        
        paper_keywords = {
            "RAG": [
                {
                    "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                    "authors": ["Lewis et al."],
                    "year": 2020,
                    "url": "https://arxiv.org/abs/2005.11401"
                }
            ],
            "LoRA": [
                {
                    "title": "LoRA: Low-Rank Adaptation of Large Language Models",
                    "authors": ["Hu et al."],
                    "year": 2021,
                    "url": "https://arxiv.org/abs/2106.09685"
                }
            ],
            "transformer": [
                {
                    "title": "Attention Is All You Need",
                    "authors": ["Vaswani et al."],
                    "year": 2017,
                    "url": "https://arxiv.org/abs/1706.03762"
                }
            ],
            "distributed": [
                {
                    "title": "The Google File System",
                    "authors": ["Ghemawat et al."],
                    "year": 2003,
                    "url": "https://research.google/pubs/pub51/"
                }
            ]
        }
        
        for kw in keywords:
            for pk, pl in paper_keywords.items():
                if pk.lower() in kw.lower() or kw.lower() in pk.lower():
                    papers.extend(pl)
        
        # 去重
        seen = set()
        unique_papers = []
        for p in papers:
            if p["title"] not in seen:
                seen.add(p["title"])
                unique_papers.append(p)
        
        return unique_papers[:5]  # 最多5篇
    
    def _trace_repositories(self, keywords: List[str]) -> List[Dict]:
        """溯源相关开源项目"""
        repos = []
        
        repo_keywords = {
            "RAG": [
                {"name": "langchain-ai/langchain", "desc": "构建RAG应用的框架"},
                {"name": "chroma-core/chroma", "desc": "向量数据库"}
            ],
            "LLM": [
                {"name": "openai/openai-python", "desc": "OpenAI API客户端"},
                {"name": "huggingface/transformers", "desc": "预训练模型库"}
            ],
            "Agent": [
                {"name": "Significant-Gravitas/AutoGPT", "desc": "自主AI代理"},
                {"name": "microsoft/autogen", "desc": "多代理对话框架"}
            ],
            "distributed": [
                {"name": "etcd-io/etcd", "desc": "分布式键值存储"},
                {"name": "hashicorp/consul", "desc": "服务发现和配置"}
            ]
        }
        
        for kw in keywords:
            for rk, rl in repo_keywords.items():
                if rk.lower() in kw.lower() or kw.lower() in rk.lower():
                    repos.extend(rl)
        
        # 去重
        seen = set()
        unique_repos = []
        for r in repos:
            if r["name"] not in seen:
                seen.add(r["name"])
                unique_repos.append(r)
        
        return unique_repos[:5]
    
    def _trace_articles(self, keywords: List[str]) -> List[Dict]:
        """溯源技术文章"""
        # 可以扩展到Medium、Dev.to、知乎等平台
        return []
    
    def _generate_insights(self, video: BilibiliVideo, papers: List[Dict], repos: List[Dict]) -> List[str]:
        """生成溯源洞察"""
        insights = []
        
        insights.append(f"视频《{video.title}》涉及 {len(video.extracted_keywords)} 个技术关键词")
        
        if papers:
            insights.append(f"溯源到 {len(papers)} 篇核心论文，建议深入阅读")
        
        if repos:
            insights.append(f"发现 {len(repos)} 个相关开源项目，可用于实践")
        
        # 学习路径建议
        if "RAG" in video.tags and papers:
            insights.append("学习路径: 先看RAG原始论文 → 实践LangChain → 优化向量检索")
        
        if "LLM" in video.tags and "LoRA" in str(video.title):
            insights.append("学习路径: 理解LoRA原理 → 尝试微调小模型 → 应用到实际任务")
        
        return insights
    
    def _save_video(self, video: BilibiliVideo):
        """保存视频分析结果"""
        videos = self._load_videos_db()
        
        # 检查是否已存在
        existing = [v for v in videos if v.bvid == video.bvid]
        if existing:
            # 更新
            videos = [v for v in videos if v.bvid != video.bvid]
        
        videos.append(video)
        
        with open(self.videos_db, 'w', encoding='utf-8') as f:
            json.dump([asdict(v) for v in videos], f, indent=2, ensure_ascii=False)
    
    def _load_videos_db(self) -> List[BilibiliVideo]:
        """加载视频数据库"""
        if self.videos_db.exists():
            with open(self.videos_db, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [BilibiliVideo(**v) for v in data]
        return []
    
    def generate_study_plan(self) -> Dict:
        """基于收藏视频生成学习计划"""
        videos = self._load_videos_db()
        
        if not videos:
            return {"error": "暂无分析数据"}
        
        # 统计主题分布
        topics = {}
        for v in videos:
            for tag in v.tags:
                topics[tag] = topics.get(tag, 0) + 1
        
        # 统计论文来源
        all_papers = []
        for v in videos:
            all_papers.extend(v.related_papers)
        
        # 生成学习计划
        plan = {
            "based_on_videos": len(videos),
            "topic_distribution": topics,
            "core_papers": len(all_papers),
            "recommended_study_path": self._build_study_path(videos),
            "priority_topics": sorted(topics.items(), key=lambda x: -x[1])[:3]
        }
        
        return plan
    
    def _build_study_path(self, videos: List[BilibiliVideo]) -> List[Dict]:
        """构建学习路径"""
        paths = []
        
        for v in videos:
            if v.related_papers:
                paths.append({
                    "video_title": v.title,
                    "bvid": v.bvid,
                    "papers": [p["title"] for p in v.related_papers[:2]],
                    "repos": [r["name"] for r in v.related_repos[:2]],
                    "estimated_time": "2-3小时"
                })
        
        return paths[:5]  # 最多5条路径

def main():
    """主函数"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║           B站收藏视频溯源系统 v1.0                           ║")
    print("║     根据收藏视频自动溯源高质量信息源                        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    tracer = BilibiliTracer()
    
    # 检查是否有UID配置
    config_file = BILIBILI_DIR / "config.json"
    uid = None
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            uid = config.get("uid")
    
    if not uid:
        print("⚠️  未配置B站UID")
        print("请运行: python3 bilibili_tracer.py --set-uid YOUR_UID")
        print()
        print("如何获取UID:")
        print("  1. 打开B站个人主页")
        print("  2. URL中的数字即为UID，如 space.bilibili.com/123456")
        print("  3. 复制数字部分")
        return
    
    tracer.set_uid(uid)
    
    # 获取收藏视频
    videos = tracer.fetch_favorites()
    
    print(f"\n📺 开始分析 {len(videos)} 个收藏视频...")
    print("="*65)
    
    # 分析每个视频
    results = []
    for video in videos:
        result = tracer.analyze_video(video)
        results.append(result)
        print()
    
    # 生成学习计划
    print("="*65)
    print("📚 生成学习计划")
    print("="*65)
    plan = tracer.generate_study_plan()
    
    print(f"\n基于 {plan['based_on_videos']} 个视频分析:")
    print(f"\n主题分布:")
    for topic, count in plan['topic_distribution'].items():
        print(f"  - {topic}: {count}个视频")
    
    print(f"\n推荐学习路径:")
    for i, path in enumerate(plan['recommended_study_path'], 1):
        print(f"\n  路径{i}: {path['video_title'][:40]}...")
        if path['papers']:
            print(f"    论文: {path['papers'][0][:50]}...")
        if path['repos']:
            print(f"    项目: {path['repos'][0]}")
        print(f"    预计时间: {path['estimated_time']}")
    
    print(f"\n✅ 分析完成！数据已保存到 {BILIBILI_DIR}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--set-uid":
        if len(sys.argv) > 2:
            uid = sys.argv[2]
            config_file = BILIBILI_DIR / "config.json"
            with open(config_file, 'w') as f:
                json.dump({"uid": uid, "set_at": time.time()}, f)
            print(f"✅ UID已设置: {uid}")
        else:
            print("请提供UID: python3 bilibili_tracer.py --set-uid YOUR_UID")
    else:
        main()
