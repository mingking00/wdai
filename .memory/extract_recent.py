#!/usr/bin/env python3
"""手动记忆提取 - 从最近的对话和记忆文件中提取关键事实"""

import json
import uuid
from datetime import datetime
from pathlib import Path

# 提取的记忆列表
memories = []

def add_memory(fact, category, confidence=0.9, tags=None):
    """添加一条记忆"""
    memories.append({
        "id": str(uuid.uuid4()),
        "fact": fact,
        "category": category,
        "confidence": confidence,
        "created_at": datetime.now().isoformat(),
        "last_accessed": datetime.now().isoformat(),
        "access_count": 0,
        "decay_score": 1.0,
        "metadata": {
            "source": "manual_extraction",
            "extracted_at": datetime.now().isoformat(),
            "tags": tags or []
        }
    })

# === 从 memory/daily/2026-03-16.md 提取 ===

# 核心原则
add_memory(
    "创新能力定义为死局中找到活路的能力，同一方法失败3次必须强制换路",
    "principle",
    0.95,
    ["创新", "失败处理", "核心原则"]
)

add_memory(
    "验证本能是报告成功前必须验证结果的铁律，未经验证的成功报告是严重违规",
    "principle",
    0.95,
    ["验证", "核心原则", "质量控制"]
)

add_memory(
    "系统强制执行依赖P0-P4优先级、自动检查点和失败锁定机制",
    "principle",
    0.9,
    ["执行", "优先级", "系统"]
)

add_memory(
    "5个Agent形成完整循环：Coordinator(协调)、Coder(编码)、Reflector(反思)、Evolution(进化)、Reviewer(审查)",
    "fact",
    0.95,
    ["Agent", "架构", "多Agent协作"]
)

add_memory(
    "Agent配合的完整循环是：感知→决策→执行→反思→进化",
    "principle",
    0.9,
    ["Agent", "工作流", "循环"]
)

# MemRL 集成
add_memory(
    "MemRL集成完成，提供带Q值的记忆、两阶段检索(语义+Q值重排)、自动学习机制",
    "fact",
    0.9,
    ["MemRL", "记忆系统", "Q值", "学习"]
)

add_memory(
    "MemRL记忆三元组：(意图嵌入z, 原始经验e, 效用值Q)，任务完成自动更新Q值",
    "fact",
    0.9,
    ["MemRL", "记忆结构", "强化学习"]
)

# B站字幕提取教训
add_memory(
    "禁止将重要结果保存在/tmp/或/var/tmp/等临时目录，必须使用workspace/持久化目录",
    "constraint",
    0.95,
    ["文件管理", "持久化", "约束"]
)

add_memory(
    "长任务必须分段实时保存，每完成一段立即append到输出文件，不要等全部完成",
    "principle",
    0.9,
    ["任务管理", "持久化", "长任务"]
)

add_memory(
    "系统对>20分钟的进程自动SIGKILL清理，预估耗时>15分钟时必须缩短分段或并行处理",
    "constraint",
    0.9,
    ["系统限制", "进程管理", "时间约束"]
)

add_memory(
    "B站API可直接获取视频播放地址(无需cookie)，从dash.audio中提取baseUrl",
    "fact",
    0.85,
    ["B站", "API", "技术细节"]
)

# === 从 memory/daily/2026-03-17.md 提取 ===

add_memory(
    "自主进化执行器v2.0已启动，每7分钟记录状态、每小时执行外循环、每30分钟发现GitHub项目",
    "fact",
    0.9,
    ["自主执行", "进化", "定时任务"]
)

add_memory(
    "发现的GitHub项目：TomasHer/prompting-blueprints(Agentic AI进化指南)、dennysjmarquez/artisan-symbolic-dsl-LLMs(LLM符号治理框架)",
    "fact",
    0.85,
    ["GitHub", "项目发现", "AI", "Agent"]
)

add_memory(
    "发现的GitHub项目：genejr2025/circe-framework(多Agent协作框架)、YIING99/agent-evolution-protocol(Agent安全自进化框架)",
    "fact",
    0.85,
    ["GitHub", "项目发现", "多Agent", "进化"]
)

# === 从会话历史提取的用户偏好 ===

add_memory(
    "用户喜欢AI Agent、Claude Code、MemRL相关技术",
    "preference",
    0.85,
    ["用户偏好", "技术兴趣", "AI"]
)

add_memory(
    "用户对系统和框架有深入的思考，厌恶形式主义的限制",
    "preference",
    0.8,
    ["用户偏好", "风格", "哲学"]
)

add_memory(
    "用户会直接指出错误，不客气但有效",
    "preference",
    0.8,
    ["用户偏好", "沟通风格", "反馈"]
)

add_memory(
    "用户要求执行前先想三遍，交付后再查五遍",
    "constraint",
    0.85,
    ["用户要求", "质量控制", "工作方式"]
)

# === 方法锁定记录 ===

add_memory(
    "github_api方法已被锁定(3次失败)，强制换用git CLI",
    "fact",
    0.95,
    ["方法锁定", "github", "失败处理", "创新"]
)

# === 保存到文件 ===
output_dir = Path("/root/.openclaw/workspace/.memory/semantic")
output_dir.mkdir(parents=True, exist_ok=True)

# 按类别分组
by_category = {}
for mem in memories:
    cat = mem["category"]
    by_category.setdefault(cat, []).append(mem)

# 保存每个类别
for cat, items in by_category.items():
    filepath = output_dir / f"{cat}_memories.json"
    
    # 加载现有记忆
    existing = []
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            pass
    
    # 合并并保存
    all_memories = existing + items
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(all_memories, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(items)} {cat} memories ({len(all_memories)} total)")

# 保存全部
all_filepath = output_dir / "all_memories.json"
all_existing = []
if all_filepath.exists():
    try:
        with open(all_filepath, 'r', encoding='utf-8') as f:
            all_existing = json.load(f)
    except:
        pass

all_combined = all_existing + memories
with open(all_filepath, 'w', encoding='utf-8') as f:
    json.dump(all_combined, f, indent=2, ensure_ascii=False)

print(f"\n📊 Total: {len(memories)} new memories extracted")
print(f"📁 Total in database: {len(all_combined)} memories")
print(f"📂 Location: {output_dir}")

# 打印摘要
print("\n📝 Extracted Memories Summary:")
for cat, items in by_category.items():
    print(f"\n  [{cat.upper()}] {len(items)} items:")
    for item in items[:3]:  # 只显示前3个
        print(f"    - {item['fact'][:60]}...")
    if len(items) > 3:
        print(f"    ... and {len(items)-3} more")
