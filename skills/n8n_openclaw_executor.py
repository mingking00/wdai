#!/usr/bin/env python3
"""
OpenClaw + n8n 执行引擎集成

将 n8n 作为 OpenClaw 的执行引擎，实现自动化工作流。

启动 n8n:
    docker run -it --rm \
      --name n8n \
      -p 5678:5678 \
      -v ~/.n8n:/home/node/.n8n \
      n8nio/n8n

访问: http://localhost:5678
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from n8n_skill import N8NSkill, WorkflowTemplate
import json


def create_openclaw_executor_workflow():
    """
    创建一个特殊的 Workflow: OpenClaw 执行引擎
    
    这个工作流接收 OpenClaw 的任务请求，执行具体操作，返回结果。
    """
    
    print("🔧 创建 OpenClaw 执行引擎工作流")
    print("=" * 60)
    
    # 工作流定义
    workflow_json = {
        "name": "OpenClaw 执行引擎",
        "nodes": [
            # 1. Webhook 接收 OpenClaw 请求
            {
                "id": "webhook-receive",
                "name": "Receive Task",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300],
                "parameters": {
                    "httpMethod": "POST",
                    "path": "openclaw-execute",
                    "responseMode": "responseNode",
                    "options": {}
                },
                "webhookId": "openclaw-execute"
            },
            
            # 2. 解析任务类型
            {
                "id": "parse-task",
                "name": "Parse Task",
                "type": "n8n-nodes-base.function",
                "position": [450, 300],
                "parameters": {
                    "functionCode": """
// 解析 OpenClaw 发送的任务
const task = $input.first().json.body || $input.first().json;

// 提取任务信息
const taskType = task.type || 'unknown';
const taskData = task.data || {};
const taskId = task.taskId || Date.now().toString();

// 根据任务类型路由
let route = 'default';
if (taskType.includes('email')) route = 'email';
else if (taskType.includes('web')) route = 'web';
else if (taskType.includes('data')) route = 'data';
else if (taskType.includes('ai')) route = 'ai';

return [{
    json: {
        taskId,
        taskType,
        taskData,
        route,
        timestamp: new Date().toISOString()
    }
}];
"""
                }
            },
            
            # 3. 条件路由
            {
                "id": "route-task",
                "name": "Route Task",
                "type": "n8n-nodes-base.switch",
                "position": [650, 300],
                "parameters": {
                    "rules": {
                        "rules": [
                            {
                                "value": "email",
                                "output": 0
                            },
                            {
                                "value": "web",
                                "output": 1
                            },
                            {
                                "value": "data",
                                "output": 2
                            },
                            {
                                "value": "ai",
                                "output": 3
                            }
                        ]
                    },
                    "dataType": "string",
                    "value1": "={{ $json.route }}"
                }
            },
            
            # 4. 邮件处理分支
            {
                "id": "process-email",
                "name": "Process Email",
                "type": "n8n-nodes-base.function",
                "position": [850, 100],
                "parameters": {
                    "functionCode": """
const task = $input.first().json;
return [{
    json: {
        taskId: task.taskId,
        result: `邮件任务处理完成: ${JSON.stringify(task.taskData)}`,
        status: 'success'
    }
}];
"""
                }
            },
            
            # 5. Web 处理分支
            {
                "id": "process-web",
                "name": "Process Web",
                "type": "n8n-nodes-base.httpRequest",
                "position": [850, 250],
                "parameters": {
                    "method": "GET",
                    "url": "={{ $json.taskData.url || 'https://api.github.com' }}",
                    "options": {}
                }
            },
            
            # 6. 数据处理分支
            {
                "id": "process-data",
                "name": "Process Data",
                "type": "n8n-nodes-base.function",
                "position": [850, 400],
                "parameters": {
                    "functionCode": """
const task = $input.first().json;
const data = task.taskData;

// 模拟数据处理
const processed = {
    ...data,
    processed: true,
    processedAt: new Date().toISOString()
};

