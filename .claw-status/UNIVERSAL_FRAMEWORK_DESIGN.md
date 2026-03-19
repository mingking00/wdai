# wdai Universal Framework - 通用底层框架设计

> 统一所有底层系统的插件化架构
> 配置驱动 · 自动发现 · 统一事件

---

## 🎯 核心设计原则

1. **插件化**: 每个系统是一个插件，可插拔
2. **配置驱动**: 规则在配置中，不在代码中
3. **统一事件**: 所有工具调用通过事件总线
4. **自动发现**: 自动识别任务类型，无需硬编码

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    wdai Universal Framework              │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Plugin    │  │   Plugin    │  │   Plugin    │     │
│  │   System    │  │   System    │  │   System    │     │
│  │  (原则执行)  │  │  (方法指纹)  │  │  (记忆系统)  │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │            │
│         └────────────────┼────────────────┘            │
│                          │                              │
│  ┌───────────────────────┴───────────────────────┐     │
│  │           Universal Event Bus (统一事件总线)    │     │
│  │                                                │     │
│  │  before_tool_call ──→ 插件处理 ──→ after_tool_call │
│  │       ↑                                    ↓      │     │
│  │  intercept(阻止/修改)              record(记录)   │     │
│  └────────────────────────────────────────────────┘     │
│                          │                              │
│         ┌────────────────┼────────────────┐            │
│         │                │                │            │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐     │
│  │   Config    │  │   Registry  │  │   Router    │     │
│  │   Store     │  │   (插件注册) │  │   (任务路由) │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 核心组件

### 1. 统一事件总线 (Universal Event Bus)

```python
class UniversalEventBus:
    """
    所有工具调用的统一入口
    自动触发所有注册的插件
    """
    
    def emit(self, event_type: str, data: Dict) -> Dict:
        """
        事件类型:
        - tool:before_call    # 工具调用前
        - tool:after_call     # 工具调用后  
        - tool:error          # 工具调用错误
        - task:complete       # 任务完成
        - task:fail           # 任务失败
        """
        pass
```

### 2. 插件基类 (Plugin Base)

```python
class UniversalPlugin:
    """
    所有插件的基类
    统一接口，便于管理
    """
    
    name: str = "base_plugin"
    version: str = "1.0"
    priority: int = 50  # 执行优先级
    
    def on_tool_before(self, context: ToolContext) -> InterceptResult:
        """工具调用前处理"""
        return InterceptResult.proceed()
    
    def on_tool_after(self, context: ToolContext, result: Any):
        """工具调用后处理"""
        pass
    
    def on_task_complete(self, context: TaskContext):
        """任务完成时处理"""
        pass
    
    def on_config_change(self, config: Dict):
        """配置变更时处理"""
        pass
```

### 3. 配置存储 (Config Store)

```json
{
  "version": "2.0",
  "plugins": {
    "principle_engine": {
      "enabled": true,
      "priority": 10,
      "config": {
        "principles": [
          {"id": "P0", "name": "安全", "weight": 1000},
          {"id": "P1", "name": "创新", "weight": 100},
          {"id": "P2", "name": "已有能力优先", "weight": 50}
        ],
        "rules": [
          {
            "when": "method_fails",
            "count": 3,
            "then": "lock_method"
          }
        ]
      }
    },
    "fingerprint_system": {
      "enabled": true,
      "priority": 20,
      "config": {
        "blacklist_threshold": 2,
        "reuse_threshold": 0.8,
        "auto_record": true
      }
    },
    "memory_system": {
      "enabled": true,
      "priority": 30,
      "config": {
        "extract_strategy": "semantic",
        "decay_enabled": true,
        "conflict_resolution": "auto"
      }
    }
  }
}
```

---

## 🔌 现有系统插件化改造

### 原则执行系统 → PrinciplePlugin

```python
class PrinciplePlugin(UniversalPlugin):
    name = "principle_engine"
    priority = 10  # 最高优先级
    
    def on_tool_before(self, context):
        # 读取配置中的原则，而非硬编码
        principles = self.config.get("principles", [])
        
        # 动态检查
        violations = self.check_principles(context, principles)
        if violations:
            return InterceptResult.block(reason=violations)
        
        return InterceptResult.proceed()
```

### 方法指纹系统 → FingerprintPlugin

