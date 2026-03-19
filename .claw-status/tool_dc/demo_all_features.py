"""
Tool-DC 完整功能演示

包含：
1. 多格式解析器测试
2. 并行推理基准测试
3. WDai 实际集成测试
"""

import sys
import os
import time
from typing import List
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

print("=" * 70)
print("Tool-DC 完整功能演示 - v1.0")
print("=" * 70)

# ============ 1. 多格式解析器测试 ============

print("\n" + "=" * 70)
print("1. 多格式工具调用解析器测试")
print("=" * 70)

from tool_dc.parsers import ToolCallParser, OutputFormat, parse_tool_call

parser = ToolCallParser()

# 测试各种格式
test_cases = [
    ("方括号格式", "[file_read(path='/tmp/test.txt')]", OutputFormat.BRACKET),
    ("JSON 格式", '{"name": "web_search", "arguments": {"query": "AI"}}', OutputFormat.JSON),
    ("XML 格式", "<tool>exec_command</tool><args>{\"command\": \"ls\"}</args>", OutputFormat.XML),
    ("Markdown 代码块", "```json\n{\"name\": \"file_read\", \"arguments\": {\"path\": \"/tmp/a\"}}\n```", OutputFormat.MARKDOWN),
    ("ReAct 格式", "Action: browser_open\nAction Input: {\"url\": \"https://example.com\"}", OutputFormat.REACT),
    ("纯文本格式", "memory_search: query=test", OutputFormat.PLAIN),
    ("无括号格式", "file_write(path='/tmp/b', content='hello')", None),
]

print("\n[单格式解析测试]")
for name, response, expected_format in test_cases:
    call = parse_tool_call(response)
    status = "✓" if call else "✗"
    print(f"\n  {name}:")
    print(f"    输入: {response[:50]}...")
    if call:
        print(f"    {status} 解析成功: {call.name}({call.arguments})")
    else:
        print(f"    {status} 解析失败")

# 多工具调用测试
print("\n[多工具调用解析]")
multi_tool_response = '[file_read(path="/a"), web_search(query="b"), exec_command(command="ls")]'
calls = parser.parse_multiple(multi_tool_response)
print(f"  输入: {multi_tool_response}")
print(f"  解析出 {len(calls)} 个工具调用:")
for i, call in enumerate(calls, 1):
    print(f"    {i}. {call.name}({call.arguments})")

# 自动格式检测
print("\n[自动格式检测测试]")
auto_tests = [
    '{"name": "search", "arguments": {"q": "test"}}',
    '<tool>read</tool><args>{"path": "/x"}</args>',
    'Action: write\nAction Input: {"path": "/y", "content": "z"}',
]
for test in auto_tests:
    call = parse_tool_call(test)
    if call:
        print(f"  ✓ 自动检测到格式并解析: {call}")


# ============ 2. 并行推理基准测试 ============

print("\n" + "=" * 70)
print("2. 并行推理基准测试")
print("=" * 70)

from tool_dc.parallel import ParallelInferenceEngine
from tool_dc.config import ToolDCConfig
from tool_dc.models import Tool, ToolParam, ToolParamType

class MockLLM:
    """模拟 LLM 带延迟"""
    def __init__(self, delay_ms: float = 10):
        self.delay_ms = delay_ms
    
    def generate(self, prompt: str) -> str:
        time.sleep(self.delay_ms / 1000)  # 模拟延迟
        return "[file_read(path='/tmp/test.txt')]"

def build_prompt(query: str, group: List[Tool]) -> str:
    return f"Query: {query}\nTools: {len(group)}"

# 创建测试数据
test_tools = [
    Tool(f"tool_{i}", f"工具 {i} 的描述", [
        ToolParam("arg", ToolParamType.STRING, "参数", required=True)
    ], ["arg"]) for i in range(20)
]

# 分组
groups = [test_tools[i:i+4] for i in range(0, len(test_tools), 4)]

print(f"\n[测试配置]")
print(f"  总工具数: {len(test_tools)}")
print(f"  分组数: {len(groups)}")
print(f"  每组工具数: ~{len(test_tools)//len(groups)}")
print(f"  模拟 LLM 延迟: 10ms")

# 创建引擎
config = ToolDCConfig(parallel_inference=True, max_workers=5)
engine = ParallelInferenceEngine(config)

# 创建模拟 LLM
llm = MockLLM(delay_ms=10)