return [{
    json: {
        taskId: task.taskId,
        result: processed,
        status: 'success'
    }
}];
"""
                }
            },
            
            # 7. AI 处理分支
            {
                "id": "process-ai",
                "name": "AI Process",
                "type": "@n8n/n8n-nodes-langchain.agent",
                "position": [850, 550],
                "parameters": {
                    "options": {
                        "systemMessage": "你是一个智能助手，帮助用户处理各种任务。"
                    }
                },
                "credentials": {
                    "openAiApi": {
                        "id": "YOUR_OPENAI_CREDENTIAL",
                        "name": "OpenAI account"
                    }
                }
            },
            
            # 8. 合并结果
            {
                "id": "merge-results",
                "name": "Merge Results",
                "type": "n8n-nodes-base.merge",
                "position": [1050, 300],
                "parameters": {
                    "mode": "mergeByIndex"
                }
            },
            
            # 9. 构建响应
            {
                "id": "build-response",
                "name": "Build Response",
                "type": "n8n-nodes-base.function",
                "position": [1250, 300],
                "parameters": {
                    "functionCode": """
const input = $input.first().json;

// 构建标准响应格式
const response = {
    success: true,
    taskId: input.taskId || 'unknown',
    result: input.result || input,
    timestamp: new Date().toISOString()
};

return [{ json: response }];
"""
                }
            },
            
            # 10. 返回响应给 OpenClaw
            {
                "id": "respond-to-openclaw",
                "name": "Respond to OpenClaw",
                "type": "n8n-nodes-base.respondToWebhook",
                "position": [1450, 300],
                "parameters": {
                    "options": {}
                }
            }
        ],
        
        "connections": {
            "Receive Task": {
                "main": [[{"node": "Parse Task", "type": "main", "index": 0}]]
            },
            "Parse Task": {
                "main": [[{"node": "Route Task", "type": "main", "index": 0}]]
            },
            "Route Task": {
                "main": [
                    [{"node": "Process Email", "type": "main", "index": 0}],
                    [{"node": "Process Web", "type": "main", "index": 0}],
                    [{"node": "Process Data", "type": "main", "index": 0}],
                    [{"node": "AI Process", "type": "main", "index": 0}]
                ]
            },
            "Process Email": {
                "main": [[{"node": "Merge Results", "type": "main", "index": 0}]]
            },
            "Process Web": {
                "main": [[{"node": "Merge Results", "type": "main", "index": 0}]]
            },
            "Process Data": {
                "main": [[{"node": "Merge Results", "type": "main", "index": 0}]]
            },
            "AI Process": {
                "main": [[{"node": "Merge Results", "type": "main", "index": 0}]]
            },
            "Merge Results": {
                "main": [[{"node": "Build Response", "type": "main", "index": 0}]]
            },
            "Build Response": {
                "main": [[{"node": "Respond to OpenClaw", "type": "main", "index": 0}]]
            }
        }
    }
    
    return workflow_json


def create_simple_ai_workflow():
    """创建一个简单的 AI 处理工作流"""
    
    print("\n🤖 创建 AI 处理工作流")
    print("=" * 60)
    
    return {
        "name": "AI 文本处理",
        "nodes": [
            {
                "id": "webhook",
                "name": "Input",
                "type": "n8n-nodes-base.webhook",
                "position": [250, 300],
                "parameters": {
                    "httpMethod": "POST",
                    "path": "ai-process",
                    "responseMode": "responseNode"
                }
            },
            {
                "id": "ai",
                "name": "AI Processing",
                "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                "position": [450, 300],
                "parameters": {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个文本处理助手。"
                        },
                        {
                            "role": "user",
                            "content": "={{ $json.body.text || $json.text }}"
                        }
                    ]
                }
            },
            {
                "id": "respond",
                "name": "Output",
                "type": "n8n-nodes-base.respondToWebhook",
                "position": [650, 300],
                "parameters": {
                    "options": {
                        "statusCode": 200,
                        "body": "={{ JSON.stringify({ result: $json.content }) }}"
                    }
                }
            }
        ],
        "connections": {
            "Input": {
                "main": [[{"node": "AI Processing", "type": "main", "index": 0}]]
            },
            "AI Processing": {
                "main": [[{"node": "Output", "type": "main", "index": 0}]]
            }
        }
    }


def demonstrate_integration():
    """演示 OpenClaw + n8n 集成"""
    
    print("\n\n🚀 OpenClaw + n8n 集成演示")
    print("=" * 60)
    
    # 1. 生成工作流配置
    print("\n[Step 1] OpenClaw 生成工作流配置")
    print("-" * 60)
    
    workflow_config = create_openclaw_executor_workflow()
    
    print(f"工作流名称: {workflow_config['name']}")
    print(f"节点数量: {len(workflow_config['nodes'])}")
    print(f"\n节点列表:")
    for node in workflow_config['nodes']:
        print(f"  - {node['name']} ({node['type']})")
    
    # 2. 保存配置
    output_file = Path("/tmp/openclaw_executor_workflow.json")
    output_file.write_text(json.dumps(workflow_config, indent=2, ensure_ascii=False))
    print(f"\n✅ 工作流配置已保存: {output_file}")
    
    # 3. 显示如何部署
    print("\n[Step 2] 部署到 n8n")
    print("-" * 60)
    print("""
