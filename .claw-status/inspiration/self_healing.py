#!/usr/bin/env python3
"""
灵感摄取系统 - 运行时自愈系统 (Self-Healing System)

处理运行时的各种技术问题:
- API失败/限流
- 网络超时
- 代码异常
- 数据损坏
- 依赖缺失

Author: wdai
Version: 1.0
"""

import json
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys

CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))


class ErrorType(Enum):
    """错误类型分类"""
    API_RATE_LIMIT = "api_rate_limit"      # API限流
    API_ERROR = "api_error"                 # API错误(4xx/5xx)
    NETWORK_TIMEOUT = "network_timeout"     # 网络超时
    NETWORK_ERROR = "network_error"         # 网络错误
    PARSE_ERROR = "parse_error"             # 解析错误
    DATA_CORRUPTION = "data_corruption"     # 数据损坏
    DEPENDENCY_MISSING = "dependency_missing"  # 依赖缺失
    CODE_EXCEPTION = "code_exception"       # 代码异常
    RESOURCE_EXHAUSTED = "resource_exhausted"  # 资源耗尽
    UNKNOWN = "unknown"                     # 未知错误


@dataclass
class ErrorRecord:
    """错误记录"""
    timestamp: str
    error_type: str
    source: str
    message: str
    stack_trace: Optional[str]
    recovery_attempted: bool = False
    recovery_success: bool = False
    recovery_method: str = ""


@dataclass
class CircuitBreaker:
    """熔断器状态"""
    source: str
    failure_count: int = 0
    last_failure: Optional[str] = None
    state: str = "closed"  # closed, open, half_open
    cooldown_until: Optional[str] = None


