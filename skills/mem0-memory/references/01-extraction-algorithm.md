# mem0-memory 提取算法详解

## 核心设计原则

提取算法是记忆系统的"入口守门人"——它决定了什么值得记住，什么应该丢弃。

设计原则：
1. **原子性** - 提取最小可复用事实，而非长段落
2. **置信度** - 每条记忆必须有置信度分数
3. **去重** - 避免重复存储相似信息
4. **结构化** - 分类标签便于后续检索

---

## 两阶段提取流程

```
对话输入
    ↓
[阶段1: 候选生成]  ← LLM提取事实
    ↓
候选记忆列表
    ↓
[阶段2: 质量过滤]  ← 去重 + 置信度阈值
    ↓
最终记忆列表 → 存储
```

---

## 完整代码实现

### 1. 核心提取器 (`extractor.py`)

```python
"""
Mem0-inspired Memory Extraction Algorithm
基于论文: https://arxiv.org/abs/2409.19113
"""

import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from dataclasses import dataclass, asdict
import re

# ============ 数据模型 ============

class MemoryCategory:
    """记忆类别 - 用于分类和检索优化"""
    PREFERENCE = "preference"      # 用户偏好
    FACT = "fact"                  # 客观事实
    GOAL = "goal"                  # 目标/意图
    CONSTRAINT = "constraint"      # 约束/限制
    RELATIONSHIP = "relationship"  # 关系定义
    PROCEDURE = "procedure"        # 流程/步骤
    LEARNING = "learning"          # 学习到的模式

class Memory(BaseModel):
    """原子记忆单元"""
    id: str = Field(description="UUID或内容哈希")
    user_id: str = Field(description="用户标识")
    content: str = Field(description="记忆内容，简洁陈述")
    category: str = Field(default=MemoryCategory.FACT)
    importance: float = Field(default=0.5, ge=0, le=1)
    confidence: float = Field(default=0.8, ge=0, le=1)
    source: str = Field(description="来源消息ID或会话ID")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    access_count: int = Field(default=0)
    last_accessed: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    
    # 元数据
    metadata: Dict = Field(default_factory=dict)
    
    def compute_hash(self) -> str:
        """计算内容哈希用于去重"""
        content_normalized = self.content.lower().strip()
        return hashlib.md5(content_normalized.encode()).hexdigest()[:12]

class ExtractionResult(BaseModel):
    """提取结果"""
    memories: List[Memory]
    discarded: List[Dict]  # 被丢弃的候选及原因
    stats: Dict

# ============ 阶段1: 候选生成 ============

EXTRACTION_PROMPT = """You are a memory extraction system. Your task is to extract atomic, factual memories from the conversation.

## Extraction Rules:

1. **ATOMIC**: Each memory should be a single, indivisible fact
   - GOOD: "User prefers Python over JavaScript"
   - BAD: "User prefers Python and uses VS Code and works at Google" (split into 3)

2. **FACTUAL**: Extract objective statements, not interpretations
   - GOOD: "User said they find React confusing"
   - BAD: "User hates React" (too interpretive)

3. **CONTEXTUAL**: Include necessary context
   - GOOD: "User's project deadline is March 15, 2026"
   - BAD: "Deadline is March 15" (missing year/context)

4. **CATEGORIES**: Assign one category per memory:
   - preference: User likes/dislikes, choices, priorities
   - fact: Objective information about user/project
   - goal: User's objectives, targets, desired outcomes
   - constraint: Limitations, requirements, rules
   - relationship: Connections between entities
   - procedure: Steps, processes, workflows
   - learning: Patterns, insights, lessons learned

## Output Format:

Return a JSON array of memories:

```json
[
  {
    "content": "concise factual statement",
    "category": "preference|fact|goal|constraint|relationship|procedure|learning",
    "importance": 0.0-1.0,
    "confidence": 0.0-1.0,
    "reasoning": "why this is worth remembering"
  }
]
```

## Conversation:

{conversation}

Extract memories (return empty array if nothing memorable):"""

class LLMExtractor:
    """LLM-based candidate generation"""
    
    def __init__(self, llm_client):
        self.llm = llm_client
        
    def extract_candidates(self, messages: List[Dict], user_id: str) -> List[Memory]:
        """
        阶段1: 从对话中提取候选记忆
        """
        # 格式化对话
        conversation = self._format_conversation(messages)
        
        # 调用LLM
        prompt = EXTRACTION_PROMPT.format(conversation=conversation)
        response = self.llm.complete(prompt, response_format="json")
        
        # 解析结果
        try:
            candidates_data = json.loads(response)
        except json.JSONDecodeError:
            # 容错：尝试从文本中提取JSON
            candidates_data = self._extract_json_fallback(response)
        
        # 转换为Memory对象
        candidates = []
        for i, data in enumerate(candidates_data):
            memory = Memory(
                id=f"{user_id}_{datetime.now().strftime('%Y%m%d')}_{i}",
                user_id=user_id,
                content=data["content"],
                category=data.get("category", MemoryCategory.FACT),
                importance=data.get("importance", 0.5),
                confidence=data.get("confidence", 0.8),
                source=messages[-1].get("id", "unknown"),
                tags=self._auto_generate_tags(data["content"]),
                metadata={
                    "extraction_reasoning": data.get("reasoning", ""),
                    "raw_timestamp": datetime.now().isoformat()
                }
            )
            memory.id = memory.compute_hash()  # 使用内容哈希作为ID
            candidates.append(memory)
        
        return candidates
    
    def _format_conversation(self, messages: List[Dict]) -> str:
        """格式化对话为提示文本"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"[{role.upper()}]: {content}")
        return "\n\n".join(formatted)
    
    def _extract_json_fallback(self, text: str) -> List[Dict]:
        """容错：从文本中提取JSON数组"""
        # 查找方括号包裹的内容
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return []
    
    def _auto_generate_tags(self, content: str) -> List[str]:
        """自动生成标签"""
        tags = []
        content_lower = content.lower()
        
        # 技术栈标签
        tech_keywords = ["python", "javascript", "typescript", "react", "vue", 
                        "docker", "kubernetes", "aws", "gcp", "azure"]
        for tech in tech_keywords:
            if tech in content_lower:
                tags.append(tech)
        
        # 主题标签
        if any(word in content_lower for word in ["like", "prefer", "favorite", "enjoy"]):
            tags.append("preference")
        if any(word in content_lower for word in ["deadline", "due", "schedule", "timeline"]):
            tags.append("timeline")
        if any(word in content_lower for word in ["problem", "issue", "bug", "error"]):
            tags.append("issue")
            
        return tags[:5]  # 最多5个标签

# ============ 阶段2: 质量过滤 ============

class QualityFilter:
    """
    阶段2: 质量过滤和去重
    
    过滤维度:
    1. 置信度阈值 (confidence < 0.6 丢弃)
    2. 内容质量 (过短/过长/无意义内容)
    3. 去重 (与已有记忆相似度 > 0.85 视为重复)
    4. 时效性检查 (过期信息)
    """
    
    def __init__(self, existing_memories: Optional[List[Memory]] = None):
        self.existing = existing_memories or []
        self.discarded = []
        
    def filter(self, candidates: List[Memory]) -> List[Memory]:
        """主过滤流程"""
        filtered = []
        
        for candidate in candidates:
            # 检查1: 置信度阈值
            if not self._check_confidence(candidate):
                continue
                
            # 检查2: 内容质量
            if not self._check_content_quality(candidate):
                continue
                
            # 检查3: 去重
            if self._is_duplicate(candidate):
                continue
                
            # 检查4: 一致性验证
            if not self._check_consistency(candidate):
                continue
            
            filtered.append(candidate)
        
        return filtered
    
    def _check_confidence(self, memory: Memory) -> bool:
        """置信度检查"""
        MIN_CONFIDENCE = 0.6
        
        if memory.confidence < MIN_CONFIDENCE:
            self.discarded.append({
                "memory": memory.content,
                "reason": f"confidence too low ({memory.confidence:.2f} < {MIN_CONFIDENCE})"
            })
            return False
        return True
    
    def _check_content_quality(self, memory: Memory) -> bool:
        """内容质量检查"""
        content = memory.content.strip()
        
        # 长度检查
        if len(content) < 10:
            self.discarded.append({
                "memory": content,
                "reason": "content too short (< 10 chars)"
            })
            return False
            
        if len(content) > 500:
            self.discarded.append({
                "memory": content[:50] + "...",
                "reason": "content too long (> 500 chars)"
            })
            return False
        
        # 无意义内容检查
        meaningless_patterns = [
            r"^\d+$",  # 纯数字
            r"^[^a-zA-Z0-9]+$",  # 无字母数字
            r"^(hi|hello|hey|ok|okay|yes|no|thanks|thank you)[!.]?$",  # 简单问候
        ]
        
        for pattern in meaningless_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                self.discarded.append({
                    "memory": content,
                    "reason": "meaningless content pattern"
                })
                return False
        
        return True
    
    def _is_duplicate(self, candidate: Memory) -> bool:
        """
        去重检查
        使用内容哈希 + 语义相似度双重检查
        """
        candidate_hash = candidate.compute_hash()
        
        for existing in self.existing:
            # 检查1: 哈希完全匹配
            if existing.compute_hash() == candidate_hash:
                self.discarded.append({
                    "memory": candidate.content,
                    "reason": "exact duplicate (hash match)",
                    "matches": existing.content
                })
                return True
            
            # 检查2: 语义相似度 (简化版，实际应使用embedding)
            similarity = self._text_similarity(candidate.content, existing.content)
            if similarity > 0.85:
                self.discarded.append({
                    "memory": candidate.content,
                    "reason": f"semantic duplicate (similarity: {similarity:.2f})",
                    "matches": existing.content
                })
                return True
        
        return False
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        简化版文本相似度 (Jaccard相似度)
        实际生产环境应使用embedding余弦相似度
        """
        # 标准化
        t1 = set(text1.lower().split())
        t2 = set(text2.lower().split())
        
        if not t1 or not t2:
            return 0.0
        
        intersection = len(t1 & t2)
        union = len(t1 | t2)
        
        return intersection / union if union > 0 else 0.0
    
    def _check_consistency(self, candidate: Memory) -> bool:
        """
        一致性检查
        检测是否与已有记忆矛盾
        """
        # 简化实现：检查是否有直接矛盾的表述
        # 实际应使用LLM进行矛盾检测
        
        contradiction_patterns = [
            (r"prefer\s+(\w+)", r"prefer\s+(\w+)", 1),  # 偏好矛盾
        ]
        
        for existing in self.existing:
            for pattern1, pattern2, group_idx in contradiction_patterns:
                m1 = re.search(pattern1, candidate.content, re.IGNORECASE)
                m2 = re.search(pattern2, existing.content, re.IGNORECASE)
                
                if m1 and m2:
                    val1 = m1.group(group_idx).lower()
                    val2 = m2.group(group_idx).lower()
                    
                    # 如果两个偏好不同，可能是更新而非矛盾
                    # 这里简化处理，实际应交给冲突解决模块
                    if val1 != val2 and candidate.category == "preference":
                        # 标记为潜在更新而非丢弃
                        candidate.metadata["potential_update_of"] = existing.id
        
        return True

# ============ 主提取流程 ============

class MemoryExtractor:
    """
    完整提取管道
    """
    
    def __init__(self, llm_client, vector_store=None):
        self.llm_extractor = LLMExtractor(llm_client)
        self.vector_store = vector_store
        
    def extract(self, 
                messages: List[Dict], 
                user_id: str,
                min_confidence: float = 0.6) -> ExtractionResult:
        """
        执行完整提取流程
        
        Args:
            messages: 对话消息列表
            user_id: 用户标识
            min_confidence: 最小置信度阈值
            
        Returns:
            ExtractionResult: 提取结果
        """
        # 获取已有记忆用于去重
        existing_memories = []
        if self.vector_store:
            existing_memories = self.vector_store.get_user_memories(user_id)
        
        # 阶段1: 候选生成
        print(f"[Extract] Phase 1: Generating candidates from {len(messages)} messages...")
        candidates = self.llm_extractor.extract_candidates(messages, user_id)
        print(f"[Extract] Generated {len(candidates)} candidates")
        
        # 阶段2: 质量过滤
        print(f"[Extract] Phase 2: Quality filtering...")
        quality_filter = QualityFilter(existing_memories)
        filtered = quality_filter.filter(candidates)
        print(f"[Extract] Filtered to {len(filtered)} memories ({len(quality_filter.discarded)} discarded)")
        
        return ExtractionResult(
            memories=filtered,
            discarded=quality_filter.discarded,
            stats={
                "input_messages": len(messages),
                "candidates_generated": len(candidates),
                "final_memories": len(filtered),
                "discarded": len(quality_filter.discarded),
                "duplicate_rate": len(quality_filter.discarded) / max(len(candidates), 1)
            }
        )

# ============ 使用示例 ============

if __name__ == "__main__":
    # 模拟对话
    conversation = [
        {"role": "user", "content": "你好，我在做一个Python项目，需要用Docker部署"},
        {"role": "assistant", "content": "好的，我可以帮你设置Docker配置。你对Python和Docker的熟悉程度如何？"},
        {"role": "user", "content": "我Python很熟练，但Docker是新手。另外我更喜欢用VS Code而不是PyCharm"},
        {"role": "assistant", "content": "了解，那我会提供详细的Docker步骤。VS Code确实有很好的Docker插件支持。"},
        {"role": "user", "content": "项目deadline是下个月15号，所以希望能快速上手"}
    ]
    
    # 提取
    extractor = MemoryExtractor(llm_client=None)  # 实际需传入LLM客户端
    result = extractor.extract(conversation, user_id="user_123")
    
    print("\n=== 提取结果 ===")
    for mem in result.memories:
        print(f"\n[{mem.category}] {mem.content}")
        print(f"  importance: {mem.importance}, confidence: {mem.confidence}")
        print(f"  tags: {mem.tags}")
    
    print(f"\n=== 统计 ===")
    print(json.dumps(result.stats, indent=2))
```

