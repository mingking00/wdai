#!/usr/bin/env python3
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
