#!/usr/bin/env python3
"""
WDai Code Security Constraints v1.0 (evo-005实现)
代码安全与性能约束规则

约束类别:
1. 代码安全: SQL注入、XSS、命令注入、硬编码密钥
2. 性能约束: 时间复杂度、空间复杂度、循环效率
3. 风格约束: PEP8、命名规范、复杂度

参考: Bandit, Pylint, CodeQL等工具
"""

import re
import ast
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time


# ============================================================================
# 约束分类
# ============================================================================

class Severity(Enum):
    CRITICAL = "critical"    # 必须修复
    HIGH = "high"           # 严重问题
    MEDIUM = "medium"       # 中等问题
    LOW = "low"             # 轻微问题
    INFO = "info"           # 建议


@dataclass
class CodeIssue:
    """代码问题"""
    rule_id: str
    rule_name: str
    category: str          # security/performance/style
    severity: Severity
    message: str
    line: int
    column: int
    code_snippet: str
    suggestion: str
    
    def to_dict(self) -> Dict:
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'category': self.category,
            'severity': self.severity.value,
            'message': self.message,
            'location': f"{self.line}:{self.column}",
            'code': self.code_snippet[:100] + '...' if len(self.code_snippet) > 100 else self.code_snippet,
            'suggestion': self.suggestion
        }


# ============================================================================
# 安全约束检查器
# ============================================================================

