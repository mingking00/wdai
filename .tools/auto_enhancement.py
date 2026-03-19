#!/usr/bin/env python3
"""
Auto-Enhancement Integration - 自动增强集成
将不确定性检测、自我纠错、元认知监控集成到工作流

使用方法：在每次对话开始和结束时自动调用
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_self import EnhancedSelf
import atexit
import json

# 全局实例（确保会话间持久化）
_enhanced_self = None

def get_enhanced_self():
    """获取或创建增强自我实例"""
    global _enhanced_self
    if _enhanced_self is None:
        _enhanced_self = EnhancedSelf()
    return _enhanced_self

def before_response(query: str) -> dict:
    """
    在生成回复前调用
    
    自动执行：
    1. 不确定性预检测
    2. 历史纠正建议检索
    3. 元认知启动
    """
    enhanced = get_enhanced_self()
    return enhanced.before_responding(query)

def after_response(response: str) -> str:
    """
    在生成回复后调用
    
    自动执行：
    1. 不确定性检测与声明
    2. 元认知反思
    3. 记录交互等待反馈
    """
    enhanced = get_enhanced_self()
    return enhanced.after_responding(response)

def on_feedback(feedback: str) -> str:
    """
    接收用户反馈时调用
    
    自动执行：
    1. 反馈类型检测
    2. 提取教训
    3. 更新学习模式
    """
    enhanced = get_enhanced_self()
    return enhanced.on_user_feedback(feedback)

def get_learning_stats() -> dict:
    """获取学习统计"""
    enhanced = get_enhanced_self()
    return enhanced.get_stats()

def save_state():
    """程序退出时保存状态"""
    global _enhanced_self
    if _enhanced_self:
        print("\n💾 保存学习状态...")
        # 数据已自动保存到 .learning/ 目录
        stats = _enhanced_self.get_stats()
        print(f"   已记录 {stats['interactions_tracked']} 次交互")
        print(f"   已学习 {stats['patterns_learned']} 个模式")

# 注册退出时保存
atexit.register(save_state)

# ==================== 实际使用示例 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 自动增强系统已激活")
    print("=" * 70)
    print("\n现在每次对话将自动应用：")
    print("  ✓ 不确定性检测")
    print("  ✓ 历史教训检索")
    print("  ✓ 元认知监控")
    print("  ✓ 反馈学习")
    print("\n学习数据保存在: .learning/")
    
    print("\n" + "-" * 70)
    print("【实时演示】")
    print("-" * 70)
    
    # 模拟实时对话流程
    query = "如何学习机器学习？"
    print(f"\n📝 用户查询: {query}")
    
    # 1. 预处理
    print("\n🔍 步骤1: 预处理检查...")
    pre = before_response(query)
    if pre['correction_suggestion']:
        print(f"   💡 发现历史教训，准备应用")
    if pre['should_search']:
        print(f"   🔍 建议搜索验证")
    
    # 2. 生成回答（模拟）
    response = "学习机器学习可以从Python和基础数学开始，然后学习经典算法如线性回归、决策树等。建议通过实际项目练习。"
    print(f"\n🤖 生成回答...")
    
    # 3. 后处理
    print("\n🔍 步骤2: 后处理增强...")
    enhanced = after_response(response)
    
    # 4. 显示统计
    print("\n📊 当前学习统计:")
    stats = get_learning_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ 自动增强系统就绪，将在每次对话中自动运行")
    print("=" * 70)
