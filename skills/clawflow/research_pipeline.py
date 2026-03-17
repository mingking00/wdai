#!/usr/bin/env python3
"""
ClawFlow Research Pipeline - 自动化研究管道

集成 OpenClaw skills:
- kimi_search / web_search: 信息搜索
- browser: 深度网页抓取
- docx: 生成 Word 报告
- pdf: 生成 PDF 报告

工作流: 输入话题 → 多源搜索 → 内容抓取 → AI分析 → 生成报告
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clawflow import WorkflowEngine
import json
from datetime import datetime


def create_research_workflow(topic: str, output_format: str = "markdown") -> dict:
    """
    创建研究工作流
    
    Args:
        topic: 研究主题
        output_format: 输出格式 (markdown/docx/pdf)
    """
    return {
        "name": f"Research: {topic}",
        "nodes": [
            # 1. 输入主题
            {
                "id": "input",
                "type": "function",
                "params": {
                    "code": f"""
output = {{
    "topic": "{topic}",
    "timestamp": "{datetime.now().isoformat()}",
    "format": "{output_format}"
}}
"""
                }
            },
            
            # 2. 多源搜索 (并行)
            {
                "id": "search_kimi",
                "type": "skill",
                "params": {
                    "skill": "kimi_search",
                    "params": {"query": "$input.topic"}
                }
            },
            {
                "id": "search_web",
                "type": "skill",
                "params": {
                    "skill": "web_search", 
                    "params": {"query": "$input.topic", "count": 5}
                }
            },
            
            # 3. 合并搜索结果
            {
                "id": "merge_search",
                "type": "merge",
                "params": {"mode": "append"}
            },
            
            # 4. 深度抓取 (模拟)
            {
                "id": "fetch_content",
                "type": "function",
                "params": {
                    "code": """
# 模拟深度内容抓取
search_results = input if isinstance(input, list) else []
content_items = []

for result in search_results[:3]:  # 取前3个结果
    if isinstance(result, dict):
        content_items.append({
            "source": result.get('source', 'unknown'),
            "title": result.get('title', 'Untitled'),
            "url": result.get('url', ''),
            "snippet": result.get('snippet', '')[:200]
        })

output = {
    "topic": "Topic",
    "sources": content_items,
    "total_sources": len(content_items)
}
"""
                }
            },
            
            # 5. AI 分析
            {
                "id": "analyze",
                "type": "llm",
                "params": {
                    "model": "mock",
                    "prompt": """分析以下研究内容，提取关键洞察:
                    
主题: {{topic}}
来源数量: {{total_sources}}

请提供:
1. 核心观点摘要
2. 关键发现 (3-5点)
3. 信息来源可信度评估
4. 建议的下一步行动
""",
                    "system_prompt": "你是一个专业的研究分析师，擅长从多源信息中提取洞察。"
                }
            },
            
            # 6. 生成报告结构
            {
                "id": "structure_report",
                "type": "function",
                "params": {
                    "code": """
import json
from datetime import datetime

# 构建报告结构
report = {
    "title": f"研究报告: Topic",
    "generated_at": datetime.now().isoformat(),
    "sections": [
        {"heading": "执行摘要", "content": input.get('response', 'No analysis available')},
        {"heading": "研究方法", "content": "使用多源搜索和AI分析"},
        {"heading": "数据来源", "content": f"共收集 {{}} 个来源"},
        {"heading": "关键发现", "content": "详见AI分析部分"},
        {"heading": "建议行动", "content": "基于分析结果制定"}
    ],
    "metadata": {
        "version": "1.0",
        "engine": "ClawFlow Research Pipeline"
    }
}

output = report
"""
                }
            },
            
            # 7. 条件输出
            {
                "id": "check_format",
                "type": "if",
                "params": {
                    "condition": "True"  # 简化处理
                }
            },
            
            # 8. 生成文件
            {
                "id": "save_report",
                "type": "json",
                "params": {
                    "operation": "write",
                    "path": f"/tmp/research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            },
            
            # 9. 输出确认
            {
                "id": "notify",
                "type": "message",
                "params": {
                    "channel": "console",
                    "message": "研究报告已生成: {{path}}"
                }
            }
        ],
        "connections": [
            # 输入 → 并行搜索
            {"from": "input", "to": "search_kimi"},
            {"from": "input", "to": "search_web"},
            
            # 搜索结果合并
            {"from": "search_kimi", "to": "merge_search"},
            {"from": "search_web", "to": "merge_search"},
            
            # 后续处理链
            {"from": "merge_search", "to": "fetch_content"},
            {"from": "fetch_content", "to": "analyze"},
            {"from": "analyze", "to": "structure_report"},
            {"from": "structure_report", "to": "check_format"},
            {"from": "check_format", "to": "save_report"},
            {"from": "save_report", "to": "notify"}
        ]
    }


def run_research(topic: str, verbose: bool = True) -> dict:
    """执行研究流程"""
    print(f"\n{'='*60}")
    print(f"🔬 开始研究: {topic}")
    print(f"{'='*60}\n")
    
    workflow = create_research_workflow(topic)
    engine = WorkflowEngine()
    
    # 可视化
    if verbose:
        print("[工作流结构]")
        print(engine.visualize(workflow, format="ascii"))
        print()
    
    # 执行
    result = engine.execute(workflow, verbose=verbose)
    
    if result.success:
        print(f"\n{'='*60}")
        print("✅ 研究完成!")
        print(f"{'='*60}")
        print(f"\n执行统计:")
        print(f"  总耗时: {result.execution_time:.2f}s")
        print(f"  节点数: {len(result.node_results)}")
        if hasattr(result, 'branches_taken'):
            print(f"  分支: {result.branches_taken}")
        
        # 显示报告路径
        final_output = result.data
        if isinstance(final_output, dict) and 'path' in final_output:
            print(f"\n📄 报告保存至: {final_output['path']}")
            
            # 尝试读取并显示部分内容
            try:
                with open(final_output['path'], 'r') as f:
                    content = json.load(f)
                    print(f"\n报告预览:")
                    print(f"  标题: {content.get('title', 'N/A')}")
                    print(f"  章节: {len(content.get('sections', []))}")
                    print(f"  生成时间: {content.get('generated_at', 'N/A')}")
            except:
                pass
        
        return result
    else:
        print(f"\n❌ 研究失败: {result.error}")
        return result


def demo_batch_research():
    """批量研究演示"""
    topics = [
        "Python asyncio最佳实践",
        "LLM Agent框架对比",
        "2024 AI发展趋势"
    ]
    
    print("\n" + "="*60)
    print("🚀 批量研究演示")
    print("="*60)
    
    results = []
    for topic in topics:
        result = run_research(topic, verbose=False)
        results.append({
            "topic": topic,
            "success": result.success,
            "time": result.execution_time
        })
    
    print("\n" + "="*60)
    print("📊 批量研究总结")
    print("="*60)
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['topic']}: {r['time']:.2f}s")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ClawFlow 自动化研究管道')
    parser.add_argument('--topic', '-t', type=str, default='AI agent框架2024',
                       help='研究主题')
    parser.add_argument('--batch', '-b', action='store_true',
                       help='批量研究模式')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='静默模式')
    
    args = parser.parse_args()
    
    if args.batch:
        demo_batch_research()
    else:
        run_research(args.topic, verbose=not args.quiet)
    
    print("\n" + "="*60)
    print("💡 提示: 使用 --batch 批量研究，使用 --topic 指定主题")
    print("="*60)


if __name__ == "__main__":
    main()
