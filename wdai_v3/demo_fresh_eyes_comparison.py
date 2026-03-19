"""
wdai v3.0 - Fresh Eyes 综合对比演示
比较三种算法：简单版、TF-IDF增强版、Embedding版
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system.models import Task, SubTask, TodoPlan, create_task
from core.agent_system.context import SimpleContextManager
from core.agent_system.context_enhanced import EnhancedContextManager
from core.agent_system.context_embedding import create_embedding_context_manager


def demo_comprehensive_comparison():
    """综合对比三种算法"""
    print("=" * 75)
    print("wdai v3.0 - Fresh Eyes 三版本综合对比")
    print("=" * 75)
    print()
    
    # 场景1: 语义理解能力
    print("【场景1: 语义理解能力测试】")
    print("-" * 75)
    print()
    
    scenarios = [
        {
            "name": "Bug修复",
            "task": "fix critical bug in user authentication",
            "files": [
                ("src/auth/authentication.py", "def authenticate(): pass"),
                ("src/utils/logger.py", "def log_error(): pass"),
                ("logs/error.log", "ERROR: auth failed at line 42"),
                ("docs/api_guide.md", "API documentation"),
            ],
            "expected": ["src/auth/authentication.py", "logs/error.log"]
        },
        {
            "name": "性能优化",
            "task": "optimize database query performance",
            "files": [
                ("src/db/query_builder.py", "def build_query(): pass"),
                ("src/db/connection.py", "class ConnectionPool: pass"),
                ("src/models/user.py", "class User(Model): pass"),
                ("config/database.yml", "pool_size: 10"),
            ],
            "expected": ["src/db/query_builder.py", "src/db/connection.py"]
        },
        {
            "name": "API设计",
            "task": "design REST API endpoints for user management",
            "files": [
                ("src/api/routes.py", "@app.route('/users')"),
                ("src/schemas/user.py", "class UserSchema: pass"),
                ("docs/api_spec.md", "REST API Specification"),
                ("tests/test_api.py", "def test_user_api(): pass"),
            ],
            "expected": ["src/api/routes.py", "docs/api_spec.md"]
        }
    ]
    
    # 初始化三个管理器
    simple_mgr = SimpleContextManager(max_files=2)
    enhanced_mgr = EnhancedContextManager(max_files=2)
    embedding_mgr = create_embedding_context_manager(max_files=2)
    
    results = []
    
    for scenario in scenarios:
        print(f"场景: {scenario['name']}")
        print(f"任务: {scenario['task']}")
        print()
        
        task = create_task(description=scenario['task'], goal="test")
        subtask = SubTask(
            parent_id=task.id,
            type="implement",
            description=scenario['task']
        )
        plan = TodoPlan(task_id=task.id, todos=[])
        
        files = [f[0] for f in scenario['files']]
        file_contents = {f[0]: f[1] for f in scenario['files']}
        
        # 三个版本分别执行
        simple_ctx = simple_mgr.narrow_context(task, subtask, plan, files)
        enhanced_ctx = enhanced_mgr.narrow_context(task, subtask, plan, files, file_contents)
        embedding_ctx = embedding_mgr.narrow_context(task, subtask, plan, files, file_contents)
        
        print(f"  简单版:     {simple_ctx.relevant_files}")
        print(f"  增强版:     {enhanced_ctx.relevant_files}")
        print(f"  Embedding:  {embedding_ctx.relevant_files}")
        
        # 计算命中率
        expected = set(scenario['expected'])
        simple_hit = len(set(simple_ctx.relevant_files) & expected) / len(expected)
        enhanced_hit = len(set(enhanced_ctx.relevant_files) & expected) / len(expected)
        embedding_hit = len(set(embedding_ctx.relevant_files) & expected) / len(expected)
        
        print(f"\n  期望文件: {scenario['expected']}")
        print(f"  命中率 - 简单: {simple_hit:.0%}, 增强: {enhanced_hit:.0%}, Embedding: {embedding_hit:.0%}")
        print()
        
        results.append({
            "scenario": scenario['name'],
            "simple": simple_hit,
            "enhanced": enhanced_hit,
            "embedding": embedding_hit
        })
    
    # 汇总
    print("=" * 75)
    print("【汇总对比】")
    print("=" * 75)
    print()
    
    print(f"{'场景':<15} {'简单版':<10} {'增强版':<10} {'Embedding':<10}")
    print("-" * 45)
    
    for r in results:
        print(f"{r['scenario']:<15} {r['simple']:<10.0%} {r['enhanced']:<10.0%} {r['embedding']:<10.0%}")
    
    avg_simple = sum(r['simple'] for r in results) / len(results)
    avg_enhanced = sum(r['enhanced'] for r in results) / len(results)
    avg_embedding = sum(r['embedding'] for r in results) / len(results)
    
    print("-" * 45)
    print(f"{'平均':<15} {avg_simple:<10.0%} {avg_enhanced:<10.0%} {avg_embedding:<10.0%}")
    print()
    
    # 算法特点对比
    print("=" * 75)
    print("【算法特点对比】")
    print("=" * 75)
    print()
    
    print("| 特性 | 简单版 | 增强版(TF-IDF) | Embedding版 |")
    print("|------|--------|----------------|-------------|")
    print("| 匹配方式 | 文件名关键词 | 词频向量 | 语义向量 |")
    print("| 语义理解 | ❌ 无 | ⚠️ 有限 | ✅ 强 |")
    print("| 计算速度 | ✅ 最快 | ✅ 快 | ⚠️ 较慢 |")
    print("| 准确率 | ⚠️ 一般 | ✅ 较好 | ✅ 最好 |")
    print("| 可解释性 | ✅ 简单 | ✅ 详细 | ✅ 详细 |")
    print("| 内存占用 | ✅ 低 | ✅ 中 | ⚠️ 较高 |")
    print("| 适用场景 | 快速预览 | 生产环境 | 高精度需求 |")
    print()
    
    # 推荐
    print("=" * 75)
    print("【使用建议】")
    print("=" * 75)
    print()
    print("• 快速原型/测试: 使用简单版")
    print("• 生产环境(推荐): 使用增强版 (平衡性能与准确性)")
    print("• 高精度需求: 使用Embedding版 (需接入真实LLM API)")
    print()
    
    print("=" * 75)


if __name__ == "__main__":
    demo_comprehensive_comparison()
