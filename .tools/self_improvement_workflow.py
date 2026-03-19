#!/usr/bin/env python3
"""
Self-Improvement Workflow - 基于Mitchell方法论的自我改进流程

将Mitchell Hashimoto的16-session方法论应用到AI助手的自我改进中
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class SessionType(Enum):
    """会话类型"""
    PLANNING = "planning"           # 规划阶段（Consult the oracle）
    PROTOTYPING = "prototyping"     # 原型探索
    CLEANUP = "cleanup"             # Anti-Slop清理
    REVIEW = "review"               # 审查（Consult the oracle，不编码）
    MANUAL = "manual"               # 战略性手动干预
    BREAKTHROUGH = "breakthrough"   # 遇到瓶颈，人工研究

@dataclass
class ImprovementSession:
    """改进会话记录"""
    session_id: str
    timestamp: str
    session_type: SessionType
    goal: str
    plan: str
    output: str
    learnings: str
    next_steps: str

class SelfImprovementWorkflow:
    """
    自我改进工作流
    
    基于Mitchell方法论的改进流程：
    1. 规划优先（Consult the oracle）
    2. 原型探索（获得灵感）
    3. 清理会议（Anti-Slop）
    4. 审查改进（Review without coding）
    5. 战略性手动干预
    6. 瓶颈突破（停止用AI，深度思考）
    """
    
    def __init__(self, workspace_dir: str = ".learning/improvement"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        self.sessions_file = self.workspace / "sessions.json"
        self.current_plan_file = self.workspace / "current_plan.md"
        
        self.sessions: List[ImprovementSession] = self._load_sessions()
        self.current_phase = "idle"
    
    def _load_sessions(self) -> List[ImprovementSession]:
        """加载历史会话"""
        if self.sessions_file.exists():
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ImprovementSession(**s) for s in data]
        return []
    
    def _save_sessions(self):
        """保存会话历史"""
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(s) for s in self.sessions], f, ensure_ascii=False, indent=2)
    
    def start_planning_session(self, goal: str) -> str:
        """
        开始规划会话（Consult the oracle）
        
        这是Mitchell方法论的第一步：
        - 不急于编码
        - 先与"Oracle"（更强的推理能力）讨论计划
        - 创建详细的spec.md
        """
        session_id = f"plan-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        plan_content = f"""# 改进计划: {goal}

## 目标
{goal}

## 规划阶段（Consult the Oracle）
在开始任何编码前，先回答以下问题：

### 1. 问题分析
- 当前系统的瓶颈是什么？
- 用户的核心痛点是什么？
- 这个问题的根本原因是什么？

### 2. 解决方案探索
- 有哪些可能的解决路径？
- 每种方案的优缺点？
- Mitchell会怎么解决这个问题？

### 3. 范围限定
- 最小可行改进(MVI)是什么？
- 哪些功能必须现在做？
- 哪些可以延后？

### 4. 成功标准
- 如何衡量改进成功？
- 有哪些可量化的指标？
- 用户反馈如何收集？

### 5. 风险评估
- 可能遇到的障碍？
- 如何验证假设？
- Plan B是什么？

## 下一步
完成规划后，进入原型探索阶段。
"""
        
        # 保存计划
        plan_file = self.workspace / f"{session_id}.md"
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(plan_content)
        
        self.current_plan_file = plan_file
        self.current_phase = "planning"
        
        return f"""
🎯 **规划会话已启动**: {session_id}

**目标**: {goal}

**下一步**:
1. 完成上述规划文档的回答
2. 使用深度推理模式（Consult the oracle）思考
3. 不要急于编码，先理解问题本质

**Mitchell的原则**: 
"Creating a comprehensive plan interactively... is a really important first-step"

计划文件: {plan_file}
"""
    
    def start_prototyping_session(self, plan_ref: str) -> str:
        """
        开始原型探索会话
        
        Mitchell的方法：
        - 快速原型获得灵感
        - 不一定要保留所有代码
        - 用AI作为"muse"（缪斯）
        """
        session_id = f"proto-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        guidelines = """
## 原型探索指南（Based on Mitchell's Method）

### 目标
快速探索可能的解决方案，获得灵感。

### 原则
1. **快速迭代**: 不追求完美，追求方向正确
2. **多方案对比**: 让AI生成2-3种不同实现
3. **获得灵感**: 即使扔掉代码，也获得了思路
4. **小步前进**: 每个原型只验证一个假设

