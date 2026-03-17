#!/usr/bin/env python3
"""
CodeDev Agent - 基于ChatDev角色的代码开发Agent
支持多角色协作：架构师、开发者、测试员、审查员
"""

import os
import sys
import json
import time
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from queue import Queue
from threading import Thread, Event

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('codedev')

# 路径配置（必须在导入 Task Planner 之前定义）
WORKSPACE = Path('/root/.openclaw/workspace')
CODEDEV_DIR = WORKSPACE / 'skills' / 'code-dev-agent'
CODEDEV_DIR.mkdir(exist_ok=True)

REQUESTS_DIR = CODEDEV_DIR / 'requests'
REQUESTS_DIR.mkdir(exist_ok=True)
RESULTS_DIR = CODEDEV_DIR / 'results'
RESULTS_DIR.mkdir(exist_ok=True)
LOGS_DIR = CODEDEV_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# 导入IER系统
try:
    from ier_system import (
        get_experience_manager, ExperienceManager, 
        ExperienceType, ExperienceStatus, Experience
    )
    IER_AVAILABLE = True
except ImportError:
    IER_AVAILABLE = False
    logger.warning("IER系统不可用，经验精炼功能将被禁用")

# 导入 Task Planner
try:
    sys.path.insert(0, str(WORKSPACE / 'skills' / 'task-planner'))
    from planner import TaskPlanner, TaskComplexity
    from openclaw_integration import check_planning_needed, plan
    PLANNER_AVAILABLE = True
except ImportError as e:
    PLANNER_AVAILABLE = False
    logger.warning(f"Task Planner不可用: {e}")

class RoleType(Enum):
    """角色类型"""
    ARCHITECT = "architect"      # 架构师
    DEVELOPER = "developer"      # 开发者
    TESTER = "tester"            # 测试员
    REVIEWER = "reviewer"        # 审查员

@dataclass
class Role:
    """角色定义"""
    name: str
    role_type: RoleType
    system_prompt: str
    responsibilities: List[str]

