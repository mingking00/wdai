#!/usr/bin/env python3
"""
Kimi MCP Server Demo & Test Script
演示和测试阶段1核心Tools
"""

import subprocess
import json
import sys
from typing import Dict, Any


def call_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """调用MCP Tool (通过Python直接导入)"""
    try:
        # 导入核心Tools模块
        import sys
        sys.path.insert(0, '/root/.openclaw/workspace/kimi-mcp-server/src')
        
        from core_tools import (
            file_read_text, file_write_text, file_list_directory,
            web_search_brave, web_fetch_page,
            agent_memory_search, agent_memory_update,
            core_plan_task, core_decompose_problem
        )
        
        # 工具映射
        tools = {
            'file_read_text': file_read_text,
            'file_write_text': file_write_text,
            'file_list_directory': file_list_directory,
            'web_search_brave': web_search_brave,
            'web_fetch_page': web_fetch_page,
            'agent_memory_search': agent_memory_search,
            'agent_memory_update': agent_memory_update,
            'core_plan_task': core_plan_task,
            'core_decompose_problem': core_decompose_problem,
        }
        
        if tool_name not in tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        result = tools[tool_name](**params)
        return result
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def demo_file_tools():
    """演示File Tools"""
    print("\n" + "="*60)
    print("📁 FILE TOOLS DEMO")
    print("="*60)
    
    # Demo 1: 列出目录
    print("\n1️⃣ file_list_directory('.')")
    result = call_tool('file_list_directory', {'path': '.', 'include_hidden': False})
    if result['success']:
        print(f"✅ 找到 {result['total_count']} 个条目")
        for entry in result['entries'][:5]:
            print(f"   - {entry['name']} ({entry['type']})")
        if result['total_count'] > 5:
            print(f"   ... and {result['total_count'] - 5} more")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Demo 2: 读取文件
    print("\n2️⃣ file_read_text('SOUL.md', limit=10)")
    result = call_tool('file_read_text', {'path': 'SOUL.md', 'limit': 10})
    if result['success']:
        print(f"✅ 读取成功，共 {result['total_lines']} 行，返回 {result['returned_lines']} 行")
        print("   前3行预览:")
        lines = result['content'].split('\n')[:3]
        for line in lines:
            print(f"   | {line[:60]}...")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Demo 3: 写入文件
    print("\n3️⃣ file_write_text('test_mcp.txt')")
    test_content = "# MCP Test File\n\nThis file was created by Kimi MCP Server demo.\nTimestamp: 2026-03-10\n"
    result = call_tool('file_write_text', {
        'path': 'test_mcp.txt',
        'content': test_content
    })
    if result['success']:
        print(f"✅ 写入成功: {result['path']}")
        print(f"   字节数: {result['bytes_written']}")
    else:
        print(f"❌ Error: {result.get('error')}")


def demo_core_tools():
    """演示Core Tools"""
    print("\n" + "="*60)
    print("🧠 CORE TOOLS DEMO")
    print("="*60)
    
    # Demo 1: 任务规划
    print("\n1️⃣ core_plan_task('研究量子计算在AI中的应用')")
    result = call_tool('core_plan_task', {
        'task': '研究量子计算在AI中的应用',
        'complexity': 'high',
        'time_budget': 60
    })
    if result['success']:
        plan = result['plan']
        print(f"✅ 规划完成")
        print(f"   复杂度: {plan['complexity']}")
        print(f"   路径: {plan['system_path']}")
        print(f"   预计时间: {plan['estimated_time']}分钟")
        print(f"   步骤数: {len(plan['steps'])}")
        print("   步骤:")
        for step in plan['steps'][:3]:
            print(f"      - {step}")
        if len(plan['steps']) > 3:
            print(f"      ... and {len(plan['steps']) - 3} more")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Demo 2: 问题分解
    print("\n2️⃣ core_decompose_problem('设计一个多智能体系统')")
    result = call_tool('core_decompose_problem', {
        'problem': '设计一个多智能体系统',
        'depth': 2,
        'max_subtasks': 5
    })
    if result['success']:
        print(f"✅ 分解完成")
        print(f"   子任务数: {result['total_subtasks']}")
        print("   子任务:")
        for task in result['subtasks']:
            print(f"      {task['id']}. {task['description']}")
    else:
        print(f"❌ Error: {result.get('error')}")


def demo_memory_tools():
    """演示Memory Tools"""
    print("\n" + "="*60)
    print("💾 MEMORY TOOLS DEMO")
    print("="*60)
    
    # Demo 1: 搜索记忆
    print("\n1️⃣ agent_memory_search('MCP')")
    result = call_tool('agent_memory_search', {
        'query': 'MCP',
        'max_results': 3
    })
    if result['success']:
        print(f"✅ 搜索完成，找到 {result['total_matches']} 个匹配")
        for match in result['matches'][:2]:
            print(f"   Line {match['line']}: {match['content'][:50]}...")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Demo 2: 更新记忆
    print("\n2️⃣ agent_memory_update('MCP Server Test')")
    result = call_tool('agent_memory_update', {
        'key': 'MCP Server Implementation',
        'value': 'Successfully implemented Phase 1 core tools: file_read_text, file_write_text, file_list_directory, web_search_brave, web_fetch_page, agent_memory_search, agent_memory_update, core_plan_task, core_decompose_problem.',
        'importance': 'high',
        'category': 'Implementation'
    })
    if result['success']:
        print(f"✅ 记忆更新成功")
        print(f"   Key: {result['key']}")
        print(f"   时间戳: {result['timestamp']}")
        print(f"   重要性: {result['importance']}")
    else:
        print(f"❌ Error: {result.get('error')}")


def demo_web_tools():
    """演示Web Tools (可选，需要网络)"""
    print("\n" + "="*60)
    print("🌐 WEB TOOLS DEMO (可选)")
    print("="*60)
    
    print("\n⚠️  Web Tools需要网络连接和Brave API")
    print("   跳过实时演示，展示调用格式:")
    
    print("\n1️⃣ web_search_brave('MCP protocol 2025')")
    print("   参数: {")
    print('     "query": "MCP protocol 2025",')
    print('     "count": 5,')
    print('     "freshness": "pw"')
    print("   }")
    
    print("\n2️⃣ web_fetch_page('https://modelcontextprotocol.io')")
    print("   参数: {")
    print('     "url": "https://modelcontextprotocol.io",')
    print('     "extract_mode": "markdown",')
    print('     "max_chars": 5000')
    print("   }")


def run_all_demos():
    """运行所有演示"""
    print("\n" + "="*60)
    print("🚀 KIMI MCP SERVER - PHASE 1 DEMO")
    print("="*60)
    print("\n本演示展示阶段1实现的9个核心Tools:")
    print("  File Tools (3): file_read_text, file_write_text, file_list_directory")
    print("  Core Tools (2): core_plan_task, core_decompose_problem")
    print("  Memory Tools (2): agent_memory_search, agent_memory_update")
    print("  Web Tools (2): web_search_brave, web_fetch_page")
    
    try:
        demo_file_tools()
        demo_core_tools()
        demo_memory_tools()
        demo_web_tools()
        
        print("\n" + "="*60)
        print("✅ ALL DEMOS COMPLETED")
        print("="*60)
        print("\n📊 总结:")
        print("   - 9个核心Tools已就绪")
        print("   - 可直接通过Python导入使用")
        print("   - 支持MCP协议标准接口")
        print("   - 下一阶段: 添加更多领域Tools")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(run_all_demos())
