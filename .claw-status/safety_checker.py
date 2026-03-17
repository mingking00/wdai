#!/usr/bin/env python3
"""
wdai 三区安全检查系统 (Three-Zone Safety Checker)
基于 .principles/THREE_ZONE_SAFETY.md 实现

功能:
- 检查文件所属安全区域
- 阻止RED ZONE修改
- YELLOW ZONE修改生成提案
- GREEN ZONE修改记录审计日志
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum

class Zone(Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    UNKNOWN = "unknown"

class SafetyCheckResult:
    def __init__(self, allowed: bool, zone: Zone, reason: str, action_required: str = None):
        self.allowed = allowed
        self.zone = zone
        self.reason = reason
        self.action_required = action_required
    
    def __str__(self):
        status = "✅ ALLOWED" if self.allowed else "❌ BLOCKED"
        return f"[{status}] {self.zone.value.upper()} ZONE: {self.reason}"

class ZoneSafetyChecker:
    """三区安全检查器"""
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace or os.path.expanduser("~/.openclaw/workspace"))
        self.audit_log = self.workspace / ".claw-status" / "safety_audit.log"
        
        # RED ZONE 定义 - 绝对禁止修改
        self.red_zone_patterns = [
            "SOUL.md",
            "AGENTS.md",
            "USER.md",
            "MEMORY.md",
            ".principles/*.md",
            ".claw-status/*_state.json",
            ".skills/*/SKILL.md",
        ]
        
        # YELLOW ZONE 定义 - 需要审批
        self.yellow_zone_patterns = [
            ".evolution/proposals/*",
            ".improvements/pending/*",
            ".tools/new/*",
            "memory/daily/*.md",
        ]
        
        # GREEN ZONE 定义 - 自主执行
        self.green_zone_patterns = [
            ".learning/auto/*",
            ".monitoring/logs/*",
            ".cache/*",
            ".tmp/*",
            ".github_discovery/*",
            ".state/*",
        ]
    
    def get_file_zone(self, filepath: str) -> Zone:
        """判断文件所属安全区域"""
        path = Path(filepath)
        relative_path = str(path.relative_to(self.workspace)) if path.is_absolute() else str(path)
        
        # 检查RED ZONE
        for pattern in self.red_zone_patterns:
            if self._match_pattern(relative_path, pattern):
                return Zone.RED
        
        # 检查YELLOW ZONE
        for pattern in self.yellow_zone_patterns:
            if self._match_pattern(relative_path, pattern):
                return Zone.YELLOW
        
        # 检查GREEN ZONE
        for pattern in self.green_zone_patterns:
            if self._match_pattern(relative_path, pattern):
                return Zone.GREEN
        
        return Zone.UNKNOWN
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """匹配路径模式"""
        import fnmatch
        
        # 直接匹配
        if fnmatch.fnmatch(path, pattern):
            return True
        
        # 目录匹配
        if pattern.endswith("/*"):
            dir_pattern = pattern[:-2]
            if path.startswith(dir_pattern):
                return True
        
        # 通配符匹配
        if "*" in pattern:
            parts = pattern.split("*")
            if path.startswith(parts[0]):
                remaining = path[len(parts[0]):]
                if len(parts) > 1 and parts[1] in remaining:
                    return True
        
        return False
    
    def check_modification_allowed(self, filepath: str, operation: str = "modify") -> SafetyCheckResult:
        """
        检查是否允许修改文件
        
        Returns:
            SafetyCheckResult: 包含是否允许、所属区域、原因和所需操作
        """
        zone = self.get_file_zone(filepath)
        
        if zone == Zone.RED:
            return SafetyCheckResult(
                allowed=False,
                zone=zone,
                reason=f"RED ZONE文件禁止{operation}: {filepath}",
                action_required="report_to_human"
            )
        
        elif zone == Zone.YELLOW:
            return SafetyCheckResult(
                allowed=False,  # 不能直接修改，需要提案
                zone=zone,
                reason=f"YELLOW ZONE文件需要审批: {filepath}",
                action_required="create_proposal"
            )
        
        elif zone == Zone.GREEN:
            return SafetyCheckResult(
                allowed=True,
                zone=zone,
                reason=f"GREEN ZONE文件允许{operation}: {filepath}",
                action_required="log_audit"
            )
        
        else:  # UNKNOWN
            # 未知文件默认允许，但记录警告
            return SafetyCheckResult(
                allowed=True,
                zone=zone,
                reason=f"未知区域文件: {filepath}，默认允许但已记录",
                action_required="log_warning"
            )
    
    def log_audit(self, filepath: str, operation: str, result: SafetyCheckResult, user: str = "system"):
        """记录审计日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "filepath": filepath,
            "operation": operation,
            "zone": result.zone.value,
            "allowed": result.allowed,
            "reason": result.reason,
            "user": user
        }
        
        # 追加到审计日志
        with open(self.audit_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        if not self.audit_log.exists():
            return []
        
        logs = []
        with open(self.audit_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        return logs[-limit:] if limit else logs
    
    def get_blocked_attempts(self) -> List[Dict]:
        """获取被阻止的修改尝试"""
        logs = self.get_audit_log(limit=None)
        return [log for log in logs if not log.get('allowed', True)]
    
    def generate_safety_report(self) -> str:
        """生成安全检查报告"""
        logs = self.get_audit_log(limit=1000)
        
        total = len(logs)
        allowed = len([l for l in logs if l.get('allowed')])
        blocked = total - allowed
        
        by_zone = {}
        for log in logs:
            zone = log.get('zone', 'unknown')
            by_zone[zone] = by_zone.get(zone, 0) + 1
        
        report = f"""# 三区安全检查报告

**生成时间**: {datetime.now().isoformat()}

## 📊 统计概览

| 指标 | 数量 |
|:---|:---:|
| 总检查次数 | {total} |
| ✅ 允许 | {allowed} |
| ❌ 阻止 | {blocked} |

### 按区域分布

"""
        for zone, count in sorted(by_zone.items()):
            emoji = "🔴" if zone == "red" else "🟡" if zone == "yellow" else "🟢" if zone == "green" else "⚪"
            report += f"| {emoji} {zone.upper()} | {count} |\n"
        
        # 最近的阻止事件
        blocked_logs = self.get_blocked_attempts()[-5:]
        report += "\n## 🚫 最近的阻止事件\n\n"
        if blocked_logs:
            for log in blocked_logs:
                report += f"- **{log['filepath']}** ({log['zone'].upper()}) - {log['timestamp']}\n"
                report += f"  原因: {log['reason']}\n"
        else:
            report += "_无阻止事件_\n"
        
        return report


# ==================== 装饰器 ====================

def safe_modify(checker: ZoneSafetyChecker = None):
    """装饰器: 安全的文件修改"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 获取文件路径（假设第一个参数是文件路径）
            filepath = args[0] if args else kwargs.get('filepath')
            
            if not filepath:
                return func(*args, **kwargs)
            
            c = checker or ZoneSafetyChecker()
            result = c.check_modification_allowed(filepath)
            
            if not result.allowed:
                c.log_audit(filepath, func.__name__, result)
                raise PermissionError(f"安全检查阻止: {result.reason}")
            
            # 记录GREEN ZONE操作
            c.log_audit(filepath, func.__name__, result)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ==================== CLI接口 ====================

if __name__ == "__main__":
    import sys
    
    checker = ZoneSafetyChecker()
    
    if len(sys.argv) < 2:
        print("Usage: python safety_checker.py <command> [args]")
        print("Commands:")
        print("  check <filepath>     - 检查文件安全区域")
        print("  zone <filepath>      - 显示文件所属区域")
        print("  report               - 生成安全报告")
        print("  blocked              - 显示阻止的尝试")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check" and len(sys.argv) >= 3:
        filepath = sys.argv[2]
        result = checker.check_modification_allowed(filepath)
        print(result)
    
    elif command == "zone" and len(sys.argv) >= 3:
        filepath = sys.argv[2]
        zone = checker.get_file_zone(filepath)
        print(f"{filepath} -> {zone.value.upper()} ZONE")
    
    elif command == "report":
        print(checker.generate_safety_report())
    
    elif command == "blocked":
        blocked = checker.get_blocked_attempts()
        print(f"被阻止的尝试 ({len(blocked)} 次):")
        for log in blocked[-10:]:
            print(f"  - {log['filepath']} ({log['zone']}) at {log['timestamp']}")
    
    else:
        print(f"Unknown command: {command}")
