#!/usr/bin/env python3
"""
Multi-Agent Research Service (MARS) v3.0
并行多Agent研究系统 - 常驻服务版本

架构:
┌─────────────────────────────────────────────────────────────┐
│                   Kimi Claw (主Agent)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 提交研究请求
                              ↓
┌─────────────────────────────────────────────────────────────┐
│        Multi-Agent Research Service (常驻) v3.0              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Conductor (统一协调器)                        │  │
│  │  - 冲突预测 + 智能调度 + 结果合并                      │  │
│  └──────────────────────────────────────────────────────┘  │
│         ↓                    ↓                    ↓        │
│  ┌──────────┐        ┌──────────┐         ┌──────────┐    │
│  │ Explorer │───────→│Investigator│──────→│  Critic  │    │
│  │  (1个)   │        │  (并行×N)  │         │(并行×M) │    │
│  └──────────┘        └──────────┘         └──────────┘    │
│         ↑                                          ↓       │
│         └────────────┐                    ┌─────────┘      │
│                      ↓                    ↓                │
│              ┌─────────────────┐    ┌──────────┐          │
│              │ ConflictCoordinator│← │Synthesist│          │
│              │   (冲突解决中心)    │   │  (1个)   │          │
│              └─────────────────┘    └──────────┘          │
└─────────────────────────────────────────────────────────────┘

通信机制:
- 请求: .mars/requests/REQ_*.json
- 响应: .mars/responses/RSP_*.json
- 状态: .mars/mars_status.json
"""

import os
import sys
import json
import time
import signal
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
from parallel_orchestrator import ParallelMultiAgentOrchestrator

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
MARS_DIR = WORKSPACE / ".mars"
REQUEST_DIR = MARS_DIR / "requests"
RESPONSE_DIR = MARS_DIR / "responses"
STATUS_FILE = MARS_DIR / "mars_status.json"
PID_FILE = MARS_DIR / "mars.pid"
RESEARCH_DIR = MARS_DIR / "research_history"

