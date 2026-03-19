#!/usr/bin/env python3
"""
Bilibili 工作流集成 - 自动化监控和分析系统

功能：
1. 监控指定 UP 主的新视频
2. 自动分析视频内容（字幕、评论、AI总结）
3. 生成结构化报告
4. 支持定时任务和手动触发

用法：
    python bilibili_workflow.py init              # 初始化配置
    python bilibili_workflow.py monitor           # 手动运行监控
    python bilibili_workflow.py analyze <BV>      # 分析单个视频
    python bilibili_workflow.py report            # 生成历史报告
    python bilibili_workflow.py cron --enable     # 启用定时任务
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

import yaml


# ============================================================================
# 配置管理
# ============================================================================

CONFIG_DIR = Path.home() / ".config" / "bilibili-workflow"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
STATE_FILE = CONFIG_DIR / "state.json"
REPORTS_DIR = CONFIG_DIR / "reports"


@dataclass
class UPMonitorConfig:
    """UP 主监控配置"""
    uid: str
    name: str
    last_checked: Optional[str] = None
    last_video_bvid: Optional[str] = None
    enabled: bool = True
    analyze_new: bool = True  # 自动分析新视频


@dataclass
class WorkflowConfig:
    """工作流配置"""
    version: str = "1.0.0"
    check_interval_hours: int = 6  # 检查间隔
    max_videos_per_up: int = 5     # 每次最多检查视频数
    auto_analyze: bool = True      # 自动分析新视频
    generate_report: bool = True   # 生成报告
    report_format: str = "markdown"  # markdown, yaml, json
    
    # 分析选项
    include_subtitle: bool = True
    include_ai_summary: bool = True
    include_comments: bool = True
    max_comments: int = 20
    
    # 通知设置
    notification_on_new: bool = True
    notification_on_error: bool = True
    
    # 监控的 UP 主列表
    up_monitors: List[UPMonitorConfig] = field(default_factory=list)


class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def init_config() -> WorkflowConfig:
        """初始化配置"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        
        config = WorkflowConfig()
        
        # 示例配置
        config.up_monitors = [
            UPMonitorConfig(uid="946974", name="影视飓风", enabled=False),
        ]
        
        ConfigManager.save_config(config)
        return config
    
    @staticmethod
    def load_config() -> WorkflowConfig:
        """加载配置"""
        if not CONFIG_FILE.exists():
            return ConfigManager.init_config()
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 转换 UP 主列表
        up_monitors = [
            UPMonitorConfig(**up) for up in data.get('up_monitors', [])
        ]
        data['up_monitors'] = up_monitors
        
        return WorkflowConfig(**data)
    
    @staticmethod
    def save_config(config: WorkflowConfig):
        """保存配置"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        data = asdict(config)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    
    @staticmethod
    def load_state() -> Dict[str, Any]:
        """加载状态"""
        if not STATE_FILE.exists():
            return {"last_run": None, "video_history": {}}
        
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def save_state(state: Dict[str, Any]):
        """保存状态"""
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


# ============================================================================
# Bilibili CLI 调用
# ============================================================================

def run_bili(args: List[str]) -> tuple[bool, Dict]:
    """运行 bilibili-cli 命令"""
    cmd = ["bili"] + args + ["--yaml"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = yaml.safe_load(result.stdout)
        
        if result.returncode == 0 and output.get('ok'):
            return True, output.get('data', {})
        else:
            return False, output.get('error', {'message': 'Unknown error'})
    except Exception as e:
        return False, {'message': str(e)}


# ============================================================================
# 核心工作流
# ============================================================================

class BilibiliWorkflow:
    """Bilibili 工作流主类"""
    
    def __init__(self, config: WorkflowConfig = None):
        self.config = config or ConfigManager.load_config()
        self.state = ConfigManager.load_state()
    
    def check_up_videos(self, up_config: UPMonitorConfig) -> List[Dict]:
        """检查 UP 主的新视频"""
        print(f"🔍 检查 UP 主: {up_config.name} ({up_config.uid})")
        
        success, data = run_bili([
            "user-videos", up_config.uid,
            "--max", str(self.config.max_videos_per_up)
        ])
        
        if not success:
            print(f"  ❌ 获取失败: {data.get('message')}")
            return []
        
        videos = data.get('items', [])
        new_videos = []
        
        for video in videos:
            bvid = video.get('bvid')
            
            # 检查是否是新视频
            if bvid != up_config.last_video_bvid:
                new_videos.append(video)
            else:
                # 遇到已知的视频，停止检查
                break
        
        if new_videos:
            print(f"  ✅ 发现 {len(new_videos)} 个新视频")
            # 更新最后检查的视频
            up_config.last_video_bvid = new_videos[0].get('bvid')
        else:
            print(f"  ℹ️ 没有新视频")
        
        up_config.last_checked = datetime.now().isoformat()
        return new_videos
    
    def analyze_video(self, bvid: str) -> Optional[Dict]:
        """分析单个视频"""
        print(f"📹 分析视频: {bvid}")
        
        analysis = {
            'bvid': bvid,
            'analyzed_at': datetime.now().isoformat(),
            'metadata': {},
            'subtitle': '',
            'ai_summary': '',
            'comments': [],
            'warnings': []
        }
        
        # 获取视频信息
        success, data = run_bili(["video", bvid])
        if not success:
            print(f"  ❌ 获取视频信息失败")
            return None
        
        video_info = data.get('video', {})
        analysis['metadata'] = {
            'title': video_info.get('title'),
            'description': video_info.get('description', '')[:200] + '...',
            'duration': video_info.get('duration'),
            'owner': video_info.get('owner', {}).get('name'),
            'pubdate': video_info.get('pubdate'),
            'stats': video_info.get('stat', {})
        }
        
        # 获取字幕
        if self.config.include_subtitle:
            subtitle_data = data.get('subtitle')
            if subtitle_data:
                analysis['subtitle'] = str(subtitle_data)[:5000]  # 限制长度
                print(f"  ✅ 获取字幕 ({len(analysis['subtitle'])} 字符)")
            else:
                analysis['warnings'].append('无字幕')
                print(f"  ⚠️ 无字幕")
        
        # 获取 AI 总结
        if self.config.include_ai_summary and not analysis['subtitle']:
            print(f"  🤖 获取 AI 总结...")
            success, ai_data = run_bili(["video", bvid, "--ai"])
            if success:
                ai_summary = ai_data.get('ai_summary')
                if ai_summary:
                    analysis['ai_summary'] = str(ai_summary)[:2000]
                    print(f"  ✅ 获取 AI 总结")
        
        # 获取评论
        if self.config.include_comments:
            print(f"  💬 获取评论...")
            success, comments_data = run_bili([
                "video", bvid, "--comments"
            ])
            if success:
                comments = comments_data.get('comments', [])
                analysis['comments'] = [
                    {
                        'user': c.get('member', {}).get('uname'),
                        'content': c.get('content', {}).get('message', '')[:200],
                        'like': c.get('like', 0)
                    }
                    for c in comments[:self.config.max_comments]
                ]
                print(f"  ✅ 获取 {len(analysis['comments'])} 条评论")
        
        return analysis
    
    def generate_report(self, analyses: List[Dict], format: str = None) -> str:
        """生成报告"""
        format = format or self.config.report_format
        
        if format == "markdown":
            return self._generate_markdown_report(analyses)
        elif format == "yaml":
            return yaml.dump({
                'generated_at': datetime.now().isoformat(),
                'count': len(analyses),
                'analyses': analyses
            }, allow_unicode=True)
        elif format == "json":
            return json.dumps({
                'generated_at': datetime.now().isoformat(),
                'count': len(analyses),
                'analyses': analyses
            }, ensure_ascii=False, indent=2)
        else:
            return self._generate_markdown_report(analyses)
    
    def _generate_markdown_report(self, analyses: List[Dict]) -> str:
        """生成 Markdown 报告"""
        lines = [
            f"# Bilibili 视频分析报告",
            f"",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"视频数量: {len(analyses)}",
            f"",
            "---",
            f"",
        ]
        
        for i, analysis in enumerate(analyses, 1):
            meta = analysis.get('metadata', {})
            lines.extend([
                f"## {i}. {meta.get('title', 'Unknown')}",
                f"",
                f"- **BV号**: {analysis.get('bvid')}",
                f"- **UP主**: {meta.get('owner', 'Unknown')}",
                f"- **时长**: {meta.get('duration', 'Unknown')} 秒",
                f"- **播放量**: {meta.get('stats', {}).get('view', 'N/A')}",
                f"- **点赞**: {meta.get('stats', {}).get('like', 'N/A')}",
                f"",
            ])
            
            # 字幕/AI总结
            if analysis.get('subtitle'):
                lines.extend([
                    f"### 字幕摘要",
                    f"",
                    f"{analysis['subtitle'][:500]}...",
                    f"",
                ])
            elif analysis.get('ai_summary'):
                lines.extend([
                    f"### AI 总结",
                    f"",
                    f"{analysis['ai_summary']}",
                    f"",
                ])
            
            # 热门评论
            if analysis.get('comments'):
                lines.extend([
                    f"### 热门评论",
                    f"",
                ])
                for comment in analysis['comments'][:3]:
                    lines.append(f"- **{comment.get('user')}**: {comment.get('content')[:100]}... (👍 {comment.get('like')})")
                lines.append(f"")
            
            lines.extend(["---", ""])
        
        return "\n".join(lines)
    
    def run_monitor(self) -> List[Dict]:
        """运行监控工作流"""
        print(f"🚀 开始监控工作流 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"=" * 50)
        
        all_analyses = []
        
        for up_config in self.config.up_monitors:
            if not up_config.enabled:
                continue
            
            # 检查新视频
            new_videos = self.check_up_videos(up_config)
            
            # 自动分析
            if self.config.auto_analyze and new_videos:
                for video in new_videos:
                    bvid = video.get('bvid')
                    analysis = self.analyze_video(bvid)
                    if analysis:
                        all_analyses.append(analysis)
            
            print()
        
        # 保存配置和状态
        ConfigManager.save_config(self.config)
        self.state['last_run'] = datetime.now().isoformat()
        
        # 保存分析历史
        for analysis in all_analyses:
            self.state.setdefault('video_history', {})[analysis['bvid']] = {
                'analyzed_at': analysis['analyzed_at'],
                'title': analysis.get('metadata', {}).get('title')
            }
        
        ConfigManager.save_state(self.state)
        
        # 生成报告
        if self.config.generate_report and all_analyses:
            report = self.generate_report(all_analyses)
            report_file = REPORTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_file.write_text(report, encoding='utf-8')
            print(f"📄 报告已保存: {report_file}")
        
        print(f"=" * 50)
        print(f"✅ 监控完成，分析了 {len(all_analyses)} 个新视频")
        
        return all_analyses
    
    def add_up(self, uid: str, name: str = None):
        """添加监控的 UP 主"""
        # 获取 UP 主信息
        if not name:
            success, data = run_bili(["user", uid])
            if success:
                name = data.get('user', {}).get('name', f'UP_{uid}')
            else:
                name = f'UP_{uid}'
        
        # 检查是否已存在
        for up in self.config.up_monitors:
            if up.uid == uid:
                print(f"⚠️ {name} ({uid}) 已在监控列表中")
                return
        
        self.config.up_monitors.append(
            UPMonitorConfig(uid=uid, name=name, enabled=True)
        )
        ConfigManager.save_config(self.config)
        print(f"✅ 已添加 {name} ({uid}) 到监控列表")
    
    def list_ups(self):
        """列出监控的 UP 主"""
        print("📋 监控的 UP 主列表:")
        for i, up in enumerate(self.config.up_monitors, 1):
            status = "✅" if up.enabled else "❌"
            last = up.last_checked or "从未"
            print(f"  {i}. {status} {up.name} ({up.uid}) - 最后检查: {last}")
    
    def toggle_up(self, uid: str, enabled: bool = None):
        """启用/禁用 UP 主监控"""
        for up in self.config.up_monitors:
            if up.uid == uid:
                if enabled is None:
                    enabled = not up.enabled
                up.enabled = enabled
                ConfigManager.save_config(self.config)
                status = "启用" if enabled else "禁用"
                print(f"✅ 已{status} {up.name} 的监控")
                return
        print(f"❌ 未找到 UID: {uid}")


# ============================================================================
# 定时任务
# ============================================================================

def setup_cron(enable: bool = True):
    """设置/取消定时任务"""
    cron_line = f"0 */6 * * * cd {Path.cwd()} && python3 bilibili_workflow.py monitor >> {CONFIG_DIR}/cron.log 2>&1"
    
    try:
        # 获取当前 crontab
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        current_crontab = result.stdout if result.returncode == 0 else ""
        
        if enable:
            # 检查是否已存在
            if "bilibili_workflow.py" in current_crontab:
                print("ℹ️ 定时任务已存在")
                return
            
            # 添加新任务
            new_crontab = current_crontab + f"\n# Bilibili Workflow Monitor\n{cron_line}\n"
            subprocess.run(["crontab", "-"], input=new_crontab, text=True)
            print("✅ 已启用定时任务 (每6小时运行一次)")
        else:
            # 移除任务
            lines = current_crontab.split('\n')
            new_lines = []
            skip_next = False
            for line in lines:
                if "bilibili_workflow.py" in line:
                    continue
                if "# Bilibili Workflow Monitor" in line:
                    continue
                new_lines.append(line)
            
            new_crontab = '\n'.join(new_lines)
            subprocess.run(["crontab", "-"], input=new_crontab, text=True)
            print("✅ 已禁用定时任务")
    
    except Exception as e:
        print(f"❌ 设置定时任务失败: {e}")
        print("提示: 手动添加以下 crontab 条目:")
        print(f"  {cron_line}")


# ============================================================================
# CLI 入口
# ============================================================================

def print_help():
    help_text = """
