#!/usr/bin/env python3
"""
测试新API key
"""

import requests

# 新API key
api_key = "sk-cp-uktdLl3PT2mV6iUY6Tm3wViEzCqhNfL7W9g9sABXsU-zCD4DX_2RbQifFw59S0DaBLljX5D2_fhLuiL-LM0hImT8wdDfPSUl4TGFsP9siUJyvrF_wInAf7A"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "MiniMax-M2-7",
    "messages": [{"role": "user", "content": "你好，请用一句话介绍MiniMax M2.7"}],
    "temperature": 0.7,
    "max_tokens": 200
}

print("="*60)
print("测试新API key")
print("="*60)

# 测试v2端点
print("\n尝试chatcompletion_v2端点...")
try:
    resp = requests.post(
        "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
        headers=headers,
        json=payload,
        timeout=60
    )
    result = resp.json()
    print(f"状态码: {resp.status_code}")
    print(f"响应: {result}")
    
    if result.get('base_resp', {}).get('status_code') == 0:
        print(f"\n✅ 成功!")
        print(f"回复: {result.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
    else:
        print(f"\n❌ API错误: {result.get('base_resp', {}).get('status_msg')}")
except Exception as e:
    print(f"❌ 异常: {e}")
