#!/usr/bin/env python3
"""
wdai 自主进化执行器 v2.0
全自动外循环 + GitHub学习 + 7分钟记录 + 自动重启
"""

import json
import time
import os
import sys
import signal
import subprocess
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 系统目录
EVOLUTION_DIR = Path("/root/.openclaw/workspace/.evolution")
SCHEDULER_DIR = Path("/root/.openclaw/workspace/.scheduler")
MEMORY_DIR = Path("/root/.openclaw/workspace/memory/daily")
STATUS_FILE = SCHEDULER_DIR / "autonomous_status.json"
LOG_FILE = SCHEDULER_DIR / "autonomous_log.json"

class AutonomousExecutor:
    """
    自主执行器
    全自动运行直到用户干预
    """
    
    def __init__(self):
        self.running = True
        self.start_time = time.time()
        self.last_record_time = 0
        self.last_evolution_time = 0
        self.last_github_check = 0
        self.cycle_count = 0
        self.error_count = 0
        
        self.RECORD_INTERVAL = 420  # 7分钟
        self.EVOLUTION_INTERVAL = 3600  # 1小时
        self.GITHUB_INTERVAL = 1800  # 30分钟
        self.RESTART_TIMEOUT = 600  # 10分钟无响应自动重启
        
        self._load_status()
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """设置信号处理"""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """信号处理"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 收到停止信号，正在保存状态...")
        self.running = False
        self._save_status()
        
    def _load_status(self):
        """加载状态"""
        if STATUS_FILE.exists():
            with open(STATUS_FILE, 'r') as f:
                status = json.load(f)
                self.cycle_count = status.get('cycle_count', 0)
                self.error_count = status.get('error_count', 0)
                self.last_evolution_time = status.get('last_evolution_time', 0)
                
    def _save_status(self):
        """保存状态"""
        with open(STATUS_FILE, 'w') as f:
            json.dump({
                'cycle_count': self.cycle_count,
                'error_count': self.error_count,
                'last_evolution_time': self.last_evolution_time,
                'last_save': time.time(),
                'running': self.running
            }, f, indent=2)
            
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'cycle': self.cycle_count
        }
        
        # 追加到日志
        logs = []
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        logs.append(log_entry)
        logs = logs[-500:]  # 只保留最近500条
        
        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
            
        print(f"[{timestamp}] [{level}] {message}")
        
    def _append_to_daily_memory(self, content: str):
        """追加到每日记忆"""
        today_file = MEMORY_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"
        with open(today_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n---\n\n**[{datetime.now().strftime('%H:%M:%S')}] 自主进化记录**\n\n{content}\n")
            
    def run_evolution_loop(self) -> bool:
        """执行外循环进化"""
        self._log("🔄 执行外循环进化...")
        
        try:
            result = subprocess.run(
                ['python3', 'evolution_loop_v2.py'],
                cwd=str(EVOLUTION_DIR),
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            success = result.returncode == 0
            if success:
                self._log("✅ 外循环完成")
            else:
                self._log(f"⚠️ 外循环返回非零: {result.stderr[:200]}", "WARN")
                
            self.last_evolution_time = time.time()
            return success
            
        except subprocess.TimeoutExpired:
            self._log("⏱️ 外循环超时", "WARN")
            return False
        except Exception as e:
            self._log(f"❌ 外循环错误: {e}", "ERROR")
            self.error_count += 1
            return False
            
    def discover_github_projects(self) -> List[Dict]:
        """发现GitHub项目学习"""
        self._log("🔍 发现GitHub项目...")
        
        # 基于用户收藏的兴趣方向
        interest_areas = [
            "AI agent memory architecture",
            "LLM autonomous evolution",
            "Claude Code skills",
            "multi-agent system",
            "RAG vector database",
            "MemRL reinforcement learning"
        ]
        
        discovered = []
        
        try:
            # 使用GitHub API搜索
            import requests
            
            query = random.choice(interest_areas)
            url = f"https://api.github.com/search/repositories?q={query.replace(' ', '+')}&sort=updated&order=desc&per_page=5"
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'wdai-autonomous-executor'
            }
            
            resp = requests.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('items', []):
                    discovered.append({
                        'name': item['full_name'],
                        'description': item['description'] or '',
                        'stars': item['stargazers_count'],
                        'url': item['html_url'],
                        'language': item['language'] or 'Unknown',
                        'discovered_at': datetime.now().isoformat()
                    })
                    
                self._log(f"✅ 发现 {len(discovered)} 个相关项目")
                
                # 保存发现的项目
                if discovered:
                    self._save_discovered_projects(discovered)
                    
        except Exception as e:
            self._log(f"⚠️ GitHub发现失败: {e}", "WARN")
            
        return discovered
        
    def _save_discovered_projects(self, projects: List[Dict]):
        """保存发现的项目"""
        projects_file = SCHEDULER_DIR / "discovered_projects.json"
        
        existing = []
        if projects_file.exists():
            with open(projects_file, 'r') as f:
                existing = json.load(f)
        
        # 合并并去重
        seen = {p['name'] for p in existing}
        for p in projects:
            if p['name'] not in seen:
                existing.append(p)
                seen.add(p['name'])
        
        # 只保留最近100个
        existing = existing[-100:]
        
        with open(projects_file, 'w') as f:
            json.dump(existing, f, indent=2)
            
    def _should_restart(self) -> bool:
        """检查是否需要自动重启"""
        # 检查状态文件更新时间
        if STATUS_FILE.exists():
            mtime = os.path.getmtime(STATUS_FILE)
            if time.time() - mtime > self.RESTART_TIMEOUT:
                return True
        return False
        
    def _restart_self(self):
        """自动重启"""
        self._log("🔄 自动重启执行器...", "WARN")
        self._save_status()
        
        # 使用exec重新启动
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    def record_status(self):
        """记录当前状态 (每7分钟)"""
        runtime = time.time() - self.start_time
        hours = int(runtime // 3600)
        minutes = int((runtime % 3600) // 60)
        
        content = f"""**自主进化运行中**
