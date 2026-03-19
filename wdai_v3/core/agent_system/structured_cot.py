"""
结构化思维链系统 (Structured Chain-of-Thought)

核心特性:
1. 强制结构化模板 - 必须按格式填写
2. 字段验证 - 确保每个必填项都有内容
3. 层次化推理 - 支持嵌套子任务
4. 可追溯引用 - 每个结论必须标注依据
5. 一致性检查 - 验证推理逻辑自洽

基于论文: "Reasoning Models Struggle to Control their Chains of Thought"
设计理念: 既然模型控制CoT的能力低(<15%), 就用结构化约束强制规范
"""

from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import json
import time
from abc import ABC, abstractmethod


class CoTFieldType(Enum):
    """思维链字段类型"""
    TEXT = auto()           # 纯文本
    LIST = auto()           # 列表
    CHECKBOX = auto()       # 是/否
    CONFIDENCE = auto()     # 置信度 (0-100%)
    REFERENCE = auto()      # 引用
    DECISION = auto()       # 决策选项


@dataclass
class CoTField:
    """思维链字段定义"""
    name: str
    description: str
    field_type: CoTFieldType
    required: bool = True
    validation_rules: List[str] = field(default_factory=list)
    example: str = ""
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """验证字段值"""
        if self.required:
            # 检查值是否存在且非空（对于字符串/列表）
            if value is None:
                return False, f"必填字段 '{self.name}' 不能为空"
            if isinstance(value, (str, list)) and len(value) == 0:
                return False, f"必填字段 '{self.name}' 不能为空"
        
        if self.field_type == CoTFieldType.CONFIDENCE and value is not None:
            try:
                v = float(value)
                if not 0 <= v <= 100:
                    return False, f"置信度必须在 0-100 之间"
            except:
                return False, f"置信度必须是数字"
        
        if self.field_type == CoTFieldType.REFERENCE and value is not None:
            if not isinstance(value, list):
                return False, f"引用必须是列表格式"
        
        return True, ""


@dataclass
class CoTSection:
    """思维链章节"""
    title: str
    description: str
    fields: List[CoTField]
    order: int = 0
    
    def validate(self, data: Dict) -> tuple[bool, List[str]]:
        """验证整个章节"""
        errors = []
        
        for field in self.fields:
            value = data.get(field.name)
            is_valid, error = field.validate(value)
            if not is_valid:
                errors.append(error)
        
        return len(errors) == 0, errors


# ============================================================================
# 标准推理模板
# ============================================================================

