#!/usr/bin/env python3
"""
Quick test of real API tools
"""

import json
import urllib.request

def test_github():
    """测试GitHub API"""
    print("Testing GitHub API...")
    try:
        url = "https://api.github.com/repos/microsoft/vscode"
        headers = {
            'User-Agent': 'Kimi-MCP-Server',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f"✅ Success!")
            print(f"   Repo: {data.get('full_name')}")
            print(f"   Stars: {data.get('stargazers_count', 0):,}")
            print(f"   Language: {data.get('language')}")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_fetch():
    """测试网页抓取"""
    print("\nTesting Web Fetch...")
    try:
        url = "https://docs.python.org/3/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # 提取标题
            import re
            match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
            title = re.sub(r'<[^>]+>', '', match.group(1)).strip() if match else "No title"
            
            print(f"✅ Success!")
            print(f"   Title: {title}")
            print(f"   Length: {len(html)} chars")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search():
    """测试搜索"""
    print("\nTesting Search...")
    try:
        import urllib.parse
        query = "Python programming"
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # 简单检查是否有结果
            if "result__a" in html:
                print(f"✅ Success!")
                print(f"   Got search results")
                return True
            else:
                print(f"⚠️  No results found")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import re  # 确保导入
    
    print("="*60)
    print("REAL API TOOLS QUICK TEST")
    print("="*60)
    
    results = []
    results.append(("GitHub API", test_github()))
    results.append(("Web Fetch", test_fetch()))
    results.append(("Search", test_search()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {name}")
    
    passed = sum(1 for _, p in results if p)
    print(f"\n   Total: {passed}/{len(results)} passed")
