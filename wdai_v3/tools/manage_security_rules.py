
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
