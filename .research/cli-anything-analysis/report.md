# CLI-Anything Architecture Analysis

## 研究目标

深入研究 HKUDS/CLI-Anything 项目，提取可复用的架构模式，应用到 Agent Skills 开发中。

---

## 第一部分：CLI-Anything 概述

### 核心功能

CLI-Anything 是一个革命性的框架，能够**自动将任何软件转换为 AI Agent 可控的 CLI 接口**。无需手动编码，无需脆弱的 GUI 自动化。

**关键数据点：**
- ⭐ 2k+ GitHub stars
- ✅ 1,436 个测试用例，100% 通过率
- 🎯 9 个应用实例
- 🔄 7 阶段全自动流水线

### 为什么 CLI 是 AI Agent 的通用接口

1. **结构化与可组合**
   - 文本命令与 LLM 输出格式天然匹配
   - 可链接构建复杂的多步骤工作流

2. **自描述 (--help)**
   - 自动提供 AI Agent 可在运行时发现的文档
   - 无需手动编写 API 规范

3. **Agent-优先的 JSON 输出**
   - 每个命令内置 `--json` 标志
   - 机器消费的结构化数据
   - 人类使用表格输出调试

4. **确定性 & 生产可靠性**
   - 一致的 CLI 结果实现可预测的 Agent 行为

---

## 第二部分：7 阶段全自动流水线

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────┐
│ Analyze │ → │ Design  │ → │Implement│ → │ Plan Tests  │ → │ Write Tests │ → │ Document    │ → │ Publish  │
└─────────┘   └─────────┘   └─────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └──────────┘
```

### 阶段 1: Analyze（分析）
- 扫描目标软件代码库
- 识别核心功能和能力
- 提取 API 边界和交互点
- 分析依赖关系和架构模式

### 阶段 2: Design（设计）
- 设计 CLI 命令结构
- 规划命令层次和分组
- 定义参数和选项约定
- 设计状态管理策略

### 阶段 3: Implement（实现）
- 生成命令处理程序代码
- 实现软件后端集成
- 创建统一的 REPL 接口 (ReplSkin)
- 构建 session 管理机制

### 阶段 4: Plan Tests（规划测试）
- 识别测试场景和边界情况
- 规划单元测试策略
- 设计端到端测试
- 定义测试数据需求

### 阶段 5: Write Tests（编写测试）
- 使用合成数据编写单元测试
- 创建真实文件的后端集成测试
- 实现 CLI 子进程验证测试

### 阶段 6: Document（文档）
- 生成 --help 文档
- 创建使用示例
- 编写 API 参考
- 制作教程内容

### 阶段 7: Publish（发布）
- 打包 pip 可安装模块
- 配置命名空间 (cli_anything.*)
- 设置入口点
- 发布到仓库

---

## 第三部分：核心架构组件

### 3.1 Agent-Software 桥接模式

**核心思想：**
CLI-Anything 的核心是一个**桥接层**，连接 AI Agent 和真实软件。

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AI Agent (Claude, Cursor, etc.)                      │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   │ Text Commands + --json
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CLI-Anything Bridge Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │ Command Router  │  │ ReplSkin (REPL) │  │ Session Manager │  │ State Manager │ │
│  └────────┬────────┘  └─────────────────┘  └─────────────────┘  └───────────────┘ │
└───────────┼──────────────────────────────────────────────────────────────────────┘
            │
            │ Direct API Calls / Backend Integration
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Real Software Backend                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐ │
│  │  GIMP      │ │  Blender   │ │  Audacity  │ │  LibreOffice│ │  ...         │ │
│  │ (Image)    │ │ (3D)       │ │ (Audio)    │ │ (Documents) │ │              │ │
│  └────────────┘ └────────────┘ └────────────┘ └─────────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**桥接层职责：**
1. **协议转换**: 将文本命令转换为软件特定的 API 调用
2. **数据序列化**: 处理 JSON ↔ 原生数据格式转换
3. **错误处理**: 统一错误格式，提供 Agent 友好的错误消息
4. **状态同步**: 保持 Agent 和软件状态的一致性

### 3.2 ReplSkin - 统一 REPL 接口

**核心设计：**

ReplSkin 是 CLI-Anything 的标志性组件，提供了一个**统一的交互式界面**，横跨所有生成的 CLI。

```python
# ReplSkin 概念架构（基于文档推断）

