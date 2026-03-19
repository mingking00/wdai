"""
wdai v3.0 - Workflow Templates
SOP工作流引擎 - 常用工作流模板
"""

from typing import Dict, Any, List, Optional
from .. import Workflow, Step, StepAction, create_workflow, create_step


class SoftwareDevTemplate:
    """软件开发工作流模板"""
    
    @staticmethod
    def create(
        name: str = "软件开发",
        requirements: str = "",
        tech_stack: str = "python",
        custom_steps: Optional[List[Step]] = None
    ) -> Workflow:
        """
        创建软件开发工作流
        
        Args:
            name: 工作流名称
            requirements: 需求描述
            tech_stack: 技术栈
            custom_steps: 自定义步骤
        """
        steps = [
            Step(
                id="analyze",
                name="需求分析",
                action=StepAction.LLM,
                config={
                    "prompt": f"""分析以下需求并输出结构化的PRD:
                    
需求: {requirements}
技术栈: {tech_stack}

请输出:
1. 核心功能列表
2. 技术方案
3. 数据结构
4. API设计
"""
                }
            ),
            Step(
                id="design",
                name="架构设计",
                action=StepAction.LLM,
                dependencies=["analyze"],
                config={
                    "prompt": """基于需求分析，设计系统架构:

需求分析输出: {analyze_output}

请输出:
1. 模块划分
2. 类/接口设计
3. 依赖关系
4. 数据流图
"""
                }
            ),
            Step(
                id="implement",
                name="代码实现",
                action=StepAction.LLM,
                dependencies=["design"],
                config={
                    "prompt": """基于架构设计，生成代码:

架构设计: {design_output}

请输出:
1. 核心代码文件
2. 测试用例
3. 使用示例
"""
                }
            ),
            Step(
                id="review",
                name="代码审查",
                action=StepAction.LLM,
                dependencies=["implement"],
                config={
                    "prompt": """审查以下代码:

实现代码: {implement_output}

请输出:
1. 代码质量评估
2. 潜在问题
3. 改进建议
"""
                }
            )
        ]
        
        if custom_steps:
            steps.extend(custom_steps)
        
        return Workflow(
            name=name,
            description=f"软件开发工作流 - {tech_stack}",
            steps=steps,
            context={
                "requirements": requirements,
                "tech_stack": tech_stack
            },
            metadata={
                "template": "software_dev",
                "version": "1.0"
            }
        )


class DataProcessingTemplate:
    """数据处理工作流模板"""
    
    @staticmethod
    def create(
        name: str = "数据处理",
        data_source: str = "",
        operations: List[str] = None
    ) -> Workflow:
        """
        创建数据处理工作流
        
        Args:
            name: 工作流名称
            data_source: 数据源描述
            operations: 处理操作列表
        """
        operations = operations or ["validate", "transform", "analyze"]
        
        steps = []
        prev_step = None
        
        for i, op in enumerate(operations):
            step_id = f"step_{i}_{op}"
            deps = [prev_step] if prev_step else []
            
            steps.append(Step(
                id=step_id,
                name=f"数据{op}",
                action=StepAction.PYTHON,
                dependencies=deps,
                config={
                    "code": f"""# 数据{op}操作
# 数据源: {data_source}

print(f"执行 {op} 操作...")

# 获取上一步输出
if 'data' in context:
    data = context['data']
else:
    data = None
    
# 执行操作
result = f"{{op}} 完成"

# 设置结果
result = {{"status": "ok", "operation": "{op}"}}
"""
                }
            ))
            prev_step = step_id
        
        return Workflow(
            name=name,
            description="数据处理工作流",
            steps=steps,
            context={
                "data_source": data_source,
                "operations": operations
            },
            metadata={
                "template": "data_processing",
                "version": "1.0"
            }
        )


class TestAutomationTemplate:
    """测试自动化工作流模板"""
    
    @staticmethod
    def create(
        name: str = "测试自动化",
        test_path: str = "./tests",
        parallel: bool = True
    ) -> Workflow:
        """
        创建测试自动化工作流
        
        Args:
            name: 工作流名称
            test_path: 测试目录
            parallel: 是否并行执行
        """
        steps = [
            Step(
                id="lint",
                name="代码检查",
                action=StepAction.SHELL,
                config={
                    "command": f"cd {test_path} && python -m py_compile *.py"
                },
                allow_parallel=parallel
            ),
            Step(
                id="unit_test",
                name="单元测试",
                action=StepAction.SHELL,
                dependencies=["lint"],
                config={
                    "command": f"cd {test_path} && python -m pytest -xvs"
                },
                retry_policy=RetryPolicy(max_retries=1),
                allow_parallel=parallel
            ),
            Step(
                id="coverage",
                name="覆盖率检查",
                action=StepAction.SHELL,
                dependencies=["unit_test"],
                config={
                    "command": f"cd {test_path} && python -m pytest --cov=. --cov-report=html"
                },
                allow_parallel=False
            )
        ]
        
        return Workflow(
            name=name,
            description="自动化测试工作流",
            steps=steps,
            context={
                "test_path": test_path,
                "parallel": parallel
            },
            metadata={
                "template": "test_automation",
                "version": "1.0"
            }
        )


class DeployTemplate:
    """部署工作流模板"""
    
    @staticmethod
    def create(
        name: str = "部署",
        environment: str = "staging",
        artifacts: str = "./dist"
    ) -> Workflow:
        """
        创建部署工作流
        
        Args:
            name: 工作流名称
            environment: 部署环境
            artifacts: 构建产物目录
        """
        steps = [
            Step(
                id="build",
                name="构建",
                action=StepAction.SHELL,
                config={
                    "command": f"mkdir -p {artifacts} && echo 'Building...' && touch {artifacts}/app.tar.gz"
                }
            ),
            Step(
                id="test_deploy",
                name="测试部署",
                action=StepAction.SHELL,
                dependencies=["build"],
                config={
                    "command": f"echo 'Deploying to {environment}...'"
                }
            ),
            Step(
                id="verify",
                name="验证",
                action=StepAction.SHELL,
                dependencies=["test_deploy"],
                config={
                    "command": f"echo 'Verifying deployment on {environment}...' && echo 'Health check OK'"
                },
                retry_policy=RetryPolicy(max_retries=3, retry_delay=2.0)
            ),
            Step(
                id="notify",
                name="通知",
                action=StepAction.CUSTOM,
                dependencies=["verify"],
                config={
                    "message": f"部署到 {environment} 完成"
                }
            )
        ]
        
        return Workflow(
            name=name,
            description=f"{environment}环境部署工作流",
            steps=steps,
            context={
                "environment": environment,
                "artifacts": artifacts
            },
            metadata={
                "template": "deploy",
                "version": "1.0"
            }
        )


# 便捷函数
def get_template(name: str):
    """获取模板类"""
    templates = {
        "software_dev": SoftwareDevTemplate,
        "data_processing": DataProcessingTemplate,
        "test_automation": TestAutomationTemplate,
        "deploy": DeployTemplate
    }
    return templates.get(name)


def list_templates() -> List[str]:
    """列出所有可用模板"""
    return ["software_dev", "data_processing", "test_automation", "deploy"]
