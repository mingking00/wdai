"""
Semgrep 规则批量导入工具
将 Semgrep 规则转换为 wdai Fast Check 格式
"""

import re
import yaml
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json


@dataclass
class ImportResult:
    """导入结果"""
    total_rules: int
    converted_rules: int
    skipped_rules: int
    errors: List[str]
    output_file: Path


class SemgrepRuleConverter:
    """
    Semgrep 规则转换器
    
    Semgrep 使用 AST 模式 (pattern)，而 Fast Check 使用正则
    这个转换器会尽力将 AST 模式转换为等价的正则表达式
    """
    
    # 常见 Semgrep 模式到正则的映射
    PATTERN_MAP = {
        # 危险函数
        r'pickle\.loads\($...\)': r'pickle\.loads\s*\(',
        r'pickle\.load\($...\)': r'pickle\.load\s*\(',
        r'yaml\.load\($...\)': r'yaml\.load\s*\([^)]*\)(?!.*SafeLoader)',
        r'exec\($...\)': r'exec\s*\(',
        r'eval\($...\)': r'eval\s*\(',
        
        # SQL 注入
        r'\.execute\(f"..."\)': r'\.execute\s*\(\s*f["\']',
        r'\.execute\("..." % \(...\)\)': r'\.execute\s*\(\s*["\'].*%',
        r'\.execute\("..."\.format\(...\)\)': r'\.execute\s*\(\s*["\'].*\.format',
        
        # 命令注入
        r'os\.system\($...\)': r'os\.system\s*\(',
        r'subprocess\.call\($...\, shell\=True\)': r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
        r'subprocess\.run\($...\, shell\=True\)': r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
        
        # 路径遍历
        r'open\($...\)': r'open\s*\(\s*(?:user|input|request|params)',
        
        # 硬编码密钥
        r'$SECRET = "..."': r'(?:password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}',
        
        # 调试信息
        r'debug\=True': r'debug\s*=\s*True',
        r'DEBUG\=True': r'DEBUG\s*=\s*True',
        
        # 弱加密
        r'hashlib\.md5\(\)': r'hashlib\.md5|md5\s*\(',
        r'MD5': r'\bMD5\b',
        
        # 随机数
        r'random\.random\(\)': r'random\.(?:random|randint|choice)\s*\(',
    }
    
    # 严重程度映射
    SEVERITY_MAP = {
        'ERROR': 'critical',
        'WARNING': 'high',
        'INFO': 'medium',
        'LOW': 'low',
        # 直接值
        'critical': 'critical',
        'high': 'high',
        'medium': 'medium',
        'low': 'low'
    }
    
    def __init__(self):
        self.errors = []
        self.converted = 0
        self.skipped = 0
    
    def convert_pattern(self, semgrep_pattern: str) -> Optional[str]:
        """
        将 Semgrep AST 模式转换为正则
        
        Semgrep 特殊语法:
        - $X: 元变量，匹配任意表达式
        - ...: 匹配任意序列
        - "...": 匹配任意字符串
        """
        # 直接映射
        if semgrep_pattern in self.PATTERN_MAP:
            return self.PATTERN_MAP[semgrep_pattern]
        
        # 尝试自动转换
        regex = self._ast_to_regex(semgrep_pattern)
        if regex:
            return regex
        
        return None
    
    def _ast_to_regex(self, pattern: str) -> Optional[str]:
        """AST 模式到正则的启发式转换"""
        regex = pattern
        
        # 转义特殊字符（使用双反斜杠）
        regex = regex.replace('(', r'\\(')
        regex = regex.replace(')', r'\\)')
        regex = regex.replace('[', r'\\[')
        regex = regex.replace(']', r'\\]')
        regex = regex.replace('{', r'\\{')
        regex = regex.replace('}', r'\\}')
        regex = regex.replace('.', r'\\.')
        regex = regex.replace('+', r'\\+')
        regex = regex.replace('?', r'\\?')
        regex = regex.replace('*', r'\\*')
        regex = regex.replace('^', r'\\^')
        regex = regex.replace('$', r'\\$')
        regex = regex.replace('|', r'\\|')
        
        # Semgrep 特殊语法转换
        # $X - 元变量 -> 匹配任意非空白字符（使用原始字符串）
        regex = re.sub(r'\$\w+', r'[^\\s\\(\\)\\[\\]\\{\\}]+', regex)
        
        # "..." - 任意字符串 -> 非引号字符
        regex = regex.replace('"\\.\\.\\."', r'[^"\']*')
        
        # ... - 任意序列 -> 非贪婪匹配
        regex = regex.replace('\\.\\.\\.', r'.*?')
        
        # 修复转义过度的字符
        regex = regex.replace(r'\\=', '=')
        regex = regex.replace(r'\\,', ',')
        regex = regex.replace(r'\\:', ':')
        
        return regex if regex != pattern else None
    
    def convert_severity(self, semgrep_severity: str) -> str:
        """转换严重程度"""
        return self.SEVERITY_MAP.get(semgrep_severity, 'medium')
    
    def convert_rule(self, semgrep_rule: Dict) -> Optional[Dict]:
        """
        转换单个 Semgrep 规则到 wdai 格式
        """
        # 获取模式
        pattern = semgrep_rule.get('pattern') or semgrep_rule.get('patterns', [{}])[0].get('pattern')
        if not pattern:
            self.skipped += 1
            return None
        
        # 转换模式
        converted_pattern = self.convert_pattern(pattern)
        if not converted_pattern:
            # 尝试 patterns 列表
            if 'patterns' in semgrep_rule:
                for p in semgrep_rule['patterns']:
                    if 'pattern' in p:
                        converted_pattern = self.convert_pattern(p['pattern'])
                        if converted_pattern:
                            break
            
            if not converted_pattern:
                self.errors.append(f"无法转换模式: {pattern[:50]}...")
                self.skipped += 1
                return None
        
        self.converted += 1
        
        return {
            'id': f"semgrep-{semgrep_rule.get('id', 'unknown')}",
            'pattern': converted_pattern,
            'severity': self.convert_severity(semgrep_rule.get('severity', 'WARNING')),
            'message': semgrep_rule.get('message', 'Semgrep 检测到的问题').replace('$X', '可疑表达式')
        }
    
    def convert_yaml(self, yaml_content: str) -> List[Dict]:
        """转换整个 YAML 文件"""
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            self.errors.append(f"YAML 解析错误: {e}")
            return []
        
        rules = data.get('rules', [])
        converted_rules = []
        
        for rule in rules:
            converted = self.convert_rule(rule)
            if converted:
                converted_rules.append(converted)
        
        return converted_rules


