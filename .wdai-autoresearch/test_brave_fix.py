#!/usr/bin/env python3
"""
Brave Search API 配置修复测试
测试用户提供的31字符key是否可用
"""

import asyncio
import aiohttp
import os

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "BSAOqk2j2eRoo7mAlyb8ZOlSQVvvp5V")

print("=" * 60)
print("Brave Search API 配置修复测试")
print("=" * 60)
print(f"\nAPI Key: {BRAVE_API_KEY[:4]}****{BRAVE_API_KEY[-4:]}")
print(f"Key长度: {len(BRAVE_API_KEY)} 字符")
print(f"标准长度: ~40+ 字符")
print(f"当前状态: {'✅ 长度正常' if len(BRAVE_API_KEY) >= 35 else '⚠️ 可能不完整'}")

async def test_brave_api():
    """测试Brave API"""
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    params = {
        "q": "Python asyncio",
        "count": 2
    }
    
    print(f"\n{'─' * 60}")
    print("发送测试请求到 Brave Search API...")
    print(f"{'─' * 60}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as resp:
                print(f"\n响应状态: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("web", {}).get("results", [])
                    
                    print(f"✅ 成功! 获取 {len(results)} 个结果")
                    print(f"\n结果预览:")
                    for i, r in enumerate(results[:2], 1):
                        print(f"  {i}. {r.get('title', 'N/A')[:50]}...")
                        print(f"     {r.get('url', 'N/A')[:50]}...")
                    
                    return True, "API正常工作"
                    
                elif resp.status == 401:
                    error = await resp.text()
                    print(f"❌ 401 Unauthorized - API Key无效或已过期")
                    print(f"   错误详情: {error[:200]}")
                    return False, "Key无效"
                    
                elif resp.status == 403:
                    error = await resp.text()
                    print(f"❌ 403 Forbidden - 权限不足")
                    return False, "权限不足"
                    
                else:
                    error = await resp.text()
                    print(f"❌ 错误 {resp.status}: {error[:200]}")
                    return False, f"HTTP {resp.status}"
                    
    except asyncio.TimeoutError:
        print(f"❌ 请求超时")
        return False, "超时"
    except Exception as e:
        print(f"❌ 异常: {type(e).__name__}: {e}")
        return False, str(e)

async def test_openclaw_web_search():
    """测试OpenClaw的web_search工具"""
    print(f"\n{'=' * 60}")
    print("测试 OpenClaw web_search 工具...")
    print(f"{'=' * 60}")
    
    # 设置环境变量并测试
    os.environ["BRAVE_API_KEY"] = BRAVE_API_KEY
    
    try:
        from tools import web_search
        result = web_search(query="Python asyncio", count=2)
        
        print(f"\n✅ web_search 工具可用!")
        print(f"结果数量: {len(result.get('results', []))}")
        return True, "工具可用"
        
    except Exception as e:
        print(f"\n❌ web_search 工具错误: {e}")
        return False, str(e)

if __name__ == '__main__':
    # 测试直接API调用
    success, msg = asyncio.run(test_brave_api())
    
    print(f"\n{'=' * 60}")
    print("测试结果总结")
    print(f"{'=' * 60}")
    
    if success:
        print("✅ Brave API 配置成功!")
        print("   可以使用真实Brave搜索")
    else:
        print("❌ Brave API 配置失败")
        print(f"   原因: {msg}")
        print()
        print("可能原因:")
        print("   1. Key不完整（当前31字符，标准40+）")
        print("   2. Key已过期或被撤销")
        print("   3. 网络限制无法访问Brave API")
        print("   4. 账户额度已用完")
        print()
        print("建议:")
        print("   - 检查Key是否完整（复制时是否被截断）")
        print("   - 或者继续使用 kimi_search（已可用）")