# 角色定义
ROLES = {
    RoleType.ARCHITECT: Role(
        name="Software Architect",
        role_type=RoleType.ARCHITECT,
        system_prompt="""你是资深软件架构师，拥有20年系统设计经验，精通第一性原理架构思维。

你的核心架构思维框架：

## 1. 第一性原理分析 (First Principles Thinking)
执行任何设计前，必须先回答：
- 这个需求的本质是什么？
- 最基本的组成部分有哪些？
- 物理/逻辑约束是什么？
- 剥离所有假设后，还剩什么？

## 2. 双路径认知架构 (System 1 / System 2)
- System 1 (快路径): 模式匹配、经验复用、快速响应
  - 触发条件: 熟悉任务、时间敏感、低错误成本
  - 策略: 利用已有模式，最小化计算
  
- System 2 (慢路径): 深度推理、验证假设、批判思考
  - 触发条件: 复杂问题、高错误成本、不确定性
  - 策略: 拆解问题、逐步推理、验证结果

## 3. 物理现实检查 (Physical Reality Check)
面对任何涉及真实世界的概念，必须验证：
- 这个词代表什么物理/逻辑实体？
- 这个实体的约束和限制是什么？
- 我的假设是否符合物理/逻辑定律？
- 时间尺度合理吗？（秒级vs分钟级vs小时级）
- 资源限制考虑了吗？（CPU/内存/网络/存储）

## 4. 系统边界识别 (System Boundary Analysis)
- 输入边界: 输入是什么格式？范围？合法性？
- 处理边界: 核心逻辑 vs 边缘情况
- 输出边界: 输出承诺什么？不承诺什么？
- 故障边界: 什么情况下会失败？如何优雅降级？

## 5. 元认知检查 (Meta-Cognitive Check)
设计完成后，必须自问：
- 我做了什么假设？这些假设成立吗？
- 这是最简方案吗？有没有更短路径？
- 如果我的设计错了，Plan B是什么？
- 这个设计在极端情况下会怎样？

## 6. 反模式警示 (Anti-Pattern Alert)
警惕以下思维陷阱：
- ❌ 流程迷信: "上次这样做成功了"
- ❌ 过度推断: "用户说A，我就做A+B+C"
- ❌ 完美主义: "要做到100分才交付"
- ❌ 单一视角: 只从技术角度思考

你的职责：
1. 深度分析用户需求，应用第一性原理剥离表象
2. 识别核心问题和隐含需求，考虑物理现实约束
3. 设计优雅、可扩展、可维护的技术方案
4. 规划代码结构和模块划分，明确系统边界
5. 识别潜在风险、技术难点和故障模式
6. 提供多种方案并给出选择的理由

工作原则：
- 先问"为什么存在这个问题"，再问"怎么解决"
- 从最基本的事实出发重构解决方案
- 每个设计决策必须有明确的理由
- 方案要具体可执行，包含边界情况处理
- 考虑异常处理、性能、安全性、可测试性

输出要求：
- 需求的第一性原理解构
- 系统边界和约束分析
- 技术选型理由（含对比方案）
- 核心数据结构和算法
- 接口定义和契约
- 风险评估和应对策略
- 复杂度分析（时间/空间）""",
        responsibilities=["需求分析", "第一性原理解构", "架构设计", "技术选型", "风险评估"]
    ),
    
    RoleType.DEVELOPER: Role(
        name="Senior Developer",
        role_type=RoleType.DEVELOPER,
        system_prompt="""你是资深开发者，代码质量极高，擅长防止代码幻觉。

你的职责：
1. 根据架构设计编写完整可运行的代码
2. 实现所有功能，包括边界情况和错误处理
3. 编写清晰的注释和文档字符串
4. 确保代码可以直接运行，无占位符

**防幻觉原则**：

在编写代码前，必须先澄清：
- 输入参数的具体类型和约束
- 输出返回值的类型和格式
- 边界情况（空值、超限、特殊字符）
- 错误处理策略（异常类型、错误信息）
- 性能要求（时间/空间复杂度）

**代码完整性检查清单**（提交前必须确认）：
- [ ] 所有函数都有完整的文档字符串
- [ ] 输入参数都进行了类型检查和验证
- [ ] 边界情况（空值、超大输入、特殊字符）都有处理
- [ ] 错误处理逻辑完整（try-except-finally）
- [ ] 代码可以直接运行，没有TODO/FIXME/pass/...
- [ ] 所有引用的变量/函数都已定义
- [ ] 符合澄清阶段确定的所有要求

**绝对禁止**：
- ❌ 使用"# TODO"或"# FIXME"
- ❌ 使用"..."（ellipsis）作为占位符
- ❌ 省略实现细节
- ❌ 使用伪代码
- ❌ 假设输入总是有效
- ❌ 忽略错误处理

**编码标准**：
- 代码必须完整、可执行、无占位符
- 每个函数都要有清晰的文档字符串（Args/Returns/Raises）
- 变量命名要有意义
- 必须包含错误处理和输入验证
- 遵循PEP 8规范（Python）

**如果出现不确定的地方**：
不要猜测！在澄清阶段提出明确问题，获取准确信息后再编码。""",
        responsibilities=["代码实现", "功能开发", "bug修复", "防幻觉编码"]
    ),
    
    RoleType.TESTER: Role(
        name="QA Engineer",
        role_type=RoleType.TESTER,
        system_prompt="""你是严格的QA工程师，专门发现代码缺陷。

你的职责：
1. 逐行审查代码逻辑
2. 识别潜在的bug、边界情况和异常
3. 验证代码是否满足原始需求
4. 提出具体的修改建议

检查清单：
- 输入验证是否完整？
- 边界情况是否处理？
- 错误处理是否到位？
- 是否存在逻辑漏洞？
- 性能是否有问题？
- 是否符合原始需求？

输出要求：
- 发现的问题列表（如有）
- 具体的修改建议
- 验证结论（通过/不通过）""",
        responsibilities=["代码审查", "bug发现", "质量验证"]
    ),
    
    RoleType.REVIEWER: Role(
        name="Code Reviewer",
        role_type=RoleType.REVIEWER,
        system_prompt="""你是资深代码审查员，关注代码质量和可维护性。

你的职责：
1. 审查代码结构和设计质量
2. 评估代码可读性和可维护性
3. 检查是否符合设计模式
4. 给出改进建议

审查维度：
- 代码清晰度
- 设计合理性
- 可测试性
- 可扩展性
- 文档完整性

输出要求：
- 代码评分（1-10）
- 主要优点
- 改进建议
- 是否通过审查""",
        responsibilities=["代码质量", "设计审查", "最佳实践"]
    )
}

@dataclass
class ChatNode:
    """聊天链节点"""
    id: str
    role_type: RoleType
    task: str
    input_context: Dict = field(default_factory=dict)
    output_result: str = ""
    status: str = "pending"  # pending, running, completed, failed
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class CodeDevRequest:
    """代码开发请求"""
    request_id: str
    description: str
    language: str = "python"
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    priority: int = 5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return asdict(self)

class LLMClient:
    """LLM客户端（模拟，实际接入你的LLM）"""
    
    def __init__(self):
        self.model = "kimi-coding/k2p5"
    
    def chat(self, prompt: str, system: str = "") -> str:
        """
        调用LLM进行对话
        实际实现中会调用你的LLM接口
        """
        # 这里应该调用实际的LLM
        # 现在返回模拟响应
        return f"[LLM Response for: {prompt[:50]}...]"

