"""
wdai v3.0 - Fresh Eyes 效果评估框架

量化测试简单版 vs 增强版的实际表现
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import json

from core.agent_system.models import Task, SubTask, TodoPlan, create_task
from core.agent_system.context import SimpleContextManager
from core.agent_system.context_enhanced import EnhancedContextManager


@dataclass
class TestCase:
    """测试用例"""
    name: str
    task_description: str
    task_type: str
    available_files: List[str]
    file_contents: Dict[str, str]
    expected_files: List[str]  # 专家标注的期望文件
    notes: str = ""  # 测试场景说明


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    version: str  # "simple" or "enhanced"
    selected_files: List[str]
    expected_files: List[str]
    
    # 指标
    precision: float  # 选中的文件中多少是期望的
    recall: float     # 期望的文件中多少被选中了
    f1_score: float   # 综合指标
    
    # 额外信息
    extra_selected: List[str]  # 多选了哪些
    missed_expected: List[str]  # 漏选了哪些


class FreshEyesEvaluator:
    """Fresh Eyes 效果评估器"""
    
    def __init__(self):
        self.simple_mgr = SimpleContextManager(max_files=5)
        self.enhanced_mgr = EnhancedContextManager(max_files=5)
        self.results: List[TestResult] = []
    
    def calculate_metrics(
        self,
        selected: List[str],
        expected: List[str]
    ) -> Tuple[float, float, float]:
        """计算精确率、召回率、F1分数"""
        selected_set = set(selected)
        expected_set = set(expected)
        
        # 真正例：选中且期望的
        true_positives = len(selected_set & expected_set)
        
        # 精确率 = TP / (TP + FP)
        precision = true_positives / len(selected_set) if selected_set else 0.0
        
        # 召回率 = TP / (TP + FN)
        recall = true_positives / len(expected_set) if expected_set else 0.0
        
        # F1 = 2 * (P * R) / (P + R)
        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0
        
        return precision, recall, f1
    
    def run_test(self, test_case: TestCase) -> Tuple[TestResult, TestResult]:
        """运行单个测试用例"""
        task = create_task(
            description=test_case.task_description,
            goal="test"
        )
        
        subtask = SubTask(
            parent_id=task.id,
            type=test_case.task_type,
            description=test_case.task_description
        )
        
        plan = TodoPlan(task_id=task.id, todos=[])
        
        # 测试简单版
        simple_context = self.simple_mgr.narrow_context(
            task, subtask, plan, test_case.available_files
        )
        
        simple_precision, simple_recall, simple_f1 = self.calculate_metrics(
            simple_context.relevant_files,
            test_case.expected_files
        )
        
        simple_result = TestResult(
            test_name=test_case.name,
            version="simple",
            selected_files=simple_context.relevant_files,
            expected_files=test_case.expected_files,
            precision=simple_precision,
            recall=simple_recall,
            f1_score=simple_f1,
            extra_selected=list(set(simple_context.relevant_files) - set(test_case.expected_files)),
            missed_expected=list(set(test_case.expected_files) - set(simple_context.relevant_files))
        )
        
        # 测试增强版
        enhanced_context = self.enhanced_mgr.narrow_context(
            task, subtask, plan,
            test_case.available_files,
            test_case.file_contents
        )
        
        enhanced_precision, enhanced_recall, enhanced_f1 = self.calculate_metrics(
            enhanced_context.relevant_files,
            test_case.expected_files
        )
        
        enhanced_result = TestResult(
            test_name=test_case.name,
            version="enhanced",
            selected_files=enhanced_context.relevant_files,
            expected_files=test_case.expected_files,
            precision=enhanced_precision,
            recall=enhanced_recall,
            f1_score=enhanced_f1,
            extra_selected=list(set(enhanced_context.relevant_files) - set(test_case.expected_files)),
            missed_expected=list(set(test_case.expected_files) - set(enhanced_context.relevant_files))
        )
        
        return simple_result, enhanced_result
    
    def run_all_tests(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """运行所有测试"""
        all_results = []
        
        for test_case in test_cases:
            print(f"\n测试: {test_case.name}")
            print(f"  场景: {test_case.notes}")
            
            simple_result, enhanced_result = self.run_test(test_case)
            all_results.extend([simple_result, enhanced_result])
            
            print(f"  简单版: P={simple_result.precision:.2f}, R={simple_result.recall:.2f}, F1={simple_result.f1_score:.2f}")
            print(f"  增强版: P={enhanced_result.precision:.2f}, R={enhanced_result.recall:.2f}, F1={enhanced_result.f1_score:.2f}")
        
        # 汇总统计
        return self._aggregate_results(all_results)
    
    def _aggregate_results(self, results: List[TestResult]) -> Dict[str, Any]:
        """汇总结果"""
        simple_results = [r for r in results if r.version == "simple"]
        enhanced_results = [r for r in results if r.version == "enhanced"]
        
        def avg_metrics(results_list):
            if not results_list:
                return {"precision": 0, "recall": 0, "f1": 0}
            return {
                "precision": sum(r.precision for r in results_list) / len(results_list),
                "recall": sum(r.recall for r in results_list) / len(results_list),
                "f1": sum(r.f1_score for r in results_list) / len(results_list)
            }
        
        return {
            "simple_avg": avg_metrics(simple_results),
            "enhanced_avg": avg_metrics(enhanced_results),
            "detailed_results": [
                {
                    "test": r.test_name,
                    "version": r.version,
                    "precision": r.precision,
                    "recall": r.recall,
                    "f1": r.f1_score,
                    "selected": r.selected_files,
                    "expected": r.expected_files
                }
                for r in results
            ]
        }


# ============ 测试用例定义 ============

def create_test_cases() -> List[TestCase]:
    """创建测试用例集合"""
    
    test_cases = []
    
    # 测试1: Bug修复场景
    test_cases.append(TestCase(
        name="Bug修复-认证失败",
        task_description="fix authentication failure when user login",
        task_type="debug",
        available_files=[
            "src/auth/service.py",
            "src/auth/models.py",
            "src/api/login.py",
            "tests/test_auth.py",
            "logs/error.log",
            "docs/auth.md",
            "config/settings.py",
            "src/utils/helpers.py"
        ],
        file_contents={
            "src/auth/service.py": "def authenticate(): pass",
            "src/auth/models.py": "class User: pass",
            "src/api/login.py": "def login_endpoint(): pass",
            "tests/test_auth.py": "def test_login(): pass",
            "logs/error.log": "ERROR: Authentication failed for user",
            "docs/auth.md": "Authentication documentation",
            "config/settings.py": "DEBUG = True",
            "src/utils/helpers.py": "def helper(): pass"
        },
        expected_files=[
            "src/auth/service.py",
            "src/auth/models.py",
            "logs/error.log",
            "tests/test_auth.py"
        ],
        notes="Debug认证失败，需要看服务代码、模型、错误日志和测试"
    ))
    
    # 测试2: 功能实现场景
    test_cases.append(TestCase(
        name="功能实现-添加用户注册",
        task_description="implement user registration endpoint",
        task_type="implement",
        available_files=[
            "src/api/routes.py",
            "src/models/user.py",
            "src/services/auth.py",
            "src/db/repository.py",
            "tests/test_user.py",
            "docs/api.md",
            "config/database.yml"
        ],
        file_contents={
            "src/api/routes.py": "@app.route('/register')",
            "src/models/user.py": "class User: def save(self): pass",
            "src/services/auth.py": "class AuthService: pass",
            "src/db/repository.py": "class UserRepository: pass",
            "tests/test_user.py": "def test_register(): pass",
            "docs/api.md": "API documentation for registration",
            "config/database.yml": "database: url"
        },
        expected_files=[
            "src/api/routes.py",
            "src/models/user.py",
            "src/services/auth.py",
            "docs/api.md"
        ],
        notes="实现注册功能，需要API路由、模型、服务代码和文档"
    ))
    
    # 测试3: 性能优化场景
    test_cases.append(TestCase(
        name="性能优化-数据库查询",
        task_description="optimize slow database query in user search",
        task_type="optimize",
        available_files=[
            "src/db/query.py",
            "src/db/connection.py",
            "src/models/user.py",
            "src/services/search.py",
            "config/database.yml",
            "logs/performance.log",
            "tests/benchmark.py"
        ],
        file_contents={
            "src/db/query.py": "def search_users(): pass",
            "src/db/connection.py": "class ConnectionPool: pass",
            "src/models/user.py": "class User: pass",
            "src/services/search.py": "class SearchService: pass",
            "config/database.yml": "pool_size: 10",
            "logs/performance.log": "Query took 5 seconds",
            "tests/benchmark.py": "def benchmark_search(): pass"
        },
        expected_files=[
            "src/db/query.py",
            "src/db/connection.py",
            "logs/performance.log",
            "config/database.yml"
        ],
        notes="优化慢查询，需要看查询代码、连接池配置和性能日志"
    ))
    
    # 测试4: 代码审查场景
    test_cases.append(TestCase(
        name="代码审查-新功能PR",
        task_description="review pull request for new payment feature",
        task_type="review",
        available_files=[
            "src/payment/service.py",
            "src/payment/models.py",
            "src/api/payment.py",
            "tests/test_payment.py",
            "docs/payment.md",
            "src/utils/validators.py",
            "requirements.txt"
        ],
        file_contents={
            "src/payment/service.py": "class PaymentService: pass",
            "src/payment/models.py": "class Payment: pass",
            "src/api/payment.py": "def process_payment(): pass",
            "tests/test_payment.py": "def test_payment(): pass",
            "docs/payment.md": "Payment integration guide",
            "src/utils/validators.py": "def validate_amount(): pass",
            "requirements.txt": "stripe==2.0"
        },
        expected_files=[
            "src/payment/service.py",
            "src/payment/models.py",
            "src/api/payment.py",
            "tests/test_payment.py"
        ],
        notes="审查支付功能PR，需要看实现代码和测试"
    ))
    
    # 测试5: 文档编写场景
    test_cases.append(TestCase(
        name="文档编写-API文档",
        task_description="write API documentation for user endpoints",
        task_type="document",
        available_files=[
            "src/api/users.py",
            "src/api/auth.py",
            "docs/README.md",
            "docs/api_template.md",
            "tests/test_api.py",
            "src/models/user.py"
        ],
        file_contents={
            "src/api/users.py": "@app.route('/users')",
            "src/api/auth.py": "@app.route('/login')",
            "docs/README.md": "Project overview",
            "docs/api_template.md": "API doc template",
            "tests/test_api.py": "def test_users(): pass",
            "src/models/user.py": "class User: pass"
        },
        expected_files=[
            "src/api/users.py",
            "docs/api_template.md",
            "src/api/auth.py"
        ],
        notes="编写API文档，需要看端点实现和文档模板"
    ))
    
    # 测试6: 文件名模糊匹配
    test_cases.append(TestCase(
        name="文件名模糊匹配-用户相关",
        task_description="fix user profile update issue",
        task_type="debug",
        available_files=[
            "src/user/profile.py",
            "src/user/settings.py",
            "src/auth/login.py",
            "tests/test_profile.py",
            "docs/user_guide.md",
            "frontend/profile.js"
        ],
        file_contents={
            "src/user/profile.py": "def update_profile(): pass",
            "src/user/settings.py": "def update_settings(): pass",
            "src/auth/login.py": "def login(): pass",
            "tests/test_profile.py": "def test_update(): pass",
            "docs/user_guide.md": "User guide",
            "frontend/profile.js": "function updateProfile() {}"
        },
        expected_files=[
            "src/user/profile.py",
            "tests/test_profile.py",
            "frontend/profile.js"
        ],
        notes="文件名关键词匹配场景，'user'、'profile'应该被识别"
    ))
    
    # 测试7: 语义理解（非字面匹配）
    test_cases.append(TestCase(
        name="语义理解-错误处理",
        task_description="investigate error handling in payment processing",
        task_type="debug",
        available_files=[
            "src/payment/service.py",
            "src/payment/exceptions.py",
            "src/utils/logger.py",
            "logs/payment.log",
            "tests/test_payment.py",
            "docs/error_codes.md"
        ],
        file_contents={
            "src/payment/service.py": "def process_payment(): raise PaymentError()",
            "src/payment/exceptions.py": "class PaymentError(Exception): pass",
            "src/utils/logger.py": "def log_error(): pass",
            "logs/payment.log": "ERROR: Payment failed with code 500",
            "tests/test_payment.py": "def test_error_handling(): pass",
            "docs/error_codes.md": "Error code documentation"
        },
        expected_files=[
            "src/payment/service.py",
            "src/payment/exceptions.py",
            "logs/payment.log"
        ],
        notes="语义理解测试：'error handling' 应该匹配 'exceptions.py' 和 'error_codes.md'"
    ))
    
    return test_cases


def print_report(results: Dict[str, Any]):
    """打印评估报告"""
    print("\n" + "=" * 70)
    print("Fresh Eyes 效果评估报告")
    print("=" * 70)
    
    simple = results["simple_avg"]
    enhanced = results["enhanced_avg"]
    
    print("\n【整体表现】")
    print(f"{'指标':<15} {'简单版':<15} {'增强版':<15} {'提升':<15}")
    print("-" * 60)
    print(f"{'精确率':<15} {simple['precision']:.3f}{'':<11} {enhanced['precision']:.3f}{'':<11} {(enhanced['precision']-simple['precision']):+.3f}")
    print(f"{'召回率':<15} {simple['recall']:.3f}{'':<11} {enhanced['recall']:.3f}{'':<11} {(enhanced['recall']-simple['recall']):+.3f}")
    print(f"{'F1分数':<15} {simple['f1']:.3f}{'':<11} {enhanced['f1']:.3f}{'':<11} {(enhanced['f1']-simple['f1']):+.3f}")
    
    print("\n【详细结果】")
    current_test = None
    for r in results["detailed_results"]:
        if r["test"] != current_test:
            current_test = r["test"]
            print(f"\n  {current_test}:")
        print(f"    {r['version']:<10} P={r['precision']:.2f} R={r['recall']:.2f} F1={r.get('f1', r.get('f1_score', 0)):.2f}")
        print(f"      选中: {r['selected']}")
        print(f"      期望: {r['expected']}")
    
    print("\n【结论】")
    f1_diff = enhanced["f1"] - simple["f1"]
    if f1_diff > 0.1:
        print(f"✅ 增强版显著优于简单版 (F1提升 {f1_diff:+.3f})")
        print("   建议：使用增强版作为默认")
    elif f1_diff > 0.05:
        print(f"⚠️ 增强版略优于简单版 (F1提升 {f1_diff:+.3f})")
        print("   建议：根据场景选择，复杂任务用增强版")
    elif f1_diff > -0.05:
        print(f"ℹ️ 两者表现相近 (F1差异 {f1_diff:+.3f})")
        print("   建议：使用简单版（更快）")
    else:
        print(f"❌ 增强版不如简单版 (F1下降 {f1_diff:+.3f})")
        print("   建议：检查增强版实现，或回退到简单版")
    
    print("\n" + "=" * 70)


def main():
    """运行评估"""
    print("\n" + "=" * 70)
    print("Fresh Eyes 效果评估")
    print("=" * 70)
    print("\n评估指标说明:")
    print("  精确率 (Precision): 选中的文件中多少是期望的")
    print("  召回率 (Recall): 期望的文件中多少被选中了")
    print("  F1分数: 精确率和召回率的调和平均")
    print()
    
    # 创建测试用例
    test_cases = create_test_cases()
    print(f"测试用例数: {len(test_cases)}")
    
    # 运行评估
    evaluator = FreshEyesEvaluator()
    results = evaluator.run_all_tests(test_cases)
    
    # 打印报告
    print_report(results)
    
    # 保存详细结果
    with open("fresh_eyes_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n详细结果已保存到: fresh_eyes_evaluation.json")


if __name__ == "__main__":
    main()
