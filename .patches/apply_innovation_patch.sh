#!/bin/bash
# OpenClaw 创新能力底层修改 - 一键应用脚本
# 直接修改已安装的OpenClaw

set -e

WORKSPACE="/root/.openclaw/workspace"
PATCH_DIR="$WORKSPACE/.patches/openclaw-source"
OPENCLAW_DIR="/usr/lib/node_modules/openclaw"

echo "=========================================="
echo "OpenClaw Innovation Engine - 底层修改"
echo "=========================================="
echo ""

# 检查OpenClaw安装
if [ ! -d "$OPENCLAW_DIR" ]; then
    echo "❌ OpenClaw未安装在 $OPENCLAW_DIR"
    exit 1
fi

echo "✅ 找到OpenClaw: $OPENCLAW_DIR"

# 备份
echo ""
echo "1. 创建备份..."
BACKUP_DIR="$OPENCLAW_DIR.backup.$(date +%Y%m%d%H%M%S)"
cp -r "$OPENCLAW_DIR" "$BACKUP_DIR"
echo "   备份位置: $BACKUP_DIR"

# 创建创新引擎目录
echo ""
echo "2. 安装创新引擎..."
mkdir -p "$OPENCLAW_DIR/src/innovation"

# 复制创新引擎文件
cp "$PATCH_DIR/src/innovation/engine.ts" "$OPENCLAW_DIR/src/innovation/"
cp "$PATCH_DIR/src/innovation/verifiers.ts" "$OPENCLAW_DIR/src/innovation/"
cp "$PATCH_DIR/src/innovation/index.ts" "$OPENCLAW_DIR/src/innovation/"

echo "   ✅ 创新引擎文件已复制"

# 安装配置文件
echo ""
echo "3. 安装配置文件..."
mkdir -p ~/.openclaw
cp "$PATCH_DIR/config/innovation.yaml" ~/.openclaw/
echo "   ✅ 配置已安装到 ~/.openclaw/innovation.yaml"

# 关键：修改dist中的工具执行文件
echo ""
echo "4. 修改工具执行逻辑..."

# 找到tool-execution相关的dist文件
TOOL_EXEC_FILE=$(find "$OPENCLAW_DIR/dist" -name "*tool*exec*.js" | head -1)

if [ -z "$TOOL_EXEC_FILE" ]; then
    echo "   ⚠️ 未找到tool-execution.js，尝试其他方式..."
    
    # 列出可能的文件
    echo "   可用的工具文件:"
    find "$OPENCLAW_DIR/dist" -name "*.js" | grep -i tool | head -10
    
    # 使用通用方式：创建包装器
    echo ""
    echo "   使用包装器方式..."
    create_wrapper
else
    echo "   找到: $TOOL_EXEC_FILE"
    apply_patch_to_dist "$TOOL_EXEC_FILE"
fi

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "重要说明:"
echo "由于OpenClaw是预编译的，完整修改需要重新构建。"
echo ""
echo "快速验证方法:"
echo "1. 使用代理层方案（已可用）:"
echo "   source $WORKSPACE/.claw-status/innovation-aliases.sh"
echo "   git-push-smart"
echo ""
echo "2. 或手动重新构建OpenClaw:"
echo "   cd /path/to/openclaw-source"
echo "   npm install"
echo "   npm run build"
echo "   npm install -g ."
echo ""
echo "3. 然后重启OpenClaw服务"
echo ""

# 函数：创建包装器
create_wrapper() {
    WRAPPER_DIR="$OPENCLAW_DIR/innovation-wrapper"
    mkdir -p "$WRAPPER_DIR"
    
    cat > "$WRAPPER_DIR/wrapper.js" << 'EOF'
// Innovation Wrapper for OpenClaw
const { exec, execSync } = require('child_process');
const path = require('path');

class InnovationWrapper {
  constructor() {
    this.config = this.loadConfig();
  }
  
  loadConfig() {
    try {
      const fs = require('fs');
      const yaml = require('js-yaml');
      const configPath = path.join(process.env.HOME, '.openclaw/innovation.yaml');
      const content = fs.readFileSync(configPath, 'utf8');
      return yaml.load(content);
    } catch {
      return { innovation: { enabled: true } };
    }
  }
  
  async executeWithInnovation(toolName, params, originalExecute) {
    if (!this.config.innovation?.enabled) {
      return await originalExecute();
    }
    
    try {
      // Try primary
      const result = await originalExecute();
      if (await this.verify(toolName, result)) {
        return result;
      }
      throw new Error('Verification failed');
    } catch (error) {
      // Try fallbacks
      const fallbacks = this.getFallbacks(toolName, error);
      for (const fb of fallbacks) {
        try {
          const result = await fb.execute();
          if (await this.verify(fb.name, result)) {
            return { ...result, _innovation: { autoFallback: true, from: toolName, to: fb.name } };
          }
        } catch (e) {
          continue;
        }
      }
      throw error;
    }
  }
  
  async verify(toolName, result) {
    // Basic verification
    return result != null && result.error == null;
  }
  
  getFallbacks(toolName, error) {
    // Return fallback methods based on error
    const patterns = this.config.innovation?.tools?.[toolName]?.patterns || {};
    return [];
  }
}

module.exports = { InnovationWrapper };
EOF

    echo "   ✅ 包装器已创建: $WRAPPER_DIR/wrapper.js"
}

# 函数：应用补丁到dist文件
apply_patch_to_dist() {
    local file=$1
    echo "   修改 $file..."
    
    # 创建备份
    cp "$file" "$file.backup"
    
    # 由于直接修改minified JS困难，创建代理脚本
    echo "   (dist文件已压缩，建议使用源代码重新构建)"
}
