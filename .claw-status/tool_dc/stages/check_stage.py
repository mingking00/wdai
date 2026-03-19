"""
Tool-DC Check Stage: Schema Consistency Validation
"""

import logging
from typing import List, Dict, Any, Union

from ..models import Tool, ToolCall, ToolParamType, ValidationResult
from ..config import ToolDCConfig

logger = logging.getLogger(__name__)


class CheckStage:
    """
    Check Stage: Schema 一致性验证
    
    基于规则的验证器，零幻觉，确保：
    1. 函数名存在
    2. 必填参数完整
    3. 数据类型匹配
    """
    
    def __init__(self, config: ToolDCConfig):
        self.config = config
    
    def validate(
        self, 
        tool_call: ToolCall, 
        available_tools: List[Tool]
    ) -> ValidationResult:
        """
        验证单个工具调用
        
        Args:
            tool_call: 工具调用
            available_tools: 所有可用工具
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        
        # 1. 函数名存在性验证
        if self.config.validate_function_name:
            tool = self._find_tool(tool_call.name, available_tools)
            if not tool:
                errors.append(f"函数 '{tool_call.name}' 不存在于工具库中")
                return ValidationResult(is_valid=False, tool_call=tool_call, errors=errors)
        else:
            tool = self._find_tool(tool_call.name, available_tools)
        
        if not tool:
            # 如果工具不存在，跳过后续验证
            return ValidationResult(is_valid=False, tool_call=tool_call, errors=errors)
        
        # 2. 必填参数验证
        if self.config.validate_required_params:
            missing = self._check_required_params(tool_call, tool)
            if missing:
                errors.append(f"缺少必填参数: {', '.join(missing)}")
        
        # 3. 数据类型验证
        if self.config.validate_data_types:
            type_errors = self._check_data_types(tool_call, tool)
            if type_errors:
                errors.extend(type_errors)
        
        is_valid = len(errors) == 0
        
        if self.config.verbose_logging:
            if is_valid:
                logger.debug(f"验证通过: {tool_call}")
            else:
                logger.warning(f"验证失败: {tool_call} - {errors}")
        
        return ValidationResult(
            is_valid=is_valid,
            tool_call=tool_call,
            errors=errors
        )
    
    def batch_validate(
        self, 
        candidates: List[ToolCall], 
        tools: List[Tool]
    ) -> List[ToolCall]:
        """
        批量验证候选调用
        
        Args:
            candidates: 候选调用列表
            tools: 可用工具列表
            
        Returns:
            List[ToolCall]: 验证通过的调用
        """
        valid = []
        passed = 0
        failed = 0
        
        for call in candidates:
            result = self.validate(call, tools)
            
            if result.is_valid:
                valid.append(call)
                passed += 1
            else:
                failed += 1
                if self.config.verbose_logging:
                    logger.info(f"过滤无效调用: {call} - {result.error_message}")
        
        if self.config.verbose_logging:
            logger.info(f"Check Stage: {passed} 通过, {failed} 失败")
        
        return valid
    
    def _find_tool(self, name: str, tools: List[Tool]) -> Union[Tool, None]:
        """根据名称查找工具"""
        for tool in tools:
            if tool.name == name:
                return tool
        return None
    
    def _check_required_params(self, call: ToolCall, tool: Tool) -> List[str]:
        """检查必填参数"""
        missing = []
        for required in tool.required_params:
            if required not in call.arguments:
                missing.append(required)
        return missing
    
    def _check_data_types(
        self, 
        call: ToolCall, 
        tool: Tool
    ) -> List[str]:
        """检查数据类型"""
        errors = []
        
        for key, value in call.arguments.items():
            param = tool.get_param(key)
            
            if not param:
                # 未知参数，如果 strict_mode 则报错
                if self.config.strict_mode:
                    errors.append(f"未知参数: {key}")
                continue
            
            # 类型检查
            expected_type = param.type
            actual_type = self._get_value_type(value)
            
            if not self._type_matches(expected_type, actual_type, value):
                errors.append(
                    f"参数 '{key}' 类型不匹配: 期望 {expected_type.value}, "
                    f"实际 {actual_type} (值: {value})"
                )
        
        return errors
    
    def _get_value_type(self, value: Any) -> str:
        """获取值的类型名称"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return type(value).__name__
    
    def _type_matches(
        self, 
        expected: ToolParamType, 
        actual: str,
        value: Any
    ) -> bool:
        """检查类型是否匹配
        
        允许宽松的类型匹配:
        - integer 可以接受 int
        - number 可以接受 int 或 float
        - string 可以接受任何类型 (自动转换)
        """
        if expected == ToolParamType.STRING:
            # 字符串可以接受任何类型
            return True
        
        if expected == ToolParamType.INTEGER:
            return isinstance(value, int) and not isinstance(value, bool)
        
        if expected == ToolParamType.NUMBER:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        
        if expected == ToolParamType.BOOLEAN:
            return isinstance(value, bool)
        
        if expected == ToolParamType.ARRAY:
            return isinstance(value, list)
        
        if expected == ToolParamType.OBJECT:
            return isinstance(value, dict)
        
        return False
    
    def get_validation_summary(
        self, 
        candidates: List[ToolCall], 
        tools: List[Tool]
    ) -> Dict[str, Any]:
        """获取验证统计摘要"""
        total = len(candidates)
        passed = 0
        failed = 0
        errors_by_type = {
            "function_not_found": 0,
            "missing_required": 0,
            "type_mismatch": 0,
            "unknown_param": 0
        }
        
        for call in candidates:
            result = self.validate(call, tools)
            if result.is_valid:
                passed += 1
            else:
                failed += 1
                # 统计错误类型
                for error in result.errors:
                    if "不存在" in error:
                        errors_by_type["function_not_found"] += 1
                    elif "必填参数" in error:
                        errors_by_type["missing_required"] += 1
                    elif "类型不匹配" in error:
                        errors_by_type["type_mismatch"] += 1
                    elif "未知参数" in error:
                        errors_by_type["unknown_param"] += 1
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "errors_by_type": errors_by_type
        }