class SelfHealingSystem:
    """
    运行时自愈系统
    
    核心机制:
    1. 错误分类 - 识别错误类型
    2. 自动恢复 - 针对不同错误类型执行恢复策略
    3. 熔断保护 - 连续失败时暂停服务
    4. 优雅降级 - 主方案失败时使用fallback
    5. 日志追踪 - 记录所有错误和恢复尝试
    """
    
    # 熔断配置
    CIRCUIT_BREAKER_CONFIG = {
        'failure_threshold': 3,      # 3次失败触发熔断
        'cooldown_minutes': 30,      # 熔断后冷却30分钟
        'half_open_attempts': 1,     # 半开状态试1次
    }
    
    # 退避配置
    BACKOFF_CONFIG = {
        'base_delay': 1,             # 基础延迟1秒
        'max_delay': 300,            # 最大延迟5分钟
        'multiplier': 2,             # 指数退避乘数
    }
    
    def __init__(self, data_dir: str = "data/healing"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.errors_file = self.data_dir / "error_log.json"
        self.circuit_file = self.data_dir / "circuit_breakers.json"
        self.stats_file = self.data_dir / "healing_stats.json"
        
        self.error_history: List[ErrorRecord] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.healing_stats = {
            'total_errors': 0,
            'auto_recovered': 0,
            'manual_intervention': 0,
            'circuit_breaks': 0,
        }
        
        self._load_data()
    
    def _load_data(self):
        """加载历史数据"""
        if self.errors_file.exists():
            try:
                with open(self.errors_file, 'r') as f:
                    data = json.load(f)
                    self.error_history = [ErrorRecord(**r) for r in data]
            except:
                self.error_history = []
        
        if self.circuit_file.exists():
            try:
                with open(self.circuit_file, 'r') as f:
                    data = json.load(f)
                    self.circuit_breakers = {
                        k: CircuitBreaker(**v) for k, v in data.items()
                    }
            except:
                self.circuit_breakers = {}
        
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    self.healing_stats = json.load(f)
            except:
                pass
    
    def _save_data(self):
        """保存数据"""
        try:
            with open(self.errors_file, 'w') as f:
                json.dump([asdict(r) for r in self.error_history[-100:]], f, indent=2)
            
            with open(self.circuit_file, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.circuit_breakers.items()}, f, indent=2)
            
            with open(self.stats_file, 'w') as f:
                json.dump(self.healing_stats, f)
        except:
            pass
    
    def classify_error(self, exception: Exception) -> ErrorType:
        """分类错误类型"""
        error_str = str(exception).lower()
        exception_type = type(exception).__name__.lower()
        
        # API限流
        if any(kw in error_str for kw in ['rate limit', 'too many requests', '429']):
            return ErrorType.API_RATE_LIMIT
        
        # API错误
        if any(kw in error_str for kw in ['api error', 'bad request', '401', '403', '500', '502', '503']):
            return ErrorType.API_ERROR
        
        # 网络超时
        if any(kw in error_str for kw in ['timeout', 'timed out']):
            return ErrorType.NETWORK_TIMEOUT
        
        # 网络错误
        if any(kw in error_str for kw in ['connection', 'network', 'dns', 'unreachable']):
            return ErrorType.NETWORK_ERROR
        
        # 解析错误
        if any(kw in error_str for kw in ['parse', 'decode', 'json', 'xml', 'html']):
            return ErrorType.PARSE_ERROR
        
        # 依赖缺失
        if any(kw in error_str for kw in ['module not found', 'import error', 'no module']):
            return ErrorType.DEPENDENCY_MISSING
        
        # 资源耗尽
        if any(kw in error_str for kw in ['memory', 'disk', 'quota exceeded', 'resource']):
            return ErrorType.RESOURCE_EXHAUSTED
        
        return ErrorType.UNKNOWN
    
    def check_circuit_breaker(self, source: str) -> Tuple[bool, str]:
        """
        检查熔断器状态
        
        Returns:
            (can_proceed, reason)
        """
        if source not in self.circuit_breakers:
            return True, "熔断器未激活"
        
        cb = self.circuit_breakers[source]
        
        # 检查冷却时间
        if cb.cooldown_until:
            cooldown = datetime.fromisoformat(cb.cooldown_until)
            if datetime.now() < cooldown:
                remaining = (cooldown - datetime.now()).total_seconds() / 60
                return False, f"熔断器开启中，还需{remaining:.0f}分钟"
            else:
                # 冷却结束，转为半开状态
                cb.state = "half_open"
                cb.cooldown_until = None
        
        if cb.state == "open":
            return False, "熔断器开启，服务暂停"
        
        return True, f"熔断器状态: {cb.state}"
    
    def record_failure(self, source: str, error_type: ErrorType):
        """记录失败，更新熔断器"""
        if source not in self.circuit_breakers:
            self.circuit_breakers[source] = CircuitBreaker(source=source)
        
        cb = self.circuit_breakers[source]
        cb.failure_count += 1
        cb.last_failure = datetime.now().isoformat()
        
        # 检查是否触发熔断
        if cb.failure_count >= self.CIRCUIT_BREAKER_CONFIG['failure_threshold']:
            cb.state = "open"
            cooldown_minutes = self.CIRCUIT_BREAKER_CONFIG['cooldown_minutes']
            cb.cooldown_until = (datetime.now() + timedelta(minutes=cooldown_minutes)).isoformat()
            self.healing_stats['circuit_breaks'] += 1
            print(f"⚠️ 熔断器触发: {source} 已熔断，冷却{cooldown_minutes}分钟")
    
    def record_success(self, source: str):
        """记录成功，重置熔断器"""
        if source in self.circuit_breakers:
            cb = self.circuit_breakers[source]
            cb.failure_count = 0
            cb.state = "closed"
            cb.cooldown_until = None
    
    def get_backoff_delay(self, attempt: int) -> float:
        """计算退避延迟"""
        base = self.BACKOFF_CONFIG['base_delay']
        max_delay = self.BACKOFF_CONFIG['max_delay']
        multiplier = self.BACKOFF_CONFIG['multiplier']
        
        delay = base * (multiplier ** attempt)
        return min(delay, max_delay)
    
    def execute_with_healing(self, operation: Callable, 
                            source: str,
                            max_retries: int = 3,
                            fallback: Optional[Callable] = None) -> Any:
        """
        执行操作，自动处理错误
        
        Args:
            operation: 主操作函数
            source: 操作来源标识
            max_retries: 最大重试次数
            fallback: 失败时的fallback函数
            
        Returns:
            操作结果，或fallback结果，或None
        """
        # 1. 检查熔断器
        can_proceed, reason = self.check_circuit_breaker(source)
        if not can_proceed:
            print(f"⛔ {source}: {reason}")
            if fallback:
                print(f"   尝试fallback...")
                try:
                    return fallback()
                except Exception as e:
                    print(f"   fallback也失败: {e}")
            return None
        
        # 2. 执行主操作，带重试
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                result = operation()
                # 成功，重置熔断器
                self.record_success(source)
                if attempt > 0:
                    print(f"   ✅ {source} 第{attempt+1}次尝试成功")
                return result
                
            except Exception as e:
                last_exception = e
                error_type = self.classify_error(e)
                
                # 记录错误
                error_record = ErrorRecord(
                    timestamp=datetime.now().isoformat(),
                    error_type=error_type.value,
                    source=source,
                    message=str(e),
                    stack_trace=traceback.format_exc() if attempt == max_retries - 1 else None
                )
                self.error_history.append(error_record)
                self.healing_stats['total_errors'] += 1
                
                # 尝试自动恢复
                recovered = self._attempt_recovery(error_type, source, attempt)
                
                if recovered:
                    self.healing_stats['auto_recovered'] += 1
                    error_record.recovery_attempted = True
                    error_record.recovery_success = True
                    # 恢复成功，继续重试
                    continue
                else:
                    # 恢复失败，记录并可能重试
                    error_record.recovery_attempted = True
                    error_record.recovery_success = False
                    
                    if attempt < max_retries - 1:
                        delay = self.get_backoff_delay(attempt)
                        print(f"   ⚠️ {source} 尝试{attempt+1}/{max_retries}失败: {error_type.value}")
                        print(f"   等待{delay}秒后重试...")
                        time.sleep(delay)
        
        # 3. 所有重试都失败
        print(f"   ❌ {source} 所有{max_retries}次尝试均失败")
        self.record_failure(source, error_type)
        
        # 4. 尝试fallback
        if fallback:
            print(f"   尝试fallback...")
            try:
                result = fallback()
                error_record = self.error_history[-1]
                error_record.recovery_method = "fallback"
                return result
            except Exception as e:
                print(f"   fallback也失败: {e}")
        
        return None
    
    def _attempt_recovery(self, error_type: ErrorType, source: str, attempt: int) -> bool:
        """
        尝试自动恢复
        
        Returns:
            True if recovered, False otherwise
        """
        recovery_method = ""
        
        if error_type == ErrorType.API_RATE_LIMIT:
            # 限流：等待更长时间
            recovery_method = "rate_limit_wait"
            wait_time = min(60 * (2 ** attempt), 600)  # 最长等10分钟
            print(f"   遇到API限流，等待{wait_time}秒...")
            time.sleep(wait_time)
            return True
        
        elif error_type == ErrorType.NETWORK_TIMEOUT:
            # 超时：增加超时时间
            recovery_method = "increase_timeout"
            # 这个需要在operation中处理，这里只标记
            return False
        
        elif error_type == ErrorType.PARSE_ERROR:
            # 解析错误：尝试不同的解析器
            recovery_method = "switch_parser"
            # 标记需要切换解析器
            return False
        
        elif error_type == ErrorType.DEPENDENCY_MISSING:
            # 依赖缺失：尝试安装
            recovery_method = "install_dependency"
            # 自动安装太危险，需要人工介入
            self.healing_stats['manual_intervention'] += 1
            return False
        
        elif error_type == ErrorType.DATA_CORRUPTION:
            # 数据损坏：尝试从备份恢复
            recovery_method = "restore_from_backup"
            return self._restore_data(source)
        
        return False
    
    def _restore_data(self, source: str) -> bool:
        """从备份恢复数据"""
        backup_dir = self.data_dir / "backups"
        if not backup_dir.exists():
            return False
        
        # 查找最近的备份
        backups = sorted(backup_dir.glob(f"{source}_*.json"), reverse=True)
        if not backups:
            return False
        
        try:
            # 这里应该实现实际的数据恢复逻辑
            print(f"   尝试从备份恢复: {backups[0]}")
            return True
        except:
            return False
    
    def get_health_report(self) -> Dict:
        """获取系统健康报告"""
        # 统计最近24小时的错误
        now = datetime.now()
        recent_errors = [
            e for e in self.error_history
            if datetime.fromisoformat(e.timestamp) > now - timedelta(hours=24)
        ]
        
        error_by_type = {}
        for e in recent_errors:
            error_by_type[e.error_type] = error_by_type.get(e.error_type, 0) + 1
        
        return {
            'status': 'healthy' if len(recent_errors) < 10 else 'degraded',
            'recent_errors_24h': len(recent_errors),
            'error_by_type': error_by_type,
            'circuit_breakers': {
                k: {
                    'state': v.state,
                    'failure_count': v.failure_count
                }
                for k, v in self.circuit_breakers.items()
            },
            'healing_stats': self.healing_stats,
            'recommendation': self._generate_recommendation(recent_errors)
        }
    
    def _generate_recommendation(self, recent_errors: List[ErrorRecord]) -> str:
        """生成修复建议"""
        if not recent_errors:
            return "系统运行正常"
        
        error_types = [e.error_type for e in recent_errors]
        
        if 'api_rate_limit' in error_types:
            return "API调用过于频繁，建议降低请求频率或升级API套餐"
        
        if 'network_timeout' in error_types or 'network_error' in error_types:
            return "网络连接不稳定，建议检查网络配置或增加超时时间"
        
        if 'parse_error' in error_types:
            return "页面结构变化导致解析失败，需要更新解析器"
        
        if 'dependency_missing' in error_types:
            return "缺少必要依赖，请运行: pip install -r requirements.txt"
        
        return "建议查看详细错误日志，分析失败原因"


