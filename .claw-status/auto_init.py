#!/usr/bin/env python3
"""
wdai 自动初始化脚本 - 每次会话启动时执行
启用 self-improving-agent 和 mem0-memory 自动功能
"""

import sys
import os
from pathlib import Path

# 添加路径
SELF_IMPROVING_PATH = "/root/.openclaw/skills/self-improving-agent"
MEM0_PATH = "/root/.openclaw/workspace/skills/mem0-memory"

def init_self_improving():
    """初始化 Self-Improving Agent"""
    try:
        sys.path.insert(0, SELF_IMPROVING_PATH)
        
        # 确保学习目录存在
        learnings_dir = Path(".learnings")
        learnings_dir.mkdir(exist_ok=True)
        
        # 创建必要的记录文件
        for filename in ["ERRORS.md", "LEARNINGS.md", "FEATURE_REQUESTS.md"]:
            filepath = learnings_dir / filename
            if not filepath.exists():
                filepath.write_text(f"# {filename.replace('.md', '')}\n\n")
        
        print("✅ Self-Improving Agent 已初始化")
        print(f"   学习记录: {learnings_dir.absolute()}")
        return True
    except Exception as e:
        print(f"⚠️ Self-Improving Agent 初始化失败: {e}")
        return False

def init_mem0_memory():
    """初始化 Mem0-Memory"""
    try:
        sys.path.insert(0, MEM0_PATH)
        
        # 确保记忆目录存在
        memory_dir = Path(".memory")
        semantic_dir = memory_dir / "semantic"
        episodic_dir = memory_dir / "episodic"
        
        semantic_dir.mkdir(parents=True, exist_ok=True)
        episodic_dir.mkdir(parents=True, exist_ok=True)
        
        # 尝试加载 MemRL
        try:
            from memrl_memory import get_memrl_memory
            memrl = get_memrl_memory()
            print(f"✅ MemRL 记忆系统已加载 ({len(memrl.memories)}条记忆)")
        except ImportError:
            print("✅ Mem0-Memory 目录已初始化 (基础模式)")
        
        print(f"   语义记忆: {semantic_dir.absolute()}")
        print(f"   经验记忆: {episodic_dir.absolute()}")
        return True
    except Exception as e:
        print(f"⚠️ Mem0-Memory 初始化失败: {e}")
        return False

def auto_record_session_start():
    """自动记录会话启动"""
    try:
        from datetime import datetime
        
        log_file = Path(".learnings/SESSION_LOG.md")
        with open(log_file, "a") as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("- 会话启动\n")
            f.write("- Self-Improving: 启用\n")
            f.write("- Mem0-Memory: 启用\n")
        
        print(f"📝 会话已记录到 {log_file}")
    except:
        pass

if __name__ == "__main__":
    print("🚀 wdai 自动初始化...\n")
    
    # 切换到工作目录
    os.chdir("/root/.openclaw/workspace")
    
    # 初始化各系统
    init_self_improving()
    print()
    init_mem0_memory()
    print()
    auto_record_session_start()
    
    print("\n✨ 所有系统就绪，开始工作！")
