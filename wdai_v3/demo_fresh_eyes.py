"""
wdai v3.0 - Fresh Eyes Demo
增强版 Fresh Eyes 算法演示

对比原始版 vs 增强版
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system.models import Task, SubTask, TodoPlan, create_task
from core.agent_system.context import SimpleContextManager
from core.agent_system.context_enhanced import EnhancedContextManager


def demo_fresh_eyes():
    """演示 Fresh Eyes 上下文裁剪"""
    print("=" * 70)
    print("wdai v3.0 - Fresh Eyes 上下文裁剪演示")
    print("=" * 70)
    print()
    
    # 创建测试场景
    task = create_task(
        description="修复用户登录认证系统的安全漏洞",
        goal="增强系统安全性",
        constraints=["使用安全的密码哈希", "防止SQL注入", "添加速率限制"]
    )
    
    subtask = SubTask(
        parent_id=task.id,
        type="debug",
        description="investigate and fix authentication security vulnerabilities in login system"
    )
    
    plan = TodoPlan(task_id=task.id, todos=[])
    
    # 模拟项目文件
    available_files = [
        # 核心文件
        "src/auth/authentication_service.py",
        "src/auth/password_hasher.py",
        "src/auth/session_manager.py",
        "src/user/user_repository.py",
        "src/user/user_model.py",
        
        # API层
        "src/api/login_endpoint.py",
        "src/api/register_endpoint.py",
        "src/api/middleware/rate_limiter.py",
        
        # 数据库
        "src/db/connection.py",
        "src/db/migrations/001_create_users.sql",
        
        # 测试
        "tests/unit/test_auth.py",
        "tests/integration/test_login_flow.py",
        
        # 配置
        "config/security.yaml",
        "config/database.yaml",
        
        # 日志
        "logs/auth.log",
        "logs/error.log",
        
        # 文档
        "docs/authentication.md",
        "docs/security_guide.md",
        
        # 工具
        "scripts/setup_db.py",
        "scripts/generate_keys.py",
    ]
    
    # 模拟文件内容
    file_contents = {
        "src/auth/authentication_service.py": '''
class AuthenticationService:
    """Handles user authentication and login"""
    
    def login(self, username, password):
        """Authenticate user with credentials"""
        user = self.user_repo.find_by_username(username)
        if user and self.verify_password(password, user.password_hash):
            return self.create_session(user)
        raise AuthenticationError("Invalid credentials")
    
    def verify_password(self, password, hash):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), hash)
''',
        "src/auth/password_hasher.py": '''
import bcrypt

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
''',
        "src/api/login_endpoint.py": '''
@app.route('/api/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()
    try:
        token = auth_service.login(data['username'], data['password'])
        return jsonify({'token': token})
    except AuthenticationError as e:
        return jsonify({'error': str(e)}), 401
''',
        "logs/error.log": '''
2024-01-15 10:23:45 ERROR: Failed login attempt for user 'admin'
2024-01-15 10:24:12 ERROR: Authentication error: Invalid credentials
2024-01-15 10:25:33 WARNING: Multiple failed login attempts from IP 192.168.1.100
''',
        "docs/authentication.md": '''
# Authentication System

## Overview
The authentication system handles user login and session management.

## Security Considerations
- Passwords are hashed using bcrypt
- Sessions expire after 24 hours
- Rate limiting prevents brute force attacks
''',
    }
    
    print(f"任务: {task.description}")
    print(f"子任务: {subtask.description}")
    print(f"可用文件: {len(available_files)} 个")
    print()
    
    # 1. 简单版 Fresh Eyes
    print("-" * 70)
    print("【简单版 Fresh Eyes】")
    print("-" * 70)
    
    simple_mgr = SimpleContextManager(max_files=5)
    simple_ctx = simple_mgr.narrow_context(task, subtask, plan, available_files)
    
    print(f"选中文件: {len(simple_ctx.relevant_files)} 个")
    for f in simple_ctx.relevant_files:
        print(f"  • {f}")
    print()
    
    # 2. 增强版 Fresh Eyes
    print("-" * 70)
    print("【增强版 Fresh Eyes】")
    print("-" * 70)
    
    enhanced_mgr = EnhancedContextManager(max_files=5, max_total_tokens=3000)
    enhanced_ctx = enhanced_mgr.narrow_context(
        task, subtask, plan, available_files, file_contents
    )
    
    # 显示选择解释
    print(enhanced_mgr.explain_selection(enhanced_ctx))
    print()
    
    # 3. 对比
    print("-" * 70)
    print("【对比分析】")
    print("-" * 70)
    
    simple_set = set(simple_ctx.relevant_files)
    enhanced_set = set(enhanced_ctx.relevant_files)
    
    print(f"简单版选中: {len(simple_set)} 个")
    print(f"增强版选中: {len(enhanced_set)} 个")
    print()
    
    # 共同选中
    common = simple_set & enhanced_set
    if common:
        print(f"共同选中 ({len(common)} 个):")
        for f in common:
            print(f"  ✓ {f}")
        print()
    
    # 增强版独有
    enhanced_only = enhanced_set - simple_set
    if enhanced_only:
        print(f"增强版独有 ({len(enhanced_only)} 个):")
        for f in enhanced_only:
            fa = enhanced_ctx._metadata.get('file_analyses', {}).get(f)
            if fa:
                print(f"  + {f} (相关性: {fa.relevance_score:.2f})")
            else:
                print(f"  + {f}")
        print()
    
    # 简单版独有
    simple_only = simple_set - enhanced_set
    if simple_only:
        print(f"简单版独有 ({len(simple_only)} 个):")
        for f in simple_only:
            print(f"  - {f}")
        print()
    
    # 总结
    print("=" * 70)
    print("【总结】")
    print("=" * 70)
    print()
    print("增强版优势:")
    print("  • 语义相似度分析 - 基于内容而非仅文件名")
    print("  • 多维度评分 - 综合考虑语义、依赖、重要性")
    print("  • 动态Token预算 - 根据任务复杂度分配资源")
    print("  • 可解释性 - 提供选择原因")
    print()
    
    if 'src/auth/authentication_service.py' in enhanced_set:
        print("✓ 增强版正确识别了认证核心文件")
    if 'logs/error.log' in enhanced_set:
        print("✓ 增强版识别了错误日志（对debug任务重要）")
    
    print()


if __name__ == "__main__":
    demo_fresh_eyes()
