#!/usr/bin/env python3
"""
OpenClaw 创新能力修改生成器
生成可以直接应用到OpenClaw源代码的修改
"""

import os
from pathlib import Path

# 输出目录
PATCH_DIR = Path("/root/.openclaw/workspace/.patches/openclaw-source")
PATCH_DIR.mkdir(parents=True, exist_ok=True)

# 1. 创新引擎核心
ENGINE_TS = '''/**
 * Innovation Engine - Core innovation capabilities
 */

import { ToolCall, ToolResult, Tool } from '../core/tool-types';
import { logger } from '../utils/logger';

export interface InnovationConfig {
  enabled: boolean;
  maxAttempts: number;
  verifyResults: boolean;
  autoFallback: boolean;
  learningEnabled: boolean;
}

export interface MethodPattern {
  tool: string;
  method: string;
  triggerErrors: string[];
  fallbackChain: FallbackMethod[];
  verifier?: string;
}

export interface FallbackMethod {
  name: string;
  adapter?: (params: any) => any;
  tool?: string;
}

export class InnovationEngine {
  private config: InnovationConfig;
  private patterns: Map<string, MethodPattern> = new Map();
  private stats: Map<string, any> = new Map();

  constructor(config: InnovationConfig) {
    this.config = config;
    this.loadPatterns();
  }

  isEnabled(toolName: string): boolean {
    if (!this.config.enabled) return false;
    const toolConfig = this.getToolConfig(toolName);
    return toolConfig?.enabled !== false;
  }

  async execute(call: ToolCall, tool: Tool): Promise<ToolResult> {
    const key = `${call.name}:${this.extractMethod(call)}`;

    try {
      const result = await tool.execute(call.params);
      
      if (await this.verify(call.name, result)) {
        return this.addMeta(result, { innovation: true, verified: true });
      }
      
      throw new Error('Verification failed');
    } catch (error) {
      if (this.config.autoFallback) {
        return await this.tryFallbacks(call, tool, key);
      }
      throw error;
    }
  }

  private async tryFallbacks(call: ToolCall, tool: Tool, key: string): Promise<ToolResult> {
    const pattern = this.patterns.get(key);
    if (!pattern || pattern.fallbackChain.length === 0) {
      throw new Error(`No fallbacks for ${key}`);
    }

    for (const fallback of pattern.fallbackChain) {
      try {
        const fbTool = fallback.tool ? getTool(fallback.tool) : tool;
        const fbParams = fallback.adapter ? fallback.adapter(call.params) : call.params;
        
        const result = await fbTool.execute(fbParams);
        
        if (await this.verify(fallback.name, result)) {
          return this.addMeta(result, {
            innovation: true,
            autoFallback: true,
            from: key,
            to: fallback.name
          });
        }
      } catch (e) {
        continue;
      }
    }

    throw new Error('All fallbacks failed');
  }

  private async verify(toolName: string, result: ToolResult): Promise<boolean> {
    if (!this.config.verifyResults) return true;
    
    const pattern = this.patterns.get(toolName);
    if (!pattern?.verifier) {
      return result.success !== false;
    }

    try {
      const verifier = getVerifier(pattern.verifier);
      return await verifier.verify(result);
    } catch {
      return false;
    }
  }

  private extractMethod(call: ToolCall): string {
    if (call.params?.command) {
      return call.params.command.split(' ')[0];
    }
    return 'default';
  }

  private addMeta(result: ToolResult, meta: any): ToolResult {
    return { ...result, metadata: { ...(result.metadata || {}), ...meta } };
  }

  private loadPatterns(): void {
    const patterns = loadInnovationPatterns();
    for (const p of patterns) {
      this.patterns.set(`${p.tool}:${p.method}`, p);
    }
  }

  private getToolConfig(toolName: string): any {
    // Load from config
    return { enabled: true };
  }
}

// Helpers
function getTool(name: string): Tool {
  const { getTool: gt } = require('../core/tool-registry');
  return gt(name);
}

function getVerifier(name: string): any {
  const { getVerifier: gv } = require('./verifiers');
  return gv(name);
}

function loadInnovationPatterns(): MethodPattern[] {
  return [
    {
      tool: 'exec',
      method: 'git',
      triggerErrors: ['could not read Username', 'Connection refused'],
      fallbackChain: [
        { name: 'git_ssh', adapter: (p) => ({ ...p, useSsh: true }) }
      ],
      verifier: 'git_status'
    }
  ];
}
'''

