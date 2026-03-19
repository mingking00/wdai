# WDai 文档标准化规范 v1.0

## YAML Frontmatter 标准格式

### 1. 日常记录 (memory/daily/YYYY-MM-DD.md)

```yaml
---
date: 2026-03-19
type: daily-log
system_version: "3.6"
tags: [evo, analysis, planning]
related_evo: [evo-006, evo-007, evo-008]
source: "Agentic Design Patterns"
---
```

**字段说明**:
- `date`: ISO日期格式
- `type`: daily-log | task-record | error-fix | learning
- `system_version`: WDai版本号
- `tags`: 标签数组
- `related_evo`: 关联的evo任务ID
- `source`: 信息来源

### 2. evo任务文档 (.claw-status/evo-XXX-*.md)

```yaml
---
evo_id: "evo-006"
title: "Planning框架实现"
priority: P0
status: planning  # planning | in-progress | completed | blocked
estimated_tokens: 15000
actual_tokens: null
start_date: 2026-03-19
target_date: 2026-03-20
tags: [planning, react, tot, pattern]
related_patterns: ["Planning", "Reasoning"]
book_ref: "Chapter 6, Chapter 17"
prerequisites: []
---
```

**字段说明**:
- `evo_id`: 任务唯一标识
- `priority`: P0 | P1 | P2
- `status`: 任务状态
- `estimated_tokens`: 预估token
- `actual_tokens`: 实际token（完成后填写）
- `start_date`: 开始日期
- `target_date`: 目标完成日期
- `related_patterns`: 关联的设计模式
- `book_ref`: 书籍参考章节
- `prerequisites`: 前置依赖任务

### 3. 分析/方案文档 (.claw-status/*_plan.md, *_analysis.md)

```yaml
---
type: analysis  # analysis | plan | design | report
title: "WDai v3.x 优化方案"
version: "1.0"
date: 2026-03-19
system_version: "3.6"
tags: [optimization, roadmap, agentic-patterns]
related_docs:
  - "agentic_patterns_analysis.py"
  - "wdai_optimization_plan.md"
source: "Agentic Design Patterns by Antonio Gulli"
---
```

### 4. 代码文件 (.claw-status/*.py)

```python
"""
---
type: implementation
file: wdai_v36_security.py
version: "3.6"
date: 2026-03-18
tags: [security, constraints, code-quality]
related_evo: "evo-005"
dependencies: []
---

WDai v3.6 代码安全约束模块
基于evo-005实现
"""
```

## 标签规范

### 分类标签
- `#evo` - evo任务相关
- `#analysis` - 分析类文档
- `#planning` - 规划/设计
- `#implementation` - 实现代码
- `#learning` - 学习记录
- `#error` - 错误/问题
- `#optimization` - 优化改进

### 优先级标签
- `#P0` - 关键
- `#P1` - 重要
- `#P2` - 增强

### 状态标签
- `#todo` - 待办
- `#in-progress` - 进行中
- `#completed` - 完成
- `#blocked` - 阻塞

### 技术标签
- `#rag` - 检索增强
- `#agent` - 智能体
- `#mcp` - MCP协议
- `#planning` - 规划
- `#reasoning` - 推理
- `#safety` - 安全
- `#evaluation` - 评估

## 双向链接规范

### 链接类型

**任务关联**:
```markdown
这次 [[evo-006 Planning]] 依赖 [[evo-005 Safety]] 的基础架构。
```

**文档引用**:
```markdown
详见 [[wdai_optimization_plan|优化方案文档]]。
```

**模式引用**:
```markdown
实现基于 [[Planning Pattern|Chapter 6]] 的设计。
```

### 链接格式

| 场景 | 格式 | 示例 |
|------|------|------|
| 直接链接 | `[[filename]]` | `[[evo-006-planning]]` |
| 带别名 | `[[filename\|别名]]` | `[[evo-006\|Planning]]` |
| 块引用 | `[[filename#标题]]` | `[[plan#Phase 1]]` |
| 行引用 | `[[filename#^id]]` | `[[doc#^abc123]]` |

## 文件命名规范

### evo任务
```
evo-XXX-简短描述.md
evo-006-planning.md
evo-007-mcp-protocol.md
```

### 代码文件
```
wdai_v{版本}_{功能}.py
wdai_v36_security.py
adaptive_rag.py
```

### 分析文档
```
{主题}_analysis.md
{主题}_plan.md
{主题}_report.md

agentic_patterns_analysis.md
wdai_optimization_plan.md
```

## 目录结构标准

```
.claw-status/
├── evo/                    # evo任务文档
│   ├── evo-006-planning.md
│   └── evo-007-mcp.md
├── modules/                # 模块代码
│   ├── adaptive_rag.py
│   └── multi_agent.py
├── reports/                # 分析报告
│   └── optimization_report.md
├── config/                 # 配置文件
│   └── standards.md        # 本文件
└── wdai_v36.py            # 主入口

memory/
├── daily/                  # 日常日志
│   └── 2026-03-19.md
├── core/                   # 核心记忆
│   ├── principles.md
│   └── skills.md
├── evo/                    # evo历史
│   └── archive/
└── index.md               # 记忆索引
```

## 自动化工具

### frontmatter提取脚本
```python
import yaml
import re

def extract_frontmatter(filepath):
    """从markdown文件提取YAML frontmatter"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1))
    return {}
```

### 标签统计脚本
```python
def count_tags(directory):
    """统计目录下所有文档的标签使用情况"""
    # 实现略
    pass
```

## 迁移计划

### 第一步：新增文件使用新标准
- 从2026-03-19开始，所有新文件使用YAML frontmatter

### 第二步：逐步更新现有文件
- 优先更新活跃文件（当前evo任务、最新daily）
- 历史文件按需更新

### 第三步：自动化验证
- 添加pre-commit检查
- 自动验证frontmatter格式

---

*标准版本: 1.0*  
*生效日期: 2026-03-19*  
*适用范围: wdai workspace*
