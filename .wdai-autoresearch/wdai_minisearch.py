#!/usr/bin/env python3
"""
wdai MiniSearch - 轻量级搜索引擎
功能: 本地文件索引 + 倒排索引 + TF-IDF排名 + Web界面
"""

import os
import re
import json
import math
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from datetime import datetime
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse


class Document:
    """文档对象"""
    def __init__(self, doc_id: str, path: str, content: str, title: str = ""):
        self.id = doc_id
        self.path = path
        self.content = content
        self.title = title or path.split('/')[-1]
        self.word_count = len(content.split())
        self.tf = {}  # 词频
        
    def compute_tf(self):
        """计算词频"""
        words = self._tokenize(self.content)
        word_counts = Counter(words)
        total = len(words)
        self.tf = {word: count/total for word, count in word_counts.items()}
        return self.tf
    
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """简单的中文/英文分词"""
        # 转换为小写
        text = text.lower()
        # 提取英文单词
        english_words = re.findall(r'[a-z]+', text)
        # 提取中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return english_words + chinese_chars


class InvertedIndex:
    """倒排索引"""
    
    def __init__(self):
        self.index: Dict[str, Set[str]] = defaultdict(set)  # word -> set(doc_ids)
        self.documents: Dict[str, Document] = {}
        self.idf: Dict[str, float] = {}  # 逆文档频率
        self.doc_count = 0
        
    def add_document(self, doc: Document):
        """添加文档到索引"""
        words = Document._tokenize(doc.content)
        unique_words = set(words)
        
        for word in unique_words:
            self.index[word].add(doc.id)
        
        self.documents[doc.id] = doc
        self.doc_count += 1
        
    def compute_idf(self):
        """计算IDF"""
        for word, doc_ids in self.index.items():
            # IDF = log(N / df)
            self.idf[word] = math.log(self.doc_count / len(doc_ids) + 1)
            
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """搜索并返回排序后的结果"""
        query_words = Document._tokenize(query)
        if not query_words:
            return []
        
        scores = defaultdict(float)
        
        for word in query_words:
            if word in self.index:
                idf = self.idf.get(word, 0)
                for doc_id in self.index[word]:
                    doc = self.documents[doc_id]
                    tf = doc.tf.get(word, 0)
                    # TF-IDF评分
                    scores[doc_id] += tf * idf
        
        # 按分数排序
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def save(self, path: str):
        """保存索引到文件"""
        data = {
            'index': {k: list(v) for k, v in self.index.items()},
            'documents': {
                doc_id: {
                    'id': doc.id,
                    'path': doc.path,
                    'title': doc.title,
                    'word_count': doc.word_count,
                    'tf': doc.tf
                }
                for doc_id, doc in self.documents.items()
            },
            'idf': self.idf,
            'doc_count': self.doc_count
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, path: str):
        """从文件加载索引"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.index = defaultdict(set, {k: set(v) for k, v in data['index'].items()})
        self.idf = data['idf']
        self.doc_count = data['doc_count']
        
        for doc_id, doc_data in data['documents'].items():
            doc = Document(doc_data['id'], doc_data['path'], "", doc_data['title'])
            doc.word_count = doc_data['word_count']
            doc.tf = doc_data['tf']
            self.documents[doc_id] = doc


class Crawler:
    """本地文件爬虫"""
    
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.supported_ext = {'.txt', '.md', '.py', '.js', '.json', '.html', '.css'}
        
    def crawl(self) -> List[Document]:
        """爬取文件"""
        documents = []
        
        for file_path in self.root.rglob('*'):
            if file_path.is_file() and file_path.suffix in self.supported_ext:
                try:
                    content = self._read_file(file_path)
                    if content:
                        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()[:16]
                        doc = Document(
                            doc_id=doc_id,
                            path=str(file_path.relative_to(self.root)),
                            content=content,
                            title=file_path.name
                        )
                        doc.compute_tf()
                        documents.append(doc)
                except Exception as e:
                    print(f"⚠️  无法读取 {file_path}: {e}")
        
        return documents
    
    def _read_file(self, path: Path) -> str:
        """读取文件内容"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            try:
                with open(path, 'r', encoding='gbk') as f:
                    return f.read()
            except:
                return ""


