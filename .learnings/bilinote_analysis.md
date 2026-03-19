# BiliNote - AI视频笔记工具分析

## 项目概况
- **仓库**: JefferyHcool/BiliNote
- **Stars**: 5.3k
- **功能**: AI视频笔记生成工具
- **支持平台**: Bilibili、YouTube、抖音、本地视频

## 核心能力
1. **音频转录** - 本地Fast-Whisper模型
2. **内容总结** - GPT大模型生成结构化笔记
3. **截图提取** - 自动截取关键帧
4. **多平台支持** - B站、YouTube、抖音链接
5. **Markdown输出** - 结构化笔记格式

## 技术栈
- 后端: FastAPI (Python)
- 前端: Vite + React
- 音频: FFmpeg + Fast-Whisper
- AI: GPT API (可配置)

## 部署方式
1. Docker一键部署
2. 本地源码运行
3. Windows打包版(exe)

## 用户需求匹配度
✅ 支持B站视频
✅ 提取音频转文字
✅ 自动生成笔记
✅ 可选截图
⚠️ 需要配置API key或本地模型
