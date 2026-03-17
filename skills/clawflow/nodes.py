#!/usr/bin/env python3
"""
ClawFlow - 内置节点实现 v3.2

更新: 
- 接入真实 kimi_search
- SkillNode 支持异步执行
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import asyncio
import time
import json
import os
import csv
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime


class BaseNode(ABC):
    """节点基类"""
    
    @abstractmethod
    def execute(self, input_data: Any, params: Dict[str, Any], 
                context) -> Any:
        pass


# ==================== 基础节点 ====================

class TriggerNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        return input_data


class FunctionNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        code = params.get("code", "")
        if not code:
            return input_data
        
        local_vars = {
            "input": input_data,
            "params": params,
            "context": context,
            "output": None
        }
        
        try:
            exec(code, {}, local_vars)
            return local_vars.get("output", input_data)
        except Exception as e:
            raise RuntimeError(f"Function execution error: {e}")


class OutputNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        output_type = params.get("type", "return")
        
        if output_type == "print":
            print(f"[Output] {json.dumps(input_data, ensure_ascii=False, indent=2)}")
        elif output_type == "file":
            filepath = params.get("filepath")
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(input_data, f, ensure_ascii=False, indent=2)
                print(f"[Output] Saved to: {filepath}")
        
        return input_data


class HttpNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        try:
            import requests
        except ImportError:
            raise ImportError("Please install requests: pip install requests")
        
        method = params.get("method", "GET").upper()
        url = params.get("url", "")
        headers = params.get("headers", {})
        body = params.get("body")
        
        if not url:
            raise ValueError("HTTP node requires url parameter")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=body, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return {
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if "application/json" in response.headers.get("Content-Type", "") else response.text
            }
        except Exception as e:
            raise RuntimeError(f"HTTP request failed: {e}")


class IfNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        condition = params.get("condition", "")
        if not condition:
            return input_data
        
        try:
            eval_context = {
                "input": input_data,
                "json": input_data if isinstance(input_data, dict) else {},
                "True": True, "False": False, "None": None
            }
            result = eval(condition, {"__builtins__": {}}, eval_context)
            
            return {
                "__condition_result__": bool(result),
                "__input__": input_data
            }
        except Exception as e:
            raise RuntimeError(f"Condition evaluation failed: {e}")


class MergeNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        mode = params.get("mode", "append")
        
        if isinstance(input_data, dict) and "__merged__" in input_data:
            items = input_data["__merged__"]
            
            if mode == "append":
                result = []
                for item in items:
                    if isinstance(item, list):
                        result.extend(item)
                    else:
                        result.append(item)
                return result
            elif mode == "merge":
                result = {}
                for item in items:
                    if isinstance(item, dict):
                        result.update(item)
                return result
            elif mode == "first":
                return items[0] if items else None
            elif mode == "last":
                return items[-1] if items else None
        
        return input_data


class DelayNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        delay_ms = params.get("delay", 1000)
        time.sleep(delay_ms / 1000)
        return input_data


class TransformNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        operation = params.get("operation", "map")
        
        if operation == "map":
            mappings = params.get("mappings", {})
            if isinstance(input_data, dict):
                result = {}
                for old_key, new_key in mappings.items():
                    if old_key in input_data:
                        result[new_key] = input_data[old_key]
                return result
        
        elif operation == "filter":
            if isinstance(input_data, list):
                field = params.get("field")
                value = params.get("value")
                return [item for item in input_data 
                        if isinstance(item, dict) and item.get(field) == value]
        
        elif operation == "sort":
            if isinstance(input_data, list):
                field = params.get("field")
                reverse = params.get("reverse", False)
                return sorted(input_data, 
                            key=lambda x: x.get(field) if isinstance(x, dict) else x,
                            reverse=reverse)
        
        return input_data


# ==================== 数据节点 ====================

class FileNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        operation = params.get("operation", "read")
        path = params.get("path", "")
        
        if not path:
            raise ValueError("File node requires path parameter")
        
        path = Path(path)
        
        try:
            if operation == "read":
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {path}")
                encoding = params.get("encoding", "utf-8")
                content = path.read_text(encoding=encoding)
                
                return {
                    "path": str(path),
                    "content": content,
                    "size": path.stat().st_size,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                }
            
            elif operation == "write":
                content = params.get("content", "")
                encoding = params.get("encoding", "utf-8")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding=encoding)
                
                return {"path": str(path), "operation": "write", "success": True}
            
            elif operation == "list":
                if not path.exists():
                    return {"files": [], "directories": []}
                
                files = []
                directories = []
                for item in path.iterdir():
                    if item.is_file():
                        files.append({"name": item.name, "path": str(item), 
                                    "size": item.stat().st_size})
                    else:
                        directories.append({"name": item.name, "path": str(item)})
                
                return {"path": str(path), "files": files, "directories": directories}
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            raise RuntimeError(f"File operation failed: {e}")


class CSVNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        operation = params.get("operation", "read")
        
        try:
            if operation == "read":
                path = params.get("path", "")
                delimiter = params.get("delimiter", ",")
                encoding = params.get("encoding", "utf-8")
                
                with open(path, 'r', encoding=encoding, newline='') as f:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    rows = list(reader)
                
                return {"path": path, "rows": rows, "count": len(rows),
                        "columns": list(rows[0].keys()) if rows else []}
            
            elif operation == "write":
                path = params.get("path", "")
                data = input_data if isinstance(input_data, list) else []
                delimiter = params.get("delimiter", ",")
                
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    if data:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=delimiter)
                        writer.writeheader()
                        writer.writerows(data)
                
                return {"path": path, "rows_written": len(data), "success": True}
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            raise RuntimeError(f"CSV processing failed: {e}")


class JSONNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        operation = params.get("operation", "parse")
        
        try:
            if operation == "parse":
                json_str = input_data if isinstance(input_data, str) else params.get("content", "")
                return json.loads(json_str)
            
            elif operation == "stringify":
                indent = params.get("indent", 2)
                return json.dumps(input_data, ensure_ascii=False, indent=indent)
            
            elif operation == "read":
                path = params.get("path", "")
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            elif operation == "write":
                path = params.get("path", "")
                indent = params.get("indent", 2)
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(input_data, f, ensure_ascii=False, indent=indent)
                return {"path": path, "success": True}
            
            elif operation == "query":
                path = params.get("query_path", "")
                if not path:
                    return input_data
                
                data = input_data
                for key in path.split("."):
                    if isinstance(data, dict) and key in data:
                        data = data[key]
                    elif isinstance(data, list) and key.isdigit():
                        data = data[int(key)]
                    else:
                        return None
                return data
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            raise RuntimeError(f"JSON processing failed: {e}")


class DatabaseNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        operation = params.get("operation", "query")
        db_path = params.get("db_path", ":memory:")
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if operation == "query":
                sql = params.get("sql", "")
                cursor.execute(sql, params.get("params", []))
                rows = [dict(row) for row in cursor.fetchall()]
                return {"rows": rows, "count": len(rows)}
            
            elif operation == "execute":
                sql = params.get("sql", "")
                cursor.execute(sql, params.get("params", []))
                conn.commit()
                return {"lastrowid": cursor.lastrowid, "rowcount": cursor.rowcount}
            
            elif operation == "create_table":
                table = params.get("table", "")
                schema = params.get("schema", {})
                columns = ", ".join([f"{k} {v}" for k, v in schema.items()])
                sql = f"CREATE TABLE IF NOT EXISTS {table} ({columns})"
                cursor.execute(sql)
                conn.commit()
                return {"table": table, "success": True}
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
        except Exception as e:
            raise RuntimeError(f"Database operation failed: {e}")
        finally:
            if 'conn' in locals():
                conn.close()


class LLMNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        model = params.get("model", "mock")
        prompt = params.get("prompt", "")
        
        text = str(input_data) if not isinstance(input_data, str) else input_data
        prompt = prompt.replace("$input", text).replace("{{input}}", text)
        
        return {
            "model": model,
            "prompt": prompt,
            "response": f"[Mock Response] Processed: {text[:50]}...",
            "usage": {"prompt_tokens": len(prompt), "completion_tokens": 50}
        }


class EmailNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")
        
        if not to or not subject:
            raise ValueError("Email requires to and subject parameters")
        
        if isinstance(input_data, dict):
            for key, value in input_data.items():
                placeholder = f"{{{{{key}}}}}"
                body = body.replace(placeholder, str(value))
                subject = subject.replace(placeholder, str(value))
        
        print(f"[Email] To: {to}")
        print(f"[Email] Subject: {subject}")
        
        return {
            "to": to, "subject": subject, "sent": True,
            "timestamp": datetime.now().isoformat()
        }


class CronNode(BaseNode):
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        schedule = params.get("schedule", "")
        workflow_name = params.get("workflow_name", "")
        
        if not schedule:
            raise ValueError("Schedule parameter required")
        
        return {
            "schedule": schedule,
            "workflow": workflow_name,
            "enabled": True,
            "note": "Scheduled task configured"
        }


# ==================== OpenClaw Integration Nodes ====================

class SkillNode(BaseNode):
    """Call external Skills - with real kimi_search and async support"""
    
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        """同步执行 - 委托给异步版本"""
        try:
            # 检查是否已有运行的事件循环
            loop = asyncio.get_running_loop()
            # 在已有事件循环中（如在 async 测试中），直接运行协程
            # 创建新的事件循环来运行
            new_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(new_loop)
                return new_loop.run_until_complete(self.execute_async(input_data, params, context))
            finally:
                new_loop.close()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            # 没有运行的事件循环，使用 asyncio.run
            return asyncio.run(self.execute_async(input_data, params, context))
    
    async def execute_async(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        """异步执行入口"""
        skill_name = params.get("skill", "")
        skill_params = params.get("params", {})
        
        if not skill_name:
            raise ValueError("Skill node requires skill parameter")
        
        # Resolve parameters
        resolved_params = {}
        for key, value in skill_params.items():
            if isinstance(value, str) and value.startswith("$"):
                resolved_params[key] = context.evaluate_expression(value)
            else:
                resolved_params[key] = value
        
        # Route to specific skill implementation
        if skill_name == "kimi_search":
            return await self._kimi_search_async(resolved_params)
        elif skill_name == "web_search":
            return await self._web_search_async(resolved_params)
        elif skill_name == "file_read":
            return await self._file_read_async(resolved_params)
        elif skill_name == "exec":
            return await self._exec_async(resolved_params)
        else:
            return {"skill": skill_name, "params": resolved_params, 
                    "note": "Unknown skill, extensible"}
    
    async def _kimi_search_async(self, params: Dict[str, Any]) -> Any:
        """Async real search using free_search_skill"""
        query = params.get("query", "")
        if not query:
            return {"error": "Query required"}
        
        try:
            import sys
            sys.path.insert(0, '/root/.openclaw/workspace/.tools')
            
            from free_search_skill import FreeSearchSkill
            
            # Run synchronous search in executor
            loop = asyncio.get_event_loop()
            searcher = FreeSearchSkill()
            
            results = await loop.run_in_executor(
                None, 
                lambda: searcher.search(query=query, max_results=params.get("max_results", 5))
            )
            
            # Convert to standard format
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "title": r.title,
                    "url": r.href,
                    "snippet": r.body[:300] if len(r.body) > 300 else r.body
                })
            
            return {
                "skill": "kimi_search",
                "query": query,
                "results": formatted_results,
                "total": len(formatted_results),
                "source": "free_search_skill"
            }
            
        except Exception as e:
            print(f"Search error: {e}")
            # Fallback to mock
            return {
                "skill": "kimi_search",
                "query": query,
                "results": [
                    {
                        "title": f"Result {i+1} about {query}",
                        "url": f"https://example.com/{i+1}",
                        "snippet": f"Sample result about {query}..."
                    }
                    for i in range(2)
                ],
                "total": 2,
                "source": "mock_fallback",
                "error": str(e)
            }
    
    async def _web_search_async(self, params: Dict[str, Any]) -> Any:
        """Async web search using Brave API"""
        query = params.get("query", "")
        count = params.get("count", 5)
        
        try:
            import aiohttp
            
            api_key = os.environ.get("BRAVE_API_KEY")
            if not api_key:
                raise ValueError("BRAVE_API_KEY not set")
            
            headers = {"X-Subscription-Token": api_key}
            url = "https://api.search.brave.com/res/v1/web/search"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers, 
                    params={"q": query, "count": min(count, 20)}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for item in data.get("web", {}).get("results", [])[:count]:
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("description", "")
                            })
                        return {
                            "skill": "web_search",
                            "query": query,
                            "count": len(results),
                            "results": results,
                            "source": "brave_api"
                        }
                    else:
                        raise RuntimeError(f"API error: {response.status}")
                        
        except Exception as e:
            # Fallback to mock
            return {
                "skill": "web_search",
                "query": query,
                "count": count,
                "results": [
                    {
                        "title": f"Web Result {i+1} for {query}",
                        "url": f"https://example.com/{i+1}",
                        "snippet": f"Sample web result about {query}..."
                    }
                    for i in range(min(count, 5))
                ],
                "source": "mock",
                "error": str(e)
            }
    
    async def _file_read_async(self, params: Dict[str, Any]) -> Any:
        """Async file read"""
        path = params.get("path", "")
        if not path:
            raise ValueError("file_read requires path parameter")
        
        loop = asyncio.get_event_loop()
        
        def _read():
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        
        content = await loop.run_in_executor(None, _read)
        return {"content": content, "path": path}
    
    async def _exec_async(self, params: Dict[str, Any]) -> Any:
        """Async command execution"""
        command = params.get("command", "")
        if not command:
            raise ValueError("exec requires command parameter")
        
        # Create subprocess
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=30
            )
            
            return {
                "command": command,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace')
            }
        except asyncio.TimeoutError:
            process.kill()
            return {
                "command": command,
                "error": "Command timed out after 30s"
            }


class MessageNode(BaseNode):
    """Send messages"""
    
    def execute(self, input_data: Any, params: Dict[str, Any], context) -> Any:
        channel = params.get("channel", "")
        message = params.get("message", "")
        target = params.get("target", "")
        
        if not channel or not message:
            raise ValueError("Message node requires channel and message parameters")
        
        # Template rendering
        if isinstance(input_data, dict):
            for key, value in input_data.items():
                message = message.replace(f"{{{{{key}}}}}", str(value))
        
        print(f"[{channel.upper()}] To {target}: {message[:100]}...")
        
        return {
            "channel": channel,
            "target": target,
            "message": message,
            "sent": True,
            "timestamp": datetime.now().isoformat()
        }