### Mitchell的提醒
> "I find the 'zero to one' stage of creation very difficult 
> and time consuming and AI is excellent at being my muse."

### 结束标准
- 找到了可行的方向？→ 进入清理阶段
- 遇到瓶颈？→ 进入瓶颈突破阶段
- 需要重构？→ 进入战略性手动干预
"""
        
        self.current_phase = "prototyping"
        
        return f"""
🔬 **原型探索会话**: {session_id}

**参考计划**: {plan_ref}

{guidelines}

**当前状态**: 🎨 探索阶段 - 快速原型，获得灵感
"""
    
    def start_cleanup_session(self, code_ref: str) -> str:
        """
        开始清理会话（Anti-Slop Session）
        
        这是Mitchell方法论的核心：
        - 每个AI编码会话后必须清理
        - 重构、重命名、移动代码
        - 添加文档
        - 确保自己理解每一行代码
        """
        session_id = f"cleanup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        cleanup_checklist = """
## Anti-Slop 清理检查清单

### 代码质量
- [ ] 重命名模糊变量/函数
- [ ] 提取重复代码为函数
- [ ] 优化条件判断（减少嵌套）
- [ ] 添加类型注解

### 架构改进
- [ ] 检查模块边界是否清晰
- [ ] 确保单一职责原则
- [ ] 优化导入顺序和分组

### 文档完善
- [ ] 为每个函数添加docstring
- [ ] 解释复杂算法的思路
- [ ] 添加使用示例
- [ ] 更新README（如果需要）

### Mitchell的清理提示示例
```
"Turn each case into a dedicated fileprivate Swift view 
that takes the typed value as its parameter 
so that we can remove the guards."
```

### 结束标准
- 代码是否比AI生成的更易读？
- 我是否理解每一行代码？
- 未来的AI能否基于这个代码更好工作？
"""
        
        self.current_phase = "cleanup"
        
        return f"""
🧹 **Anti-Slop清理会话**: {session_id}

**待清理代码**: {code_ref}

{cleanup_checklist}

**Mitchell的提醒**:
> "The cleanup step is really important. To cleanup effectively 
> you have to have a pretty good understanding of the code, 
> so this forces me to not blindly accept AI-written code."
> 
> "I sometimes tongue-in-cheek refer to this as the 'anti-slop session'."

**当前状态**: 🧽 清理阶段 - 重构、文档、理解
"""
    
    def start_review_session(self, feature_ref: str) -> str:
        """
        开始审查会话（Review without Coding）
        
        Mitchell的标准结束提示：
        - 不编写代码
        - Consult the oracle
        - 思考改进点
        - 识别遗漏的测试
        """
        session_id = f"review-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        review_prompt = f"""
## 深度审查（Consult the Oracle）

**审查目标**: {feature_ref}

### 标准审查提示（基于Mitchell）
```
Are there any other improvements you can see to be made 
with the {feature_ref}? 

Don't write any code. Consult the oracle. 

Consider parts of the code that can also get more unit tests added.
```

### 审查维度
1. **功能完整性**: 是否满足原始需求？
2. **边界情况**: 异常输入如何处理？
3. **性能**: 是否有明显的性能问题？
4. **安全**: 是否有安全隐患？
5. **可维护性**: 其他开发者能否理解？
6. **测试覆盖**: 哪些场景缺少测试？

### 输出格式
- 发现的问题（按优先级排序）
- 建议的改进（不实现，只建议）
- 下一步行动计划
"""
        
        self.current_phase = "review"
        
        return f"""
🔍 **审查会话**: {session_id}

{review_prompt}

**Mitchell的方法**:
> "I advise ending every session with a prompt like this one, 
> asking the agent about any obvious omissions..."
> 
> "Don't write any code. Consult the oracle."

**当前状态**: 👁️ 审查阶段 - 思考、分析、不编码
"""
    
    def start_manual_intervention(self, reason: str) -> str:
        """
        开始战略性手动干预
        
        Mitchell的做法：
        - 在关键架构点手动调整
        - 为后续AI会话铺路
        - 重构类型系统
        """
        session_id = f"manual-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        intervention_guide = """
## 战略性手动干预指南

### 何时需要手动干预
- 关键架构决策点
- 类型系统设计
- AI反复失败的复杂重构
- 需要深度领域知识的优化