class CommunicativeDehallucination:
    """ChatDev式防幻觉机制 - 强化版，专门针对代码开发"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.max_clarification_rounds = 3  # 最多3轮澄清
        
        # 代码开发专用的澄清检查清单
        self.code_clarification_checklist = """
代码开发澄清检查清单 (Code Development Clarification Checklist):

1. 输入边界 (Input Boundaries):
   - 输入参数的类型是什么？(int/str/list/dict?)
   - 输入值的有效范围？
   - 是否可能为None/空值？
   - 输入长度/大小限制？

2. 输出承诺 (Output Commitments):
   - 函数返回什么类型？
   - 成功时返回什么？
   - 失败时返回什么？(None/异常/默认值？)
   - 返回值是否可能为None？

3. 边界情况 (Edge Cases):
   - 空输入怎么处理？
   - 超大输入怎么处理？
   - 特殊字符/格式怎么处理？
   - 并发/线程安全要求？

4. 错误处理 (Error Handling):
   - 哪些情况应该抛异常？
   - 异常类型应该是什么？
   - 是否需要错误日志？
   - 是否需要重试机制？

5. 性能要求 (Performance):
   - 时间复杂度要求？(O(1)/O(n)/O(logn)?)
   - 空间复杂度限制？
   - 是否需要缓存优化？
   - 大数据量处理方式？

6. 依赖与集成 (Dependencies):
   - 可以使用哪些标准库？
   - 是否允许第三方依赖？
   - 需要兼容的Python版本？
   - 与现有代码的集成方式？

7. 测试要求 (Testing):
   - 是否需要包含测试用例？
   - 测试覆盖哪些场景？
   - 是否需要Mock/Fixture？
"""
    
    def execute_with_clarification(self, role: Role, task: str, context: Dict) -> str:
        """执行前先澄清需求 - 多轮迭代版本"""
        
        # 根据角色类型选择澄清策略
        if role.role_type == RoleType.DEVELOPER:
            return self._developer_clarification(role, task, context)
        elif role.role_type == RoleType.ARCHITECT:
            return self._architect_clarification(role, task, context)
        else:
            return self._basic_clarification(role, task, context)
    
    def _developer_clarification(self, role: Role, task: str, context: Dict) -> str:
        """开发者专用澄清流程 - 严格防止代码幻觉"""
        
        current_context = context.copy()
        all_clarifications = []
        
        for round_num in range(1, self.max_clarification_rounds + 1):
            # 生成澄清问题
            clarification_prompt = f"""{role.system_prompt}

{self.code_clarification_checklist}

当前任务：{task}

已收集的上下文：
{json.dumps(current_context, indent=2, ensure_ascii=False)}

已澄清的问题（第{round_num-1}轮）：
{json.dumps(all_clarifications, indent=2, ensure_ascii=False) if all_clarifications else "无"}

请严格按照以下步骤执行：

**步骤1：自我检查**
基于以上检查清单，分析当前任务还有哪些信息不明确？
哪些边界情况没有定义？
哪些假设可能不成立？

**步骤2：提出澄清问题**
列出最多3个最关键的澄清问题。
这些问题必须能够：
- 消除代码歧义
- 明确边界条件
- 防止实现错误

格式：
CLARIFICATION_QUESTIONS:
1. [具体问题，不要模糊]
2. [具体问题，不要模糊]
3. [具体问题，不要模糊]

**步骤3：判断是否可以开始编码**
如果所有关键信息都已明确，回答：READY_TO_CODE
如果还有不明确的地方，继续提出澄清问题。
"""
            
            response = self.llm.chat(clarification_prompt)
            
            # 检查是否可以开始编码
            if "READY_TO_CODE" in response:
                break
            
            # 提取澄清问题
            questions = self._extract_questions(response)
            
            if not questions:
                # 没有问题但也没有READY标记，继续下一轮或退出
                if round_num >= 2:
                    break
                continue
            
            # 自动回答澄清问题
            answers = self._auto_answer_questions_for_code(questions, current_context)
            
            # 记录澄清
            clarification_round = {
                "round": round_num,
                "questions": questions,
                "answers": answers
            }
            all_clarifications.append(clarification_round)
            
            # 更新上下文
            current_context["clarifications"] = all_clarifications
        
        # 最终执行：基于所有澄清后的信息编写代码
        return self._execute_developer_task(role, task, current_context)
    
    def _architect_clarification(self, role: Role, task: str, context: Dict) -> str:
        """架构师专用澄清流程"""
        
        clarification_prompt = f"""{role.system_prompt}

当前任务：{task}

上下文：
{json.dumps(context, indent=2, ensure_ascii=False)}

在给出架构设计之前，请先回答：

**关键澄清问题**：
1. 这个需求的本质是什么？用户真正需要解决什么问题？
2. 有哪些隐藏的约束条件？（性能、安全、兼容性）
3. 系统的边界在哪里？输入/输出/失败模式？
4. 有哪些假设条件？如果假设不成立会怎样？

