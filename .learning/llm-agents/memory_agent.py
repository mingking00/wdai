"""
Advanced Agent with Memory System
进阶Agent实现 - 包含短期和长期记忆

扩展功能:
- Short-term Memory (Working Memory)
- Long-term Memory (Retrieval)
- Reflection Capabilities
"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import deque
import numpy as np


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    memory_type: str  # "short_term" or "long_term"
    importance: float  # 0-10
    timestamp: str
    tags: List[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed: str = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp


class MemorySystem:
    """
    记忆系统 - 管理短期和长期记忆
    
    设计理念:
    - 短期记忆: 有限的上下文窗口，用于当前任务
    - 长期记忆: 持久化存储，可检索历史信息
    - 记忆衰减: 不常用的记忆会逐渐淡出
    """
    
    def __init__(
        self,
        short_term_capacity: int = 5,
        long_term_capacity: int = 100,
        decay_rate: float = 0.1
    ):
        self.short_term: deque = deque(maxlen=short_term_capacity)
        self.long_term: List[MemoryEntry] = []
        self.long_term_capacity = long_term_capacity
        self.decay_rate = decay_rate
        self.memory_index: Dict[str, MemoryEntry] = {}
    
    def add_to_short_term(self, content: str, importance: float = 5.0) -> str:
        """添加到短期记忆"""
        entry = MemoryEntry(
            id=str(uuid.uuid4())[:8],
            content=content,
            memory_type="short_term",
            importance=importance,
            timestamp=datetime.now().isoformat(),
            tags=self._extract_tags(content)
        )
        self.short_term.append(entry)
        self.memory_index[entry.id] = entry
        return entry.id
    
    def add_to_long_term(self, content: str, importance: float = 7.0) -> str:
        """添加到长期记忆"""
        # 如果达到容量上限，移除最不重要的记忆
        if len(self.long_term) >= self.long_term_capacity:
            self._prune_long_term_memory()
        
        entry = MemoryEntry(
            id=str(uuid.uuid4())[:8],
            content=content,
            memory_type="long_term",
            importance=importance,
            timestamp=datetime.now().isoformat(),
            tags=self._extract_tags(content)
        )
        self.long_term.append(entry)
        self.memory_index[entry.id] = entry
        return entry.id
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[MemoryEntry, float]]:
        """
        检索相关记忆
        
        使用简单的关键词匹配 + 重要性加权
        实际应用中可以使用向量相似度
        """
        query_terms = set(query.lower().split())
        scored_memories = []
        
        # 搜索所有记忆
        all_memories = list(self.short_term) + self.long_term
        
        for entry in all_memories:
            # 计算相关性得分
            content_terms = set(entry.content.lower().split())
            tag_terms = set(tag.lower() for tag in entry.tags)
            
            overlap = len(query_terms & content_terms) + len(query_terms & tag_terms) * 2
            relevance = overlap / max(len(query_terms), 1)
            
            # 重要性加权
            importance_weight = entry.importance / 10.0
            
            # 时间衰减
            age_hours = self._calculate_age_hours(entry.timestamp)
            recency_weight = np.exp(-self.decay_rate * age_hours)
            
            # 访问频率加权
            access_weight = min(entry.access_count / 10.0, 1.0)
            
            # 综合得分
            score = (relevance * 0.4 + importance_weight * 0.3 + 
                    recency_weight * 0.2 + access_weight * 0.1)
            
            scored_memories.append((entry, score))
            
            # 更新访问信息
            if relevance > 0:
                entry.access_count += 1
                entry.last_accessed = datetime.now().isoformat()
        
        # 按得分排序并返回top_k
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories[:top_k]
    
    def consolidate(self) -> List[str]:
        """
        记忆巩固 - 将重要的短期记忆转移到长期记忆
        
        模拟睡眠时的记忆巩固过程
        """
        consolidated_ids = []
        
        for entry in list(self.short_term):
            if entry.importance >= 6.0 or entry.access_count >= 2:
                # 转移到长期记忆
                new_id = self.add_to_long_term(
                    content=entry.content,
                    importance=entry.importance
                )
                consolidated_ids.append(new_id)
        
        # 清空短期记忆
        self.short_term.clear()
        
        return consolidated_ids
    
    def get_short_term_context(self) -> str:
        """获取短期记忆作为上下文"""
        if not self.short_term:
            return "(无短期记忆)"
        
        context_parts = []
        for i, entry in enumerate(self.short_term, 1):
            context_parts.append(f"{i}. {entry.content}")
        
        return "\n".join(context_parts)
    
    def _prune_long_term_memory(self):
        """修剪长期记忆 - 移除最不重要的"""
        # 按重要性+访问频率排序
        self.long_term.sort(
            key=lambda e: (e.importance + min(e.access_count, 10)) / 2,
            reverse=True
        )
        # 保留前80%
        keep_count = int(self.long_term_capacity * 0.8)
        removed = self.long_term[keep_count:]
        self.long_term = self.long_term[:keep_count]
        
        # 清理索引
        for entry in removed:
            self.memory_index.pop(entry.id, None)
    
    def _extract_tags(self, content: str) -> List[str]:
        """从内容中提取标签"""
        # 简单实现：提取关键词作为标签
        keywords = ["agent", "tool", "memory", "task", "user", "system"]
        tags = [kw for kw in keywords if kw in content.lower()]
        return tags[:3]  # 最多3个标签
    
    def _calculate_age_hours(self, timestamp: str) -> float:
        """计算记忆年龄（小时）"""
        try:
            created = datetime.fromisoformat(timestamp)
            age = datetime.now() - created
            return age.total_seconds() / 3600
        except:
            return 0.0
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计"""
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "total_memories": len(self.memory_index),
            "short_term_capacity": self.short_term.maxlen,
            "long_term_capacity": self.long_term_capacity,
            "avg_importance": np.mean([e.importance for e in self.long_term]) if self.long_term else 0
        }


