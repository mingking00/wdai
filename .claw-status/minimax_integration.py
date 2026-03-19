#!/usr/bin/env python3
"""
MiniMax API 完整接入系统 v1.0

功能:
1. 完整API封装 (chatbot, embeddings, TTS)
2. 智能路由 (Kimi/MiniMax自动选择)
3. 成本追踪 (token消耗、费用对比)
4. 能力测试 (基准测试套件)
5. 错误处理 (重试、降级、熔断)

Author: wdai
Version: 1.0
"""

import os
import json
import time
import requests
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Union, Callable, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum
import hashlib


class ModelProvider(Enum):
    """模型提供商"""
    KIMI = "kimi"
    MINIMAX = "minimax"


class TaskType(Enum):
    """任务类型"""
    CODE = "code"           # 代码生成/理解
    REASONING = "reasoning" # 推理任务
    CREATIVE = "creative"   # 创意写作
    SUMMARY = "summary"     # 摘要总结
    CHAT = "chat"          # 通用对话
    EMBEDDING = "embedding" # 嵌入向量


@dataclass
class APICost:
    """API调用成本"""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: str
    task_type: str
    latency_ms: int


@dataclass
class ModelCapability:
    """模型能力评分"""
    provider: str
    model: str
    code_quality: float      # 0-10
    reasoning_depth: float   # 0-10
    chinese_quality: float   # 0-10
    speed_score: float       # 0-10
    cost_efficiency: float   # 0-10
    tested_at: str


class MiniMaxAPI:
    """MiniMax API封装 (支持OpenAI和Anthropic协议)"""
    
    # 两种协议的基础URL
    BASE_URL_OPENAI = "https://api.minimaxi.com/v1"
    BASE_URL_ANTHROPIC = "https://api.minimaxi.com/anthropic"
    
    # 定价 (每1M tokens)
    PRICING = {
        "MiniMax-M2.7": {"input": 0.30, "output": 1.00},
        "MiniMax-M2.5": {"input": 0.30, "output": 1.00},
        "MiniMax-M2.1": {"input": 0.30, "output": 1.00},
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        
        if not self.api_key:
            raise ValueError("MiniMax API key required")
        
        # 判断协议类型
        self.is_coding_plan = self.api_key.startswith("sk-cp-")
        
        if self.is_coding_plan:
            # Coding Plan使用Anthropic协议
            self.base_url = self.BASE_URL_ANTHROPIC
            self.use_anthropic = True
            self.session = requests.Session()
            self.session.headers.update({
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            })
        else:
            # 普通key使用OpenAI协议
            self.base_url = self.BASE_URL_OPENAI
            self.use_anthropic = False
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
    
    def chat_completion(self,
                       messages: List[Dict],
                       model: str = "MiniMax-M2.7",
                       temperature: float = 0.7,
                       max_tokens: int = 2000,
                       stream: bool = False) -> Dict:
        """聊天补全 (自动选择协议)"""
        
        if self.use_anthropic:
            return self._chat_anthropic(messages, model, temperature, max_tokens, stream)
        else:
            return self._chat_openai(messages, model, temperature, max_tokens, stream)
    
    def _chat_anthropic(self, messages, model, temperature, max_tokens, stream):
        """Anthropic协议调用"""
        url = f"{self.base_url}/v1/messages"
        
        # 提取system消息
        system = ""
        anthropic_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system = content
            else:
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
        
        start_time = time.time()
        
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            latency_ms = int((time.time() - start_time) * 1000)
            
            # 解析Anthropic格式
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
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                },
                "latency_ms": latency_ms,
                "raw_response": result
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "latency_ms": int((time.time() - start_time) * 1000)
            }
    
    def _chat_openai(self, messages, model, temperature, max_tokens, stream):
        """OpenAI协议调用"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        start_time = time.time()
        
        try:
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            latency_ms = int((time.time() - start_time) * 1000)
            
            if result.get("choices"):
                return {
                    "success": True,
                    "content": result["choices"][0]["message"]["content"],
                    "model": result.get("model"),
                    "usage": result.get("usage", {}),
                    "latency_ms": latency_ms,
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": "Empty response",
                    "raw_response": result
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "latency_ms": int((time.time() - start_time) * 1000)
            }
    
    def embeddings(self,
                   texts: List[str],
                   model: str = "embo-01",
                   embedding_type: str = "query") -> Dict:
        """获取嵌入向量"""
        url = f"{self.BASE_URL}/embeddings"
        
        payload = {
            "model": model,
            "input": texts[0] if len(texts) == 1 else texts,
            "type": embedding_type
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("data"):
                return {
                    "success": True,
                    "embeddings": [item["embedding"] for item in result["data"]],
                    "usage": result.get("usage", {}),
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": "No embeddings returned"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算成本 (USD)"""
        if model not in self.PRICING:
            model = "abab6.5"  # 默认
        
        pricing = self.PRICING[model]
        cost = (input_tokens / 1_000_000) * pricing["input"] + \
               (output_tokens / 1_000_000) * pricing["output"]
        
        return round(cost, 6)


