"""
Tool-DC Data Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum


class ToolParamType(Enum):
    """工具参数类型"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParam:
    """工具参数定义"""
    name: str
    type: ToolParamType
    description: str = ""
    required: bool = False
    default: Any = None
    enum: Optional[List[Any]] = None


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: List[ToolParam] = field(default_factory=list)
    required_params: List[str] = field(default_factory=list)
    
    def get_param(self, name: str) -> Optional[ToolParam]:
        """获取参数定义"""
        for param in self.parameters:
            if param.name == name:
                return param
        return None
    
    def to_schema(self) -> Dict[str, Any]:
        """转换为 JSON Schema 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.type.value,
                        "description": p.description,
                        **({"enum": p.enum} if p.enum else {})
                    } for p in self.parameters
                },
                "required": self.required_params
            }
        }


@dataclass
class ToolCall:
    """工具调用"""
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # 置信度
    source_group: Optional[int] = None  # 来自哪个组
    
    def __str__(self) -> str:
        args_str = ", ".join(f"{k}={repr(v)}" for k, v in self.arguments.items())
        return f"{self.name}({args_str})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "arguments": self.arguments,
            "confidence": self.confidence
        }


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    tool_call: ToolCall
    errors: List[str] = field(default_factory=list)
    
    @property
    def error_message(self) -> str:
        return "; ".join(self.errors) if self.errors else ""


@dataclass
class ToolDCResult:
    """Tool-DC 完整执行结果"""
    final_call: Optional[ToolCall] = None
    try_candidates: List[ToolCall] = field(default_factory=list)
    valid_candidates: List[ToolCall] = field(default_factory=list)
    groups_processed: int = 0
    validation_passed: int = 0
    validation_failed: int = 0
    execution_time_ms: float = 0.0
    fallback_used: bool = False  # 是否使用了降级策略
    
    @property
    def success(self) -> bool:
        return self.final_call is not None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "final_call": self.final_call.to_dict() if self.final_call else None,
            "try_candidates": [c.to_dict() for c in self.try_candidates],
            "valid_candidates": [c.to_dict() for c in self.valid_candidates],
            "groups_processed": self.groups_processed,
            "validation_passed": self.validation_passed,
            "validation_failed": self.validation_failed,
            "execution_time_ms": self.execution_time_ms,
            "fallback_used": self.fallback_used
        }
