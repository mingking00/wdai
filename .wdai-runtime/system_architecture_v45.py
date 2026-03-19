#!/usr/bin/env python3
"""
wdai 完整系统架构 v4.5
外循环-内循环连接完整闭环

系统架构:
┌─────────────────────────────────────────────────────────────────────────┐
│                           wdai 完整系统 v4.5                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      外循环 (执行层)                              │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  AgentConductor (指挥家)                                   │  │    │
│  │  │  └── 观察系统 → 识别机会 → 创建任务队列                    │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  │                              ↓                                   │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  AgentExecutionEngine (执行引擎)                           │  │    │
│  │  │  ├── RealAgentExecutor                                    │  │    │
│  │  │  │   ├── Coder: 真实生成代码文件                         │  │    │
│  │  │  │   ├── Reviewer: 真实审查代码                          │  │    │
│  │  │  │   ├── Reflector: 真实分析数据                         │  │    │
│  │  │  │   └── Evolution: 真实更新系统                         │  │    │
│  │  │  ├── ParallelExecutor: 并行执行                          │  │    │
│  │  │  └── ConflictArbitrator: 冲突仲裁                       │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ↓ (IER连接器)                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     IER连接器 (桥接层)                           │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  外循环 → 内循环                                          │  │    │
│  │  │  ├── capture_execution(): 捕获执行数据                    │  │    │
│  │  │  ├── trigger_reflection(): 触发反思分析                  │  │    │
│  │  │  └── distill_experience(): 提炼经验                      │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  内循环 → 外循环                                          │  │    │
│  │  │  ├── retrieve_experiences(): 检索相关经验                │  │    │
│  │  │  └── inject_experience(): 注入Prompt                     │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      内循环 (反思进化层)                          │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  SRA-IER (Self-Reflection Agent)                          │  │    │
│  │  │  ├── Experience Acquisition: 经验获取                     │  │    │
│  │  │  ├── Experience Utilization: 经验利用                     │  │    │
│  │  │  ├── Experience Propagation: 经验传播                     │  │    │
│  │  │  └── Experience Elimination: 经验淘汰                     │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  │  ┌───────────────────────────────────────────────────────────┐  │    │
│  │  │  SEA-IER (System Evolution Agent)                         │  │    │
│  │  │  ├── Refactoring经验                                     │  │    │
│  │  │  ├── Code Pattern经验                                    │  │    │
│  │  │  ├── Design Decision经验                                 │  │    │
│  │  │  └── Error Fix经验                                       │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      沉淀层                                       │    │
│  │  ├── 代码文件 (.wdai-runtime/generated_*.py)                   │    │
│  │  ├── MEMORY.md (记忆更新)                                       │    │
│  │  ├── 经验存储 (.ier-connector/)                                 │    │
│  │  └── Agent历史 (.wdai-runtime/agent_history.json)              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

执行流程:
1. 指挥家观察系统，识别改进机会
2. 创建任务队列，分配给最适合的Agent
3. 执行前: IER检索相关经验，注入Prompt
4. 执行引擎并行执行任务
5. 执行后: IER捕获数据 → 反思分析 → 提炼经验
6. 经验存储，供下次执行使用
7. 成果沉淀到文件系统和MEMORY.md
"""

print(__doc__)

# 显示当前系统状态
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")

print("\n" + "="*73)
print("当前系统组件状态")
print("="*73)

components = {
    "外循环-指挥家": WORKSPACE / ".wdai-runtime/agent_conductor_v3.py",
    "外循环-执行引擎": WORKSPACE / ".wdai-runtime/agent_executor_v4.py",
    "IER连接器": WORKSPACE / ".wdai-runtime/ier_connector_v1.py",
    "内循环-SRA-IER": WORKSPACE / "skills/self-reflection-agent/IER.md",
    "内循环-SEA-IER": WORKSPACE / "skills/system-evolution-agent/IER.md",
}

for name, path in components.items():
    status = "✅" if path.exists() else "❌"
    size = path.stat().st_size if path.exists() else 0
    print(f"  {status} {name:<25} {size>8,} bytes")

# 统计生成的文件
runtime_dir = WORKSPACE / ".wdai-runtime"
generated_files = list(runtime_dir.glob("generated_*.py"))

print(f"\n生成的代码文件: {len(generated_files)} 个")
for f in generated_files[-3:]:
    print(f"  - {f.name} ({f.stat().st_size} bytes)")

# IER状态
ier_file = WORKSPACE / ".ier-connector/connector_state.json"
if ier_file.exists():
    import json
    with open(ier_file, 'r') as f:
        ier_state = json.load(f)
    print(f"\nIER连接器状态:")
    print(f"  洞察数: {ier_state.get('insights_count', 0)}")
    print(f"  经验数: {ier_state.get('experiences_count', 0)}")
    print(f"  最后更新: {ier_state.get('last_updated', 'N/A')}")

print("\n" + "="*73)
print("✅ 外循环-内循环连接完成")
print("="*73)
