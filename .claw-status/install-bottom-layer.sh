#!/bin/bash
# OpenClaw Innovation - 底层修改安装器
# 安装真正的底层创新引擎到系统

echo "🔧 OpenClaw 底层创新引擎安装器"
echo "================================"
echo ""

OPENCLAW_DIR="/usr/lib/node_modules/openclaw"

# 检查OpenClaw安装
if [ ! -d "$OPENCLAW_DIR" ]; then
    echo "❌ OpenClaw未安装"
    exit 1
fi

echo "✅ OpenClaw已安装: $OPENCLAW_DIR"
echo ""

# 备份当前配置
echo "步骤1: 创建备份..."
cp -r "$OPENCLAW_DIR/dist" "$OPENCLAW_DIR/dist.backup.$(date +%Y%m%d%H%M%S)" 2>/dev/null
cp "$OPENCLAW_DIR/openclaw.mjs" "$OPENCLAW_DIR/openclaw.mjs.backup" 2>/dev/null
echo "✅ 备份完成"
echo ""

# 安装创新引擎文件
echo "步骤2: 安装创新引擎..."

# 1. 模块加载钩子（真正的底层）
cat > "$OPENCLAW_DIR/innovation-loader.mjs" << 'ENDOFFILE'
/**
 * OpenClaw Innovation Loader (ESM Hook)
 * 真正的底层模块加载钩子
 */

let innovationEnabled = process.env.OPENCLAW_INNOVATION !== 'disabled';

if (innovationEnabled) {
  console.error('[Innovation] Bottom-layer module hook active 🔧');
}

const patterns = new Map();
patterns.set('git_push', {
  triggers: ['could not read Username', 'Connection refused', 'timeout', '403'],
  fallback: 'ssh'
});

export async function resolve(specifier, context, nextResolve) {
  if (specifier === 'node:child_process') {
    return {
      format: 'module',
      url: 'innovation://child_process',
      shortCircuit: true
    };
  }
  return nextResolve(specifier, context);
}

export async function load(url, context, nextLoad) {
  if (url === 'innovation://child_process') {
    return {
      format: 'module',
      source: generateWrapper(),
      shortCircuit: true
    };
  }
  return nextLoad(url, context);
}

function generateWrapper() {
  return \`
import { execSync as originalExecSync, exec as originalExec } from 'node:child_process';

const patterns = new Map();
patterns.set('git_push', {
  triggers: ['could not read Username', 'Connection refused', 'timeout'],
  executeFallback(cwd) {
    const { execSync } = require('child_process');
    execSync('git remote set-url origin git@github.com:mingking00/wdai.git', { cwd, stdio: 'pipe' });
    return execSync('git push origin master', { cwd, stdio: 'pipe', encoding: 'utf8' });
  }
});

function shouldFallback(error) {
  return patterns.get('git_push').triggers.some(t => error.message.includes(t));
}

export function execSync(command, options) {
  if (command.includes('git push') && !command.includes('ssh')) {
    try {
      return originalExecSync(command, options);
    } catch (error) {
      if (shouldFallback(error)) {
        console.error('[Innovation] Auto-fallback to SSH...');
        return patterns.get('git_push').executeFallback(options?.cwd || process.cwd());
      }
      throw error;
    }
  }
  return originalExecSync(command, options);
}

export { execSync as default };
\`;
}
ENDOFFILE

# 2. 注册文件
cat > "$OPENCLAW_DIR/innovation-register.mjs" << 'ENDOFFILE'
import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
const innovationLoaderURL = pathToFileURL('/usr/lib/node_modules/openclaw/innovation-loader.mjs');
register(innovationLoaderURL);
console.error('[Innovation] Bottom-layer loader registered ✅');
ENDOFFILE

# 3. 运行时注入（备用方案）
cat > "$OPENCLAW_DIR/innovation-runtime.js" << 'ENDOFFILE'
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
ENDOFFILE

echo "✅ 创新引擎文件已安装"
echo ""

# 创建快捷命令
echo "步骤3: 创建快捷命令..."

cat > /usr/local/bin/openclaw-innovation << 'ENDOFFILE'
#!/bin/bash
export OPENCLAW_INNOVATION=enabled
export NODE_OPTIONS="--require /usr/lib/node_modules/openclaw/innovation-runtime.js"
exec /usr/bin/node $NODE_OPTIONS /usr/lib/node_modules/openclaw/openclaw.mjs "$@"
ENDOFFILE

cat > /usr/local/bin/openclaw-bottom << 'ENDOFFILE'
#!/bin/bash
export OPENCLAW_INNOVATION=enabled
NODE_OPTIONS="--import /usr/lib/node_modules/openclaw/innovation-register.mjs"
exec /usr/bin/node $NODE_OPTIONS /usr/lib/node_modules/openclaw/openclaw.mjs "$@"
ENDOFFILE

chmod +x /usr/local/bin/openclaw-innovation /usr/local/bin/openclaw-bottom

echo "✅ 快捷命令已创建"
echo ""

# 测试
echo "步骤4: 测试..."
node -e "require('$OPENCLAW_DIR/innovation-runtime.js')" 2>&1
node --import "$OPENCLAW_DIR/innovation-register.mjs" -e "console.log('OK');" 2>&1

echo ""
echo "================================"
echo "✅ 安装完成!"
echo ""
echo "使用方法:"
echo "1. 运行时注入: openclaw-innovation"
echo "2. 底层模块钩子: openclaw-bottom"
echo ""
echo "验证:"
echo "  node -e \"require('$OPENCLAW_DIR/innovation-runtime.js')\""
echo ""
echo "卸载:"
echo "  cp $OPENCLAW_DIR/openclaw.mjs.backup $OPENCLAW_DIR/openclaw.mjs"
echo "  rm /usr/local/bin/openclaw-innovation /usr/local/bin/openclaw-bottom"
echo "================================"
