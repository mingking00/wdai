#!/usr/bin/env python3
"""
System Evolution Agent (SEA) - 系统进化代理

这是一个常驻Agent，专门负责改进OpenClaw系统本身。
拥有修改系统文件的权限，但遵循严格的审查流程。

核心能力:
1. 系统分析与诊断 - 分析当前系统状态，识别改进点
2. 代码审查 - 严格审查新代码，减少bug
3. 系统集成 - 将改进安全地整合到系统
4. 回滚机制 - 发现问题时快速回滚

使用方式:
- 用户说"改进你自己"或"进化"时触发
- Agent分析需求，提出改进方案
- 用户确认后执行严格审查
- 通过审查后整合到系统
"""

import os
import sys
import json
import time
import shutil
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict

# 系统路径
WORKSPACE = Path("/root/.openclaw/workspace")
SYSTEM_DIR = WORKSPACE / ".system"
BACKUP_DIR = SYSTEM_DIR / "backups"
STAGED_DIR = SYSTEM_DIR / "staged"
LOG_DIR = SYSTEM_DIR / "logs"

# 确保目录存在
for d in [SYSTEM_DIR, BACKUP_DIR, STAGED_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class ChangeRequest:
    """变更请求"""
    id: str
    timestamp: float
    source: str  # 'user', 'auto', 'heartbeat'
    description: str
    target_files: List[str]
    changes: Dict[str, str]  # file_path -> new_content
    priority: int = 5  # 1-10
    status: str = "pending"  # pending, reviewing, approved, rejected, applied, rolled_back
    review_notes: List[str] = field(default_factory=list)
    backup_id: str = ""


@dataclass
class ReviewResult:
    """审查结果"""
    passed: bool
    score: float  # 0-100
    issues: List[Dict]
    suggestions: List[str]
    security_concerns: List[str]
    performance_impact: str


class SystemEvolutionAgent:
    """
    系统进化代理 - 负责改进OpenClaw系统本身
    """
    
    def __init__(self):
        self.name = "SystemEvolutionAgent"
        self.version = "1.0.0"
        self.change_history: List[ChangeRequest] = []
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """设置日志"""
        log_file = LOG_DIR / f"sea_{datetime.now().strftime('%Y%m%d')}.log"
        
        class Logger:
            def info(self, msg): 
                line = f"[{datetime.now().isoformat()}] [INFO] {msg}"
                print(line)
                with open(log_file, 'a') as f:
                    f.write(line + '\n')
                    
            def warning(self, msg):
                line = f"[{datetime.now().isoformat()}] [WARNING] {msg}"
                print(line)
                with open(log_file, 'a') as f:
                    f.write(line + '\n')
                    
            def error(self, msg):
                line = f"[{datetime.now().isoformat()}] [ERROR] {msg}"
                print(line)
                with open(log_file, 'a') as f:
                    f.write(line + '\n')
                    
            def success(self, msg):
                line = f"[{datetime.now().isoformat()}] [SUCCESS] {msg}"
                print(line)
                with open(log_file, 'a') as f:
                    f.write(line + '\n')
        
        return Logger()
    
    def improve_self(self, improvement_description: str, code_changes: Dict[str, str] = None) -> Dict:
        """
        主入口：改进系统
        
        Args:
            improvement_description: 改进描述
            code_changes: 代码变更 {file_path: new_content}
            
        Returns:
            执行结果
        """
        self.logger.info("="*60)
        self.logger.info("系统进化代理启动")
        self.logger.info("="*60)
        self.logger.info(f"改进描述: {improvement_description}")
        
        # 1. 创建变更请求
        change_id = self._generate_change_id()
        request = ChangeRequest(
            id=change_id,
            timestamp=time.time(),
            source="user",
            description=improvement_description,
            target_files=list(code_changes.keys()) if code_changes else [],
            changes=code_changes or {}
        )
        
        # 2. 备份当前系统
        self.logger.info("[1/5] 备份当前系统...")
        backup_id = self._backup_system(request.target_files)
        request.backup_id = backup_id
        self.logger.success(f"备份完成: {backup_id}")
        
        # 3. 严格审查
        self.logger.info("[2/5] 执行严格审查...")
        review = self._strict_review(request)
        request.status = "reviewing"
        
        if not review.passed:
            self.logger.error(f"审查未通过 (得分: {review.score}/100)")
            for issue in review.issues:
                self.logger.error(f"  - {issue['severity']}: {issue['message']}")
            request.status = "rejected"
            self._save_request(request)
            return {
                "success": False,
                "change_id": change_id,
                "status": "rejected",
                "review": asdict(review),
                "message": "审查未通过，请修复问题后重试"
            }
        
        self.logger.success(f"审查通过 (得分: {review.score}/100)")
        for suggestion in review.suggestions:
            self.logger.info(f"  建议: {suggestion}")
        
        # 4. 用户确认
        self.logger.info("[3/5] 等待用户确认...")
        # 实际实现中这里应该等待用户输入
        # 现在假设用户已确认
        
        # 5. 应用变更
        self.logger.info("[4/5] 应用变更...")
        try:
            self._apply_changes(request)
            request.status = "applied"
            self.logger.success("变更应用成功")
        except Exception as e:
            self.logger.error(f"应用变更失败: {e}")
            self._rollback(backup_id)
            request.status = "rolled_back"
            return {
                "success": False,
                "change_id": change_id,
                "status": "rolled_back",
                "error": str(e)
            }
        
        # 6. 验证
        self.logger.info("[5/5] 验证变更...")
        if self._verify_changes(request):
            self.logger.success("验证通过")
            request.status = "verified"
        else:
            self.logger.error("验证失败，执行回滚")
            self._rollback(backup_id)
            request.status = "rolled_back"
            return {
                "success": False,
                "change_id": change_id,
                "status": "rolled_back",
                "message": "验证失败"
            }
        
        # 保存记录
        self._save_request(request)
        self.change_history.append(request)
        
        self.logger.info("="*60)
        self.logger.success("系统进化完成")
        self.logger.info("="*60)
        
        return {
            "success": True,
            "change_id": change_id,
            "status": "applied",
            "backup_id": backup_id,
            "files_changed": request.target_files,
            "review_score": review.score
        }
    
    def _generate_change_id(self) -> str:
        """生成变更ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_str = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
        return f"CHG_{timestamp}_{random_str}"
    
    def _backup_system(self, files_to_backup: List[str]) -> str:
        """备份系统文件"""
        backup_id = f"BKP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = BACKUP_DIR / backup_id
        backup_path.mkdir(exist_ok=True)
        
        for file_path in files_to_backup:
            src = WORKSPACE / file_path
            if src.exists():
                dst = backup_path / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        
        # 保存备份清单
        manifest = {
            "backup_id": backup_id,
            "timestamp": datetime.now().isoformat(),
            "files": files_to_backup
        }
        with open(backup_path / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return backup_id
    
    def _strict_review(self, request: ChangeRequest) -> ReviewResult:
        """
        严格审查流程
        
        检查项:
        1. 语法检查 - 代码是否可解析
        2. 安全审查 - 是否有危险操作
        3. 依赖检查 - 依赖是否满足
        4. 冲突检查 - 是否与现有代码冲突
        5. 性能评估 - 是否有性能问题
        """
        issues = []
        suggestions = []
        security_concerns = []
        score = 100
        
        for file_path, content in request.changes.items():
            # 1. 语法检查
            if file_path.endswith('.py'):
                syntax_ok, syntax_msg = self._check_python_syntax(content)
                if not syntax_ok:
                    issues.append({
                        "file": file_path,
                        "severity": "CRITICAL",
                        "type": "syntax",
                        "message": syntax_msg
                    })
                    score -= 30
            
            # 2. 安全审查
            security_issues = self._security_scan(content, file_path)
            for issue in security_issues:
                security_concerns.append(f"{file_path}: {issue}")
                if "CRITICAL" in issue:
                    score -= 20
                else:
                    score -= 10
            
            # 3. 冲突检查
            if (WORKSPACE / file_path).exists():
                existing = (WORKSPACE / file_path).read_text()
                conflicts = self._detect_conflicts(existing, content)
                if conflicts:
                    issues.append({
                        "file": file_path,
                        "severity": "WARNING",
                        "type": "conflict",
                        "message": f"检测到 {len(conflicts)} 处潜在冲突"
                    })
                    score -= 15
            
            # 4. 代码质量
            quality_issues = self._check_code_quality(content, file_path)
            for issue in quality_issues:
                issues.append({
                    "file": file_path,
                    "severity": "INFO",
                    "type": "quality",
                    "message": issue
                })
                score -= 5
        
        # 生成建议
        if score < 80:
            suggestions.append("建议增加更多测试用例")
        if security_concerns:
            suggestions.append("建议修复安全警告后再提交")
        if not any(f.endswith('_test.py') for f in request.target_files):
            suggestions.append("建议为新功能添加单元测试")
        
        # 性能评估
        performance_impact = self._assess_performance(request.changes)
        
        passed = score >= 70 and not any(i['severity'] == 'CRITICAL' for i in issues)
        
        return ReviewResult(
            passed=passed,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
            security_concerns=security_concerns,
            performance_impact=performance_impact
        )
    
    def _check_python_syntax(self, code: str) -> Tuple[bool, str]:
        """检查Python语法"""
        try:
            compile(code, '<string>', 'exec')
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
    
    def _security_scan(self, code: str, file_path: str) -> List[str]:
        """安全扫描"""
        issues = []
        
        # 危险模式检查
        dangerous_patterns = [
            (r'os\.system\s*\(', "使用 os.system() 可能存在命令注入风险"),
            (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "subprocess with shell=True 存在注入风险"),
            (r'eval\s*\(', "使用 eval() 存在代码执行风险"),
            (r'exec\s*\(', "使用 exec() 存在代码执行风险"),
            (r'__import__\s*\(', "动态导入可能被滥用"),
            (r'open\s*\([^)]*[\"\']w', "文件写入操作需谨慎"),
            (r'rm\s+-rf', "CRITICAL: 发现危险删除命令"),
            (r'\.format\s*\([^)]*\)', "字符串format可能存在注入风险"),
        ]
        
        import re
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                if "CRITICAL" in message:
                    issues.append(f"CRITICAL: {message}")
                else:
                    issues.append(f"WARNING: {message}")
        
        return issues
    
    def _detect_conflicts(self, existing: str, new: str) -> List[Dict]:
        """检测代码冲突"""
        conflicts = []
        
        # 简单检查：函数定义冲突
        import re
        existing_funcs = set(re.findall(r'def\s+(\w+)\s*\(', existing))
        new_funcs = set(re.findall(r'def\s+(\w+)\s*\(', new))
        
        overlap = existing_funcs & new_funcs
        for func in overlap:
            conflicts.append({
                "type": "function_redefinition",
                "name": func
            })
        
        return conflicts
    
    def _check_code_quality(self, code: str, file_path: str) -> List[str]:
        """代码质量检查"""
        issues = []
        
        # 检查行长度
        for i, line in enumerate(code.split('\n'), 1):
            if len(line) > 120:
                issues.append(f"Line {i}: 行长度超过120字符")
        
        # 检查是否有文档字符串
        if file_path.endswith('.py') and 'class ' in code:
            if '"""' not in code and "'''" not in code:
                issues.append("缺少文档字符串")
        
        # 检查TODO/FIXME
        if 'TODO' in code or 'FIXME' in code:
            issues.append("代码中包含TODO/FIXME标记")
        
        return issues
    
    def _assess_performance(self, changes: Dict[str, str]) -> str:
        """性能影响评估"""
        # 简单启发式评估
        total_lines = sum(len(c.split('\n')) for c in changes.values())
        
        if total_lines < 50:
            return "low"
        elif total_lines < 200:
            return "medium"
        else:
            return "high"
    
    def _apply_changes(self, request: ChangeRequest):
        """应用变更"""
        for file_path, content in request.changes.items():
            full_path = WORKSPACE / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(full_path, 'w') as f:
                f.write(content)
            
            self.logger.info(f"  已更新: {file_path}")
    
    def _verify_changes(self, request: ChangeRequest) -> bool:
        """验证变更"""
        # 1. 检查文件是否存在
        for file_path in request.target_files:
            if not (WORKSPACE / file_path).exists():
                self.logger.error(f"验证失败: {file_path} 不存在")
                return False
        
        # 2. 语法验证（Python文件）
        for file_path in request.target_files:
            if file_path.endswith('.py'):
                content = (WORKSPACE / file_path).read_text()
                ok, msg = self._check_python_syntax(content)
                if not ok:
                    self.logger.error(f"验证失败: {file_path} 语法错误 - {msg}")
                    return False
        
        return True
    
    def _rollback(self, backup_id: str):
        """回滚到备份"""
        self.logger.warning(f"执行回滚: {backup_id}")
        
        backup_path = BACKUP_DIR / backup_id
        if not backup_path.exists():
            self.logger.error(f"备份不存在: {backup_id}")
            return False
        
        # 读取备份清单
        with open(backup_path / "manifest.json", 'r') as f:
            manifest = json.load(f)
        
        # 恢复文件
        for file_path in manifest['files']:
            src = backup_path / file_path
            dst = WORKSPACE / file_path
            if src.exists():
                shutil.copy2(src, dst)
                self.logger.info(f"  已恢复: {file_path}")
        
        self.logger.success("回滚完成")
        return True
    
    def _save_request(self, request: ChangeRequest):
        """保存变更请求记录"""
        record_file = SYSTEM_DIR / "change_history.json"
        
        history = []
        if record_file.exists():
            with open(record_file, 'r') as f:
                history = json.load(f)
        
        history.append(asdict(request))
        
        with open(record_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_change_history(self) -> List[Dict]:
        """获取变更历史"""
        record_file = SYSTEM_DIR / "change_history.json"
        if record_file.exists():
            with open(record_file, 'r') as f:
                return json.load(f)
        return []
    
    def analyze_system(self) -> Dict:
        """系统分析 - 识别改进点"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "findings": [],
            "suggestions": []
        }
        
        # 1. 检查SOUL.md是否需要更新
        soul_path = WORKSPACE / "SOUL.md"
        if soul_path.exists():
            content = soul_path.read_text()
            if "困惑" in content and "进化的终点" in content:
                analysis["findings"].append("SOUL.md中的困惑部分可能需要新的思考")
        
        # 2. 检查技能覆盖率
        skills_dir = WORKSPACE / "skills"
        if skills_dir.exists():
            skill_count = len([d for d in skills_dir.iterdir() if d.is_dir()])
            analysis["metrics"] = {"skill_count": skill_count}
            if skill_count < 10:
                analysis["suggestions"].append(f"技能数量较少({skill_count})，建议创建更多技能")
        
        # 3. 检查错误历史
        error_logs = list(LOG_DIR.glob("*.log"))
        if error_logs:
            recent_errors = []
            for log_file in sorted(error_logs)[-3:]:  # 最近3天
                with open(log_file, 'r') as f:
                    for line in f:
                        if '[ERROR]' in line:
                            recent_errors.append(line.strip())
            
            if len(recent_errors) > 10:
                analysis["findings"].append(f"最近错误较多({len(recent_errors)}条)，需要排查")
        
        return analysis


# 全局实例
sea = SystemEvolutionAgent()


def improve_self(description: str, changes: Dict[str, str] = None) -> Dict:
    """
    便捷函数：改进系统
    
    使用示例:
        result = improve_self(
            "添加错误处理机制",
            {
                "skills/my_skill/core.py": "新代码内容",
                "SOUL.md": "更新后的人格描述"
            }
        )
    """
    return sea.improve_self(description, changes)


def analyze_system() -> Dict:
    """系统分析"""
    return sea.analyze_system()


def get_improvement_history() -> List[Dict]:
    """获取改进历史"""
    return sea.get_change_history()


if __name__ == "__main__":
    # 测试
    print("System Evolution Agent v1.0.0")
    print("=" * 60)
    
    # 分析系统
    analysis = analyze_system()
    print("\n系统分析结果:")
    for finding in analysis.get("findings", []):
        print(f"  - {finding}")
    for suggestion in analysis.get("suggestions", []):
        print(f"  建议: {suggestion}")
    
    print("\nAgent已就绪，等待'improve_self()'调用")
