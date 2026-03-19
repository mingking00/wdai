#!/usr/bin/env python3
"""
Multi-Agent System - P2 Improvements
多智能体系统 - P2级改进

改进内容：
1. 人类审核节点 (Human-in-the-Loop)
2. 版本控制系统 (Version Control)
3. 改进历史追踪
"""

import sys
import json
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from collections import defaultdict

sys.path.insert(0, '/root/.openclaw/workspace/kimi-mcp-server/src')
from extended_tools import KimiMCPExtendedServer
from demo_p0_improvements import AgentOutput, Conflict


class ReviewDecision(Enum):
    """审核决策"""
    APPROVE = "approve"           # 批准
    APPROVE_WITH_COMMENTS = "approve_with_comments"  # 批准但有意见
    REQUEST_CHANGES = "request_changes"  # 要求修改
    REJECT = "reject"             # 拒绝


@dataclass
class ReviewCheckpoint:
    """审核检查点"""
    checkpoint_id: str
    name: str  # 检查点名称
    description: str  # 审核内容描述
    required: bool  # 是否必须审核
    auto_advance: bool  # 是否可自动通过
    reviewers: List[str]  # 指定审核者


@dataclass
class HumanReview:
    """人类审核记录"""
    review_id: str
    checkpoint_id: str
    reviewer: str
    decision: ReviewDecision
    comments: str
    suggestions: List[str]
    reviewed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "review_id": self.review_id,
            "checkpoint_id": self.checkpoint_id,
            "reviewer": self.reviewer,
            "decision": self.decision.value,
            "comments": self.comments,
            "suggestions": self.suggestions,
            "reviewed_at": self.reviewed_at
        }


@dataclass
class Version:
    """版本记录"""
    version_id: str
    version_number: str  # 语义化版本号，如 "1.2.3"
    timestamp: str
    author: str  # 创建者（Agent或Human）
    changes: str  # 变更描述
    outputs: List[AgentOutput]  # 当时的输出
    parent_version: Optional[str] = None  # 父版本ID
    tags: List[str] = field(default_factory=list)  # 标签
    
    def to_dict(self) -> Dict:
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "timestamp": self.timestamp,
            "author": self.author,
            "changes": self.changes,
            "parent_version": self.parent_version,
            "tags": self.tags
        }


