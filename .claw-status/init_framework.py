#!/usr/bin/env python3
"""
Universal Framework 初始化脚本
在系统启动时执行
"""

import sys
from pathlib import Path

# 添加框架路径
FRAMEWORK_DIR = Path("/root/.openclaw/workspace/.claw-status")
sys.path.insert(0, str(FRAMEWORK_DIR))

def init_framework():
    """初始化通用框架"""
    print("=" * 60)
    print("🚀 wdai Universal Framework 初始化")
    print("=" * 60)
    
    try:
        from framework import UniversalFramework
        
        # 创建数据目录
        data_dir = FRAMEWORK_DIR / "data"
        data_dir.mkdir(exist_ok=True)
        
        # 初始化框架
        framework = UniversalFramework(
            config_path=str(FRAMEWORK_DIR / "config" / "framework.json")
        )
        
        # 发现并加载所有插件
        plugins_dir = FRAMEWORK_DIR / "plugins"
        framework.discover_plugins(str(plugins_dir))
        
        # 显示状态
        stats = framework.get_stats()
        print(f"\n📊 框架状态:")
        print(f"  已加载插件: {stats['plugins_loaded']}")
        print(f"  插件列表: {', '.join(stats['plugin_names'])}")
        print(f"  事件记录: {stats['events_logged']}")
        
        print("\n✅ Universal Framework 初始化完成!")
        print("=" * 60)
        
        return framework
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    framework = init_framework()
