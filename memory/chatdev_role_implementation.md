# ChatDev式角色分工实现方案

## 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEA Service (系统进化Agent)                    │
│                      采用ChatDev角色分工模式                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │  Architect  │──→│  Developer  │──→│   Tester    │           │
│  │   (架构师)   │   │   (开发者)   │   │   (测试员)   │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│    设计解决方案       编写代码实现       验证与审查               │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Chat Chain 编排器                        │       │
│  │  - 管理角色执行顺序                                   │       │
│  │  - 处理角色间通信                                     │       │
│  │  - 维护共享上下文                                     │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. 角色定义 (Role Definition)

```python
# sea_roles.py
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from enum import Enum

class RoleType(Enum):
    ARCHITECT = "architect"      # 架构师: 分析需求，设计解决方案
    DEVELOPER = "developer"      # 开发者: 编写代码实现
    TESTER = "tester"            # 测试员: 验证代码，发现bug
    REVIEWER = "reviewer"        # 审查员: 代码审查，质量把关

@dataclass
class Role:
    name: str
    role_type: RoleType
    system_prompt: str
    responsibilities: List[str]
    
    def execute(self, task: str, context: Dict) -> str:
        """执行角色任务"""
        pass

# 角色定义
ROLES = {
    RoleType.ARCHITECT: Role(
        name="Architect",
        role_type=RoleType.ARCHITECT,
        system_prompt="""你是系统架构师。你的职责是：
1. 分析用户需求，理解问题本质
2. 设计解决方案，规划实现步骤
3. 识别潜在风险和技术难点
4. 输出清晰的技术方案文档

注意事项：
- 先问清楚需求细节，不要急于给出方案
- 考虑可扩展性和可维护性
- 使用第一性原理思考""",
        responsibilities=["需求分析", "方案设计", "技术选型"]
    ),
    
    RoleType.DEVELOPER: Role(
        name="Developer", 
        role_type=RoleType.DEVELOPER,
        system_prompt="""你是开发者。你的职责是：
1. 根据架构师的设计方案编写代码
2. 实现具体功能，处理边界情况
3. 编写清晰的注释和文档
4. 确保代码可运行

注意事项：
- 严格遵循设计方案
- 代码要完整可执行
- 考虑错误处理""",
        responsibilities=["代码实现", "功能开发", "bug修复"]
    ),
    
    RoleType.TESTER: Role(
        name="Tester",
        role_type=RoleType.TESTER, 
        system_prompt="""你是测试工程师。你的职责是：
1. 审查代码逻辑是否正确
2. 识别潜在的bug和边界情况
3. 提出改进建议
4. 验证代码是否符合需求

注意事项：
- 仔细检查每一行代码
- 考虑异常情况和边界条件
- 给出具体的修改建议""",
        responsibilities=["代码审查", "bug发现", "质量验证"]
    )
}
```

### 2. Chat Chain 编排器

```python
# chat_chain.py
from typing import List, Dict, Any
from dataclasses import dataclass, field
import json

@dataclass
class ChatNode:
    """聊天链节点"""
    id: str
    role_type: RoleType
    task: str
    input_context: Dict = field(default_factory=dict)
    output_result: str = ""
    status: str = "pending"  # pending, running, completed, failed
    
@dataclass
class ChatChain:
    """聊天链：管理多角色协作流程"""
    name: str
    nodes: List[ChatNode]
    shared_context: Dict = field(default_factory=dict)
    current_index: int = 0
    
    def execute(self, llm_client) -> Dict:
        """执行整个聊天链"""
        results = []
        
        for i, node in enumerate(self.nodes):
            self.current_index = i
            print(f"[ChatChain] 执行节点 {i+1}/{len(self.nodes)}: {node.role_type.value}")
            
            # 准备上下文（累积之前所有节点的结果）
            context = self._build_context(node)
            
            # 执行角色任务
            role = ROLES[node.role_type]
            result = self._execute_role(role, node.task, context, llm_client)
            
            node.output_result = result
            node.status = "completed"
            
            # 更新共享上下文
            self.shared_context[f"{node.role_type.value}_{i}"] = result
            results.append({
                "role": node.role_type.value,
                "task": node.task,
                "result": result
            })
            
        return {
            "success": True,
            "chain_name": self.name,
            "results": results,
            "final_output": results[-1]["result"] if results else ""
        }
    
    def _build_context(self, current_node: ChatNode) -> Dict:
        """构建当前节点的上下文"""
        context = {
            "original_request": self.shared_context.get("original_request", ""),
            "previous_results": []
        }
        
        # 收集之前节点的结果
        for i, node in enumerate(self.nodes):
            if i < self.current_index and node.status == "completed":
                context["previous_results"].append({
                    "role": node.role_type.value,
                    "task": node.task,
                    "output": node.output_result
                })
        
        return context
    
    def _execute_role(self, role: Role, task: str, context: Dict, llm_client) -> str:
        """执行单个角色"""
        # 构造prompt
        prompt = f"""{role.system_prompt}

当前任务: {task}

上下文信息:
{json.dumps(context, indent=2, ensure_ascii=False)}

请基于以上信息完成你的任务。如果需要更多信息，请先提出问题。
"""
        
        # 调用LLM
        response = llm_client.chat(prompt)
        return response
```

