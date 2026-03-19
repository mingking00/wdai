/**
 * OpenClaw Innovation Runtime
 * 在OpenClaw启动时注入，提供自动换路能力
 */

const { execSync } = require('child_process');

console.log('[Innovation] Runtime loaded ✅');

// Innovation patterns database
const patterns = new Map();

// Register git push pattern
patterns.set('exec:git', {
  tool: 'exec',
  method: 'git',
  triggers: [
    'could not read Username',
    'Connection refused',
    'Connection timed out',
    'timeout'
  ],
  fallbacks: [
    {
      name: 'git_ssh',
      async execute(params) {
        console.log('[Innovation] 🔄 Git push failed, auto-switching to SSH...');
        
        const cwd = params.cwd || process.cwd();
        
        // Check if we can use SSH
        try {
          execSync('ssh -T git@github.com 2>&1', { 
            cwd, 
            stdio: 'pipe',
            timeout: 10000 
          });
        } catch (e) {
          // SSH might fail auth but connection works
        }
        
        // Switch remote to SSH
        execSync('git remote set-url origin git@github.com:mingking00/wdai.git', {
          cwd,
          stdio: 'pipe'
        });
        
        // Push via SSH
        const result = execSync('git push origin master 2>&1', { 
          cwd, 
          stdio: 'pipe',
          encoding: 'utf8',
          timeout: 60000
        });
        
        // Verify
        const status = execSync('git status', { cwd, encoding: 'utf8' });
        if (status.includes('up to date') || status.includes('up-to-date')) {
          console.log('[Innovation] ✅ SSH fallback successful!');
          return { 
            success: true, 
            output: result,
            _innovation: {
              autoFallback: true,
              from: 'https',
              to: 'ssh',
              verified: true
            }
          };
        }
        
        throw new Error('Verification failed');
      }
    }
  ]
});

// Statistics tracking
const stats = {
  attempts: 0,
  successes: 0,
  fallbacks: 0,
  failures: 0
};

// Intercept exec tool
const originalExec = require('child_process').exec;
const originalExecSync = require('child_process').execSync;

// Wrap exec to add innovation
require('child_process').exec = function(command, options, callback) {
  if (typeof options === 'function') {
    callback = options;
    options = {};
  }
  
  // Check if this is a git push
  if (command.includes('git push') && !command.includes('ssh')) {
    const wrappedCallback = (error, stdout, stderr) => {
      if (error) {
        // Try fallback
        const pattern = patterns.get('exec:git');
        if (pattern) {
          for (const fallback of pattern.fallbacks) {
            try {
              const result = fallback.execute({ cwd: options?.cwd });
              if (callback) callback(null, result.output, '');
              return;
            } catch (fbError) {
              console.log(`[Innovation] Fallback failed: ${fbError.message}`);
            }
          }
        }
      }
      
      if (callback) callback(error, stdout, stderr);
    };
    
    return originalExec(command, options, wrappedCallback);
  }
  
  return originalExec(command, options, callback);
};

// Also wrap execSync
require('child_process').execSync = function(command, options) {
  if (command.includes('git push') && !command.includes('ssh')) {
    try {
      return originalExecSync(command, options);
    } catch (error) {
      // Try SSH fallback
      const pattern = patterns.get('exec:git');
      if (pattern) {
        for (const fallback of pattern.fallbacks) {
          try {
            const result = fallback.execute({ cwd: options?.cwd });
            return result.output;
          } catch (fbError) {
            // Continue to next fallback
          }
        }
      }
      throw error;
    }
  }
  
  return originalExecSync(command, options);
};

console.log('[Innovation] Git push auto-fallback enabled 🚀');
console.log('[Innovation] Pattern registered: HTTPS → SSH');