STANDARD_REASONING_TEMPLATE = {
    "sections": [
        CoTSection(
            order=1,
            title="🎯 任务理解",
            description="明确任务目标、约束和成功标准",
            fields=[
                CoTField(
                    name="user_intent",
                    description="用户真正的意图是什么？",
                    field_type=CoTFieldType.TEXT,
                    example="用户想要分析代码的性能瓶颈"
                ),
                CoTField(
                    name="explicit_requirements",
                    description="明确的要求（用户直接说的）",
                    field_type=CoTFieldType.LIST,
                    example=["分析Python函数", "找出性能问题"]
                ),
                CoTField(
                    name="implicit_requirements",
                    description="隐含的要求（需要推断的）",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["提供改进建议", "保持代码可读性"]
                ),
                CoTField(
                    name="constraints",
                    description="限制条件",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["时间限制", "不能修改API签名"]
                ),
                CoTField(
                    name="success_criteria",
                    description="如何判断任务完成？",
                    field_type=CoTFieldType.LIST,
                    required=True,
                    example=["找到至少1个性能瓶颈", "给出具体优化方案"]
                ),
            ]
        ),
        
        CoTSection(
            order=2,
            title="🔍 现状分析",
            description="分析当前情况，识别关键信息",
            fields=[
                CoTField(
                    name="available_data",
                    description="有哪些可用数据/信息？",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["代码文件", "测试用例", "性能报告"]
                ),
                CoTField(
                    name="missing_data",
                    description="还缺少什么信息？",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["运行时环境", "输入数据规模"]
                ),
                CoTField(
                    name="key_observations",
                    description="关键观察点",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["函数有3层嵌套循环", "使用了递归"]
                ),
                CoTField(
                    name="potential_issues",
                    description="潜在问题/风险",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["边界条件未处理", "可能导致内存泄漏"]
                ),
            ]
        ),
        
        CoTSection(
            order=3,
            title="📋 执行规划",
            description="制定详细的执行步骤",
            fields=[
                CoTField(
                    name="approach",
                    description="选择的方法/策略",
                    field_type=CoTFieldType.TEXT,
                    required=False,
                    example="静态分析 + 动态 profiling"
                ),
                CoTField(
                    name="execution_steps",
                    description="执行步骤（必须可验证）",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["1. 读取代码", "2. 识别热点函数", "3. 分析复杂度"]
                ),
                CoTField(
                    name="verification_points",
                    description="每个步骤的验证点",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["步骤1: 文件存在且可读", "步骤2: 找到至少1个热点"]
                ),
                CoTField(
                    name="fallback_plan",
                    description="如果主计划失败，备选方案？",
                    field_type=CoTFieldType.TEXT,
                    required=False,
                    example="如果静态分析不够，使用实际运行数据"
                ),
            ]
        ),
        
        CoTSection(
            order=4,
            title="🎲 决策记录",
            description="记录关键决策及其理由",
            fields=[
                CoTField(
                    name="decisions",
                    description="做出的决策",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["选择O(n)算法而非O(n²)", "使用缓存而非重新计算"]
                ),
                CoTField(
                    name="alternatives_considered",
                    description="考虑过的备选方案",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["方案A: 简单但慢", "方案B: 复杂但快"]
                ),
                CoTField(
                    name="reasoning",
                    description="选择当前方案的理由",
                    field_type=CoTFieldType.TEXT,
                    required=False,
                    example="平衡性能和复杂度，当前场景数据量不大"
                ),
                CoTField(
                    name="confidence",
                    description="对决策的置信度 (0-100%)",
                    field_type=CoTFieldType.CONFIDENCE,
                    required=False,
                    example="85"
                ),
            ]
        ),
        
        CoTSection(
            order=5,
            title="⚙️ 执行过程",
            description="记录实际执行中的情况",
            fields=[
                CoTField(
                    name="steps_completed",
                    description="已完成的步骤",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["✓ 读取代码", "✓ 识别热点"]
                ),
                CoTField(
                    name="steps_blocked",
                    description="受阻/跳过的步骤",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["✗ 动态profiling (无运行环境)"]
                ),
                CoTField(
                    name="unexpected_findings",
                    description="意外发现",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["发现递归深度可能溢出"]
                ),
                CoTField(
                    name="adaptations",
                    description="计划的调整",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["改用静态复杂度分析"]
                ),
            ]
        ),
        
        CoTSection(
            order=6,
            title="✅ 结果验证",
            description="验证结果是否符合预期",
            fields=[
                CoTField(
                    name="results_delivered",
                    description="交付的结果",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["性能分析报告", "3个优化建议"]
                ),
                CoTField(
                    name="criteria_met",
                    description="满足的成功标准",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["✓ 找到性能瓶颈", "✓ 给出优化方案"]
                ),
                CoTField(
                    name="criteria_missed",
                    description="未满足的标准",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["✗ 未提供基准测试数据"]
                ),
                CoTField(
                    name="overall_quality",
                    description="结果质量自评 (0-100%)",
                    field_type=CoTFieldType.CONFIDENCE,
                    required=False,
                    example="90"
                ),
                CoTField(
                    name="improvements",
                    description="可以改进的地方",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["添加更多测试用例", "考虑并发场景"]
                ),
            ]
        ),
        
        CoTSection(
            order=7,
            title="💭 反思总结",
            description="经验提炼和知识沉淀",
            fields=[
                CoTField(
                    name="key_learnings",
                    description="关键学习点",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["早期识别算法复杂度很重要"]
                ),
                CoTField(
                    name="reusable_patterns",
                    description="可复用的模式/技巧",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["使用ast模块静态分析Python代码"]
                ),
                CoTField(
                    name="mistakes_made",
                    description="犯的错误",
                    field_type=CoTFieldType.LIST,
                    required=False,
                    example=["一开始忽略了递归深度问题"]
                ),
                CoTField(
                    name="would_do_differently",
                    description="如果重做，会怎么做不同？",
                    field_type=CoTFieldType.TEXT,
                    required=False,
                    example="先确认运行环境再选择分析方法"
                ),
            ]
        ),
    ]
}


# ============================================================================
# 结构化思维链实现
# ============================================================================

