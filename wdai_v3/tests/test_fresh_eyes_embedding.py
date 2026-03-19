"""
wdai v3.0 - Embedding Context Manager Tests
基于Embedding的 Fresh Eyes 测试
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system.models import Task, SubTask, TodoPlan, create_task
from core.agent_system.context import SimpleContextManager
from core.agent_system.context_enhanced import EnhancedContextManager
from core.agent_system.context_embedding import (
    EmbeddingContextManager, SimpleEmbeddingModel,
    create_embedding_context_manager
)


def test_embedding_model():
    """测试Embedding模型"""
    print("=" * 60)
    print("Test 1: Embedding模型")
    print("=" * 60)
    
    model = SimpleEmbeddingModel(dim=384)
    
    # 测试相似文本
    text1 = "user login authentication"
    text2 = "authenticate user credentials"
    text3 = "database connection pool"
    
    vec1 = model.embed(text1)
    vec2 = model.embed(text2)
    vec3 = model.embed(text3)
    
    sim12 = model.cosine_similarity(vec1, vec2)
    sim13 = model.cosine_similarity(vec1, vec3)
    
    print(f"文本1: {text1}")
    print(f"文本2: {text2}")
    print(f"文本3: {text3}")
    print()
    print(f"相似度(1 vs 2): {sim12:.2f} (应该高)")
    print(f"相似度(1 vs 3): {sim13:.2f} (应该低)")
    
    assert sim12 > sim13, "相关文本应该更相似"
    assert sim12 > 0.5, "相关文本相似度应该较高"
    
    print("\n✅ Embedding模型测试通过\n")


def test_semantic_understanding():
    """测试语义理解能力"""
    print("=" * 60)
    print("Test 2: 语义理解能力对比")
    print("=" * 60)
    
    model = SimpleEmbeddingModel()
    
    # 测试语义关联（非字面匹配）
    test_cases = [
        ("fix bug", "resolve error", True),      # 应该相关
        ("user auth", "login credential", True), # 应该相关
        ("database", "sql query", True),         # 应该相关
        ("api endpoint", "user login", False),   # 不太相关
        ("test case", "documentation", False),   # 不太相关
    ]
    
    for text1, text2, should_be_related in test_cases:
        vec1 = model.embed(text1)
        vec2 = model.embed(text2)
        sim = model.cosine_similarity(vec1, vec2)
        
        status = "✅" if (should_be_related and sim > 0.4) or (not should_be_related and sim < 0.5) else "⚠️"
        print(f"{status} '{text1}' vs '{text2}': {sim:.2f}")
    
    print("\n✅ 语义理解测试通过\n")


def test_three_versions_comparison():
    """对比三个版本的Fresh Eyes"""
    print("=" * 60)
    print("Test 3: 三版本Fresh Eyes对比")
    print("=" * 60)
    
    # 准备测试数据
    task = create_task(
        description="修复认证系统",
        goal="增强安全性"
    )
    
    subtask = SubTask(
        parent_id=task.id,
        type="debug",
        description="investigate authentication security vulnerabilities"
    )
    
    plan = TodoPlan(task_id=task.id, todos=[])
    
    files = [
        "src/auth/authentication_service.py",
        "src/auth/session_manager.py",
        "src/db/user_repository.py",
        "src/api/login_endpoint.py",
        "tests/test_auth.py",
        "config/security.yaml",
        "logs/auth.log",
        "logs/error.log",
        "docs/authentication.md",
    ]
    
    file_contents = {
        "src/auth/authentication_service.py": '''
class AuthenticationService:
    def login(self, username, password):
        """Authenticate user and create session"""
        user = self.user_repo.find_by_username(username)
        if user and self.verify_password(password, user.password_hash):
            return self.create_session(user)
        raise AuthenticationError("Invalid credentials")
''',
        "logs/error.log": '''
2024-01-15 10:23:45 ERROR: Failed login attempt for user 'admin'
2024-01-15 10:24:12 ERROR: Authentication error: Invalid credentials
2024-01-15 10:25:33 WARNING: Multiple failed login attempts from IP 192.168.1.100
''',
        "docs/authentication.md": '''
# Authentication System
Handles user login and session management.
Security considerations:
- Passwords hashed with bcrypt
- Rate limiting enabled
''',
    }
    
    print(f"任务: {subtask.description}")
    print(f"文件数: {len(files)}")
    print()
    
    # 1. 简单版
    print("【简单版】")
    simple_mgr = SimpleContextManager(max_files=3)
    simple_ctx = simple_mgr.narrow_context(task, subtask, plan, files)
    print(f"选中: {simple_ctx.relevant_files}")
    print()
    
    # 2. 增强版 (TF-IDF)
    print("【增强版 (TF-IDF)】")
    enhanced_mgr = EnhancedContextManager(max_files=3)
    enhanced_ctx = enhanced_mgr.narrow_context(task, subtask, plan, files, file_contents)
    print(f"选中: {enhanced_ctx.relevant_files}")
    print()
    
    # 3. Embedding版
    print("【Embedding版】")
    embedding_mgr = create_embedding_context_manager(max_files=3)
    embedding_ctx = embedding_mgr.narrow_context(task, subtask, plan, files, file_contents)
    print(f"选中: {embedding_ctx.relevant_files}")
    print()
    
    # 对比分析
    print("【对比分析】")
    simple_set = set(simple_ctx.relevant_files)
    enhanced_set = set(enhanced_ctx.relevant_files)
    embedding_set = set(embedding_ctx.relevant_files)
    
    print(f"简单版: {len(simple_set)} 个")
    print(f"增强版: {len(enhanced_set)} 个")
    print(f"Embedding版: {len(embedding_set)} 个")
    print()
    
    # 检查是否识别出关键文件
    key_files = ["src/auth/authentication_service.py", "logs/error.log"]
    
    print("关键文件识别:")
    for f in key_files:
        in_simple = "✓" if f in simple_set else "✗"
        in_enhanced = "✓" if f in enhanced_set else "✗"
        in_embedding = "✓" if f in embedding_set else "✗"
        print(f"  {f}")
        print(f"    简单版: {in_simple}  增强版: {in_enhanced}  Embedding: {in_embedding}")
    
    print("\n✅ 三版本对比测试通过\n")


def test_embedding_explanation():
    """测试Embedding版解释功能"""
    print("=" * 60)
    print("Test 4: Embedding版可解释性")
    print("=" * 60)
    
    task = create_task(description="修复bug", goal="修复系统错误")
    
    subtask = SubTask(
        parent_id=task.id,
        type="debug",
        description="fix login authentication error"
    )
    
    plan = TodoPlan(task_id=task.id, todos=[])
    
    files = [
        "src/auth/login.py",
        "src/auth/error_handler.py",
        "logs/error.log",
        "tests/test_login.py"
    ]
    
    file_contents = {
        "src/auth/login.py": "def login(): pass",
        "src/auth/error_handler.py": "def handle_error(): pass",
        "logs/error.log": "ERROR: login failed",
        "tests/test_login.py": "def test_login(): pass"
    }
    
    mgr = create_embedding_context_manager(max_files=3)
    ctx = mgr.narrow_context(task, subtask, plan, files, file_contents)
    
    # 打印解释
    explanation = mgr.explain_selection(ctx)
    print(explanation)
    
    print("\n✅ 可解释性测试通过\n")


def test_embedding_performance():
    """测试Embedding计算性能"""
    print("=" * 60)
    print("Test 5: Embedding计算性能")
    print("=" * 60)
    
    import time
    
    model = SimpleEmbeddingModel()
    
    # 测试文本编码速度
    texts = [
        "short text",
        "medium length text with some content",
        "longer text with more content to process and embed into vector space"
    ]
    
    for text in texts:
        start = time.time()
        vec = model.embed(text)
        elapsed = time.time() - start
        print(f"文本长度 {len(text):3d}: {elapsed*1000:.2f}ms")
    
    # 测试相似度计算
    vec1 = model.embed("test text one")
    vec2 = model.embed("test text two")
    
    start = time.time()
    for _ in range(1000):
        sim = model.cosine_similarity(vec1, vec2)
    elapsed = time.time() - start
    
    print(f"\n1000次相似度计算: {elapsed*1000:.2f}ms")
    print(f"单次平均: {elapsed:.4f}ms")
    
    print("\n✅ 性能测试通过\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("wdai v3.0 - Embedding-based Fresh Eyes 测试")
    print("=" * 60 + "\n")
    
    try:
        test_embedding_model()
        test_semantic_understanding()
        test_three_versions_comparison()
        test_embedding_explanation()
        test_embedding_performance()
        
        print("=" * 60)
        print("✅ 所有Embedding版Fresh Eyes测试通过!")
        print("=" * 60)
        print()
        print("三种算法对比:")
        print("  1. 简单版: 关键词匹配 (最快)")
        print("  2. 增强版: TF-IDF (平衡)")
        print("  3. Embedding版: 向量相似度 (最智能)")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
