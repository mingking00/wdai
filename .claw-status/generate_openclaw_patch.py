#!/usr/bin/env python3
"""
OpenClaw 创新能力集成补丁

快速实施版本 - 修改现有系统
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

PATCH_CONTENT = """
// ============================================================================
// OpenClaw Innovation Patch
// 将以下代码插入到 OpenClaw 核心文件中
// ============================================================================

// ============================================================================
// 文件1: src/core/tool-router.ts (插入点: executeTool函数开头)
// ============================================================================

// 原代码:
// async function executeTool(toolName: string, params: any): Promise<Result> {
//     const tool = getTool(toolName);
//     return await tool.execute(params);
// }

// 新代码:
import { InnovationEngine } from '../innovation/engine';

const innovationEngine = new InnovationEngine();

async function executeTool(toolName: string, params: any, context?: any): Promise<Result> {
    const tool = getTool(toolName);
    
    // 检查是否启用创新能力
    if (innovationEngine.isEnabled(toolName, params)) {
        return await innovationEngine.execute(toolName, params, context);
    }
    
    // 标准执行路径
    return await tool.execute(params);
}

// ============================================================================
// 文件2: src/innovation/engine.ts (新建文件)
// ============================================================================

export interface InnovationResult {
    success: boolean;
    result: any;
    method: string;
    attempts: number;
    metadata?: {
        autoFallback?: boolean;
        from?: string;
        to?: string;
        verified?: boolean;
    };
}

export interface MethodPattern {
    tool: string;
    method: string;
    triggerErrors: string[];
    fallbackChain: string[];
    verifier?: string;
}

export class InnovationEngine {
    private patterns: Map<string, MethodPattern> = new Map();
    private stats: Map<string, any> = new Map();
    private config: any;
    
    constructor() {
        this.loadConfig();
        this.loadPatterns();
    }
    
    isEnabled(tool: string, params?: any): boolean {
        // 检查全局开关
        if (process.env.OPENCLAW_INNOVATION === 'disabled') {
            return false;
        }
        
        // 检查工具级别配置
        const toolConfig = this.config?.tools?.[tool];
        return toolConfig?.enabled !== false;
    }
    
    async execute(tool: string, params: any, context?: any): Promise<Result> {
        const method = this.extractMethod(tool, params);
        const key = `${tool}:${method}`;
        
        // 1. 执行主方法
        const startTime = Date.now();
        let result: any;
        let error: any;
        
        try {
            const toolInstance = getTool(tool);
            result = await toolInstance.execute(params);
            
            // 2. 验证结果
            if (await this.verify(tool, method, result)) {
                this.recordSuccess(key, Date.now() - startTime);
                return this.wrapResult(result, key, 1);
            }
            
            error = new Error('Verification failed');
        } catch (e) {
            error = e;
        }
        
        // 3. 记录失败
        this.recordFailure(key, error, Date.now() - startTime);
        
        // 4. 尝试备选方案
        const pattern = this.patterns.get(key);
        if (pattern) {
            return await this.tryFallbacks(pattern, params, context);
        }
        
        // 5. 通用备选
        return await this.tryGenericFallbacks(tool, method, params, error);
    }
    
    private async verify(tool: string, method: string, result: any): Promise<boolean> {
        const pattern = this.patterns.get(`${tool}:${method}`);
        if (!pattern?.verifier) return true; // 无验证器默认通过
        
        const verifier = getVerifier(pattern.verifier);
        return await verifier.verify(result);
    }
    
    private async tryFallbacks(
        pattern: MethodPattern, 
        params: any, 
        context?: any
    ): Promise<InnovationResult> {
        
        for (let i = 0; i < pattern.fallbackChain.length; i++) {
            const fallback = pattern.fallbackChain[i];
            
            try {
                const fbParams = this.adaptParams(params, fallback);
                const tool = getToolFromFallback(fallback);
                const result = await tool.execute(fbParams);
                
                if (await this.verifyFromFallback(fallback, result)) {
                    return this.wrapResult(result, fallback, i + 2, {
                        autoFallback: true,
                        from: `${pattern.tool}:${pattern.method}`,
                        to: fallback
                    });
                }
            } catch (e) {
                continue;
            }
        }
        
        throw new Error('All fallback methods failed');
    }
    