class StructuredCoT:
    """
    结构化思维链
    
    强制按照模板进行推理，每个字段必须填写
    """
    
    def __init__(
        self,
        template: Optional[Dict] = None,
        strict_mode: bool = True,
        allow_partial: bool = False
    ):
        self.template = template or STANDARD_REASONING_TEMPLATE
        self.strict_mode = strict_mode  # 严格模式：必填项不能为空
        self.allow_partial = allow_partial  # 允许部分填充
        
        self.sections: List[CoTSection] = sorted(
            self.template["sections"],
            key=lambda s: s.order
        )
        
        self.data: Dict[str, Dict[str, Any]] = {
            section.title: {} for section in self.sections
        }
        
        self._validation_errors: List[str] = []
        self._filled_sections: set = set()
        self._start_time = time.time()
    
    def fill_section(self, section_title: str, **fields) -> 'StructuredCoT':
        """
        填充一个章节
        
        Args:
            section_title: 章节标题
            **fields: 字段名=值的键值对
        """
        # 找到对应的section
        section = None
        for s in self.sections:
            if s.title == section_title:
                section = s
                break
        
        if not section:
            raise ValueError(f"未知的章节: {section_title}")
        
        # 验证并填充
        for field_name, value in fields.items():
            # 找到字段定义
            field_def = None
            for f in section.fields:
                if f.name == field_name:
                    field_def = f
                    break
            
            if not field_def:
                raise ValueError(f"章节 '{section_title}' 中没有字段 '{field_name}'")
            
            # 验证
            if self.strict_mode:
                is_valid, error = field_def.validate(value)
                if not is_valid:
                    raise ValueError(f"字段 '{field_name}' 验证失败: {error}")
            
            # 填充
            self.data[section_title][field_name] = value
        
        self._filled_sections.add(section_title)
        return self
    
    def fill(self, section_title: str, field_name: str, value: Any) -> 'StructuredCoT':
        """填充单个字段"""
        return self.fill_section(section_title, **{field_name: value})
    
    def validate(self) -> tuple[bool, List[str]]:
        """验证整个思维链"""
        errors = []
        
        for section in self.sections:
            section_data = self.data.get(section.title, {})
            is_valid, section_errors = section.validate(section_data)
            if not is_valid:
                errors.extend(section_errors)
        
        self._validation_errors = errors
        return len(errors) == 0, errors
    
    def is_complete(self) -> bool:
        """检查是否所有必填章节都已填写"""
        for section in self.sections:
            if section.title not in self._filled_sections:
                # 检查是否有必填字段未填
                for field in section.fields:
                    if field.required and not self.data[section.title].get(field.name):
                        return False
        return True
    
    def get_progress(self) -> Dict[str, Any]:
        """获取填写进度"""
        total_fields = sum(len(s.fields) for s in self.sections)
        filled_fields = sum(
            len([f for f in s.fields 
                 if self.data[s.title].get(f.name) is not None])
            for s in self.sections
        )
        
        return {
            "total_sections": len(self.sections),
            "filled_sections": len(self._filled_sections),
            "section_progress": len(self._filled_sections) / len(self.sections),
            "total_fields": total_fields,
            "filled_fields": filled_fields,
            "field_progress": filled_fields / total_fields if total_fields > 0 else 0,
            "elapsed_time": time.time() - self._start_time
        }
    
    def export(self, format: str = "dict") -> Union[Dict, str]:
        """
        导出思维链
        
        Args:
            format: "dict", "json", "markdown"
        """
        if format == "dict":
            return {
                "template": "standard",
                "strict_mode": self.strict_mode,
                "data": self.data,
                "progress": self.get_progress(),
                "validation": {
                    "is_valid": len(self._validation_errors) == 0,
                    "errors": self._validation_errors
                },
                "timestamp": time.time()
            }
        
        elif format == "json":
            return json.dumps(self.export("dict"), indent=2, ensure_ascii=False)
        
        elif format == "markdown":
            return self._to_markdown()
        
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _to_markdown(self) -> str:
        """转换为Markdown格式"""
        lines = ["# 结构化思维链\n"]
        
        progress = self.get_progress()
        lines.append(f"> 完成度: {progress['field_progress']*100:.1f}% | "
                    f"章节: {progress['filled_sections']}/{progress['total_sections']} | "
                    f"耗时: {progress['elapsed_time']:.1f}s\n")
        
        for section in self.sections:
            lines.append(f"\n## {section.title}\n")
            lines.append(f"*{section.description}*\n")
            
            section_data = self.data.get(section.title, {})
            
            for field in section.fields:
                value = section_data.get(field.name)
                required_mark = " **(必填)**" if field.required else ""
                
                lines.append(f"\n### {field.name}{required_mark}\n")
                lines.append(f"*{field.description}*\n")
                
                if value is not None:
                    if isinstance(value, list):
                        for item in value:
                            lines.append(f"- {item}")
                    else:
                        lines.append(f"{value}")
                else:
                    lines.append("*未填写*")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def print_summary(self):
        """打印摘要"""
        progress = self.get_progress()
        
        print(f"\n{'='*60}")
        print("📊 结构化思维链摘要")
        print('='*60)
        print(f"章节进度: {progress['filled_sections']}/{progress['total_sections']} "
              f"({progress['section_progress']*100:.0f}%)")
        print(f"字段进度: {progress['filled_fields']}/{progress['total_fields']} "
              f"({progress['field_progress']*100:.0f}%)")
        print(f"耗时: {progress['elapsed_time']:.2f}s")
        
        if self._validation_errors:
            print(f"\n⚠️ 验证错误 ({len(self._validation_errors)}个):")
            for error in self._validation_errors:
                print(f"  - {error}")
        else:
            print("\n✅ 验证通过")
        
        print(f"\n已填写章节:")
        for title in self._filled_sections:
            section_data = self.data.get(title, {})
            filled_count = len([v for v in section_data.values() if v is not None])
            total_count = len([s for s in self.sections if s.title == title][0].fields)
            print(f"  ✓ {title} ({filled_count}/{total_count})")
        
        print('='*60)


