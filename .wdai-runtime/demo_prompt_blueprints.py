#!/usr/bin/env python3
"""
wdai Prompt蓝图系统演示
展示4种标准化Prompt模板的使用
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.wdai-runtime')
sys.path.insert(0, '/root/.openclaw/workspace/.knowledge')

from prompt_blueprint_loader import PromptBlueprintLoader

def demo_reflection_blueprint():
    """演示反思分析蓝图"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     🧠 Prompt蓝图 #1: 反思分析                              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    loader = PromptBlueprintLoader('/root/.openclaw/workspace/.knowledge/prompt_blueprints.json')
    
    # 获取蓝图
    bp = loader.get_blueprint('reflection')
    print(f"蓝图名称: {bp['name']}")
    print(f"用途: {bp['purpose']}")
    print()
    
    # 渲染模板（模拟一个刚完成的任务）
    print("─" * 65)
    print("📋 任务场景:")
    print("   类型: GitHub项目分析")
    print("   结果: 成功发现5个相关项目")
    print("   耗时: 2分钟")
    print("─" * 65)
    print()
    
    prompt = loader.render_blueprint(
        'reflection',
        task_type="GitHub项目分析",
        result="成功发现5个相关项目",
        duration="2分钟",
        understanding_assessment="准确理解用户需求，识别关键架构模式",
        process_review="使用API获取详情，结构化分析，生成报告",
        error_detection="无重大错误，GitHub API偶有延迟",
        improvements="可添加缓存机制减少API调用"
    )
    
    print("📝 生成的Prompt:")
    print("=" * 65)
    print(prompt)
    print("=" * 65)
    print()
    
    # 模拟输出
    print("🎯 预期输出结构:")
    print("""
{
  "insights": [
    {"type": "pattern", "content": "API调用可优化", "priority": "medium"},
    {"type": "success", "content": "分析方法有效", "priority": "high"}
  ],
  "improvements": ["添加缓存机制"],
  "success_patterns": ["结构化分析流程"]
}
    """)
    print()

def demo_evolution_blueprint():
    """演示系统进化蓝图"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     🚀 Prompt蓝图 #2: 系统进化                              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    loader = PromptBlueprintLoader('/root/.openclaw/workspace/.knowledge/prompt_blueprints.json')
    
    bp = loader.get_blueprint('evolution')
    print(f"蓝图名称: {bp['name']}")
    print(f"用途: {bp['purpose']}")
    print(f"安全检查: {', '.join(bp['safety_checks'])}")
    print()
    
    print("─" * 65)
    print("📋 进化场景:")
    print("   当前版本: v2.0")
    print("   已知问题: 自主执行缺乏安全边界")
    print("   目标: 实施三区安全架构")
    print("─" * 65)
    print()
    
    prompt = loader.render_blueprint(
        'evolution',
        current_version="v2.0",
        known_issues="自主执行缺乏安全边界，用户无法控制",
        target_dimensions="安全性、可控性、可审计性"
    )
    
    print("📝 生成的Prompt:")
    print("=" * 65)
    print(prompt)
    print("=" * 65)
    print()

def demo_conflict_resolution_blueprint():
    """演示冲突解决蓝图"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     ⚖️ Prompt蓝图 #3: 冲突解决                              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    loader = PromptBlueprintLoader('/root/.openclaw/workspace/.knowledge/prompt_blueprints.json')
    
    bp = loader.get_blueprint('conflict_resolution')
    print(f"蓝图名称: {bp['name']}")
    print(f"用途: {bp['purpose']}")
    print(f"决策标准: {', '.join(bp['decision_criteria'])}")
    print()
    
    print("─" * 65)
    print("📋 冲突场景:")
    print("   Coder Agent: 建议用 Python 重构整个系统")
    print("   Reviewer Agent: 建议保持现有架构，渐进式改进")
    print("   冲突类型: 技术路线选择")
    print("─" * 65)
    print()
    
    prompt = loader.render_blueprint(
        'conflict_resolution',
        suggestion_a="用Python重构整个系统，现代化架构",
        suggestion_b="保持现有架构，渐进式改进",
        conflict_type="技术路线选择"
    )
    
    print("📝 生成的Prompt:")
    print("=" * 65)
    print(prompt)
    print("=" * 65)
    print()
    
    # 模拟决策
    print("🎯 模拟决策过程:")
    print("""
1. 原则对比 (P2 已有能力优先):
   → 渐进式改进 胜出 (保持现有能力)
   
2. 历史胜率:
   → 渐进式改进 成功率 85%
   → 全面重构 成功率 45%
   
3. 风险权衡:
   → 渐进式改进: 低风险，可回滚
   → 全面重构: 高风险，可能引入bug
   
4. 决策输出:
   → 选择: 渐进式改进
   → 理由: 符合P2原则，历史验证，风险可控
    """)
    print()

