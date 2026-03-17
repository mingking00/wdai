# OpenClaw 集成指南
# 将 OCA-MAS 集成到 OpenClaw 主流程

## 快速集成步骤

### 1. 复制技能到 OpenClaw

```bash
# 复制到 OpenClaw skills 目录
cp -r multi-agent-research ~/.openclaw/skills/

# 验证
ls ~/.openclaw/skills/multi-agent-research
```

### 2. 添加到 OpenClaw 配置

编辑 `~/.openclaw/config.json`:

```json
{
  "skills": {
    "entries": {
      "multi-agent-research": {
        "enabled": true,
        "path": "skills/multi-agent-research",
        "auto_load": true
      }
    }
  }
}
```

### 3. 更新 AGENTS.md

在 `AGENTS.md` 中添加：

```markdown
## Multi-Agent Research

当需要深入研究时，使用 OCA-MAS 系统：

```python
from skills.multi_agent_research.adaptive_orchestrator import research

# 自动触发多智能体研究
result = await research(user_query, max_parallel=5)
```

触发条件：
- 用户要求研究某个主题
- 需要多来源信息验证
- 问题复杂度较高
```

## 深度集成

### 方式1: 自动触发 (推荐)

修改 `SOUL.md`，添加自动检测：

```python
# 在回复前自动检测是否需要研究
def should_use_research(query: str) -> bool:
    indicators = [
        "研究", "分析", "对比", "最新",
        "research", "analyze", "compare", "latest"
    ]
    return any(word in query.lower() for word in indicators)

# 主流程
if should_use_research(user_input):
    result = await research(user_input)
    response = result["answer"]
else:
    response = await normal_response(user_input)
```

### 方式2: 命令触发

添加 `/research` 命令：

```python
# 在命令处理器中添加
async def handle_research_command(query: str):
    """/research 命令处理器"""
    result = await research(query, max_parallel=5)
    
    return f"""
🔬 研究完成

{result['answer']}

---
📊 统计:
- 来源: {result['sources_count']} 个
- 时间: {result['critical_path_time']:.1f}s
- 并行Agent: {result['parallel_agents']} 个
"""
```

### 方式3: 内存集成

与 `mem0-memory` 技能集成：

```python
# 在研究中自动使用记忆
from skills.mem0_memory.scripts.retrieve_hybrid import hybrid_retrieve
from skills.multi_agent_research.adaptive_orchestrator import research

async def research_with_memory(query: str, user_id: str):
    # 先检索相关记忆
    memories = hybrid_retrieve(query, user_id, top_k=5)
    
    # 构建增强查询
    enhanced_query = f"""
用户查询: {query}

相关历史记忆:
{chr(10).join([m.content for m in memories])}

请基于以上信息进行研究。
"""
    
    # 执行研究
    result = await research(enhanced_query)
    
    # 存储新发现到记忆
    for insight in result['insights']:
        store_memory(insight, user_id, category="research")
    
    return result
```

## 配置选项

### 环境变量

```bash
# .env 文件
OCA_MAS_MAX_PARALLEL=5          # 默认并行度
OCA_MAS_MAX_LOOPS=3             # 最大反思循环
OCA_MAS_ENABLE_MONITORING=true  # 启用监察
OCA_MAS_TIMEOUT=300             # 超时秒数
```

### 配置文件

创建 `~/.openclaw/skills/multi-agent-research/config.yaml`:

```yaml
orchestrator:
  max_parallel: 5
  max_research_loops: 3
  enable_monitoring: true
  
agents:
  explorer:
    model: "kimi-coding/k2p5"
    timeout: 60
    
  investigator:
    model: "kimi-coding/k2p5"
    timeout: 120
    max_instances: 10
    
  critic:
    model: "kimi-coding/k2p5"
    timeout: 60
    
  synthesist:
    model: "kimi-coding/k2p5"
    timeout: 90
    
  anchor:
    enabled: true
    report_interval: 10  # 秒

performance:
  cache_enabled: true
  cache_ttl: 3600
  
monitoring:
  log_level: "INFO"
  save_history: true
```

## 使用示例

### 示例1: 基础研究

```python
# 用户问: "2026年最新的AI Agent框架有哪些？"

from skills.multi_agent_research.adaptive_orchestrator import research

result = await research(
    "2026年最新的AI Agent框架",
    max_parallel=5
)

# 输出:
# 🔬 启动多智能体研究...
# [1/5] 🔭 Explorer: 生成搜索查询...
# [2/5] 🔍 Investigator 并行深度穿透 (5个实例)...
# [3/5] 🎯 Critic: 评估信息充足度...
# [4/5] 🎨 Synthesist: 模式编织...
# [5/5] 📡 Anchor: 心智共情...
#
# ✅ 研究完成 (12.3s)
#
# 基于23个来源的综合分析:
# 1. LangGraph 继续主导，新增并行执行特性
# 2. CrewAI 推出 v2.0，支持100+智能体集群
# 3. AutoGen 集成 GPT-5，推理能力大幅提升
# ...
```

