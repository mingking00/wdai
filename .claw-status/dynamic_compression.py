#!/usr/bin/env python3
"""
WDai Dynamic Compression Engine
动态压缩工作记忆到情节记忆

触发条件:
1. 对话超过10轮
2. 主题切换检测 (语义相似度<0.5)
3. 显式"总结"指令
4. 工作记忆容量>80%

输出: 压缩后的事件写入 memory/daily/YYYY-MM-DD.md
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
import hashlib
from vector_memory import VectorMemoryStore


@dataclass
class ConversationTurn:
    """单轮对话"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float
    metadata: Dict = None


@dataclass
class CompressedEvent:
    """压缩后的事件"""
    event_id: str
    event_type: str  # 'error_correction', 'decision', 'new_information', 'routine'
    summary: str
    entities: List[str]
    decisions: List[Dict]
    corrections: List[Dict]
    key_insights: List[str]
    importance_score: float
    created_at: datetime
    source_turns: int  # 原始对话轮数


class DynamicCompressionEngine:
    """动态压缩引擎"""
    
    # 重要性权重
    IMPORTANCE_WEIGHTS = {
        'error_correction': 1.0,
        'decision': 0.8,
        'new_information': 0.6,
        'routine_confirmation': 0.3
    }
    
    # 触发阈值
    TRIGGERS = {
        'turn_limit': 10,
        'capacity_threshold': 0.8,
        'topic_similarity_threshold': 0.5
    }
    
    def __init__(self, vector_store: VectorMemoryStore = None):
        self.vector_store = vector_store
        self.working_memory: List[ConversationTurn] = []
        self.current_topic: Optional[str] = None
        self.active_entities: set = set()
        
        # 简单embedding用于主题检测
        self.vocab = self._build_vocab()
    
    def _build_vocab(self) -> Dict[str, int]:
        """构建简单词表"""
        words = [
            "代码", "架构", "设计", "实现", "部署", "测试",
            "错误", "问题", "修复", "解决", "优化",
            "记忆", "向量", "检索", "压缩", "存储",
            "监控", "源", "GitHub", "B站", "YouTube",
            "工具", "技能", "学习", "进化", "改进",
        ]
        return {word: idx for idx, word in enumerate(words)}
    
    def _simple_embed(self, text: str) -> List[float]:
        """简单embedding"""
        text_lower = text.lower()
        vec = [0.0] * len(self.vocab)
        
        for word, idx in self.vocab.items():
            if word in text_lower:
                vec[idx] += 1.0
        
        # 归一化
        import math
        norm = math.sqrt(sum(x*x for x in vec))
        if norm > 0:
            vec = [x/norm for x in vec]
        return vec
    
    def add_turn(self, role: str, content: str, metadata: Dict = None):
        """添加对话轮次"""
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now().timestamp(),
            metadata=metadata or {}
        )
        self.working_memory.append(turn)
        
        # 检查是否触发压缩
        should_compress, reason = self._check_trigger()
        if should_compress:
            print(f"\n⚡ 触发压缩: {reason}")
            event = self.compress()
            self._save_event(event)
            self._clear_working_memory()
            return event
        
        return None
    
    def _check_trigger(self) -> Tuple[bool, str]:
        """检查是否触发压缩"""
        # 1. 轮数检查
        if len(self.working_memory) >= self.TRIGGERS['turn_limit']:
            return True, f"轮数超过{self.TRIGGERS['turn_limit']}"
        
        # 2. 主题切换检查
        if len(self.working_memory) >= 3:
            recent = self.working_memory[-3:]
            previous = self.working_memory[:3] if len(self.working_memory) > 6 else self.working_memory[:3]
            
            recent_text = " ".join(t.content for t in recent)
            previous_text = " ".join(t.content for t in previous)
            
            similarity = self._calculate_similarity(recent_text, previous_text)
            if similarity < self.TRIGGERS['topic_similarity_threshold']:
                return True, f"主题切换 (相似度{similarity:.2f})"
        
        return False, ""
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度"""
        vec1 = self._simple_embed(text1)
        vec2 = self._simple_embed(text2)
        
        import math
        dot = sum(a*b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a*a for a in vec1))
        norm2 = math.sqrt(sum(b*b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
    
    def compress(self) -> CompressedEvent:
        """执行压缩"""
        # 1. 提取关键信息 (基于规则，无需LLM)
        entities = self._extract_entities()
        decisions = self._extract_decisions()
        corrections = self._extract_corrections()
        insights = self._extract_insights()
        
        # 2. 生成摘要
        summary = self._generate_summary(entities, decisions, corrections)
        
        # 3. 计算重要性
        importance = self._calculate_importance(corrections, decisions, insights)
        
        # 4. 确定事件类型
        event_type = self._determine_event_type(corrections, decisions)
        
        # 5. 创建事件
        event = CompressedEvent(
            event_id=self._generate_event_id(summary),
            event_type=event_type,
            summary=summary,
            entities=list(entities),
            decisions=decisions,
            corrections=corrections,
            key_insights=insights,
            importance_score=importance,
            created_at=datetime.now(),
            source_turns=len(self.working_memory)
        )
        
        return event
    
    def _extract_entities(self) -> set:
        """提取实体 (关键词)"""
        entities = set()
        
        # 技术词汇模式
        import re
        
        # 匹配驼峰命名 (如 DynamicCompression)
        camel_pattern = re.compile(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b')
        
        # 匹配代码块中的内容
        code_pattern = re.compile(r'`([^`]+)`')
        
        # 匹配文件路径
        path_pattern = re.compile(r'\b[\w\-/]+\.(?:py|js|ts|md|json|yaml)\b')
        
        for turn in self.working_memory:
            content = turn.content
            
            # 提取驼峰命名
            entities.update(camel_pattern.findall(content))
            
            # 提取代码片段
            code_snippets = code_pattern.findall(content)
            entities.update(code_snippets)
            
            # 提取文件路径
            paths = path_pattern.findall(content)
            entities.update(paths)
            
            # 提取大写缩写 (如 API, LLM)
            acronym_pattern = re.compile(r'\b[A-Z]{2,}\b')
            entities.update(acronym_pattern.findall(content))
        
        return entities
    
    def _extract_decisions(self) -> List[Dict]:
        """提取决策点"""
        decisions = []
        
        # 决策关键词模式
        decision_markers = [
            "决定", "选择", "采用", "使用", "确定", "选定",
            "方案", "策略", "方法", "架构",
        ]
        
        for i, turn in enumerate(self.working_memory):
            if turn.role != 'user':
                content_lower = turn.content.lower()
                for marker in decision_markers:
                    if marker in content_lower:
                        # 提取包含决策的句子
                        sentences = turn.content.split('。')
                        for sent in sentences:
                            if marker in sent:
                                decisions.append({
                                    'what': sent.strip()[:200],
                                    'context': f"turn_{i}",
                                    'timestamp': turn.timestamp
                                })
                                break
                        break  # 每轮只取一个决策
        
        return decisions[:3]  # 最多3个
    
    def _extract_corrections(self) -> List[Dict]:
        """提取纠正记录"""
        corrections = []
        
        # 纠正模式：用户说"不对"、"应该"、"错误"
        correction_markers = [
            "不对", "不是", "错了", "应该", "正确",
            "修正", "改正", "更正",
        ]
        
        for i in range(1, len(self.working_memory)):
            turn = self.working_memory[i]
            if turn.role == 'user':
                content_lower = turn.content.lower()
                
                for marker in correction_markers:
                    if marker in content_lower:
                        # 获取上一轮助手回复作为"原错误"
                        prev_turn = self.working_memory[i-1]
                        if prev_turn.role == 'assistant':
                            corrections.append({
                                'original': prev_turn.content[:200],
                                'corrected': turn.content[:200],
                                'context': marker,
                                'timestamp': turn.timestamp
                            })
                        break
        
        return corrections[:3]
    
    def _extract_insights(self) -> List[str]:
        """提取关键洞察"""
        insights = []
        
        # 洞察模式
        insight_markers = [
            "原因是", "问题在于", "解决方案", "关键在于",
            "本质是", "核心", "重要", "有效",
        ]
        
        for turn in self.working_memory:
            if turn.role == 'assistant':
                for marker in insight_markers:
                    if marker in turn.content:
                        # 提取包含洞察的句子
                        sentences = turn.content.split('。')
                        for sent in sentences:
                            if marker in sent and len(sent) > 20:
                                insights.append(sent.strip()[:150])
                                break
                        break
        
        return insights[:3]
    
    def _generate_summary(
        self,
        entities: set,
        decisions: List[Dict],
        corrections: List[Dict]
    ) -> str:
        """生成事件摘要"""
        parts = []
        
        # 基于实体生成主题
        if entities:
            entity_str = ", ".join(list(entities)[:5])
            parts.append(f"涉及: {entity_str}")
        
        # 基于决策生成摘要
        if decisions:
            parts.append(f"关键决策: {decisions[0]['what'][:80]}...")
        
        # 基于纠正生成摘要
        if corrections:
            parts.append(f"重要纠正: {corrections[0]['context']}")
        
        if not parts:
            # 回退：使用最后一轮的内容
            if self.working_memory:
                last = self.working_memory[-1]
                parts.append(f"对话主题: {last.content[:100]}...")
        
        return " | ".join(parts)
    
    def _calculate_importance(
        self,
        corrections: List[Dict],
        decisions: List[Dict],
        insights: List[str]
    ) -> float:
        """计算重要性分数"""
        score = 0.0
        
        # 纠正最重要
        score += len(corrections) * self.IMPORTANCE_WEIGHTS['error_correction']
        
        # 决策次之
        score += len(decisions) * self.IMPORTANCE_WEIGHTS['decision']
        
        # 洞察
        score += len(insights) * 0.2
        
        # 对话长度奖励 (但不超过0.3)
        length_bonus = min(len(self.working_memory) * 0.02, 0.3)
        score += length_bonus
        
        return min(score, 1.0)
    
    def _determine_event_type(
        self,
        corrections: List[Dict],
        decisions: List[Dict]
    ) -> str:
        """确定事件类型"""
        if corrections:
            return 'error_correction'
        elif decisions:
            return 'decision'
        elif len(self.working_memory) > 5:
            return 'new_information'
        else:
            return 'routine'
    
    def _generate_event_id(self, summary: str) -> str:
        """生成事件ID"""
        content = f"{summary}_{datetime.now().timestamp()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _save_event(self, event: CompressedEvent):
        """保存事件到daily文件"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = Path(f"/root/.openclaw/workspace/memory/daily/{today}.md")
        
        # 确保文件存在
        if not daily_file.exists():
            daily_file.parent.mkdir(parents=True, exist_ok=True)
            daily_file.write_text(f"# {today} - 工作记录\n\n", encoding='utf-8')
        
        # 格式化事件
        event_text = self._format_event(event)
        
        # 追加到文件
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write(event_text)
        
        print(f"✅ 事件已保存到 {daily_file}")
        
        # 同时添加到向量存储
        if self.vector_store:
            from vector_memory import MemoryEntry
            entry = MemoryEntry(
                id=f"event_{event.event_id}",
                content=event.summary,
                metadata={
                    "type": "compressed_event",
                    "event_type": event.event_type,
                    "importance": event.importance_score,
                    "entities": event.entities,
                    "source_turns": event.source_turns
                },
                timestamp=event.created_at.timestamp(),
                source="semantic"
            )
            self.vector_store.add_memory(entry)
    
    def _format_event(self, event: CompressedEvent) -> str:
        """格式化事件为Markdown"""
        lines = [
            f"\n---\n",
            f"## 自动压缩事件 [{event.event_type.upper()}]\n",
            f"**时间**: {event.created_at.strftime('%H:%M')}\n",
            f"**重要性**: {event.importance_score:.2f}\n",
            f"**原始轮数**: {event.source_turns}\n\n",
            f"### 摘要\n{event.summary}\n\n",
        ]
        
        if event.entities:
            lines.append(f"### 实体\n{', '.join(event.entities)}\n\n")
        
        if event.decisions:
            lines.append("### 决策\n")
            for d in event.decisions:
                lines.append(f"- {d['what'][:100]}...\n")
            lines.append("\n")
        
        if event.corrections:
            lines.append("### 纠正\n")
            for c in event.corrections:
                lines.append(f"- **{c['context']}**: {c['corrected'][:80]}...\n")
            lines.append("\n")
        
        if event.key_insights:
            lines.append("### 洞察\n")
            for insight in event.key_insights:
                lines.append(f"- {insight}\n")
            lines.append("\n")
        
        return ''.join(lines)
    
    def _clear_working_memory(self):
        """清空工作记忆"""
        self.working_memory = []
        self.current_topic = None
        self.active_entities = set()
        print("🧹 工作记忆已清空，开始新会话块")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "working_memory_turns": len(self.working_memory),
            "current_topic": self.current_topic,
            "active_entities": len(self.active_entities),
            "triggers": self.TRIGGERS
        }


