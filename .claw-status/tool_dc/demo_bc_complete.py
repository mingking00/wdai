"""
WDai Tool-DC 完整演示

展示：
- B. WDai Skills → Tool 自动转换
- C. BM25 检索器
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

# ============ 1. WDai Skills 自动转换演示 ============

print("=" * 70)
print("演示 B: WDai Skills → Tool 自动转换")
print("=" * 70)

from tool_dc.adapters import WDaiSkillAdapter, WDaiSkillRegistry
from tool_dc.models import Tool, ToolParam, ToolParamType

# 示例 1: OpenAI Function Schema 转换
openai_schema = {
    "name": "file_read",
    "description": "读取文件内容，支持文本和二进制文件",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径，可以是相对路径或绝对路径"
            },
            "limit": {
                "type": "integer",
                "description": "最大读取行数（仅文本文件有效）",
                "default": 1000
            },
            "offset": {
                "type": "integer",
                "description": "起始行号（1-based）",
                "default": 1
            }
        },
        "required": ["path"]
    }
}

tool1 = WDaiSkillAdapter.from_openai_schema(openai_schema)
print(f"\n[OpenAI Schema → Tool]")
print(f"  名称: {tool1.name}")
print(f"  描述: {tool1.description}")
print(f"  参数: {len(tool1.parameters)} 个")
for param in tool1.parameters:
    req = "(必填)" if param.required else "(可选)"
    print(f"    - {param.name}: {param.type.value} {req}")
print(f"  必填参数: {tool1.required_params}")

# 示例 2: 批量转换
openai_schemas = [
    {
        "name": "web_search",
        "description": "搜索网络信息",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "count": {"type": "integer", "description": "结果数量"},
                "freshness": {"type": "string", "description": "时间过滤", "enum": ["pd", "pw", "pm", "py"]}
            },
            "required": ["query"]
        }
    },
    {
        "name": "exec_command",
        "description": "执行命令",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "命令"},
                "timeout": {"type": "integer", "description": "超时秒数"},
                "workdir": {"type": "string", "description": "工作目录"}
            },
            "required": ["command"]
        }
    }
]

tools_batch = WDaiSkillAdapter.batch_convert(openai_schemas, "openai")
print(f"\n[批量转换 {len(openai_schemas)} 个 Schemas]")
for tool in tools_batch:
    print(f"  ✓ {tool.name}: {len(tool.parameters)} 个参数")

# 示例 3: 自定义字典格式转换
custom_dict = {
    "tool_name": "memory_search",
    "doc": "搜索长期记忆",
    "args": {
        "query": {"type": "string", "required": True, "description": "搜索关键词"},
        "max_results": {"type": "integer", "required": False, "default": 5}
    }
}

tool2 = WDaiSkillAdapter.from_dict(custom_dict)
print(f"\n[自定义字典 → Tool]")
print(f"  名称: {tool2.name}")
print(f"  描述: {tool2.description}")

# 示例 4: Python 函数转换
def browser_open(url: str, timeout: int = 30, headless: bool = False):
    """
    打开浏览器访问指定 URL
    
    Args:
        url: 要访问的网址
        timeout: 页面加载超时（秒）
        headless: 是否使用无头模式
    """
    pass

tool3 = WDaiSkillAdapter.from_python_function(browser_open)
print(f"\n[Python 函数 → Tool]")
print(f"  名称: {tool3.name}")
print(f"  描述: {tool3.description}")
print(f"  参数:")
for param in tool3.parameters:
    default = f" = {param.default}" if param.default is not None else ""
    req = "(必填)" if param.required else "(可选)"
    print(f"    - {param.name}: {param.type.value}{default} {req}")

# 示例 5: Skills 注册表
print(f"\n[Skills 注册表扫描]")
registry = WDaiSkillRegistry()
try:
    tools_found = registry.scan_skills()
    print(f"  发现 {len(tools_found)} 个工具")
    for tool in tools_found[:5]:  # 只显示前5个
        print(f"    - {tool.name}")
    if len(tools_found) > 5:
        print(f"    ... 还有 {len(tools_found) - 5} 个")
except Exception as e:
    print(f"  扫描失败: {e}")
    print(f"  （这是正常的，如果没有配置 skills 目录）")


# ============ 2. BM25 检索器演示 ============

print("\n" + "=" * 70)
print("演示 C: BM25 检索器")
print("=" * 70)

from tool_dc.retrievers import BM25Retriever

# 创建测试工具库
test_tools = [
    Tool(name="file_read", description="读取文件内容", parameters=[
        ToolParam("path", ToolParamType.STRING, "文件路径", required=True)
    ], required_params=["path"]),
    
    Tool(name="file_write", description="写入文件", parameters=[
        ToolParam("path", ToolParamType.STRING, "文件路径", required=True),
        ToolParam("content", ToolParamType.STRING, "内容", required=True)
    ], required_params=["path", "content"]),
    
    Tool(name="web_search", description="网络搜索", parameters=[
        ToolParam("query", ToolParamType.STRING, "搜索词", required=True)
    ], required_params=["query"]),
    
    Tool(name="browser_open", description="打开浏览器访问网页", parameters=[
        ToolParam("url", ToolParamType.STRING, "网址", required=True)
    ], required_params=["url"]),
    
    Tool(name="exec_command", description="执行系统命令", parameters=[
        ToolParam("command", ToolParamType.STRING, "命令", required=True)
    ], required_params=["command"]),
    
    Tool(name="memory_search", description="搜索记忆", parameters=[
        ToolParam("query", ToolParamType.STRING, "搜索词", required=True)
    ], required_params=["query"]),
    
    Tool(name="message_send", description="发送消息到频道", parameters=[
        ToolParam("channel", ToolParamType.STRING, "频道", required=True),
        ToolParam("message", ToolParamType.STRING, "消息", required=True)
    ], required_params=["channel", "message"]),
    
    Tool(name="calendar_create", description="创建日历事件", parameters=[
        ToolParam("title", ToolParamType.STRING, "标题", required=True),
        ToolParam("start_time", ToolParamType.STRING, "开始时间", required=True)
    ], required_params=["title", "start_time"]),
    
    Tool(name="email_send", description="发送邮件", parameters=[
        ToolParam("to", ToolParamType.STRING, "收件人", required=True),
        ToolParam("subject", ToolParamType.STRING, "主题", required=True)
    ], required_params=["to", "subject"]),
    
    Tool(name="database_query", description="查询数据库", parameters=[
        ToolParam("sql", ToolParamType.STRING, "SQL语句", required=True)
    ], required_params=["sql"]),
]

# 创建 BM25 检索器
retriever = BM25Retriever(k1=1.5, b=0.75)

# 构建索引
retriever.build_index(test_tools)
print(f"\n[构建 BM25 索引]")
print(f"  文档数: {retriever.total_docs}")
print(f"  平均长度: {retriever.avgdl:.2f}")
print(f"  词汇表大小: {len(retriever.idf)}")

# 测试检索
queries = [
    "读取文件",
    "搜索网络信息",
    "打开网页",
    "发送消息",
    "查询数据"
]

print(f"\n[检索测试]")
for query in queries:
    results = retriever.retrieve(query, test_tools, top_k=3)
    print(f"\n  查询: '{query}'")
    for i, tool in enumerate(results, 1):
        score = retriever._score_document(
            retriever._tokenize(query),
            test_tools.index(tool)
        )
        print(f"    {i}. {tool.name} (score: {score:.4f})")


# ============ 3. 完整集成演示 ============

print("\n" + "=" * 70)
print("演示: Tool-DC 完整流程")
print("=" * 70)

from tool_dc import create_tool_dc_handler

# 模拟 LLM
class DemoLLM:
    def generate(self, prompt: str) -> str:
        # 简单规则匹配
        if "file" in prompt.lower() or "文件" in prompt:
            return "[file_read(path='/tmp/test.txt')]"
        elif "search" in prompt.lower() or "搜索" in prompt:
            return "[web_search(query='test')]"
        elif "browser" in prompt.lower() or "浏览器" in prompt:
            return "[browser_open(url='https://example.com')]"
        else:
            return "[exec_command(command='ls')]"

# 创建处理器
llm = DemoLLM()
handler = create_tool_dc_handler(llm=llm)

# 使用 BM25 检索器的处理器
from tool_dc.config import ToolDCConfig
config = ToolDCConfig(max_groups=3, verbose_logging=True)
handler_with_retriever = create_tool_dc_handler(
    llm=llm,
    retriever=retriever,
    config=config
)

# 测试
test_queries = [
    "读取配置文件",
    "搜索 AI 新闻",
    "打开百度",
]

print(f"\n[完整流程测试]")
for query in test_queries:
    print(f"\n  查询: '{query}'")
    result = handler_with_retriever.select_tool(query, test_tools)
    
    if result.success:
        print(f"    ✓ 选中: {result.final_call}")
        print(f"    处理组数: {result.groups_processed}")
        print(f"    验证: {result.validation_passed}/{result.validation_passed + result.validation_failed} 通过")
        print(f"    耗时: {result.execution_time_ms:.2f}ms")
    else:
        print(f"    ✗ 失败")


print("\n" + "=" * 70)
print("演示完成！")
print("=" * 70)

print("""
总结:
- B. WDai Skills → Tool 转换已支持:
  • OpenAI Function Schema
  • OpenAPI/Swagger
  • Python 函数（类型注解 + docstring）
  • 自定义字典格式
  • Skills 目录自动扫描

- C. BM25 检索器已实现:
  • 完整的 BM25 算法
  • 索引构建和查询
  • 与 Tool-DC 集成
""")