class ReplSkin:
    """
    统一 REPL 接口，为所有 CLI-Anything 生成的 CLI 提供一致的交互体验。
    
    核心职责：
    1. 命令解析和分派
    2. 交互式会话管理
    3. 状态持久化和恢复
    4. 撤销/重做支持
    5. 跨平台兼容的终端处理
    """
    
    def __init__(self, command_registry, session_manager):
        self.command_registry = command_registry
        self.session_manager = session_manager
        self.history = CommandHistory()
        self.state = SessionState()
    
    def run_interactive_loop(self):
        """主交互循环"""
        while self.active:
            # 1. 显示提示符 (支持上下文感知)
            prompt = self._generate_contextual_prompt()
            user_input = self._read_input(prompt)
            
            # 2. 解析命令
            parsed = self._parse_command(user_input)
            
            # 3. 执行命令
            result = self._execute_command(parsed)
            
            # 4. 更新状态和历史
            self._update_state(result)
            self.history.add(parsed, result)
            
            # 5. 输出结果 (支持人类可读和 JSON 两种格式)
            self._render_output(result)
    
    def _execute_command(self, parsed):
        """命令执行，内置 undo/redo 支持"""
        command = self.command_registry.get(parsed.command_name)
        
        # 创建命令快照用于撤销
        if command.modifies_state:
            snapshot = self.state.create_snapshot()
            
        result = command.execute(parsed.args, parsed.kwargs)
        
        if command.modifies_state:
            self.state.register_undo_point(snapshot, result)
            
        return result
```

**ReplSkin 特性：**

| 特性 | 描述 |
|------|------|
| 上下文感知提示符 | 根据当前状态动态调整提示符 |
| 历史记录 | 跨会话的命令历史 |
| Tab 补全 | 命令和参数的自动补全 |
| 内联帮助 | 随时可访问的帮助系统 |
| 撤销/重做 | 跨命令的状态撤销/重做 |
| 状态持久化 | Session 状态的保存和恢复 |

### 3.3 Session 管理设计

**分层状态模型：**

```
┌─────────────────────────────────────────────────────────────┐
│                      Global State                           │
│         (跨所有 session 共享的配置和缓存)                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   Session A   │      │   Session B   │      │   Session C   │
│  (Project 1)  │      │  (Project 2)  │      │  (Project 3)  │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  Undo Stack   │      │  Undo Stack   │      │  Undo Stack   │
├───────────────┤      ├───────────────┤      ├───────────────┤
│ State Snap. 1 │      │ State Snap. 1 │      │ State Snap. 1 │
│ State Snap. 2 │      │ State Snap. 2 │      │ State Snap. 2 │
│ State Snap. 3 │      │ ...           │      │ ...           │
└───────────────┘      └───────────────┘      └───────────────┘
```

**状态管理原则：**

1. **不可变快照**: 每个状态变更前创建完整快照
2. **增量存储**: 只存储状态差异，优化内存使用
3. **序列化支持**: 所有状态可序列化为 JSON
4. **事务边界**: 命令是状态变更的原子单位

**Undo/Redo 实现模式：**

```python
class CommandHistory:
    """
    命令历史管理器，支持撤销和重做
    """
    def __init__(self, max_history=100):
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = max_history
    
    def record(self, command, state_before, state_after):
        """记录命令执行"""
        entry = {
            'command': command,
            'before': state_before,
            'after': state_after,
            'timestamp': time.time()
        }
        self.undo_stack.append(entry)
        self.redo_stack.clear()  # 新操作清空 redo 栈
        
        # 限制历史大小
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
    
    def undo(self):
        """撤销最后一个命令"""
        if not self.undo_stack:
            return None
        
        entry = self.undo_stack.pop()
        self.redo_stack.append(entry)
        return entry['before']  # 恢复到之前的状态
    
    def redo(self):
        """重做最后一个撤销的命令"""
        if not self.redo_stack:
            return None
            
        entry = self.redo_stack.pop()
        self.undo_stack.append(entry)
        return entry['after']  # 恢复到之后的状态
