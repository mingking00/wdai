#!/usr/bin/env python3
"""
wdai IER连接器 v1.0
连接外循环(执行层)和内循环(反思进化层)

完整闭环:
外循环执行 ──→ 触发反思 ──→ 经验提炼 ──→ 优化策略 ──→ 外循环改进
     ↑                                               ↓
     └──────────── 反馈影响执行质量 ←────────────────┘
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.insert(0, '/root/.openclaw/workspace/.wdai-runtime')
sys.path.insert(0, '/root/.openclaw/workspace/skills/self-reflection-agent')
sys.path.insert(0, '/root/.openclaw/workspace/skills/system-evolution-agent')

# 导入外循环组件
from agent_executor_v4 import AgentExecutionEngine, ExecutionResult
from agent_conductor_v3 import AgentConductor, AgentTask, TaskPriority

WORKSPACE = Path("/root/.openclaw/workspace")
RUNTIME_DIR = WORKSPACE / ".wdai-runtime"
IER_DIR = WORKSPACE / ".ier-connector"
IER_DIR.mkdir(exist_ok=True)

@dataclass
class ExecutionContext:
    """执行上下文 - 外循环执行时的完整信息"""
    task_id: str
    task_type: str
    description: str
    agent_id: str
    start_time: str
    end_time: Optional[str] = None
    execution_result: Optional[Dict] = None
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    user_feedback: Optional[str] = None  # 用户反馈

@dataclass
class ReflectionInsight:
    """反思洞察 - 内循环产出"""
    insight_id: str
    source_task_id: str
    insight_type: str  # 'success_pattern', 'error_pattern', 'improvement', 'principle'
    content: str
    confidence: float  # 0-1
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    applied_count: int = 0
    success_when_applied: int = 0

@dataclass
class Experience:
    """经验 - 可复用的知识"""
    experience_id: str
    experience_type: str  # 'execution_pattern', 'refactoring', 'design_decision', 'error_fix'
    context: str
    before: str
    after: str
    success_rate: float
    usage_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class IERConnector:
    """
    IER连接器 - 桥接外循环和内循环
    
    核心职责:
    1. 捕获外循环执行数据
    2. 触发内循环反思分析
    3. 提炼经验并存储
    4. 在后续执行中注入经验
    """
    
    def __init__(self):
        self.execution_history: List[ExecutionContext] = []
        self.insights: List[ReflectionInsight] = []
        self.experiences: List[Experience] = []
        self.connector_state_file = IER_DIR / "connector_state.json"
        self.load_state()
        
    def load_state(self):
        """加载连接器状态"""
        if self.connector_state_file.exists():
            with open(self.connector_state_file, 'r') as f:
                state = json.load(f)
                self.insights = [ReflectionInsight(**i) for i in state.get('insights', [])]
                self.experiences = [Experience(**e) for e in state.get('experiences', [])]
    
    def save_state(self):
        """保存连接器状态"""
        state = {
            "last_updated": datetime.now().isoformat(),
            "insights_count": len(self.insights),
            "experiences_count": len(self.experiences),
            "insights": [self._insight_to_dict(i) for i in self.insights],
            "experiences": [self._experience_to_dict(e) for e in self.experiences]
        }
        with open(self.connector_state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _insight_to_dict(self, insight: ReflectionInsight) -> dict:
        return {
            "insight_id": insight.insight_id,
            "source_task_id": insight.source_task_id,
            "insight_type": insight.insight_type,
            "content": insight.content,
            "confidence": insight.confidence,
            "extracted_at": insight.extracted_at,
            "applied_count": insight.applied_count,
            "success_when_applied": insight.success_when_applied
        }
    
    def _experience_to_dict(self, exp: Experience) -> dict:
        return {
            "experience_id": exp.experience_id,
            "experience_type": exp.experience_type,
            "context": exp.context,
            "before": exp.before,
            "after": exp.after,
            "success_rate": exp.success_rate,
            "usage_count": exp.usage_count,
            "created_at": exp.created_at
        }
    
    # =========================================================================
    # 外循环 → 内循环: 捕获执行数据
    # =========================================================================
    def capture_execution(self, execution_result: ExecutionResult, task: Dict) -> ExecutionContext:
        """
        捕获外循环执行结果，准备传递给内循环
        
        这是连接层的入口：外循环执行完成后调用
        """
        context = ExecutionContext(
            task_id=execution_result.task_id,
            task_type=task.get('task_type', 'unknown'),
            description=task.get('description', ''),
            agent_id=execution_result.agent_id,
            start_time=execution_result.logs[0][:19] if execution_result.logs else datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            execution_result={
                "success": execution_result.success,
                "output_type": type(execution_result.output).__name__,
                "execution_time": execution_result.execution_time
            },
            files_created=execution_result.files_created,
            files_modified=execution_result.files_modified,
            errors=[execution_result.error] if execution_result.error else []
        )
        
        self.execution_history.append(context)
        
        print(f"[IER连接器] 捕获执行: {context.task_id}")
        print(f"            Agent: {context.agent_id}")
        print(f"            成功: {context.execution_result['success']}")
        print(f"            文件: {len(context.files_created)} 创建, {len(context.files_modified)} 修改")
        
        return context
    
    # =========================================================================
    # 内循环: 反思分析
    # =========================================================================
    def trigger_reflection(self, context: ExecutionContext) -> List[ReflectionInsight]:
        """
        触发内循环反思分析
        
        分析执行结果，提取洞察
        """
        print(f"\n[IER连接器] 触发反思分析: {context.task_id}")
        
        new_insights = []
        
        # 1. 成功模式分析
        if context.execution_result and context.execution_result.get('success'):
            insight = ReflectionInsight(
                insight_id=f"insight_{datetime.now().strftime('%H%M%S')}_{len(self.insights)}",
                source_task_id=context.task_id,
                insight_type="success_pattern",
                content=f"{context.agent_id}成功执行{context.task_type}: {context.description[:50]}...",
                confidence=0.8
            )
            new_insights.append(insight)
            print(f"            ✓ 提取成功模式")
        
        # 2. 错误模式分析
        if context.errors:
            for error in context.errors:
                if error:
                    insight = ReflectionInsight(
                        insight_id=f"insight_{datetime.now().strftime('%H%M%S')}_{len(self.insights) + len(new_insights)}",
                        source_task_id=context.task_id,
                        insight_type="error_pattern",
                        content=f"{context.agent_id}错误: {error[:100]}",
                        confidence=0.9
                    )
                    new_insights.append(insight)
                    print(f"            ✓ 提取错误模式")
        
        # 3. 改进机会分析
        if len(context.files_created) == 0 and context.task_type == "code_implementation":
            insight = ReflectionInsight(
                insight_id=f"insight_{datetime.now().strftime('%H%M%S')}_{len(self.insights) + len(new_insights)}",
                source_task_id=context.task_id,
                insight_type="improvement",
                content=f"{context.agent_id}代码生成任务未创建文件，需要改进代码生成逻辑",
                confidence=0.7
            )
            new_insights.append(insight)
            print(f"            ✓ 提取改进点")
        
        # 保存洞察
        self.insights.extend(new_insights)
        
        print(f"            共提取 {len(new_insights)} 条洞察")
        
        return new_insights
    
    # =========================================================================
    # 内循环: 经验提炼
    # =========================================================================
    def distill_experience(self, context: ExecutionContext, insights: List[ReflectionInsight]) -> Optional[Experience]:
        """
        从执行和洞察中提炼可复用经验
        
        将洞察转化为可应用的经验
        """
        print(f"\n[IER连接器] 经验提炼: {context.task_id}")
        
        # 只有成功的执行才提炼经验
        if not context.execution_result or not context.execution_result.get('success'):
            print(f"            ✗ 执行失败，跳过经验提炼")
            return None
        
        # 根据任务类型创建不同类型的经验
        if context.task_type == "code_implementation" and context.files_created:
            exp = Experience(
                experience_id=f"exp_{datetime.now().strftime('%H%M%S')}_{len(self.experiences)}",
                experience_type="execution_pattern",
                context=f"{context.task_type}: {context.description[:50]}",
                before="无代码文件",
                after=f"生成 {len(context.files_created)} 个代码文件: {', '.join(context.files_created)}",
                success_rate=1.0
            )
            self.experiences.append(exp)
            print(f"            ✓ 提炼执行模式经验")
            return exp
        
        elif context.task_type == "code_review":
            exp = Experience(
                experience_id=f"exp_{datetime.now().strftime('%H%M%S')}_{len(self.experiences)}",
                experience_type="code_pattern",
                context=f"{context.task_type}: {context.description[:50]}",
                before="未审查代码",
                after="完成代码审查，发现潜在问题",
                success_rate=1.0
            )
            self.experiences.append(exp)
            print(f"            ✓ 提炼代码审查经验")
            return exp
        
        return None
    
    # =========================================================================
    # 内循环 → 外循环: 注入经验
    # =========================================================================
    def retrieve_relevant_experiences(self, task_type: str, agent_id: str, top_k: int = 3) -> List[Experience]:
        """
        为即将执行的任务检索相关经验
        
        这是连接层的出口：外循环执行前调用
        """
        # 匹配相同任务类型的经验
        relevant = [e for e in self.experiences if task_type in e.context]
        
        # 按成功率排序
        relevant.sort(key=lambda x: x.success_rate, reverse=True)
        
        return relevant[:top_k]
    
    def inject_experience_to_prompt(self, task: Dict, experiences: List[Experience]) -> str:
        """
        将经验注入到任务Prompt中
        """
        if not experiences:
            return task.get('description', '')
        
        enhanced_prompt = f"""{task.get('description', '')}