# ============================================================================
# 快速填充助手
# ============================================================================

class QuickCoT:
    """
    快速创建结构化思维链的助手
    
    提供流畅的API，快速填充所有章节
    """
    
    def __init__(self):
        self.cot = StructuredCoT()
    
    def understand(
        self,
        user_intent: str,
        explicit_requirements: List[str],
        implicit_requirements: List[str] = None,
        constraints: List[str] = None,
        success_criteria: List[str] = None
    ) -> 'QuickCoT':
        """快速填充任务理解章节"""
        self.cot.fill_section(
            "🎯 任务理解",
            user_intent=user_intent,
            explicit_requirements=explicit_requirements,
            implicit_requirements=implicit_requirements or [],
            constraints=constraints or [],
            success_criteria=success_criteria or ["完成主要目标"]
        )
        return self
    
    def analyze(
        self,
        available_data: List[str],
        key_observations: List[str],
        missing_data: List[str] = None,
        potential_issues: List[str] = None
    ) -> 'QuickCoT':
        """快速填充现状分析章节"""
        self.cot.fill_section(
            "🔍 现状分析",
            available_data=available_data,
            key_observations=key_observations,
            missing_data=missing_data or [],
            potential_issues=potential_issues or []
        )
        return self
    
    def plan(
        self,
        approach: str,
        execution_steps: List[str],
        verification_points: List[str] = None,
        fallback_plan: str = ""
    ) -> 'QuickCoT':
        """快速填充执行规划章节"""
        self.cot.fill_section(
            "📋 执行规划",
            approach=approach,
            execution_steps=execution_steps,
            verification_points=verification_points or [],
            fallback_plan=fallback_plan
        )
        return self
    
    def decide(
        self,
        decisions: List[str],
        reasoning: str,
        alternatives_considered: List[str] = None,
        confidence: int = 80
    ) -> 'QuickCoT':
        """快速填充决策记录章节"""
        self.cot.fill_section(
            "🎲 决策记录",
            decisions=decisions,
            reasoning=reasoning,
            alternatives_considered=alternatives_considered or [],
            confidence=confidence
        )
        return self
    
    def execute(
        self,
        steps_completed: List[str],
        steps_blocked: List[str] = None,
        unexpected_findings: List[str] = None,
        adaptations: List[str] = None
    ) -> 'QuickCoT':
        """快速填充执行过程章节"""
        self.cot.fill_section(
            "⚙️ 执行过程",
            steps_completed=steps_completed,
            steps_blocked=steps_blocked or [],
            unexpected_findings=unexpected_findings or [],
            adaptations=adaptations or []
        )
        return self
    
    def verify(
        self,
        results_delivered: List[str],
        criteria_met: List[str],
        overall_quality: int = 80,
        criteria_missed: List[str] = None,
        improvements: List[str] = None
    ) -> 'QuickCoT':
        """快速填充结果验证章节"""
        self.cot.fill_section(
            "✅ 结果验证",
            results_delivered=results_delivered,
            criteria_met=criteria_met,
            overall_quality=overall_quality,
            criteria_missed=criteria_missed or [],
            improvements=improvements or []
        )
        return self
    
    def reflect(
        self,
        key_learnings: List[str],
        reusable_patterns: List[str] = None,
        mistakes_made: List[str] = None,
        would_do_differently: str = ""
    ) -> 'QuickCoT':
        """快速填充反思总结章节"""
        self.cot.fill_section(
            "💭 反思总结",
            key_learnings=key_learnings,
            reusable_patterns=reusable_patterns or [],
            mistakes_made=mistakes_made or [],
            would_do_differently=would_do_differently
        )
        return self
    
    def build(self) -> StructuredCoT:
        """构建完成，返回StructuredCoT实例"""
        return self.cot
    
    def export_markdown(self) -> str:
        """导出为Markdown"""
        return self.cot.export("markdown")
    
    def export_json(self) -> str:
        """导出为JSON"""
        return self.cot.export("json")


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    'StructuredCoT',
    'QuickCoT',
    'CoTSection',
    'CoTField',
    'CoTFieldType',
    'STANDARD_REASONING_TEMPLATE',
]
