#!/bin/bash
# Proactive autonomy triggers

WORKSPACE="${HOME}/.openclaw/workspace"

# Check memory usage
MEMORY_USAGE=$(du -s "${WORKSPACE}/.memory-system" 2>/dev/null | awk '{print $1}' || echo 0)
if [ "$MEMORY_USAGE" -gt 102400 ]; then  # 100MB
    echo "[AUTONOMY] Memory usage high (${MEMORY_USAGE}KB), triggering optimization..."
    ~/.openclaw/skills/enhanced-memory-system/scripts/memory-op.sh maintenance 2>/dev/null || true
fi

# Check for pending errors
PENDING_ERRORS=$(grep -c "Status.*pending" "${WORKSPACE}/.learnings/ERRORS.md" 2>/dev/null || echo 0)
if [ "$PENDING_ERRORS" -gt 3 ]; then
    echo "[AUTONOMY] ${PENDING_ERRORS} pending errors detected, triggering analysis..."
    ~/.openclaw/skills/self-evolution-orchestrator/scripts/evolution-check.sh --analyze planning 2>/dev/null || true
fi

# Check skill count
SKILL_COUNT=$(ls -1 "${WORKSPACE}/skills/" 2>/dev/null | wc -l)
if [ "$SKILL_COUNT" -lt 5 ]; then
    echo "[AUTONOMY] Skill count low (${SKILL_COUNT}), consider installing more..."
fi

echo "[AUTONOMY] Trigger check complete at $(date)"
