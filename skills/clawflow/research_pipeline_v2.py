#!/usr/bin/env python3
"""
ClawFlow Research Pipeline v2 - Complete Automated Research Pipeline

Features:
- Multi-source search (kimi_search + web_search)
- AI content analysis
- Generate structured reports (Markdown/JSON)
- Scheduled execution support
- Report history management
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clawflow import WorkflowEngine
from datetime import datetime
import json
import argparse


class ResearchPipeline:
    """Research Pipeline Class"""
    
    def __init__(self, output_dir: str = "/tmp/clawflow_research"):
        self.engine = WorkflowEngine()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_workflow(self, topic: str, depth: str = "standard") -> dict:
        """Create workflow definition"""
        
        # Adjust parameters based on depth
        search_count = 10 if depth == "deep" else 5
        fetch_limit = 5 if depth == "deep" else 3
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"research_{topic.replace(' ', '_')[:30]}_{timestamp}"
        
        return {
            "name": f"Research: {topic}",
            "nodes": [
                # Stage 1: Input and configuration
                {
                    "id": "setup",
                    "type": "function",
                    "params": {
                        "code": f"""
output = {{
    "topic": "{topic}",
    "depth": "{depth}",
    "timestamp": "{datetime.now().isoformat()}",
    "search_count": {search_count},
    "fetch_limit": {fetch_limit},
    "report_file": "{report_file}"
}}
"""
                    }
                },
                
                # Stage 2: Parallel search (multi-source)
                {
                    "id": "search_primary",
                    "type": "skill",
                    "params": {
                        "skill": "web_search",
                        "params": {
                            "query": "$input.topic",
                            "count": "$input.search_count"
                        }
                    }
                },
                {
                    "id": "search_secondary",
                    "type": "skill",
                    "params": {
                        "skill": "kimi_search",
                        "params": {
                            "query": "$input.topic"
                        }
                    }
                },
                
                # Stage 3: Merge and deduplicate
                {
                    "id": "aggregate",
                    "type": "function",
                    "params": {
                        "code": """
# Handle merged inputs from multiple sources
if isinstance(input, dict) and "__merged__" in input:
    items = input["__merged__"]
elif isinstance(input, list):
    items = input
else:
    items = [input] if input else []

# Merge search results
results = []
for item in items:
    if isinstance(item, dict) and 'results' in item:
        results.extend(item['results'])
    elif isinstance(item, dict):
        results.append(item)

# Deduplicate (based on URL)
seen = set()
unique = []
for r in results:
    url = r.get('url', '') if isinstance(r, dict) else ''
    if url and url not in seen:
        seen.add(url)
        unique.append(r)

output = {
    "raw_results": unique,
    "total_found": len(results),
    "unique_count": len(unique)
}
"""
                    }
                },
                
                # Stage 4: Content filtering
                {
                    "id": "filter",
                    "type": "function",
                    "params": {
                        "code": f"""
# Select most relevant results
data = input if isinstance(input, dict) else {{}}
raw = data.get('raw_results', [])

# Simple scoring: title and snippet contain keywords
topic = "{topic}".lower()
topic_words = topic.split()
scored = []

for item in raw:
    if isinstance(item, dict):
        score = 10  # base score
        title = str(item.get('title', '')).lower()
        snippet = str(item.get('snippet', '')).lower()
        text = title + ' ' + snippet
        
        # Keyword match bonus
        for word in topic_words:
            if word and word in text:
                score += 5
        
        item_copy = dict(item)
        item_copy["relevance_score"] = int(score)
        scored.append(item_copy)

# Sort by score (descending)
try:
    scored.sort(key=lambda x: int(x.get('relevance_score', 0) or 0), reverse=True)
except:
    pass

limit = min(len(scored), 3)
output = {{
    "selected_sources": scored[:limit],
    "selection_count": limit,
    "total_scored": len(scored)
}}
"""
                    }
                },
                
                # Stage 5: AI analysis
                {
                    "id": "ai_analysis",
                    "type": "llm",
                    "params": {
                        "model": "mock",
                        "prompt": """As a research analyst, please generate a structured research report based on the following content:

