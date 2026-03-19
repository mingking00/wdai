#!/usr/bin/env python3
"""
Universal Method Fingerprint System - 通用方法指纹系统
自动拦截和记录所有工具调用

使用方法:
1. 导入: from universal_fingerprint import execute_with_fingerprint
2. 替换所有工具调用: result = execute_with_fingerprint(tool_name, params)

或者自动包装（推荐）:
from universal_fingerprint import enable_auto_wrap
enable_auto_wrap()  # 自动包装所有工具
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

DB_PATH = Path(__file__).parent / "method_fingerprints.json"


class UniversalFingerprintSystem:
    """通用方法指纹系统"""
    
    def __init__(self):
        self.db = self._load_db()
        self.execution_stack = []  # 执行栈，用于嵌套调用
    
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
    
    def _infer_task_type(self, tool_name: str, params: Dict) -> str:
        """
        智能推断任务类型 - 通用规则
        """
        # 规则1: 根据工具+关键参数组合
        signatures = []
        
        # 消息类
        if tool_name in ["message", "cron"]:
            channel = params.get("channel", "")
            if channel:
                if params.get("filePath") or params.get("buffer"):
                    signatures.append(f"send_{channel}_file")
                else:
                    signatures.append(f"send_{channel}_message")
        
        # 文件操作类
        if tool_name == "exec":
            cmd = params.get("command", "")
            if "pptxgen" in cmd or "create_ppt" in cmd:
                signatures.append("generate_pptx")
            elif "libreoffice" in cmd:
                signatures.append("convert_document")
            elif "git" in cmd:
                signatures.append("git_operation")
            elif "python" in cmd or "node" in cmd:
                signatures.append("script_execution")
        
        # 搜索类
        if tool_name == "web_search":
            signatures.append("web_search")
        
        if tool_name == "kimi_search":
            signatures.append("kimi_search")
        
        # 读写类
        if tool_name in ["read", "write", "edit"]:
            file_path = params.get("file_path", params.get("path", ""))
            ext = Path(file_path).suffix if file_path else ""
            signatures.append(f"file_{tool_name}{ext}")
        
        # API调用类
        if tool_name in ["feishu_doc", "feishu_drive", "feishu_wiki"]:
            action = params.get("action", "")
            signatures.append(f"{tool_name}_{action}")
        
        # 返回最具体的签名
        return signatures[0] if signatures else f"{tool_name}_operation"
    
    def check_before_execute(self, tool_name: str, params: Dict) -> Dict:
        """
        执行前检查 - 返回建议
        """
        task_type = self._infer_task_type(tool_name, params)
        method = {"tool": tool_name, **params}
        
        # 如果没有该任务类型的记录，允许执行
        if task_type not in self.db["fingerprints"]:
            return {
                "should_proceed": True,
                "task_type": task_type,
                "message": "No history, proceeding with new method",
                "is_new": True
            }
        
        fingerprint = self.db["fingerprints"][task_type]
        
        # 1. 检查黑名单
        for failure in fingerprint.get("failure_patterns", []):
            if failure.get("status") == "blacklisted":
                if self._match_method(method, failure.get("signature", {})):
                    return {
                        "should_proceed": False,
                        "task_type": task_type,
                        "message": f"⚠️ 此方法已被标记为失败模式: {failure.get('error_pattern', 'unknown')}",
                        "alternative": self._suggest_alternative(task_type),
                        "fingerprint_id": failure.get("id")
                    }
        
        # 2. 查找成功案例
        for success in fingerprint.get("success_patterns", []):
            if success.get("status") == "active":
                metrics = success.get("metrics", {})
                success_rate = metrics.get("success_rate", 0)
                
                if success_rate >= self.db["global_rules"]["success_confidence_threshold"]:
                    return {
                        "should_proceed": True,
                        "task_type": task_type,
                        "message": f"✓ 复用成功模式 (置信度: {success_rate:.0%})",
                        "suggested_params": success.get("optimal_params", {}),
                        "confidence": success_rate,
                        "fingerprint_id": success.get("id"),
                        "avg_tokens": metrics.get("avg_tokens", 0),
                        "is_new": False
                    }
        
        # 3. 有记录但不满足复用条件
        return {
            "should_proceed": True,
            "task_type": task_type,
            "message": "Proceeding with caution (low confidence history)",
            "is_new": False
        }
    
    def record_result(self, tool_name: str, params: Dict, result: Any, tokens: int = 0):
        """
        记录执行结果
        """
        task_type = self._infer_task_type(tool_name, params)
        method = {"tool": tool_name, **params}
        
        # 判断成功/失败
        success = self._is_success(result)
        error = self._extract_error(result)
        
        # 初始化任务类型记录
        if task_type not in self.db["fingerprints"]:
            self.db["fingerprints"][task_type] = {
                "category": self._categorize_task(task_type),
                "description": task_type,
                "success_patterns": [],
                "failure_patterns": []
            }
        
        fingerprint = self.db["fingerprints"][task_type]
        
        if success:
            self._update_success_pattern(fingerprint, method, tokens)
        else:
            self._update_failure_pattern(fingerprint, method, error)
        
        self._save_db()
    
    def execute_with_advice(self, tool_name: str, params: Dict, executor: Callable, *args, **kwargs) -> Dict:
        """
        带建议的执行 - 核心函数
        
        Args:
            tool_name: 工具名
            params: 参数
            executor: 实际执行函数
            *args, **kwargs: 传递给executor的参数
        
        Returns:
            {
                "success": bool,
                "result": Any,  # 实际执行结果
                "advice": Dict,  # 建议信息
                "tokens": int,   # 估算token
                "used_fingerprint": bool
            }
        """
        # 1. 检查建议
        advice = self.check_before_execute(tool_name, params)
        task_type = advice["task_type"]
        
        # 2. 如果被阻止，直接返回
        if not advice.get("should_proceed", True):
            return {
                "success": False,
                "result": None,
                "advice": advice,
                "error": advice["message"],
                "alternative": advice.get("alternative"),
                "tokens": 0,
                "used_fingerprint": True
            }
        
        # 3. 执行
        print(f"🔧 执行任务: {task_type}")
        if advice.get("suggested_params"):
            print(f"💡 建议: {advice['message']}")
        
        try:
            result = executor(*args, **kwargs)
            success = True
        except Exception as e:
            result = {"error": str(e)}
            success = False
        
        # 4. 记录结果
        # 估算token（简单估算）
        estimated_tokens = len(json.dumps(params)) + len(json.dumps(result))
        self.record_result(tool_name, params, result, estimated_tokens)
        
        return {
            "success": success,
            "result": result,
            "advice": advice,
            "tokens": estimated_tokens,
            "used_fingerprint": advice.get("fingerprint_id") is not None
        }
    
    def _match_method(self, method: Dict, signature: Dict) -> bool:
        """匹配方法签名"""
        for key, value in signature.items():
            if key == "tool" and method.get(key) != value:
                return False
            if key in method and method[key] != value:
                return False
        return True
    
    def _is_success(self, result: Any) -> bool:
        """判断成功/失败"""
        if isinstance(result, dict):
            if "error" in result and result["error"]:
                return False
            status = str(result.get("status", "")).lower()
            if "error" in status or "fail" in status:
                return False
        return True
    
    def _extract_error(self, result: Any) -> str:
        """提取错误信息"""
        if isinstance(result, dict):
            return str(result.get("error", result.get("message", "")))
        return ""
    
    def _categorize_task(self, task_type: str) -> str:
        """分类任务"""
        if "send" in task_type:
            return "messaging"
        if "search" in task_type:
            return "search"
        if "file" in task_type or "convert" in task_type:
            return "file_operation"
        if "pptx" in task_type or "doc" in task_type:
            return "document"
        return "general"
    
    def _update_success_pattern(self, fingerprint: Dict, method: Dict, tokens: int):
        """更新成功模式"""
        now = datetime.now().isoformat()
        
        # 查找或创建
        for pattern in fingerprint.get("success_patterns", []):
            if self._match_method(method, pattern.get("signature", {})):
                metrics = pattern["metrics"]
                metrics["execution_count"] = metrics.get("execution_count", 0) + 1
                metrics["last_success"] = now
                
                # 更新平均token
                old_avg = metrics.get("avg_tokens", 0)
                count = metrics["execution_count"]
                metrics["avg_tokens"] = (old_avg * (count - 1) + tokens) / count
                return
        
        # 新建
        new_pattern = {
            "id": f"fp_{len(fingerprint.get('success_patterns', [])) + 1:03d}",
            "signature": method,
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
    
    def _update_failure_pattern(self, fingerprint: Dict, method: Dict, error: str):
        """更新失败模式"""
        now = datetime.now().isoformat()
        
        for pattern in fingerprint.get("failure_patterns", []):
            if self._match_method(method, pattern.get("signature", {})):
                pattern["fail_count"] = pattern.get("fail_count", 0) + 1
                pattern["last_failure"] = now
                
                # 检查是否达到黑名单阈值
                if pattern["fail_count"] >= self.db["global_rules"]["blacklist_threshold"]:
                    pattern["status"] = "blacklisted"
                return
        
        # 新建
        new_pattern = {
            "id": f"ff_{len(fingerprint.get('failure_patterns', [])) + 1:03d}",
            "signature": method,
            "error_pattern": error[:100] if error else "unknown",
            "fail_count": 1,
            "first_failure": now,
            "status": "active"
        }
        fingerprint["failure_patterns"].append(new_pattern)
    
    def _extract_optimal_params(self, method: Dict) -> Dict:
        """提取最优参数模式"""
        optimal = {}
        
        # 提取消息长度模式
        if "message" in method:
            msg_len = len(str(method["message"]))
            optimal["message_length"] = "short" if msg_len < 200 else "medium" if msg_len < 1000 else "long"
        
        # 提取payload类型
        if "payload" in method and isinstance(method["payload"], dict):
            optimal["payload_kind"] = method["payload"].get("kind")
        
        # 提取文件类型
        if "filePath" in method:
            ext = Path(method["filePath"]).suffix
            optimal["file_type"] = ext if ext else "unknown"
        
        return optimal
    
    def _suggest_alternative(self, task_type: str) -> Optional[Dict]:
        """建议替代方案"""
        fingerprint = self.db["fingerprints"].get(task_type, {})
        
        for success in fingerprint.get("success_patterns", []):
            if success.get("status") == "active":
                return {
                    "method": success.get("signature"),
                    "params": success.get("optimal_params"),
                    "confidence": success["metrics"].get("success_rate", 0)
                }
        return None
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_tasks = len(self.db["fingerprints"])
        total_success = sum(
            len(f.get("success_patterns", []))
            for f in self.db["fingerprints"].values()
        )
        total_blacklisted = sum(
            sum(1 for p in f.get("failure_patterns", []) if p.get("status") == "blacklisted")
            for f in self.db["fingerprints"].values()
        )
        
        return {
            "total_task_types": total_tasks,
            "total_success_patterns": total_success,
            "total_blacklisted": total_blacklisted,
            "task_types": list(self.db["fingerprints"].keys())
        }


# 全局实例
_universal_system = None

def get_universal_system() -> UniversalFingerprintSystem:
    """获取全局实例"""
    global _universal_system
    if _universal_system is None:
        _universal_system = UniversalFingerprintSystem()
    return _universal_system


# 便捷函数
def check(tool_name: str, params: Dict) -> Dict:
    """快速检查"""
    return get_universal_system().check_before_execute(tool_name, params)

def execute(tool_name: str, params: Dict, executor: Callable, *args, **kwargs) -> Dict:
    """带建议的执行"""
    return get_universal_system().execute_with_advice(tool_name, params, executor, *args, **kwargs)

def record(tool_name: str, params: Dict, result: Any, tokens: int = 0):
    """记录结果"""
    return get_universal_system().record_result(tool_name, params, result, tokens)

def stats() -> Dict:
    """获取统计"""
    return get_universal_system().get_stats()


if __name__ == "__main__":
    # 测试
    print("📊 Universal Fingerprint System Stats:")
    print(json.dumps(stats(), indent=2))
