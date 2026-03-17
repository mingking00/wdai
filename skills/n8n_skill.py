#!/usr/bin/env python3
"""
n8n Skill - OpenClaw 集成封装

将 n8n 作为 OpenClaw 的执行引擎，实现：
1. 自然语言生成工作流
2. 自动化任务执行
3. 跨系统集成

用法:
    from skills.n8n_skill import N8NSkill
    
    skill = N8NSkill()
    
    # 创建 AI Agent 工作流
    result = skill.create_ai_agent_workflow(
        name="邮件助手",
        description="自动处理邮件，生成智能回复",
        triggers=["email"],
        actions=["ai_process", "send_email"]
    )
"""

from __future__ import annotations

import json
import sys
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from n8n_client import N8NClient, Workflow, ExecutionResult


@dataclass
class WorkflowTemplate:
    """工作流模板"""
    name: str
    description: str
    category: str
    icon: str
    nodes: List[Dict[str, Any]]
    connections: Dict[str, Any]
    required_credentials: List[str] = field(default_factory=list)


class N8NSkill:
    """
    n8n Skill - 工作流自动化
    
    封装 n8n 能力，为 OpenClaw 提供：
    - 工作流生成（从自然语言描述）
    - 工作流管理（CRUD + 激活/停用）
    - 执行监控（触发 + 结果获取）
    - 模板库（预置常用工作流）
    """
    
    def __init__(self, base_url: str = "http://localhost:5678", 
                 api_key: Optional[str] = None):
        """
        初始化 n8n Skill
        
        Args:
            base_url: n8n 实例地址
            api_key: API Key（可选）
        """
        self.client = N8NClient(base_url=base_url, api_key=api_key)
        self._templates: Dict[str, WorkflowTemplate] = self._init_templates()
    
    def _init_templates(self) -> Dict[str, WorkflowTemplate]:
        """初始化预置模板"""
        return {
            "email_auto_reply": WorkflowTemplate(
                name="邮件自动回复",
                description="收到邮件后，使用 AI 生成回复并发送",
                category="communication",
                icon="📧",
                nodes=[
                    {
                        "id": "email_trigger",
                        "name": "Email Trigger",
                        "type": "n8n-nodes-base.emailReadImap",
                        "parameters": {
                            "mailbox": "INBOX",
                            "triggerOn": "onPoll"
                        }
                    },
                    {
                        "id": "ai_reply",
                        "name": "AI Reply",
                        "type": "@n8n/n8n-nodes-langchain.agent",
                        "parameters": {
                            "options": {
                                "systemMessage": "你是一个专业的邮件助手，生成礼貌、简洁的回复。"
                            }
                        }
                    },
                    {
                        "id": "send_reply",
                        "name": "Send Reply",
                        "type": "n8n-nodes-base.sendEmail",
                        "parameters": {}
                    }
                ],
                connections={
                    "Email Trigger": {
                        "main": [[{"node": "AI Reply", "type": "main", "index": 0}]]
                    },
                    "AI Reply": {
                        "main": [[{"node": "Send Reply", "type": "main", "index": 0}]]
                    }
                },
                required_credentials=["imap", "smtp", "openai"]
            ),
            
            "webhook_ai_processor": WorkflowTemplate(
                name="Webhook AI 处理器",
                description="接收 Webhook，使用 AI 处理后返回结果",
                category="api",
                icon="🪝",
                nodes=[
                    {
                        "id": "webhook",
                        "name": "Webhook",
                        "type": "n8n-nodes-base.webhook",
                        "parameters": {
                            "httpMethod": "POST",
                            "responseMode": "responseNode"
                        }
                    },
                    {
                        "id": "ai",
                        "name": "AI Process",
                        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                        "parameters": {
                            "model": "gpt-4o-mini"
                        }
                    },
                    {
                        "id": "respond",
                        "name": "Respond",
                        "type": "n8n-nodes-base.respondToWebhook",
                        "parameters": {}
                    }
                ],
                connections={
                    "Webhook": {
                        "main": [[{"node": "AI Process", "type": "main", "index": 0}]]
                    },
                    "AI Process": {
                        "main": [[{"node": "Respond", "type": "main", "index": 0}]]
                    }
                },
                required_credentials=["openai"]
            ),
            
            "scheduled_report": WorkflowTemplate(
                name="定时报告生成",
                description="定时从数据库获取数据，生成报告并发送",
                category="data",
                icon="📊",
                nodes=[
                    {
                        "id": "schedule",
                        "name": "Schedule",
                        "type": "n8n-nodes-base.scheduleTrigger",
                        "parameters": {
                            "rule": {"interval": [{"field": "hours", "hoursInterval": 24}]}
                        }
                    },
                    {
                        "id": "postgres",
                        "name": "Query DB",
                        "type": "n8n-nodes-base.postgres",
                        "parameters": {}
                    },
                    {
                        "id": "summarize",
                        "name": "AI Summarize",
                        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                        "parameters": {}
                    },
                    {
                        "id": "send",
                        "name": "Send Email",
                        "type": "n8n-nodes-base.sendEmail",
                        "parameters": {}
                    }
                ],
                connections={
                    "Schedule": {
                        "main": [[{"node": "Query DB", "type": "main", "index": 0}]]
                    },
                    "Query DB": {
                        "main": [[{"node": "AI Summarize", "type": "main", "index": 0}]]
                    },
                    "AI Summarize": {
                        "main": [[{"node": "Send Email", "type": "main", "index": 0}]]
                    }
                },
                required_credentials=["postgres", "smtp", "openai"]
            ),
            
            "slack_bot": WorkflowTemplate(
                name="Slack AI 机器人",
                description="监听 Slack 消息，使用 AI 回复",
                category="communication",
                icon="💬",
                nodes=[
                    {
                        "id": "slack_trigger",
                        "name": "Slack Trigger",
                        "type": "n8n-nodes-base.slackTrigger",
                        "parameters": {
                            "events": ["message"]
                        }
                    },
                    {
                        "id": "ai",
                        "name": "AI Reply",
                        "type": "@n8n/n8n-nodes-langchain.agent",
                        "parameters": {
                            "options": {
                                "systemMessage": "你是一个有帮助的 Slack 助手。"
                            }
                        }
                    },
                    {
                        "id": "slack_post",
                        "name": "Post to Slack",
                        "type": "n8n-nodes-base.slack",
                        "parameters": {
                            "operation": "post"
                        }
                    }
                ],
                connections={
                    "Slack Trigger": {
                        "main": [[{"node": "AI Reply", "type": "main", "index": 0}]]
                    },
                    "AI Reply": {
                        "main": [[{"node": "Post to Slack", "type": "main", "index": 0}]]
                    }
                },
                required_credentials=["slack", "openai"]
            ),
            
            "data_sync": WorkflowTemplate(
                name="数据同步",
                description="从一个数据源同步到另一个（如 Sheets → Database）",
                category="data",
                icon="🔄",
                nodes=[
                    {
                        "id": "schedule",
                        "name": "Schedule",
                        "type": "n8n-nodes-base.scheduleTrigger",
                        "parameters": {}
                    },
                    {
                        "id": "source",
                        "name": "Get Data",
                        "type": "n8n-nodes-base.googleSheets",
                        "parameters": {"operation": "read"}
                    },
                    {
                        "id": "transform",
                        "name": "Transform",
                        "type": "n8n-nodes-base.set",
                        "parameters": {}
                    },
                    {
                        "id": "target",
                        "name": "Save Data",
                        "type": "n8n-nodes-base.postgres",
                        "parameters": {"operation": "insert"}
                    }
                ],
                connections={
                    "Schedule": {
                        "main": [[{"node": "Get Data", "type": "main", "index": 0}]]
                    },
                    "Get Data": {
                        "main": [[{"node": "Transform", "type": "main", "index": 0}]]
                    },
                    "Transform": {
                        "main": [[{"node": "Save Data", "type": "main", "index": 0}]]
                    }
                },
                required_credentials=["googleSheets", "postgres"]
            )
        }
    
    # ==================== 模板管理 ====================
    
    def list_templates(self, category: Optional[str] = None) -> List[WorkflowTemplate]:
        """列出所有工作流模板"""
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """获取模板详情"""
        return self._templates.get(template_id)
    
    def create_from_template(self, template_id: str, 
                            name: Optional[str] = None,
                            custom_params: Optional[Dict] = None) -> Workflow:
        """
        从模板创建工作流
        
        Args:
            template_id: 模板 ID
            name: 自定义名称（可选）
            custom_params: 自定义参数（可选）
        """
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        workflow_name = name or template.name
        
        # 深拷贝节点和连接
        import copy
        nodes = copy.deepcopy(template.nodes)
        connections = copy.deepcopy(template.connections)
        
        # 应用自定义参数
        if custom_params:
            for node in nodes:
                if node["id"] in custom_params:
                    node["parameters"].update(custom_params[node["id"]])
        
        # 创建工作流
        return self.client.create_workflow(
            name=workflow_name,
            nodes=nodes,
            connections=connections
        )
    
    # ==================== 自然语言生成 ====================
    
    def generate_workflow_from_description(self, description: str,
                                          name: Optional[str] = None) -> Dict[str, Any]:
        """
        从自然语言描述生成工作流配置
        
        Args:
            description: 工作流描述
            name: 工作流名称
            
        Returns:
            工作流配置（可用于 create_workflow）
        """
        # 分析描述，匹配最佳模板
        description_lower = description.lower()
        
        # 关键词匹配
        if any(kw in description_lower for kw in ["邮件", "email", "回复", "reply"]):
            template_id = "email_auto_reply"
        elif any(kw in description_lower for kw in ["webhook", "api", "接口"]):
            template_id = "webhook_ai_processor"
        elif any(kw in description_lower for kw in ["定时", "报告", "report", "schedule"]):
            template_id = "scheduled_report"
        elif any(kw in description_lower for kw in ["slack", "机器人", "bot"]):
            template_id = "slack_bot"
        elif any(kw in description_lower for kw in ["同步", "sync", "数据"]):
            template_id = "data_sync"
        else:
            # 默认使用 Webhook AI 处理器
            template_id = "webhook_ai_processor"
        
        template = self._templates.get(template_id)
        
        return {
            "template_id": template_id,
            "template_name": template.name,
            "name": name or template.name,
            "nodes": template.nodes,
            "connections": template.connections,
            "required_credentials": template.required_credentials
        }
    
    # ==================== 工作流管理 ====================
    
    def create_workflow(self, name: str, nodes: List[Dict],
                       connections: Dict) -> Workflow:
        """创建工作流"""
        return self.client.create_workflow(name, nodes, connections)
    
    def list_workflows(self) -> List[Workflow]:
        """列出所有工作流"""
        return self.client.list_workflows()
    
    def get_workflow(self, workflow_id: str) -> Workflow:
        """获取工作流详情"""
        return self.client.get_workflow(workflow_id)
    
    def delete_workflow(self, workflow_id: str):
        """删除工作流"""
        self.client.delete_workflow(workflow_id)
    
    def activate_workflow(self, workflow_id: str) -> Workflow:
        """激活工作流"""
        return self.client.activate_workflow(workflow_id)
    
    def deactivate_workflow(self, workflow_id: str) -> Workflow:
        """停用工作流"""
        return self.client.deactivate_workflow(workflow_id)
    
    # ==================== 执行管理 ====================
    
    def execute_workflow(self, workflow_id: str,
                        data: Optional[Dict] = None) -> ExecutionResult:
        """执行工作流"""
        return self.client.execute_workflow(workflow_id, data)
    
    def get_execution(self, execution_id: str) -> ExecutionResult:
        """获取执行详情"""
        return self.client.get_execution(execution_id)
    
    # ==================== 智能执行（OpenClaw 集成）====================
    
    def run_task(self, task_description: str, 
                input_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        智能执行任务（OpenClaw 集成入口）
        
        Args:
            task_description: 任务描述（自然语言）
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        # 1. 解析任务，生成工作流
        config = self.generate_workflow_from_description(task_description)
        
        # 2. 创建工作流
        workflow = self.create_workflow(
            name=config["name"],
            nodes=config["nodes"],
            connections=config["connections"]
        )
        
        # 3. 执行工作流
        result = self.execute_workflow(workflow.id, input_data)
        
        # 4. 清理（临时工作流）
        # self.delete_workflow(workflow.id)  # 可选：保留或删除
        
        return {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "execution_id": result.execution_id,
            "status": result.status,
            "data": result.data
        }


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    skill = N8NSkill()
    
    # 示例 1: 从模板创建工作流
    print("=" * 50)
    print("示例 1: 从模板创建工作流")
    print("=" * 50)
    
    # 列出可用模板
    templates = skill.list_templates()
    print(f"\n可用模板 ({len(templates)} 个):")
    for t in templates:
        print(f"  {t.icon} {t.name} ({t.category})")
        print(f"     {t.description}")
    
    # 示例 2: 自然语言生成
    print("\n" + "=" * 50)
    print("示例 2: 自然语言生成工作流")
    print("=" * 50)
    
    description = "帮我创建一个邮件自动回复的工作流，收到邮件后用 AI 生成回复"
    config = skill.generate_workflow_from_description(description, "我的邮件助手")
    
    print(f"\n描述: {description}")
    print(f"匹配模板: {config['template_name']}")
    print(f"工作流名称: {config['name']}")
    print(f"所需凭证: {', '.join(config['required_credentials'])}")
    print(f"节点数: {len(config['nodes'])}")
    
    # 示例 3: 执行工作流（需要实际 n8n 实例）
    # result = skill.run_task("处理邮件", {"email": "test@test.com"})
    # print(result)


if __name__ == "__main__":
    example_usage()
