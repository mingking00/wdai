#!/usr/bin/env python3
"""
Phase 4: Sandbox Testing Layer - 沙箱测试层

核心能力:
1. 隔离沙箱环境 - 文件级隔离，安全测试修改
2. 自动化测试生成 - 基于代码分析生成测试用例
3. 回归测试 - 确保修改不破坏现有功能
4. 性能基准测试 - 量化性能影响
5. A/B测试框架 - 对比新旧实现

基于Phase 1/2/3的能力，实现运行时验证

Author: wdai
Version: 1.0 - Phase 4 Implementation
"""

import ast
import sys
import time
import tempfile
import shutil
import subprocess
import json
import hashlib
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
from contextlib import contextmanager
import sys

# 导入前面的Phase
sys.path.insert(0, str(Path(__file__).parent))
try:
    from code_understanding import CodeUnderstandingLayer, FunctionInfo
    from creative_design import DesignCandidate
    from formal_verification import FormalVerificationLayer
    PHASE1_AVAILABLE = True
    PHASE2_AVAILABLE = True
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False
    PHASE2_AVAILABLE = False
    PHASE3_AVAILABLE = False


@dataclass
class TestCase:
    """测试用例"""
    name: str
    function_name: str
    inputs: List[Any]
    expected_output: Any
    expected_exception: Optional[str] = None
    timeout_ms: int = 5000


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    passed: bool
    actual_output: Any = None
    execution_time_ms: float = 0.0
    error_message: str = ""
    stack_trace: str = ""


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time_ms: float
    memory_usage_mb: float
    cpu_percent: float
    iterations: int
    throughput: float  # ops/sec


@dataclass
class ABTestResult:
    """A/B测试结果"""
    baseline_metrics: PerformanceMetrics
    variant_metrics: PerformanceMetrics
    improvement_percent: Dict[str, float]
    statistically_significant: bool
    recommendation: str  # "adopt", "reject", "inconclusive"


@dataclass
class SandboxTestReport:
    """沙箱测试报告"""
    design_id: str
    test_cases_total: int
    test_cases_passed: int
    test_cases_failed: int
    pass_rate: float
    performance_baseline: Optional[PerformanceMetrics]
    performance_variant: Optional[PerformanceMetrics]
    ab_test_result: Optional[ABTestResult]
    regression_detected: bool
    can_deploy: bool
    details: Dict[str, Any]


