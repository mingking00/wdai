#!/usr/bin/env python3
"""
WDai 闭环自优化系统 v2

完整闭环：感知 → 分析 → 决策 → 执行 → 验证 → 学习
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Callable

WORKSPACE = Path("/root/.openclaw/workspace")
CLAW = WORKSPACE / ".claw-status"
EVO = WORKSPACE / ".evolution"
SCHEDULER = WORKSPACE / ".scheduler"

class ClosedLoopOptimizer:
    """闭环自优化器"""
    
    def __init__(self):
        self.metrics_db = []
        self.execution_db = []
        self.feedback_db = []
        self.optimizations_applied = []
        
    # ============ 1. 感知层 ============
    
    def collect_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        import psutil
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
            "active_tasks": len(list(SCHEDULER.glob("*.json"))) if SCHEDULER.exists() else 0,
        }
        
        # 保存到数据库
        metrics_file = CLAW / "metrics_db.jsonl"
        with open(metrics_file, "a") as f:
            f.write(json.dumps(metrics) + "\n")
        
        return metrics
    
    def collect_execution_results(self) -> List[Dict]:
        """收集执行结果"""
        results_file = EVO / "execution_results.json"
        if results_file.exists():
            with open(results_file) as f:
                return json.load(f)
        return []
    
    def collect_user_feedback(self) -> List[Dict]:
        """收集用户反馈（从记忆文件）"""
        feedback = []
        
        # 从daily记录中提取反馈
        memory_dir = WORKSPACE / "memory" / "daily"
        if memory_dir.exists():
            for f in sorted(memory_dir.glob("*.md"))[-7:]:  # 最近7天
                content = f.read_text()
                # 简单提取成功/失败标记
                if "✅" in content or "完成" in content:
                    feedback.append({
                        "date": f.stem,
                        "type": "success",
                        "source": str(f)
                    })
                elif "❌" in content or "失败" in content:
                    feedback.append({
                        "date": f.stem, 
                        "type": "failure",
                        "source": str(f)
                    })
        
        return feedback
    
    # ============ 2. 分析层 ============
    
    def analyze_bottlenecks(self) -> List[Dict]:
        """分析瓶颈"""
        bottlenecks = []
        
        # 分析执行结果
        results = self.collect_execution_results()
        if not results:
            return bottlenecks
        
        # 按维度统计
        by_dimension = defaultdict(lambda: {"success": 0, "fail": 0, "errors": []})
        for r in results:
            dim = r.get("dimension", "unknown")
            if r.get("success"):
                by_dimension[dim]["success"] += 1
            else:
                by_dimension[dim]["fail"] += 1
                by_dimension[dim]["errors"].append(r.get("message", ""))
        
        # 识别瓶颈
        for dim, stats in by_dimension.items():
            total = stats["success"] + stats["fail"]
            if total > 0:
                fail_rate = stats["fail"] / total
                if fail_rate > 0.3:  # 失败率超过30%
                    # 分析错误类型
                    error_types = Counter()
                    for err in stats["errors"]:
                        if "syntax" in err.lower():
                            error_types["syntax"] += 1
                        elif "timeout" in err.lower():
                            error_types["timeout"] += 1
                        elif "file" in err.lower():
                            error_types["file"] += 1
                        else:
                            error_types["other"] += 1
                    
                    top_error = error_types.most_common(1)[0] if error_types else ("unknown", 0)
                    
                    bottlenecks.append({
                        "type": "high_failure_rate",
                        "dimension": dim,
                        "fail_rate": fail_rate,
                        "total_executions": total,
                        "primary_error": top_error[0],
                        "error_count": top_error[1],
                        "severity": "critical" if fail_rate > 0.7 else "high" if fail_rate > 0.5 else "medium"
                    })
        
        return bottlenecks
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """分析性能趋势"""
        metrics_file = CLAW / "metrics_db.jsonl"
        if not metrics_file.exists():
            return {}
        
        metrics = []
        with open(metrics_file) as f:
            for line in f:
                try:
                    metrics.append(json.loads(line))
                except:
                    pass
        
        if len(metrics) < 2:
            return {"insufficient_data": True}
        
        # 计算趋势
        recent = metrics[-10:]
        older = metrics[:10] if len(metrics) >= 20 else metrics[:len(metrics)//2]
        
        trends = {}
        
        # 响应时间趋势
        recent_response = sum(m.get("response_time_ms", 0) for m in recent) / len(recent)
        older_response = sum(m.get("response_time_ms", 0) for m in older) / len(older)
        trends["response_time"] = {
            "recent_avg": recent_response,
            "older_avg": older_response,
            "trend": "improving" if recent_response < older_response * 0.9 else "degrading" if recent_response > older_response * 1.1 else "stable"
        }
        
        return trends
    
    # ============ 3. 决策层 ============
    
    def generate_actionable_fixes(self, bottlenecks: List[Dict]) -> List[Dict]:
        """生成可执行的修复方案"""
        fixes = []
        
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "high_failure_rate":
                if bottleneck["primary_error"] == "syntax":
                    fixes.append({
                        "id": f"fix_syntax_{bottleneck['dimension']}",
                        "target": bottleneck["dimension"],
                        "problem": f"{bottleneck['fail_rate']:.0%}失败率，主要是语法错误",
                        "solution": "添加代码生成后的语法验证",
                        "implementation": self._create_syntax_validator,
                        "validation": self._test_syntax_validator,
                        "expected_improvement": 0.5,  # 预期减少50%错误
                        "auto_apply": True
                    })
                
                elif bottleneck["primary_error"] == "timeout":
                    fixes.append({
                        "id": f"fix_timeout_{bottleneck['dimension']}",
                        "target": bottleneck["dimension"],
                        "problem": f"{bottleneck['fail_rate']:.0%}失败率，主要是超时",
                        "solution": "添加执行超时控制和分阶段检查点",
                        "implementation": self._create_timeout_handler,
                        "validation": self._test_timeout_handler,
                        "expected_improvement": 0.3,
                        "auto_apply": True
                    })
                
                else:
                    fixes.append({
                        "id": f"fix_generic_{bottleneck['dimension']}",
                        "target": bottleneck["dimension"],
                        "problem": f"{bottleneck['fail_rate']:.0%}失败率",
                        "solution": "添加错误重试和日志记录",
                        "implementation": self._create_retry_handler,
                        "validation": self._test_retry_handler,
                        "expected_improvement": 0.2,
                        "auto_apply": True
                    })
        
        return fixes
    
    # ============ 4. 执行层 ============
    
    def _create_syntax_validator(self) -> Path:
        """创建语法验证器"""
        code = '''"""自动生成的语法验证模块"""
import ast
from typing import Dict, Any

def validate_python_code(code: str) -> Dict[str, Any]:
    """验证Python代码语法"""
    try:
        tree = ast.parse(code)
        return {
            "valid": True,
            "ast": tree,
            "error": None,
            "line_count": len(code.splitlines())
        }
    except SyntaxError as e:
        return {
            "valid": False,
            "ast": None,
            "error": f"SyntaxError at line {e.lineno}: {e.msg}",
            "line_count": 0
        }
    except Exception as e:
        return {
            "valid": False,
            "ast": None, 
            "error": f"Unexpected error: {e}",
            "line_count": 0
        }

def fix_common_syntax_errors(code: str) -> str:
    """尝试修复常见语法错误"""
    # 修复未闭合的字符串
    lines = code.splitlines()
    fixed = []
    
    for line in lines:
        # 简单的引号匹配检查
        single_quotes = line.count("'") - line.count("\\'")
        double_quotes = line.count('"') - line.count('\\"')
        
        if single_quotes % 2 == 1 and double_quotes % 2 == 0:
            line = line + "'"
        elif double_quotes % 2 == 1 and single_quotes % 2 == 0:
            line = line + '"'
        
        fixed.append(line)
    
    return "\\n".join(fixed)
'''
        
        validator_file = CLAW / "auto_syntax_validator.py"
        validator_file.write_text(code)
        return validator_file
    
    def _create_timeout_handler(self) -> Path:
        """创建超时处理器"""
        code = '''"""自动生成的超时处理模块"""
import signal
import time
from typing import Callable, Any, Optional
from functools import wraps

class TimeoutError(Exception):
    pass

def with_timeout(seconds: float):
    """装饰器：为函数添加超时控制"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise TimeoutError(f"Function execution exceeded {seconds} seconds")
            
            # 设置信号处理器
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 取消闹钟
                return {"success": True, "result": result, "execution_time": time.time()}
            except TimeoutError as e:
                return {"success": False, "error": str(e), "timeout": True}
            except Exception as e:
                return {"success": False, "error": str(e), "timeout": False}
            finally:
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator

