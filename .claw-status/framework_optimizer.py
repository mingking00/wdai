#!/usr/bin/env python3
"""
WDai 框架自优化引擎

真正的闭环：数据收集 → 模式分析 → 优化决策 → 代码执行 → 效果验证
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

WORKSPACE = Path("/root/.openclaw/workspace")
CLAW = WORKSPACE / ".claw-status"
EVO = WORKSPACE / ".evolution"
METRICS_FILE = CLAW / "system_metrics.jsonl"
RESULTS_FILE = EVO / "execution_results.json"
HISTORY_FILE = EVO / "evolution_history.json"
INSIGHTS_FILE = EVO / "insights.json"

class FrameworkOptimizer:
    """框架自优化引擎"""
    
    def __init__(self):
        self.metrics = []
        self.execution_results = []
        self.insights = []
        self.proposed_optimizations = []
        
    def load_data(self):
        """加载所有数据"""
        # 1. 加载系统指标
        if METRICS_FILE.exists():
            with open(METRICS_FILE) as f:
                for line in f:
                    try:
                        self.metrics.append(json.loads(line))
                    except:
                        pass
        
        # 2. 加载执行结果
        if RESULTS_FILE.exists():
            with open(RESULTS_FILE) as f:
                self.execution_results = json.load(f)
        
        # 3. 加载已有洞察
        if INSIGHTS_FILE.exists():
            with open(INSIGHTS_FILE) as f:
                self.insights = json.load(f)
        
        print(f"📊 数据加载完成:")
        print(f"   系统指标: {len(self.metrics)} 条")
        print(f"   执行结果: {len(self.execution_results)} 条")
        print(f"   已有洞察: {len(self.insights)} 条")
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """分析执行模式，识别问题和机会"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "success_rate_by_dimension": {},
            "common_errors": [],
            "performance_trends": {},
            "recommendations": []
        }
        
        # 1. 按维度分析成功率
        dimension_results = defaultdict(lambda: {"success": 0, "fail": 0})
        for result in self.execution_results:
            dim = result.get("dimension", "unknown")
            if result.get("success"):
                dimension_results[dim]["success"] += 1
            else:
                dimension_results[dim]["fail"] += 1
        
        for dim, counts in dimension_results.items():
            total = counts["success"] + counts["fail"]
            rate = counts["success"] / total if total > 0 else 0
            analysis["success_rate_by_dimension"][dim] = {
                "success": counts["success"],
                "fail": counts["fail"],
                "rate": round(rate, 2)
            }
        
        # 2. 分析常见错误
        error_patterns = defaultdict(int)
        for result in self.execution_results:
            if not result.get("success"):
                error = result.get("message", "")
                # 提取错误类型
                if "syntax" in error.lower() or "语法" in error:
                    error_patterns["syntax_error"] += 1
                elif "timeout" in error.lower() or "超时" in error:
                    error_patterns["timeout"] += 1
                elif "file" in error.lower() or "文件" in error:
                    error_patterns["file_operation"] += 1
                elif "permission" in error.lower() or "权限" in error:
                    error_patterns["permission"] += 1
                else:
                    error_patterns["other"] += 1
        
        analysis["common_errors"] = [
            {"type": k, "count": v} 
            for k, v in sorted(error_patterns.items(), key=lambda x: -x[1])
        ]
        
        # 3. 性能趋势分析
        if len(self.metrics) >= 10:
            recent = self.metrics[-10:]
            avg_response = sum(m.get("response_time_ms", 0) for m in recent) / len(recent)
            avg_overload = sum(m.get("overload_score", 0) for m in recent) / len(recent)
            avg_memory = sum(m.get("memory_percent", 0) for m in recent) / len(recent)
            
            analysis["performance_trends"] = {
                "avg_response_ms": round(avg_response, 2),
                "avg_overload_score": round(avg_overload, 2),
                "avg_memory_percent": round(avg_memory, 2),
                "health_status": "good" if avg_overload < 0.5 else "warning" if avg_overload < 0.8 else "critical"
            }
        
        return analysis
    
    def generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """基于分析结果生成优化建议"""
        recommendations = []
        
        # 1. 基于成功率低的问题
        for dim, stats in analysis.get("success_rate_by_dimension", {}).items():
            if stats["rate"] < 0.7 and stats["fail"] > 3:
                recommendations.append({
                    "type": "fix_reliability",
                    "target": dim,
                    "priority": "high",
                    "reason": f"{dim}维度成功率仅{stats['rate']:.0%}，需要修复",
                    "action": f"检查并修复{dim}相关代码的错误处理逻辑",
                    "estimated_impact": f"将成功率提升到90%以上"
                })
        
        # 2. 基于常见错误
        for error in analysis.get("common_errors", [])[:3]:
            if error["count"] >= 3:
                if error["type"] == "syntax_error":
                    recommendations.append({
                        "type": "add_validation",
                        "target": "code_generation",
                        "priority": "high",
                        "reason": f"语法错误发生{error['count']}次",
                        "action": "在代码生成后增加自动语法检查",
                        "estimated_impact": "减少50%的语法错误"
                    })
                elif error["type"] == "timeout":
                    recommendations.append({
                        "type": "optimize_performance",
                        "target": "execution_loop",
                        "priority": "medium",
                        "reason": f"超时错误发生{error['count']}次",
                        "action": "优化执行循环，添加进度检查点",
                        "estimated_impact": "减少30%的超时"
                    })
        
        # 3. 基于性能趋势
        perf = analysis.get("performance_trends", {})
        if perf.get("health_status") == "warning":
            recommendations.append({
                "type": "resource_optimization",
                "target": "system",
                "priority": "medium",
                "reason": f"系统负载较高(overload_score={perf.get('avg_overload_score')})",
                "action": "实施资源优化策略：限制并发任务数、优化内存使用",
                "estimated_impact": "降低20%的系统负载"
            })
        
        # 4. 基于执行频率
        recent_executions = [r for r in self.execution_results 
                           if datetime.fromtimestamp(r.get("timestamp", 0)) > datetime.now() - timedelta(hours=24)]
        if len(recent_executions) > 50:
            recommendations.append({
                "type": "batch_optimization",
                "target": "execution_strategy",
                "priority": "low",
                "reason": f"24小时内执行了{len(recent_executions)}次任务",
                "action": "优化执行策略，合并相似任务，减少重复执行",
                "estimated_impact": "减少30%的无效执行"
            })
        
        return recommendations
    
    def create_optimization_plan(self, recommendations: List[Dict]) -> Dict:
        """创建优化执行计划"""
        # 选择优先级最高的建议
        high_priority = [r for r in recommendations if r["priority"] == "high"]
        medium_priority = [r for r in recommendations if r["priority"] == "medium"]
        
        selected = (high_priority[:1] + medium_priority[:1]) if high_priority else recommendations[:2]
        
        plan = {
            "timestamp": datetime.now().isoformat(),
            "selected_optimizations": selected,
            "execution_steps": []
        }
        
        for opt in selected:
            steps = self._generate_execution_steps(opt)
            plan["execution_steps"].extend(steps)
        
        return plan
    
    def _generate_execution_steps(self, optimization: Dict) -> List[Dict]:
        """为每个优化生成具体执行步骤"""
        opt_type = optimization["type"]
        steps = []
        
        if opt_type == "add_validation":
            steps = [
                {
                    "action": "create_file",
                    "file": str(CLAW / "code_validator.py"),
                    "content": self._get_validator_code(),
                    "description": "创建代码验证模块"
                },
                {
                    "action": "update_file",
                    "file": str(EVO / "evolution_loop.py"),
                    "description": "在代码生成后添加验证调用",
                    "insert_before": "def apply_code_changes",
                    "code": "        # 验证代码语法\n        from .claw-status.code_validator import validate_code\n        validation = validate_code(code)\n        if not validation['valid']:\n            return {'success': False, 'error': validation['error']}"
                }
            ]
        
        elif opt_type == "optimize_performance":
            steps = [
                {
                    "action": "create_file",
                    "file": str(CLAW / "performance_monitor.py"),
                    "content": self._get_performance_monitor_code(),
                    "description": "创建性能监控模块"
                },
                {
                    "action": "update_config",
                    "file": str(EVO / "config.json"),
                    "changes": {
                        "max_execution_time": 300,
                        "enable_progress_checkpoints": True
                    },
                    "description": "更新执行配置"
                }
            ]
        
        elif opt_type == "fix_reliability":
            steps = [
                {
                    "action": "create_file",
                    "file": str(CLAW / "reliability_enhancer.py"),
                    "content": self._get_reliability_code(),
                    "description": "创建可靠性增强模块"
                }
            ]
        
        return steps
    
    def _get_validator_code(self) -> str:
        """生成代码验证模块代码"""
        return '''"""代码验证模块 - 自动生成"""
import ast
from typing import Dict, Any

def validate_code(code: str) -> Dict[str, Any]:
    """验证Python代码语法"""
    try:
        ast.parse(code)
        return {"valid": True, "error": None}
    except SyntaxError as e:
        return {"valid": False, "error": str(e)}
    except Exception as e:
        return {"valid": False, "error": f"未知错误: {e}"}
'''
    
    def _get_performance_monitor_code(self) -> str:
        """生成性能监控代码"""
        return '''"""性能监控模块 - 自动生成"""
import time
from typing import Callable, Any

def with_timeout(func: Callable, timeout: float = 300) -> Any:
    """带超时的函数执行"""
    import signal
    
    def handler(signum, frame):
        raise TimeoutError(f"执行超过{timeout}秒")
    
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(int(timeout))
    
    try:
        result = func()
        signal.alarm(0)
        return result
    except TimeoutError:
        return {"success": False, "error": "执行超时"}
'''
    
    def _get_reliability_code(self) -> str:
        """生成可靠性增强代码"""
        return '''"""可靠性增强模块 - 自动生成"""
import traceback
from typing import Callable, Any, Dict

def with_retry(func: Callable, max_retries: int = 3) -> Dict[str, Any]:
    """带重试的函数执行"""
    for attempt in range(max_retries):
        try:
            return {"success": True, "result": func(), "attempts": attempt + 1}
        except Exception as e:
            if attempt == max_retries - 1:
                return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
    return {"success": False, "error": "所有重试都失败"}
'''
    
    def execute_plan(self, plan: Dict) -> Dict:
        """执行优化计划"""
        results = []
        
        for step in plan.get("execution_steps", []):
            try:
                if step["action"] == "create_file":
                    Path(step["file"]).write_text(step["content"])
                    results.append({
                        "step": step["description"],
                        "status": "success",
                        "file": step["file"]
                    })
                
                elif step["action"] == "update_file":
                    # 简化的文件更新（实际需要更复杂的逻辑）
                    results.append({
                        "step": step["description"],
                        "status": "pending_manual",
                        "note": "需要手动应用更改"
                    })
                
                elif step["action"] == "update_config":
                    config_file = Path(step["file"])
                    config = json.loads(config_file.read_text()) if config_file.exists() else {}
                    config.update(step["changes"])
                    config_file.write_text(json.dumps(config, indent=2))
                    results.append({
                        "step": step["description"],
                        "status": "success",
                        "changes": step["changes"]
                    })
            
            except Exception as e:
                results.append({
                    "step": step["description"],
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "success_rate": sum(1 for r in results if r["status"] == "success") / len(results) if results else 0
        }
    
    def generate_report(self, analysis: Dict, recommendations: List[Dict], 
                       plan: Dict, execution: Dict) -> str:
        """生成优化报告"""
        report = f"""# WDai 框架自优化报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 1. 数据分析

### 执行成功率（按维度）
"""
        for dim, stats in analysis.get("success_rate_by_dimension", {}).items():
            report += f"- **{dim}**: {stats['rate']:.0%} ({stats['success']}/{stats['success']+stats['fail']})\n"
        
        report += "\n### 常见错误\n"
        for error in analysis.get("common_errors", [])[:5]:
            report += f"- {error['type']}: {error['count']} 次\n"
        
        perf = analysis.get("performance_trends", {})
        report += f"""
### 系统健康度
- **平均响应时间**: {perf.get('avg_response_ms', 'N/A')} ms
- **平均负载分数**: {perf.get('avg_overload_score', 'N/A')}
- **健康状态**: {perf.get('health_status', 'unknown')}

## 2. 优化建议

"""
        for i, rec in enumerate(recommendations, 1):
            report += f"""### {i}. {rec['target']} - {rec['type']}
- **优先级**: {rec['priority']}
- **原因**: {rec['reason']}
- **建议行动**: {rec['action']}
- **预期效果**: {rec['estimated_impact']}

"""
        
        report += f"""
## 3. 执行结果

**选中优化**: {len(plan.get('selected_optimizations', []))} 项
**执行步骤**: {len(plan.get('execution_steps', []))} 步
**成功率**: {execution.get('success_rate', 0):.0%}

### 详细结果
"""
        for result in execution.get("results", []):
            status_icon = "✅" if result["status"] == "success" else "⚠️" if result["status"] == "pending_manual" else "❌"
            report += f"- {status_icon} {result['step']}\n"
        
        report += """
## 4. 下一步行动

1. 检查执行结果中的"pending_manual"项，手动完成剩余更改
2. 运行测试验证优化效果
3. 持续监控系统指标
4. 24小时后再次运行分析，评估优化效果

---
*由 WDai 框架自优化引擎自动生成*
"""
        
        return report


def main():
    """主函数"""
    print("=" * 60)
    print("WDai 框架自优化引擎")
    print("=" * 60)
    
    optimizer = FrameworkOptimizer()
    
    # 1. 加载数据
    print("\n📥 步骤1: 加载数据...")
    optimizer.load_data()
    
    # 2. 分析模式
    print("\n🔍 步骤2: 分析执行模式...")
    analysis = optimizer.analyze_patterns()
    print(f"   发现 {len(analysis.get('common_errors', []))} 种常见错误")
    
    # 3. 生成建议
    print("\n💡 步骤3: 生成优化建议...")
    recommendations = optimizer.generate_recommendations(analysis)
    print(f"   生成 {len(recommendations)} 条优化建议")
    for rec in recommendations:
        print(f"   - [{rec['priority'].upper()}] {rec['type']}: {rec['target']}")
    
    # 4. 创建计划
    print("\n📋 步骤4: 创建执行计划...")
    plan = optimizer.create_optimization_plan(recommendations)
    print(f"   选中 {len(plan.get('selected_optimizations', []))} 项优化")
    print(f"   生成 {len(plan.get('execution_steps', []))} 个执行步骤")
    
    # 5. 执行计划
    print("\n⚙️ 步骤5: 执行优化...")
    execution = optimizer.execute_plan(plan)
    print(f"   执行成功率: {execution.get('success_rate', 0):.0%}")
    
    # 6. 生成报告
    print("\n📝 步骤6: 生成报告...")
    report = optimizer.generate_report(analysis, recommendations, plan, execution)
    
    # 保存报告
    report_file = CLAW / f"optimization_report_{datetime.now():%Y%m%d_%H%M%S}.md"
    report_file.write_text(report)
    print(f"   报告已保存: {report_file}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("优化摘要")
    print("=" * 60)
    print(f"\n✅ 分析了 {len(optimizer.execution_results)} 条执行记录")
    print(f"✅ 识别了 {len(analysis.get('common_errors', []))} 类问题")
    print(f"✅ 生成了 {len(recommendations)} 条优化建议")
    print(f"✅ 执行了 {len(execution.get('results', []))} 个优化步骤")
    print(f"✅ 成功率: {execution.get('success_rate', 0):.0%}")
    print(f"\n📄 完整报告: {report_file}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
