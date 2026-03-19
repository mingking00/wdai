"""
批量导入 Semgrep 规则 - CLI 工具

使用示例:
    # 导入 Python 安全规则
    python3 import_semgrep_rules.py --category python/lang/security
    
    # 导入所有类别
    python3 import_semgrep_rules.py --all
    
    # 从本地文件导入
    python3 import_semgrep_rules.py --file /path/to/rules.yaml
"""

import sys
import asyncio
from pathlib import Path
from typing import List

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wdai_v3.core.security.semgrep_importer import (
    SemgrepRuleImporter,
    import_semgrep_rules,
    import_semgrep_from_file
)


async def import_category(category: str):
    """导入指定类别"""
    print(f"📥 正在导入: {category}")
    print("-" * 50)
    
    importer = SemgrepRuleImporter()
    result = await importer.import_from_github(category)
    
    print(f"✅ 导入完成!")
    print(f"   总规则: {result.total_rules}")
    print(f"   成功转换: {result.converted_rules}")
    print(f"   跳过: {result.skipped_rules}")
    print(f"   输出: {result.output_file}")
    
    if result.errors:
        print(f"\n⚠️  警告 ({len(result.errors)}):")
        for error in result.errors[:3]:
            print(f"   - {error}")
    
    print()
    return result


async def import_all():
    """导入所有可用类别"""
    importer = SemgrepRuleImporter()
    categories = importer.list_available_categories()
    
    print(f"🚀 开始批量导入 {len(categories)} 个类别")
    print("=" * 60)
    
    total_rules = 0
    total_converted = 0
    
    for category, description in categories.items():
        print(f"\n📦 {description}")
        result = await import_category(category)
        total_rules += result.total_rules
        total_converted += result.converted_rules
    
    print("=" * 60)
    print(f"🎉 批量导入完成!")
    print(f"   总计规则: {total_rules}")
    print(f"   成功转换: {total_converted}")
    print(f"   输出目录: {importer.output_dir}")


def import_local_file(file_path: Path):
    """从本地文件导入"""
    print(f"📄 导入本地文件: {file_path}")
    print("-" * 50)
    
    result = import_semgrep_from_file(file_path)
    
    print(f"✅ 导入完成!")
    print(f"   总规则: {result.total_rules}")
    print(f"   成功转换: {result.converted_rules}")
    print(f"   跳过: {result.skipped_rules}")
    print(f"   输出: {result.output_file}")
    
    if result.errors:
        print(f"\n⚠️  警告 ({len(result.errors)}):")
        for error in result.errors[:5]:
            print(f"   - {error}")


def show_categories():
    """显示可用类别"""
    importer = SemgrepRuleImporter()
    categories = importer.list_available_categories()
    
    print("📚 可用的 Semgrep 规则类别:")
    print("-" * 60)
    for category, description in categories.items():
        print(f"  {category:30s} - {description}")
    print("\n使用: --category <类别名> 导入指定类别")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='批量导入 Semgrep 规则到 wdai Security Agent'
    )
    parser.add_argument(
        '--category', '-c',
        help='导入指定类别 (如: python/lang/security)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='导入所有可用类别'
    )
    parser.add_argument(
        '--file', '-f',
        type=Path,
        help='从本地 YAML 文件导入'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出可用类别'
    )
    
    args = parser.parse_args()
    
    if args.list:
        show_categories()
    elif args.all:
        await import_all()
    elif args.category:
        await import_category(args.category)
    elif args.file:
        import_local_file(args.file)
    else:
        parser.print_help()
        print("\n示例:")
        print("  python3 import_semgrep_rules.py --list")
        print("  python3 import_semgrep_rules.py --category python/lang/security")
        print("  python3 import_semgrep_rules.py --all")


if __name__ == "__main__":
    asyncio.run(main())
