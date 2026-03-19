#!/usr/bin/env python3
"""
Mini-RAGFlow Light - 轻量级 RAG 引擎 (BM25 版本)

纯 Python 实现，无需下载大模型：
- 使用 BM25 关键词检索代替向量检索
- 支持模板化文档解析
- 有据引用
- 完全离线运行

依赖安装:
    pip install rank-bm25 jieba unstructured pdf2image pypdf

用法:
    python mini_ragflow_light.py parse doc.pdf --template laws
    python mini_ragflow_light.py index ./docs --kb my_kb
    python mini_ragflow_light.py query "问题" --kb my_kb --cite
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import pickle
import shutil

# 配置
KB_DIR = Path.home() / ".config" / "mini-ragflow" / "knowledge_bases"
CACHE_DIR = Path.home() / ".cache" / "mini-ragflow"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


@dataclass
class DocumentChunk:
    """文档分块"""
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    page: int = 0
    chunk_type: str = "text"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "source": self.source,
            "page": self.page,
            "chunk_type": self.chunk_type
        }


@dataclass
class Citation:
    """引用信息"""
    chunk_id: str
    text: str
    source: str
    page: int
    score: float


@dataclass
class QueryResult:
    """查询结果"""
    answer: str
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 0.0
    
    def to_markdown(self) -> str:
        lines = [self.answer, ""]
        if self.citations:
            lines.append("**参考来源：**")
            for i, cite in enumerate(self.citations, 1):
                lines.append(f"{i}. {cite.source} (第{cite.page}页)")
                lines.append(f"   > {cite.text[:100]}...")
        return "\n".join(lines)


# ============================================================================
# 文档解析（复用之前的 DeepDocParser）
# ============================================================================

class DeepDocParser:
    """深度文档解析器"""
    
    def __init__(self):
        self.supported_formats = {'.pdf', '.docx', '.txt', '.md', '.html'}
        self._init_parsers()
    
    def _init_parsers(self):
        try:
            import pypdf
            self.has_pypdf = True
        except ImportError:
            self.has_pypdf = False
    
    def parse(self, file_path: str, template: str = "naive") -> List[DocumentChunk]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        ext = path.suffix.lower()
        if ext == '.pdf':
            raw_chunks = self._parse_pdf(path)
        elif ext in ['.docx']:
            raw_chunks = self._parse_docx(path)
        else:
            raw_chunks = self._parse_text(path)
        
        return self._apply_template(raw_chunks, template, path.name)
    
    def _parse_pdf(self, path: Path) -> List[Dict]:
        chunks = []
        try:
            import fitz
            doc = fitz.open(path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    chunks.append({"text": text, "page": page_num + 1, "type": "text"})
            doc.close()
        except ImportError:
            print("请安装 PyMuPDF: pip install PyMuPDF")
            sys.exit(1)
        return chunks
    
    def _parse_docx(self, path: Path) -> List[Dict]:
        try:
            from docx import Document
            doc = Document(path)
            return [{"text": para.text, "page": 1, "type": "text"} 
                    for para in doc.paragraphs if para.text.strip()]
        except ImportError:
            print("请安装 python-docx: pip install python-docx")
            sys.exit(1)
    
    def _parse_text(self, path: Path) -> List[Dict]:
        text = path.read_text(encoding='utf-8')
        return [{"text": text, "page": 1, "type": "text"}]
    
    def _apply_template(self, raw_chunks: List[Dict], template: str, source: str) -> List[DocumentChunk]:
        if template == "laws":
            return self._laws_chunking(raw_chunks, source)
        elif template == "paper":
            return self._paper_chunking(raw_chunks, source)
        else:
            return self._naive_chunking(raw_chunks, source)
    
    def _naive_chunking(self, raw_chunks: List[Dict], source: str) -> List[DocumentChunk]:
        chunks = []
        chunk_id = 0
        for raw in raw_chunks:
            text = raw["text"]
            page = raw.get("page", 1)
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            
            current_chunk = ""
            for para in paragraphs:
                if len(current_chunk) + len(para) > CHUNK_SIZE:
                    if current_chunk:
                        chunk_id += 1
                        chunks.append(DocumentChunk(
                            id=f"{source}_{chunk_id}",
                            text=current_chunk.strip(),
                            source=source, page=page, chunk_type="text"
                        ))
                    current_chunk = para
                else:
                    current_chunk += "\n" + para if current_chunk else para
            
            if current_chunk.strip():
                chunk_id += 1
                chunks.append(DocumentChunk(
                    id=f"{source}_{chunk_id}",
                    text=current_chunk.strip(),
                    source=source, page=page, chunk_type="text"
                ))
        return chunks
    
    def _laws_chunking(self, raw_chunks: List[Dict], source: str) -> List[DocumentChunk]:
        chunks = []
        chunk_id = 0
        full_text = "\n".join([c["text"] for c in raw_chunks])
        
        # 匹配法律条款
        article_pattern = r'(?:^|\n)\s*(第[一二三四五六七八九十百千]+条[\s:：])'
        articles = list(re.finditer(article_pattern, full_text))
        
        if len(articles) < 2:
            return self._naive_chunking(raw_chunks, source)
        
        for i, match in enumerate(articles):
            start = match.start()
            end = articles[i + 1].start() if i + 1 < len(articles) else len(full_text)
            article_text = full_text[start:end].strip()
            article_num = match.group(1).strip()
            
            if article_text:
                chunk_id += 1
                chunks.append(DocumentChunk(
                    id=f"{source}_{article_num.replace(' ', '_')}_{chunk_id}",
                    text=article_text,
                    source=source, page=1, chunk_type="article",
                    metadata={"article": article_num}
                ))
        return chunks
    
    def _paper_chunking(self, raw_chunks: List[Dict], source: str) -> List[DocumentChunk]:
        return self._naive_chunking(raw_chunks, source)  # 简化版


# ============================================================================
# BM25 知识库（无需向量模型）
# ============================================================================

class BM25KnowledgeBase:
    """基于 BM25 的关键词知识库"""
    
    def __init__(self, name: str):
        self.name = name
        self.kb_path = KB_DIR / name
        self.kb_path.mkdir(parents=True, exist_ok=True)
        
        self.chunks: List[DocumentChunk] = []
        self.bm25 = None
        self.tokenized_corpus: List[List[str]] = []
        
        self._load()
    
    def _load(self):
        """加载已有知识库"""
        chunks_file = self.kb_path / "chunks.pkl"
        if chunks_file.exists():
            with open(chunks_file, 'rb') as f:
                data = pickle.load(f)
                self.chunks = data.get('chunks', [])
                self.tokenized_corpus = data.get('tokenized_corpus', [])
            
            if self.chunks:
                self._init_bm25()
    
    def _init_bm25(self):
        """初始化 BM25"""
        try:
            from rank_bm25 import BM25Okapi
            if self.tokenized_corpus:
                self.bm25 = BM25Okapi(self.tokenized_corpus)
        except ImportError:
            print("请安装 rank-bm25: pip install rank-bm25")
            sys.exit(1)
    
    def _tokenize(self, text: str) -> List[str]:
        """中文分词"""
        try:
            import jieba
            # 添加自定义词典（法律术语等）
            jieba.add_word('违约金')
            jieba.add_word('知识产权')
            jieba.add_word('保密条款')
            return list(jieba.cut(text.lower()))
        except ImportError:
            # Fallback: 简单字符分割
            return list(text.lower())
    
    def add_documents(self, chunks: List[DocumentChunk]):
        """添加文档"""
        if not chunks:
            return
        
        print(f"正在为 {len(chunks)} 个文本块建立索引...")
        
        self.chunks.extend(chunks)
        
        # 分词
        for chunk in chunks:
            tokens = self._tokenize(chunk.text)
            self.tokenized_corpus.append(tokens)
        
        # 初始化 BM25
        self._init_bm25()
        
        # 保存
        self._save()
        
        print(f"✅ 已添加 {len(chunks)} 个文本块到知识库 '{self.name}'")
    
    def _save(self):
        """保存知识库"""
        chunks_file = self.kb_path / "chunks.pkl"
        with open(chunks_file, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'tokenized_corpus': self.tokenized_corpus
            }, f)
    
    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """BM25 检索"""
        if not self.bm25 or not self.chunks:
            return []
        
        # 分词查询
        query_tokens = self._tokenize(query_text)
        
        # BM25 打分
        scores = self.bm25.get_scores(query_tokens)
        
        # 获取 top_k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # 只返回有分数的结果
                # 归一化分数到 0-1
                normalized_score = min(scores[idx] / 10, 1.0)  # 简单归一化
                results.append((self.chunks[idx], normalized_score))
        
        return results
    
    def delete(self):
        """删除知识库"""
        if self.kb_path.exists():
            shutil.rmtree(self.kb_path)
            print(f"已删除知识库: {self.name}")


# ============================================================================
# RAG 引擎
# ============================================================================

class RAGEngine:
    """RAG 引擎"""
    
    def __init__(self, kb: BM25KnowledgeBase):
        self.kb = kb
        self.llm_client = None
    
    def set_llm_client(self, client):
        self.llm_client = client
    
    def query(self, query_text: str, top_k: int = 5, with_citation: bool = True) -> QueryResult:
        if not self.llm_client:
            raise ValueError("请先设置 LLM 客户端")
        
        # 检索
        print(f"🔍 检索相关文档...")
        retrieved = self.kb.query(query_text, top_k=top_k)
        
        if not retrieved:
            return QueryResult(answer="未找到相关信息。", confidence=0.0)
        
        # 准备上下文
        context_parts = []
        citations = []
        
        for i, (chunk, score) in enumerate(retrieved):
            context_parts.append(f"[文档 {i+1}]\n{chunk.text}\n")
            if with_citation:
                citations.append(Citation(
                    chunk_id=chunk.id,
                    text=chunk.text,
                    source=chunk.source,
                    page=chunk.page,
                    score=score
                ))
        
        context = "\n".join(context_parts)
        
        # 构建 Prompt
        prompt = f"""基于以下参考文档回答问题。如果参考文档中没有相关信息，请明确说明。

