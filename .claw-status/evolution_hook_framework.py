#!/usr/bin/env python3
"""
进化系统Hook架构 (Evolution Hook Framework)
将evo模块从"手动库"变成"自动机制"

核心设计:
1. 事件总线 - 统一事件定义和分发
2. Hook注册 - evo模块自动挂载到事件
3. 透明执行 - 用户无感知，自动触发
4. 状态持久 - 跨会话保持进化状态

Author: wdai
Version: 1.0
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from functools import wraps

# 路径设置
CLAW_STATUS = Path(__file__).parent
sys.path.insert(0, str(CLAW_STATUS))


# ============================================================================
# 事件定义
# ============================================================================

class EvolutionEvent(Enum):
    """进化系统事件类型"""
    # 会话生命周期
    SESSION_START = "session_start"           # 会话开始
    SESSION_END = "session_end"               # 会话结束
    
    # 记忆操作
    MEMORY_BEFORE_SEARCH = "memory_before_search"   # memory_search前
    MEMORY_AFTER_SEARCH = "memory_after_search"     # memory_search后
    MEMORY_UPDATE = "memory_update"                 # 记忆更新
    
    # 工具调用
    TOOL_BEFORE_CALL = "tool_before_call"     # 工具调用前
    TOOL_AFTER_CALL = "tool_after_call"       # 工具调用后
    TOOL_FAILED = "tool_failed"               # 工具调用失败
    
    # 任务执行
    TASK_START = "task_start"                 # 任务开始
    TASK_COMPLETE = "task_complete"           # 任务完成
    TASK_FAILED = "task_failed"               # 任务失败
    
    # 反思与学习
    REFLECTION_TRIGGER = "reflection_trigger" # 触发反思
    LEARNING_EXTRACT = "learning_extract"     # 提取学习


@dataclass
class EventContext:
    """事件上下文"""
    event_type: EvolutionEvent
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""
    agent_id: str = "main"
    data: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None


# ============================================================================
# Hook注册表
# ============================================================================

class EvolutionHookRegistry:
    """
    进化Hook注册中心
    管理所有evo模块的自动触发逻辑
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Hook存储: {event_type: [(priority, hook_name, handler)]}
        self._hooks: Dict[EvolutionEvent, List[tuple]] = {
            event: [] for event in EvolutionEvent
        }
        
        # Hook状态
        self._hook_states: Dict[str, Dict] = {}
        self._state_file = CLAW_STATUS / "evolution_hook_states.json"
        
        # 加载状态
        self._load_states()
        
        # 活跃标记
        self._active = True
        self._execution_log: List[Dict] = []
    
    def _load_states(self):
        """加载Hook状态"""
        if self._state_file.exists():
            try:
                with open(self._state_file, 'r') as f:
                    self._hook_states = json.load(f)
            except:
                self._hook_states = {}
    
    def _save_states(self):
        """保存Hook状态"""
        try:
            with open(self._state_file, 'w') as f:
                json.dump(self._hook_states, f, indent=2)
        except Exception as e:
            print(f"[EvolutionHook] 状态保存失败: {e}")
    
    def register(self, event: EvolutionEvent, handler: Callable, 
                 name: str = "", priority: int = 50):
        """
        注册Hook
        
        Args:
            event: 事件类型
            handler: 处理函数 (接收EventContext, 返回处理结果)
            name: Hook名称
            priority: 优先级 (0-100, 数字小优先)
        """
        name = name or handler.__name__
        self._hooks[event].append((priority, name, handler))
        self._hooks[event].sort(key=lambda x: x[0])  # 按优先级排序
        
        print(f"[EvolutionHook] 注册: {name} → {event.value} (P{priority})")
    
    def emit(self, event: EvolutionEvent, **data) -> List[Any]:
        """
        触发事件
        
        Returns:
            所有handler的返回结果列表
        """
        if not self._active:
            return []
        
        context = EventContext(
            event_type=event,
            data=data,
            session_id=data.get('session_id', ''),
            agent_id=data.get('agent_id', 'main')
        )
        
        results = []
        for priority, name, handler in self._hooks[event]:
            try:
                start = time.time()
                result = handler(context)
                elapsed = time.time() - start
                
                results.append({
                    'hook': name,
                    'result': result,
                    'time_ms': round(elapsed * 1000, 2)
                })
                
                # 记录执行日志
                self._execution_log.append({
                    'timestamp': time.time(),
                    'event': event.value,
                    'hook': name,
                    'elapsed_ms': round(elapsed * 1000, 2)
                })
                
            except Exception as e:
                print(f"[EvolutionHook] {name} 执行失败: {e}")
                results.append({'hook': name, 'error': str(e)})
        
        return results
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'hooks_registered': {
                event.value: len(hooks) 
                for event, hooks in self._hooks.items()
            },
            'total_hooks': sum(len(h) for h in self._hooks.values()),
            'recent_executions': len(self._execution_log),
            'active': self._active
        }


# 全局注册表实例
_registry = None

def get_registry() -> EvolutionHookRegistry:
    """获取全局Hook注册表"""
    global _registry
    if _registry is None:
        _registry = EvolutionHookRegistry()
    return _registry