```python
class FingerprintPlugin(UniversalPlugin):
    name = "fingerprint_system"
    priority = 20
    
    def on_tool_before(self, context):
        # 自动推断任务类型（已通用化）
        task_type = self.infer_task_type(context)
        
        # 查指纹库
        advice = self.fingerprint_db.query(task_type, context.params)
        
        if advice.is_blacklisted:
            return InterceptResult.block(
                reason=advice.blacklist_reason,
                alternative=advice.alternative
            )
        
        if advice.can_reuse:
            context.suggested_params = advice.optimal_params
        
        return InterceptResult.proceed()
    
    def on_tool_after(self, context, result):
        # 自动记录结果
        self.fingerprint_db.record(
            task_type=self.infer_task_type(context),
            method=context.params,
            result=result,
            tokens=context.token_usage
        )
```

### 记忆系统 → MemoryPlugin

```python
class MemoryPlugin(UniversalPlugin):
    name = "memory_system"
    priority = 30
    
    def on_task_complete(self, context):
        # 配置驱动的提取策略
        strategy = self.config.get("extract_strategy", "semantic")
        
        if strategy == "semantic":
            facts = self.semantic_extract(context)
        elif strategy == "keyword":
            facts = self.keyword_extract(context)
        elif strategy == "template":
            facts = self.template_extract(context, self.config.get("templates", []))
        
        # 存储
        self.memory_store.save(facts)
```

### 自动学习系统 → LearningPlugin

```python
class LearningPlugin(UniversalPlugin):
    name = "auto_learning"
    priority = 40
    
    def on_tool_error(self, context, error):
        # 统一错误记录
        self.error_db.record({
            "tool": context.tool_name,
            "params": context.params,
            "error": str(error),
            "timestamp": now(),
            "context": context.task_id
        })
        
        # 触发学习
        if self.should_learn(error):
            self.trigger_learning(context, error)
    
    def on_user_correction(self, context, correction):
        # 统一记录用户纠正
        self.correction_db.record({
            "original": context.original_output,
            "correction": correction,
            "task_type": context.task_type
        })
```

---

## 🚀 使用方式

### 初始化框架

```python
from wdai_framework import UniversalFramework

# 加载框架
framework = UniversalFramework()
framework.load_config(".claw-status/framework_config.json")

# 自动发现并加载所有插件
framework.discover_plugins(".claw-status/plugins/")

# 启用自动包装
framework.enable_auto_wrap()
```

### 工具调用（自动触发所有插件）

```python
# 任何工具调用自动经过插件处理
result = framework.tool_call(
    tool="message",
    action="send",
    channel="feishu",
    filePath="/tmp/test.png"
)

# 流程:
# 1. PrinciplePlugin 检查原则 ✓
# 2. FingerprintPlugin 查黑名单 → 阻止 ❌
# 3. FingerprintPlugin 建议替代方案 💡
# 4. 返回建议，不执行
```

### 添加新插件

```python
# 新建文件: .claw-status/plugins/my_plugin.py

from wdai_framework import UniversalPlugin

class MyPlugin(UniversalPlugin):
    name = "my_custom_plugin"
    priority = 50
    
    def on_tool_before(self, context):
        # 自定义逻辑
        if context.tool_name == "web_search":
            print("🔍 即将执行搜索...")
        return InterceptResult.proceed()
```

框架自动发现并加载，无需修改核心代码。

---

## 📁 新目录结构

```
.claw-status/
├── framework/                    # 通用框架核心
│   ├── __init__.py
│   ├── event_bus.py              # 统一事件总线
│   ├── plugin_base.py            # 插件基类
│   ├── plugin_registry.py        # 插件注册表
│   └── config_store.py           # 配置存储
├── plugins/                      # 插件目录
│   ├── principle_plugin.py       # 原则执行插件
│   ├── fingerprint_plugin.py     # 方法指纹插件
│   ├── memory_plugin.py          # 记忆系统插件
│   ├── learning_plugin.py        # 自动学习插件
│   └── evolution_plugin.py       # 进化系统插件
├── config/
│   └── framework.json            # 框架配置
└── data/
    ├── fingerprints.json         # 指纹数据
    ├── memories.json             # 记忆数据
    ├── learnings.json            # 学习记录
    └── principles.json           # 原则库
```

---

## 🎯 带来的改变

| 之前 | 之后 |
|------|------|
| 5个独立系统 | 1个统一框架 + 5个插件 |
| 硬编码规则 | 配置驱动规则 |
| 各自触发机制 | 统一事件总线 |
| 修改代码添加功能 | 添加插件文件即可 |
| 预定义任务类型 | 自动推断所有任务 |

---

## ✅ 实现步骤

1. 实现框架核心（event_bus, plugin_base, registry）
2. 将现有系统改造为插件
3. 迁移数据到统一格式
4. 编写配置模板
5. 测试所有场景

要我实现这个框架吗？