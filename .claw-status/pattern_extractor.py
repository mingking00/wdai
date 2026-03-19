#!/usr/bin/env python3
"""
WDai 全局模式提取器
Global Pattern Extractor
从经验中提取可复用模式
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class SuccessPattern:
    """成功模式"""
    id: str
    name: str
    task_type: str
    sequence: List[str]  # 行动序列
    preconditions: List[str]
    success_rate: float
    applied_count: int
    created_at: str
    source_experiences: List[str]


class GlobalPatternExtractor:
    """全局模式提取器"""
    
    def __init__(self, workspace: str = "/root/.openclaw/workspace"):
        self.workspace = Path(workspace)
        self.memory_dir = self.workspace / "memory"
        self.patterns_dir = self.workspace / "memory" / "patterns"
        self.patterns_dir.mkdir(exist_ok=True)
        
        # 模式库文件
        self.patterns_file = self.patterns_dir / "success_patterns.json"
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, SuccessPattern]:
        """加载已保存的模式"""
        if self.patterns_file.exists():
            with open(self.patterns_file) as f:
                data = json.load(f)
                return {k: SuccessPattern(**v) for k, v in data.items()}
        return {}
    
    def save_patterns(self):
        """保存模式库"""
        with open(self.patterns_file, 'w') as f:
            json.dump({k: asdict(v) for k, v in self.patterns.items()}, f, indent=2)
    
    def extract_from_project(self, project_name: str):
        """
        从项目记忆提取模式
        """
        print(f"\n🔍 从项目 '{project_name}' 提取模式...")
        
        # 读取项目文件
        project_file = self.memory_dir / "project" / f"{project_name}.md"
        if not project_file.exists():
            print(f"   ⚠️ 项目文件不存在: {project_file}")
            return
        
        content = project_file.read_text()
        
        # 1. 提取成功序列
        sequences = self._extract_sequences(content)
        print(f"   找到 {len(sequences)} 个行动序列")
        
        # 2. 分析成功模式
        for seq in sequences:
            pattern = self._analyze_sequence(seq, project_name)
            if pattern:
                self.patterns[pattern.id] = pattern
                print(f"   ✅ 提取模式: {pattern.name}")
        
        # 3. 保存
        self.save_patterns()
        print(f"   💾 模式库已更新，共 {len(self.patterns)} 个模式")
    
    def _extract_sequences(self, content: str) -> List[List[str]]:
        """从内容中提取行动序列"""
        sequences = []
        
        # 按日期分割
        sections = re.split(r'\n## \d{4}-\d{2}-\d{2}', content)
        
        for section in sections:
            if not section.strip():
                continue
            
            # 提取行动关键词
            actions = []
            
            # 匹配 "完成"、"实现"、"添加" 等动词
            action_patterns = [
                r'完成([^.，]+)',
                r'实现([^.，]+)',
                r'添加([^.，]+)',
                r'修复([^.，]+)',
                r'优化([^.，]+)',
                r'创建([^.，]+)',
            ]
            
            for pattern in action_patterns:
                matches = re.findall(pattern, section)
                actions.extend(matches)
            
            if len(actions) >= 2:  # 至少2个行动构成序列
                sequences.append(actions)
        
        return sequences
    
    def _analyze_sequence(self, sequence: List[str], source: str) -> SuccessPattern:
        """分析序列，生成模式"""
        # 生成模式ID
        seq_hash = hashlib.md5(
            json.dumps(sequence, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        # 推断任务类型
        task_type = self._classify_task_type(sequence)
        
        # 提取前置条件
        preconditions = self._extract_preconditions(sequence)
        
        # 生成模式名称
        name = self._generate_pattern_name(sequence, task_type)
        
        return SuccessPattern(
            id=f"pat-{task_type}-{seq_hash}",
            name=name,
            task_type=task_type,
            sequence=sequence,
            preconditions=preconditions,
            success_rate=0.8,  # 初始估计
            applied_count=1,
            created_at=datetime.now().isoformat(),
            source_experiences=[source]
        )
    
    def _classify_task_type(self, sequence: List[str]) -> str:
        """分类任务类型"""
        seq_text = ' '.join(sequence).lower()
        
        if any(w in seq_text for w in ['代码', '实现', '修复', '优化', 'code']):
            return 'coding'
        elif any(w in seq_text for w in ['搜索', '研究', '分析', 'search']):
            return 'research'
        elif any(w in seq_text for w in ['设计', '架构', 'design']):
            return 'design'
        elif any(w in seq_text for w in ['测试', '验证', 'test']):
            return 'testing'
        else:
            return 'general'
    
    def _extract_preconditions(self, sequence: List[str]) -> List[str]:
        """提取前置条件"""
        preconditions = []
        seq_text = ' '.join(sequence).lower()
        
        # 常见前置条件模式
        if '需求' in seq_text or '要求' in seq_text:
            preconditions.append('需求明确')
        if '方案' in seq_text or '设计' in seq_text:
            preconditions.append('有设计方案')
        if '依赖' in seq_text:
            preconditions.append('依赖已解决')
        
        return preconditions
    
    def _generate_pattern_name(self, sequence: List[str], task_type: str) -> str:
        """生成模式名称"""
        if len(sequence) >= 2:
            return f"{task_type}: {sequence[0][:15]}...→{sequence[-1][:15]}"
        return f"{task_type}: {' → '.join(sequence[:2])}"
    
    def suggest_pattern(self, current_task: str) -> List[SuccessPattern]:
        """
        为当前任务推荐模式
        """
        print(f"\n💡 为任务推荐模式: '{current_task[:40]}...'")
        
        # 分类当前任务
        task_type = self._classify_task_type([current_task])
        
        # 查找匹配的模式
        matching_patterns = []
        for pattern in self.patterns.values():
            # 类型匹配
            if pattern.task_type == task_type:
                matching_patterns.append(pattern)
            # 关键词匹配
            elif self._keyword_match(current_task, pattern):
                matching_patterns.append(pattern)
        
        # 按成功率排序
        matching_patterns.sort(
            key=lambda p: (p.success_rate, p.applied_count),
            reverse=True
        )
        
        return matching_patterns[:3]
    
    def _keyword_match(self, task: str, pattern: SuccessPattern) -> bool:
        """关键词匹配"""
        task_words = set(task.lower().split())
        pattern_words = set(' '.join(pattern.sequence).lower().split())
        
        overlap = task_words & pattern_words
        return len(overlap) >= 2
    
    def update_pattern_success(self, pattern_id: str, success: bool):
        """
        更新模式成功率
        """
        if pattern_id not in self.patterns:
            return
        
        pattern = self.patterns[pattern_id]
        pattern.applied_count += 1
        
        # 增量更新成功率
        if success:
            pattern.success_rate = (
                pattern.success_rate * (pattern.applied_count - 1) + 1
            ) / pattern.applied_count
        else:
            pattern.success_rate = (
                pattern.success_rate * (pattern.applied_count - 1)
            ) / pattern.applied_count
        
        self.save_patterns()
    
    def get_top_patterns(self, task_type: str = None, n: int = 5) -> List[SuccessPattern]:
        """获取最佳模式"""
        patterns = list(self.patterns.values())
        
        if task_type:
            patterns = [p for p in patterns if p.task_type == task_type]
        
        patterns.sort(key=lambda p: p.success_rate, reverse=True)
        return patterns[:n]
    
    def generate_report(self) -> str:
        """生成模式库报告"""
        report = []
        report.append("=" * 60)
        report.append("WDai 成功模式库报告")
        report.append("=" * 60)
        
        # 统计
        total = len(self.patterns)
        by_type = defaultdict(int)
        for p in self.patterns.values():
            by_type[p.task_type] += 1
        
        report.append(f"\n📊 总体统计")
        report.append(f"   总模式数: {total}")
        report.append(f"   按类型分布:")
        for task_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            report.append(f"      {task_type}: {count}")
        
        # Top模式
        report.append(f"\n🏆 最佳模式 (Top 5)")
        for i, p in enumerate(self.get_top_patterns(n=5), 1):
            report.append(f"   {i}. [{p.task_type}] {p.name}")
            report.append(f"      成功率: {p.success_rate:.0%} | 应用: {p.applied_count}次")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)


def main():
    """主入口 - 演示"""
    extractor = GlobalPatternExtractor()
    
    print("=" * 60)
    print("全局模式提取器演示")
    print("=" * 60)
    
    # 模拟从evo-006提取模式
    extractor.extract_from_project("evo-006")
    
    # 模拟推荐
    print("\n" + "=" * 60)
    task = "实现一个新的Planning功能"
    suggestions = extractor.suggest_pattern(task)
    
    print(f"\n📝 任务: {task}")
    print(f"\n推荐模式:")
    for i, p in enumerate(suggestions, 1):
        print(f"   {i}. {p.name}")
        print(f"      序列: {' → '.join(p.sequence[:3])}")
        print(f"      成功率: {p.success_rate:.0%}")
    
    # 生成报告
    print("\n" + extractor.generate_report())


if __name__ == "__main__":
    main()