class ReflectiveAgent:
    """
    反思型Agent
    
    扩展ReAct，添加:
    - 工作记忆系统
    - 任务完成后反思
    - 从经验中学习
    """
    
    def __init__(self, name: str = "ReflectiveAgent"):
        self.name = name
        self.memory = MemorySystem(
            short_term_capacity=7,
            long_term_capacity=50
        )
        self.task_history: List[Dict] = []
        self.reflections: List[str] = []
    
    def execute_task(self, task: str, tools: Dict[str, callable]) -> Dict:
        """
        执行任务并记录到记忆
        
        Args:
            task: 任务描述
            tools: 可用工具字典
            
        Returns:
            任务执行结果
        """
        print(f"\n🎯 执行任务: {task}")
        
        # 检索相关历史记忆
        relevant_memories = self.memory.retrieve(task, top_k=3)
        if relevant_memories:
            print("📚 检索到相关记忆:")
            for mem, score in relevant_memories:
                print(f"   - {mem.content[:50]}... (相关度: {score:.2f})")
        
        # 添加到短期记忆
        self.memory.add_to_short_term(
            content=f"开始任务: {task}",
            importance=8.0
        )
        
        # 模拟任务执行（实际应用中使用LLM）
        result = self._simulate_execution(task, tools)
        
        # 记录结果
        task_record = {
            "id": str(uuid.uuid4())[:8],
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "relevant_memories": [m[0].id for m in relevant_memories]
        }
        self.task_history.append(task_record)
        
        # 添加到记忆
        self.memory.add_to_short_term(
            content=f"任务完成: {task} -> {result}",
            importance=7.0
        )
        
        print(f"✅ 结果: {result}")
        
        return task_record
    
    def _simulate_execution(self, task: str, tools: Dict[str, callable]) -> str:
        """模拟任务执行"""
        # 这里应该调用实际的LLM和工具
        # 现在用简单逻辑演示
        
        if "计算" in task:
            return "使用calculator工具完成计算"
        elif "搜索" in task or "查询" in task:
            return "使用search工具获取信息"
        else:
            return "任务已处理"
    
    def reflect(self) -> str:
        """
        反思最近的任务
        
        分析执行历史，生成洞察
        """
        if not self.task_history:
            return "没有任务历史可供反思"
        
        print("\n🤔 开始反思...")
        
        # 分析最近的任务
        recent_tasks = self.task_history[-5:]
        
        # 生成反思
        patterns = self._identify_patterns(recent_tasks)
        insights = self._generate_insights(patterns)
        
        reflection = f"""
反思报告 ({datetime.now().isoformat()}):
================================
分析任务数: {len(recent_tasks)}

识别到的模式:
{chr(10).join(f"- {p}" for p in patterns)}

洞察:
{chr(10).join(f"- {i}" for i in insights)}

改进建议:
- 继续优化常用工具的使用
- 加强任务间的关联记忆
- 定期巩固重要信息到长期记忆
"""
        
        self.reflections.append(reflection)
        
        # 将反思添加到长期记忆
        self.memory.add_to_long_term(
            content=f"反思: 最近{len(recent_tasks)}个任务的模式分析",
            importance=9.0
        )
        
        # 触发记忆巩固
        consolidated = self.memory.consolidate()
        print(f"💾 记忆巩固完成，转移了 {len(consolidated)} 条记忆到长期存储")
        
        return reflection
    
    def _identify_patterns(self, tasks: List[Dict]) -> List[str]:
        """识别任务模式"""
        patterns = []
        
        # 简单模式识别
        tool_usage = {}
        for task in tasks:
            task_text = task["task"].lower()
            if "计算" in task_text:
                tool_usage["calculator"] = tool_usage.get("calculator", 0) + 1
            if "搜索" in task_text:
                tool_usage["search"] = tool_usage.get("search", 0) + 1
        
        if tool_usage:
            most_used = max(tool_usage.items(), key=lambda x: x[1])
            patterns.append(f"最常使用工具: {most_used[0]} ({most_used[1]}次)")
        
        patterns.append(f"平均任务复杂度: {sum(len(t['task']) for t in tasks) / len(tasks):.1f}字符")
        
        return patterns
    
    def _generate_insights(self, patterns: List[str]) -> List[str]:
        """生成洞察"""
        insights = []
        
        if len(self.task_history) > 3:
            insights.append("任务执行效率随着经验积累而提升")
        
        if any("计算" in p for p in patterns):
            insights.append("数学计算类任务占比较高，可优化相关工具")
        
        insights.append("任务间关联性有待加强，建议改进记忆检索策略")
        
        return insights
    
    def get_memory_context(self) -> str:
        """获取记忆上下文"""
        return f"""
短期记忆:
{self.memory.get_short_term_context()}

记忆统计:
{json.dumps(self.memory.get_memory_stats(), indent=2)}
"""


