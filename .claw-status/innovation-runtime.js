const { execSync } = require('child_process');
console.error('[Innovation] Runtime loaded ✅');

const originalExecSync = require('child_process').execSync;
require('child_process').execSync = function(command, options) {
  if (command.includes('git push') && !command.includes('ssh')) {
    try {
      return originalExecSync(command, options);
    } catch (error) {
      if (error.message.includes('could not read Username')) {
        console.error('[Innovation] Auto-switching to SSH...');
        const cwd = options?.cwd || process.cwd();
        originalExecSync('git remote set-url origin git@github.com:mingking00/wdai.git', { cwd, stdio: 'pipe' });
        return originalExecSync('git push origin master', { cwd, stdio: 'pipe', encoding: 'utf8' });
      }
      throw error;
    }
  }
  return originalExecSync(command, options);
};