class SearchEngine:
    """搜索引擎主类"""
    
    def __init__(self, index_dir: str = ".wdai-search"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        self.index = InvertedIndex()
        self.index_path = self.index_dir / "index.json"
        self.stats_path = self.index_dir / "stats.json"
        
    def build_index(self, source_dir: str):
        """构建索引"""
        print(f"🔍 开始索引: {source_dir}")
        
        crawler = Crawler(source_dir)
        documents = crawler.crawl()
        
        print(f"📄 找到 {len(documents)} 个文档")
        
        for doc in documents:
            self.index.add_document(doc)
        
        self.index.compute_idf()
        self.index.save(str(self.index_path))
        
        # 保存统计
        stats = {
            'doc_count': len(documents),
            'term_count': len(self.index.index),
            'indexed_at': datetime.now().isoformat(),
            'source_dir': source_dir
        }
        with open(self.stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"✅ 索引完成!")
        print(f"   文档数: {len(documents)}")
        print(f"   词汇数: {len(self.index.index)}")
        print(f"   索引文件: {self.index_path}")
        
    def load(self):
        """加载已有索引"""
        if self.index_path.exists():
            self.index.load(str(self.index_path))
            print(f"✅ 已加载索引: {self.index.doc_count} 个文档")
            return True
        return False
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """执行搜索"""
        if not self.index.documents:
            self.load()
        
        results = self.index.search(query, top_k)
        
        output = []
        for doc_id, score in results:
            doc = self.index.documents[doc_id]
            output.append({
                'id': doc_id,
                'title': doc.title,
                'path': doc.path,
                'score': round(score, 4),
                'word_count': doc.word_count
            })
        
        return output
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if self.stats_path.exists():
            with open(self.stats_path) as f:
                return json.load(f)
        return {}


class SearchHandler(BaseHTTPRequestHandler):
    """Web请求处理器"""
    
    engine = None
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        
        if path == '/' or path == '/search':
            query = params.get('q', [''])[0]
            results = []
            
            if query and self.engine:
                results = self.engine.search(query)
            
            html = self._render_page(query, results)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        elif path == '/api/search':
            query = params.get('q', [''])[0]
            results = self.engine.search(query) if self.engine else []
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())
            
        elif path == '/api/stats':
            stats = self.engine.get_stats() if self.engine else {}
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
            
        else:
            self.send_error(404)
    
    def _render_page(self, query: str, results: List[Dict]) -> str:
        """渲染搜索页面"""
        results_html = ""
        for r in results:
            results_html += f"""
            <div class="result">
                <div class="title">{r['title']}</div>
                <div class="path">{r['path']}</div>
                <div class="meta">评分: {r['score']} | 词数: {r['word_count']}</div>
            </div>
            """
        
        if query and not results:
            results_html = '<div class="no-results">未找到结果</div>'
        
        stats = self.engine.get_stats() if self.engine else {}
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>wdai MiniSearch</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 32px;
            color: #333;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 14px;
        }}
        .search-box {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .search-box input {{
            width: 100%;
            padding: 12px 16px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            outline: none;
        }}
        .search-box input:focus {{
            border-color: #4CAF50;
        }}
        .stats {{
            background: white;
            border-radius: 8px;
            padding: 15px 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            font-size: 14px;
            color: #666;
        }}
        .results {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .result {{
            padding: 20px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .result:last-child {{
            border-bottom: none;
        }}
        .result .title {{
            font-size: 16px;
            font-weight: 600;
            color: #1a0dab;
            margin-bottom: 4px;
        }}
        .result .path {{
            font-size: 13px;
            color: #006621;
            margin-bottom: 4px;
        }}
        .result .meta {{
            font-size: 12px;
            color: #999;
        }}
        .no-results {{
            padding: 40px;
            text-align: center;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 wdai MiniSearch</h1>
            <div class="subtitle">轻量级本地搜索引擎 | TF-IDF排名 | 倒排索引</div>
        </div>
        
        <div class="search-box">
            <form method="GET" action="/search">
                <input type="text" name="q" value="{query}" 
                       placeholder="输入搜索词..." autofocus>
            </form>
        </div>
        
        <div class="stats">
            📊 索引统计: {stats.get('doc_count', 0)} 文档 | 
            {stats.get('term_count', 0)} 词汇 | 
            索引时间: {stats.get('indexed_at', 'N/A')[:10] if stats.get('indexed_at') else 'N/A'}
        </div>
        
        <div class="results">
            {results_html}
        </div>
    </div>
</body>
</html>"""
    
    def log_message(self, format, *args):
        pass  # 禁用日志输出


def main():
    """主函数"""
    import sys
    
    print("=" * 60)
    print("🔍 wdai MiniSearch - 轻量级搜索引擎")
    print("=" * 60)
    print()
    print("命令:")
    print("  python3 wdai_minisearch.py index <目录>   - 构建索引")
    print("  python3 wdai_minisearch.py search <关键词> - 命令行搜索")
    print("  python3 wdai_minisearch.py web [端口]      - 启动Web界面")
    print()
    
    if len(sys.argv) < 2:
        print("❌ 请提供命令")
        return
    
    cmd = sys.argv[1]
    engine = SearchEngine()
    
    if cmd == 'index':
        if len(sys.argv) < 3:
            print("❌ 请提供要索引的目录")
            return
        source_dir = sys.argv[2]
        engine.build_index(source_dir)
        
    elif cmd == 'search':
        if len(sys.argv) < 3:
            print("❌ 请提供搜索关键词")
            return
        query = sys.argv[2]
        
        if not engine.load():
            print("❌ 没有找到索引，请先运行 index 命令")
            return
        
        print(f"🔍 搜索: '{query}'")
        results = engine.search(query)
        
        print(f"\n找到 {len(results)} 个结果:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['title']}")
            print(f"   路径: {r['path']}")
            print(f"   评分: {r['score']}")
            print()
            
    elif cmd == 'web':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        
        if not engine.load():
            print("⚠️  没有找到索引，将创建空索引")
        
        SearchHandler.engine = engine
        server = HTTPServer(('0.0.0.0', port), SearchHandler)
        
        print(f"🌐 Web界面已启动: http://localhost:{port}")
        print(f"   索引文档: {engine.index.doc_count}")
        print(f"   按 Ctrl+C 停止")
        print()
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 服务器已停止")
            
    else:
        print(f"❌ 未知命令: {cmd}")


if __name__ == '__main__':
    main()
