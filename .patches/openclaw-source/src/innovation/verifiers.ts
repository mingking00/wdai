/**
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