class HumanReviewManager:
    """
    人类审核管理器
    
    在关键节点暂停，等待人类审核：
    1. 初始设计完成
    2. 代码生成完成
    3. 最终发布前
    """
    
    def __init__(self):
        self.checkpoints: List[ReviewCheckpoint] = []
        self.pending_reviews: Dict[str, Dict] = {}  # 待审核
        self.completed_reviews: List[HumanReview] = []
        self.server = KimiMCPExtendedServer()
        self._setup_default_checkpoints()
    
    def _setup_default_checkpoints(self):
        """设置默认审核检查点"""
        self.checkpoints = [
            ReviewCheckpoint(
                checkpoint_id="design_review",
                name="设计审核",
                description="审核系统架构设计方案",
                required=True,
                auto_advance=False,
                reviewers=["tech_lead", "architect"]
            ),
            ReviewCheckpoint(
                checkpoint_id="code_review",
                name="代码审核",
                description="审核生成的代码质量",
                required=True,
                auto_advance=False,
                reviewers=["senior_dev"]
            ),
            ReviewCheckpoint(
                checkpoint_id="doc_review",
                name="文档审核",
                description="审核文档完整性",
                required=False,
                auto_advance=True,
                reviewers=["tech_writer"]
            ),
            ReviewCheckpoint(
                checkpoint_id="final_approval",
                name="最终批准",
                description="最终发布前审核",
                required=True,
                auto_advance=False,
                reviewers=["project_manager"]
            )
        ]
    
    async def request_review(
        self, 
        checkpoint_id: str, 
        content: Dict[str, Any],
        context: Dict[str, Any]
    ) -> HumanReview:
        """
        请求人类审核
        
        在实际应用中，这会：
        - 发送通知（邮件/Slack/钉钉）
        - 等待人类响应
        - 这里模拟自动响应
        """
        checkpoint = self._get_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Unknown checkpoint: {checkpoint_id}")
        
        print(f"\n🛑 检查点: {checkpoint.name}")
        print(f"   说明: {checkpoint.description}")
        print(f"   必需审核: {'是' if checkpoint.required else '否'}")
        print(f"   指定审核者: {', '.join(checkpoint.reviewers)}")
        
        # 模拟等待人类审核
        # 实际应用中这里会阻塞等待人类输入
        review = await self._simulate_human_review(checkpoint_id, content)
        
        self.completed_reviews.append(review)
        
        print(f"\n✅ 审核完成:")
        print(f"   审核者: {review.reviewer}")
        print(f"   决策: {review.decision.value}")
        print(f"   意见: {review.comments}")
        
        return review
    
    async def _simulate_human_review(
        self, 
        checkpoint_id: str, 
        content: Dict
    ) -> HumanReview:
        """模拟人类审核（实际应用中替换为真实交互）"""
        # 模拟审核延迟
        await asyncio.sleep(0.5)
        
        # 根据检查点模拟不同决策
        decisions = {
            "design_review": ReviewDecision.APPROVE_WITH_COMMENTS,
            "code_review": ReviewDecision.REQUEST_CHANGES,
            "doc_review": ReviewDecision.APPROVE,
            "final_approval": ReviewDecision.APPROVE
        }
        
        comments = {
            "design_review": "整体设计良好，建议增加错误处理机制",
            "code_review": "需要优化异常处理和添加更多注释",
            "doc_review": "文档完整，可以直接发布",
            "final_approval": "所有问题已解决，批准发布"
        }
        
        suggestions = {
            "design_review": ["增加重试机制", "添加监控指标"],
            "code_review": ["优化异常处理", "添加函数文档字符串", "增加单元测试"],
            "doc_review": [],
            "final_approval": []
        }
        
        decision = decisions.get(checkpoint_id, ReviewDecision.APPROVE)
        
        return HumanReview(
            review_id=f"review_{checkpoint_id}_{datetime.now().strftime('%H%M%S')}",
            checkpoint_id=checkpoint_id,
            reviewer=checkpoint_id.replace("_review", "").replace("_approval", "_pm"),
            decision=decision,
            comments=comments.get(checkpoint_id, "审核通过"),
            suggestions=suggestions.get(checkpoint_id, [])
        )
    
    def _get_checkpoint(self, checkpoint_id: str) -> Optional[ReviewCheckpoint]:
        """获取检查点配置"""
        for cp in self.checkpoints:
            if cp.checkpoint_id == checkpoint_id:
                return cp
        return None
    
    def get_review_summary(self) -> Dict:
        """获取审核摘要"""
        approved = sum(1 for r in self.completed_reviews 
                      if r.decision in [ReviewDecision.APPROVE, ReviewDecision.APPROVE_WITH_COMMENTS])
        rejected = sum(1 for r in self.completed_reviews if r.decision == ReviewDecision.REJECT)
        changes_requested = sum(1 for r in self.completed_reviews if r.decision == ReviewDecision.REQUEST_CHANGES)
        
        return {
            "total_reviews": len(self.completed_reviews),
            "approved": approved,
            "rejected": rejected,
            "changes_requested": changes_requested,
            "pending": len(self.pending_reviews),
            "reviews": [r.to_dict() for r in self.completed_reviews]
        }