Research Topic: $input.topic
Data Sources: $input.selected_sources

Please generate the following sections:

## Executive Summary
Summarize core findings in 2-3 sentences

## Key Insights (3-5 points)
- Insight 1: [key point]
- Insight 2: [key point]
...

## Information Source Assessment
- Source Quality: [High/Medium/Low]
- Information Consistency: [Consistent/Disagreement]
- Timeliness: [Latest/General/Outdated]

## Recommended Actions
1. [specific recommendation]
2. [specific recommendation]

## Confidence Score (1-10)
[score and reasoning]""",
                        "system_prompt": "You are a professional research analyst, skilled at extracting structured insights from multi-source information."
                    }
                },
                
                # Stage 6: Build final report
                {
                    "id": "build_report",
                    "type": "function",
                    "params": {
                        "code": f"""
from datetime import datetime

# Build complete report
report = {{
    "metadata": {{
        "title": f"Research Report: {topic}",
        "generated_at": "{datetime.now().isoformat()}",
        "engine": "ClawFlow Research Pipeline v2",
        "version": "2.0",
        "depth": "{depth}"
    }},
    "topic": "{topic}",
    "analysis": input.get('response', 'No analysis available'),
    "sources": [],  # Simplified
    "statistics": {{
        "total_sources": 0,
        "analysis_timestamp": "{datetime.now().isoformat()}"
    }}
}}

output = report
"""
                    }
                },
                
                # Stage 7: Save report
                {
                    "id": "save_json",
                    "type": "json",
                    "params": {
                        "operation": "write",
                        "path": str(report_file) + ".json",
                        "indent": 2
                    }
                },
                
                # Stage 8: Generate Markdown version
                {
                    "id": "generate_md",
                    "type": "function",
                    "params": {
                        "code": f"""
# Generate Markdown format report
report = input if isinstance(input, dict) else {{}}
meta = report.get('metadata', {{}})
analysis = report.get('analysis', '')

md_content = f'''# {{meta.get('title', 'Research Report')}}

**Generated**: {{meta.get('generated_at', 'N/A')}}  
**Research Depth**: {{meta.get('depth', 'standard')}}  
**Engine**: {{meta.get('engine', 'ClawFlow')}}

---

## Research Topic
{topic}

---

## AI Analysis

{{analysis}}

---

## Metadata
- Version: {{meta.get('version', '1.0')}}
- Report ID: {timestamp}

---
*Generated by ClawFlow Research Pipeline*
'''

# Save Markdown
md_path = "{str(report_file)}.md"
with open(md_path, 'w', encoding='utf-8') as f:
    f.write(md_content)

