# wdai CLI-Anything 整合方案

## 已完成的整合

### 1. CLI-Anything SKILL 安装 ✅

**位置**: `/root/.openclaw/skills/cli-anything/SKILL.md`

**使用方法**:
```bash
@cli-anything build ./gimp
@cli-anything refine ./gimp "batch processing"
```

### 2. wdai_minisearch CLI ✅

**位置**: `/root/.openclaw/workspace/wdai-cli-tools/minisearch/`

**安装**:
```bash
cd /root/.openclaw/workspace/wdai-cli-tools/minisearch/agent-harness
pip install -e .
```

**使用**:
```bash
# 索引目录
cli-anything-wdai-minisearch index ./documents

# 搜索
cli-anything-wdai-minisearch search "machine learning"

# JSON输出
cli-anything-wdai-minisearch --json search "query"

# 查看状态
cli-anything-wdai-minisearch status
```

### 3. wdai_autoresearch CLI ✅

**位置**: `/root/.openclaw/workspace/wdai-cli-tools/autoresearch/`

**安装**:
```bash
cd /root/.openclaw/workspace/wdai-cli-tools/autoresearch/agent-harness
pip install -e .
```

**使用**:
```bash
# 开始研究
cli-anything-wdai-autoresearch research "AI agents"

# 指定深度
cli-anything-wdai-autoresearch research "Python" -d 4

# 查看状态
cli-anything-wdai-autoresearch status

# 获取发现
cli-anything-wdai-autoresearch findings "project-name"
```

## 项目结构

```
wdai-cli-tools/
├── minisearch/
│   └── agent-harness/
│       ├── cli_anything/minisearch/cli.py
│       ├── setup.py
│       └── SKILL.md
└── autoresearch/
    └── agent-harness/
        ├── cli_anything/autoresearch/cli.py
        ├── setup.py
        └── SKILL.md
```

## 下一步

### 1. 安装CLI工具
```bash
# 安装minisearch CLI
cd /root/.openclaw/workspace/wdai-cli-tools/minisearch/agent-harness
pip install -e .

# 安装autoresearch CLI
cd /root/.openclaw/workspace/wdai-cli-tools/autoresearch/agent-harness
pip install -e .
```

### 2. 测试使用
```bash
# 测试minisearch
cli-anything-wdai-minisearch index ~/.openclaw/workspace
cli-anything-wdai-minisearch --json search "AI agent"

# 测试autoresearch
cli-anything-wdai-autoresearch research "CLI tools"
```

### 3. 生成更多工具的CLI
可以继续为以下工具生成CLI:
- SEA Service
- IER (Iterative Evolution Registry)
- Work Monitor
- Growth Check

## CLI-Anything 方法论应用

| 原则 | wdai实现 |
|:---|:---|
| **真实软件集成** | 直接调用wdai工具，不模拟 |
| **统一REPL接口** | Click CLI框架 |
| **JSON输出** | 所有命令支持 `--json` |
| **SKILL.md生成** | 每个CLI包含SKILL.md |
| **零配置安装** | `pip install -e .` |

## 与OpenClaw集成

CLI-Anything SKILL已在OpenClaw中可用:
- **技能路径**: `~/.openclaw/skills/cli-anything/SKILL.md`
- **使用**: `@cli-anything build <software>`

wdai工具的CLI已准备安装:
- **minisearch**: `cli-anything-wdai-minisearch`
- **autoresearch**: `cli-anything-wdai-autoresearch`
