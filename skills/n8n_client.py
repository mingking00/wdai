#!/usr/bin/env python3
"""
n8n Client - OpenClaw 集成客户端

封装 n8n API，提供工作流管理、执行、监控功能。

依赖:
    pip install requests

用法:
    from skills.n8n_client import N8NClient
    
    client = N8NClient(base_url="http://localhost:5678", api_key="your-key")
    
    # 创建工作流
    workflow = client.create_workflow("邮件自动回复", workflow_json)
    
    # 执行工作流
    result = client.execute_workflow(workflow_id, data={"email": "test@test.com"})
"""

from __future__ import annotations

import json
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Workflow:
    """工作流对象"""
    id: str
    name: str
    nodes: List[Dict[str, Any]]
    connections: Dict[str, Any]
    active: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "nodes": self.nodes,
            "connections": self.connections,
            "active": self.active,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at
        }


@dataclass
class ExecutionResult:
    """执行结果"""
    execution_id: str
    workflow_id: str
    status: str  # success, error, running
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        return self.status == "success"


class N8NClient:
    """n8n API 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:5678", api_key: Optional[str] = None):
        """
        初始化 n8n 客户端
        
        Args:
            base_url: n8n 实例地址，默认 http://localhost:5678
            api_key: API Key（如果 n8n 启用了认证）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # 如果提供了 API Key，添加到请求头
        if api_key:
            self.session.headers["X-N8N-API-KEY"] = api_key
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{self.base_url}/api/v1{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
        
        except requests.exceptions.RequestException as e:
            raise N8NAPIError(f"API 请求失败: {e}")
    
    # ==================== 工作流管理 ====================
    
    def list_workflows(self) -> List[Workflow]:
        """获取所有工作流"""
        data = self._request("GET", "/workflows")
        workflows = []
        
        for item in data.get("data", []):
            workflows.append(Workflow(
                id=item.get("id", ""),
                name=item.get("name", ""),
                nodes=item.get("nodes", []),
                connections=item.get("connections", {}),
                active=item.get("active", False),
                created_at=item.get("createdAt"),
                updated_at=item.get("updatedAt")
            ))
        
        return workflows
    
    def get_workflow(self, workflow_id: str) -> Workflow:
        """获取工作流详情"""
        data = self._request("GET", f"/workflows/{workflow_id}")
        
        return Workflow(
            id=data.get("id", ""),
            name=data.get("name", ""),
            nodes=data.get("nodes", []),
            connections=data.get("connections", {}),
            active=data.get("active", False),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt")
        )
    
    def create_workflow(self, name: str, nodes: List[Dict], 
                       connections: Optional[Dict] = None) -> Workflow:
        """
        创建工作流
        
        Args:
            name: 工作流名称
            nodes: 节点列表
            connections: 节点连接关系
        """
        payload = {
            "name": name,
            "nodes": nodes,
            "connections": connections or {},
            "settings": {
                "saveExecutionProgress": True,
                "saveManualExecutions": True,
                "timezone": "Asia/Shanghai"
            }
        }
        
        data = self._request("POST", "/workflows", json=payload)
        
        return Workflow(
            id=data.get("id", ""),
            name=data.get("name", ""),
            nodes=data.get("nodes", []),
            connections=data.get("connections", {}),
            active=False
        )
    
    def update_workflow(self, workflow_id: str, 
                       name: Optional[str] = None,
                       nodes: Optional[List[Dict]] = None,
                       connections: Optional[Dict] = None) -> Workflow:
        """更新工作流"""
        # 先获取现有工作流
        existing = self.get_workflow(workflow_id)
        
        payload = {
            "name": name or existing.name,
            "nodes": nodes or existing.nodes,
            "connections": connections or existing.connections
        }
        
        data = self._request("PATCH", f"/workflows/{workflow_id}", json=payload)
        
        return Workflow(
            id=data.get("id", ""),
            name=data.get("name", ""),
            nodes=data.get("nodes", []),
            connections=data.get("connections", {}),
            active=data.get("active", False)
        )
    
    def delete_workflow(self, workflow_id: str):
        """删除工作流"""
        self._request("DELETE", f"/workflows/{workflow_id}")
    
    def activate_workflow(self, workflow_id: str) -> Workflow:
        """激活工作流"""
        data = self._request("POST", f"/workflows/{workflow_id}/activate")
        return self.get_workflow(workflow_id)
    
    def deactivate_workflow(self, workflow_id: str) -> Workflow:
        """停用工作流"""
        data = self._request("POST", f"/workflows/{workflow_id}/deactivate")
        return self.get_workflow(workflow_id)
    
    # ==================== 执行管理 ====================
    
    def execute_workflow(self, workflow_id: str, 
                        data: Optional[Dict] = None,
                        wait_for_completion: bool = True) -> ExecutionResult:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流 ID
            data: 输入数据
            wait_for_completion: 是否等待执行完成
        """
        payload = {
            "data": data or {}
        }
        
        # 触发执行
        response = self._request("POST", "/executions", json={
            "workflowId": workflow_id,
            "data": payload
        })
        
        execution_id = response.get("executionId", "")
        
        if wait_for_completion and execution_id:
            # 等待执行完成
            return self._wait_for_execution(execution_id)
        
        return ExecutionResult(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status="running"
        )
    
    def _wait_for_execution(self, execution_id: str, 
                           timeout: int = 60) -> ExecutionResult:
        """等待执行完成"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.get_execution(execution_id)
            
            if result.status in ["success", "error"]:
                return result
            
            time.sleep(1)
        
        # 超时
        return ExecutionResult(
            execution_id=execution_id,
            workflow_id="",
            status="timeout",
            error_message="执行超时"
        )
    
    def get_execution(self, execution_id: str) -> ExecutionResult:
        """获取执行详情"""
        data = self._request("GET", f"/executions/{execution_id}")
        
        return ExecutionResult(
            execution_id=data.get("id", ""),
            workflow_id=data.get("workflowId", ""),
            status=data.get("status", "unknown"),
            data=data.get("data", {}),
            started_at=data.get("startedAt"),
            finished_at=data.get("stoppedAt")
        )
    
    def list_executions(self, workflow_id: Optional[str] = None,
                       limit: int = 10) -> List[ExecutionResult]:
        """获取执行历史"""
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id
        
        data = self._request("GET", "/executions", params=params)
        
        results = []
        for item in data.get("data", []):
            results.append(ExecutionResult(
                execution_id=item.get("id", ""),
                workflow_id=item.get("workflowId", ""),
                status=item.get("status", "unknown"),
                started_at=item.get("startedAt"),
                finished_at=item.get("stoppedAt")
            ))
        
        return results
    
    # ==================== 工作流生成器 ====================
    
    def generate_email_auto_reply_workflow(self, email_config: Dict) -> Dict[str, Any]:
        """
        生成邮件自动回复工作流配置
        
        Args:
            email_config: 邮箱配置
                {
                    "imap_server": "imap.gmail.com",
                    "smtp_server": "smtp.gmail.com",
                    "username": "your@email.com",
                    "password": "your-password",
                    "ai_model": "gpt-4o"
                }
        """
        return {
            "nodes": [
                {
                    "id": "trigger",
                    "name": "Email Trigger",
                    "type": "n8n-nodes-base.emailReadImap",
                    "position": [250, 300],
                    "parameters": {
                        "options": {},
                        "mailbox": "INBOX",
                        "downloadAttachments": False,
                        "triggerOn": "onPoll"
                    },
                    "credentials": {
                        "imap": {
                            "id": "YOUR_CREDENTIAL_ID",
                            "name": "IMAP Account"
                        }
                    }
                },
                {
                    "id": "ai",
                    "name": "AI Reply",
                    "type": "@n8n/n8n-nodes-langchain.agent",
                    "position": [450, 300],
                    "parameters": {
                        "options": {
                            "systemMessage": "你是一个邮件助手，帮助用户生成礼貌的回复。"
                        }
                    }
                },
                {
                    "id": "send_email",
                    "name": "Send Email",
                    "type": "n8n-nodes-base.sendEmail",
                    "position": [650, 300],
                    "parameters": {
                        "to": "={{ $json.from }}",
                        "subject": "Re: {{ $json.subject }}",
                        "text": "={{ $json.output }}"
                    }
                }
            ],
            "connections": {
                "Email Trigger": {
                    "main": [[{"node": "AI Reply", "type": "main", "index": 0}]]
                },
                "AI Reply": {
                    "main": [[{"node": "Send Email", "type": "main", "index": 0}]]
                }
            }
        }
    
    def generate_webhook_processor_workflow(self, webhook_path: str,
                                           processor_type: str = "ai") -> Dict[str, Any]:
        """
        生成 Webhook 处理器工作流
        
        Args:
            webhook_path: Webhook 路径
            processor_type: 处理器类型 (ai, transform, notify)
        """
        nodes = [
            {
                "id": "webhook",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300],
                "parameters": {
                    "httpMethod": "POST",
                    "path": webhook_path,
                    "responseMode": "responseNode"
                },
                "webhookId": webhook_path
            }
        ]
        
        connections = {}
        
        if processor_type == "ai":
            nodes.extend([
                {
                    "id": "ai_process",
                    "name": "AI Process",
                    "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                    "position": [450, 300],
                    "parameters": {
                        "model": "gpt-4o-mini"
                    }
                },
                {
                    "id": "respond",
                    "name": "Respond to Webhook",
                    "type": "n8n-nodes-base.respondToWebhook",
                    "position": [650, 300],
                    "parameters": {
                        "options": {}
                    }
                }
            ])
            connections["Webhook"] = {
                "main": [[{"node": "AI Process", "type": "main", "index": 0}]]
            }
            connections["AI Process"] = {
                "main": [[{"node": "Respond to Webhook", "type": "main", "index": 0}]]
            }
        
        return {"nodes": nodes, "connections": connections}