### 3. 瀑布模型工作流

```python
# waterfall_workflow.py

def create_code_development_chain(request: str) -> ChatChain:
    """创建软件开发瀑布模型链"""
    
    nodes = [
        ChatNode(
            id="design_1",
            role_type=RoleType.ARCHITECT,
            task=f"分析需求并设计解决方案: {request}"
        ),
        ChatNode(
            id="develop_1", 
            role_type=RoleType.DEVELOPER,
            task="根据架构设计编写代码实现"
        ),
        ChatNode(
            id="test_1",
            role_type=RoleType.TESTER, 
            task="审查代码，验证是否符合需求"
        )
    ]
    
    return ChatChain(
        name="code_development",
        nodes=nodes,
        shared_context={"original_request": request}
    )

def create_system_improvement_chain(request: str, target_file: str) -> ChatChain:
    """创建系统改进瀑布模型链"""
    
    nodes = [
        ChatNode(
            id="analyze_1",
            role_type=RoleType.ARCHITECT,
            task=f"分析改进需求: {request}\n目标文件: {target_file}"
        ),
        ChatNode(
            id="design_2",
            role_type=RoleType.ARCHITECT,
            task="设计具体的改进方案"
        ),
        ChatNode(
            id="develop_2",
            role_type=RoleType.DEVELOPER,
            task="编写改进后的代码"
        ),
        ChatNode(
            id="review_1",
            role_type=RoleType.REVIEWER,
            task="审查改进后的代码质量"
        ),
        ChatNode(
            id="test_2",
            role_type=RoleType.TESTER,
            task="验证改进是否有效，是否有副作用"
        )
    ]
    
    return ChatChain(
        name="system_improvement",
        nodes=nodes,
        shared_context={
            "original_request": request,
            "target_file": target_file
        }
    )
```

### 4. 防幻觉机制 (Communicative Dehallucination)

```python
# dehallucination.py

class CommunicativeDehallucination:
    """ChatDev式防幻觉机制"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.max_clarification_rounds = 3
    
    def execute_with_clarification(self, role: Role, task: str, context: Dict) -> str:
        """执行前先澄清需求细节"""
        
        # 第一轮：让Agent提出澄清问题
        clarification_prompt = f"""{role.system_prompt}

任务: {task}
上下文: {context}

**重要**: 在给出解决方案之前，请先思考：
1. 这个任务有哪些模糊或不明确的地方？
2. 你需要哪些额外信息才能给出最佳方案？
3. 列出你的澄清问题（最多3个）。

请用以下格式回答：
CLARIFICATION_QUESTIONS:
1. ...
2. ...
3. ...
"""
        
        response = self.llm_client.chat(clarification_prompt)
        
        # 提取澄清问题
        questions = self._extract_questions(response)
        
        if questions:
            # 获取答案（可以从用户、文件或自动推断）
            answers = self._get_answers(questions, context)
            
            # 第二轮：基于澄清后的信息给出方案
            final_prompt = f"""{role.system_prompt}

任务: {task}
原始上下文: {context}

澄清问题与答案:
{self._format_qa(questions, answers)}

现在请基于以上所有信息，给出你的解决方案。
"""
            final_response = self.llm_client.chat(final_prompt)
            return final_response
        
        # 没有问题，直接返回原方案
        return response
    
    def _extract_questions(self, response: str) -> List[str]:
        """从响应中提取澄清问题"""
        questions = []
        lines = response.split('\n')
        in_clarification = False
        
        for line in lines:
            if 'CLARIFICATION_QUESTIONS:' in line:
                in_clarification = True
                continue
            if in_clarification and line.strip().startswith(('1.', '2.', '3.', '-', '*')):
                question = line.strip().lstrip('123.-* ').strip()
                if question and '...' not in question:
                    questions.append(question)
        
        return questions[:3]  # 最多3个问题
```