output = {{
    "json_path": "{str(report_file)}.json",
    "markdown_path": md_path,
    "topic": "{topic}",
    "generated_at": "{datetime.now().isoformat()}"
}}
"""
                    }
                },
                
                # Stage 9: Complete notification
                {
                    "id": "complete",
                    "type": "output",
                    "params": {
                        "type": "print"
                    }
                }
            ],
            "connections": [
                # Stage 1 -> Stage 2 (parallel search)
                {"from": "setup", "to": "search_primary"},
                {"from": "setup", "to": "search_secondary"},
                
                # Stage 2 -> Stage 3
                {"from": "search_primary", "to": "aggregate"},
                {"from": "search_secondary", "to": "aggregate"},
                
                # Stage 3 -> Stage 4 -> Stage 5
                {"from": "aggregate", "to": "filter"},
                {"from": "filter", "to": "ai_analysis"},
                
                # Stage 5 -> Stage 6 -> Stage 7/8
                {"from": "ai_analysis", "to": "build_report"},
                {"from": "build_report", "to": "save_json"},
                {"from": "build_report", "to": "generate_md"},
                
                # Stage 8 -> Stage 9
                {"from": "generate_md", "to": "complete"}
            ]
        }
    
    def run(self, topic: str, depth: str = "standard", verbose: bool = True) -> dict:
        """Execute research"""
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔬 ClawFlow Research Pipeline")
            print(f"{'='*60}")
            print(f"Topic: {topic}")
            print(f"Depth: {depth}")
            print(f"Output Directory: {self.output_dir}")
        
        workflow = self.create_workflow(topic, depth)
        
        # Visualize
        if verbose:
            print(f"\n[Workflow Visualization]")
            print(self.engine.visualize(workflow, format="ascii"))
        
        # Execute
        if verbose:
            print(f"\n[Executing Workflow...]")
        
        result = self.engine.execute(workflow, verbose=verbose)
        
        if result.success:
            data = result.data
            if verbose:
                print(f"\n{'='*60}")
                print("✅ Research Complete!")
                print(f"{'='*60}")
                print(f"\n📊 Execution Statistics:")
                print(f"  Total Time: {result.execution_time:.2f}s")
                print(f"  Nodes Executed: {len(result.node_results)}")
                
                if isinstance(data, dict):
                    print(f"\n📄 Generated Files:")
                    if 'json_path' in data:
                        print(f"  JSON: {data['json_path']}")
                    if 'markdown_path' in data:
                        print(f"  Markdown: {data['markdown_path']}")
                        
                        # Show partial content
                        try:
                            with open(data['markdown_path'], 'r') as f:
                                content = f.read()
                                print(f"\n📝 Report Preview (first 500 chars):")
                                print("-" * 40)
                                print(content[:500] + "...")
                                print("-" * 40)
                        except:
                            pass
            
            return {
                "success": True,
                "topic": topic,
                "data": data,
                "execution_time": result.execution_time
            }
        else:
            if verbose:
                print(f"\n❌ Research Failed: {result.error}")
            return {"success": False, "error": result.error}
    
    def schedule_daily(self, topic: str, hour: int = 9, minute: int = 0):
        """Set up daily scheduled research"""
        workflow = self.create_workflow(topic)
        
        cron_expr = f"{minute} {hour} * * *"
        
        result = self.engine.schedule(
            workflow=workflow,
            cron_expr=cron_expr,
            name=f"daily_research_{topic.replace(' ', '_')[:20]}",
            channel="telegram"
        )
        
        print(f"\n📅 Scheduled Task Configured")
        print(f"  Topic: {topic}")
        print(f"  Time: Daily {hour:02d}:{minute:02d}")
        print(f"  Cron: {cron_expr}")
        
        return result
    
    def list_reports(self) -> list:
        """List all generated reports"""
        reports = []
        for f in self.output_dir.glob("research_*.json"):
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    reports.append({
                        "file": str(f),
                        "title": data.get('metadata', {}).get('title', 'Unknown'),
                        "date": data.get('metadata', {}).get('generated_at', 'Unknown'),
                        "topic": data.get('topic', 'Unknown')
                    })
            except:
                pass
        
        return sorted(reports, key=lambda x: x['date'], reverse=True)


def main():
    """Main Function"""
    parser = argparse.ArgumentParser(description='ClawFlow Automated Research Pipeline v2')
    parser.add_argument('topic', nargs='?', default='AI Agent Frameworks 2024',
                       help='Research topic')
    parser.add_argument('--depth', '-d', choices=['quick', 'standard', 'deep'],
                       default='standard', help='Research depth')
    parser.add_argument('--schedule', '-s', action='store_true',
                       help='Set up scheduled task')
    parser.add_argument('--hour', type=int, default=9,
                       help='Scheduled task hour (0-23)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List historical reports')
    parser.add_argument('--output-dir', '-o', default='/tmp/clawflow_research',
                       help='Output directory')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet mode')
    
    args = parser.parse_args()
    
    pipeline = ResearchPipeline(output_dir=args.output_dir)
    
    if args.list:
        reports = pipeline.list_reports()
        print(f"\n📚 Historical Reports ({len(reports)} total):")
        for r in reports[:10]:
            print(f"  - {r['topic']}: {r['date']}")
    elif args.schedule:
        pipeline.schedule_daily(args.topic, args.hour)
    else:
        result = pipeline.run(args.topic, args.depth, verbose=not args.quiet)
        sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
