# Universal Sources - 通用信息源管理

> 不限于B站，统一管理所有优质信息来源
> 版本: v1.0 | 更新: 2026-03-18

## 信息源分类

### 📺 视频平台
| 平台 | 来源 | 监控方式 | 频率 |
|------|------|----------|------|
| B站 | 收藏夹 | API抓取 | 每日 |
| YouTube | 订阅频道 | RSS | 实时 |
| 抖音 | 关注列表 | 网页监控 | 每日 |

### 📰 技术媒体
| 来源 | 类型 | 监控方式 | 优先级 |
|------|------|----------|--------|
| Hacker News | 社区 | RSS | 高 |
| Lobsters | 社区 | RSS | 高 |
| GitHub Trending | 开源 | API | 高 |
| arXiv (cs.AI) | 论文 | RSS | 中 |
| Papers With Code | 论文+代码 | RSS | 中 |

### 📧 Newsletter
| 来源 | 领域 | 接收方式 |
|------|------|----------|
| TLDR AI | AI综合 | 邮件转发 |
| Import AI | 机器学习 | 邮件转发 |
| The Batch | DeepLearning.AI | 邮件转发 |

### 🎧 播客
| 播客 | 平台 | 监控方式 |
|------|------|----------|
| 待添加 | - | - |

---

## ✅ 已配置监控列表 (2026-03-18)

### 📺 YouTube
| 频道 | 等级 | 监控频率 | RSS地址 |
|------|:----:|----------|---------|
| **@Yonggie** | A (8.5) | 每日检查 | https://www.youtube.com/feeds/videos.xml?channel_id=UCYjwzfvKIQpgJ7aRjE5B-QQ |
| 说明: 中文AI深度解析，Claude/LLM前沿解读 | | | |

### 📧 Newsletter
| 来源 | 等级 | 频率 | 接收方式 |
|------|:----:|------|----------|
| **TLDR AI** | A (8.5) | 每日 | tldrnewsletter.com/ai |
| **Import AI** | A- (8.0) | 每周 | importai.substack.com |
| 说明: 每日AI精选 + 深度技术解读 | | | |

### 📝 技术博客
| 博客 | 作者 | 等级 | RSS地址 |
|------|------|:----:|---------|
| **Anthropic Blog** | Anthropic | S (9.5) | anthropic.com/research/rss.xml |
| **Lil'Log** | Lilian Weng | A+ (9.0) | lilianweng.github.io/rss.xml |
| **Simon Willison** | Simon Willison | A (8.5) | simonwillison.net/atom.xml |
| 说明: 官方研究 + 权威解读 + 工具实践 | | | |

### 📺 B站 (原有)
| UP主 | UID | 等级 | 监控方式 | 说明 |
|------|-----|:----:|----------|------|
| **慢学AI** | 28321599 | A (8.5) | 收藏夹同步 | Claude官方解读 |
| **橘鸦Juya** | 285286947 | A (8.3) | UID监控 | AI早报 |
| **黑客酒吧** | 328460261 | B+ | UID监控 | AI/系统安全 |
| **许粲昊ThomasCXu** | 524313676 | B+ | UID监控 | AI方向，1.2万粉 |
| **吴恩达Agentic** | 3546982291343656 | A | UID监控 | 大模型+论文指导 |
| **唐国梁Tommy** | 474347248 | A | UID监控 | AI算法研究工程师 |
| **探索未至之境** | 441831884 | B | UID监控 | 哲学/认知/多样性 |

**说明**: Claude官方解读 + AI早报 + 安全专项 + AI内容 + 专家UP + 认知类

---

## 监控策略总览

| 来源 | 推送阈值 | 推送方式 |
|------|----------|----------|
| Anthropic Blog | 所有文章 | 立即推送 🔔 |
| Lil'Log | 所有文章 | 立即推送 🔔 |
| @Yonggie | ≥1.5分 | 立即推送 🔔 |
| 慢学AI | ≥1.0分 | 立即推送 🔔 |
| 橘鸦Juya | ≥1.2分 | 每日汇总 📋 |
| **黑客酒吧** | **≥1.0分** | **每日汇总 📋** |
| **许粲昊ThomasCXu** | **≥1.0分** | **每日汇总 📋** |
| TLDR AI | ≥1.0分 | 每日汇总 📋 |
| Import AI | ≥0.8分 | 每周汇总 📊 |
| Simon Willison | ≥1.0分 | 选择性推送 |

---

## 添加新来源的3种方式

### 方式1: 用户主动添加（推荐）
当你发现好内容时，直接发给我：

