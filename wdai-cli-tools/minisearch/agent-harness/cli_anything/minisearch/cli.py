#!/usr/bin/env python3
"""
CLI-Anything style harness for wdai_minisearch
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
@click.pass_context
def cli(ctx, json_output):
    """wdai_minisearch - Semantic search for wdai workspace"""
    ctx.ensure_object(dict)
    ctx.obj['JSON'] = json_output

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--output', '-o', default='.minisearch-index', help='Index output directory')
@click.pass_context
def index(ctx, directory, output):
    """Index a directory for semantic search"""
    try:
        from wdai_minisearch import MiniSearch
        
        search = MiniSearch(output)
        search.index_directory(directory)
        
        if ctx.obj.get('JSON'):
            click.echo(json.dumps({
                "status": "success",
                "directory": directory,
                "index_path": output,
                "message": f"Indexed {directory} to {output}"
            }))
        else:
            click.echo(f"✓ Indexed {directory} to {output}")
    except Exception as e:
        if ctx.obj.get('JSON'):
            click.echo(json.dumps({"status": "error", "message": str(e)}))
        else:
            click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('query')
@click.option('--index', '-i', default='.minisearch-index', help='Index directory')
@click.option('--top-k', '-k', default=5, help='Number of results')
@click.option('--threshold', '-t', default=0.5, type=float, help='Similarity threshold')
@click.pass_context
def search(ctx, query, index, top_k, threshold):
    """Search the index with a query"""
    try:
        from wdai_minisearch import MiniSearch
        
        search_engine = MiniSearch(index)
        results = search_engine.search(query, top_k=top_k, threshold=threshold)
        
        if ctx.obj.get('JSON'):
            click.echo(json.dumps({
                "status": "success",
                "query": query,
                "results": results
            }, indent=2))
        else:
            click.echo(f"Results for: {query}")
            click.echo("-" * 50)
            for i, r in enumerate(results, 1):
                click.echo(f"{i}. [{r.get('score', 0):.3f}] {r.get('file', 'N/A')}")
                click.echo(f"   {r.get('content', '')[:100]}...")
    except Exception as e:
        if ctx.obj.get('JSON'):
            click.echo(json.dumps({"status": "error", "message": str(e)}))
        else:
            click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def status(ctx):
    """Check index status"""
    try:
        from wdai_minisearch import MiniSearch
        
        search = MiniSearch('.minisearch-index')
        stats = search.get_stats()
        
        if ctx.obj.get('JSON'):
            click.echo(json.dumps({
                "status": "success",
                "stats": stats
            }))
        else:
            click.echo("Index Status:")
            for key, value in stats.items():
                click.echo(f"  {key}: {value}")
    except Exception as e:
        if ctx.obj.get('JSON'):
            click.echo(json.dumps({"status": "error", "message": str(e)}))
        else:
            click.echo(f"✗ Error: {e}", err=True)

if __name__ == '__main__':
    cli()
