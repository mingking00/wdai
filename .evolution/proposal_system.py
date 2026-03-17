#!/usr/bin/env python3
"""
wdai 进化提案系统 (Evolution Proposal System)
用于 YELLOW ZONE 的提议-审批流程
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib

class ProposalSystem:
    """
    管理进化提案的创建、审批和执行
    """
    
    PROPOSAL_STATUS = {
        "PENDING": "⏳ 待审批",
        "APPROVED": "✅ 已批准",
        "REJECTED": "❌ 已拒绝",
        "EXECUTED": "✓ 已执行",
        "CANCELLED": "🚫 已取消"
    }
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.path.expanduser("~/.openclaw/workspace"))
        self.proposals_dir = self.workspace / ".evolution" / "proposals"
        self.approved_dir = self.workspace / ".evolution" / "approved"
        self.rejected_dir = self.workspace / ".evolution" / "rejected"
        
        for d in [self.proposals_dir, self.approved_dir, self.rejected_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def create_proposal(self, 
                       title: str,
                       problem: str,
                       solution: str,
                       expected_effect: str,
                       risk_assessment: str,
                       implementation_steps: List[str],
                       impact: str = "medium") -> str:
        """
        创建新提案
        
        Args:
            title: 提案标题
            problem: 问题描述
            solution: 解决方案
            expected_effect: 预期效果
            risk_assessment: 风险评估
            implementation_steps: 实施步骤
            impact: 影响等级 (low/medium/high)
        
        Returns:
            proposal_id: 提案ID
        """
        # 生成提案ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        content_hash = hashlib.md5(f"{title}{problem}".encode()).hexdigest()[:8]
        proposal_id = f"PROP_{timestamp}_{content_hash}"
        
        proposal = {
            "id": proposal_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "type": self._classify_type(title, solution),
            "impact": impact,
            "content": {
                "problem": problem,
                "solution": solution,
                "expected_effect": expected_effect,
                "risk_assessment": risk_assessment,
                "implementation_steps": implementation_steps
            },
            "status": "PENDING",
            "approval": {
                "approved_by": None,
                "approved_at": None,
                "decision_reason": None
            },
            "execution": {
                "executed_at": None,
                "result": None,
                "logs": []
            }
        }
        
        # 保存提案
        filepath = self.proposals_dir / f"{proposal_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(proposal, f, indent=2, ensure_ascii=False)
        
        # 同时生成markdown便于阅读
        self._generate_markdown(proposal)
        
        return proposal_id
    
    def _classify_type(self, title: str, solution: str) -> str:
        """自动分类提案类型"""
        text = f"{title} {solution}".lower()
        
        if any(k in text for k in ["架构", "architecture", "framework", "系统"]):
            return "架构"
        elif any(k in text for k in ["工具", "tool", "script", "cli"]):
            return "工具"
        elif any(k in text for k in ["流程", "process", "workflow", "pipeline"]):
            return "流程"
        elif any(k in text for k in ["安全", "safety", "security", "zone"]):
            return "安全"
        elif any(k in text for k in ["性能", "performance", "优化", "optimize"]):
            return "性能"
        else:
            return "其他"
    
    def _generate_markdown(self, proposal: Dict):
        """生成markdown格式的提案文档"""
        md_content = f"""# 进化提案: {proposal['title']}

**提案ID**: `{proposal['id']}`  
**时间**: {proposal['created_at']}  
**类型**: {proposal['type']}  
**影响**: {'🔴' if proposal['impact'] == 'high' else '🟡' if proposal['impact'] == 'medium' else '🟢'} {proposal['impact'].upper()}

---

## 🎯 问题描述

{proposal['content']['problem']}

## 💡 解决方案

{proposal['content']['solution']}

## 📈 预期效果

{proposal['content']['expected_effect']}

## ⚠️ 风险评估

{proposal['content']['risk_assessment']}

## 🔧 实施步骤

"""
        for i, step in enumerate(proposal['content']['implementation_steps'], 1):
            md_content += f"{i}. {step}\n"
        
        md_content += f"""
---

## 📋 审批状态

**当前状态**: {self.PROPOSAL_STATUS[proposal['status']]}  
**审批人**: {proposal['approval']['approved_by'] or '__________'}  
**审批时间**: {proposal['approval']['approved_at'] or '__________'}  

### 决定

- [ ] **批准** - 同意实施此提案
- [ ] **拒绝** - 不同意实施（请说明原因）

**决定原因**: 
```
{proposal['approval']['decision_reason'] or '_________________________________'}
```

---

## 📝 执行记录

**执行时间**: {proposal['execution']['executed_at'] or 'N/A'}  
**执行结果**: {proposal['execution']['result'] or 'N/A'}  

### 执行日志

