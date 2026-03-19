"""
WDai Tool-DC 集成示例

展示如何在 WDai 中使用 Tool-DC 增强工具调用
"""

import logging
from typing import List, Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO)

# ============ 1. 定义工具 ============

from tool_dc.models import Tool, ToolParam, ToolParamType

# 定义 WDai 的 Skills 作为工具
tools = [
    Tool(
        name="file_read",
        description="读取文件内容",
        parameters=[
            ToolParam("path", ToolParamType.STRING, "文件路径", required=True),
            ToolParam("limit", ToolParamType.INTEGER, "最大行数", required=False),
        ],
        required_params=["path"]
    ),
    Tool(
        name="file_write",
        description="写入文件内容",
        parameters=[
            ToolParam("path", ToolParamType.STRING, "文件路径", required=True),
            ToolParam("content", ToolParamType.STRING, "文件内容", required=True),
        ],
        required_params=["path", "content"]
    ),
    Tool(
        name="web_search",
        description="搜索网络信息",
        parameters=[
            ToolParam("query", ToolParamType.STRING, "搜索关键词", required=True),
            ToolParam("count", ToolParamType.INTEGER, "结果数量", required=False),
        ],
        required_params=["query"]
    ),
    Tool(
        name="exec_command",
        description="执行命令",
        parameters=[
            ToolParam("command", ToolParamType.STRING, "命令", required=True),
            ToolParam("timeout", ToolParamType.INTEGER, "超时秒数", required=False),
        ],
        required_params=["command"]
    ),
    Tool(
        name="memory_search",
        description="搜索记忆",
        parameters=[
            ToolParam("query", ToolParamType.STRING, "搜索关键词", required=True),
        ],
        required_params=["query"]
    ),
    Tool(
        name="browser_open",
        description="打开浏览器",
        parameters=[
            ToolParam("url", ToolParamType.STRING, "URL", required=True),
        ],
        required_params=["url"]
    ),
    Tool(
        name="message_send",
        description="发送消息",
        parameters=[
            ToolParam("channel", ToolParamType.STRING, "频道", required=True),
            ToolParam("message", ToolParamType.STRING, "消息内容", required=True),
        ],
        required_params=["channel", "message"]
    ),
]

# ============ 2. 实现 LLM 接口 ============

class SimpleLLM:
    """简单的 LLM 模拟，实际使用时应替换为真实 LLM 调用"""
    
    def generate(self, prompt: str) -> str:
        """
        模拟 LLM 生成
        
        实际使用时应调用真实的 LLM API，如：
        - Kimi API
        - Claude API
        - OpenAI API
        """
        # 这里仅做演示，返回模拟响应
        # 实际应调用: return call_llm_api(prompt)
        
        # 简单规则匹配用于演示
        if "读取文件" in prompt or "read" in prompt.lower():
            return "[file_read(path='/tmp/test.txt')]"
        elif "搜索" in prompt or "search" in prompt.lower():
            return "[web_search(query='test', count=5)]"
        elif "执行" in prompt or "run" in prompt.lower():
            return "[exec_command(command='ls -la')]"
        else:
            return "[file_read(path='/tmp/test.txt')]"


# ============ 3. 使用 Tool-DC ============

from tool_dc import create_tool_dc_handler, ToolDCConfig
from tool_dc.config import HIGH_ACCURACY_CONFIG

def demo_basic():
    """基础演示"""
    print("=" * 60)
    print("Tool-DC 基础演示")
    print("=" * 60)
    
    # 创建处理器
    llm = SimpleLLM()
    handler = create_tool_dc_handler(llm=llm)
    
    # 测试查询
    query = "帮我读取 /tmp/test.txt 文件"
    
    print(f"\n用户查询: {query}")
    print(f"可用工具数: {len(tools)}\n")
    
    # 选择工具
    result = handler.select_tool(query, tools)
    
    print(f"选择成功: {result.success}")
    print(f"最终调用: {result.final_call}")
    print(f"Try 候选数: {len(result.try_candidates)}")
    print(f"验证通过: {result.validation_passed}")
    print(f"验证失败: {result.validation_failed}")
    print(f"耗时: {result.execution_time_ms:.2f}ms")
    print(f"使用降级: {result.fallback_used}")
    
    return result