[相关经验参考]
基于历史 {len(experiences)} 次成功执行:
"""
        
        for i, exp in enumerate(experiences, 1):
            enhanced_prompt += f"""
{i}. {exp.experience_type} (成功率: {exp.success_rate:.0%})
   场景: {exp.context}
   方法: {exp.after}
"""
        
        enhanced_prompt += "\n请参考以上经验执行当前任务。"
        
        return enhanced_prompt
    
    # =========================================================================
    # 完整闭环: 执行后自动处理
    # =========================================================================
    def post_execution_pipeline(self, execution_result: ExecutionResult, task: Dict) -> Dict:
        """
        执行后完整处理流程
        
        外循环执行 → 捕获 → 反思 → 提炼 → 保存
        """
        print("\n" + "="*65)
        print("[IER连接器] 执行后处理流程")
        print("="*65)
        
        # 1. 捕获执行
        context = self.capture_execution(execution_result, task)
        
        # 2. 触发反思
        insights = self.trigger_reflection(context)
        
        # 3. 提炼经验
        experience = self.distill_experience(context, insights)
        
        # 4. 保存状态
        self.save_state()
        
        # 5. 返回处理结果
        result = {
            "task_id": context.task_id,
            "insights_extracted": len(insights),
            "experience_distilled": experience is not None,
            "total_insights": len(self.insights),
            "total_experiences": len(self.experiences)
        }
        
        print("\n[IER连接器] 处理完成")
        print(f"            总洞察数: {result['total_insights']}")
        print(f"            总经验数: {result['total_experiences']}")
        print("="*65)
        
        return result
    
    def get_statistics(self) -> Dict:
        """获取连接器统计"""
        return {
            "executions_captured": len(self.execution_history),
            "insights_extracted": len(self.insights),
            "experiences_distilled": len(self.experiences),
            "insight_types": {},
            "experience_types": {}
        }


class IntegratedAgentSystem:
    """
    集成Agent系统
    外循环 + IER连接器 + 内循环 = 完整闭环
    """
    
    def __init__(self):
        self.engine = AgentExecutionEngine()
        self.connector = IERConnector()
        
    async def execute_with_learning(self, task: Dict, agent_id: str) -> Dict:
        """
        带学习的执行
        
        完整流程:
        1. 检索相关经验
        2. 注入经验增强Prompt
        3. 执行外循环
        4. IER后处理（反思→提炼→保存）
        5. 返回完整结果
        """
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║     🔗 集成Agent系统 - 带学习的执行                        ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print()
        
        # 1. 检索经验（内循环 → 外循环）
        print("[阶段1] 检索相关经验...")
        experiences = self.connector.retrieve_relevant_experiences(
            task.get('task_type', ''),
            agent_id
        )
        print(f"        找到 {len(experiences)} 条相关经验")
        
        # 2. 注入经验
        if experiences:
            enhanced_description = self.connector.inject_experience_to_prompt(task, experiences)
            task['description'] = enhanced_description
            print("        ✓ 经验已注入Prompt")
        
        # 3. 执行外循环
        print("\n[阶段2] 执行外循环...")
        result = await self.engine.execute_single(task, agent_id)
        
        # 4. IER后处理（外循环 → 内循环）
        print("\n[阶段3] IER后处理（反思→提炼→保存）...")
        ier_result = self.connector.post_execution_pipeline(result, task)
        
        # 5. 返回完整结果
        print("\n[阶段4] 执行完成")
        return {
            "execution": {
                "success": result.success,
                "task_id": result.task_id,
                "files_created": result.files_created
            },
            "learning": {
                "insights_extracted": ier_result['insights_extracted'],
                "experience_distilled": ier_result['experience_distilled'],
                "total_insights": ier_result['total_insights'],
                "total_experiences": ier_result['total_experiences']
            },
            "experience_applied": len(experiences)
        }


async def demo_integration():
    """演示集成系统"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     🔗 IER连接器演示: 外循环 ↔ 内循环                       ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    system = IntegratedAgentSystem()
    
    # 演示1: 首次执行（无经验）
    print("─" * 65)
    print("演示1: 首次执行（无经验参考）")
    print("─" * 65)
    
    task1 = {
        "task_id": "task_demo_001",
        "task_type": "code_implementation",
        "description": "实现一个日志记录模块"
    }
    
    result1 = await system.execute_with_learning(task1, "coder")
    
    print(f"\n执行结果:")
    print(f"  成功: {result1['execution']['success']}")
    print(f"  学习: {result1['learning']['insights_extracted']} 洞察, "
          f"{result1['learning']['total_experiences']} 经验")
    
    # 演示2: 第二次执行（有经验参考）
    print("\n" + "─" * 65)
    print("演示2: 第二次执行（有经验参考）")
    print("─" * 65)
    
    task2 = {
        "task_id": "task_demo_002",
        "task_type": "code_implementation",
        "description": "实现另一个工具模块"
    }
    
    result2 = await system.execute_with_learning(task2, "coder")
    
    print(f"\n执行结果:")
    print(f"  成功: {result2['execution']['success']}")
    print(f"  应用经验: {result2['experience_applied']} 条")
    print(f"  新学习: {result2['learning']['insights_extracted']} 洞察")
    
    # 演示3: 查看连接器状态
    print("\n" + "─" * 65)
    print("IER连接器状态")
    print("─" * 65)
    
    stats = system.connector.get_statistics()
    print(f"  捕获执行: {stats['executions_captured']}")
    print(f"  提取洞察: {stats['insights_extracted']}")
    print(f"  提炼经验: {stats['experiences_distilled']}")
    
    print("\n" + "=" * 65)
    print("✅ IER连接器演示完成")
    print("=" * 65)
    print()
    print("💡 连接闭环已建立:")
    print("   外循环执行 → IER连接器 → 内循环反思 → 经验提炼")
    print("   经验存储 → 下次执行前检索 → 注入Prompt → 优化执行")


if __name__ == '__main__':
    import asyncio
    asyncio.run(demo_integration())