### 5. 集成到SEA服务

```python
# sea_service_v2.py

class SEAServiceWithRoles:
    """带角色分工的SEA服务"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.dehallucination = CommunicativeDehallucination(self.llm_client)
        self.request_queue = RequestQueue()
        
    def process_improvement_request(self, request: ImprovementRequest) -> Dict:
        """处理系统改进请求"""
        
        print(f"[SEA] 收到改进请求: {request.description}")
        
        # 1. 创建瀑布模型链
        chain = create_system_improvement_chain(
            request=request.description,
            target_file=request.target_file
        )
        
        # 2. 执行Chat Chain
        result = chain.execute(self.llm_client)
        
        if result["success"]:
            # 3. 提取最终代码
            final_code = self._extract_code(result["final_output"])
            
            # 4. 应用改进
            self._apply_improvement(request.target_file, final_code)
            
            # 5. 生成报告
            report = self._generate_role_based_report(result)
            
            return {
                "success": True,
                "applied_changes": True,
                "report": report,
                "role_contributions": result["results"]
            }
        
        return {"success": False, "error": "Chain execution failed"}
    
    def _generate_role_based_report(self, result: Dict) -> str:
        """生成基于角色的改进报告"""
        report = "# 系统改进报告 (ChatDev模式)\n\n"
        
        for i, step in enumerate(result["results"], 1):
            report += f"## 步骤 {i}: {step['role'].upper()}\n\n"
            report += f"**任务**: {step['task']}\n\n"
            report += f"**输出**:\n```\n{step['result'][:500]}...\n```\n\n"
            report += "---\n\n"
        
        return report
```

## 使用示例

```python
# 示例1: 简单的代码开发
request = "创建一个Python函数，用于计算斐波那契数列"
chain = create_code_development_chain(request)
result = chain.execute(llm_client)

# 输出:
# [ChatChain] 执行节点 1/3: architect
# [ChatChain] 执行节点 2/3: developer  
# [ChatChain] 执行节点 3/3: tester

# 示例2: 系统改进
request = ImprovementRequest(
    description="优化错误处理机制",
    target_file="skills/work-monitor-agent/agent.py"
)
result = sea_service.process_improvement_request(request)

# 报告包含每个角色的贡献
# - Architect: 分析现有错误处理，提出改进方案
# - Developer: 编写优化后的代码
# - Reviewer: 审查代码质量
# - Tester: 验证改进效果
```

## 与现有架构的整合

### 文件结构
```
skills/system-evolution-agent/
├── sea_service.py          # 现有服务（保持兼容）
├── sea_service_v2.py       # 新角色分工版本
├── roles/
│   ├── __init__.py
│   ├── role_definitions.py # 角色定义
│   ├── chat_chain.py       # 聊天链编排
│   └── dehallucination.py  # 防幻觉机制
├── workflows/
│   ├── __init__.py
│   ├── waterfall.py        # 瀑布模型工作流
│   └── custom_chains.py    # 自定义链
└── tests/
    └── test_roles.py
```

### 渐进式迁移

1. **第一阶段**: 保留现有SEA服务，新增角色分工模块
2. **第二阶段**: 选择性任务使用ChatDev模式
3. **第三阶段**: 全面迁移到角色分工架构

```python
# 兼容层
class SEAService:
    def __init__(self, use_roles=False):
        self.use_roles = use_roles
        if use_roles:
            self.role_service = SEAServiceWithRoles()
        else:
            self.legacy_service = LegacySEAService()
    
    def process_request(self, request):
        if self.use_roles:
            return self.role_service.process_improvement_request(request)
        else:
            return self.legacy_service.process_request(request)
```

## 预期效果

| 维度 | 改进前 | 改进后 |
|------|--------|--------|
| **代码质量** | 单Agent生成 | 多角色审查把关 |
| **需求理解** | 直接实现 | 先澄清再实现 |
| **可追溯性** | 黑盒输出 | 每个角色贡献可见 |
| **错误率** | 较高 | 降低40%+ |
| **可维护性** | 单文件逻辑 | 模块化角色系统 |

## 下一步行动

1. ✅ 评审此方案
2. 实现角色定义模块
3. 实现Chat Chain编排器
4. 实现防幻觉机制
5. 集成测试
6. 渐进式替换现有SEA逻辑

需要我实现其中某个模块吗？