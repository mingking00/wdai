# CLI-Anything 深度分析报告
## 香港大学 HKUDS 实验室开源项目

---

## 📋 项目概述

**核心目标**: 让任何软件拥有"智能体原生"(Agent-Native)特性

**解决的问题**:
- AI Agent推理能力强，但打不开Blender菜单、点不了GIMP按钮
- UI自动化 fragile（换个主题就崩）
- API覆盖率通常不到10%
- 重新实现会丢掉大量专业能力

**解决方案**: 自动为任何软件生成CLI接口

---

## 🏗️ 7阶段自动化流水线

```
Phase 1: 🔍 Analyze    - 扫描源码，映射GUI动作到API
Phase 2: 📐 Design     - 架构命令组、状态模型、输出格式
Phase 3: 🔨 Implement  - 构建Click CLI（REPL、JSON输出、undo/redo）
Phase 4: 📋 Plan Tests - 创建TEST.md（单元+E2E测试计划）
Phase 5: 🧪 Write Tests- 实现完整测试套件
Phase 6: 📝 Document   - 更新TEST.md结果
Phase 6.5: 🤖 SKILL.md - 生成AI可发现的技能定义 ⭐ 新增
Phase 7: 📦 Publish    - 创建setup.py，安装到PATH
```

---

## ✅ 已验证的软件（13款，1,588个测试）

| 软件 | 领域 | 测试数 | 后端技术 |
|------|------|--------|----------|
| GIMP | 图像编辑 | 107 | Pillow + GEGL/Script-Fu |
| Blender | 3D建模 | 208 | bpy (Python scripting) |
| Inkscape | 矢量图形 | 202 | SVG/XML操作 |
| Audacity | 音频制作 | 161 | Python wave + sox |
| LibreOffice | 办公套件 | 158 | ODF生成 + headless LO |
| OBS Studio | 直播录制 | 153 | JSON scene + obs-websocket |
| Kdenlive | 视频剪辑 | 155 | MLT XML + melt renderer |
| Shotcut | 视频剪辑 | 154 | MLT XML + melt |
| Zoom | 视频会议 | 22 | Zoom REST API |
| Draw.io | 图表绘制 | 138 | mxGraph XML |
| Mermaid | 图表 | 10 | Mermaid state |
| AnyGen | AI内容生成 | 50 | AnyGen REST API |
| ComfyUI | AI图像生成 | 70 | ComfyUI REST API |

**总计**: 1,588个测试，100%通过率

---

## 🎯 核心设计原则（对wdai的启示）

### 1. 真实的软件集成
```
❌ 错误: 用Pillow替代GIMP
✅ 正确: 生成有效项目文件 → 调用真实后端渲染

启示: wdai应该直接调用真实工具，而不是模拟
```

### 2. 灵活的交互模式
```
REPL模式: 交互式Agent会话
命令模式: 脚本/流水线
JSON输出: 结构化数据供机器消费

启示: wdai工具应该支持多种输出格式
```

### 3. Agent-Native设计
```
--json 标志: 每个命令都支持
--help 自描述: 标准发现机制
which 命令: Agent通过标准命令发现工具

启示: wdai工具应该标准化接口
```

### 4. SKILL.md 自动生成 ⭐ 关键
```
位置: cli_anything/<software>/skills/SKILL.md
内容:
  - YAML frontmatter (名称、描述)
  - 命令组文档
  - 使用示例
  - Agent专用指导(JSON输出、错误处理)

启示: wdai可以自动生成SKILL.md供其他Agent使用
```

---

## 🤖 支持的Agent平台

| 平台 | 状态 | 安装方式 |
|------|------|----------|
| Claude Code | ✅ 官方 | /plugin install cli-anything |
| OpenCode | ✅ 实验性 | 复制commands目录 |
| OpenClaw | ✅ 社区 | SKILL.md |
| Codex | ✅ 社区 | install.sh |
| Qodercli | ✅ 社区 | setup-qodercli.sh |
| Goose | ⏳ 实验性 | 通过CLI provider |
| Cursor | ⏳ 即将到来 | - |
| Windsurf | ⏳ 即将到来 | - |

---

