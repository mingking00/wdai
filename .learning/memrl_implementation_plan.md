# MemRL 借鉴实施方案
# 下次重启自动执行

> 目标: 将MemRL的Q值机制和自动反馈闭环集成到现有系统
> 执行方式: 下次重启时通过AGENTS.md自动加载
> 创建时间: 2026-03-16

---

## 实施阶段规划

```
阶段1 (重启后自动执行): 基础设施搭建
  ├─ 创建记忆Q值存储结构
  ├─ 初始化现有记忆的Q值
  └─ 创建Q值更新模块

阶段2 (1周内): 两阶段检索实现
  ├─ 修改memory_search工具
  ├─ 实现语义+Q值混合排序
  └─ A/B测试验证效果

阶段3 (2周内): 自动反馈闭环
  ├─ 任务追踪系统集成
  ├─ 结果验证器实现
  └─ Coordinator Agent集成

阶段4 (持续): 优化调参
  ├─ Lambda权重调优
  ├─ 学习率Alpha调优
  └─ 记忆衰减策略
```

---

## 阶段1详细设计: 基础设施

### 1.1 记忆Q值数据结构

```json
// memory/core/skills_with_q.json (新文件)
{
  "version": "1.0",
  "schema": "skill_with_q",
  "skills": [
    {
      "id": "skill_deploy_001",
      "content": "用git push部署到GitHub",
      "embedding": [0.1, 0.2, ...],  // 向量表示
      "q_value": 0.85,              // ★ 效用值 (0-1)
      "usage_count": 12,            // 使用次数
      "success_count": 11,          // 成功次数
      "fail_count": 1,              // 失败次数
      "created_at": "2026-03-10",
      "last_used": "2026-03-16",
      "last_updated": "2026-03-16",
      "source": "MEMORY.md",        // 来源
      "tags": ["deploy", "git", "github"]
    }
  ]
}
```

### 1.2 核心模块设计

```python
# .claw-status/memrl_memory.py
class MemRLMemory:
    """MemRL风格的记忆管理系统"""
    
    def __init__(self, alpha=0.1, lambda_weight=0.5):
        self.alpha = alpha          # Q值学习率
        self.lambda_weight = lambda_weight  # 语义vs效用权重
        self.memory_file = "memory/core/skills_with_q.json"
        self.memories = self._load_memories()
    
    def _load_memories(self) -> List[Dict]:
        """加载带Q值的记忆"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file) as f:
                data = json.load(f)
                return data.get("skills", [])
        return []
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        两阶段检索:
        1. 语义召回 (Top 20)
        2. Q值重排 (Top k)
        """
        # 阶段A: 语义召回
        query_embedding = self._embed(query)
        candidates = []
        
        for memory in self.memories:
            similarity = cosine_similarity(
                query_embedding, 
                memory["embedding"]
            )
            if similarity > 0.5:  # 阈值
                candidates.append({
                    "memory": memory,
                    "similarity": similarity
                })
        
        # 按相似度排序，取top-20
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        candidates = candidates[:20]
        
        # 阶段B: Q值重排
        for cand in candidates:
            q_value = cand["memory"].get("q_value", 0.5)
            # 综合得分
            cand["final_score"] = (
                (1 - self.lambda_weight) * cand["similarity"] +
                self.lambda_weight * q_value
            )
        
        # 按综合得分排序
        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        
        return candidates[:top_k]
    
    def update_q_value(self, skill_id: str, reward: float) -> Dict:
        """
        更新记忆的Q值
        
        Formula: Q_new = Q_old + α * (reward - Q_old)
        """
        for memory in self.memories:
            if memory["id"] == skill_id:
                old_q = memory.get("q_value", 0.5)
                new_q = old_q + self.alpha * (reward - old_q)
                
                memory["q_value"] = round(new_q, 4)
                memory["usage_count"] = memory.get("usage_count", 0) + 1
                memory["last_updated"] = datetime.now().isoformat()
                
                if reward > 0.5:
                    memory["success_count"] = memory.get("success_count", 0) + 1
                else:
                    memory["fail_count"] = memory.get("fail_count", 0) + 1
                
                self._save_memories()
                
                return {
                    "skill_id": skill_id,
                    "old_q": old_q,
                    "new_q": new_q,
                    "delta": new_q - old_q,
                    "converged": abs(reward - old_q) < 0.05
                }
        
        return {"error": "Skill not found"}
    
    def add_experience(self, query: str, experience: str, 
                       reward: float) -> str:
        """
        添加新经验到记忆库
        """
        skill_id = f\"skill_{datetime.now().strftime('%Y%m%d_%H%M%S')}\"
        
        new_skill = {
            "id": skill_id,
            "content": experience,
            "embedding": self._embed(query),
            "q_value": reward,  # 初始Q值 = 第一次奖励
            "usage_count": 1,
            "success_count": 1 if reward > 0.5 else 0,
            "fail_count": 0 if reward > 0.5 else 1,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "source": "runtime_learning",
            "tags": self._extract_tags(query)
        }
        
        self.memories.append(new_skill)
        self._save_memories()
        
        return skill_id
```

