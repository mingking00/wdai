"""
wdai Security Fast Check - L1 Security Layer
毫秒级代码安全检查，预编译正则规则
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import yaml


@dataclass
class SecurityFinding:
    """安全发现"""
    rule_id: str
    severity: str  # critical, high, medium, low
    message: str
    line_number: int
    line_content: str
    confidence: float = 1.0


@dataclass
class FastCheckResult:
    """Fast Check 结果"""
    findings: List[SecurityFinding]
    risk_score: float  # 0-1
    checked_lines: int
    elapsed_ms: float
    
    @property
    def has_critical(self) -> bool:
        return any(f.severity == "critical" for f in self.findings)
    
    @property
    def has_high(self) -> bool:
        return any(f.severity == "high" for f in self.findings)


class SecurityRule:
    """单个安全规则"""
    
    def __init__(self, rule_id: str, pattern: str, severity: str, message: str):
        self.rule_id = rule_id
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.severity = severity
        self.message = message
        self.severity_score = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.1
        }.get(severity, 0.1)
    
    def check(self, line: str, line_number: int) -> Optional[SecurityFinding]:
        """检查单行代码"""
        if self.pattern.search(line):
            return SecurityFinding(
                rule_id=self.rule_id,
                severity=self.severity,
                message=self.message,
                line_number=line_number,
                line_content=line.strip()[:100]  # 截断长行
            )
        return None


class FastCheck:
    """
    毫秒级安全快速检查
    
    特点:
    - 预编译正则，微秒级匹配
    - 无外部依赖，纯本地执行
    - 规则可热更新
    """
    
    # 内置默认规则（当配置文件不存在时使用）
    DEFAULT_RULES = [
        # Critical - 立即阻止
        {
            "id": "exec-user-input",
            "pattern": r'exec\s*\(\s*.*(?:user|input|request|params)',
            "severity": "critical",
            "message": "执行用户输入，可能导致远程代码执行 (RCE)"
        },
        {
            "id": "eval-dangerous",
            "pattern": r'eval\s*\(\s*.*(?:user|input|request|params)',
            "severity": "critical",
            "message": "eval() 处理用户输入，存在代码注入风险"
        },
        {
            "id": "os-system-user-input",
            "pattern": r'os\.system\s*\(\s*.*(?:user|input|request|params|f["\'])',
            "severity": "critical",
            "message": "os.system() 执行动态命令，存在命令注入风险"
        },
        {
            "id": "subprocess-shell-true",
            "pattern": r'subprocess\..*shell\s*=\s*True',
            "severity": "critical",
            "message": "subprocess 使用 shell=True，存在命令注入风险"
        },
        
        # High - 需要人工审查
        {
            "id": "sql-string-format",
            "pattern": r'(?:execute|query|raw)\s*\(\s*["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*(?:%s|%d|\{.*\}|\+.*\+)',
            "severity": "high",
            "message": "SQL 字符串拼接/格式化，可能存在 SQL 注入"
        },
        {
            "id": "pickle-load",
            "pattern": r'pickle\.load|pickle\.loads',
            "severity": "high",
            "message": "pickle 反序列化不可信数据，可能导致任意代码执行"
        },
        {
            "id": "yaml-unsafe-load",
            "pattern": r'yaml\.load\s*\([^)]*\)(?!.*Loader\s*=\s*yaml\.SafeLoader)',
            "severity": "high",
            "message": "yaml.load() 使用不安全加载器，可能导致任意代码执行"
        },
        
        # Medium - 建议改进
        {
            "id": "hardcoded-secret",
            "pattern": r'(?:password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']',
            "severity": "medium",
            "message": "可能的硬编码凭据"
        },
        {
            "id": "debug-mode-enabled",
            "pattern": r'debug\s*=\s*True|DEBUG\s*=\s*True',
            "severity": "medium",
            "message": "调试模式开启，生产环境应该关闭"
        },
        {
            "id": "disabled-verification",
            "pattern": r'verify\s*=\s*False|ssl_verify\s*=\s*False',
            "severity": "medium",
            "message": "SSL/TLS 验证被禁用，存在中间人攻击风险"
        },
        
        # Low - 信息性
        {
            "id": "todo-security",
            "pattern": r'#\s*TODO.*(?:security|vulnerability|fix|hack)',
            "severity": "low",
            "message": "安全相关的 TODO 注释，需要跟进"
        },
        {
            "id": "broad-except",
            "pattern": r'except\s*:\s*$|except\s+Exception\s*:',
            "severity": "low",
            "message": "过于宽泛的异常捕获，可能隐藏安全问题"
        }
    ]
    
    def __init__(self, rules_path: Optional[Path] = None):
        """
        初始化 Fast Check
        
        Args:
            rules_path: 规则文件路径，如果为 None 使用内置规则
        """
        self.rules: List[SecurityRule] = []
        self._load_rules(rules_path)
    
    def _load_rules(self, rules_path: Optional[Path] = None):
        """加载规则"""
        if rules_path and rules_path.exists():
            # 从 YAML 文件加载
            with open(rules_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                for rule_data in config.get('rules', []):
                    self.rules.append(SecurityRule(
                        rule_id=rule_data['id'],
                        pattern=rule_data['pattern'],
                        severity=rule_data['severity'],
                        message=rule_data['message']
                    ))
        else:
            # 使用内置规则
            for rule_data in self.DEFAULT_RULES:
                self.rules.append(SecurityRule(
                    rule_id=rule_data['id'],
                    pattern=rule_data['pattern'],
                    severity=rule_data['severity'],
                    message=rule_data['message']
                ))
    
    def check(self, code: str) -> FastCheckResult:
        """
        检查代码
        
        Args:
            code: 要检查的代码字符串
            
        Returns:
            FastCheckResult 包含所有发现
        """
        import time
        start_time = time.perf_counter()
        
        findings = []
        lines = code.split('\n')
        
        for line_number, line in enumerate(lines, 1):
            for rule in self.rules:
                finding = rule.check(line, line_number)
                if finding:
                    findings.append(finding)
        
        elapsed = (time.perf_counter() - start_time) * 1000  # 毫秒
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(findings)
        
        return FastCheckResult(
            findings=findings,
            risk_score=risk_score,
            checked_lines=len(lines),
            elapsed_ms=elapsed
        )
    
    def _calculate_risk_score(self, findings: List[SecurityFinding]) -> float:
        """计算总体风险分数"""
        if not findings:
            return 0.0
        
        # 基于最高严重程度 + 发现数量加权
        severity_scores = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.1
        }
        
        max_score = max(severity_scores.get(f.severity, 0) for f in findings)
        
        # 如果有关键问题，直接返回高风险
        if any(f.severity == "critical" for f in findings):
            return min(1.0, 0.8 + len(findings) * 0.05)
        
        # 否则基于数量和严重程度计算
        total_score = sum(severity_scores.get(f.severity, 0) for f in findings)
        return min(1.0, max_score + total_score * 0.1)
    
    def reload_rules(self, rules_path: Optional[Path] = None):
        """热重载规则"""
        self.rules = []
        self._load_rules(rules_path)


# 便捷的检查函数
def quick_security_check(code: str) -> FastCheckResult:
    """快速安全检查入口"""
    checker = FastCheck()
    return checker.check(code)


if __name__ == "__main__":
    # 测试
    test_code = """
import os
import pickle

def process_user_input(user_data):
    # TODO: fix security issue
    result = os.system(f"echo {user_data}")  # 危险！
    data = pickle.loads(user_data)  # 危险！
    return result

password = "hardcoded_secret_123"  # 硬编码密码
"""
    
    result = quick_security_check(test_code)
    print(f"风险分数: {result.risk_score:.2f}")
    print(f"检查行数: {result.checked_lines}")
    print(f"耗时: {result.elapsed_ms:.3f} ms")
    print(f"\n发现问题 ({len(result.findings)}):")
    for f in result.findings:
        print(f"  [{f.severity.upper()}] 第{f.line_number}行: {f.message}")
