#!/usr/bin/env python3
"""
CLI-Anything style harness for wdai_autoresearch
Auto-generated CLI interface
"""

import click
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

@click.group()
@click.option('--json-output', '--json', is_flag=True, help='Output JSON for agent consumption')
@click.option('--workspace', '-w', default='.wdai-autoresearch', help='Workspace directory')
@click.pass_context
def cli(ctx, json_output, workspace):
    """wdai_autoresearch - Autonomous research with self-improvement"""
    ctx.ensure_object(dict)
    ctx.obj['JSON'] = json_output
    ctx.obj['WORKSPACE'] = workspace

@cli.command()
@click.argument('topic')
@click.option('--hypothesis', '-h', help='Initial hypothesis')
@click.option('--depth', '-d', default=3, type=int, help='Research depth (1-5)')
@click.option('--output', '-o', help='Output file')
@click.pass_context
def research(ctx, topic, hypothesis, depth, output):
    """Start autonomous research on a topic"""
    try:
        # Import would go here
        # from wdai_autoresearch_v3_4 import AutoResearcher
        # researcher = AutoResearcher(workspace=ctx.obj['WORKSPACE'])
        # result = researcher.research(topic, hypothesis=hypothesis, depth=depth)
        
        result = {
            "topic": topic,
            "hypothesis": hypothesis or "To be determined",
            "depth": depth,
            "workspace": ctx.obj['WORKSPACE'],
            "status": "started"
        }
        
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
        
        if ctx.obj.get('JSON'):
            click.echo(json.dumps(result))
        else:
            click.echo(f"✓ Started research on: {topic}")
            click.echo(f"  Hypothesis: {result['hypothesis']}")
            click.echo(f"  Depth: {depth}")
            click.echo(f"  Workspace: {ctx.obj['WORKSPACE']}")
            if output:
                click.echo(f"  Output: {output}")
    except Exception as e:
        if ctx.obj.get('JSON'):
            click.echo(json.dumps({"status": "error", "message": str(e)}))
        else:
            click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def status(ctx):
    """Check research status"""
    try:
        workspace = ctx.obj['WORKSPACE']
        
        result = {
            "workspace": workspace,
            "active_research": [],
            "completed": [],
            "total_findings": 0
        }
        
        # Check workspace for research projects
        if os.path.exists(workspace):
            for item in os.listdir(workspace):
                item_path = os.path.join(workspace, item)
                if os.path.isdir(item_path):
                    result["active_research"].append(item)
        
        if ctx.obj.get('JSON'):
            click.echo(json.dumps(result))
        else:
            click.echo("Research Status:")
            click.echo(f"  Workspace: {workspace}")
            click.echo(f"  Active Projects: {len(result['active_research'])}")
            for project in result['active_research']:
                click.echo(f"    - {project}")
    except Exception as e:
        if ctx.obj.get('JSON'):
            click.echo(json.dumps({"status": "error", "message": str(e)}))
        else:
            click.echo(f"✗ Error: {e}", err=True)

@cli.command()
@click.argument('project')
@click.pass_context
def findings(ctx, project):
    """Get findings for a research project"""
    try:
        workspace = ctx.obj['WORKSPACE']
        project_path = os.path.join(workspace, project)
        
        result = {
            "project": project,
            "findings": [],
            "sources": []
        }
        
        # Load findings from project directory
        findings_file = os.path.join(project_path, 'findings.json')
        if os.path.exists(findings_file):
            with open(findings_file) as f:
                result = json.load(f)
        
        if ctx.obj.get('JSON'):
            click.echo(json.dumps(result))
        else:
            click.echo(f"Findings for: {project}")
            for finding in result.get('findings', []):
                click.echo(f"  - {finding}")
    except Exception as e:
        if ctx.obj.get('JSON'):
            click.echo(json.dumps({"status": "error", "message": str(e)}))
        else:
            click.echo(f"✗ Error: {e}", err=True)

if __name__ == '__main__':
    cli()
