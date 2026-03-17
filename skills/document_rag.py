#!/usr/bin/env python3
"""
Document RAG Skill - 文档知识库 Skill

封装 mini_ragflow_light，提供自动化的文档解析和问答能力。

用法:
    from skills.document_rag import DocumentRAGSkill
    
    skill = DocumentRAGSkill()
    
    # 自动处理文档
    skill.process_document("合同.pdf", kb_name="legal_docs")
    
    # 问答（带引用）
    result = skill.query("违约金是多少？", kb_name="legal_docs")
    print(result.answer)
    print(result.citations)
"""

from __future__ import annotations

import json
import sys
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
import tempfile
import shutil

# 将 tools 目录加入路径
TOOLS_DIR = Path(__file__).parent.parent / ".tools"
sys.path.insert(0, str(TOOLS_DIR))

try:
    from mini_ragflow_light import (
        DeepDocParser, BM25KnowledgeBase, RAGEngine,
        KimiLLMClient, DocumentChunk, Citation, QueryResult
    )
except ImportError as e:
    print(f"Error importing mini_ragflow_light: {e}")
    print(f"请确保 {TOOLS_DIR}/mini_ragflow_light.py 存在")
    raise


@dataclass
class DocumentInfo:
    """文档信息"""
    filename: str
    chunks_count: int
    template: str
    kb_name: str


@dataclass
class RAGResponse:
    """RAG 响应"""
    answer: str
    citations: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = [self.answer, ""]
        
        if self.citations:
            lines.append("**📚 参考来源：**")
            for i, cite in enumerate(self.citations, 1):
                lines.append(f"\n{i}. **{cite.get('source', 'Unknown')}** (第{cite.get('page', 1)}页)")
                lines.append(f"   > {cite.get('text', '')[:150]}...")
                if cite.get('score'):
                    lines.append(f"   _相关度: {cite.get('score'):.1%}_")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": self.citations,
            "confidence": self.confidence,
            "sources": list(set(self.sources))
        }


