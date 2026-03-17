#!/usr/bin/env python3
"""
AutoCodeReviewer Helper Script
简单的代码审查辅助工具
"""

import sys
import re
import json
from pathlib import Path

def analyze_code(file_path, content):
    """分析单个文件的代码问题"""
    issues = []
    lines = content.split('\n')
    
    # Python检查
    if file_path.endswith('.py'):
        for i, line in enumerate(lines, 1):
            # 检查行长度
            if len(line) > 88:
                issues.append({
                    'line': i,
                    'severity': 'warning',
                    'type': 'style',
                    'message': f'行长度超过88字符 ({len(line)}字符)',
                    'suggestion': '考虑换行或简化表达式'
                })
            
            # 检查bare except
            if re.match(r'^\s*except\s*:', line):
                issues.append({
                    'line': i,
                    'severity': 'error',
                    'type': 'bug',
                    'message': '使用了bare except，会捕获所有异常包括KeyboardInterrupt',
                    'suggestion': '使用具体的异常类型，如 except ValueError:'
                })
            
            # 检查print语句（可能是调试遗留）
            if re.search(r'print\s*\(', line) and '>>>' not in line:
                issues.append({
                    'line': i,
                    'severity': 'info',
                    'type': 'style',
                    'message': '发现print语句',
                    'suggestion': '考虑使用logging模块代替print'
                })
            
            # 检查TODO注释
            if 'TODO' in line or 'FIXME' in line:
                issues.append({
                    'line': i,
                    'severity': 'warning',
                    'type': 'style',
                    'message': f'发现未完成的标记: {line.strip()}',
                    'suggestion': '尽快完成或创建Issue跟踪'
                })
    
    # JavaScript/TypeScript检查
    elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
        for i, line in enumerate(lines, 1):
            # 检查console.log
            if 'console.log' in line:
                issues.append({
                    'line': i,
                    'severity': 'warning',
                    'type': 'style',
                    'message': '发现console.log（可能是调试遗留）',
                    'suggestion': '生产代码中移除或使用专业日志库'
                })
            
            # 检查var使用
            if re.match(r'^\s*var\s+', line):
                issues.append({
                    'line': i,
                    'severity': 'warning',
                    'type': 'style',
                    'message': '使用var声明变量',
                    'suggestion': '使用let或const代替var'
                })
            
            # 检查== vs ===
            if re.search(r'[^=!]==[^=]', line) and '==' in line.replace('===', ''):
                issues.append({
                    'line': i,
                    'severity': 'warning',
                    'type': 'bug',
                    'message': '使用了==而不是===',
                    'suggestion': '使用===进行严格相等比较'
                })
    
    return issues

def generate_report(file_path, issues):
    """生成审查报告"""
    if not issues:
        return f"✅ {file_path}: 未发现问题"
    
    report = [f"\n📄 {file_path}", "-" * 40]
    
    for issue in issues:
        severity_emoji = {'error': '🔴', 'warning': '🟡', 'info': '🟢'}[issue['severity']]
        report.append(f"{severity_emoji} 第{issue['line']}行 [{issue['type']}]")
        report.append(f"   问题: {issue['message']}")
        report.append(f"   建议: {issue['suggestion']}")
    
    return '\n'.join(report)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 review_helper.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = analyze_code(file_path, content)
        print(generate_report(file_path, issues))
        
        # 输出JSON格式供OpenClaw解析
        print(f"\n<!-- JSON_RESULT: {json.dumps({'file': file_path, 'issues': issues, 'total': len(issues)})} -->")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        sys.exit(1)