```

### 3.4 命令定义方式

**声明式命令定义模式：**

基于公开信息和架构推断，CLI-Anything 使用声明式方式来定义命令。

```python
# 推断的命令定义模式

@command(
    name="image.resize",
    description="Resize an image to specified dimensions",
    category="image",
    modifies_state=True,
    undoable=True
)
class ImageResizeCommand:
    """
    命令参数使用声明式定义，自动生成 CLI 解析器和帮助文档
    """
    
    # 参数定义 (类型、默认值、验证规则)
    width = Argument(
        type=int,
        required=True,
        help="Target width in pixels",
        validators=[Range(1, 10000)]
    )
    
    height = Argument(
        type=int,
        required=True,
        help="Target height in pixels", 
        validators=[Range(1, 10000)]
    )
    
    maintain_aspect_ratio = Option(
        type=bool,
        default=True,
        help="Maintain aspect ratio when resizing"
    )
    
    output_format = Option(
        type=str,
        choices=["png", "jpg", "webp"],
        default=None,
        help="Output format (defaults to input format)"
    )
    
    def execute(self, ctx: CommandContext) -> CommandResult:
        """
        执行命令的核心逻辑
        
        Args:
            ctx: 包含 session 状态、配置和软件后端的上下文
            
        Returns:
            包含输出数据和状态变更的结果对象
        """
        # 1. 从上下文获取当前状态
        project = ctx.session.get_current_project()
        image = project.get_active_image()
        
        # 2. 创建状态快照 (用于撤销)
        snapshot = image.create_snapshot()
        
        # 3. 执行实际的后端操作
        result = ctx.backend.gimp.resize_image(
            image=image,
            width=self.width,
            height=self.height,
            maintain_aspect_ratio=self.maintain_aspect_ratio,
            output_format=self.output_format
        )
        
        # 4. 构建结果
        return CommandResult(
            success=result.success,
            data={
                "new_dimensions": result.dimensions,
                "file_path": result.output_path,
                "format": result.format
            },
            state_change=StateChange(
                type="image_modified",
                snapshot=snapshot,
                undo_available=True
            )
        )
```

**命令注册和发现机制：**

```python
class CommandRegistry:
    """
    命令注册表，支持自动发现和动态加载
    """
    
    def __init__(self):
        self._commands = {}  # name -> CommandClass
        self._categories = defaultdict(list)
    
    def register(self, command_class):
        """注册命令类"""
        metadata = command_class.__command_metadata__
        name = metadata['name']
        
        self._commands[name] = command_class
        self._categories[metadata['category']].append(name)
        
        # 自动生成 CLI 参数解析器
        self._build_arg_parser(name, command_class)
    
    def discover(self, package_path: str):
        """自动发现包中的所有命令"""
        for module in self._scan_modules(package_path):
            for name, obj in inspect.getmembers(module):
                if hasattr(obj, '__command_metadata__'):
                    self.register(obj)
    
    def get_help_tree(self) -> dict:
        """生成帮助文档树"""
        return {
            category: {
                name: self._commands[name].__doc__
                for name in commands
            }
            for category, commands in self._categories.items()
        }
```

---

## 第四部分：测试策略

### 4.1 多层次测试架构

CLI-Anything 宣称有 1,436 个测试用例，100% 通过率。这需要一个系统化的测试策略。

**三层测试模型：**

```
┌─────────────────────────────────────────────────────────────┐
│                    E2E Tests (150+)                          │
│              真实文件 + 真实软件后端                        │
│         验证完整的用户场景和集成路径                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Integration Tests (500+)                        │
│            CLI 子进程验证 + 模块集成                          │
│        验证命令调度和状态管理                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Unit Tests (786+)                              │
│             合成数据 + Mock 后端                              │
│         验证单个命令和工具函数                                │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 测试组织方式

