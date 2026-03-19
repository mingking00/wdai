#!/usr/bin/env python3
"""
Multi-Agent System - P3 Improvements (Final Phase)
多智能体系统 - P3级改进（最终阶段）

改进内容：
1. 共识投票机制 (Consensus Voting)
2. 权重投票系统 (Weighted Voting)
3. 决策记录与审计
"""

import sys
import json
import asyncio
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from collections import defaultdict
import random

sys.path.insert(0, '/root/.openclaw/workspace/kimi-mcp-server/src')
from extended_tools import KimiMCPExtendedServer
from demo_p0_improvements import AgentOutput


class VoteOption(Enum):
    """投票选项"""
    STRONGLY_AGREE = ("strongly_agree", 2.0, "强烈同意")
    AGREE = ("agree", 1.0, "同意")
    NEUTRAL = ("neutral", 0.0, "中立")
    DISAGREE = ("disagree", -1.0, "反对")
    STRONGLY_DISAGREE = ("strongly_disagree", -2.0, "强烈反对")
    
    def __init__(self, value: str, weight: float, label: str):
        self._value = value
        self.weight = weight
        self.label = label
    
    @property
    def value(self):
        return self._value


class ConsensusMethod(Enum):
    """共识计算方法"""
    SIMPLE_MAJORITY = auto()      # 简单多数
    SUPER_MAJORITY = auto()       # 绝对多数 (2/3)
    UNANIMOUS = auto()            # 全体一致
    WEIGHTED_AVERAGE = auto()     # 加权平均
    BORDA_COUNT = auto()          # 博尔达计数


@dataclass
class Vote:
    """投票记录"""
    voter_id: str
    voter_role: str
    option: VoteOption
    reasoning: str  # 投票理由
    confidence: float  # 置信度 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def weighted_vote(self) -> float:
        """计算加权投票值"""
        return self.option.weight * self.confidence


@dataclass
class VotingProposal:
    """投票提案"""
    proposal_id: str
    title: str
    description: str
    options: List[str]  # 投票选项
    proposer: str  # 提案人
    quorum: float = 0.67  # 法定人数 (默认2/3)
    deadline: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "description": self.description,
            "options": self.options,
            "proposer": self.proposer,
            "quorum": self.quorum
        }


@dataclass
class VotingResult:
    """投票结果"""
    proposal_id: str
    consensus_reached: bool
    winning_option: Optional[str]
    vote_count: Dict[str, int]
    weighted_score: float
    participation_rate: float
    voter_details: List[Vote]
    consensus_method: ConsensusMethod
    
    def to_dict(self) -> Dict:
        return {
            "proposal_id": self.proposal_id,
            "consensus_reached": self.consensus_reached,
            "winning_option": self.winning_option,
            "vote_count": self.vote_count,
            "weighted_score": round(self.weighted_score, 2),
            "participation_rate": round(self.participation_rate, 2),
            "consensus_method": self.consensus_method.name
        }


