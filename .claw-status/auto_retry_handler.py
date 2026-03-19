"""自动生成的重试处理模块"""
import time
import random
from typing import Callable, Any, Dict, Optional
from functools import wraps

def with_retry(max_retries: int = 3, backoff: bool = True):
    """装饰器：为函数添加重试机制"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    return {
                        "success": True,
                        "result": result,
                        "attempts": attempt + 1
                    }
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        if backoff:
                            # 指数退避
                            sleep_time = (2 ** attempt) + random.uniform(0, 1)
                            time.sleep(sleep_time)
            
            return {
                "success": False,
                "error": str(last_exception),
                "attempts": max_retries
            }
        
        return wrapper
    return decorator

def with_fallback(fallback_value: Any):
    """装饰器：失败时返回默认值"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                return fallback_value
        return wrapper
    return decorator