- 运行时长: {hours}小时{minutes}分钟
- 循环次数: {self.cycle_count}
- 错误次数: {self.error_count}
- 上次进化: {datetime.fromtimestamp(self.last_evolution_time).strftime('%H:%M:%S') if self.last_evolution_time else 'N/A'}
- 状态: 正常运行
"""
        
        self._append_to_daily_memory(content)
        self._log(f"📝 已记录状态 (运行{hours}h{minutes}m)")
        self.last_record_time = time.time()
        
    def run_single_cycle(self):
        """运行单次循环"""
        self.cycle_count += 1
        current_time = time.time()
        
        # 检查是否需要重启
        if self._should_restart():
            self._restart_self()
            
        # 1. 检查是否需要执行外循环
        if current_time - self.last_evolution_time > self.EVOLUTION_INTERVAL:
            self.run_evolution_loop()
            
        # 2. 检查是否需要发现GitHub项目
        if current_time - self.last_github_check > self.GITHUB_INTERVAL:
            self.discover_github_projects()
            self.last_github_check = current_time
            
        # 3. 检查是否需要记录状态 (每7分钟)
        if current_time - self.last_record_time > self.RECORD_INTERVAL:
            self.record_status()
            
        # 4. 保存状态
        self._save_status()
        
    def run(self):
        """主运行循环"""
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║           wdai 自主进化执行器 v2.0                          ║")
        print("║     全自动外循环 | GitHub学习 | 7分钟记录 | 自动重启       ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
        print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📝 记录间隔: 7分钟")
        print(f"🔄 进化间隔: 1小时")
        print(f"🔍 GitHub发现: 30分钟")
        print(f"🔄 自动重启: 10分钟无响应")
        print()
        print("💡 按 Ctrl+C 停止")
        print()
        
        self._log("🚀 自主进化执行器启动")
        
        while self.running:
            try:
                self.run_single_cycle()
                
                # 短暂休眠
                time.sleep(10)
                
            except KeyboardInterrupt:
                self._log("👋 用户中断")
                break
            except Exception as e:
                self._log(f"❌ 循环错误: {e}", "ERROR")
                self.error_count += 1
                time.sleep(30)  # 出错后等待30秒
                
        self._log("🏁 执行器停止")
        self._save_status()

def main():
    """主函数"""
    executor = AutonomousExecutor()
    executor.run()

if __name__ == '__main__':
    main()
