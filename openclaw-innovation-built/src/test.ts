import { executeTool, registerTool } from './index';
import { Tool } from './core/tool-types';

async function test() {
  console.log('Testing OpenClaw Innovation Engine...\n');
  
  // Register a mock exec tool
  const execTool: Tool = {
    name: 'exec',
    execute: async (params) => {
      console.log(`Executing: ${params.command}`);
      
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
      console.log(`   From: ${result.metadata.from}`);
      console.log(`   To: ${result.metadata.to}`);
    }
  } catch (error) {
    console.error('\n❌ FAILED:', error);
  }
}

test();
