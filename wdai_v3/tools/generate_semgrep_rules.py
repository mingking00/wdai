"""
生成完整的 Semgrep Python 安全规则库（本地生成）
基于常见安全模式，无需网络下载
"""

import yaml
from pathlib import Path
from typing import List, Dict


# 基于 Semgrep 常见 Python 安全规则的模式
SEMGREP_PYTHON_RULES = [
    # ========== 注入类漏洞 ==========
    {
        "id": "python-sql-injection-string-format",
        "pattern": r'(?:cursor|db|conn)\.(?:execute|executemany)\s*\(\s*["\'].*(?:%s|%d|\{.*\}|\+.*\+|\.format\()',
        "severity": "critical",
        "message": "SQL 字符串格式化/拼接，存在 SQL 注入风险"
    },
    {
        "id": "python-command-injection-os-system",
        "pattern": r'os\.(?:system|popen)\s*\([^)]*(?:\+|\%|\.format\(|f["\'])',
        "severity": "critical",
        "message": "os.system/popen 使用动态命令，存在命令注入"
    },
    {
        "id": "python-command-injection-subprocess",
        "pattern": r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
        "severity": "critical",
        "message": "subprocess 使用 shell=True，存在命令注入风险"
    },
    {
        "id": "python-ssti-jinja2",
        "pattern": r'(?:jinja2\.)?(?:Template|Environment)\s*\([^)]*\)\.render\s*\([^)]*(?:\+|\%|\.format\(|f["\'])',
        "severity": "critical",
        "message": "Jinja2 模板渲染用户输入，存在 SSTI 注入"
    },
    
    # ========== 反序列化漏洞 ==========
    {
        "id": "python-deserialization-pickle",
        "pattern": r'pickle\.(?:load|loads)\s*\(',
        "severity": "critical",
        "message": "pickle 反序列化任意对象，可导致任意代码执行"
    },
    {
        "id": "python-deserialization-yaml-unsafe",
        "pattern": r'yaml\.load\s*\([^)]*\)(?!.*(?:SafeLoader|CSafeLoader))',
        "severity": "critical",
        "message": "yaml.load 使用不安全加载器，可导致任意代码执行"
    },
    {
        "id": "python-deserialization-marshal",
        "pattern": r'marshal\.(?:load|loads)\s*\(',
        "severity": "critical",
        "message": "marshal 反序列化不可信数据，可导致任意代码执行"
    },
    {
        "id": "python-deserialization-shelve",
        "pattern": r'shelve\.(?:open|DbfilenameShelf)',
        "severity": "high",
        "message": "shelve 模块基于 pickle，存在反序列化风险"
    },
    
    # ========== 路径遍历 ==========
    {
        "id": "python-path-traversal-open",
        "pattern": r'open\s*\([^)]*(?:user|input|request|params|args|argv)',
        "severity": "high",
        "message": "使用用户输入作为文件路径，存在路径遍历风险"
    },
    {
        "id": "python-path-traversal-io",
        "pattern": r'io\.(?:open|FileIO)\s*\([^)]*(?:user|input|request)',
        "severity": "high",
        "message": "io 模块使用用户输入路径，存在路径遍历风险"
    },
    
    # ========== 不安全的加密 ==========
    {
        "id": "python-weak-crypto-md5",
        "pattern": r'hashlib\.md5\s*\(|\.md5\s*\(',
        "severity": "medium",
        "message": "使用 MD5 哈希，已被证明不安全，建议改用 SHA-256"
    },
    {
        "id": "python-weak-crypto-sha1",
        "pattern": r'hashlib\.sha1\s*\(|\.sha1\s*\(',
        "severity": "medium",
        "message": "使用 SHA-1 哈希，已被证明不安全，建议改用 SHA-256"
    },
    {
        "id": "python-weak-random",
        "pattern": r'random\.(?:random|randint|choice|shuffle)\s*\(',
        "severity": "medium",
        "message": "使用伪随机数生成器，不适用于安全场景（如密码、token）"
    },
    {
        "id": "python-weak-ssl",
        "pattern": r'ssl\._create_unverified_context|ssl\.CERT_NONE',
        "severity": "high",
        "message": "禁用 SSL 证书验证，存在中间人攻击风险"
    },
    
    # ========== 硬编码敏感信息 ==========
    {
        "id": "python-hardcoded-password",
        "pattern": r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']',
        "severity": "high",
        "message": "可能的硬编码密码"
    },
    {
        "id": "python-hardcoded-secret",
        "pattern": r'(?:secret|api_key|apikey|token|access_key|private_key)\s*=\s*["\'][^"\']{16,}["\']',
        "severity": "high",
        "message": "可能的硬编码密钥/令牌"
    },
    {
        "id": "python-aws-key",
        "pattern": r'AKIA[0-9A-Z]{16}',
        "severity": "critical",
        "message": "检测到 AWS Access Key ID"
    },
    {
        "id": "python-openai-key",
        "pattern": r'sk-[a-zA-Z0-9]{48}',
        "severity": "critical",
        "message": "检测到 OpenAI API Key"
    },
    
    # ========== 调试/开发代码 ==========
    {
        "id": "python-debug-enabled",
        "pattern": r'(?:debug|DEBUG)\s*=\s*True',
        "severity": "medium",
        "message": "调试模式开启，生产环境应关闭"
    },
    {
        "id": "python-ipdb-debug",
        "pattern": r'import\s+(?:ipdb|pdb|breakpoint)|(?:ipdb|pdb)\.set_trace\(\)',
        "severity": "medium",
        "message": "代码中包含调试器调用，应移除后再部署"
    },
    
    # ========== 不安全的 HTTP ==========
    {
        "id": "python-insecure-http-verify",
        "pattern": r'requests\.(?:get|post|put|delete)\s*\([^)]*verify\s*=\s*False',
        "severity": "high",
        "message": "requests 禁用 SSL 验证，存在中间人攻击风险"
    },
    {
        "id": "python-http-url",
        "pattern": r'["\']http://[^"\']+["\']',
        "severity": "low",
        "message": "使用 HTTP 而非 HTTPS，数据传输未加密"
    },
    
    # ========== SSRF ==========
    {
        "id": "python-ssrf-requests",
        "pattern": r'requests\.(?:get|post)\s*\(\s*(?:user|input|request|params)',
        "severity": "high",
        "message": "requests 使用用户输入 URL，存在 SSRF 风险"
    },
    {
        "id": "python-ssrf-urllib",
        "pattern": r'urllib\.(?:request|urlopen)\s*\([^)]*(?:user|input|request)',
        "severity": "high",
        "message": "urllib 使用用户输入 URL，存在 SSRF 风险"
    },
    
    # ========== XXE ==========
    {
        "id": "python-xxe-lxml",
        "pattern": r'lxml\.etree\.(?:parse|fromstring|XML)\s*\(',
        "severity": "high",
        "message": "lxml 解析 XML，可能存在 XXE 漏洞，建议禁用外部实体"
    },
    {
        "id": "python-xxe-defused",
        "pattern": r'xml\.(?:parse|etree)\.(?:parse|fromstring)',
        "severity": "medium",
        "message": "使用标准库解析 XML，建议使用 defusedxml 防止 XXE"
    },
    
    # ========== 权限问题 ==========
    {
        "id": "python-eval-exec",
        "pattern": r'(?:eval|exec)\s*\(',
        "severity": "critical",
        "message": "使用 eval/exec 执行动态代码，存在代码注入风险"
    },
    {
        "id": "python-compile-code",
        "pattern": r'compile\s*\([^)]*\).*exec|exec\s*\(\s*compile',
        "severity": "critical",
        "message": "动态编译执行代码，存在代码注入风险"
    },
    {
        "id": "python-os-chmod",
        "pattern": r'os\.chmod\s*\([^)]*0o777|os\.chmod\s*\([^)]*stat\.S_IRWXU',
        "severity": "medium",
        "message": "设置文件权限为 777，过于宽松"
    },
    
    # ========== 敏感信息泄露 ==========
    {
        "id": "python-print-secret",
        "pattern": r'print\s*\([^)]*(?:password|secret|token|key)',
        "severity": "medium",
        "message": "打印敏感信息，可能泄露到日志"
    },
    {
        "id": "python-log-sensitive",
        "pattern": r'(?:logging|logger)\.(?:info|debug|warning|error)\s*\([^)]*(?:password|secret|token)',
        "severity": "medium",
        "message": "日志记录敏感信息，可能导致泄露"
    },
    {
        "id": "python-exception-sensitive",
        "pattern": r'raise\s+\w+\s*\([^)]*(?:user|password|secret)',
        "severity": "medium",
        "message": "异常信息包含敏感数据，可能泄露给用户"
    },
    
    # ========== 不安全的临时文件 ==========
    {
        "id": "python-tempfile-mktemp",
        "pattern": r'tempfile\.mktemp',
        "severity": "high",
        "message": "使用不安全的 mktemp，存在竞态条件，建议使用 mkstemp"
    },
    
    # ========== Flask/Django 特定 ==========
    {
        "id": "python-flask-debug",
        "pattern": r'app\.run\s*\([^)]*debug\s*=\s*True',
        "severity": "critical",
        "message": "Flask 调试模式开启，存在远程代码执行风险"
    },
    {
        "id": "python-django-raw-sql",
        "pattern": r'\.raw\s*\(\s*["\'].*(?:%s|%d|\{.*\}|\.format\()',
        "severity": "critical",
        "message": "Django raw() 使用字符串格式化，存在 SQL 注入"
    },
    {
        "id": "python-django-secret-key",
        "pattern": r'SECRET_KEY\s*=\s*["\'][^"\']+["\']',
        "severity": "critical",
        "message": "Django SECRET_KEY 硬编码，应使用环境变量"
    },
    
    # ========== JWT 安全 ==========
    {
        "id": "python-jwt-weak-algorithm",
        "pattern": r'jwt\.encode\s*\([^)]*algorithm\s*=\s*["\']none["\']',
        "severity": "critical",
        "message": "JWT 使用 'none' 算法，存在严重的认证绕过风险"
    },
    {
        "id": "python-jwt-no-verify",
        "pattern": r'jwt\.decode\s*\([^)]*verify\s*=\s*False',
        "severity": "critical",
        "message": "JWT 禁用签名验证，存在认证绕过风险"
    },
    
    # ========== 其他常见漏洞 ==========
    {
        "id": "python-telnetlib",
        "pattern": r'import\s+telnetlib|from\s+telnetlib',
        "severity": "high",
        "message": "使用不安全的 telnetlib，数据传输明文，建议使用 SSH"
    },
    {
        "id": "python-ftp-lib",
        "pattern": r'import\s+ftplib|from\s+ftplib',
        "severity": "medium",
        "message": "使用 FTP 明文传输，建议使用 SFTP/SCP"
    },
    {
        "id": "python-binding-all",
        "pattern": r'["\']0\.0\.0\.0["\']|bind.*0\.0\.0\.0',
        "severity": "low",
        "message": "服务绑定到 0.0.0.0，监听所有接口，可能暴露到公网"
    },
]


