"""
Kimi API LLM 接口实现

支持 Moonshot AI API (Kimi)
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional, Iterator
import logging

logger = logging.getLogger(__name__)


class KimiLLM:
    """
    Kimi API LLM 接口
    
    支持模型:
    - kimi-k2.5 (默认)
    - kimi-k1.5
    - kimi-latest
    """
    
    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_MODEL = "kimi-k2.5"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 512,
        timeout: int = 60
    ):
        """
        初始化 Kimi LLM
        
        Args:
            api_key: API Key，默认从环境变量 KIMI_API_KEY 读取
            base_url: API 基础 URL
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            timeout: 请求超时秒数
        """
        self.api_key = api_key or os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("请提供 api_key 或设置 KIMI_API_KEY 环境变量")
        
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        logger.info(f"KimiLLM 初始化完成 (model={self.model})")
    
    def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        生成文本 (Tool-DC 接口)
        
        Args:
            prompt: 用户提示
            system: 系统提示
            **kwargs: 额外参数
            
        Returns:
            str: 生成的文本
        """
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat_completion(
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens)
        )
        
        return response["choices"][0]["message"]["content"]
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        聊天补全 API
        
        Args:
            messages: 消息列表
            temperature: 温度
            max_tokens: 最大 token 数
            stream: 是否流式返回
            
        Returns:
            API 响应
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": stream
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_stream(response)
            else:
                return response.json()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Kimi API 请求失败: {e}")
            raise
    
    def _handle_stream(self, response) -> Iterator[str]:
        """处理流式响应"""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk['choices'][0]['delta']
                        if 'content' in delta:
                            yield delta['content']
                    except (json.JSONDecodeError, KeyError):
                        continue
    
    def list_models(self) -> List[Dict[str, Any]]:
        """列出可用模型"""
        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json().get("data", [])
    
    def count_tokens(self, text: str) -> int:
        """
        估算 token 数 (粗略估算)
        
        实际应使用 API 的 token counting endpoint
        """
        # 中文约 1 token/字，英文约 1 token/4 chars
        import re
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        return chinese_chars + other_chars // 4 + 1


class KimiLLMWithFallback:
    """
    带降级策略的 Kimi LLM
    
    当 Kimi API 失败时，可以尝试其他模型
    """
    
    def __init__(
        self,
        primary: KimiLLM,
        fallback: Optional[Any] = None
    ):
        self.primary = primary
        self.fallback = fallback
    
    def generate(self, prompt: str, **kwargs) -> str:
        """生成，带降级"""
        try:
            return self.primary.generate(prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Primary LLM 失败: {e}")
            if self.fallback:
                logger.info("使用 Fallback LLM")
                return self.fallback.generate(prompt, **kwargs)
            raise


# 便捷创建函数
def create_kimi_llm(
    api_key: Optional[str] = None,
    model: str = "kimi-k2.5",
    **kwargs
) -> KimiLLM:
    """
    创建 Kimi LLM 实例
    
    Args:
        api_key: API Key，默认从环境变量读取
        model: 模型名称
        **kwargs: 其他参数
        
    Returns:
        KimiLLM: LLM 实例
    """
    return KimiLLM(
        api_key=api_key,
        model=model,
        **kwargs
    )