def demo_memory_system():
    """演示记忆系统"""
    
    print("=" * 60)
    print("🧠 Advanced Agent with Memory System")
    print("=" * 60)
    
    # 创建Agent
    agent = ReflectiveAgent(name="MemoAgent")
    
    # 定义工具
    tools = {
        "calculator": lambda x: f"计算结果: {x}",
        "search": lambda x: f"搜索结果: {x}",
        "memory": lambda x: agent.memory.retrieve(x)
    }
    
    # 执行任务序列
    tasks = [
        "计算 25 * 16",
        "搜索 ReAct论文相关信息",
        "计算 100 / 4",
        "查询之前的计算结果",
        "搜索 LLM agent最新进展",
        "计算 3.14159 * 2",
    ]
    
    for task in tasks:
        agent.execute_task(task, tools)
    
    # 显示记忆状态
    print("\n" + "=" * 60)
    print("📊 记忆系统状态")
    print("=" * 60)
    print(agent.get_memory_context())
    
    # 执行反思
    print("\n" + "=" * 60)
    reflection = agent.reflect()
    print(reflection)
    
    # 测试记忆检索
    print("\n" + "=" * 60)
    print("🔍 测试记忆检索")
    print("=" * 60)
    
    queries = ["计算", "搜索", "ReAct"]
    for query in queries:
        print(f"\n查询: '{query}'")
        results = agent.memory.retrieve(query, top_k=2)
        for mem, score in results:
            print(f"  → {mem.content[:60]}... (得分: {score:.3f})")


if __name__ == "__main__":
    demo_memory_system()