def demo_github_learning_blueprint():
    """演示GitHub学习蓝图"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     🔍 Prompt蓝图 #4: GitHub项目学习                        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    loader = PromptBlueprintLoader('/root/.openclaw/workspace/.knowledge/prompt_blueprints.json')
    
    bp = loader.get_blueprint('github_learning')
    print(f"蓝图名称: {bp['name']}")
    print(f"用途: {bp['purpose']}")
    print(f"评估标准: {', '.join(bp['evaluation_criteria'])}")
    print()
    
    print("─" * 65)
    print("📋 学习场景:")
    print("   项目: genejr2025/circe-framework")
    print("   描述: 多Agent编排框架，循环进化")
    print("   Stars: 1")
    print("─" * 65)
    print()
    
    prompt = loader.render_blueprint(
        'github_learning',
        repo_name="genejr2025/circe-framework",
        description="Multi-Agent编排框架，循环进化，文件协议存储",
        stars="1",
        forks="0"
    )
    
    print("📝 生成的Prompt:")
    print("=" * 65)
    print(prompt)
    print("=" * 65)
    print()
    
    # 模拟分析结果
    print("🎯 模拟分析结果:")
    print("""
适用性评分: 0.8/1.0

关键洞察:
1. "循环进化"理念与wdai外循环一致
2. 文件协议存储与MEMORY.md模式匹配
3. 多Agent编排可改进现有协调机制

建议优先级: HIGH
- 参考其实现优化Agent间通信
- 借鉴循环进化设计
    """)
    print()

def show_all_blueprints():
    """显示所有可用蓝图"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     📚 Prompt蓝图库概览                                     ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    loader = PromptBlueprintLoader('/root/.openclaw/workspace/.knowledge/prompt_blueprints.json')
    blueprints = loader.list_blueprints()
    
    print(f"可用蓝图数量: {len(blueprints)}")
    print()
    
    for name in blueprints:
        bp = loader.get_blueprint(name)
        print(f"  📋 {name}")
        print(f"     名称: {bp.get('name')}")
        print(f"     用途: {bp.get('purpose')}")
        print()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Prompt蓝图演示')
    parser.add_argument('demo', nargs='?', default='all', 
                       choices=['all', 'reflection', 'evolution', 'conflict', 'github', 'list'],
                       help='选择要演示的蓝图')
    args = parser.parse_args()
    
    if args.demo == 'all':
        show_all_blueprints()
        print("\n" + "="*65 + "\n")
        
        demo_reflection_blueprint()
        print("\n" + "="*65 + "\n")
        
        demo_evolution_blueprint()
        print("\n" + "="*65 + "\n")
        
        demo_conflict_resolution_blueprint()
        print("\n" + "="*65 + "\n")
        
        demo_github_learning_blueprint()
        
    elif args.demo == 'reflection':
        demo_reflection_blueprint()
    elif args.demo == 'evolution':
        demo_evolution_blueprint()
    elif args.demo == 'conflict':
        demo_conflict_resolution_blueprint()
    elif args.demo == 'github':
        demo_github_learning_blueprint()
    elif args.demo == 'list':
        show_all_blueprints()
    
    print()
    print("="*65)
    print("✅ Prompt蓝图演示完成!")
    print("="*65)

if __name__ == '__main__':
    main()
