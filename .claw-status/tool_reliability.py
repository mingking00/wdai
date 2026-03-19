#!/usr/bin/env python3
"""
Tool Call Reliability Enhancement
工具调用可靠性优化

核心策略:
1. 前置验证 - 调用前检查参数合法性
2. 重试机制 - 失败时自动重试 + 指数退避
3. 降级策略 - 主方法失败时切换备选方案
4. 结果验证 - 调用后验证输出有效性
5. 错误分类 - 区分可恢复/不可恢复错误
"""

import time
import json
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from functools import wraps


class ErrorType(Enum):
    """错误类型分类"""
    TRANSIENT = "transient"      # 临时错误，可重试
    PERMANENT = "permanent"      # 永久错误，需换方法
    VALIDATION = "validation"    # 参数错误，需修正
    TIMEOUT = "timeout"          # 超时，可重试
    RATE_LIMIT = "rate_limit"    # 限流，需等待


@dataclass
class ToolResult:
    """工具调用结果"""
    success: bool
    data: Any
    error_type: Optional[ErrorType]
    error_message: str
    attempts: int
    duration_ms: float
    fallback_used: bool = False


class ToolValidator:
    """工具参数预验证器"""
    
    @staticmethod
    def validate_file_path(path: str) -> Tuple[bool, str]:
        """验证文件路径"""
        import os
        
        # 检查空路径
        if not path or not path.strip():
            return False, "路径不能为空"
        
        # 检查非法字符
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in path:
                return False, f"路径包含非法字符: {char}"
        
        # 检查路径长度
        if len(path) > 4096:
            return False, "路径过长"
        
        return True, "OK"
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """验证URL"""
        if not url.startswith(('http://', 'https://')):
            return False, "URL必须以http://或https://开头"
        
        if len(url) > 2048:
            return False, "URL过长"
        
        return True, "OK"
    
    @staticmethod
    def validate_api_params(params: Dict, required: List[str]) -> Tuple[bool, str]:
        """验证API参数"""
        for key in required:
            if key not in params or params[key] is None:
                return False, f"缺少必需参数: {key}"
        
        return True, "OK"


