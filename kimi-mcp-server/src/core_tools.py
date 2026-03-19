# Kimi MCP Server - Phase 1 Core Tools Implementation
# 阶段1: 核心Tools实现

from fastmcp import FastMCP, Context
from typing import Optional, List, Dict, Any
import os
import json
import subprocess
from pathlib import Path

# 初始化MCP Server
mcp = FastMCP("Kimi Claw MCP Server", version="1.0.0")

# ============================================================
# File Tools (文件操作)
# ============================================================

@mcp.tool()
def file_read_text(
    path: str,
    offset: int = 1,
    limit: int = 100,
    encoding: str = "utf-8"
) -> Dict[str, Any]:
    """
    读取文本文件内容
    
    Args:
        path: 文件路径 (绝对路径或相对于workspace)
        offset: 起始行号 (1-based)
        limit: 最大读取行数
        encoding: 文件编码
    
    Returns:
        包含content、total_lines、truncated的字典
    """
    try:
        # 解析路径
        if not path.startswith('/'):
            path = os.path.join('/root/.openclaw/workspace', path)
        
        path = os.path.expanduser(path)
        
        if not os.path.exists(path):
            return {
                "success": False,
                "error": f"File not found: {path}",
                "content": None
            }
        
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
        return {
            "success": False,
            "error": str(e),
            "content": None
        }


@mcp.tool()
def file_write_text(
    path: str,
    content: str,
    append: bool = False,
    encoding: str = "utf-8",
    create_dirs: bool = True
) -> Dict[str, Any]:
    """
    写入文本文件
    
    Args:
        path: 文件路径
        content: 写入内容
        append: 是否追加模式
        encoding: 文件编码
        create_dirs: 是否自动创建目录
    
    Returns:
        操作结果状态
    """
    try:
        # 解析路径
        if not path.startswith('/'):
            path = os.path.join('/root/.openclaw/workspace', path)
        
        path = os.path.expanduser(path)
        
        # 创建目录
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
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def file_list_directory(
    path: str = ".",
    pattern: str = "*",
    include_hidden: bool = False
) -> Dict[str, Any]:
    """
    列出目录内容
    
    Args:
        path: 目录路径
        pattern: 文件匹配模式
        include_hidden: 是否包含隐藏文件
    
    Returns:
        文件和目录列表
    """
    try:
        if not path.startswith('/'):
            path = os.path.join('/root/.openclaw/workspace', path)
        
        path = os.path.expanduser(path)
        
        if not os.path.exists(path):
            return {
                "success": False,
                "error": f"Directory not found: {path}"
            }
        
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
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# Web Tools (网络访问)
# ============================================================

@mcp.tool()
def web_search_brave(
    query: str,
    count: int = 5,
    freshness: Optional[str] = None,
    country: str = "US"
) -> Dict[str, Any]:
    """
    使用Brave Search搜索网络
    
    Args:
        query: 搜索查询
        count: 返回结果数量 (1-10)
        freshness: 时效性过滤 (pd=24h, pw=7d, pm=30d, py=1y)
        country: 国家代码
    
    Returns:
        搜索结果列表
    """
    try:
        # 通过subprocess调用openclaw web_search
        cmd = [
            "openclaw", "web_search",
            "--query", query,
            "--count", str(min(count, 10)),
            "--country", country
        ]
        
        if freshness:
            cmd.extend(["--freshness", freshness])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr
            }
        
        # 解析输出
        output = result.stdout
        
        return {
            "success": True,
            "query": query,
            "results": output,
            "count_requested": count
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def web_fetch_page(
    url: str,
    extract_mode: str = "markdown",
    max_chars: int = 5000
) -> Dict[str, Any]:
    """
    抓取网页内容
    
    Args:
        url: 网页URL
        extract_mode: 提取模式 (markdown/text)
        max_chars: 最大字符数
    
    Returns:
        网页内容
    """
    try:
        cmd = [
            "openclaw", "web_fetch",
            "--url", url,
            "--extract-mode", extract_mode,
            "--max-chars", str(max_chars)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr
            }
        
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
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# Agent Memory Tools (代理记忆)
# ============================================================

@mcp.tool()
def agent_memory_search(
    query: str,
    max_results: int = 5,
    min_score: float = 0.5
) -> Dict[str, Any]:
    """
    搜索长期记忆
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
        min_score: 最低相关性分数
    
    Returns:
        记忆片段列表
    """
    try:
        # 读取MEMORY.md
        memory_path = "/root/.openclaw/workspace/MEMORY.md"
        
        if not os.path.exists(memory_path):
            return {
                "success": False,
                "error": "Memory file not found"
            }
        
        with open(memory_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单关键词匹配 (未来可升级为语义搜索)
        lines = content.split('\n')
        matches = []
        
        query_lower = query.lower()
        for i, line in enumerate(lines, 1):
            if query_lower in line.lower():
                # 获取上下文
                start = max(0, i - 3)
                end = min(len(lines), i + 3)
                context = '\n'.join(lines[start:end])
                
                matches.append({
                    "line": i,
                    "content": line.strip(),
                    "context": context
                })
        
        # 限制结果数
        matches = matches[:max_results]
        
        return {
            "success": True,
            "query": query,
            "matches": matches,
            "total_matches": len(matches),
            "memory_file": memory_path
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def agent_memory_update(
    key: str,
    value: str,
    importance: str = "medium",
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    更新长期记忆
    
    Args:
        key: 记忆键
        value: 记忆内容
        importance: 重要性 (high/medium/low)
        category: 分类标签
    
    Returns:
        更新状态
    """
    try:
        memory_path = "/root/.openclaw/workspace/MEMORY.md"
        
        # 读取现有内容
        if os.path.exists(memory_path):
            with open(memory_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = "# MEMORY.md - Long-Term Memory\n\n"
        
        # 格式化新记忆条目
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        entry = f"\n## {key}\n"
        entry += f"**Time**: {timestamp}\n"
        entry += f"**Importance**: {importance}\n"
        if category:
            entry += f"**Category**: {category}\n"
        entry += f"\n{value}\n"
        entry += "---\n"
        
        # 追加到文件
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
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# Core Planning Tools (核心规划)
# ============================================================

@mcp.tool()
def core_plan_task(
    task: str,
    complexity: str = "medium",
    time_budget: Optional[int] = None,
    available_tools: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    规划任务执行方案
    
    Args:
        task: 任务描述
        complexity: 复杂度 (low/medium/high)
        time_budget: 时间预算(分钟)
        available_tools: 可用工具列表
    
    Returns:
        执行计划
    """
    try:
        # 根据复杂度生成规划模板
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
        
        else:  # high
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
        
        return {
            "success": True,
            "plan": plan
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def core_decompose_problem(
    problem: str,
    depth: int = 2,
    max_subtasks: int = 5
) -> Dict[str, Any]:
    """
    问题分解
    
    Args:
        problem: 问题描述
        depth: 分解深度
        max_subtasks: 最大子任务数
    
    Returns:
        子任务树
    """
    try:
        # 简单的模板化分解 (未来可升级为AI驱动的动态分解)
        subtasks = []
        
        # 基于常见模式生成子任务
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
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# Server Launch
# ============================================================

if __name__ == "__main__":
    # 启动MCP Server
    # 支持stdio或http传输
    mcp.run()
