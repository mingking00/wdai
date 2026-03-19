"""
结构化思维链测试

演示如何使用 StructuredCoT 和 QuickCoT
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/wdai_v3')

from core.agent_system.structured_cot import (
    StructuredCoT,
    QuickCoT,
    CoTFieldType,
    STANDARD_REASONING_TEMPLATE
)


def test_basic_structured_cot():
    """测试基础结构化思维链"""
    print("\n" + "="*70)
    print("测试1: 基础结构化思维链")
    print("="*70)
    
    # 创建结构化思维链
    cot = StructuredCoT(strict_mode=True)
    
    # 填充各个章节
    cot.fill_section(
        "🎯 任务理解",
        user_intent="优化Python代码性能",
        explicit_requirements=["分析性能瓶颈", "提供优化建议"],
        implicit_requirements=["保持代码可读性", "不要改变API"],
        constraints=["时间限制10分钟"],
        success_criteria=["找到至少1个瓶颈", "给出具体优化方案"]
    )
    
    cot.fill_section(
        "🔍 现状分析",
        available_data=["Python源代码", "测试用例"],
        key_observations=["函数有嵌套循环", "使用了列表推导"],
        potential_issues=["时间复杂度可能是O(n²)"]
    )
    
    cot.fill_section(
        "📋 执行规划",
        approach="静态代码分析",
        execution_steps=["读取代码", "分析复杂度", "生成报告"],
        verification_points=["代码可读取", "复杂度可计算"]
    )
    
    # 验证
    is_valid, errors = cot.validate()
    print(f"\n验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
    if errors:
        print(f"错误: {errors}")
    
    # 查看进度
    progress = cot.get_progress()
    print(f"\n进度:")
    print(f"  - 章节: {progress['filled_sections']}/{progress['total_sections']}")
    print(f"  - 字段: {progress['filled_fields']}/{progress['total_fields']}")
    
    # 导出JSON
    json_output = cot.export("json")
    print(f"\nJSON导出长度: {len(json_output)} 字符")
    
    return is_valid


def test_quick_cot():
    """测试快速助手"""
    print("\n" + "="*70)
    print("测试2: 快速助手 (QuickCoT)")
    print("="*70)
    
    # 使用流畅API快速创建
    cot = QuickCoT() \
        .understand(
            user_intent="部署博客到GitHub Pages",
            explicit_requirements=["自动构建", "自动部署"],
            constraints=["使用GitHub Actions", "免费额度"],
            success_criteria=["成功部署", "可访问"]
        ) \
        .analyze(
            available_data=["源代码", "GitHub仓库"],
            key_observations=["使用Hugo", "有GitHub账号"],
            potential_issues=["Token权限", "分支配置"]
        ) \
        .plan(
            approach="GitHub Actions + gh-pages分支",
            execution_steps=["配置workflow", "设置secrets", "测试部署"],
            verification_points=["workflow运行成功", "页面可访问"]
        ) \
        .decide(
            decisions=["使用peaceiris/actions-hugo", "使用GITHUB_TOKEN"],
            reasoning="社区维护，使用简单",
            confidence=90
        ) \
        .execute(
            steps_completed=["✓ 配置workflow", "✓ 设置secrets", "✓ 测试部署"],
            unexpected_findings=["需要baseURL配置"]
        ) \
        .verify(
            results_delivered=["部署完成", "可访问"],
            criteria_met=["✓ 自动构建", "✓ 自动部署"],
            overall_quality=95
        ) \
        .reflect(
            key_learnings=["GitHub Actions配置有缓存机制"],
            reusable_patterns=["gh-pages分支模式"]
        ) \
        .build()
    
    # 打印摘要
    cot.print_summary()
    
    # 导出Markdown
    md_output = cot.export("markdown")
    print(f"\n📝 Markdown预览 (前800字符):")
    print(md_output[:800] + "...")
    
    return cot.is_complete()


def test_validation():
    """测试验证功能"""
    print("\n" + "="*70)
    print("测试3: 验证功能")
    print("="*70)
    
    # 创建不完整的思维链（应该验证失败）
    cot = StructuredCoT(strict_mode=True)
    
    # 只填一部分
    cot.fill_section(
        "🎯 任务理解",
        user_intent="测试",
        # 故意不填必填的 success_criteria
        explicit_requirements=["测试"]
    )
    
    # 验证
    is_valid, errors = cot.validate()
    
    print(f"\n验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
    if errors:
        print(f"发现 {len(errors)} 个错误:")
        for i, error in enumerate(errors[:3], 1):
            print(f"  {i}. {error}")
    
    return not is_valid  # 期望验证失败


def test_custom_template():
    """测试自定义模板"""
    print("\n" + "="*70)
    print("测试4: 自定义模板")
    print("="*70)
    
    from core.agent_system.structured_cot import CoTSection, CoTField
    
    # 创建简化模板
    simple_template = {
        "sections": [
            CoTSection(
                order=1,
                title="📌 目标",
                description="明确要做什么",
                fields=[
                    CoTField("what", "做什么", CoTFieldType.TEXT),
                    CoTField("why", "为什么", CoTFieldType.TEXT),
                ]
            ),
            CoTSection(
                order=2,
                title="✅ 结果",
                description="做得怎么样",
                fields=[
                    CoTField("outcome", "结果", CoTFieldType.TEXT),
                    CoTField("score", "评分", CoTFieldType.CONFIDENCE),
                ]
            ),
        ]
    }
    
    cot = StructuredCoT(template=simple_template)
    
    cot.fill_section("📌 目标", what="学习Rust", why="需要高性能")
    cot.fill_section("✅ 结果", outcome="完成了基础语法", score=85)
    
    is_valid, errors = cot.validate()
    print(f"\n验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
    print(f"完成度: {cot.get_progress()['field_progress']*100:.0f}%")
    
    return is_valid


def test_markdown_export():
    """测试Markdown导出"""
    print("\n" + "="*70)
    print("测试5: Markdown导出")
    print("="*70)
    
    cot = QuickCoT() \
        .understand(
            user_intent="实现用户登录功能",
            explicit_requirements=["支持邮箱登录", "支持密码重置"],
            success_criteria=["用户可登录", "密码可重置"]
        ) \
        .analyze(
            available_data=["用户表", "邮件服务"],
            key_observations=["需要JWT", "需要加密"]
        ) \
        .plan(
            approach="JWT + bcrypt",
            execution_steps=["设计API", "实现认证", "添加中间件"]
        ) \
        .build()
    
    md = cot.export("markdown")
    
    # 保存到文件
    output_file = "/tmp/wdai_structured_cot.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md)
    
    print(f"\n💾 Markdown已保存到: {output_file}")
    print(f"📄 文件大小: {len(md)} 字符")
    
    # 显示部分内容
    print("\n预览:")
    lines = md.split('\n')
    for line in lines[:30]:
        print(line)
    if len(lines) > 30:
        print("...")
    
    return True


def test_comparison_with_unstructured():
    """对比：结构化 vs 非结构化"""
    print("\n" + "="*70)
    print("测试6: 结构化 vs 非结构化 对比")
    print("="*70)
    
    print("\n❌ 非结构化推理（黑盒）:")
    print("  用户：分析这个函数")
    print("  AI：好的，让我分析一下...")
    print("  [黑盒处理...]")
    print("  AI：分析完成，发现3个问题")
    print("  → 你不知道：分析了什么？怎么分析的？依据是什么？")
    
    print("\n✅ 结构化推理（透明）:")
    
    cot = QuickCoT() \
        .understand(
            user_intent="分析函数性能",
            explicit_requirements=["找出瓶颈"]
        ) \
        .analyze(
            available_data=["源代码"],
            key_observations=["O(n²)复杂度"]
        ) \
        .decide(
            decisions=["使用哈希表优化"],
            reasoning="可将O(n²)降至O(n)",
            confidence=90
        ) \
        .build()
    
    print(f"  用户：分析这个函数")
    print(f"  AI：")
    for section in cot.sections[:4]:  # 只显示前4个
        print(f"    {section.title}")
        section_data = cot.data.get(section.title, {})
        for field in section.fields[:2]:  # 每节只显示前2个字段
            value = section_data.get(field.name)
            if value:
                if isinstance(value, list):
                    value = value[0] if value else "..."
                preview = str(value)[:40]
                print(f"      - {field.name}: {preview}...")
    print("  → 每一步都有记录，可追溯、可验证")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("结构化思维链 (Structured CoT) 测试套件")
    print("="*70)
    
    results = []
    
    tests = [
        ("基础结构化思维链", test_basic_structured_cot),
        ("快速助手 (QuickCoT)", test_quick_cot),
        ("验证功能", test_validation),
        ("自定义模板", test_custom_template),
        ("Markdown导出", test_markdown_export),
        ("结构化 vs 非结构化", test_comparison_with_unstructured),
    ]
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            print(f"\n✅ {name}: {'通过' if result else '失败'}")
        except Exception as e:
            print(f"\n❌ {name}: 异常 - {e}")
            results.append((name, False))
    
    # 汇总
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.0f}%)")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