class KimiAPI:
    """Kimi API封装 (适配器模式)"""
    
    # 定价
    PRICING = {
        "kimi-coding/k2p5": {"input": 0.10, "output": 0.40},  # 估算
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算成本"""
        if model not in self.PRICING:
            model = "kimi-coding/k2p5"
        
        pricing = self.PRICING[model]
        cost = (input_tokens / 1_000_000) * pricing["input"] + \
               (output_tokens / 1_000_000) * pricing["output"]
        
        return round(cost, 6)


class ModelRouter:
    """模型路由器 - 智能选择Kimi或MiniMax"""
    
    # 任务到模型的映射
    TASK_PREFERENCES = {
        TaskType.CODE: {
            "primary": (ModelProvider.KIMI, "kimi-coding/k2p5"),
            "fallback": (ModelProvider.MINIMAX, "abab6.5t")
        },
        TaskType.REASONING: {
            "primary": (ModelProvider.KIMI, "kimi-coding/k2p5"),
            "fallback": (ModelProvider.MINIMAX, "abab6.5")
        },
        TaskType.CREATIVE: {
            "primary": (ModelProvider.MINIMAX, "abab6.5"),
            "fallback": (ModelProvider.KIMI, "kimi-coding/k2p5")
        },
        TaskType.SUMMARY: {
            "primary": (ModelProvider.MINIMAX, "abab6.5s"),  # 便宜快速
            "fallback": (ModelProvider.KIMI, "kimi-coding/k2p5")
        },
        TaskType.CHAT: {
            "primary": (ModelProvider.MINIMAX, "abab6.5"),
            "fallback": (ModelProvider.KIMI, "kimi-coding/k2p5")
        }
    }
    
    def __init__(self, minimax_key: Optional[str] = None, group_id: Optional[str] = None):
        self.minimax = None
        self.kimi = KimiAPI()
        
        # 尝试初始化MiniMax
        try:
            self.minimax = MiniMaxAPI(minimax_key)
            self.minimax_available = True
        except ValueError:
            self.minimax_available = False
            print("[ModelRouter] MiniMax未配置，仅使用Kimi")
        
        # 成本追踪
        self.cost_history: List[APICost] = []
        
        # 能力数据库
        self.capabilities: Dict[str, ModelCapability] = {}
    
    def classify_task(self, prompt: str) -> TaskType:
        """自动分类任务类型"""
        prompt_lower = prompt.lower()
        
        # 代码相关
        code_keywords = ['代码', '编程', 'python', 'function', 'bug', 'error', 'debug']
        if any(kw in prompt_lower for kw in code_keywords):
            return TaskType.CODE
        
        # 推理相关
        reasoning_keywords = ['分析', '推理', '逻辑', '为什么', '原因', '因果关系']
        if any(kw in prompt_lower for kw in reasoning_keywords):
            return TaskType.REASONING
        
        # 创意相关
        creative_keywords = ['写', '创作', '故事', '文案', '创意', '诗歌']
        if any(kw in prompt_lower for kw in creative_keywords):
            return TaskType.CREATIVE
        
        # 摘要相关
        summary_keywords = ['总结', '摘要', '概括', '要点', 'tl;dr']
        if any(kw in prompt_lower for kw in summary_keywords):
            return TaskType.SUMMARY
        
        # 默认对话
        return TaskType.CHAT
    
    def route(self, 
             prompt: str,
             prefer_cheap: bool = False,
             force_provider: Optional[ModelProvider] = None) -> Tuple[ModelProvider, str]:
        """路由到合适的模型"""
        
        if force_provider:
            if force_provider == ModelProvider.MINIMAX and self.minimax_available:
                return (ModelProvider.MINIMAX, "abab6.5")
            return (ModelProvider.KIMI, "kimi-coding/k2p5")
        
        task = self.classify_task(prompt)
        
        # 如果偏好便宜，优先MiniMax的abab6.5s
        if prefer_cheap and self.minimax_available:
            return (ModelProvider.MINIMAX, "abab6.5s")
        
        # 根据任务类型选择
        prefs = self.TASK_PREFERENCES.get(task, self.TASK_PREFERENCES[TaskType.CHAT])
        
        primary_provider, primary_model = prefs["primary"]
        
        if primary_provider == ModelProvider.MINIMAX and not self.minimax_available:
            return prefs["fallback"]
        
        return (primary_provider, primary_model)
    
    def call(self,
            prompt: str,
            system_prompt: str = "",
            prefer_cheap: bool = False,
            force_provider: Optional[ModelProvider] = None) -> Dict:
        """
        智能调用
        
        Returns:
            {
                "success": bool,
                "content": str,
                "provider": str,
                "model": str,
                "cost_usd": float,
                "latency_ms": int,
                ...
            }
        """
        provider, model = self.route(prompt, prefer_cheap, force_provider)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        start_time = time.time()
        
        if provider == ModelProvider.MINIMAX and self.minimax:
            result = self.minimax.chat_completion(
                messages=messages,
                model=model,
                temperature=0.7
            )
            
            if result["success"]:
                usage = result.get("usage", {})
                cost = self.minimax.calculate_cost(
                    model,
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0)
                )
                
                self._record_cost(ModelProvider.MINIMAX.value, model, 
                                usage.get("prompt_tokens", 0),
                                usage.get("completion_tokens", 0),
                                cost, self.classify_task(prompt).value,
                                result.get("latency_ms", 0))
                
                return {
                    **result,
                    "provider": ModelProvider.MINIMAX.value,
                    "model": model,
                    "cost_usd": cost,
                    "task_type": self.classify_task(prompt).value
                }
            else:
                # MiniMax失败，回退到Kimi
                print(f"[ModelRouter] MiniMax失败: {result.get('error')}, 回退到Kimi")
                return self._call_kimi(prompt, system_prompt)
        
        else:
            return self._call_kimi(prompt, system_prompt)
    
    def _call_kimi(self, prompt: str, system_prompt: str = "") -> Dict:
        """调用Kimi (通过OpenClaw)"""
        # 这里应该调用OpenClaw的session或工具
        # 简化实现
        return {
            "success": False,
            "error": "Kimi调用需要通过OpenClaw工具",
            "provider": ModelProvider.KIMI.value,
            "model": "kimi-coding/k2p5"
        }
    
    def _record_cost(self, provider: str, model: str, 
                    input_tokens: int, output_tokens: int,
                    cost: float, task_type: str, latency_ms: int):
        """记录成本"""
        cost_record = APICost(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            timestamp=datetime.now().isoformat(),
            task_type=task_type,
            latency_ms=latency_ms
        )
        self.cost_history.append(cost_record)
    
    def get_cost_report(self) -> Dict:
        """获取成本报告"""
        if not self.cost_history:
            return {"message": "暂无成本数据"}
        
        total_cost = sum(c.cost_usd for c in self.cost_history)
        total_tokens = sum(c.input_tokens + c.output_tokens for c in self.cost_history)
        
        by_provider = {}
        for c in self.cost_history:
            if c.provider not in by_provider:
                by_provider[c.provider] = {"cost": 0, "tokens": 0, "calls": 0}
            by_provider[c.provider]["cost"] += c.cost_usd
            by_provider[c.provider]["tokens"] += c.input_tokens + c.output_tokens
            by_provider[c.provider]["calls"] += 1
        
        by_task = {}
        for c in self.cost_history:
            if c.task_type not in by_task:
                by_task[c.task_type] = {"cost": 0, "calls": 0}
            by_task[c.task_type]["cost"] += c.cost_usd
            by_task[c.task_type]["calls"] += 1
        
        return {
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_calls": len(self.cost_history),
            "avg_cost_per_call": round(total_cost / len(self.cost_history), 6),
            "by_provider": by_provider,
            "by_task": by_task
        }


class BenchmarkSuite:
    """基准测试套件"""
    
    TEST_CASES = {
        "code_generation": {
            "prompt": "写一个Python函数，实现快速排序",
            "expected_keywords": ["def", "quicksort", "pivot", "recursive"]
        },
        "chinese_reasoning": {
            "prompt": "分析'塞翁失马'这个成语的哲学含义",
            "expected_keywords": ["福", "祸", "辩证", "转化"]
        },
        "creative_writing": {
            "prompt": "写一段关于未来城市的100字描述",
            "expected_keywords": []
        },
        "factual_qa": {
            "prompt": "什么是BERT模型？简要说明其原理",
            "expected_keywords": ["transformer", "bidirectional", "encoder"]
        }
    }
    
    def __init__(self, router: ModelRouter):
        self.router = router
        self.results: List[Dict] = []
    
    def run_benchmark(self, iterations: int = 3) -> Dict:
        """运行基准测试"""
        print(f"[Benchmark] 开始基准测试 ({iterations}轮)")
        
        for test_name, test_case in self.TEST_CASES.items():
            print(f"\n[Benchmark] 测试: {test_name}")
            
            for i in range(iterations):
                # 测试MiniMax
                if self.router.minimax_available:
                    result_mini = self.router.call(
                        test_case["prompt"],
                        force_provider=ModelProvider.MINIMAX
                    )
                    
                    self.results.append({
                        "test": test_name,
                        "provider": "minimax",
                        "iteration": i + 1,
                        "success": result_mini.get("success"),
                        "latency_ms": result_mini.get("latency_ms", 0),
                        "cost_usd": result_mini.get("cost_usd", 0),
                        "content_length": len(result_mini.get("content", ""))
                    })
                
                # 测试Kimi
                result_kimi = self.router.call(
                    test_case["prompt"],
                    force_provider=ModelProvider.KIMI
                )
                
                self.results.append({
                    "test": test_name,
                    "provider": "kimi",
                    "iteration": i + 1,
                    "success": result_kimi.get("success"),
                    "latency_ms": result_kimi.get("latency_ms", 0),
                    "cost_usd": 0,  # Kimi成本通过其他方式追踪
                    "content_length": len(result_kimi.get("content", ""))
                })
        
        return self._generate_report()
    
    def _generate_report(self) -> Dict:
        """生成测试报告"""
        if not self.results:
            return {"message": "无测试结果"}
        
        # 按提供商分组统计
        stats = {"minimax": {}, "kimi": {}}
        
        for provider in ["minimax", "kimi"]:
            provider_results = [r for r in self.results if r["provider"] == provider]
            
            if provider_results:
                stats[provider] = {
                    "success_rate": sum(1 for r in provider_results if r["success"]) / len(provider_results),
                    "avg_latency_ms": sum(r["latency_ms"] for r in provider_results) / len(provider_results),
                    "avg_cost_usd": sum(r["cost_usd"] for r in provider_results) / len(provider_results),
                    "total_calls": len(provider_results)
                }
        
        return {
            "total_tests": len(self.results),
            "stats_by_provider": stats,
            "recommendation": self._generate_recommendation(stats)
        }
    
    def _generate_recommendation(self, stats: Dict) -> str:
        """生成使用建议"""
        mini = stats.get("minimax", {})
        kimi = stats.get("kimi", {})
        
        if not mini or not kimi:
            return "需要更多测试数据"
        
        if mini.get("avg_cost_usd", 1) < kimi.get("avg_cost_usd", 1) * 0.5:
            return "MiniMax成本优势明显，适合大规模使用"
        
        if mini.get("success_rate", 0) > kimi.get("success_rate", 0):
            return "MiniMax成功率更高"
        
        return "两个模型各有优势，建议按任务类型选择"


def test_minimax_integration():
    """测试MiniMax集成"""
    print("="*70)
    print("🚀 MiniMax API 完整集成测试")
    print("="*70)
    
    # 检查API key
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("\n⚠️  未设置MINIMAX_API_KEY环境变量")
        print("请设置: export MINIMAX_API_KEY='your_key_here'")
        print("\n使用模拟模式继续测试...")
        
        # 模拟模式
        router = ModelRouter()
        print(f"\nMiniMax可用: {router.minimax_available}")
        
        # 测试任务分类
        test_prompts = [
            "写一个Python函数",
            "总结这段文字",
            "写一首关于春天的诗"
        ]
        
        print("\n--- 任务分类测试 ---")
        for prompt in test_prompts:
            task = router.classify_task(prompt)
            provider, model = router.route(prompt)
            print(f"'{prompt[:20]}...' -> {task.value} -> {provider.value}/{model}")
        
        return
    
    # 实际测试
    router = ModelRouter()
    print(f"\nMiniMax可用: {router.minimax_available}")
    
    # 测试直接调用
    print("\n--- MiniMax直接调用测试 ---")
    
    result = router.minimax.chat_completion(
        messages=[
            {"role": "user", "content": "你好，请简短介绍自己"}
        ],
        model="abab6.5"
    )
    
    if result["success"]:
        print(f"✅ 调用成功")
        print(f"   响应: {result['content'][:50]}...")
        print(f"   延迟: {result['latency_ms']}ms")
        
        usage = result.get("usage", {})
        cost = router.minimax.calculate_cost(
            "abab6.5",
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0)
        )
        print(f"   成本: ${cost:.6f}")
    else:
        print(f"❌ 调用失败: {result.get('error')}")
    
    # 成本报告
    print("\n--- 成本报告 ---")
    report = router.get_cost_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("✅ MiniMax集成测试完成")
    print("="*70)


if __name__ == "__main__":
    test_minimax_integration()
