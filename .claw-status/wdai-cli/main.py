#!/usr/bin/env python3
"""
wdai 统一CLI工具集
整合所有wdai工具到一个统一的命令行接口
"""

import click
import json
import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

@click.group()
@click.version_option(version="2.1.0")
def cli():
    """wdai - 工作空间自适应智能进化系统"""
    pass


# ==================== 仪表盘命令 ====================

@cli.group()
def dashboard():
    """系统监控仪表盘"""
    pass

@dashboard.command()
def show():
    """显示系统仪表盘"""
    from dashboard import SystemDashboard
    d = SystemDashboard()
    click.echo(d.generate_dashboard_text())

@dashboard.command()
def health():
    """显示系统健康度"""
    from dashboard import SystemDashboard
    d = SystemDashboard()
    h = d._calculate_health()
    click.echo(f"整体健康度: {h['overall']}% ({h['status']})")
    for comp, score in h['components'].items():
        click.echo(f"  {comp}: {score}%")

@dashboard.command()
@click.option('--json', 'as_json', is_flag=True, help='JSON格式输出')
def status(as_json):
    """获取系统状态"""
    from dashboard import SystemDashboard
    d = SystemDashboard()
    if as_json:
        click.echo(json.dumps(d.collect_all_status(), indent=2))
    else:
        s = d.collect_all_status()
        click.echo(f"系统时间: {s['timestamp']}")
        click.echo(f"工作空间: {s['workspace']}")


# ==================== 安全命令 ====================

@cli.group()
def safety():
    """三区安全检查"""
    pass

@safety.command()
@click.argument('filepath')
def zone(filepath):
    """检查文件所属安全区域"""
    from safety_checker import ZoneSafetyChecker
    c = ZoneSafetyChecker()
    z = c.get_file_zone(filepath)
    click.echo(f"{filepath} -> {z.value.upper()} ZONE")

@safety.command()
@click.argument('filepath')
def check(filepath):
    """检查文件修改权限"""
    from safety_checker import ZoneSafetyChecker
    c = ZoneSafetyChecker()
    r = c.check_modification_allowed(filepath)
    click.echo(r)

@safety.command()
def report():
    """生成安全报告"""
    from safety_checker import ZoneSafetyChecker
    c = ZoneSafetyChecker()
    click.echo(c.generate_safety_report())

@safety.command()
def blocked():
    """显示被阻止的修改尝试"""
    from safety_checker import ZoneSafetyChecker
    c = ZoneSafetyChecker()
    blocked = c.get_blocked_attempts()
    click.echo(f"被阻止的尝试 ({len(blocked)} 次):")
    for log in blocked[-10:]:
        click.echo(f"  - {log['filepath']} ({log['zone']}) at {log['timestamp']}")


# ==================== 提案命令 ====================

@cli.group()
def proposal():
    """进化提案管理"""
    pass

@proposal.command()
def list():
    """列出所有提案"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / '.evolution'))
    from proposal_system import ProposalSystem
    ps = ProposalSystem()
    proposals = ps.list_proposals()
    
    click.echo(f"总计: {len(proposals)} 个提案")
    click.echo()
    
    for p in proposals[:10]:
        status_emoji = {
            "PENDING": "🟡",
            "APPROVED": "✅",
            "EXECUTED": "✓",
            "REJECTED": "❌"
        }.get(p['status'], "⚪")
        click.echo(f"{status_emoji} {p['id']}")
        click.echo(f"   标题: {p['title']}")
        click.echo(f"   状态: {p['status']} | 类型: {p['type']} | 影响: {p['impact']}")
        click.echo()

@proposal.command()
@click.argument('proposal_id')
def show(proposal_id):
    """显示提案详情"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / '.evolution'))
    from proposal_system import ProposalSystem
    ps = ProposalSystem()
    p = ps.get_proposal(proposal_id)
    
    if not p:
        click.echo(f"提案未找到: {proposal_id}", err=True)
        return
    
    click.echo(f"提案: {p['title']}")
    click.echo(f"ID: {p['id']}")
    click.echo(f"状态: {p['status']}")
    click.echo(f"类型: {p['type']} | 影响: {p['impact']}")
    click.echo()
    click.echo(f"问题: {p['content']['problem'][:100]}...")

@proposal.command()
def pending():
    """显示待审批提案"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / '.evolution'))
    from proposal_system import ProposalSystem
    ps = ProposalSystem()
    pending = ps.list_proposals(status="PENDING")
    
    click.echo(f"待审批提案: {len(pending)} 个")
    click.echo()
    
    for p in pending:
        impact_emoji = "🔴" if p['impact'] == 'high' else "🟡" if p['impact'] == 'medium' else "🟢"
        click.echo(f"{impact_emoji} {p['title']}")
        click.echo(f"   ID: {p['id']}")
        click.echo(f"   类型: {p['type']}")
        click.echo()

@proposal.command()
def stats():
    """显示提案统计"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / '.evolution'))
    from proposal_system import ProposalSystem
    ps = ProposalSystem()
    stats = ps.get_stats()
    
    click.echo("提案统计:")
    for k, v in stats.items():
        click.echo(f"  {k}: {v}")


# ==================== 状态命令 ====================

@cli.group()
def state():
    """持久状态管理"""
    pass

@state.command()
def tasks():
    """显示任务列表"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / '.state'))
    from state_manager import get_state_manager
    sm = get_state_manager()
    stats = sm.get_stats()
    
    click.echo(f"任务统计:")
    click.echo(f"  总计: {stats['tasks']['total']}")
    for status, count in stats['tasks'].get('by_status', {}).items():
        click.echo(f"  {status}: {count}")

@state.command()
def sessions():
    """显示会话列表"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / '.state'))
    from state_manager import get_state_manager
    sm = get_state_manager()
    stats = sm.get_stats()
    
    click.echo(f"会话: {stats['sessions']}")


# ==================== 内存命令 ====================

@cli.group()
def memory():
    """记忆系统管理"""
    pass

@memory.command()
def status():
    """显示记忆系统状态"""
    workspace = Path(os.path.expanduser("~/.openclaw/workspace"))
    memory_dir = workspace / "memory"
    
    if not memory_dir.exists():
        click.echo("记忆系统未初始化")
        return
    
    daily_dir = memory_dir / "daily"
    core_dir = memory_dir / "core"
    
    daily_count = len(list(daily_dir.glob("*.md"))) if daily_dir.exists() else 0
    core_count = len(list(core_dir.glob("*.md"))) if core_dir.exists() else 0
    
    click.echo(f"记忆系统状态:")
    click.echo(f"  每日记录: {daily_count}")
    click.echo(f"  核心记忆: {core_count}")


# ==================== 主入口 ====================

if __name__ == "__main__":
    cli()
