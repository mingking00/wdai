/**
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