---

## 关键设计决策

### 1. 为什么用两阶段？

| 阶段 | 职责 | 优势 |
|------|------|------|
| 阶段1 (LLM) | 创造性提取 | 利用LLM理解上下文，提取复杂语义 |
| 阶段2 (规则) | 质量控制 | 确定性过滤，可解释，低成本 |

### 2. 置信度 vs 重要性

```
confidence (置信度)
  └── 这条记忆是否准确反映了对话？
  └── 由LLM根据上下文清晰度评估

importance (重要性)  
  └── 这条记忆有多重要？值得长期保留吗？
  └── 由LLM根据用户意图评估

示例:
- "用户说可能喜欢用Python" → confidence=0.6, importance=0.4 (不确定)
- "用户明确表示Python是唯一选择" → confidence=0.95, importance=0.9 (确定且重要)
```

### 3. 去重策略

```
Level 1: 哈希匹配 (O(1))
  └── 完全相同的内容
  
Level 2: 语义相似度 (O(n))
  └── embedding余弦相似度 > 0.85
  └── 或简化版Jaccard相似度
  
Level 3: 矛盾检测 (LLM)
  └── 新旧记忆是否矛盾？
  └── 矛盾时保留置信度高的
```

---

## 性能优化

### 批处理
```python
# 大量对话时批量处理
BATCH_SIZE = 5  # 每5轮对话提取一次
```

### 增量提取
```python
# 只提取新消息，避免重复处理历史
def extract_incremental(new_messages, last_extracted_id):
    # 只处理last_extracted_id之后的消息
    pass
```

---

## 下一步

提取后的记忆进入存储层 → `store.py`