### 1.3 初始化脚本 (重启后自动执行)

```python
# .claw-status/init_memrl.py
#!/usr/bin/env python3
"""
MemRL集成初始化脚本
在AGENTS.md Every Session时自动执行
"""

import os
import json
from datetime import datetime
from pathlib import Path

def initialize_memrl():
    """
    初始化MemRL记忆系统
    下次重启时自动执行
    """
    print("🔧 初始化MemRL记忆系统...")
    
    # 1. 创建记忆目录
    mem_dir = Path("memory/core")
    mem_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. 创建/加载带Q值的记忆文件
    q_memory_file = mem_dir / "skills_with_q.json"
    
    if not q_memory_file.exists():
        # 从现有MEMORY.md迁移
        print("  从MEMORY.md迁移现有记忆...")
        
        # 创建基础结构
        q_memory = {
            "version": "1.0",
            "schema": "skill_with_q",
            "created_at": datetime.now().isoformat(),
            "skills": []
        }
        
        # TODO: 解析MEMORY.md，提取现有技能，初始化Q值为0.5
        # 这需要根据实际MEMORY.md内容来实现
        
        with open(q_memory_file, 'w') as f:
            json.dump(q_memory, f, indent=2)
        
        print(f"  ✅ 已创建: {q_memory_file}")
    else:
        print(f"  ✅ 已存在: {q_memory_file}")
    
    # 3. 验证MemRL模块
    try:
        from memrl_memory import MemRLMemory
        mem = MemRLMemory()
        print(f"  ✅ MemRL模块加载成功 ({len(mem.memories)}条记忆)")
    except Exception as e:
        print(f"  ⚠️ MemRL模块加载失败: {e}")
    
    # 4. 更新memory_search工具 (如果可能)
    print("  检查memory_search集成...")
    
    print("\n✅ MemRL系统初始化完成")
    return True

if __name__ == "__main__":
    initialize_memrl()
```

---

## 阶段2详细设计: 两阶段检索

### 2.1 修改memory_search工具

```python
# 在现有的memory_search工具基础上扩展

def memory_search_with_q(query: str, maxResults: int = 5, 
                         use_q_value: bool = True) -> List[Dict]:
    """
    增强版memory_search，支持Q值排序
    
    Args:
        query: 搜索查询
        maxResults: 返回结果数
        use_q_value: 是否使用Q值排序 (默认True)
    
    Returns:
        带Q值和置信度的记忆列表
    """
    if not use_q_value:
        # 回退到原生的语义搜索
        return original_memory_search(query, maxResults)
    
    # 使用MemRL两阶段检索
    from memrl_memory import MemRLMemory
    
    mem = MemRLMemory()
    results = mem.retrieve(query, top_k=maxResults)
    
    # 格式化返回
    formatted = []
    for r in results:
        formatted.append({
            "content": r["memory"]["content"],
            "q_value": r["memory"].get("q_value", 0.5),
            "similarity": r["similarity"],
            "final_score": r["final_score"],
            "usage_count": r["memory"].get("usage_count", 0),
            "success_rate": r["memory"].get("success_count", 0) / 
                           max(r["memory"].get("usage_count", 1), 1),
            "source": r["memory"].get("source", "unknown")
        })
    
    return formatted
```

### 2.2 记忆使用追踪

