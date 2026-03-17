# SKILL.md - wdai_minisearch

## Overview

Semantic search tool for wdai workspace with CLI-Anything style interface.

## Commands

### index

Index a directory for semantic search.

**Usage:**
```
cli-anything-wdai-minisearch index <directory> [options]
```

**Options:**
- `-o, --output`: Index output directory (default: .minisearch-index)

**Example:**
```bash
cli-anything-wdai-minisearch index ./documents
cli-anything-wdai-minisearch index ./src -o ./custom-index
```

### search

Search the indexed documents.

**Usage:**
```
cli-anything-wdai-minisearch search <query> [options]
```

**Options:**
- `-i, --index`: Index directory (default: .minisearch-index)
- `-k, --top-k`: Number of results (default: 5)
- `-t, --threshold`: Similarity threshold (default: 0.5)

**Example:**
```bash
cli-anything-wdai-minisearch search "machine learning"
cli-anything-wdai-minisearch search "deployment" -k 10 -t 0.7
```

### status

Check index status and statistics.

**Example:**
```bash
cli-anything-wdai-minisearch status
```

## JSON Output

All commands support `--json` for agent consumption:

```bash
cli-anything-wdai-minisearch --json search "query"
```

Output format:
```json
{
  "status": "success",
  "query": "machine learning",
  "results": [
    {"file": "doc1.md", "score": 0.85, "content": "..."}
  ]
}
```

## Installation

```bash
cd minisearch/agent-harness
pip install -e .
```

## Requirements

- Python 3.10+
- sentence-transformers
- chromadb