# ============ 集成到系统 ============

class CompressionManager:
    """压缩管理器 - 系统级集成"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.engine = DynamicCompressionEngine()
        self._initialized = True
    
    def on_user_message(self, content: str):
        """用户消息回调"""
        event = self.engine.add_turn('user', content)
        return event
    
    def on_assistant_message(self, content: str, metadata: Dict = None):
        """助手回复回调"""
        event = self.engine.add_turn('assistant', content, metadata)
        return event
    
    def force_compress(self) -> Optional[CompressedEvent]:
        """强制压缩当前工作记忆"""
        if len(self.engine.working_memory) < 2:
            print("⚠️ 工作记忆太短，无需压缩")
            return None
        
        event = self.engine.compress()
        self.engine._save_event(event)
        self.engine._clear_working_memory()
        return event


# ============ 测试 ============

if __name__ == "__main__":
    print("="*60)
    print("Dynamic Compression Engine - 测试")
    print("="*60)
    
    engine = DynamicCompressionEngine()
    
    # 模拟对话
    print("\n模拟对话...")
    
    messages = [
        ("user", "帮我实现一个动态压缩算法"),
        ("assistant", "好的，我可以帮你实现。动态压缩算法的核心是..."),
        ("user", "不对，应该用事件驱动而不是时间驱动"),
        ("assistant", "明白了，改为事件驱动架构。当触发条件满足时..."),
        ("user", "还有，要支持向量存储集成"),
        ("assistant", "好的，添加VectorMemoryStore集成..."),
        ("user", "什么时候能完成？"),
        ("assistant", "预计2-3天可以完成核心功能..."),
        ("user", "太慢了，今晚就要"),
        ("assistant", "那我调整优先级，今晚先完成MVP版本..."),
        ("user", "MVP要包含哪些？"),
        ("assistant", "MVP包含：1)触发检测 2)实体提取 3)摘要生成..."),
        ("user", "可以，先做这三个"),
        ("assistant", "好的，开始实现..."),
    ]
    
    for role, content in messages:
        print(f"\n{'👤' if role == 'user' else '🤖'} {content[:50]}...")
        event = engine.add_turn(role, content)
        
        if event:
            print(f"\n⚡ 压缩触发!")
            print(f"   类型: {event.event_type}")
            print(f"   重要性: {event.importance_score:.2f}")
            print(f"   摘要: {event.summary[:80]}...")
    
    # 显示统计
    print("\n" + "="*60)
    print("统计信息")
    print("="*60)
    stats = engine.get_stats()
    print(f"工作记忆轮数: {stats['working_memory_turns']}")
    print(f"活跃实体: {stats['active_entities']}")
    
    print("\n✅ 测试完成")