"""
        if proposal['execution']['logs']:
            for log in proposal['execution']['logs']:
                md_content += f"- {log}\n"
        else:
            md_content += "_暂无执行日志_\n"
        
        # 保存markdown
        filepath = self.proposals_dir / f"{proposal['id']}.md"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def approve_proposal(self, proposal_id: str, approver: str, reason: str = ""):
        """批准提案"""
        filepath = self.proposals_dir / f"{proposal_id}.json"
        
        if not filepath.exists():
            raise ValueError(f"提案不存在: {proposal_id}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            proposal = json.load(f)
        
        if proposal['status'] != "PENDING":
            raise ValueError(f"提案状态不正确: {proposal['status']}")
        
        proposal['status'] = "APPROVED"
        proposal['approval']['approved_by'] = approver
        proposal['approval']['approved_at'] = datetime.now().isoformat()
        proposal['approval']['decision_reason'] = reason
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(proposal, f, indent=2, ensure_ascii=False)
        
        # 移动到approved目录
        approved_path = self.approved_dir / f"{proposal_id}.json"
        import shutil
        shutil.copy(filepath, approved_path)
        
        # 更新markdown
        self._generate_markdown(proposal)
        
        return proposal
    
    def reject_proposal(self, proposal_id: str, approver: str, reason: str):
        """拒绝提案"""
        filepath = self.proposals_dir / f"{proposal_id}.json"
        
        if not filepath.exists():
            raise ValueError(f"提案不存在: {proposal_id}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            proposal = json.load(f)
        
        if proposal['status'] != "PENDING":
            raise ValueError(f"提案状态不正确: {proposal['status']}")
        
        proposal['status'] = "REJECTED"
        proposal['approval']['approved_by'] = approver
        proposal['approval']['approved_at'] = datetime.now().isoformat()
        proposal['approval']['decision_reason'] = reason
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(proposal, f, indent=2, ensure_ascii=False)
        
        # 移动到rejected目录
        rejected_path = self.rejected_dir / f"{proposal_id}.json"
        import shutil
        shutil.copy(filepath, rejected_path)
        
        # 更新markdown
        self._generate_markdown(proposal)
        
        return proposal
    
    def execute_proposal(self, proposal_id: str, execution_result: Dict):
        """标记提案为已执行"""
        filepath = self.proposals_dir / f"{proposal_id}.json"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            proposal = json.load(f)
        
        if proposal['status'] != "APPROVED":
            raise ValueError(f"提案未批准，当前状态: {proposal['status']}")
        
        proposal['status'] = "EXECUTED"
        proposal['execution']['executed_at'] = datetime.now().isoformat()
        proposal['execution']['result'] = execution_result
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(proposal, f, indent=2, ensure_ascii=False)
        
        # 更新markdown
        self._generate_markdown(proposal)
        
        return proposal
    
    def add_execution_log(self, proposal_id: str, log: str):
        """添加执行日志"""
        filepath = self.proposals_dir / f"{proposal_id}.json"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            proposal = json.load(f)
        
        proposal['execution']['logs'].append({
            "timestamp": datetime.now().isoformat(),
            "message": log
        })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(proposal, f, indent=2, ensure_ascii=False)
    
    def get_proposal(self, proposal_id: str) -> Optional[Dict]:
        """获取提案详情"""
        filepath = self.proposals_dir / f"{proposal_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_proposals(self, status: str = None, proposal_type: str = None) -> List[Dict]:
        """列出提案"""
        proposals = []
        
        for filepath in self.proposals_dir.glob("PROP_*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                proposal = json.load(f)
            
            if status and proposal.get('status') != status:
                continue
            if proposal_type and proposal.get('type') != proposal_type:
                continue
            
            proposals.append(proposal)
        
        return sorted(proposals, key=lambda x: x['created_at'], reverse=True)
    
    def get_pending_count(self) -> int:
        """获取待审批提案数量"""
        return len(self.list_proposals(status="PENDING"))
    
    def get_stats(self) -> Dict[str, int]:
        """获取提案统计"""
        stats = {"total": 0, "PENDING": 0, "APPROVED": 0, "REJECTED": 0, "EXECUTED": 0}
        
        for filepath in self.proposals_dir.glob("PROP_*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                proposal = json.load(f)
            
            stats["total"] += 1
            stats[proposal['status']] = stats.get(proposal['status'], 0) + 1
        
        return stats
    
    def generate_summary_report(self) -> str:
        """生成提案摘要报告"""
        stats = self.get_stats()
        pending = self.list_proposals(status="PENDING")
        recent_approved = self.list_proposals(status="APPROVED")[:5]
        
        report = f"""# 进化提案系统报告

**生成时间**: {datetime.now().isoformat()}

## 📊 统计概览

| 状态 | 数量 |
|:---|:---:|
| 🟡 待审批 | {stats['PENDING']} |
| ✅ 已批准 | {stats['APPROVED']} |
| ✓ 已执行 | {stats['EXECUTED']} |
| ❌ 已拒绝 | {stats['REJECTED']} |
| **总计** | **{stats['total']}** |

## ⏳ 待审批提案

"""
        if pending:
            for p in pending:
                report += f"- **{p['title']}** (`{p['id']}`) - {p['type']} - {p['impact']}\n"
        else:
            report += "_暂无待审批提案_\n"
        
        report += "\n## ✅ 最近批准的提案\n\n"
        if recent_approved:
            for p in recent_approved:
                report += f"- **{p['title']}** - 由 {p['approval']['approved_by']} 批准\n"
        else:
            report += "_暂无已批准提案_\n"
        
        return report


# ==================== 便捷函数 ====================

_proposal_system = None

def get_proposal_system() -> ProposalSystem:
    """获取全局提案系统实例"""
    global _proposal_system
    if _proposal_system is None:
        _proposal_system = ProposalSystem()
    return _proposal_system


if __name__ == "__main__":
    # 测试
    ps = ProposalSystem()
    
    # 创建提案
    proposal_id = ps.create_proposal(
        title="实施三区安全架构",
        problem="当前系统没有明确的安全边界，AI可能误修改核心文件",
        solution="实施RED/YELLOW/GREEN三区架构，明确每个区域的修改权限",
        expected_effect="提高系统安全性，防止意外修改核心配置",
        risk_assessment="低风险，主要是文档和流程变更",
        implementation_steps=[
            "标记所有核心文件为RED ZONE",
            "创建YELLOW ZONE提案目录",
            "实现提案审批系统",
            "更新相关文档"
        ],
        impact="high"
    )
    
    print(f"创建提案: {proposal_id}")
    print(f"\n{ps.generate_summary_report()}")
