---
name: autocode-reviewer
version: 1.0.0
description: 自动代码审查工具，支持PR分析、代码质量检查、风格建议和Bug检测
author: OpenClaw Community
license: MIT
allowed-tools: Bash(git:*) Read Write Edit exec
---

# AutoCodeReviewer - 自动代码审查

## 功能概述

AutoCodeReviewer 是一个自动化代码审查工具，集成到OpenClaw中，可以：
- 自动分析Pull Request
- 检测代码风格问题
- 发现潜在的Bug和性能问题
- 提供可操作的改进建议
- 直接在GitHub/GitLab/Bitbucket上评论

## 适用场景

当用户提到以下关键词时激活此Skill：
- "审查PR"、"review PR"
- "代码审查"、"code review"
- "检查代码"、"check code"
- "分析提交"、"analyze commit"
- "代码质量"、"code quality"

## 工作流程

### 1. 获取PR信息
1. 使用git命令获取PR的diff
2. 解析文件变更列表
3. 读取变更文件的完整内容

### 2. 代码分析
分析维度包括：
- **风格检查**：命名规范、缩进、空格
- **Bug检测**：空指针、未处理异常、资源泄漏
- **性能建议**：低效循环、冗余计算
- **安全扫描**：SQL注入、XSS漏洞
- **最佳实践**：代码复用、单一职责

### 3. 生成报告
输出格式：
```
📋 PR审查报告 #XXX
━━━━━━━━━━━━━━━━━━━━

🔴 严重问题 (X个)
- 文件:path/to/file.py:45
  问题: [描述]
  建议: [修复方案]

🟡 改进建议 (X个)
- 文件:path/to/file.py:78
  问题: [描述]
  建议: [改进方案]

🟢 风格问题 (X个)
- 文件:path/to/file.py:120
  问题: [描述]
  建议: [规范方案]

✅ 总体评价: [A/B/C/D]
```

## 使用方法

### 基础审查
```
审查PR #42
review PR #42
检查这个PR的代码
```

### 指定仓库
```
审查 openclaw/skills PR #15
review PR #42 in repo myproject/backend
```

### 批量审查
```
审查所有开放的PR
review all open PRs
```

### 对比分支
```
比较 main 和 feature-branch
review diff between main and develop
```

## 配置选项

在 `~/.openclaw/skills/autocode-reviewer/config.yaml` 中配置：

```yaml
review_rules:
  style_check: true        # 代码风格检查
  bug_detection: true      # Bug检测
  performance: true        # 性能建议
  security: true           # 安全扫描
  complexity: true         # 复杂度分析
  
languages:
  - python
  - javascript
  - typescript
  - go
  - rust
  - java
  
severity_threshold: "warning"  # 报告阈值: error/warning/info
comment_style: "detailed"      # 详细程度: brief/detailed/verbose
auto_fix: false                # 是否自动修复（谨慎使用）

exclude_patterns:
  - "*.test.js"
  - "*_test.py"
  - "vendor/"
  - "node_modules/"
```

## 支持的代码规范

### Python
- PEP 8
- Google Python Style Guide
- pylint规则

### JavaScript/TypeScript
- ESLint推荐规则
- Airbnb Style Guide
- Prettier格式

### Go
- gofmt标准
- golint规则

## 注意事项

1. **需要GitHub Token**：配置 `GITHUB_TOKEN` 环境变量或运行 `claw config github`
2. **权限要求**：需要repo读取权限
3. **网络访问**：需要访问GitHub/GitLab API
4. **Token消耗**：大PR可能消耗较多tokens

## 安全提醒

- 不要公开分享审查报告中的敏感信息
- 审查结果仅供参考，重要代码仍需人工审核
- 自动修复功能谨慎使用，建议先 review 再应用
