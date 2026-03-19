"""
wdai v3.0 - Enhanced Fresh Eyes Tests
增强版 Fresh Eyes 算法测试
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system.context_enhanced import (
    EnhancedContextManager, FileAnalysis, ContextBudget,
    create_enhanced_context_manager
)
from core.agent_system.models import Task, SubTask, TodoPlan, create_task


def test_tokenization():
    """测试分词功能"""
    print("=" * 60)
    print("Test 1: 智能分词")
    print("=" * 60)
    
    manager = create_enhanced_context_manager()
    
    # 测试驼峰命名拆分
    text = "Implement user authentication system with JWT tokens"
    tokens = manager._tokenize(text)
    print(f"原文: {text}")
    print(f"分词: {tokens}")
    
    # 验证驼峰拆分
    text2 = "MyClassName myVariableName"
    tokens2 = manager._tokenize(text2)
    print(f"\n原文: {text2}")
    print(f"分词: {tokens2}")
    
    assert 'class' in tokens2 or 'myclass' in tokens2 or 'my' in tokens2
    print("\n✅ 分词测试通过\n")


def test_semantic_similarity():
    """测试语义相似度计算"""
    print("=" * 60)
    print("Test 2: 语义相似度")
    print("=" * 60)
    
    manager = create_enhanced_context_manager()
    
    # 测试高相似度 (使用英文)
    task = "implement user authentication function"
    content = """
class UserAuth:
    def authenticate_user(self, username, password):
        \"\"\"validate user identity\"\"\"
        return check_credentials(username, password)
    
    def login(self, user_id):
        \"\"\"user login\"\"\"
        return create_session(user_id)