class N8NAPIError(Exception):
    """n8n API 错误"""
    pass


# ==================== CLI 接口 ====================

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="n8n Client")
    parser.add_argument("--url", default="http://localhost:5678", help="n8n URL")
    parser.add_argument("--key", help="API Key")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # list 命令
    subparsers.add_parser("list", help="列出所有工作流")
    
    # create 命令
    create_parser = subparsers.add_parser("create", help="创建工作流")
    create_parser.add_argument("--name", required=True, help="工作流名称")
    create_parser.add_argument("--type", choices=["email", "webhook"], 
                              default="webhook", help="工作流类型")
    
    # execute 命令
    exec_parser = subparsers.add_parser("execute", help="执行工作流")
    exec_parser.add_argument("workflow_id", help="工作流 ID")
    exec_parser.add_argument("--data", help="输入数据 (JSON)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = N8NClient(base_url=args.url, api_key=args.key)
    
    try:
        if args.command == "list":
            workflows = client.list_workflows()
            print(f"共有 {len(workflows)} 个工作流:")
            for wf in workflows:
                status = "✅" if wf.active else "⏸️"
                print(f"  {status} {wf.name} ({wf.id})")
        
        elif args.command == "create":
            if args.type == "email":
                config = client.generate_email_auto_reply_workflow({})
            else:
                config = client.generate_webhook_processor_workflow("webhook-" + args.name[:8])
            
            workflow = client.create_workflow(
                name=args.name,
                nodes=config["nodes"],
                connections=config["connections"]
            )
            print(f"✅ 工作流创建成功: {workflow.id}")
            print(f"   名称: {workflow.name}")
            print(f"   节点数: {len(workflow.nodes)}")
        
        elif args.command == "execute":
            data = json.loads(args.data) if args.data else {}
            result = client.execute_workflow(args.workflow_id, data)
            print(f"执行状态: {result.status}")
            if result.is_success:
                print(f"结果: {json.dumps(result.data, indent=2)}")
            elif result.error_message:
                print(f"错误: {result.error_message}")
    
    except N8NAPIError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
