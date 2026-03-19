#!/usr/bin/env python3
"""
WDai进化系统自动初始化器
在每次会话启动时自动加载所有evo hooks

使用方式:
1. 在会话启动脚本中调用: initialize_evolution_system()
2. 或在Python中: from init_evolution_system import initialize_evolution_system; initialize_evolution_system()

Author: wdai
Version: 1.0
"""

import sys
from pathlib import Path

# 添加到路径
CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))


def initialize_evolution_system(agent_id: str = "main"):
    """
    初始化WDai进化系统
    
    自动完成:
    1. 加载Hook框架
    2. 注册所有evo模块hooks
    3. 触发SESSION_START事件
    4. 返回系统状态
    
    Args:
        agent_id: Agent标识符
        
    Returns:
        (success: bool, stats: dict)
    """
    try:
        from evolution_hook_framework import initialize_evolution_hooks, get_registry
        
        # 初始化并注册所有hooks
        registry = initialize_evolution_hooks()
        
        # 获取统计
        stats = registry.get_stats()
        
        return True, stats
        
    except Exception as e:
        print(f"[EvolutionSystem] 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False, {'error': str(e)}


def get_evolution_status():
    """获取进化系统当前状态"""
    try:
        from evolution_hook_framework import get_registry
        registry = get_registry()
        return registry.get_stats()
    except:
        return {'status': 'not_initialized'}


# 如果直接运行，执行初始化
if __name__ == "__main__":
    success, stats = initialize_evolution_system()
    
    if success:
        print("\n✅ 进化系统初始化完成")
        print(f"   Hook总数: {stats.get('total_hooks', 0)}")
        print(f"   活跃事件: {len([e for e in stats.get('hooks_registered', {}).values() if e > 0])}")
    else:
        print("\n❌ 进化系统初始化失败")
        print(f"   错误: {stats.get('error', 'unknown')}")
