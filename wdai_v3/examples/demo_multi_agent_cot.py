"""
多 Agent 协作 + 结构化思维链 完整演示

场景：代码审查任务
- Coder Agent: 编写代码实现
- Reviewer Agent: 审查代码质量
- Reflector Agent: 反思整个过程

每个 Agent 都生成：
1. 实时推理追踪（步骤可见）
2. 结构化思维链文档（完整记录）
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

import asyncio
from typing import Dict, Any
from datetime import datetime

from core.agent_system import (
    ServiceAgent, ServiceResult,
    ReasoningStepType, tracer,
    QuickCoT
)


class CoderAgent(ServiceAgent):
    """
    Coder Agent - 编写代码实现
    
    思维链重点：
    - 任务理解：明确功能需求
    - 规划：选择算法和数据结构
    - 决策：权衡性能和可读性
    """
    
    def __init__(self):
        super().__init__("Coder", enable_tracing=True)
    
    async def _handle(self, request: Dict[str, Any]) -> ServiceResult:
        task_id = request.get('task_id', 'unknown')
        feature = request.get('feature', 'unknown')
        
        print(f"\n{'='*70}")
        print(f"📝 Coder Agent 开始工作")
        print(f"{'='*70}")
        
        # 初始化结构化思维链
        cot = QuickCoT()
        
        # ========== 🎯 任务理解 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.UNDERSTAND,
            f"理解需求：实现 {feature} 功能", self.name
        )
        
        cot.understand(
            user_intent=f"实现 {feature} 功能",
            explicit_requirements=["功能正确", "代码清晰"],
            implicit_requirements=["处理边界情况", "易于维护"],
            constraints=["使用Python", "单文件实现"],
            success_criteria=["通过基本测试", "代码可审查"]
        )
        
        # ========== 🔍 现状分析 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.ANALYZE,
            "分析实现方案", self.name
        )
        
        cot.analyze(
            available_data=["功能需求文档", "示例输入输出"],
            key_observations=["需要处理列表数据", "可能有重复元素"],
            potential_issues=[["大数据量性能", "边界情况处理"]]
        )
        
        await asyncio.sleep(0.2)  # 模拟思考时间
        
        # ========== 📋 执行规划 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.PLAN,
            "制定实现计划", self.name
        )
        
        cot.plan(
            approach="迭代开发 + 单元测试",
            execution_steps=[
                "1. 设计函数签名",
                "2. 实现核心逻辑",
                "3. 添加边界处理",
                "4. 编写测试用例"
            ],
            verification_points=[
                "步骤1: 签名符合需求",
                "步骤2: 逻辑正确",
                "步骤3: 边界不崩溃",
                "步骤4: 测试通过"
            ],
            fallback_plan="如果太复杂，先实现MVP版本"
        )
        
        # ========== 🎲 决策记录 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.DECISION,
            "选择实现方案", self.name
        )
        
        cot.decide(
            decisions=[
                "使用列表推导式（简洁）",
                "使用类型提示（可读性）",
                "添加docstring（维护性）"
            ],
            reasoning="在性能和可读性之间平衡，当前场景数据量不大",
            alternatives_considered=[
                "方案A: 纯循环（快但丑）",
                "方案B: 函数式（酷但难懂）"
            ],
            confidence=85
        )
        
        # ========== ⚙️ 执行过程 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.EXECUTE,
            "编写代码实现 (1/3)", self.name
        )
        
        await asyncio.sleep(0.3)
        
        code = '''def deduplicate(items: list) -> list:
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
'''
        
        self.tracer.add_step(
            task_id, ReasoningStepType.EXECUTE,
            "编写代码实现 (2/3) - 核心逻辑完成", self.name
        )
        
        await asyncio.sleep(0.2)
        
        self.tracer.add_step(
            task_id, ReasoningStepType.EXECUTE,
            "编写代码实现 (3/3) - 测试用例完成", self.name
        )
        
        cot.execute(
            steps_completed=[
                "✓ 设计函数签名",
                "✓ 实现核心逻辑",
                "✓ 添加边界处理",
                "✓ 编写测试用例"
            ],
            unexpected_findings=["发现集合+列表组合效率最佳"]
        )
        
        # ========== ✅ 结果验证 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.VERIFY,
            "验证代码质量", self.name
        )
        
        cot.verify(
            results_delivered=["deduplicate函数", "测试用例", "文档字符串"],
            criteria_met=[
                "✓ 功能正确",
                "✓ 代码清晰",
                "✓ 有类型提示",
                "✓ 有文档"
            ],
            overall_quality=90
        )
        
        # ========== 💭 反思总结 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.REFLECT,
            "总结经验", self.name
        )
        
        cot.reflect(
            key_learnings=["集合+列表组合是Python去重最佳实践"],
            reusable_patterns=["类型提示+docstring模板"],
            would_do_differently="下次先写测试再写实现"
        )
        
        # 导出思维链
        structured_cot = cot.build()
        output_file = f"/tmp/cot_coder_{task_id}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(structured_cot.export("markdown"))
        
        print(f"✅ Coder 完成，思维链已保存到: {output_file}")
        
        return ServiceResult.ok({
            'code': code,
            'cot_file': output_file,
            'quality_score': 90
        })


class ReviewerAgent(ServiceAgent):
    """
    Reviewer Agent - 审查代码质量
    
    思维链重点：
    - 现状分析：识别代码问题
    - 决策：确定问题的严重性
    - 验证：确认改进建议有效
    """
    
    def __init__(self):
        super().__init__("Reviewer", enable_tracing=True)
    
    async def _handle(self, request: Dict[str, Any]) -> ServiceResult:
        task_id = request.get('task_id', 'unknown')
        code = request.get('code', '')
        
        print(f"\n{'='*70}")
        print(f"🔍 Reviewer Agent 开始审查")
        print(f"{'='*70}")
        
        cot = QuickCoT()
        
        # ========== 🎯 任务理解 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.UNDERSTAND,
            "理解审查目标", self.name
        )
        
        cot.understand(
            user_intent="审查代码质量",
            explicit_requirements=["找出bug", "提出改进建议"],
            success_criteria=["找出所有严重问题", "建议具体可行"]
        )
        
        # ========== 🔍 现状分析 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.ANALYZE,
            "分析代码", self.name
        )
        
        issues = []
        
        # 模拟静态分析
        if "def " in code:
            issues.append({
                'line': 1,
                'type': 'style',
                'message': '函数缺少返回值类型检查',
                'severity': 'low'
            })
        
        if "set()" in code:
            issues.append({
                'line': 4,
                'type': 'performance',
                'message': '对于不可哈希对象会失败',
                'severity': 'medium'
            })
        
        cot.analyze(
            available_data=["代码内容", "Python最佳实践"],
            key_observations=[
                f"代码长度: {len(code)} 字符",
                f"发现问题: {len(issues)} 个"
            ],
            potential_issues=[i['message'] for i in issues]
        )
        
        await asyncio.sleep(0.3)  # 模拟审查时间
        
        # ========== 🎲 决策记录 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.DECISION,
            "评估问题严重性", self.name
        )
        
        cot.decide(
            decisions=[
                "性能问题标记为medium（特定场景触发）",
                "风格问题标记为low（非阻塞）"
            ],
            reasoning="主要功能正确，边界情况需要改进",
            confidence=80
        )
        
        # ========== ⚙️ 执行过程 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.EXECUTE,
            "生成审查报告", self.name
        )
        
        review_report = {
            'issues': issues,
            'summary': {
                'total': len(issues),
                'critical': 0,
                'high': 0,
                'medium': 1,
                'low': 1
            },
            'recommendations': [
                "添加对不可哈希对象的处理",
                "考虑使用try-except包装"
            ]
        }
        
        cot.execute(
            steps_completed=[
                "✓ 静态代码分析",
                "✓ 识别潜在问题",
                "✓ 生成审查报告"
            ]
        )
        
        # ========== ✅ 结果验证 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.VERIFY,
            "验证审查完整性", self.name
        )
        
        cot.verify(
            results_delivered=["审查报告", "问题列表", "改进建议"],
            criteria_met=["✓ 找出问题", "✓ 建议具体"],
            overall_quality=85
        )
        
        # ========== 💭 反思总结 ==========
        cot.reflect(
            key_learnings=["集合操作需要考虑元素可哈希性"],
            reusable_patterns=["静态分析checklist"]
        )
        
        # 导出思维链
        structured_cot = cot.build()
        output_file = f"/tmp/cot_reviewer_{task_id}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(structured_cot.export("markdown"))
        
        print(f"✅ Reviewer 完成，思维链已保存到: {output_file}")
        print(f"   发现问题: {len(issues)} 个")
        
        return ServiceResult.ok({
            'review_report': review_report,
            'cot_file': output_file,
            'pass': len([i for i in issues if i['severity'] == 'critical']) == 0
        })


class ReflectorAgent(ServiceAgent):
    """
    Reflector Agent - 反思整个过程
    
    思维链重点：
    - 综合多个 Agent 的输出
    - 提炼跨任务的经验
    - 识别系统性改进点
    """
    
    def __init__(self):
        super().__init__("Reflector", enable_tracing=True)
    
    async def _handle(self, request: Dict[str, Any]) -> ServiceResult:
        task_id = request.get('task_id', 'unknown')
        coder_result = request.get('coder_result', {})
        reviewer_result = request.get('reviewer_result', {})
        
        print(f"\n{'='*70}")
        print(f"💭 Reflector Agent 开始反思")
        print(f"{'='*70}")
        
        cot = QuickCoT()
        
        # ========== 🎯 任务理解 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.UNDERSTAND,
            "综合整个协作过程", self.name
        )
        
        cot.understand(
            user_intent="反思代码开发全流程",
            explicit_requirements=["总结经验", "识别改进点"],
            success_criteria=["提炼可复用模式", "指出系统性问题"]
        )
        
        # ========== 🔍 现状分析 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.ANALYZE,
            "分析协作过程", self.name
        )
        
        coder_quality = coder_result.get('quality_score', 0)
        review_pass = reviewer_result.get('pass', False)
        issues = reviewer_result.get('review_report', {}).get('issues', [])
        
        cot.analyze(
            available_data=[
                f"Coder产出质量: {coder_quality}/100",
                f"审查结果: {'通过' if review_pass else '需改进'}",
                f"发现问题数: {len(issues)}"
            ],
            key_observations=[
                "Coder注重可读性",
                "Reviewer发现边界情况遗漏",
                "协作流程顺畅"
            ]
        )
        
        await asyncio.sleep(0.2)
        
        # ========== 🎲 决策记录 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.DECISION,
            "确定改进优先级", self.name
        )
        
        cot.decide(
            decisions=[
                "优先改进边界情况处理",
                "保持代码可读性优势"
            ],
            reasoning="功能正确性 > 性能 > 风格",
            confidence=90
        )
        
        # ========== ⚙️ 执行过程 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.EXECUTE,
            "生成反思报告", self.name
        )
        
        insights = {
            'coder_strengths': ['代码清晰', '文档完善', '类型提示'],
            'coder_improvements': ['边界情况处理', '测试覆盖'],
            'reviewer_effectiveness': '高',
            'workflow_efficiency': '良好',
            'systemic_issues': ['边界情况容易被忽视']
        }
        
        cot.execute(
            steps_completed=[
                "✓ 分析Coder产出",
                "✓ 评估审查效果",
                "✓ 识别系统问题",
                "✓ 生成改进建议"
            ],
            unexpected_findings=["边界情况处理是普遍问题"]
        )
        
        # ========== ✅ 结果验证 ==========
        self.tracer.add_step(
            task_id, ReasoningStepType.VERIFY,
            "验证反思深度", self.name
        )
        
        cot.verify(
            results_delivered=["反思报告", "改进建议", "可复用模式"],
            criteria_met=["✓ 总结Coder表现", "✓ 评估审查效果", "✓ 提出系统性改进"],
            overall_quality=88
        )
        
        # ========== 💭 反思总结 ==========
        cot.reflect(
            key_learnings=[
                "多Agent协作能提高代码质量",
                "边界情况处理需要checklist",
                "Coder和Reviewer互补效果好"
            ],
            reusable_patterns=[
                "Coder代码模板",
                "Reviewer检查清单",
                "多Agent协作流程"
            ],
            would_do_differently="在需求阶段就明确边界情况要求"
        )
        
        # 导出思维链
        structured_cot = cot.build()
        output_file = f"/tmp/cot_reflector_{task_id}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(structured_cot.export("markdown"))
        
        print(f"✅ Reflector 完成，思维链已保存到: {output_file}")
        
        return ServiceResult.ok({
            'insights': insights,
            'cot_file': output_file
        })


async def run_multi_agent_workflow():
    """
    运行完整的多 Agent 协作工作流
    """
    print("\n" + "="*70)
    print("多 Agent 协作 + 结构化思维链 演示")
    print("="*70)
    print("\n场景：实现一个去重函数，Coder编写，Reviewer审查，Reflector反思")
    print("\n每个 Agent 都会生成：")
    print("  1. 实时推理追踪（步骤可见）")
    print("  2. 结构化思维链文档（完整记录）")
    
    # 生成任务ID
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ========== Phase 1: Coder ==========
    print("\n" + "🚀"*35)
    print("Phase 1/3: Coder Agent 编写代码")
    print("🚀"*35)
    
    coder = CoderAgent()
    coder_result = await coder.call({
        'task_id': f"{task_id}_coder",
        'task_type': 'code-implementation',
        'feature': '列表去重（保持顺序）',
        'metadata': {'priority': 'high'}
    })
    
    if not coder_result.success:
        print(f"❌ Coder 失败: {coder_result.error}")
        return False
    
    print(f"\n📄 生成的代码:\n{coder_result.data['code']}")
    
    # ========== Phase 2: Reviewer ==========
    print("\n" + "🔍"*35)
    print("Phase 2/3: Reviewer Agent 审查代码")
    print("🔍"*35)
    
    reviewer = ReviewerAgent()
    reviewer_result = await reviewer.call({
        'task_id': f"{task_id}_reviewer",
        'task_type': 'code-review',
        'code': coder_result.data['code'],
        'metadata': {'review_depth': 'standard'}
    })
    
    if not reviewer_result.success:
        print(f"❌ Reviewer 失败: {reviewer_result.error}")
        return False
    
    # ========== Phase 3: Reflector ==========
    print("\n" + "💭"*35)
    print("Phase 3/3: Reflector Agent 反思总结")
    print("💭"*35)
    
    reflector = ReflectorAgent()
    reflector_result = await reflector.call({
        'task_id': f"{task_id}_reflector",
        'task_type': 'reflection',
        'coder_result': coder_result.data,
        'reviewer_result': reviewer_result.data,
        'metadata': {'scope': 'full-workflow'}
    })
    
    if not reflector_result.success:
        print(f"❌ Reflector 失败: {reflector_result.error}")
        return False
    
    # ========== 汇总报告 ==========
    print("\n" + "="*70)
    print("📊 协作完成 - 思维链文档汇总")
    print("="*70)
    
    files = [
        ("Coder", coder_result.data['cot_file']),
        ("Reviewer", reviewer_result.data['cot_file']),
        ("Reflector", reflector_result.data['cot_file'])
    ]
    
    for agent_name, file_path in files:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # 提取关键信息
        lines = content.split('\n')
        completion_line = [l for l in lines if '完成度:' in l]
        sections_line = [l for l in lines if '章节:' in l]
        
        print(f"\n📄 {agent_name}:")
        print(f"   文件: {file_path}")
        if completion_line:
            print(f"   {completion_line[0].strip()}")
        print(f"   文档大小: {len(content)} 字符")
    
    # 导出所有追踪记录
    all_traces_file = f"/tmp/wdai_all_traces_{task_id}.json"
    tracer.export_all(all_traces_file)
    
    print(f"\n💾 所有追踪记录已导出到: {all_traces_file}")
    
    # 显示 Reflector 的关键洞察
    print("\n" + "="*70)
    print("💡 Reflector 关键洞察")
    print("="*70)
    
    insights = reflector_result.data['insights']
    print(f"\nCoder 优势: {', '.join(insights['coder_strengths'])}")
    print(f"Coder 改进点: {', '.join(insights['coder_improvements'])}")
    print(f"审查效果: {insights['reviewer_effectiveness']}")
    print(f"系统性问题: {', '.join(insights['systemic_issues'])}")
    
    print("\n" + "="*70)
    print("✅ 多 Agent 协作完成！")
    print("="*70)
    print("\n每个 Agent 的完整思维链已保存，你可以：")
    print("  1. 查看 /tmp/cot_*.md 了解每个 Agent 的思考过程")
    print("  2. 查看 /tmp/wdai_all_traces_*.json 获取结构化数据")
    print("  3. 对比不同 Agent 对同一任务的不同视角")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_multi_agent_workflow())
    sys.exit(0 if success else 1)
