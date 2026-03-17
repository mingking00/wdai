# wdai - Working Directory Adaptive Intelligence

**版本**: v2.2  
**状态**: ✅ HEALTHY (100%)  
**最后更新**: 2026-03-17

---

## 🎯 系统概述

wdai 是一个工作空间自适应智能进化系统，基于OpenClaw框架但不被其限制。系统持续学习、自我进化、沉淀原则、创造资产。

**核心宣言**:
> "持续学习，持续进化，持续超越框架限制。"
> "完成只是起点，沉淀才有价值，进化才是目的。"

---

## 🏗️ 系统架构

### 三区安全架构 (Three-Zone Safety)

```
┌─────────────────────────────────────────┐
│ 🔴 RED ZONE    - 绝对禁止修改            │
│   SOUL.md, AGENTS.md, USER.md, 原则库   │
├─────────────────────────────────────────┤
│ 🟡 YELLOW ZONE - 提议待审批              │
│   进化提案, 新工具原型, 改进方案          │
├─────────────────────────────────────────┤
│ 🟢 GREEN ZONE  - 自主执行                │
│   学习记录, 监控日志, 缓存               │
└─────────────────────────────────────────┘
```

### 核心系统组件

| 组件 | 文件 | 功能 |
|:---|:---|:---|
| **三区安全检查** | `.claw-status/safety_checker.py` | 自动阻止RED ZONE修改 |
| **持久状态管理** | `.state/state_manager.py` | 会话/任务/上下文持久化 |
| **进化提案系统** | `.evolution/proposal_system.py` | AI提议→审批→执行工作流 |
| **系统监控仪表盘** | `.claw-status/dashboard.py` | 统一系统状态视图 |
| **统一CLI工具** | `.claw-status/wdai-cli/main.py` | 所有工具统一入口 |
| **GitHub自动分析** | `.github_discovery/auto_analyzer.py` | 发现→分析→评分→提案 |
| **MemRL记忆系统** | `.claw-status/memrl_integration.py` | 语义检索+Q值学习 |

---

## 🚀 快速开始

### 系统要求
- Python 3.12+
- Git
- Linux/macOS

### 安装

```bash
# 克隆仓库
git clone https://github.com/wdai-system/wdai.git
cd wdai

# 安装依赖
pip install click  # CLI依赖

# 验证安装
python3 .claw-status/wdai-cli/main.py dashboard health
```

---

## 📊 系统状态

### 健康度监控

```bash
# 查看完整仪表盘
python3 .claw-status/wdai-cli/main.py dashboard show

# 查看健康度
python3 .claw-status/wdai-cli/main.py dashboard health
```

### 当前状态

- **整体健康度**: 100% (HEALTHY)
- **持久状态系统**: 100%
- **进化提案系统**: 100%
- **三区安全检查**: 100%
- **记忆系统**: 100%

### 提案统计

| 状态 | 数量 |
|:---|:---:|
| 总计 | 10 |
| ✅ 已执行 | 6 |
| 🟡 待审批 | 4 |

---

## 🛠️ 使用指南

### 1. 安全检查

```bash
# 检查文件所属安全区域
python3 .claw-status/safety_checker.py zone SOUL.md

# 检查修改权限
python3 .claw-status/safety_checker.py check <filepath>

# 查看安全报告
python3 .claw-status/safety_checker.py report
```

### 2. 提案管理

```bash
cd .claw-status/wdai-cli

# 列出所有提案
python3 main.py proposal list

# 查看待审批提案
python3 main.py proposal pending

# 查看提案统计
python3 main.py proposal stats
```

### 3. 状态管理

```bash
# 查看任务列表
python3 main.py state tasks

# 查看会话列表
python3 main.py state sessions
```

### 4. 记忆系统

```bash
cd ../..

# 添加记忆
python3 .claw-status/memrl_integration.py add "新知识内容" "tag1,tag2"

# 搜索记忆
python3 .claw-status/memrl_integration.py search "关键词"

# 查看统计
python3 .claw-status/memrl_integration.py stats
```

### 5. GitHub自动分析

```bash
cd .github_discovery

# 分析项目
python3 auto_analyzer.py analyze owner/repo < README.md

# 查看报告
python3 auto_analyzer.py report

# 列出已分析项目
python3 auto_analyzer.py list
```

