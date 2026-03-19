#!/usr/bin/env python3
"""
Mini-RAGFlow - 轻量级 RAG 引擎

纯 Python 实现 RAGFlow 核心功能，无需复杂部署：
- DeepDoc 风格文档解析
- 本地向量知识库
- 简单 Agentic 工作流
- 有据引用支持

依赖安装:
    pip install chromadb sentence-transformers unstructured pdf2image pypdf
    
可选（用于 OCR）:
    pip install paddlepaddle paddleocr

用法:
    python mini_ragflow.py parse doc.pdf --output chunks.json
    python mini_ragflow.py index ./docs --kb my_kb
    python mini_ragflow.py query "问题" --kb my_kb --cite
    python mini_ragflow.py agent "复杂任务" --kb my_kb
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import hashlib
import shutil

# ============================================================================
# 配置
# ============================================================================

CACHE_DIR = Path.home() / ".cache" / "mini-ragflow"
KB_DIR = Path.home() / ".config" / "mini-ragflow" / "knowledge_bases"
DEFAULT_EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"  # 使用中文模型，国内更容易下载
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# ============================================================================
# 数据模型
# ============================================================================

@dataclass
class DocumentChunk:
    """文档分块"""
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""  # 来源文件
    page: int = 0     # 页码
    bbox: Optional[Tuple[float, float, float, float]] = None  # 坐标
    chunk_type: str = "text"  # text, table, title, etc.
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "metadata": self.metadata,
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
    
    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text[:150] + "..." if len(self.text) > 150 else self.text,
            "source": self.source,
            "page": self.page,
            "relevance_score": round(self.score, 4)
        }

@dataclass
class QueryResult:
    """查询结果"""
    answer: str
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        lines = [self.answer, ""]
        if self.citations:
            lines.append("**参考来源：**")
            for i, cite in enumerate(self.citations, 1):
                lines.append(f"{i}. {cite.source} (第{cite.page}页) - 相关度: {cite.score:.2%}")
                lines.append(f"   > {cite.text[:100]}...")
        return "\n".join(lines)

# ============================================================================
# DeepDoc 风格文档解析
# ============================================================================

class DeepDocParser:
    """深度文档解析器"""
    
    def __init__(self):
        self.supported_formats = {'.pdf', '.docx', '.txt', '.md', '.html'}
        self._init_parsers()
    
    def _init_parsers(self):
        """初始化解析器"""
        try:
            import pypdf
            self.has_pypdf = True
        except ImportError:
            self.has_pypdf = False
            
        try:
            from unstructured.partition.pdf import partition_pdf
            self.has_unstructured = True
        except ImportError:
            self.has_unstructured = False
    
    def parse(self, file_path: str, template: str = "naive") -> List[DocumentChunk]:
        """
        解析文档
        
        Args:
            file_path: 文件路径
            template: 分块模板 (naive, paper, laws, book)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        ext = path.suffix.lower()
        if ext not in self.supported_formats:
            raise ValueError(f"不支持的格式: {ext}")
        
        # 解析原始文本
        if ext == '.pdf':
            raw_chunks = self._parse_pdf(path)
        elif ext in ['.docx']:
            raw_chunks = self._parse_docx(path)
        elif ext in ['.txt', '.md']:
            raw_chunks = self._parse_text(path)
        else:
            raw_chunks = self._parse_generic(path)
        
        # 应用模板化分块
        return self._apply_template(raw_chunks, template, path.name)
    
    def _parse_pdf(self, path: Path) -> List[Dict]:
        """解析 PDF"""
        chunks = []
        
        if self.has_pypdf:
            import pypdf
            with open(path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        chunks.append({
                            "text": text,
                            "page": page_num,
                            "type": "text"
                        })
        else:
            # Fallback: 使用 PyMuPDF
            try:
                import fitz
                doc = fitz.open(path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        chunks.append({
                            "text": text,
                            "page": page_num + 1,
                            "type": "text"
                        })
                doc.close()
            except ImportError:
                print("错误: 请安装 PyMuPDF: pip install PyMuPDF")
                sys.exit(1)
        
        return chunks
    
    def _parse_docx(self, path: Path) -> List[Dict]:
        """解析 Word"""
        try:
            from docx import Document
            doc = Document(path)
            chunks = []
            current_page = 1
            
            for para in doc.paragraphs:
                if para.text.strip():
                    chunks.append({
                        "text": para.text,
                        "page": current_page,
                        "type": "text"
                    })
            return chunks
        except ImportError:
            print("错误: 请安装 python-docx: pip install python-docx")
            sys.exit(1)
    
    def _parse_text(self, path: Path) -> List[Dict]:
        """解析文本文件"""
        text = path.read_text(encoding='utf-8')
        return [{"text": text, "page": 1, "type": "text"}]
    
    def _parse_generic(self, path: Path) -> List[Dict]:
        """通用解析（使用 unstructured）"""
        if self.has_unstructured:
            from unstructured.partition.auto import partition
            elements = partition(str(path))
            return [{"text": str(e), "page": 1, "type": "text"} for e in elements]
        else:
            return self._parse_text(path)
    
    def _apply_template(self, raw_chunks: List[Dict], template: str, source: str) -> List[DocumentChunk]:
        """应用分块模板"""
        
        if template == "naive":
            return self._naive_chunking(raw_chunks, source)
        elif template == "paper":
            return self._paper_chunking(raw_chunks, source)
        elif template == "laws":
            return self._laws_chunking(raw_chunks, source)
        else:
            return self._naive_chunking(raw_chunks, source)
    
    def _naive_chunking(self, raw_chunks: List[Dict], source: str) -> List[DocumentChunk]:
        """基础分块 - 按字符切分"""
        chunks = []
        chunk_id = 0
        
        for raw in raw_chunks:
            text = raw["text"]
            page = raw.get("page", 1)
            
            # 智能分块：按段落和长度
            paragraphs = text.split('\n')
            current_chunk = ""
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # 如果当前段落太长，需要进一步切分
                if len(para) > CHUNK_SIZE:
                    if current_chunk:
                        chunk_id += 1
                        chunks.append(DocumentChunk(
                            id=f"{source}_{chunk_id}",
                            text=current_chunk.strip(),
                            source=source,
                            page=page,
                            chunk_type="text"
                        ))
                        current_chunk = ""
                    
                    # 长段落切分
                    for i in range(0, len(para), CHUNK_SIZE - CHUNK_OVERLAP):
                        sub_text = para[i:i + CHUNK_SIZE]
                        chunk_id += 1
                        chunks.append(DocumentChunk(
                            id=f"{source}_{chunk_id}",
                            text=sub_text,
                            source=source,
                            page=page,
                            chunk_type="text"
                        ))
                else:
                    # 检查是否需要新分块
                    if len(current_chunk) + len(para) > CHUNK_SIZE:
                        chunk_id += 1
                        chunks.append(DocumentChunk(
                            id=f"{source}_{chunk_id}",
                            text=current_chunk.strip(),
                            source=source,
                            page=page,
                            chunk_type="text"
                        ))
                        current_chunk = para
                    else:
                        current_chunk += "\n" + para if current_chunk else para
            
            # 处理剩余内容
            if current_chunk.strip():
                chunk_id += 1
                chunks.append(DocumentChunk(
                    id=f"{source}_{chunk_id}",
                    text=current_chunk.strip(),
                    source=source,
                    page=page,
                    chunk_type="text"
                ))
        
        return chunks
    
    def _paper_chunking(self, raw_chunks: List[Dict], source: str) -> List[DocumentChunk]:
        """学术论文分块 - 识别章节结构"""
        chunks = []
        chunk_id = 0
        
        # 章节关键词
        section_patterns = [
            r'(?:^|\n)\s*Abstract[\s:]*\n',
            r'(?:^|\n)\s*Introduction[\s:]*\n',
            r'(?:^|\n)\s*Methods?[\s:]*\n',
            r'(?:^|\n)\s*Results?[\s:]*\n',
            r'(?:^|\n)\s*Discussion[\s:]*\n',
            r'(?:^|\n)\s*Conclusion[\s:]*\n',
            r'(?:^|\n)\s*References?[\s:]*\n',
            # 中文
            r'(?:^|\n)\s*摘要[\s:]*\n',
            r'(?:^|\n)\s*引言[\s:]*\n',
            r'(?:^|\n)\s*方法[\s:]*\n',
            r'(?:^|\n)\s*结果[\s:]*\n',
            r'(?:^|\n)\s*讨论[\s:]*\n',
            r'(?:^|\n)\s*结论[\s:]*\n',
            r'(?:^|\n)\s*参考文献[\s:]*\n',
        ]
        
        full_text = "\n".join([c["text"] for c in raw_chunks])
        
        # 尝试识别章节
        sections = []
        current_pos = 0
        
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
            for match in matches:
                sections.append((match.start(), match.group().strip()))
        
        sections.sort()
        
        if len(sections) < 2:
            # 未识别到章节，回退到基础分块
            return self._naive_chunking(raw_chunks, source)
        
        # 按章节分块
        for i, (pos, section_name) in enumerate(sections):
            end_pos = sections[i + 1][0] if i + 1 < len(sections) else len(full_text)
            section_text = full_text[pos:end_pos].strip()
            
            if section_text:
                chunk_id += 1
                chunks.append(DocumentChunk(
                    id=f"{source}_{section_name.replace(' ', '_')}_{chunk_id}",
                    text=section_text[:CHUNK_SIZE * 2],  # 章节允许更长
                    source=source,
                    page=1,
                    chunk_type="section",
                    metadata={"section": section_name}
                ))
        
        return chunks
    
    def _laws_chunking(self, raw_chunks: List[Dict], source: str) -> List[DocumentChunk]:
        """法律文档分块 - 识别条款结构"""
        chunks = []
        chunk_id = 0
        
        full_text = "\n".join([c["text"] for c in raw_chunks])
        
        # 匹配法律条款: 第X条、第X章、第X节
        article_pattern = r'(?:^|\n)\s*(第[一二三四五六七八九十百千]+条[\s:：])'
        chapter_pattern = r'(?:^|\n)\s*(第[一二三四五六七八九十]+章[\s:：][^\n]*)'
        
        articles = list(re.finditer(article_pattern, full_text))
        chapters = list(re.finditer(chapter_pattern, full_text))
        
        if len(articles) < 2:
            return self._naive_chunking(raw_chunks, source)
        
        # 按条款分块
        for i, match in enumerate(articles):
            start = match.start()
            end = articles[i + 1].start() if i + 1 < len(articles) else len(full_text)
            
            article_text = full_text[start:end].strip()
            article_num = match.group(1).strip()
            
            # 确定所属章节
            chapter = ""
            for chap_match in chapters:
                if chap_match.start() < start:
                    chapter = chap_match.group(1).strip()
            
            chunk_id += 1
            chunks.append(DocumentChunk(
                id=f"{source}_{article_num.replace(' ', '_')}_{chunk_id}",
                text=article_text,
                source=source,
                page=1,
                chunk_type="article",
                metadata={"article": article_num, "chapter": chapter}
            ))
        
        return chunks


# ============================================================================
# 向量知识库
# ============================================================================

class VectorKnowledgeBase:
    """本地向量知识库"""
    
    def __init__(self, name: str, embedding_model: str = None):
        self.name = name
        self.embedding_model = embedding_model or DEFAULT_EMBEDDING_MODEL
        self.kb_path = KB_DIR / name
        self.kb_path.mkdir(parents=True, exist_ok=True)
        
        self._init_chroma()
        self._init_embedding()
    
    def _init_chroma(self):
        """初始化 ChromaDB"""
        import chromadb
        self.client = chromadb.PersistentClient(path=str(self.kb_path / "chroma"))
        self.collection = self.client.get_or_create_collection(
            name=self.name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def _init_embedding(self):
        """初始化嵌入模型（使用国内镜像源）"""
        try:
            from sentence_transformers import SentenceTransformer
            import os
            
            # 设置国内镜像源
            # 优先使用 ModelScope，备选 Hugging Face 镜像
            os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
            
            # 使用缓存目录
            cache_dir = CACHE_DIR / "models"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"正在加载嵌入模型: {self.embedding_model}")
            print(f"使用镜像源: https://hf-mirror.com")
            
            # 尝试从 ModelScope 下载（更稳定）
            model_name = self._get_modelscope_name(self.embedding_model)
            
            self.embedding_fn = SentenceTransformer(
                model_name,
                cache_folder=str(cache_dir),
                trust_remote_code=True
            )
            print("模型加载完成")
        except ImportError:
            print("错误: 请安装 sentence-transformers: pip install sentence-transformers")
            sys.exit(1)
        except Exception as e:
            print(f"从镜像源加载失败: {e}")
            print("尝试使用本地模型...")
            self._try_load_local_model()
    
    def _get_modelscope_name(self, hf_name: str) -> str:
        """将 Hugging Face 模型名转换为 ModelScope 模型名"""
        # 常见模型映射
        mappings = {
            "BAAI/bge-small-zh-v1.5": "iic/nlp_corom_sentence-embedding_chinese-base",
            "BAAI/bge-large-zh-v1.5": "BAAI/bge-large-zh-v1.5",
            "shibing624/text2vec-base-chinese": "shibing624/text2vec-base-chinese",
        }
        return mappings.get(hf_name, hf_name)
    
    def _try_load_local_model(self):
        """尝试加载本地已下载的模型"""
        cache_dir = CACHE_DIR / "models"
        
        # 检查是否有已下载的模型
        if cache_dir.exists():
            model_dirs = [d for d in cache_dir.iterdir() if d.is_dir()]
            if model_dirs:
                print(f"找到本地模型: {model_dirs[0].name}")
                from sentence_transformers import SentenceTransformer
                self.embedding_fn = SentenceTransformer(str(model_dirs[0]))
                return
        
        print("错误: 无法加载模型。请检查网络连接或手动下载模型。")
        sys.exit(1)
    
    def add_documents(self, chunks: List[DocumentChunk]):
        """添加文档到知识库"""
        if not chunks:
            return
        
        # 准备数据
        texts = [c.text for c in chunks]
        ids = [c.id for c in chunks]
        metadatas = [{
            "source": c.source,
            "page": c.page,
            "chunk_type": c.chunk_type,
            **c.metadata
        } for c in chunks]
        
        # 生成嵌入
        print(f"正在为 {len(chunks)} 个文本块生成嵌入...")
        embeddings = self.embedding_fn.encode(texts, show_progress_bar=True)
        
        # 添加到 Chroma
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        # 保存 chunks 元数据（用于引用）
        self._save_chunks_meta(chunks)
        
        print(f"✅ 已添加 {len(chunks)} 个文本块到知识库 '{self.name}'")
    
    def _save_chunks_meta(self, chunks: List[DocumentChunk]):
        """保存 chunks 元数据"""
        meta_file = self.kb_path / "chunks_meta.json"
        
        existing = {}
        if meta_file.exists():
            existing = json.loads(meta_file.read_text())
        
        for chunk in chunks:
            existing[chunk.id] = {
                "text": chunk.text,
                "source": chunk.source,
                "page": chunk.page,
                "chunk_type": chunk.chunk_type,
                "metadata": chunk.metadata
            }
        
        meta_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    
    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """查询知识库"""
        # 生成查询嵌入
        query_embedding = self.embedding_fn.encode([query_text])
        
        # 检索
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=top_k
        )
        
        # 加载元数据
        meta_file = self.kb_path / "chunks_meta.json"
        if meta_file.exists():
            all_meta = json.loads(meta_file.read_text())
        else:
            all_meta = {}
        
        # 组装结果
        chunks_with_scores = []
        for i, doc_id in enumerate(results['ids'][0]):
            distance = results['distances'][0][i]
            score = 1 - distance  # 转换为相似度
            
            meta = all_meta.get(doc_id, {})
            chunk = DocumentChunk(
                id=doc_id,
                text=meta.get("text", results['documents'][0][i]),
                source=meta.get("source", "unknown"),
                page=meta.get("page", 0),
                chunk_type=meta.get("chunk_type", "text"),
                metadata=meta.get("metadata", {})
            )
            chunks_with_scores.append((chunk, score))
        
        return chunks_with_scores
    
    def delete(self):
        """删除知识库"""
        if self.kb_path.exists():
            shutil.rmtree(self.kb_path)
            print(f"已删除知识库: {self.name}")


# ============================================================================
# RAG 引擎
# ============================================================================

class RAGEngine:
    """RAG 引擎 - 检索增强生成"""
    
    def __init__(self, kb: VectorKnowledgeBase):
        self.kb = kb
        self.llm_client = None  # 将由外部设置
    
    def set_llm_client(self, client):
        """设置 LLM 客户端"""
        self.llm_client = client
    
    def query(self, query_text: str, top_k: int = 5, with_citation: bool = True) -> QueryResult:
        """
        执行 RAG 查询
        
        Args:
            query_text: 查询文本
            top_k: 检索 top_k 个文档
            with_citation: 是否包含有据引用
        """
        if not self.llm_client:
            raise ValueError("请先设置 LLM 客户端")
        
        # 1. 检索相关文档
        print(f"🔍 检索相关文档...")
        retrieved = self.kb.query(query_text, top_k=top_k)
        
        if not retrieved:
            return QueryResult(
                answer="未找到相关信息。",
                confidence=0.0
            )
        
        # 2. 准备上下文
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
        
        # 3. 构建 Prompt
        prompt = f"""基于以下参考文档回答问题。如果参考文档中没有相关信息，请明确说明。

参考文档：
{context}

问题：{query_text}

请提供准确、简洁的回答。如果使用了参考文档中的信息，请在回答中标注引用 [1], [2] 等。

回答："""
        
        # 4. 生成回答
        print(f"🤖 生成回答...")
        answer = self.llm_client.generate(prompt)
        
        # 5. 计算置信度
        avg_score = sum(score for _, score in retrieved) / len(retrieved)
        confidence = min(avg_score * 1.2, 1.0)  # 简单启发式
        
        return QueryResult(
            answer=answer,
            citations=citations if with_citation else [],
            confidence=confidence,
            metadata={
                "retrieved_chunks": len(retrieved),
                "avg_retrieval_score": avg_score
            }
        )


# ============================================================================
# 简单 Agentic 工作流
# ============================================================================

class SimpleAgent:
    """简单 ReAct Agent"""
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine
        self.max_iterations = 3
    
    def run(self, query: str) -> QueryResult:
        """
        执行 Agentic 查询（支持多跳推理）
        
        简化版：尝试查询，如果结果不满意则重写查询再试
        """
        current_query = query
        all_citations = []
        iteration_logs = []
        
        for i in range(self.max_iterations):
            print(f"\n🔄 迭代 {i+1}/{self.max_iterations}: {current_query[:50]}...")
            
            # 执行 RAG 查询
            result = self.rag.query(current_query, top_k=3, with_citation=True)
            
            # 记录
            iteration_logs.append({
                "iteration": i + 1,
                "query": current_query,
                "answer": result.answer[:100],
                "confidence": result.confidence
            })
            
            # 收集引用
            for cite in result.citations:
                if cite.chunk_id not in [c.chunk_id for c in all_citations]:
                    all_citations.append(cite)
            
            # 检查置信度
            if result.confidence > 0.8:
                print(f"✅ 置信度足够高 ({result.confidence:.2%})，停止迭代")
                break
            
            # 重写查询（简化版：基于当前结果扩展）
            if i < self.max_iterations - 1:
                current_query = self._rewrite_query(query, result.answer)
        
        # 综合所有信息生成最终答案
        final_answer = self._synthesize(query, iteration_logs, all_citations)
        
        # 按相关度排序引用
        all_citations.sort(key=lambda x: x.score, reverse=True)
        
        return QueryResult(
            answer=final_answer,
            citations=all_citations[:5],  # 最多 5 个引用
            confidence=max([r["confidence"] for r in iteration_logs]),
            metadata={"iterations": iteration_logs}
        )
    
    def _rewrite_query(self, original_query: str, previous_answer: str) -> str:
        """重写查询（简化实现）"""
        # 实际应该用 LLM 重写，这里简化处理
        return f"{original_query} 详细信息"
    
    def _synthesize(self, original_query: str, logs: List[Dict], citations: List[Citation]) -> str:
        """综合多轮结果生成最终答案"""
        # 简化：返回最后一轮的结果
        if logs:
            return logs[-1]["answer"]
        return "无法生成答案"


# ============================================================================
# LLM 客户端（适配 Kimi）
# ============================================================================

class KimiLLMClient:
    """Kimi API 客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.base_url = base_url or "https://api.moonshot.cn/v1"
        
        if not self.api_key:
            print("警告: 未设置 KIMI_API_KEY，将使用模拟响应")
    
    def generate(self, prompt: str, model: str = "moonshot-v1-8k") -> str:
        """调用 Kimi API 生成文本"""
        if not self.api_key:
            return self._mock_generate(prompt)
        
        try:
            import openai
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"API 调用失败: {e}")
            return self._mock_generate(prompt)
    
    def _mock_generate(self, prompt: str) -> str:
        """模拟生成（无 API 时）"""
        # 简单提取 prompt 中的上下文信息作为回答
        lines = prompt.split('\n')
        for line in lines:
            if '问题：' in line:
                question = line.replace('问题：', '').strip()
                return f"[模拟回答] 关于 '{question}' 的问题，请参考提供的上下文文档。"
        
        return "[模拟回答] 这是一个模拟的回答。请设置 KIMI_API_KEY 获取真实回答。"


# ============================================================================
# CLI 接口
# ============================================================================

def print_help():
    help_text = """
Mini-RAGFlow - 轻量级 RAG 引擎

用法:
    python mini_ragflow.py parse <文件路径> [--template TEMPLATE] [--output OUTPUT]
    python mini_ragflow.py index <文档目录> --kb <知识库名称>
    python mini_ragflow.py query <问题> --kb <知识库名称> [--cite]
    python mini_ragflow.py agent <复杂问题> --kb <知识库名称>
    python mini_ragflow.py list
    python mini_ragflow.py delete --kb <知识库名称>

命令:
    parse    解析文档并输出分块结果
    index    将文档添加到知识库
    query    基于知识库回答问题
    agent    使用 Agentic 工作流回答复杂问题
    list     列出所有知识库
    delete   删除知识库

选项:
    --template {naive,paper,laws}  分块模板 (默认: naive)
    --kb NAME                      知识库名称
    --cite                         显示引用来源
    --output FILE                  输出文件路径
    --top-k N                      检索数量 (默认: 5)

示例:
    # 解析 PDF
    python mini_ragflow.py parse contract.pdf --template laws --output chunks.json
    
    # 构建知识库
    python mini_ragflow.py index ./documents --kb legal_kb
    
    # 问答（带引用）
    python mini_ragflow.py query "违约金条款是什么？" --kb legal_kb --cite
    
    # Agentic 查询
    python mini_ragflow.py agent "对比 A 和 B 合同的付款条款" --kb legal_kb

环境变量:
    KIMI_API_KEY    Kimi API 密钥（用于生成回答）
"""
    print(help_text)


def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)
    
    command = args[0]
    
    # 解析通用选项
    kb_name = None
    template = "naive"
    output = None
    with_cite = False
    top_k = 5
    
    i = 1
    while i < len(args):
        if args[i] == "--kb" and i + 1 < len(args):
            kb_name = args[i + 1]
            i += 2
        elif args[i] == "--template" and i + 1 < len(args):
            template = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == "--cite":
            with_cite = True
            i += 1
        elif args[i] == "--top-k" and i + 1 < len(args):
            top_k = int(args[i + 1])
            i += 2
        else:
            i += 1
    
    try:
        if command == "parse":
            if len(args) < 2:
                print("错误: 需要提供文件路径")
                sys.exit(1)
            
            file_path = args[1]
            print(f"📄 解析文档: {file_path}")
            print(f"   使用模板: {template}")
            
            parser = DeepDocParser()
            chunks = parser.parse(file_path, template=template)
            
            print(f"✅ 解析完成，共 {len(chunks)} 个文本块")
            
            # 输出
            result = [c.to_dict() for c in chunks]
            output_text = json.dumps(result, ensure_ascii=False, indent=2)
            
            if output:
                Path(output).write_text(output_text, encoding='utf-8')
                print(f"💾 结果已保存: {output}")
            else:
                print(output_text)
        
        elif command == "index":
            if len(args) < 2:
                print("错误: 需要提供文档目录")
                sys.exit(1)
            if not kb_name:
                print("错误: 需要使用 --kb 指定知识库名称")
                sys.exit(1)
            
            docs_dir = args[1]
            print(f"📚 构建知识库: {kb_name}")
            print(f"   文档目录: {docs_dir}")
            
            # 解析所有文档
            parser = DeepDocParser()
            all_chunks = []
            
            docs_path = Path(docs_dir)
            files = list(docs_path.glob("**/*"))
            files = [f for f in files if f.suffix.lower() in parser.supported_formats]
            
            for file in files:
                print(f"   解析: {file.name}")
                try:
                    chunks = parser.parse(str(file), template=template)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"   ⚠️ 解析失败: {e}")
            
            print(f"\n📊 共解析 {len(all_chunks)} 个文本块")
            
            # 构建知识库
            kb = VectorKnowledgeBase(kb_name)
            kb.add_documents(all_chunks)
            
            print(f"✅ 知识库 '{kb_name}' 构建完成")
        
        elif command == "query":
            if len(args) < 2:
                print("错误: 需要提供查询问题")
                sys.exit(1)
            if not kb_name:
                print("错误: 需要使用 --kb 指定知识库名称")
                sys.exit(1)
            
            query_text = args[1]
            print(f"❓ 问题: {query_text}")
            print(f"📚 知识库: {kb_name}")
            
            # 加载知识库
            kb = VectorKnowledgeBase(kb_name)
            
            # 设置 LLM
            llm = KimiLLMClient()
            
            # 执行 RAG
            engine = RAGEngine(kb)
            engine.set_llm_client(llm)
            
            result = engine.query(query_text, top_k=top_k, with_citation=with_cite)
            
            print(f"\n{'='*50}")
            print(result.to_markdown())
            print(f"{'='*50}")
            print(f"置信度: {result.confidence:.2%}")
        
        elif command == "agent":
            if len(args) < 2:
                print("错误: 需要提供查询问题")
                sys.exit(1)
            if not kb_name:
                print("错误: 需要使用 --kb 指定知识库名称")
                sys.exit(1)
            
            query_text = args[1]
            print(f"🤖 Agentic 查询: {query_text}")
            print(f"📚 知识库: {kb_name}")
            
            # 初始化
            kb = VectorKnowledgeBase(kb_name)
            llm = KimiLLMClient()
            engine = RAGEngine(kb)
            engine.set_llm_client(llm)
            agent = SimpleAgent(engine)
            
            # 执行
            result = agent.run(query_text)
            
            print(f"\n{'='*50}")
            print(result.to_markdown())
            print(f"{'='*50}")
            print(f"置信度: {result.confidence:.2%}")
        
        elif command == "list":
            print("📚 知识库列表:")
            KB_DIR.mkdir(parents=True, exist_ok=True)
            kbs = [d.name for d in KB_DIR.iterdir() if d.is_dir()]
            if kbs:
                for i, kb in enumerate(kbs, 1):
                    print(f"  {i}. {kb}")
            else:
                print("  (暂无知识库)")
        
        elif command == "delete":
            if not kb_name:
                print("错误: 需要使用 --kb 指定知识库名称")
                sys.exit(1)
            
            kb = VectorKnowledgeBase(kb_name)
            kb.delete()
        
        else:
            print(f"未知命令: {command}")
            print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⏹️ 已取消")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