# 确保目录存在
for d in [MARS_DIR, REQUEST_DIR, RESPONSE_DIR, RESEARCH_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class ResearchTask:
    """研究任务"""
    id: str
    query: str
    priority: int  # 1-10
    max_parallel: int
    enable_conflict_resolution: bool
    submitted_at: str
    status: str = "pending"  # pending, processing, completed, failed
    result: Dict = field(default_factory=dict)
    completed_at: str = ""


@dataclass
class ServiceStatus:
    """服务状态"""
    pid: int
    start_time: str
    last_heartbeat: str
    total_requests: int
    pending_requests: int
    completed_requests: int
    failed_requests: int
    is_running: bool = True
    current_task: str = ""


class MultiAgentResearchService:
    """
    多Agent研究服务 v3.0
    常驻服务，支持实时研究请求
    """
    
    def __init__(self, max_parallel: int = 5):
        self.pid = os.getpid()
        self.max_parallel = max_parallel
        self.status = ServiceStatus(
            pid=self.pid,
            start_time=datetime.now().isoformat(),
            last_heartbeat=datetime.now().isoformat(),
            total_requests=0,
            pending_requests=0,
            completed_requests=0,
            failed_requests=0
        )
        self.running = False
        self.worker_thread = None
        self.heartbeat_thread = None
        self.auto_research_thread = None
        
        # 保存PID
        with open(PID_FILE, 'w') as f:
            f.write(str(self.pid))
    
    def start(self):
        """启动服务"""
        print(f"[{datetime.now().isoformat()}] Multi-Agent Research Service v3.0 启动")
        print(f"PID: {self.pid}")
        print(f"最大并行Agent数: {self.max_parallel}")
        print(f"请求目录: {REQUEST_DIR}")
        print(f"响应目录: {RESPONSE_DIR}")
        print("-" * 60)
        
        self.running = True
        
        # 启动工作线程
        self.worker_thread = threading.Thread(target=self._request_processor)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        # 启动自动研究线程
        self.auto_research_thread = threading.Thread(target=self._auto_research_loop)
        self.auto_research_thread.daemon = True
        self.auto_research_thread.start()
        
        # 主循环
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n收到停止信号...")
        finally:
            self.stop()
    
    def stop(self):
        """停止服务"""
        print(f"[{datetime.now().isoformat()}] 停止服务...")
        self.running = False
        self.status.is_running = False
        self._save_status()
        
        if PID_FILE.exists():
            PID_FILE.unlink()
        
        print("服务已停止")
    
    def _request_processor(self):
        """请求处理循环"""
        print("请求处理器启动")
        
        while self.running:
            try:
                requests = self._scan_requests()
                
                for req_file in requests:
                    self._process_request(req_file)
                
                time.sleep(2)
                
            except Exception as e:
                print(f"请求处理器错误: {e}")
                time.sleep(5)
    
    def _scan_requests(self) -> List[Path]:
        """扫描请求文件"""
        if not REQUEST_DIR.exists():
            return []
        
        requests = sorted(
            REQUEST_DIR.glob("REQ_*.json"),
            key=lambda p: p.stat().st_mtime
        )
        
        return requests
    
    def _process_request(self, req_file: Path):
        """处理单个请求"""
        try:
            with open(req_file, 'r') as f:
                request = json.load(f)
            
            req_id = request.get('id', 'unknown')
            query = request.get('query', '')
            
            self.status.current_task = req_id
            self.status.pending_requests += 1
            self._save_status()
            
            print(f"\n[{datetime.now().isoformat()}] 开始研究: {req_id}")
            print(f"  查询: {query[:80]}...")
            
            # 执行研究
            result = asyncio.run(self._execute_research(request))
            
            # 保存响应
            self._save_response(req_id, result)
            
            # 保存完整研究报告
            self._save_research_report(req_id, query, result)
            
            # 更新统计
            self.status.total_requests += 1
            self.status.pending_requests -= 1
            if result.get('success'):
                self.status.completed_requests += 1
                print(f"  ✓ 研究完成")
            else:
                self.status.failed_requests += 1
                print(f"  ✗ 研究失败: {result.get('error', 'Unknown')}")
            
            # 移动请求文件
            done_dir = REQUEST_DIR / "completed"
            done_dir.mkdir(exist_ok=True)
            req_file.rename(done_dir / req_file.name)
            
        except Exception as e:
            print(f"处理请求失败: {e}")
            self.status.failed_requests += 1
        finally:
            self.status.current_task = ""
            self._save_status()
    
    async def _execute_research(self, request: Dict) -> Dict:
        """执行研究"""
        try:
            query = request.get('query', '')
            max_parallel = request.get('max_parallel', self.max_parallel)
            enable_conflict = request.get('enable_conflict_resolution', True)
            
            # 创建编排器
            orchestrator = ParallelMultiAgentOrchestrator(
                max_parallel=max_parallel,
                enable_conflict_resolution=enable_conflict
            )
            
            # 执行研究
            result = await orchestrator.research(query, max_parallel=max_parallel)
            
            return {
                'success': True,
                'query': query,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'query': request.get('query', ''),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _save_response(self, req_id: str, result: Dict):
        """保存响应"""
        resp_file = RESPONSE_DIR / f"RSP_{req_id}.json"
        
        response = {
            'id': req_id,
            'timestamp': datetime.now().isoformat(),
            'result': result
        }
        
        with open(resp_file, 'w') as f:
            json.dump(response, f, indent=2)
    
    def _save_research_report(self, req_id: str, query: str, result: Dict):
        """保存研究报告"""
        report_file = RESEARCH_DIR / f"REPORT_{req_id}_{datetime.now().strftime('%Y%m%d')}.md"
        
        if not result.get('success'):
            content = f"""# 研究报告: {query}

**状态**: 失败  
**时间**: {datetime.now().isoformat()}  
**错误**: {result.get('error', 'Unknown')}
"""
        else:
            research_result = result.get('result', {})
            final_answer = research_result.get('final_answer', 'N/A')
            parallel_agents = research_result.get('performance', {}).get('parallel_agents_used', 0)
            duration = research_result.get('performance', {}).get('total_duration_seconds', 0)
            
            content = f"""# 研究报告: {query}

**状态**: 成功  
**时间**: {datetime.now().isoformat()}  
**并行Agent数**: {parallel_agents}  
**耗时**: {duration:.1f}秒

## 研究结论

{final_answer}

## 技术细节

- **冲突解决**: {'启用' if research_result.get('conflict_resolution_enabled') else '禁用'}
- **冲突检测**: {research_result.get('conflicts_detected', 0)} 个
- **冲突解决**: {research_result.get('conflicts_resolved', 0)} 个

## 来源

"""
            # 添加来源
            sources = research_result.get('merged_sources', [])
            for i, source in enumerate(sources[:10], 1):  # 最多10个来源
                content += f"{i}. [{source.get('title', 'Unknown')}]({source.get('url', '#')})\n"
        
        with open(report_file, 'w') as f:
            f.write(content)
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            self.status.last_heartbeat = datetime.now().isoformat()
            self._save_status()
            time.sleep(30)
    
    def _auto_research_loop(self):
        """自动研究循环"""
        print("自动研究器启动")
        
        while self.running:
            try:
                now = datetime.now()
                # 每天早上8点自动执行AI趋势研究
                if now.hour == 8 and now.minute == 0:
                    print(f"[{now.isoformat()}] 执行每日自动研究...")
                    
                    query = "Latest AI trends and breakthroughs 2026"
                    req_id = self._create_auto_request(query, priority=8)
                    
                    print(f"  已创建自动研究请求: {req_id}")
                    time.sleep(60)  # 避免重复触发
                
                time.sleep(30)
                
            except Exception as e:
                print(f"自动研究错误: {e}")
                time.sleep(60)
    
    def _create_auto_request(self, query: str, priority: int = 5) -> str:
        """创建自动研究请求"""
        req_id = f"AUTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        request = {
            'id': req_id,
            'type': 'research',
            'query': query,
            'priority': priority,
            'max_parallel': self.max_parallel,
            'enable_conflict_resolution': True,
            'submitted_at': datetime.now().isoformat(),
            'source': 'auto'
        }
        
        req_file = REQUEST_DIR / f"{req_id}.json"
        with open(req_file, 'w') as f:
            json.dump(request, f, indent=2)
        
        return req_id
    
    def _save_status(self):
        """保存状态"""
        with open(STATUS_FILE, 'w') as f:
            json.dump(asdict(self.status), f, indent=2)


# 便捷函数

def submit_research_request(query: str, priority: int = 5, max_parallel: int = 5) -> str:
    """
    提交研究请求
    
    Args:
        query: 研究查询
        priority: 优先级 1-10
        max_parallel: 最大并行Agent数
        
    Returns:
        请求ID
    """
    req_id = f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"
    
    request = {
        'id': req_id,
        'type': 'research',
        'query': query,
        'priority': priority,
        'max_parallel': max_parallel,
        'enable_conflict_resolution': True,
        'submitted_at': datetime.now().isoformat()
    }
    
    req_file = REQUEST_DIR / f"{req_id}.json"
    with open(req_file, 'w') as f:
        json.dump(request, f, indent=2)
    
    return req_id


def get_response(req_id: str, timeout: int = 300) -> Optional[Dict]:
    """
    获取响应
    
    Args:
        req_id: 请求ID
        timeout: 超时秒数（研究可能需要较长时间）
        
    Returns:
        响应结果或None
    """
    resp_file = RESPONSE_DIR / f"RSP_{req_id}.json"
    
    waited = 0
    while waited < timeout:
        if resp_file.exists():
            with open(resp_file, 'r') as f:
                return json.load(f)
        time.sleep(1)
        waited += 1
    
    return None


def get_service_status() -> Optional[Dict]:
    """获取服务状态"""
    if STATUS_FILE.exists():
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    return None


def is_service_running() -> bool:
    """检查服务是否运行"""
    if not PID_FILE.exists():
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def quick_research(query: str, timeout: int = 300) -> Dict:
    """
    便捷函数：快速研究
    
    一键提交研究请求并等待结果
    
    Args:
        query: 研究查询
        timeout: 超时秒数
        
    Returns:
        研究结果
    """
    print(f"提交研究请求: {query}")
    req_id = submit_research_request(query)
    print(f"请求ID: {req_id}")
    print("等待研究完成...")
    
    response = get_response(req_id, timeout=timeout)
    
    if response:
        result = response.get('result', {})
        if result.get('success'):
            print(f"✓ 研究完成")
            return result.get('result', {})
        else:
            print(f"✗ 研究失败: {result.get('error', 'Unknown')}")
            return result
    else:
        print("✗ 等待超时")
        return {'success': False, 'error': 'Timeout'}


# 主入口

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Agent Research Service v3.0")
    parser.add_argument("command", choices=["start", "stop", "status", "research"],
                       help="命令: start(启动), stop(停止), status(状态), research(研究)")
    parser.add_argument("--query", "-q", help="研究查询（用于research命令）")
    parser.add_argument("--max-parallel", "-p", type=int, default=5,
                       help="最大并行Agent数")
    
    args = parser.parse_args()
    
    if args.command == "start":
        if is_service_running():
            print("服务已在运行")
            sys.exit(1)
        
        service = MultiAgentResearchService(max_parallel=args.max_parallel)
        service.start()
    
    elif args.command == "stop":
        if not is_service_running():
            print("服务未运行")
            sys.exit(1)
        
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        os.kill(pid, signal.SIGTERM)
        print(f"已发送停止信号到进程 {pid}")
    
    elif args.command == "status":
        if is_service_running():
            status = get_service_status()
            if status:
                print("服务状态: 运行中")
                print(f"  PID: {status.get('pid')}")
                print(f"  启动时间: {status.get('start_time')}")
                print(f"  最后心跳: {status.get('last_heartbeat')}")
                print(f"  总请求数: {status.get('total_requests')}")
                print(f"  待处理: {status.get('pending_requests')}")
                print(f"  已完成: {status.get('completed_requests')}")
                print(f"  失败: {status.get('failed_requests')}")
                if status.get('current_task'):
                    print(f"  当前任务: {status.get('current_task')}")
            else:
                print("服务运行中，但无法读取状态")
        else:
            print("服务状态: 未运行")
    
    elif args.command == "research":
        if not args.query:
            print("请提供研究查询: --query '你的查询'")
            sys.exit(1)
        
        if not is_service_running():
            print("服务未运行，请先启动: python3 mars_service.py start")
            sys.exit(1)
        
        result = quick_research(args.query)
        print("\n" + "="*60)
        print("研究结果:")
        print("="*60)
        if result.get('success'):
            print(result.get('final_answer', 'N/A'))
        else:
            print(f"错误: {result.get('error', 'Unknown')}")