参考文档：
{context}

问题：{query_text}

请提供准确、简洁的回答。如果使用了参考文档中的信息，请在回答中标注引用 [1], [2] 等。

回答："""
        
        # 生成
        print(f"🤖 生成回答...")
        answer = self.llm_client.generate(prompt)
        
        avg_score = sum(score for _, score in retrieved) / len(retrieved) if retrieved else 0
        
        return QueryResult(
            answer=answer,
            citations=citations if with_citation else [],
            confidence=avg_score
        )


# ============================================================================
# LLM 客户端
# ============================================================================

class KimiLLMClient:
    """Kimi API 客户端"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
    
    def generate(self, prompt: str, model: str = "moonshot-v1-8k") -> str:
        if not self.api_key:
            return "[模拟回答] 请设置 KIMI_API_KEY 获取真实回答。"
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url="https://api.moonshot.cn/v1")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[错误] API 调用失败: {e}"


# ============================================================================
# CLI
# ============================================================================

def print_help():
    print("""
Mini-RAGFlow Light - 轻量级 RAG 引擎 (BM25 版本)

用法:
    python mini_ragflow_light.py parse <文件> [--template TEMPLATE]
    python mini_ragflow_light.py index <目录> --kb <名称>
    python mini_ragflow_light.py query <问题> --kb <名称> [--cite]
    python mini_ragflow_light.py list
    python mini_ragflow_light.py delete --kb <名称>

示例:
    python mini_ragflow_light.py parse contract.txt --template laws
    python mini_ragflow_light.py index ./docs --kb legal_kb
    python mini_ragflow_light.py query "违约金是多少？" --kb legal_kb --cite
""")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print_help()
        sys.exit(0)
    
    command = args[0]
    kb_name = None
    template = "naive"
    with_cite = False
    
    # 解析选项
    i = 1
    while i < len(args):
        if args[i] == "--kb" and i + 1 < len(args):
            kb_name = args[i + 1]
            i += 2
        elif args[i] == "--template" and i + 1 < len(args):
            template = args[i + 1]
            i += 2
        elif args[i] == "--cite":
            with_cite = True
            i += 1
        else:
            i += 1
    
    try:
        if command == "parse":
            if len(args) < 2:
                print("错误: 需要提供文件路径")
                sys.exit(1)
            
            file_path = args[1]
            print(f"📄 解析文档: {file_path} (模板: {template})")
            
            parser = DeepDocParser()
            chunks = parser.parse(file_path, template=template)
            
            print(f"✅ 解析完成，共 {len(chunks)} 个文本块")
            for c in chunks[:5]:
                print(f"  - {c.id}: {c.text[:50]}...")
        
        elif command == "index":
            if len(args) < 2 or not kb_name:
                print("错误: 需要提供目录和 --kb 参数")
                sys.exit(1)
            
            docs_dir = args[1]
            print(f"📚 构建知识库: {kb_name}")
            
            parser = DeepDocParser()
            kb = BM25KnowledgeBase(kb_name)
            
            # 解析所有文档
            all_chunks = []
            docs_path = Path(docs_dir)
            files = list(docs_path.glob("**/*"))
            files = [f for f in files if f.suffix.lower() in parser.supported_formats]
            
            for file in files[:10]:  # 限制文件数量
                print(f"   解析: {file.name}")
                try:
                    chunks = parser.parse(str(file), template=template)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"   ⚠️ 失败: {e}")
            
            kb.add_documents(all_chunks)
        
        elif command == "query":
            if len(args) < 2 or not kb_name:
                print("错误: 需要提供问题和 --kb 参数")
                sys.exit(1)
            
            query_text = args[1]
            print(f"❓ 问题: {query_text}")
            
            kb = BM25KnowledgeBase(kb_name)
            llm = KimiLLMClient()
            
            engine = RAGEngine(kb)
            engine.set_llm_client(llm)
            
            result = engine.query(query_text, with_citation=with_cite)
            
            print(f"\n{'='*50}")
            print(result.to_markdown())
            print(f"{'='*50}")
        
        elif command == "list":
            print("📚 知识库列表:")
            KB_DIR.mkdir(parents=True, exist_ok=True)
            kbs = [d.name for d in KB_DIR.iterdir() if d.is_dir()]
            for kb in kbs:
                print(f"  - {kb}")
        
        elif command == "delete":
            if not kb_name:
                print("错误: 需要使用 --kb 参数")
                sys.exit(1)
            BM25KnowledgeBase(kb_name).delete()
        
        else:
            print(f"未知命令: {command}")
            print_help()
    
    except KeyboardInterrupt:
        print("\n⏹️ 已取消")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
