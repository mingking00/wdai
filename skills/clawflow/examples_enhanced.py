#!/usr/bin/env python3
"""
ClawFlow - 增强版使用示例
展示新功能和节点
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clawflow import WorkflowEngine
import json
import tempfile


def example_file_operations():
    """示例: 文件操作"""
    print("=" * 60)
    print("示例: 文件读写操作")
    print("=" * 60)
    
    # 创建临时文件
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "test.txt"
    
    # 写入工作流
    workflow_write = {
        "name": "写入文件",
        "nodes": [
            {
                "id": "create",
                "type": "function",
                "params": {
                    "code": f"""
output = {{
    "content": "Hello from ClawFlow!\\n这是自动生成的文件。",
    "filepath": "{test_file}"
}}
"""
                }
            },
            {
                "id": "write",
                "type": "file",
                "params": {
                    "operation": "write",
                    "path": str(test_file),
                    "content": "Hello from ClawFlow!\n这是自动生成的文件。"
                }
            },
            {
                "id": "read",
                "type": "file",
                "params": {
                    "operation": "read",
                    "path": str(test_file)
                }
            }
        ],
        "connections": [
            {"from": "create", "to": "write"},
            {"from": "write", "to": "read"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow_write, verbose=True)
    
    if result.success:
        print(f"\n✅ 文件操作成功")
        print(f"内容: {result.data.get('content', 'N/A')[:50]}...")
    else:
        print(f"\n❌ 失败: {result.error}")
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)


def example_csv_processing():
    """示例: CSV 处理"""
    print("\n" + "=" * 60)
    print("示例: CSV 数据处理")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    csv_file = Path(temp_dir) / "data.csv"
    
    # 先创建 CSV 文件
    csv_content = "name,age,city\n张三,25,北京\n李四,30,上海\n王五,28,广州"
    csv_file.write_text(csv_content, encoding='utf-8')
    
    workflow = {
        "name": "CSV处理",
        "nodes": [
            {
                "id": "read_csv",
                "type": "csv",
                "params": {
                    "operation": "read",
                    "path": str(csv_file)
                }
            },
            {
                "id": "filter",
                "type": "transform",
                "params": {
                    "operation": "filter",
                    "field": "city",
                    "value": "北京"
                }
            }
        ],
        "connections": [
            {"from": "read_csv", "to": "filter"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, verbose=True)
    
    if result.success:
        print(f"\n✅ CSV 处理完成")
        print(f"筛选结果: {json.dumps(result.data, ensure_ascii=False, indent=2)}")
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)


def example_json_processing():
    """示例: JSON 处理"""
    print("\n" + "=" * 60)
    print("示例: JSON 查询")
    print("=" * 60)
    
    workflow = {
        "name": "JSON查询",
        "nodes": [
            {
                "id": "create_json",
                "type": "function",
                "params": {
                    "code": """
