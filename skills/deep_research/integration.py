"""
Deep Research Skill 集成模块

将此文件导入到主 Agent 以启用深度研究功能
"""

from typing import Any, Dict

# 导入 Skill
from skills.deep_research import run as deep_research_run
from skills.deep_research import research, run_stream


class DeepResearchExtension:
    """
    Deep Research 扩展
    
    为主 Agent 添加研究能力
    """
    
    def __init__(self):
        self.name = "deep_research"
        self.description = "深度研究工具，支持快速/标准/深度三种模式"
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行研究任务
        
        参数:
            query: 研究问题
            depth: quick/standard/deep
            sources: 搜索源列表
        """
        return await deep_research_run(params)
    
    async def research(self, query: str, depth: str = "standard"):
        """
        便捷研究接口
        
        示例:
            result = await extension.research("AI frameworks", depth="deep")
        """
        return await research(query, depth=depth)


# 快捷函数
async def deep_research(query: str, depth: str = "standard") -> Dict[str, Any]:
    """
    便捷研究函数
    
    示例:
        result = await deep_research("Python best practices", depth="quick")
        print(result.answer)
        print(result.references_text)
    """
    return await research(query, depth=depth)


# 注册到主 Agent 的示例
def register_to_agent(agent):
    """
    将 Deep Research 注册到主 Agent
    
    示例:
        from deep_research_integration import register_to_agent
        register_to_agent(my_agent)
    """
    extension = DeepResearchExtension()
    
    # 注册为工具
    if hasattr(agent, 'register_tool'):
        agent.register_tool(
            name="deep_research",
            func=extension.execute,
            description="深度研究工具: query(问题), depth(quick/standard/deep)"
        )
    
    # 或者直接附加为属性
    agent.deep_research = extension
    
    return extension


# 命令解析器示例
RESEARCH_COMMAND_PATTERNS = [
    r"研究\s*(.+)",
    r"research\s+(.+)",
    r"调查\s*(.+)",
    r"查一下\s*(.+)",
]


def parse_research_command(text: str) -> tuple:
    """
    解析研究命令
    
    返回: (is_research_command, query, depth)
    
    示例:
        >>> parse_research_command("研究 Python asyncio")
        (True, "Python asyncio", "standard")
        
        >>> parse_research_command("深度研究 AI frameworks")
        (True, "AI frameworks", "deep")
    """
    import re
    
    # 检查深度关键词
    depth = "standard"
    if any(kw in text for kw in ["深度", "deep", "详细"]):
        depth = "deep"
    elif any(kw in text for kw in ["快速", "quick", "简要"]):
        depth = "quick"
    
    # 匹配命令
    for pattern in RESEARCH_COMMAND_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            return True, query, depth
    
    return False, None, None


# 主 Agent 消息处理器示例
async def handle_message(agent, message: str) -> str:
    """
    主 Agent 消息处理示例
    
    示例:
        response = await handle_message(agent, "研究 Python asyncio")
    """
    is_research, query, depth = parse_research_command(message)
    
    if is_research:
        result = await research(query, depth=depth)
        
        if result.success:
            response = f"{result.answer}\n\n{result.references_text}"
        else:
            response = f"研究失败: {result.error}"
        
        return response
    
    # 非研究命令，使用原有处理
    return await agent.default_handle(message)
