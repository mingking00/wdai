"""
推理追踪系统 (Reasoning Trace System)

实现目标:
1. 记录每个 Agent 的完整推理过程
2. 实时推送工作流状态
3. 结构化思维链，便于审查
4. 多 Agent 共享推理上下文
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import threading
from contextlib import contextmanager


class ReasoningStepType(Enum):
    """推理步骤类型"""
    UNDERSTAND = "understand"      # 任务理解
    ANALYZE = "analyze"            # 分析
    PLAN = "plan"                  # 规划
    EXECUTE = "execute"            # 执行
    VERIFY = "verify"              # 验证
    REFLECT = "reflect"            # 反思
    DECISION = "decision"          # 决策
    ERROR = "error"                # 错误


@dataclass
class ReasoningStep:
    """单个推理步骤"""
    step_type: ReasoningStepType
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_name: str = ""
    task_id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'step_type': self.step_type.value,
            'content': self.content,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'metadata': self.metadata,
            'agent_name': self.agent_name,
            'task_id': self.task_id
        }


@dataclass
class TaskTrace:
    """任务完整追踪记录"""
    task_id: str
    task_type: str
    start_time: float
    end_time: Optional[float] = None
    steps: List[ReasoningStep] = field(default_factory=list)
    status: str = "running"  # running, completed, failed
    result: Any = None
    error: Optional[str] = None
    
    def add_step(self, step: ReasoningStep):
        """添加推理步骤"""
        self.steps.append(step)
    
    def complete(self, result: Any = None):
        """标记完成"""
        self.end_time = time.time()
        self.status = "completed"
        self.result = result
    
    def fail(self, error: str):
        """标记失败"""
        self.end_time = time.time()
        self.status = "failed"
        self.error = error
    
    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.end_time - self.start_time if self.end_time else None,
            'status': self.status,
            'steps': [s.to_dict() for s in self.steps],
            'step_count': len(self.steps),
            'result': str(self.result)[:500] if self.result else None,  # 截断
            'error': self.error
        }


class TraceObserver:
    """追踪观察者接口"""
    
    def on_step_added(self, task_id: str, step: ReasoningStep):
        """当新步骤添加时调用"""
        pass
    
    def on_task_completed(self, task_id: str, trace: TaskTrace):
        """当任务完成时调用"""
        pass
    
    def on_task_failed(self, task_id: str, trace: TaskTrace, error: str):
        """当任务失败时调用"""
        pass


class ConsoleObserver(TraceObserver):
    """控制台观察者 - 实时打印推理过程"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
    
    def on_step_added(self, task_id: str, step: ReasoningStep):
        if self.verbose:
            icon = {
                ReasoningStepType.UNDERSTAND: "🎯",
                ReasoningStepType.ANALYZE: "🔍",
                ReasoningStepType.PLAN: "📋",
                ReasoningStepType.EXECUTE: "⚙️",
                ReasoningStepType.VERIFY: "✅",
                ReasoningStepType.REFLECT: "💭",
                ReasoningStepType.DECISION: "🎲",
                ReasoningStepType.ERROR: "❌"
            }.get(step.step_type, "📝")
            
            print(f"[{icon}] {step.agent_name} | {step.step_type.value}: {step.content[:80]}...")
    
    def on_task_completed(self, task_id: str, trace: TaskTrace):
        duration = trace.end_time - trace.start_time if trace.end_time else 0
        print(f"\n✨ 任务完成 [{task_id}] - {len(trace.steps)} 步, {duration:.2f}s")
    
    def on_task_failed(self, task_id: str, trace: TaskTrace, error: str):
        print(f"\n💥 任务失败 [{task_id}]: {error}")