方式 A: 通过 n8n UI 导入
  1. 访问 http://localhost:5678
  2. 点击左侧菜单 "Workflows"
  3. 点击 "Import from File"
  4. 选择 /tmp/openclaw_executor_workflow.json

方式 B: 通过 API 创建
  curl -X POST http://localhost:5678/api/v1/workflows \\
    -H "Content-Type: application/json" \\
    -d @/tmp/openclaw_executor_workflow.json

方式 C: 使用 Python Client
  from skills.n8n_skill import N8NSkill
  
  skill = N8NSkill()
  workflow = skill.create_workflow(
      name="OpenClaw 执行引擎",
      nodes=workflow_config['nodes'],
      connections=workflow_config['connections']
  )
  print(f"工作流 ID: {workflow.id}")
    """)
    
    # 4. 显示如何调用
    print("\n[Step 3] OpenClaw 调用 n8n 执行引擎")
    print("-" * 60)
    print("""
任务请求示例:

POST http://localhost:5678/webhook/openclaw-execute
Content-Type: application/json

{
  "taskId": "task-001",
  "type": "ai",
  "data": {
    "prompt": "总结以下内容...",
    "text": "需要处理的文本..."
  }
}

Python 调用:
  import requests
  
  response = requests.post(
      "http://localhost:5678/webhook/openclaw-execute",
      json={
          "taskId": "task-001",
          "type": "ai",
          "data": {"text": "Hello World"}
      }
  )
  result = response.json()
  print(result)

预期响应:
  {
    "success": true,
    "taskId": "task-001",
    "result": "...",
    "timestamp": "2025-03-13T10:00:00Z"
  }
    """)
    
    # 5. 生成 AI 工作流
    print("\n[Step 4] 额外：AI 专用工作流")
    print("-" * 60)
    
    ai_workflow = create_simple_ai_workflow()
    ai_file = Path("/tmp/ai_workflow.json")
    ai_file.write_text(json.dumps(ai_workflow, indent=2, ensure_ascii=False))
    
    print(f"AI 工作流已保存: {ai_file}")
    print(f"Endpoint: POST http://localhost:5678/webhook/ai-process")
    print("""
调用示例:
  curl -X POST http://localhost:5678/webhook/ai-process \\
    -H "Content-Type: application/json" \\
    -d '{"text": "翻译成中文: Hello World"}'
    """)


def main():
    """主入口"""
    demonstrate_integration()
    
    print("\n\n" + "=" * 60)
    print("📋 文件生成清单")
    print("=" * 60)
    print("""
已生成以下工作流配置文件:

1. /tmp/openclaw_executor_workflow.json
   - 完整的 OpenClaw 执行引擎
   - 支持 email/web/data/ai 四种任务类型
   - Webhook: POST /webhook/openclaw-execute

2. /tmp/ai_workflow.json
   - 简单的 AI 文本处理工作流
   - Webhook: POST /webhook/ai-process

使用步骤:
  1. 启动 n8n: docker run -p 5678:5678 n8nio/n8n
  2. 导入工作流: n8n UI → Workflows → Import
  3. 配置凭证: Settings → Credentials (OpenAI 等)
  4. 激活工作流: 点击 "Active" 开关
  5. 测试调用: 使用上面的 curl 命令

OpenClaw 集成代码:
  见 skills/n8n_skill.py - run_task() 方法
    """)


if __name__ == "__main__":
    main()