def demo_with_many_tools():
    """多工具场景演示"""
    print("\n" + "=" * 60)
    print("多工具场景演示 (20个工具)")
    print("=" * 60)
    
    # 创建更多工具
    many_tools = tools.copy()
    for i in range(13):
        many_tools.append(Tool(
            name=f"tool_{i}",
            description=f"工具 {i} 的描述",
            parameters=[
                ToolParam("arg1", ToolParamType.STRING, "参数1", required=True),
            ],
            required_params=["arg1"]
        ))
    
    llm = SimpleLLM()
    handler = create_tool_dc_handler(llm=llm)
    
    query = "搜索 Tool-DC 论文"
    
    print(f"\n用户查询: {query}")
    print(f"可用工具数: {len(many_tools)}\n")
    
    result = handler.select_tool(query, many_tools)
    
    print(f"选择成功: {result.success}")
    print(f"最终调用: {result.final_call}")
    print(f"处理组数: {result.groups_processed}")
    print(f"Try 候选数: {len(result.try_candidates)}")
    print(f"验证通过: {result.validation_passed}")
    print(f"验证失败: {result.validation_failed}")
    print(f"耗时: {result.execution_time_ms:.2f}ms")
    print(f"使用降级: {result.fallback_used}")


def demo_high_accuracy():
    """高精度模式演示"""
    print("\n" + "=" * 60)
    print("高精度模式演示")
    print("=" * 60)
    
    llm = SimpleLLM()
    
    # 使用高精度配置
    handler = create_tool_dc_handler(
        llm=llm,
        config=HIGH_ACCURACY_CONFIG
    )
    
    query = "执行 ls 命令查看目录"
    
    print(f"\n用户查询: {query}")
    print(f"配置: max_groups={HIGH_ACCURACY_CONFIG.max_groups}")
    print(f"      strict_mode={HIGH_ACCURACY_CONFIG.strict_mode}\n")
    
    result = handler.select_tool(query, tools)
    
    print(f"选择成功: {result.success}")
    print(f"最终调用: {result.final_call}")


# ============ 4. 与 WDai ReAct 集成 ============

class WDaiToolDCIntegration:
    """
    WDai ReAct 集成 Tool-DC 的示例
    
    在 ReAct 循环中，当需要选择工具时：
    1. 如果可用工具数 > 5，启用 Tool-DC
    2. 否则使用标准 ReAct
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.tool_dc = create_tool_dc_handler(llm=llm)
        self.tools = []
    
    def register_tools(self, tools: List[Tool]):
        """注册可用工具"""
        self.tools = tools
    
    def select_tool_for_action(self, thought: str, query: str) -> Dict[str, Any]:
        """
        为 ReAct Action 选择工具
        
        Args:
            thought: 当前的 Thought
            query: 原始用户查询
            
        Returns:
            工具调用结果
        """
        # Tool-DC 自动判断是否需要启用
        result = self.tool_dc.select_tool(query, self.tools)
        
        if result.success:
            return {
                "action": result.final_call.name,
                "action_input": result.final_call.arguments,
                "tool_dc_meta": {
                    "try_candidates": len(result.try_candidates),
                    "validation_passed": result.validation_passed,
                    "execution_time_ms": result.execution_time_ms,
                    "fallback_used": result.fallback_used
                }
            }
        else:
            return {
                "action": "error",
                "action_input": {"error": "工具选择失败"}
            }


if __name__ == "__main__":
    # 运行演示
    demo_basic()
    demo_with_many_tools()
    demo_high_accuracy()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n要将 Tool-DC 集成到 WDai:")
    print("1. 实现真实的 LLM 接口")
    print("2. 将 WDai Skills 转换为 Tool 对象")
    print("3. 在 ReAct 循环中调用 WDaiToolDCIntegration")
    print("4. 根据需要调整配置参数")