### Mitchell的案例
从 `struct with optionals` 重构为 `tagged union`：
> "I spent some time manually restructured the view model... 
> I renamed some types, moved stuff around."
> 
> "I knew from experience that this small bit of manual work 
> in the middle would set the agents up for success 
> in future sessions..."

### 干预后
- 记录为什么这样重构
- 更新文档说明新架构
- 验证AI在新架构上工作更好
"""
        
        self.current_phase = "manual"
        
        return f"""
✋ **战略性手动干预**: {session_id}

**干预原因**: {reason}

{intervention_guide}

**当前状态**: 🔧 手动干预 - 关键架构调整，为AI铺路
"""
    
    def handle_breakthrough(self, problem: str) -> str:
        """
        处理瓶颈突破
        
        Mitchell的关键洞察：
        - AI反复失败时，停止用AI
        - 切换到人工研究
        - "AI is no longer the solution; it is a liability"
        """
        session_id = f"breakthrough-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        breakthrough_protocol = f"""
## 瓶颈突破协议 🚨

**当前问题**: {problem}

### Mitchell的警告
> "It's at this point that I know I need to step back, 
> review what it did, and come up with my own plans."
> 
> "It's time to educate myself and think critically. 
> AI is no longer the solution; it is a liability."

### 突破步骤
1. **停止AI协助**: 不再使用AI生成代码
2. **问题分析**: 手写/画出问题本质
3. **资料研究**: 搜索相关文档、论文、源码
4. **深度思考**: 散步/洗澡时思考（Mitchell推荐）
5. **小规模实验**: 手动写最小复现
6. **验证理解**: 确保完全理解后再用AI

### 返回AI的条件
- ✅ 完全理解问题根因
- ✅ 有清晰的解决思路
- ✅ 能给AI明确的指导

### 记录
记录突破过程，这是重要的学习资产。
"""
        
        self.current_phase = "breakthrough"
        
        return f"""
💡 **瓶颈突破会话**: {session_id}

{breakthrough_protocol}

**当前状态**: 🧠 深度思考 - 停止AI，人工研究
"""
    
    def log_session(self, session_type: SessionType, goal: str, 
                   plan: str, output: str, learnings: str, next_steps: str):
        """记录会话"""
        session = ImprovementSession(
            session_id=f"{session_type.value}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            session_type=session_type,
            goal=goal,
            plan=plan,
            output=output,
            learnings=learnings,
            next_steps=next_steps
        )
        
        self.sessions.append(session)
        self._save_sessions()
        
        return f"✅ 会话已记录: {session.session_id}"
    
    def get_stats(self) -> Dict:
        """获取改进统计"""
        return {
            "total_sessions": len(self.sessions),
            "by_type": {
                t.value: len([s for s in self.sessions if s.session_type == t])
                for t in SessionType
            },
            "current_phase": self.current_phase,
            "recent_learnings": [s.learnings for s in self.sessions[-5:]]
        }


def demo_workflow():
    """演示完整工作流"""
    workflow = SelfImprovementWorkflow()
    
    print("=" * 60)
    print("🚀 Self-Improvement Workflow Demo")
    print("   Based on Mitchell Hashimoto's Methodology")
    print("=" * 60)
    
    # 1. 规划阶段
    print("\n[Phase 1] Planning Session")
    print("-" * 40)
    print(workflow.start_planning_session(
        "改进我的不确定性检测系统，使其更准确"
    ))
    
    # 2. 原型探索
    print("\n[Phase 2] Prototyping Session")
    print("-" * 40)
    print(workflow.start_prototyping_session("plan-20260313-123456"))
    
    # 3. 清理会议
    print("\n[Phase 3] Cleanup Session (Anti-Slop)")
    print("-" * 40)
    print(workflow.start_cleanup_session(".tools/uncertainty_detector.py"))
    
    # 4. 审查阶段
    print("\n[Phase 4] Review Session")
    print("-" * 40)
    print(workflow.start_review_session("uncertainty_detector"))
    
    # 5. 瓶颈突破（示例）
    print("\n[Phase 5] Breakthrough Session")
    print("-" * 40)
    print(workflow.handle_breakthrough(
        "AI无法理解复杂的置信度计算逻辑"
    ))
    
    print("\n" + "=" * 60)
    print("📊 统计")
    print("=" * 60)
    stats = workflow.get_stats()
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Current phase: {stats['current_phase']}")


if __name__ == "__main__":
    demo_workflow()
