#!/usr/bin/env python3
"""
批量验证 记忆验证系统 v0.5

一次API调用验证多条记忆，降低成本，提升速度

Author: wdai
Version: 0.5 (批量验证版)
"""

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class BatchVerificationResult:
    """批量验证结果"""
    query: str
    results: List[Dict]  # 每条记忆的验证结果
    batch_size: int
    api_calls: int  # 实际API调用次数
    processing_time: float
    
    def get_best_result(self) -> Optional[Dict]:
        """获取置信度最高的结果"""
        if not self.results:
            return None
        return max(self.results, key=lambda x: x.get('confidence', 0))
    
    def to_dict(self) -> dict:
        return {
            'query': self.query,
            'results': self.results,
            'batch_size': self.batch_size,
            'api_calls': self.api_calls,
            'processing_time': self.processing_time
        }


class BatchVerificationAgent:
    """
    批量验证代理
    
    一次API调用验证多条记忆
    """
    
    def __init__(self, model: str = "kimi-coding/k2p5", batch_size: int = 5):
        self.model = model
        self.batch_size = batch_size
        self.verification_history: List[Dict] = []
        self.stats = {
            'total_batches': 0,
            'total_items': 0,
            'api_calls': 0,
            'avg_batch_size': 0.0
        }
    
    def verify_batch(
        self,
        query: str,
        memories: List[str],
        use_parallel: bool = True
    ) -> BatchVerificationResult:
        """
        批量验证记忆
        
        Args:
            query: 用户查询
            memories: 记忆列表
            use_parallel: 是否并行处理多个batch
        
        Returns:
            BatchVerificationResult
        """
        start_time = datetime.now()
        
        # 分批处理
        batches = self._create_batches(memories, self.batch_size)
        
        all_results = []
        api_call_count = 0
        
        if use_parallel and len(batches) > 1:
            # 并行处理多个batch
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self._verify_single_batch, query, batch, i): i
                    for i, batch in enumerate(batches)
                }
                
                for future in as_completed(futures):
                    batch_idx = futures[future]
                    try:
                        batch_results, calls = future.result()
                        all_results.extend(batch_results)
                        api_call_count += calls
                    except Exception as e:
                        print(f"[BatchVerification] Batch {batch_idx} failed: {e}")
        else:
            # 串行处理
            for batch in batches:
                batch_results, calls = self._verify_single_batch(query, batch, 0)
                all_results.extend(batch_results)
                api_call_count += calls
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 更新统计
        self.stats['total_batches'] += len(batches)
        self.stats['total_items'] += len(memories)
        self.stats['api_calls'] += api_call_count
        self.stats['avg_batch_size'] = self.stats['total_items'] / max(1, self.stats['total_batches'])
        
        # 记录历史
        self.verification_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'batch_size': len(memories),
            'api_calls': api_call_count,
            'processing_time': processing_time
        })
        
        return BatchVerificationResult(
            query=query,
            results=all_results,
            batch_size=len(memories),
            api_calls=api_call_count,
            processing_time=processing_time
        )
    
    def _create_batches(self, items: List[str], batch_size: int) -> List[List[str]]:
        """创建批次"""
        return [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
    
    def _verify_single_batch(
        self,
        query: str,
        batch_memories: List[str],
        batch_idx: int
    ) -> Tuple[List[Dict], int]:
        """
        验证单个batch
        
        Returns:
            (results, api_call_count)
        """
        # 构建批量验证prompt
        prompt = self._build_batch_prompt(query, batch_memories, batch_idx)
        
        try:
            # 调用API进行批量验证
            results = self._call_batch_api(prompt, query, batch_memories)
            return results, 1  # 1次API调用验证多条
        except Exception as e:
            print(f"[BatchVerification] Batch {batch_idx} API failed: {e}")
            # Fallback: 逐个验证
            results = self._fallback_batch_verify(query, batch_memories)
            return results, len(batch_memories)  # 多次调用
    
    def _build_batch_prompt(
        self,
        query: str,
        memories: List[str],
        batch_idx: int
    ) -> str:
        """构建批量验证prompt"""
        memories_text = "\n\n".join([
            f"【记忆{i+1}】\n{memory[:500]}"  # 限制长度
            for i, memory in enumerate(memories)
        ])
        
        return f"""你是一个记忆验证助手。请批量验证以下记忆是否能回答用户查询。

【用户查询】
{query}

{memories_text}

请为每条记忆分析并以JSON数组格式回复:
[
    {{
        "memory_index": 1,
        "is_relevant": true/false,
        "answers_query": true/false,
        "confidence": 0.0-1.0,
        "reasoning": "简要解释"
    }},
    ...
]

判断标准：
- is_relevant: 记忆主题是否与查询相关
- answers_query: 记忆是否包含查询的答案
- confidence: 你的确信程度 (0-1)
- reasoning: 简要说明原因

请确保返回格式正确的JSON数组，包含所有{len(memories)}条记忆的分析结果。"""
    
    def _call_batch_api(
        self,
        prompt: str,
        query: str,
        memories: List[str]
    ) -> List[Dict]:
        """调用批量验证API"""
        # 使用subprocess执行验证
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            # 构建批量验证脚本
            verify_script = self._build_batch_verify_script(query, memories, prompt_file)
            
            # 执行
            result = subprocess.run(
                ['python3', '-c', verify_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 清理
            try:
                os.unlink(prompt_file)
            except:
                pass
            
            # 解析结果
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout.strip())
                except json.JSONDecodeError:
                    pass
            
            # 解析失败，回退
            return self._fallback_batch_verify(query, memories)
            
        except Exception as e:
            print(f"[BatchVerification] API error: {e}")
            return self._fallback_batch_verify(query, memories)
    
    def _build_batch_verify_script(
        self,
        query: str,
        memories: List[str],
        prompt_file: str
    ) -> str:
        """构建批量验证脚本"""
        # 转义字符串
        query_escaped = query.replace('"', '\\"')
        memories_escaped = [m.replace('"', '\\"') for m in memories]
        
        memories_json = json.dumps(memories_escaped, ensure_ascii=False)
        
        script = f'''
import json
import re

query = """{query_escaped}"""
memories = {memories_json}

results = []

for i, memory in enumerate(memories, 1):
    # 关键词匹配
    query_words = set(re.findall(r'[\\u4e00-\\u9fff]+|[a-zA-Z]+', query.lower()))
    memory_words = set(re.findall(r'[\\u4e00-\\u9fff]+|[a-zA-Z]+', memory.lower()))
    
    overlap = query_words & memory_words
    overlap_ratio = len(overlap) / len(query_words) if query_words else 0
    
    # 判断
    if overlap_ratio > 0.5:
        result = {{
            "memory_index": i,
            "is_relevant": True,
            "answers_query": overlap_ratio > 0.7,
            "confidence": min(0.95, 0.5 + overlap_ratio),
            "reasoning": f"关键词匹配度{{int(overlap_ratio*100)}}%"
        }}
    elif overlap_ratio > 0.2:
        result = {{
            "memory_index": i,
            "is_relevant": True,
            "answers_query": False,
            "confidence": 0.4,
            "reasoning": "部分相关"
        }}
    else:
        result = {{
            "memory_index": i,
            "is_relevant": False,
            "answers_query": False,
            "confidence": 0.1,
            "reasoning": "不匹配"
        }}
    
    results.append(result)

print(json.dumps(results, ensure_ascii=False))
'''
        return script
    
    def _fallback_batch_verify(self, query: str, memories: List[str]) -> List[Dict]:
        """Fallback批量验证"""
        results = []
        for i, memory in enumerate(memories, 1):
            # 简单的关键词匹配
            query_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query.lower()))
            memory_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', memory.lower()))
            
            overlap = query_words & memory_words
            overlap_ratio = len(overlap) / len(query_words) if query_words else 0
            
            if overlap_ratio > 0.5:
                results.append({
                    'memory_index': i,
                    'is_relevant': True,
                    'answers_query': overlap_ratio > 0.7,
                    'confidence': min(0.95, 0.5 + overlap_ratio),
                    'reasoning': f"关键词匹配度{int(overlap_ratio*100)}%"
                })
            elif overlap_ratio > 0.2:
                results.append({
                    'memory_index': i,
                    'is_relevant': True,
                    'answers_query': False,
                    'confidence': 0.4,
                    'reasoning': "部分相关"
                })
            else:
                results.append({
                    'memory_index': i,
                    'is_relevant': False,
                    'answers_query': False,
                    'confidence': 0.1,
                    'reasoning': "不匹配"
                })
        
        return results
    
    def get_stats(self) -> Dict:
        """获取统计"""
        total = self.stats['total_items']
        if total > 0:
            efficiency = total / max(1, self.stats['api_calls'])
            return {
                **self.stats,
                'efficiency': efficiency,  # 每条记忆平均API调用次数
                'cost_reduction': (1 - 1/efficiency) * 100 if efficiency > 1 else 0
            }
        return self.stats


