#!/usr/bin/env python3
"""
ClawFlow Research Pipeline - With REAL Search Data
使用真实的搜索结果生成报告
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clawflow import WorkflowEngine
from clawflow.nodes import SkillNode
from datetime import datetime
import json


def run_research(topic: str):
    """执行研究 - 使用真实搜索数据"""
    
    print(f"\n{'='*60}")
    print(f"🔬 ClawFlow Research Pipeline (Real Data)")
    print(f"{'='*60}")
    print(f"Topic: {topic}")
    
    # Step 1: 获取真实搜索结果
    print(f"\n[1/3] 搜索中...")
    node = SkillNode()
    search_result = node.execute(
        None, 
        {'skill': 'kimi_search', 'params': {'query': topic}}, 
        None
    )
    
    sources = search_result.get('results', [])
    print(f"✓ 找到 {len(sources)} 个真实来源")
    
    if not sources:
        print("❌ 没有找到结果")
        return False
    
    # 显示前几个结果
    print(f"\n前3个来源:")
    for i, s in enumerate(sources[:3], 1):
        print(f"  {i}. {s.get('title', 'N/A')[:60]}...")
    
    # Step 2: 使用 ClawFlow 处理
    print(f"\n[2/3] 使用 ClawFlow 分析...")
    
    # 准备输入数据
    input_data = {
        "topic": topic,
        "sources": sources,
        "total": len(sources)
    }
    
    # 简化版工作流 - 直接生成报告
    workflow = {
        "name": f"Research: {topic}",
        "nodes": [
            {
                "id": "process",
                "type": "function",
                "params": {
                    "code": f"""
# Process real search results
import json
from datetime import datetime

topic = "{topic}"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
base_path = f"/tmp/clawflow_research/research_real_{{timestamp}}"

# Get sources from input
sources = {json.dumps(sources)}

# Build report
report = {{
    "metadata": {{
        "title": f"Research: {topic}",
        "generated_at": datetime.now().isoformat(),
        "engine": "ClawFlow + Real Search",
        "sources_count": len(sources)
    }},
    "topic": topic,
    "sources": sources,
    "summary": [s.get('title', '') for s in sources[:5]]
}}

# Save JSON
json_path = base_path + ".json"
with open(json_path, 'w') as f:
    json.dump(report, f, indent=2)

# Build Markdown
md_content = f'''# {{report['metadata']['title']}}

**生成时间**: {{report['metadata']['generated_at']}}  
**来源数量**: {{report['metadata']['sources_count']}}  
**引擎**: {{report['metadata']['engine']}}

## 研究主题
{topic}

## 来源列表
'''

for i, s in enumerate(sources[:5], 1):
    md_content += f"{{i}}. **{{s.get('title', 'N/A')}}**\\n"
    md_content += f"   - 链接: {{s.get('url', '')}}\\n"
    md_content += f"   - 摘要: {{s.get('snippet', '')[:150]}}...\\n\\n"

md_content += '''
---
*由 ClawFlow Research Pipeline 生成*
'''

md_path = base_path + ".md"
with open(md_path, 'w', encoding='utf-8') as f:
    f.write(md_content)

output = {{
    "json_path": json_path,
    "markdown_path": md_path,
    "sources_count": len(sources)
}}
"""
                }
            },
            {
                "id": "done",
                "type": "output",
                "params": {}
            }
        ],
        "connections": [
            {"from": "process", "to": "done"}
        ]
    }
    
    engine = WorkflowEngine()
    result = engine.execute(workflow, verbose=False)
    
    if result.success:
        print(f"\n{'='*60}")
        print("✅ 研究完成!")
        print(f"{'='*60}")
        
        data = result.data
        print(f"\n📄 生成文件:")
        print(f"  JSON: {data.get('json_path')}")
        print(f"  Markdown: {data.get('markdown_path')}")
        print(f"  来源数: {data.get('sources_count')}")
        
        # 显示报告
        if 'markdown_path' in data:
            try:
                with open(data['markdown_path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"\n📝 报告内容:")
                    print("-" * 50)
                    print(content)
                    print("-" * 50)
            except Exception as e:
                print(f"读取错误: {e}")
        
        return True
    else:
        print(f"\n❌ 失败: {result.error}")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("topic", nargs="?", default="Python asyncio best practices")
    args = parser.parse_args()
    
    run_research(args.topic)
