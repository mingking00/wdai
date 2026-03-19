#!/usr/bin/env python3
"""
调试MiniMax API - 测试模型名称
"""

import json
import requests

api_key = "sk-api-EYDzL1SbY3PznTQ4OWUP1lDVoPUdzEJcwqSg6jJX-7r966h32wAraUQvU4Ixkp9YaJw4cFo6JWizKiErNC5yo1Dp6-IxHiL-9KMOKlcywWbCGIVaWf6kgOA"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 测试不同模型名称
models = [
    "MiniMax-M2-7",
    "minimax-m2-7", 
    "M2-7",
    "m2-7",
    "MiniMax-M2.7",
    "abab6.5s-chat",  # MiniMax常见模型
    "abab6-chat",
]

print("="*60)
print("测试不同模型名称 (使用旧版端点)")
print("="*60)

for model in models:
    print(f"\n测试模型: {model}")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "你好"}],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    try:
        resp = requests.post(
            "https://api.minimaxi.com/v1/text/chatcompletion",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        result = resp.json()
        
        if result.get('base_resp', {}).get('status_code') == 0:
            print(f"  ✅ 成功! 回复: {result.get('reply', 'N/A')[:50]}...")
            print(f"  模型 {model} 可用!")
            break
        else:
            error = result.get('base_resp', {}).get('status_msg', 'Unknown')
            print(f"  ❌ {error}")
    except Exception as e:
        print(f"  ❌ 异常: {str(e)[:100]}")

print("\n" + "="*60)
print("尝试获取可用模型列表...")
print("="*60)

# 尝试使用chatv2端点测试
test_models = [
    "MiniMax-M2-7",
    "MiniMax-Text-01",
    "MiniMax-VL-01",
]

for model in test_models:
    print(f"\n测试chatv2端点: {model}")
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "你好"}],
    }
    
    try:
        resp = requests.post(
            "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        result = resp.json()
        print(f"  响应: {result}")
    except Exception as e:
        print(f"  异常: {str(e)[:100]}")