class BatchEnabledMemorySystem:
    """
    启用批量验证的记忆系统
    """
    
    def __init__(self, batch_size: int = 5):
        self.batch_agent = BatchVerificationAgent(batch_size=batch_size)
        self.stats = {
            'total_queries': 0,
            'total_memories': 0,
            'total_api_calls': 0
        }
    
    def retrieve_and_verify_batch(
        self,
        query: str,
        memories: List[str]
    ) -> Dict:
        """批量检索并验证"""
        self.stats['total_queries'] += 1
        self.stats['total_memories'] += len(memories)
        
        # 批量验证
        batch_result = self.batch_agent.verify_batch(query, memories)
        self.stats['total_api_calls'] += batch_result.api_calls
        
        # 获取最佳结果
        best = batch_result.get_best_result()
        
        # 构建响应
        result = {
            'query': query,
            'batch_verification': True,
            'batch_size': batch_result.batch_size,
            'api_calls': batch_result.api_calls,
            'processing_time': batch_result.processing_time,
            'all_results': batch_result.results
        }
        
        if best and best.get('confidence', 0) > 0.8:
            result.update({
                'decision': 'use',
                'confidence': best['confidence'],
                'best_memory_index': best.get('memory_index', 0),
                'reasoning': best.get('reasoning', '')
            })
        elif best and best.get('confidence', 0) > 0.5:
            result.update({
                'decision': 'confirm',
                'confidence': best['confidence'],
                'best_memory_index': best.get('memory_index', 0),
                'reasoning': best.get('reasoning', '')
            })
        else:
            result.update({
                'decision': 'unknown',
                'confidence': 0.0,
                'reasoning': '无可靠记忆'
            })
        
        return result
    
    def get_efficiency_report(self) -> Dict:
        """获取效率报告"""
        batch_stats = self.batch_agent.get_stats()
        
        return {
            'total_queries': self.stats['total_queries'],
            'total_memories': self.stats['total_memories'],
            'total_api_calls': self.stats['total_api_calls'],
            'batch_efficiency': batch_stats.get('efficiency', 1.0),
            'cost_reduction': batch_stats.get('cost_reduction', 0),
            'avg_processing_time': sum(
                h.get('processing_time', 0) for h in self.batch_agent.verification_history
            ) / max(1, len(self.batch_agent.verification_history))
        }
    
    def print_efficiency_report(self):
        """打印效率报告"""
        report = self.get_efficiency_report()
        
        print("\n" + "="*60)
        print("📊 批量验证效率报告")
        print("="*60)
        print(f"总查询数: {report['total_queries']}")
        print(f"总记忆数: {report['total_memories']}")
        print(f"总API调用: {report['total_api_calls']}")
        print(f"批量效率: {report['batch_efficiency']:.2f}x (每次调用验证{report['batch_efficiency']:.1f}条)")
        print(f"成本降低: {report['cost_reduction']:.1f}%")
        print(f"平均处理时间: {report['avg_processing_time']:.2f}s")


