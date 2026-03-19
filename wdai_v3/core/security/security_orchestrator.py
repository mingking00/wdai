"""
wdai Security Orchestrator - 三层安全审查协调器
整合 Fast Check、Static Analysis、AI Review
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from .fast_check import FastCheck, FastCheckResult, SecurityFinding


@dataclass
class StaticAnalysisResult:
    """静态分析结果（L2）"""
    findings: List[SecurityFinding]
    risk_score: float
    tool_used: str
    elapsed_seconds: float
    raw_output: Optional[str] = None


@dataclass
class AIReviewResult:
    """AI 深度审查结果（L3）"""
    findings: List[SecurityFinding]
    risk_score: float
    suggestions: List[str]
    explanation: str
    elapsed_seconds: float


@dataclass
class SecurityReport:
    """完整安全审查报告"""
    code_hash: str
    fast_result: FastCheckResult
    static_result: Optional[StaticAnalysisResult]
    ai_result: Optional[AIReviewResult]
    overall_risk: float
    recommendations: List[str] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        lines = [
            "# 安全审查报告",
            "",
            f"**总体风险**: {'🔴 极高' if self.overall_risk > 0.8 else '🟠 高' if self.overall_risk > 0.5 else '🟡 中' if self.overall_risk > 0.3 else '🟢 低'} ({self.overall_risk:.2f})",
            "",
            "## L1 - Fast Check",
            f"- 耗时: {self.fast_result.elapsed_ms:.3f} ms",
            f"- 发现问题: {len(self.fast_result.findings)} 个",
            f"- 风险分数: {self.fast_result.risk_score:.2f}",
            ""
        ]
        
        if self.fast_result.findings:
            lines.append("### 发现的问题")
            for f in self.fast_result.findings:
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(f.severity, "⚪")
                lines.append(f"- {emoji} **[{f.severity.upper()}]** 第{f.line_number}行: {f.message}")
                lines.append(f"  ```python")
                lines.append(f"  {f.line_content}")
                lines.append(f"  ```")
            lines.append("")
        
        if self.static_result:
            lines.extend([
                "## L2 - Static Analysis",
                f"- 工具: {self.static_result.tool_used}",
                f"- 耗时: {self.static_result.elapsed_seconds:.2f} s",
                f"- 发现问题: {len(self.static_result.findings)} 个",
                ""
            ])
        
        if self.ai_result:
            lines.extend([
                "## L3 - AI Review",
                f"- 耗时: {self.ai_result.elapsed_seconds:.2f} s",
                f"- 建议: {len(self.ai_result.suggestions)} 条",
                "",
                "### AI 分析",
                self.ai_result.explanation,
                "",
                "### 修复建议"
            ])
            for suggestion in self.ai_result.suggestions:
                lines.append(f"- {suggestion}")
            lines.append("")
        
        if self.recommendations:
            lines.extend([
                "## 总体建议",
                ""
            ])
            for rec in self.recommendations:
                lines.append(f"- {rec}")
        
        return "\n".join(lines)
    
    def is_safe(self) -> bool:
        """代码是否被认为安全"""
        return self.overall_risk < 0.5 and not self.fast_result.has_critical


class SecurityOrchestrator:
    """
    三层安全审查协调器
    
    架构:
    - L1: Fast Check (总是运行) - 毫秒级
    - L2: Static Analysis (Fast risk > 0.3 时运行) - 秒级
    - L3: AI Review (Static risk > 0.7 时运行) - 十秒级
    """
    
    # 风险阈值配置
    STATIC_ANALYSIS_THRESHOLD = 0.3
    AI_REVIEW_THRESHOLD = 0.7
    
    def __init__(self, rules_path: Optional[Path] = None, enable_static: bool = False, enable_ai: bool = False):
        """
        初始化安全协调器
        
        Args:
            rules_path: 自定义规则文件路径
            enable_static: 是否启用 L2 静态分析
            enable_ai: 是否启用 L3 AI 审查
        """
        self.fast_checker = FastCheck(rules_path)
        self.enable_static = enable_static
        self.enable_ai = enable_ai
        
        # L2/L3 组件懒加载
        self._static_analyzer = None
        self._ai_reviewer = None
    
    async def review(self, code: str, context: Optional[Dict[str, Any]] = None) -> SecurityReport:
        """
        执行完整安全审查
        
        Args:
            code: 要审查的代码
            context: 可选的上下文信息（文件路径、项目类型等）
            
        Returns:
            SecurityReport 完整报告
        """
        import hashlib
        code_hash = hashlib.md5(code.encode()).hexdigest()[:8]
        
        # L1: Fast Check (总是运行)
        fast_result = self.fast_checker.check(code)
        
        # L2: Static Analysis (有条件运行)
        static_result = None
        if self.enable_static and fast_result.risk_score > self.STATIC_ANALYSIS_THRESHOLD:
            static_result = await self._run_static_analysis(code, context)
        
        # L3: AI Review (有条件运行)
        ai_result = None
        if self.enable_ai and static_result and static_result.risk_score > self.AI_REVIEW_THRESHOLD:
            ai_result = await self._run_ai_review(code, context)
        
        # 计算总体风险
        overall_risk = self._calculate_overall_risk(fast_result, static_result, ai_result)
        
        # 生成建议
        recommendations = self._generate_recommendations(fast_result, static_result, ai_result)
        
        return SecurityReport(
            code_hash=code_hash,
            fast_result=fast_result,
            static_result=static_result,
            ai_result=ai_result,
            overall_risk=overall_risk,
            recommendations=recommendations
        )
    
    async def quick_check(self, code: str) -> bool:
        """
        快速检查代码是否安全
        
        Returns:
            True 如果代码通过安全检查
        """
        result = self.fast_checker.check(code)
        return not result.has_critical and result.risk_score < 0.5
    
    async def _run_static_analysis(self, code: str, context: Optional[Dict]) -> Optional[StaticAnalysisResult]:
        """运行 L2 静态分析"""
        # P0 阶段暂不实现，返回占位
        return StaticAnalysisResult(
            findings=[],
            risk_score=0.0,
            tool_used="placeholder",
            elapsed_seconds=0.0
        )
    
    async def _run_ai_review(self, code: str, context: Optional[Dict]) -> Optional[AIReviewResult]:
        """运行 L3 AI 审查"""
        # P0 阶段暂不实现，返回占位
        return AIReviewResult(
            findings=[],
            risk_score=0.0,
            suggestions=[],
            explanation="AI Review 在 P0 阶段未启用",
            elapsed_seconds=0.0
        )
    
    def _calculate_overall_risk(self, fast: FastCheckResult, 
                                 static: Optional[StaticAnalysisResult],
                                 ai: Optional[AIReviewResult]) -> float:
        """计算总体风险分数"""
        # 基础权重
        weights = {"fast": 0.4, "static": 0.3, "ai": 0.3}
        
        scores = [fast.risk_score * weights["fast"]]
        
        if static:
            scores.append(static.risk_score * weights["static"])
        else:
            scores.append(fast.risk_score * weights["static"])
        
        if ai:
            scores.append(ai.risk_score * weights["ai"])
        else:
            scores.append(fast.risk_score * weights["ai"])
        
        return min(1.0, sum(scores))
    
    def _generate_recommendations(self, fast: FastCheckResult,
                                   static: Optional[StaticAnalysisResult],
                                   ai: Optional[AIReviewResult]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        if fast.has_critical:
            recommendations.append("🚨 发现严重安全问题，建议立即修复后再继续")
        
        if fast.has_high:
            recommendations.append("⚠️ 发现高风险问题，建议人工审查")
        
        if fast.findings:
            severities = [f.severity for f in fast.findings]
            if severities.count("medium") > 3:
                recommendations.append("ℹ️ 多个中风险问题，建议批量修复")
        
        if not fast.findings:
            recommendations.append("✅ Fast Check 通过，代码看起来安全")
        
        return recommendations


# 便捷函数
def create_security_orchestrator(enable_static: bool = False, 
                                  enable_ai: bool = False) -> SecurityOrchestrator:
    """创建安全协调器"""
    return SecurityOrchestrator(enable_static=enable_static, enable_ai=enable_ai)


async def review_code(code: str, enable_static: bool = False, 
                     enable_ai: bool = False) -> SecurityReport:
    """一键代码审查"""
    orchestrator = create_security_orchestrator(enable_static, enable_ai)
    return await orchestrator.review(code)


if __name__ == "__main__":
    # 测试
    test_code = """
import os

def dangerous_function(user_input):
    # 执行用户输入 - 危险！
    os.system(f"echo {user_input}")
    return True
"""
    
    async def main():
        report = await review_code(test_code)
        print(report.to_markdown())
        print(f"\n是否安全: {report.is_safe()}")
    
    asyncio.run(main())
