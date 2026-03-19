#!/usr/bin/env python3
"""
创新能力自动化系统 (Innovation Automation System)

核心机制:
1. 方法失败自动检测
2. 备选方案自动尝试
3. 成功经验自动沉淀
4. 失败模式自动学习
"""

import json
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Tuple
from dataclasses import dataclass, asdict
from functools import wraps

WORKSPACE = Path("/root/.openclaw/workspace")
CLAW = WORKSPACE / ".claw-status"
INNOVATION_DB = CLAW / "innovation_patterns.jsonl"
METHOD_STATS = CLAW / "method_stats.json"


@dataclass
class MethodAttempt:
    """方法尝试记录"""
    method: str
    timestamp: str
    success: bool
    error: Optional[str] = None
    duration_ms: float = 0.0
    context: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InnovationPattern:
    """创新模式记录"""
    pattern_id: str
    trigger_method: str  # 触发条件
    trigger_error: str   # 触发错误类型
    fallback_methods: List[str]  # 备选方案列表
    success_rate: float
    created_at: str
    last_used: str
    use_count: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


class InnovationEngine:
    """创新引擎"""
    
    def __init__(self):
        self.method_stats: Dict[str, Dict] = self._load_method_stats()
        self.patterns: List[InnovationPattern] = self._load_patterns()
        self.current_context: Dict[str, Any] = {}
    
    def _load_method_stats(self) -> Dict:
        """加载方法统计"""
        if METHOD_STATS.exists():
            with open(METHOD_STATS) as f:
                return json.load(f)
        return {}
    
    def _load_patterns(self) -> List[InnovationPattern]:
        """加载创新模式"""
        patterns = []
        if INNOVATION_DB.exists():
            with open(INNOVATION_DB) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        patterns.append(InnovationPattern(**data))
                    except:
                        pass
        return patterns
    
    def record_attempt(self, method: str, success: bool, error: str = None, 
                      duration_ms: float = 0, context: Dict = None):
        """记录方法尝试"""
        attempt = MethodAttempt(
            method=method,
            timestamp=datetime.now().isoformat(),
            success=success,
            error=error,
            duration_ms=duration_ms,
            context=context or {}
        )
        
        # 更新统计
        if method not in self.method_stats:
            self.method_stats[method] = {
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "consecutive_failures": 0,
                "last_error": None
            }
        
        stats = self.method_stats[method]
        stats["attempts"] += 1
        
        if success:
            stats["successes"] += 1
            stats["consecutive_failures"] = 0
        else:
            stats["failures"] += 1
            stats["consecutive_failures"] += 1
            stats["last_error"] = error
        
        # 保存统计
        with open(METHOD_STATS, 'w') as f:
            json.dump(self.method_stats, f, indent=2)
        
        # 保存详细记录
        record_file = CLAW / "method_attempts.jsonl"
        with open(record_file, 'a') as f:
            f.write(json.dumps(attempt.to_dict()) + '\n')
    
    def should_innovate(self, method: str, threshold: int = 2) -> bool:
        """判断是否需要创新（方法失败次数超过阈值）"""
        stats = self.method_stats.get(method, {})
        return stats.get("consecutive_failures", 0) >= threshold
    
    def find_fallback_pattern(self, method: str, error: str) -> Optional[InnovationPattern]:
        """查找备选方案模式"""
        # 1. 先找精确匹配
        for pattern in self.patterns:
            if pattern.trigger_method == method and error in pattern.trigger_error:
                return pattern
        
        # 2. 找部分匹配
        for pattern in self.patterns:
            if pattern.trigger_method == method:
                return pattern
        
        return None
    
    def learn_pattern(self, trigger_method: str, trigger_error: str, 
                     fallback_methods: List[str], success: bool):
        """学习新的创新模式"""
        if not success:
            return
        
        pattern = InnovationPattern(
            pattern_id=f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            trigger_method=trigger_method,
            trigger_error=trigger_error,
            fallback_methods=fallback_methods,
            success_rate=1.0,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            use_count=1
        )
        
        self.patterns.append(pattern)
        
        # 保存到数据库
        with open(INNOVATION_DB, 'a') as f:
            f.write(json.dumps(pattern.to_dict()) + '\n')
    
    def execute_with_innovation(self, primary_method: str, 
                                execute_fn: Callable, 
                                fallback_fns: List[Callable],
                                context: Dict = None) -> Dict:
        """
        带自动创新的执行
        
        Args:
            primary_method: 主要方法标识
            execute_fn: 主执行函数
            fallback_fns: 备选执行函数列表
            context: 执行上下文
        """
        self.current_context = context or {}
        
        # 尝试1: 主方法
        print(f"[创新引擎] 尝试主方法: {primary_method}")
        start = time.time()
        
        try:
            result = execute_fn()
            duration = (time.time() - start) * 1000
            
            if self._is_success(result):
                self.record_attempt(primary_method, True, duration_ms=duration, 
                                  context=context)
                return {
                    "success": True,
                    "method": primary_method,
                    "result": result,
                    "attempts": 1,
                    "duration_ms": duration
                }
            else:
                error = self._extract_error(result)
                self.record_attempt(primary_method, False, error, duration, context)
        except Exception as e:
            duration = (time.time() - start) * 1000
            error = str(e)
            self.record_attempt(primary_method, False, error, duration, context)
        
        # 尝试2: 自动换路（备选方案）
        print(f"[创新引擎] 主方法失败，自动尝试备选方案...")
        
        for i, fallback_fn in enumerate(fallback_fns, 2):
            fallback_name = f"{primary_method}_fallback_{i-1}"
            print(f"[创新引擎] 尝试备选方案 {i-1}/{len(fallback_fns)}")
            
            start = time.time()
            try:
                result = fallback_fn()
                duration = (time.time() - start) * 1000
                
                if self._is_success(result):
                    self.record_attempt(fallback_name, True, duration_ms=duration,
                                      context=context)
                    
                    # 学习这个模式
                    self.learn_pattern(
                        trigger_method=primary_method,
                        trigger_error=error,
                        fallback_methods=[fallback_name],
                        success=True
                    )
                    
                    return {
                        "success": True,
                        "method": fallback_name,
                        "result": result,
                        "attempts": i,
                        "duration_ms": duration,
                        "note": f"自动换路: {primary_method} → {fallback_name}"
                    }
                else:
                    err = self._extract_error(result)
                    self.record_attempt(fallback_name, False, err, duration, context)
            except Exception as e:
                duration = (time.time() - start) * 1000
                self.record_attempt(fallback_name, False, str(e), duration, context)
        
        # 所有方法都失败
        return {
            "success": False,
            "method": primary_method,
            "error": "所有方法都失败",
            "attempts": len(fallback_fns) + 1,
            "message": "需要人工介入或新的备选方案"
        }
    
    def _is_success(self, result: Any) -> bool:
        """判断结果是否成功"""
        if isinstance(result, dict):
            return result.get("success", False) or result.get("status") == "success"
        if isinstance(result, bool):
            return result
        return result is not None
    
    def _extract_error(self, result: Any) -> str:
        """提取错误信息"""
        if isinstance(result, dict):
            return result.get("error", str(result))
        return str(result)
    
    def generate_report(self) -> str:
        """生成创新报告"""
        report = f"""# 创新能力自动化报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 方法统计

| 方法 | 尝试次数 | 成功 | 失败 | 连续失败 | 状态 |
|------|---------|------|------|---------|------|
"""
        
        for method, stats in self.method_stats.items():
            status = "🟢" if stats["consecutive_failures"] == 0 else "🟡" if stats["consecutive_failures"] < 3 else "🔴"
            report += f"| {method} | {stats['attempts']} | {stats['successes']} | {stats['failures']} | {stats['consecutive_failures']} | {status} |\n"
        
        report += f"""
## 创新模式 ({len(self.patterns)} 个)

"""
        for pattern in self.patterns[-5:]:  # 最近5个
            report += f"""### {pattern.pattern_id}
- **触发方法**: {pattern.trigger_method}
- **触发错误**: {pattern.trigger_error}
- **备选方案**: {', '.join(pattern.fallback_methods)}
- **成功率**: {pattern.success_rate:.0%}
- **使用次数**: {pattern.use_count}

"""
        
        return report