**按功能领域组织：**

```
tests/
├── conftest.py                 # 全局 fixtures
├── fixtures/                   # 测试数据
│   ├── images/
│   ├── audio/
│   ├── documents/
│   └── projects/
├── unit/
│   ├── commands/              # 命令单元测试
│   ├── session/               # 会话管理测试
│   ├── state/                 # 状态管理测试
│   └── repl/                  # REPL 组件测试
├── integration/
│   ├── backends/              # 后端集成测试
│   ├── cli/                   # CLI 调用测试
│   └── workflows/             # 工作流测试
└── e2e/
    ├── scenarios/             # 端到端场景
    │   ├── image_editing/
    │   ├── audio_processing/
    │   └── document_creation/
    └── regression/            # 回归测试套件
```

### 4.3 测试自动化模式

```python
# 推断的测试辅助工具

class CLITestHarness:
    """
    CLI-Anything 测试的核心辅助类
    """
    
    def __init__(self, cli_path: str, backend_mock=None):
        self.cli = cli_path
        self.backend = backend_mock or RealBackend()
        self.session = TestSession()
    
    def run_command(self, command: str, args: dict = None, 
                    expect_json: bool = True) -> dict:
        """
        运行 CLI 命令并返回结果
        """
        cmd = f"{self.cli} {command}"
        if expect_json:
            cmd += " --json"
        if args:
            cmd += " " + self._format_args(args)
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise CommandFailed(result.stderr)
        
        if expect_json:
            return json.loads(result.stdout)
        return result.stdout
    
    def assert_state_change(self, before: dict, after: dict, 
                           expected_change_type: str):
        """断言状态变更符合预期"""
        # 验证状态变更
        pass
    
    def create_temp_project(self, template: str = None) -> Path:
        """创建临时项目用于测试"""
        # 返回临时项目路径
        pass
    
    def cleanup(self):
        """清理测试产物"""
        # 删除临时文件和会话
        pass
```

---

## 第五部分：应用到我们的工具开发

### 5.1 将模式应用到 .tools/ 目录

**当前结构分析：**

我们的 .tools/ 目录需要向 CLI-Anything 的模式演进：

```
.tools/ 目标结构：

.tools/
├── skill_generator.py          # Skill 生成器（将创建）
├── repl_framework/             # 统一 REPL 组件
│   ├── __init__.py
│   ├── repl_skin.py           # 核心 REPL 引擎
│   ├── session_manager.py     # 会话管理
│   ├── state_manager.py       # 状态管理
│   └── command_registry.py    # 命令注册
├── test_harness/              # 标准化测试框架
│   ├── __init__.py
│   ├── base_test.py           # 测试基类
│   ├── cli_runner.py          # CLI 运行器
│   └── fixtures/             # 测试数据
└── templates/                 # Skill 模板
    ├── basic_skill/
    ├── repl_skill/
    └── advanced_skill/
```

### 5.2 Skill Generator 设计

**生成器功能：**

1. **输入**：技能需求描述（自然语言）
2. **处理**：
   - 分析需求
   - 选择模板
   - 生成命令结构
   - 创建测试骨架
3. **输出**：完整可运行的 Skill 包

---

## 第六部分：关键洞察总结

### 核心架构原则

1. **Agent-First 设计**: 所有设计决策优先考虑 AI Agent 的消费方式
2. **声明式优于命令式**: 使用装饰器和元数据定义命令
3. **统一接口**: ReplSkin 提供一致的交互体验
4. **状态即核心**: 完善的 session 和状态管理
5. **测试驱动**: 1,436 个测试证明了质量的重要性

### 可复用模式

| 模式 | 应用场景 |
|------|----------|
| 桥接层 | 连接 AI Agent 和现有工具 |
| 声明式命令 | 快速定义新技能命令 |
| 状态快照 | 实现 undo/redo 功能 |
| 分层测试 | 保证技能质量 |
| 统一 REPL | 提供一致用户体验 |

---

*报告生成时间：2026-03-12*
*数据来源：CLI-Anything 官方文档、GitHub 仓库公开信息、架构推断*
