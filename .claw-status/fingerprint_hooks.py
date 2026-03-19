#!/usr/bin/env python3
"""
Method Fingerprint Hooks - 方法指纹钩子
自动集成到工具调用流程中

在每次工具调用前后自动记录和复用指纹
"""

import sys
from pathlib import Path

# 添加方法指纹系统到路径
sys.path.insert(0, str(Path(__file__).parent))

from method_fingerprint import (
    check_before_execute,
    record_execution,
    get_fingerprint_system
)


class FingerprintHook:
    """工具调用钩子"""
    
    def __init__(self):
        self.system = get_fingerprint_system()
        self.current_task = None
        self.current_method = None
    
    def before_tool_call(self, tool_name: str, params: dict, task_context: dict = None) -> dict:
        """
        工具调用前检查
        
        Returns:
            {
                "should_proceed": bool,
                "message": str,  # 如果should_proceed=False
                "suggested_params": dict  # 如果有建议参数
            }
        """
        task_type = self._infer_task_type(tool_name, params)
        method = {"tool": tool_name, **params}
        
        result = check_before_execute(task_type, method)
        
        if result["action"] == "block":
            return {
                "should_proceed": False,
                "message": f"⚠️ 检测到已知的失败模式: {result['reason']}",
                "alternative": result.get("alternative")
            }
        
        if result["action"] == "reuse":
            return {
                "should_proceed": True,
                "message": f"✓ 复用成功模式 (置信度: {result['confidence']:.0%})",
                "suggested_params": result.get("suggested_params"),
                "fingerprint_id": result.get("fingerprint_id")
            }
        
        return {"should_proceed": True, "message": "proceeding with new method"}
    
    def after_tool_call(self, tool_name: str, params: dict, result: dict, tokens: int = 0):
        """工具调用后记录"""
        task_type = self._infer_task_type(tool_name, params)
        method = {"tool": tool_name, **params}
        
        # 判断成功/失败
        success = self._is_success(result)
        error = self._extract_error(result)
        
        record_execution(
            task_type=task_type,
            method=method,
            result={"success": success, "error": error},
            tokens=tokens
        )
    
    def _infer_task_type(self, tool_name: str, params: dict) -> str:
        """推断任务类型"""
        # 根据工具和参数推断任务类型
        if tool_name == "message" or tool_name == "cron":
            channel = params.get("channel", "")
            if channel == "feishu":
                if params.get("filePath") or params.get("buffer"):
                    return "send_feishu_image"
                return "send_feishu_message"
        
        if tool_name == "exec":
            cmd = params.get("command", "")
            if "pptxgen" in cmd or "create_port_ppt" in cmd:
                return "pptx_generate"
            if "libreoffice" in cmd and "pdftoppm" in cmd:
                return "convert_ppt_to_image"
        
        if tool_name == "web_search":
            return "web_search"
        
        if tool_name == "read" or tool_name == "write":
            return "file_operation"
        
        return f"{tool_name}_operation"
    
    def _is_success(self, result: dict) -> bool:
        """判断执行是否成功"""
        if isinstance(result, dict):
            # 检查常见错误字段
            if "error" in result and result["error"]:
                return False
            if "status" in result:
                return result["status"] in ["success", "ok", "completed"]
            # 检查是否有status字段且值为error
            status = result.get("status", "").lower()
            if "error" in status or "fail" in status:
                return False
        return True
    
    def _extract_error(self, result: dict) -> str:
        """提取错误信息"""
        if isinstance(result, dict):
            if "error" in result:
                return str(result["error"])
            if "message" in result and "error" in str(result.get("status", "")).lower():
                return str(result["message"])
        return ""


# 装饰器模式（用于包装工具调用）
def with_fingerprint(task_type: str = None):
    """
    工具调用装饰器
    
    用法:
        @with_fingerprint("send_feishu_image")
        def send_image(...):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            hook = FingerprintHook()
            
            # 提取参数
            tool_name = func.__name__
            params = kwargs
            
            # 检查前
            check_result = hook.before_tool_call(tool_name, params)
            
            if not check_result.get("should_proceed", True):
                alt = check_result.get("alternative")
                if alt:
                    return {
                        "error": check_result["message"],
                        "suggestion": f"建议改用: {alt}"
                    }
                return {"error": check_result["message"]}
            
            # 如果有建议参数，打印提示
            if "suggested_params" in check_result:
                print(f"💡 {check_result['message']}")
            
            # 执行
            result = func(*args, **kwargs)
            
            # 记录后
            hook.after_tool_call(tool_name, params, result)
            
            return result
        return wrapper
    return decorator


# 初始化钩子（在系统启动时调用）
def install_hooks():
    """安装钩子到系统"""
    print("✅ Method Fingerprint System 已激活")
    print(f"   数据库: {get_fingerprint_system().db.get('last_updated', 'N/A')}")
    return FingerprintHook()


if __name__ == "__main__":
    # 测试
    hook = FingerprintHook()
    
    # 模拟检查
    result = hook.before_tool_call("message", {
        "action": "send",
        "channel": "feishu",
        "filePath": "/tmp/test.png"
    })
    print(result)
