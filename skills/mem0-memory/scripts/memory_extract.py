#!/usr/bin/env python3
"""
Memory Extractor — Automatic fact extraction from conversations
Inspired by Mem0's extraction pipeline

Usage:
    python memory_extract.py --source memory/2026-03-10.md --output .memory/semantic/
"""

import argparse
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Extraction patterns (simplified version of LLM-based extraction)
# In production, this would call an LLM API

FACT_PATTERNS = {
    'preference': [
        r'(?:我|用户|他|她).*?(?:喜欢|偏好| prefer).*?(.+?)(?:\.|$)',
        r'(?:I|user|he|she).*?(?:prefer|like).*?(.+?)(?:\.|$)',
    ],
    'constraint': [
        r'(?:限制|约束|必须|需要).*?(.+?)(?:\.|$)',
        r'(?:constraint|must|need to|have to).*?(.+?)(?:\.|$)',
    ],
    'decision': [
        r'(?:决定|选择|采用|使用).*?(.+?)(?:\.|$)',
        r'(?:decided|chose|selected|using).*?(.+?)(?:\.|$)',
    ],
    'todo': [
        r'(?:TODO|待办|需要|应该).*?(.+?)(?:\.|$)',
        r'(?:need to|should|will|plan to).*?(.+?)(?:\.|$)',
    ],
}


def extract_facts_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract atomic facts from text using patterns."""
    facts = []
    
    for category, patterns in FACT_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                fact_text = match.group(1).strip()
                if len(fact_text) > 10:  # Filter out very short matches
                    facts.append({
                        'id': str(uuid.uuid4()),
                        'fact': fact_text,
                        'category': category,
                        'confidence': 0.7,  # Pattern-based = medium confidence
                        'created_at': datetime.now().isoformat(),
                        'last_accessed': datetime.now().isoformat(),
                        'access_count': 0,
                        'decay_score': 1.0,
                        'embedding': None,  # Would be populated by embedding model
                        'metadata': {
                            'source': 'pattern_extraction',
                            'extracted_by': 'memory_extract.py'
                        }
                    })
    
    return facts


def load_existing_memories(memory_path: Path) -> List[Dict]:
    """Load existing memories from directory."""
    memories = []
    if memory_path.exists():
        for file in memory_path.glob('*.json'):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        memories.extend(data)
                    else:
                        memories.append(data)
            except Exception as e:
                print(f"Warning: Could not load {file}: {e}")
    return memories


def check_conflicts(new_fact: Dict, existing_memories: List[Dict]) -> List[str]:
    """Check for potential conflicts with existing memories."""
    conflicts = []
    
    for existing in existing_memories:
        # Simple similarity check (in production, use embedding similarity)
        if similar_facts(new_fact['fact'], existing['fact']):
            conflicts.append(existing['id'])
    
    return conflicts


def similar_facts(fact1: str, fact2: str, threshold: float = 0.6) -> bool:
    """Check if two facts are similar."""
    # Simple word overlap (in production, use semantic similarity)
    words1 = set(fact1.lower().split())
    words2 = set(fact2.lower().split())
    
    if not words1 or not words2:
        return False
    
    overlap = len(words1 & words2)
    similarity = overlap / max(len(words1), len(words2))
    
    return similarity > threshold


def save_memories(memories: List[Dict], output_path: Path, category: str = None):
    """Save memories to file."""
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"extracted_{category or 'all'}_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(memories, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(memories)} memories to {filepath}")


def main():
    parser = argparse.ArgumentParser(description='Extract memories from conversation')
    parser.add_argument('--source', required=True, help='Source file to extract from')
    parser.add_argument('--output', default='.memory/semantic/', help='Output directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be extracted without saving')
    
    args = parser.parse_args()
    
    # Load source
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}")
        return 1
    
    with open(source_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Load existing memories for conflict detection
    output_path = Path(args.output)
    existing_memories = load_existing_memories(output_path)
    print(f"Loaded {len(existing_memories)} existing memories")
    
    # Extract facts
    facts = extract_facts_from_text(text)
    print(f"Extracted {len(facts)} candidate facts")
    
    # Check for conflicts
    for fact in facts:
        conflicts = check_conflicts(fact, existing_memories)
        if conflicts:
            fact['metadata']['potential_conflicts'] = conflicts
            print(f"  ⚠️  Potential conflict: {fact['fact'][:50]}...")
    
    # Group by category
    by_category = {}
    for fact in facts:
        cat = fact['category']
        by_category.setdefault(cat, []).append(fact)
    
    print("\nBreakdown by category:")
    for cat, items in by_category.items():
        print(f"  {cat}: {len(items)}")
    
    if args.dry_run:
        print("\n--- Dry Run: Would extract ---")
        for fact in facts[:5]:  # Show first 5
            print(f"\n[{fact['category']}] {fact['fact']}")
            if 'potential_conflicts' in fact['metadata']:
                print(f"  ⚠️ Conflicts with: {fact['metadata']['potential_conflicts']}")
        if len(facts) > 5:
            print(f"\n... and {len(facts) - 5} more")
    else:
        # Save by category
        for cat, items in by_category.items():
            save_memories(items, output_path, cat)
        
        # Also save combined
        save_memories(facts, output_path, 'all')
    
    return 0


if __name__ == '__main__':
    exit(main())
