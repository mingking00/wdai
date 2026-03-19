#!/usr/bin/env python3
"""
Method Fingerprint System - 方法指纹系统
自动记录成功案例，避免重复试错

Version: 1.0
Author: wdai
Date: 2026-03-18
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

DB_PATH = Path(__file__).parent / "method_fingerprints.json"


class MethodFingerprintSystem:
    """方法指纹系统主类"""
    
    def __init__(self):
        self.db = self._load_db()
    
    def _load_db(self) -> Dict:
        """加载指纹数据库"""
        if DB_PATH.exists():
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "fingerprints": {},
            "global_rules": {
                "max_retries": 2,
                "blacklist_threshold": 2,
                "success_confidence_threshold": 0.8,
                "auto_reuse_enabled": True
            }
        }
    
    def _save_db(self):
        """保存指纹数据库"""
        self.db["last_updated"] = datetime.now().isoformat()
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)
    
    def _generate_signature(self, method: Dict) -> str:
        """生成方法签名（用于匹配）"""
        # 提取关键特征
        signature = {
            "tool": method.get("tool"),
            "action": method.get("action"),
            "channel": method.get("channel"),
            "payload_kind": method.get("payload", {}).get("kind") if isinstance(method.get("payload"), dict) else None
        }
        # 生成哈希
        sig_str = json.dumps(signature, sort_keys=True)
        return hashlib.md5(sig_str.encode()).hexdigest()[:12]
    
    def check_before_execute(self, task_type: str, proposed_method: Dict) -> Dict:
        """
        执行前检查：查找历史成功案例和黑名单
        
        Returns:
            {
                "action": "reuse" | "block" | "proceed",
                "reason": str,
                "suggested_params": Dict (if action=reuse),
                "confidence": float (if action=reuse)
            }
        """
        if task_type not in self.db["fingerprints"]:
            return {"action": "proceed", "reason": "no_history"}
        
        fingerprint = self.db["fingerprints"][task_type]
        proposed_sig = self._generate_signature(proposed_method)
        
        # 1. 检查黑名单
        for failure in fingerprint.get("failure_patterns", []):
            if failure.get("status") == "blacklisted":
                # 检查是否匹配
                if self._match_signature(proposed_method, failure.get("signature", {})):
                    return {
                        "action": "block",
                        "reason": f"Known failure pattern: {failure.get('error_pattern', 'unknown')}",
                        "alternative": self._suggest_alternative(task_type)
                    }
        
        # 2. 查找成功案例
        for success in fingerprint.get("success_patterns", []):
            if success.get("status") == "active":
                metrics = success.get("metrics", {})
                success_rate = metrics.get("success_rate", 0)
                
                if success_rate >= self.db["global_rules"]["success_confidence_threshold"]:
                    return {
                        "action": "reuse",
                        "reason": f"Found successful pattern with {success_rate:.0%} success rate",
                        "suggested_params": success.get("optimal_params", {}),
                        "confidence": success_rate,
                        "fingerprint_id": success.get("id")
                    }
        
        return {"action": "proceed", "reason": "no_confident_pattern"}
    
    def record_execution(self, task_type: str, method: Dict, result: Dict, tokens: int = 0):
        """
        执行后记录结果
        
        Args:
            task_type: 任务类型（如 send_feishu_image）
            method: 使用的方法参数
            result: 执行结果 {"success": bool, "error": str|None}
            tokens: 消耗的token数
        """
        if task_type not in self.db["fingerprints"]:
            self.db["fingerprints"][task_type] = {
                "category": "uncategorized",
                "description": task_type,
                "success_patterns": [],
                "failure_patterns": []
            }
        
        fingerprint = self.db["fingerprints"][task_type]
        
        if result.get("success"):
            self._record_success(fingerprint, method, tokens)
        else:
            self._record_failure(fingerprint, method, result.get("error"), tokens)
        
        self._save_db()
    
    def _record_success(self, fingerprint: Dict, method: Dict, tokens: int):
        """记录成功案例"""
        sig = self._generate_signature(method)
        now = datetime.now().isoformat()
        
        # 查找是否已存在
        for pattern in fingerprint.get("success_patterns", []):
            if pattern.get("signature_hash") == sig:
                # 更新统计
                metrics = pattern["metrics"]
                metrics["execution_count"] = metrics.get("execution_count", 0) + 1
                metrics["last_success"] = now
                # 更新平均token
                old_avg = metrics.get("avg_tokens", 0)
                count = metrics["execution_count"]
                metrics["avg_tokens"] = (old_avg * (count - 1) + tokens) / count
                metrics["success_rate"] = 1.0  # 保持成功
                return
        
        # 创建新记录
        new_pattern = {
            "id": f"fp_{len(fingerprint.get('success_patterns', [])) + 1:03d}",
            "signature": method,
            "signature_hash": sig,
            "optimal_params": self._extract_optimal_params(method),
            "metrics": {
                "success_rate": 1.0,
                "avg_tokens": tokens,
                "execution_count": 1,
                "first_success": now,
                "last_success": now
            },
            "status": "active"
        }
        
        fingerprint["success_patterns"].append(new_pattern)
    
    def _record_failure(self, fingerprint: Dict, method: Dict, error: str, tokens: int):
        """记录失败案例"""
        sig = self._generate_signature(method)
        now = datetime.now().isoformat()
        
        # 查找是否已存在
        for pattern in fingerprint.get("failure_patterns", []):
            if pattern.get("signature_hash") == sig:
                pattern["fail_count"] = pattern.get("fail_count", 0) + 1
                pattern["last_failure"] = now
                
                # 检查是否达到黑名单阈值
                if pattern["fail_count"] >= self.db["global_rules"]["blacklist_threshold"]:
                    pattern["status"] = "blacklisted"
                return
        
        # 创建新记录
        new_pattern = {
            "id": f"ff_{len(fingerprint.get('failure_patterns', [])) + 1:03d}",
            "signature": method,
            "signature_hash": sig,
            "error_pattern": error[:100] if error else "unknown",
            "fail_count": 1,
            "first_failure": now,
            "status": "active"
        }
        
        fingerprint["failure_patterns"].append(new_pattern)
    
    def _match_signature(self, method: Dict, signature: Dict) -> bool:
        """检查方法是否匹配签名"""
        for key, value in signature.items():
            if key == "tools":
                # 特殊处理工具链匹配
                if not all(t in str(method) for t in value):
                    return False
            elif method.get(key) != value:
                return False
        return True
    
    def _extract_optimal_params(self, method: Dict) -> Dict:
        """从成功方法中提取最优参数"""
        # 提取关键参数（排除具体值，保留模式）
        optimal = {}
        
        if "message" in method:
            msg = method["message"]
            optimal["message_length"] = "short" if len(str(msg)) < 200 else "long"
            optimal["include_context"] = "context" in str(msg).lower()
        
        if "payload" in method and isinstance(method["payload"], dict):
            optimal["payload_kind"] = method["payload"].get("kind")
        
        return optimal
    
    def _suggest_alternative(self, task_type: str) -> Optional[Dict]:
        """当被阻塞时，建议替代方案"""
        fingerprint = self.db["fingerprints"].get(task_type, {})
        
        for success in fingerprint.get("success_patterns", []):
            if success.get("status") == "active":
                return {
                    "method": success.get("signature"),
                    "params": success.get("optimal_params"),
                    "confidence": success["metrics"].get("success_rate", 0)
                }
        
        return None
    
    def get_report(self) -> str:
        """生成系统报告"""
        lines = ["📊 Method Fingerprint System Report", "=" * 50]
        
        total_tasks = len(self.db["fingerprints"])
        total_success = sum(
            len(f.get("success_patterns", []))
            for f in self.db["fingerprints"].values()
        )
        total_blacklisted = sum(
            sum(1 for p in f.get("failure_patterns", []) if p.get("status") == "blacklisted")
            for f in self.db["fingerprints"].values()
        )
        
        lines.extend([
            f"Total task types: {total_tasks}",
            f"Success patterns: {total_success}",
            f"Blacklisted methods: {total_blacklisted}",
            "",
            "Active Success Patterns:"
        ])
        
        for task_type, data in self.db["fingerprints"].items():
            for pattern in data.get("success_patterns", []):
                if pattern.get("status") == "active":
                    metrics = pattern["metrics"]
                    lines.append(
                        f"  ✓ {task_type}: {metrics.get('success_rate', 0):.0%} success, "
                        f"{metrics.get('execution_count', 0)} executions"
                    )
        
        if total_blacklisted > 0:
            lines.extend(["", "Blacklisted Methods (avoid):"])
            for task_type, data in self.db["fingerprints"].items():
                for pattern in data.get("failure_patterns", []):
                    if pattern.get("status") == "blacklisted":
                        lines.append(f"  ✗ {task_type}: {pattern.get('error_pattern', 'unknown')}")
        
        return "\n".join(lines)


# 全局实例
_fingerprint_system = None

def get_fingerprint_system() -> MethodFingerprintSystem:
    """获取指纹系统实例（单例）"""
    global _fingerprint_system
    if _fingerprint_system is None:
        _fingerprint_system = MethodFingerprintSystem()
    return _fingerprint_system


# 便捷函数
def check_before_execute(task_type: str, method: Dict) -> Dict:
    """执行前检查"""
    return get_fingerprint_system().check_before_execute(task_type, method)

def record_execution(task_type: str, method: Dict, result: Dict, tokens: int = 0):
    """记录执行结果"""
    get_fingerprint_system().record_execution(task_type, method, result, tokens)

def get_report() -> str:
    """获取报告"""
    return get_fingerprint_system().get_report()


if __name__ == "__main__":
    # 测试运行
    print(get_report())