```python
# .claw-status/task_memory_tracker.py
class TaskMemoryTracker:
    """
    追踪任务执行过程中使用的记忆
    用于后续Q值更新
    """
    
    def __init__(self):
        self.active_tasks = {}
    
    def start_task(self, task_id: str, query: str):
        """开始追踪任务"""
        self.active_tasks[task_id] = {
            "query": query,
            "retrieved_memories": [],  # 记录使用的记忆ID
            "start_time": datetime.now().isoformat()
        }
    
    def log_memory_usage(self, task_id: str, skill_id: str, 
                         context: str = ""):
        """记录使用了某条记忆"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["retrieved_memories"].append({
                "skill_id": skill_id,
                "context": context,
                "timestamp": datetime.now().isoformat()
            })
    
    def complete_task(self, task_id: str, success: bool, 
                     verification: Dict = None) -> Dict:
        """
        完成任务，更新所有使用过的记忆的Q值
        
        Returns:
            更新记录
        """
        if task_id not in self.active_tasks:
            return {"error": "Task not found"}
        
        task = self.active_tasks.pop(task_id)
        
        # 计算奖励
        reward = self._calculate_reward(success, verification)
        
        # 更新所有使用过的记忆
        from memrl_memory import MemRLMemory
        mem = MemRLMemory()
        
        updates = []
        for usage in task["retrieved_memories"]:
            result = mem.update_q_value(usage["skill_id"], reward)
            updates.append(result)
        
        # 如果任务成功，添加新经验
        if success and reward > 0.7:
            # 总结新经验并添加
            new_skill_id = mem.add_experience(
                task["query"],
                f\"任务成功: {task['query']}\",
                reward
            )
            updates.append({"new_skill": new_skill_id})
        
        return {
            "task_id": task_id,
            "reward": reward,
            "updates": updates
        }
    
    def _calculate_reward(self, success: bool, 
                         verification: Dict = None) -> float:
        """
        计算任务奖励
        
        评分标准:
        - 1.0: 完全成功 + 已验证
        - 0.8: 成功但未验证
        - 0.5: 部分成功
        - 0.0: 失败
        """
        if not success:
            return 0.0
        
        if verification:
            if verification.get("verified"):
                return 1.0
            elif verification.get("user_confirmed"):
                return 0.9
            else:
                return 0.7
        
        return 0.8  # 成功但无验证信息
```

---

## 阶段3详细设计: 自动反馈闭环

### 3.1 集成到Coordinator Agent

```python
# .claw-status/coordinator_memrl.py
class CoordinatorWithMemRL:
    """
    增强版Coordinator，集成MemRL自动学习
    """
    
    def __init__(self):
        self.coord = get_coordinator()
        self.memory_tracker = TaskMemoryTracker()
        self.memrl = MemRLMemory()
    
    def execute_task(self, task_description: str, task_type: str):
        """
        执行任务，自动追踪记忆使用和更新Q值
        """
        import uuid
        task_id = f\"task_{uuid.uuid4().hex[:8]}\"
        
        # 1. 检索相关记忆 (使用MemRL)
        print(f\"[Coordinator] 检索相关记忆...\")
        relevant_memories = self.memrl.retrieve(task_description, top_k=3)
        
        # 记录记忆使用
        self.memory_tracker.start_task(task_id, task_description)
        for mem in relevant_memories:
            self.memory_tracker.log_memory_usage(
                task_id, 
                mem["memory"]["id"],
                context="initial_retrieval"
            )
        
        # 2. 分配任务给Agent (使用现有协调器)
        print(f\"[Coordinator] 分配任务...\")
        assignment = self.coord.assign_task(task_description, task_type)
        
        if assignment["status"] != "assigned":
            return assignment
        
        agent_id = assignment["agent_id"]
        
        # 3. 等待任务完成
        print(f\"[Coordinator] 等待{agent_id}完成任务...\")
        # ... (等待逻辑)
        
        # 4. 获取结果并验证
        result = self._wait_for_completion(assignment["task_id"])
        
        # 5. 自动更新记忆Q值
        print(f\"[Coordinator] 更新记忆Q值...\")
        verification = {
            "verified": result.get("verified", False),
            "user_confirmed": result.get("user_confirmed", False)
        }
        
        updates = self.memory_tracker.complete_task(
            task_id,
            result["success"],
            verification
        )
        
        print(f\"[Coordinator] 更新了{len(updates['updates'])}条记忆的Q值\")
        
        return result
```

