#!/usr/bin/env python3
"""
Pattern Accumulation System - 模式积累系统
将学习到的经验转化为可复用的模式
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class LearnedPattern:
    """学习到的模式"""
    pattern_id: str
    pattern_type: str  # 'correction', 'preference', 'context', 'strategy'
    trigger: str       # 触发条件
    action: str        # 应对策略
    confidence: float  # 置信度 (0-1)
    usage_count: int
    last_used: str
    success_rate: float

class PatternAccumulation:
    """
    模式积累系统
    
    功能：
    1. 将反馈转化为结构化模式
    2. 模式匹配和应用
    3. 模式效果追踪
    4. 定期模式优化
    """
    
    def __init__(self, storage_dir: str = ".learning/patterns"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.patterns_file = self.storage_dir / "accumulated_patterns.json"
        self.patterns: Dict[str, LearnedPattern] = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """加载已积累的模式"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for pid, pdata in data.items():
                    self.patterns[pid] = LearnedPattern(**pdata)
    
    def _save_patterns(self):
        """保存模式"""
        data = {pid: {
            'pattern_id': p.pattern_id,
            'pattern_type': p.pattern_type,
            'trigger': p.trigger,
            'action': p.action,
            'confidence': p.confidence,
            'usage_count': p.usage_count,
            'last_used': p.last_used,
            'success_rate': p.success_rate
        } for pid, p in self.patterns.items()}
        
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_pattern(
        self,
        pattern_type: str,
        trigger: str,
        action: str,
        confidence: float = 0.7
    ) -> str:
        """
        添加新模式
        
        Args:
            pattern_type: 模式类型 (correction/preference/context/strategy)
            trigger: 触发条件描述
            action: 应对策略
            confidence: 初始置信度
        
        Returns:
            pattern_id: 新模式ID
        """
        pattern_id = f"pat_{int(datetime.now().timestamp())}"
        
        pattern = LearnedPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            trigger=trigger,
            action=action,
            confidence=confidence,
            usage_count=0,
            last_used=datetime.now().isoformat(),
            success_rate=0.0
        )
        
        self.patterns[pattern_id] = pattern
        self._save_patterns()
        
        return pattern_id
    
    def match_patterns(self, query: str, context: Dict = None) -> List[LearnedPattern]:
        """
        匹配查询相关的模式
        
        Args:
            query: 用户查询
            context: 上下文信息
        
        Returns:
            匹配的模式列表（按置信度排序）
        """
        matched = []
        
        for pattern in self.patterns.values():
            # 简单关键词匹配（实际可用更复杂的NLP）
            trigger_keywords = pattern.trigger.lower().split()
            query_lower = query.lower()
            
            match_score = sum(1 for kw in trigger_keywords if kw in query_lower)
            
            if match_score > 0:
                # 计算匹配度
                relevance = match_score / len(trigger_keywords)
                combined_score = relevance * pattern.confidence * pattern.success_rate
                
                if combined_score > 0.3:  # 阈值
                    matched.append((pattern, combined_score))
        
        # 按综合得分排序
        matched.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in matched[:3]]  # 返回Top3
    
    def apply_pattern(self, pattern_id: str) -> Optional[str]:
        """
        应用模式并追踪效果
        
        Args:
            pattern_id: 模式ID
        
        Returns:
            应对策略，如果模式不存在返回None
        """
        if pattern_id not in self.patterns:
            return None
        
        pattern = self.patterns[pattern_id]
        pattern.usage_count += 1
        pattern.last_used = datetime.now().isoformat()
        self._save_patterns()
        
        return pattern.action
    
    def report_success(self, pattern_id: str, success: bool):
        """
        报告模式应用结果
        
        Args:
            pattern_id: 模式ID
            success: 是否成功
        """
        if pattern_id not in self.patterns:
            return
        
        pattern = self.patterns[pattern_id]
        
        # 更新成功率（指数移动平均）
        alpha = 0.3  # 学习率
        current = 1.0 if success else 0.0
        pattern.success_rate = (1 - alpha) * pattern.success_rate + alpha * current
        
        # 更新置信度
        if pattern.success_rate > 0.8 and pattern.usage_count > 5:
            pattern.confidence = min(0.95, pattern.confidence + 0.05)
        elif pattern.success_rate < 0.3:
            pattern.confidence = max(0.3, pattern.confidence - 0.1)
        
        self._save_patterns()
    
    def get_pattern_stats(self) -> Dict:
        """获取模式统计"""
        if not self.patterns:
            return {"total": 0, "by_type": {}}
        
        by_type = {}
        for p in self.patterns.values():
            by_type[p.pattern_type] = by_type.get(p.pattern_type, 0) + 1
        
        total_usage = sum(p.usage_count for p in self.patterns.values())
        avg_confidence = sum(p.confidence for p in self.patterns.values()) / len(self.patterns)
        
        return {
            "total_patterns": len(self.patterns),
            "by_type": by_type,
            "total_applications": total_usage,
            "avg_confidence": avg_confidence,
            "high_confidence_patterns": sum(1 for p in self.patterns.values() if p.confidence > 0.8)
        }
    
    def export_patterns_for_prompt(self) -> str:
        """
        将高置信度模式导出为提示词格式
        
        用于增强后续回答
        """
        high_conf_patterns = [
            p for p in self.patterns.values()
            if p.confidence > 0.7 and p.success_rate > 0.6
        ]
        
        if not high_conf_patterns:
            return ""
        
        lines = ["\n🧠 **基于历史学习的建议**:\n"]
        
        for p in high_conf_patterns[:5]:  # 最多5个
            lines.append(f"- 当{p.trigger}时，{p.action} (置信度: {p.confidence:.0%})")
        
        return "\n".join(lines)

def demo():
    """演示模式积累"""
    print("=" * 70)
    print("🧬 模式积累系统演示")
    print("=" * 70)
    
    accumulation = PatternAccumulation()
    
    # 添加一些学习到的模式
    print("\n【添加学习模式】")
    
    patterns_to_add = [
        ("correction", "股市 明天 预测", "应该询问分析方法而非预测", 0.8),
        ("preference", "天气", "提供查询方法而非直接回答", 0.7),
        ("strategy", "学习 怎么", "提供学习路径而非直接答案", 0.75),
    ]
    
    for ptype, trigger, action, conf in patterns_to_add:
        pid = accumulation.add_pattern(ptype, trigger, action, conf)
        print(f"✓ 添加模式: {trigger[:20]}... (ID: {pid[:10]})")
    
    # 模拟匹配
    print("\n【模式匹配测试】")
    test_queries = [
        "明天股市会涨吗？",
        "今天天气怎么样？",
        "如何学习Python？"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        matches = accumulation.match_patterns(query)
        if matches:
            for p in matches:
                print(f"  → 匹配: {p.action[:40]}...")
        else:
            print("  → 无匹配模式")
    
    # 显示统计
    print("\n" + "-" * 70)
    print("【模式统计】")
    stats = accumulation.get_pattern_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 导出为提示词
    print("\n【导出提示词】")
    prompt_addition = accumulation.export_patterns_for_prompt()
    print(prompt_addition)

if __name__ == "__main__":
    demo()