class DocumentRAGSkill:
    """
    文档 RAG Skill
    
    自动化的文档解析和知识库问答系统。
    """
    
    def __init__(self, api_key: str = None):
        """
        初始化 Skill
        
        Args:
            api_key: Kimi API Key（可选，不设置则使用模拟回答）
        """
        self.parser = DeepDocParser()
        self.llm_client = KimiLLMClient(api_key=api_key)
        self._active_kbs: Dict[str, BM25KnowledgeBase] = {}
    
    def _get_kb(self, name: str) -> BM25KnowledgeBase:
        """获取或加载知识库"""
        if name not in self._active_kbs:
            self._active_kbs[name] = BM25KnowledgeBase(name)
        return self._active_kbs[name]
    
    def detect_template(self, file_path: Union[str, Path]) -> str:
        """
        自动检测文档类型并返回推荐模板
        
        Args:
            file_path: 文件路径
            
        Returns:
            推荐的模板名称: naive, laws, paper
        """
        path = Path(file_path)
        
        # 读取部分内容进行检测
        try:
            if path.suffix.lower() == '.pdf':
                import fitz
                doc = fitz.open(path)
                text = ""
                for page in doc[:3]:  # 前3页
                    text += page.get_text()
                doc.close()
            else:
                text = path.read_text(encoding='utf-8', errors='ignore')[:5000]
        except:
            return "naive"
        
        # 检测法律文档特征
        law_patterns = [
            r'第[一二三四五六七八九十百千]+条',
            r'合同|协议|条款|甲方|乙方',
            r'违约|赔偿|保密|知识产权'
        ]
        law_score = sum(1 for p in law_patterns if re.search(p, text))
        
        # 检测论文特征
        paper_patterns = [
            r'Abstract|Introduction|Methods|Results|Discussion',
            r'摘要|关键词|引言|方法|结果|讨论|结论'
        ]
        paper_score = sum(1 for p in paper_patterns if re.search(p, text, re.I))
        
        if law_score >= 2:
            return "laws"
        elif paper_score >= 2:
            return "paper"
        else:
            return "naive"
    
    def process_document(
        self, 
        file_path: Union[str, Path], 
        kb_name: str,
        template: str = "auto",
        verbose: bool = True
    ) -> DocumentInfo:
        """
        处理文档并添加到知识库
        
        Args:
            file_path: 文档路径
            kb_name: 知识库名称
            template: 分块模板 (auto, naive, laws, paper)，auto 表示自动检测
            verbose: 是否打印详细信息
            
        Returns:
            DocumentInfo: 处理结果信息
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 自动检测模板
        if template == "auto":
            template = self.detect_template(path)
            if verbose:
                print(f"🔍 检测到文档类型: {template}")
        
        if verbose:
            print(f"📄 解析文档: {path.name}")
            print(f"   使用模板: {template}")
        
        # 解析文档
        chunks = self.parser.parse(str(path), template=template)
        
        if verbose:
            print(f"✅ 解析完成，共 {len(chunks)} 个文本块")
        
        # 添加到知识库
        kb = self._get_kb(kb_name)
        kb.add_documents(chunks)
        
        return DocumentInfo(
            filename=path.name,
            chunks_count=len(chunks),
            template=template,
            kb_name=kb_name
        )
    
    def process_directory(
        self,
        dir_path: Union[str, Path],
        kb_name: str,
        template: str = "auto",
        file_types: List[str] = None,
        verbose: bool = True
    ) -> List[DocumentInfo]:
        """
        批量处理目录中的文档
        
        Args:
            dir_path: 目录路径
            kb_name: 知识库名称
            template: 分块模板
            file_types: 处理的文件类型列表，如 ['.pdf', '.docx']
            verbose: 是否打印详细信息
            
        Returns:
            List[DocumentInfo]: 每个文档的处理结果
        """
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"目录不存在: {dir_path}")
        
        # 默认文件类型
        if file_types is None:
            file_types = ['.pdf', '.docx', '.txt', '.md']
        
        # 收集文件
        files = []
        for ext in file_types:
            files.extend(dir_path.glob(f"**/*{ext}"))
        
        if verbose:
            print(f"📁 发现 {len(files)} 个文档")
        
        # 处理每个文件
        results = []
        for file in files:
            try:
                info = self.process_document(file, kb_name, template, verbose=False)
                results.append(info)
                if verbose:
                    print(f"  ✅ {file.name}: {info.chunks_count} chunks")
            except Exception as e:
                if verbose:
                    print(f"  ❌ {file.name}: {e}")
        
        if verbose:
            total_chunks = sum(r.chunks_count for r in results)
            print(f"\n📊 总计: {len(results)} 个文档, {total_chunks} 个文本块")
        
        return results
    
    def query(
        self,
        question: str,
        kb_name: str,
        top_k: int = 5,
        with_citation: bool = True
    ) -> RAGResponse:
        """
        基于知识库回答问题
        
        Args:
            question: 问题
            kb_name: 知识库名称
            top_k: 检索文档数量
            with_citation: 是否包含有据引用
            
        Returns:
            RAGResponse: 回答和引用信息
        """
        # 获取知识库
        kb = self._get_kb(kb_name)
        
        # 检查知识库是否为空
        if not kb.chunks:
            return RAGResponse(
                answer=f"知识库 '{kb_name}' 为空，请先添加文档。",
                citations=[],
                confidence=0.0
            )
        
        # 执行 RAG
        engine = RAGEngine(kb)
        engine.set_llm_client(self.llm_client)
        
        result = engine.query(question, top_k=top_k, with_citation=with_citation)
        
        # 转换为 RAGResponse
        citations = [
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "source": c.source,
                "page": c.page,
                "score": c.score
            }
            for c in result.citations
        ]
        
        sources = list(set(c.source for c in result.citations))
        
        return RAGResponse(
            answer=result.answer,
            citations=citations,
            confidence=result.confidence,
            sources=sources
        )
    
    def quick_answer(
        self,
        question: str,
        file_path: Union[str, Path],
        template: str = "auto"
    ) -> RAGResponse:
        """
        快速问答 - 处理单个文档并立即回答
        
        适用于一次性问答场景，不需要持久化知识库。
        
        Args:
            question: 问题
            file_path: 文档路径
            template: 分块模板
            
        Returns:
            RAGResponse: 回答
        """
        # 创建临时知识库
        temp_kb_name = f"temp_{hash(file_path) % 10000}"
        
        try:
            # 处理文档
            self.process_document(file_path, temp_kb_name, template, verbose=False)
            
            # 回答问题
            result = self.query(question, temp_kb_name, with_citation=True)
            
            return result
        finally:
            # 清理临时知识库
            kb = self._get_kb(temp_kb_name)
            kb.delete()
    
    def list_knowledge_bases(self) -> List[str]:
        """列出所有知识库"""
        from mini_ragflow_light import KB_DIR
        
        if not KB_DIR.exists():
            return []
        
        return [d.name for d in KB_DIR.iterdir() if d.is_dir()]
    
    def get_kb_info(self, kb_name: str) -> Dict[str, Any]:
        """获取知识库信息"""
        kb = self._get_kb(kb_name)
        
        sources = set()
        for chunk in kb.chunks:
            sources.add(chunk.source)
        
        return {
            "name": kb_name,
            "chunks_count": len(kb.chunks),
            "sources": list(sources),
            "path": str(kb.kb_path)
        }
    
    def delete_knowledge_base(self, kb_name: str):
        """删除知识库"""
        kb = self._get_kb(kb_name)
        kb.delete()
        if kb_name in self._active_kbs:
            del self._active_kbs[kb_name]


# ============================================================================
# CLI 接口
# ============================================================================

def cli_main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Document RAG Skill")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # process 命令
    process_parser = subparsers.add_parser("process", help="处理文档")
    process_parser.add_argument("file", help="文档路径")
    process_parser.add_argument("--kb", required=True, help="知识库名称")
    process_parser.add_argument("--template", default="auto", help="分块模板")
    
    # query 命令
    query_parser = subparsers.add_parser("query", help="问答")
    query_parser.add_argument("question", help="问题")
    query_parser.add_argument("--kb", required=True, help="知识库名称")
    query_parser.add_argument("--top-k", type=int, default=5, help="检索数量")
    
    # quick 命令
    quick_parser = subparsers.add_parser("quick", help="快速问答")
    quick_parser.add_argument("question", help="问题")
    quick_parser.add_argument("file", help="文档路径")
    
    # list 命令
    subparsers.add_parser("list", help="列出知识库")
    
    # info 命令
    info_parser = subparsers.add_parser("info", help="知识库信息")
    info_parser.add_argument("kb", help="知识库名称")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    skill = DocumentRAGSkill()
    
    if args.command == "process":
        info = skill.process_document(args.file, args.kb, args.template)
        print(f"\n✅ 处理完成:")
        print(f"   文件: {info.filename}")
        print(f"   模板: {info.template}")
        print(f"   分块: {info.chunks_count}")
        print(f"   知识库: {info.kb_name}")
    
    elif args.command == "query":
        result = skill.query(args.question, args.kb, top_k=args.top_k)
        print(result.to_markdown())
    
    elif args.command == "quick":
        result = skill.quick_answer(args.question, args.file)
        print(result.to_markdown())
    
    elif args.command == "list":
        kbs = skill.list_knowledge_bases()
        print("📚 知识库列表:")
        for kb in kbs:
            print(f"  - {kb}")
    
    elif args.command == "info":
        info = skill.get_kb_info(args.kb)
        print(f"📊 知识库: {info['name']}")
        print(f"   文本块: {info['chunks_count']}")
        print(f"   来源文档: {', '.join(info['sources'])}")


if __name__ == "__main__":
    import re  # 需要添加 re 导入
    cli_main()