Bilibili Workflow - 自动化监控和分析工作流

用法:
    python bilibili_workflow.py init                    # 初始化配置
    python bilibili_workflow.py monitor                 # 手动运行监控
    python bilibili_workflow.py analyze <BV号>          # 分析单个视频
    python bilibili_workflow.py report [格式]           # 生成历史报告
    python bilibili_workflow.py add <UID> [名称]        # 添加 UP 主
    python bilibili_workflow.py list                    # 列出监控的 UP 主
    python bilibili_workflow.py toggle <UID>            # 启用/禁用监控
    python bilibili_workflow.py cron --enable           # 启用定时任务
    python bilibili_workflow.py cron --disable          # 禁用定时任务

示例:
    # 初始化并添加 UP 主
    python bilibili_workflow.py init
    python bilibili_workflow.py add 946974 "影视飓风"
    
    # 手动运行一次监控
    python bilibili_workflow.py monitor
    
    # 分析单个视频
    python bilibili_workflow.py analyze BV1ABcsztEcY
    
    # 生成 Markdown 报告
    python bilibili_workflow.py report markdown
    
    # 启用自动定时监控
    python bilibili_workflow.py cron --enable

配置位置: ~/.config/bilibili-workflow/
"""
    print(help_text)


def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)
    
    command = args[0]
    
    try:
        if command == "init":
            config = ConfigManager.init_config()
            print(f"✅ 配置已初始化: {CONFIG_FILE}")
            print(f"编辑该文件添加要监控的 UP 主")
        
        elif command == "monitor":
            workflow = BilibiliWorkflow()
            workflow.run_monitor()
        
        elif command == "analyze":
            if len(args) < 2:
                print("错误: 需要提供 BV 号")
                print_help()
                sys.exit(1)
            
            bvid = args[1]
            workflow = BilibiliWorkflow()
            analysis = workflow.analyze_video(bvid)
            
            if analysis:
                print("\n" + "=" * 50)
                print(workflow.generate_report([analysis], "markdown"))
        
        elif command == "report":
            format_type = args[1] if len(args) > 1 else "markdown"
            workflow = BilibiliWorkflow()
            
            # 从状态加载历史分析
            state = ConfigManager.load_state()
            history = state.get('video_history', {})
            
            if not history:
                print("ℹ️ 暂无分析历史")
                sys.exit(0)
            
            # 生成报告（这里简化处理，实际应该保存完整分析数据）
            print(f"📊 历史分析报告:")
            print(f"共分析过 {len(history)} 个视频")
            for bvid, info in list(history.items())[:10]:
                print(f"  - {bvid}: {info.get('title', 'Unknown')}")
        
        elif command == "add":
            if len(args) < 2:
                print("错误: 需要提供 UID")
                print_help()
                sys.exit(1)
            
            uid = args[1]
            name = args[2] if len(args) > 2 else None
            
            workflow = BilibiliWorkflow()
            workflow.add_up(uid, name)
        
        elif command == "list":
            workflow = BilibiliWorkflow()
            workflow.list_ups()
        
        elif command == "toggle":
            if len(args) < 2:
                print("错误: 需要提供 UID")
                print_help()
                sys.exit(1)
            
            uid = args[1]
            workflow = BilibiliWorkflow()
            workflow.toggle_up(uid)
        
        elif command == "cron":
            if "--enable" in args:
                setup_cron(enable=True)
            elif "--disable" in args:
                setup_cron(enable=False)
            else:
                print("请使用 --enable 或 --disable")
                print_help()
        
        else:
            print(f"未知命令: {command}")
            print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⏹️ 已取消")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
