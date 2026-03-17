# SKILL.md - wdai_autoresearch

## Overview

Autonomous research system with self-improvement capabilities.

## Commands

### research

Start autonomous research on a topic.

**Usage:**
```
cli-anything-wdai-autoresearch research <topic> [options]
```

**Options:**
- `-h, --hypothesis`: Initial hypothesis
- `-d, --depth`: Research depth 1-5 (default: 3)
- `-o, --output`: Output file for results

**Example:**
```bash
cli-anything-wdai-autoresearch research "Python asyncio"
cli-anything-wdai-autoresearch research "AI agents" -h "Agents will replace GUIs" -d 4
```

### status

Check active research projects.

**Example:**
```bash
cli-anything-wdai-autoresearch status
cli-anything-wdai-autoresearch status -w ./custom-workspace
```

### findings

Get findings for a specific project.

**Usage:**
```
cli-anything-wdai-autoresearch findings <project>
```

**Example:**
```bash
cli-anything-wdai-autoresearch findings "python-asyncio"
```

## JSON Output

All commands support `--json` for agent consumption:

```bash
cli-anything-wdai-autoresearch --json research "topic"
```

Output format:
```json
{
  "topic": "Python asyncio",
  "hypothesis": "...",
  "depth": 3,
  "status": "started"
}
```

## Installation

```bash
cd autoresearch/agent-harness
pip install -e .
```

## Research Phases

1. **Explore**: Generate diverse search queries
2. **Investigate**: Parallel web research
3. **Reflect**: Multi-critic analysis
4. **Synthesize**: Cross-validate and consolidate
5. **Learn**: Extract principles for future use
6. **Navigate**: Self-correct and iterate

## Features

- Self-Navigating: Dynamic query adjustment
- Self-Attributing: Source tracking
- Self-Improving: IER (Iterative Evolution Registry)
- Cross-validation: Multiple perspectives