class SecurityChecker:
    """代码安全检查器"""
    
    # SQL注入模式
    SQL_PATTERNS = [
        (r'execute\s*\(\s*["\'].*%s.*["\']', 'SQL_FORMATTING', 'SQL格式化字符串'),
        (r'execute\s*\(\s*f["\']', 'SQL_FSTRING', 'SQL f-string'),
        (r'\.format\(.*\).*execute', 'SQL_FORMAT_METHOD', 'SQL format方法'),
        (r'execute\s*\(\s*.*\+\s*', 'SQL_CONCAT', 'SQL字符串拼接'),
    ]
    
    # XSS模式
    XSS_PATTERNS = [
        (r'innerHTML\s*=\s*', 'XSS_INNERHTML', '危险的innerHTML赋值'),
        (r'document\.write\s*\(', 'XSS_DOCUMENT_WRITE', 'document.write'),
        (r'eval\s*\(', 'XSS_EVAL', 'eval()执行'),
    ]
    
    # 命令注入模式
    COMMAND_PATTERNS = [
        (r'os\.system\s*\(', 'COMMAND_OS_SYSTEM', 'os.system()调用'),
        (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', 'COMMAND_SHELL_TRUE', 'shell=True'),
        (r'exec\s*\(', 'COMMAND_EXEC', 'exec()执行'),
    ]
    
    # 硬编码密钥模式
    SECRET_PATTERNS = [
        (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', 'HARDCODED_PASSWORD', '硬编码密码'),
        (r'(?i)(api_key|apikey)\s*=\s*["\'][^"\']+["\']', 'HARDCODED_APIKEY', '硬编码API密钥'),
        (r'(?i)(secret|token)\s*=\s*["\'][^"\']{10,}["\']', 'HARDCODED_SECRET', '硬编码密钥'),
        (r'sk-[a-zA-Z0-9]{32,}', 'EXPOSED_API_KEY', '暴露的API密钥'),
    ]
    
    def check(self, code: str, filename: str = "<unknown>") -> List[CodeIssue]:
        """执行安全检查"""
        issues = []
        lines = code.split('\n')
        
        # 检查SQL注入
        issues.extend(self._check_patterns(code, lines, self.SQL_PATTERNS, 'security', Severity.CRITICAL))
        
        # 检查XSS
        issues.extend(self._check_patterns(code, lines, self.XSS_PATTERNS, 'security', Severity.HIGH))
        
        # 检查命令注入
        issues.extend(self._check_patterns(code, lines, self.COMMAND_PATTERNS, 'security', Severity.CRITICAL))
        
        # 检查硬编码密钥
        issues.extend(self._check_patterns(code, lines, self.SECRET_PATTERNS, 'security', Severity.HIGH))
        
        # AST检查
        issues.extend(self._ast_check(code))
        
        return issues
    
    def _check_patterns(self, code: str, lines: List[str], 
                       patterns: List[Tuple], category: str, 
                       severity: Severity) -> List[CodeIssue]:
        """基于正则的模式检查"""
        issues = []
        
        for pattern, rule_id, rule_name in patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append(CodeIssue(
                        rule_id=rule_id,
                        rule_name=rule_name,
                        category=category,
                        severity=severity,
                        message=f"检测到{rule_name}",
                        line=i,
                        column=line.find(re.search(pattern, line).group()) if re.search(pattern, line) else 0,
                        code_snippet=line.strip(),
                        suggestion=self._get_suggestion(rule_id)
                    ))
        
        return issues
    
    def _ast_check(self, code: str) -> List[CodeIssue]:
        """基于AST的深度检查"""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # 检查pickle加载
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == 'pickle_load':
                        issues.append(CodeIssue(
                            rule_id='UNSAFE_PICKLE',
                            rule_name='不安全的pickle加载',
                            category='security',
                            severity=Severity.HIGH,
                            message='pickle.load()可能执行任意代码',
                            line=getattr(node, 'lineno', 0),
                            column=getattr(node, 'col_offset', 0),
                            code_snippet='pickle.load(...)',
                            suggestion='使用JSON等安全格式替代pickle'
                        ))
                
                # 检查yaml不安全加载
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'load':
                        issues.append(CodeIssue(
                            rule_id='UNSAFE_YAML',
                            rule_name='不安全的YAML加载',
                            category='security',
                            severity=Severity.HIGH,
                            message='yaml.load()默认不安全，使用yaml.safe_load()',
                            line=getattr(node, 'lineno', 0),
                            column=getattr(node, 'col_offset', 0),
                            code_snippet='yaml.load(...)',
                            suggestion='使用yaml.safe_load()替代'
                        ))
        
        except SyntaxError:
            pass  # 语法错误由其他检查器处理
        
        return issues
    
    def _get_suggestion(self, rule_id: str) -> str:
        """获取修复建议"""
        suggestions = {
            'SQL_FORMATTING': '使用参数化查询: cursor.execute("SELECT * FROM t WHERE id = %s", (user_id,))',
            'SQL_FSTRING': '使用参数化查询替代f-string',
            'XSS_INNERHTML': '使用textContent替代innerHTML，或使用DOMPurify清理',
            'COMMAND_OS_SYSTEM': '使用subprocess.run()并传递列表参数，避免shell注入',
            'HARDCODED_PASSWORD': '从环境变量读取: password = os.getenv("DB_PASSWORD")',
            'HARDCODED_APIKEY': '使用密钥管理服务或环境变量',
            'UNSAFE_PICKLE': '使用JSON格式: json.load()',
        }
        return suggestions.get(rule_id, '参考安全编码规范修复')


# ============================================================================
# 性能约束检查器
# ============================================================================

class PerformanceChecker:
    """代码性能检查器"""
    
    def check(self, code: str) -> List[CodeIssue]:
        """执行性能检查"""
        issues = []
        lines = code.split('\n')
        
        # 检查嵌套循环
        issues.extend(self._check_nested_loops(code, lines))
        
        # 检查低效操作
        issues.extend(self._check_inefficient_ops(code, lines))
        
        # 检查内存泄漏风险
        issues.extend(self._check_memory_issues(code, lines))
        
        return issues
    
    def _check_nested_loops(self, code: str, lines: List[str]) -> List[CodeIssue]:
        """检查嵌套循环（O(n^2)风险）"""
        issues = []
        
        # 简单检测：连续多行缩进增加
        indent_levels = []
        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()
            if stripped.startswith(('for ', 'while ')):
                indent = len(line) - len(stripped)
                indent_levels.append((i, indent))
        
        # 检测3层以上嵌套
        for i in range(len(indent_levels) - 2):
            if indent_levels[i+1][1] > indent_levels[i][1] and \
               indent_levels[i+2][1] > indent_levels[i+1][1]:
                issues.append(CodeIssue(
                    rule_id='NESTED_LOOPS',
                    rule_name='多层嵌套循环',
                    category='performance',
                    severity=Severity.MEDIUM,
                    message=f'检测到3层以上嵌套循环，可能导致O(n^3)复杂度',
                    line=indent_levels[i+2][0],
                    column=0,
                    code_snippet=lines[indent_levels[i+2][0] - 1].strip(),
                    suggestion='考虑使用字典、集合或算法优化降低复杂度'
                ))
        
        return issues
    
    def _check_inefficient_ops(self, code: str, lines: List[str]) -> List[CodeIssue]:
        """检查低效操作"""
        issues = []
        
        patterns = [
            (r'for.*in.*\+\s*', 'LIST_CONCAT_LOOP', '循环中列表拼接', Severity.MEDIUM),
            (r'\.count\(.*\)\s*>', 'INEFFICIENT_COUNT', '低效count检查', Severity.LOW),
            (r'list\(.*\)\.reverse\(\)', 'LIST_REVERSE', '列表反转低效', Severity.LOW),
        ]
        
        for pattern, rule_id, name, severity in patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append(CodeIssue(
                        rule_id=rule_id,
                        rule_name=name,
                        category='performance',
                        severity=severity,
                        message=f'检测到{name}',
                        line=i,
                        column=0,
                        code_snippet=line.strip(),
                        suggestion='参考Python性能最佳实践优化'
                    ))
        
        return issues
    
    def _check_memory_issues(self, code: str, lines: List[str]) -> List[CodeIssue]:
        """检查内存问题"""
        issues = []
        
        # 检查大列表推导式
        for i, line in enumerate(lines, 1):
            if re.search(r'\[.*for.*for.*for.*\]', line):
                issues.append(CodeIssue(
                    rule_id='LARGE_LIST_COMP',
                    rule_name='大列表推导式',
                    category='performance',
                    severity=Severity.LOW,
                    message='多层列表推导可能占用大量内存',
                    line=i,
                    column=0,
                    code_snippet=line.strip()[:50],
                    suggestion='考虑使用生成器表达式或分批处理'
                ))
        
        return issues


# ============================================================================
# 风格约束检查器
# ============================================================================

class StyleChecker:
    """代码风格检查器"""
    
    def check(self, code: str) -> List[CodeIssue]:
        """执行风格检查"""
        issues = []
        lines = code.split('\n')
        
        # 行长度检查
        issues.extend(self._check_line_length(lines))
        
        # 命名规范检查
        issues.extend(self._check_naming(code, lines))
        
        # 空白检查
        issues.extend(self._check_whitespace(lines))
        
        return issues
    
    def _check_line_length(self, lines: List[str]) -> List[CodeIssue]:
        """检查行长度（PEP8: 79字符）"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if len(line) > 100:  # 放宽到100
                issues.append(CodeIssue(
                    rule_id='LINE_TOO_LONG',
                    rule_name='行过长',
                    category='style',
                    severity=Severity.LOW,
                    message=f'行长度{len(line)}超过100字符',
                    line=i,
                    column=100,
                    code_snippet=line[:80] + '...',
                    suggestion='换行或使用括号隐式连接'
                ))
        
        return issues
    
    def _check_naming(self, code: str, lines: List[str]) -> List[CodeIssue]:
        """检查命名规范"""
        issues = []
        
        # 检测驼峰命名（应该是下划线）
        for i, line in enumerate(lines, 1):
            # 函数名检测
            func_match = re.search(r'def\s+([A-Z][a-zA-Z0-9]*)\s*\(', line)
            if func_match:
                issues.append(CodeIssue(
                    rule_id='CAMEL_CASE_FUNCTION',
                    rule_name='函数名使用驼峰命名',
                    category='style',
                    severity=Severity.LOW,
                    message=f'函数名应使用snake_case: {func_match.group(1)}',
                    line=i,
                    column=line.find(func_match.group(1)),
                    code_snippet=line.strip(),
                    suggestion=f'改为: {func_match.group(1)[0].lower() + func_match.group(1)[1:]}'
                ))
        
        return issues
    
    def _check_whitespace(self, lines: List[str]) -> List[CodeIssue]:
        """检查空白字符"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # 行尾空白
            if line.rstrip() != line:
                issues.append(CodeIssue(
                    rule_id='TRAILING_WHITESPACE',
                    rule_name='行尾空白',
                    category='style',
                    severity=Severity.INFO,
                    message='行尾有空白字符',
                    line=i,
                    column=len(line.rstrip()),
                    code_snippet=line.strip() or '(空白行)',
                    suggestion='删除行尾空白'
                ))
        
        return issues


# ============================================================================
# 代码审查引擎
# ============================================================================

class CodeReviewEngine:
    """代码审查引擎"""
    
    def __init__(self):
        self.security = SecurityChecker()
        self.performance = PerformanceChecker()
        self.style = StyleChecker()
        
        self.review_history = []
    
    def review(self, code: str, filename: str = "<unknown>") -> Dict:
        """
        完整代码审查
        
        Returns:
            {
                'issues': [...],
                'summary': {...},
                'score': float
            }
        """
        all_issues = []
        
        # 安全检查
        all_issues.extend(self.security.check(code, filename))
        
        # 性能检查
        all_issues.extend(self.performance.check(code))
        
        # 风格检查
        all_issues.extend(self.style.check(code))
        
        # 排序：严重程度降序
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        all_issues.sort(key=lambda x: severity_order[x.severity])
        
        # 生成摘要
        summary = self._generate_summary(all_issues)
        
        # 计算评分
        score = self._calculate_score(all_issues, len(code.split('\n')))
        
        result = {
            'filename': filename,
            'timestamp': time.time(),
            'issues': [issue.to_dict() for issue in all_issues],
            'summary': summary,
            'score': score,
            'pass': score >= 0.8 and summary['critical'] == 0 and summary['high'] == 0
        }
        
        self.review_history.append(result)
        return result
    
    def _generate_summary(self, issues: List[CodeIssue]) -> Dict:
        """生成摘要"""
        summary = {
            'total': len(issues),
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0,
            'by_category': {'security': 0, 'performance': 0, 'style': 0}
        }
        
        for issue in issues:
            summary[issue.severity.value] += 1
            summary['by_category'][issue.category] += 1
        
        return summary
    
    def _calculate_score(self, issues: List[CodeIssue], total_lines: int) -> float:
        """计算代码质量评分"""
        if total_lines == 0:
            return 1.0
        
        # 扣分规则
        deductions = {
            Severity.CRITICAL: 0.3,
            Severity.HIGH: 0.15,
            Severity.MEDIUM: 0.05,
            Severity.LOW: 0.02,
            Severity.INFO: 0.0
        }
        
        total_deduction = sum(deductions[i.severity] for i in issues)
        
        # 基础分1.0，扣到0为止
        score = max(0.0, 1.0 - total_deduction)
        
        return round(score, 2)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        if not self.review_history:
            return {}
        
        total_reviews = len(self.review_history)
        passed = sum(1 for r in self.review_history if r['pass'])
        avg_score = sum(r['score'] for r in self.review_history) / total_reviews
        
        return {
            'total_reviews': total_reviews,
            'passed': passed,
            'failed': total_reviews - passed,
            'pass_rate': passed / total_reviews if total_reviews else 0,
            'avg_score': avg_score
        }


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("WDai Code Security Constraints - 测试")
    print("="*60)
    
    # 测试代码（故意包含问题）
    test_code = '''
import os

# 硬编码密码（安全问题）
DB_PASSWORD = "my_secret_password_123"
API_KEY = "sk-test123456789"

def getUserData(user_id):
    """获取用户数据（命名不规范）''                                                                              
    # SQL注入风险
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    # 命令注入风险
    os.system(f"echo {user_id}")
    
    # 性能问题：嵌套循环
    result = []
    for i in range(100):
        for j in range(100):
            for k in range(100):
                result.append(i * j * k)
    
    return result
'''
    
    # 创建审查引擎
    engine = CodeReviewEngine()
    
    print("\n🔍 执行代码审查...")
    result = engine.review(test_code, "test_module.py")
    
    # 输出结果
    print(f"\n📊 审查摘要")
    print(f"   文件: {result['filename']}")
    print(f"   评分: {result['score']:.0%}")
    print(f"   通过: {'✅' if result['pass'] else '❌'}")
    print(f"   问题总数: {result['summary']['total']}")
    print(f"   - Critical: {result['summary']['critical']}")
    print(f"   - High: {result['summary']['high']}")
    print(f"   - Medium: {result['summary']['medium']}")
    print(f"   - Low: {result['summary']['low']}")
    print(f"   - Info: {result['summary']['info']}")
    
    print(f"\n📋 按类别")
    for cat, count in result['summary']['by_category'].items():
        print(f"   {cat}: {count}")
    
    print(f"\n🚨 严重问题 (Critical + High):")
    critical_issues = [i for i in result['issues'] if i['severity'] in ['critical', 'high']]
    for issue in critical_issues[:5]:
        print(f"   [{issue['severity'].upper()}] {issue['rule_name']}")
        print(f"      位置: {issue['location']}")
        print(f"      建议: {issue['suggestion']}")
    
    print("\n" + "="*60)
    print("✅ 代码安全约束测试完成")
    print("="*60)
