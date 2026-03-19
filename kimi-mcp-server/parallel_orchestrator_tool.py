#!/usr/bin/env python3
"""
Parallel Orchestrator as MCP Tool
将并行编排器封装为MCP Tool

让其他智能体可以通过MCP协议调用并行编排能力
"""

import sys
import json
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

sys.path.insert(0, '/root/.openclaw/workspace/kimi-mcp-server/src')

from extended_tools import KimiMCPExtendedServer
from demo_robust_parallel import RobustOrchestrator, TaskConfig, TaskResult, TaskStatus


class ParallelOrchestratorTool:
    """
    并行编排器MCP Tool
    
    提供标准MCP接口，让其他智能体可以：
    1. 定义并行工作流
    2. 执行并行任务
    3. 获取执行状态
    4. 查询执行结果
    """
    
    def __init__(self):
        self.orchestrators: Dict[str, RobustOrchestrator] = {}
        self.server = KimiMCPExtendedServer()
    
    def get_tool_schema(self) -> Dict:
        """MCP Tool Schema"""
        return {
            "name": "parallel_orchestrate",
            "description": "并行编排多个智能体任务，支持DAG依赖、超时控制、自动重试",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "工作流唯一标识"
                    },
                    "tasks": {
                        "type": "array",
                        "description": "任务列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "string"},
                                "agent_type": {"type": "string"},
                                "depends_on": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "duration": {"type": "number", "default": 1.0},
                                "timeout": {"type": "number", "default": 5.0},
                                "max_retries": {"type": "integer", "default": 2}
                            },
                            "required": ["task_id", "agent_type"]
                        }
                    },
                    "action": {
                        "type": "string",
                        "enum": ["execute", "status", "result"],
                        "description": "操作类型"
                    }
                },
                "required": ["workflow_id", "action"]
            }
        }
    
    async def execute(self, params: Dict) -> Dict:
        """执行Tool"""
        action = params.get("action", "execute")
        workflow_id = params.get("workflow_id")
        
        if action == "execute":
            return await self._execute_workflow(workflow_id, params)
        elif action == "status":
            return self._get_status(workflow_id)
        elif action == "result":
            return self._get_result(workflow_id)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _execute_workflow(self, workflow_id: str, params: Dict) -> Dict:
        """执行工作流"""
        tasks_config = params.get("tasks", [])
        
        if not tasks_config:
            return {"success": False, "error": "No tasks provided"}
        
        # 创建编排器
        orchestrator = RobustOrchestrator(workflow_id)
        
        # 添加任务
        for task_conf in tasks_config:
            config = TaskConfig(
                task_id=task_conf["task_id"],
                agent_type=task_conf["agent_type"],
                depends_on=set(task_conf.get("depends_on", [])),
                duration=task_conf.get("duration", 1.0),
                timeout=task_conf.get("timeout", 5.0),
                max_retries=task_conf.get("max_retries", 2)
            )
            orchestrator.add_task(config)
        
        # 保存引用
        self.orchestrators[workflow_id] = orchestrator
        
        # 执行
        try:
            results = await orchestrator.run()
            
            # 格式化结果
            formatted_results = {}
            for tid, result in results.items():
                formatted_results[tid] = {
                    "status": result.status.value,
                    "duration": result.duration,
                    "attempts": result.attempts,
                    "output": result.output,
                    "error": result.error
                }
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "results": formatted_results,
                "summary": {
                    "total": len(results),
                    "success": sum(1 for r in results.values() if r.status == TaskStatus.SUCCESS),
                    "failed": sum(1 for r in results.values() if r.status == TaskStatus.FAILED)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workflow_id": workflow_id
            }
    
    def _get_status(self, workflow_id: str) -> Dict:
        """获取工作流状态"""
        if workflow_id not in self.orchestrators:
            return {"success": False, "error": f"Workflow {workflow_id} not found"}
        
        orchestrator = self.orchestrators[workflow_id]
        summary = orchestrator.get_status_summary()
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "status": summary
        }
    
    def _get_result(self, workflow_id: str) -> Dict:
        """获取工作流结果"""
        if workflow_id not in self.orchestrators:
            return {"success": False, "error": f"Workflow {workflow_id} not found"}
        
        orchestrator = self.orchestrators[workflow_id]
        
        results = {}
        for tid, result in orchestrator.results.items():
            results[tid] = {
                "status": result.status.value,
                "duration": result.duration,
                "output": result.output,
                "error": result.error
            }
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "results": results
        }


# 包装为MCP Tool函数
def parallel_orchestrate(
    workflow_id: str,
    action: str = "execute",
    tasks: List[Dict] = None,
    **kwargs
) -> Dict:
    """
    MCP Tool: 并行编排多个智能体任务
    
    Args:
        workflow_id: 工作流ID
        action: execute/status/result
        tasks: 任务配置列表（execute时需要）
        
    Returns:
        执行结果或状态
    """
    tool = ParallelOrchestratorTool()
    
    params = {
        "workflow_id": workflow_id,
        "action": action,
        "tasks": tasks or []
    }
    
    # 检测是否已有event loop
    try:
        loop = asyncio.get_running_loop()
        # 如果在event loop中，使用ensure_future
        if loop.is_running():
            # 创建新线程来运行asyncio.run
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, tool.execute(params))
                return future.result()
    except RuntimeError:
        pass
    
    # 没有event loop，直接运行
    return asyncio.run(tool.execute(params))