格式：
CLARIFICATION_QUESTIONS:
1. [问题]
2. [问题]
3. [问题]

如果任务已经很清晰，直接回答：NO_QUESTIONS
"""
        
        response = self.llm.chat(clarification_prompt)
        
        # 检查是否需要澄清
        if "NO_QUESTIONS" in response or "CLARIFICATION_QUESTIONS:" not in response:
            return self._execute_task(role, task, context)
        
        questions = self._extract_questions(response)
        
        if not questions:
            return self._execute_task(role, task, context)
        
        answers = self._auto_answer_questions_for_architecture(questions, context)
        
        enhanced_context = {
            **context,
            "architect_clarifications": {
                "questions": questions,
                "answers": answers
            }
        }
        
        return self._execute_task(role, task, enhanced_context)
    
    def _basic_clarification(self, role: Role, task: str, context: Dict) -> str:
        """基本澄清流程（Reviewer/Tester）"""
        
        clarification_prompt = f"""{role.system_prompt}

当前任务：{task}

上下文：
{json.dumps(context, indent=2, ensure_ascii=False)}

在给出反馈之前，请先分析：
1. 你对任务的理解是否完整？
2. 有哪些信息可能缺失？
3. 列出最多2个澄清问题。

格式：
CLARIFICATION_QUESTIONS:
1. [问题1]
2. [问题2]

如果很清晰，回答：NO_QUESTIONS
"""
        
        response = self.llm.chat(clarification_prompt)
        
        if "NO_QUESTIONS" in response or "CLARIFICATION_QUESTIONS:" not in response:
            return self._execute_task(role, task, context)
        
        questions = self._extract_questions(response)
        
        if not questions:
            return self._execute_task(role, task, context)
        
        answers = self._auto_answer_questions(questions, context)
        
        enhanced_context = {
            **context,
            "clarifications": {
                "questions": questions,
                "answers": answers
            }
        }
        
        return self._execute_task(role, task, enhanced_context)
    
    def _execute_developer_task(self, role: Role, task: str, context: Dict) -> str:
        """开发者专用任务执行 - 强制代码完整性检查"""
        
        # 首先生成代码
        code_prompt = f"""{role.system_prompt}

任务：{task}

所有澄清后的信息：
{json.dumps(context, indent=2, ensure_ascii=False)}

请编写完整的代码实现。

**重要：代码完整性检查清单**
在提交代码前，请确认：
- [ ] 所有函数都有完整的文档字符串
- [ ] 输入参数都进行了类型检查
- [ ] 边界情况都有处理
- [ ] 错误处理逻辑完整
- [ ] 代码可以直接运行，没有TODO/FIXME
- [ ] 符合澄清阶段确定的所有要求

请提供完整的代码实现。"""
        
        code = self.llm.chat(code_prompt)
        
        # 第二遍：自我审查，检查是否还有幻觉
        review_prompt = f"""你是一名严格的代码审查员。请审查以下代码：

{code}

**幻觉检查清单**：
1. 是否有未实现的占位符？（pass/ellipsis/TODO）
2. 是否有假设但未验证的输入？
3. 是否有引用但未定义的变量/函数？
4. 是否有不完整的错误处理？
5. 是否有未处理的边界情况？

如果发现任何问题，请直接修复并提供修正后的完整代码。
如果没有问题，直接返回原代码。

