#!/usr/bin/env python3
"""
调试MiniMax API - 尝试不同格式
MiniMax通常需要group_id
"""

import os
import json
import requests

api_key = "sk-api-EYDzL1SbY3PznTQ4OWUP1lDVoPUdzEJcwqSg6jJX-7r966h32wAraUQvU4Ixkp9YaJw4cFo6JWizKiErNC5yo1Dp6-IxHiL-9KMOKlcywWbCGIVaWf6kgOA"

# MiniMax通常需要group_id，从API key中提取或单独设置
# 尝试格式1: Authorization Bearer
print("="*60)
print("尝试格式1: Bearer Token")
print("="*60)

headers1 = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "MiniMax-M2-7",
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
    "max_tokens": 100
}

resp1 = requests.post(
    "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
    headers=headers1,
    json=payload,
    timeout=30
)
print(f"状态: {resp1.status_code}")
print(f"响应: {resp1.json()}")

# 尝试格式2: 使用x-api-key header
print("\n" + "="*60)
print("尝试格式2: x-api-key header")
print("="*60)

headers2 = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

resp2 = requests.post(
    "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
    headers=headers2,
    json=payload,
    timeout=30
)
print(f"状态: {resp2.status_code}")
print(f"响应: {resp2.json()}")

# 尝试格式3: 使用group_id (MiniMax通常需要)
print("\n" + "="*60)
print("尝试格式3: 使用group_id")
print("="*60)

# 从API key中提取group_id (如果有)
group_id = api_key.split('-')[2] if len(api_key.split('-')) > 2 else ""
print(f"尝试group_id: {group_id}")

headers3 = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload3 = {
    "model": "MiniMax-M2-7",
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
    "max_tokens": 100,
    "group_id": group_id  # MiniMax可能需要
}

resp3 = requests.post(
    "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
    headers=headers3,
    json=payload3,
    timeout=30
)
print(f"状态: {resp3.status_code}")
print(f"响应: {resp3.json()}")

# 尝试格式4: 使用旧版API端点
print("\n" + "="*60)
print("尝试格式4: 旧版API端点")
print("="*60)

resp4 = requests.post(
    "https://api.minimaxi.com/v1/text/chatcompletion",
    headers=headers1,
    json=payload,
    timeout=30
)
print(f"状态: {resp4.status_code}")
print(f"响应: {resp4.json() if resp4.status_code == 200 else resp4.text[:200]}")