class ConsensusVotingSystem:
    """
    共识投票系统
    
    功能：
    1. 发起投票提案
    2. 收集Agent投票
    3. 计算共识结果
    4. 处理投票争议
    5. 生成投票报告
    """
    
    def __init__(self):
        self.proposals: Dict[str, VotingProposal] = {}
        self.votes: Dict[str, List[Vote]] = defaultdict(list)
        self.results: Dict[str, VotingResult] = {}
        self.voter_weights: Dict[str, float] = {}
        self.server = KimiMCPExtendedServer()
    
    def set_voter_weight(self, voter_id: str, weight: float):
        """设置投票人权重"""
        self.voter_weights[voter_id] = weight
    
    def create_proposal(
        self,
        title: str,
        description: str,
        options: List[str],
        proposer: str,
        quorum: float = 0.67
    ) -> VotingProposal:
        """创建投票提案"""
        proposal_id = f"proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        proposal = VotingProposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            options=options,
            proposer=proposer,
            quorum=quorum
        )
        
        self.proposals[proposal_id] = proposal
        
        print(f"\n📋 投票提案创建:")
        print(f"   ID: {proposal_id}")
        print(f"   标题: {title}")
        print(f"   选项: {', '.join(options)}")
        print(f"   提案人: {proposer}")
        print(f"   法定人数: {quorum*100}%")
        
        return proposal
    
    def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        voter_role: str,
        option: VoteOption,
        reasoning: str,
        confidence: float = 1.0
    ) -> bool:
        """投票"""
        if proposal_id not in self.proposals:
            print(f"❌ 提案不存在: {proposal_id}")
            return False
        
        # 检查是否已投票
        existing = [v for v in self.votes[proposal_id] if v.voter_id == voter_id]
        if existing:
            print(f"⚠️  {voter_id} 已投票，更新投票")
            self.votes[proposal_id].remove(existing[0])
        
        vote = Vote(
            voter_id=voter_id,
            voter_role=voter_role,
            option=option,
            reasoning=reasoning,
            confidence=confidence
        )
        
        self.votes[proposal_id].append(vote)
        
        print(f"   🗳️  {voter_id} ({voter_role}) 投票: {option.label}")
        if reasoning:
            print(f"      理由: {reasoning[:50]}...")
        
        return True
    
    def calculate_consensus(
        self,
        proposal_id: str,
        method: ConsensusMethod = ConsensusMethod.SUPER_MAJORITY
    ) -> VotingResult:
        """计算共识结果"""
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")
        
        votes = self.votes.get(proposal_id, [])
        
        if not votes:
            return VotingResult(
                proposal_id=proposal_id,
                consensus_reached=False,
                winning_option=None,
                vote_count={},
                weighted_score=0.0,
                participation_rate=0.0,
                voter_details=[],
                consensus_method=method
            )
        
        # 计算投票统计
        vote_count = defaultdict(int)
        weighted_scores = defaultdict(float)
        
        for vote in votes:
            weight = self.voter_weights.get(vote.voter_id, 1.0)
            vote_count[vote.option.value] += 1
            weighted_scores[vote.option.value] += vote.weighted_vote * weight
        
        # 根据共识方法判断
        total_votes = len(votes)
        total_weighted = sum(abs(v.weighted_vote) for v in votes)
        
        if method == ConsensusMethod.SIMPLE_MAJORITY:
            consensus_reached, winner = self._check_simple_majority(vote_count, proposal.options)
        elif method == ConsensusMethod.SUPER_MAJORITY:
            consensus_reached, winner = self._check_super_majority(weighted_scores, total_weighted, proposal.quorum)
        elif method == ConsensusMethod.WEIGHTED_AVERAGE:
            consensus_reached, winner = self._check_weighted_average(weighted_scores)
        else:
            consensus_reached, winner = False, None
        
        # 计算参与率（假设有5个Agent）
        total_agents = 5
        participation_rate = len(set(v.voter_id for v in votes)) / total_agents
        
        result = VotingResult(
            proposal_id=proposal_id,
            consensus_reached=consensus_reached,
            winning_option=winner,
            vote_count=dict(vote_count),
            weighted_score=sum(weighted_scores.values()),
            participation_rate=participation_rate,
            voter_details=votes,
            consensus_method=method
        )
        
        self.results[proposal_id] = result
        
        return result
    
    def _check_simple_majority(self, vote_count: Dict, options: List[str]) -> Tuple[bool, Optional[str]]:
        """检查简单多数"""
        total = sum(vote_count.values())
        for option in options:
            agree_count = vote_count.get("agree", 0) + vote_count.get("strongly_agree", 0)
            if agree_count / total > 0.5:
                return True, option
        return False, None
    
    def _check_super_majority(
        self, 
        weighted_scores: Dict, 
        total: float,
        quorum: float
    ) -> Tuple[bool, Optional[str]]:
        """检查绝对多数"""
        positive_score = weighted_scores.get("agree", 0) + weighted_scores.get("strongly_agree", 0)
        
        if total > 0 and positive_score / total >= quorum:
            return True, "approved"
        
        return False, None
    
    def _check_weighted_average(self, weighted_scores: Dict) -> Tuple[bool, Optional[str]]:
        """检查加权平均"""
        total_score = sum(weighted_scores.values())
        
        if total_score > 0:
            return True, "approved"
        return False, "rejected"
    
    def display_result(self, proposal_id: str):
        """显示投票结果"""
        result = self.results.get(proposal_id)
        if not result:
            print(f"❌ 无结果: {proposal_id}")
            return
        
        print(f"\n📊 投票结果 ({proposal_id}):")
        print(f"   共识达成: {'✅ 是' if result.consensus_reached else '❌ 否'}")
        print(f"   获胜选项: {result.winning_option or 'N/A'}")
        print(f"   计算方法: {result.consensus_method.name}")
        print(f"   参与率: {result.participation_rate*100:.0f}%")
        print(f"   加权得分: {result.weighted_score:.2f}")
        
        print(f"\n   投票分布:")
        for option, count in result.vote_count.items():
            bar = "█" * count + "░" * (5 - count)
            print(f"      {option:20} │{bar}│ {count}")
        
        print(f"\n   投票详情:")
        for vote in result.voter_details:
            icon = "👍" if vote.option.weight > 0 else "👎" if vote.option.weight < 0 else "😐"
            print(f"      {icon} {vote.voter_id} ({vote.voter_role}): {vote.option.label}")


class MultiAgentConsensusDemo:
    """多智能体共识演示"""
    
    def __init__(self):
        self.voting_system = ConsensusVotingSystem()
        self.server = KimiMCPExtendedServer()
    
    async def demo_consensus_voting(self):
        """演示共识投票"""
        print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🗳️  CONSENSUS VOTING SYSTEM - P3 FINAL                                ║