# ===== 自动创新装饰器 =====

def auto_innovate(fallback_methods: List[str] = None):
    """自动创新装饰器
    
    用法:
    @auto_innovate(fallback_methods=["method_ssh", "method_api"])
    def my_function():
        return method_https()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            engine = InnovationEngine()
            
            def primary():
                return func(*args, **kwargs)
            
            # 从字符串加载备选函数
            fallbacks = []
            if fallback_methods:
                for method_name in fallback_methods:
                    # 这里简化处理，实际需要动态加载
                    fallbacks.append(lambda: {"success": False, "error": "fallback not implemented"})
            
            return engine.execute_with_innovation(
                primary_method=func.__name__,
                execute_fn=primary,
                fallback_fns=fallbacks
            )
        
        return wrapper
    return decorator


# ===== 具体任务执行器（带自动创新） =====

class GitPusher:
    """Git推送器（带自动换路）"""
    
    def __init__(self):
        self.engine = InnovationEngine()
    
    def push_https(self) -> Dict:
        """HTTPS推送"""
        result = subprocess.run(
            ["git", "push", "https://github.com/mingking00/wdai.git", "master"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        else:
            return {"success": False, "error": result.stderr}
    
    def push_ssh(self) -> Dict:
        """SSH推送"""
        # 先切换remote
        subprocess.run(
            ["git", "remote", "set-url", "origin", 
             "git@github.com:mingking00/wdai.git"],
            check=True
        )
        
        result = subprocess.run(
            ["git", "push", "origin", "master"],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        else:
            return {"success": False, "error": result.stderr}
    
    def push(self) -> Dict:
        """智能推送（自动换路）"""
        return self.engine.execute_with_innovation(
            primary_method="git_push_https",
            execute_fn=self.push_https,
            fallback_fns=[self.push_ssh],
            context={"repo": "mingking00/wdai", "branch": "master"}
        )


def main():
    """演示"""
    engine = InnovationEngine()
    
    print("=" * 60)
    print("创新能力自动化系统")
    print("=" * 60)
    
    # 示例：Git推送
    print("\n📤 演示：Git智能推送")
    pusher = GitPusher()
    result = pusher.push()
    
    print(f"\n结果: {result}")
    
    # 生成报告
    print("\n" + "=" * 60)
    print("创新报告")
    print("=" * 60)
    report = engine.generate_report()
    print(report)


if __name__ == "__main__":
    main()