### 示例2: 带工作监察

```python
# 用户可以看到实时进度

from skills.multi_agent_research.adaptive_orchestrator import research
from work_monitor import start_task, progress

start_task("深度研究: 量子计算应用", steps=5)

result = await research(
    "量子计算在药物发现中的最新应用",
    max_parallel=8,
    enable_monitoring=True
)

# 用户可以随时查看:
# cat STATUS.md
# 或
# python3 .claw-status/work_monitor.py
```

### 示例3: 复杂研究任务

```python
# 多轮迭代研究

async def deep_research(topic: str):
    """深度研究，自动迭代直到满意"""
    
    orchestrator = AdaptiveOrchestrator(
        max_parallel=10,
        enable_monitoring=True
    )
    
    # 第一次研究
    result1 = await orchestrator.execute(f"{topic} 基础概念")
    
    # 基于发现深化研究
    for insight in result1['insights']:
        result2 = await orchestrator.execute(
            f"{topic} {insight} 详细分析"
        )
    
    # 综合所有结果
    final = await orchestrator.execute(
        f"综合以下关于{topic}的所有发现: " + 
        result1['answer'][:500]
    )
    
    return final
```

## 故障排除

### 问题1: 研究超时

**解决方案:**
```python
# 增加超时时间
orchestrator = AdaptiveOrchestrator(
    agent_timeout=600  # 10分钟
)

# 或减少并行度以稳定运行
result = await research(query, max_parallel=3)
```

### 问题2: 结果质量不高

**解决方案:**
```python
# 增加反思循环
orchestrator = AdaptiveOrchestrator()
orchestrator.state.max_research_loops = 5

# 或启用更严格的Critic
result = await research(
    query,
    critic_threshold=0.9  # 更高质量标准
)
```

### 问题3: 内存占用过高

**解决方案:**
```python
# 限制缓存大小
orchestrator = AdaptiveOrchestrator(
    max_cache_size=100,  # MB
    cache_ttl=1800       # 30分钟
)

# 或减少并行实例
result = await research(query, max_parallel=3)
```

## 性能优化

### 缓存策略

```python
# 启用结果缓存
orchestrator = AdaptiveOrchestrator(
    cache_enabled=True,
    cache_backend="redis",  # 或 "memory", "file"
    cache_ttl=3600
)

# 相同查询直接返回缓存
result = await research("相同的查询")  # 从缓存返回
```

### 自适应并行度

```python
# 根据任务复杂度自动调整
async def adaptive_research(query: str):
    complexity = estimate_complexity(query)
    
    if complexity == "simple":
        max_parallel = 2
    elif complexity == "medium":
        max_parallel = 5
    else:  # complex
        max_parallel = 10
    
    return await research(query, max_parallel=max_parallel)
```

## 监控与日志

### 查看工作状态

```bash
# 实时状态
cat STATUS.md

# 详细状态
python3 .claw-status/work_monitor.py

# 历史记录
python3 .claw-status/work_monitor.py history

# JSON格式
cat .claw-status/current.json | jq
```

### 日志分析

```python
# 分析研究效率
from work_monitor import get_monitor

monitor = get_monitor()
history = monitor.get_history(limit=100)

# 计算平均研究时间
avg_time = sum(
    h['elapsed_seconds'] for h in history
) / len(history)

print(f"平均研究时间: {avg_time:.1f}s")
```

## 高级定制

### 自定义Agent

```python
from personas import AgentPersona, PersonaTeam

# 创建新Agent
DATA_SCIENTIST = AgentPersona(
    role="Data Science Agent",
    name="DataWhiz",
    emoji="📊",
    core_trait="数据直觉力 - 从噪声中识别真实信号",
    superpower="能一眼看出数据中的异常模式和隐藏关联",
    evolution_metric="从描述性统计 → 预测建模 → 因果推断",
    catchphrase="数据从不说谎",
    failure_mode="过度拟合，混淆相关与因果",
    collaboration_style="提供数据洞察，让Synthesist编织成故事"
)

# 注册
PersonaTeam.ALL_PERSONAS["data_scientist"] = DATA_SCIENTIST

# 使用
result = await research(
    "分析销售数据趋势",
    custom_agents=["data_scientist"]
)
```

## 最佳实践

1. **合理设置并行度**: 通常5-8个实例最优
2. **启用监察**: 让用户知道你在做什么
3. **缓存常用查询**: 避免重复研究
4. **及时反馈**: 每10-15秒更新一次进度
5. **质量优先**: 宁可慢也要准，让Critic严格把关

---

## 支持与反馈

遇到问题？
1. 查看 `DETAILED_DOCS.md`
2. 运行测试: `python -m pytest tests/`
3. 查看日志: `cat .claw-status/current.json`