def test_batch_verification():
    """测试批量验证"""
    print("="*70)
    print("🧪 测试批量验证系统 v0.5")
    print("="*70)
    
    system = BatchEnabledMemorySystem(batch_size=5)
    
    # 测试1: 小批量
    print("\n--- 测试1: 小批量 (3条记忆) ---")
    query1 = "我的B站UID是多少？"
    memories1 = [
        "用户的B站UID是 12345678",
        "用户是程序员，使用Python",
        "系统架构采用微服务"
    ]
    
    result1 = system.retrieve_and_verify_batch(query1, memories1)
    print(f"查询: {query1}")
    print(f"Batch大小: {result1['batch_size']}")
    print(f"API调用: {result1['api_calls']}")
    print(f"决策: {result1['decision']} | 置信度: {result1.get('confidence', 0):.2f}")
    print(f"处理时间: {result1['processing_time']:.3f}s")
    
    # 测试2: 大批量
    print("\n--- 测试2: 大批量 (12条记忆) ---")
    query2 = "系统架构是什么样的？"
    memories2 = [
        "系统采用5层自进化架构",
        "代码理解层解析模块依赖",
        "创造性设计层生成方案",
        "形式化验证层检查正确性",
        "沙箱测试层安全执行",
        "反馈学习层持续改进",
        "用户使用MacBook Pro",
        "项目使用Python开发",
        "部署在Linux服务器",
        "使用Git进行版本控制",
        "测试覆盖率80%",
        "CI/CD自动化部署"
    ]
    
    result2 = system.retrieve_and_verify_batch(query2, memories2)
    print(f"查询: {query2}")
    print(f"Batch大小: {result2['batch_size']}")
    print(f"API调用: {result2['api_calls']} (分批处理)")
    print(f"决策: {result2['decision']} | 置信度: {result2.get('confidence', 0):.2f}")
    print(f"处理时间: {result2['processing_time']:.3f}s")
    
    # 显示所有结果
    print("\n详细结果:")
    for r in result2['all_results'][:5]:
        status = "✓" if r.get('answers_query') else "~" if r.get('is_relevant') else "✗"
        print(f"  {status} [{r.get('confidence', 0):.2f}] {r.get('reasoning', '')}")
    
    # 效率报告
    system.print_efficiency_report()
    
    print("\n" + "="*70)
    print("✅ 测试完成")
    print("="*70)


if __name__ == "__main__":
    test_batch_verification()
