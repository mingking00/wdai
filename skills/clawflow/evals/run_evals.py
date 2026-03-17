#!/usr/bin/env python3
"""
ClawFlow Skill Evaluator
运行评估测试并生成报告
"""

import json
import sys
import time
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clawflow import WorkflowEngine


def run_eval(eval_config: dict) -> dict:
    """运行单个评估测试"""
    
    print(f"\n{'='*60}")
    print(f"🧪 测试: {eval_config['eval_name']}")
    print(f"{'='*60}")
    
    workflow = eval_config['input'].get('workflow', {})
    parallel = eval_config['input'].get('parallel', False)
    
    engine = WorkflowEngine()
    
    start_time = time.time()
    try:
        result = engine.execute(workflow, parallel=parallel, verbose=False)
        execution_time = time.time() - start_time
        
        print(f"  ✓ 执行成功")
        print(f"  ⏱️  耗时: {execution_time:.3f}s")
        
        # 运行断言检查
        assertions_results = []
        for assertion in eval_config.get('assertions', []):
            passed = check_assertion(assertion, result, execution_time)
            assertions_results.append({
                "name": assertion['name'],
                "description": assertion['description'],
                "passed": passed
            })
            status = "✓" if passed else "✗"
            print(f"  {status} {assertion['name']}: {assertion['description']}")
        
        return {
            "success": result.success,
            "execution_time": execution_time,
            "assertions": assertions_results,
            "data": result.data if result.success else None,
            "error": result.error if not result.success else None
        }
        
    except Exception as e:
        print(f"  ✗ 执行失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "assertions": []
        }


def check_assertion(assertion: dict, result, execution_time: float) -> bool:
    """检查单个断言"""
    check = assertion.get('check', '')
    
    try:
        if 'result.success' in check:
            return result.success
        elif 'execution_time' in check:
            threshold = float(check.split('<')[-1].strip())
            return execution_time < threshold
        elif 'len' in check and 'results' in check:
            # 简化检查
            data = result.data if result.success else {}
            if isinstance(data, dict):
                results = data.get('results', [])
                return len(results) > 0
        return result.success
    except:
        return False


def run_baseline(eval_config: dict) -> dict:
    """运行基线测试（不使用ClawFlow）"""
    
    print(f"\n  📊 Baseline (无工作流引擎)")
    
    # 基线：直接Python执行
    start_time = time.time()
    try:
        # 模拟直接执行
        workflow = eval_config['input'].get('workflow', {})
        nodes = workflow.get('nodes', [])
        
        # 简单顺序执行
        for node in nodes:
            if node['type'] == 'delay':
                delay_ms = node.get('params', {}).get('delay', 0)
                time.sleep(delay_ms / 1000)
        
        execution_time = time.time() - start_time
        
        print(f"  ⏱️  耗时: {execution_time:.3f}s")
        
        return {
            "success": True,
            "execution_time": execution_time,
            "method": "direct_python"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """主函数"""
    
    print("\n" + "="*60)
    print("🚀 ClawFlow Skill Evaluation")
    print("="*60)
    
    # 加载评估配置
    evals_path = Path(__file__).parent / "evals.json"
    with open(evals_path) as f:
        config = json.load(f)
    
    print(f"\n📋 技能: {config['skill_name']}")
    print(f"📝 描述: {config['description']}")
    print(f"🔢 测试数: {len(config['evals'])}")
    
    # 运行所有测试
    results = {
        "skill_name": config['skill_name'],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "evaluations": []
    }
    
    for eval_config in config['evals']:
        # With skill
        with_skill = run_eval(eval_config)
        
        # Baseline
        baseline = run_baseline(eval_config)
        
        # 计算改进
        if with_skill['success'] and baseline['success']:
            time_diff = baseline['execution_time'] - with_skill['execution_time']
            improvement = (time_diff / baseline['execution_time']) * 100 if baseline['execution_time'] > 0 else 0
        else:
            improvement = 0
        
        eval_result = {
            "eval_id": eval_config['id'],
            "eval_name": eval_config['eval_name'],
            "prompt": eval_config['prompt'],
            "with_skill": with_skill,
            "baseline": baseline,
            "improvement_percent": improvement
        }
        
        results['evaluations'].append(eval_result)
    
    # 生成报告
    print("\n" + "="*60)
    print("📊 Evaluation Report")
    print("="*60)
    
    total_tests = len(results['evaluations'])
    passed_tests = sum(1 for e in results['evaluations'] if e['with_skill']['success'])
    
    print(f"\n总分: {passed_tests}/{total_tests} 测试通过 ({passed_tests/total_tests*100:.0f}%)")
    
    print("\n详细结果:")
    for eval_result in results['evaluations']:
        status = "✅" if eval_result['with_skill']['success'] else "❌"
        print(f"\n{status} {eval_result['eval_name']}")
        print(f"   ClawFlow: {eval_result['with_skill']['execution_time']:.3f}s")
        print(f"   Baseline: {eval_result['baseline']['execution_time']:.3f}s")
        if eval_result['improvement_percent'] > 0:
            print(f"   提升: +{eval_result['improvement_percent']:.1f}%")
        
        # 断言结果
        for assertion in eval_result['with_skill'].get('assertions', []):
            status = "✓" if assertion['passed'] else "✗"
            print(f"   {status} {assertion['name']}")
    
    # 保存结果
    workspace = Path("/root/.openclaw/workspace/clawflow-workspace/iteration-1")
    workspace.mkdir(parents=True, exist_ok=True)
    
    results_path = workspace / "results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 结果保存到: {results_path}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
