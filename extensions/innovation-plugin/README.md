# Innovation Tracker Plugin for OpenClaw

**创新追踪器插件** - 为 OpenClaw 提供强制创新机制

## 功能

- **自动追踪工具调用失败**
- **3次失败后自动锁定方法**
- **阻断被锁定工具的调用**
- **成功调用后自动重置计数器**

## 安装

### 方法1: 作为工作区插件安装（推荐）

```bash
# 进入 OpenClaw 工作区
cd ~/.openclaw/workspace

# 克隆或复制此插件
cp -r extensions/innovation-plugin ~/.openclaw/workspace/.openclaw/extensions/innovation-plugin

# 启用插件
openclaw plugins enable innovation-tracker

# 重启 OpenClaw Gateway
openclaw gateway restart
```

### 方法2: 全局安装

```bash
# 复制到 OpenClaw 全局扩展目录
cp -r extensions/innovation-plugin ~/.openclaw/extensions/innovation-tracker

# 启用
openclaw plugins enable innovation-tracker
```

## 配置

在 `openclaw.json` 中添加配置：

```json
{
  "plugins": {
    "innovation-tracker": {
      "stateFile": ".claw-status/innovation_state.json",
      "maxFailures": 3
    }
  }
}
```

## 工作原理

### before_tool_call Hook
在每次工具调用前执行：
1. 检测工具对应的方法类型
2. 检查该方法是否已被锁定
3. 如果锁定，返回 `block: true` 阻断调用
4. 如果未锁定，允许执行

### after_tool_call Hook
在每次工具调用后执行：
1. 如果调用失败（有 error），增加失败计数
2. 如果失败次数达到阈值，锁定该方法
3. 如果调用成功，重置失败计数器

## 工具映射

| 工具名 | 方法类型 |
|--------|----------|
| web_search | web_search |
| web_fetch | web_fetch |
| browser | browser_automation |
| exec | bash_exec |
| read/write/edit | file_ops |
| pdf | pdf_ops |
| github/git | github_api |

## 状态文件

状态保存在 `.claw-status/innovation_state.json`：

```json
{
  "task_123:github_api": {
    "count": 3,
    "firstFail": "2026-03-17T01:00:00.000Z",
    "lastFail": "2026-03-17T01:05:00.000Z"
  }
}
```

## 日志输出

插件会在控制台输出追踪日志：

```
[InnovationTracker] Initialized with state file: ...
[InnovationTracker] → web_search (web_search)      # 调用前
[InnovationTracker] ✓ web_search SUCCESS           # 调用成功
[InnovationTracker] ✗ web_search FAILED (1/3)      # 调用失败
[InnovationTracker] 🚨 LOCKED: web_search is now locked!  # 达到阈值
[InnovationTracker] 🔒 BLOCKED: github_api is locked      # 阻断调用
```

## 与现有系统的关系

此插件与 `.claw-status/innovation_tracker.py` 共享同一个状态文件，可以：
- 从 Python 脚本查看锁定状态
- 从 Shell 脚本手动重置计数器
- 在插件中自动处理

## 测试

```bash
# 检查插件是否加载
openclaw plugins list

# 查看日志输出（需要 verbose 模式）
openclaw gateway --verbose
```

## 许可证

MIT - 与 OpenClaw 一致
