#!/bin/bash
# OpenClaw Innovation Installation Script

set -e

OPENCLAW_DIR="${1:-/usr/lib/node_modules/openclaw}"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing OpenClaw Innovation..."
echo "Target: $OPENCLAW_DIR"
echo ""

# Backup
echo "1. Creating backup..."
cp -r "$OPENCLAW_DIR/src" "$OPENCLAW_DIR/src.backup.$(date +%Y%m%d%H%M%S)"

# Copy new files
echo "2. Copying innovation engine..."
cp -r "$PATCH_DIR/src/innovation" "$OPENCLAW_DIR/src/"

# Apply patch to tool-execution.ts
echo "3. Patching tool-execution.ts..."
cd "$OPENCLAW_DIR"
# Note: This is a manual step - see tool-execution.patch for changes

echo "4. Copying config..."
mkdir -p ~/.openclaw
cp "$PATCH_DIR/config/innovation.yaml" ~/.openclaw/

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Review and apply tool-execution.patch manually"
echo "2. Rebuild OpenClaw: npm run build"
echo "3. Restart OpenClaw service"
echo "4. Test: git push (should auto-fallback on failure)"
