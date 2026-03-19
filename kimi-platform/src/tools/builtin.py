"""
Kimi Multi-Agent Platform - Tools
内置工具集
"""

import json
import time
from typing import Any, Dict, List
from agents.agent import Tool


def create_file_tool() -> Tool:
    """文件操作工具"""
    def file_handler(action: str, path: str, content: str = None) -> Any:
        if action == "read":
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        
        elif action == "write":
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"File written: {path}"
            except Exception as e:
                return f"Error writing file: {e}"
        
        elif action == "append":
            try:
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return f"Content appended to: {path}"
            except Exception as e:
                return f"Error appending file: {e}"
        
        else:
            return f"Unknown action: {action}"
    
    return Tool(
        name="file_operations",
        description="Read, write, or append files",
        handler=file_handler
    )


def create_web_search_tool() -> Tool:
    """网络搜索工具（模拟）"""
    def search_handler(query: str, limit: int = 5) -> List[Dict]:
        # 这里应该调用真实搜索API
        # 现在是模拟实现
        return [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a simulated search result {i+1}..."
            }
            for i in range(min(limit, 3))
        ]
    
    return Tool(
        name="web_search",
        description="Search the web for information",
        handler=search_handler
    )


def create_code_executor_tool() -> Tool:
    """代码执行工具"""
    def execute_handler(code: str, language: str = "python") -> Dict:
        if language == "python":
            try:
                # 危险操作：实际使用时需要沙箱
                # 这里简化处理，只执行简单表达式
                result = eval(code)
                return {
                    "success": True,
                    "output": str(result),
                    "language": language
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "language": language
                }
        else:
            return {
                "success": False,
                "error": f"Language {language} not supported",
                "language": language
            }
    
    return Tool(
        name="code_executor",
        description="Execute code snippets",
        handler=execute_handler
    )


def create_memory_tool() -> Tool:
    """记忆操作工具"""
    storage = {}
    
    def memory_handler(action: str, key: str = None, value: Any = None) -> Any:
        if action == "get":
            return storage.get(key)
        
        elif action == "set":
            storage[key] = value
            return f"Stored: {key}"
        
        elif action == "list":
            return list(storage.keys())
        
        elif action == "clear":
            storage.clear()
            return "Memory cleared"
        
        else:
            return f"Unknown action: {action}"
    
    return Tool(
        name="memory_operations",
        description="Store and retrieve data from memory",
        handler=memory_handler
    )


def create_calculator_tool() -> Tool:
    """计算器工具"""
    def calc_handler(expression: str) -> str:
        try:
            # 安全计算
            allowed = {
                'abs': abs, 'max': max, 'min': min,
                'sum': sum, 'len': len,
            }
            result = eval(expression, {"__builtins__": {}}, allowed)
            return str(result)
        except Exception as e:
            return f"Error: {e}"
    
    return Tool(
        name="calculator",
        description="Perform calculations",
        handler=calc_handler
    )


def create_summarize_tool() -> Tool:
    """文本摘要工具（模拟）"""
    def summarize_handler(text: str, max_length: int = 100) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    return Tool(
        name="text_summarizer",
        description="Summarize long text",
        handler=summarize_handler
    )


# 工具工厂
def get_default_tools() -> List[Tool]:
    """获取默认工具集"""
    return [
        create_file_tool(),
        create_web_search_tool(),
        create_code_executor_tool(),
        create_memory_tool(),
        create_calculator_tool(),
        create_summarize_tool(),
    ]


# 扩展工具导入
def get_all_tools() -> List[Tool]:
    """获取所有工具（内置 + 扩展）"""
    from tools.extended import get_extended_tools
    return get_default_tools() + get_extended_tools()
