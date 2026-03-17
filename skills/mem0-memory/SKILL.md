---
name: mem0-memory
description: "Mem0-inspired adaptive memory system for OpenClaw. Provides automatic memory extraction, intelligent conflict resolution, semantic retrieval, and time-based decay. Use when you need to remember facts across sessions, resolve conflicting information, or retrieve relevant context based on semantic similarity rather than just keyword matching."
---

# mem0-memory — Adaptive Memory Layer

> "Memory is not just storage. It's intelligent extraction, conflict resolution, and contextual retrieval."
> 
> — Inspired by Mem0 architecture

---

## Core Concepts

This skill implements a **three-layer memory architecture** inspired by Mem0:

```
┌─────────────────────────────────────────┐
│      Working Memory (当前会话)            │
│  - Active conversation context          │
│  - Recent interactions                  │
└─────────────────────────────────────────┘
              ↕
┌─────────────────────────────────────────┐
│      Episodic Memory (经验记忆)           │
│  - Session summaries                    │
│  - Interaction patterns                 │
│  - Project history                      │
└─────────────────────────────────────────┘
              ↕
┌─────────────────────────────────────────┐
│      Semantic Memory (语义记忆)           │
│  - User preferences                     │
│  - Learned principles                   │
│  - Domain knowledge                     │
└─────────────────────────────────────────┘
```

---

## When to Use

| Scenario | Use mem0-memory |
|----------|-----------------|
| Conversation ends, need to extract key facts | ✅ `memory_extract` |
| Detecting conflicting information | ✅ `memory_resolve` |
| Finding relevant past context | ✅ `memory_search` |
| Cleaning up old memories | ✅ `memory_decay` |
| Simple file read/write | ❌ Use built-in `read`/`write` |

---

## Memory Operations

### 1. Extract — Automatic Memory Extraction

Extract atomic facts from conversation and store them.

```bash
python $SKILL_DIR/scripts/memory_extract.py \
  --source memory/2026-03-10.md \
  --output .memory/semantic/
```

**What gets extracted:**
- User preferences ("I prefer Python over JavaScript")
- Key decisions ("We decided to use PostgreSQL")
- Constraints ("Budget is limited to $1000")
- TODOs ("Need to research AWS pricing")

**Atomicity principle:** Each memory is a single, complete fact.

---

### 2. Resolve — Conflict Resolution

Detect and resolve conflicts between new and existing memories.

```bash
python $SKILL_DIR/scripts/memory_resolve.py \
  --new .memory/temp/new_facts.json \
  --existing .memory/semantic/
```

**Resolution strategies:**
- **Override**: New fact replaces old (user changed preference)
- **Merge**: Combine related facts
- **Flag**: Mark for human review when uncertain
- **Version**: Keep both with timestamps

---

### 3. Search — Semantic Retrieval

Find relevant memories using semantic similarity.

```bash
python $SKILL_DIR/scripts/memory_search.py \
  --query "What database did we choose?" \
  --memory-path .memory/semantic/ \
  --top-k 5
```

**Retrieval features:**
- Semantic matching (not just keywords)
- Time decay weighting (recent > old)
- Confidence filtering
- Category filtering

---

### 4. Decay — Memory Maintenance

Apply time-based decay to old memories.

```bash
python $SKILL_DIR/scripts/memory_decay.py \
  --memory-path .memory/semantic/ \
  --half-life 30  # days
```

**Decay formula:**
```
current_score = base_score * (0.5 ^ (days_old / half_life))
```

Memories below threshold can be archived or deleted.

---

## Memory Schema

Each memory is stored as:

```json
{
  "id": "uuid-v4",
  "fact": "User prefers Python for backend development",
  "category": "preference",
  "confidence": 0.95,
  "created_at": "2026-03-10T14:30:00Z",
  "last_accessed": "2026-03-10T14:30:00Z",
  "access_count": 1,
  "decay_score": 1.0,
  "embedding": [0.12, -0.05, ...],  // vector representation
  "metadata": {
    "source": "conversation",
    "session_id": "abc123",
    "tags": ["python", "backend"]
  }
}
```

**Categories:**
- `preference` — User preferences and likes/dislikes
- `constraint` — Limitations, requirements, boundaries
- `decision` — Key decisions made
- `fact` — Objective facts learned
- `todo` — Action items
- `principle` — Learned principles/patterns

---

## Integration with OpenClaw

### Recommended Workflow

**At session start:**
```bash
# Load relevant memories into context
python $SKILL_DIR/scripts/memory_search.py \
  --query "Current project context" \
  --top-k 10 > .memory/working/session_context.json
```

**During conversation:**
- Use working memory for immediate context
- Reference episodic memory for past sessions
- Ground responses in semantic memory for consistency

**At session end:**
```bash
# Extract and store new memories
python $SKILL_DIR/scripts/memory_extract.py \
  --source memory/$(date +%Y-%m-%d).md

# Resolve any conflicts
python $SKILL_DIR/scripts/memory_resolve.py

# Apply decay to old memories
python $SKILL_DIR/scripts/memory_decay.py
```

### AGENTS.md Integration

Add to your `AGENTS.md`:

```markdown
## Memory Management

Before starting work:
1. Check `.memory/working/` for active session context
2. Search semantic memory for relevant past context

During work:
- Reference stored preferences for consistency
- Respect recorded constraints

After work:
- Run memory_extract.py to capture key facts
- Review and resolve conflicts
- Update SOUL.md if principles evolved
```

---

## Directory Structure

```
.memory/
├── working/              # Current session context
│   └── session_context.json
├── episodic/             # Session summaries by date
│   ├── 2026-03-09.json
│   └── 2026-03-10.json
├── semantic/             # Long-term knowledge
│   ├── preferences.json
│   ├── constraints.json
│   └── principles.json
└── vector/               # Embedding index
    └── index.faiss
```

---

## Comparison with Simple File Storage

| Aspect | Simple Files | mem0-memory |
|--------|-------------|-------------|
| Storage | Raw text | Structured JSON |
| Retrieval | Keyword search | Semantic + keyword |
| Conflicts | Manual handling | Automatic detection |
| Relevance | Time-based | Decay-weighted |
| Context | Full file load | Targeted retrieval |

---

## Configuration

Environment variables (optional):

```bash
export MEMORY_PATH=".memory"           # Base memory directory
export EMBEDDING_MODEL="text-embedding-3-small"  # For semantic search
export DECAY_HALF_LIFE=30              # Days
export CONFIDENCE_THRESHOLD=0.7        # Minimum confidence to store
```

---

## Best Practices

1. **Extract early, extract often** — Don't wait for end of session
2. **Be atomic** — One fact per memory
3. **Tag generously** — Improves retrieval
4. **Review conflicts** — Don't auto-resolve high-stakes conflicts
5. **Decay aggressively** — Let old memories fade naturally
6. **Backup semantic/** — This is your long-term knowledge

---

## Troubleshooting

**Too many memories retrieved?**
→ Lower `--top-k` or add `--category-filter`

**Conflicting memories piling up?**
→ Run `memory_resolve.py` more frequently

**Old memories interfering?**
→ Adjust `--half-life` or run `memory_decay.py`

**Missing important context?**
→ Check if it was extracted with sufficient confidence

---

## References

- [Mem0 Official](https://mem0.ai) — Production memory layer
- [Mem0 GitHub](https://github.com/mem0ai/mem0) — 41k+ stars
- `references/memory-architecture.md` — Deep dive
- `references/extraction-prompts.md` — Prompt engineering

---

## License

MIT — Same as Mem0 (Apache 2.0 for core concepts, MIT for this implementation)
