#!/usr/bin/env python3
"""
System Evolution Agent Service (SEAS)
常驻服务版本

运行方式:
- 独立进程长期运行
- 监听请求文件队列
- 定时自动分析系统
- 支持实时触发

通信机制:
- 请求文件: .system/requests/REQ_*.json
- 响应文件: .system/responses/RSP_*.json
- 状态文件: .system/seas_status.json
"""

import os
import sys
import json
import time
import signal
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
from sea import SystemEvolutionAgent, ChangeRequest

# 导入SEA-IER系统
try:
    from sea_ier import get_sea_experience_manager, SEAExperienceManager
    IER_AVAILABLE = True
except ImportError:
    IER_AVAILABLE = False
    print("[WARNING] SEA-IER系统不可用")

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
SYSTEM_DIR = WORKSPACE / ".system"
REQUEST_DIR = SYSTEM_DIR / "requests"
RESPONSE_DIR = SYSTEM_DIR / "responses"
STATUS_FILE = SYSTEM_DIR / "seas_status.json"
PID_FILE = SYSTEM_DIR / "seas.pid"

# 确保目录存在
for d in [SYSTEM_DIR, REQUEST_DIR, RESPONSE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


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


class SystemEvolutionAgentService:
    """
    System Evolution Agent 常驻服务 - 集成IER经验精炼
    """
    
    def __init__(self):
        self.pid = os.getpid()
        self.sea = SystemEvolutionAgent()
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
        self.auto_analysis_thread = None
        
        # 初始化IER系统
        self.exp_manager = None
        if IER_AVAILABLE:
            try:
                self.exp_manager = get_sea_experience_manager()
                print("[SEA-IER] 经验精炼系统已加载")
            except Exception as e:
                print(f"[SEA-IER] 初始化失败: {e}")
        
        # 保存PID
        with open(PID_FILE, 'w') as f:
            f.write(str(self.pid))
    
    def start(self):
        """启动服务"""
        print(f"[{datetime.now().isoformat()}] System Evolution Agent Service 启动")
        print(f"PID: {self.pid}")
        print(f"请求目录: {REQUEST_DIR}")
        print(f"响应目录: {RESPONSE_DIR}")
        if self.exp_manager:
            print(f"[SEA-IER] 当前经验数: {len(self.exp_manager.experiences)}")
        print("-" * 60)
        
        self.running = True
        
        # 启动时运行经验淘汰
        if self.exp_manager:
            self._run_experience_maintenance()
        
        # 启动工作线程
        self.worker_thread = threading.Thread(target=self._request_processor)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        # 启动自动分析线程
        self.auto_analysis_thread = threading.Thread(target=self._auto_analysis_loop)
        self.auto_analysis_thread.daemon = True
        self.auto_analysis_thread.start()
        
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
        
        # 清理PID文件
        if PID_FILE.exists():
            PID_FILE.unlink()
        
        print("服务已停止")
    
    def _run_experience_maintenance(self):
        """运行经验维护（淘汰过时经验）"""
        try:
            print("[SEA-IER] 运行经验维护...")
            eliminated = self.exp_manager.evaluate_and_eliminate()
            if eliminated:
                print(f"[SEA-IER] 淘汰了 {len(eliminated)} 条经验")
            stats = self.exp_manager.get_statistics()
            print(f"[SEA-IER] 当前状态: {stats['active_experiences']}/{stats['total_experiences']} 活跃经验")
        except Exception as e:
            print(f"[SEA-IER] 经验维护失败: {e}")
    
    def _request_processor(self):
        """请求处理循环"""
        print("请求处理器启动")
        
        while self.running:
            try:
                # 扫描请求文件
                requests = self._scan_requests()
                
                for req_file in requests:
                    self._process_request(req_file)
                
                time.sleep(2)  # 每2秒检查一次
                
            except Exception as e:
                print(f"请求处理器错误: {e}")
                time.sleep(5)
    
    def _scan_requests(self) -> List[Path]:
        """扫描请求文件"""
        if not REQUEST_DIR.exists():
            return []
        
        # 获取所有待处理的请求文件（按时间排序）
        requests = sorted(
            REQUEST_DIR.glob("REQ_*.json"),
            key=lambda p: p.stat().st_mtime
        )
        
        return requests
    
    def _process_request(self, req_file: Path):
        """处理单个请求 - 集成IER经验精炼"""
        try:
            # 读取请求
            with open(req_file, 'r') as f:
                request = json.load(f)
            
            req_id = request.get('id', 'unknown')
            req_type = request.get('type', 'unknown')
            description = request.get('description', '')
            target_files = request.get('changes', {}).get('files', [])
            
            self.status.current_task = req_id
            self.status.pending_requests += 1
            self._save_status()
            
            print(f"[{datetime.now().isoformat()}] 处理请求: {req_id}")
            print(f"  类型: {req_type}")
            print(f"  描述: {description}")
            
            # IER: 记录任务开始
            if self.exp_manager and req_type == 'improve':
                self.exp_manager.record_task_start(
                    req_id, description, target_files, 'improve'
                )
                
                # IER: 检索相关经验
                relevant_exps = self.exp_manager.retrieve_relevant_experiences(
                    description, 
                    target_files[0] if target_files else "",
                    req_type
                )
                if relevant_exps:
                    print(f"  [SEA-IER] 找到 {len(relevant_exps)} 条相关经验")
                    request['_ier_experiences'] = relevant_exps
            
            # 执行请求
            result = self._execute_request(request)
            
            # IER: 提取新经验（如果是改进请求且有代码变更）
            if self.exp_manager and req_type == 'improve' and result.get('success'):
                try:
                    # 获取代码diff（假设在result中有）
                    diff = result.get('diff', '')
                    target_file = target_files[0] if target_files else ''
                    
                    if diff:
                        new_exps = self.exp_manager.acquire_from_change(
                            req_id, description, diff, target_file, True
                        )
                        if new_exps:
                            print(f"  [SEA-IER] 提取了 {len(new_exps)} 条新经验")
                            result['experiences_generated'] = [exp.id for exp in new_exps]
                except Exception as e:
                    print(f"  [SEA-IER] 经验提取失败: {e}")
            
            # IER: 记录任务完成
            if self.exp_manager and req_type == 'improve':
                self.exp_manager.record_task_complete(
                    req_id,
                    result.get('success', False),
                    result.get('rollback_needed', False),
                    result.get('error')
                )
            
            # 保存响应
            self._save_response(req_id, result)
            
            # 更新统计
            self.status.total_requests += 1
            self.status.pending_requests -= 1
            if result.get('success'):
                self.status.completed_requests += 1
                print(f"  ✓ 完成")
            else:
                self.status.failed_requests += 1
                print(f"  ✗ 失败: {result.get('message', 'Unknown error')}")
            
            # 移动请求文件到已完成
            done_dir = REQUEST_DIR / "completed"
            done_dir.mkdir(exist_ok=True)
            req_file.rename(done_dir / req_file.name)
            
        except Exception as e:
            print(f"处理请求失败: {e}")
            self.status.failed_requests += 1
        finally:
            self.status.current_task = ""
            self._save_status()
    
    def _execute_request(self, request: Dict) -> Dict:
        """执行请求 - 支持IER经验注入"""
        req_type = request.get('type')
        
        if req_type == 'improve':
            # 系统改进请求
            # 如果有IER经验，格式化后传递给改进方法
            experiences = request.get('_ier_experiences', [])
            exp_prompt = ""
            if self.exp_manager and experiences:
                exp_prompt = self.exp_manager.format_experiences_for_prompt(experiences)
            
            return self.sea.improve_self(
                description=request.get('description', '') + exp_prompt,
                changes=request.get('changes', {})
            )
        
        elif req_type == 'analyze':
            # 系统分析请求
            return {
                'success': True,
                'type': 'analysis',
                'result': self.sea.analyze_system()
            }
        
        elif req_type == 'status':
            # 状态查询
            response = {
                'success': True,
                'type': 'status',
                'service_status': asdict(self.status),
                'change_history': self.sea.get_change_history()
            }
            
            # 添加IER统计
            if self.exp_manager:
                response['ier_statistics'] = self.exp_manager.get_statistics()
            
            return response
        
        elif req_type == 'rollback':
            # 回滚请求
            backup_id = request.get('backup_id', '')
            if backup_id:
                success = self.sea._rollback(backup_id)
                return {
                    'success': success,
                    'type': 'rollback',
                    'backup_id': backup_id
                }
            else:
                return {
                    'success': False,
                    'type': 'rollback',
                    'message': 'Missing backup_id'
                }
        
        elif req_type == 'ier_stats':
            # IER统计查询
            if self.exp_manager:
                return {
                    'success': True,
                    'type': 'ier_stats',
                    'statistics': self.exp_manager.get_statistics()
                }
            else:
                return {
                    'success': False,
                    'type': 'ier_stats',
                    'message': 'IER system not available'
                }
        
        elif req_type == 'ier_list':
            # IER经验列表
            if self.exp_manager:
                exp_type = request.get('exp_type')
                exps = self.exp_manager.list_experiences(exp_type)
                return {
                    'success': True,
                    'type': 'ier_list',
                    'experiences': exps
                }
            else:
                return {
                    'success': False,
                    'type': 'ier_list',
                    'message': 'IER system not available'
                }
        
        elif req_type == 'ier_maintain':
            # IER经验维护
            if self.exp_manager:
                eliminated = self.exp_manager.evaluate_and_eliminate()
                stats = self.exp_manager.get_statistics()
                return {
                    'success': True,
                    'type': 'ier_maintain',
                    'eliminated_count': len(eliminated),
                    'eliminated_ids': eliminated,
                    'statistics': stats
                }
            else:
                return {
                    'success': False,
                    'type': 'ier_maintain',
                    'message': 'IER system not available'
                }
        
        else:
            return {
                'success': False,
                'message': f'Unknown request type: {req_type}'
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
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            self.status.last_heartbeat = datetime.now().isoformat()
            self._save_status()
            time.sleep(30)  # 每30秒更新一次
    
    def _auto_analysis_loop(self):
        """自动分析循环"""
        print("自动分析器启动")
        
        while self.running:
            try:
                # 每天凌晨4点执行自动分析
                now = datetime.now()
                if now.hour == 4 and now.minute == 0:
                    print(f"[{now.isoformat()}] 执行每日自动分析...")
                    
                    analysis = self.sea.analyze_system()
                    
                    # 如果有重要发现，创建改进建议
                    if analysis.get('findings') or analysis.get('suggestions'):
                        suggestion_file = SYSTEM_DIR / f"auto_suggestion_{now.strftime('%Y%m%d')}.json"
                        with open(suggestion_file, 'w') as f:
                            json.dump(analysis, f, indent=2)
                        
                        print(f"  发现 {len(analysis.get('findings', []))} 个问题")
                        print(f"  生成 {len(analysis.get('suggestions', []))} 条建议")
                        print(f"  建议已保存到: {suggestion_file}")
                    
                    # 等待到下一分钟，避免重复执行
                    time.sleep(60)
                
                time.sleep(30)  # 每30秒检查一次时间
                
            except Exception as e:
                print(f"自动分析错误: {e}")
                time.sleep(60)
    
    def _save_status(self):
        """保存状态"""
        with open(STATUS_FILE, 'w') as f:
            json.dump(asdict(self.status), f, indent=2)


# 便捷函数（供其他Agent调用）

def submit_improvement_request(description: str, changes: Dict[str, str]) -> str:
    """
    提交改进请求
    
    Returns:
        请求ID
    """
    req_id = f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"
    
    request = {
        'id': req_id,
        'type': 'improve',
        'description': description,
        'changes': changes,
        'submitted_at': datetime.now().isoformat()
    }
    
    req_file = REQUEST_DIR / f"{req_id}.json"
    with open(req_file, 'w') as f:
        json.dump(request, f, indent=2)
    
    return req_id


def submit_analysis_request() -> str:
    """提交分析请求"""
    req_id = f"REQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"
    
    request = {
        'id': req_id,
        'type': 'analyze',
        'submitted_at': datetime.now().isoformat()
    }
    
    req_file = REQUEST_DIR / f"{req_id}.json"
    with open(req_file, 'w') as f:
        json.dump(request, f, indent=2)
    
    return req_id


def get_response(req_id: str, timeout: int = 60) -> Optional[Dict]:
    """
    获取响应
    
    Args:
        req_id: 请求ID
        timeout: 超时秒数
        
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
        
        # 检查进程是否存在
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


# 主入口

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="System Evolution Agent Service")
    parser.add_argument("command", choices=["start", "stop", "status"], 
                       help="命令: start(启动), stop(停止), status(状态)")
    
    args = parser.parse_args()
    
    if args.command == "start":
        if is_service_running():
            print("服务已在运行")
            sys.exit(1)
        
        service = SystemEvolutionAgentService()
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
