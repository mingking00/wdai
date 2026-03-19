"""
Tool-DC Response Parsers

支持多种 LLM 输出格式的解析器
"""

import json
import re
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

from ..models import ToolCall

logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """支持的输出格式"""
    BRACKET = "bracket"           # [func_name(args)]
    JSON = "json"                 # {"name": "func", "arguments": {...}}
    XML = "xml"                   # <tool>func_name</tool><args>{...}</args>
    MARKDOWN = "markdown"         # ```json {...} ```
    CODE_BLOCK = "code_block"     # ```func_name(args)```
    PLAIN = "plain"               # func_name: args
    REACT = "react"               # Action: func_name\nAction Input: {...}


class ToolCallParser:
    """
    工具调用解析器
    
    支持多种格式的自动识别和解析
    """
    
    def __init__(self):
        self.parsers = {
            OutputFormat.BRACKET: self._parse_bracket,
            OutputFormat.JSON: self._parse_json,
            OutputFormat.XML: self._parse_xml,
            OutputFormat.MARKDOWN: self._parse_markdown,
            OutputFormat.CODE_BLOCK: self._parse_code_block,
            OutputFormat.PLAIN: self._parse_plain,
            OutputFormat.REACT: self._parse_react,
        }
    
    def parse(self, response: str, preferred_format: Optional[OutputFormat] = None) -> Optional[ToolCall]:
        """
        解析工具调用
        
        Args:
            response: LLM 响应文本
            preferred_format: 优先尝试的格式
            
        Returns:
            Optional[ToolCall]: 解析结果
        """
        response = response.strip()
        
        if not response or response.upper() in ("NO_TOOL", "NONE", "NULL"):
            return None
        
        # 优先尝试指定格式
        if preferred_format and preferred_format in self.parsers:
            result = self.parsers[preferred_format](response)
            if result:
                return result
        
        # 自动检测格式
        for fmt, parser in self.parsers.items():
            if fmt == preferred_format:
                continue  # 已经尝试过
            try:
                result = parser(response)
                if result:
                    logger.debug(f"使用 {fmt.value} 格式解析成功")
                    return result
            except Exception:
                continue
        
        logger.warning(f"无法解析响应: {response[:100]}...")
        return None
    
    def parse_multiple(self, response: str) -> List[ToolCall]:
        """
        解析多个工具调用
        
        支持格式:
        - [func1(args1), func2(args2)]
        - [{...}, {...}]
        """
        calls = []
        response = response.strip()
        
        # 尝试解析 JSON 数组
        if response.startswith("[") and response.endswith("]"):
            try:
                data = json.loads(response)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "name" in item:
                            calls.append(ToolCall(
                                name=item["name"],
                                arguments=item.get("arguments", {})
                            ))
                    if calls:
                        return calls
            except json.JSONDecodeError:
                pass
            
            # 尝试解析函数调用列表
            # [func1(args1), func2(args2)]
            inner = response[1:-1].strip()
            # 简单分割（可能不完美）
            parts = self._split_function_calls(inner)
            for part in parts:
                call = self.parse(part)
                if call:
                    calls.append(call)
        
        # 单工具调用
        if not calls:
            call = self.parse(response)
            if call:
                calls.append(call)
        
        return calls
    
    def _parse_bracket(self, response: str) -> Optional[ToolCall]:
        """解析方括号格式: [func_name(args)]"""
        # 匹配 [func_name(args)]
        pattern = r'\[([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*\]'
        match = re.search(pattern, response, re.DOTALL)
        
        if not match:
            # 尝试不带方括号的格式
            pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)$'
            match = re.search(pattern, response.strip(), re.DOTALL)
        
        if match:
            func_name = match.group(1)
            args_str = match.group(2).strip()
            arguments = self._parse_arguments(args_str)
            return ToolCall(name=func_name, arguments=arguments)
        
        return None
    
    def _parse_json(self, response: str) -> Optional[ToolCall]:
        """解析 JSON 格式: {"name": "func", "arguments": {...}}"""
        # 尝试提取 JSON 对象
        json_pattern = r'\{[^{}]*"name"[^{}]*\}'
        
        # 更宽松的匹配
        try:
            # 尝试整个响应作为 JSON
            if response.startswith("{") and response.endswith("}"):
                data = json.loads(response)
                if "name" in data:
                    return ToolCall(
                        name=data["name"],
                        arguments=data.get("arguments", data.get("parameters", {}))
                    )
        except json.JSONDecodeError:
            pass
        
        # 尝试提取代码块中的 JSON
        code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        match = re.search(code_block_pattern, response)
        if match:
            try:
                data = json.loads(match.group(1).strip())
                if "name" in data:
                    return ToolCall(
                        name=data["name"],
                        arguments=data.get("arguments", {})
                    )
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _parse_xml(self, response: str) -> Optional[ToolCall]:
        """解析 XML 格式: <tool>func_name</tool><args>{...}</args>"""
        # 匹配 <tool>func_name</tool>
        tool_pattern = r'<tool>([a-zA-Z_][a-zA-Z0-9_]*)</tool>'
        tool_match = re.search(tool_pattern, response)
        
        if tool_match:
            func_name = tool_match.group(1)
            
            # 尝试提取参数
            args_pattern = r'<args>(.*?)</args>'
            args_match = re.search(args_pattern, response, re.DOTALL)
            
            if args_match:
                args_str = args_match.group(1).strip()
                try:
                    arguments = json.loads(args_str)
                except json.JSONDecodeError:
                    arguments = self._parse_arguments(args_str)
            else:
                arguments = {}
            
            return ToolCall(name=func_name, arguments=arguments)
        
        return None
    
    def _parse_markdown(self, response: str) -> Optional[ToolCall]:
        """解析 Markdown 代码块格式"""
        # ```json {...} ```
        pattern = r'```(?:json)?\s*([\s\S]*?)```'
        match = re.search(pattern, response)
        
        if match:
            content = match.group(1).strip()
            
            # 尝试作为 JSON 解析
            try:
                data = json.loads(content)
                if "name" in data:
                    return ToolCall(
                        name=data["name"],
                        arguments=data.get("arguments", {})
                    )
            except json.JSONDecodeError:
                pass
            
            # 尝试作为函数调用解析
            return self._parse_bracket(content)
        
        return None
    
    def _parse_code_block(self, response: str) -> Optional[ToolCall]:
        """解析代码块格式: ```func_name(args)```"""
        pattern = r'```\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)\s*```'
        match = re.search(pattern, response, re.DOTALL)
        
        if match:
            func_name = match.group(1)
            args_str = match.group(2).strip()
            arguments = self._parse_arguments(args_str)
            return ToolCall(name=func_name, arguments=arguments)
        
        return None
    
    def _parse_plain(self, response: str) -> Optional[ToolCall]:
        """解析纯文本格式: func_name: args"""
        # func_name: arg1=val1, arg2=val2
        pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.+)$'
        match = re.match(pattern, response, re.DOTALL)
        
        if match:
            func_name = match.group(1)
            args_str = match.group(2).strip()
            arguments = self._parse_arguments(args_str)
            return ToolCall(name=func_name, arguments=arguments)
        
        return None
    
    def _parse_react(self, response: str) -> Optional[ToolCall]:
        """解析 ReAct 格式"""
        # Action: func_name
        # Action Input: {...}
        action_pattern = r'Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)'
        input_pattern = r'Action Input:\s*(\{.*?\}|.+?)(?=\n|$)'
        
        action_match = re.search(action_pattern, response)
        input_match = re.search(input_pattern, response, re.DOTALL)
        
        if action_match:
            func_name = action_match.group(1).strip()
            
            if input_match:
                input_str = input_match.group(1).strip()
                # 尝试作为 JSON 解析
                try:
                    arguments = json.loads(input_str)
                except json.JSONDecodeError:
                    arguments = self._parse_arguments(input_str)
            else:
                arguments = {}
            
            return ToolCall(name=func_name, arguments=arguments)
        
        return None
    
    def _parse_arguments(self, args_str: str) -> Dict[str, Any]:
        """解析参数字符串"""
        arguments = {}
        
        if not args_str:
            return arguments
        
        # 尝试作为 JSON 解析
        try:
            if args_str.startswith("{") and args_str.endswith("}"):
                return json.loads(args_str)
        except json.JSONDecodeError:
            pass
        
        # 解析 key=value 格式
        # 使用正则匹配 key=value，支持引号
        pattern = r'(\w+)\s*=\s*("[^"]*"|\'[^\']*\'|[^,]+)'
        matches = re.findall(pattern, args_str)
        
        for key, val in matches:
            val = val.strip()
            # 去除引号
            if (val.startswith('"') and val.endswith('"')) or \
               (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            
            # 尝试转换类型
            arguments[key] = self._convert_value(val)
        
        return arguments
    
    def _convert_value(self, val: str) -> Any:
        """转换值为适当类型"""
        val = val.strip()
        
        # 布尔值
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        if val.lower() in ("none", "null"):
            return None
        
        # 整数
        try:
            return int(val)
        except ValueError:
            pass
        
        # 浮点数
        try:
            return float(val)
        except ValueError:
            pass
        
        # 数组
        if val.startswith("[") and val.endswith("]"):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass
        
        # 对象
        if val.startswith("{") and val.endswith("}"):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass
        
        # 默认字符串
        return val
    
    def _split_function_calls(self, text: str) -> List[str]:
        """分割多个函数调用"""
        parts = []
        depth = 0
        current = ""
        
        for char in text:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                if current.strip():
                    parts.append(current.strip())
                current = ""
                continue
            
            current += char
        
        if current.strip():
            parts.append(current.strip())
        
        return parts


# 全局解析器实例
_default_parser = ToolCallParser()


def parse_tool_call(response: str, preferred_format: Optional[OutputFormat] = None) -> Optional[ToolCall]:
    """便捷函数：解析工具调用"""
    return _default_parser.parse(response, preferred_format)


def parse_multiple_tool_calls(response: str) -> List[ToolCall]:
    """便捷函数：解析多个工具调用"""
    return _default_parser.parse_multiple(response)
