#!/bin/bash
# OpenClaw Innovation - 本地构建脚本
# 创建最小可运行的OpenClaw开发环境

set -e

WORKSPACE="/root/.openclaw/workspace"
PATCH_DIR="$WORKSPACE/.patches/openclaw-source"
BUILD_DIR="/opt/openclaw-innovation"

echo "=========================================="
echo "OpenClaw Innovation - 本地构建"
echo "=========================================="
echo ""

# 创建构建目录
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# 创建最小项目结构
echo "1. 创建项目结构..."
mkdir -p src/{core,innovation,utils,config} dist

# 复制我们的创新引擎
echo "2. 复制创新引擎..."
cp $PATCH_DIR/src/innovation/*.ts src/innovation/

# 创建简化版工具执行文件
cat > src/core/tool-execution.ts << 'ENDOFFILE'
import { ToolCall, ToolResult } from './tool-types';
import { getTool } from './tool-registry';
import { InnovationEngine } from '../innovation/engine';

let innovationEngine: InnovationEngine | null = null;

export async function executeTool(call: ToolCall): Promise<ToolResult> {
  const tool = getTool(call.name);
  
  // Innovation layer
  const engine = getInnovationEngine();
  if (engine.isEnabled(call.name)) {
    try {
      return await engine.execute(call, tool);
    } catch (error) {
      // Fall through to standard execution on critical errors
      if (isCriticalError(error)) throw error;
    }
  }
  
  return await tool.execute(call.params);
}

function getInnovationEngine(): InnovationEngine {
  if (!innovationEngine) {
    innovationEngine = new InnovationEngine({
      enabled: process.env.OPENCLAW_INNOVATION !== 'disabled',
      maxAttempts: 3,
      verifyResults: true,
      autoFallback: true,
      learningEnabled: true
    });
  }
  return innovationEngine;
}

function isCriticalError(error: any): boolean {
  return error?.message?.includes('security') || 
         error?.message?.includes('permission');
}
ENDOFFILE

# 创建类型定义
cat > src/core/tool-types.ts << 'ENDOFFILE'
export interface ToolCall {
  name: string;
  params: any;
  sessionId?: string;
}

export interface ToolResult {
  success?: boolean;
  result?: any;
  error?: string;
  metadata?: any;
}

export interface Tool {
  name: string;
  execute(params: any): Promise<ToolResult>;
}
ENDOFFILE

# 创建工具注册表
cat > src/core/tool-registry.ts << 'ENDOFFILE'
import { Tool } from './tool-types';

const tools: Map<string, Tool> = new Map();

export function registerTool(name: string, tool: Tool): void {
  tools.set(name, tool);
}

export function getTool(name: string): Tool {
  const tool = tools.get(name);
  if (!tool) throw new Error(`Tool not found: ${name}`);
  return tool;
}

export function listTools(): string[] {
  return Array.from(tools.keys());
}
ENDOFFILE

# 创建logger
cat > src/utils/logger.ts << 'ENDOFFILE'
export const logger = {
  debug: (msg: string) => console.log(`[DEBUG] ${msg}`),
  info: (msg: string) => console.log(`[INFO] ${msg}`),
  warn: (msg: string) => console.warn(`[WARN] ${msg}`),
  error: (msg: string) => console.error(`[ERROR] ${msg}`),
};
ENDOFFILE

# 复制并修复创新引擎（移除外部依赖）
echo "3. 适配创新引擎..."
cat > src/innovation/engine.ts << 'ENDOFFILE'
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
  execute?: (params: any) => Promise<any>;
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
    return true;
  }

  async execute(call: ToolCall, tool: Tool): Promise<ToolResult> {
    const key = \`\${call.name}:\${this.extractMethod(call)}\`;
    
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
      throw new Error(\`No fallbacks for \${key}\`);
    }

    for (const fallback of pattern.fallbackChain) {
      try {
        let result;
        if (fallback.execute) {
          result = await fallback.execute(call.params);
        } else {
          result = await tool.execute(call.params);
        }
        
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
    return result.success !== false && result.error == null;
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
    // Load git push pattern
    this.patterns.set('exec:git', {
      tool: 'exec',
      method: 'git',
      triggerErrors: ['could not read Username', 'Connection refused'],
      fallbackChain: [
        {
          name: 'git_ssh',
          execute: async (params) => {
            const { execSync } = require('child_process');
            const cwd = params.cwd || '/root/.openclaw/workspace';
            
            // Switch to SSH
            execSync('git remote set-url origin git@github.com:mingking00/wdai.git', {
              cwd,
              stdio: 'pipe'
            });
            
            // Push
            execSync('git push origin master', { cwd, stdio: 'pipe' });
            
            return { success: true };
          }
        }
      ],
      verifier: 'git_status'
    });
  }

  getStats(): any {
    return Object.fromEntries(this.stats);
  }
}
ENDOFFILE

# 创建验证器
cat > src/innovation/verifiers.ts << 'ENDOFFILE'
import { ToolResult } from '../core/tool-types';

export interface Verifier {
  name: string;
  verify(result: ToolResult): Promise<boolean>;
}

const verifiers: Map<string, Verifier> = new Map();

export function getVerifier(name: string): Verifier {
  const v = verifiers.get(name);
  if (!v) throw new Error(\`Unknown verifier: \${name}\`);
  return v;
}

export function registerVerifier(verifier: Verifier): void {
  verifiers.set(verifier.name, verifier);
}
ENDOFFILE

# 创建导出文件
cat > src/innovation/index.ts << 'ENDOFFILE'
export * from './engine';
export * from './verifiers';
ENDOFFILE

# 创建主入口
cat > src/index.ts << 'ENDOFFILE'
export { executeTool } from './core/tool-execution';
export { registerTool, getTool, listTools } from './core/tool-registry';
export { InnovationEngine } from './innovation/engine';
export type { ToolCall, ToolResult, Tool } from './core/tool-types';
ENDOFFILE

# 创建package.json
cat > package.json << 'ENDOFFILE'
{
  "name": "openclaw-innovation",
  "version": "1.0.0",
  "description": "OpenClaw with Innovation Engine",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "test": "node dist/test.js"
  },
  "dependencies": {},
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
ENDOFFILE

# 创建tsconfig.json
cat > tsconfig.json << 'ENDOFFILE'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true
  },
  "include": ["src/**/*"]
}
ENDOFFILE