# ============================================================================
# 装饰器
# ============================================================================

def evolution_hook(event: EvolutionEvent, priority: int = 50):
    """
    装饰器: 将函数注册为进化Hook
    
    用法:
        @evolution_hook(EvolutionEvent.MEMORY_AFTER_SEARCH, priority=10)
        def evaluate_retrieval_quality(ctx: EventContext):
            # 自动在每次memory_search后执行
            ...
    """
    def decorator(func: Callable):
        registry = get_registry()
        registry.register(event, func, name=func.__name__, priority=priority)
        return func
    return decorator


# ============================================================================
# 初始化入口
# ============================================================================

def initialize_evolution_hooks():
    """
    初始化所有进化系统Hooks
    在会话启动时自动调用
    """
    registry = get_registry()
    
    print("\n" + "="*60)
    print("🔥 进化系统Hook架构初始化")
    print("="*60)
    
    # 加载所有evo模块并注册它们的hooks
    _load_evo_modules()
    
    # 触发会话开始事件
    registry.emit(EvolutionEvent.SESSION_START, 
                  timestamp=time.time(),
                  init_time=time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # 输出状态
    stats = registry.get_stats()
    print(f"\n✅ Hook系统已激活")
    print(f"   注册Hook数: {stats['total_hooks']}")
    print(f"   事件类型: {len([e for e in stats['hooks_registered'] if stats['hooks_registered'][e] > 0])}")
    
    print("="*60 + "\n")
    
    return registry


def _load_evo_modules():
    """加载所有evo模块，自动注册它们的hooks"""
    
    # 模块列表: (模块名, 文件路径)
    evo_modules = [
        ('evo_rag_hooks', str(CLAW_STATUS / 'evo' / 'evo_hooks_rag.py')),
        ('evo_agent_hooks', str(CLAW_STATUS / 'evo' / 'evo_hooks_agents.py')),
        ('evo_planning_hooks', str(CLAW_STATUS / 'evo' / 'evo_hooks_planning.py')),
    ]
    
    for module_name, file_path in evo_modules:
        try:
            if Path(file_path).exists():
                # 动态导入模块
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                
                # 执行模块 (注册hooks)
                spec.loader.exec_module(module)
                
                print(f"[EvolutionHook] 加载模块: {module_name}")
        except Exception as e:
            print(f"[EvolutionHook] 加载 {module_name} 失败: {e}")


# ============================================================================
# 手动触发接口 (用于包装原始函数)
# ============================================================================

def emit_event(event: EvolutionEvent, **data) -> List[Any]:
    """手动触发事件 (用于在原始工具调用中插入)"""
    return get_registry().emit(event, **data)


# 便捷函数
def on_session_start(**data): return emit_event(EvolutionEvent.SESSION_START, **data)
def on_session_end(**data): return emit_event(EvolutionEvent.SESSION_END, **data)
def on_memory_before(**data): return emit_event(EvolutionEvent.MEMORY_BEFORE_SEARCH, **data)
def on_memory_after(**data): return emit_event(EvolutionEvent.MEMORY_AFTER_SEARCH, **data)
def on_tool_before(tool_name: str, **data): 
    return emit_event(EvolutionEvent.TOOL_BEFORE_CALL, tool=tool_name, **data)
def on_tool_after(tool_name: str, result: Any, **data):
    return emit_event(EvolutionEvent.TOOL_AFTER_CALL, tool=tool_name, result=result, **data)
def on_tool_failed(tool_name: str, error: str, **data):
    return emit_event(EvolutionEvent.TOOL_FAILED, tool=tool_name, error=error, **data)


# ============================================================================
# 自动包装器 (用于包装原始工具函数)
# ============================================================================

def wrap_with_evolution(original_func, event_prefix: str):
    """
    包装原始函数，自动触发进化事件
    
    用法:
        memory_search = wrap_with_evolution(original_memory_search, "memory")
    """
    @wraps(original_func)
    def wrapper(*args, **kwargs):
        # 触发Before事件
        before_event = getattr(EvolutionEvent, f"{event_prefix.upper()}_BEFORE_CALL", None)
        if before_event:
            emit_event(before_event, args=args, kwargs=kwargs)
        
        try:
            # 执行原始函数
            result = original_func(*args, **kwargs)
            
            # 触发After事件
            after_event = getattr(EvolutionEvent, f"{event_prefix.upper()}_AFTER_CALL", None)
            if after_event:
                emit_event(after_event, args=args, kwargs=kwargs, result=result)
            
            return result
            
        except Exception as e:
            # 触发失败事件
            failed_event = getattr(EvolutionEvent, f"{event_prefix.upper()}_FAILED", None)
            if failed_event:
                emit_event(failed_event, args=args, kwargs=kwargs, error=str(e))
            raise
    
    return wrapper


# 模块测试
if __name__ == "__main__":
    # 测试初始化
    registry = initialize_evolution_hooks()
    
    # 输出统计
    print("\n统计:", json.dumps(registry.get_stats(), indent=2))
