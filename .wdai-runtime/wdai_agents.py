#!/usr/bin/env python3
"""
wdai Agent实现
基于wdai Runtime的具体Agent类型
"""

import time
import json
from typing import Dict, Any, Optional
from wdai_runtime import BaseAgent, wdaiRuntime, AgentMessage
from innovation_tracker_rt import InnovationTracker, get_tracker

# 全局追踪器实例
_innovation_tracker = None

def get_innovation_tracker() -> InnovationTracker:
    """获取全局创新追踪器"""
    global _innovation_tracker
    if _innovation_tracker is None:
        _innovation_tracker = InnovationTracker()
    return _innovation_tracker

class CoordinatorAgent(BaseAgent):
    """
    协调者Agent - 任务分发、冲突仲裁
    """
    def __init__(self):
        super().__init__("coordinator", "coordinator")
        self.task_queue = []
        self.agent_capabilities = {}
        
    def _tick(self):
        """协调者tick"""
        # 检查待分配任务
        if self.task_queue:
            task = self.task_queue.pop(0)
            self._assign_task(task)
        time.sleep(0.5)
        
    def _handle_message(self, msg: AgentMessage):
        """处理消息"""
        super()._handle_message(msg)
        
        if msg.msg_type == "task_request":
            # 收到任务请求，加入队列
            self.task_queue.append({
                "from": msg.from_agent,
                "task": msg.payload,
                "msg_id": msg.msg_id
            })
            
        elif msg.msg_type == "task_result":
            # 任务完成，触发反思
            self._trigger_reflection(msg)
            
        elif msg.msg_type == "conflict":
            # 冲突仲裁
            self._arbitrate_conflict(msg)
            
    def _assign_task(self, task: Dict):
        """分配任务给合适的Agent"""
        task_type = task["task"].get("task_type")
        
        # 根据任务类型选择Agent
        agent_mapping = {
            "code": "coder",
            "review": "reviewer", 
            "reflection": "reflector",
            "evolve": "evolution",
            "research": "researcher"
        }
        
        target_agent = agent_mapping.get(task_type, "coder")
        
        # 发送任务
        self.send_message(
            to_agent=target_agent,
            msg_type="task_assignment",
            payload={
                "original_from": task["from"],
                "task": task["task"],
                "request_id": task["msg_id"]
            }
        )
        
        print(f"[Coordinator] Assigned task '{task_type}' to {target_agent}")
        
    def _trigger_reflection(self, msg: AgentMessage):
        """触发反思"""
        result = msg.payload
        
        # 发送反思任务
        self.send_message(
            to_agent="reflector",
            msg_type="task_assignment",
            payload={
                "task_type": "reflection",
                "description": f"反思任务: {result.get('task_type', 'unknown')}",
                "data": {
                    "original_task": result,
                    "completed_by": msg.from_agent
                }
            }
        )
        
    def _arbitrate_conflict(self, msg: AgentMessage):
        """仲裁冲突"""
        conflict = msg.payload
        print(f"[Coordinator] Arbitrating conflict between {conflict.get('agent_a')} and {conflict.get('agent_b')}")
        
        # 简单的仲裁逻辑：优先级高的Agent胜出
        # 实际应该基于原则权重判断
        winner = conflict.get("agent_a")  # 简化处理
        
        # 广播仲裁结果
        self.runtime.broadcast_event(
            from_agent=self.agent_id,
            event_type="conflict_resolved",
            data={
                "conflict_id": conflict.get("conflict_id"),
                "winner": winner,
                "reason": "Priority-based arbitration"
            }
        )

class CoderAgent(BaseAgent):
    """
    编码者Agent - 实际执行任务
    """
    def __init__(self):
        super().__init__("coder", "coder")
        self.current_task = None
        
    def _handle_message(self, msg: AgentMessage):
        super()._handle_message(msg)
        
        if msg.msg_type == "task_assignment":
            self._execute_task(msg.payload)
            
    def _execute_task(self, assignment: Dict):
        """执行任务（集成创新追踪器）"""
        task = assignment.get("task", {})
        task_type = task.get("task_type")
        description = task.get("description", "")
        task_data = task.get("data", {})
        
        # 检测可能使用的工具
        method = task_data.get("method", task_type)
        
        print(f"[Coder] Executing: {description}")
        print(f"[Coder] Method: {method}")
        
        # 获取创新追踪器
        tracker = get_innovation_tracker()
        
        # 执行前检查：方法是否被锁定
        block_reason = tracker.check_before_execute(method)
        if block_reason:
            print(f"[Coder] 🚫 BLOCKED: {block_reason}")
            
            # 发送失败结果
            self.send_message(
                to_agent="coordinator",
                msg_type="task_result",
                payload={
                    "request_id": assignment.get("request_id"),
                    "original_from": assignment.get("original_from"),
                    "task_type": task_type,
                    "success": False,
                    "error": block_reason,
                    "result": None
                }
            )
            
            # 触发反思
            self.send_message(
                to_agent="reflector",
                msg_type="task_assignment",
                payload={
                    "task_type": "reflection",
                    "description": f"方法被锁定: {method}",
                    "data": {
                        "locked_method": method,
                        "task": task
                    }
                }
            )
            return
        
        self.state.status = "busy"
        self.state.current_task = assignment.get("request_id")
        self._update_state()
        
        # 模拟执行（实际应该是真实的工具调用）
        time.sleep(2)
        
        # 模拟：github_api 会失败，其他方法成功
        if method == "github_api":
            success = False
            error = "API rate limit exceeded"
        else:
            success = True
            error = None
        
        # 执行后报告结果
        result = tracker.report_after_execute(method, success, error)
        print(f"[Coder] {result['message']}")
        
        result_data = {
            "method": method, 
            "duration": "2s",
            "success": success
        }
        
        if not success:
            result_data["error"] = error
        
        # 发送结果回协调者
        self.send_message(
            to_agent="coordinator",
            msg_type="task_result",
            payload={
                "request_id": assignment.get("request_id"),
                "original_from": assignment.get("original_from"),
                "task_type": task_type,
                "success": success,
                "error": error,
                "result": result_data
            }
        )
        
        self.state.status = "idle"
        self.state.current_task = None
        self._update_state()
        
        if success:
            print(f"[Coder] ✅ Completed: {description}")
        else:
            print(f"[Coder] ❌ Failed: {description}")
            print(f"[Coder]    Error: {error}")

