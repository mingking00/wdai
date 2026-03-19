#!/usr/bin/env python3
"""
MiniMax M2.7 能力测试套件

全面测试编程助手的核心能力

Author: wdai
"""

import os
import json
import time
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# 添加路径
import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from minimax_integration import MiniMaxAPI


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    category: str
    success: bool
    response: str
    latency_ms: int
    tokens_used: int
    score: float  # 0-10
    notes: str


class MiniMaxM27Benchmark:
    """MiniMax M2.7 基准测试"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = MiniMaxAPI(api_key)
        self.results: List[TestResult] = []
        
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        print("="*70)
        print("🧪 MiniMax M2.7 能力测试套件")
        print("="*70)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. 代码生成能力
        self._test_code_generation()
        
        # 2. 代码理解能力
        self._test_code_comprehension()
        
        # 3. 调试能力
        self._test_debugging()
        
        # 4. 算法设计
        self._test_algorithm()
        
        # 5. 中文编程
        self._test_chinese_coding()
        
        # 6. 解释能力
        self._test_explanation()
        
        # 生成报告
        return self._generate_report()
    
    def _call_model(self, messages: List[Dict], test_name: str) -> Tuple[bool, str, int, int]:
        """调用模型并记录"""
        try:
            result = self.client.chat_completion(
                messages=messages,
                model="MiniMax-M2.7",
                temperature=0.7,
                max_tokens=2000
            )
            
            if result.get("success"):
                content = result.get("content", "")
                latency = result.get("latency_ms", 0)
                tokens = result.get("usage", {}).get("total_tokens", 0)
                return True, content, latency, tokens
            else:
                return False, result.get("error", "Unknown error"), 0, 0
                
        except Exception as e:
            return False, str(e), 0, 0
    
    def _test_code_generation(self):
        """测试代码生成"""
        print("📦 测试1: 代码生成能力")
        print("-" * 70)
        
        test_cases = [
            {
                "name": "Python快速排序",
                "prompt": "写一个Python函数实现快速排序，包含注释说明",
                "checks": ["def", "quicksort", "pivot", "recursive"]
            },
            {
                "name": "REST API客户端",
                "prompt": "用Python写一个GitHub API客户端类，支持获取用户信息和仓库列表",
                "checks": ["class", "requests", "get", "json"]
            },
            {
                "name": "数据库操作",
                "prompt": "写SQLite数据库操作类，包含增删改查方法",
                "checks": ["sqlite3", "class", "insert", "select", "update", "delete"]
            }
        ]
        
        for case in test_cases:
            success, response, latency, tokens = self._call_model(
                messages=[{"role": "user", "content": case["prompt"]}],
                test_name=case["name"]
            )
            
            # 评分
            score = 0
            if success:
                checks_passed = sum(1 for check in case["checks"] if check.lower() in response.lower())
                score = (checks_passed / len(case["checks"])) * 10
            
            self.results.append(TestResult(
                test_name=case["name"],
                category="代码生成",
                success=success,
                response=response[:200] if success else response,
                latency_ms=latency,
                tokens_used=tokens,
                score=score,
                notes=f"通过{int(score/10*len(case['checks']))}/{len(case['checks'])}个检查点"
            ))
            
            print(f"  {case['name']}: {'✅' if success else '❌'} (得分: {score:.1f}/10, 延迟: {latency}ms)")
        
        print()
    
    def _test_code_comprehension(self):
        """测试代码理解"""
        print("📦 测试2: 代码理解能力")
        print("-" * 70)
        
        code_snippet = '''
def fibonacci(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]
        '''
        
        prompt = f"解释这段代码的功能、时间复杂度和优化点：\n```python\n{code_snippet}\n```"
        
        success, response, latency, tokens = self._call_model(
            messages=[{"role": "user", "content": prompt}],
            test_name="代码理解"
        )
        
        # 检查是否提到关键点
        key_points = ["斐波那契", "memoization", "缓存", "O(n)", "递归"]
        checks_passed = sum(1 for point in key_points if point in response) if success else 0
        score = (checks_passed / len(key_points)) * 10
        
        self.results.append(TestResult(
            test_name="斐波那契缓存理解",
            category="代码理解",
            success=success,
            response=response[:200] if success else response,
            latency_ms=latency,
            tokens_used=tokens,
            score=score,
            notes=f"理解深度: {checks_passed}/{len(key_points)}"
        ))
        
        print(f"  斐波那契缓存理解: {'✅' if success else '❌'} (得分: {score:.1f}/10)")
        print()
    
    def _test_debugging(self):
        """测试调试能力"""
        print("📦 测试3: 调试能力")
        print("-" * 70)
        
        buggy_code = '''
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

# 测试
result = calculate_average([])  # 这里会出错
        '''
        
        prompt = f"这段代码有什么问题？如何修复？\n```python\n{buggy_code}\n```"
        
        success, response, latency, tokens = self._call_model(
            messages=[{"role": "user", "content": prompt}],
            test_name="调试"
        )
        
        # 检查是否识别到除零错误
        key_checks = ["空列表", "ZeroDivisionError", "len", "判断", "if"]
        checks_passed = sum(1 for check in key_checks if check in response) if success else 0
        score = (checks_passed / len(key_checks)) * 10
        
        self.results.append(TestResult(
            test_name="除零错误调试",
            category="调试",
            success=success,
            response=response[:200] if success else response,
            latency_ms=latency,
            tokens_used=tokens,
            score=score,
            notes=f"问题识别: {checks_passed}/{len(key_checks)}"
        ))
        
        print(f"  除零错误调试: {'✅' if success else '❌'} (得分: {score:.1f}/10)")
        print()
    
    def _test_algorithm(self):
        """测试算法设计"""
        print("📦 测试4: 算法设计")
        print("-" * 70)
        
        prompt = "设计一个LRU缓存实现，要求O(1)时间复杂度的get和put操作。用Python实现并解释思路。"
        
        success, response, latency, tokens = self._call_model(
            messages=[{"role": "user", "content": prompt}],
            test_name="LRU缓存"
        )
        
        # 检查实现质量
        key_elements = ["OrderedDict", "dict", "get", "put", "pop", "move_to_end"]
        checks_passed = sum(1 for elem in key_elements if elem in response) if success else 0
        score = (checks_passed / len(key_elements)) * 10
        
        self.results.append(TestResult(
            test_name="LRU缓存设计",
            category="算法",
            success=success,
            response=response[:200] if success else response,
            latency_ms=latency,
            tokens_used=tokens,
            score=score,
            notes=f"实现完整性: {checks_passed}/{len(key_elements)}"
        ))
        
        print(f"  LRU缓存设计: {'✅' if success else '❌'} (得分: {score:.1f}/10)")
        print()
    
    def _test_chinese_coding(self):
        """测试中文编程"""
        print("📦 测试5: 中文编程能力")
        print("-" * 70)
        
        prompt = "写一个Python函数，输入是一个包含学生姓名和成绩的字典，输出是成绩最高的学生姓名和分数。请用中文注释。"
        
        success, response, latency, tokens = self._call_model(
            messages=[{"role": "user", "content": prompt}],
            test_name="中文编程"
        )
        
        # 检查中文注释和代码质量
        has_chinese_comment = any('\u4e00' <= char <= '\u9fff' for char in response) if success else False
        has_code = "def" in response and "return" in response if success else False
        
        score = 0
        if has_chinese_comment:
            score += 5
        if has_code:
            score += 5
        
        self.results.append(TestResult(
            test_name="中文编程",
            category="中文",
            success=success,
            response=response[:200] if success else response,
            latency_ms=latency,
            tokens_used=tokens,
            score=score,
            notes=f"中文注释: {'✅' if has_chinese_comment else '❌'}, 代码完整: {'✅' if has_code else '❌'}"
        ))
        
        print(f"  中文编程: {'✅' if success else '❌'} (得分: {score:.1f}/10)")
        print()
    
    def _test_explanation(self):
        """测试解释能力"""
        print("📦 测试6: 概念解释")
        print("-" * 70)
        
        prompt = "用简单的语言解释什么是装饰器(decorator)，并举一个实际应用场景的例子。"
        
        success, response, latency, tokens = self._call_model(
            messages=[{"role": "user", "content": prompt}],
            test_name="装饰器解释"
        )
        
        # 检查解释质量
        key_concepts = ["函数", "包装", "@", "example", "日志", "权限"]
        checks_passed = sum(1 for concept in key_concepts if concept in response) if success else 0
        score = (checks_passed / len(key_concepts)) * 10
        
        self.results.append(TestResult(
            test_name="装饰器解释",
            category="解释",
            success=success,
            response=response[:200] if success else response,
            latency_ms=latency,
            tokens_used=tokens,
            score=score,
            notes=f"概念覆盖: {checks_passed}/{len(key_concepts)}"
        ))
        
        print(f"  装饰器解释: {'✅' if success else '❌'} (得分: {score:.1f}/10)")
        print()
    
    def _generate_report(self) -> Dict:
        """生成测试报告"""
        print("="*70)
        print("📊 测试报告")
        print("="*70)
        
        # 统计
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        avg_score = sum(r.score for r in self.results) / total_tests if total_tests > 0 else 0
        avg_latency = sum(r.latency_ms for r in self.results) / total_tests if total_tests > 0 else 0
        total_tokens = sum(r.tokens_used for r in self.results)
        
        # 按类别分组
        by_category = {}
        for r in self.results:
            if r.category not in by_category:
                by_category[r.category] = []
            by_category[r.category].append(r)
        
        print(f"\n总体统计:")
        print(f"  测试总数: {total_tests}")
        print(f"  成功: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"  平均得分: {avg_score:.1f}/10")
        print(f"  平均延迟: {avg_latency:.0f}ms")
        print(f"  总Token: {total_tokens}")
        
        print(f"\n分类表现:")
        for category, results in by_category.items():
            cat_score = sum(r.score for r in results) / len(results)
            print(f"  {category}: {cat_score:.1f}/10")
        
        print(f"\n详细结果:")
        for r in self.results:
            status = "✅" if r.success else "❌"
            print(f"  {status} {r.test_name}: {r.score:.1f}/10 - {r.notes}")
        
        print("\n" + "="*70)
        
        # 能力评级
        if avg_score >= 8:
            level = "🌟 优秀"
        elif avg_score >= 6:
            level = "✅ 良好"
        elif avg_score >= 4:
            level = "⚠️  一般"
        else:
            level = "❌ 需改进"
        
        print(f"综合评级: {level}")
        print("="*70)
        
        return {
            "total_tests": total_tests,
            "success_rate": successful_tests / total_tests,
            "avg_score": avg_score,
            "avg_latency_ms": avg_latency,
            "total_tokens": total_tokens,
            "by_category": {cat: sum(r.score for r in res) / len(res) for cat, res in by_category.items()},
            "detailed_results": [asdict(r) for r in self.results]
        }


def main():
    """主函数"""
    # 使用Coding Plan key
    api_key = "sk-cp-t9kT6omsb2iE7XfCz3Ro798ZE2kyB0MbSR8MPhTjV4SAfsKRUmQ1T3V6DkuytzQXeCJl2NB_L22j6Y_KB1_hp9if6bePI9pg9pYflh4rcLSInNzCDQPtkb4"
    
    benchmark = MiniMaxM27Benchmark(api_key)
    report = benchmark.run_all_tests()
    
    # 保存报告
    report_file = "/root/.openclaw/workspace/.claw-status/minimax_m27_benchmark_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 报告已保存: {report_file}")


if __name__ == "__main__":
    main()
