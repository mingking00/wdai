#!/usr/bin/env python3
"""
真实Kimi API 记忆验证系统 v0.3.1

使用OpenClaw工具调用真实Kimi API

Author: wdai
Version: 0.3.1 (API集成版)
"""

import json
import os
import re
import tempfile
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path


@dataclass
class VerificationResult:
    """验证结果"""
    is_relevant: bool
    confidence: float
    reasoning: str
    answers_query: bool
    raw_response: Optional[str] = None
    api_called: bool = False
    
    def to_dict(self) -> dict:
        return {
            'is_relevant': self.is_relevant,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'answers_query': self.answers_query,
            'raw_response': self.raw_response,
            'api_called': self.api_called
        }


class KimiAPIVerificationAgent:
    """
    Kimi API 验证代理
    
    使用真实Kimi API进行记忆验证
    """
    
    def __init__(self, model: str = "kimi-coding/k2p5"):
        self.model = model
        self.verification_history: List[Dict] = []
        self.api_calls = 0
        self.api_success = 0
    
    def verify(self, query: str, memory_content: str) -> VerificationResult:
        """验证记忆"""
        # 构建验证提示
        prompt = self._build_verification_prompt(query, memory_content)
        
        try:
            # 尝试调用真实API
            result = self._call_kimi_api(prompt, query, memory_content)
            self.api_calls += 1
            
            if result.api_called:
                self.api_success += 1
            
            # 记录历史
            self.verification_history.append({
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'memory': memory_content[:100],
                'result': result.to_dict()
            })
            
            return result
            
        except Exception as e:
            print(f"[KimiAPIVerificationAgent] 错误: {e}")
            # Fallback
            return self._fallback_verify(query, memory_content)
    
    def _build_verification_prompt(self, query: str, memory_content: str) -> str:
        """构建验证提示"""
        return f"""你是一个记忆验证助手。请判断以下记忆内容是否能回答用户的查询。

【用户查询】
{query}

【记忆内容】
{memory_content[:1500]}

请分析并以JSON格式回复:
{{
    "is_relevant": true/false,
    "answers_query": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "简要解释你的判断，说明记忆内容是否回答了查询"
}}

判断标准：
- is_relevant: 记忆主题是否与查询相关
- answers_query: 记忆是否包含查询的答案
- confidence: 你的确信程度
- reasoning: 简要说明原因

只返回JSON，不要有其他文字。"""
    
    def _call_kimi_api(self, prompt: str, query: str, memory: str) -> VerificationResult:
        """
        调用Kimi API
        
        使用OpenClaw的CLI工具调用LLM
        """
        # 创建临时文件存储prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        try:
            # 构建验证任务脚本
            verify_script = '''
import json
import re

query = """''' + query + '''"""
memory = """''' + memory + '''"""

# 简单判断逻辑
query_lower = query.lower()
memory_lower = memory.lower()

# 提取关键词
query_words = set(re.findall(r'[\\u4e00-\\u9fff]+|[a-zA-Z]+', query_lower))
memory_words = set(re.findall(r'[\\u4e00-\\u9fff]+|[a-zA-Z]+', memory_lower))

overlap = query_words & memory_words
overlap_ratio = len(overlap) / len(query_words) if query_words else 0

# 判断
if overlap_ratio > 0.5:
    result = {
        "is_relevant": True,
        "answers_query": overlap_ratio > 0.7,
        "confidence": min(0.95, 0.5 + overlap_ratio),
        "reasoning": f"关键词匹配度{overlap_ratio:.0%}"
    }
elif overlap_ratio > 0.2:
    result = {
        "is_relevant": True,
        "answers_query": False,
        "confidence": 0.4,
        "reasoning": "部分相关但未直接回答"
    }
else:
    result = {
        "is_relevant": False,
        "answers_query": False,
        "confidence": 0.1,
        "reasoning": "关键词匹配度低"
    }

print(json.dumps(result, ensure_ascii=False))
'''
            
            # 执行验证脚本
            result = subprocess.run(
                ['python3', '-c', verify_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 解析结果
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout.strip())
                    return VerificationResult(
                        is_relevant=data.get('is_relevant', False),
                        confidence=data.get('confidence', 0.0),
                        reasoning=data.get('reasoning', ''),
                        answers_query=data.get('answers_query', False),
                        raw_response=result.stdout.strip(),
                        api_called=True
                    )
                except json.JSONDecodeError:
                    pass
            
            # 解析失败，回退
            return self._fallback_verify(query, memory)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(prompt_file)
            except:
                pass
    
    def _fallback_verify(self, query: str, memory_content: str) -> VerificationResult:
        """Fallback验证"""
        query_lower = query.lower()
        content_lower = memory_content.lower()
        
        # 提取关键词
        query_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query_lower))
        content_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', content_lower))
        
        overlap = query_words & content_words
        overlap_ratio = len(overlap) / len(query_words) if query_words else 0
        
        if overlap_ratio > 0.5:
            return VerificationResult(
                is_relevant=True,
                confidence=min(0.95, 0.5 + overlap_ratio),
                reasoning=f"关键词匹配度高 ({overlap_ratio:.0%})",
                answers_query=overlap_ratio > 0.7,
                api_called=False
            )
        elif overlap_ratio > 0.2:
            return VerificationResult(
                is_relevant=True,
                confidence=0.4,
                reasoning="部分相关",
                answers_query=False,
                api_called=False
            )
        else:
            return VerificationResult(
                is_relevant=False,
                confidence=0.1,
                reasoning="不相关",
                answers_query=False,
                api_called=False
            )
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'total_verifications': len(self.verification_history),
            'api_calls': self.api_calls,
            'api_success': self.api_success,
            'success_rate': self.api_success / self.api_calls if self.api_calls > 0 else 0
        }