class ReflectorAgent(BaseAgent):
    """
    反思者Agent - 过程分析、原则提炼
    """
    def __init__(self):
        super().__init__("reflector", "reflector")
        
    def _handle_message(self, msg: AgentMessage):
        super()._handle_message(msg)
        
        if msg.msg_type == "task_assignment":
            self._reflect(msg.payload)
            
    def _reflect(self, assignment: Dict):
        """执行反思（集成创新追踪器）"""
        task = assignment.get("task", {})
        data = task.get("data", {})
        original_task = data.get("original_task", {})
        locked_method = data.get("locked_method")
        
        print(f"[Reflector] Reflecting on: {original_task.get('task_type', 'unknown')}")
        if locked_method:
            print(f"[Reflector] Locked method detected: {locked_method}")
        
        self.state.status = "busy"
        self._update_state()
        
        # 模拟反思
        time.sleep(1)
        
        # 提炼洞察
        insights = self._extract_insights(original_task, locked_method)
        
        # 保存到共享状态
        reflections = self.get_shared("reflections", [])
        reflections.append({
            "timestamp": time.time(),
            "task": original_task,
            "locked_method": locked_method,
            "insights": insights
        })
        self.set_shared("reflections", reflections)
        
        # 触发进化
        if len(insights) > 0:
            self.send_message(
                to_agent="evolution",
                msg_type="evolve_request",
                payload={
                    "insights": insights,
                    "source_reflection": len(reflections) - 1
                }
            )
        
        self.state.status = "idle"
        self._update_state()
        print(f"[Reflector] Reflection complete. Insights: {len(insights)}")
        
    def _extract_insights(self, task_result: Dict, locked_method: str = None) -> list:
        """从任务结果中提取洞察"""
        insights = []
        
        # 如果方法被锁定，提炼替代方案
        if locked_method == "github_api":
            insights.append({
                "type": "best_practice",
                "content": "github_api 失败时应换用 git CLI",
                "alternative": "git_push",
                "confidence": 0.9
            })
        
        # 检查是否有改进空间
        if task_result.get("method") == "github_api":
            insights.append({
                "type": "best_practice",
                "content": "github_api 失败时应换用 git CLI",
                "alternative": "git_push",
                "confidence": 0.9
            })
        
        # 检查失败模式
        if not task_result.get("success", True):
            error = task_result.get("error", "")
            if "rate limit" in error.lower():
                insights.append({
                    "type": "reliability",
                    "content": "API rate limit频繁出现，应优先使用本地工具",
                    "confidence": 0.85
                })
            
        return insights
        if task_result.get("method") == "github_api":
            insights.append({
                "type": "best_practice",
                "content": "github_api 失败时应换用 git CLI",
                "confidence": 0.9
            })
            
        return insights

class EvolutionAgent(BaseAgent):
    """
    进化者Agent - 系统更新、能力进化
    """
    def __init__(self):
        super().__init__("evolution", "evolution")
        
    def _handle_message(self, msg: AgentMessage):
        super()._handle_message(msg)
        
        if msg.msg_type == "evolve_request":
            self._evolve(msg.payload)
            
    def _evolve(self, request: Dict):
        """执行进化"""
        insights = request.get("insights", [])
        
        print(f"[Evolution] Processing {len(insights)} insights")
        self.state.status = "busy"
        self._update_state()
        
        for insight in insights:
            if insight.get("type") == "best_practice":
                # 更新最佳实践
                practices = self.get_shared("best_practices", [])
                practices.append(insight)
                self.set_shared("best_practices", practices)
                print(f"[Evolution] Added best practice: {insight.get('content', '')[:50]}...")
        
        self.state.status = "idle"
        self._update_state()
        print("[Evolution] Evolution complete")

# 导出
__all__ = ['CoordinatorAgent', 'CoderAgent', 'ReflectorAgent', 'EvolutionAgent']

if __name__ == "__main__":
    print("=== wdai Agent Implementations ===")
    print()
    print("Available agents:")
    print("  - CoordinatorAgent: 任务分发、冲突仲裁")
    print("  - CoderAgent: 实际执行任务")
    print("  - ReflectorAgent: 过程分析、原则提炼")
    print("  - EvolutionAgent: 系统更新、能力进化")
    print()
    print("Usage:")
    print("  from wdai_agents import CoordinatorAgent, CoderAgent")
    print("  runtime = wdaiRuntime()")
    print("  runtime.register_agent(CoordinatorAgent())")
    print("  runtime.register_agent(CoderAgent())")
    print("  runtime.start()")
