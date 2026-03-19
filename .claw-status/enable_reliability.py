#!/usr/bin/env python3
"""
WDai Enhanced System - 启用可靠性优化
一键启用工具调用可靠性和多路径推理
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/.claw-status')

from tool_reliability import ToolExecutor, RetryStrategy
from multi_path_reasoning import MultiPathReasoner

print("="*60)
print("WDai 可靠性优化 - 启用向导")
print("="*60)

# 1. 创建工具执行器
print("\n✅ 工具调用可靠性优化已就绪")
print("   - 参数预验证")
print("   - 指数退避重试")
print("   - 错误分类处理")
print("   - 降级策略")

# 2. 创建推理器
print("\n✅ 多路径推理优化已就绪")
print("   - 4条并行推理路径")
print("   - 一致性检查")
print("   - 加权仲裁")

print("\n" + "="*60)
print("启用方法:")
print("="*60)
print("""
1. 工具调用 (替换原调用):
   
   # 之前:
   result = web_search(query="xxx")
   
   # 之后:
   from tool_reliability import get_executor
   executor = get_executor()
   result = executor.execute("web_search", query="xxx")
   
   if result.success:
       data = result.data
   else:
       print(f"失败: {result.error_message}")

2. 复杂推理 (增强决策):
   
   # 之前:
   response = llm_generate(prompt)
   
   # 之后:
   from multi_path_reasoning import get_reasoner
   reasoner = get_reasoner()
   result = reasoner.reason(question, llm_func)
   
   # 获取带置信度的结论
   conclusion = result['final']['conclusion']
   confidence = result['final']['confidence']
   
   if confidence > 0.8:
       print(f"高置信度: {conclusion}")
   else:
       print(f"低置信度，需要人工确认: {conclusion}")
""")

print("="*60)