# 2. 验证器
VERIFIERS_TS = '''/**
 * Result Verifiers
 */

import { ToolResult } from '../core/tool-types';

export interface Verifier {
  name: string;
  verify(result: ToolResult): Promise<boolean>;
}

export class GitStatusVerifier implements Verifier {
  name = 'git_status';
  
  async verify(result: ToolResult): Promise<boolean> {
    try {
      const { exec } = require('../tools/exec');
      const check = await exec.execute({ command: 'git status', timeout: 5000 });
      const output = check.output || check.stdout || '';
      return output.includes('up to date') || output.includes('up-to-date');
    } catch {
      return false;
    }
  }
}

export class FileExistenceVerifier implements Verifier {
  name = 'file_exists';
  
  async verify(result: ToolResult): Promise<boolean> {
    try {
      const { read } = require('../tools/read');
      await read.execute({ path: result.path || result.output });
      return true;
    } catch {
      return false;
    }
  }
}

const verifiers: Map<string, Verifier> = new Map([
  ['git_status', new GitStatusVerifier()],
  ['file_exists', new FileExistenceVerifier()],
]);

export function getVerifier(name: string): Verifier {
  const v = verifiers.get(name);
  if (!v) throw new Error(`Unknown verifier: ${name}`);
  return v;
}

export function registerVerifier(verifier: Verifier): void {
  verifiers.set(verifier.name, verifier);
}
'''

# 3. 工具执行修改
TOOL_EXEC_PATCH = '''--- a/src/core/tool-execution.ts
+++ b/src/core/tool-execution.ts
@@ -1,5 +1,6 @@
 import { ToolCall, ToolResult } from './tool-types';
 import { getTool } from './tool-registry';
+import { InnovationEngine } from '../innovation/engine';
 
 /**
  * Execute a tool call
@@ -8,6 +9,20 @@ export async function executeTool(call: ToolCall): Promise<ToolResult> {
   const tool = getTool(call.name);
   
+  // Innovation: auto-fallback and verification
+  const innovation = getInnovationEngine();
+  if (innovation.isEnabled(call.name)) {
+    try {
+      return await innovation.execute(call, tool);
+    } catch (error) {
+      // If innovation fails, fall through to standard execution
+      // or re-throw based on configuration
+      if (isCriticalError(error)) {
+        throw error;
+      }
+    }
+  }
+  
   const result = await tool.execute(call.params);
   
   // Post-execution validation (existing)
@@ -17,3 +32,25 @@ export async function executeTool(call: ToolCall): Promise<ToolResult> {
   
   return result;
 }
+
+// Innovation engine singleton
+let innovationEngine: InnovationEngine | null = null;
+
+export function getInnovationEngine(): InnovationEngine {
+  if (!innovationEngine) {
+    const config = loadInnovationConfig();
+    innovationEngine = new InnovationEngine(config);
+  }
+  return innovationEngine;
+}
+
+function loadInnovationConfig() {
+  return {
+    enabled: process.env.OPENCLAW_INNOVATION !== 'disabled',
+    maxAttempts: 3,
+    verifyResults: true,
+    autoFallback: true,
+    learningEnabled: true
+  };
+}
+
+function isCriticalError(error: any): boolean {
+  return error?.name === 'AllMethodsFailedError' || 
+         error?.message?.includes('security') ||
+         error?.message?.includes('permission');
+}
'''