    private async tryGenericFallbacks(
        tool: string, 
        method: string, 
        params: any,
        originalError: any
    ): Promise<InnovationResult> {
        
        // 根据错误类型选择通用备选
        const errorType = this.classifyError(originalError);
        const fallbacks = this.config?.generic_fallbacks?.[errorType];
        
        if (!fallbacks) {
            throw originalError;
        }
        
        for (const fallback of fallbacks) {
            try {
                const result = await this.executeGenericFallback(fallback, tool, method, params);
                return this.wrapResult(result, fallback, 2, {
                    autoFallback: true,
                    generic: true
                });
            } catch (e) {
                continue;
            }
        }
        
        throw originalError;
    }
    
    private classifyError(error: any): string {
        const msg = error?.message || String(error);
        
        if (msg.includes('timeout') || msg.includes('ETIMEDOUT')) {
            return 'timeout_error';
        }
        if (msg.includes('ECONNREFUSED') || msg.includes('network')) {
            return 'network_error';
        }
        if (msg.includes('permission') || msg.includes('EACCES')) {
            return 'permission_error';
        }
        return 'unknown_error';
    }
    
    private recordSuccess(key: string, duration: number) {
        const stats = this.stats.get(key) || { attempts: 0, successes: 0, failures: 0 };
        stats.attempts++;
        stats.successes++;
        stats.lastSuccess = new Date().toISOString();
        stats.avgDuration = (stats.avgDuration || 0) * 0.9 + duration * 0.1;
        this.stats.set(key, stats);
    }
    
    private recordFailure(key: string, error: any, duration: number) {
        const stats = this.stats.get(key) || { attempts: 0, successes: 0, failures: 0 };
        stats.attempts++;
        stats.failures++;
        stats.lastError = error?.message;
        stats.consecutiveFailures = (stats.consecutiveFailures || 0) + 1;
        this.stats.set(key, stats);
    }
    
    private wrapResult(result: any, method: string, attempts: number, metadata?: any): Result {
        return {
            success: true,
            result,
            metadata: {
                innovation: true,
                method,
                attempts,
                ...metadata
            }
        };
    }
    
    private loadConfig() {
        const configPath = process.env.HOME + '/.openclaw/innovation.yaml';
        // 加载YAML配置
        this.config = loadYamlConfig(configPath);
    }
    
    private loadPatterns() {
        // 从数据库加载已知模式
        const patterns = loadPatternsFromDB();
        for (const p of patterns) {
            this.patterns.set(`${p.tool}:${p.method}`, p);
        }
    }
}

// ============================================================================
// 文件3: src/innovation/verifiers.ts (新建文件)
// ============================================================================

export interface Verifier {
    name: string;
    verify(result: any): Promise<boolean>;
}

export class GitStatusVerifier implements Verifier {
    name = 'git_status_check';
    
    async verify(result: any): Promise<boolean> {
        try {
            const { exec } = require('../tools/exec');
            const check = await exec.execute({ 
                command: 'git status',
                timeout: 5000 
            });
            return check.output?.includes('up to date') || 
                   check.output?.includes('up-to-date');
        } catch {
            return false;
        }
    }
}

export class FileExistenceVerifier implements Verifier {
    name = 'file_exists_check';
    
    async verify(result: any): Promise<boolean> {
        try {
            const { read } = require('../tools/read');
            await read.execute({ path: result.path });
            return true;
        } catch {
            return false;
        }
    }
}

export class HttpStatusVerifier implements Verifier {
    name = 'http_status_check';
    
    async verify(result: any): Promise<boolean> {
        return result.statusCode >= 200 && result.statusCode < 300;
    }
}

// 验证器注册表
const verifiers: Map<string, Verifier> = new Map([
    ['git_status_check', new GitStatusVerifier()],
    ['file_exists_check', new FileExistenceVerifier()],
    ['http_status_check', new HttpStatusVerifier()],
]);

export function getVerifier(name: string): Verifier {
    const v = verifiers.get(name);
    if (!v) throw new Error(`Unknown verifier: ${name}`);
    return v;
}

