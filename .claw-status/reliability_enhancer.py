"""可靠性增强模块 - 自动生成"""
import traceback
from typing import Callable, Any, Dict

def with_retry(func: Callable, max_retries: int = 3) -> Dict[str, Any]:
    """带重试的函数执行"""
    for attempt in range(max_retries):
        try:
            return {"success": True, "result": func(), "attempts": attempt + 1}
        except Exception as e:
            if attempt == max_retries - 1:
                return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
    return {"success": False, "error": "所有重试都失败"}