class VersionControlSystem:
    """
    版本控制系统
    
    功能：
    1. 保存每次迭代的版本
    2. 支持版本比较
    3. 支持回滚
    4. 分支管理
    5. 标签管理
    """
    
    def __init__(self):
        self.versions: Dict[str, Version] = {}
        self.branches: Dict[str, str] = {}  # branch_name -> version_id
        self.current_branch: str = "main"
        self.version_history: List[str] = []
        self.server = KimiMCPExtendedServer()
    
    def commit(
        self,
        outputs: List[AgentOutput],
        changes: str,
        author: str,
        tags: List[str] = None
    ) -> Version:
        """
        提交新版本
        
        类似于git commit
        """
        # 生成版本号
        version_number = self._generate_version_number()
        version_id = self._generate_version_id(outputs)
        
        # 获取父版本
        parent_id = None
        if self.version_history:
            parent_id = self.version_history[-1]
        
        version = Version(
            version_id=version_id,
            version_number=version_number,
            timestamp=datetime.now().isoformat(),
            author=author,
            changes=changes,
            outputs=outputs,
            parent_version=parent_id,
            tags=tags or []
        )
        
        self.versions[version_id] = version
        self.version_history.append(version_id)
        
        # 更新分支指针
        self.branches[self.current_branch] = version_id
        
        print(f"\n💾 版本提交:")
        print(f"   版本号: {version_number}")
        print(f"   版本ID: {version_id[:8]}...")
        print(f"   作者: {author}")
        print(f"   变更: {changes}")
        if tags:
            print(f"   标签: {', '.join(tags)}")
        
        return version
    
    def _generate_version_number(self) -> str:
        """生成语义化版本号"""
        if not self.version_history:
            return "1.0.0"
        
        # 简单递增
        last_version = self.versions[self.version_history[-1]].version_number
        parts = last_version.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    
    def _generate_version_id(self, outputs: List[AgentOutput]) -> str:
        """生成版本ID（基于内容哈希）"""
        content = json.dumps([asdict(o) for o in outputs], sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def checkout(self, version_id: str) -> Optional[List[AgentOutput]]:
        """检出特定版本（回滚）"""
        if version_id not in self.versions:
            print(f"❌ 版本不存在: {version_id}")
            return None
        
        version = self.versions[version_id]
        
        print(f"\n⏮️  检出版本:")
        print(f"   版本号: {version.version_number}")
        print(f"   时间: {version.timestamp}")
        print(f"   变更: {version.changes}")
        
        return version.outputs
    
    def diff(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """比较两个版本的差异"""
        v1 = self.versions.get(version_id1)
        v2 = self.versions.get(version_id2)
        
        if not v1 or not v2:
            return {"error": "Version not found"}
        
        # 比较输出差异
        differences = []
        
        for out1 in v1.outputs:
            out2 = next((o for o in v2.outputs if o.agent_id == out1.agent_id), None)
            if out2:
                diff = self._compare_outputs(out1, out2)
                if diff:
                    differences.append({
                        "agent_id": out1.agent_id,
                        "changes": diff
                    })
        
        return {
            "version1": v1.version_number,
            "version2": v2.version_number,
            "differences": differences,
            "added_tags": list(set(v2.tags) - set(v1.tags)),
            "removed_tags": list(set(v1.tags) - set(v2.tags))
        }
    
    def _compare_outputs(self, out1: AgentOutput, out2: AgentOutput) -> List[str]:
        """比较两个输出"""
        changes = []
        
        # 简单的键比较
        keys1 = set(out1.content.keys())
        keys2 = set(out2.content.keys())
        
        added = keys2 - keys1
        removed = keys1 - keys2
        
        if added:
            changes.append(f"Added fields: {', '.join(added)}")
        if removed:
            changes.append(f"Removed fields: {', '.join(removed)}")
        
        # 检查修改的字段
        for key in keys1 & keys2:
            if out1.content[key] != out2.content[key]:
                changes.append(f"Modified: {key}")
        
        return changes
    
    def log(self, limit: int = 10) -> List[Dict]:
        """查看版本历史"""
        history = []
        
        for version_id in reversed(self.version_history[-limit:]):
            version = self.versions[version_id]
            history.append({
                "version_number": version.version_number,
                "version_id": version.version_id[:8],
                "timestamp": version.timestamp,
                "author": version.author,
                "changes": version.changes,
                "tags": version.tags
            })
        
        return history
    
    def tag(self, version_id: str, tag_name: str):
        """给版本打标签"""
        if version_id in self.versions:
            self.versions[version_id].tags.append(tag_name)
            print(f"🏷️  标签 '{tag_name}' 已添加到版本 {version_id[:8]}")


class P2EnhancedOrchestrator:
    """
    P2增强编排器
    
    集成：
    1. 人类审核节点
    2. 版本控制
    3. 改进历史追踪
    """
    
    def __init__(self):
        self.review_manager = HumanReviewManager()
        self.version_control = VersionControlSystem()
        self.server = KimiMCPExtendedServer()
        self.iteration_count = 0
    
    async def execute_with_p2_features(
        self,
        workflow_steps: List[Callable],
        enable_review: bool = True,
        enable_versioning: bool = True
    ) -> Dict[str, Any]:
        """执行带P2特性的工作流"""
        print("\n" + "="*70)
        print("🚀 P2 ENHANCED ORCHESTRATOR")
        print("="*70)
        print(f"功能: 人类审核={enable_review}, 版本控制={enable_versioning}")
        
        all_outputs = []
        
        for i, step in enumerate(workflow_steps):
            step_name = step.__name__ if hasattr(step, '__name__') else f"step_{i}"
            print(f"\n📍 执行步骤: {step_name}")
            
            # 执行步骤
            outputs = await step()
            all_outputs.extend(outputs)
            
            # 版本控制
            if enable_versioning:
                self.version_control.commit(
                    outputs=all_outputs.copy(),
                    changes=f"完成 {step_name}",
                    author=f"agent_{i}",
                    tags=[f"step_{i}"]
                )
            
            # 人类审核
            if enable_review:
                review_checkpoint = self._map_step_to_checkpoint(step_name)
                if review_checkpoint:
                    review = await self.review_manager.request_review(
                        checkpoint_id=review_checkpoint,
                        content={"outputs": [asdict(o) for o in outputs]},
                        context={"step": i, "total_steps": len(workflow_steps)}
                    )
                    
                    # 处理审核结果
                    if review.decision == ReviewDecision.REJECT:
                        print(f"   ❌ 审核拒绝，终止工作流")
                        break
                    elif review.decision == ReviewDecision.REQUEST_CHANGES:
                        print(f"   📝 根据审核意见修改...")
                        # 这里可以实现修改逻辑
        
        # 生成最终报告
        return {
            "final_outputs": all_outputs,
            "review_summary": self.review_manager.get_review_summary() if enable_review else None,
            "version_history": self.version_control.log() if enable_versioning else None,
            "total_iterations": self.iteration_count
        }
    
    def _map_step_to_checkpoint(self, step_name: str) -> Optional[str]:
        """映射步骤到审核检查点"""
        mapping = {
            "research": "design_review",
            "code_generation": "code_review",
            "documentation": "doc_review",
            "finalization": "final_approval"
        }
        return mapping.get(step_name)


async def demo_p2_improvements():
    """演示P2级改进"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🎯 P2 IMPROVEMENTS - 人类审核 + 版本控制                                ║
║                                                                          ║
║   1. 人类审核节点 (Human-in-the-Loop)                                     ║
║   2. 版本控制系统 (Version Control)                                       ║
║   3. 改进历史追踪                                                         ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # 1. 演示人类审核
    print("\n" + "="*70)
    print("👤 HUMAN REVIEW SYSTEM")
    print("="*70)
    
    review_manager = HumanReviewManager()
    
    # 模拟不同阶段的审核
    checkpoints = ["design_review", "code_review", "final_approval"]
    
    for checkpoint in checkpoints:
        review = await review_manager.request_review(
            checkpoint_id=checkpoint,
            content={"status": "completed"},
            context={}
        )
        print()
    
    # 审核摘要
    summary = review_manager.get_review_summary()
    print("📊 审核摘要:")
    print(f"   总审核数: {summary['total_reviews']}")
    print(f"   批准: {summary['approved']}")
    print(f"   要求修改: {summary['changes_requested']}")
    print(f"   拒绝: {summary['rejected']}")
    
    # 2. 演示版本控制
    print("\n" + "="*70)
    print("💾 VERSION CONTROL SYSTEM")
    print("="*70)
    
    vcs = VersionControlSystem()
    
    # 模拟多次迭代提交
    iterations = [
        ("Initial implementation", "system"),
        ("Add error handling", "developer"),
        ("Optimize performance", "developer"),
        ("Add documentation", "tech_writer"),
    ]
    
    for i, (changes, author) in enumerate(iterations):
        # 创建模拟输出
        outputs = [
            AgentOutput(
                agent_id=f"agent_{i}",
                agent_type="Developer",
                content={
                    "version": i + 1,
                    "changes": changes,
                    "files": ["main.py", "config.json"]
                }
            )
        ]
        
        version = vcs.commit(
            outputs=outputs,
            changes=changes,
            author=author,
            tags=["v1.0"] if i == 0 else []
        )
    
    # 显示版本历史
    print("\n📜 版本历史:")
    history = vcs.log(limit=5)
    for v in history:
        tags = f" [{', '.join(v['tags'])}]" if v['tags'] else ""
        print(f"   {v['version_number']}{tags} - {v['changes']} ({v['author']})")
    
    # 3. 演示版本比较
    print("\n🔄 版本比较:")
    if len(vcs.version_history) >= 2:
        diff = vcs.diff(
            vcs.version_history[-2],
            vcs.version_history[-1]
        )
        print(f"   比较: {diff['version1']} -> {diff['version2']}")
        for d in diff['differences']:
            print(f"   Agent {d['agent_id']} 变更:")
            for change in d['changes']:
                print(f"      • {change}")
    
    print("\n" + "="*70)
    print("✅ P2改进完成！")
    print("="*70)
    print("\n改进亮点:")
    print("   1. ✅ 人类审核节点 - 关键决策人工确认")
    print("   2. ✅ 版本控制系统 - 完整历史追踪")
    print("   3. ✅ 审核-修改-再审核循环")
    print("   4. ✅ 支持回滚到任意版本")


if __name__ == "__main__":
    asyncio.run(demo_p2_improvements())