def with_progress_checkpoints(func: Callable, checkpoint_interval: float = 60) -> Callable:
    """添加进度检查点"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        last_checkpoint = start_time
        
        def checkpoint():
            nonlocal last_checkpoint
            elapsed = time.time() - start_time
            since_last = time.time() - last_checkpoint
            
            if since_last > checkpoint_interval:
                last_checkpoint = time.time()
                return {
                    "elapsed": elapsed,
                    "status": "running",
                    "last_checkpoint": last_checkpoint
                }
            return None
        
        # 将checkpoint函数注入kwargs
        kwargs['_checkpoint'] = checkpoint
        return func(*args, **kwargs)
    
    return wrapper
'''
        
        timeout_file = CLAW / "auto_timeout_handler.py"
        timeout_file.write_text(code)
        return timeout_file
    
    def _create_retry_handler(self) -> Path:
        """创建重试处理器"""
        code = '''"""自动生成的重试处理模块"""
import time
import random
from typing import Callable, Any, Dict, Optional
from functools import wraps

def with_retry(max_retries: int = 3, backoff: bool = True):
    """装饰器：为函数添加重试机制"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    return {
                        "success": True,
                        "result": result,
                        "attempts": attempt + 1
                    }
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        if backoff:
                            # 指数退避
                            sleep_time = (2 ** attempt) + random.uniform(0, 1)
                            time.sleep(sleep_time)
            
            return {
                "success": False,
                "error": str(last_exception),
                "attempts": max_retries
            }
        
        return wrapper
    return decorator

