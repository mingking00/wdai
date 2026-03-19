# Kimi Claw 内部MCP接口设计方案

**版本**: v1.0  
**设计时间**: 2026-03-10  
**技能总数**: 85个（归类为12个领域）

---

## 一、架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Kimi Claw MCP Server                     │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Core Tools │  │ File Tools  │  │  Web Tools  │          │
│  │  (核心工具)  │  │  (文件操作)  │  │  (网络访问)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │Comm Tools   │  │Media Tools  │  │Agent Tools  │          │
│  │(通信协作)    │  │(媒体处理)    │  │(代理增强)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │Research     │  │Productivity │  │System Tools │          │
│  │(研究分析)    │  │(生产力)      │  │(系统管理)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │   MCP Client   │
                    │   (Kimi Core)  │
                    └────────────────┘
```

### 1.2 命名规范

```
命名格式: <domain>_<action>_<target>

示例:
- file_read_text        # 文件领域-读取操作-文本目标
- web_search_brave      # 网络领域-搜索操作-Brave引擎
- comm_send_message     # 通信领域-发送操作-消息目标
- research_deep_search  # 研究领域-深度操作-搜索目标
```

---

## 二、Tools 详细设计

### 2.1 Core Tools (核心工具)

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `core_plan_task` | 任务规划 | `task`, `complexity`, `time_budget` | 执行计划 |
| `core_reflect_on_work` | 工作反思 | `session_id`, `focus_area` | 反思报告 |
| `core_route_system` | 系统路由 | `task_type`, `urgency` | System 1/2 |
| `core_evaluate_output` | 输出评估 | `content`, `criteria` | 质量评分 |
| `core_decompose_problem` | 问题分解 | `problem`, `depth` | 子任务列表 |

**映射来源**: advanced-planner, workflow-orchestrator, cognitive-transparency

---

### 2.2 File Tools (文件操作) - 12个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `file_read_text` | 读取文本文件 | `path`, `offset`, `limit` | 文件内容 |
| `file_write_text` | 写入文本文件 | `path`, `content`, `append` | 成功状态 |
| `file_edit_text` | 编辑文本文件 | `path`, `old_text`, `new_text` | 成功状态 |
| `file_list_directory` | 列出目录 | `path`, `pattern` | 文件列表 |
| `file_pdf_extract` | PDF内容提取 | `path`, `pages`, `mode` | 文本/Markdown |
| `file_pdf_create` | 创建PDF | `source_paths`, `output_path` | PDF文件 |
| `file_docx_read` | 读取Word文档 | `path` | 文档内容 |
| `file_docx_create` | 创建Word文档 | `content`, `output_path` | DOCX文件 |
| `file_xlsx_read` | 读取Excel | `path`, `sheet` | 表格数据 |
| `file_xlsx_create` | 创建Excel | `data`, `output_path` | XLSX文件 |
| `file_pptx_read` | 读取PPT | `path` | 幻灯片内容 |
| `file_pptx_create` | 创建PPT | `slides`, `output_path` | PPTX文件 |
| `file_md_to_pdf` | Markdown转PDF | `md_path`, `output_path` | PDF文件 |

**映射来源**: pdf, docx, xlsx, pptx, md-to-pdf

---

### 2.3 Web Tools (网络访问) - 6个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `web_search_brave` | Brave搜索 | `query`, `count`, `freshness` | 搜索结果 |
| `web_fetch_page` | 网页抓取 | `url`, `extract_mode`, `max_chars` | 页面内容 |
| `web_browser_open` | 浏览器打开 | `url`, `profile` | 页面快照 |
| `web_browser_act` | 浏览器操作 | `action`, `target`, `params` | 操作结果 |
| `web_screenshot` | 网页截图 | `url`, `full_page` | 图片路径 |
| `web_dogfood_test` | 应用测试 | `app_url`, `test_type` | 测试报告 |

**映射来源**: agent-browser, dogfood

---

### 2.4 Communication Tools (通信协作) - 10个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `comm_send_message` | 发送消息 | `channel`, `target`, `message` | 发送状态 |
| `comm_list_channels` | 列出频道 | `platform` | 频道列表 |
| `comm_read_history` | 读取历史 | `channel`, `limit` | 消息列表 |
| `comm_slack_search` | Slack搜索 | `query`, `channels` | 搜索结果 |
| `comm_discord_send` | Discord发送 | `channel_id`, `content` | 发送状态 |
| `comm_imessage_send` | iMessage发送 | `recipient`, `message` | 发送状态 |
| `comm_trello_card` | Trello卡片 | `board`, `list`, `title` | 卡片信息 |
| `comm_notion_page` | Notion页面 | `database`, `properties` | 页面链接 |
| `comm_obsidian_note` | Obsidian笔记 | `vault`, `title`, `content` | 笔记路径 |
| `comm_apple_note` | Apple笔记 | `title`, `content` | 笔记ID |

**映射来源**: slack, discord, imsg, trello, notion, obsidian, apple-notes

---

### 2.5 Media Tools (媒体处理) - 10个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `media_image_generate` | 生成图片 | `prompt`, `size`, `style` | 图片URL/路径 |
| `media_image_edit` | 编辑图片 | `image_path`, `edit_prompt` | 编辑后图片 |
| `media_audio_tts` | 文字转语音 | `text`, `voice`, `speed` | 音频文件 |
| `media_audio_transcribe` | 语音转文字 | `audio_path`, `language` | 转录文本 |
| `media_video_frames` | 视频帧提取 | `video_path`, `interval` | 帧图片集 |
| `media_gif_search` | GIF搜索 | `query`, `limit` | GIF链接列表 |
| `media_gif_create` | 创建GIF | `frames`, `duration` | GIF文件 |
| `media_canvas_present` | Canvas展示 | `content`, `format` | 展示状态 |
| `media_canvas_snapshot` | Canvas截图 | `format` | 图片路径 |
| `media_art_generate` | 艺术生成 | `style`, `parameters` | 艺术作品 |

**映射来源**: openai-image-gen, openai-whisper, video-frames, canvas, algorithmic-art, slack-gif-creator

---

### 2.6 Agent Enhancement Tools (代理增强) - 12个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `agent_research_orchestrate` | 研究编排 | `topic`, `sources`, `depth` | 研究报告 |
| `agent_deep_research` | 深度研究 | `topic`, `evaluation_criteria` | 深度报告 |
| `agent_daily_report` | 日报生成 | `date`, `categories` | 日报PDF |
| `agent_coding_assist` | 编程辅助 | `code`, `task`, `language` | 代码/建议 |
| `agent_skill_create` | 创建技能 | `name`, `description`, `scripts` | 技能包 |
| `agent_self_improve` | 自我改进 | `observation`, `lesson_type` | 改进记录 |
| `agent_evolution_check` | 进化检查 | `component`, `trigger` | 检查报告 |
| `agent_memory_search` | 记忆搜索 | `query`, `max_results` | 记忆片段 |
| `agent_memory_update` | 记忆更新 | `key`, `value`, `importance` | 更新状态 |
| `agent_progress_report` | 进度报告 | `task_id`, `milestone` | 进度更新 |
| `agent_theme_apply` | 应用主题 | `artifact`, `theme_id` | 主题化产物 |
| `agent_find_skills` | 发现技能 | `query`, `category` | 技能列表 |

**映射来源**: research-orchestrator, advanced-research-orchestrator, daily-report, coding-agent, skill-creator, self-improving-agent, self-evolution-orchestrator, enhanced-memory-system, progress-reporter, theme-factory, find-skills

---

### 2.7 Research Tools (研究分析) - 6个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `research_web_search` | 网络搜索 | `query`, `sources` | 搜索结果 |
| `research_paper_search` | 论文搜索 | `query`, `arxiv`, `scholar` | 论文列表 |
| `research_github_explore` | GitHub探索 | `repo`, `topic` | 仓库信息 |
| `research_blog_monitor` | 博客监控 | `feeds`, `keywords` | 更新通知 |
| `research_summarize` | 内容摘要 | `content`, `length`, `style` | 摘要文本 |
| `research_citation_extract` | 引用提取 | `text` | 引用列表 |

**映射来源**: research-orchestrator, github, blogwatcher, summarize

---

### 2.8 Productivity Tools (生产力) - 10个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `prod_reminder_create` | 创建提醒 | `title`, `time`, `priority` | 提醒ID |
| `prod_reminder_list` | 列出提醒 | `status`, `time_range` | 提醒列表 |
| `prod_todo_create` | 创建待办 | `title`, `due`, `tags` | 待办ID |
| `prod_calendar_check` | 检查日历 | `date_range` | 事件列表 |
| `prod_note_quick` | 快速笔记 | `content`, `tags` | 笔记ID |
| `prod_spotify_play` | Spotify播放 | `query`, `type` | 播放状态 |
| `prod_spotify_search` | Spotify搜索 | `query`, `type` | 结果列表 |
| `prod_things_task` | Things任务 | `title`, `project`, `tag` | 任务ID |
| `prod_session_log` | 会话记录 | `session_id`, `format` | 日志文件 |
| `prod_doc_create` | 文档创建 | `type`, `content`, `template` | 文档路径 |

**映射来源**: apple-reminders, things-mac, spotify-player, session-logs, doc-coauthoring

---

### 2.9 System Tools (系统管理) - 10个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `sys_health_check` | 健康检查 | `scope`, `risk_level` | 检查报告 |
| `sys_cron_manage` | 定时任务 | `action`, `job_config` | 任务状态 |
| `sys_node_list` | 节点列表 | `status` | 节点信息 |
| `sys_node_camera` | 相机拍照 | `node`, `facing` | 照片路径 |
| `sys_node_screen` | 屏幕录制 | `node`, `duration` | 视频路径 |
| `sys_tmux_control` | Tmux控制 | `action`, `session` | 控制结果 |
| `sys_gateway_config` | 网关配置 | `action`, `config` | 配置状态 |
| `sys_clawhub_install` | 安装技能 | `skill_name`, `version` | 安装状态 |
| `sys_clawhub_update` | 更新技能 | `skill_name` | 更新状态 |
| `sys_password_get` | 获取密码 | `service`, `account` | 密码值 |

**映射来源**: healthcheck, cron, nodes, tmux, clawhub, 1password

---

### 2.10 Home Automation Tools (家庭自动化) - 5个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `home_hue_control` | Hue灯光控制 | `light`, `action`, `color` | 控制状态 |
| `home_sonos_control` | Sonos控制 | `speaker`, `action`, `volume` | 控制状态 |
| `home_location_get` | 获取位置 | `accuracy` | 位置信息 |
| `home_camera_snap` | 相机拍照 | `camera`, `room` | 照片路径 |
| `home_device_list` | 设备列表 | `type`, `room` | 设备列表 |

**映射来源**: openhue, sonoscli, camsnap

---

### 2.11 Specialized Tools (专业工具) - 4个Skills

| Tool名称 | 描述 | 输入参数 | 返回值 |
|---------|------|---------|--------|
| `spec_oracle_query` | Oracle查询 | `query`, `connection` | 查询结果 |
| `spec_order_place` | 下单 | `vendor`, `items`, `payment` | 订单信息 |
| `spec_gemini_chat` | Gemini对话 | `message`, `model` | 回复内容 |
| `spec_song_identify` | 歌曲识别 | `audio_source` | 歌曲信息 |

**映射来源**: oracle, ordercli, gemini, songsee

---

## 三、Resources 设计

### 3.1 可访问资源

```json
{
  "resources": [
    {
      "uri": "memory://long-term",
      "name": "长期记忆",
      "description": "用户的长期记忆数据库",
      "mimeType": "application/json"
    },
    {
      "uri": "memory://session/{session_id}",
      "name": "会话记忆",
      "description": "特定会话的记忆",
      "mimeType": "application/json"
    },
    {
      "uri": "workspace://files",
      "name": "工作区文件",
      "description": "工作目录文件列表",
      "mimeType": "text/plain"
    },
    {
      "uri": "skills://list",
      "name": "技能列表",
      "description": "所有可用技能的清单",
      "mimeType": "application/json"
    },
    {
      "uri": "learning://progress",
      "name": "学习进度",
      "description": "学习模式的进度和统计",
      "mimeType": "application/json"
    }
  ]
}
```

---

## 四、Prompts 设计

### 4.1 可复用提示模板

```json
{
  "prompts": [
    {
      "name": "research_deep_dive",
      "description": "深度研究模式",
      "template": "你是一个专业研究员。请对以下主题进行深度研究：{{topic}}。要求：1)使用System 2慢路径思考 2)至少使用3个不同来源 3)提供结构化报告"
    },
    {
      "name": "code_review",
      "description": "代码审查模式",
      "template": "你是一个资深工程师。请审查以下代码：{{code}}。关注：1)安全性 2)性能 3)可维护性 4)提供改进建议"
    },
    {
      "name": "creative_explore",
      "description": "创意探索模式",
      "template": "你是一个创意探索者。针对主题：{{topic}}，请：1)提出3个不同角度的思考 2)每个角度深入2层 3)发现潜在关联"
    },
    {
      "name": "learning_mode",
      "description": "学习模式",
      "template": "启动学习模式。主题：{{topic}}。配置：自动执行={{auto}}，System 2触发={{deep_trigger}}，评估周期={{eval_rounds}}轮"
    }
  ]
}
```

---

## 五、实施路线图

### 阶段1: 核心Tools (1-2周)
- [ ] file_read_text / file_write_text
- [ ] web_search_brave / web_fetch_page
- [ ] agent_memory_search / agent_memory_update
- [ ] core_plan_task / core_decompose_problem

### 阶段2: 领域Tools (2-3周)
- [ ] File Tools完整实现
- [ ] Web Tools完整实现
- [ ] Communication Tools核心功能

### 阶段3: 高级功能 (3-4周)
- [ ] Resources支持
- [ ] Prompts模板系统
- [ ] Sampling能力

### 阶段4: 优化与扩展 (持续)
- [ ] 性能优化
- [ ] 新Skills自动注册
- [ ] 外部MCP Server连接

---

## 六、示例调用

### 6.1 文件读取
```json
{
  "tool": "file_read_text",
  "params": {
    "path": "/root/.openclaw/workspace/MEMORY.md",
    "offset": 1,
    "limit": 50
  }
}
```

### 6.2 深度研究
```json
{
  "tool": "agent_deep_research",
  "params": {
    "topic": "multi-agent systems 2025",
    "evaluation_criteria": ["relevance", "authority", "timeliness", "credibility"],
    "depth": "comprehensive"
  }
}
```

### 6.3 消息发送
```json
{
  "tool": "comm_send_message",
  "params": {
    "channel": "telegram",
    "target": "user_id",
    "message": "研究完成，报告已生成"
  }
}
```

---

## 七、与OpenClaw集成

### 7.1 配置文件
```yaml
# /root/.openclaw/mcp.yaml
mcp:
  server:
    name: "Kimi Claw MCP Server"
    version: "1.0.0"
    transport: stdio  # 或 http
    
  tools:
    auto_register: true
    prefix: "kimi_"
    
  skills:
    mapping:
      "pdf": ["file_pdf_extract", "file_pdf_create"]
      "docx": ["file_docx_read", "file_docx_create"]
      "slack": ["comm_slack_send", "comm_slack_search"]
      # ... 其他映射
```

### 7.2 启动方式
```bash
# 方式1: 内嵌启动
openclaw mcp serve --embed

# 方式2: 独立进程
python -m kimi_mcp_server

# 方式3: stdio模式（IDE集成）
npx -y kimi-mcp-server
```

---

## 八、总结

**本设计将85个Skills归类为12个领域的48个核心Tools**，通过MCP协议标准化接口，实现：

1. **统一发现**: 所有能力通过`tools/list`自动暴露
2. **类型安全**: 每个Tool有明确的JSON Schema
3. **可组合性**: Tools可链式调用构建复杂工作流
4. **可扩展性**: 新Skills自动注册为Tools
5. **互操作性**: 未来可连接外部MCP Clients

**下一步**: 是否开始实现阶段1的核心Tools？
