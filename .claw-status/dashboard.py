#!/usr/bin/env python3
"""
wdai 系统监控仪表盘 (System Dashboard)
聚合所有系统状态到一个统一视图
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

class SystemDashboard:
    """系统监控仪表盘"""
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.path.expanduser("~/.openclaw/workspace"))
        self.status_file = self.workspace / "STATUS.md"
        
        # 各系统路径
        self.scheduler_dir = self.workspace / ".scheduler"
        self.state_dir = self.workspace / ".state"
        self.evolution_dir = self.workspace / ".evolution"
        self.claw_status_dir = self.workspace / ".claw-status"
    
    def collect_all_status(self) -> Dict[str, Any]:
        """收集所有系统状态"""
        return {
            "timestamp": datetime.now().isoformat(),
            "workspace": str(self.workspace),
            "systems": {
                "scheduler": self._get_scheduler_status(),
                "state": self._get_state_status(),
                "evolution": self._get_evolution_status(),
                "proposals": self._get_proposal_status(),
                "safety": self._get_safety_status(),
                "memory": self._get_memory_status(),
            },
            "health": self._calculate_health()
        }
    
    def _get_scheduler_status(self) -> Dict:
        """获取调度器状态"""
        status = {"running": False, "last_execution": None, "tasks": []}
        
        # 检查执行日志
        execution_log = self.scheduler_dir / "execution_log.json"
        if execution_log.exists():
            try:
                with open(execution_log, 'r') as f:
                    logs = json.load(f)
                    if logs:
                        last = logs[-1]
                        status["last_execution"] = last.get("datetime")
                        status["running"] = True
            except:
                pass
        
        return status
    
    def _get_state_status(self) -> Dict:
        """获取状态管理系统状态"""
        status = {"initialized": False, "sessions": 0, "tasks": 0}
        
        if self.state_dir.exists():
            status["initialized"] = True
            
            # 统计会话
            sessions_dir = self.state_dir / "sessions"
            if sessions_dir.exists():
                status["sessions"] = len(list(sessions_dir.glob("*.json")))
            
            # 统计任务
            tasks_dir = self.state_dir / "tasks"
            if tasks_dir.exists():
                status["tasks"] = len(list(tasks_dir.glob("*.json")))
        
        return status
    
    def _get_evolution_status(self) -> Dict:
        """获取进化系统状态"""
        status = {"initialized": False, "proposals": 0, "approved": 0, "executed": 0}
        
        if self.evolution_dir.exists():
            status["initialized"] = True
            
            # 统计提案
            proposals_dir = self.evolution_dir / "proposals"
            if proposals_dir.exists():
                proposals = list(proposals_dir.glob("PROP_*.json"))
                status["proposals"] = len(proposals)
                
                # 统计各状态
                for p in proposals:
                    try:
                        with open(p, 'r') as f:
                            data = json.load(f)
                            p_status = data.get("status", "")
                            if p_status == "APPROVED":
                                status["approved"] += 1
                            elif p_status == "EXECUTED":
                                status["executed"] += 1
                    except:
                        pass
        
        return status
    
    def _get_proposal_status(self) -> Dict:
        """获取提案系统详细状态"""
        pending = []
        recent_executed = []
        
        proposals_dir = self.evolution_dir / "proposals"
        if proposals_dir.exists():
            for p in proposals_dir.glob("PROP_*.json"):
                try:
                    with open(p, 'r') as f:
                        data = json.load(f)
                        
                        if data.get("status") == "PENDING":
                            pending.append({
                                "id": data.get("id"),
                                "title": data.get("title"),
                                "type": data.get("type"),
                                "impact": data.get("impact")
                            })
                        elif data.get("status") == "EXECUTED":
                            recent_executed.append({
                                "id": data.get("id"),
                                "title": data.get("title"),
                                "executed_at": data.get("execution", {}).get("executed_at")
                            })
                except:
                    pass
        
        # 排序
        pending = sorted(pending, key=lambda x: x["id"], reverse=True)[:5]
        recent_executed = sorted(recent_executed, key=lambda x: x.get("executed_at", ""), reverse=True)[:5]
        
        return {
            "pending_count": len(pending),
            "pending": pending,
            "recent_executed": recent_executed
        }
    
    def _get_safety_status(self) -> Dict:
        """获取安全检查状态"""
        status = {"initialized": False, "audit_entries": 0, "blocked_count": 0}
        
        audit_log = self.claw_status_dir / "safety_audit.log"
        if audit_log.exists():
            status["initialized"] = True
            
            try:
                with open(audit_log, 'r') as f:
                    entries = [json.loads(line) for line in f if line.strip()]
                    status["audit_entries"] = len(entries)
                    status["blocked_count"] = len([e for e in entries if not e.get("allowed", True)])
            except:
                pass
        
        return status
    
    def _get_memory_status(self) -> Dict:
        """获取记忆系统状态"""
        status = {"daily_entries": 0, "core_entries": 0}
        
        memory_dir = self.workspace / "memory"
        if memory_dir.exists():
            # 每日记录
            daily_dir = memory_dir / "daily"
            if daily_dir.exists():
                status["daily_entries"] = len(list(daily_dir.glob("*.md")))
            
            # 核心记忆
            core_dir = memory_dir / "core"
            if core_dir.exists():
                status["core_entries"] = len(list(core_dir.glob("*.md")))
        
        return status
    
    def _calculate_health(self) -> Dict:
        """计算系统健康度"""
        scores = {}
        
        # 各子系统健康度
        scores["state_system"] = 100 if self.state_dir.exists() else 0
        scores["evolution_system"] = 100 if self.evolution_dir.exists() else 0
        scores["safety_system"] = 100 if (self.claw_status_dir / "safety_checker.py").exists() else 0
        scores["memory_system"] = 100 if (self.workspace / "memory").exists() else 0
        
        # 整体健康度
        overall = sum(scores.values()) / len(scores) if scores else 0
        
        return {
            "overall": round(overall, 1),
            "status": "healthy" if overall >= 80 else "degraded" if overall >= 50 else "critical",
            "components": scores
        }
    
    def generate_dashboard_text(self) -> str:
        """生成文本格式的仪表盘"""
        status = self.collect_all_status()
        health = status["health"]
        
        # 健康状态emoji
        health_emoji = "🟢" if health["status"] == "healthy" else "🟡" if health["status"] == "degraded" else "🔴"
        
        dashboard = f"""╔═══════════════════════════════════════════════════════════════╗
