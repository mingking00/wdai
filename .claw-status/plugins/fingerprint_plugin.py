"""
Fingerprint Plugin - 方法指纹插件
自动记录和复用成功/失败模式
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from framework import UniversalPlugin, InterceptResult, ToolContext, TaskContext
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import hashlib
import json


class FingerprintPlugin(UniversalPlugin):
    """
    方法指纹系统插件
    自动推断任务类型，记录成功/失败模式
    """
    
    name = "fingerprint_system"
    version = "2.0.0"
    priority = 20  # 在原则检查之后执行
    
    DB_PATH = Path("/root/.openclaw/workspace/.claw-status/data/fingerprints.json")
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.db = self._load_db()
        self.current_task_methods: Dict[str, List[str]] = {}  # 任务ID -> 已使用方法
    
    def _load_db(self) -> Dict:
        """加载指纹数据库"""
        if self.DB_PATH.exists():
            with open(self.DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "2.0",
            "last_updated": datetime.now().isoformat(),
            "fingerprints": {},
            "global_rules": {
                "blacklist_threshold": self.config.get("blacklist_threshold", 2),
                "reuse_threshold": self.config.get("reuse_threshold", 0.8)
            }
        }
    
    def _save_db(self):
        """保存指纹数据库"""
        self.db["last_updated"] = datetime.now().isoformat()
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)
    
    def _infer_task_type(self, tool_name: str, params: Dict) -> str:
        """
        智能推断任务类型
        """
        # 消息类
        if tool_name in ["message", "cron"]:
            channel = params.get("channel", "")
            if channel:
                if params.get("filePath") or params.get("buffer"):
                    return f"send_{channel}_file"
                return f"send_{channel}_message"
        
        # 文件操作类
        if tool_name == "exec":
            cmd = params.get("command", "")
            if "pptxgen" in cmd or "create_ppt" in cmd:
                return "generate_pptx"
            elif "libreoffice" in cmd or "pdftoppm" in cmd:
                return "convert_document"
            elif "git" in cmd:
                return "git_operation"
            elif "python" in cmd:
                return "python_execution"
            elif "node" in cmd:
                return "node_execution"
        
        # 搜索类
        if tool_name in ["web_search", "kimi_search"]:
            return f"{tool_name}_query"
        
        # 读写类
        if tool_name in ["read", "write", "edit"]:
            path = params.get("file_path", params.get("path", ""))
            ext = Path(path).suffix if path else ""
            return f"file_{tool_name}{ext}"
        
        # API类
        if tool_name.startswith("feishu_"):
            action = params.get("action", "")
            return f"{tool_name}_{action}"
        
        # 浏览器类
        if tool_name == "browser":
            action = params.get("action", "")
            return f"browser_{action}"
        
        return f"{tool_name}_operation"
    
    def on_tool_before(self, context: ToolContext) -> InterceptResult:
        """
        工具调用前检查指纹库
        """
        task_type = self._infer_task_type(context.tool_name, context.params)
        context.metadata["task_type"] = task_type
        
        # 检查是否有该任务的记录
        if task_type not in self.db["fingerprints"]:
            return InterceptResult.proceed()
        
        fingerprint = self.db["fingerprints"][task_type]
        method_sig = self._generate_signature(context.tool_name, context.params)
        
        # 1. 检查黑名单
        for failure in fingerprint.get("failure_patterns", []):
            if failure.get("status") == "blacklisted":
                if failure.get("signature_hash") == method_sig:
                    return InterceptResult.block(
                        reason=f"🚫 此方法已被标记为失败 ({failure.get('fail_count')}次失败): {failure.get('error_pattern', 'unknown')}",
                        alternative=self._suggest_alternative(task_type)
                    )
        
        # 2. 查找成功案例
        best_match = None
        best_confidence = 0
        
        for success in fingerprint.get("success_patterns", []):
            if success.get("status") != "active":
                continue
            
            metrics = success.get("metrics", {})
            success_rate = metrics.get("success_rate", 0)
            
            if success_rate >= self.db["global_rules"]["reuse_threshold"]:
                if success_rate > best_confidence:
                    best_confidence = success_rate
                    best_match = success
        
        if best_match:
            self.logger(f"💡 复用成功模式: {task_type} (置信度: {best_confidence:.0%})")
            context.suggested_params = best_match.get("optimal_params", {})
            context.metadata["fingerprint_id"] = best_match.get("id")
        
        return InterceptResult.proceed()
    
    def on_tool_after(self, context: ToolContext, result: Any):
        """
        工具调用后记录结果
        """
        task_type = context.metadata.get("task_type") or self._infer_task_type(
            context.tool_name, context.params
        )
        
        # 初始化任务类型记录
        if task_type not in self.db["fingerprints"]:
            self.db["fingerprints"][task_type] = {
                "category": self._categorize_task(task_type),
                "description": task_type,
                "success_patterns": [],
                "failure_patterns": []
            }
        
        fingerprint = self.db["fingerprints"][task_type]
        method_sig = self._generate_signature(context.tool_name, context.params)
        
        # 判断成功/失败
        success = self._is_success(result)
        
        if success:
            self._update_success_pattern(fingerprint, context, method_sig)
        else:
            self._update_failure_pattern(fingerprint, context, method_sig, result)
        
        self._save_db()
    
    def on_tool_error(self, context: ToolContext, error: Exception):
        """
        工具调用错误记录
        """
        self.on_tool_after(context, {"error": str(error), "status": "error"})
    
    def _generate_signature(self, tool_name: str, params: Dict) -> str:
        """生成方法签名"""
        # 提取关键特征
        sig = {
            "tool": tool_name,
            "action": params.get("action"),
            "channel": params.get("channel"),
            "payload_kind": params.get("payload", {}).get("kind") if isinstance(params.get("payload"), dict) else None
        }
        sig_str = json.dumps(sig, sort_keys=True)
        return hashlib.md5(sig_str.encode()).hexdigest()[:12]
    
    def _is_success(self, result: Any) -> bool:
        """判断执行是否成功"""
        if isinstance(result, dict):
            if "error" in result and result["error"]:
                return False
            if "success" in result:
                return result["success"]
            status = str(result.get("status", "")).lower()
            if "error" in status or "fail" in status:
                return False
        return True
    
    def _update_success_pattern(self, fingerprint: Dict, context: ToolContext, sig: str):
        """更新成功模式"""
        now = datetime.now().isoformat()
        
        for pattern in fingerprint["success_patterns"]:
            if pattern.get("signature_hash") == sig:
                metrics = pattern["metrics"]
                metrics["execution_count"] = metrics.get("execution_count", 0) + 1
                metrics["last_success"] = now
                
                # 更新平均token
                old_avg = metrics.get("avg_tokens", 0)
                count = metrics["execution_count"]
                tokens = context.token_usage or 1000
                metrics["avg_tokens"] = (old_avg * (count - 1) + tokens) / count
                return
        
        # 新建成功模式
        new_pattern = {
            "id": f"fp_{len(fingerprint['success_patterns']) + 1:03d}",
            "signature": {"tool": context.tool_name, **context.params},
            "signature_hash": sig,
            "optimal_params": self._extract_optimal_params(context.params),
            "metrics": {
                "success_rate": 1.0,
                "avg_tokens": context.token_usage or 1000,
                "execution_count": 1,
                "first_success": now,
                "last_success": now
            },
            "status": "active"
        }
        fingerprint["success_patterns"].append(new_pattern)
    
    def _update_failure_pattern(self, fingerprint: Dict, context: ToolContext, sig: str, result: Any):
        """更新失败模式"""
        now = datetime.now().isoformat()
        error = str(result.get("error", "unknown")) if isinstance(result, dict) else "unknown"
        
        for pattern in fingerprint["failure_patterns"]:
            if pattern.get("signature_hash") == sig:
                pattern["fail_count"] = pattern.get("fail_count", 0) + 1
                pattern["last_failure"] = now
                
                # 检查是否达到黑名单阈值
                if pattern["fail_count"] >= self.db["global_rules"]["blacklist_threshold"]:
                    pattern["status"] = "blacklisted"
                    self.logger(f"🚫 方法已加入黑名单: {pattern['error_pattern'][:50]}")
                return
        
        # 新建失败模式
        new_pattern = {
            "id": f"ff_{len(fingerprint['failure_patterns']) + 1:03d}",
            "signature": {"tool": context.tool_name, **context.params},
            "signature_hash": sig,
            "error_pattern": error[:100],
            "fail_count": 1,
            "first_failure": now,
            "status": "active"
        }
        fingerprint["failure_patterns"].append(new_pattern)
    
    def _extract_optimal_params(self, params: Dict) -> Dict:
        """提取最优参数"""
        optimal = {}
        
        if "message" in params:
            msg_len = len(str(params["message"]))
            optimal["message_length"] = "short" if msg_len < 200 else "long"
        
        if "payload" in params and isinstance(params["payload"], dict):
            optimal["payload_kind"] = params["payload"].get("kind")
        
        return optimal
    
    def _suggest_alternative(self, task_type: str) -> Optional[Dict]:
        """建议替代方案"""
        fingerprint = self.db["fingerprints"].get(task_type, {})
        
        for success in fingerprint.get("success_patterns", []):
            if success.get("status") == "active":
                return {
                    "method": success.get("signature"),
                    "confidence": success["metrics"].get("success_rate", 0)
                }
        return None
    
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
    
    def get_report(self) -> Dict:
        """获取指纹报告"""
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


if __name__ == "__main__":
    # 测试
    plugin = FingerprintPlugin()
    print(plugin.get_report())
