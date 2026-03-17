#!/usr/bin/env python3
"""
Memory Resolver — Intelligent conflict resolution
Inspired by Mem0's conflict handling

Usage:
    python memory_resolve.py --new .memory/temp/new.json --existing .memory/semantic/
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple


class ConflictResolver:
    """Resolve conflicts between new and existing memories."""
    
    STRATEGIES = {
        'override': 'New memory replaces old (user changed preference)',
        'merge': 'Combine related memories into one',
        'flag': 'Mark for human review',
        'keep_both': 'Keep both with version timestamps',
        'ignore_new': 'Keep existing, discard new',
    }
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
    
    def detect_conflicts(self, new_memories: List[Dict], existing_memories: List[Dict]) -> List[Tuple[Dict, Dict, float]]:
        """Detect potential conflicts between new and existing memories."""
        conflicts = []
        
        for new_mem in new_memories:
            for existing_mem in existing_memories:
                similarity = self._calculate_similarity(new_mem, existing_mem)
                if similarity > 0.5:  # Threshold for potential conflict
                    conflicts.append((new_mem, existing_mem, similarity))
        
        # Sort by similarity (highest first)
        conflicts.sort(key=lambda x: x[2], reverse=True)
        return conflicts
    
    def _calculate_similarity(self, mem1: Dict, mem2: Dict) -> float:
        """Calculate semantic similarity between two memories."""
        # Use embedding if available
        if mem1.get('embedding') and mem2.get('embedding'):
            return self._cosine_similarity(mem1['embedding'], mem2['embedding'])
        
        # Fallback to text similarity
        return self._text_similarity(mem1['fact'], mem2['fact'])
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity based on word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1 & words2)
        return overlap / max(len(words1), len(words2))
    
    def resolve(self, new_mem: Dict, existing_mem: Dict, similarity: float) -> Dict[str, Any]:
        """Determine resolution strategy for a conflict."""
        
        # High similarity = likely the same fact
        if similarity > 0.8:
            if new_mem['confidence'] > existing_mem['confidence']:
                return {
                    'strategy': 'override',
                    'reason': 'New fact has higher confidence',
                    'action': 'Replace existing with new'
                }
            else:
                return {
                    'strategy': 'ignore_new',
                    'reason': 'Existing fact has equal or higher confidence',
                    'action': 'Keep existing'
                }
        
        # Medium similarity = might be related
        if similarity > 0.6:
            # Check if they contradict
            if self._might_contradict(new_mem, existing_mem):
                return {
                    'strategy': 'flag',
                    'reason': 'Potential contradiction detected',
                    'action': 'Mark for human review'
                }
            else:
                return {
                    'strategy': 'merge',
                    'reason': 'Related facts can be combined',
                    'action': 'Merge into single memory'
                }
        
        # Low similarity but above threshold = related but distinct
        return {
            'strategy': 'keep_both',
            'reason': 'Related but distinct facts',
            'action': 'Keep both with relationship noted'
        }
    
    def _might_contradict(self, mem1: Dict, mem2: Dict) -> bool:
        """Check if two memories might contradict each other."""
        # Simple heuristic: same category, similar topic, but different content
        if mem1['category'] != mem2['category']:
            return False
        
        # Check for negation patterns
        negation_words = ['not', 'no', 'never', "don't", '不喜欢', '不', '没']
        
        has_negation1 = any(word in mem1['fact'].lower() for word in negation_words)
        has_negation2 = any(word in mem2['fact'].lower() for word in negation_words)
        
        # If one has negation and other doesn't, might contradict
        if has_negation1 != has_negation2:
            return True
        
        return False
    
    def apply_resolution(self, new_mem: Dict, existing_mem: Dict, resolution: Dict) -> Dict:
        """Apply the resolution strategy."""
        strategy = resolution['strategy']
        
        if strategy == 'override':
            # Update existing with new content, keep history
            existing_mem['fact'] = new_mem['fact']
            existing_mem['confidence'] = new_mem['confidence']
            existing_mem['last_accessed'] = datetime.now().isoformat()
            if 'history' not in existing_mem:
                existing_mem['history'] = []
            existing_mem['history'].append({
                'replaced_at': datetime.now().isoformat(),
                'previous_fact': existing_mem.get('fact', '')
            })
            return existing_mem
        
        elif strategy == 'merge':
            # Combine facts
            merged_fact = f"{existing_mem['fact']}; Also: {new_mem['fact']}"
            existing_mem['fact'] = merged_fact
            existing_mem['confidence'] = max(existing_mem['confidence'], new_mem['confidence'])
            existing_mem['last_accessed'] = datetime.now().isoformat()
            return existing_mem
        
        elif strategy == 'keep_both':
            # Note relationship and keep both
            new_mem['metadata']['related_to'] = existing_mem['id']
            existing_mem['metadata']['related_to'] = new_mem['id']
            return new_mem  # Return new for addition
        
        elif strategy == 'flag':
            # Mark both for review
            existing_mem['metadata']['needs_review'] = True
            existing_mem['metadata']['conflict_with'] = new_mem['id']
            new_mem['metadata']['needs_review'] = True
            new_mem['metadata']['conflict_with'] = existing_mem['id']
            return new_mem
        
        elif strategy == 'ignore_new':
            # Just update access time on existing
            existing_mem['last_accessed'] = datetime.now().isoformat()
            existing_mem['access_count'] = existing_mem.get('access_count', 0) + 1
            return None  # Don't add new
        
        return new_mem


def load_memories(path: Path) -> List[Dict]:
    """Load memories from file or directory."""
    memories = []
    
    if path.is_file():
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                memories = data
            else:
                memories = [data]
    elif path.is_dir():
        for file in path.glob('*.json'):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    memories.extend(data)
                else:
                    memories.append(data)
    
    return memories


def save_memories(memories: List[Dict], output_path: Path):
    """Save resolved memories."""
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Group by category
    by_category = {}
    for mem in memories:
        cat = mem.get('category', 'uncategorized')
        by_category.setdefault(cat, []).append(mem)
    
    for cat, items in by_category.items():
        filepath = output_path / f"{cat}_resolved.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(items)} {cat} memories to {filepath}")


def main():
    parser = argparse.ArgumentParser(description='Resolve memory conflicts')
    parser.add_argument('--new', required=True, help='New memories file or directory')
    parser.add_argument('--existing', required=True, help='Existing memories directory')
    parser.add_argument('--output', help='Output directory (default: overwrite existing)')
    parser.add_argument('--dry-run', action='store_true', help='Show resolutions without applying')
    
    args = parser.parse_args()
    
    # Load memories
    new_memories = load_memories(Path(args.new))
    existing_memories = load_memories(Path(args.existing))
    
    print(f"Loaded {len(new_memories)} new memories")
    print(f"Loaded {len(existing_memories)} existing memories")
    
    # Initialize resolver
    resolver = ConflictResolver()
    
    # Detect conflicts
    conflicts = resolver.detect_conflicts(new_memories, existing_memories)
    print(f"\nDetected {len(conflicts)} potential conflicts")
    
    # Resolve conflicts
    resolved_memories = list(existing_memories)  # Start with existing
    
    for new_mem, existing_mem, similarity in conflicts[:10]:  # Process top 10
        resolution = resolver.resolve(new_mem, existing_mem, similarity)
        
        print(f"\n[{similarity:.2f}] Conflict detected:")
        print(f"  Existing: {existing_mem['fact'][:60]}...")
        print(f"  New:      {new_mem['fact'][:60]}...")
        print(f"  Strategy: {resolution['strategy']} - {resolution['reason']}")
        
        if not args.dry_run:
            result = resolver.apply_resolution(new_mem, existing_mem, resolution)
            if result and result not in resolved_memories:
                resolved_memories.append(result)
    
    # Add non-conflicting new memories
    conflicting_new_ids = {id(m) for _, m, _ in conflicts}
    for new_mem in new_memories:
        if id(new_mem) not in conflicting_new_ids:
            resolved_memories.append(new_mem)
    
    print(f"\nTotal memories after resolution: {len(resolved_memories)}")
    
    if not args.dry_run:
        output_path = Path(args.output) if args.output else Path(args.existing)
        save_memories(resolved_memories, output_path)
        print(f"\nResolved memories saved to {output_path}")
    
    return 0


if __name__ == '__main__':
    exit(main())