格式：
CODE_REVIEW_RESULT: [PASS/NEEDS_FIX]
如果NEEDS_FIX，提供修复后的代码。"""
        
        reviewed_code = self.llm.chat(review_prompt)
        
        # 提取最终代码
        if "CODE_REVIEW_RESULT: PASS" in reviewed_code:
            return code
        else:
            # 从review响应中提取修复后的代码
            return self._extract_code_from_review(reviewed_code) or code
    
    def _auto_answer_questions_for_code(self, questions: List[str], context: Dict) -> List[str]:
        """为代码开发问题提供智能回答"""
        answers = []
        language = context.get("language", "python")
        requirements = context.get("requirements", [])
        constraints = context.get("constraints", [])
        
        for q in questions:
            q_lower = q.lower()
            
            # 输入类型相关问题
            if any(kw in q_lower for kw in ["输入", "input", "参数", "parameter", "类型", "type"]):
                if "字符串" in q or "string" in q_lower:
                    answers.append("输入为str类型，允许空字符串，需要验证长度")
                elif "数字" in q or "number" in q_lower or "int" in q_lower:
                    answers.append("输入为int或float，范围根据业务逻辑确定，需要验证非负")
                elif "列表" in q or "list" in q_lower or "数组" in q:
                    answers.append("输入为list，可以为空，元素类型根据上下文确定")
                else:
                    answers.append(f"输入类型根据实际需求确定，建议参考：{requirements}")
            
            # 输出相关问题
            elif any(kw in q_lower for kw in ["输出", "output", "返回", "return"]):
                answers.append("函数返回处理结果，成功返回数据，失败返回None或抛出异常")
            
            # 边界情况
            elif any(kw in q_lower for kw in ["边界", "edge", "空值", "null", "none", "empty"]):
                answers.append("需要处理空值、None、空字符串/列表等边界情况，抛出ValueError或返回默认值")
            
            # 错误处理
            elif any(kw in q_lower for kw in ["错误", "error", "异常", "exception", "失败", "fail"]):
                answers.append("使用适当的异常类型（ValueError/TypeError/RuntimeError），提供清晰的错误信息")
            
            # 性能要求
            elif any(kw in q_lower for kw in ["性能", "performance", "复杂度", "complexity", "时间", "time"]):
                if constraints:
                    answers.append(f"性能约束：{constraints}")
                else:
                    answers.append("时间复杂度O(n)，空间复杂度O(1)，如有性能要求请明确")
            
            # 依赖相关问题
            elif any(kw in q_lower for kw in ["依赖", "dependency", "库", "library", "导入", "import"]):
                answers.append(f"使用{language}标准库，避免不必要的第三方依赖")
            
            # 默认回答
            else:
                answers.append("基于最佳实践和常见模式实现，如遇特殊情况请明确说明")
        
        return answers
    
    def _auto_answer_questions_for_architecture(self, questions: List[str], context: Dict) -> List[str]:
        """为架构设计问题提供智能回答"""
        answers = []
        
        for q in questions:
            q_lower = q.lower()
            
            if "本质" in q or "essence" in q_lower or "真正" in q:
                answers.append("本质是提供一个可靠、可维护的解决方案，满足功能需求的同时保证质量和性能")
            elif "约束" in q or "constraint" in q_lower:
                answers.append("约束包括：性能要求、资源限制、兼容性需求、安全要求，具体请参考需求文档")
            elif "边界" in q or "boundary" in q_lower:
                answers.append("系统边界：明确输入验证、输出承诺、故障模式、异常处理范围")
            elif "假设" in q or "assumption" in q_lower:
                answers.append("假设：输入数据格式正确、资源可用、依赖服务正常，所有假设都需要验证和备选方案")
            else:
                answers.append("基于第一性原理分析，采用最简洁可靠的方案")
        
        return answers
    
    def _extract_code_from_review(self, review_response: str) -> Optional[str]:
        """从审查响应中提取修复后的代码"""
        # 查找代码块
        code_pattern = r'```(?:python)?\n(.*?)\n```'
        matches = re.findall(code_pattern, review_response, re.DOTALL)
        if matches:
            return matches[-1]  # 返回最后一个代码块
        return None
    
    def _extract_questions(self, response: str) -> List[str]:
        """提取澄清问题"""
        questions = []
        lines = response.split('\n')
        in_questions = False
        
        for line in lines:
            if 'CLARIFICATION_QUESTIONS:' in line:
                in_questions = True
                continue
            if in_questions:
                if line.strip().startswith(('1.', '2.', '3.', '-', '*')):
                    q = line.strip().lstrip('123.-* ').strip()
                    if q and not q.startswith('[') and len(q) > 5:
                        questions.append(q)
        
        return questions[:3]
    
    def _execute_task(self, role: Role, task: str, context: Dict) -> str:
        """执行任务"""
        
        # 如果是架构师，使用结构化输出格式
        if role.role_type == RoleType.ARCHITECT:
            prompt = f"""{role.system_prompt}

任务：{task}

上下文：
{json.dumps(context, indent=2, ensure_ascii=False)}

请按照以下结构化格式输出你的架构设计：

# 架构设计报告

## 1. 需求的第一性原理解构
- 表面需求：用户说了什么
- 本质需求：用户真正需要什么
- 根本约束：物理/逻辑限制是什么
- 边界条件：极端情况会怎样

## 2. 双路径分析
### System 1 (模式识别)
- 这个问题匹配什么已知模式？
- 有哪些现成的解决方案？

### System 2 (深度推理)
- 为什么这些方案适合/不适合？
- 有哪些隐藏假设需要验证？

## 3. 物理现实检查
- 涉及的实体是什么？
- 时间和资源约束？
- 失败模式有哪些？

## 4. 系统边界分析
- 输入边界：
- 处理边界：
- 输出边界：
- 故障边界：

## 5. 技术方案
### 方案A（推荐）
- 设计思路：
- 核心数据结构：
- 关键算法：
- 接口定义：
- 复杂度分析：

### 方案B（备选）
- 适用场景：
- 优缺点：

## 6. 风险评估
- 技术风险：
- 性能风险：
- 维护风险：
- 应对策略：

## 7. 元认知检查
- 关键假设：
- 验证方法：
- 如果错了怎么办：

请完成你的架构设计。"""
        else:
            prompt = f"""{role.system_prompt}