║                                                                          ║
║   场景: 多个Agent对重要技术决策进行投票                                   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
        """)
        
        # 场景: 选择技术栈
        proposal = self.voting_system.create_proposal(
            title="技术栈选择",
            description="项目应该使用哪种AI框架？",
            options=["LangChain", "AutoGen", "LlamaIndex"],
            proposer="tech_lead"
        )
        
        # 设置投票人权重（根据专业程度）
        self.voting_system.set_voter_weight("senior_architect", 1.5)
        self.voting_system.set_voter_weight("ml_expert", 1.3)
        self.voting_system.set_voter_weight("senior_dev", 1.2)
        self.voting_system.set_voter_weight("junior_dev", 1.0)
        self.voting_system.set_voter_weight("devops", 0.8)
        
        print("\n🗳️  开始投票...")
        
        # 模拟各Agent投票
        votes = [
            ("senior_architect", "Senior Architect", VoteOption.STRONGLY_AGREE, 
             "LangChain生态最完善，文档齐全，适合生产环境", 0.95),
            
            ("ml_expert", "ML Expert", VoteOption.AGREE,
             "LangChain的模块化设计很好，但AutoGen的多智能体支持更强", 0.85),
            
            ("senior_dev", "Senior Developer", VoteOption.AGREE,
             "团队对LangChain更熟悉，学习成本低", 0.90),
            
            ("junior_dev", "Junior Developer", VoteOption.NEUTRAL,
             "两种框架都可以，需要更多培训", 0.70),
            
            ("devops", "DevOps Engineer", VoteOption.AGREE,
             "LangChain的部署工具更成熟", 0.80)
        ]
        
        for voter_id, role, option, reasoning, confidence in votes:
            self.voting_system.cast_vote(
                proposal.proposal_id,
                voter_id,
                role,
                option,
                reasoning,
                confidence
            )
        
        # 计算结果
        print("\n📊 计算共识结果...")
        result = self.voting_system.calculate_consensus(
            proposal.proposal_id,
            ConsensusMethod.SUPER_MAJORITY
        )
        
        # 显示结果
        self.voting_system.display_result(proposal.proposal_id)
        
        return result
    
    async def demo_controversial_decision(self):
        """演示有争议的决策"""
        print("\n" + "="*70)
        print("⚖️  争议决策场景")
        print("="*70)
        
        proposal = self.voting_system.create_proposal(
            title="是否采用微服务架构",
            description="项目初期是否应该直接使用微服务架构？",
            options=["采用微服务", "单体优先", "混合方案"],
            proposer="cto"
        )
        
        print("\n🗳️  投票 (存在分歧)...")
        
        # 有分歧的投票
        votes = [
            ("architect_a", "Architect A", VoteOption.STRONGLY_AGREE,
             "微服务是未来趋势，应该从一开始就设计好", 0.90),
            
            ("architect_b", "Architect B", VoteOption.DISAGREE,
             "项目初期应该快速迭代，单体更合适", 0.85),
            
            ("senior_dev_a", "Senior Dev A", VoteOption.AGREE,
             "团队有微服务经验，可以handle", 0.80),
            
            ("senior_dev_b", "Senior Dev B", VoteOption.STRONGLY_DISAGREE,
             "运维成本太高，前期不值得", 0.90),
            
            ("product_manager", "Product Manager", VoteOption.NEUTRAL,
             "需要评估对交付时间的影响", 0.70)
        ]
        
        for voter_id, role, option, reasoning, confidence in votes:
            self.voting_system.cast_vote(
                proposal.proposal_id,
                voter_id,
                role,
                option,
                reasoning,
                confidence
            )
        
        result = self.voting_system.calculate_consensus(
            proposal.proposal_id,
            ConsensusMethod.SUPER_MAJORITY
        )
        
        self.voting_system.display_result(proposal.proposal_id)
        
        if not result.consensus_reached:
            print("\n⚠️  未达成共识，需要:")
            print("   1. 进一步讨论各方关切")
            print("   2. 寻找折中方案")
            print("   3. 或者请更高级决策者裁决")


async def demo_p3_improvements():
    """演示P3级改进"""
    demo = MultiAgentConsensusDemo()
    
    # 演示1: 达成共识
    await demo.demo_consensus_voting()
    
    # 演示2: 争议决策
    await demo.demo_controversial_decision()
    
    print("\n" + "="*70)
    print("✅ P3改进完成！")
    print("="*70)
    print("\n改进亮点:")
    print("   1. ✅ 共识投票机制 - 民主决策")
    print("   2. ✅ 权重投票系统 - 专家意见更重要")
    print("   3. ✅ 多种共识算法 - 简单多数/绝对多数/加权")
    print("   4. ✅ 投票理由记录 - 可追溯决策过程")
    print("\n🎉 所有优先级改进完成！")
    print("   P0: 仲裁者 + 冲突检测 ✅")
    print("   P1: 深度评估 + 迭代改进 ✅")
    print("   P2: 人类审核 + 版本控制 ✅")
    print("   P3: 共识投票 ✅")


if __name__ == "__main__":
    asyncio.run(demo_p3_improvements())
