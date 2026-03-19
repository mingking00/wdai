"""
wdai v3.0 - Step Executor
SOP工作流引擎 - 步骤执行器

负责执行各种类型的步骤
"""

import asyncio
import time
import traceback
from typing import Dict, Any, Optional, Callable, Awaitable
from abc import ABC, abstractmethod
from datetime import datetime

from .models import Step, StepAction, StepStatus, StepState, ErrorInfo, RetryPolicy


class StepExecutionResult:
    """步骤执行结果"""
    
    def __init__(self, success: bool, output: Any = None, error: Optional[ErrorInfo] = None):
        self.success = success
        self.output = output
        self.error = error
        self.execution_time_ms: int = 0
    
    @property
    def failed(self) -> bool:
        return not self.success


class BaseExecutor(ABC):
    """执行器基类"""
    
    def __init__(self, action_type: StepAction):
        self.action_type = action_type
    
    @abstractmethod
    async def execute(self, step: Step, context: Dict[str, Any]) -> StepExecutionResult:
        """执行步骤"""
        pass
    
    def can_handle(self, action: StepAction) -> bool:
        """检查是否可以处理该动作类型"""
        return action == self.action_type


class LLMExecutor(BaseExecutor):
    """LLM调用执行器"""
    
    def __init__(self, llm_client=None):
        super().__init__(StepAction.LLM)
        self.llm_client = llm_client
    
    async def execute(self, step: Step, context: Dict[str, Any]) -> StepExecutionResult:
        """执行LLM调用"""
        config = step.config
        prompt = config.get("prompt", "")
        
        # 渲染模板
        try:
            prompt = prompt.format(**context)
        except KeyError as e:
            return StepExecutionResult(
                success=False,
                error=ErrorInfo(
                    step_id=step.id,
                    error_type="TemplateError",
                    error_message=f"Prompt模板变量缺失: {e}"
                )
            )
        
        # 调用LLM（模拟）
        try:
            if self.llm_client:
                response = await self.llm_client.generate(prompt)
            else:
                # 模拟延迟
                await asyncio.sleep(0.1)
                response = f"LLM响应: {prompt[:50]}..."
            
            return StepExecutionResult(success=True, output={
                "prompt": prompt,
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return StepExecutionResult(
                success=False,
                error=ErrorInfo(
                    step_id=step.id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=traceback.format_exc()
                )
            )


class ShellExecutor(BaseExecutor):
    """Shell命令执行器"""
    
    def __init__(self):
        super().__init__(StepAction.SHELL)
    
    async def execute(self, step: Step, context: Dict[str, Any]) -> StepExecutionResult:
        """执行Shell命令"""
        config = step.config
        command = config.get("command", "")
        
        if not command:
            return StepExecutionResult(
                success=False,
                error=ErrorInfo(
                    step_id=step.id,
                    error_type="ConfigError",
                    error_message="Shell命令为空"
                )
            )
        
        try:
            # 使用 asyncio 执行命令
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 设置超时
            timeout = step.timeout or 60
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return StepExecutionResult(
                    success=False,
                    error=ErrorInfo(
                        step_id=step.id,
                        error_type="TimeoutError",
                        error_message=f"命令执行超时（{timeout}秒）"
                    )
                )
            
            stdout_str = stdout.decode().strip() if stdout else ""
            stderr_str = stderr.decode().strip() if stderr else ""
            
            if proc.returncode != 0:
                return StepExecutionResult(
                    success=False,
                    error=ErrorInfo(
                        step_id=step.id,
                        error_type="CommandError",
                        error_message=f"命令返回非零状态: {proc.returncode}",
                        traceback=stderr_str
                    ),
                    output={
                        "stdout": stdout_str,
                        "stderr": stderr_str,
                        "returncode": proc.returncode
                    }
                )
            
            return StepExecutionResult(success=True, output={
                "stdout": stdout_str,
                "stderr": stderr_str,
                "returncode": proc.returncode
            })
            
        except Exception as e:
            return StepExecutionResult(
                success=False,
                error=ErrorInfo(
                    step_id=step.id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=traceback.format_exc()
                )
            )


class PythonExecutor(BaseExecutor):
    """Python代码执行器"""
    
    def __init__(self):
        super().__init__(StepAction.PYTHON)
    
    async def execute(self, step: Step, context: Dict[str, Any]) -> StepExecutionResult:
        """执行Python代码"""
        config = step.config
        code = config.get("code", "")
        
        if not code:
            return StepExecutionResult(
                success=False,
                error=ErrorInfo(
                    step_id=step.id,
                    error_type="ConfigError",
                    error_message="Python代码为空"
                )
            )
        
        try:
            # 创建执行环境
            exec_globals = {"__builtins__": __builtins__, "context": context}
            exec_globals.update(context)
            
            # 执行代码
            exec(code, exec_globals)
            
            # 获取结果（如果有result变量）
            result = exec_globals.get("result", None)
            
            return StepExecutionResult(success=True, output={
                "result": result,
                "code": code[:200]  # 截断显示
            })
            
        except Exception as e:
            return StepExecutionResult(
                success=False,
                error=ErrorInfo(
                    step_id=step.id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=traceback.format_exc()
                )
            )


class WaitExecutor(BaseExecutor):
    """等待执行器（用于条件等待）"""
    
    def __init__(self):
        super().__init__(StepAction.WAIT)
    
    async def execute(self, step: Step, context: Dict[str, Any]) -> StepExecutionResult:
        """等待指定时间或条件"""
        config = step.config
        
        # 等待固定时间
        if "duration" in config:
            duration = config["duration"]
            await asyncio.sleep(duration)
            return StepExecutionResult(success=True, output={
                "waited_seconds": duration
            })
        
        # 等待条件（简化版，实际可能更复杂）
        condition = config.get("condition")
        if condition:
            max_wait = config.get("max_wait", 60)
            check_interval = config.get("check_interval", 1)
            elapsed = 0
            
            while elapsed < max_wait:
                # 评估条件（这里简化处理）
                if condition in context and context[condition]:
                    return StepExecutionResult(success=True, output={
                        "condition_met": condition,
                        "waited_seconds": elapsed
                    })
                
                await asyncio.sleep(check_interval)
                elapsed += check_interval
            
            return StepExecutionResult(
                success=False,
                error=ErrorInfo(
                    step_id=step.id,
                    error_type="TimeoutError",
                    error_message=f"等待条件超时: {condition}"
                ),
                output={"waited_seconds": elapsed}
            )
        
        return StepExecutionResult(
            success=False,
            error=ErrorInfo(
                step_id=step.id,
                error_type="ConfigError",
                error_message="等待步骤需要duration或condition配置"
            )
        )


class CustomExecutor(BaseExecutor):
    """自定义执行器"""
    
    def __init__(self, handler: Optional[Callable] = None):
        super().__init__(StepAction.CUSTOM)
        self.handler = handler
    
    async def execute(self, step: Step, context: Dict[str, Any]) -> StepExecutionResult:
        """执行自定义逻辑"""
        if self.handler:
            try:
                if asyncio.iscoroutinefunction(self.handler):
                    result = await self.handler(step, context)
                else:
                    result = self.handler(step, context)
                
                return StepExecutionResult(success=True, output=result)
            except Exception as e:
                return StepExecutionResult(
                    success=False,
                    error=ErrorInfo(
                        step_id=step.id,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        traceback=traceback.format_exc()
                    )
                )
        
        return StepExecutionResult(
            success=False,
            error=ErrorInfo(
                step_id=step.id,
                error_type="ConfigError",
                error_message="自定义步骤未设置处理器"
            )
        )


class ExecutorRegistry:
    """执行器注册表"""
    
    def __init__(self):
        self._executors: Dict[StepAction, BaseExecutor] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """注册默认执行器"""
        self.register(LLMExecutor())
        self.register(ShellExecutor())
        self.register(PythonExecutor())
        self.register(WaitExecutor())
        self.register(CustomExecutor())
    
    def register(self, executor: BaseExecutor):
        """注册执行器"""
        self._executors[executor.action_type] = executor
    
    def get(self, action: StepAction) -> Optional[BaseExecutor]:
        """获取执行器"""
        return self._executors.get(action)
    
    async def execute(
        self,
        step: Step,
        context: Dict[str, Any],
        retry_policy: Optional[RetryPolicy] = None
    ) -> StepExecutionResult:
        """
        执行步骤（带重试）
        
        Args:
            step: 要执行的步骤
            context: 执行上下文
            retry_policy: 重试策略
        
        Returns:
            执行结果
        """
        executor = self.get(step.action)
        if not executor:
            return StepExecutionResult(
                success=False,
                error=ErrorInfo(
                    step_id=step.id,
                    error_type="ExecutorError",
                    error_message=f"未找到执行器: {step.action}"
                )
            )
        
        retry_policy = retry_policy or step.retry_policy
        last_error = None
        
        for attempt in range(retry_policy.max_retries + 1):
            start_time = time.time()
            
            try:
                result = await executor.execute(step, context)
                result.execution_time_ms = int((time.time() - start_time) * 1000)
                
                if result.success:
                    return result
                
                last_error = result.error
                
                # 检查是否需要重试
                if attempt < retry_policy.max_retries:
                    delay = retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                last_error = ErrorInfo(
                    step_id=step.id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=traceback.format_exc()
                )
                
                if attempt < retry_policy.max_retries:
                    delay = retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
        
        # 所有重试都失败
        return StepExecutionResult(
            success=False,
            error=last_error
        )


# 全局执行器注册表
_default_registry = None

def get_executor_registry() -> ExecutorRegistry:
    """获取默认执行器注册表"""
    global _default_registry
    if _default_registry is None:
        _default_registry = ExecutorRegistry()
    return _default_registry
