#!/usr/bin/env python3
"""
B站收藏视频溯源系统 v1.1
支持UID 3461564002732313
"""

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BILIBILI_DIR = Path("/root/.openclaw/workspace/.knowledge/bilibili")
BILIBILI_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class BilibiliVideo:
    """B站视频信息"""
    bvid: str
    title: str
    description: str
    owner: str
    tags: List[str]
    category: str
    view_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    pub_date: str = ""
    
    # 溯源结果
    extracted_keywords: List[str] = field(default_factory=list)
    related_papers: List[Dict] = field(default_factory=list)
    related_repos: List[Dict] = field(default_factory=list)
    
    analyzed_at: float = field(default_factory=time.time)

class BilibiliTracerV2:
    """B站视频溯源器 v2.0"""
    
    def __init__(self, uid: str):
        self.uid = uid
        self.bilibili_dir = BILIBILI_DIR
        self.videos_db = self.bilibili_dir / f"videos_{uid}.json"
        self.report_file = self.bilibili_dir / f"report_{uid}.md"
        
        # 扩展学术关键词库
        self.academic_keywords = {
            "LLM": ["large language model", "GPT", "transformer"],
            "RAG": ["retrieval augmented generation", "vector database"],
            "Agent": ["autonomous agent", "multi-agent system"],
            "LoRA": ["low-rank adaptation", "parameter-efficient"],
            "神经网络": ["neural network", "deep learning"],
            "强化学习": ["reinforcement learning", "RLHF"],
            "计算机视觉": ["computer vision", "CNN", "ResNet"],
            "NLP": ["natural language processing", "BERT"],
            "多模态": ["multimodal", "vision-language"],
            "分布式": ["distributed system", "microservices"],
            "数据库": ["database", "SQL", "NoSQL"],
            "算法": ["algorithm", "data structure"],
            "编译器": ["compiler", "parser", "AST"],
            "操作系统": ["operating system", "kernel"],
            "区块链": ["blockchain", "consensus"],
            "机器学习": ["machine learning", "supervised learning"],
            "图神经网络": ["graph neural network", "GNN"],
            "注意力机制": ["attention mechanism", "self-attention"],
            "向量检索": ["vector search", "similarity search"],
            "知识图谱": ["knowledge graph", "knowledge base"],
            "AutoML": ["automated machine learning", "NAS"],
            "联邦学习": ["federated learning", "privacy-preserving"],
            "量子计算": ["quantum computing", "quantum algorithm"],
        }
        
    def load_from_manual_export(self, export_file: Path) -> List[BilibiliVideo]:
        """从手动导出的收藏夹文件加载"""
        videos = []
        
        with open(export_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 格式: BV号 | 标题 | UP主
                parts = line.split('|')
                if len(parts) >= 2:
                    bvid = parts[0].strip()
                    title = parts[1].strip()
                    owner = parts[2].strip() if len(parts) > 2 else "未知"
                    
                    video = BilibiliVideo(
                        bvid=bvid,
                        title=title,
                        description="",
                        owner=owner,
                        tags=[],
                        category="未分类"
                    )
                    videos.append(video)
        
        return videos
    
    def analyze_video(self, video: BilibiliVideo) -> BilibiliVideo:
        """分析单个视频"""
        print(f"\n[分析] {video.title[:50]}...")
        
        # 提取关键词
        keywords = self._extract_keywords(video)
        video.extracted_keywords = keywords
        print(f"  🔑 关键词: {', '.join(keywords[:6])}")
        
        # 溯源论文
        papers = self._trace_papers(keywords)
        video.related_papers = papers
        if papers:
            print(f"  📄 论文: {len(papers)}篇")
            for p in papers[:2]:
                print(f"     - {p['title'][:40]}...")
        
        # 溯源项目
        repos = self._trace_repos(keywords)
        video.related_repos = repos
        if repos:
            print(f"  💻 项目: {len(repos)}个")
            for r in repos[:2]:
                print(f"     - {r['name']}")
        
        return video
    
    def _extract_keywords(self, video: BilibiliVideo) -> List[str]:
        """提取关键词"""
        keywords = []
        text = video.title + " " + video.description
        
        # 匹配学术关键词
        for cn_kw, en_kws in self.academic_keywords.items():
            if cn_kw in text or any(ek.lower() in text.lower() for ek in en_kws):
                keywords.append(cn_kw)
                keywords.extend(en_kws[:2])
        
        # 匹配英文技术术语
        import re
        english_terms = re.findall(r'[A-Z]{2,}', text)
        keywords.extend([t for t in english_terms if t not in ['BV', 'HTTP', 'URL']])
        
        return list(set(keywords))[:15]
    
    def _trace_papers(self, keywords: List[str]) -> List[Dict]:
        """溯源论文"""
        papers = []
        
        paper_db = {
            "RAG": [{"title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", "authors": "Lewis et al.", "year": 2020, "venue": "NeurIPS"}],
            "LoRA": [{"title": "LoRA: Low-Rank Adaptation of Large Language Models", "authors": "Hu et al.", "year": 2021, "venue": "ICLR"}],
            "transformer": [{"title": "Attention Is All You Need", "authors": "Vaswani et al.", "year": 2017, "venue": "NeurIPS"}],
            "GPT": [{"title": "Language Models are Few-Shot Learners", "authors": "Brown et al.", "year": 2020, "venue": "NeurIPS"}],
            "BERT": [{"title": "BERT: Pre-training of Deep Bidirectional Transformers", "authors": "Devlin et al.", "year": 2019, "venue": "NAACL"}],
            "ResNet": [{"title": "Deep Residual Learning for Image Recognition", "authors": "He et al.", "year": 2016, "venue": "CVPR"}],
            "GNN": [{"title": "Graph Convolutional Networks", "authors": "Kipf et al.", "year": 2017, "venue": "ICLR"}],
            "联邦学习": [{"title": "Communication-Efficient Learning of Deep Networks", "authors": "McMahan et al.", "year": 2017, "venue": "AISTATS"}],
        }
        
        for kw in keywords:
            for pk, pl in paper_db.items():
                if pk.lower() in kw.lower() or kw.lower() in pk.lower():
                    papers.extend(pl)
        
        # 去重
        seen = set()
        unique = []
        for p in papers:
            if p["title"] not in seen:
                seen.add(p["title"])
                unique.append(p)
        
        return unique[:5]
    
    def _trace_repos(self, keywords: List[str]) -> List[Dict]:
        """溯源开源项目"""
        repos = []
        
        repo_db = {
            "RAG": [
                {"name": "langchain-ai/langchain", "desc": "构建LLM应用的框架"},
                {"name": "chroma-core/chroma", "desc": "向量数据库"},
                {"name": "microsoft/semantic-kernel", "desc": "微软语义内核"}
            ],
            "LLM": [
                {"name": "huggingface/transformers", "desc": "预训练模型库"},
                {"name": "openai/openai-python", "desc": "OpenAI API"},
                {"name": "oobabooga/text-generation-webui", "desc": "大模型Web界面"}
            ],
            "Agent": [
                {"name": "Significant-Gravitas/AutoGPT", "desc": "自主AI代理"},
                {"name": "microsoft/autogen", "desc": "多代理框架"},
                {"name": "langchain-ai/langgraph", "desc": "代理工作流"}
            ],
            "GNN": [
                {"name": "pyg-team/pytorch_geometric", "desc": "PyTorch图神经网络"},
                {"name": "dmlc/dgl", "desc": "深度图学习库"}
            ],
            "分布式": [
                {"name": "etcd-io/etcd", "desc": "分布式键值存储"},
                {"name": "hashicorp/consul", "desc": "服务发现"}
            ],
        }
        
        for kw in keywords:
            for rk, rl in repo_db.items():
                if rk.lower() in kw.lower() or kw.lower() in rk.lower():
                    repos.extend(rl)
        
        seen = set()
        unique = []
        for r in repos:
            if r["name"] not in seen:
                seen.add(r["name"])
                unique.append(r)
        
        return unique[:5]
    
    def generate_report(self, videos: List[BilibiliVideo]) -> str:
        """生成分析报告"""
        report = []
        report.append("# B站收藏视频溯源报告")
        report.append(f"\n**UID**: {self.uid}")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**分析视频数**: {len(videos)}")
        
        # 统计主题
        all_keywords = []
        all_papers = []
        for v in videos:
            all_keywords.extend(v.extracted_keywords)
            all_papers.extend(v.related_papers)
        
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        
        report.append(f"\n## 📊 技术主题分布")
        report.append(f"\n识别出 {len(keyword_counts)} 个技术关键词：")
        for kw, count in keyword_counts.most_common(15):
            report.append(f"- **{kw}**: {count}次")
        
        report.append(f"\n## 📚 推荐论文")
        seen_papers = set()
        for v in videos:
            for p in v.related_papers:
                if p["title"] not in seen_papers:
                    seen_papers.add(p["title"])
                    report.append(f"\n### {p['title']}")
                    report.append(f"- 作者: {p['authors']}")
                    report.append(f"- 年份: {p['year']}")
                    report.append(f"- 会议: {p.get('venue', 'N/A')}")
        
        report.append(f"\n## 💻 推荐项目")
        seen_repos = set()
        for v in videos:
            for r in v.related_repos:
                if r["name"] not in seen_repos:
                    seen_repos.add(r["name"])
                    report.append(f"\n- **{r['name']}**: {r['desc']}")
        
        report.append(f"\n## 📺 视频详细分析")
        for i, v in enumerate(videos, 1):
            report.append(f"\n### {i}. {v.title}")
            report.append(f"- UP主: {v.owner}")
            report.append(f"- BV号: {v.bvid}")
            if v.extracted_keywords:
                report.append(f"- 关键词: {', '.join(v.extracted_keywords[:8])}")
        
        return '\n'.join(report)
    
    def save_results(self, videos: List[BilibiliVideo]):
        """保存结果"""
        # 保存JSON
        with open(self.videos_db, 'w', encoding='utf-8') as f:
            json.dump([asdict(v) for v in videos], f, indent=2, ensure_ascii=False)
        
        # 生成并保存报告
        report = self.generate_report(videos)
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ 结果已保存:")
        print(f"  - JSON: {self.videos_db}")
        print(f"  - 报告: {self.report_file}")

def analyze_uid(uid: str):
    """分析指定UID的收藏"""
    print(f"\n{'='*65}")
    print(f"🎬 B站收藏视频溯源分析")
    print(f"{'='*65}")
    print(f"UID: {uid}")
    
    tracer = BilibiliTracerV2(uid)
    
    # 检查是否有手动导出的数据
    export_file = BILIBILI_DIR / f"export_{uid}.txt"
    
    if export_file.exists():
        print(f"\n📁 从导出文件加载: {export_file}")
        videos = tracer.load_from_manual_export(export_file)
    else:
        print(f"\n⚠️  API访问受限（B站风控）")
        print(f"请手动导出收藏夹:")
        print(f"  1. 打开B站 → 收藏夹")
        print(f"  2. 复制视频列表")
        print(f"  3. 保存到: {export_file}")
        print(f"  格式: BV号 | 标题 | UP主")
        
        # 使用示例数据演示
        print(f"\n🔄 使用示例数据进行演示...")
        videos = tracer.load_from_manual_export(BILIBILI_DIR / "sample_export.txt")
    
    if not videos:
        print("❌ 没有找到视频数据")
        return
    
    print(f"\n🔍 开始分析 {len(videos)} 个视频...")
    
    # 分析每个视频
    analyzed = []
    for video in videos:
        analyzed.append(tracer.analyze_video(video))
    
    # 保存结果
    tracer.save_results(analyzed)
    
    print(f"\n{'='*65}")
    print("✅ 分析完成!")
    print(f"{'='*65}")

if __name__ == "__main__":
    import sys
    
    uid = sys.argv[1] if len(sys.argv) > 1 else "3461564002732313"
    analyze_uid(uid)
