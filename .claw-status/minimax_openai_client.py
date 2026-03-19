#!/usr/bin/env python3
"""
MiniMax API 直接调用 (OpenAI兼容格式)

通过OpenAI兼容端点调用MiniMax
无需OpenCode客户端

Author: wdai
"""

import os
import json
import requests
from typing import Dict, List, Optional


class MiniMaxOpenAIClient:
    """MiniMax OpenAI兼容客户端"""
    
    # MiniMax OpenAI兼容端点 (国内版)
    BASE_URL_OPENAI = "https://api.minimaxi.com/v1"
    BASE_URL_ANTHROPIC = "https://api.minimaxi.com/anthropic"
    
    # 支持的模型 (M2.7是最新编程助手模型)
    MODELS = {
        "MiniMax-M2.7": "MiniMax-M2.7",  # 最新编程助手 ⭐
        "MiniMax-M2.5": "MiniMax-M2.5",
        "MiniMax-M2.1": "MiniMax-M2.1",
        "abab6.5": "abab6.5",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise ValueError("需要MINIMAX_API_KEY")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def chat_completion(self,
                       messages: List[Dict],
                       model: str = "MiniMax-M2.7",  # 默认使用M2.7
                       temperature: float = 0.7,
                       max_tokens: int = 2000,
                       stream: bool = False) -> Dict:
        """
        聊天补全 (OpenAI兼容格式)
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度
            max_tokens: 最大token数
            stream: 是否流式输出
        """
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("choices"):
                return {
                    "success": True,
                    "content": result["choices"][0]["message"]["content"],
                    "model": result.get("model"),
                    "usage": result.get("usage", {}),
                    "raw": result
                }
            else:
                return {
                    "success": False,
                    "error": "No choices in response",
                    "raw": result
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_models(self) -> List[str]:
        """获取可用模型列表"""
        url = f"{self.BASE_URL}/models"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            models = [m.get("id") for m in result.get("data", [])]
            return models
            
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return list(self.MODELS.keys())


def test_with_api_key(api_key: str):
    """测试API Key"""
    print("="*60)
    print("🚀 MiniMax API 测试 (OpenAI兼容格式)")
    print("="*60)
    print(f"API Key: {api_key[:15]}...")
    print()
    
    client = MiniMaxOpenAIClient(api_key)
    
    # 获取模型列表
    print("--- 可用模型 ---")
    models = client.list_models()
    for model in models[:5]:
        print(f"  • {model}")
    print()
    
    # 测试对话
    print("--- 对话测试 ---")
    test_messages = [
        {"role": "user", "content": "你好，请用一句话介绍自己"}
    ]
    
    result = client.chat_completion(
        messages=test_messages,
        model="MiniMax-M2.7"  # 使用M2.7模型
    )
    
    if result["success"]:
        print(f"✅ 调用成功!")
        print(f"模型: {result.get('model')}")
        print(f"响应: {result['content']}")
        
        usage = result.get("usage", {})
        if usage:
            print(f"Token: {usage.get('total_tokens')} " +
                  f"(输入:{usage.get('prompt_tokens')}, " +
                  f"输出:{usage.get('completion_tokens')})")
    else:
        print(f"❌ 调用失败: {result.get('error')}")
    
    print()
    print("="*60)


if __name__ == "__main__":
    # 测试 - 使用普通API Key
    import sys
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("MINIMAX_API_KEY")
    
    if not api_key:
        print("请提供API Key: python3 minimax_openai_client.py 'sk-api-...'")
        print("或设置环境变量: export MINIMAX_API_KEY='sk-api-...'")
        sys.exit(1)
    
    test_with_api_key(api_key)