// ============================================================================
// 配置文件: ~/.openclaw/innovation.yaml
// ============================================================================
"""

CONFIG_YAML = """
# OpenClaw 创新能力配置
innovation:
  enabled: true
  
  # 执行策略
  execution:
    max_attempts: 3
    timeout_ms: 60000
    verify_results: true
    
  # 学习设置
  learning:
    enabled: true
    analysis_interval_minutes: 60
    min_samples_for_pattern: 3
    
  # 工具配置
  tools:
    exec:
      enabled: true
      patterns:
        git_push:
          fallbacks:
            - git_push_ssh
            - git_push_api
          verifier: git_status_check
          
        curl:
          fallbacks:
            - curl_with_proxy
            - wget
            - http_get
          verifier: http_status_check
          
        pip_install:
          fallbacks:
            - pip_install_mirror
            - pip_install_cache
    
    read:
      enabled: true
      patterns:
        read_file:
          fallbacks:
            - read_with_sudo
            - read_from_backup
          verifier: file_exists_check
    
    write:
      enabled: true
      patterns:
        write_file:
          fallbacks:
            - write_with_sudo
            - write_to_temp_then_move
          verifier: file_exists_check
    
    browser:
      enabled: true
      patterns:
        navigate:
          fallbacks:
            - navigate_with_proxy
            - navigate_mobile_useragent
          verifier: http_status_check
    
    web_search:
      enabled: true
      patterns:
        search:
          fallbacks:
            - search_with_cache
            - search_alternative_engine
  
  # 通用备选规则
  generic_fallbacks:
    timeout_error:
      - increase_timeout
      - split_request
    
    network_error:
      - retry_with_backoff
      - try_alternative_protocol
      - use_cached_result
    
    permission_error:
      - retry_with_sudo
      - request_permission
"""

def generate_patch():
    """生成补丁文件"""
    patch_dir = Path("/root/.openclaw/workspace/.patches")
    patch_dir.mkdir(exist_ok=True)
    
    # 保存代码补丁
    patch_file = patch_dir / "openclaw_innovation.patch"
    with open(patch_file, 'w') as f:
        f.write(PATCH_CONTENT)
    
    # 保存配置文件
    config_file = patch_dir / "innovation.yaml"
    with open(config_file, 'w') as f:
        f.write(CONFIG_YAML)
    
    print(f"✅ 补丁已生成:")
    print(f"   代码补丁: {patch_file}")
    print(f"   配置文件: {config_file}")
    
    return patch_dir


def print_installation_guide():
    """打印安装指南"""
    guide = """
# OpenClaw 创新能力集成 - 安装指南

## 1. 备份现有系统
```bash
cd /usr/lib/node_modules/openclaw
cp -r src src.backup.$(date +%Y%m%d)
```

## 2. 应用代码补丁
```bash
# 创建创新引擎目录
mkdir -p /usr/lib/node_modules/openclaw/src/innovation

# 复制引擎文件 (从patch中提取)
# 手动将 src/innovation/engine.ts 内容写入对应文件
# 手动将 src/innovation/verifiers.ts 内容写入对应文件

# 修改工具路由
cd /usr/lib/node_modules/openclaw/src/core
# 手动将 tool-router.ts 中的 executeTool 函数替换为补丁版本
```

## 3. 安装配置文件
```bash
mkdir -p ~/.openclaw
cp /root/.openclaw/workspace/.patches/innovation.yaml ~/.openclaw/
```

## 4. 安装依赖
```bash
cd /usr/lib/node_modules/openclaw
npm install js-yaml  # 用于解析YAML配置
```

## 5. 重启OpenClaw
```bash
# 如果是systemd服务
sudo systemctl restart openclaw

# 或者手动重启
openclaw restart
```

## 6. 验证安装
```bash
# 检查日志中是否有创新引擎加载信息
tail -f /var/log/openclaw.log | grep -i innovation

# 测试git推送
git push origin master
# 观察是否自动切换协议
```

## 7. 调试模式
```bash
export OPENCLAW_INNOVATION=debug
openclaw
```
"""
    print(guide)


if __name__ == "__main__":
    print("=" * 60)
    print("OpenClaw 创新能力集成补丁生成器")
    print("=" * 60)
    
    patch_dir = generate_patch()
    print()
    print_installation_guide()
    
    print("\n" + "=" * 60)
    print("下一步:")
    print("=" * 60)
    print(f"1. 查看补丁文件: ls -la {patch_dir}")
    print("2. 按照安装指南手动应用补丁")
    print("3. 重启OpenClaw验证")
