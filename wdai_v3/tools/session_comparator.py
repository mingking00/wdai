"""
Session 对比工具
对比任意两个 Session 之间的系统变化

借鉴 learn-claude-code 的"Before vs After"理念
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path
import json


@dataclass
class SessionSnapshot:
    """Session 状态快照"""
    session_id: str
    timestamp: str
    
    # 代码指标
    total_lines: int
    python_files: int
    test_files: int
    
    # 功能指标
    agent_count: int
    skill_count: int
    rule_count: int
    
    # 能力指标
    capabilities: List[str]
    
    # 资产列表
    key_files: List[str]


class SessionComparator:
    """Session 对比器"""
    
    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path
    
    def create_snapshot(self, session_id: str) -> SessionSnapshot:
        """创建当前状态的快照"""
        import subprocess
        
        # 统计代码行数
        try:
            result = subprocess.run(
                ["find", str(self.workspace), "-name", "*.py", "-exec", "wc", "-l", "{}", "+"],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.strip().split('\n')
            total_lines = sum(int(line.split()[0]) for line in lines if line.split())
            python_files = len([l for l in lines if l.strip()]) - 1  # 减去总计行
        except:
            total_lines = 0
            python_files = 0
        
        # 统计测试文件
        try:
            result = subprocess.run(
                ["find", str(self.workspace), "-name", "test_*.py", "-o", "-name", "*_test.py"],
                capture_output=True, text=True, timeout=10
            )
            test_files = len([l for l in result.stdout.strip().split('\n') if l.strip()])
        except:
            test_files = 0
        
        # 统计 Agent 数量
        try:
            agent_dir = self.workspace / "wdai_v3" / "agents"
            agent_count = len([f for f in agent_dir.glob("*.py") if f.is_file()]) if agent_dir.exists() else 0
        except:
            agent_count = 0
        
        # 统计 Skill 数量
        try:
            skills_dir = self.workspace / "skills"
            skill_count = len([d for d in skills_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]) if skills_dir.exists() else 0
        except:
            skill_count = 0
        
        # 统计规则数量
        try:
            rules_file = self.workspace / "wdai_v3" / "core" / "rules" / "security" / "semgrep" / "all_rules.yml"
            if rules_file.exists():
                import yaml
                with open(rules_file) as f:
                    rules = yaml.safe_load(f)
                rule_count = len(rules.get('rules', []))
            else:
                rule_count = 0
        except:
            rule_count = 0
        
        return SessionSnapshot(
            session_id=session_id,
            timestamp=str(Path().stat().st_mtime),  # 简化
            total_lines=total_lines,
            python_files=python_files,
            test_files=test_files,
            agent_count=agent_count,
            skill_count=skill_count,
            rule_count=rule_count,
            capabilities=self._detect_capabilities(),
            key_files=self._list_key_files()
        )
    
    def _detect_capabilities(self) -> List[str]:
        """检测当前系统能力"""
        capabilities = []
        
        # 检查核心模块
        core_dir = self.workspace / "wdai_v3" / "core"
        if core_dir.exists():
            if (core_dir / "security").exists():
                capabilities.append("安全审查")
            if (core_dir / "agent_system").exists():
                capabilities.append("多 Agent 协调")
            if (core_dir / "memory").exists():
                capabilities.append("记忆系统")
        
        # 检查 Skills
        skills_dir = self.workspace / "skills"
        if skills_dir.exists():
            if (skills_dir / "multi_agent_research").exists():
                capabilities.append("多 Agent 研究")
            if (skills_dir / "mem0-memory").exists():
                capabilities.append("Mem0 记忆")
        
        return capabilities
    
    def _list_key_files(self) -> List[str]:
        """列出关键文件"""
        key_files = []
        
        # 核心文件
        patterns = [
            "wdai_v3/core/**/*.py",
            "skills/**/SKILL.md",
            "memory/**/*.md",
            ".claw-status/*.py"
        ]
        
        for pattern in patterns:
            for file in self.workspace.glob(pattern):
                if file.is_file():
                    key_files.append(str(file.relative_to(self.workspace)))
        
        return sorted(key_files)[:20]  # 限制数量
    
    def compare(self, before: SessionSnapshot, after: SessionSnapshot) -> Dict:
        """对比两个快照"""
        return {
            "session_transition": f"{before.session_id} → {after.session_id}",
            "code_changes": {
                "lines_added": after.total_lines - before.total_lines,
                "files_added": after.python_files - before.python_files,
                "tests_added": after.test_files - before.test_files,
            },
            "capability_changes": {
                "new_capabilities": [c for c in after.capabilities if c not in before.capabilities],
                "removed_capabilities": [c for c in before.capabilities if c not in after.capabilities],
            },
            "infrastructure": {
                "agents": after.agent_count - before.agent_count,
                "skills": after.skill_count - before.skill_count,
                "rules": after.rule_count - before.rule_count,
            }
        }
    
    def print_comparison(self, before: SessionSnapshot, after: SessionSnapshot):
        """打印对比结果"""
        diff = self.compare(before, after)
        
        print("=" * 70)
        print(f"Session 对比: {diff['session_transition']}")
        print("=" * 70)
        
        print("\n📊 代码变化:")
        code = diff['code_changes']
        print(f"  代码行数: {code['lines_added']:+d}")
        print(f"  Python文件: {code['files_added']:+d}")
        print(f"  测试文件: {code['tests_added']:+d}")
        
        print("\n🎯 新增能力:")
        for cap in diff['capability_changes']['new_capabilities']:
            print(f"  + {cap}")
        
        if diff['capability_changes']['removed_capabilities']:
            print("\n⚠️ 移除能力:")
            for cap in diff['capability_changes']['removed_capabilities']:
                print(f"  - {cap}")
        
        print("\n🏗️ 基础设施变化:")
        infra = diff['infrastructure']
        print(f"  Agent: {infra['agents']:+d}")
        print(f"  Skill: {infra['skills']:+d}")
        print(f"  规则: {infra['rules']:+d}")
        
        print("\n" + "=" * 70)


def show_current_state():
    """显示当前系统状态"""
    workspace = Path("/root/.openclaw/workspace")
    comparator = SessionComparator(workspace)
    
    print("=" * 70)
    print("wdai 当前系统状态")
    print("=" * 70)
    
    snapshot = comparator.create_snapshot("current")
    
    print(f"\n📁 代码统计:")
    print(f"  Python文件: {snapshot.python_files}")
    print(f"  代码总行数: {snapshot.total_lines:,}")
    print(f"  测试文件: {snapshot.test_files}")
    
    print(f"\n🧩 系统组件:")
    print(f"  Agent数量: {snapshot.agent_count}")
    print(f"  Skill数量: {snapshot.skill_count}")
    print(f"  安全规则: {snapshot.rule_count}")
    
    print(f"\n✨ 已启用能力:")
    for cap in snapshot.capabilities:
        print(f"  ✓ {cap}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    show_current_state()
