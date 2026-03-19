#!/usr/bin/env python3
"""
MiniMax API - Anthropic协议支持

Coding Plan专属key (sk-cp-) 使用Anthropic兼容端点
Base URL: https://api.minimaxi.com/anthropic

Author: wdai
"""

import os
import json
import requests
from typing import Dict, List, Optional


class MiniMaxAnthropicClient:
    """MiniMax Anthropic协议客户端"""
    
    # Anthropic兼容端点 (Coding Plan专用)
    BASE_URL = "https://api.minimaxi.com/anthropic"
    
    # 支持的模型
    MODELS = {
        "MiniMax-M2.7": "MiniMax-M2.7",  # 最新编程助手 ⭐
        "MiniMax-M2.5": "MiniMax-M2.5",
        "MiniMax-M2.1": "MiniMax-M2.1",
        "MiniMax-M2": "MiniMax-M2",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise ValueError("需要MINIMAX_API_KEY (Coding Plan sk-cp- key)")
        
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        })
    
    def create_message(self,
                      messages: List[Dict],
                      model: str = "MiniMax-M2.7",
                      system: str = "",
                      max_tokens: int = 2000,
                      temperature: float = 0.7,
                      stream: bool = False) -> Dict:
        """
        创建消息 (Anthropic messages API格式)
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称 (MiniMax-M2.7)
            system: 系统提示
            max_tokens: 最大token数
            temperature: 温度
            stream: 是否流式输出
        """
        url = f"{self.BASE_URL}/v1/messages"
        
        # Anthropic格式转换
        anthropic_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # 转换角色: system->assistant, user->user, assistant->assistant
            if role == "system":
                # Anthropic把system放到顶层参数
                continue
            
            anthropic_messages.append({
                "role": role,
                "content": content
            })
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # 解析Anthropic格式响应
            content = ""
            if result.get("content"):
                for block in result["content"]:
                    if block.get("type") == "text":
                        content += block.get("text", "")
            
            usage = result.get("usage", {})
            
            return {
                "success": True,
                "content": content,
                "model": result.get("model"),
                "usage": {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                },
                "stop_reason": result.get("stop_reason"),
                "raw": result
            }
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json()
            except:
                error_detail = response.text[:200]
            
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {error_detail}",
                "raw": error_detail
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def chat_completion(self,
                       messages: List[Dict],
                       model: str = "MiniMax-M2.7",
                       **kwargs) -> Dict:
        """
        OpenAI兼容的chat_completion接口 (底层使用Anthropic协议)
        """
        # 提取system消息
        system = ""
        filtered_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                filtered_messages.append(msg)
        
        return self.create_message(
            messages=filtered_messages,
            model=model,
            system=system,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.7),
            stream=kwargs.get("stream", False)
        )


def test_coding_plan_key(api_key: str):
    """测试Coding Plan key"""
    print("="*60)
    print("🚀 MiniMax Coding Plan 测试 (Anthropic协议)")
    print("="*60)
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: {MiniMaxAnthropicClient.BASE_URL}")
    print()
    
    client = MiniMaxAnthropicClient(api_key)
    
    # 测试对话
    print("--- 测试 MiniMax-M2.7 ---")
    
    result = client.create_message(
        messages=[{"role": "user", "content": "你好，请用一句话介绍自己"}],
        model="MiniMax-M2.7",
        system="你是一个有帮助的编程助手"
    )
    
    if result["success"]:
        print(f"✅ 调用成功!")
        print(f"模型: {result.get('model')}")
        print(f"响应: {result['content']}")
        
        usage = result.get("usage", {})
        if usage:
            print(f"Token: {usage.get('total_tokens')} " +
                  f"(输入:{usage.get('input_tokens')}, " +
                  f"输出:{usage.get('output_tokens')})")
    else:
        print(f"❌ 调用失败: {result.get('error')}")
        if result.get('raw'):
            print(f"原始响应: {result['raw']}")
    
    print()
    print("="*60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("MINIMAX_API_KEY")
    
    if not api_key:
        print("请提供Coding Plan API Key:")
        print("python3 minimax_anthropic_client.py 'sk-cp-...'")
        sys.exit(1)
    
    test_coding_plan_key(api_key)