```
你: "这个YouTube频道不错: @codebullet"
我: ✅ 已添加到监控列表 (codebullet)
     领域: AI/编程
     优先级: 高
     下次同步时纳入监控
```

### 方式2: 自动反向追踪
你收藏/点赞的内容，系统自动提取来源：
- 视频 → 提取UP主/频道
- 文章 → 提取作者/博客
- 项目 → 提取作者GitHub

### 方式3: 社区推荐
从相似用户的行为中学习（需要多用户数据）

## 统一评分系统

所有来源的内容都用同一个**品味模型**评分：

```
输入: 任意平台的内容
  ↓
提取特征: 标题/作者/关键词/时长
  ↓
品味模型评分 (0-2.0)
  ↓
分级处理:
  ≥1.2 → 立即推送
  0.7-1.2 → 每日汇总  
  <0.7 → 周报/忽略
```

## 当前已接入

| 平台 | 状态 | 来源数 | 备注 |
|------|------|--------|------|
| B站收藏夹 | ✅ 运行中 | 8个UP主 | 每日同步 |
| **YouTube** | **✅ 已配置** | **1个频道** | **@Yonggie** |
| **Newsletter** | **✅ 已配置** | **2个订阅** | **TLDR AI, Import AI** |
| **技术博客** | **✅ 已配置** | **3个博客** | **Anthropic, Lil'Log, Simon Willison** |
| Hacker News | ⏳ 待配置 | - | 需要RSS地址 |
| GitHub Trending | ⏳ 待配置 | - | 需要关键词 |

## 添加新来源模板

```yaml
source_name: "来源名称"
platform: "bilibili|youtube|newsletter|github|..."
url: "来源地址"
category: "ai|programming|productivity|..."
trust_level: 1-10  # 你的信任度
auto_notify: true  # 是否自动推送高分内容
```

## 快速添加命令

当你发现好内容时，可以直接发给我：

```
添加信息源:
- 平台: YouTube
- 频道: @SomeAIChannel
- 原因: 讲Claude Agent很深入
- 优先级: 高
```

我会立即：
1. 解析频道信息
2. 添加到监控列表
3. 下次运行开始追踪
4. 反馈已添加的来源

---

**如何扩展？发给我任何好内容的链接，我会自动分析并决定是否加入监控列表。**


---

## 🔧 GitHub仓库监控 (2026-03-18新增)

### S级 - Anthropic官方 (立即通知)
| 仓库 | 组织 | 领域 | 监控内容 |
|------|------|------|----------|
| **claude-code** | Anthropic | AI编程工具 | Release更新 |
| **anthropic-cookbook** | Anthropic | 最佳实践 | Commit/Release |
| **anthropic-sdk-python** | Anthropic | Python SDK | Release更新 |

### A+级 - 核心工具 (立即/每日通知)
| 仓库 | 作者 | 领域 | 监控内容 |
|------|------|------|----------|
| **aider** | Aider-AI | AI结对编程 | Release |
| **langgraph** | LangChain | Agent工作流 | Release |
| **continue** | ContinueDev | IDE插件 | Release |

### A级 - 重要框架 (每日通知)
| 仓库 | 作者 | 领域 | 监控内容 |
|------|------|------|----------|
| **crewAI** | CrewAI | 多Agent协作 | Release |
| **mem0** | Mem0AI | AI记忆层 | Release |
| **E2B** | E2B | AI沙箱环境 | Release |

### B+级 - 辅助工具 (每周通知)
| 仓库 | 作者 | 领域 | 监控内容 |
|------|------|------|----------|
| **langchain** | LangChain | Agent框架 | Major Release |
| **llama_index** | LlamaIndex | RAG框架 | Major Release |
| **browser-use** | BrowserUse | AI浏览器控制 | Release |
| **AutoGPT** | SignificantGravitas | 经典Agent | Major Release |

### 📈 Trending监控
| 类型 | 监控方式 | 阈值 | 推送策略 |
|------|----------|------|----------|
| GitHub Trending AI | 日增Star数 | >100/日 | 每日精选 |

---

## 📊 监控状态总览 (2026-03-18)

| 平台 | 数量 | 等级分布 |
|------|------|----------|
| B站 | 2个UP主 | A级x2 |
| YouTube | 1个频道 | A级 |
| Newsletter | 2个订阅 | A级x1, A-级x1 |
| 技术博客 | 3个博客 | S级x1, A+级x1, A级x1 |
| **GitHub** | **14个仓库+Trending** | **S级x3, A+级x3, A级x4, B+级x4** |
| **总计** | **24个核心来源** | **全覆盖AI领域** |

---

*最后更新: 2026-03-18*  
*版本: v2.0 - 添加GitHub全量监控*