output = {
    "users": [
        {"name": "张三", "age": 25, "city": "北京"},
        {"name": "李四", "age": 30, "city": "上海"}
    ],
    "total": 2
}
"""
                }
            },
            {
                "id": "query",
                "type": "json",
                "params": {
                    "operation": "query",
                    "query_path": "users.0.name"
                }
            }
        ],
        "connections": [
            {"from": "create_json", "to": "query"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, verbose=True)
    
    if result.success:
        print(f"\n✅ JSON 查询结果: {result.data}")


def example_database():
    """示例: 数据库操作"""
    print("\n" + "=" * 60)
    print("示例: SQLite 数据库")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    db_file = Path(temp_dir) / "test.db"
    
    workflow = {
        "name": "数据库操作",
        "nodes": [
            {
                "id": "create_table",
                "type": "database",
                "params": {
                    "operation": "create_table",
                    "db_path": str(db_file),
                    "table": "users",
                    "schema": {
                        "id": "INTEGER PRIMARY KEY",
                        "name": "TEXT",
                        "age": "INTEGER"
                    }
                }
            },
            {
                "id": "insert1",
                "type": "database",
                "params": {
                    "operation": "insert",
                    "db_path": str(db_file),
                    "table": "users",
                    "data": {"name": "张三", "age": 25}
                }
            },
            {
                "id": "insert2",
                "type": "database",
                "params": {
                    "operation": "insert",
                    "db_path": str(db_file),
                    "table": "users",
                    "data": {"name": "李四", "age": 30}
                }
            },
            {
                "id": "query",
                "type": "database",
                "params": {
                    "operation": "query",
                    "db_path": str(db_file),
                    "sql": "SELECT * FROM users WHERE age > 25"
                }
            }
        ],
        "connections": [
            {"from": "create_table", "to": "insert1"},
            {"from": "insert1", "to": "insert2"},
            {"from": "insert2", "to": "query"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, verbose=True)
    
    if result.success:
        print(f"\n✅ 数据库查询结果:")
        print(json.dumps(result.data, ensure_ascii=False, indent=2))
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)


def example_workflow_validation():
    """示例: 工作流验证"""
    print("\n" + "=" * 60)
    print("示例: 工作流验证")
    print("=" * 60)
    
    engine = WorkflowEngine()
    
    # 有效的工作流
    valid_workflow = {
        "name": "有效工作流",
        "nodes": [
            {"id": "start", "type": "trigger", "params": {}},
            {"id": "end", "type": "output", "params": {}}
        ],
        "connections": [
            {"from": "start", "to": "end"}
        ]
    }
    
    validation = engine.validate(valid_workflow)
    print(f"\n有效工作流检查:")
    print(f"  通过: {validation.valid}")
    print(f"  错误: {validation.errors}")
    print(f"  警告: {validation.warnings}")
    
    # 无效的工作流
    invalid_workflow = {
        "name": "无效工作流",
        "nodes": [
            {"id": "start", "type": "trigger", "params": {}},
            {"id": "bad", "type": "unknown_type", "params": {}}
        ],
        "connections": [
            {"from": "start", "to": "nonexistent"}
        ]
    }
    
    validation = engine.validate(invalid_workflow)
    print(f"\n无效工作流检查:")
    print(f"  通过: {validation.valid}")
    print(f"  错误: {validation.errors}")


def example_llm():
    """示例: LLM 节点"""
    print("\n" + "=" * 60)
    print("示例: LLM 节点")
    print("=" * 60)
    
    workflow = {
        "name": "LLM处理",
        "nodes": [
            {
                "id": "input",
                "type": "function",
                "params": {
                    "code": 'output = {"text": "分析这段文本的情感倾向"}'
                }
            },
            {
                "id": "llm",
                "type": "llm",
                "params": {
                    "model": "mock",
                    "prompt": "{{input}}",
                    "system_prompt": "你是一个情感分析助手"
                }
            }
        ],
        "connections": [
            {"from": "input", "to": "llm"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, verbose=True)
    
    if result.success:
        print(f"\n✅ LLM 响应:")
        print(result.data.get('response', 'N/A'))


def example_complex_workflow():
    """示例: 复杂工作流 - 数据处理管道"""
    print("\n" + "=" * 60)
    print("示例: 复杂数据处理管道")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    csv_file = Path(temp_dir) / "input.csv"
    json_file = Path(temp_dir) / "output.json"
    
    # 创建输入 CSV
    csv_content = "name,age,score\n张三,25,85\n李四,30,92\n王五,28,78\n赵六,35,88"
    csv_file.write_text(csv_content, encoding='utf-8')
    
    workflow = {
        "name": "数据处理管道",
        "nodes": [
            {
                "id": "read",
                "type": "csv",
                "params": {
                    "operation": "read",
                    "path": str(csv_file)
                }
            },
            {
                "id": "filter",
                "type": "transform",
                "params": {
                    "operation": "filter",
                    "field": "score",
                    "value": "80"  # 这里需要转换类型
                }
            },
            {
                "id": "sort",
                "type": "transform",
                "params": {
                    "operation": "sort",
                    "field": "score",
                    "reverse": True
                }
            },
            {
                "id": "process",
                "type": "function",
                "params": {
                    "code": """
# 处理数据
if isinstance(input, list):
    output = {
        "students": [
            {"name": row.get("name"), "grade": "A" if int(row.get("score", 0)) >= 90 else "B"}
            for row in input
        ],
        "count": len(input)
    }
else:
    output = input
"""
                }
            },
            {
                "id": "save",
                "type": "json",
                "params": {
                    "operation": "write",
                    "path": str(json_file)
                }
            },
            {
                "id": "output",
                "type": "output",
                "params": {"type": "print"}
            }
        ],
        "connections": [
            {"from": "read", "to": "filter"},
            {"from": "filter", "to": "sort"},
            {"from": "sort", "to": "process"},
            {"from": "process", "to": "save"},
            {"from": "save", "to": "output"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, verbose=True)
    
    if result.success:
        print(f"\n✅ 复杂工作流执行完成")
        print(f"执行日志:")
        for log in result.execution_log:
            print(f"  {log['node_id']}: {log['status']} ({log['duration']:.3f}s)")
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("🚀 ClawFlow Enhanced - 增强版工作流引擎")
    print("=" * 60)
    print("新增节点:")
    print("  - file: 文件读写、复制、列表")
    print("  - csv: CSV 读写、解析")
    print("  - json: JSON 读写、查询")
    print("  - database: SQLite 操作")
    print("  - llm: 大模型调用")
    print("  - email: 邮件发送")
    print("  - cron: 定时任务配置")
    print()
    print("增强功能:")
    print("  ✅ 工作流验证")
    print("  ✅ 详细执行日志")
    print("  ✅ 错误重试机制")
    print("  ✅ 工作流持久化")
    print("=" * 60)
    
    # 运行示例
    example_file_operations()
    example_csv_processing()
    example_json_processing()
    example_database()
    example_workflow_validation()
    example_llm()
    example_complex_workflow()
    
    print("\n" + "=" * 60)
    print("✅ 所有示例执行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
