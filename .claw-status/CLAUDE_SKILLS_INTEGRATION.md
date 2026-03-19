# Claude Skills for OpenClaw

## 安装信息

**仓库**: https://github.com/alirezarezvani/claude-skills  
**本地路径**: `/root/.openclaw/workspace/claude-skills`  
**大小**: 31 MB  
**技能数**: 461个SKILL.md  
**Python工具**: 296个脚本

---

## 快速使用

### 1. 品牌声音分析

```bash
# 分析文本文件的品牌声音
python3 /root/.openclaw/workspace/claude-skills/marketing-skill/content-production/scripts/brand_voice_analyzer.py your-text.txt

# JSON格式输出
python3 /root/.openclaw/workspace/claude-skills/marketing-skill/content-production/scripts/brand_voice_analyzer.py your-text.txt --format json
```

**输出示例**:
```
品牌声音分析报告
================
正式度: 7/10 (Professional)
语气: Authoritative, Informative
视角: Third-person
Flesch可读性: 65 (Standard)
句子结构: 平均18词/句
建议: 减少15%句子长度以提升可读性
```

### 2. SEO优化分析

```bash
# 分析Markdown文件的SEO
python3 /root/.openclaw/workspace/claude-skills/marketing-skill/content-production/scripts/seo_optimizer.py blog-post.md "目标关键词"

# 带次要关键词
python3 /root/.openclaw/workspace/claude-skills/marketing-skill/content-production/scripts/seo_optimizer.py blog-post.md "主关键词" "次要关键词1,次要关键词2"
```

**输出示例**:
```
SEO优化报告
===========
SEO评分: 68/100

关键词密度:
- 主关键词: 0.8% (目标: 1-2%)
- 建议: 增加3次提及

内容结构:
- H2标题: 2个 (建议: 包含主关键词)
- 段落长度: 良好
- 内链: 1个 (建议: 2-3个)

元标签建议:
- Title: AI自动化完整指南 (58字符)
- Description: 探索AI自动化的最佳实践... (155字符)
```

---

## 主要技能目录

| 目录 | 技能数 | 说明 |
|------|--------|------|
| `marketing-skill/` | 43+ | 营销、内容创作、SEO |
| `engineering-team/` | 26+ | 工程、架构、DevOps |
| `product-team/` | 14+ | 产品管理、UX、敏捷 |
| `c-level-advisor/` | 28+ | C级顾问、战略 |
| `project-management/` | 6+ | 项目管理、Jira |
| `ra-qm-team/` | 12+ | 法规、质量、合规 |
| `business-growth/` | 4+ | 业务增长、销售 |
| `finance/` | 2+ | 财务分析、SaaS指标 |

---

## 在OpenClaw中使用

### 方式1: 直接读取SKILL.md

```python
# 读取技能定义
with open('/root/.openclaw/workspace/claude-skills/marketing-skill/content-creator/SKILL.md') as f:
    skill_content = f.read()

# 在对话中引用
# "使用content-creator技能，帮我写一篇文章..."
```

### 方式2: 调用Python工具

```python
import subprocess

# 品牌声音分析
result = subprocess.run([
    'python3', 
    '/root/.openclaw/workspace/claude-skills/marketing-skill/content-production/scripts/brand_voice_analyzer.py',
    'article.txt',
    '--format', 'json'
], capture_output=True, text=True)

analysis = json.loads(result.stdout)
```

### 方式3: 集成到智能路由

```python
# 在wdai系统中使用
from minimax_integration import ModelRouter

# 结合技能做内容创作
# 1. 用M2.7生成初稿
# 2. 用brand_voice_analyzer分析
# 3. 用seo_optimizer优化
# 4. 用Kimi润色
```

---

## 推荐技能

### 内容创作
- `marketing-skill/content-creator/` - 内容创作框架
- `marketing-skill/content-production/` - 内容生产工具
- `marketing-skill/copywriting/` - 文案写作
- `marketing-skill/seo-audit/` - SEO审计

### 工程开发
- `engineering-team/senior-fullstack/` - 全栈开发
- `engineering-team/code-reviewer/` - 代码审查
- `engineering-team/playwright-pro/` - 测试自动化
- `engineering/skill-security-auditor/` - 安全审计

### 产品管理
- `product-team/product-manager-toolkit/` - PM工具包
- `product-team/agile-product-owner/` - 敏捷PO
- `product-team/ux-researcher-designer/` - UX研究

---

## 更新维护

```bash
cd /root/.openclaw/workspace/claude-skills
git pull origin main
```

---

*集成日期: 2026-03-20*  
*版本: 仓库最新版*  
*来源: alirezarezvani/claude-skills*
