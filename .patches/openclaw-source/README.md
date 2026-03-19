# OpenClaw Innovation Source Patch

Generated: 2026-03-19

## Files

```
openclaw-source/
├── src/
│   ├── innovation/
│   │   ├── engine.ts      # Core innovation engine
│   │   ├── verifiers.ts   # Result verifiers
│   │   └── index.ts       # Exports
│   └── core/
│       └── tool-execution.patch  # Patch for tool execution
├── config/
│   └── innovation.yaml    # Configuration
└── install.sh             # Installation script
```

## Installation

```bash
cd /root/.openclaw/workspace/.patches/openclaw-source
./install.sh /usr/lib/node_modules/openclaw
```

## Manual Steps

1. Apply `tool-execution.patch` to `src/core/tool-execution.ts`
2. Rebuild: `npm run build`
3. Restart OpenClaw

## Verification

Test innovation:
```bash
# Block HTTPS port
sudo iptables -A OUTPUT -p tcp --dport 443 -j DROP

# Try git push - should auto-fallback to SSH
git push origin master

# Check result
git status  # Should show "up to date"
```

## Configuration

Edit `~/.openclaw/innovation.yaml` to customize patterns.

Set environment variable to disable:
```bash
export OPENCLAW_INNOVATION=disabled
```
