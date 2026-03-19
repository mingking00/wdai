/**
 * OpenClaw Innovation Loader (ESM Hook)
 * 真正的底层模块加载钩子 - 简化版
 */

console.error('[Innovation] Bottom-layer module hook active 🔧');

// Simple interception at the loader level
export async function resolve(specifier, context, nextResolve) {
  return nextResolve(specifier, context);
}

export async function load(url, context, nextLoad) {
  const result = await nextLoad(url, context);
  
  // Log module loading (for debugging)
  if (url.includes('child_process')) {
    console.error('[Innovation] Intercepted child_process loading');
  }
  
  return result;
}