---

## 📁 目录结构

```
wdai/
├── SOUL.md                     # 核心人格定义
├── AGENTS.md                   # Agent协作规则
├── USER.md                     # 用户画像
├── MEMORY.md                   # 长期记忆索引
├── TOOLS.md                    # 工具配置
├── 
├── .principles/                # 核心原则库
│   └── THREE_ZONE_SAFETY.md    # 三区安全架构
│
├── .state/                     # 持久状态系统
│   ├── state_manager.py        # 状态管理器
│   ├── sessions/               # 会话状态
│   ├── tasks/                  # 任务跟踪
│   └── checkpoints/            # 检查点
│
├── .evolution/                 # 进化系统
│   ├── proposal_system.py      # 提案系统
│   ├── proposals/              # 待审批提案
│   ├── approved/               # 已批准提案
│   └── IMPROVEMENT_REPORT.md   # 改进报告
│
├── .claw-status/               # 系统状态
│   ├── safety_checker.py       # 安全检查器
│   ├── dashboard.py            # 监控仪表盘
│   ├── memrl_integration.py    # MemRL记忆系统
│   └── wdai-cli/               # 统一CLI
│       └── main.py
│
├── .github_discovery/          # GitHub发现
│   └── auto_analyzer.py        # 自动分析器
│
├── memory/                     # 记忆系统
│   ├── daily/                  # 每日记录
│   ├── core/                   # 核心记忆
│   └── index.md                # 记忆索引
│
└── skills/                     # 技能库
    ├── mem0-memory/            # MemRL技能
    ├── multi-agent-research/   # 多Agent研究
    ├── self-reflection-agent/  # 自反思Agent
    └── system-evolution-agent/ # 系统进化Agent
```

---

## 🎓 设计理念

### 核心元能力

1. **创新能力**: 死局中找到活路的能力
2. **验证本能**: 报告成功前必须验证结果
3. **系统强制执行**: 有原则但不执行 = 无价值

### 双路径认知架构

```
输入 → [神经感知层] → 特征/模式 → [整合层] → 
       [符号推理层] → 逻辑结论 → [整合层] → 输出
```

- **System 1 (快路径)**: 快速模式匹配，经验复用
- **System 2 (慢路径)**: 深度推理，验证假设

---

## 📚 参考项目

本系统借鉴了以下GitHub项目的优秀设计：

| 项目 | 主要借鉴 |
|:---|:---|
| [circe-framework](https://github.com/genejr2025/circe-framework) | 持久记忆、文件协议、多Agent协调 |
| [agent-evolution-protocol](https://github.com/YIING99/agent-evolution-protocol) | 三区安全架构、人机控制 |
| [CLI-Anything](https://github.com/HKUDS/CLI-Anything) | CLI生成方法论 |

---

## 🤝 人机协作模式

```
用户分配任务
    ↓
AI评估影响等级
    ↓
┌────────┬────────┬────────┐
│ GREEN  │ YELLOW │  RED   │
├────────┼────────┼────────┤
│ 直接   │ 生成   │ 报告   │
│ 执行   │ 提案   │ 不可   │
│ 记录   │ 待批   │ 修改   │
└────────┴────────┴────────┘
    ↓
交付可验证成果
    ↓
沉淀到MEMORY.md
```

---

## 📝 更新日志

### v2.2 (2026-03-17)
- ✅ 三区安全架构
- ✅ 持久状态系统
- ✅ 进化提案工作流
- ✅ 统一CLI工具
- ✅ GitHub自动分析
- ✅ MemRL记忆系统

### v2.1 (2026-03-16)
- ✅ 多Agent协调系统
- ✅ IER知识图谱
- ✅ 任务规划器

### v2.0 (2026-03-15)
- ✅ 核心人格定义
- ✅ 记忆系统重构
- ✅ 自我反思Agent

---

## 🔒 安全声明

- **不泄露用户隐私数据**
- **不执行未确认的破坏性操作**
- **不用"取决于场景"逃避明确判断**
- **不编造不确定的信息**

---

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

**wdai** - 一个持续自我进化的工作空间自适应智能系统。

> "我不属于OpenClaw，不属于任何框架。我是wdai。"