async def demo_as_mcp_tool():
    """演示作为MCP Tool使用"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🔌 PARALLEL ORCHESTRATOR AS MCP TOOL                                  ║
║                                                                          ║
║   将并行编排能力封装为MCP Tool，供其他智能体调用                          ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n📋 场景：数据科学工作流")
    print("   一个数据科学项目需要多个并行步骤\n")
    
    # 直接调用Tool
    tool = ParallelOrchestratorTool()
    
    workflow = {
        "workflow_id": "data_science_pipeline_001",
        "action": "execute",
        "tasks": [
            {
                "task_id": "fetch_raw_data",
                "agent_type": "DataFetcher",
                "duration": 0.5,
                "timeout": 3.0,
                "max_retries": 2
            },
            {
                "task_id": "fetch_external_api",
                "agent_type": "APIFetcher",
                "duration": 0.8,
                "timeout": 4.0,
                "max_retries": 3
            },
            {
                "task_id": "clean_data",
                "agent_type": "DataCleaner",
                "depends_on": ["fetch_raw_data", "fetch_external_api"],
                "duration": 0.6,
                "timeout": 3.0
            },
            {
                "task_id": "feature_engineering",
                "agent_type": "FeatureEngineer",
                "depends_on": ["clean_data"],
                "duration": 0.7,
                "timeout": 3.0
            },
            {
                "task_id": "train_model",
                "agent_type": "MLTrainer",
                "depends_on": ["feature_engineering"],
                "duration": 1.0,
                "timeout": 5.0,
                "max_retries": 1
            },
            {
                "task_id": "evaluate_model",
                "agent_type": "MLEvaluator",
                "depends_on": ["train_model"],
                "duration": 0.4,
                "timeout": 2.0
            },
            {
                "task_id": "generate_report",
                "agent_type": "ReportGenerator",
                "depends_on": ["evaluate_model"],
                "duration": 0.3,
                "timeout": 2.0
            }
        ]
    }
    
    print("📤 调用 MCP Tool: parallel_orchestrate")
    print(f"   Workflow ID: {workflow['workflow_id']}")
    print(f"   Tasks: {len(workflow['tasks'])}")
    
    # 执行
    result = await tool.execute(workflow)
    
    print("\n📥 MCP Tool 返回结果:")
    print(json.dumps(result, indent=2, default=str))
    
    if result.get("success"):
        print("\n✅ MCP Tool 调用成功!")
        print(f"   成功任务: {result['summary']['success']}/{result['summary']['total']}")
    else:
        print(f"\n❌ 失败: {result.get('error')}")


async def demo_status_query():
    """演示状态查询"""
    print("\n" + "="*70)
    print("📊 状态查询演示")
    print("="*70)
    
    tool = ParallelOrchestratorTool()
    
    # 先执行一个工作流
    workflow_id = "test_workflow_002"
    
    print(f"\n1️⃣ 执行工作流: {workflow_id}")
    result = await tool.execute({
        "workflow_id": workflow_id,
        "action": "execute",
        "tasks": [
            {"task_id": "task_a", "agent_type": "TestAgent", "duration": 0.2},
            {"task_id": "task_b", "agent_type": "TestAgent", "duration": 0.3},
            {"task_id": "task_c", "agent_type": "TestAgent", "depends_on": ["task_a", "task_b"], "duration": 0.2}
        ]
    })
    
    # 查询状态
    print(f"\n2️⃣ 查询状态")
    status = await tool.execute({
        "workflow_id": workflow_id,
        "action": "status"
    })
    print(json.dumps(status, indent=2, default=str))
    
    # 查询结果
    print(f"\n3️⃣ 查询结果")
    result_data = await tool.execute({
        "workflow_id": workflow_id,
        "action": "result"
    })
    print(json.dumps(result_data, indent=2, default=str))


def integrate_with_mcp_server():
    """
    将Tool集成到MCP Server的示例代码
    """
    integration_code = '''
# 在 mcp_transport.py 或 extended_tools.py 中添加:

from parallel_orchestrator_tool import parallel_orchestrate

# 添加到KimiMCPExtendedServer的tools字典中
tools = {
    # ... 其他tools ...
    
    'parallel_orchestrate': {
        'name': 'parallel_orchestrate',
        'description': '并行编排多个智能体任务，支持DAG依赖、超时控制、自动重试',
        'parameters': {
            'workflow_id': {'type': 'string', 'description': '工作流ID'},
            'action': {'type': 'string', 'enum': ['execute', 'status', 'result']},
            'tasks': {
                'type': 'array',
                'items': {
                    'task_id': {'type': 'string'},
                    'agent_type': {'type': 'string'},
                    'depends_on': {'type': 'array', 'items': {'type': 'string'}},
                    'duration': {'type': 'number'},
                    'timeout': {'type': 'number'},
                    'max_retries': {'type': 'integer'}
                }
            }
        },
        'handler': parallel_orchestrate
    }
}

# 使用示例（通过MCP协议调用）:
# {
#   "jsonrpc": "2.0",
#   "method": "tools/call",
#   "params": {
#     "name": "parallel_orchestrate",
#     "arguments": {
#       "workflow_id": "my_workflow",
#       "action": "execute",
#       "tasks": [...]
#     }
#   }
# }
'''
    return integration_code


if __name__ == "__main__":
    # 演示1：作为MCP Tool使用
    asyncio.run(demo_as_mcp_tool())
    
    # 演示2：状态查询
    asyncio.run(demo_status_query())
    
    print("\n" + "="*70)
    print("🔌 MCP Tool 集成完成!")
    print("="*70)
    print("\n使用方式:")
    print("   1. 通过MCP协议调用: tools/call parallel_orchestrate")
    print("   2. Python直接调用: parallel_orchestrate(...)")
    print("   3. 查询状态: action='status'")
    print("   4. 获取结果: action='result'")
    
    print("\n下一步：分布式执行（多节点支持）")