class SemgrepRuleImporter:
    """
    Semgrep 规则批量导入器
    
    支持从以下源导入:
    - Semgrep 官方规则库 (GitHub)
    - 本地规则文件
    - 自定义规则仓库
    """
    
    # Semgrep 官方规则库结构
    OFFICIAL_RULES = {
        'python/lang/security': 'Python 语言安全',
        'python/lang/best-practice': 'Python 最佳实践',
        'python/django': 'Django 安全',
        'python/flask': 'Flask 安全',
        'python/fastapi': 'FastAPI 安全',
        'python/sqlalchemy': 'SQLAlchemy 安全',
        'python/aws': 'AWS 安全',
        'python/cryptography': '密码学安全',
        'python/requests': 'HTTP 请求安全',
        'python/telnetlib': 'Telnet 安全',
    }
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "rules" / "security" / "semgrep"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.converter = SemgrepRuleConverter()
    
    async def import_from_github(self, category: str) -> ImportResult:
        """
        从 GitHub 导入指定类别的规则
        
        Args:
            category: 规则类别，如 'python/lang/security'
        """
        import aiohttp
        
        base_url = f"https://raw.githubusercontent.com/semgrep/semgrep-rules/develop/{category}"
        errors = []
        all_rules = []
        
        # 获取文件列表 (简化版本，实际应使用 GitHub API)
        # 这里使用预定义的常见规则文件
        common_files = [
            'audit',
            'command-injection',
            'injection',
            'deserialization',
            'path-traversal',
            'ssrf',
            'eval',
        ]
        
        async with aiohttp.ClientSession() as session:
            for file_name in common_files:
                yaml_url = f"{base_url}/{file_name}.yaml"
                try:
                    async with session.get(yaml_url, timeout=10) as resp:
                        if resp.status == 200:
                            content = await resp.text()
                            rules = self.converter.convert_yaml(content)
                            all_rules.extend(rules)
                except Exception as e:
                    errors.append(f"下载 {yaml_url} 失败: {e}")
        
        # 保存转换后的规则
        output_file = self.output_dir / f"{category.replace('/', '_')}.yml"
        self._save_rules(all_rules, output_file)
        
        return ImportResult(
            total_rules=len(all_rules) + self.converter.skipped,
            converted_rules=self.converter.converted,
            skipped_rules=self.converter.skipped,
            errors=errors + self.converter.errors,
            output_file=output_file
        )
    
    def import_from_local(self, yaml_file: Path) -> ImportResult:
        """从本地文件导入"""
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        rules = self.converter.convert_yaml(content)
        
        output_file = self.output_dir / f"local_{yaml_file.stem}.yml"
        self._save_rules(rules, output_file)
        
        return ImportResult(
            total_rules=len(rules) + self.converter.skipped,
            converted_rules=self.converter.converted,
            skipped_rules=self.converter.skipped,
            errors=self.converter.errors,
            output_file=output_file
        )
    
    def import_from_content(self, yaml_content: str, name: str) -> ImportResult:
        """从 YAML 内容直接导入"""
        rules = self.converter.convert_yaml(yaml_content)
        
        output_file = self.output_dir / f"{name}.yml"
        self._save_rules(rules, output_file)
        
        return ImportResult(
            total_rules=len(rules) + self.converter.skipped,
            converted_rules=self.converter.converted,
            skipped_rules=self.converter.skipped,
            errors=self.converter.errors,
            output_file=output_file
        )
    
    def _save_rules(self, rules: List[Dict], output_file: Path):
        """保存规则到文件"""
        output = {'rules': rules}
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(output, f, default_flow_style=False, allow_unicode=True)
    
    def list_available_categories(self) -> Dict[str, str]:
        """列出可用的规则类别"""
        return self.OFFICIAL_RULES.copy()