---

## 集成到AGENTS.md (下次重启自动执行)

```markdown
## MemRL集成 (下次重启自动执行)

### 自动初始化

```python
# 在AGENTS.md的 Every Session 部分添加

# 1. 初始化MemRL记忆系统
try:
    sys.path.insert(0, str(Path(__file__).parent / ".claw-status"))
    from init_memrl import initialize_memrl
    initialize_memrl()
except Exception as e:
    print(f"⚠️ MemRL初始化失败: {e}")

# 2. 加载MemRL增强的memory_search
try:
    from memrl_memory import MemRLMemory
    # 全局可用
    memrl_memory = MemRLMemory()
    print(f"✅ MemRL记忆系统已加载 ({len(memrl_memory.memories)}条记忆)")
except Exception as e:
    print(f"⚠️ MemRL模块加载失败: {e}")
```

### 使用方式

```python
# 检索记忆 (自动使用Q值排序)
results = memrl_memory.retrieve("部署博客", top_k=5)
# 返回: 按综合得分排序的记忆列表

# 更新记忆Q值 (任务完成后自动调用)
memrl_memory.update_q_value("skill_001", reward=1.0)
# reward: 1.0=成功, 0.0=失败

# 添加新经验
new_id = memrl_memory.add_experience(
    query="部署博客",
    experience="用git push比API更稳定",
    reward=1.0
)
```

### 配置参数

```python
# .claw-status/memrl_config.json
{
  "alpha": 0.1,           # Q值学习率 (0.05-0.2)
  "lambda_weight": 0.5,   # 语义vs效用权重 (0-1)
  "similarity_threshold": 0.5,  # 语义召回阈值
  "top_k_candidates": 20,  # 阶段A召回数量
  "top_k_final": 5,        # 阶段B最终数量
  "decay_enabled": true,   # 是否启用记忆衰减
  "decay_days": 30         # 多少天未使用开始衰减
}
```
```

---

## 验证清单

### 重启后自动检查

```bash
# 1. 检查MemRL记忆文件
ls -la memory/core/skills_with_q.json

# 2. 检查初始化日志
grep "MemRL" .claw-status/init.log

# 3. 测试检索
python3 -c "
from memrl_memory import MemRLMemory
mem = MemRLMemory()
results = mem.retrieve('部署博客', top_k=3)
print(f'检索到{len(results)}条记忆')
for r in results:
    print(f\"  - Q值: {r['memory'].get('q_value', 0.5):.2f}, 内容: {r['memory']['content'][:30]}...\")
"

# 4. 测试Q值更新
python3 -c "
from memrl_memory import MemRLMemory
mem = MemRLMemory()
result = mem.update_q_value('skill_001', reward=1.0)
print(f\"Q值更新: {result.get('old_q')} -> {result.get('new_q')}\")
"
```

---

## 实施时间表

| 阶段 | 任务 | 预计时间 | 依赖 |
|------|------|---------|------|
| **阶段1** | 基础设施搭建 | 重启后立即 | AGENTS.md |
| | - 创建memrl_memory.py | | |
| | - 创建init_memrl.py | | |
| | - 迁移现有记忆 | | |
| **阶段2** | 两阶段检索 | 1周内 | 阶段1 |
| | - 修改memory_search | | |
| | - A/B测试 | | |
| **阶段3** | 自动反馈闭环 | 2周内 | 阶段2 |
| | - 任务追踪器 | | |
| | - Coordinator集成 | | |
| **阶段4** | 优化调参 | 持续 | 阶段3 |

---

## 预期效果

重启后，系统将具备:
1. ✅ **带Q值的记忆** - 每条记忆都有效用评分
2. ✅ **两阶段检索** - 语义召回 + Q值重排
3. ✅ **自动学习** - 任务完成自动更新Q值
4. ✅ **经验积累** - 成功经验自动优先推荐

**下次重启 = 自动执行阶段1 = MemRL基础设施就绪**

---

*Created: 2026-03-16*  
*Next Action: 重启后自动执行init_memrl.py*
