"""
认知安全系统 v1.0 (Cognitive Safety System)

防止滚雪球式编造、过度自信、关键决策偷懒

核心机制:
1. 强制检查点 - 每个关键决策前必须验证
2. 工具使用规范 - 外部数据必须读取
3. 不确定性显化 - 所有推测必须标注
4. 违规阻断 - 危险操作自动拦截
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
import json
import time
from pathlib import Path


class SafetyLevel(Enum):
    """安全级别"""
    CRITICAL = auto()   # 必须验证，否则阻断
    HIGH = auto()       # 强烈建议验证
    MEDIUM = auto()     # 建议验证
    LOW = auto()        # 可选验证


class ViolationType(Enum):
    """违规类型"""
    UNVERIFIED_EXTERNAL_DATA = auto()  # 未验证外部数据
    FABRICATED_CONTENT = auto()        # 编造内容
    UNCERTAINTY_NOT_EXPLICIT = auto()  # 不确定性未显化
    ABSOLUTE_STATEMENT = auto()        # 绝对化表述
    TOOL_AVAILABLE_BUT_UNUSED = auto() # 有工具却不用


@dataclass
class SafetyCheck:
    """安全检查项"""
    name: str
    description: str
    check_function: Callable[[str, Dict], Tuple[bool, str]]
    level: SafetyLevel
    auto_fix: bool = False


@dataclass  
class Violation:
    """违规记录"""
    type: ViolationType
    message: str
    timestamp: float
    context: str
    severity: int  # 1-5


class CognitiveSafetySystem:
    """
    认知安全系统 - 防止推理偏差和编造
    
    使用方式:
    1. 创建检查点
    2. 运行检查
    3. 根据结果决定阻断或放行
    """
    
    def __init__(self):
        self.checks: List[SafetyCheck] = []
        self.violations: List[Violation] = []
        self._register_default_checks()
        
    def _register_default_checks(self):
        """注册默认安全检查"""
        
        # 检查1: 外部数据引用验证
        self.add_check(SafetyCheck(
            name="external_data_verification",
            description="检查是否引用了未验证的外部数据（图片、文件等）",
            check_function=self._check_external_data,
            level=SafetyLevel.CRITICAL,
            auto_fix=False
        ))
        
        # 检查2: 编造内容检测
        self.add_check(SafetyCheck(
            name="fabrication_detection",
            description="检测是否包含编造的具体细节",
            check_function=self._check_fabrication,
            level=SafetyLevel.CRITICAL,
            auto_fix=False
        ))
        
        # 检查3: 不确定性显化
        self.add_check(SafetyCheck(
            name="uncertainty_explicit",
            description="检查不确定性是否已显化标注",
            check_function=self._check_uncertainty_explicit,
            level=SafetyLevel.HIGH,
            auto_fix=True
        ))
        
        # 检查4: 绝对化表述
        self.add_check(SafetyCheck(
            name="absolute_statement_check",
            description="检查是否使用了绝对化表述（'一定'、'肯定'等）",
            check_function=self._check_absolute_statements,
            level=SafetyLevel.MEDIUM,
            auto_fix=True
        ))
        
        # 检查5: 工具使用检查
        self.add_check(SafetyCheck(
            name="tool_usage_check",
            description="检查是否有可用工具但未使用",
            check_function=self._check_tool_usage,
            level=SafetyLevel.CRITICAL,
            auto_fix=False
        ))
    
    def add_check(self, check: SafetyCheck):
        """添加安全检查"""
        self.checks.append(check)
    
    def validate_response(
        self, 
        response: str, 
        context: Dict[str, Any],
        available_tools: List[str] = None
    ) -> Dict[str, Any]:
        """
        验证回复是否安全
        
        Args:
            response: 待发送的回复
            context: 上下文信息（包含是否已读取文件等）
            available_tools: 可用工具列表
            
        Returns:
            {
                'is_safe': bool,
                'violations': List[Violation],
                'corrected_response': str,
                'block_reason': Optional[str]
            }
        """
        violations = []
        corrected = response
        
        for check in self.checks:
            is_passed, message = check.check_function(corrected, context)
            
            if not is_passed:
                violation = Violation(
                    type=self._get_violation_type(check.name),
                    message=message,
                    timestamp=time.time(),
                    context=response[:200],
                    severity=self._get_severity(check.level)
                )
                violations.append(violation)
                
                # 尝试自动修复
                if check.auto_fix:
                    corrected = self._auto_fix(corrected, check.name)
        
        # 判断阻断
        critical_violations = [v for v in violations if v.severity >= 4]
        is_safe = len(critical_violations) == 0
        
        block_reason = None
        if not is_safe:
            block_reason = f"发现 {len(critical_violations)} 个严重违规: " + \
                          "; ".join([v.message for v in critical_violations[:3]])
        
        return {
            'is_safe': is_safe,
            'violations': violations,
            'corrected_response': corrected,
            'block_reason': block_reason
        }
    
    def _check_external_data(self, response: str, context: Dict) -> Tuple[bool, str]:
        """检查外部数据引用"""
        # 检查是否引用了图片但未读取
        if '图片' in response or '截图' in response:
            if not context.get('image_read', False):
                return False, "引用了图片内容但未读取图片（image_read=False）"
        
        # 检查是否引用了文件但未读取
        if '文件显示' in response or '根据文件' in response:
            if not context.get('file_read', False):
                return False, "引用了文件内容但未读取文件"
        
        return True, ""
    
    def _check_fabrication(self, response: str, context: Dict) -> Tuple[bool, str]:
        """检测编造内容"""
        # 检测模式：过于具体的对话、细节，但没有来源
        fabrication_indicators = [
            # 具体对话引用但没有来源
            '"' in response and '说' in response and not context.get('has_quote_source', False),
            # 具体细节（数字、时间）但没有依据
            any(char.isdigit() for char in response) and '根据' not in response,
        ]
        
        if any(fabrication_indicators):
            return False, "包含可能编造的具体细节，缺乏明确来源"
        
        return True, ""
    
    def _check_uncertainty_explicit(self, response: str, context: Dict) -> Tuple[bool, str]:
        """检查不确定性是否显化"""
        # 如果包含推测性词汇，检查是否显化
        speculative_words = ['可能', '也许', '推测', '猜测', '应该']
        certainty_words = ['肯定', '一定', '绝对', '毫无疑问']
        
        has_speculative = any(word in response for word in speculative_words)
        has_certainty = any(word in response for word in certainty_words)
        
        # 如果用了绝对化词汇，但没有验证，警告
        if has_certainty and not context.get('verified', False):
            return False, "使用了绝对化表述，但未验证"
        
        return True, ""
    
    def _check_absolute_statements(self, response: str, context: Dict) -> Tuple[bool, str]:
        """检查绝对化表述"""
        absolute_words = ['肯定', '一定', '绝对', '毫无疑问', '必然']
        
        for word in absolute_words:
            if word in response:
                return False, f"使用了绝对化词汇'{word}'，建议改为'可能'、'推测'等"
        
        return True, ""
    
    def _check_tool_usage(self, response: str, context: Dict) -> Tuple[bool, str]:
        """检查工具使用情况"""
        # 如果提到了文件/图片，但没用工具
        if '文件' in response and not context.get('file_read', False):
            if context.get('has_read_tool', False):
                return False, "有read工具可用但未使用来读取文件"
        
        return True, ""
    
    def _auto_fix(self, response: str, check_name: str) -> str:
        """自动修复"""
        if check_name == "absolute_statement_check":
            # 替换绝对化词汇
            replacements = {
                '肯定': '推测',
                '一定': '可能',
                '绝对': '相对',
                '毫无疑问': '可能',
            }
            for old, new in replacements.items():
                response = response.replace(old, new)
        
        elif check_name == "uncertainty_explicit":
            # 添加不确定性前缀
            if not response.startswith(('我不确定', '我推测', '可能')):
                response = "我推测：" + response
        
        return response
    
    def _get_violation_type(self, check_name: str) -> ViolationType:
        """获取违规类型"""
        mapping = {
            "external_data_verification": ViolationType.UNVERIFIED_EXTERNAL_DATA,
            "fabrication_detection": ViolationType.FABRICATED_CONTENT,
            "uncertainty_explicit": ViolationType.UNCERTAINTY_NOT_EXPLICIT,
            "absolute_statement_check": ViolationType.ABSOLUTE_STATEMENT,
            "tool_usage_check": ViolationType.TOOL_AVAILABLE_BUT_UNUSED,
        }
        return mapping.get(check_name, ViolationType.FABRICATED_CONTENT)
    
    def _get_severity(self, level: SafetyLevel) -> int:
        """获取严重级别"""
        mapping = {
            SafetyLevel.CRITICAL: 5,
            SafetyLevel.HIGH: 3,
            SafetyLevel.MEDIUM: 2,
            SafetyLevel.LOW: 1,
        }
        return mapping.get(level, 3)
    
    def record_violation(self, violation: Violation):
        """记录违规"""
        self.violations.append(violation)
        self._save_violation(violation)
    
    def _save_violation(self, violation: Violation):
        """保存违规到文件"""
        log_dir = Path("/root/.openclaw/workspace/.cognitive-safety")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "violations.jsonl"
        
        record = {
            'type': violation.type.name,
            'message': violation.message,
            'timestamp': violation.timestamp,
            'severity': violation.severity,
            'context': violation.context[:100]
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    def get_violation_stats(self) -> Dict:
        """获取违规统计"""
        stats = {}
        for v in self.violations:
            v_type = v.type.name
            stats[v_type] = stats.get(v_type, 0) + 1
        return stats


# 便捷函数
def create_safety_system() -> CognitiveSafetySystem:
    """创建认知安全系统实例"""
    return CognitiveSafetySystem()


def validate_before_send(
    response: str, 
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    发送前快速验证
    
    使用示例:
    ```python
    result = validate_before_send(
        response="根据图片，这是B站评论...",
        context={'image_read': False}  # 关键！标记图片是否已读
    )
    
    if not result['is_safe']:
        print(f"阻断原因: {result['block_reason']}")
        # 必须修正后才能发送
    ```
    """
    system = create_safety_system()
    return system.validate_response(response, context)


# 预设的上下文模板
CONTEXT_TEMPLATES = {
    'image_not_read': {
        'image_read': False,
        'file_read': False,
        'verified': False,
        'has_read_tool': True,
    },
    'image_read': {
        'image_read': True,
        'file_read': False,
        'verified': True,
        'has_read_tool': True,
    },
    'file_read': {
        'image_read': False,
        'file_read': True,
        'verified': True,
        'has_read_tool': True,
    },
}


__all__ = [
    'CognitiveSafetySystem',
    'SafetyLevel',
    'ViolationType',
    'SafetyCheck',
    'Violation',
    'create_safety_system',
    'validate_before_send',
    'CONTEXT_TEMPLATES',
]