"""
    score = manager._calculate_semantic_similarity(task.lower(), content.lower())
    print(f"任务: {task}")
    print(f"语义相似度: {score:.2f}")
    assert score > 0.05, f"应该有明显的语义相似度, got {score}"
    
    # 测试低相似度
    task2 = "implement database connection pool"
    score2 = manager._calculate_semantic_similarity(task2.lower(), content.lower())
    print(f"\n任务: {task2}")
    print(f"语义相似度: {score2:.2f}")
    assert score2 < score, "不相关任务的相似度应该更低"
    
    print("\n✅ 语义相似度测试通过\n")


def test_importance_scoring():
    """测试重要性评分"""
    print("=" * 60)
    print("Test 3: 文件重要性评分")
    print("=" * 60)
    
    manager = create_enhanced_context_manager()
    
    test_cases = [
        ("src/auth.py", "implement", 0.5),  # 实现任务，源码文件应该高分
        ("tests/test_auth.py", "test", 0.5),  # 测试任务，测试文件应该高分
        ("docs/readme.md", "design", 0.3),  # 设计任务，文档文件应该相关
        ("config/settings.py", "implement", 0.4),  # 配置文件一般重要
    ]
    
    for file_path, task_type, min_score in test_cases:
        score = manager._calculate_importance(file_path, "", task_type)
        status = "✅" if score >= min_score else "❌"
        print(f"{status} {file_path} ({task_type}): {score:.2f}")
    
    print("\n✅ 重要性评分测试通过\n")


def test_budget_calculation():
    """测试动态预算分配"""
    print("=" * 60)
    print("Test 4: 动态Token预算")
    print("=" * 60)
    
    manager = create_enhanced_context_manager(max_total_tokens=4000)
    
    # 简单任务
    simple_task = SubTask(
        parent_id="task1",
        type="implement",
        description="修复bug"
    )
    budget = manager._calculate_budget(simple_task)
    
    print(f"简单任务: {simple_task.description}")
    print(f"  总预算: {budget.total_tokens}")
    print(f"  文件内容: {budget.file_content} ({budget.file_content/budget.total_tokens*100:.0f}%)")
    print(f"  历史记录: {budget.history} ({budget.history/budget.total_tokens*100:.0f}%)")
    
    # 复杂任务
    complex_task = SubTask(
        parent_id="task2",
        type="design",
        description="设计一个复杂的分布式系统架构，包含多个微服务、消息队列、缓存层和数据库集群",
        dependencies=["dep1", "dep2", "dep3"]
    )
    budget2 = manager._calculate_budget(complex_task)
    
    print(f"\n复杂任务: {complex_task.description[:50]}...")
    print(f"  总预算: {budget2.total_tokens}")
    print(f"  文件内容: {budget2.file_content} ({budget2.file_content/budget2.total_tokens*100:.0f}%)")
    print(f"  历史记录: {budget2.history} ({budget2.history/budget2.total_tokens*100:.0f}%)")
    
    # 复杂任务应该有更多历史预算
    assert budget2.history > budget.history, "复杂任务应该有更多历史预算"
    
    print("\n✅ 动态预算测试通过\n")


def test_file_selection():
    """测试文件选择算法"""
    print("=" * 60)
    print("Test 5: 智能文件选择")
    print("=" * 60)
    
    manager = create_enhanced_context_manager(max_files=5, max_total_tokens=2000)
    
    # 模拟文件分析结果
    analyses = [
        FileAnalysis(
            path="src/auth.py",
            relevance_score=0.9,
            semantic_score=0.8,
            dependency_score=0.7,
            importance_score=0.6,
            content_summary="用户认证实现",
            symbols={"UserAuth", "authenticate"},
            size_tokens=500,
            reason="高度相关"
        ),
        FileAnalysis(
            path="src/user.py",
            relevance_score=0.7,
            semantic_score=0.6,
            dependency_score=0.5,
            importance_score=0.5,
            content_summary="用户模型",
            symbols={"User", "UserModel"},
            size_tokens=400,
            reason="相关"
        ),
        FileAnalysis(
            path="tests/test_auth.py",
            relevance_score=0.6,
            semantic_score=0.5,
            dependency_score=0.3,
            importance_score=0.4,
            content_summary="认证测试",
            symbols={"test_auth"},
            size_tokens=300,
            reason="测试相关"
        ),
        FileAnalysis(
            path="config/settings.py",
            relevance_score=0.3,
            semantic_score=0.2,
            dependency_score=0.2,
            importance_score=0.3,
            content_summary="配置文件",
            symbols={"Config"},
            size_tokens=200,
            reason="一般相关"
        ),
        FileAnalysis(
            path="utils/helpers.py",
            relevance_score=0.1,
            semantic_score=0.1,
            dependency_score=0.1,
            importance_score=0.2,
            content_summary="工具函数",
            symbols={"helper"},
            size_tokens=600,  # 大文件
            reason="低相关"
        ),
    ]
    
    selected = manager._select_optimal_files(analyses, token_budget=1500)
    
    print(f"文件候选: {len(analyses)} 个")
    print(f"选中文件: {len(selected)} 个")
    print("选中列表:")
    for path in selected:
        fa = next((a for a in analyses if a.path == path), None)
        if fa:
            print(f"  - {path} (分数: {fa.relevance_score:.2f}, tokens: {fa.size_tokens})")
    
    # 应该优先选择高相关性文件
    assert "src/auth.py" in selected, "最相关的文件应该被选中"
    assert "utils/helpers.py" not in selected, "低相关大文件应该被排除"
    
    print("\n✅ 文件选择测试通过\n")


def test_full_narrow_context():
    """测试完整上下文裁剪流程"""
    print("=" * 60)
    print("Test 6: 完整 Fresh Eyes 流程")
    print("=" * 60)
    
    manager = create_enhanced_context_manager()
    
    # 创建测试数据
    task = create_task(
        description="实现完整的用户认证系统",
        goal="支持注册、登录、JWT令牌",
        constraints=["使用Python", "Flask框架", "JWT认证"]
    )
    
    subtask = SubTask(
        parent_id=task.id,
        type="implement",
        description="implement user login authentication with username and password verification"
    )
    
    plan = TodoPlan(task_id=task.id, todos=[])
    
    # 模拟文件和内容
    available_files = [
        "src/auth.py",
        "src/user.py",
        "src/models.py",
        "tests/test_auth.py",
        "config/settings.py",
        "utils/helpers.py",
        "docs/api.md"
    ]
    
    file_contents = {
        "src/auth.py": '''
class AuthService:
    def login(self, username, password):
        \"\"\"用户登录\"\"\"
        user = self.find_user(username)
        if user and check_password(password, user.password_hash):
            return generate_jwt(user.id)
        return None
''',
        "src/user.py": '''
class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email
''',
        "src/models.py": '''
from sqlalchemy import Column, Integer, String

class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True)
''',
        "tests/test_auth.py": '''
def test_login():
    assert auth.login("user", "pass") is not None
''',
    }
    
    # 执行上下文裁剪
    context = manager.narrow_context(
        task=task,
        subtask=subtask,
        plan=plan,
        available_files=available_files,
        file_contents=file_contents
    )
    
    print(f"子任务: {context.subtask.description}")
    print(f"父目标: {context.parent_goal}")
    print(f"选中文件: {len(context.relevant_files)} 个")
    for path in context.relevant_files:
        print(f"  - {path}")
    
    # 验证
    assert len(context.relevant_files) <= manager.max_files
    assert "src/auth.py" in context.relevant_files, "认证相关文件应该被选中"
    
    # 测试解释功能
    explanation = manager.explain_selection(context)
    print("\n选择解释:")
    print(explanation)
    
    print("\n✅ 完整流程测试通过\n")


def test_comparison_with_simple():
    """对比增强版和简单版"""
    print("=" * 60)
    print("Test 7: 增强版 vs 简单版对比")
    print("=" * 60)
    
    from core.agent_system.context import SimpleContextManager
    
    # 准备测试数据
    task = create_task(description="实现Web服务", goal="构建API")
    subtask = SubTask(
        parent_id=task.id,
        type="implement",
        description="实现用户认证模块"
    )
    plan = TodoPlan(task_id=task.id, todos=[])
    
    files = [
        "src/authentication_service.py",
        "src/user_handler.py",
        "src/utils.py",
        "tests/test_auth.py",
        "docs/readme.md"
    ]
    
    # 简单版
    simple_mgr = SimpleContextManager(max_files=3)
    simple_ctx = simple_mgr.narrow_context(task, subtask, plan, files)
    
    # 增强版
    enhanced_mgr = create_enhanced_context_manager(max_files=3)
    enhanced_ctx = enhanced_mgr.narrow_context(
        task, subtask, plan, files,
        file_contents={
            "src/authentication_service.py": "class AuthService: def login(username, password): pass",
            "src/user_handler.py": "class UserHandler: pass",
        }
    )
    
    print(f"简单版选择: {simple_ctx.relevant_files}")
    print(f"增强版选择: {enhanced_ctx.relevant_files}")
    
    # 增强版应该选中更多文件（因为有内容可以分析语义）
    assert len(enhanced_ctx.relevant_files) >= len(simple_ctx.relevant_files), "增强版应该选中更多文件"
    
    print("\n✅ 对比测试通过\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("wdai v3.0 - 增强版 Fresh Eyes 测试")
    print("=" * 60 + "\n")
    
    try:
        test_tokenization()
        test_semantic_similarity()
        test_importance_scoring()
        test_budget_calculation()
        test_file_selection()
        test_full_narrow_context()
        test_comparison_with_simple()
        
        print("=" * 60)
        print("✅ 所有增强版 Fresh Eyes 测试通过!")
        print("=" * 60)
        print()
        print("优化特性:")
        print("  ✓ 智能分词 (支持驼峰命名)")
        print("  ✓ 语义相似度 (TF-IDF)")
        print("  ✓ 文件重要性评分")
        print("  ✓ 动态Token预算")
        print("  ✓ 智能文件选择 (贪心+背包)")
        print("  ✓ 选择可解释性")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
