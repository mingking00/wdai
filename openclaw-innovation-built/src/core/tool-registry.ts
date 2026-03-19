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
