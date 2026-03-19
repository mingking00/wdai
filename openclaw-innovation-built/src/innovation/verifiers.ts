import { ToolResult } from '../core/tool-types';

export interface Verifier {
  name: string;
  verify(result: ToolResult): Promise<boolean>;
}

const verifiers: Map<string, Verifier> = new Map();

export function getVerifier(name: string): Verifier {
  const v = verifiers.get(name);
  if (!v) throw new Error(`Unknown verifier: ${name}`);
  return v;
}

export function registerVerifier(verifier: Verifier): void {
  verifiers.set(verifier.name, verifier);
}
