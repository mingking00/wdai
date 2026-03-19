#!/usr/bin/env python3
"""
EMPO² + MemRL 集成系统 v1.0

将EMPO²的混合学习机制整合到MemRL记忆系统中

核心创新:
1. Tips生成 - 自动从失败/成功中提取指导提示
2. 双模式检索 - 有记忆/无记忆自适应切换
3. 参数化内化 - 高频记忆自动固化到系统配置
4. 探索奖励 - 尝试新方法的内在激励机制

Author: wdai
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib

# 导入现有MemRL系统
import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from memrl_memory import MemRLMemory


@dataclass
class EMPO2Tip:
    """EMPO² Tip结构"""
    tip_id: str
    content: str          # 提示内容
    source_task: str      # 来源任务
    source_error: str     # 来源错误/成功
    context: str          # 上下文
    created_at: str
    usage_count: int = 0  # 使用次数
    effectiveness: float = 0.5  # 有效性评分 (0-1)


@dataclass
class TaskOutcome:
    """任务结果记录"""
    task_id: str
    query: str
    actions: List[str]    # 执行的动作序列
    outcome: str          # success / failure / partial
    error_message: str    # 错误信息
    duration_sec: int     # 执行时间
    tips_used: List[str]  # 使用的tips
    tips_generated: List[str]  # 生成的新tips
    timestamp: str


class EMPO2MemoryIntegration:
    """
    EMPO² + MemRL集成系统
    
    实现EMPO²的四个核心机制:
    1. Self-Generated Memory (自我生成记忆)
    2. Hybrid Rollout (双模式Rollout)
    3. On/Off-Policy Update (混合策略更新)
    4. Knowledge Distillation (知识蒸馏内化)
    """
    
    def __init__(self):
        # 基础MemRL系统
        self.base_memory = MemRLMemory()
        
        # EMPO²扩展目录
        self.empo2_dir = Path("/root/.openclaw/workspace/.claw-status/empo2_integration")
        self.tips_file = self.empo2_dir / "tips.json"
        self.outcomes_file = self.empo2_dir / "outcomes.json"
        self.internalized_file = self.empo2_dir / "internalized_rules.json"
        
        # 确保目录存在
        self.empo2_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载EMPO²特定数据
        self.tips: List[EMPO2Tip] = self._load_tips()
        self.outcomes: List[TaskOutcome] = self._load_outcomes()
        self.internalized_rules: List[Dict] = self._load_internalized_rules()
        
        # 配置
        self.config = {
            "tip_generation_threshold": 3,      # 生成tip的最小错误次数
            "internalization_threshold": 5,     # 内化到参数的使用次数
            "effectiveness_threshold": 0.7,     # 高有效性阈值
            "exploration_bonus": 0.1,           # 探索奖励系数
            "memory_rollout_prob": 0.6,         # 使用记忆的rollout概率
        }
        
        print(f"🚀 EMPO² + MemRL 集成系统初始化完成")
        print(f"   基础记忆: {len(self.base_memory.memories)}条")
        print(f"   Tips: {len(self.tips)}个")
        print(f"   内化规则: {len(self.internalized_rules)}条")
    
    def _load_tips(self) -> List[EMPO2Tip]:
        """加载Tips"""
        if not self.tips_file.exists():
            return []
        try:
            with open(self.tips_file) as f:
                data = json.load(f)
                return [EMPO2Tip(**tip) for tip in data.get("tips", [])]
        except Exception as e:
            print(f"⚠️ 加载tips失败: {e}")
            return []
    
    def _save_tips(self):
        """保存Tips"""
        with open(self.tips_file, 'w') as f:
            json.dump({
                "tips": [asdict(tip) for tip in self.tips],
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def _load_outcomes(self) -> List[TaskOutcome]:
        """加载任务结果"""
        if not self.outcomes_file.exists():
            return []
        try:
            with open(self.outcomes_file) as f:
                data = json.load(f)
                return [TaskOutcome(**outcome) for outcome in data.get("outcomes", [])]
        except Exception as e:
            print(f"⚠️ 加载outcomes失败: {e}")
            return []
    
    def _save_outcomes(self):
        """保存任务结果"""
        with open(self.outcomes_file, 'w') as f:
            json.dump({
                "outcomes": [asdict(o) for o in self.outcomes[-100:]],  # 保留最近100条
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def _load_internalized_rules(self) -> List[Dict]:
        """加载已内化的规则"""
        if not self.internalized_file.exists():
            return []
        try:
            with open(self.internalized_file) as f:
                return json.load(f).get("rules", [])
        except Exception as e:
            print(f"⚠️ 加载internalized rules失败: {e}")
            return []
    
    def _save_internalized_rules(self):
        """保存已内化的规则"""
        with open(self.internalized_file, 'w') as f:
            json.dump({
                "rules": self.internalized_rules,
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    # ========== 1. Self-Generated Memory ==========
    
    def generate_tip(self, task_outcome: TaskOutcome) -> Optional[EMPO2Tip]:
        """
        从任务结果生成Tip
        
        类似于EMPO²中的: tip_i ~ π_θ(s_t, task, tip_generation_prompt)
        """
        # 只有失败或部分成功才生成tip
        if task_outcome.outcome == "success":
            return None
        
        # 基于错误类型生成tip内容
        error_patterns = {
            r"timeout|timed out": "⚠️ 超时错误 - 考虑减小任务粒度或增加超时时间",
            r"permission|access denied": "🔒 权限错误 - 检查文件/目录权限或使用sudo",
            r"not found|no such file": "📁 路径错误 - 确认文件/目录存在，使用绝对路径",
            r"already exists": "📝 已存在 - 检查是否需要覆盖或先删除旧文件",
            r"rate limit|too many requests": "⏳ 限流错误 - 添加重试逻辑或降低请求频率",
            r"invalid api key|unauthorized": "🔑 API密钥错误 - 检查环境变量或配置文件",
            r"parse|syntax error": "🐛 语法错误 - 检查代码格式，特别是括号匹配",
        }
        
        tip_content = None
        for pattern, suggestion in error_patterns.items():
            if re.search(pattern, task_outcome.error_message.lower()):
                tip_content = suggestion
                break
        
        if not tip_content:
            # 通用tip
            tip_content = f"💡 遇到错误: {task_outcome.error_message[:50]}... - 考虑分解任务或换种方法"
        
        tip = EMPO2Tip(
            tip_id=f"tip_{hashlib.md5(f'{task_outcome.task_id}_{datetime.now()}'.encode()).hexdigest()[:8]}",
            content=tip_content,
            source_task=task_outcome.query[:100],
            source_error=task_outcome.error_message[:200],
            context=f"任务类型: {self._classify_task_type(task_outcome.query)}",
            created_at=datetime.now().isoformat(),
            usage_count=0,
            effectiveness=0.5
        )
        
        self.tips.append(tip)
        self._save_tips()
        
        return tip
    
    def _classify_task_type(self, query: str) -> str:
        """简单任务分类"""
        keywords = {
            "代码": ["code", "python", "function", "class", "script"],
            "文件": ["file", "read", "write", "directory", "path"],
            "网络": ["http", "api", "request", "url", "web"],
            "部署": ["deploy", "server", "docker", "kubernetes", "k8s"],
            "调试": ["debug", "error", "fix", "bug", "troubleshoot"],
        }
        query_lower = query.lower()
        for task_type, words in keywords.items():
            if any(word in query_lower for word in words):
                return task_type
        return "general"
    
    # ========== 2. Hybrid Rollout (双模式检索) ==========
    
    def retrieve_with_mode(self, query: str, mode: str = "auto") -> Dict:
        """
        双模式检索
        
        mode:
        - "no_memory": 不使用记忆，纯参数化响应 (类似EMPO²模式1)
        - "with_memory": 使用记忆+tips (类似EMPO²模式2)
        - "auto": 自适应选择 (概率p使用记忆)
        """
        import random
        
        if mode == "auto":
            # 自适应: 以概率p使用记忆
            use_memory = random.random() < self.config["memory_rollout_prob"]
        else:
            use_memory = (mode == "with_memory")
        
        result = {
            "mode_used": "with_memory" if use_memory else "no_memory",
            "memories": [],
            "tips": [],
            "internalized_rules": []
        }
        
        if use_memory:
            # 检索基础记忆 (MemRL)
            base_results = self.base_memory.retrieve(query)
            result["memories"] = base_results[:3]  # Top-3记忆
            
            # 检索相关Tips
            relevant_tips = self._retrieve_tips(query)
            result["tips"] = relevant_tips[:2]  # Top-2 tips
        
        # 始终包含已内化的规则 (参数化知识)
        result["internalized_rules"] = self._get_relevant_internalized_rules(query)
        
        return result
    
    def _retrieve_tips(self, query: str) -> List[EMPO2Tip]:
        """检索相关Tips (简单关键词匹配)"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_tips = []
        for tip in self.tips:
            tip_words = set(tip.content.lower().split())
            tip_source_words = set(tip.source_task.lower().split())
            
            # 计算相似度
            content_overlap = len(query_words & tip_words)
            source_overlap = len(query_words & tip_source_words)
            
            # 综合评分: 内容匹配 + 来源匹配 + 有效性
            score = (content_overlap * 2 + source_overlap) * tip.effectiveness
            
            if score > 0:
                scored_tips.append((tip, score))
        
        # 按评分排序
        scored_tips.sort(key=lambda x: x[1], reverse=True)
        return [tip for tip, _ in scored_tips]
    
    def _get_relevant_internalized_rules(self, query: str) -> List[Dict]:
        """获取相关的内化规则"""
        query_lower = query.lower()
        return [
            rule for rule in self.internalized_rules
            if any(keyword in query_lower for keyword in rule.get("keywords", []))
        ]
    
    # ========== 3. On/Off-Policy Update ==========
    
    def update_from_outcome(self, task_outcome: TaskOutcome):
        """
        基于任务结果更新系统
        
        模拟EMPO²的混合更新:
        - On-policy: 直接更新基础记忆Q值
        - Off-policy: 更新Tips有效性，触发知识蒸馏
        """
        # 1. 记录结果
        self.outcomes.append(task_outcome)
        self._save_outcomes()
        
        # 2. On-policy: 更新基础记忆
        if task_outcome.outcome == "success":
            # 成功的任务提升相关记忆的Q值
            self._boost_related_memories(task_outcome.query)
        
        # 3. 更新使用的Tips有效性 (On-policy反馈)
        for tip_id in task_outcome.tips_used:
            self._update_tip_effectiveness(tip_id, task_outcome.outcome)
        
        # 4. Off-policy: 如果成功且使用了tips，考虑内化
        if task_outcome.outcome == "success" and task_outcome.tips_used:
            self._consider_internalization(task_outcome)
        
        # 5. 生成新Tips (如果失败)
        if task_outcome.outcome == "failure":
            self.generate_tip(task_outcome)
    
    def _boost_related_memories(self, query: str):
        """提升相关记忆的Q值"""
        # 简化的实现: 找到query相关的记忆并提升Q值
        for memory in self.base_memory.memories:
            if query.lower() in memory.get("query", "").lower():
                current_q = memory.get("q_value", 0.5)
                memory["q_value"] = min(1.0, current_q + 0.05)
        
        self.base_memory._save_memories()
    
    def _update_tip_effectiveness(self, tip_id: str, outcome: str):
        """更新Tip的有效性"""
        for tip in self.tips:
            if tip.tip_id == tip_id:
                tip.usage_count += 1
                
                # 根据结果更新有效性
                if outcome == "success":
                    tip.effectiveness = min(1.0, tip.effectiveness + 0.1)
                elif outcome == "failure":
                    tip.effectiveness = max(0.1, tip.effectiveness - 0.1)
                
                break
        
        self._save_tips()
    
    # ========== 4. Knowledge Distillation (知识蒸馏内化) ==========
    
    def _consider_internalization(self, task_outcome: TaskOutcome):
        """
        考虑将成功模式内化到参数
        
        EMPO² Off-policy update的核心:
        将外部记忆的好处内化到模型参数
        """
        for tip_id in task_outcome.tips_used:
            tip = next((t for t in self.tips if t.tip_id == tip_id), None)
            if not tip:
                continue
            
            # 内化条件:
            # 1. 使用次数足够
            # 2. 有效性高
            if (tip.usage_count >= self.config["internalization_threshold"] and
                tip.effectiveness >= self.config["effectiveness_threshold"]):
                
                self._internalize_tip(tip)
    
    def _internalize_tip(self, tip: EMPO2Tip):
        """将Tip内化为系统规则"""
        # 检查是否已内化
        existing = next((r for r in self.internalized_rules 
                        if r.get("source_tip_id") == tip.tip_id), None)
        
        if existing:
            return  # 已内化
        
        # 创建内化规则
        rule = {
            "rule_id": f"rule_{tip.tip_id}",
            "content": tip.content,
            "keywords": self._extract_keywords(tip.source_task),
            "source_tip_id": tip.tip_id,
            "internalized_at": datetime.now().isoformat(),
            "confidence": tip.effectiveness
        }
        
        self.internalized_rules.append(rule)
        self._save_internalized_rules()
        
        print(f"🧠 Tip已内化: {tip.content[:50]}...")
        
        # 触发系统更新 (如更新AGENTS.md或SOUL.md)
        self._update_system_documentation(rule)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单实现: 提取名词和动词
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        stop_words = {'this', 'that', 'with', 'from', 'they', 'have', 'been', 'were'}
        return list(set([w for w in words if w not in stop_words]))[:10]
    
    def _update_system_documentation(self, rule: Dict):
        """更新系统文档 (参数化内化)"""
        # 实际应用中，这里可以自动更新AGENTS.md或创建新的规则文件
        doc_file = Path("/root/.openclaw/workspace/.claw-status/auto_internalized_rules.md")
        
        with open(doc_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## {rule['rule_id']}\n")
            f.write(f"- **规则**: {rule['content']}\n")
            f.write(f"- **关键词**: {', '.join(rule['keywords'])}\n")
            f.write(f"- **内化时间**: {rule['internalized_at']}\n")
            f.write(f"- **置信度**: {rule['confidence']:.2f}\n\n")
    
    # ========== 5. 高级功能 ==========
    
    def get_exploration_bonus(self, query: str) -> float:
        """
        计算探索奖励
        
        对于从未尝试过的新类型任务，给予探索奖励
        """
        # 检查是否有过类似任务
        similar_outcomes = [
            o for o in self.outcomes
            if self._task_similarity(query, o.query) > 0.5
        ]
        
        if not similar_outcomes:
            # 全新任务类型，高探索奖励
            return self.config["exploration_bonus"] * 2
        
        # 根据历史成功率调整
        success_rate = sum(1 for o in similar_outcomes if o.outcome == "success") / len(similar_outcomes)
        if success_rate < 0.3:
            # 困难任务，给予探索奖励鼓励尝试新方法
            return self.config["exploration_bonus"]
        
        return 0.0
    
    def _task_similarity(self, query1: str, query2: str) -> float:
        """简单任务相似度"""
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) if union else 0.0
    
    def generate_report(self) -> Dict:
        """生成系统报告"""
        return {
            "base_memories": len(self.base_memory.memories),
            "tips": {
                "total": len(self.tips),
                "high_effectiveness": len([t for t in self.tips if t.effectiveness >= 0.7])
            },
            "outcomes": {
                "total": len(self.outcomes),
                "success": len([o for o in self.outcomes if o.outcome == "success"]),
                "failure": len([o for o in self.outcomes if o.outcome == "failure"]),
                "partial": len([o for o in self.outcomes if o.outcome == "partial"])
            },
            "internalized_rules": len(self.internalized_rules),
            "config": self.config
        }


