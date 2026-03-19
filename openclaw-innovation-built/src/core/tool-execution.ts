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