class ReasoningTracer:
    """推理追踪器 - 核心组件"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._traces: Dict[str, TaskTrace] = {}
        self._observers: List[TraceObserver] = []
        self._current_task: Optional[str] = None
        self._lock = threading.RLock()
        self._initialized = True
        
        # 默认添加控制台观察者
        self.add_observer(ConsoleObserver())
    
    def add_observer(self, observer: TraceObserver):
        """添加观察者"""
        self._observers.append(observer)
    
    def start_task(self, task_id: str, task_type: str, agent_name: str = "") -> TaskTrace:
        """开始追踪新任务"""
        trace = TaskTrace(
            task_id=task_id,
            task_type=task_type,
            start_time=time.time()
        )
        
        with self._lock:
            self._traces[task_id] = trace
            self._current_task = task_id
        
        # 记录开始步骤
        self.add_step(
            task_id=task_id,
            step_type=ReasoningStepType.UNDERSTAND,
            content=f"开始任务: {task_type}",
            agent_name=agent_name
        )
        
        return trace
    
    def add_step(
        self,
        task_id: str,
        step_type: ReasoningStepType,
        content: str,
        agent_name: str = "",
        metadata: Optional[Dict] = None
    ):
        """添加推理步骤"""
        step = ReasoningStep(
            step_type=step_type,
            content=content,
            agent_name=agent_name,
            task_id=task_id,
            metadata=metadata or {}
        )
        
        with self._lock:
            if task_id in self._traces:
                self._traces[task_id].add_step(step)
        
        # 通知观察者
        for observer in self._observers:
            try:
                observer.on_step_added(task_id, step)
            except Exception as e:
                print(f"Observer error: {e}")
    
    def complete_task(self, task_id: str, result: Any = None):
        """完成任务"""
        with self._lock:
            if task_id in self._traces:
                self._traces[task_id].complete(result)
                trace = self._traces[task_id]
                
                # 通知观察者
                for observer in self._observers:
                    try:
                        observer.on_task_completed(task_id, trace)
                    except Exception as e:
                        print(f"Observer error: {e}")
    
    def fail_task(self, task_id: str, error: str):
        """任务失败"""
        with self._lock:
            if task_id in self._traces:
                self._traces[task_id].fail(error)
                trace = self._traces[task_id]
                
                # 通知观察者
                for observer in self._observers:
                    try:
                        observer.on_task_failed(task_id, trace, error)
                    except Exception as e:
                        print(f"Observer error: {e}")
    
    def get_trace(self, task_id: str) -> Optional[TaskTrace]:
        """获取任务追踪记录"""
        with self._lock:
            return self._traces.get(task_id)
    
    def get_all_traces(self) -> Dict[str, TaskTrace]:
        """获取所有追踪记录"""
        with self._lock:
            return dict(self._traces)
    
    def export_trace(self, task_id: str, filepath: str):
        """导出追踪记录到文件"""
        trace = self.get_trace(task_id)
        if trace:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(trace.to_dict(), f, indent=2, ensure_ascii=False)
    
    def export_all(self, filepath: str):
        """导出所有追踪记录"""
        with self._lock:
            data = {tid: t.to_dict() for tid, t in self._traces.items()}
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @contextmanager
    def trace_context(self, task_id: str, task_type: str, agent_name: str = ""):
        """上下文管理器 - 自动追踪任务"""
        self.start_task(task_id, task_type, agent_name)
        try:
            yield self
        except Exception as e:
            self.fail_task(task_id, str(e))
            raise
        else:
            self.complete_task(task_id)


# 全局追踪器实例
tracer = ReasoningTracer()


class StructuredReasoning:
    """结构化推理模板"""
    
    TEMPLATE = """
## 任务理解
用户想要什么: {goal}
约束条件: {constraints}
成功标准: {success_criteria}

## 分析
当前情况: {current_state}
关键挑战: {challenges}
可用资源: {resources}

## 规划
执行步骤:
{steps}

## 决策
选择方案: {chosen_option}
理由: {reasoning}
风险: {risks}

## 执行
正在执行: {current_action}
进度: {progress}

## 验证
结果检查: {verification}
是否符合预期: {is_valid}
改进点: {improvements}
"""
    
    def __init__(self, tracer: ReasoningTracer, task_id: str, agent_name: str = ""):
        self.tracer = tracer
        self.task_id = task_id
        self.agent_name = agent_name
        self.sections = {}
    
    def understand(self, goal: str, constraints: str = "", success_criteria: str = ""):
        """记录任务理解"""
        content = f"目标: {goal}\n约束: {constraints}\n成功标准: {success_criteria}"
        self.tracer.add_step(
            self.task_id, ReasoningStepType.UNDERSTAND, content, self.agent_name
        )
        self.sections['understand'] = {'goal': goal, 'constraints': constraints}
    
    def analyze(self, current_state: str, challenges: str = "", resources: str = ""):
        """记录分析"""
        content = f"当前: {current_state}\n挑战: {challenges}\n资源: {resources}"
        self.tracer.add_step(
            self.task_id, ReasoningStepType.ANALYZE, content, self.agent_name
        )
    
    def plan(self, steps: List[str]):
        """记录规划"""
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        self.tracer.add_step(
            self.task_id, ReasoningStepType.PLAN, f"执行步骤:\n{steps_text}", self.agent_name,
            metadata={'steps': steps}
        )
    
    def decide(self, option: str, reasoning: str, risks: str = ""):
        """记录决策"""
        content = f"选择: {option}\n理由: {reasoning}\n风险: {risks}"
        self.tracer.add_step(
            self.task_id, ReasoningStepType.DECISION, content, self.agent_name
        )
    
    def execute(self, action: str, progress: str = ""):
        """记录执行"""
        content = f"正在: {action}\n进度: {progress}"
        self.tracer.add_step(
            self.task_id, ReasoningStepType.EXECUTE, content, self.agent_name
        )
    
    def verify(self, result: str, is_valid: bool, improvements: str = ""):
        """记录验证"""
        content = f"结果: {result}\n有效: {is_valid}\n改进: {improvements}"
        self.tracer.add_step(
            self.task_id, ReasoningStepType.VERIFY, content, self.agent_name,
            metadata={'is_valid': is_valid}
        )
    
    def reflect(self, insight: str):
        """记录反思"""
        self.tracer.add_step(
            self.task_id, ReasoningStepType.REFLECT, insight, self.agent_name
        )
    
    def error(self, error_msg: str, recovery: str = ""):
        """记录错误"""
        content = f"错误: {error_msg}\n恢复: {recovery}"
        self.tracer.add_step(
            self.task_id, ReasoningStepType.ERROR, content, self.agent_name
        )


# 导出
__all__ = [
    'ReasoningTracer',
    'ReasoningStep',
    'ReasoningStepType',
    'TaskTrace',
    'TraceObserver',
    'ConsoleObserver',
    'StructuredReasoning',
    'tracer'
]
