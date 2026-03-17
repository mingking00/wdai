"""
OpenClaw Main Integration - OCA-MAS
将多智能体研究系统无缝集成到 OpenClaw 主流程
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio

# 添加技能路径
SKILL_PATH = Path(__file__).parent
sys.path.insert(0, str(SKILL_PATH))

from adaptive_orchestrator import research, AdaptiveOrchestrator
from personas import PersonaTeam

# 尝试导入工作监察
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / ".claw-status"))
    from work_monitor import start_task, progress, artifact, complete
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    def start_task(*a, **k): pass
    def progress(*a, **k): pass
    def artifact(*a, **k): pass
    def complete(*a, **k): pass


class OCAMASIntegration:
    """
    OCA-MAS 与 OpenClaw 的集成接口
    
    使用方式:
        integration = OCAMASIntegration()
        result = await integration.research("Your query")
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_parallel = self.config.get('max_parallel', 5)
        self.enable_monitoring = self.config.get('enable_monitoring', True)
        
    async def research(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """
        执行研究并返回格式化结果
        
        这是主要的集成接口
        """
        if self.enable_monitoring and MONITORING_AVAILABLE:
            start_task(f"研究: {query[:50]}...", steps=5)
        
        try:
            # 执行研究
            result = await research(
                query=query,
                max_parallel=self.max_parallel
            )
            
            if self.enable_monitoring and MONITORING_AVAILABLE:
                artifact("研究结果", "research_result.json")
                complete(f"研究完成，发现{result['sources_count']}个来源")
            
            # 格式化输出
            return self._format_response(result)
            
        except Exception as e:
            if self.enable_monitoring and MONITORING_AVAILABLE:
                from work_monitor import get_monitor
                monitor = get_monitor()
                if monitor.current_session:
                    monitor.error(str(e), recoverable=False)
            
            raise
    
    def _format_response(self, result: Dict) -> Dict[str, Any]:
        """格式化研究结果为 OpenClaw 可用格式"""
        return {
            "content": result["answer"],
            "insights": result.get("insights", []),
            "metadata": {
                "sources_count": result["sources_count"],
                "parallel_agents": result["parallel_agents"],
                "execution_time": result["critical_path_time"],
                "tokens_used": result.get("total_tokens", 0)
            },
            "formatted": self._generate_formatted_output(result)
        }
    
    def _generate_formatted_output(self, result: Dict) -> str:
        """生成格式化输出"""
        output = f"""🔬 研究完成

{result['answer']}

---
📊 研究统计
• 来源数量: {result['sources_count']} 个
• 并行Agent: {result['parallel_agents']} 个
• 执行时间: {result['critical_path_time']:.1f} 秒

💡 关键洞察
"""
        
        for i, insight in enumerate(result.get("insights", []), 1):
            output += f"{i}. {insight}\n"
        
        return output


# ============ 便捷函数 ============

async def quick_research(query: str) -> str:
    """
    快速研究 - 返回格式化字符串
    
    这是最简单的使用方式
    """
    integration = OCAMASIntegration()
    result = await integration.research(query)
    return result["formatted"]


def should_use_research(query: str) -> bool:
    """
    判断是否应该使用研究模式
    
    基于关键词启发式判断
    """
    research_indicators = [
        # 中文
        "研究", "分析", "对比", "比较", "最新", "趋势",
        "调查", "综述", "总结", "报告", "评估",
        # 英文
        "research", "analyze", "compare", "comparison",
        "latest", "trend", "survey", "review", "report",
        "evaluate", "study", "investigate"
    ]
    
    query_lower = query.lower()
    
    # 检查关键词
    has_indicator = any(
        indicator in query_lower 
        for indicator in research_indicators
    )
    
    # 检查问题复杂度 (简单启发式)
    word_count = len(query.split())
    is_complex = word_count > 10
    
    return has_indicator or is_complex


# ============ OpenClaw 主流程集成 ============

class OpenClawPlugin:
    """
    OpenClaw 插件接口
    
    在 OpenClaw 主流程中注册此插件
    """
    
    name = "multi-agent-research"
    version = "1.0.0"
    description = "多智能体研究系统"
    
    def __init__(self, openclaw_instance):
        self.oc = openclaw_instance
        self.integration = OCAMASIntegration()
    
    async def on_message(self, message: str, context: Dict = None) -> Optional[str]:
        """
        消息处理钩子
        
        当检测到研究需求时自动触发
        """
        if should_use_research(message):
            result = await self.integration.research(message, context)
            return result["formatted"]
        
        return None  # 不处理，让其他插件处理
    
    async def on_command(self, command: str, args: str) -> Optional[str]:
        """
        命令处理钩子
        
        支持 /research 命令
        """
        if command == "research":
            result = await self.integration.research(args)
            return result["formatted"]
        
        return None


# ============ 配置示例 ============

DEFAULT_CONFIG = {
    "enabled": True,
    "auto_trigger": True,  # 自动检测研究需求
    "max_parallel": 5,
    "enable_monitoring": True,
    "commands": {
        "research": "/research"
    }
}


# ============ 使用示例 ============

if __name__ == "__main__":
    import sys
    
    # 测试模式
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        
        print(f"🔬 测试研究: {query}\n")
        
        result = asyncio.run(quick_research(query))
        print(result)
    else:
        # 运行自检测试
        print("🔍 OCA-MAS 集成测试\n")
        
        # 测试1: 集成实例化
        integration = OCAMASIntegration()
        print("✓ 集成实例化成功")
        
        # 测试2: 研究判断
        test_queries = [
            "Hello",  # 不需要研究
            "研究AI最新发展",  # 需要研究
            "对比Python和JavaScript",  # 需要研究
        ]
        
        for q in test_queries:
            should = should_use_research(q)
            print(f"  '{q[:30]}...' -> {'研究' if should else '直接回复'}")
        
        # 测试3: 人格可用性
        for role in ["explorer", "investigator", "critic", "synthesist", "anchor"]:
            persona = PersonaTeam.get_persona(role)
            assert persona is not None
        print("✓ 所有Agent人格可用")
        
        print("\n✅ 所有测试通过!")
        print("\n使用方法:")
        print("  from openclaw_integration import quick_research")
        print("  result = await quick_research('Your query')")