## 🔧 对wdai的启示与应用

### 当前wdai工具链
```
研究: AutoResearch v3.4
搜索: MiniSearch (本地) + kimi_search (网页)
进化: SEA Service
记忆: MemRL + IER
```

### 可以CLI-Anything化的工具

#### 1. wdai_minisearch → CLI-Anything化
```bash
# 当前
python3 wdai_minisearch.py index <dir>
python3 wdai_minisearch.py search "query"

# CLI-Anything化后
cli-anything-minisearch index <dir>
cli-anything-minisearch search "query" --json
cli-anything-minisearch  # 进入REPL
```

#### 2. wdai_autoresearch → CLI-Anything化
```bash
# 当前
python3 wdai_autoresearch_v3_4.py

# CLI-Anything化后
cli-anything-autoresearch research "Python asyncio" --hypothesis "xxx"
cli-anything-autoresearch --json status
cli-anything-autoresearch  # 进入REPL模式
```

#### 3. SEA Service → CLI-Anything化
```bash
cli-anything-sea analyze
cli-anything-sea improve "description" "file.py"
cli-anything-sea ier-stats
```

---

## 📊 CLI-Anything vs wdai 对比

| 特性 | CLI-Anything | wdai AutoResearch |
|------|--------------|-------------------|
| **目标** | 软件Agent-Native化 | 自主研究进化 |
| **方法** | 生成CLI接口 | 6 Phase研究流程 |
| **经验学习** | ❌ 未明确 | ✅ Self-Navigating + IER |
| **贡献分析** | ❌ 未明确 | ✅ Self-Attributing |
| **自动优化** | ❌ 依赖外部Agent | ✅ SEA Service |
| **SKILL.md** | ✅ 自动生成 | ❌ 未实现 |
| **REPL** | ✅ 统一ReplSkin | ❌ 未实现 |
| **测试** | ✅ 1,588测试 | ⚠️ 有限测试 |

**互补性**: CLI-Anything解决"工具如何被使用"，wdai解决"如何自主研究和进化"

---

## 🚀 整合建议

### 短期（直接可用）
1. **安装CLI-Anything SKILL到OpenClaw**
   ```bash
   git clone https://github.com/HKUDS/CLI-Anything.git
   mkdir -p ~/.openclaw/skills/cli-anything
   cp CLI-Anything/openclaw-skill/SKILL.md ~/.openclaw/skills/cli-anything/
   ```

2. **用CLI-Anything为wdai工具生成CLI**
   - 为wdai_minisearch生成CLI
   - 为wdai_autoresearch生成CLI
   - 自动生成SKILL.md

### 中期（深度融合）
3. **统一ReplSkin接口**
   - 将所有wdai工具接入ReplSkin
   - 统一REPL体验

4. **SKILL.md自动生成**
   - wdai完成任务后自动生成SKILL.md
   - 沉淀为可复用技能

### 长期（协同进化）
5. **双向增强**
   - CLI-Anything生成的CLI使用wdai进行研究优化
   - wdai使用CLI-Anything生成的工具扩展能力

---

## 📚 关键文档

| 文档 | 内容 |
|------|------|
| HARNESS.md | 方法论SOP，7阶段流水线标准 |
| cli-anything-plugin/README.md | 插件文档 |
| QUICKSTART.md | 5分钟入门 |
| PUBLISHING.md | 发布指南 |

---

## 💡 关键洞察

1. **CLI是Agent的通用接口**: 结构化、可组合、自描述
2. **真实软件集成**: 不替代，而是包装（生成项目文件→调用真实后端）
3. **SKILL.md是Agent发现机制**: 让AI能自动学习使用工具
4. **测试是质量保证**: 1,588测试确保可靠性

---

## 🎯 对wdai的直接价值

1. **工具标准化**: 所有工具统一CLI接口
2. **SKILL.md生成**: 自动沉淀可复用技能
3. **REPL体验**: 交互式工具使用
4. **测试覆盖**: 借鉴1,588测试的经验
5. **生态兼容**: 与Claude Code、OpenClaw等兼容

**结论**: CLI-Anything为wdai提供了工具标准化的方法论，值得深度整合！
