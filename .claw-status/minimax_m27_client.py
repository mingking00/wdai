#!/usr/bin/env python3
"""
MiniMax M2.7 API Client
用于接入M2.7模型执行evo任务
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Any


class MiniMaxM27Client:
    """MiniMax M2.7 API客户端"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('MINIMAX_API_KEY')
        self.base_url = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"
        self.model = "MiniMax-M2-7"
        
        if not self.api_key:
            raise ValueError("API key required")
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             temperature: float = 0.7,
             max_tokens: int = 4000) -> Dict[str, Any]:
        """
        调用M2.7聊天接口
        
        Args:
            messages: [{"role": "user"/"assistant", "content": "..."}]
            temperature: 采样温度
            max_tokens: 最大输出token数
        
        Returns:
            模型响应
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # MiniMax API格式
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            # 先打印原始响应用于调试
            result = response.json()
            
            # MiniMax的错误处理
            if 'base_resp' in result and result['base_resp'].get('status_code') != 0:
                return {
                    'success': False,
                    'error': f"API Error: {result['base_resp'].get('status_msg', 'Unknown')}",
                    'raw': result
                }
            
            # 解析响应 - MiniMax格式
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0].get('message', {})
                return {
                    'success': True,
                    'content': message.get('content', ''),
                    'usage': result.get('usage', {}),
                    'model': self.model
                }
            elif 'reply' in result:
                # 可能的不同格式
                return {
                    'success': True,
                    'content': result['reply'],
                    'usage': result.get('usage', {}),
                    'model': self.model
                }
            else:
                return {
                    'success': False,
                    'error': 'Unexpected response format',
                    'raw': result
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def generate_code(self, 
                     prompt: str,
                     language: str = "python",
                     context: str = "") -> Dict[str, Any]:
        """
        代码生成专用接口
        """
        system_prompt = f"""你是一个专业的{language}开发者。
你的任务是编写高质量、安全、高效的代码。
请遵循最佳实践，添加适当的注释和错误处理。"""
        
        user_prompt = f"""{context}

请编写以下功能的代码：
{prompt}

要求：
1. 代码清晰易读
2. 添加必要注释
3. 包含错误处理
4. 符合安全规范

请直接输出代码，不需要解释。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.chat(messages, temperature=0.3, max_tokens=4000)
    
    def review_code(self, 
                   code: str,
                   check_security: bool = True,
                   check_performance: bool = True) -> Dict[str, Any]:
        """
        代码审查专用接口
        """
        checks = []
        if check_security:
            checks.append("安全漏洞（SQL注入、XSS、命令注入等）")
        if check_performance:
            checks.append("性能问题（时间复杂度、内存泄漏等）")
        
        system_prompt = "你是一个严格的代码审查专家，擅长发现安全漏洞和性能问题。"
        
        user_prompt = f"""请审查以下代码：

```python
{code}
```

请检查以下方面：
{chr(10).join(f"- {c}" for c in checks)}

输出格式：
1. 发现的问题列表（如有）
2. 严重性评级（高/中/低）
3. 修复建议
4. 总体评价

如果没有问题，请明确说明"代码审查通过"。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.chat(messages, temperature=0.2, max_tokens=3000)


# 测试
if __name__ == "__main__":
    import os
    
    api_key = os.getenv('MINIMAX_API_KEY')
    if not api_key:
        print("❌ 未设置 MINIMAX_API_KEY 环境变量")
        exit(1)
    
    print("="*60)
    print("MiniMax M2.7 API Client - 测试")
    print("="*60)
    
    client = MiniMaxM27Client(api_key)
    
    # 测试简单对话
    print("\n🧪 测试简单对话...")
    result = client.chat([
        {"role": "user", "content": "你好，请用一句话介绍自己"}
    ])
    
    if result['success']:
        print(f"   ✅ 成功")
        print(f"   回复: {result['content'][:100]}...")
        if 'usage' in result:
            print(f"   Token使用: {result['usage']}")
    else:
        print(f"   ❌ 失败: {result.get('error')}")
    
    print("\n" + "="*60)
    print("✅ 客户端测试完成")
    print("="*60)
