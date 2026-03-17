# 学习记录: B站视频处理最佳实践

**日期**: 2026-03-15  
**来源**: video_to_kg.py 实测验证  
**标签**: #bilibili #video-processing #subtitles #rag

---

## 核心发现

处理B站视频时，**优先使用原生字幕，避免Whisper转录**。

---

## 原因

| 方案 | 速度 | 稳定性 | 质量 |
|------|------|--------|------|
| yt-dlp下载原生字幕 | ⚡ 秒级 | ✅ 稳定 | ✅ AI字幕准确 |
| Whisper本地转录 | 🐢 30-40分钟 | ❌ 进程被SIGKILL | ✅ 准确 |

**关键问题**: 系统对运行>20分钟的进程自动清理(SIGKILL)，导致Whisper转录失败。

---

## 正确流程

```bash
# 1. 检查可用字幕
yt-dlp --list-subs URL --cookies cookies.txt

# 2. 下载原生字幕（如果有）
yt-dlp --skip-download --write-subs --sub-langs ai-zh \
  --output output/subtitles/BV_ID --cookies cookies.txt URL

# 3. 无字幕时才用Whisper（分段处理避免超时）
```

---

## 可用字幕类型

- `ai-zh`: B站AI生成中文字幕 ✅ 推荐
- `ai-en`: AI英文字幕
- `danmaku`: 弹幕(xml格式)

---

## 技术细节

### 时间格式转换
SRT格式用逗号分隔毫秒：`00:01:23,456`  
ffmpeg需要点号：`00:01:23.456`

```python
timestamp = sub['start'].replace(',', '.')  # 关键转换
```

### Cookie有效性
- 从浏览器导出cookies.txt有效
- 支持1080P高码率下载
- 无Cookie时降质到480P

---

## 应用于知识图谱

本次实测：BV1nvcuz5Ewj (Kimi K2.5论文串讲)
- 1581条AI字幕
- 提取12个关键时刻
- 生成KG JSON可直接导入RAG-Anything

---

## 经验总结

1. **先检查后执行**: 总是先用 `--list-subs` 检查
2. **分层降级**: 原生字幕 → Whisper → 无字幕处理
3. **时间敏感任务**: >10分钟考虑分段或后台cron

---

*固化时间: 2026-03-15*