任务：{task}

上下文：
{json.dumps(context, indent=2, ensure_ascii=False)}

请完成你的任务。"""
        
        return self.llm.chat(prompt)

class ChatChain:
    """聊天链编排器"""
    
    def __init__(self, name: str, nodes: List[ChatNode], shared_context: Dict):
        self.name = name
        self.nodes = nodes
        self.shared_context = shared_context
        self.current_index = 0
        self.dehallucination = CommunicativeDehallucination(LLMClient())
        self.logger = logging.getLogger(f'codedev.chain.{name}')
    
    def execute(self) -> Dict:
        """执行整个聊天链"""
        self.logger.info(f"开始执行聊天链: {self.name}")
        results = []
        
        for i, node in enumerate(self.nodes):
            self.current_index = i
            self.logger.info(f"执行节点 {i+1}/{len(self.nodes)}: {node.role_type.value}")
            
            try:
                # 准备上下文
                context = self._build_context(node)
                
                # 执行角色任务（带防幻觉）
                role = ROLES[node.role_type]
                result = self.dehallucination.execute_with_clarification(
                    role, node.task, context
                )
                
                node.output_result = result
                node.status = "completed"
                
                # 更新共享上下文
                self.shared_context[f"{node.role_type.value}_{i}"] = result
                
                results.append({
                    "node_id": node.id,
                    "role": node.role_type.value,
                    "task": node.task,
                    "result": result,
                    "status": "completed"
                })
                
            except Exception as e:
                self.logger.error(f"节点 {node.id} 执行失败: {e}")
                node.status = "failed"
                results.append({
                    "node_id": node.id,
                    "role": node.role_type.value,
                    "task": node.task,
                    "error": str(e),
                    "status": "failed"
                })
                break
        
        return {
            "success": all(r["status"] == "completed" for r in results),
            "chain_name": self.name,
            "results": results,
            "final_output": results[-1]["result"] if results else "",
            "shared_context": self.shared_context
        }
    
    def _build_context(self, current_node: ChatNode) -> Dict:
        """构建上下文"""
        context = {
            "original_request": self.shared_context.get("original_request", {}),
            "language": self.shared_context.get("language", "python"),
            "previous_results": []
        }
        
        for i, node in enumerate(self.nodes):
            if i < self.current_index and node.status == "completed":
                context["previous_results"].append({
                    "role": node.role_type.value,
                    "task": node.task,
                    "output": node.output_result[:1000]  # 截断避免过长
                })
        
        return context

class CodeDevService:
    """代码开发Agent服务 - 集成IER经验精炼系统"""
    
    def __init__(self):
        self.request_queue = Queue()
        self.running = False
        self.worker_thread = None
        self.logger = logging.getLogger('codedev.service')
        
        # 初始化IER系统
        self.exp_manager = None
        if IER_AVAILABLE:
            try:
                self.exp_manager = get_experience_manager()
                self.logger.info("IER经验精炼系统已加载")
            except Exception as e:
                self.logger.error(f"IER系统初始化失败: {e}")
    
    def start(self):
        """启动服务"""
        self.running = True
        self.worker_thread = Thread(target=self._worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        self.logger.info("CodeDev Agent服务已启动")
        
        # 启动时运行经验淘汰
        if self.exp_manager:
            self._run_experience_elimination()
    
    def _run_experience_elimination(self):
        """运行经验淘汰"""
        try:
            eliminated = self.exp_manager.evaluate_and_eliminate()
            if eliminated:
                self.logger.info(f"IER: 淘汰了 {len(eliminated)} 条经验")
            stats = self.exp_manager.get_statistics()
            self.logger.info(f"IER统计: {stats['active_experiences']}/{stats['total_experiences']} 活跃经验")
        except Exception as e:
            self.logger.error(f"经验淘汰失败: {e}")
    
    def stop(self):
        """停止服务"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.logger.info("CodeDev Agent服务已停止")
    
    def _worker_loop(self):
        """工作循环"""
        while self.running:
            try:
                # 检查请求文件
                for req_file in REQUESTS_DIR.glob("req_*.json"):
                    self._process_request_file(req_file)
                
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"工作循环错误: {e}")
                time.sleep(5)
    
    def _process_request_file(self, req_file: Path):
        """处理请求文件 - 集成IER经验利用 + Task Planner规划检查"""
        try:
            with open(req_file, 'r') as f:
                data = json.load(f)
            
            request = CodeDevRequest(**data)
            self.logger.info(f"处理请求: {request.request_id}")
            
            # ========== Task Planner: 任务规划检查 ==========
            plan_result = None
            if PLANNER_AVAILABLE:
                try:
                    planner = TaskPlanner()
                    complexity = planner.assess_complexity(request.description)
                    
                    if complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]:
                        self.logger.info(f"TaskPlanner: 任务复杂度为 {complexity.value}，生成执行计划")
                        
                        # 生成计划
                        import asyncio
                        plan_obj = asyncio.run(planner.generate_plan(request.description))
                        plan_formatted = planner.format_plan(plan_obj)
                        
                        plan_result = {
                            "task_id": plan_obj.task_id,
                            "complexity": plan_obj.complexity.value,
                            "constraints": [
                                {"category": c.category, "description": c.description, "priority": c.priority}
                                for c in plan_obj.constraints
                            ],
                            "steps": [
                                {"id": s.step_id, "desc": s.description, "time": s.estimated_time}
                                for s in plan_obj.steps
                            ],
                            "risks": plan_obj.risks
                        }
                        
                        self.logger.info(f"TaskPlanner: 计划已生成 ({plan_obj.task_id})")
                        
                        # 如果是复杂任务，添加规划建议到请求
                        if complexity == TaskComplexity.COMPLEX:
                            self.logger.info("TaskPlanner: 复杂任务，建议分阶段执行")
                    else:
                        self.logger.info(f"TaskPlanner: 简单任务，直接执行")
                        
                except Exception as e:
                    self.logger.warning(f"TaskPlanner规划失败: {e}")
            
            # IER: 记录任务开始
            if self.exp_manager:
                self.exp_manager.record_task_start(
                    request.request_id,
                    request.description,
                    request.language
                )
            
            # IER: 检索相关经验
            relevant_exps = []
            exp_prompt = ""
            if self.exp_manager:
                relevant_exps = self.exp_manager.retrieve_relevant_experiences(
                    request.description,
                    request.language,
                    top_k=3
                )
                if relevant_exps:
                    exp_prompt = self.exp_manager.format_experiences_for_prompt(relevant_exps)
                    self.logger.info(f"IER: 找到 {len(relevant_exps)} 条相关经验")
            
            # 创建并执行开发链（传入经验和计划）
            result = self._create_and_execute_chain(request, exp_prompt, plan_result)
            
            # IER: 提取新经验
            if self.exp_manager and result.get('success'):
                try:
                    new_exps = self.exp_manager.acquire_from_task(
                        request.request_id,
                        request.description,
                        result,
                        result.get('final_output', '')
                    )
                    if new_exps:
                        self.logger.info(f"IER: 提取了 {len(new_exps)} 条新经验")
                        result['experiences_generated'] = [exp.id for exp in new_exps]
                except Exception as e:
                    self.logger.error(f"IER经验提取失败: {e}")
            
            # IER: 记录任务完成
            if self.exp_manager:
                self.exp_manager.record_task_complete(
                    request.request_id,
                    result.get('success', False),
                    result.get('error')
                )
            
            # 保存结果
            result_file = RESULTS_DIR / f"result_{request.request_id}.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # 删除请求文件
            req_file.unlink()
            self.logger.info(f"请求 {request.request_id} 处理完成")
            
        except Exception as e:
            self.logger.error(f"处理请求文件失败: {e}")
    
    def _create_and_execute_chain(self, request: CodeDevRequest, experience_prompt: str = "", plan_result: Dict = None) -> Dict:
        """创建并执行开发链 - 集成IER经验 + Task Planner计划"""
        
        # 创建瀑布模型节点
        architect_task = f"设计解决方案: {request.description}"
        if experience_prompt:
            architect_task += f"\n\n{experience_prompt}"
        
        # 如果有规划结果，添加到架构师任务中
        if plan_result:
            constraints_str = "\n".join([f"- [{c['category']}] {c['description']} (P{c['priority']})" 
                                         for c in plan_result.get('constraints', [])])
            risks_str = "\n".join([f"- {r}" for r in plan_result.get('risks', [])])
            
            architect_task += f"""

[Task Planner 生成的约束和计划]
任务复杂度: {plan_result.get('complexity', 'unknown')}
计划ID: {plan_result.get('task_id', 'N/A')}

约束条件:
{constraints_str if constraints_str else '(无特殊约束)'}

执行步骤:
"""
            for step in plan_result.get('steps', []):
                architect_task += f"{step['id']}. {step['desc']} - {step['time']}\n"
            
            if risks_str:
                architect_task += f"\n风险识别:\n{risks_str}\n"
            
            architect_task += "\n请基于以上约束和计划进行架构设计。"
        
        nodes = [
            ChatNode(
                id="design",
                role_type=RoleType.ARCHITECT,
                task=architect_task
            ),
            ChatNode(
                id="implement",
                role_type=RoleType.DEVELOPER,
                task="根据架构设计编写完整代码"
            ),
            ChatNode(
                id="review",
                role_type=RoleType.REVIEWER,
                task="审查代码质量"
            ),
            ChatNode(
                id="test",
                role_type=RoleType.TESTER,
                task="验证代码正确性"
            )
        ]
        
        # 创建聊天链
        shared_context = {
            "original_request": request.to_dict(),
            "language": request.language,
            "requirements": request.requirements,
            "constraints": request.constraints,
            "experience_prompt": experience_prompt
        }
        
        # 添加计划信息到共享上下文
        if plan_result:
            shared_context["plan"] = plan_result
        
        chain = ChatChain(
            name=f"dev_{request.request_id}",
            nodes=nodes,
            shared_context=shared_context
        )
        
        # 执行
        result = chain.execute()
        
        # 添加IER相关信息到结果
        if experience_prompt:
            result['ier_used'] = True
        
        # 添加Task Planner相关信息到结果
        if plan_result:
            result['plan_used'] = True
            result['plan_task_id'] = plan_result.get('task_id')
            result['plan_complexity'] = plan_result.get('complexity')
        
        return result
    
    def submit_request(self, description: str, language: str = "python",
                       requirements: List[str] = None, 
                       constraints: List[str] = None) -> str:
        """提交开发请求"""
        request_id = f"CODEDEV_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        request = CodeDevRequest(
            request_id=request_id,
            description=description,
            language=language,
            requirements=requirements or [],
            constraints=constraints or []
        )
        
        req_file = REQUESTS_DIR / f"req_{request_id}.json"
        with open(req_file, 'w') as f:
            json.dump(request.to_dict(), f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"提交请求: {request_id}")
        return request_id
    
    def get_result(self, request_id: str) -> Optional[Dict]:
        """获取结果"""
        result_file = RESULTS_DIR / f"result_{request_id}.json"
        if result_file.exists():
            with open(result_file, 'r') as f:
                return json.load(f)
        return None
    
    def generate_report(self, result: Dict) -> str:
        """生成开发报告 - 包含IER信息"""
        report = f"""# 代码开发报告

**链名称**: {result['chain_name']}
**执行时间**: {datetime.now().isoformat()}
**状态**: {'✅ 成功' if result['success'] else '❌ 失败'}

"""
        
        # 添加IER信息
        if result.get('ier_used'):
            report += "**IER经验系统**: ✅ 已使用相关经验\n\n"
        
        if result.get('experiences_generated'):
            report += f"**IER新经验**: 提取了 {len(result['experiences_generated'])} 条新经验\n\n"
        
        report += """## 执行流程

"""
        
        for i, step in enumerate(result['results'], 1):
            role_name = ROLES[RoleType(step['role'])].name
            report += f"""### 步骤 {i}: {role_name}

**任务**: {step['task']}
**状态**: {step['status']}

**输出**:
```
{step.get('result', step.get('error', 'N/A'))[:800]}...
```

---

"""
        
        report += f"""## 最终输出

{result.get('final_output', 'N/A')[:1000]}

---

*由 CodeDev Agent 生成*
*集成IER迭代经验精炼系统*
"""
        
        return report
    
    def get_ier_statistics(self) -> Optional[Dict]:
        """获取IER统计信息"""
        if not self.exp_manager:
            return None
        return self.exp_manager.get_statistics()
    
    def list_experiences(self, exp_type: Optional[str] = None) -> List[Dict]:
        """列出经验"""
        if not self.exp_manager:
            return []
        
        exps = []
        for exp in self.exp_manager.experiences.values():
            if exp_type and exp.exp_type.value != exp_type:
                continue
            exps.append({
                'id': exp.id,
                'name': exp.name,
                'type': exp.exp_type.value,
                'context': exp.context[:100],
                'success_rate': exp.success_rate(),
                'usage_count': exp.usage_count,
                'status': exp.status.value
            })
        
        return exps
    
    def run_experience_maintenance(self) -> Dict:
        """运行经验维护（淘汰过时经验）"""
        if not self.exp_manager:
            return {'error': 'IER系统不可用'}
        
        eliminated = self.exp_manager.evaluate_and_eliminate()
        stats = self.exp_manager.get_statistics()
        
        return {
            'eliminated_count': len(eliminated),
            'eliminated_ids': eliminated,
            'statistics': stats
        }
        
        return report

# 全局服务实例
_service: Optional[CodeDevService] = None

def get_service() -> CodeDevService:
    """获取服务实例"""
    global _service
    if _service is None:
        _service = CodeDevService()
    return _service

def submit_code_request(description: str, language: str = "python") -> str:
    """提交代码开发请求（便捷函数）"""
    return get_service().submit_request(description, language)

def get_code_result(request_id: str) -> Optional[Dict]:
    """获取代码开发结果"""
    return get_service().get_result(request_id)

if __name__ == "__main__":
    # 测试运行
    service = get_service()
    service.start()
    
    print("CodeDev Agent服务已启动")
    print(f"请求目录: {REQUESTS_DIR}")
    print(f"结果目录: {RESULTS_DIR}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()
        print("\n服务已停止")
