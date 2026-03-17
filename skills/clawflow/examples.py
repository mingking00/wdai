#!/usr/bin/env python3
"""
ClawFlow - 使用示例
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clawflow import WorkflowEngine, ExecutionContext
import json


def example_1_basic_workflow():
    """示例 1: 基础工作流"""
    
    print("=" * 60)
    print("示例 1: 基础数据处理工作流")
    print("=" * 60)
    
    workflow = {
        "name": "数据处理",
        "nodes": [
            {
                "id": "start",
                "type": "trigger",
                "params": {}
            },
            {
                "id": "process",
                "type": "function",
                "params": {
                    "code": """
# 处理数据
data = input if isinstance(input, dict) else {"text": str(input)}
data["processed"] = True
data["length"] = len(data.get("text", ""))
output = data
"""
                }
            },
            {
                "id": "output",
                "type": "output",
                "params": {"type": "print"}
            }
        ],
        "connections": [
            {"from": "start", "to": "process"},
            {"from": "process", "to": "output"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, input_data={"text": "Hello, ClawFlow!"})
    
    print(f"\n执行结果:")
    print(f"  成功: {result.success}")
    print(f"  数据: {json.dumps(result.data, ensure_ascii=False, indent=2)}")
    print(f"  耗时: {result.execution_time:.3f}s")


def example_2_http_workflow():
    """示例 2: HTTP 请求工作流"""
    
    print("\n" + "=" * 60)
    print("示例 2: HTTP 请求工作流")
    print("=" * 60)
    
    workflow = {
        "name": "获取数据",
        "nodes": [
            {
                "id": "trigger",
                "type": "trigger",
                "params": {}
            },
            {
                "id": "fetch",
                "type": "http",
                "params": {
                    "method": "GET",
                    "url": "https://api.github.com"
                }
            },
            {
                "id": "process",
                "type": "function",
                "params": {
                    "code": """
# 处理响应
if isinstance(input, dict) and "body" in input:
    output = {
        "status": input.get("status"),
        "message": "数据获取成功"
    }
else:
    output = {"error": "请求失败"}
"""
                }
            }
        ],
        "connections": [
            {"from": "trigger", "to": "fetch"},
            {"from": "fetch", "to": "process"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow)
    
    print(f"\n执行结果:")
    print(f"  成功: {result.success}")
    if result.success:
        print(f"  数据: {json.dumps(result.data, ensure_ascii=False, indent=2)}")
    else:
        print(f"  错误: {result.error}")


def example_3_conditional_workflow():
    """示例 3: 条件分支工作流"""
    
    print("\n" + "=" * 60)
    print("示例 3: 条件分支工作流")
    print("=" * 60)
    
    workflow = {
        "name": "条件判断",
        "nodes": [
            {
                "id": "start",
                "type": "trigger",
                "params": {}
            },
            {
                "id": "check",
                "type": "if",
                "params": {
                    "condition": "json.get('score', 0) >= 60"
                }
            },
            {
                "id": "pass",
                "type": "function",
                "params": {
                    "code": "output = {'result': '通过', 'message': '恭喜你！'}"
                }
            },
            {
                "id": "fail",
                "type": "function",
                "params": {
                    "code": "output = {'result': '未通过', 'message': '继续努力'}"
                }
            },
            {
                "id": "output",
                "type": "output",
                "params": {}
            }
        ],
        "connections": [
            {"from": "start", "to": "check"},
            {"from": "check", "to": "pass"},
            {"from": "check", "to": "fail"},
            {"from": "pass", "to": "output"},
            {"from": "fail", "to": "output"}
        ]
    }
    
    engine = WorkflowEngine()
    
    # 测试通过情况
    print("\n测试 1: 分数 85 (应该通过)")
    result = engine.execute(workflow, input_data={"score": 85})
    print(f"  结果: {result.data}")
    
    # 测试未通过情况
    print("\n测试 2: 分数 45 (应该未通过)")
    result = engine.execute(workflow, input_data={"score": 45})
    print(f"  结果: {result.data}")


def example_4_data_transformation():
    """示例 4: 数据转换"""
    
    print("\n" + "=" * 60)
    print("示例 4: 数据转换")
    print("=" * 60)
    
    workflow = {
        "name": "数据转换",
        "nodes": [
            {
                "id": "start",
                "type": "trigger",
                "params": {}
            },
            {
                "id": "transform",
                "type": "function",
                "params": {
                    "code": """
# 模拟数据转换
if isinstance(input, list):
    output = [
        {
            "id": item.get("id"),
            "full_name": f"{item.get('first_name', '')} {item.get('last_name', '')}".strip(),
            "email": item.get("email")
        }
        for item in input
    ]
else:
    output = input
"""
                }
            },
            {
                "id": "output",
                "type": "output",
                "params": {"type": "print"}
            }
        ],
        "connections": [
            {"from": "start", "to": "transform"},
            {"from": "transform", "to": "output"}
        ]
    }
    
    input_data = [
        {"id": 1, "first_name": "张", "last_name": "三", "email": "zhang@example.com"},
        {"id": 2, "first_name": "李", "last_name": "四", "email": "li@example.com"}
    ]
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, input_data=input_data)
    
    print(f"\n转换结果:")
    print(json.dumps(result.data, ensure_ascii=False, indent=2))


def example_5_expression_evaluation():
    """示例 5: 表达式评估"""
    
    print("\n" + "=" * 60)
    print("示例 5: 表达式评估")
    print("=" * 60)
    
    from clawflow.engine import ExecutionContext
    
    context = ExecutionContext({
        "name": "ClawFlow",
        "version": "1.0.0"
    })
    
    # 模拟节点输出
    context.set_node_output("node1", {"status": "success", "data": "hello"})
    context.set_variable("counter", 42)
    
    # 测试表达式
    expressions = [
        ("$input.name", "访问输入"),
        ("$input.version", "访问嵌套输入"),
        ("$node.node1.status", "访问节点输出"),
        ("$var.counter", "访问变量"),
        ("$json", "访问当前 JSON")
    ]
    
    print("\n表达式测试结果:")
    for expr, desc in expressions:
        result = context.evaluate_expression(expr)
        print(f"  {desc}")
        print(f"    {expr} = {result}")


def main():
    """运行所有示例"""
    
    print("\n" + "=" * 60)
    print("🚀 ClawFlow - 轻量级工作流引擎")
    print("=" * 60)
    print("基于 n8n 架构原理实现的 Python 工作流引擎\n")
    
    example_1_basic_workflow()
    # example_2_http_workflow()  # 需要网络
    example_3_conditional_workflow()
    example_4_data_transformation()
    example_5_expression_evaluation()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例执行完成！")
    print("=" * 60)
    print("""
核心特性:
  ✅ JSON 定义工作流
  ✅ 节点化架构
  ✅ 拓扑排序执行
  ✅ 表达式系统
  ✅ 数据流管理
  ✅ 执行历史记录

可用节点:
  - trigger: 触发器
  - function: 函数处理
  - http: HTTP 请求
  - if: 条件分支
  - merge: 数据合并
  - output: 输出
  - delay: 延迟

下一步:
  1. 创建自己的工作流 JSON
  2. 使用 WorkflowEngine 执行
  3. 扩展自定义节点
    """)


if __name__ == "__main__":
    main()