def generate_semgrep_rules():
    """生成完整的 Semgrep 规则库"""
    
    output_dir = Path(__file__).parent.parent / "core" / "rules" / "security" / "semgrep"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 按类别分组
    categories = {
        "injection": ["sql", "command", "ssti"],
        "deserialization": ["pickle", "yaml", "marshal"],
        "path-traversal": ["path", "traversal"],
        "crypto": ["md5", "sha1", "random", "ssl"],
        "secrets": ["password", "secret", "aws", "openai"],
        "debug": ["debug", "ipdb", "pdb"],
        "http": ["http", "verify", "ssl"],
        "ssrf": ["ssrf", "requests", "urllib"],
        "xxe": ["xml", "xxe", "lxml"],
        "permission": ["eval", "exec", "chmod"],
        "leak": ["print", "log", "exception"],
        "tempfile": ["temp", "mktemp"],
        "web": ["flask", "django", "jwt"],
        "network": ["telnet", "ftp", "bind"],
    }
    
    # 分类规则
    categorized_rules = {cat: [] for cat in categories.keys()}
    other_rules = []
    
    for rule in SEMGREP_PYTHON_RULES:
        rule_id = rule["id"].lower()
        assigned = False
        
        for cat, keywords in categories.items():
            if any(kw in rule_id for kw in keywords):
                categorized_rules[cat].append(rule)
                assigned = True
                break
        
        if not assigned:
            other_rules.append(rule)
    
    # 保存分类规则
    total_rules = 0
    for cat, rules in categorized_rules.items():
        if rules:
            output_file = output_dir / f"{cat}.yml"
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump({"rules": rules}, f, default_flow_style=False, allow_unicode=True)
            print(f"✅ {cat:15s}: {len(rules):2d} 条规则 -> {output_file.name}")
            total_rules += len(rules)
    
    # 保存其他规则
    if other_rules:
        output_file = output_dir / "other.yml"
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump({"rules": other_rules}, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ {'other':15s}: {len(other_rules):2d} 条规则 -> {output_file.name}")
        total_rules += len(other_rules)
    
    # 保存完整版
    all_rules_file = output_dir / "all_rules.yml"
    with open(all_rules_file, 'w', encoding='utf-8') as f:
        yaml.dump({"rules": SEMGREP_PYTHON_RULES}, f, default_flow_style=False, allow_unicode=True)
    print(f"\n📦 完整规则库: {total_rules} 条规则 -> {all_rules_file.name}")
    
    return total_rules, output_dir


def merge_with_default_rules():
    """合并 Semgrep 规则和默认规则"""
    from wdai_v3.core.security.fast_check import FastCheck
    
    output_dir = Path(__file__).parent.parent / "core" / "rules" / "security" / "semgrep"
    all_rules_file = output_dir / "all_rules.yml"
    
    if not all_rules_file.exists():
        print("❌ 未找到 Semgrep 规则文件，请先运行 generate_semgrep_rules()")
        return None
    
    # 加载 Semgrep 规则
    with open(all_rules_file, 'r') as f:
        semgrep_config = yaml.safe_load(f)
    
    # 合并
    all_rules = []
    
    # 先添加默认规则
    for rule in FastCheck.DEFAULT_RULES:
        all_rules.append(rule)
    
    # 添加 Semgrep 规则
    for rule in semgrep_config.get('rules', []):
        all_rules.append({
            'id': rule['id'],
            'pattern': rule['pattern'],
            'severity': rule['severity'],
            'message': rule['message']
        })
    
    # 保存合并后的规则
    merged_file = output_dir / "merged_with_default.yml"
    with open(merged_file, 'w', encoding='utf-8') as f:
        yaml.dump({"rules": all_rules}, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ 合并完成: {len(all_rules)} 条规则（默认 {len(FastCheck.DEFAULT_RULES)} + Semgrep {len(semgrep_config.get('rules', []))}）")
    print(f"   输出文件: {merged_file}")
    
    return merged_file


if __name__ == "__main__":
    print("=" * 60)
    print("生成 Semgrep Python 安全规则库")
    print("=" * 60)
    print()
    
    total, output_dir = generate_semgrep_rules()
    
    print()
    print("=" * 60)
    print("合并默认规则")
    print("=" * 60)
    print()
    
    merge_with_default_rules()
    
    print()
    print("=" * 60)
    print(f"✅ 规则库生成完成！")
    print("=" * 60)
    print(f"\n总共 {total} 条 Semgrep 规则")
    print(f"规则目录: {output_dir}")
    print(f"\n使用方式:")
    print(f"  from wdai_v3.core.security import FastCheck")
    print(f"  checker = FastCheck(rules_path='{output_dir}/all_rules.yml')")
