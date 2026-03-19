# Kimi MCP Server - Pure Python Implementation (No external deps)
# 纯Python实现，用于演示

from typing import Optional, List, Dict, Any
import os
import json
import subprocess
from datetime import datetime


# ============================================================
# File Tools (文件操作)
# ============================================================

def file_read_text(
    path: str,
    offset: int = 1,
    limit: int = 100,
    encoding: str = "utf-8"
) -> Dict[str, Any]:
    """读取文本文件内容"""
    try:
        if not path.startswith('/'):
            path = os.path.join('/root/.openclaw/workspace', path)
        path = os.path.expanduser(path)
        
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}", "content": None}
        
        with open(path, 'r', encoding=encoding, errors='replace') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        start_idx = max(0, offset - 1)
        end_idx = min(total_lines, start_idx + limit)
        selected_lines = lines[start_idx:end_idx]
        content = ''.join(selected_lines)
        
        return {
            "success": True,
            "path": path,
            "content": content,
            "total_lines": total_lines,
            "returned_lines": len(selected_lines),
            "truncated": end_idx < total_lines,
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        return {"success": False, "error": str(e), "content": None}


def file_write_text(
    path: str,
    content: str,
    append: bool = False,
    encoding: str = "utf-8",
    create_dirs: bool = True
) -> Dict[str, Any]:
    """写入文本文件"""
    try:
        if not path.startswith('/'):
            path = os.path.join('/root/.openclaw/workspace', path)
        path = os.path.expanduser(path)
        
        if create_dirs:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        
        mode = 'a' if append else 'w'
        with open(path, mode, encoding=encoding) as f:
            f.write(content)
        
        return {
            "success": True,
            "path": path,
            "bytes_written": len(content.encode(encoding)),
            "mode": "append" if append else "write"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def file_list_directory(
    path: str = ".",
    pattern: str = "*",
    include_hidden: bool = False
) -> Dict[str, Any]:
    """列出目录内容"""
    try:
        if not path.startswith('/'):
            path = os.path.join('/root/.openclaw/workspace', path)
        path = os.path.expanduser(path)
        
        if not os.path.exists(path):
            return {"success": False, "error": f"Directory not found: {path}"}
        
        entries = []
        for entry in os.listdir(path):
            if not include_hidden and entry.startswith('.'):
                continue
            full_path = os.path.join(path, entry)
            entry_info = {
                "name": entry,
                "path": full_path,
                "type": "directory" if os.path.isdir(full_path) else "file",
                "size": os.path.getsize(full_path) if os.path.isfile(full_path) else None
            }
            entries.append(entry_info)
        
        return {
            "success": True,
            "path": path,
            "entries": entries,
            "total_count": len(entries)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Core Planning Tools (核心规划)
# ============================================================

def core_plan_task(
    task: str,
    complexity: str = "medium",
    time_budget: Optional[int] = None,
    available_tools: Optional[List[str]] = None
) -> Dict[str, Any]:
    """规划任务执行方案"""
    try:
        if complexity == "low":
            steps = [
                f"1. 理解任务: {task}",
                "2. 直接执行 (System 1快速模式)",
                "3. 输出结果"
            ]
            system_path = "System 1 (Fast Path)"
        elif complexity == "medium":
            steps = [
                f"1. 理解任务: {task}",
                "2. 分解为3-5个子任务",
                "3. 按需调用工具",
                "4. 整合结果",
                "5. 质量检查"
            ]
            system_path = "System 1 → System 2 (Adaptive)"
        else:
            steps = [
                f"1. 深度理解任务: {task}",
                "2. 第一性原理分析",
                "3. 生成多个候选方案",
                "4. 评估每个方案",
                "5. 选择最优路径",
                "6. 细粒度执行",
                "7. 反思与验证",
                "8. 输出最终结果"
            ]
            system_path = "System 2 (Deep Path)"
        
        plan = {
            "task": task,
            "complexity": complexity,
            "system_path": system_path,
            "steps": steps,
            "estimated_time": time_budget or (10 if complexity == "low" else 30 if complexity == "medium" else 60),
            "recommended_tools": available_tools or ["file_read_text", "web_search_brave", "agent_memory_search"]
        }
        
        return {"success": True, "plan": plan}
    except Exception as e:
        return {"success": False, "error": str(e)}


def core_decompose_problem(
    problem: str,
    depth: int = 2,
    max_subtasks: int = 5
) -> Dict[str, Any]:
    """问题分解"""
    try:
        if "research" in problem.lower() or "研究" in problem:
            subtasks = [
                "定义研究范围和目标",
                "收集背景信息",
                "搜索最新资料",
                "分析并综合信息",
                "生成研究报告"
            ]
        elif "code" in problem.lower() or "编程" in problem:
            subtasks = [
                "理解需求和约束",
                "设计解决方案",
                "实现核心逻辑",
                "测试和调试",
                "优化和文档"
            ]
        elif "write" in problem.lower() or "写作" in problem:
            subtasks = [
                "确定主题和受众",
                "收集素材和观点",
                "创建大纲",
                "撰写内容",
                "编辑和润色"
            ]
        else:
            subtasks = [
                f"分析: {problem}",
                "收集必要信息",
                "制定解决方案",
                "执行并验证",
                "总结输出"
            ]
        
        subtasks = subtasks[:max_subtasks]
        
        return {
            "success": True,
            "original_problem": problem,
            "depth": depth,
            "subtasks": [
                {"id": i+1, "description": task, "status": "pending"}
                for i, task in enumerate(subtasks)
            ],
            "total_subtasks": len(subtasks)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Agent Memory Tools (代理记忆)
# ============================================================

def agent_memory_search(
    query: str,
    max_results: int = 5,
    min_score: float = 0.5
) -> Dict[str, Any]:
    """搜索长期记忆"""
    try:
        memory_path = "/root/.openclaw/workspace/MEMORY.md"
        
        if not os.path.exists(memory_path):
            return {"success": False, "error": "Memory file not found"}
        
        with open(memory_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        matches = []
        query_lower = query.lower()
        
        for i, line in enumerate(lines, 1):
            if query_lower in line.lower():
                start = max(0, i - 3)
                end = min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])
                matches.append({
                    "line": i,
                    "content": line.strip(),
                    "context": context
                })
        
        matches = matches[:max_results]
        
        return {
            "success": True,
            "query": query,
            "matches": matches,
            "total_matches": len(matches),
            "memory_file": memory_path
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def agent_memory_update(
    key: str,
    value: str,
    importance: str = "medium",
    category: Optional[str] = None
) -> Dict[str, Any]:
    """更新长期记忆"""
    try:
        memory_path = "/root/.openclaw/workspace/MEMORY.md"
        
        if os.path.exists(memory_path):
            with open(memory_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = "# MEMORY.md - Long-Term Memory\n\n"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"\n## {key}\n"
        entry += f"**Time**: {timestamp}\n"
        entry += f"**Importance**: {importance}\n"
        if category:
            entry += f"**Category**: {category}\n"
        entry += f"\n{value}\n"
        entry += "---\n"
        
        with open(memory_path, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        return {
            "success": True,
            "key": key,
            "importance": importance,
            "memory_file": memory_path,
            "timestamp": timestamp
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Web Tools (网络访问)
# ============================================================

def web_search_brave(
    query: str,
    count: int = 5,
    freshness: Optional[str] = None,
    country: str = "US"
) -> Dict[str, Any]:
    """使用Brave Search搜索网络"""
    try:
        # 使用openclaw命令行工具
        cmd = ["openclaw", "web_search", "--query", query, "--count", str(min(count, 10))]
        if freshness:
            cmd.extend(["--freshness", freshness])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        
        return {
            "success": True,
            "query": query,
            "results": result.stdout,
            "count_requested": count
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def web_fetch_page(
    url: str,
    extract_mode: str = "markdown",
    max_chars: int = 5000
) -> Dict[str, Any]:
    """抓取网页内容"""
    try:
        cmd = ["openclaw", "web_fetch", "--url", url, "--extract-mode", extract_mode]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        
        content = result.stdout
        if len(content) > max_chars:
            content = content[:max_chars] + "\n... [truncated]"
        
        return {
            "success": True,
            "url": url,
            "content": content,
            "length": len(content),
            "extract_mode": extract_mode
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# MCP Server Interface (MCP服务器接口)
# ============================================================

class KimiMCPServer:
    """Kimi MCP Server - Phase 1 Implementation"""
    
    def __init__(self):
        self.tools = {
            # File Tools
            'file_read_text': file_read_text,
            'file_write_text': file_write_text,
            'file_list_directory': file_list_directory,
            # Core Tools
            'core_plan_task': core_plan_task,
            'core_decompose_problem': core_decompose_problem,
            # Memory Tools
            'agent_memory_search': agent_memory_search,
            'agent_memory_update': agent_memory_update,
            # Web Tools
            'web_search_brave': web_search_brave,
            'web_fetch_page': web_fetch_page,
        }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用Tools"""
        tool_definitions = [
            {
                "name": "file_read_text",
                "description": "读取文本文件内容",
                "parameters": {
                    "path": {"type": "string", "description": "文件路径"},
                    "offset": {"type": "integer", "description": "起始行号", "default": 1},
                    "limit": {"type": "integer", "description": "最大行数", "default": 100}
                }
            },
            {
                "name": "file_write_text",
                "description": "写入文本文件",
                "parameters": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "写入内容"},
                    "append": {"type": "boolean", "description": "是否追加", "default": False}
                }
            },
            {
                "name": "file_list_directory",
                "description": "列出目录内容",
                "parameters": {
                    "path": {"type": "string", "description": "目录路径", "default": "."},
                    "include_hidden": {"type": "boolean", "description": "包含隐藏文件", "default": False}
                }
            },
            {
                "name": "core_plan_task",
                "description": "规划任务执行方案",
                "parameters": {
                    "task": {"type": "string", "description": "任务描述"},
                    "complexity": {"type": "string", "description": "复杂度", "enum": ["low", "medium", "high"]},
                    "time_budget": {"type": "integer", "description": "时间预算(分钟)"}
                }
            },
            {
                "name": "core_decompose_problem",
                "description": "问题分解",
                "parameters": {
                    "problem": {"type": "string", "description": "问题描述"},
                    "depth": {"type": "integer", "description": "分解深度", "default": 2}
                }
            },
            {
                "name": "agent_memory_search",
                "description": "搜索长期记忆",
                "parameters": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "max_results": {"type": "integer", "description": "最大结果数", "default": 5}
                }
            },
            {
                "name": "agent_memory_update",
                "description": "更新长期记忆",
                "parameters": {
                    "key": {"type": "string", "description": "记忆键"},
                    "value": {"type": "string", "description": "记忆内容"},
                    "importance": {"type": "string", "description": "重要性", "default": "medium"}
                }
            },
            {
                "name": "web_search_brave",
                "description": "使用Brave搜索网络",
                "parameters": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "count": {"type": "integer", "description": "结果数量", "default": 5}
                }
            },
            {
                "name": "web_fetch_page",
                "description": "抓取网页内容",
                "parameters": {
                    "url": {"type": "string", "description": "网页URL"},
                    "max_chars": {"type": "integer", "description": "最大字符数", "default": 5000}
                }
            }
        ]
        return tool_definitions
    
    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用指定Tool"""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            return self.tools[tool_name](**params)
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局服务器实例
server = KimiMCPServer()
