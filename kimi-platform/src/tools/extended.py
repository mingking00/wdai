"""
Kimi Multi-Agent Platform - Extended Tools
扩展工具集
"""

import json
import time
import uuid
import random
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from agents.agent import Tool


def create_http_tool() -> Tool:
    """HTTP请求工具"""
    def http_handler(
        method: str = "GET",
        url: str = "",
        headers: Dict = None,
        params: Dict = None,
        data: Any = None,
        timeout: int = 30
    ) -> Dict:
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            return {
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:1000]  # 限制长度
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return Tool(
        name="http_request",
        description="Make HTTP requests (GET/POST/PUT/DELETE)",
        handler=http_handler
    )


def create_json_tool() -> Tool:
    """JSON处理工具"""
    def json_handler(action: str, data: Any = None, path: str = None) -> Any:
        if action == "parse":
            try:
                return json.loads(data) if isinstance(data, str) else data
            except Exception as e:
                return {"error": str(e)}
        
        elif action == "stringify":
            try:
                return json.dumps(data, ensure_ascii=False, indent=2)
            except Exception as e:
                return {"error": str(e)}
        
        elif action == "get":
            try:
                keys = path.split(".")
                result = data
                for key in keys:
                    if isinstance(result, dict):
                        result = result.get(key)
                    elif isinstance(result, list) and key.isdigit():
                        result = result[int(key)]
                    else:
                        return None
                return result
            except Exception:
                return None
        
        elif action == "set":
            try:
                keys = path.split(".")
                target = data
                for key in keys[:-1]:
                    if key not in target:
                        target[key] = {}
                    target = target[key]
                target[keys[-1]] = data.get("__value__")
                return data
            except Exception as e:
                return {"error": str(e)}
        
        else:
            return {"error": f"Unknown action: {action}"}
    
    return Tool(
        name="json_processor",
        description="Parse, stringify, and manipulate JSON data",
        handler=json_handler
    )


def create_datetime_tool() -> Tool:
    """日期时间工具"""
    def datetime_handler(action: str, format: str = None, delta: Dict = None) -> str:
        now = datetime.now()
        
        if action == "now":
            fmt = format or "%Y-%m-%d %H:%M:%S"
            return now.strftime(fmt)
        
        elif action == "today":
            return now.strftime("%Y-%m-%d")
        
        elif action == "timestamp":
            return str(int(now.timestamp()))
        
        elif action == "add":
            if delta:
                days = delta.get("days", 0)
                hours = delta.get("hours", 0)
                minutes = delta.get("minutes", 0)
                new_time = now + timedelta(days=days, hours=hours, minutes=minutes)
                fmt = format or "%Y-%m-%d %H:%M:%S"
                return new_time.strftime(fmt)
        
        elif action == "format":
            # 假设input是timestamp
            try:
                ts = float(format) if format else now.timestamp()
                dt = datetime.fromtimestamp(ts)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                return str(now)
        
        else:
            return str(now)
    
    return Tool(
        name="datetime",
        description="Get current time, format dates, calculate time deltas",
        handler=datetime_handler
    )


def create_random_tool() -> Tool:
    """随机数/UUID工具"""
    def random_handler(action: str, min_val: int = 0, max_val: int = 100, length: int = 8) -> str:
        if action == "int":
            return str(random.randint(min_val, max_val))
        
        elif action == "float":
            return str(random.uniform(min_val, max_val))
        
        elif action == "choice":
            choices = ["a", "b", "c", "d", "e"]
            return random.choice(choices)
        
        elif action == "uuid":
            return str(uuid.uuid4())
        
        elif action == "id":
            # 短ID
            chars = "abcdefghijklmnopqrstuvwxyz0123456789"
            return "".join(random.choices(chars, k=length))
        
        elif action == "shuffle":
            items = list(range(min_val, max_val))
            random.shuffle(items)
            return str(items[:10])
        
        else:
            return str(random.random())
    
    return Tool(
        name="random_generator",
        description="Generate random numbers, UUIDs, and random choices",
        handler=random_handler
    )


def create_system_tool() -> Tool:
    """系统信息工具"""
    def system_handler(action: str) -> Any:
        import platform
        import os
        
        if action == "platform":
            return {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
        
        elif action == "env":
            return dict(os.environ)
        
        elif action == "cwd":
            return os.getcwd()
        
        elif action == "listdir":
            return os.listdir(".")
        
        elif action == "cpu_count":
            return os.cpu_count()
        
        else:
            return {"platform": platform.system()}
    
    return Tool(
        name="system_info",
        description="Get system information, environment variables, directory listing",
        handler=system_handler
    )


def create_data_transform_tool() -> Tool:
    """数据转换工具"""
    def transform_handler(action: str, data: Any = None, separator: str = ",") -> Any:
        if action == "list_to_csv":
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], list):
                    return "\n".join([separator.join(map(str, row)) for row in data])
                else:
                    return separator.join(map(str, data))
            return ""
        
        elif action == "csv_to_list":
            if isinstance(data, str):
                lines = data.strip().split("\n")
                return [line.split(separator) for line in lines]
            return []
        
        elif action == "unique":
            if isinstance(data, list):
                seen = set()
                result = []
                for item in data:
                    if item not in seen:
                        seen.add(item)
                        result.append(item)
                return result
            return data
        
        elif action == "sort":
            if isinstance(data, list):
                return sorted(data)
            return data
        
        elif action == "count":
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                return len(data)
            elif isinstance(data, str):
                return len(data)
            return 0
        
        elif action == "filter":
            if isinstance(data, list):
                # 过滤掉None和空字符串
                return [x for x in data if x is not None and x != ""]
            return data
        
        else:
            return {"error": f"Unknown action: {action}"}
    
    return Tool(
        name="data_transform",
        description="Transform data: list/csv conversion, unique, sort, filter",
        handler=transform_handler
    )


def create_text_tool() -> Tool:
    """文本处理工具"""
    def text_handler(action: str, text: str = "", pattern: str = "", replacement: str = "") -> Any:
        if action == "upper":
            return text.upper()
        
        elif action == "lower":
            return text.lower()
        
        elif action == "split":
            return text.split(pattern) if pattern else text.split()
        
        elif action == "join":
            if isinstance(text, list):
                return pattern.join(text)
            return text
        
        elif action == "replace":
            return text.replace(pattern, replacement)
        
        elif action == "strip":
            return text.strip()
        
        elif action == "length":
            return len(text)
        
        elif action == "contains":
            return pattern in text
        
        elif action == "startswith":
            return text.startswith(pattern)
        
        elif action == "endswith":
            return text.endswith(pattern)
        
        else:
            return text
    
    return Tool(
        name="text_processor",
        description="Text processing: case conversion, split/join, replace, check",
        handler=text_handler
    )


def get_extended_tools() -> List[Tool]:
    """获取扩展工具集"""
    return [
        create_http_tool(),
        create_json_tool(),
        create_datetime_tool(),
        create_random_tool(),
        create_system_tool(),
        create_data_transform_tool(),
        create_text_tool(),
    ]


# 合并所有工具
def get_all_tools() -> List[Tool]:
    """获取所有工具（内置 + 扩展）"""
    from tools.builtin import get_default_tools
    return get_default_tools() + get_extended_tools()