# 创建测试文件
cat > src/test.ts << 'ENDOFFILE'
import { executeTool, registerTool } from './index';
import { Tool } from './core/tool-types';

async function test() {
  console.log('Testing OpenClaw Innovation Engine...\n');
  
  // Register a mock exec tool
  const execTool: Tool = {
    name: 'exec',
    execute: async (params) => {
      console.log(\`Executing: \${params.command}\`);
      
      // Simulate git push failure
      if (params.command.includes('git push') && !params.useSsh) {
        throw new Error('could not read Username for https://github.com');
      }
      
      return { success: true, output: 'Success!' };
    }
  };
  
  registerTool('exec', execTool);
  
  // Test with innovation
  try {
    const result = await executeTool({
      name: 'exec',
      params: { command: 'git push origin master' }
    });
    
    console.log('\nResult:', JSON.stringify(result, null, 2));
    
    if (result.metadata?.autoFallback) {
      console.log('\n✅ SUCCESS: Auto-fallback worked!');
      console.log(\`   From: \${result.metadata.from}\`);
      console.log(\`   To: \${result.metadata.to}\`);
    }
  } catch (error) {
    console.error('\n❌ FAILED:', error);
  }
}

test();
ENDOFFILE

echo "4. 项目结构:"
find src -type f | head -20

echo ""
echo "=========================================="
echo "项目创建完成: $BUILD_DIR"
echo "=========================================="
echo ""
echo "下一步:"
echo "  cd $BUILD_DIR"
echo "  npm install"
echo "  npm run build"
echo "  npm test"
