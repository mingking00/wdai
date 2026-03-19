"""
规则库扩展演示 - 批量导入 & 使用
展示如何扩展 wdai Security Agent 的规则库
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from wdai_v3.core.security import FastCheck, quick_security_check
from wdai_v3.core.security.semgrep_importer import SemgrepRuleImporter


# 示例 1: 使用新导入的 Semgrep 规则
print("=" * 60)
print("示例 1: 使用导入的 Semgrep 规则")
print("=" * 60)

# 从导入的规则文件创建检查器
semgrep_rules_path = Path(__file__).parent.parent / "core" / "rules" / "security" / "semgrep" / "sample_import.yml"

if semgrep_rules_path.exists():
    checker = FastCheck(rules_path=semgrep_rules_path)
    
    test_code = '''
import pickle
import os

# 危险代码
data = pickle.loads(user_input)  # 应该触发 pickle 规则
os.system(user_command)          # 应该触发 os.system 规则
'''
    
    result = checker.check(test_code)
    print(f"\n检查 {semgrep_rules_path.name} 的规则:")
    print(f"  发现问题: {len(result.findings)} 个")
    for f in result.findings:
        emoji = {"critical": "🔴", "high": "🟠"}.get(f.severity, "⚪")
        print(f"  {emoji} [{f.severity}] {f.rule_id}: {f.message}")


# 示例 2: 合并多个规则源
print("\n" + "=" * 60)
print("示例 2: 合并默认规则 + Semgrep 规则")
print("=" * 60)

# 先加载默认规则
checker = FastCheck()

# 然后添加 Semgrep 规则（如果存在）
if semgrep_rules_path.exists():
    # 重新加载包含所有规则
    import yaml
    
    # 合并规则
    all_rules = []
    
    # 添加默认规则
    for rule_data in FastCheck.DEFAULT_RULES:
        all_rules.append(rule_data)
    
    # 添加 Semgrep 规则
    with open(semgrep_rules_path, 'r') as f:
        semgrep_config = yaml.safe_load(f)
        for rule in semgrep_config.get('rules', []):
            all_rules.append({
                'id': rule['id'],
                'pattern': rule['pattern'],
                'severity': rule['severity'],
                'message': rule['message']
            })
    
    print(f"\n合并后规则总数: {len(all_rules)}")
    print(f"  - 默认规则: {len(FastCheck.DEFAULT_RULES)}")
    print(f"  - Semgrep 规则: {len(all_rules) - len(FastCheck.DEFAULT_RULES)}")


# 示例 3: 动态添加规则
print("\n" + "=" * 60)
print("示例 3: 动态添加自定义规则")
print("=" * 60)

from wdai_v3.core.security import SecurityRule

checker = FastCheck()

# 添加自定义规则
custom_rule = SecurityRule(
    rule_id="my-api-key-detection",
    pattern=r'sk-[a-zA-Z0-9]{48}',  # OpenAI API Key 格式
    severity="critical",
    message="检测到 OpenAI API Key，请使用环境变量"
)
checker.rules.append(custom_rule)

test_api_key = '''
# 配置文件
api_key = "sk-abcdefghijklmnopqrstuvwxyz1234567890ABCDEF"
'''

result = checker.check(test_api_key)
print(f"\n自定义规则检测结果:")
print(f"  发现问题: {len(result.findings)} 个")
for f in result.findings:
    print(f"  🔴 [{f.severity}] {f.message}")


# 示例 4: 展示可用的 Semgrep 类别
print("\n" + "=" * 60)
print("示例 4: 可导入的 Semgrep 规则类别")
print("=" * 60)

importer = SemgrepRuleImporter()
categories = importer.list_available_categories()

print(f"\n共有 {len(categories)} 个类别可导入:")
for category, description in categories.items():
    print(f"  • {category:30s} - {description}")


# 示例 5: 规则热重载
print("\n" + "=" * 60)
print("示例 5: 规则热重载")
print("=" * 60)

checker = FastCheck()
original_count = len(checker.rules)
print(f"\n原始规则数: {original_count}")

# 热重载（从文件）
if semgrep_rules_path.exists():
    checker.reload_rules(semgrep_rules_path)
    new_count = len(checker.rules)
    print(f"重载后规则数: {new_count}")
    print(f"新增规则: {new_count - original_count}")


# 示例 6: 完整的规则管理脚本模板
print("\n" + "=" * 60)
print("示例 6: 规则管理脚本模板")
print("=" * 60)

script_template = '''
#!/usr/bin/env python3
"""
规则管理脚本
用法: python3 manage_rules.py [command]
"""

import sys
from wdai_v3.core.security import FastCheck
from wdai_v3.core.security.semgrep_importer import SemgrepRuleImporter

def cmd_list():
    """列出当前规则"""
    checker = FastCheck()
    print(f"当前共有 {len(checker.rules)} 条规则:")
    for rule in checker.rules:
        print(f"  [{rule.severity:8s}] {rule.rule_id}")

def cmd_import(category):
    """导入 Semgrep 规则"""
    import asyncio
    asyncio.run(import_semgrep_rules(category))

def cmd_add(id, pattern, severity, message):
    """添加自定义规则"""
    # 实现添加逻辑
    pass

def cmd_reload():
    """热重载规则"""
    checker = FastCheck()
    checker.reload_rules()
    print("规则已重载")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 manage_rules.py [list|import|add|reload]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "list":
        cmd_list()
    elif cmd == "import":
        cmd_import(sys.argv[2] if len(sys.argv) > 2 else "python/lang/security")
    elif cmd == "reload":
        cmd_reload()
'''

print("\n创建规则管理脚本:")
print(script_template)

# 保存脚本模板
script_path = Path(__file__).parent.parent / "tools" / "manage_security_rules.py"
with open(script_path, 'w') as f:
    f.write(script_template)
print(f"\n脚本已保存到: {script_path}")


print("\n" + "=" * 60)
print("总结: 规则库扩展方式")
print("=" * 60)
print("""
1. 批量导入 Semgrep 规则:
   python3 wdai_v3/tools/import_semgrep_rules.py --all

2. 从本地文件导入:
   python3 wdai_v3/tools/import_semgrep_rules.py --file rules.yaml

3. 动态添加规则（代码）:
   checker.rules.append(SecurityRule(...))

4. 热重载规则:
   checker.reload_rules(new_rules_path)

5. 合并多个规则源:
   加载默认规则 + 导入的 Semgrep 规则

规则文件位置:
  - 默认规则: wdai_v3/rules/security/default_rules.yml
  - Semgrep规则: wdai_v3/core/rules/security/semgrep/*.yml
""")
