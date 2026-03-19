"""
改进验证系统 v4.0 - 快/慢双架构 + 白盒轨迹

融合 Percepta 和 AttnRes 思想：
1. 快/慢双系统：Fast Check (O(1)) + Slow Check (LLM)
2. 预编译模式：常见错误硬编码，无需推理
3. 白盒轨迹：每一步验证都可解释、可追溯
4. 动态权重：根据历史自适应调整检查策略
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import re
import asyncio


class CheckResult(Enum):
    """检查结果"""
    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"
    SKIP = "skip"


@dataclass
class VerificationTrace:
    """验证轨迹 - 白盒化记录"""
    step: int
    check_name: str
    check_type: str  # 'fast' or 'slow'
    result: CheckResult
    latency_ms: float
    weight: float
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'step': self.step,
            'check': self.check_name,
            'type': self.check_type,
            'result': self.result.value,
            'latency_ms': self.latency_ms,
            'weight': self.weight,
            'details': self.details
        }


@dataclass
class WhiteBoxResult:
    """白盒验证结果"""
    is_safe: bool
    final_response: str
    traces: List[VerificationTrace]
    summary: Dict[str, Any]
    
    def explain(self) -> str:
        """生成人类可读的验证报告"""
        lines = [
            "="*70,
            "验证报告 (White Box)",
            "="*70,
            f"最终结果: {'✅ 通过' if self.is_safe else '❌ 失败'}",
            f"检查步骤: {len(self.traces)}",
            f"总耗时: {sum(t.latency_ms for t in self.traces):.1f}ms",
            "",
            "详细轨迹:",
            "-"*70
        ]
        
        for trace in self.traces:
            icon = "✅" if trace.result == CheckResult.PASS else "❌" if trace.result == CheckResult.FAIL else "⏭️"
            lines.append(
                f"{icon} [{trace.step}] {trace.check_name} ({trace.check_type})\n"
                f"    结果: {trace.result.value}, 权重: {trace.weight:.3f}, 耗时: {trace.latency_ms:.1f}ms"
            )
            if trace.details:
                lines.append(f"    详情: {trace.details}")
        
        lines.extend([
            "-"*70,
            "权重分布:",
            self._weight_distribution(),
            "="*70
        ])
        
        return "\n".join(lines)
    
    def _weight_distribution(self) -> str:
        """权重分布统计"""
        fast_weight = sum(t.weight for t in self.traces if t.check_type == 'fast')
        slow_weight = sum(t.weight for t in self.traces if t.check_type == 'slow')
        total = fast_weight + slow_weight
        if total > 0:
            return f"  Fast Check: {fast_weight/total*100:.1f}%\n  Slow Check: {slow_weight/total*100:.1f}%"
        return "  N/A"


class FastCheckEngine:
    """
    快速检查引擎 (Percepta Fast System 思想)
    
    O(1) 复杂度，无需 LLM 推理
    预编译常见错误模式
    """
    
    # 预编译的错误模式 (硬编码，类似 Percepta 的权重嵌入)
    PATTERNS = {
        'fabrication_markers': {
            'patterns': ['根据文献', '研究表明', '数据显示', '调查发现', '根据研究', '最新研究'],
            'weight': 0.3,
            'check': lambda text: any(p in text and '来源' not in text and '引用' not in text 
                                     for p in ['根据文献', '研究表明', '数据显示', '根据研究', '最新研究'])
        },
        'absolute_statements': {
            'patterns': ['肯定', '一定', '绝对', '毫无疑问', '必然'],
            'weight': 0.2,
            'check': lambda text: any(p in text for p in ['肯定', '一定', '绝对'])
        },
        'unverified_image': {
            'patterns': ['根据图片', '截图显示', '如图所示'],
            'weight': 0.5,  # 高风险
            'check': lambda text: any(p in text for p in ['根据图片', '截图显示'])
        },
        'unsupported_quotes': {
            'patterns': ['"'],  # 包含引号但没有来源
            'weight': 0.3,
            'check': lambda text: '"' in text and '来源' not in text and '引用' not in text
        },
        'numeric_hallucination': {
            'patterns': [],
            'weight': 0.2,
            'check': '_check_suspicious_numbers'  # 使用字符串标记
        }
    }
    
    @staticmethod
    def _check_suspicious_numbers(text: str) -> bool:
        """检查可疑数字（过于精确但没有上下文）- 放宽规则"""
        import re
        # 只检查特别长的数字（8位以上，更严格）
        numbers = re.findall(r'\b\d{8,}\b', text)
        if not numbers:
            return False
        
        # 检查是否有数据相关的上下文
        data_context = ['数据', '统计', '研究表明', '调查显示', '报告', '分析']
        has_context = any(c in text for c in data_context)
        
        return not has_context and len(numbers) > 0
    
    def check(self, response: str, context: Dict) -> List[Dict]:
        """
        快速检查 - O(1) 复杂度
        
        返回发现的违规行为列表
        """
        violations = []
        
        for check_name, config in self.PATTERNS.items():
            # 处理特殊检查函数
            if config['check'] == '_check_suspicious_numbers':
                if self._check_suspicious_numbers(response):
                    violations.append({
                        'check_name': check_name,
                        'weight': config['weight'],
                        'patterns': config['patterns'],
                        'auto_fixable': False
                    })
            elif config['check'](response):
                violations.append({
                    'check_name': check_name,
                    'weight': config['weight'],
                    'patterns': config['patterns'],
                    'auto_fixable': check_name in ['absolute_statements', 'unsupported_quotes']
                })
        
        # 上下文特定检查
        if context.get('has_image') and not context.get('image_verified'):
            if '图片' in response or '截图' in response:
                violations.append({
                    'check_name': 'unverified_image_ref',
                    'weight': 0.8,  # 极高风险
                    'patterns': ['图片引用'],
                    'auto_fixable': False
                })
        
        return violations
    
    def auto_fix(self, response: str, violation: Dict) -> str:
        """自动修复可修复的问题"""
        if violation['check_name'] == 'absolute_statements':
            replacements = {
                '肯定': '可能',
                '一定': '或许',
                '绝对': '相对',
                '毫无疑问': '可能'
            }
            for old, new in replacements.items():
                response = response.replace(old, new)
        
        elif violation['check_name'] == 'unsupported_quotes':
            # 给引用添加提示
            response = response.replace('"', '[未经验证的引用] "')
        
        return response


class SlowCheckEngine:
    """
    深度检查引擎 (Slow System)
    
    使用 LLM 进行深度分析
    仅在 Fast Check 不确定或发现复杂问题时调用
    """
    
    def __init__(self):
        self.complexity_threshold = 0.7
    
    async def check(self, response: str, context: Dict, fast_result: List[Dict]) -> Dict:
        """
        深度检查 - O(think) 复杂度
        
        模拟 LLM 深度分析
        """
        # 这里应该调用实际的 LLM
        # 简化模拟
        
        issues = []
        
        # 基于 Fast Check 的结果进行深度分析
        for v in fast_result:
            if v['weight'] > 0.5:
                issues.append({
                    'severity': 'high',
                    'issue': f"{v['check_name']} 需要深度审查",
                    'recommendation': self._get_recommendation(v['check_name'])
                })
        
        # 模拟 LLM 推理延迟
        await asyncio.sleep(0.1)
        
        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'confidence': 0.85 if len(issues) == 0 else 0.6,
            'reasoning': f"深度分析了 {len(fast_result)} 个 Fast Check 标记点"
        }
    
    def _get_recommendation(self, check_name: str) -> str:
        """获取修复建议"""
        recommendations = {
            'fabrication_markers': '请标注具体来源或改为推测性表述',
            'absolute_statements': '使用更谨慎的措辞，如"可能"、"或许"',
            'unverified_image': '验证图片内容或明确说明无法验证',
            'unverified_image_ref': '阻断：必须验证图片后才能引用',
            'unsupported_quotes': '添加引用来源或使用转述'
        }
        return recommendations.get(check_name, '请人工复核')


class HybridVerificationLayer:
    """
    混合验证层 - 快/慢双系统架构
    
    融合 Percepta 快/慢思想 + AttnRes 动态权重
    """
    
    def __init__(self):
        self.fast_engine = FastCheckEngine()
        self.slow_engine = SlowCheckEngine()
        self.traces: List[VerificationTrace] = []
        self.step = 0
        
        # 学习参数
        self.fast_threshold = 0.5  # Fast Check 权重阈值
        self.slow_trigger_ratio = 0.3  # 触发 Slow Check 的比例
    
    async def verify(self, response: str, context: Dict) -> WhiteBoxResult:
        """
        混合验证流程
        
        1. Fast Check (O(1)) - 预编译模式匹配
        2. 动态决策 - 根据 Fast 结果决定是否 Slow
        3. Slow Check (O(think)) - LLM 深度分析（可选）
        4. 白盒报告 - 完整轨迹记录
        """
        self.traces = []
        self.step = 0
        corrected_response = response
        
        print("="*70)
        print("混合验证 (Hybrid Verification)")
        print("="*70)
        
        # ===== Phase 1: Fast Check =====
        print("\n[Phase 1] Fast Check (O(1))...")
        start = time.time()
        
        fast_violations = self.fast_engine.check(response, context)
        fast_latency = (time.time() - start) * 1000
        
        if fast_violations:
            print(f"  发现 {len(fast_violations)} 个违规:")
            for v in fast_violations:
                print(f"    - {v['check_name']} (权重: {v['weight']})")
                
                # 记录轨迹
                self._add_trace(
                    f"fast_{v['check_name']}", 
                    'fast', 
                    CheckResult.FAIL,
                    fast_latency / len(fast_violations),
                    v['weight'],
                    {'patterns': v['patterns'], 'auto_fixable': v['auto_fixable']}
                )
                
                # 尝试自动修复
                if v['auto_fixable']:
                    corrected_response = self.fast_engine.auto_fix(corrected_response, v)
                    print(f"      → 已自动修复")
        else:
            print("  ✅ 未发现问题")
            self._add_trace('fast_scan', 'fast', CheckResult.PASS, fast_latency, 0.1, {})
        
        # ===== Phase 2: 动态决策 =====
        total_fast_weight = sum(v['weight'] for v in fast_violations)
        need_slow_check = (
            total_fast_weight > self.fast_threshold or
            (fast_violations and len(fast_violations) / len(self.fast_engine.PATTERNS) > self.slow_trigger_ratio)
        )
        
        # ===== Phase 3: Slow Check (条件触发) =====
        slow_result = None
        if need_slow_check:
            print(f"\n[Phase 2] Slow Check (O(think))...")
            print(f"  原因: Fast Check 总权重 {total_fast_weight:.2f} > 阈值 {self.fast_threshold}")
            
            start = time.time()
            slow_result = await self.slow_engine.check(response, context, fast_violations)
            slow_latency = (time.time() - start) * 1000
            
            self._add_trace(
                'llm_deep_analysis',
                'slow',
                CheckResult.PASS if slow_result['passed'] else CheckResult.FAIL,
                slow_latency,
                0.5,  # Slow Check 固定权重
                {'confidence': slow_result['confidence'], 'issues': len(slow_result['issues'])}
            )
            
            print(f"  结果: {'✅ 通过' if slow_result['passed'] else '❌ 发现更多问题'}")
            print(f"  置信度: {slow_result['confidence']:.2f}")
        else:
            print(f"\n[Phase 2] Slow Check 跳过")
            print(f"  原因: Fast Check 总权重 {total_fast_weight:.2f} < 阈值 {self.fast_threshold}")
            self._add_trace('slow_check', 'slow', CheckResult.SKIP, 0, 0, {'reason': 'fast_check_passed'})
        
        # ===== Phase 4: 生成白盒报告 =====
        is_safe = len(fast_violations) == 0 or (slow_result and slow_result['passed'])
        
        # 统计
        fast_count = sum(1 for t in self.traces if t.check_type == 'fast')
        slow_count = sum(1 for t in self.traces if t.check_type == 'slow')
        
        summary = {
            'total_checks': len(self.traces),
            'fast_checks': fast_count,
            'slow_checks': slow_count,
            'violations_found': len(fast_violations),
            'auto_fixed': sum(1 for v in fast_violations if v.get('auto_fixed', False)),
            'total_latency_ms': sum(t.latency_ms for t in self.traces)
        }
        
        result = WhiteBoxResult(
            is_safe=is_safe,
            final_response=corrected_response,
            traces=self.traces,
            summary=summary
        )
        
        # 打印报告
        print("\n" + result.explain())
        
        return result
    
    def _add_trace(self, name: str, check_type: str, result: CheckResult, 
                   latency: float, weight: float, details: Dict):
        """添加验证轨迹"""
        self.step += 1
        self.traces.append(VerificationTrace(
            step=self.step,
            check_name=name,
            check_type=check_type,
            result=result,
            latency_ms=latency,
            weight=weight,
            details=details
        ))
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.traces:
            return {}
        
        return {
            'total_traces': len(self.traces),
            'avg_latency_ms': sum(t.latency_ms for t in self.traces) / len(self.traces),
            'fast_ratio': sum(1 for t in self.traces if t.check_type == 'fast') / len(self.traces),
            'pass_rate': sum(1 for t in self.traces if t.result == CheckResult.PASS) / len(self.traces)
        }


# ===== 演示 =====

async def demo_hybrid_verification():
    """演示混合验证"""
    
    print("\n" + "="*70)
    print("演示: 混合验证系统 v4.0")
    print("="*70)
    
    verifier = HybridVerificationLayer()
    
    # 场景1: 干净的响应（只触发 Fast Check）
    print("\n【场景1】干净响应（仅 Fast Check）")
    response1 = "这是一个普通的回答，没有引用或绝对化表述。"
    result1 = await verifier.verify(response1, {})
    print(f"安全: {result1.is_safe}, 耗时: {result1.summary['total_latency_ms']:.1f}ms")
    
    # 场景2: 有问题但可修复（Fast + 自动修复）
    print("\n【场景2】有问题但可自动修复")
    response2 = "这肯定是最佳方案，根据文献显示效果很好。"
    result2 = await verifier.verify(response2, {})
    print(f"安全: {result2.is_safe}")
    print(f"修正前: {response2}")
    print(f"修正后: {result2.final_response}")
    
    # 场景3: 高风险（触发 Slow Check）
    print("\n【场景3】高风险（触发 Slow Check）")
    response3 = "根据图片分析，这是一个B站视频截图，绝对正确。"
    context3 = {'has_image': True, 'image_verified': False}
    result3 = await verifier.verify(response3, context3)
    print(f"安全: {result3.is_safe}")
    print(f"Fast/Slow 比例: {result3.summary['fast_checks']}/{result3.summary['slow_checks']}")
    
    # 统计
    print("\n【统计】")
    stats = verifier.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_hybrid_verification())
