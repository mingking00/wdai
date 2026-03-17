#!/usr/bin/env python3
"""
Tag Activator - 标签化记忆激活器
自动从用户输入中提取标签，加载相关记忆上下文
"""

import re
import yaml
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ActivatedTag:
    """激活的标签"""
    name: str
    priority: int
    source: str  # 关键词/模式/意图
    is_mandatory: bool = False


@dataclass
class MemoryContext:
    """组装的记忆上下文"""
    constraints: List[str] = field(default_factory=list)
    session: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    cognition: List[str] = field(default_factory=list)
    knowledge: List[str] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    selected_depth: str = "FastThink"
    activated_tags: List[str] = field(default_factory=list)


class TagActivator:
    """
    标签化记忆激活器核心类
    
    使用流程:
        activator = TagActivator()
        context = activator.activate("设计一个系统")
        print(context.assemble())
    """
    
    def __init__(self, rules_path: str = None, priorities_path: str = None):
        """
        初始化激活器
        
        Args:
            rules_path: 规则文件路径，默认 memory/tag_activator_rules.yaml
            priorities_path: 优先级文件路径，默认 memory/tag_priorities.yaml
        """
        self.base_path = Path(__file__).parent
        self.rules_path = rules_path or self.base_path / "tag_activator_rules.yaml"
        self.priorities_path = priorities_path or self.base_path / "tag_priorities.yaml"
        
        # 加载配置
        self.rules = self._load_yaml(self.rules_path)
        self.priorities = self._load_yaml(self.priorities_path)
        
        # 编译正则表达式
        self._compile_patterns()
    
    def _load_yaml(self, path: Path) -> Dict:
        """加载YAML配置文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"警告: 配置文件不存在 {path}")
            return {}
        except yaml.YAMLError as e:
            print(f"错误: YAML解析失败 {e}")
            return {}
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.compiled_patterns = []
        patterns = self.rules.get('pattern_matches', [])
        for p in patterns:
            try:
                compiled = re.compile(p['pattern'])
                self.compiled_patterns.append({
                    'pattern': compiled,
                    'tags': p['tags'],
                    'priority_boost': p.get('priority_boost', 0)
                })
            except re.error as e:
                print(f"警告: 正则表达式编译失败: {p['pattern']} - {e}")
    
    def extract_keywords(self, user_input: str) -> List[str]:
        """
        从用户输入中提取关键词
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            提取的关键词列表
        """
        # 简单分词（实际可用jieba等中文分词）
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', user_input)
        return words
    
    def match_exact_keywords(self, keywords: List[str]) -> List[ActivatedTag]:
        """
        精确关键词匹配
        
        Args:
            keywords: 关键词列表
            
        Returns:
            激活的标签列表
        """
        exact_matches = self.rules.get('exact_matches', {})
        activated = []
        
        for keyword in keywords:
            if keyword in exact_matches:
                for tag in exact_matches[keyword]:
                    priority = self._get_tag_priority(tag)
                    activated.append(ActivatedTag(
                        name=tag,
                        priority=priority,
                        source=f"关键词: {keyword}"
                    ))
        
        return activated
    
    def match_patterns(self, user_input: str) -> List[ActivatedTag]:
        """
        正则模式匹配
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            激活的标签列表
        """
        activated = []
        
        for p in self.compiled_patterns:
            if p['pattern'].search(user_input):
                for tag in p['tags']:
                    priority = self._get_tag_priority(tag) + p['priority_boost']
                    activated.append(ActivatedTag(
                        name=tag,
                        priority=priority,
                        source=f"模式: {p['pattern'].pattern}"
                    ))
        
        return activated
    
    def classify_intent(self, user_input: str) -> Tuple[str, List[ActivatedTag]]:
        """
        意图分类
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            (意图类型, 相关标签列表)
        """
        intent_rules = self.rules.get('intent_classification', {})
        activated = []
        detected_intent = None
        
        for intent_name, intent_config in intent_rules.items():
            keywords = intent_config.get('keywords', [])
            for keyword in keywords:
                if keyword in user_input:
                    detected_intent = intent_name
                    default_depth = intent_config.get('default_depth', 'FastThink')
                    required_tags = intent_config.get('required_tags', [])
                    
                    # 添加默认推理深度标签
                    depth_tag = f"#self/cognition/{default_depth}"
                    activated.append(ActivatedTag(
                        name=depth_tag,
                        priority=self._get_tag_priority(depth_tag),
                        source=f"意图: {intent_name} -> 默认深度"
                    ))
                    
                    # 添加必需标签
                    for tag in required_tags:
                        activated.append(ActivatedTag(
                            name=tag,
                            priority=self._get_tag_priority(tag),
                            source=f"意图: {intent_name} -> 必需"
                        ))
                    
                    break
            
            if detected_intent:
                break
        
        return detected_intent, activated
    
    def _get_tag_priority(self, tag: str) -> int:
        """
        获取标签优先级
        
        Args:
            tag: 标签名称
            
        Returns:
            优先级数值（默认50）
        """
        # 遍历优先级配置
        for category, tags in self.priorities.items():
            if isinstance(tags, dict) and tag in tags:
                return tags[tag].get('priority', 50)
        return 50
    
    def _is_mandatory(self, tag: str) -> bool:
        """检查标签是否强制"""
        for category, tags in self.priorities.items():
            if isinstance(tags, dict) and tag in tags:
                return tags[tag].get('mandatory', False)
        return False
    
    def resolve_conflicts(self, tags: List[ActivatedTag]) -> List[ActivatedTag]:
        """
        解决标签冲突
        
        Args:
            tags: 激活的标签列表
            
        Returns:
            冲突解决后的标签列表
        """
        # 按优先级排序
        tags.sort(key=lambda x: x.priority, reverse=True)
        
        # 去重（保留高优先级）
        seen = set()
        resolved = []
        for tag in tags:
            if tag.name not in seen:
                seen.add(tag.name)
                resolved.append(tag)
        
        # 特殊冲突处理（简化版）
        conflict_rules = self.priorities.get('conflict_resolution', {}).get('special_cases', [])
        # TODO: 实现更复杂的冲突解决逻辑
        
        return resolved
    
    def load_memory_chunks(self, tags: List[ActivatedTag]) -> Dict[str, List[str]]:
        """
        加载记忆片段
        
        Args:
            tags: 激活的标签列表
            
        Returns:
            分类的记忆内容
        """
        chunks = {
            'constraints': [],
            'session': [],
            'preferences': [],
            'skills': [],
            'cognition': [],
            'knowledge': []
        }
        
        # 根据标签类别分类
        for tag in tags:
            tag_name = tag.name
            
            if 'constraints' in tag_name:
                chunks['constraints'].append(f"[{tag_name}] 优先级:{tag.priority}")
            elif 'session' in tag_name:
                chunks['session'].append(f"[{tag_name}] 来自:{tag.source}")
            elif 'user' in tag_name:
                chunks['preferences'].append(f"[{tag_name}] 来自:{tag.source}")
            elif 'skills' in tag_name:
                chunks['skills'].append(f"[{tag_name}] 能力边界相关")
            elif 'cognition' in tag_name:
                chunks['cognition'].append(f"[{tag_name}] 推理模式")
            elif 'knowledge' in tag_name or 'evolution' in tag_name:
                chunks['knowledge'].append(f"[{tag_name}] 知识资产")
        
        return chunks
    
    def generate_instructions(self, tags: List[ActivatedTag]) -> List[str]:
        """
        生成动态指令
        
        Args:
            tags: 激活的标签列表
            
        Returns:
            指令列表
        """
        instruction_rules = self.rules.get('dynamic_instructions', {})
        instructions = []
        
        for tag in tags:
            if tag.name in instruction_rules:
                rule = instruction_rules[tag.name]
                instructions.append(rule['instruction'])
        
        return instructions
    
    def select_depth(self, tags: List[ActivatedTag]) -> str:
        """
        选择推理深度
        
        Args:
            tags: 激活的标签列表
            
        Returns:
            选定的推理深度
        """
        depth_tags = [t for t in tags if 'cognition/' in t.name and any(
            d in t.name for d in ['NoThink', 'FastThink', 'CoreThink', 'DeepThink']
        )]
        
        if not depth_tags:
            return "FastThink"
        
        # 选择最高优先级的深度标签
        depth_tags.sort(key=lambda x: x.priority, reverse=True)
        selected = depth_tags[0].name
        
        # 提取深度名称
        for depth in ['DeepThink', 'CoreThink', 'FastThink', 'NoThink']:
            if depth in selected:
                return depth
        
        return "FastThink"
    
    def activate(self, user_input: str) -> MemoryContext:
        """
        主激活函数
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            组装的记忆上下文
        """
        # 1. 提取关键词
        keywords = self.extract_keywords(user_input)
        
        # 2. 多维度匹配
        activated_tags = []
        activated_tags.extend(self.match_exact_keywords(keywords))
        activated_tags.extend(self.match_patterns(user_input))
        
        intent, intent_tags = self.classify_intent(user_input)
        activated_tags.extend(intent_tags)
        
        # 3. 冲突解决
        resolved_tags = self.resolve_conflicts(activated_tags)
        
        # 4. 加载记忆
        chunks = self.load_memory_chunks(resolved_tags)
        
        # 5. 生成指令
        instructions = self.generate_instructions(resolved_tags)
        
        # 6. 选择推理深度
        selected_depth = self.select_depth(resolved_tags)
        
        # 7. 组装上下文
        context = MemoryContext(
            constraints=chunks['constraints'],
            session=chunks['session'],
            preferences=chunks['preferences'],
            skills=chunks['skills'],
            cognition=chunks['cognition'],
            knowledge=chunks['knowledge'],
            instructions=instructions,
            selected_depth=selected_depth,
            activated_tags=[t.name for t in resolved_tags]
        )
        
        return context
    
    def format_context(self, context: MemoryContext) -> str:
        """
        格式化上下文为提示词
        
        Args:
            context: 记忆上下文
            
        Returns:
            格式化后的提示词
        """
        lines = ["## 激活的记忆上下文", ""]
        
        # 约束（最高优先级）
        if context.constraints:
            lines.extend(["### 🔴 强制约束（必须遵守）", ""])
            for c in context.constraints:
                lines.append(f"- {c}")
            lines.append("")
        
        # 会话上下文
        if context.session:
            lines.extend(["### 🟡 会话上下文", ""])
            for s in context.session:
                lines.append(f"- {s}")
            lines.append("")
        
        # 用户偏好
        if context.preferences:
            lines.extend(["### 🟢 用户偏好", ""])
            for p in context.preferences:
                lines.append(f"- {p}")
            lines.append("")
        
        # 能力边界
        if context.skills:
            lines.extend(["### 🔧 能力边界", ""])
            for s in context.skills:
                lines.append(f"- {s}")
            lines.append("")
        
        # 认知模式
        if context.cognition:
            lines.extend(["### 🧠 认知模式", ""])
            for c in context.cognition:
                lines.append(f"- {c}")
            lines.append("")
        
        # 动态指令
        if context.instructions:
            lines.extend(["---", "### ⚡ 动态指令", ""])
            for i, inst in enumerate(context.instructions, 1):
                lines.append(f"{i}. {inst}")
            lines.append("")
        
        # 元信息
        lines.extend([
            "---",
            f"**当前推理深度**: {context.selected_depth}",
            f"**激活标签**: {', '.join(context.activated_tags)}",
            ""
        ])
        
        return '\n'.join(lines)


# ============== 使用示例 ==============

def demo():
    """演示如何使用激活器"""
    activator = TagActivator()
    
    # 测试输入
    test_inputs = [
        "设计一个标签提取算法，从第一步开始",
        "直接告诉我这个能不能实现",
        "不对，重新分析",
        "优化我的记忆系统，让它更快"
    ]
    
    for user_input in test_inputs:
        print(f"\n{'='*60}")
        print(f"输入: {user_input}")
        print(f"{'='*60}")
        
        context = activator.activate(user_input)
        formatted = activator.format_context(context)
        print(formatted)


if __name__ == "__main__":
    demo()
