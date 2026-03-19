"""
wdai v3.0 - 代码依赖图 + Fresh Eyes 集成演示

展示如何使用代码依赖分析增强上下文裁剪
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system.dependency_analyzer import (
    build_dependency_graph,
    DependencyAwareFreshEyes
)
from core.agent_system.models import Task, SubTask, TodoPlan, create_task
from core.agent_system.context_enhanced import create_enhanced_context_manager


def demo_dependency_aware_fresh_eyes():
    """演示依赖感知的Fresh Eyes"""
    print("=" * 70)
    print("代码依赖图 + Fresh Eyes 集成演示")
    print("=" * 70)
    print()
    
    # 模拟一个真实项目的文件结构
    project_files = {
        # 核心模块（被多处依赖）
        "src/core/config.py": '''
"""全局配置"""
DATABASE_URL = "sqlite:///app.db"
DEBUG = False
''',
        "src/core/exceptions.py": '''
"""自定义异常"""
class AppError(Exception):
    pass

class ValidationError(AppError):
    pass
''',
        
        # 模型层
        "src/models/user.py": '''
from core.config import DATABASE_URL
from core.exceptions import ValidationError

class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def validate(self):
        if not self.email:
            raise ValidationError("Email required")
''',
        "src/models/post.py": '''
from models.user import User
from core.config import DATABASE_URL

class Post:
    def __init__(self, title, content, author: User):
        self.title = title
        self.content = content
        self.author = author
''',
        
        # 服务层
        "src/services/auth_service.py": '''
from models.user import User
from core.exceptions import ValidationError

class AuthService:
    def login(self, email, password):
        user = User.find_by_email(email)
        if not user:
            raise ValidationError("User not found")
        return user
    
    def register(self, name, email, password):
        user = User(name, email)
        user.validate()
        return user.save()
''',
        "src/services/post_service.py": '''
from models.post import Post
from models.user import User
from services.auth_service import AuthService

class PostService:
    def create_post(self, user_id, title, content):
        user = AuthService().get_user(user_id)
        post = Post(title, content, user)
        return post.save()
''',
        
        # API层
        "src/api/auth_api.py": '''
from services.auth_service import AuthService
from flask import request

auth_service = AuthService()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    return auth_service.login(data['email'], data['password'])
''',
        "src/api/post_api.py": '''
from services.post_service import PostService
from services.auth_service import AuthService
from flask import request

post_service = PostService()

@app.route('/posts', methods=['POST'])
def create_post():
    user = AuthService().get_current_user()
    return post_service.create_post(user.id, request.json)
''',
        
        # 测试
        "tests/test_user.py": '''
from models.user import User

def test_user_creation():
    user = User("Test", "test@example.com")
    assert user.name == "Test"
''',
        "tests/test_auth.py": '''
from services.auth_service import AuthService
from models.user import User

def test_login():
    auth = AuthService()
    # test code
''',
        
        # 日志文件
        "logs/error.log": '''
2024-01-15 ERROR: ValidationError in auth_service.login
2024-01-15 ERROR: Database connection failed in user.save
''',
    }
    
    print(f"项目包含 {len(project_files)} 个文件")
    print()
    
    # 1. 构建依赖图
    print("【步骤1】构建代码依赖图...")
    graph = build_dependency_graph(project_files)
    print(f"✅ 依赖图构建完成: {len(graph._nodes)} 个节点")
    print()
    
    # 2. 展示依赖图
    print("【步骤2】核心文件分析...")
    print("-" * 70)
    
    # 按中心性排序
    sorted_files = sorted(
        graph._nodes.keys(),
        key=lambda x: len(graph.get_dependents(x)),
        reverse=True
    )
    
    print("\n文件中心性排名 (被依赖最多的文件):")
    for i, file_path in enumerate(sorted_files[:5], 1):
        deps = len(graph.get_dependencies(file_path))
        dependents = len(graph.get_dependents(file_path))
        centrality = graph.get_centrality(file_path)
        
        icon = "🔴" if dependents > 3 else "🟡" if dependents > 1 else "🟢"
        print(f"{i}. {icon} {file_path}")
        print(f"   依赖 {deps} 个文件, 被 {dependents} 个文件依赖 (中心性: {centrality:.2f})")
        
        # 显示依赖的文件
        if dependents > 0:
            dependent_list = list(graph.get_dependents(file_path))[:3]
            print(f"   ← 被: {', '.join(dependent_list)}")
    
    print()
    
    # 3. 影响分析
    print("【步骤3】影响分析...")
    print("-" * 70)
    
    # 假设我们要修改 user.py
    changed_files = ["src/models/user.py"]
    impact = graph.get_impact_analysis(changed_files)
    
    print(f"\n如果修改 {' '.join(changed_files)}:")
    print(f"  直接影响: {len(impact['directly_affected'])} 个文件")
    for f in impact['directly_affected'][:5]:
        print(f"    - {f}")
    
    print(f"\n  需要重新运行的测试:")
    tests_to_run = [f for f in impact['directly_affected'] if 'test' in f]
    for t in tests_to_run:
        print(f"    - {t}")
    
    print()
    
    # 4. Fresh Eyes 集成
    print("【步骤4】依赖感知的 Fresh Eyes...")
    print("-" * 70)
    
    # 创建任务
    task = create_task(
        description="修复用户认证Bug",
        goal="解决用户登录失败的问题"
    )
    
    subtask = SubTask(
        parent_id=task.id,
        type="debug",
        description="investigate why user login is failing with ValidationError"
    )
    
    plan = TodoPlan(task_id=task.id, todos=[])
    
    # 普通 Fresh Eyes（仅语义分析）
    print("\n普通 Fresh Eyes (仅语义分析):")
    context_mgr = create_enhanced_context_manager(max_files=5)
    
    # 手动设置文件内容用于语义分析
    context_mgr._file_contents = project_files
    
    normal_context = context_mgr.narrow_context(
        task=task,
        subtask=subtask,
        plan=plan,
        available_files=list(project_files.keys()),
        file_contents=project_files
    )
    
    print(f"  选中: {normal_context.relevant_files}")
    
    # 依赖感知的 Fresh Eyes
    print("\n依赖感知的 Fresh Eyes (语义 + 依赖):")
    enhancer = DependencyAwareFreshEyes(None, graph)
    
    # 先获取语义选择，然后添加依赖
    enhanced_files = enhancer.enhance_context_selection(
        normal_context.relevant_files,
        project_files
    )
    
    print(f"  原始语义选择: {normal_context.relevant_files}")
    print(f"  增强后选择: {enhanced_files}")
    
    # 新增的依赖文件
    added = set(enhanced_files) - set(normal_context.relevant_files)
    if added:
        print(f"  ✅ 自动添加的关键依赖: {list(added)}")
    else:
        print(f"  ℹ️ 语义选择已覆盖关键依赖")
    
    print()
    
    # 5. 循环依赖检测
    print("【步骤5】代码质量检查...")
    print("-" * 70)
    
    cycles = graph._detect_cycles()
    if cycles:
        print(f"⚠️ 检测到 {len(cycles)} 个循环依赖:")
        for cycle in cycles:
            print(f"  {' -> '.join(cycle)}")
    else:
        print("✅ 未发现循环依赖")
    
    modularity = graph.get_modularity_score()
    print(f"\n模块化评分: {modularity:.2f} (1.0 = 最佳)")
    
    print()
    
    # 6. 使用建议
    print("【步骤6】使用建议...")
    print("-" * 70)
    
    # 找出关键路径
    critical_files = [
        f for f in graph._nodes.keys()
        if len(graph.get_dependents(f)) > 3
    ]
    
    if critical_files:
        print("\n🔴 关键文件 (被多处依赖，修改需谨慎):")
        for f in critical_files:
            print(f"  - {f}")
            print(f"    被 {len(graph.get_dependents(f))} 个文件依赖")
    
    # 建议的测试策略
    print("\n🧪 建议的测试策略:")
    print("  1. 修改核心模块 (config, exceptions) 后运行全部测试")
    print("  2. 修改服务层后运行相关API测试")
    print("  3. 使用影响分析自动选择需要运行的测试")
    
    print()
    print("=" * 70)
    print("演示完成!")
    print("=" * 70)


if __name__ == "__main__":
    demo_dependency_aware_fresh_eyes()