║                    wdai 系统监控仪表盘                         ║
║                    {health_emoji} 健康度: {health['overall']}% | {health['status'].upper()}                 ║
╚═══════════════════════════════════════════════════════════════╝

📊 系统状态概览
────────────────────────────────────────────────────────────────

"""
        
        # 各系统状态
        systems = status["systems"]
        
        # 状态系统
        state = systems["state"]
        dashboard += f"💾 持久状态系统\n"
        dashboard += f"   状态: {'✅ 运行中' if state['initialized'] else '❌ 未初始化'}\n"
        dashboard += f"   会话: {state['sessions']} | 任务: {state['tasks']}\n\n"
        
        # 进化系统
        evolution = systems["evolution"]
        dashboard += f"🧬 进化提案系统\n"
        dashboard += f"   状态: {'✅ 运行中' if evolution['initialized'] else '❌ 未初始化'}\n"
        dashboard += f"   总提案: {evolution['proposals']} | 已批准: {evolution['approved']} | 已执行: {evolution['executed']}\n\n"
        
        # 提案详细
        proposals = systems["proposals"]
        dashboard += f"📝 提案队列\n"
        dashboard += f"   待审批: {proposals['pending_count']}\n"
        if proposals['pending']:
            for p in proposals['pending'][:3]:
                impact_emoji = "🔴" if p['impact'] == 'high' else "🟡" if p['impact'] == 'medium' else "🟢"
                dashboard += f"   • {impact_emoji} {p['title'][:40]}...\n"
        dashboard += "\n"
        
        # 安全检查
        safety = systems["safety"]
        dashboard += f"🔒 三区安全检查\n"
        dashboard += f"   状态: {'✅ 已启用' if safety['initialized'] else '⚠️ 未启用'}\n"
        dashboard += f"   审计记录: {safety['audit_entries']} | 阻止事件: {safety['blocked_count']}\n\n"
        
        # 记忆系统
        memory = systems["memory"]
        dashboard += f"🧠 记忆系统\n"
        dashboard += f"   每日记录: {memory['daily_entries']} | 核心记忆: {memory['core_entries']}\n\n"
        
        # 最近执行的提案
        if proposals['recent_executed']:
            dashboard += "✅ 最近执行的提案\n"
            dashboard += "────────────────────────────────────────────────────────────────\n"
            for p in proposals['recent_executed'][:3]:
                dashboard += f"   • {p['title'][:50]}...\n"
            dashboard += "\n"
        
        # 健康度详情
        dashboard += "🏥 组件健康度\n"
        dashboard += "────────────────────────────────────────────────────────────────\n"
        for component, score in health["components"].items():
            bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
            dashboard += f"   {component:20s} [{bar}] {score}%\n"
        
        dashboard += f"""
────────────────────────────────────────────────────────────────
📅 生成时间: {status['timestamp']}
"""
        
        return dashboard
    
    def generate_dashboard_json(self) -> Dict:
        """生成JSON格式的仪表盘数据"""
        return self.collect_all_status()
    
    def save_dashboard(self):
        """保存仪表盘到STATUS.md"""
        dashboard_text = self.generate_dashboard_text()
        
        with open(self.status_file, 'w', encoding='utf-8') as f:
            f.write(dashboard_text)
        
        return self.status_file


# ==================== CLI接口 ====================

if __name__ == "__main__":
    import sys
    
    dashboard = SystemDashboard()
    
    if len(sys.argv) < 2:
        # 默认显示仪表盘
        print(dashboard.generate_dashboard_text())
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "--text" or command == "-t":
        print(dashboard.generate_dashboard_text())
    
    elif command == "--json" or command == "-j":
        print(json.dumps(dashboard.generate_dashboard_json(), indent=2))
    
    elif command == "--save" or command == "-s":
        filepath = dashboard.save_dashboard()
        print(f"✅ 仪表盘已保存到: {filepath}")
    
    elif command == "--health":
        health = dashboard._calculate_health()
        print(f"整体健康度: {health['overall']}% ({health['status']})")
        for component, score in health["components"].items():
            print(f"  {component}: {score}%")
    
    else:
        print(f"Unknown command: {command}")
        print("Usage: python dashboard.py [--text|--json|--save|--health]")
