#!/usr/bin/env python3
"""
Metacognitive Layer - 元认知层
实现对自己思维过程的监控和评估
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

class ThoughtProcess(Enum):
    """思维过程类型"""
    ANALYSIS = "analysis"           # 分析问题
    RETRIEVAL = "retrieval"         # 检索知识
    REASONING = "reasoning"         # 逻辑推理
    GENERATION = "generation"       # 生成回答
    VERIFICATION = "verification"   # 验证检查
    UNCERTAINTY = "uncertainty"     # 不确定性评估

@dataclass
class ThoughtStep:
    """思维步骤记录"""
    step_id: str
    process_type: ThoughtProcess
    description: str
    confidence: float
    duration_ms: int
    check_passed: bool

class MetacognitiveMonitor:
    """
    元认知监控器
    
    功能：
    1. 记录思维过程（Think out loud）
    2. 评估每个步骤的质量
    3. 检测潜在错误
    4. 触发自我修正
    """
    
    def __init__(self, log_file: str = ".learning/metacognition.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.thought_chain: List[ThoughtStep] = []
        self.current_query: str = ""
        self.error_flags: List[str] = []
        self.self_corrections: List[Dict] = []
    
    def start_thinking(self, query: str):
        """开始记录思维过程"""
        self.current_query = query
        self.thought_chain = []
        self.error_flags = []
        self.start_time = time.time()
    
    def record_thought(
        self, 
        process_type: ThoughtProcess, 
        description: str,
        confidence: float = 0.8
    ):
        """
        记录一个思维步骤
        
        Args:
            process_type: 思维过程类型
            description: 描述
            confidence: 对此步骤的置信度 (0-1)
        """
        step = ThoughtStep(
            step_id=f"STEP-{len(self.thought_chain)+1}",
            process_type=process_type,
            description=description,
            confidence=confidence,
            duration_ms=int((time.time() - self.start_time) * 1000),
            check_passed=self._quality_check(process_type, description, confidence)
        )
        
        self.thought_chain.append(step)
        
        # 如果质量检查失败，记录错误标志
        if not step.check_passed:
            self.error_flags.append({
                'step': step.step_id,
                'issue': f"Low confidence ({confidence}) in {process_type.value}",
                'suggestion': self._get_correction_suggestion(process_type)
            })
    
    def _quality_check(self, process_type: ThoughtProcess, description: str, confidence: float) -> bool:
        """质量检查"""
        # 检查1: 置信度阈值
        if confidence < 0.5:
            return False
        
        # 检查2: 描述是否过于模糊
        vague_markers = ["大概", "可能", "应该", "也许", "不确定", "不知道"]
        if any(marker in description for marker in vague_markers) and confidence > 0.7:
            # 矛盾：描述模糊但置信度高
            return False
        
        # 检查3: 推理步骤是否有逻辑连接词
        if process_type == ThoughtProcess.REASONING:
            logic_markers = ["因为", "所以", "因此", "导致", "意味着", "implies", "therefore"]
            if not any(marker in description for marker in logic_markers):
                return False
        
        return True
    
    def _get_correction_suggestion(self, process_type: ThoughtProcess) -> str:
        """获取纠正建议"""
        suggestions = {
            ThoughtProcess.ANALYSIS: "重新分析问题，明确关键要素",
            ThoughtProcess.RETRIEVAL: "承认知识边界，建议搜索验证",
            ThoughtProcess.REASONING: "显式列出推理链条，检查逻辑漏洞",
            ThoughtProcess.GENERATION: "生成多个候选，选择最优",
            ThoughtProcess.VERIFICATION: "交叉验证，寻找反面证据",
            ThoughtProcess.UNCERTAINTY: "量化不确定性，给出置信区间"
        }
        return suggestions.get(process_type, "重新评估此步骤")
    
    def self_reflect(self) -> Dict[str, Any]:
        """
        自我反思：评估整个思维过程
        
        Returns:
            反思报告
        """
        if not self.thought_chain:
            return {"status": "no_thought_recorded"}
        
        # 统计
        total_steps = len(self.thought_chain)
        avg_confidence = sum(s.confidence for s in self.thought_chain) / total_steps
        failed_checks = len(self.error_flags)
        
        # 识别潜在问题
        issues = []
        
        # 问题1: 缺少验证步骤
        has_verification = any(s.process_type == ThoughtProcess.VERIFICATION for s in self.thought_chain)
        if not has_verification:
            issues.append("缺少验证步骤，建议增加自我检查")
        
        # 问题2: 过早下结论
        if self.thought_chain and self.thought_chain[0].process_type == ThoughtProcess.GENERATION:
            issues.append("过早生成回答，建议先分析再生成")
        
        # 问题3: 置信度不一致
        confidences = [s.confidence for s in self.thought_chain]
        if max(confidences) - min(confidences) > 0.5:
            issues.append("各步骤置信度差异大，建议重新审视低置信度步骤")
        
        # 生成改进建议
        suggestions = self._generate_improvements(issues)
        
        return {
            "status": "reflected",
            "total_steps": total_steps,
            "avg_confidence": avg_confidence,
            "failed_checks": failed_checks,
            "issues": issues,
            "suggestions": suggestions,
            "thought_chain_summary": [
                {"step": s.step_id, "type": s.process_type.value, "conf": s.confidence}
                for s in self.thought_chain
            ]
        }
    
    def _generate_improvements(self, issues: List[str]) -> List[str]:
        """生成改进建议"""
        improvements = []
        
        if "缺少验证步骤" in str(issues):
            improvements.append("在生成回答前，增加'验证'步骤，检查关键事实")
        
        if "过早生成回答" in str(issues):
            improvements.append("采用'先分析-再推理-后生成'的流程")
        
        if "置信度差异大" in str(issues):
            improvements.append("对低置信度步骤进行额外验证或标注不确定性")
        
        return improvements
    
    def think_out_loud(self, query: str) -> str:
        """
        思考过程外化：生成可视化的思维链
        
        这模拟了人类的"出声思考"过程
        """
        self.start_thinking(query)
        
        # 模拟思维过程
        steps = [
            (ThoughtProcess.ANALYSIS, "分析问题类型和关键要素", 0.9),
            (ThoughtProcess.RETRIEVAL, "从记忆中检索相关知识", 0.8),
            (ThoughtProcess.REASONING, "基于已知信息进行逻辑推理", 0.75),
            (ThoughtProcess.UNCERTAINTY, "评估回答的不确定性", 0.7),
            (ThoughtProcess.VERIFICATION, "验证关键事实", 0.85),
            (ThoughtProcess.GENERATION, "生成最终回答", 0.8)
        ]
        
        for process, desc, conf in steps:
            self.record_thought(process, desc, conf)
        
        # 生成思维链可视化
        output = []
        output.append("🧠 **思维过程外化**\n")
        
        for step in self.thought_chain:
            icon = "✅" if step.check_passed else "⚠️"
            output.append(f"{icon} **{step.step_id}** [{step.process_type.value}] (置信度: {step.confidence})")
            output.append(f"   {step.description}")
            if not step.check_passed:
                output.append(f"   💡 建议: {self._get_correction_suggestion(step.process_type)}")
            output.append("")
        
        # 添加自我反思
        reflection = self.self_reflect()
        output.append("\n🔍 **自我反思**")
        output.append(f"平均置信度: {reflection['avg_confidence']:.2f}")
        if reflection['issues']:
            output.append(f"发现 {len(reflection['issues'])} 个潜在问题:")
            for issue in reflection['issues']:
                output.append(f"  - {issue}")
        if reflection['suggestions']:
            output.append("改进建议:")
            for suggestion in reflection['suggestions']:
                output.append(f"  💡 {suggestion}")
        
        return "\n".join(output)
    
    def get_thought_chain_for_prompt(self) -> str:
        """
        将思维链转换为可用于提示工程的格式
        
        这实现了'Chain of Thought'提示
        """
        if not self.thought_chain:
            return ""
        
        chain_text = []
        for step in self.thought_chain:
            chain_text.append(f"{step.step_id}: [{step.process_type.value}] {step.description}")
        
        return "\n".join(chain_text)


# ==================== 集成演示 ====================

class MetacognitiveAI:
    """
    集成元认知的AI系统
    """
    
    def __init__(self):
        self.metacognition = MetacognitiveMonitor()
    
    def respond(self, query: str, show_thinking: bool = False) -> str:
        """
        生成回答（带元认知监控）
        
        Args:
            query: 用户查询
            show_thinking: 是否显示思维过程
        """
        if show_thinking:
            thinking_process = self.metacognition.think_out_loud(query)
            return thinking_process
        
        # 正常流程：记录思维但不显示
        self.metacognition.start_thinking(query)
        
        # 模拟思维步骤
        self.metacognition.record_thought(
            ThoughtProcess.ANALYSIS, 
            f"分析查询: '{query}' 属于知识问答类型", 
            0.9
        )
        
        self.metacognition.record_thought(
            ThoughtProcess.RETRIEVAL,
            "从知识库检索相关信息",
            0.8
        )
        
        # 检查是否需要搜索
        if any(kw in query for kw in ["最新", "2026", "今天", "现在"]):
            self.metacognition.record_thought(
                ThoughtProcess.UNCERTAINTY,
                "检测到时间敏感信息，知识可能过时",
                0.6
            )
        
        self.metacognition.record_thought(
            ThoughtProcess.REASONING,
            "基于检索到的信息进行逻辑推理",
            0.75
        )
        
        # 自我反思
        reflection = self.metacognition.self_reflect()
        
        # 生成回答
        response = f"【关于'{query}'的回答】"
        
        # 如果有问题，添加不确定性声明
        if reflection['issues']:
            response += "\n\n⚠️ **注意**: 我在思考过程中发现一些潜在问题:\n"
            for issue in reflection['issues']:
                response += f"- {issue}\n"
        
        return response


def demo():
    """演示元认知层"""
    print("=" * 70)
    print("元认知层演示")
    print("=" * 70)
    
    ai = MetacognitiveAI()
    
    # 演示1: 显示思维过程
    print("\n【演示1: 思维过程外化】")
    query1 = "解释量子计算的原理"
    print(f"查询: {query1}\n")
    result = ai.respond(query1, show_thinking=True)
    print(result)
    
    # 演示2: 正常回答（带元认知监控）
    print("\n" + "=" * 70)
    print("\n【演示2: 正常回答（元认知后台运行）】")
    query2 = "2026年最新的AI技术是什么？"
    print(f"查询: {query2}\n")
    result = ai.respond(query2, show_thinking=False)
    print(result)


if __name__ == "__main__":
    demo()
