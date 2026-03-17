# GitHub 备份指南

本指南帮助你将 wdai 系统备份到 GitHub 仓库。

---

## 方法一：使用 GitHub CLI（推荐）

### 1. 安装 GitHub CLI

```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# 其他系统
# 访问 https://github.com/cli/cli/releases
```

### 2. 登录 GitHub

```bash
gh auth login
```

按照提示完成登录。

### 3. 运行推送脚本

```bash
cd /root/.openclaw/workspace
chmod +x push_to_github.sh
./push_to_github.sh your-github-username
```

---

## 方法二：手动推送

### 1. 在 GitHub 上创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `wdai` (或你喜欢的名字)
   - **Description**: `wdai - Working Directory Adaptive Intelligence System`
   - **Visibility**: Public 或 Private
   - **不要勾选** "Initialize this repository with a README"
3. 点击 "Create repository"

### 2. 添加远程仓库

```bash
cd /root/.openclaw/workspace
git remote add origin https://github.com/YOUR_USERNAME/wdai.git
```

### 3. 推送代码

```bash
git branch -M master
git push -u origin master
```

---

## 方法三：使用 SSH 密钥

如果你有 SSH 密钥配置：

```bash
# 添加远程仓库（SSH方式）
git remote add origin git@github.com:YOUR_USERNAME/wdai.git

# 推送
git push -u origin master
```

---

## 验证推送

推送完成后，访问：

```
https://github.com/YOUR_USERNAME/wdai
```

你应该能看到完整的 wdai 系统文件。

---

## 后续更新

当系统有更新时：

```bash
cd /root/.openclaw/workspace

# 添加所有更改
git add .

# 提交
git commit -m "描述本次更新"

# 推送到GitHub
git push
```

---

## 仓库内容说明

推送完成后，GitHub仓库将包含：

```
wdai/
├── README.md           # 项目说明
├── LICENSE             # MIT许可证
├── SOUL.md            # 核心人格
├── AGENTS.md          # Agent协作规则
├── USER.md            # 用户画像
├── MEMORY.md          # 长期记忆索引
├── TOOLS.md           # 工具配置
├── .principles/       # 核心原则库
├── .state/            # 持久状态系统
├── .evolution/        # 进化系统
├── .claw-status/      # 系统状态
├── .github_discovery/ # GitHub发现
├── memory/            # 记忆系统
└── skills/            # 技能库
```

---

## 故障排除

### 问题：remote origin already exists

**解决**:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/wdai.git
```

### 问题：Permission denied

**解决**: 检查GitHub凭据或Token权限

### 问题：仓库已存在

**解决**: 如果你要覆盖现有仓库：
```bash
git push -f origin master
```
**注意**: 这会覆盖远程仓库的所有内容！

---

## 备份完成后的建议

1. **启用GitHub Actions**: 可以设置自动测试或文档生成
2. **添加Issue模板**: 方便追踪改进提案
3. **启用Dependabot**: 自动检查依赖更新
4. **设置Branch Protection**: 保护master分支

---

## 需要帮助？

参考：
- [GitHub Docs](https://docs.github.com)
- [Git 文档](https://git-scm.com/doc)