class RetryStrategy:
    """重试策略"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_errors: List[ErrorType] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_errors = retryable_errors or [
            ErrorType.TRANSIENT,
            ErrorType.TIMEOUT,
            ErrorType.RATE_LIMIT
        ]
    
    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """判断是否应重试"""
        if attempt >= self.max_attempts:
            return False
        
        if error_type not in self.retryable_errors:
            return False
        
        return True
    
    def get_delay(self, attempt: int) -> float:
        """计算延迟时间 (指数退避)"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class ToolExecutor:
    """
    可靠的工具执行器
    
    使用示例:
        executor = ToolExecutor()
        
        @executor.register(
            name="file_read",
            validators=[ToolValidator.validate_file_path],
            retry_strategy=RetryStrategy(max_attempts=3)
        )
        def read_file(path: str):
            with open(path, 'r') as f:
                return f.read()
        
        # 执行
        result = executor.execute("file_read", path="/path/to/file")
    """
    
    def __init__(self):
        self.tools: Dict[str, Dict] = {}
        self.fallbacks: Dict[str, List[str]] = {}  # 主工具 -> 备选工具列表
    
    def register(
        self,
        name: str,
        validators: List[Callable] = None,
        retry_strategy: RetryStrategy = None,
        timeout: float = 30.0
    ):
        """注册工具的装饰器"""
        def decorator(func: Callable):
            self.tools[name] = {
                'func': func,
                'validators': validators or [],
                'retry': retry_strategy or RetryStrategy(),
                'timeout': timeout
            }
            return func
        return decorator
    
    def register_fallback(self, primary: str, fallback: str):
        """注册备选工具"""
        if primary not in self.fallbacks:
            self.fallbacks[primary] = []
        self.fallbacks[primary].append(fallback)
    
    def classify_error(self, error: Exception) -> ErrorType:
        """分类错误类型"""
        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 限流错误
        if any(x in error_msg for x in ['rate limit', 'too many requests', '429']):
            return ErrorType.RATE_LIMIT
        
        # 超时错误
        if any(x in error_msg for x in ['timeout', 'timed out']):
            return ErrorType.TIMEOUT
        
        # 临时网络错误
        if any(x in error_msg for x in ['connection', 'network', 'temporary']):
            return ErrorType.TRANSIENT
        
        # 参数错误
        if any(x in error_msg for x in ['invalid', 'bad request', 'validation']):
            return ErrorType.VALIDATION
        
        # 默认永久错误
        return ErrorType.PERMANENT
    
    def validate_params(
        self,
        tool_name: str,
        kwargs: Dict
    ) -> Tuple[bool, str]:
        """验证参数"""
        if tool_name not in self.tools:
            return False, f"未知工具: {tool_name}"
        
        tool = self.tools[tool_name]
        
        for validator in tool['validators']:
            # 获取验证器需要的参数
            import inspect
            sig = inspect.signature(validator)
            param_names = list(sig.parameters.keys())
            
            # 构建验证参数
            validate_args = {}
            for param_name in param_names:
                if param_name in kwargs:
                    validate_args[param_name] = kwargs[param_name]
            
            if validate_args:
                valid, message = validator(**validate_args)
                if not valid:
                    return False, message
        
        return True, "OK"
    
    def execute(
        self,
        tool_name: str,
        **kwargs
    ) -> ToolResult:
        """
        执行工具
        
        完整流程:
        1. 参数验证
        2. 尝试执行 (带重试)
        3. 失败时尝试备选工具
        4. 结果验证
        """
        start_time = time.time()
        
        # 1. 参数验证
        valid, message = self.validate_params(tool_name, kwargs)
        if not valid:
            return ToolResult(
                success=False,
                data=None,
                error_type=ErrorType.VALIDATION,
                error_message=message,
                attempts=0,
                duration_ms=(time.time() - start_time) * 1000
            )
        
        # 2. 尝试主工具
        result = self._execute_with_retry(tool_name, kwargs)
        
        # 3. 失败时尝试备选
        if not result.success and tool_name in self.fallbacks:
            for fallback_name in self.fallbacks[tool_name]:
                if fallback_name in self.tools:
                    print(f"🔄 尝试备选工具: {fallback_name}")
                    fallback_result = self._execute_with_retry(fallback_name, kwargs)
                    
                    if fallback_result.success:
                        fallback_result.fallback_used = True
                        return fallback_result
        
        return result
    
    def _execute_with_retry(
        self,
        tool_name: str,
        kwargs: Dict
    ) -> ToolResult:
        """带重试的执行"""
        tool = self.tools[tool_name]
        retry = tool['retry']
        
        attempt = 0
        last_error = None
        
        while attempt < retry.max_attempts:
            attempt += 1
            
            try:
                start = time.time()
                result = tool['func'](**kwargs)
                duration = (time.time() - start) * 1000
                
                # 验证结果
                if self._validate_result(result):
                    return ToolResult(
                        success=True,
                        data=result,
                        error_type=None,
                        error_message="",
                        attempts=attempt,
                        duration_ms=duration
                    )
                else:
                    return ToolResult(
                        success=False,
                        data=None,
                        error_type=ErrorType.VALIDATION,
                        error_message="结果验证失败",
                        attempts=attempt,
                        duration_ms=duration
                    )
                    
            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)
                
                print(f"⚠️ 尝试 {attempt}/{retry.max_attempts} 失败: {e}")
                
                # 检查是否应该重试
                if retry.should_retry(error_type, attempt):
                    delay = retry.get_delay(attempt)
                    print(f"⏱️ 等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
                else:
                    break
        
        # 所有尝试失败
        return ToolResult(
            success=False,
            data=None,
            error_type=self.classify_error(last_error) if last_error else ErrorType.PERMANENT,
            error_message=str(last_error) if last_error else "未知错误",
            attempts=attempt,
            duration_ms=(time.time() - time.time()) * 1000
        )
    
    def _validate_result(self, result: Any) -> bool:
        """验证结果有效性"""
        # 基础验证：结果不为None
        if result is None:
            return False
        
        # 字符串结果：不为空
        if isinstance(result, str) and len(result.strip()) == 0:
            return False
        
        # 列表/字典结果：不为空
        if isinstance(result, (list, dict)) and len(result) == 0:
            return False
        
        return True


# ==================== 实际使用示例 ====================

# 创建执行器
executor = ToolExecutor()

# 注册工具
@executor.register(
    name="web_search",
    validators=[ToolValidator.validate_url],
    retry_strategy=RetryStrategy(
        max_attempts=3,
        base_delay=2.0,
        retryable_errors=[ErrorType.TRANSIENT, ErrorType.TIMEOUT, ErrorType.RATE_LIMIT]
    )
)
def web_search(query: str):
    """网络搜索 (模拟)"""
    # 模拟有时失败
    import random
    if random.random() < 0.3:
        raise Exception("Connection timeout")
    return f"搜索结果: {query}"

@executor.register(
    name="local_search",
    retry_strategy=RetryStrategy(max_attempts=2)
)
def local_search(query: str):
    """本地搜索 (备选)"""
    return f"本地缓存结果: {query}"

# 注册备选
executor.register_fallback("web_search", "local_search")


# ==================== 测试 ====================

if __name__ == "__main__":
    print("="*60)
    print("Tool Call Reliability - 测试")
    print("="*60)
    
    # 测试1: 正常调用
    print("\n1. 正常调用测试")
    result = executor.execute("web_search", query="Python教程")
    print(f"   成功: {result.success}")
    print(f"   尝试次数: {result.attempts}")
    print(f"   耗时: {result.duration_ms:.0f}ms")
    if result.success:
        print(f"   结果: {result.data}")
    
    # 测试2: 参数验证失败
    print("\n2. 参数验证测试")
    result = executor.execute("web_search", query="")  # 空查询
    print(f"   成功: {result.success}")
    print(f"   错误类型: {result.error_type}")
    print(f"   错误信息: {result.error_message}")
    
    # 测试3: 多次运行观察重试
    print("\n3. 重试机制测试 (运行5次观察)")
    for i in range(5):
        result = executor.execute("web_search", query="测试")
        status = "✅" if result.success else "❌"
        fallback = " (备选)" if result.fallback_used else ""
        print(f"   {status} 第{i+1}次: {result.attempts}次尝试{fallback}")
    
    # 测试4: 统计
    print("\n4. 工具注册信息")
    for name in executor.tools:
        tool = executor.tools[name]
        print(f"   {name}:")
        print(f"      验证器: {len(tool['validators'])}个")
        print(f"      最大重试: {tool['retry'].max_attempts}")
        print(f"      超时: {tool['timeout']}秒")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