# ========== 使用示例 ==========

def demo():
    """演示EMPO²+MemRL集成"""
    print("="*60)
    print("🚀 EMPO² + MemRL 集成演示")
    print("="*60)
    
    # 初始化系统
    empo2 = EMPO2MemoryIntegration()
    
    # 模拟任务执行
    print("\n--- 任务1: 失败的API调用 ---")
    outcome1 = TaskOutcome(
        task_id="task_001",
        query="调用GitHub API获取仓库信息",
        actions=["web_search", "api_call"],
        outcome="failure",
        error_message="API rate limit exceeded. Please try again later.",
        duration_sec=5,
        tips_used=[],
        tips_generated=[],
        timestamp=datetime.now().isoformat()
    )
    
    # 更新系统 (会生成tip)
    empo2.update_from_outcome(outcome1)
    print(f"生成了 {len(empo2.tips)} 个tips")
    
    # 检索 (使用记忆模式)
    print("\n--- 检索相关指导 ---")
    result = empo2.retrieve_with_mode("调用GitHub API", mode="with_memory")
    print(f"模式: {result['mode_used']}")
    print(f"找到 {len(result['tips'])} 个相关tips")
    for tip in result['tips'][:2]:
        print(f"  - {tip.content}")
    
    # 模拟成功任务 (使用tips)
    print("\n--- 任务2: 成功的API调用 (使用tips) ---")
    outcome2 = TaskOutcome(
        task_id="task_002",
        query="调用GitHub API获取仓库信息",
        actions=["check_rate_limit", "add_token", "api_call"],
        outcome="success",
        error_message="",
        duration_sec=3,
        tips_used=[empo2.tips[0].tip_id] if empo2.tips else [],
        tips_generated=[],
        timestamp=datetime.now().isoformat()
    )
    
    empo2.update_from_outcome(outcome2)
    
    # 生成报告
    print("\n--- 系统报告 ---")
    report = empo2.generate_report()
    print(f"基础记忆: {report['base_memories']}条")
    print(f"Tips: {report['tips']['total']}个 (高效: {report['tips']['high_effectiveness']})")
    print(f"内化规则: {report['internalized_rules']}条")
    
    print("\n✅ 演示完成!")


if __name__ == "__main__":
    demo()
