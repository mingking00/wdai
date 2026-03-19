"""
WDai OpenClaw Integration

在 WDai (OpenClaw) 中实际集成 Tool-DC
"""

import logging
import os
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from .. import create_tool_dc_handler, ToolDCHandler
from ..models import Tool, ToolCall, ToolDCResult
from ..config import ToolDCConfig
from ..adapters import WDaiSkillRegistry, WDaiSkillAdapter
from ..llm.kimi import create_kimi_llm

logger = logging.getLogger(__name__)


class WDaiToolDC:
    """
    WDai Tool-DC 集成器
    
    为 OpenClaw 提供 Tool-DC 增强的工具调用能力
    """
    
    def __init__(
        self,
        config: Optional[ToolDCConfig] = None,
        llm=None,
        skills_dir: Optional[Path] = None
    ):
        """
        初始化
        
        Args:
            config: Tool-DC 配置
            llm: LLM 实例，None 时自动创建
            skills_dir: Skills 目录
        """
        self.config = config or ToolDCConfig()
        self.skills_dir = skills_dir or Path("/root/.openclaw/workspace/skills")
        
        # 初始化 LLM
        if llm is None:
            self.llm = self._create_default_llm()
        else:
            self.llm = llm
        
        # 初始化 Tool-DC
        self.handler = create_tool_dc_handler(
            llm=self.llm,
            config=self.config
        )
        
        # Skills 注册表
        self.registry = WDaiSkillRegistry(skills_dir=self.skills_dir)
        self._tools: List[Tool] = []
        self._skill_executors: Dict[str, Callable] = {}
        
        logger.info(f"WDaiToolDC 初始化完成")
    
    def _create_default_llm(self):
        """创建默认 LLM"""
        # 尝试 Kimi
        kimi_key = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
        if kimi_key:
            try:
                return create_kimi_llm(api_key=kimi_key)
            except Exception as e:
                logger.warning(f"Kimi LLM 创建失败: {e}")
        
        # 尝试其他模型...
        # 这里可以添加更多模型支持
        
        raise ValueError("无法创建默认 LLM，请提供 api_key 或 llm 实例")
    
    def load_skills(self) -> List[Tool]:
        """
        加载所有 Skills 作为工具
        
        Returns:
            List[Tool]: 工具列表
        """
        self._tools = self.registry.scan_skills()
        
        if not self._tools:
            logger.warning(f"未在 {self.skills_dir} 发现 Skills")
            # 加载默认工具
            self._tools = self._get_default_tools()
        
        logger.info(f"加载了 {len(self._tools)} 个工具")
        return self._tools
    
    def _get_default_tools(self) -> List[Tool]:
        """获取默认工具列表"""
        from ..models import ToolParam, ToolParamType
        
        return [
            Tool(
                name="read",
                description="读取文件内容",
                parameters=[
                    ToolParam("file_path", ToolParamType.STRING, "文件路径", required=True),
                ],
                required_params=["file_path"]
            ),
            Tool(
                name="write",
                description="写入文件",
                parameters=[
                    ToolParam("file_path", ToolParamType.STRING, "文件路径", required=True),
                    ToolParam("content", ToolParamType.STRING, "内容", required=True),
                ],
                required_params=["file_path", "content"]
            ),
            Tool(
                name="search",
                description="搜索信息",
                parameters=[
                    ToolParam("query", ToolParamType.STRING, "搜索词", required=True),
                ],
                required_params=["query"]
            ),
            Tool(
                name="exec",
                description="执行命令",
                parameters=[
                    ToolParam("command", ToolParamType.STRING, "命令", required=True),
                ],
                required_params=["command"]
            ),
        ]
    
    def register_skill_executor(self, skill_name: str, executor: Callable):
        """
        注册 Skill 执行器
        
        Args:
            skill_name: Skill 名称
            executor: 执行函数，接收参数 dict，返回结果
        """
        self._skill_executors[skill_name] = executor
        logger.debug(f"注册执行器: {skill_name}")
    
    def select_and_execute(
        self, 
        query: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        选择并执行工具
        
        Args:
            query: 用户查询
            context: 上下文
            
        Returns:
            Dict: 执行结果
        """
        if not self._tools:
            self.load_skills()
        
        # 使用 Tool-DC 选择工具
        result = self.handler.select_tool(query, self._tools)
        
        if not result.success:
            return {
                "success": False,
                "error": "工具选择失败",
                "query": query,
                "tool_dc_result": result.to_dict()
            }
        
        call = result.final_call
        
        # 执行工具
        execution_result = self._execute_tool(call)
        
        return {
            "success": execution_result.get("success", False),
            "tool_call": call.to_dict(),
            "result": execution_result.get("result"),
            "error": execution_result.get("error"),
            "tool_dc_result": result.to_dict()
        }
    
    def _execute_tool(self, call: ToolCall) -> Dict[str, Any]:
        """执行工具"""
        tool_name = call.name
        arguments = call.arguments
        
        # 检查是否有注册的执行器
        if tool_name in self._skill_executors:
            try:
                result = self._skill_executors[tool_name](arguments)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 尝试映射到 OpenClaw 工具
        return self._map_to_openclaw_tool(tool_name, arguments)
    
    def _map_to_openclaw_tool(self, tool_name: str, arguments: Dict) -> Dict[str, Any]:
        """
        映射到 OpenClaw 内置工具
        
        支持的映射:
        - read → read 工具
        - write → write 工具
        - search → web_search
        - exec → exec_command
        """
        # 标准化名称
        name_mapping = {
            "file_read": "read",
            "file_write": "write",
            "web_search": "search",
            "exec_command": "exec",
            "browser_open": "browser",
            "message_send": "message",
        }
        
        normalized_name = name_mapping.get(tool_name, tool_name)
        
        # 这里应该调用实际的 OpenClaw 工具
        # 为了演示，返回模拟结果
        return {
            "success": True,
            "result": f"[模拟执行] {normalized_name}({arguments})",
            "note": "需要接入实际的 OpenClaw 工具执行"
        }
    
    def chat(
        self, 
        message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        聊天接口
        
        简单的单轮工具调用接口
        
        Args:
            message: 用户消息
            conversation_history: 对话历史
            
        Returns:
            Dict: 响应
        """
        result = self.select_and_execute(message)
        
        if result["success"]:
            return {
                "response": f"执行结果: {result['result']}",
                "tool_used": result["tool_call"]["name"],
                "success": True
            }
        else:
            return {
                "response": f"执行失败: {result.get('error', '未知错误')}",
                "success": False
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "tools_loaded": len(self._tools),
            "executors_registered": len(self._skill_executors),
            "skills_dir": str(self.skills_dir),
            "config": {
                "max_groups": self.config.max_groups,
                "fallback_threshold": self.config.fallback_threshold,
                "strict_mode": self.config.strict_mode,
            }
        }


# 便捷函数
def create_wdai_tool_dc(
    api_key: Optional[str] = None,
    config: Optional[ToolDCConfig] = None,
    **kwargs
) -> WDaiToolDC:
    """
    创建 WDai Tool-DC 实例
    
    Args:
        api_key: API Key，默认从环境变量读取
        config: 配置
        **kwargs: 其他参数
        
    Returns:
        WDaiToolDC: 实例
    """
    if api_key:
        llm = create_kimi_llm(api_key=api_key)
    else:
        llm = None
    
    return WDaiToolDC(config=config, llm=llm, **kwargs)


# 全局实例（单例）
_wdai_tool_dc: Optional[WDaiToolDC] = None


def get_wdai_tool_dc() -> WDaiToolDC:
    """获取全局 WDai Tool-DC 实例"""
    global _wdai_tool_dc
    if _wdai_tool_dc is None:
        _wdai_tool_dc = WDaiToolDC()
    return _wdai_tool_dc
