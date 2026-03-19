#!/usr/bin/env python3
"""
Real API Tools - 真实API实现
替换模拟数据，使用真实HTTP请求
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from datetime import datetime


def web_search_brave_real(
    query: str,
    count: int = 5,
    freshness: Optional[str] = None,
    country: str = "US"
) -> Dict[str, Any]:
    """
    使用Brave Search API搜索网络 (真实实现)
    需要 BRAVE_API_KEY 环境变量
    """
    import os
    
    api_key = os.environ.get('BRAVE_API_KEY')
    
    if not api_key:
        # 如果没有API key，使用替代搜索方案
        return _fallback_search(query, count)
    
    try:
        headers = {
            'X-Subscription-Token': api_key,
            'Accept': 'application/json'
        }
        
        url = f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count={min(count, 20)}"
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            results = []
            for item in data.get('web', {}).get('results', [])[:count]:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'description': item.get('description', '')
                })
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'total': len(results),
                'source': 'brave_api'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'query': query
        }


def _fallback_search(query: str, count: int = 5) -> Dict[str, Any]:
    """备用搜索 - 使用DuckDuckGo (无需API key)"""
    try:
        import urllib.parse
        
        # DuckDuckGo HTML搜索
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
            
            # 简单解析结果
            results = []
            import re
            
            # 提取搜索结果
            titles = re.findall(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', html)
            snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html)
            urls = re.findall(r'<a[^>]*class="result__url"[^>]*href="([^"]*)"', html)
            
            for i in range(min(count, len(titles))):
                # 清理HTML标签
                title = re.sub(r'<[^>]+>', '', titles[i]) if i < len(titles) else ''
                snippet = re.sub(r'<[^>]+>', '', snippets[i]) if i < len(snippets) else ''
                url = urls[i] if i < len(urls) else ''
                
                if title:
                    results.append({
                        'title': title,
                        'url': url,
                        'description': snippet
                    })
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'total': len(results),
                'source': 'duckduckgo_fallback',
                'note': 'Using DuckDuckGo (Brave API key not configured)'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Fallback search failed: {str(e)}',
            'query': query
        }


def web_fetch_page_real(
    url: str,
    extract_mode: str = "markdown",
    max_chars: int = 5000
) -> Dict[str, Any]:
    """
    抓取网页内容 (真实实现)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            content_type = response.headers.get('Content-Type', '')
            
            # 处理编码
            charset = 'utf-8'
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[-1].split(';')[0].strip()
            
            html = response.read().decode(charset, errors='ignore')
            
            # 转换为markdown
            if extract_mode == "markdown":
                content = _html_to_markdown(html)
            else:
                content = _extract_text(html)
            
            # 截断
            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n... [truncated]"
            
            return {
                'success': True,
                'url': url,
                'content': content,
                'length': len(content),
                'title': _extract_title(html),
                'extract_mode': extract_mode
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'url': url
        }