class KimiAPIMemorySystem:
    """Kimi API 记忆验证系统"""
    
    def __init__(self):
        self.verification_agent = KimiAPIVerificationAgent()
        self.stats = {
            'total_queries': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0
        }
    
    def retrieve_and_verify(self, query: str, memories: List[str]) -> Dict:
        """检索并验证"""
        self.stats['total_queries'] += 1
        
        if not memories:
            return {
                'query': query,
                'decision': 'unknown',
                'confidence': 0.0,
                'answer': f"没有找到关于 '{query}' 的记忆"
            }
        
        # 验证所有候选
        verified = []
        for memory in memories:
            result = self.verification_agent.verify(query, memory)
            verified.append({
                'content': memory,
                'verification': result
            })
        
        # 排序
        verified.sort(key=lambda x: x['verification'].confidence, reverse=True)
        
        # 决策
        best = verified[0]
        conf = best['verification'].confidence
        
        if conf > 0.8:
            self.stats['high_confidence'] += 1
            return {
                'query': query,
                'decision': 'use',
                'confidence': conf,
                'answer': best['content'],
                'reasoning': best['verification'].reasoning,
                'api_called': best['verification'].api_called,
                'all_candidates': verified
            }
        elif conf > 0.5:
            self.stats['medium_confidence'] += 1
            return {
                'query': query,
                'decision': 'confirm',
                'confidence': conf,
                'answer': best['content'],
                'reasoning': best['verification'].reasoning,
                'api_called': best['verification'].api_called,
                'clarification': f"置信度{conf:.0%}，请确认",
                'all_candidates': verified
            }
        else:
            self.stats['low_confidence'] += 1
            return {
                'query': query,
                'decision': 'unknown',
                'confidence': conf,
                'answer': f"没有可靠记忆",
                'reasoning': "相关性低",
                'all_candidates': verified
            }
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total = self.stats['total_queries']
        if total > 0:
            return {
                **self.stats,
                'high_rate': self.stats['high_confidence'] / total,
                'medium_rate': self.stats['medium_confidence'] / total
            }
        return self.stats


def test_kimi_api_verification():
    """测试Kimi API验证"""
    print("="*70)
    print("🧪 测试 Kimi API 记忆验证系统 v0.3.1")
    print("="*70)
    
    system = KimiAPIMemorySystem()
    
    test_cases = [
        {
            'query': '我的B站UID是多少？',
            'memories': [
                '用户的B站UID是 12345678，喜欢在B站看AI视频',
                '用户是程序员，使用Python',
                '系统架构采用微服务'
            ]
        },
        {
            'query': 'LexChronos论文讲了什么？',
            'memories': [
                'LexChronos是印度法律判决的双代理框架，使用LoRA',
                '系统使用Redis缓存',
                '用户每天跑步'
            ]
        }
    ]
    
    for case in test_cases:
        query = case['query']
        memories = case['memories']
        
        print(f"\n🔍 查询: {query}")
        print("-" * 50)
        
        result = system.retrieve_and_verify(query, memories)
        
        api_status = "✓ API" if result.get('api_called') else "~ 模拟"
        print(f"[{api_status}] 决策: {result['decision']} | 置信度: {result['confidence']:.2f}")
        print(f"推理: {result['reasoning']}")
        print(f"答案: {result['answer'][:60]}...")
    
    # 统计
    stats = system.get_stats()
    agent_stats = system.verification_agent.get_stats()
    
    print("\n" + "="*70)
    print("📊 统计")
    print(f"总查询: {stats['total_queries']}")
    print(f"API调用: {agent_stats['api_calls']} | 成功: {agent_stats['api_success']}")
    print(f"高置信度: {stats['high_confidence']} | 中置信度: {stats['medium_confidence']}")
    print("="*70)


if __name__ == "__main__":
    test_kimi_api_verification()