def with_fallback(fallback_value: Any):
    """装饰器：失败时返回默认值"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                return fallback_value
        return wrapper
    return decorator
'''
        
        retry_file = CLAW / "auto_retry_handler.py"
        retry_file.write_text(code)
        return retry_file
    
    # ============ 5. 验证层 ============
    
    def _test_syntax_validator(self, file_path: Path) -> bool:
        """测试语法验证器"""
        try:
            # 尝试导入和测试
            import importlib.util
            spec = importlib.util.spec_from_file_location("validator", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 测试验证功能
            result = module.validate_python_code("x = 1 + 2")
            assert result["valid"] == True
            
            result = module.validate_python_code("x = 1 + ")
            assert result["valid"] == False
            
            return True
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            return False
    
    def _test_timeout_handler(self, file_path: Path) -> bool:
        """测试超时处理器"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("timeout", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 测试超时功能
            @module.with_timeout(0.1)
            def slow_function():
                time.sleep(1)
                return "done"
            
            result = slow_function()
            assert result["success"] == False
            assert result["timeout"] == True
            
            return True
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            return False
    
    def _test_retry_handler(self, file_path: Path) -> bool:
        """测试重试处理器"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("retry", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 测试重试功能
            call_count = 0
            
            @module.with_retry(max_retries=2, backoff=False)
            def failing_function():
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise ValueError("fail")
                return "success"
            
            result = failing_function()
            assert result["success"] == True
            assert result["attempts"] == 2
            
            return True
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            return False
    
    # ============ 主流程 ============
    
    def run_optimization_cycle(self) -> Dict[str, Any]:
        """运行完整的优化周期"""
        print("\n" + "=" * 60)
        print("🔄 WDai 闭环自优化系统 v2")
        print("=" * 60)
        
        results = {
            "cycle_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "phases": {}
        }
        
        # Phase 1: 感知
        print("\n📡 Phase 1: 感知 - 收集系统数据...")
        metrics = self.collect_metrics()
        executions = self.collect_execution_results()
        feedback = self.collect_user_feedback()
        
        print(f"   ✓ 系统指标: CPU {metrics['cpu_percent']:.1f}%, 内存 {metrics['memory_percent']:.1f}%")
        print(f"   ✓ 执行记录: {len(executions)} 条")
        print(f"   ✓ 用户反馈: {len(feedback)} 条")
        
        results["phases"]["perception"] = {
            "metrics": metrics,
            "execution_count": len(executions),
            "feedback_count": len(feedback)
        }
        
        # Phase 2: 分析
        print("\n🔍 Phase 2: 分析 - 识别瓶颈...")
        bottlenecks = self.analyze_bottlenecks()
        trends = self.analyze_performance_trends()
        
        if bottlenecks:
            print(f"   ⚠️ 发现 {len(bottlenecks)} 个瓶颈:")
            for b in bottlenecks:
                print(f"      - {b['dimension']}: {b['fail_rate']:.0%}失败率 ({b['severity']})")
        else:
            print("   ✅ 没有发现明显瓶颈")
        
        results["phases"]["analysis"] = {
            "bottlenecks": bottlenecks,
            "trends": trends
        }
        
        # Phase 3: 决策
        print("\n🎯 Phase 3: 决策 - 生成修复方案...")
        fixes = self.generate_actionable_fixes(bottlenecks)
        
        if fixes:
            print(f"   ✓ 生成 {len(fixes)} 个修复方案:")
            for fix in fixes:
                print(f"      - {fix['id']}: {fix['solution']}")
        else:
            print("   ℹ 无需修复")
        
        results["phases"]["decision"] = {
            "fixes_generated": len(fixes),
            "fixes": fixes
        }
        
        # Phase 4: 执行
        print("\n⚙️ Phase 4: 执行 - 应用优化...")
        applied_fixes = []
        
        for fix in fixes:
            if fix.get("auto_apply"):
                print(f"   🔧 应用: {fix['id']}")
                try:
                    # 执行修复
                    file_path = fix["implementation"]()
                    print(f"      ✓ 创建: {file_path.name}")
                    
                    # 验证修复
                    if fix.get("validation"):
                        valid = fix["validation"](file_path)
                        if valid:
                            print(f"      ✓ 验证通过")
                            applied_fixes.append({
                                "id": fix["id"],
                                "file": str(file_path),
                                "status": "applied_and_verified"
                            })
                        else:
                            print(f"      ❌ 验证失败")
                            applied_fixes.append({
                                "id": fix["id"],
                                "file": str(file_path),
                                "status": "applied_but_failed_validation"
                            })
                    else:
                        applied_fixes.append({
                            "id": fix["id"],
                            "file": str(file_path),
                            "status": "applied"
                        })
                
                except Exception as e:
                    print(f"      ❌ 应用失败: {e}")
                    applied_fixes.append({
                        "id": fix["id"],
                        "error": str(e),
                        "status": "failed"
                    })
        
        results["phases"]["execution"] = {
            "fixes_applied": len(applied_fixes),
            "details": applied_fixes
        }
        
        # Phase 5: 验证（简化版：记录当前状态作为基线）
        print("\n✅ Phase 5: 验证 - 记录优化基线...")
        baseline = {
            "timestamp": datetime.now().isoformat(),
            "bottlenecks_before": len(bottlenecks),
            "fixes_applied": len(applied_fixes),
            "expected_improvement": sum(f.get("expected_improvement", 0) for f in fixes) / len(fixes) if fixes else 0
        }
        print(f"   ✓ 基线已记录，24小时后对比效果")
        
        results["phases"]["verification"] = baseline
        
        # Phase 6: 学习
        print("\n🧠 Phase 6: 学习 - 沉淀经验...")
        
        # 保存本次优化记录
        optimization_record = {
            "cycle_id": results["cycle_id"],
            "timestamp": datetime.now().isoformat(),
            "bottlenecks_found": len(bottlenecks),
            "fixes_applied": len(applied_fixes),
            "success_rate": sum(1 for a in applied_fixes if "verified" in a.get("status", "")) / len(applied_fixes) if applied_fixes else 0
        }
        
        # 追加到优化历史
        history_file = CLAW / "optimization_history.jsonl"
        with open(history_file, "a") as f:
            f.write(json.dumps(optimization_record) + "\n")
        
        print(f"   ✓ 优化经验已记录到: {history_file}")
        
        results["phases"]["learning"] = optimization_record
        
        # 生成报告
        print("\n" + "=" * 60)
        print("📊 优化周期完成")
        print("=" * 60)
        print(f"\n周期ID: {results['cycle_id']}")
        print(f"发现瓶颈: {len(bottlenecks)} 个")
        print(f"应用修复: {len(applied_fixes)} 个")
        print(f"成功率: {optimization_record['success_rate']:.0%}")
        
        return results


def main():
    """主函数"""
    optimizer = ClosedLoopOptimizer()
    results = optimizer.run_optimization_cycle()
    
    # 保存完整报告
    report_file = CLAW / f"closed_loop_report_{results['cycle_id']}.json"
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 完整报告: {report_file}")


if __name__ == "__main__":
    main()