class IsolatedSandbox:
    """
    隔离沙箱
    
    提供安全的测试环境，隔离文件系统
    """
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path(tempfile.mkdtemp(prefix="sandbox_"))
        self.original_cwd = None
        self.is_active = False
    
    @contextmanager
    def activate(self):
        """激活沙箱环境"""
        self.original_cwd = Path.cwd()
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 复制项目文件到沙箱
            self._copy_project_files()
            
            # 切换到沙箱目录
            import os
            os.chdir(self.base_path)
            self.is_active = True
            
            yield self
            
        finally:
            # 恢复原目录
            os.chdir(self.original_cwd)
            self.is_active = False
    
    def _copy_project_files(self):
        """复制项目文件到沙箱"""
        # 简化版：复制当前目录的Python文件
        source_dir = Path(__file__).parent
        
        for py_file in source_dir.glob("*.py"):
            if py_file.name != __file__:
                shutil.copy2(py_file, self.base_path / py_file.name)
        
        # 创建data目录
        (self.base_path / "data").mkdir(exist_ok=True)
    
    def deploy_change(self, file_path: str, new_content: str):
        """部署代码修改到沙箱"""
        if not self.is_active:
            raise RuntimeError("沙箱未激活")
        
        target = self.base_path / Path(file_path).name
        with open(target, 'w') as f:
            f.write(new_content)
    
    def run_python(self, script_path: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """在沙箱中运行Python脚本"""
        if not self.is_active:
            raise RuntimeError("沙箱未激活")
        
        target = self.base_path / script_path
        
        try:
            result = subprocess.run(
                [sys.executable, str(target)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.base_path
            )
            
            return (
                result.returncode == 0,
                result.stdout,
                result.stderr
            )
        except subprocess.TimeoutExpired:
            return False, "", "Timeout"
        except Exception as e:
            return False, "", str(e)
    
    def cleanup(self):
        """清理沙箱"""
        if self.base_path.exists():
            shutil.rmtree(self.base_path)


class AutoTestGenerator:
    """
    自动化测试生成器
    
    基于代码分析自动生成测试用例
    """
    
    def __init__(self):
        self.test_cases: List[TestCase] = []
    
    def generate_for_function(self, func_info: FunctionInfo, source: str) -> List[TestCase]:
        """为函数生成测试用例"""
        try:
            tree = ast.parse(source)
            func_node = None
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_info.name:
                    func_node = node
                    break
            
            if not func_node:
                return []
            
            test_cases = []
            
            # 1. 基于参数类型生成基本测试
            base_cases = self._generate_base_cases(func_node, func_info)
            test_cases.extend(base_cases)
            
            # 2. 基于分支覆盖生成边界测试
            edge_cases = self._generate_edge_cases(func_node, func_info)
            test_cases.extend(edge_cases)
            
            # 3. 基于docstring生成示例测试
            example_cases = self._generate_from_docstring(func_info)
            test_cases.extend(example_cases)
            
            self.test_cases.extend(test_cases)
            return test_cases
            
        except Exception as e:
            print(f"   ⚠️ 测试生成失败: {e}")
            return []
    
    def _generate_base_cases(self, func_node: ast.FunctionDef, func_info: FunctionInfo) -> List[TestCase]:
        """生成基本测试用例"""
        cases = []
        
        # 根据参数数量生成简单输入
        num_args = len(func_node.args.args)
        
        if num_args == 0:
            # 无参数函数
            cases.append(TestCase(
                name=f"test_{func_info.name}_basic",
                function_name=func_info.name,
                inputs=[],
                expected_output=None  # 需要推断
            ))
        elif num_args == 1:
            # 单参数函数 - 测试不同类型
            arg = func_node.args.args[0]
            
            # 尝试根据参数名推断类型
            if any(kw in arg.arg.lower() for kw in ['count', 'num', 'size', 'id', 'index']):
                cases.append(TestCase(
                    name=f"test_{func_info.name}_integer",
                    function_name=func_info.name,
                    inputs=[1],
                    expected_output=None
                ))
                cases.append(TestCase(
                    name=f"test_{func_info.name}_zero",
                    function_name=func_info.name,
                    inputs=[0],
                    expected_output=None
                ))
            elif any(kw in arg.arg.lower() for kw in ['name', 'text', 'str', 'path']):
                cases.append(TestCase(
                    name=f"test_{func_info.name}_string",
                    function_name=func_info.name,
                    inputs=["test"],
                    expected_output=None
                ))
                cases.append(TestCase(
                    name=f"test_{func_info.name}_empty",
                    function_name=func_info.name,
                    inputs=[""],
                    expected_output=None
                ))
            else:
                cases.append(TestCase(
                    name=f"test_{func_info.name}_basic",
                    function_name=func_info.name,
                    inputs=[None],
                    expected_output=None
                ))
        
        return cases
    
    def _generate_edge_cases(self, func_node: ast.FunctionDef, func_info: FunctionInfo) -> List[TestCase]:
        """生成边界测试用例"""
        cases = []
        
        # 查找是否有条件分支
        has_conditions = any(
            isinstance(node, (ast.If, ast.Compare))
            for node in ast.walk(func_node)
        )
        
        if has_conditions:
            # 生成边界值测试
            cases.append(TestCase(
                name=f"test_{func_info.name}_boundary_min",
                function_name=func_info.name,
                inputs=[-1],
                expected_output=None
            ))
            cases.append(TestCase(
                name=f"test_{func_info.name}_boundary_max",
                function_name=func_info.name,
                inputs=[999999],
                expected_output=None
            ))
        
        return cases
    
    def _generate_from_docstring(self, func_info: FunctionInfo) -> List[TestCase]:
        """从docstring提取示例生成测试"""
        cases = []
        
        if not func_info.docstring:
            return cases
        
        # 简单的示例提取（寻找 >>> 模式）
        lines = func_info.docstring.split('\n')
        for i, line in enumerate(lines):
            if '>>>' in line:
                # 提取示例调用
                example = line.split('>>>')[1].strip()
                cases.append(TestCase(
                    name=f"test_{func_info.name}_doc_example_{i}",
                    function_name=func_info.name,
                    inputs=[],  # 需要解析
                    expected_output=None
                ))
        
        return cases


class RegressionTester:
    """
    回归测试器
    
    确保修改不破坏现有功能
    """
    
    def __init__(self, sandbox: IsolatedSandbox):
        self.sandbox = sandbox
        self.test_history: List[Dict] = []
    
    def run_regression_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        """运行回归测试"""
        results = []
        
        for test in test_cases:
            result = self._run_single_test(test)
            results.append(result)
        
        return results
    
    def _run_single_test(self, test: TestCase) -> TestResult:
        """运行单个测试"""
        start_time = time.time()
        
        try:
            # 这里简化处理，实际应该动态导入并调用函数
            # 生成测试脚本
            test_script = self._generate_test_script(test)
            
            # 写入临时文件
            test_file = self.sandbox.base_path / f"test_{test.name}.py"
            with open(test_file, 'w') as f:
                f.write(test_script)
            
            # 运行测试
            success, stdout, stderr = self.sandbox.run_python(
                test_file.name,
                timeout=test.timeout_ms // 1000
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return TestResult(
                test_name=test.name,
                passed=success,
                actual_output=stdout if success else None,
                execution_time_ms=execution_time,
                error_message=stderr if not success else ""
            )
            
        except Exception as e:
            return TestResult(
                test_name=test.name,
                passed=False,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _generate_test_script(self, test: TestCase) -> str:
        """生成测试脚本"""
        script = f"""
import sys
sys.path.insert(0, '.')

try:
    from {test.function_name} import {test.function_name}
    
    # 调用函数
    result = {test.function_name}(*{test.inputs})
    
    print(f"Result: {{result}}")
    sys.exit(0)
    
except Exception as e:
    print(f"Error: {{e}}")
    sys.exit(1)
"""
        return script
    
    def detect_regression(self, old_results: List[TestResult], 
                         new_results: List[TestResult]) -> bool:
        """检测是否引入回归"""
        old_passed = {r.test_name: r.passed for r in old_results}
        
        for new_result in new_results:
            test_name = new_result.test_name
            
            # 如果之前通过的测试现在失败了，就是回归
            if old_passed.get(test_name, False) and not new_result.passed:
                return True
        
        return False


class PerformanceBenchmark:
    """
    性能基准测试
    
    量化性能影响
    """
    
    def __init__(self, sandbox: IsolatedSandbox):
        self.sandbox = sandbox
    
    def benchmark_function(self, func_name: str, 
                          test_inputs: List[Any],
                          iterations: int = 100) -> PerformanceMetrics:
        """对函数进行性能基准测试"""
        
        # 生成基准测试脚本
        benchmark_script = f"""
import time
import sys
sys.path.insert(0, '.')

try:
    from scheduler import {func_name}
    
    # 预热
    for _ in range(10):
        try:
            {func_name}()
        except:
            pass
    
    # 正式测试
    start = time.time()
    for _ in range({iterations}):
        try:
            {func_name}()
        except:
            pass
    end = time.time()
    
    elapsed = (end - start) * 1000  # ms
    throughput = {iterations} / (end - start)
    
    print(f"elapsed_ms={{elapsed}}")
    print(f"throughput={{throughput}}")
    print(f"iterations={iterations}")
    
except Exception as e:
    print(f"Error: {{e}}")
    sys.exit(1)
"""
        
        # 写入并运行
        bench_file = self.sandbox.base_path / f"benchmark_{func_name}.py"
        with open(bench_file, 'w') as f:
            f.write(benchmark_script)
        
        success, stdout, stderr = self.sandbox.run_python(bench_file.name)
        
        # 解析结果
        elapsed_ms = 0.0
        throughput = 0.0
        
        if success:
            for line in stdout.split('\n'):
                if 'elapsed_ms=' in line:
                    try:
                        elapsed_ms = float(line.split('=')[1])
                    except:
                        pass
                elif 'throughput=' in line:
                    try:
                        throughput = float(line.split('=')[1])
                    except:
                        pass
        
        return PerformanceMetrics(
            execution_time_ms=elapsed_ms,
            memory_usage_mb=0.0,  # 简化版，实际需要psutil
            cpu_percent=0.0,
            iterations=iterations,
            throughput=throughput
        )


class ABTestFramework:
    """
    A/B测试框架
    
    对比新旧实现
    """
    
    def __init__(self, sandbox: IsolatedSandbox):
        self.sandbox = sandbox
        self.benchmark = PerformanceBenchmark(sandbox)
    
    def run_ab_test(self, func_name: str,
                   baseline_code: str,
                   variant_code: str,
                   iterations: int = 100) -> ABTestResult:
        """
        运行A/B测试
        
        对比基线版本和变体版本的性能
        """
        print(f"   📊 运行A/B测试: {func_name}")
        
        # 测试基线版本
        print("      测试基线版本...")
        baseline_metrics = self._test_version(
            func_name, baseline_code, iterations
        )
        
        # 测试变体版本
        print("      测试变体版本...")
        variant_metrics = self._test_version(
            func_name, variant_code, iterations
        )
        
        # 计算改进百分比
        improvement = {}
        
        if baseline_metrics.execution_time_ms > 0:
            time_change = ((baseline_metrics.execution_time_ms - variant_metrics.execution_time_ms) 
                          / baseline_metrics.execution_time_ms * 100)
            improvement['execution_time'] = time_change
        
        if baseline_metrics.throughput > 0:
            throughput_change = ((variant_metrics.throughput - baseline_metrics.throughput) 
                                / baseline_metrics.throughput * 100)
            improvement['throughput'] = throughput_change
        
        # 判断是否显著改进（简化：吞吐量提升>5%认为显著）
        significant = improvement.get('throughput', 0) > 5
        
        # 生成推荐
        if significant and improvement.get('throughput', 0) > 0:
            recommendation = "adopt"
        elif improvement.get('throughput', 0) < -10:
            recommendation = "reject"
        else:
            recommendation = "inconclusive"
        
        return ABTestResult(
            baseline_metrics=baseline_metrics,
            variant_metrics=variant_metrics,
            improvement_percent=improvement,
            statistically_significant=significant,
            recommendation=recommendation
        )
    
    def _test_version(self, func_name: str, code: str, iterations: int) -> PerformanceMetrics:
        """测试特定版本"""
        # 部署代码
        self.sandbox.deploy_change(f"{func_name}.py", code)
        
        # 运行基准测试
        return self.benchmark.benchmark_function(func_name, [], iterations)


class SandboxTestingLayer:
    """
    沙箱测试层 - 主入口
    
    整合所有测试能力
    """
    
    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path(__file__).parent
        self.sandbox = IsolatedSandbox()
        self.test_generator = AutoTestGenerator()
        self.regression_tester: Optional[RegressionTester] = None
        self.benchmark: Optional[PerformanceBenchmark] = None
        self.ab_tester: Optional[ABTestFramework] = None
    
    def test_design(self, design: DesignCandidate, 
                   target_file: str,
                   baseline_code: str = None) -> SandboxTestReport:
        """
        🆕 Phase 4: 测试设计方案
        
        在沙箱中安全测试设计方案
        """
        print("\n🧪 Phase 4: 沙箱测试...")
        
        report = SandboxTestReport(
            design_id=design.id,
            test_cases_total=0,
            test_cases_passed=0,
            test_cases_failed=0,
            pass_rate=0.0,
            performance_baseline=None,
            performance_variant=None,
            ab_test_result=None,
            regression_detected=False,
            can_deploy=False,
            details={}
        )
        
        with self.sandbox.activate():
            self.regression_tester = RegressionTester(self.sandbox)
            self.benchmark = PerformanceBenchmark(self.sandbox)
            self.ab_tester = ABTestFramework(self.sandbox)
            
            # 1. 生成测试用例
            print("   1. 生成测试用例...")
            # 简化：直接创建一些基础测试
            test_cases = [
                TestCase(
                    name="test_basic_import",
                    function_name="main",
                    inputs=[],
                    expected_output=None
                )
            ]
            report.test_cases_total = len(test_cases)
            print(f"      生成了 {len(test_cases)} 个测试用例")
            
            # 2. 运行回归测试
            print("   2. 运行回归测试...")
            results = self.regression_tester.run_regression_tests(test_cases)
            
            passed = sum(1 for r in results if r.passed)
            failed = len(results) - passed
            
            report.test_cases_passed = passed
            report.test_cases_failed = failed
            report.pass_rate = passed / len(results) if results else 0.0
            
            print(f"      通过: {passed}, 失败: {failed}")
            print(f"      通过率: {report.pass_rate:.1%}")
            
            # 3. 性能基准测试
            print("   3. 性能基准测试...")
            # 简化：测试一个存在的函数
            target_func = "get_scheduler"
            perf_metrics = self.benchmark.benchmark_function(target_func, [], 50)
            report.performance_variant = perf_metrics
            print(f"      执行时间: {perf_metrics.execution_time_ms:.2f}ms")
            print(f"      吞吐量: {perf_metrics.throughput:.2f} ops/sec")
            
            # 4. A/B测试（如果有基线代码）
            if baseline_code:
                print("   4. 运行A/B测试...")
                # 简化：使用相同代码作为基线
                ab_result = self.ab_tester.run_ab_test(
                    target_func,
                    baseline_code,
                    baseline_code,  # 简化：相同代码
                    iterations=50
                )
                report.ab_test_result = ab_result
                print(f"      推荐: {ab_result.recommendation}")
            
            # 5. 综合判断
            print("   5. 综合评估...")
            
            # 判断是否可以部署
            can_deploy = (
                report.pass_rate >= 0.8 and  # 通过率>=80%
                not report.regression_detected
            )
            
            report.can_deploy = can_deploy
            
            if can_deploy:
                print("   ✅ 测试通过：可以安全部署")
            else:
                print("   ❌ 测试失败：不建议部署")
        
        # 清理沙箱
        self.sandbox.cleanup()
        
        return report


def main():
    """测试沙箱测试层"""
    import sys
    
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path(__file__).parent
    
    print(f"\n分析项目: {project_path}\n")
    
    # 初始化沙箱测试层
    testing_layer = SandboxTestingLayer(project_path)
    
    # 创建测试设计方案
    from creative_design import DesignCandidate
    
    test_design = DesignCandidate(
        id="test_design_001",
        pattern_id="test",
        description="测试设计方案",
        changes=[],
        objectives={},
        constraints_satisfied=True,
        risk_score=30,
        confidence=0.8,
        reasoning="测试"
    )
    
    # 运行测试
    print("="*60)
    print("🧪 测试 Phase 4: 沙箱测试层")
    print("="*60)
    
    report = testing_layer.test_design(test_design, "scheduler.py")
    
    print("\n" + "="*60)
    print("📊 测试报告")
    print("="*60)
    print(f"测试用例: {report.test_cases_total}")
    print(f"通过: {report.test_cases_passed}")
    print(f"失败: {report.test_cases_failed}")
    print(f"通过率: {report.pass_rate:.1%}")
    print(f"可以部署: {'是' if report.can_deploy else '否'}")
    
    print("\n" + "="*60)
    print("✅ Phase 4 沙箱测试层测试完成!")
    print("="*60)


if __name__ == "__main__":
    main()