# 便捷函数
async def import_semgrep_rules(category: str = 'python/lang/security') -> ImportResult:
    """快速导入 Semgrep 规则"""
    importer = SemgrepRuleImporter()
    return await importer.import_from_github(category)


def import_semgrep_from_file(yaml_file: Path) -> ImportResult:
    """从文件导入"""
    importer = SemgrepRuleImporter()
    return importer.import_from_local(yaml_file)


if __name__ == "__main__":
    # 示例：转换内置的 Semgrep 规则格式
    sample_semgrep = """
rules:
  - id: dangerous-pickle-load
    pattern: pickle.loads($X)
    message: "Pickle 反序列化可能导致任意代码执行"
    severity: ERROR
    
  - id: sql-injection-fstring
    pattern: $CURSOR.execute(f"...")
    message: "SQL f-string 拼接可能存在注入漏洞"
    severity: WARNING
    
  - id: os-system-call
    pattern: os.system($X)
    message: "os.system 执行命令存在注入风险"
    severity: ERROR
"""
    
    importer = SemgrepRuleImporter()
    result = importer.import_from_content(sample_semgrep, "sample_import")
    
    print(f"导入结果:")
    print(f"  总规则: {result.total_rules}")
    print(f"  成功转换: {result.converted_rules}")
    print(f"  跳过: {result.skipped_rules}")
    print(f"  错误: {len(result.errors)}")
    print(f"  输出文件: {result.output_file}")
    
    if result.errors:
        print("\n错误详情:")
        for error in result.errors[:5]:
            print(f"  - {error}")