def _html_to_markdown(html: str) -> str:
    """简单HTML转Markdown"""
    import re
    
    # 提取title
    title = _extract_title(html)
    
    # 移除script和style
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    
    # 转换标题
    html = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n\n', html, flags=re.DOTALL)
    html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n\n', html, flags=re.DOTALL)
    html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n\n', html, flags=re.DOTALL)
    
    # 转换段落
    html = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html, flags=re.DOTALL)
    
    # 转换链接
    html = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', html, flags=re.DOTALL)
    
    # 转换代码
    html = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', html, flags=re.DOTALL)
    html = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```\n', html, flags=re.DOTALL)
    
    # 移除其他标签
    html = re.sub(r'<[^>]+>', '', html)
    
    # 清理
    html = re.sub(r'&lt;', '<', html)
    html = re.sub(r'&gt;', '>', html)
    html = re.sub(r'&amp;', '&', html)
    html = re.sub(r'&quot;', '"', html)
    
    # 合并空行
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    return f"# {title}\n\n{html.strip()}"


def _extract_text(html: str) -> str:
    """提取纯文本"""
    import re
    # 移除script和style
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    # 移除所有标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 清理空白
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _extract_title(html: str) -> str:
    """提取标题"""
    import re
    match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    if match:
        return re.sub(r'<[^>]+>', '', match.group(1)).strip()
    return "No title"


def research_github_explore_real(
    repo: Optional[str] = None,
    topic: Optional[str] = None,
    action: str = "info"
) -> Dict[str, Any]:
    """
    探索GitHub仓库/话题 (真实API实现)
    GitHub API对公开仓库不需要认证
    """
    try:
        if repo:
            # 获取仓库信息
            url = f"https://api.github.com/repos/{repo}"
            
            headers = {
                'User-Agent': 'Kimi-MCP-Server',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                return {
                    'success': True,
                    'repo': repo,
                    'info': {
                        'name': data.get('name'),
                        'full_name': data.get('full_name'),
                        'description': data.get('description'),
                        'stars': data.get('stargazers_count'),
                        'forks': data.get('forks_count'),
                        'language': data.get('language'),
                        'created_at': data.get('created_at'),
                        'updated_at': data.get('updated_at'),
                        'url': data.get('html_url'),
                        'topics': data.get('topics', []),
                        'open_issues': data.get('open_issues_count'),
                        'license': data.get('license', {}).get('name') if data.get('license') else None
                    },
                    'source': 'github_api'
                }
        
        elif topic:
            # 搜索话题
            url = f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&order=desc&per_page=10"
            
            headers = {
                'User-Agent': 'Kimi-MCP-Server',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                repos = []
                for item in data.get('items', []):
                    repos.append({
                        'name': item.get('full_name'),
                        'stars': item.get('stargazers_count'),
                        'language': item.get('language'),
                        'description': item.get('description'),
                        'url': item.get('html_url')
                    })
                
                return {
                    'success': True,
                    'topic': topic,
                    'repositories': repos,
                    'total_count': data.get('total_count', 0),
                    'source': 'github_api'
                }
        
        else:
            return {'success': False, 'error': 'Either repo or topic required'}
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {'success': False, 'error': f'Repository not found: {repo}'}
        elif e.code == 403:
            return {'success': False, 'error': 'GitHub API rate limit exceeded. Try again later.'}
        else:
            return {'success': False, 'error': f'GitHub API error: {e.code}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def test_real_tools():
    """测试真实API Tools"""
    print("="*70)
    print("🔬 TESTING REAL API TOOLS")
    print("="*70)
    
    # Test 1: GitHub API
    print("\n1️⃣ Testing GitHub API (microsoft/vscode)...")
    result = research_github_explore_real(repo="microsoft/vscode")
    if result['success']:
        info = result['info']
        print(f"   ✅ {info['full_name']}")
        print(f"   ⭐ Stars: {info['stars']:,}")
        print(f"   🍴 Forks: {info['forks']:,}")
        print(f"   💻 Language: {info['language']}")
        print(f"   📝 {info['description'][:80]}...")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Test 2: Web Fetch
    print("\n2️⃣ Testing Web Fetch (docs.python.org)...")
    result = web_fetch_page_real("https://docs.python.org/3/", max_chars=500)
    if result['success']:
        print(f"   ✅ Title: {result['title']}")
        print(f"   📄 Content length: {len(result['content'])} chars")
        print(f"   📝 Preview: {result['content'][:100]}...")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Test 3: Search (Fallback)
    print("\n3️⃣ Testing Search (fallback to DuckDuckGo)...")
    result = _fallback_search("Python programming language", count=3)
    if result['success']:
        print(f"   ✅ Query: {result['query']}")
        print(f"   📊 Results: {result['total']}")
        print(f"   📡 Source: {result['source']}")
        for i, r in enumerate(result['results'][:2], 1):
            print(f"   {i}. {r['title'][:50]}...")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    print("\n" + "="*70)
    print("✅ REAL API TOOLS TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_real_tools()