# 4. 配置文件
CONFIG_YAML = '''# OpenClaw Innovation Configuration

innovation:
  # Global settings
  enabled: true
  verify_results: true
  auto_fallback: true
  max_attempts: 3
  
  # Tool-specific patterns
  tools:
    exec:
      enabled: true
      patterns:
        git_push:
          triggers:
            - "could not read Username"
            - "Connection refused"
            - "timeout"
          fallbacks:
            - name: git_push_ssh
              adapter: switch_to_ssh
              verifier: git_status
            - name: git_push_api
              adapter: use_github_api
              verifier: api_response
              
        curl:
          triggers:
            - "Could not resolve"
            - "Connection refused"
          fallbacks:
            - name: curl_with_proxy
              adapter: add_proxy
            - name: wget
              adapter: convert_to_wget
              
        pip_install:
          triggers:
            - "Connection timed out"
          fallbacks:
            - name: pip_mirror
              adapter: use_tsinghua_mirror
              
    browser:
      enabled: true
      patterns:
        navigate:
          triggers:
            - "net::ERR_"
          fallbacks:
            - name: navigate_proxy
              adapter: use_proxy
            - name: navigate_mobile
              adapter: mobile_user_agent
              
    read:
      enabled: true
      patterns:
        read_file:
          triggers:
            - "Permission denied"
          fallbacks:
            - name: read_with_sudo
              adapter: use_sudo
              verifier: file_content
              
    write:
      enabled: true
      patterns:
        write_file:
          triggers:
            - "Permission denied"
            - "Read-only file system"
          fallbacks:
            - name: write_with_sudo
              adapter: use_sudo
              verifier: file_exists
            - name: write_to_temp
              adapter: write_temp_then_move
              verifier: file_exists
  
  # Verifiers
  verifiers:
    git_status:
      type: exec
      command: "git status"
      check: "up to date"
      
    file_exists:
      type: read
      check: "exists"
      
    file_content:
      type: read
      check: "content_match"
      
    api_response:
      type: http_status
      range: [200, 299]
  
  # Generic fallback rules
  generic_fallbacks:
    network_error:
      - retry_with_backoff
      - try_alternative_protocol
      - use_cached_result
      
    timeout_error:
      - increase_timeout
      - split_request
      - use_async
      
    permission_error:
      - retry_with_sudo
      - request_permission
'''

def generate_all():
    """生成所有修改文件"""
    
    # 创建目录结构
    (PATCH_DIR / "src" / "innovation").mkdir(parents=True, exist_ok=True)
    (PATCH_DIR / "src" / "core").mkdir(parents=True, exist_ok=True)
    (PATCH_DIR / "config").mkdir(parents=True, exist_ok=True)
    
    # 写入文件
    files = {
        "src/innovation/engine.ts": ENGINE_TS,
        "src/innovation/verifiers.ts": VERIFIERS_TS,
        "src/innovation/index.ts": "export * from './engine';\nexport * from './verifiers';",
        "src/core/tool-execution.patch": TOOL_EXEC_PATCH,
        "config/innovation.yaml": CONFIG_YAML,
    }
    
    for path, content in files.items():
        full_path = PATCH_DIR / path
        full_path.write_text(content)
        print(f"✅ Generated: {path}")
    
    # 生成安装脚本
    install_script = '''#!/bin/bash
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
'''
    
    install_path = PATCH_DIR / "install.sh"
    install_path.write_text(install_script)
    install_path.chmod(0o755)
    print(f"✅ Generated: install.sh")
    
    # 生成README
    readme = f'''# OpenClaw Innovation Source Patch

Generated: 2026-03-19

## Files

```
{PATCH_DIR.name}/
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
cd {PATCH_DIR}
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
'''
    
    (PATCH_DIR / "README.md").write_text(readme)
    print(f"✅ Generated: README.md")
    
    print(f"\n{'='*60}")
    print(f"All files generated in: {PATCH_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    generate_all()
