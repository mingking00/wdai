#!/usr/bin/env python3
"""
MemRL Memory System
基于论文: MemRL: Self-Evolving Agents via Runtime Reinforcement Learning on Episodic Memory

核心功能:
1. 带Q值的记忆存储 (Intent-Experience-Utility)
2. 两阶段检索 (语义召回 + Q值重排)
3. 自动Q值更新 (运行时强化学习)
"""

import os
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

class MemRLMemory:
    """
    MemRL风格的记忆管理系统
    
    记忆结构: (z, e, Q) 三元组
    - z: intent_embedding (意图嵌入)
    - e: raw_experience (原始经验)
    - Q: q_value (学习效用, 0-1)
    """
    
    DEFAULT_CONFIG = {
        "alpha": 0.1,              # Q值学习率
        "lambda_weight": 0.5,      # 语义vs效用权重
        "similarity_threshold": 0.5,  # 语义召回阈值
        "top_k_candidates": 20,    # 阶段A召回数量
        "top_k_final": 5,          # 阶段B最终数量
        "initial_q": 0.5,          # 新记忆初始Q值
        "min_q": 0.1,              # Q值下限
        "max_q": 1.0               # Q值上限
    }
    
    def __init__(self, config: Dict = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.memory_dir = Path("/root/.openclaw/workspace/memory/core")
        self.memory_file = self.memory_dir / "skills_with_q.json"
        self.config_file = Path("/root/.openclaw/workspace/.claw-status/memrl_config.json")
        
        # 确保目录存在
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self._load_config()
        
        # 加载记忆
        self.memories = self._load_memories()
        
        print(f"🔧 MemRL Memory 初始化完成 ({len(self.memories)}条记忆)")
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载配置失败: {e}")
    
    def _load_memories(self) -> List[Dict]:
        """加载带Q值的记忆"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file) as f:
                    data = json.load(f)
                    return data.get("skills", [])
            except Exception as e:
                print(f"⚠️ 加载记忆失败: {e}")
                return []
        return []
    
    def _save_memories(self):
        """保存记忆到文件"""
        data = {
            "version": "1.0",
            "schema": "skill_with_q",
            "updated_at": datetime.now().isoformat(),
            "count": len(self.memories),
            "skills": self.memories
        }
        
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存记忆失败: {e}")
    
    def _simple_embed(self, text: str) -> List[float]:
        """
        简化的文本嵌入 (使用hash)
        实际应用中应使用OpenAI/text-embedding-3等模型
        """
        # 使用多个hash函数生成128维向量
        np.random.seed(int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32))
        return np.random.randn(128).tolist()
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        a = np.array(a)
        b = np.array(b)
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """
        两阶段检索:
        
        阶段A: 语义召回 (Similarity-Based Recall)
        - 计算查询与所有记忆的余弦相似度
        - 筛选出相似度>阈值的候选
        
        阶段B: 价值感知选择 (Value-Aware Selection)
        - 对候选记忆计算综合得分
        - 得分 = (1-λ) * 相似度 + λ * Q值
        - 按综合得分排序返回
        
        Args:
            query: 查询文本
            top_k: 返回结果数 (默认使用配置)
        
        Returns:
            记忆列表，包含相似度、Q值、综合得分
        """
        if top_k is None:
            top_k = self.config["top_k_final"]
        
        if not self.memories:
            return []
        
        # 生成查询的嵌入
        query_embedding = self._simple_embed(query)
        
        # === 阶段A: 语义召回 ===
        candidates = []
        threshold = self.config["similarity_threshold"]
        
        for memory in self.memories:
            embedding = memory.get("embedding", [])
            if not embedding:
                # 如果没有预计算embedding，临时计算
                embedding = self._simple_embed(memory.get("content", ""))
            
            similarity = self._cosine_similarity(query_embedding, embedding)
            
            if similarity >= threshold:
                candidates.append({
                    "memory": memory,
                    "similarity": similarity
                })
        
        # 按相似度排序，取top-k1
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        candidates = candidates[:self.config["top_k_candidates"]]
        
        if not candidates:
            return []
        
        # === 阶段B: 价值感知选择 ===
        lambda_w = self.config["lambda_weight"]
        
        for cand in candidates:
            q_value = cand["memory"].get("q_value", self.config["initial_q"])
            
            # 归一化Q值 (已经在0-1范围内)
            normalized_q = max(self.config["min_q"], min(self.config["max_q"], q_value))
            
            # 综合得分公式
            cand["final_score"] = (1 - lambda_w) * cand["similarity"] + lambda_w * normalized_q
            cand["q_value"] = normalized_q
        
        # 按综合得分排序
        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        
        return candidates[:top_k]
    
    def update_q_value(self, skill_id: str, reward: float) -> Dict:
        """
        更新记忆的Q值 (核心RL机制)
        
        Formula (指数移动平均):
            Q_new = Q_old + α * (reward - Q_old)
        
        特性:
        - reward > Q_old: Q值上升 (正强化)
        - reward < Q_old: Q值下降 (负强化)
        - reward = Q_old: Q值不变 (已收敛)
        
        Args:
            skill_id: 记忆ID
            reward: 奖励信号 (0.0-1.0)
                  1.0 = 完全成功
                  0.5 = 部分成功
                  0.0 = 失败
        
        Returns:
            更新结果，包含新旧Q值和收敛状态
        """
        for memory in self.memories:
            if memory.get("id") == skill_id:
                old_q = memory.get("q_value", self.config["initial_q"])
                alpha = self.config["alpha"]
                
                # MemRL核心更新公式
                new_q = old_q + alpha * (reward - old_q)
                
                # 限制在有效范围
                new_q = max(self.config["min_q"], min(self.config["max_q"], new_q))
                new_q = round(new_q, 4)
                
                # 更新记忆
                memory["q_value"] = new_q
                memory["usage_count"] = memory.get("usage_count", 0) + 1
                memory["last_updated"] = datetime.now().isoformat()
                
                if reward > 0.5:
                    memory["success_count"] = memory.get("success_count", 0) + 1
                else:
                    memory["fail_count"] = memory.get("fail_count", 0) + 1
                
                # 保存
                self._save_memories()
                
                # 判断是否收敛
                converged = abs(reward - old_q) < 0.05
                
                return {
                    "skill_id": skill_id,
                    "old_q": old_q,
                    "new_q": new_q,
                    "delta": round(new_q - old_q, 4),
                    "converged": converged,
                    "reward": reward
                }
        
        return {"error": f"Skill {skill_id} not found"}
    
    def add_experience(self, query: str, experience: str, 
                       reward: float = 0.5,
                       tags: List[str] = None) -> str:
        """
        添加新经验到记忆库
        
        Args:
            query: 查询/任务描述
            experience: 经验内容
            reward: 初始奖励 (决定初始Q值)
            tags: 标签列表
        
        Returns:
            新记忆ID
        """
        skill_id = f"skill_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query) % 10000}"
        
        new_skill = {
            "id": skill_id,
            "content": experience,
            "query": query,
            "embedding": self._simple_embed(query),
            "q_value": reward,  # 初始Q值 = 第一次奖励
            "usage_count": 1,
            "success_count": 1 if reward > 0.5 else 0,
            "fail_count": 0 if reward > 0.5 else 1,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "source": "runtime_learning",
            "tags": tags or []
        }
        
        self.memories.append(new_skill)
        self._save_memories()
        
        return skill_id
    
    def get_stats(self) -> Dict:
        """获取记忆库统计信息"""
        if not self.memories:
            return {"count": 0, "avg_q": 0, "total_usage": 0}
        
        q_values = [m.get("q_value", 0.5) for m in self.memories]
        usages = [m.get("usage_count", 0) for m in self.memories]
        
        return {
            "count": len(self.memories),
            "avg_q": round(sum(q_values) / len(q_values), 4),
            "min_q": round(min(q_values), 4),
            "max_q": round(max(q_values), 4),
            "total_usage": sum(usages),
            "high_q_skills": len([q for q in q_values if q > 0.8]),
            "low_q_skills": len([q for q in q_values if q < 0.3])
        }
    
    def export_to_markdown(self, output_file: str = None) -> str:
        """
        导出记忆为Markdown格式 (用于人类阅读)
        """
        if output_file is None:
            output_file = self.memory_dir / "skills_with_q_export.md"
        
        lines = [
            "# 技能记忆库 (带Q值)",
            "",
            f"> 导出时间: {datetime.now().isoformat()}",
            f"> 总技能数: {len(self.memories)}",
            ""
        ]
        
        # 按Q值排序
        sorted_memories = sorted(
            self.memories,
            key=lambda x: x.get("q_value", 0),
            reverse=True
        )
        
        for i, mem in enumerate(sorted_memories[:50], 1):  # 只导出前50
            q = mem.get("q_value", 0.5)
            usage = mem.get("usage_count", 0)
            success = mem.get("success_count", 0)
            
            # Q值可视化
            q_bar = "█" * int(q * 10) + "░" * (10 - int(q * 10))
            
            lines.extend([
                f"## {i}. {mem.get('id', 'unknown')}",
                "",
                f"**Q值**: {q:.2f} {q_bar}",
                f"**使用次数**: {usage} (成功: {success})",
                f"**来源**: {mem.get('source', 'unknown')}",
                f"**创建时间**: {mem.get('created_at', 'unknown')}",
                "",
                f"**内容**:",
                f"```",
                mem.get("content", "无内容"),
                f"```",
                ""
            ])
        
        content = "\n".join(lines)
        
        with open(output_file, 'w') as f:
            f.write(content)
        
        return str(output_file)


# 全局实例 (单例模式)
_memrl_instance = None

def get_memrl_memory(config: Dict = None) -> MemRLMemory:
    """获取MemRLMemory单例"""
    global _memrl_instance
    if _memrl_instance is None:
        _memrl_instance = MemRLMemory(config)
    return _memrl_instance


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("MemRL Memory System 测试")
    print("=" * 60)
    
    mem = MemRLMemory()
    
    # 添加测试记忆
    print("\n1. 添加测试记忆")
    skill1 = mem.add_experience(
        query="部署博客到GitHub",
        experience="用git push比API更稳定",
        reward=1.0,
        tags=["deploy", "git"]
    )
    print(f"   添加: {skill1}")
    
    skill2 = mem.add_experience(
        query="部署到服务器",
        experience="用rsync同步文件",
        reward=0.8,
        tags=["deploy", "sync"]
    )
    print(f"   添加: {skill2}")
    
    # 检索测试
    print("\n2. 检索测试")
    results = mem.retrieve("怎么部署博客", top_k=3)
    for i, r in enumerate(results, 1):
        print(f"   {i}. 相似度:{r['similarity']:.2f} Q值:{r['q_value']:.2f} 得分:{r['final_score']:.2f}")
        print(f"      内容: {r['memory']['content'][:40]}...")
    
    # Q值更新测试
    print("\n3. Q值更新测试")
    result = mem.update_q_value(skill1, reward=1.0)
    print(f"   {result['skill_id']}: {result['old_q']:.2f} -> {result['new_q']:.2f} (delta: {result['delta']:+.4f})")
    
    # 统计
    print("\n4. 统计信息")
    stats = mem.get_stats()
    print(f"   总记忆: {stats['count']}")
    print(f"   平均Q值: {stats['avg_q']:.2f}")
    print(f"   高Q值技能: {stats['high_q_skills']}")
    
    print("\n✅ 测试完成")
