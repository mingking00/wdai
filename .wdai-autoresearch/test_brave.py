#!/usr/bin/env python3
"""
wdai AutoResearch v3.1 - Brave Search 测试
简化版，测试API连接
"""

import asyncio
import os
import sys
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
AUTORESEARCH_DIR = WORKSPACE / ".wdai-autoresearch"

# 加载环境变量
env_file = AUTORESEARCH_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().strip().split('\n'):
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key] = value

api_key = os.environ.get('BRAVE_API_KEY', '')
print(f"Brave Search API Key: {api_key[:4]}****{api_key[-4:] if len(api_key)>8 else ''}")
print(f"Key length: {len(api_key)}")

async def test_brave_search():
    import aiohttp
    
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key
    }
    params = {
        "q": "python asyncio tutorial",
        "count": 3
    }
    
    print(f"\n发送请求到 Brave Search API...")
    print(f"URL: {url}")
    print(f"Headers: {headers['X-Subscription-Token'][:10]}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=15) as resp:
                print(f"\n响应状态: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("web", {}).get("results", [])
                    print(f"✅ 成功! 获取 {len(results)} 个结果")
                    
                    for i, r in enumerate(results[:3], 1):
                        print(f"\n  {i}. {r.get('title', 'N/A')[:60]}...")
                        print(f"     {r.get('url', 'N/A')[:60]}...")
                else:
                    error = await resp.text()
                    print(f"❌ 错误: {resp.status}")
                    print(f"   {error[:200]}")
                    
    except asyncio.TimeoutError:
        print("❌ 请求超时 (15s)")
    except Exception as e:
        print(f"❌ 异常: {type(e).__name__}: {e}")

if __name__ == '__main__':
    asyncio.run(test_brave_search())
