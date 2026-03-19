import type { AnyAgentTool } from "openclaw/plugin-sdk";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";

// 工具名到方法类型的映射
const TOOL_METHOD_MAP: Record<string, string> = {
  web_search: "web_search",
  web_fetch: "web_fetch",
  browser: "browser_automation",
  exec: "bash_exec",
  read: "file_ops",
  write: "file_ops",
  edit: "file_ops",
  pdf: "pdf_ops",
  tts: "tts_ops",
  image: "image_ops",
  canvas: "canvas_ops",
  cron: "cron_ops",
  sessions: "sessions_ops",
  nodes: "nodes_ops",
  message: "message_ops",
};

// 状态文件路径
let stateFilePath: string;
let maxFailures: number;

// 读取状态
function readState(): Record<string, { count: number; firstFail: string; lastFail: string }> {
  try {
    const fs = require("node:fs");
    if (!fs.existsSync(stateFilePath)) {
      return {};
    }
    const content = fs.readFileSync(stateFilePath, "utf-8");
    return JSON.parse(content);
  } catch {
    return {};
  }
}

// 写入状态
function writeState(state: Record<string, any>) {
  try {
    const fs = require("node:fs");
    const path = require("node:path");
    const dir = path.dirname(stateFilePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(stateFilePath, JSON.stringify(state, null, 2));
  } catch (err) {
    console.error("[InnovationTracker] Failed to write state:", err);
  }
}

// 检测方法类型
function detectMethod(toolName: string): string {
  // 直接匹配
  if (TOOL_METHOD_MAP[toolName]) {
    return TOOL_METHOD_MAP[toolName];
  }
  
  // 关键词匹配
  if (toolName.includes("github") || toolName.includes("git")) return "github_api";
  if (toolName.includes("web_search") || toolName.includes("search")) return "web_search";
  if (toolName.includes("fetch") || toolName.includes("curl")) return "web_fetch";
  if (toolName.includes("browser") || toolName.includes("page")) return "browser_automation";
  if (toolName.includes("exec") || toolName.includes("bash") || toolName.includes("shell")) return "bash_exec";
  
  return toolName;
}

// 检查是否锁定
function isLocked(method: string, taskHint?: string): boolean {
  const state = readState();
  const key = taskHint ? `${taskHint}:${method}` : method;
  
  // 检查具体任务
  if (state[key] && state[key].count >= maxFailures) {
    return true;
  }
  
  // 检查该方法的所有记录
  for (const [k, v] of Object.entries(state)) {
    if (k.endsWith(`:${method}`) && v.count >= maxFailures) {
      return true;
    }
  }
  
  return false;
}

// 记录失败
function recordFailure(method: string, taskHint?: string): { count: number; locked: boolean } {
  const state = readState();
  const key = taskHint ? `${taskHint}:${method}` : method;
  const now = new Date().toISOString();
  
  if (!state[key]) {
    state[key] = { count: 0, firstFail: now, lastFail: now };
  }
  
  state[key].count += 1;
  state[key].lastFail = now;
  
  writeState(state);
  
  return {
    count: state[key].count,
    locked: state[key].count >= maxFailures
  };
}

// 重置计数器
function resetCounter(method: string, taskHint?: string) {
  const state = readState();
  const key = taskHint ? `${taskHint}:${method}` : method;
  
  if (state[key]) {
    delete state[key];
    writeState(state);
  }
}

// 主注册函数
export default async function register(api: OpenClawPluginApi) {
  // 读取配置
  const config = api.pluginConfig || {};
  stateFilePath = config.stateFile || ".claw-status/innovation_state.json";
  maxFailures = config.maxFailures || 3;
  
  // 确保路径是绝对路径
  if (!stateFilePath.startsWith("/")) {
    const path = require("node:path");
    stateFilePath = path.resolve(api.runtime.stateDir || ".", "..", stateFilePath);
  }
  
  console.log(`[InnovationTracker] Initialized with state file: ${stateFilePath}`);
  console.log(`[InnovationTracker] Max failures before lock: ${maxFailures}`);
  
  // 注册管理命令
  api.on("system_command", async (event, ctx) => {
    const cmd = event.command;
    
    if (cmd === "innovation_status") {
      const state = readState();
      const locked = Object.entries(state)
        .filter(([k, v]) => v.count >= maxFailures)
        .map(([k, v]) => ({ method: k, count: v.count }));
      
      return {
        status: "ok",
        locked_methods: locked,
        total_tracked: Object.keys(state).length
      };
    }
    
    if (cmd === "innovation_unlock") {
      const method = event.args?.method;
      if (method) {
        resetCounter(method);
        console.log(`[InnovationTracker] Unlocked: ${method}`);
        return { status: "ok", message: `Unlocked ${method}` };
      } else {
        // 解锁所有
        const fs = require("node:fs");
        if (fs.existsSync(stateFilePath)) {
          fs.writeFileSync(stateFilePath, "{}");
        }
        console.log("[InnovationTracker] All locks cleared");
        return { status: "ok", message: "All locks cleared" };
      }
    }
    
    return undefined; // 不处理其他命令
  });
  
  // 注册 before_tool_call Hook - 检查锁定
  api.on("before_tool_call", async (event, ctx) => {
    const method = detectMethod(event.toolName);
    
    if (isLocked(method)) {
      console.error(`[InnovationTracker] 🔒 BLOCKED: ${method} is locked after ${maxFailures} failures`);
      return {
        block: true,
        blockReason: `🔒 ${method} 已被锁定（${maxFailures}次失败）。这是强制创新机制，必须换用其他方法！`
      };
    }
    
    // 记录调用开始（用于调试）
    console.log(`[InnovationTracker] → ${event.toolName} (${method})`);
    
    return undefined; // 允许执行
  });
  
  // 注册 after_tool_call Hook - 记录结果
  api.on("after_tool_call", async (event, ctx) => {
    const method = detectMethod(event.toolName);
    
    if (event.error) {
      // 记录失败
      const result = recordFailure(method);
      console.error(`[InnovationTracker] ✗ ${event.toolName} FAILED (${result.count}/${maxFailures})`);
      
      if (result.locked) {
        console.error(`[InnovationTracker] 🚨 LOCKED: ${method} is now locked!`);
      }
    } else {
      // 记录成功，重置计数器
      resetCounter(method);
      console.log(`[InnovationTracker] ✓ ${event.toolName} SUCCESS (counter reset)`);
    }
  });
  
  console.log("[InnovationTracker] Plugin registered successfully");
}
