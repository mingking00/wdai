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
