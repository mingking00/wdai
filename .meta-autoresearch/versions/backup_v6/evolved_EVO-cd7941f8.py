
def record_ier(phase: str):
    """自动记录IER的装饰器"""
    def decorator(func):
        async def wrapper(self, task, *args, **kwargs):
            result = await func(self, task, *args, **kwargs)
            
            # 自动提取洞察
            insight = self._extract_insight(func.__name__, result)
            
            # 记录IER
            self.ier.record(
                task_id=task.id,
                phase=phase,
                agent=self.__class__.__name__,
                observation=f"完成{func.__name__}",
                insight=insight
            )
            
            return result
        return wrapper
    return decorator

# 使用示例
class ResearcherAgent:
    @record_ier("GATHER")
    async def gather(self, task): ...
