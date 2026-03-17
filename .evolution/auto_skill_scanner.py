#!/usr/bin/env python3
"""
自动技能扫描器
由进化循环 v1.1 自动生成
目标: 扩展工具覆盖率
生成时间: 2026-03-17T02:14:47.243767
"""

from pathlib import Path

def scan_available_skills() -> list:
    """扫描可用的技能"""
    skills_dir = Path("/root/.openclaw/skills")
    if not skills_dir.exists():
        return []
    
    skills = []
    for skill_dir in skills_dir.glob("*"):
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skills.append(skill_dir.name)
    
    return skills

if __name__ == "__main__":
    skills = scan_available_skills()
    print(f"发现 {len(skills)} 个技能")
    for skill in skills[:10]:  # 只显示前10个
        print(f"  - {skill}")
