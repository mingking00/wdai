# CodeDev Agent - 代码开发Agent

基于ChatDev角色分工模式的专门代码开发Agent，集成IER（迭代经验精炼）系统。

## 特点

- 🎭 **多角色协作**: 架构师、开发者、测试员、审查员
- 🔄 **瀑布模型**: 设计 → 开发 → 审查 → 测试
- 🛡️ **防幻觉机制**: 执行前先澄清需求
- 📝 **完整报告**: 每个角色的贡献清晰可见
- ⚙️ **常驻服务**: 后台运行，随时响应
- 🧠 **IER经验系统**: 迭代经验精炼，持续学习改进

## 🧠 IER迭代经验精炼系统

基于ChatDev论文 ["Iterative Experience Refinement of Software-Developing Agents"](https://arxiv.org/abs/2405.04219)

### IER四大核心机制

```
┌─────────────────────────────────────────────────────────────┐
│                   IER 迭代经验精炼系统                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Experience Acquisition (经验获取)                        │
│     └── 从任务执行中提取经验                                  │
│         ├── Pattern经验：设计模式                            │
│         ├── Shortcut经验：特定场景快捷方案                    │
│         ├── Tool经验：工具使用技巧                           │
│         └── Optimization经验：优化技巧                       │
│                                                              │
│  2. Experience Utilization (经验利用)                        │
│     └── 在新任务中应用已有经验                                │
│         ├── 相关性计算                                        │
│         ├── 经验排序                                          │
│         └── 注入Prompt                                        │
│                                                              │
│  3. Experience Propagation (经验传播)                        │
│     └── 在相似场景间传播经验                                  │
│         ├── 经验适配                                          │
│         └── 经验合并                                          │
│                                                              │
│  4. Experience Elimination (经验淘汰)                        │
│     └── 移除过时或错误的经验                                  │
│         ├── 成功率检查                                        │
│         ├── 使用频率检查                                      │
│         └── 版本替代检查                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 经验类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **Shortcut** | 快捷方案 | "使用列表推导式替代循环" |
| **Pattern** | 设计模式 | "使用装饰器模式实现缓存" |
| **Anti-Pattern** | 反模式 | "避免在循环中使用字符串拼接" |
| **Tool** | 工具技巧 | "使用lru_cache优化递归" |
| **Lesson** | 教训 | "忘记检查文件存在性导致错误" |
| **Optimization** | 优化 | "使用set替代list进行查找" |

### IER工作流程

```
新任务到达
    ↓
[IER检索] 查找相关经验
    ↓
[经验注入] 将经验加入Architect Prompt
    ↓
[Chat Chain] 多角色协作开发
    ↓
[IER提取] 从新代码中提取经验
    ↓
[IER记录] 记录任务使用经验的结果
    ↓
定期[IER淘汰] 移除过时经验
```

### IER命令

```bash
# 查看IER统计
./codedev.sh ier-stats

# 列出所有经验
./codedev.sh ier-list

# 列出特定类型经验
./codedev.sh ier-list pattern
./codedev.sh ier-list shortcut
./codedev.sh ier-list optimization

# 运行经验维护（淘汰过时经验）
./codedev.sh ier-maintain
```

### IER统计信息

```
总经验数: 25
活跃经验: 22
可靠经验: 15
历史任务: 50

按类型分布:
  pattern: 8
  shortcut: 10
  optimization: 5
  lesson: 2
```

## 🧠 架构师的架构思维框架

CodeDev Agent的架构师角色集成了系统化的架构思维方法：

### 1. 第一性原理分析 (First Principles Thinking)
```
表面需求 → 本质需求 → 基本组成部分 → 物理约束 → 重构方案
```
**问题清单**:
- 这个需求的本质是什么？
- 最基本的组成部分有哪些？
- 物理/逻辑约束是什么？
- 剥离所有假设后，还剩什么？

### 2. 双路径认知架构 (System 1 / System 2)
| 路径 | 适用场景 | 策略 |
|------|----------|------|
| **System 1** (快) | 熟悉任务、时间敏感 | 模式匹配、经验复用 |
| **System 2** (慢) | 复杂问题、高错误成本 | 深度推理、验证假设 |

架构师会自动评估："这个问题适合用哪种路径？"

### 3. 物理现实检查 (Physical Reality Check)
```
概念识别 → 约束查询 → 假设验证 → 文献查证
```
**检查清单**:
- [ ] 涉及的实体是什么？
- [ ] 时间尺度合理吗？（秒级vs分钟级）
- [ ] 资源限制考虑了吗？（CPU/内存/网络/存储）
- [ ] 失败模式有哪些？

### 4. 系统边界识别 (System Boundary Analysis)
```
输入边界 → 处理边界 → 输出边界 → 故障边界
```
**关键问题**:
- 输入承诺什么？不承诺什么？
- 核心逻辑 vs 边缘情况
- 输出在什么条件下失效？
- 如何优雅降级？

### 5. 元认知检查 (Meta-Cognitive Check)
设计完成后，架构师会自问：
- 我做了什么假设？这些假设成立吗？
- 这是最简方案吗？有没有更短路径？
- 如果我的设计错了，Plan B是什么？
- 这个设计在极端情况下会怎样？

### 6. 反模式警示 (Anti-Pattern Alert)
架构师会警惕：
- ❌ 流程迷信: "上次这样做成功了"
- ❌ 过度推断: "用户说A，我就做A+B+C"
- ❌ 完美主义: "要做到100分才交付"
- ❌ 单一视角: 只从技术角度思考

## 架构师输出结构

```markdown
# 架构设计报告

## 1. 需求的第一性原理解构
- 表面需求：...
- 本质需求：...
- 根本约束：...

## 2. 双路径分析
### System 1 (模式识别)
- 匹配的模式：...

### System 2 (深度推理)
- 隐藏假设：...

## 3. 物理现实检查
- 实体约束：...
- 资源限制：...

## 4. 系统边界分析
- 输入边界：...
- 处理边界：...
- 输出边界：...
- 故障边界：...

## 5. 技术方案
### 方案A（推荐）
- 设计思路
- 核心数据结构
- 关键算法
- 接口定义
- 复杂度分析

### 方案B（备选）
- 适用场景
- 优缺点

## 6. 风险评估
- 技术风险
- 性能风险
- 应对策略

## 7. 元认知检查
- 关键假设
- 验证方法
- Plan B
```

## 架构

```
CodeDev Agent Service
    ├── Architect (架构师) - 应用架构思维框架
    │   └── 第一性原理 → 双路径分析 → 物理检查 → 边界识别
    ├── Developer (开发者)
    │   └── 编写完整可运行的代码
    ├── Reviewer (审查员)
    │   └── 审查代码质量
    └── Tester (测试员)
        └── 验证代码正确性
```

## 快速开始

### 1. 启动服务

```bash
cd /root/.openclaw/workspace/skills/code-dev-agent

./codedev.sh start      # 启动服务
./codedev.sh status     # 查看状态
./codedev.sh logs       # 查看日志
```

### 2. 提交开发请求

```bash
# 基本用法
./codedev.sh dev "创建一个Python函数，计算斐波那契数列"

# 指定语言
./codedev.sh dev "创建一个JavaScript防抖函数" javascript

# 复杂需求
./codedev.sh dev "创建一个带缓存的HTTP客户端，支持自动重试和超时控制"
```

### 3. 查看结果

```bash
# 列出所有结果
./codedev.sh result

# 查看特定结果
./codedev.sh result CODEDEV_20260315_120000
```

## 使用示例

### 示例1: 简单函数

```bash
$ ./codedev.sh dev "创建一个函数，判断字符串是否为回文"

✓ 已提交开发请求
  请求ID: CODEDEV_20260315_143022
  语言: python

正在处理中，请稍候...
✓ 处理完成!

执行流程:
  architect: completed
  developer: completed
  reviewer: completed
  tester: completed

最终输出预览:
def is_palindrome(s: str) -> bool:
    \"\"\"判断字符串是否为回文\"\"\"
    ...
```

### 示例2: 架构设计（展示思维框架）

```bash
$ ./codedev.sh dev "设计一个API速率限制器，防止服务被滥用"

✓ 处理完成!

架构师输出:
# 架构设计报告

## 1. 需求的第一性原理解构
- 表面需求：限制API调用频率
- 本质需求：保护资源，防止滥用，保证公平性
- 根本约束：分布式环境、高并发、低延迟

## 2. 双路径分析
### System 1
- 模式匹配：令牌桶、漏桶、滑动窗口

### System 2
- 隐藏假设：所有请求权重相同？时间同步精准？

## 3. 物理现实检查
- Redis作为存储，网络延迟1-5ms
- 并发10k QPS，内存限制
- 失败模式：Redis不可用、时钟漂移
...
```

## 程序化调用

```python
from codedev_service import get_service, submit_code_request, get_code_result

# 获取服务实例
service = get_service()
service.start()

# 提交请求
request_id = service.submit_request(
    description="创建一个日志装饰器",
    language="python",
    requirements=["支持异步函数", "可配置日志级别"],
    constraints=["不要依赖第三方库"]
)

# 等待结果
import time
time.sleep(30)

# 获取结果
result = service.get_result(request_id)
if result and result['success']:
    print("开发完成!")
    for step in result['results']:
        print(f"{step['role']}: {step['status']}")
    
    # 查看架构师的详细分析
    architect_output = result['results'][0]['result']
    print(architect_output)
```

## 工作流程

```
用户请求
    ↓
[Architect] 应用架构思维框架
    ├── 第一性原理解构需求
    ├── 双路径分析方案
    ├── 物理现实检查
    ├── 系统边界识别
    └── 元认知检查
    ↓
[Developer] 根据架构设计编写代码
    ↓
[Reviewer] 审查代码质量
    ↓
[Tester] 验证正确性
    ↓
生成报告，返回结果
```

## 文件结构

```
skills/code-dev-agent/
├── codedev_service.py      # 服务主体（含架构思维框架）
├── codedev.sh              # 管理脚本
├── README.md               # 使用说明
├── requests/               # 请求队列
├── results/                # 结果存储
└── logs/                   # 日志文件
```

## 角色说明

### Architect (架构师)
- **架构思维框架**: 第一性原理、双路径认知、物理现实检查
- **输出**: 结构化架构设计报告
- **核心能力**: 深度分析、风险评估、方案对比

### Developer (开发者)
- 编写完整代码
- 处理边界情况
- 编写文档注释
- 确保代码可运行

### Reviewer (审查员)
- 审查代码质量
- 评估可维护性
- 检查设计模式
- 给出改进建议

### Tester (测试员)
- 逐行审查逻辑
- 发现潜在bug
- 验证需求满足度
- 提出修改建议

## 防幻觉机制 (Communicative Dehallucination)

CodeDev实现了**强化版ChatDev防幻觉机制**，专门针对代码开发场景：

### 核心机制

**1. 多轮澄清 (Multi-Round Clarification)**
```
第1轮: 识别模糊点 → 提问 → 回答
第2轮: 识别剩余模糊点 → 提问 → 回答  
第3轮: 确认就绪 → READY_TO_CODE
```

**2. 代码开发专用检查清单 (Code-Specific Checklist)**

| 检查维度 | 关键问题 | 防止的幻觉 |
|----------|----------|------------|
| **输入边界** | 参数类型？范围？空值？ | 假设输入总是有效 |
| **输出承诺** | 返回类型？失败时？ | 返回类型不一致 |
| **边界情况** | 空输入？超大输入？ | 忽略边界处理 |
| **错误处理** | 异常类型？错误信息？ | 不完整的try-catch |
| **性能要求** | 复杂度？优化？ | 性能不达预期 |
| **依赖集成** | 标准库？第三方？ | 未声明的依赖 |

**3. 双重验证 (Dual Verification)**

**第一遍：生成代码**
- 基于澄清后的完整上下文
- 强制代码完整性检查清单

**第二遍：自我审查**
- 自动检查代码幻觉：
  - ❌ 未实现的占位符 (pass/TODO/ellipsis)
  - ❌ 假设但未验证的输入
  - ❌ 引用但未定义的变量/函数
  - ❌ 不完整的错误处理
  - ❌ 未处理的边界情况
- 自动修复发现的问题

### 防幻觉示例

**传统方式（易产生幻觉）**：
```python
# 用户："创建一个函数处理用户输入"
def process_data(data):
    # 幻觉：假设data总是dict
    return data["value"] * 2  # 可能KeyError
```

**CodeDev方式（防幻觉）**：
```python
# 澄清阶段识别的关键问题：
# 1. data的类型是什么？→ 可能是dict/list/str
# 2. 如何处理无效输入？→ 验证+异常
# 3. value字段一定存在吗？→ 需要检查

def process_data(data):
    """处理用户输入数据。
    
    Args:
        data: 输入数据，支持dict/list
        
    Returns:
        处理后的结果
        
    Raises:
        TypeError: 输入类型不支持
        ValueError: 数据格式无效
    """
    if not isinstance(data, (dict, list)):
        raise TypeError(f"不支持的数据类型: {type(data)}")
    
    if isinstance(data, dict):
        if "value" not in data:
            raise ValueError("字典缺少'value'字段")
        return data["value"] * 2
    
    return [item * 2 for item in data]
```

### 工作流程

```
用户请求
    ↓
[Architect] 应用架构思维框架
    ├── 第一性原理解构需求
    ├── 双路径分析方案
    ├── 物理现实检查
    ├── 系统边界识别
    └── 元认知检查
    ↓
[Developer] 防幻觉代码生成
    ├── 多轮澄清需求细节
    ├── 生成代码
    └── 自我审查修复
    ↓
[Reviewer] 审查代码质量
    ↓
[Tester] 验证正确性
    ↓
生成报告，返回结果
```

## 高级配置

### 自定义架构师Prompt

编辑 `codedev_service.py` 中的 `ROLES[RoleType.ARCHITECT]`，修改：

```python
system_prompt="""你的自定义架构思维框架..."""
```

### 调整工作流

修改 `_create_and_execute_chain` 方法：

```python
nodes = [
    ChatNode(id="analyze", role_type=RoleType.ARCHITECT, task="深度分析"),
    ChatNode(id="design", role_type=RoleType.ARCHITECT, task="架构设计"),
    ChatNode(id="code", role_type=RoleType.DEVELOPER, task="编写代码"),
    # 添加更多节点...
]
```

## 故障排除

### 服务无法启动
```bash
# 检查日志
cat logs/service.log

# 检查Python环境
python3 --version

# 手动启动查看错误
python3 codedev_service.py
```

### 请求处理超时
```bash
# 检查服务状态
./codedev.sh status

# 查看是否有堆积的请求
ls requests/

# 重启服务
./codedev.sh restart
```

### 结果不符合预期
- 检查需求描述是否清晰
- 考虑添加更多约束条件
- 查看架构师的详细分析输出

## 与现有Agent的关系

| Agent | 职责 | 区别 |
|-------|------|------|
| **CodeDev** | 专门代码开发 | 多角色协作，瀑布模型，架构思维框架 |
| **SEA** | 系统进化 | 改进现有代码 |
| **MARS** | 研究 | 信息收集分析 |
| **SRA** | 复盘 | 自我反思总结 |

**协作方式**:
- 需要写新代码 → CodeDev
- 需要改进现有代码 → SEA
- 需要研究技术 → MARS
- 需要总结经验 → SRA

## 未来计划

- [ ] 接入真实LLM接口
- [ ] 支持更多编程语言
- [ ] 代码执行验证
- [ ] 单元测试生成
- [ ] 可视化工作流
- [ ] 与SEA集成（改进生成的代码）

---

*基于ChatDev论文实现: https://github.com/OpenBMB/ChatDev*
*架构思维框架参考自SOUL.md和AGENTS.md*