# 装饰器版本，更方便使用
def with_healing(max_retries: int = 3, fallback: Optional[Callable] = None):
    """自愈装饰器"""
    healing_system = SelfHealingSystem()
    
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            source = func.__name__
            operation = lambda: func(*args, **kwargs)
            return healing_system.execute_with_healing(
                operation, source, max_retries, fallback
            )
        return wrapper
    return decorator


# ============ 实际使用示例 ============

def example_usage():
    """使用示例"""
    healing = SelfHealingSystem()
    
    # 方式1: 使用上下文管理器风格
    def fetch_arxiv():
        # 模拟可能失败的API调用
        import random
        if random.random() < 0.7:  # 70%失败率
            raise Exception("rate limit exceeded")
        return ["paper1", "paper2"]
    
    def fallback_fetch():
        print("   使用本地缓存")
        return ["cached_paper1"]
    
    result = healing.execute_with_healing(
        operation=fetch_arxiv,
        source="arxiv_api",
        max_retries=3,
        fallback=fallback_fetch
    )
    
    print(f"结果: {result}")
    
    # 方式2: 使用装饰器
    @with_healing(max_retries=3)
    def fetch_github():
        return ["repo1", "repo2"]
    
    result2 = fetch_github()
    print(f"装饰器结果: {result2}")
    
    # 查看健康报告
    report = healing.get_health_report()
    print(f"\n健康报告: {json.dumps(report, indent=2)}")


if __name__ == "__main__":
    example_usage()
