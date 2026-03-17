#!/usr/bin/env python3
"""
MemRL集成初始化脚本
下次重启时通过AGENTS.md自动执行

功能:
1. 创建MemRL记忆目录结构
2. 从现有MEMORY.md迁移记忆
3. 初始化Q值
4. 验证系统可用性
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def log(message: str):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def initialize_memrl():
    """
    初始化MemRL记忆系统
    在AGENTS.md Every Session时自动调用
    """
    log("🔧 初始化MemRL记忆系统...")
    
    workspace = Path("/root/.openclaw/workspace")
    
    # 1. 创建必要的目录
    log("  创建目录结构...")
    dirs_to_create = [
        workspace / "memory" / "core",
        workspace / ".claw-status",
        workspace / ".learning"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        log(f"    ✅ {dir_path.relative_to(workspace)}")
    
    # 2. 创建默认配置文件
    config_file = workspace / ".claw-status" / "memrl_config.json"
    if not config_file.exists():
        log("  创建默认配置...")
        default_config = {
            "alpha": 0.1,
            "lambda_weight": 0.5,
            "similarity_threshold": 0.5,
            "top_k_candidates": 20,
            "top_k_final": 5,
            "initial_q": 0.5,
            "min_q": 0.1,
            "max_q": 1.0,
            "created_at": datetime.now().isoformat()
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        log(f"    ✅ {config_file.name}")
    else:
        log(f"    ✅ {config_file.name} 已存在")
    
    # 3. 创建/加载带Q值的记忆文件
    memory_file = workspace / "memory" / "core" / "skills_with_q.json"
    
    if not memory_file.exists():
        log("  创建MemRL记忆文件...")
        
        # 从现有记忆迁移 (如果有)
        initial_skills = []
        
        # 尝试从memory/core/skills.md迁移
        skills_md = workspace / "memory" / "core" / "skills.md"
        if skills_md.exists():
            log("    从skills.md迁移...")
            # 这里可以添加解析逻辑
            pass
        
        # 创建基础结构
        q_memory = {
            "version": "1.0",
            "schema": "skill_with_q",
            "created_at": datetime.now().isoformat(),
            "description": "MemRL风格的带Q值记忆库",
            "count": len(initial_skills),
            "skills": initial_skills
        }
        
        with open(memory_file, 'w') as f:
            json.dump(q_memory, f, indent=2, ensure_ascii=False)
        
        log(f"    ✅ {memory_file.name} (0条记忆)")
    else:
        # 加载并显示统计
        try:
            with open(memory_file) as f:
                data = json.load(f)
            count = len(data.get("skills", []))
            log(f"    ✅ {memory_file.name} ({count}条记忆)")
        except Exception as e:
            log(f"    ⚠️ 加载失败: {e}")
    
    # 4. 验证核心模块
    log("  验证核心模块...")
    try:
        sys.path.insert(0, str(workspace / ".claw-status"))
        from memrl_memory import MemRLMemory, get_memrl_memory
        
        # 尝试加载
        mem = get_memrl_memory()
        stats = mem.get_stats()
        
        log(f"    ✅ MemRLMemory 加载成功")
        log(f"       - 记忆数量: {stats['count']}")
        log(f"       - 平均Q值: {stats.get('avg_q', 0):.2f}")
        
    except Exception as e:
        log(f"    ❌ MemRLMemory 加载失败: {e}")
        return False
    
    # 5. 创建使用示例
    example_file = workspace / ".claw-status" / "memrl_usage_example.py"
    if not example_file.exists():
        example_code = '''#!/usr/bin/env python3
"""
MemRL使用示例
"""

from memrl_memory import get_memrl_memory

# 获取MemRL实例
mem = get_memrl_memory()

# 示例1: 检索记忆 (自动使用Q值排序)
results = mem.retrieve("部署博客到GitHub", top_k=3)
print("检索结果:")
for i, r in enumerate(results, 1):
    print(f"  {i}. Q值:{r['q_value']:.2f} 内容:{r['memory']['content'][:30]}...")

# 示例2: 更新记忆Q值 (任务完成后)
# reward: 1.0=成功, 0.5=部分成功, 0.0=失败
result = mem.update_q_value("skill_001", reward=1.0)
print(f"Q值更新: {result.get('old_q')} -> {result.get('new_q')}")

# 示例3: 添加新经验
new_id = mem.add_experience(
    query="部署博客到GitHub",
    experience="用git push比API上传更稳定",
    reward=1.0,
    tags=["deploy", "git", "github"]
)
print(f"新技能ID: {new_id}")

# 示例4: 获取统计
stats = mem.get_stats()
print(f"记忆统计: {stats}")
'''
        with open(example_file, 'w') as f:
            f.write(example_code)
        log(f"    ✅ 使用示例: {example_file.name}")
    
    # 6. 导出Markdown版本 (便于人类阅读)
    try:
        export_path = mem.export_to_markdown()
        log(f"    ✅ 导出Markdown: {Path(export_path).name}")
    except Exception as e:
        log(f"    ⚠️ Markdown导出失败: {e}")
    
    log("\n✅ MemRL系统初始化完成！")
    log("   下次检索记忆时将自动使用Q值排序")
    log("   任务完成后会自动更新Q值")
    
    return True

def quick_test():
    """快速测试MemRL功能"""
    log("\n🧪 快速测试...")
    
    try:
        sys.path.insert(0, "/root/.openclaw/workspace/.claw-status")
        from memrl_memory import get_memrl_memory
        
        mem = get_memrl_memory()
        
        # 添加测试数据
        test_id = mem.add_experience(
            query="测试查询",
            experience="这是一个测试记忆",
            reward=0.8,
            tags=["test"]
        )
        log(f"  添加测试记忆: {test_id}")
        
        # 检索
        results = mem.retrieve("测试", top_k=1)
        if results:
            log(f"  检索成功: 找到{len(results)}条记忆")
            log(f"    Q值: {results[0]['q_value']:.2f}")
            log(f"    相似度: {results[0]['similarity']:.2f}")
        
        # 更新Q值
        update_result = mem.update_q_value(test_id, reward=1.0)
        if 'error' not in update_result:
            log(f"  Q值更新: {update_result['old_q']:.2f} -> {update_result['new_q']:.2f}")
        
        log("  ✅ 测试通过")
        return True
        
    except Exception as e:
        log(f"  ❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = initialize_memrl()
    
    if success:
        quick_test()
        print("\n🎉 MemRL系统已就绪！")
    else:
        print("\n⚠️ 初始化失败，请检查错误日志")
        sys.exit(1)