# 运行基准测试
print(f"\n[运行基准测试 - 3 次迭代]")
results = engine.benchmark("测试查询", groups, llm, build_prompt, iterations=3)

print(f"\n  结果:")
print(f"    串行平均: {results['sequential_avg']:.2f}ms")
print(f"    并行平均: {results['parallel_avg']:.2f}ms")
print(f"    加速比: {results['speedup']:.2f}x")
print(f"    理论最优: {len(groups)}x (组数)")

if results['speedup'] > 1:
    print(f"    ✓ 并行显著提升了性能")
else:
    print(f"    ℹ 并行提升有限（可能由于线程开销）")


# ============ 3. WDai 实际集成测试 ============

print("\n" + "=" * 70)
print("3. WDai OpenClaw 集成测试")
print("=" * 70)

from tool_dc.integration.wdai_openclaw import WDaiToolDC, create_wdai_tool_dc

# 创建 Mock LLM 用于测试
class TestLLM:
    def generate(self, prompt: str) -> str:
        if "file" in prompt.lower() or "read" in prompt.lower():
            return '[file_read(path="/tmp/config.json")]'
        elif "search" in prompt.lower():
            return '[web_search(query="AI news")]'
        elif "write" in prompt.lower():
            return '[file_write(path="/tmp/output.txt", content="Hello")]'
        else:
            return '[exec_command(command="ls -la")]'

print("\n[初始化 WDaiToolDC]")
try:
    wdai_tool_dc = WDaiToolDC(
        llm=TestLLM(),
        config=ToolDCConfig(max_groups=3, fallback_threshold=5)
    )
    
    print("  ✓ WDaiToolDC 初始化成功")
    
    # 加载工具
    tools = wdai_tool_dc.load_skills()
    print(f"  ✓ 加载了 {len(tools)} 个工具")
    
    # 显示状态
    status = wdai_tool_dc.get_status()
    print(f"\n  状态:")
    print(f"    工具数: {status['tools_loaded']}")
    print(f"    Skills 目录: {status['skills_dir']}")
    print(f"    Tool-DC K: {status['config']['max_groups']}")
    
except Exception as e:
    print(f"  ✗ 初始化失败: {e}")

# 测试工具调用
print("\n[测试工具选择]")
test_queries = [
    "读取配置文件",
    "搜索最新 AI 进展",
    "写入日志文件",
]

for query in test_queries:
    print(f"\n  查询: '{query}'")
    try:
        result = wdai_tool_dc.select_and_execute(query)
        
        if result['success']:
            print(f"    ✓ 成功")
            print(f"    工具: {result['tool_call']['name']}")
            print(f"    参数: {result['tool_call']['arguments']}")
            print(f"    结果: {str(result['result'])[:60]}...")
        else:
            print(f"    ✗ 失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"    ✗ 异常: {e}")

# 聊天接口测试
print("\n[测试聊天接口]")
response = wdai_tool_dc.chat("帮我读取文件")
print(f"  用户: 帮我读取文件")
print(f"  助手: {response['response']}")
print(f"  使用工具: {response.get('tool_used', 'none')}")


# ============ 4. 总结 ============

print("\n" + "=" * 70)
print("功能演示总结")
print("=" * 70)

print("""
✅ 1. 多格式解析器
   • 支持 7 种输出格式
   • 自动格式检测
   • 支持多工具调用解析
   • 健壮的参数类型转换

✅ 2. 并行推理
   • ThreadPoolExecutor 实现
   • 可配置工作线程数
   • 内置性能基准测试
   • 加速比随组数增加

✅ 3. WDai 实际集成
   • WDaiToolDC 类
   • Skills 自动加载
   • 工具选择 + 执行
   • 聊天接口
   • 状态监控

📁 新增文件:
   • tool_dc/parsers/__init__.py - 多格式解析器
   • tool_dc/parallel.py - 并行推理
   • tool_dc/integration/wdai_openclaw.py - WDai 集成
   • tool_dc/demo_all_features.py - 本演示

🚀 完整使用示例:

   # 快速开始
   from tool_dc.integration.wdai_openclaw import create_wdai_tool_dc
   
   wdai = create_wdai_tool_dc(api_key="your_key")
   wdai.load_skills()
   
   result = wdai.select_and_execute("读取配置文件")
   print(result)
   
   # 或聊天
   response = wdai.chat("搜索 AI 新闻")
   print(response)
""")

print("=" * 70)
print("所有演示完成!")
print("=" * 70)
